from django import forms
from .models import UserInfo, EvaluationSurvey, Prefecture, Municipality, Country

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
        fields = ['name', 'country', 'municipality']
        labels = {
            'name': 'Your name',
            'country': 'Your country',
            'municipality': 'Your current municipality',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.Select(attrs={'class': 'form-control'}),
            'municipality': forms.Select(attrs={'class': 'form-control'}),
        }

class EvaluationSurveyBaseForm(forms.Form):
    pass


class MatchingSurveyBaseForm(forms.Form):
    pass

class CriteriaPriorityForm(forms.Form):
    priority = forms.IntegerField(label="Priority", min_value=1, max_value=5)

    def __init__(self, *args, **kwargs):
        self.criteria = kwargs.pop('criteria', None)
        super().__init__(*args, **kwargs)
        if self.criteria:
            self.fields['priority'].help_text = f"Priority for {self.criteria.name}"