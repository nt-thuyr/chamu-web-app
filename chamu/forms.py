from django import forms
from .models import UserInfo, EvaluationSurvey, City, Province, Nationality

class UserInfoForm(forms.ModelForm):
    # Field này để người dùng chọn hành động tiếp theo
    ACTION_CHOICES = [
        ('match', 'Tìm thành phố phù hợp'),
        ('evaluate', 'Đánh giá thành phố')
    ]
    next_action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect,
        initial='match',
        label="Bạn muốn làm gì?"
    )

    class Meta:
        model = UserInfo
        # Các trường cần nhập cho người dùng
        fields = ['name', 'nationality', 'province']
        labels = {
            'name': 'Tên của bạn',
            'nationality': 'Quốc tịch',
            'province': 'Tỉnh/Thành phố hiện tại (nếu có)'
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

