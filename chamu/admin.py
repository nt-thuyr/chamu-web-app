from django.contrib import admin
from .models import (
    City, Province, Nationality, UserInfo, Criteria,
    EvaluationSurvey, ProvinceBaseScore, ProvinceMatchingScore
)

# Inlines để quản lý dữ liệu liên quan ngay trong trang cha
class ProvinceBaseScoreInline(admin.TabularInline):
    model = ProvinceBaseScore
    extra = 1

class ProvinceMatchingScoreInline(admin.TabularInline):
    model = ProvinceMatchingScore
    extra = 1

class ProvinceInline(admin.TabularInline):
    model = Province
    extra = 1

# Đăng ký các model chính với các tùy chỉnh hiển thị
@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    inlines = [ProvinceInline]

@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ('name', 'city',)
    list_filter = ('city',)
    search_fields = ('name',)
    inlines = [ProvinceBaseScoreInline]

@admin.register(Nationality)
class NationalityAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(UserInfo)
class UserInfoAdmin(admin.ModelAdmin):
    list_display = ('name', 'nationality', 'province',)
    list_filter = ('nationality', 'province',)
    search_fields = ('name',)

@admin.register(Criteria)
class CriteriaAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug',)
    search_fields = ('name', 'slug',)

@admin.register(EvaluationSurvey)
class EvaluationSurveyAdmin(admin.ModelAdmin):
    list_display = ('user', 'province', 'criteria', 'score',)
    list_filter = ('province', 'criteria', 'user__nationality',)
    search_fields = ('user__name',)

@admin.register(ProvinceMatchingScore)
class ProvinceMatchingScoreAdmin(admin.ModelAdmin):
    list_display = ('province', 'nationality', 'criteria', 'avg_score', 'final_score',)
    list_filter = ('province', 'nationality', 'criteria',)
    search_fields = ('province__name', 'nationality__name',)

@admin.register(ProvinceBaseScore)
class ProvinceBaseScoreAdmin(admin.ModelAdmin):
    list_display = ('province', 'criteria', 'base_score',)
    list_filter = ('province', 'criteria',)