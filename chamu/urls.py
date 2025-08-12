from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('ajax/login/', views.ajax_login, name='ajax_login'),
    path('ajax/signup/', views.ajax_signup, name='ajax_signup'),
    path('ajax/update/', views.ajax_update, name='ajax_update'),
    path('ajax/logout/', views.ajax_logout, name='ajax_logout'),
    path('evaluation/<int:user_info_id>/', views.evaluation_survey_view, name='evaluation_survey'),
    path('matching/<int:user_info_id>/', views.matching_survey_view, name='matching_survey'),
    path('results/<int:user_info_id>/', views.matching_results_view, name='matching_results'),
    # path('api/matching-details/<int:user_info_id>/<int:province_id>/',
    #      views.get_province_matching_details, name='matching_details_api'),
]
