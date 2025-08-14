# urls.py
from django.urls import path, include
from django.contrib import admin
from chamu import views

urlpatterns = [
    path('api/prefectures/', views.get_prefectures, name='get_prefectures'),
    path('api/municipalities/', views.get_municipalities, name='get_municipalities'),
    path('api/prefecture_coords/', views.get_prefecture_coords, name='get_prefecture_coords'),
    path('api/municipality_coords/', views.get_municipality_coords, name='get_municipality_coords'),
    path('api/location_by_coords/', views.get_location_by_coords, name='get_location_by_coords'),
    path('admin/', admin.site.urls),
    path('', include('chamu.urls')),
    path('ajax/login/', views.ajax_login, name='ajax_login'),
    path('ajax/signup/', views.ajax_signup, name='ajax_signup'),
    path('ajax/update/', views.ajax_update, name='ajax_update'),
    path('ajax/logout/', views.ajax_logout, name='ajax_logout'),
]