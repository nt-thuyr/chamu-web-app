from django import forms
from .models import (
    UserInfo,
    EvaluationSurvey,
)

class UserInfoForm(forms.ModelForm):
    NATIONALITY_CHOICES = [
        ('vietnam', 'Vietnam'),
        ('america', 'America'),
        ('korea', 'Korea'),
        ('other', 'Other'),
    ]

    RESIDENCE_CHOICES = [
        ('', '--Select city--'),
        ('tokyo', 'Tokyo'),
        ('osaka', 'Osaka'),
        ('kyoto', 'Kyoto'),
        ('sapporo', 'Sapporo'),
        ('fukuoka', 'Fukuoka'),
        ('other', 'Other'),
    ]

    name = forms.CharField(
        label='Name',
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Your name'})
    )

    birthday = forms.DateField(
        label='Birthday',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'id': 'birthday'})
    )

    nationality = forms.ChoiceField(
        label='Nationality',
        required=True,
        choices=NATIONALITY_CHOICES
    )

    current_residence = forms.ChoiceField(
        label='Current Residence in Japan',
        required=True,
        choices=RESIDENCE_CHOICES
    )

    class Meta:
        model = UserInfo
        fields = ['name', 'birthday', 'nationality', 'current_residence']

    # Thêm radio buttons (không lưu trong model)
    next_action = forms.ChoiceField(
        label='What would you like to do next?',
        choices=[
            ('match', 'I want to find a more suitable place to live'),
            ('evaluate', 'I want to contribute by evaluating my current city'),
        ],
        widget=forms.RadioSelect,
        required=True,
    )

class EvaluationSurveyForm(forms.ModelForm):
    class Meta:
        model = EvaluationSurvey
        fields = [
            'cheap_expensive',
            'quiet_crowded',
            'lowcrime_highcrime',
            'fewshops_manyshops',
            'cool_hot',
        ]
        labels = {
            'cheap_expensive': '1: Cheap — 5: Expensive',
            'quiet_crowded': '1: Quiet — 5: Crowded',
            'lowcrime_highcrime': '1: Low crime rate — 5: High crime rate',
            'fewshops_manyshops': '1: Few local shops — 5: Many local shops',
            'cool_hot': '1: Cool temperature — 5: Hot temperature',
        }
        widgets = {
            field: forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)])
            for field in fields
        }