# urls.py
from django.urls import path, include
from django.contrib import admin
from chamu import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('chamu/', include('chamu.urls')),
    path('api/municipalities/', views.get_municipalities, name='get_municipalities'),
    path('api/prefectures/', views.get_prefectures, name='get_prefectures'),
]