from django import forms
from .models import UserInfo, EvaluationSurvey, City, Province, Nationality

class UserInfoForm(forms.ModelForm):
    # This field allows the user to choose the next action they want to take
    ACTION_CHOICES = [
        ('match', 'Find suitable place'),
        ('evaluate', 'Rate current place')
    ]
    next_action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect,
        initial='match',
        label="What do you want to do?"
    )

    class Meta:
        model = UserInfo
        # Specify the fields to include in the form
        fields = ['name', 'nationality', 'province']
        labels = {
            'name': 'Your name',
            'nationality': 'Your nationality',
            'province': 'Your current province',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'nationality': forms.Select(attrs={'class': 'form-control'}),
            'province': forms.Select(attrs={'class': 'form-control'}),
        }

class EvaluationSurveyBaseForm(forms.Form):
    pass


class MatchingSurveyBaseForm(forms.Form):
    pass