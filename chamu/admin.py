from django.contrib import admin
from .models import (
    City,
    Nationality,
    LocalShop,
    UserInfo,
    EvaluationSurvey,
    CityScore
)

# Để hiển thị các trường liên kết, bạn cần dùng TabularInline
class LocalShopInline(admin.TabularInline):
    model = LocalShop
    extra = 1  # Số lượng form trống để thêm mới

class CityScoreInline(admin.TabularInline):
    model = CityScore
    extra = 1

# Các lớp Admin chính để tùy chỉnh giao diện
@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_cost_of_living', 'base_local_shops', 'base_temperature')
    search_fields = ('name',)
    inlines = [LocalShopInline, CityScoreInline] # Hiển thị LocalShop và CityScore trong trang City

@admin.register(Nationality)
class NationalityAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(UserInfo)
class UserInfoAdmin(admin.ModelAdmin):
    list_display = ('name', 'nationality', 'city')
    list_filter = ('nationality', 'city')
    search_fields = ('name',)

@admin.register(EvaluationSurvey)
class EvaluationSurveyAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'cost_of_living_score', 'created_at')
    list_filter = ('city', 'user__nationality') # Lọc khảo sát theo thành phố và quốc tịch của người dùng
    search_fields = ('user__name',)

@admin.register(LocalShop)
class LocalShopAdmin(admin.ModelAdmin):
    list_display = ('city', 'nationality', 'shop_number')
    list_filter = ('city', 'nationality')

@admin.register(CityScore)
class CityScoreAdmin(admin.ModelAdmin):
    list_display = ('city', 'nationality', 'avg_cost_of_living', 'final_cost_of_living')
    list_filter = ('city', 'nationality')