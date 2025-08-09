# urls.py
from django.urls import path
from django.contrib import admin
from chamu import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.homepage, name='homepage'),
    path('evaluation/<int:user_info_id>/', views.evaluation_survey_view, name='evaluation_survey'),
    path('matching/<int:user_info_id>/', views.matching_survey_view, name='matching_survey'),
    path('results/<int:user_info_id>/', views.matching_results_view, name='matching_results'),
    # path('api/matching-details/<int:user_info_id>/<int:province_id>/',
    #      views.get_province_matching_details, name='matching_details_api'),
]