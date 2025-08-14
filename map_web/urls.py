# urls.py
from django.urls import path, include
from django.contrib import admin
from chamu import views

urlpatterns = [
    path('api/municipalities/', views.get_municipalities, name='get_municipalities'),
    path('admin/', admin.site.urls),
    path('', include('chamu.urls')),
    path('ajax/login/', views.ajax_login, name='ajax_login'),
    path('ajax/signup/', views.ajax_signup, name='ajax_signup'),
    path('ajax/update/', views.ajax_update, name='ajax_update'),
    path('ajax/logout/', views.ajax_logout, name='ajax_logout'),
]