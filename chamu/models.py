# models.py
from django.db import models

class City(models.Model):
    name = models.CharField(max_length=100, unique=True)
    # description = models.TextField(blank=True)

    # Base scores for the city, set by the initial data
    base_cost_of_living = models.FloatField(default=0.0)  # cheap/expensive
    base_local_shops = models.FloatField(default=0.0)  # few/many local shops
    base_temperature = models.FloatField(default=0.0)  # cool/hot
    base_crime_rate = models.FloatField(default=0.0)  # low/high crime rate
    base_population = models.FloatField(default=0.0)  # quiet/crowded

    def __str__(self):
        return self.name

class Nationality(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class LocalShop(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    nationality = models.ForeignKey(Nationality, on_delete=models.CASCADE)

    shop_number = models.IntegerField(default=0)  # Số lượng cửa hàng địa phương


class UserInfo(models.Model):
    name = models.CharField(max_length=100)
    # models.py
    nationality = models.ForeignKey(Nationality, on_delete=models.SET_NULL, null=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name


class EvaluationSurvey(models.Model):
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    # Các điểm số từ khảo sát của người dùng
    cost_of_living_score = models.IntegerField(default=0)
    local_shops_score = models.IntegerField(default=0)
    temperature_score = models.IntegerField(default=0)
    crime_rate_score = models.IntegerField(default=0)
    population_score = models.IntegerField(default=0)
    # Thêm các trường khác nếu cần
    created_at = models.DateTimeField(auto_now_add=True)

class CityScore(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    nationality = models.ForeignKey(Nationality, on_delete=models.CASCADE)

    # Survey scores for the city, updated based on user evaluations
    avg_cost_of_living = models.FloatField(default=0.0)  # cheap/expensive
    avg_local_shops = models.FloatField(default=0.0)  # few/many local shops
    avg_temperature = models.FloatField(default=0.0)  # cool/hot
    avg_crime_rate = models.FloatField(default=0.0)  # low/high crime rate
    avg_population = models.FloatField(default=0.0)  # quiet/crowded

    # Final scores for matching
    final_cost_of_living = models.FloatField(default=0.0)  # cheap/expensive
    final_local_shops = models.FloatField(default=0.0)  # few/many local shops
    final_temperature = models.FloatField(default=0.0)  # cool/hot
    final_crime_rate = models.FloatField(default=0.0)  # low/high crime rate
    final_population = models.FloatField(default=0.0)  # quiet/crowded

    class Meta:
        unique_together = ('city', 'nationality')

    def __str__(self):
        return f'{self.city.name} - {self.nationality}'
