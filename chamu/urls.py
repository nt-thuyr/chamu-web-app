from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('api/municipalities/', views.get_municipalities, name='get_municipalities'),
    path('api/prefectures/', views.get_prefectures, name='get_prefectures'),
    path('ajax/login/', views.ajax_login, name='ajax_login'),
    path('ajax/signup/', views.ajax_signup, name='ajax_signup'),
    path('ajax/update/', views.ajax_update, name='ajax_update'),
    path('ajax/logout/', views.ajax_logout, name='ajax_logout'),
    # path('api/matching-details/<int:user_info_id>/<int:province_id>/',
    #      views.get_province_matching_details, name='matching_details_api'),
    path('match-info/', views.match_info_view, name='match_info'),
    path('evaluate-info/', views.evaluate_info_view, name='evaluate_info'),
    # Các URL cho survey
    path('survey/<int:user_info_id>/<int:target_prefecture_id>/match/', views.matching_survey_view, name='matching_survey'),
    path('survey/<int:user_info_id>/evaluate/', views.evaluation_survey_view, name='evaluation_survey'),
    path('survey/<int:user_info_id>/<int:target_prefecture_id>/match/result', views.matching_results_view, name='matching_results'),
    path('municipality/<int:municipality_id>/', views.municipality_details_view, name='municipality_details')
]
