import json
from datetime import timedelta
import urllib.parse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q

# Import Model & Form Lokal (Pastikan nama Form sudah TransaksiForm atau KonfirmasiPembayaran)
from .models import Transaksi, Produk, LaporanPenjualan, DetailTransaksi, Ulasan, MutasiStok
from .forms import KonfirmasiPembayaran
from users.models import User
from .forms import ProdukForm

from django.core.paginator import Paginator

# --- HELPER PERMISSION ---
def is_admin(user):
    return user.is_authenticated and user.is_superuser

# --- VIEW: HALAMAN UTAMA (HOME) ---
def home(request):
    if request.user.is_authenticated:
        if request.user.is_staff or getattr(request.user, 'role', None) == 'Owner':
            return redirect('dashboard')
    
    # Untuk Menampilkan Notifikasi Popup Selamat Datang
    show_welcome = request.session.get('just_logged_in', False)
    if show_welcome:
        del request.session['just_logged_in']
        
    # Untuk Jenis Produk dan Menghitungnya
    produk_besar = Produk.objects.filter(nama__icontains="Besar").first()
    produk_kecil = Produk.objects.filter(nama__icontains="Kecil").first()

    context = {
        'stok_besar': produk_besar.stok if produk_besar else 0,
        'stok_kecil': produk_kecil.stok if produk_kecil else 0,
        'show_welcome': show_welcome,
    }
    return render(request, 'home.html', context)

# --- VIEW: PROSES TRANSAKSI (CHECKOUT) ---
def product_list(request):
    if request.method == 'POST':
        try:
            # 1. Ambil data JSON dari frontend (cart/keranjang)
            data = json.loads(request.body)
            items = data.get('items', [])
            total = data.get('total', 0)
            
            # --- AMBIL WILAYAH YANG DIPILIH DARI FRONTEND ---
            wilayah_id = data.get('wilayah_id') # Menangkap pilihan wilayah dari javascript checkout
            
            # 2. Validasi keranjang kosong
            if not items:
                return JsonResponse({'status': 'error', 'message': 'Keranjang belanja Anda kosong.'}, status=400)

            # 3. Membuat Transaksi Baru
            # (Kolom ongkir, kemasan, layanan, dan total_pembayaran terisi OTOMATIS berkat model save() kamu)
            transaksi = Transaksi.objects.create(
                user=request.user,
                total_harga=total,
                wilayah_tujuan_id=wilayah_id, # Masukkan ID wilayah ke foreignkey
                status_bayar='Menunggu Konfirmasi'
            )

            # 4. Simpan Detail Item yang Dibeli
            for item in items:
                produk = get_object_or_404(Produk, id=item['id'])
                DetailTransaksi.objects.create(
                    transaksi=transaksi,
                    produk=produk,
                    jumlah_pesanan=item['quantity']
                )

            # 5. Berhasil! Kirim URL redirect ke halaman pembayaran
            return JsonResponse({
                'status': 'success', 
                'redirect_url': '/payment/',
                'invoice': transaksi.kode_transaksi 
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    # --- BAGIAN GET TETAP SAMA SEPERTI KODE KAMU ---
    produk_besar = Produk.objects.filter(nama__icontains="Besar").first()
    produk_kecil = Produk.objects.filter(nama__icontains="Kecil").first()

    # Tambahkan daftar_wilayah ke context agar bisa dirender di HTML
    from .models import Wilayah # Pastikan Wilayah di-import
    context = {
        'produk_besar': produk_besar,
        'produk_kecil': produk_kecil,
        'stok_besar': produk_besar.stok if produk_besar else 0,
        'stok_kecil': produk_kecil.stok if produk_kecil else 0,
        'daftar_wilayah': Wilayah.objects.all(), # Mengirim data ke dropdown HTML
        'title': 'Pemesanan Es Kristal - PT. ICESAND'
    }
    return render(request, 'transaksi/product_list.html', context)

# --- VIEW: PEMBAYARAN (CUSTOMER) ---
@login_required
def payment_list(request):
    # Ambil transaksi terbaru yang masih menunggu konfirmasi
    transaksi = Transaksi.objects.filter(user=request.user, status_bayar='Menunggu Konfirmasi').order_by('-id').first()

    # Proteksi: Jika tidak ada pesanan yang sedang diproses, jangan tampilkan halaman checkout
    if not transaksi and request.method == 'GET':
        messages.warning(request, "Anda tidak memiliki pesanan yang perlu dikonfirmasi.")
        return redirect('product_list')

    if request.method == 'POST':
        if not transaksi:
            messages.error(request, "Data transaksi tidak ditemukan!")
            return redirect('product_list')

        form = KonfirmasiPembayaran(request.POST, request.FILES, instance=transaksi)
        if form.is_valid():
            # Simpan form terlebih dahulu namun jangan langsung di-commit ke database murni
            trx_obj = form.save(commit=False)
            # Paksa jalankan fungsi save() kustom dari models.py kamu agar hitungan otomatis berjalan
            trx_obj.save() 
            
            messages.success(request, f"Pembayaran {transaksi.kode_transaksi} sedang diverifikasi Admin.")
            return redirect('detail_transaksi') 
    else:
        # Inisialisasi form dengan instance transaksi untuk method GET
        form = KonfirmasiPembayaran(instance=transaksi)

        # Logika Otomatis Terisi saat halaman pertama kali dimuat
        if transaksi:
            if not transaksi.nama_penerima:
                form.initial['nama_penerima'] = request.user.nama_lengkap
            
            if not transaksi.telepon:
                form.initial['telepon'] = request.user.no_telepon
                
            if not transaksi.alamat_lengkap:
                form.initial['alamat_lengkap'] = request.user.alamat

    # --- BARIS INI YANG TADI TERPOTONG ATAU HILANG ---
    context = {
        'form': form,
        'trx': transaksi,
    }
    return render(request, 'Payment/payment_list.html', context)

# --- VIEW: DETAIL & CANCEL ---
@login_required
def detail_transaksi(request, transaksi_id=None):
    if transaksi_id:
        # Menampilkan Detail Invoice (Satu Transaksi)
        trx = get_object_or_404(Transaksi, id=transaksi_id, user=request.user)
        return render(request, 'transaksi/detail_transaksi.html', {'trx': trx})
    else:
        # --- LOGIKA AUTO-CLEANUP DI-UPDATE AGAR LEBIH AKURAT ---
        # Hapus semua transaksi sampah yang statusnya masih 'Menunggu Konfirmasi' 
        # TAPI user belum memilih wilayah tujuan (wilayah_tujuan=None) atau total_pembayaran masih 0
        Transaksi.objects.filter(
            user=request.user, 
            status_bayar='Menunggu Konfirmasi',
            wilayah_tujuan__isnull=True
        ).delete()

        Transaksi.objects.filter(
            user=request.user, 
            status_bayar='Menunggu Konfirmasi',
            total_pembayaran=0
        ).delete()
        # --- LOGIKA AUTO-CLEANUP END ---

        # Menampilkan Tabel Riwayat yang sudah bersih dari sampah
        daftar_trx = Transaksi.objects.filter(user=request.user).order_by('-tanggal')
        return render(request, 'transaksi/detail_transaksi.html', {'daftar_trx': daftar_trx})
        

@login_required
def cetak_nota(request, transaksi_id):
    if request.user.is_superuser:
        # Jika Admin (Superuser), boleh cetak nota siapa saja
        trx = get_object_or_404(Transaksi, id=transaksi_id)
    else:
        # Jika Pelanggan, hanya boleh cetak nota miliknya sendiri
        trx = get_object_or_404(Transaksi, id=transaksi_id, user=request.user)
    
    return render(request, 'cetak_nota.html', {'trx': trx})

def contact(request):
    return render(request, 'kontak_kami.html')


# Cancel Order Ketika di Detail Transaction
@login_required
def cancel_order(request, trx_id):
    if request.method == 'POST':
        # Admin bisa batalin punya siapa aja, User cuma punya sendiri
        if request.user.is_staff:
            trx = get_object_or_404(Transaksi, id=trx_id)
        else:
            trx = get_object_or_404(Transaksi, id=trx_id, user=request.user)
        
        # AMBIL STATUS ASLI & BERSIHKAN (PENTING!)
        # .strip() hapus spasi di depan/belakang
        # .lower() ubah jadi huruf kecil semua
        status_db = str(trx.status_bayar).strip().lower()
        
        # Cek apakah statusnya adalah 'menunggu konfirmasi'
        if status_db == 'menunggu konfirmasi':
            trx.status_bayar = 'Dibatalkan'
            trx.save()
            return JsonResponse({'status': 'success'})
        else:
            # Jika gagal, tampilkan status asli yang dibaca sistem agar kita tahu salahnya dimana
            return JsonResponse({
                'status': 'error', 
                'message': f'Gagal! Di sistem statusnya "{trx.status_bayar}". Pembatalan hanya bisa jika Menunggu Konfirmasi.'
            })
            
    return JsonResponse({'status': 'error', 'message': 'Metode tidak diizinkan'})


# Cancel Transaksi di Payment List
def cancel_transaction(request, trx_id):
    if request.method == 'POST':
        # Logika hapus atau update status transaksi di sini
        # Contoh: Transaction.objects.filter(id=trx_id).delete()
        return redirect('home')
    

# Selesai Order
# Cancel Order Ketika di Detail Transaction
@login_required
def cancel_order(request, trx_id):
    if request.method == 'POST':
        # Admin bisa batalin punya siapa aja, User cuma punya sendiri
        if request.user.is_staff:
            trx = get_object_or_404(Transaksi, id=trx_id)
        else:
            trx = get_object_or_404(Transaksi, id=trx_id, user=request.user)
        
        # .strip() hapus spasi di depan/belakang
        # .lower() ubah jadi huruf kecil semua
        status_db = str(trx.status_bayar).strip().lower()
        
        # Cek apakah statusnya adalah 'menunggu konfirmasi'
        if status_db == 'menunggu konfirmasi':
            trx.status_bayar = 'Dibatalkan'
            trx.save()
            return JsonResponse({'status': 'success'})
        else:
            # Jika gagal, tampilkan status asli yang dibaca sistem agar kita tahu salahnya dimana
            return JsonResponse({
                'status': 'error', 
                'message': f'Gagal! Di sistem statusnya "{trx.status_bayar}". Pembatalan hanya bisa jika Menunggu Konfirmasi.'
            })
            
    return JsonResponse({'status': 'error', 'message': 'Metode tidak diizinkan'})


# Cancel Transaksi di Payment List
def cancel_transaction(request, trx_id):
    if request.method == 'POST':
        # Logika hapus atau update status transaksi di sini
        # Contoh: Transaction.objects.filter(id=trx_id).delete()
        return redirect('home')
    
# Selesai Order
@login_required
def selesai_order(request, trx_id):
    if request.method == 'POST':
        # Admin bisa menyelesaikan punya siapa saja, User cuma bisa menyelesaikan punya sendiri
        if request.user.is_staff:
            trx = get_object_or_404(Transaksi, id=trx_id)
        else:
            trx = get_object_or_404(Transaksi, id=trx_id, user=request.user)
        
        # Ambil status asli dan bersihkan untuk validasi aman
        status_db = str(trx.status_bayar).strip().lower()
        
        # Validasi: Hanya pesanan yang sedang 'dikirim' yang bisa diselesaikan oleh pelanggan
        if status_db == 'dikirim':
            trx.status_bayar = 'Selesai'
            
            # Ambil file foto bukti yang dikirimkan oleh JavaScript FormData
            if 'foto_bukti' in request.FILES:
                trx.foto_bukti = request.FILES['foto_bukti']
            
            trx.save()
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({
                'status': 'error', 
                'message': f'Gagal! Di sistem statusnya "{trx.status_bayar}". Konfirmasi selesai hanya bisa jika status pesanan "Dikirim".'
            })
            
    return JsonResponse({'status': 'error', 'message': 'Metode tidak diizinkan'})





# --- VIEW: DASHBOARD ADMIN ---
@user_passes_test(lambda u: u.is_authenticated)
def dashboard(request):
    is_owner = request.user.is_staff and not request.user.is_superuser 
    waktu_sekarang = timezone.localtime(timezone.now())
    hari_ini = waktu_sekarang.date()

    # --- DATA DASHBOARD LAINNYA ---
    status_filter = request.GET.get('status', 'Menunggu Konfirmasi')
    transaksi_qs = Transaksi.objects.all().order_by('-tanggal')
    transaksi_filtered = transaksi_qs.filter(status_bayar=status_filter)

    # HALAMAN UNTUK DETAIL TRANSAKSI
    paginator = Paginator(transaksi_filtered, 5)
    page_number = request.GET.get('page') 
    page_obj = paginator.get_page(page_number)
    transaksi_semua = paginator.get_page(page_number)

    # HITUNG TANGGAL TRANSAKSI HARI INI
    transaksi_hari_ini = Transaksi.objects.filter(tanggal__date=hari_ini).count()
    pesanan_selesai = Transaksi.objects.filter(status_bayar='Selesai').count()
    pesanan_dibatalkan = Transaksi.objects.filter(status_bayar='Dibatalkan').count()

    # --- LOGIKA FILTER TANGGAL ---
    tgl_mulai_input = request.GET.get('tgl_mulai')
    tgl_akhir_input = request.GET.get('tgl_akhir')

    if tgl_mulai_input and tgl_akhir_input:
        tgl_mulai = tgl_mulai_input
        tgl_akhir = tgl_akhir_input
    else:
        # Default tampilkan data 30 hari terakhir jika belum difilter
        tgl_mulai = (hari_ini - timedelta(days=30)).strftime('%Y-%m-%d')
        tgl_akhir = hari_ini.strftime('%Y-%m-%d')

    # Query khusus untuk tab laporan (berdasarkan filter tanggal)
    laporan_qs = Transaksi.objects.filter(
        status_bayar='Selesai',
        tanggal__date__range=[tgl_mulai, tgl_akhir]
    )

    # Agregasi Laporan
    stats_laporan = laporan_qs.aggregate(
        total_pendapatan=Sum('total_harga'),
        tunai=Sum('total_harga', filter=Q(metode_pembayaran='Tunai')),
        non_tunai=Sum('total_harga', filter=Q(metode_pembayaran='Non-Tunai'))
    )
        
    # Badge counters
    transaksi_menunggu = transaksi_qs.filter(status_bayar='Menunggu Konfirmasi').count()
    transaksi_diproses = transaksi_qs.filter(status_bayar='Sedang Diproses').count()
    transaksi_dikirim = transaksi_qs.filter(status_bayar='Dikirim').count()
    stok_habis = Produk.objects.filter(stok__lte=0).count()
    stok_menipis = Produk.objects.filter(stok__lte=20).count()

    # Omzet hari ini (tetap real-time hari ini)
    omzet_hari_ini = transaksi_qs.filter(
        tanggal__date=hari_ini, 
        status_bayar='Selesai'
    ).aggregate(total=Sum('total_harga'))['total'] or 0

    # Grafik Penjualan (7 Hari Terakhir)
    labels, data_grafik = [], []
    for i in range(6, -1, -1):
        tgl = hari_ini - timedelta(days=i)
        labels.append(tgl.strftime('%d %b'))
        total = transaksi_qs.filter(tanggal__date=tgl, status_bayar='Selesai').aggregate(t=Sum('total_harga'))['t'] or 0
        data_grafik.append(int(total))

    # Ulasan Pelanggan
    ulasan_list = Ulasan.objects.all().order_by('-tanggal')
    rata_rata_rating = round(ulasan_list.aggregate(Avg('rating'))['rating__avg'] or 0, 1)

    # Laporan Stok Lama (Dipertahankan jika masih dibutuhkan skrip lain)
    produk_qs = Produk.objects.all().order_by('nama')
    laporan_mutasi = []
    total_keluar_stok = 0

    for p in produk_qs:
        total_keluar = p.detailtransaksi_set.filter(
            transaksi__status_bayar__in=['Sedang Diproses', 'Dikirim', 'Selesai'],
            transaksi__tanggal__date__range=[tgl_mulai, tgl_akhir]
        ).aggregate(total=Sum('jumlah_pesanan'))['total'] or 0
        
        laporan_mutasi.append({
            'id': p.id,
            'nama': p.nama,
            'stok_akhir': p.stok,
            'total_keluar': total_keluar,
            'estimasi_stok_awal': p.stok + total_keluar,
        })

    # ===================================================================
    # REVISI DOSEN: LOGIKA PEMROSESAN MUTASI STOK BARU (VIEW OWNER)
    # ===================================================================
    produk_filter = request.GET.get('produk_filter', 'all')
    mutasi_base = MutasiStok.objects.all()
    
    # 1. Terapkan filter Produk Dropdown jika dipilih spesifik
    produk_nama_terpilih = None
    if produk_filter and produk_filter != 'all':
        mutasi_base = mutasi_base.filter(produk_id=produk_filter)
        try:
            produk_nama_terpilih = Produk.objects.get(id=produk_filter).nama
        except Produk.DoesNotExist:
            produk_nama_terpilih = None

    # 2. Hitung Nilai Akumulasi Stok Awal (Semua mutasi SEBELUM tgl_mulai)
    # Rumus: (AWAL + MASUK) - (KELUAR + RUSAK + REJECT)
    sa_awal = mutasi_base.filter(tanggal__lt=tgl_mulai, tipe='AWAL').aggregate(total=Sum('jumlah'))['total'] or 0
    sa_masuk = mutasi_base.filter(tanggal__lt=tgl_mulai, tipe='MASUK').aggregate(total=Sum('jumlah'))['total'] or 0
    sa_keluar = mutasi_base.filter(tanggal__lt=tgl_mulai, tipe='KELUAR').aggregate(total=Sum('jumlah'))['total'] or 0
    sa_rusak = mutasi_base.filter(tanggal__lt=tgl_mulai, tipe='RUSAK').aggregate(total=Sum('jumlah'))['total'] or 0
    sa_reject = mutasi_base.filter(tanggal__lt=tgl_mulai, tipe='REJECT').aggregate(total=Sum('jumlah'))['total'] or 0
    
    total_stok_awal = (sa_awal + sa_masuk) - (sa_keluar + sa_rusak + sa_reject)

    # 3. Ambil data mutasi yang masuk dalam rentang tanggal filter untuk tabel
    mutasi_qs = mutasi_base.filter(tanggal__range=[tgl_mulai, tgl_akhir]).order_by('-tanggal', '-id')
    
    # 4. Hitung Akumulasi data dalam rentang filter periode ini
    total_masuk = mutasi_qs.filter(tipe='MASUK').aggregate(total=Sum('jumlah'))['total'] or 0
    total_keluar = mutasi_qs.filter(tipe='KELUAR').aggregate(total=Sum('jumlah'))['total'] or 0
    
    # Hitung gabungan barang rusak (es mencair) & reject (gagal sortir)
    total_rusak_periode = mutasi_qs.filter(tipe='RUSAK').aggregate(total=Sum('jumlah'))['total'] or 0
    total_reject_periode = mutasi_qs.filter(tipe='REJECT').aggregate(total=Sum('jumlah'))['total'] or 0
    total_reject = total_rusak_periode + total_reject_periode

    # 5. Hitung Sisa Stok Akhir Gudang
    if produk_filter and produk_filter != 'all':
        total_stok_gudang = Produk.objects.filter(id=produk_filter).aggregate(total=Sum('stok'))['total'] or 0
    else:
        total_stok_gudang = Produk.objects.aggregate(total=Sum('stok'))['total'] or 0
    # ===================================================================

    context = {
        'is_owner': is_owner,
        'transaksi_menunggu': transaksi_menunggu,
        'transaksi_diproses': transaksi_diproses,
        'transaksi_dikirim': transaksi_dikirim,
        'stok_habis': stok_habis,
        'omzet_hari_ini': omzet_hari_ini,
        'transaksi_hari_ini': transaksi_hari_ini,
        'pesanan_selesai': pesanan_selesai,
        'pesanan_dibatalkan': pesanan_dibatalkan,
        'stok_menipis': stok_menipis,

        # Laporan Stok Lama
        'laporan_mutasi': laporan_mutasi, 
        'produk_semua': produk_qs,
        'total_keluar_stok': total_keluar_stok,
        
        # === INJECT VARIABEL MUTASISTOK BARU (REVISI) ===
        'mutasi_stok': mutasi_qs,
        'produk_filter': produk_filter,
        'produk_nama_terpilih': produk_nama_terpilih,
        'total_stok_awal': total_stok_awal,
        'total_masuk': total_masuk,
        'total_keluar': total_keluar,
        'total_reject': total_reject,
        'total_stok_gudang': total_stok_gudang,
        # ====================================================

        # Variabel Laporan (Hasil Filter)
        'tgl_mulai': tgl_mulai,
        'tgl_akhir': tgl_akhir,
        'total_pendapatan_rekap': stats_laporan['total_pendapatan'] or 0,
        'pendapatan_tunai': stats_laporan['tunai'] or 0,
        'pendapatan_non_tunai': stats_laporan['non_tunai'] or 0,
        'transaksi_selesai_count': laporan_qs.count(),
        'transaksi_laporan': laporan_qs.order_by('-tanggal'),
        
        # Data Lainnya
        'labels_grafik': labels,
        'data_grafik': data_grafik,
        'transaksi_semua': page_obj, 
        'total_produk': Produk.objects.count(),
        'pelanggan_list': User.objects.all().order_by('-is_staff', 'username'),
        'total_pelanggan': User.objects.count(),
        'ulasan_list': ulasan_list[:10],
        'rata_rata_rating': rata_rata_rating,
        'status_aktif': status_filter,
    }
    return render(request, 'dashboard/dashboard.html', context)

@user_passes_test(lambda u: u.is_staff)
def simpan_mutasi_stok(request, produk_id):
    if request.method == 'POST':
        tipe = request.POST.get('tipe')
        jumlah = int(request.POST.get('jumlah'))
        keterangan = request.POST.get('keterangan')
        
        try:
            produk = Produk.objects.get(id=produk_id)
            
            # 1. Update stok utama pada model Produk
            if tipe == 'MASUK':
                produk.stok += jumlah
                msg_status = f"Berhasil menambahkan {jumlah} Bal ke stok masuk {produk.nama}."
            elif tipe in ['RUSAK', 'REJECT']:
                if produk.stok < jumlah:
                    messages.error(request, f"Gagal! Sisa stok {produk.nama} tidak mencukupi untuk dikurangi.")
                    return redirect('/dashboard/?menu=Produk')
                produk.stok -= jumlah
                msg_status = f"Berhasil mencatat mutasi {tipe.lower()} sebanyak {jumlah} Bal."
            
            produk.save() # Simpan perubahan stok akhir ke tabel Produk
            
            # 2. Catat riwayat log ke model MutasiStok untuk laporan Owner
            MutasiStok.objects.create(
                produk=produk,
                tanggal=timezone.now().date(),
                tipe=tipe,
                jumlah=jumlah,
                keterangan=keterangan if keterangan else f"Diinput manual oleh Admin"
            )
            
            messages.success(request, msg_status)
        except Produk.DoesNotExist:
            messages.error(request, "Produk tidak ditemukan.")
            
    return redirect('/dashboard/?menu=Produk')

@user_passes_test(lambda u: u.is_staff)
def update_status_transaksi(request, transaksi_id):
    if request.method == 'POST':
        aksi = request.POST.get('aksi')
        transaksi = get_object_or_404(Transaksi, id=transaksi_id)
        
        status_baru = transaksi.status_bayar
        tab_target = 'Konfirmasi'

        if aksi == 'terima': 
            status_baru = 'Sedang Diproses'
            tab_target = 'Diproses'
        elif aksi == 'kirim': 
            status_baru = 'Dikirim'
            tab_target = 'Dikirim'
        elif aksi == 'selesai': 
            status_baru = 'Selesai'
            tab_target = 'Selesai'
        elif aksi == 'batalkan': 
            status_baru = 'Dibatalkan'
            tab_target = 'Batal'

        try:
            # Mengubah status transaksi
            transaksi.status_bayar = status_baru
            
            # Cukup panggil transaksi.save(), maka pengurangan stok fisik produk
            # dan pencatatan histori MutasiStok akan dilakukan secara otomatis oleh models.py
            transaksi.save() 
            
            messages.success(request, f"Status diperbarui ke: {status_baru}")
            return redirect(f"/dashboard/?menu=Transaksi&tab={tab_target}")
            
        except Exception as e:
            messages.error(request, f"Gagal: {str(e)}")
            
    return redirect('dashboard')
    
# Produk CRUD
@user_passes_test(lambda u: u.is_staff)
def product_add(request):
    if request.method == 'POST':
        # request.FILES wajib disertakan agar foto produk ter-upload
        form = ProdukForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Produk es kristal baru berhasil ditambahkan!")
            return redirect('dashboard') # Redirect ke halaman utama admin
        else:
            messages.error(request, "Gagal menambahkan produk. Silakan periksa kembali inputan Anda.")
    else:
        # Jika akses biasa (GET), tampilkan form kosong
        form = ProdukForm()

    return render(request, 'dashboard/product_edit.html', {
        'form': form,
        'title': 'Tambah Produk Baru',
        'is_edit': False # Menandakan ini bukan mode edit
    })

@user_passes_test(lambda u: u.is_staff)
def edit_produk(request, pk):
    # Langsung cari produk berdasarkan ID, kalau tidak ada muncul 404
    produk = get_object_or_404(Produk, pk=pk)
    
    # === TAMBAHAN: Catat jumlah stok sebelum diperbarui ===
    stok_lama = produk.stok 
    
    if request.method == 'POST':
        # Post data dan file foto ke form dengan instance produk lama
        form = ProdukForm(request.POST, request.FILES, instance=produk)
        if form.is_valid():
            # 1. Simpan perubahan dari form ke database
            produk_terupdate = form.save() 
            
            # 2. Ambil nilai stok terbaru langsung dari objek yang baru saja di-save
            stok_baru = produk_terupdate.stok 
            
            # 3. Jalankan logika pengecekan selisih mutasi
            if stok_baru > stok_lama:
                MutasiStok.objects.create(
                    produk=produk_terupdate, # Gunakan objek yang sudah terupdate
                    tipe='MASUK',
                    jumlah=stok_baru - stok_lama,
                    keterangan="Pasokan Tambahan / Input Produksi Pabrik Harian"
                )
            elif stok_baru < stok_lama:
                MutasiStok.objects.create(
                    produk=produk_terupdate,
                    tipe='KELUAR',
                    jumlah=stok_lama - stok_baru,
                    keterangan="Penyesuaian Data Stok (Penyusutan / Es Mencair)"
                )
            # ========================================================
            
            messages.success(request, f"Data {produk.nama} berhasil diperbarui!")
            return redirect('dashboard') # Kembali ke dashboard admin
    else:
        # Tampilkan form dengan data produk yang sudah ada di database
        form = ProdukForm(instance=produk)

    return render(request, 'dashboard/product_edit.html', {
        'form': form,
        'produk': produk, # Kirim data produk buat jaga-jaga kalau butuh nama produk di HTML
        'title': f"Edit {produk.nama}",
        'is_edit': True
    })

# Fungsi Hapus (Tanpa HTML)
def hapus_produk(request, pk):
    produk = get_object_or_404(Produk, pk=pk)
    produk.delete()
    messages.success(request, "Produk telah dihapus dari katalog.")
    return redirect('dashboard')


# Ulasan Pelanggan
@login_required
def simpan_ulasan(request, trx_id):
    if request.method == 'POST':
        try:
            # Ambil data JSON yang dikirim dari Fetch API JavaScript tadi
            data = json.loads(request.body)
            transaksi = get_object_or_404(Transaksi, id=trx_id)
            
            # Kita cari produk apa saja yang dibeli di transaksi ini
            # Agar ulasannya nempel ke semua produk yang ada di nota tersebut
            details = transaksi.details.all()
            
            for d in details:
                Ulasan.objects.create(
                    user=request.user,
                    produk=d.produk,
                    rating=data.get('rating'),
                    komentar=data.get('komentar')
                )
            
            return JsonResponse({'status': 'success', 'message': 'Ulasan berhasil disimpan'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=405)


@user_passes_test(lambda u: u.is_staff)
def profil_dashboard(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Admin mengupdate data target
        target_user.email = request.POST.get('email')
        target_user.nama_usaha = request.POST.get('nama_usaha')
        target_user.no_telepon = request.POST.get('no_telepon')
        target_user.alamat = request.POST.get('alamat')
        
        target_user.save()
        messages.success(request, f"Data {target_user.username} berhasil diperbarui!")
        return redirect('dashboard')

    return render(request, 'dashboard/profil_dashboard.html', {'pelanggan': target_user})