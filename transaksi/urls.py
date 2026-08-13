from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # --- HALAMAN UTAMA ---
    path('', views.home, name='home'),
    path('home/', views.home, name='home_alias'), # Alias agar link home.html lama tidak error
    
    # --- PRODUK & BELANJA ---
    path('products/', views.product_list, name='product_list'),
    path('contact/', views.contact, name='contact'),
    
    # --- DASHBOARD ADMIN ---
    path('dashboard/', views.dashboard, name='dashboard'),
    path('update-status-transaksi/<int:transaksi_id>/', views.update_status_transaksi, name='update_status_transaksi'),
    path('dashboard/user/edit/<int:user_id>/', views.profil_dashboard, name='profil_dashboard'),
    path('produk/tambah/', views.product_add, name='product_add'),
    path('produk/edit/<int:pk>/', views.edit_produk, name='product_edit'),
    path('produk/hapus/<int:pk>/', views.hapus_produk, name='prodict_edit'),
    path('simpan-ulasan/<int:trx_id>/', views.simpan_ulasan, name='simpan_ulasan'),
    path('produk/mutasi/<int:produk_id>/', views.simpan_mutasi_stok, name='simpan_mutasi_stok'),
    
    # --- TRANSAKSI & PEMBAYARAN (CUSTOMER) ---
    path('payment/', views.payment_list, name='payment_list'),
    path('detail-transaksi/', views.detail_transaksi, name='detail_transaksi'),
    path('detail-transaksi/<int:transaksi_id>/', views.detail_transaksi, name='detail_transaksi_detail'),
    path('selesai-order/<int:trx_id>/', views.selesai_order, name='selesai_order'),
    path('cancel-order/<int:trx_id>/', views.cancel_order, name='cancel_order'),
    path('cancel-transaction/<int:trx_id>/', views.cancel_transaction, name='cancel_transaction'),
    path('cetak-nota/<int:transaksi_id>/', views.cetak_nota, name='cetak_nota'),
    
]

# --- MEDIA SETTINGS (UNTUK FOTO PRODUK & BUKTI BAYAR) ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
























# from django.urls import path
# from . import views
# from django.urls import path, include
# from django.contrib import admin
# from django.conf import settings
# from django.conf.urls.static import static
# from django.shortcuts import render, redirect
# from django.contrib.auth.decorators import login_required
# from .models import Produk
# from django.contrib.auth import views as auth_views


# urlpatterns = [
#     path('home.html',views.home,name='home'),
#     path('',views.home,name='home'),
#     path('admin/', admin.site.urls),
#     path('products/', views.product_list, name='product_list'),
#     path('contact/', views.contact, name='contact'),
#     path('dashboard/', views.dashboard, name='dashboard'),
#     path('cetak-nota/<int:transaksi_id>/', views.cetak_nota, name='cetak_nota'),
# # pesanan/urls.py
#     path('update-status/<int:transaksi_id>/', views.update_status_pesanan, name='update_status'),
#     path('payment/', views.payment_list, name='payment_list'),
#     path('detail-transaksi/<int:transaksi_id>/', views.detail_transaksi, name='detail_transaksi'),
#     path('cancel-pesanan/<int:transaksi_id>/', views.cancel_pesanan, name='cancel_pesanan'),

# ]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)