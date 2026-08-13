from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .forms import CreateUserForm, UserUpdateForm

User = get_user_model()

# --- FUNGSI LOGIN ---
def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.role in ['admin', 'owner']:
            return redirect('dashboard')
        return redirect('home')

    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        
        if user is not None:
            login(request, user)
            
            # Menitipkan tanda agar popup welcome muncul di halaman home
            request.session['just_logged_in'] = True

            if user.is_superuser or user.role == 'admin' or user.role == 'owner':
                messages.success(request, f"Selamat datang kembali, {user.username}!")
                return redirect('dashboard')
            else:
                return redirect('home')
        else:
            messages.error(request, "Username atau Password salah!")
            # Kembalikan nilai 'u' ke template agar tidak hilang
            return render(request, 'accounts/login.html', {'last_username': u})
            
    return render(request, 'accounts/login.html')
    
# --- FUNGSI LOGOUT ---
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.info(request, "Berhasil keluar.")
        return redirect('login')
    # Jika diakses lewat URL biasa, arahkan ke home atau logout paksa
    logout(request)
    return redirect('login')

# --- FUNGSI REGISTER ---
def register_view(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'pelanggan' # Default role dari models
            user.save()
            messages.success(request, f"Akun {user.nama_usaha or user.nama_lengkap} berhasil dibuat! Silakan login.")
            return redirect('login')
        else:
            messages.error(request, "Pendaftaran gagal. Mohon periksa kembali data Anda.")
    else:
        form = CreateUserForm()
    
    return render(request, 'accounts/register.html', {'form': form})

# --- FUNGSI EDIT PROFIL ---
@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil berhasil diperbarui!")
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=request.user)
    
    return render(request, 'accounts/edit_profile.html', {'form': form})

# --- FUNGSI PROFILE ---
@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {'user': request.user})


@login_required
def edit_profile(request):
    if request.method == 'POST':
        # request.FILES wajib ada agar foto profil tersimpan
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil bisnis Anda berhasil diperbarui!")
            return redirect('profile') # Mengarahkan kembali ke halaman profil
        else:
            messages.error(request, "Gagal memperbarui profil. Silakan cek kembali inputan Anda.")
    else:
        # Menampilkan data lama user secara otomatis di kotak input (Auto-fill)
        form = UserUpdateForm(instance=request.user)
    
    return render(request, 'accounts/edit_profile.html', {'form': form})