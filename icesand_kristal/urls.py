from unicodedata import name
from django.contrib import admin
from django.urls import path, include
from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path,include
from transaksi import views
from users.urls import User


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('transaksi.urls' )),
    path('', include('users.urls')), 
]


from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
