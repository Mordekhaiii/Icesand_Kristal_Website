from django.db import models, transaction
from django.conf import settings
from django.db.models import Sum
from django.core.exceptions import ValidationError
import uuid
from datetime import datetime
from django.utils import timezone
import urllib.parse #WA

class Produk(models.Model):
    STATUS_CHOICES = [
        ('Tersedia', 'Tersedia'),
        ('Habis', 'Habis'),
    ]
    
    nama = models.CharField(max_length=100)
    foto = models.ImageField(upload_to='produk/', null=True, blank=True)
    deskripsi = models.TextField()
    harga = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Tersedia') 
    stok = models.PositiveIntegerField(default=0, help_text="Stok Fisik Saat Ini")

    def __str__(self):
        return self.nama

    # --- TAMBAHAN UNTUK AKOMODASI REVISI PENGUJI ---

    @property
    def stok_awal(self):
        # Mengambil total mutasi bertipe 'AWAL'
        total = self.mutasi.filter(tipe='AWAL').aggregate(Sum('jumlah'))['jumlah__sum'] or 0
        return total

    @property
    def total_masuk(self):
        # Tambahan jika ada restock bulanan di luar stok awal
        total = self.mutasi.filter(tipe='MASUK').aggregate(Sum('jumlah'))['jumlah__sum'] or 0
        return total

    @property
    def stok_keluar(self):
        # Mengambil total mutasi bertipe 'KELUAR' (Penjualan)
        total = self.mutasi.filter(tipe='KELUAR').aggregate(Sum('jumlah'))['jumlah__sum'] or 0
        return total

    @property
    def barang_rusak(self):
        # Mengambil total mutasi bertipe 'RUSAK' (Misal: Es Mencair di jalan/gudang)
        total = self.mutasi.filter(tipe='RUSAK').aggregate(Sum('jumlah'))['jumlah__sum'] or 0
        return total

    @property
    def stock_reject(self):
        # Mengambil total mutasi bertipe 'REJECT' (Gagal sortir sebelum dijual)
        total = self.mutasi.filter(tipe='REJECT').aggregate(Sum('jumlah'))['jumlah__sum'] or 0
        return total

    @property
    def stock_akhir(self):
        # RUMUS REVISI PENGUJI:
        # Stock Akhir = (Stok Awal + Masuk) - Stok Keluar - Barang Rusak - Stock Reject
        akhir = (self.stok_awal + self.total_masuk) - self.stok_keluar - self.barang_rusak - self.stock_reject
        return akhir

class Wilayah(models.Model):
    nama_wilayah = models.CharField(max_length=100) # Contoh: "Kota Depok", "Kota Sukabumi"
    biaya_ongkir = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.nama_wilayah} (Rp {self.biaya_ongkir:,.0f})"

    class Meta:
        verbose_name = "Master Wilayah Ongkir"
        verbose_name_plural = "Master Wilayah Ongkir"


# 2. Update Model Transaksi Kamu Jadi Seperti Ini:
class Transaksi(models.Model):
    # --- STATUS TRANSAKSI & METODE PEMBAYARAN (Tetap sama seperti kode kamu) ---
    STATUS_PILIHAN = [
        ('Menunggu Konfirmasi', 'Menunggu Konfirmasi'),
        ('Sedang Diproses', 'Sedang Diproses'),
        ('Dikirim', 'Dikirim'),
        ('Selesai', 'Selesai'),
        ('Dibatalkan', 'Dibatalkan'),
    ]
    METODE_PILIHAN = [
        ('Tunai', 'Tunai (Cash)'),
        ('Non-Tunai', 'Non-Tunai (Transfer / QRIS)'),
    ]

    kode_transaksi = models.CharField(max_length=20, unique=True, editable=False, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tanggal = models.DateTimeField(auto_now_add=True)
    status_bayar = models.CharField(max_length=50, choices=STATUS_PILIHAN, default='Menunggu Konfirmasi')
    
    # --- FIELD UPDATE REVISI PENGUJI ---
    wilayah_tujuan = models.ForeignKey(Wilayah, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Wilayah Tujuan")
    biaya_ongkir = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Biaya Ongkir")
    biaya_kemasan = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Biaya Kemasan")
    biaya_layanan = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Biaya Layanan")
    
    # total_harga ini adalah total murni harga produk (Subtotal dari semua DetailTransaksi)
    total_harga = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total Harga Produk")
    
    # total_pembayaran ini adalah hasil akhir: total_harga + biaya_ongkir + biaya_kemasan + biaya_layanan
    total_pembayaran = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total Akhir Pembayaran")
    
    metode_pembayaran = models.CharField(max_length=50, choices=METODE_PILIHAN, default='Tunai')
    bukti_pembayaran = models.ImageField(upload_to='bukti_bayar/', null=True, blank=True)
    nama_penerima = models.CharField(max_length=100, blank=True, null=True)
    telepon = models.CharField(max_length=20, blank=True, null=True)
    alamat_lengkap = models.TextField(blank=True, null=True)
    foto_bukti = models.ImageField(upload_to='bukti_penerimaan/', null=True, blank=True)

    def __str__(self):
        return f"{self.kode_transaksi} - {self.nama_penerima}"

    def clean(self):
        if self.metode_pembayaran == 'Non-Tunai' and not self.bukti_pembayaran:
            raise ValidationError({'bukti_pembayaran': 'Mohon lampirkan bukti Transfer/QRIS Anda.'})
        super().clean()

    # --- UPDATE WHATSAPP LINK (Menampilkan total_pembayaran akhir beserta rincian biaya) ---
    def get_whatsapp_link(self):
        nomor_admin = "628111165221" 
        pesan = (
            f"Halo Admin Icesand Kristal,\n\n"
            f"Saya Mau Konfirmasi Pembayaran:\n"
            f"📌 *No. Transaksi:* {self.kode_transaksi}\n"
            f"👤 *Nama:* {self.nama_penerima}\n"
            f"📍 *Tujuan:* {self.wilayah_tujuan.nama_wilayah if self.wilayah_tujuan else '-'}\n"
            f"📦 *Total Produk:* Rp {self.total_harga:,.0f}\n"
            f"🚚 *Ongkir:* Rp {self.biaya_ongkir:,.0f}\n"
            f"🛍️ *Kemasan:* Rp {self.biaya_kemasan:,.0f}\n"
            f"💳 *Layanan:* Rp {self.biaya_layanan:,.0f}\n"
            f"💰 *TOTAL AKHIR:* Rp {self.total_pembayaran:,.0f}\n"
            f"💳 *Metode:* {self.metode_pembayaran}\n\n"
            f"Mohon segera diproses ya Admin, Terima kasih.."
        )
        pesan_encoded = urllib.parse.quote(pesan)
        return f"https://wa.me/{nomor_admin}?text={pesan_encoded}"

    def save(self, *args, **kwargs):
        # 1. Logika Pembuatan Kode Transaksi Otomatis (Tetap sama seperti kode kamu)
        if not self.kode_transaksi:
            sekarang = timezone.now()
            tahun = sekarang.strftime('%Y')
            bulan = sekarang.strftime('%m')
            prefix = f"INV/{tahun}/{bulan}/"
            last_transaction = type(self).objects.filter(kode_transaksi__startswith=prefix).order_by('-id').first()

            if last_transaction and last_transaction.kode_transaksi:
                try:
                    last_number = int(last_transaction.kode_transaksi.split('/')[-1])
                    nomor_urut = last_number + 1
                except (ValueError, IndexError):
                    nomor_urut = 1
            else:
                nomor_urut = 1

            self.kode_transaksi = f"{prefix}{str(nomor_urut).zfill(3)}"

      # # 2. OTOMATISASI BIAYA BERDASARKAN MASTER DATA WILAYAH YANG DIPILIH
        if self.wilayah_tujuan:
            # Otomatis mengambil tarif ongkir dari Master Wilayah
            self.biaya_ongkir = self.wilayah_tujuan.biaya_ongkir
            
            # Otomatis menentukan biaya kemasan (Luar Bogor Styrofoam, Dalam Bogor Gratis)
            # Menggunakan .lower() agar deteksi teks tidak sensitif huruf besar/kecil
            if "luar bogor" in self.wilayah_tujuan.nama_wilayah.lower():
                self.biaya_kemasan = 25000  # Biaya Styrofoam Box agar es kristal tidak cair
            else:
                self.biaya_kemasan = 0      # GANTI KE 0: Kemasan plastik gratis untuk wilayah Bogor
        else:
            self.biaya_ongkir = 0
            self.biaya_kemasan = 0

        # Otomatis mengisi biaya layanan flat aplikasi
        self.biaya_layanan = 2000

        # 3. HITUNG TOTAL AKHIR PEMBAYARAN SECARA OTOMATIS
        self.total_pembayaran = float(self.total_harga) + float(self.biaya_ongkir) + float(self.biaya_kemasan) + float(self.biaya_layanan)

        self.full_clean()
        
        # 4. Logika Update Stok & Histori MutasiStok Keluar (Tetap sama seperti kode kamu)
        if self.pk:
            status_lama = Transaksi.objects.get(pk=self.pk).status_bayar
            if status_lama == 'Menunggu Konfirmasi' and self.status_bayar == 'Sedang Diproses':
                with transaction.atomic():
                    for item in self.details.all():
                        produk = item.produk
                        if produk.stok >= item.jumlah_pesanan:
                            produk.stok -= item.jumlah_pesanan
                            produk.save()
                            
                            # Catat mutasi keluar riil
                            MutasiStok.objects.create(
                                produk=produk,
                                tipe='KELUAR',
                                jumlah=item.jumlah_pesanan,
                                keterangan=f"Penjualan No Transaksi {self.kode_transaksi}"
                            )
                        else:
                            raise ValueError(f"Stok {produk.nama} tidak mencukupi!")
            
            elif status_lama in ['Sedang Diproses', 'Dikirim'] and self.status_bayar == 'Dibatalkan':
                with transaction.atomic():
                    for item in self.details.all():
                        produk = item.produk
                        produk.stok += item.jumlah_pesanan
                        produk.save()
                        
                        # Catat mutasi masuk kembali (pembatalan)
                        MutasiStok.objects.create(
                            produk=produk,
                            tipe='MASUK',
                            jumlah=item.jumlah_pesanan,
                            keterangan=f"Pembatalan Transaksi {self.kode_transaksi}"
                        )

        super().save(*args, **kwargs)

# DetailTransaksi dan LaporanPenjualan tetap sama 
        
class DetailTransaksi(models.Model):
    transaksi = models.ForeignKey(Transaksi, on_delete=models.CASCADE, related_name='details')
    produk = models.ForeignKey(Produk, on_delete=models.CASCADE)
    jumlah_pesanan = models.PositiveIntegerField(default=1)
    # INI YANG AKAN MUNCUL DI HALAMAN FOTO KAMU:
    total_harga = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False, verbose_name="Subtotal")

    def save(self, *args, **kwargs):
        # 1. Hitung subtotal otomatis (Harga Produk x Jumlah)
        self.total_harga = self.produk.harga * self.jumlah_pesanan
        super().save(*args, **kwargs)

        # 2. Update otomatis Total Harga di Nota induknya
        # Menggunakan .update() agar lebih cepat dan tidak memicu pengulangan save()
        all_details = DetailTransaksi.objects.filter(transaksi=self.transaksi)
        new_total = all_details.aggregate(Sum('total_harga'))['total_harga__sum'] or 0
        Transaksi.objects.filter(id=self.transaksi.id).update(total_harga=new_total)

    def __str__(self):
        return f"{self.produk.nama} ({self.jumlah_pesanan})"
    
class LaporanPenjualan(models.Model):
    tanggal_laporan = models.DateTimeField(auto_now_add=True, verbose_name="Waktu Pembuatan")
    periode = models.CharField(max_length=50, unique=True, verbose_name="Periode Laporan")
    
    # Filter Mesin
    tanggal_mulai = models.DateField(
        verbose_name="Dari Tanggal",
        help_text="Catatan: Input sesuai tanggal lokal Anda."
    )
    tanggal_akhir = models.DateField(
        verbose_name="Sampai Tanggal",
        help_text="Catatan: Input sesuai tanggal lokal Anda."
    )
    
    # Hasil Otomatis
    total_transaksi = models.IntegerField(default=0, editable=False)
    pendapatan_cash = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    pendapatan_non_tunai = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    total_pendapatan = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)

    def save(self, *args, **kwargs):
        # Menggunakan range tanggal. Django akan menangani konversi timezone 
        # jika USE_TZ = True di settings.py
        qs_filter = Transaksi.objects.filter(
            status_bayar='Selesai',
            tanggal__date__range=[self.tanggal_mulai, self.tanggal_akhir]
        )
        
        self.total_transaksi = qs_filter.count()
        
        # Perhitungan agregasi
        stats = qs_filter.aggregate(
            cash=Sum('total_harga', filter=models.Q(metode_pembayaran='Cash')),
            non_tunai=Sum('total_harga', filter=models.Q(metode_pembayaran='Non-Tunai'))
        )
        
        self.pendapatan_cash = stats['cash'] or 0
        self.pendapatan_non_tunai = stats['non_tunai'] or 0
        self.total_pendapatan = self.pendapatan_cash + self.pendapatan_non_tunai
        
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Laporan Penjualan"
        verbose_name_plural = "Laporan Penjualan"

    def __str__(self):
        return self.periode
    

class Ulasan(models.Model):
    RATING_CHOICES = [
        (1, '1 - Sangat Buruk'),
        (2, '2 - Buruk'),
        (3, '3 - Cukup'),
        (4, '4 - Bagus'),
        (5, '5 - Sangat Puas'),
    ]

    produk = models.ForeignKey(Produk, on_delete=models.CASCADE, related_name='ulasan')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES, default=5)
    komentar = models.TextField()
    tanggal = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.produk.nama} ({self.rating}★)"
    

class MutasiStok(models.Model):
    TIPE_CHOICES = [
        ('AWAL', 'Stok Awal'),
        ('MASUK', 'Masuk (Restock)'),
        ('KELUAR', 'Keluar (Penjualan)'),
        ('RUSAK', 'Barang Rusak (Es Mencair)'),
        ('REJECT', 'Stock Reject (Gagal Sortir)'),
    ]
    
    produk = models.ForeignKey(Produk, on_delete=models.CASCADE, related_name='mutasi')
    tanggal = models.DateField(default=timezone.now)
    # Ubah max_length menjadi 7 agar muat menampung string 'KELUAR' atau 'REJECT'
    tipe = models.CharField(max_length=7, choices=TIPE_CHOICES) 
    jumlah = models.IntegerField()
    keterangan = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.tanggal} - {self.produk.nama} ({self.tipe} {self.jumlah})" 