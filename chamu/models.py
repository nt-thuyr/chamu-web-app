from django.db import models

SCALE_CHOICES = [(i, str(i)) for i in range(1, 6)]

class UserInfo(models.Model):
    name = models.CharField(max_length=100)
    birthday = models.DateField(blank=True, null=True)
    nationality = models.CharField(max_length=100)
    current_residence = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class EvaluationSurvey(models.Model):
    user_info = models.ForeignKey(UserInfo, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    cheap_expensive = models.IntegerField(choices=SCALE_CHOICES)
    quiet_crowded = models.IntegerField(choices=SCALE_CHOICES)
    lowcrime_highcrime = models.IntegerField(choices=SCALE_CHOICES)
    fewshops_manyshops = models.IntegerField(choices=SCALE_CHOICES)
    cool_hot = models.IntegerField(choices=SCALE_CHOICES)

    def __str__(self):
        return f"Survey of {self.user_info.name} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"
