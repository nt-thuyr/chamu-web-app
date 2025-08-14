from django.conf import settings
from django.db import models
from django.utils.text import slugify
from autoslug import AutoSlugField

User = settings.AUTH_USER_MODEL

class Criteria(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Name of the criteria, e.g. 'Cost of Living', 'Safety', etc.")
    slug = AutoSlugField(populate_from='name', unique=True, always_update=True)

    left_label = models.CharField(max_length=100, help_text="Good. e.g. 'Cheap', 'Safe', ...")
    right_label = models.CharField(max_length=100, help_text="Bad. e.g. 'Expensive', 'Unsafe', ...")

    is_reverse = models.BooleanField(default=False)

    def __str__(self):
        return self.name

# -----------------
# Core Models
# -----------------
class Prefecture(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class Municipality(models.Model):
    name = models.CharField(max_length=100, unique=True)
    prefecture = models.ForeignKey(Prefecture, on_delete=models.CASCADE)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    def __str__(self):
        return f'{self.name} ({self.prefecture.name})'

class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class UserInfo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    municipality = models.ForeignKey(Municipality, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

# -----------------
# Score Models
# -----------------
class MunicipalityScore(models.Model):
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    criteria = models.ForeignKey(Criteria, on_delete=models.CASCADE)
    base_score = models.FloatField(default=0.0)
    avg_score = models.FloatField(default=0.0)
    final_score = models.FloatField(default=0.0)

    class Meta:
        unique_together = ('municipality', 'country', 'criteria')

    def __str__(self):
        return f'{self.municipality.name} - {self.criteria.name} (Base)'

class EvaluationSurvey(models.Model):
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE)
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE)
    criteria = models.ForeignKey(Criteria, on_delete=models.CASCADE)
    score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)