from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('nama_lengkap', 'no_telepon', 'alamat', 'role')}),
    )
    list_display = ['username', 'email', 'nama_lengkap', 'role']

admin.site.register(User, CustomUserAdmin)