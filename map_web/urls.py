# urls.py
from django.urls import path, include
from django.contrib import admin
from chamu import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('chamu/', include('chamu.urls')),
]