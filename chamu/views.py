from django import forms
from django.db.models import Avg
from django.forms import formset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .forms import (
    UserInfoForm, EvaluationSurveyBaseForm
)
from .models import (Criteria, UserInfo, City, Province, Nationality, ProvinceBaseScore, ProvinceMatchingScore, EvaluationSurvey
)


# -----------------
# Views
# -----------------
def homepage(request):
    if request.method == 'POST':
        form = UserInfoForm(request.POST)
        if form.is_valid():
            next_action = form.cleaned_data['next_action']
            user_info = form.save()  # Lưu thông tin người dùng ngay

            if next_action == 'match':
                return redirect('matching_survey')
            elif next_action == 'evaluate':
                return redirect('evaluation_survey', user_info_id=user_info.id)
            else:
                return HttpResponse("Invalid choice.")
    else:
        form = UserInfoForm()
    return render(request, 'homepage.html', {'form': form})


def evaluation_survey_view(request, user_info_id):
    user_info = get_object_or_404(UserInfo, id=user_info_id)
    criteria_list = Criteria.objects.all()

    # Tạo formset động để thêm trường 'score' cho mỗi form
    def get_evaluation_survey_formset():
        fields = {}
        for criteria in criteria_list:
            fields[f'score_{criteria.slug}'] = forms.IntegerField(
                min_value=1, max_value=5, label=criteria.name
            )
        return type('DynamicEvaluationSurveyForm', (forms.Form,), fields)

    DynamicEvaluationSurveyForm = get_evaluation_survey_formset()
    EvaluationSurveyFormSet = formset_factory(DynamicEvaluationSurveyForm, extra=0)

    if request.method == 'POST':
        formset = EvaluationSurveyFormSet(request.POST)
        if formset.is_valid():
            for i, form in enumerate(formset):
                criteria = criteria_list[i]
                score = form.cleaned_data.get(f'score_{criteria.slug}')

                # Lưu vào database
                EvaluationSurvey.objects.create(
                    user=user_info,
                    province=user_info.province,
                    criteria=criteria,
                    score=score,
                )
            # Sau khi lưu xong, cập nhật điểm trung bình của tỉnh
            # update_province_avg_score(user_info.province)
            return redirect('homepage')
    else:
        formset = EvaluationSurveyFormSet()

    return render(request, 'evaluation_survey.html', {'formset': formset, 'criteria_list': criteria_list})


# -----------------
# Functions
# -----------------
def normalize_score(raw_value, min_value, max_value):
    score = (raw_value - min_value) / (max_value - min_value) * 4 + 1
    return max(1, min(5, round(score)))


def update_province_base_score(province, criteria, raw_data):
    min_value = 0
    max_value = 10
    normalized_score = normalize_score(raw_data, min_value, max_value)
    ProvinceBaseScore.objects.update_or_create(
        province=province,
        criteria=criteria,
        defaults={'base_score': normalized_score}
    )


def update_province_avg_score(province):
    # Lấy tất cả các tiêu chí để tính điểm
    criteria_list = Criteria.objects.all()
    for criteria in criteria_list:
        avg_score = EvaluationSurvey.objects.filter(
            province=province, criteria=criteria
        ).aggregate(Avg('score'))['score__avg'] or 0.0

        ProvinceMatchingScore.objects.update_or_create(
            province=province,
            criteria=criteria,
            defaults={'avg_score': avg_score}
        )