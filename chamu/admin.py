from django.contrib import admin
from .models import (
    Prefecture, Municipality, Country, UserInfo, Criteria,
    EvaluationSurvey, MunicipalityBaseScore, MunicipalityMatchingScore
)

# Inlines để quản lý dữ liệu liên quan ngay trong trang cha
class MunicipalityBaseScoreInline(admin.TabularInline):
    model = MunicipalityBaseScore
    extra = 1

class MunicipalityMatchingScoreInline(admin.TabularInline):
    model = MunicipalityMatchingScore
    extra = 1

class MunicipalityInline(admin.TabularInline):
    model = Municipality
    extra = 1

# Đăng ký các model chính với các tùy chỉnh hiển thị
@admin.register(Prefecture)
class PrefectureAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    inlines = [MunicipalityInline]

@admin.register(Municipality)
class MunicipalityAdmin(admin.ModelAdmin):
    list_display = ('name', 'prefecture',)
    list_filter = ('prefecture',)
    search_fields = ('name',)
    inlines = [MunicipalityBaseScoreInline]

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(UserInfo)
class UserInfoAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'municipality',)
    list_filter = ('country', 'municipality',)
    search_fields = ('name',)

@admin.register(Criteria)
class CriteriaAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug',)
    search_fields = ('name', 'slug',)

@admin.register(EvaluationSurvey)
class EvaluationSurveyAdmin(admin.ModelAdmin):
    list_display = ('user', 'municipality', 'criteria', 'score',)
    list_filter = ('municipality', 'criteria', 'user__country',)
    search_fields = ('user__name',)

@admin.register(MunicipalityMatchingScore)
class MunicipalityMatchingScoreAdmin(admin.ModelAdmin):
    list_display = ('municipality', 'country', 'criteria', 'avg_score', 'final_score',)
    list_filter = ('municipality', 'country', 'criteria',)
    search_fields = ('municipality__name', 'country__name',)

@admin.register(MunicipalityBaseScore)
class MunicipalityBaseScoreAdmin(admin.ModelAdmin):
    list_display = ('municipality', 'criteria', 'base_score',)
    list_filter = ('municipality', 'criteria',)