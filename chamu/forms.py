from django import forms
from .models import UserInfo, Prefecture, Municipality, Country

# --- Base form ---
# This form stores all basic user information.
class BaseUserInfoForm(forms.ModelForm):
    # These fields are common for both Evaluate and Match forms.
    current_prefecture = forms.ModelChoiceField(
        queryset=Prefecture.objects.all().order_by('name'), # type: ignore
        required=False,
        label='Prefecture you currently live in'
    )
    current_municipality = forms.ModelChoiceField(
        queryset=Municipality.objects.none(),
        required=False,
        label='Municipality you currently live in'
    )
    country = forms.ModelChoiceField(
        queryset=Country.objects.all().order_by('name'),    # type: ignore
        required=True,
        label='Country'
    )

    class Meta:
        model = UserInfo
        fields = ['name', 'country', 'current_prefecture', 'current_municipality']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['country'].queryset = Country.objects.all().order_by('name')


# --- Form for Evaluate flow ---
# Extends the base form.
class EvaluateInfoForm(BaseUserInfoForm):
    class EvaluateInfoForm(BaseUserInfoForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Set required fields for evaluation
            self.fields['current_prefecture'].required = True
            self.fields['current_municipality'].required = True


# --- Form for Match flow ---
# Add target fields for matching.
class MatchInfoForm(forms.ModelForm):
    target_prefecture = forms.ModelChoiceField(
        queryset=Prefecture.objects.all().order_by('name'), # type: ignore
        required=True,
        label='Prefecture you want to move in'
    )
    target_municipality = forms.ModelChoiceField(
        queryset=Municipality.objects.none(),
        required=True,
        label='Municipality you want to move in'
    )
    country = forms.ModelChoiceField(
        queryset=Country.objects.all().order_by('name'),    # type: ignore
        required=True,
        label='Country'
    )

    class Meta:
        model = UserInfo
        fields = ['name', 'country', 'target_prefecture', 'target_municipality']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['country'].queryset = Country.objects.all().order_by('name')

# --- Other base form ---
class EvaluationSurveyBaseForm(forms.Form):
    pass

class MatchingSurveyBaseForm(forms.Form):
    pass