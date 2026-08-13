from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import get_user_model
from .models import Transaksi  # Pastikan import model Transaksi yang baru
from django import forms
from .models import Produk

User = get_user_model()

# --- FORM: PENDAFTARAN USER BARU ---
class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['nama_lengkap', 'username', 'email', 'nama_usaha', 'no_telepon', 'alamat']

# --- FORM: EDIT PROFIL PELANGGAN ---
class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['nama_lengkap', 'nama_usaha', 'no_telepon', 'alamat', 'profile_picture']
        widgets = {
            'nama_lengkap': forms.TextInput(attrs={'class': 'form-control'}),
            'nama_usaha': forms.TextInput(attrs={'class': 'form-control'}),
            'no_telepon': forms.TextInput(attrs={'class': 'form-control'}),
            'alamat': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

# --- FORM: UPDATE USERNAME/EMAIL ---
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

# --- FORM: GANTI PASSWORD ---
class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

# --- FORM: KONFIRMASI PEMBAYARAN & ALAMAT (REVISI WILAYAH) ---
class KonfirmasiPembayaran(forms.ModelForm):
    class Meta:
        model = Transaksi
        fields = [
            'nama_penerima', 
            'telepon', 
            'wilayah_tujuan',  # <-- 1. Tambahkan field Wilayah Tujuan di sini
            'alamat_lengkap', 
            'metode_pembayaran', 
            'bukti_pembayaran'
        ]
        
        widgets = {
            'nama_penerima': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contoh: Toko Berkah / Bpk. Mordekhai'
            }),
            'telepon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contoh: 08123456789'
            }),
            # <-- 2. Tambahkan widget Select untuk Dropdown Wilayah Tujuan
            'wilayah_tujuan': forms.Select(attrs={
                'class': 'form-control',
            }),
            'alamat_lengkap': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Alamat pengiriman lengkap...'
            }),
            'metode_pembayaran': forms.Select(attrs={
                'class': 'form-control',
            }),
            'bukti_pembayaran': forms.ClearableFileInput(attrs={
                'class': 'form-control',
            }),
        }

    def __init__(self, *args, **kwargs):
        super(KonfirmasiPembayaran, self).__init__(*args, **kwargs)
        # Menambahkan label kosong yang rapi untuk dropdown Wilayah dan Metode
        self.fields['wilayah_tujuan'].empty_label = "--- Pilih Kota / Kabupaten Tujuan ---"
        self.fields['metode_pembayaran'].empty_label = "--- Pilih Metode Pembayaran ---"
        
        self.fields['wilayah_tujuan'].label = "Wilayah Tujuan Pengiriman"
        self.fields['bukti_pembayaran'].label = "Unggah Bukti Scan QRIS (Jika Non-Tunai)"



class ProdukForm(forms.ModelForm):
    class Meta:
        model = Produk
        fields = ['nama', 'harga', 'stok', 'foto', 'deskripsi', 'status']







































# from django.forms import ModelForm
# from django.contrib.auth.forms import UserCreationForm
# from django.contrib.auth.models import User
# from django import forms
# from users.models import User
# from django import forms
# from django.contrib.auth import get_user_model

# User = get_user_model()



# class CreateUserForm(UserCreationForm):
#     class Meta:
#         model = User
#         fields = [ 'nama_lengkap', 'username', 'email', 'nama_usaha', 'no_telepon', 'alamat', 'password1', 'password2']

# class EditProfileForm(forms.ModelForm):
#     class Meta:
#         model = User
#         # Tulis semua field yang ingin ditampilkan di form
#         fields = ['nama_lengkap', 'nama_usaha', 'no_telepon', 'alamat', 'profile_picture']

# # Update Profile Form
# from django.contrib.auth.forms import PasswordChangeForm
# from django import forms

# class UserUpdateForm(forms.ModelForm):
#     class Meta:
#         model = User
#         fields = ['username', 'email']
#         widgets = {
#             'username': forms.TextInput(attrs={'class': 'form-control'}),
#             'email': forms.EmailInput(attrs={'class': 'form-control'}),
#         }

# class CustomPasswordChangeForm(PasswordChangeForm):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['old_password'].widget.attrs.update({'class': 'form-control'})
#         self.fields['new_password1'].widget.attrs.update({'class': 'form-control'})
#         self.fields['new_password2'].widget.attrs.update({'class': 'form-control'})


# from django import forms
# from .models import Transaksi

# class KonfirmasiPembayaran(forms.ModelForm):
#     class Meta:
#         model = Transaksi
#         # HAPUS 'quantity' dan 'product' dari sini karena di model Transaksi tidak ada
#         fields = [
#             'nama_penerima', 
#             'telepon', 
#             'alamat_lengkap', 
#             'metode_pembayaran', 
#             'bukti_pembayaran'
#         ]
        
#         # Pastikan tulisan 'widgets' ini lurus/sejajar dengan 'fields' di atasnya
#         widgets = {
#             'nama_penerima': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Contoh: Toko Berkah / Bpk. Mordekhai'
#             }),
#             'telepon': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Contoh: 08123456789'
#             }),
#             'alamat_lengkap': forms.Textarea(attrs={
#                 'class': 'form-control',
#                 'rows': 3,
#                 'placeholder': 'Alamat pengiriman...'
#             }),
#             'metode_pembayaran': forms.Select(attrs={
#                 'class': 'form-control',
#             }),
#             'bukti_pembayaran': forms.ClearableFileInput(attrs={
#                 'class': 'form-control',
#             }),
#         }


# # Bukti Pembayaran
# # from .models import bukti_pembayaran  # Model untuk menyimpan bukti pembayaran

# # class bukti_pembayaran(forms.ModelForm):
# #     class Meta:
# #         model = bukti_pembayaran
# #         fields = ['bukti_bayar']  # Field untuk mengunggah bukti pembayaran

