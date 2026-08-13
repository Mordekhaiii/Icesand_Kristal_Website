from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class CreateUserForm(UserCreationForm):
    # --- Definisi Fields ---
    nama_lengkap = forms.CharField(label="Nama Lengkap Pemilik", max_length=255)
    nama_usaha = forms.CharField(label="Nama Toko/Usaha", max_length=255, required=False, widget=forms.TextInput(attrs={'placeholder': 'Contoh: Kopi Nako'}))
    no_telepon = forms.CharField(label="Nomor Telepon", max_length=15)
    email = forms.EmailField(label="Email Bisnis")
    alamat = forms.CharField(label="Alamat Pengiriman", widget=forms.Textarea(attrs={'rows': 2}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = [
            'username',
            'nama_lengkap', 
            'nama_usaha',
            'email', 
            'no_telepon',
            'alamat',
        ]

    # --- Validasi ---
    def clean_no_telepon(self):
        no_telepon = self.cleaned_data.get('no_telepon')
        if User.objects.filter(no_telepon=no_telepon).exists():
            raise ValidationError("Nomor Telepon ini sudah terdaftar.")
        return no_telepon

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email ini sudah digunakan.")
        return email

    # --- PENTING: Fungsi Save Agar Data Tersimpan ---
    def save(self, commit=True):
        user = super().save(commit=False)
        # Ambil data dari field custom dan masukkan ke model user
        user.nama_lengkap = self.cleaned_data["nama_lengkap"]
        user.nama_usaha = self.cleaned_data["nama_usaha"]
        user.no_telepon = self.cleaned_data["no_telepon"]
        user.email = self.cleaned_data["email"]
        user.alamat = self.cleaned_data["alamat"]
        user.role = User.PELANGGAN # Set otomatis jadi pelanggan
        
        if commit:
            user.save()
        return user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = ""
        # Loop ini jauh lebih bersih daripada ngetik 'class' satu-satu
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

# --- FORM EDIT PROFIL (SETTING) ---
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['nama_lengkap', 'nama_usaha', 'email', 'no_telepon', 'alamat', 'profile_picture']
        widgets = {
            'alamat': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'forxm-control'})