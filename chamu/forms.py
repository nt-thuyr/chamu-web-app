from django import forms
from .models import UserInfo, EvaluationSurvey, City


# --- UserInfoForm ---
# Định nghĩa các lựa chọn cho form
NATIONALITY_CHOICES = [
    ('vietnam', 'Vietnam'),
    ('america', 'America'),
    ('korea', 'Korea'),
    ('other', 'Other'),
]
class UserInfoForm(forms.ModelForm):
    # next_action không lưu vào model, nên được định nghĩa bên ngoài Meta
    next_action = forms.ChoiceField(
        label='What would you like to do next?',
        choices=[
            ('match', 'I want to find a more suitable place to live'),
            ('evaluate', 'I want to contribute by evaluating my current city'),
        ],
        widget=forms.RadioSelect,
        required=True,
    )

    class Meta:
        model = UserInfo
        fields = ['name', 'nationality', 'city']

        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Your name'}),
            'birthday': forms.DateInput(attrs={'type': 'date', 'id': 'birthday'}),
            'nationality': forms.Select(choices=NATIONALITY_CHOICES),
            # Trường city sẽ là ModelChoiceField, tự động tạo các lựa chọn từ model City
            'city': forms.Select(),
        }

        labels = {
            'name': 'Name',
            'birthday': 'Birthday',
            'nationality': 'Nationality',
            'city': 'Current Residence in Japan'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tùy chỉnh các lựa chọn cho trường city
        self.fields['city'].queryset = City.objects.all()
        self.fields['city'].widget.choices = [('', '--Select city--')] + list(self.fields['city'].choices)[1:]



# --- EvaluationSurveyForm ---
# Các lựa chọn cho các trường RadioSelect
RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
class EvaluationSurveyForm(forms.ModelForm):
    class Meta:
        model = EvaluationSurvey
        fields = [
            'cost_of_living_score',
            'local_shops_score',
            'temperature_score',
            'crime_rate_score',
        ]

        widgets = {
            'cost_of_living_score': forms.RadioSelect(choices=RATING_CHOICES),
            'local_shops_score': forms.RadioSelect(choices=RATING_CHOICES),
            'temperature_score': forms.RadioSelect(choices=RATING_CHOICES),
            'crime_rate_score': forms.RadioSelect(choices=RATING_CHOICES),
            'population_score': forms.RadioSelect(choices=RATING_CHOICES),
        }

        labels = {
            'cost_of_living_score': '1: Cheap — 5: Expensive',
            'local_shops_score': '1: Few local shops — 5: Many local shops',
            'temperature_score': '1: Cool temperature — 5: Hot temperature',
            'crime_rate_score': '1: Low crime rate — 5: High crime rate',
            'population_score': '1: Quiet — 5: Crowded',
        }

class MatchingSurveyForm(forms.Form):
    # Các lựa chọn cho RadioSelect
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    # Các trường sở thích của người dùng
    cost_of_living_score = forms.ChoiceField(
        label='1: Cheap — 5: Expensive',
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        required=True
    )
    local_shops_score = forms.ChoiceField(
        label='1: Few local shops — 5: Many local shops',
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        required=True
    )
    temperature_score = forms.ChoiceField(
        label='1: Cool temperature — 5: Hot temperature',
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        required=True
    )
    crime_rate_score = forms.ChoiceField(
        label='1: Safe — 5: Not safe',
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        required=True
    )
    population_score = forms.ChoiceField(
        label='1: Quiet — 5: Crowded',
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        required=True
    )