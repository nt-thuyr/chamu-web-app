from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('match-info/', views.match_info_view, name='match_info'),
    path('evaluate-info/', views.evaluate_info_view, name='evaluate_info'),
    # Các URL cho survey
    path('survey/<int:user_info_id>/<int:target_prefecture_id>/match/', views.matching_survey_view, name='matching_survey'),
    path('survey/<int:user_info_id>/evaluate/', views.evaluation_survey_view, name='evaluation_survey'),
    path('survey/<int:user_info_id>/<int:target_prefecture_id>/match/result', views.matching_results_view, name='matching_results'),
    path('municipality/<int:municipality_id>/', views.municipality_details_view, name='municipality_details'),
    path('about/', views.about_view, name='about'),
    path('survey/<int:user_info_id>/evaluate/thank_you', views.thank_you_view, name='thank_you'),
]
