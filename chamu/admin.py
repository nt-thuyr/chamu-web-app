from django.contrib import admin
from .models import (
    UserInfo,
    EvaluationSurvey,
)

# Register your models here.
@admin.register(UserInfo)
class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'birthday', 'nationality', 'current_residence')

@admin.register(EvaluationSurvey)
class EvaluationSurveyAdmin(admin.ModelAdmin):
    list_display = ('user_info', 'created_at', 'cheap_expensive', 'quiet_crowded',
                    'lowcrime_highcrime', 'fewshops_manyshops', 'cool_hot')
    list_filter = ('created_at',)
    search_fields = ('user_info__name',)
    date_hierarchy = 'created_at'
