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
    municipality = forms.ModelChoiceField(
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
        fields = ['name', 'country', 'current_prefecture', 'municipality']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['country'].queryset = Country.objects.all().order_by('name')


# --- Form for Evaluate flow ---
# Extends the base form.
class EvaluateInfoForm(BaseUserInfoForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Đặt lại required=True cho các trường
        self.fields['current_prefecture'].required = True
        self.fields['municipality'].required = True

        # Lấy prefecture_id từ dữ liệu POST, nếu có
        prefecture_id = self.data.get('current_prefecture')
        if prefecture_id:
            try:
                # Cập nhật queryset cho municipality
                self.fields['municipality'].queryset = Municipality.objects.filter(prefecture_id=prefecture_id) # type: ignore
            except (ValueError, TypeError):
                # Xử lý trường hợp prefecture_id không hợp lệ
                pass


# --- Form for Match flow ---
# Add target fields for matching.
class MatchInfoForm(forms.ModelForm):
    target_prefecture = forms.ModelChoiceField(
        queryset=Prefecture.objects.all().order_by('name'), # type: ignore
        required=True,
        label='Prefecture you want to move in'
    )
    country = forms.ModelChoiceField(
        queryset=Country.objects.all().order_by('name'),    # type: ignore
        required=True,
        label='Country'
    )

    class Meta:
        model = UserInfo
        fields = ['name', 'country', 'target_prefecture']
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