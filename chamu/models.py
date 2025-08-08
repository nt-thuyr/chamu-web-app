from django.contrib.auth.models import User
from django.db import models

class Criteria(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="e.g. cost of living, local shops, ...")
    slug = models.SlugField(unique=True, help_text="e.g. cost_of_living, local_shops, ...")

    def __str__(self):
        return self.name

# -----------------
# Core Models
# -----------------
class City(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class Province(models.Model):
    name = models.CharField(max_length=100, unique=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    def __str__(self):
        return f'{self.name} ({self.city.name})'

class Nationality(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class UserInfo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    nationality = models.ForeignKey(Nationality, on_delete=models.SET_NULL, null=True, blank=True)
    province = models.ForeignKey(Province, on_delete=models.SET_NULL, null=True, blank=True)
    def __str__(self):
        return self.name

# -----------------
# Score Models
# -----------------
class ProvinceBaseScore(models.Model):
    province = models.ForeignKey(Province, on_delete=models.CASCADE)
    criteria = models.ForeignKey(Criteria, on_delete=models.CASCADE)
    base_score = models.FloatField(default=0.0)

    class Meta:
        unique_together = ('province', 'criteria')

    def __str__(self):
        return f'{self.province.name} - {self.criteria.name} (Base)'

class EvaluationSurvey(models.Model):
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE)
    province = models.ForeignKey(Province, on_delete=models.CASCADE)
    criteria = models.ForeignKey(Criteria, on_delete=models.CASCADE)
    score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

class ProvinceMatchingScore(models.Model):
    province = models.ForeignKey(Province, on_delete=models.CASCADE)
    nationality = models.ForeignKey(Nationality, on_delete=models.CASCADE)
    criteria = models.ForeignKey(Criteria, on_delete=models.CASCADE)
    avg_score = models.FloatField(default=0.0)
    final_score = models.FloatField(default=0.0)

    class Meta:
        unique_together = ('province', 'nationality', 'criteria')

    def __str__(self):
        return f'{self.province.name} - {self.nationality.name} - {self.criteria.name}'