from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

class User(AbstractUser):
    OWNER = 'owner'
    ADMIN = 'admin'
    PELANGGAN = 'pelanggan'
    
    ROLES = [
        (OWNER, 'Owner'),
        (ADMIN, 'Admin/Staff'),
        (PELANGGAN, 'Pelanggan'),
    ]

    # --- Identitas Bisnis ---
    nama_lengkap = models.CharField(max_length=255)
    nama_usaha = models.CharField(max_length=255, null=True, blank=True, help_text="Contoh: Kopi Nako Bogor")
    email = models.EmailField(unique=True)
    
    # --- Data Kontak & Pengiriman (Penting untuk Distributor) ---
    alamat = models.TextField(null=True, blank=True, help_text="Alamat lengkap pengiriman es")
    
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Nomor telepon tidak valid.")
    no_telepon = models.CharField(validators=[phone_regex], max_length=15, null=True, blank=True)
    
    # --- Foto Profil (Bagus untuk Admin mengenali pelanggan) ---
    profile_picture = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)
    
    # --- Hak Akses ---
    role = models.CharField(max_length=20, choices=ROLES, default=PELANGGAN)

    def __str__(self):
        # Biar di Admin muncul: morde - Kopi Nako Bogor
        return f"{self.username} - {self.nama_usaha if self.nama_usaha else self.nama_lengkap}"
    
    @property
    def is_owner_role(self):
        # Akun superuser otomatis dianggap owner demi kemudahan akses
        return self.role == self.OWNER or self.is_superuser

    @property
    def is_admin_role(self):
        return self.role == self.ADMIN