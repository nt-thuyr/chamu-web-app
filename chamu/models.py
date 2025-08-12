from django.conf import settings
from django.db import models
from django.utils.text import slugify

User = settings.AUTH_USER_MODEL

class Criteria(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="e.g. cost of living, local shops, ...")
    slug = models.SlugField(unique=True, help_text="e.g. cost_of_living, local_shops, ...")

    left_label = models.CharField(max_length=100, help_text="Not good. e.g. 'Expensive', 'Low', ...")
    right_label = models.CharField(max_length=100, help_text="Good. e.g. 'Cheap', 'High', ...")

    is_reverse = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Criteria, self).save(*args, **kwargs)

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
class MunicipalityBaseScore(models.Model):
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    criteria = models.ForeignKey(Criteria, on_delete=models.CASCADE)
    base_score = models.FloatField(default=0.0)

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

class MunicipalityMatchingScore(models.Model):
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    criteria = models.ForeignKey(Criteria, on_delete=models.CASCADE)
    avg_score = models.FloatField(default=0.0)
    final_score = models.FloatField(default=0.0)

    class Meta:
        unique_together = ('municipality', 'country', 'criteria')

    def __str__(self):
        return f'{self.municipality.name} - {self.country.name} - {self.criteria.name}'