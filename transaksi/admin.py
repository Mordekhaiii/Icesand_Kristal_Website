from django.contrib import admin
from django.contrib import admin
from .models import Produk, Transaksi, DetailTransaksi, LaporanPenjualan, Ulasan, MutasiStok, Wilayah
from django.utils.html import format_html
import urllib.parse



# Wilayah
admin.site.register(Wilayah)

@admin.register(Produk)
class ProdukAdmin(admin.ModelAdmin):
    list_display = (
        'nama', 'harga', 'stok_awal', 'total_masuk', 
        'stok_keluar', 'barang_rusak', 'stock_reject', 
        'stock_akhir', 'status'
    )

    readonly_fields = ('stok_awal', 'total_masuk', 'stok_keluar', 'barang_rusak', 'stock_reject', 'stock_akhir')

@admin.register(MutasiStok)
class MutasiStokAdmin(admin.ModelAdmin):
    list_display = ('tanggal', 'produk', 'tipe', 'jumlah', 'keterangan')
    list_filter = ('tipe', 'tanggal', 'produk')
    search_fields = ('produk__nama', 'keterangan')

@admin.register(DetailTransaksi)
class DetailTransaksiAdmin(admin.ModelAdmin):
    # Ini yang bikin kolomnya muncul di halaman "Change detail transaksi"
    list_display = ('transaksi', 'produk', 'jumlah_pesanan', 'total_harga')
    readonly_fields = ('total_harga',)
    fields = ('transaksi', 'produk', 'jumlah_pesanan', 'total_harga')

# Tambahkan ini juga biar di halaman Transaksi (induk) muncul otomatis
class DetailTransaksiInline(admin.TabularInline):
    model = DetailTransaksi
    extra = 1
    readonly_fields = ('total_harga',)

from django.utils.html import format_html

# pesanan/admin.py
# pesanan/admin.py
import urllib.parse
from django.contrib import admin
from django.utils.html import format_html
from .models import Transaksi, DetailTransaksi # pastikan import ini benar

class DetailTransaksiInline(admin.TabularInline):
    model = DetailTransaksi
    extra = 1
    readonly_fields = ('total_harga',)

@admin.register(Transaksi)
class TransaksiAdmin(admin.ModelAdmin):
    # 1. Menampilkan field baru di halaman list/daftar transaksi admin
    list_display = ('kode_transaksi', 'user', 'wilayah_tujuan', 'total_harga', 'total_pembayaran', 'status_bayar', 'tombol_wa')
    
    # 2. Tambahkan wilayah_tujuan__nama_wilayah agar admin bisa mencari berdasarkan nama kota/kabupaten
    search_fields = ('kode_transaksi', 'nama_penerima', 'telepon', 'wilayah_tujuan__nama_wilayah')
    
    # 3. Masukkan field kalkulasi otomatis ke readonly agar tidak bisa diubah manual oleh admin
    readonly_fields = ('kode_transaksi', 'total_harga', 'total_pembayaran', 'tombol_wa')
    
    # Biarkan inline kamu tetap ada
    # inlines = [DetailTransaksiInline] 

    def tombol_wa(self, obj):
        if obj.kode_transaksi:
            # Format ribuan ala Indonesia untuk semua komponen biaya
            produk_formatted = "{:,.0f}".format(obj.total_harga).replace(',', '.')
            ongkir_formatted = "{:,.0f}".format(obj.biaya_ongkir).replace(',', '.')
            kemasan_formatted = "{:,.0f}".format(obj.biaya_kemasan).replace(',', '.')
            layanan_formatted = "{:,.0f}".format(obj.biaya_layanan).replace(',', '.')
            total_formatted = "{:,.0f}".format(obj.total_pembayaran).replace(',', '.')
            
            nama_wilayah = obj.wilayah_tujuan.nama_wilayah if obj.wilayah_tujuan else "Bogor"
            
            # Pesan WA diperbarui agar memuat rincian sesuai kemauan penguji
            pesan = (
                f"Halo Admin PT. ICESAND,\n\n"
                f"Saya mau konfirmasi pembayaran untuk:\n"
                f"📌 *Nota:* {obj.kode_transaksi}\n"
                f"👤 *Nama Penerima:* {obj.nama_penerima or '-'}\n"
                f"📍 *Tujuan:* {nama_wilayah}\n\n"
                f"📋 *Rincian Biaya:*\n"
                f"▪️ Total Produk: Rp {produk_formatted}\n"
                f"▪️ Biaya Ongkir: Rp {ongkir_formatted}\n"
                f"▪️ Biaya Kemasan: Rp {kemasan_formatted}\n"
                f"▪️ Biaya Layanan: Rp {layanan_formatted}\n"
                f"=========================\n"
                f"💰 *TOTAL AKHIR:* Rp {total_formatted}\n\n"
                f"Mohon dicek dan segera diproses ya, terima kasih."
            )
            pesan_enc = urllib.parse.quote(pesan)
            link = f"https://wa.me/6281293387036?text={pesan_enc}"
            
            return format_html(
                '<a class="button" href="{}" target="_blank" '
                'style="background-color: #25D366; color: white; padding: 5px 10px; '
                'border-radius: 4px; text-decoration: none; font-weight: bold;">'
                '<i class="fab fa-whatsapp"></i> Chat WA</a>',
                link
            )
        return "-"
    
    tombol_wa.short_description = 'Konfirmasi WhatsApp'
    
from django.contrib import admin
from .models import LaporanPenjualan

@admin.register(LaporanPenjualan)
class LaporanPenjualanAdmin(admin.ModelAdmin):
    # Mengubah judul halaman form
    change_form_template = None 
    
    list_display = ('periode', 'tanggal_mulai', 'tanggal_akhir', 'total_pendapatan')
    
    fieldsets = (
        ('Parameter Laporan', {
            'fields': ('periode', 'tanggal_mulai', 'tanggal_akhir'),
            'description': '<div style="color: #666; margin-bottom: 10px;">Pilih rentang tanggal untuk menarik data riwayat transaksi.</div>'
        }),
        ('Hasil Perhitungan (Otomatis)', {
            'fields': ('total_transaksi', 'pendapatan_tunai', 'pendapatan_non-tunai', 'total_pendapatan'),
            'description': '<strong>Nilai di bawah ini akan terisi otomatis saat Anda menekan tombol Save.</strong>'
        }),
    )

    readonly_fields = ('total_transaksi', 'pendapatan_cash', 'pendapatan_non_tunai', 'total_pendapatan')

    # Mengubah judul di breadcrumb dan title tag
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Riwayat Laporan Penjualan'
        return super().changelist_view(request, extra_context=extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Buat Laporan Baru'
        return super().add_view(request, form_url, extra_context=extra_context)
# admin.site.register(LaporanPenjualan)