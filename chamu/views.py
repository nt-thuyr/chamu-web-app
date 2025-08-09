from django import forms
from django.db.models import Avg
from django.forms import formset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .forms import (
    UserInfoForm, EvaluationSurveyBaseForm, MatchingSurveyBaseForm
)
from .models import (
    Criteria, UserInfo, City, Province, Nationality,
    ProvinceBaseScore, ProvinceMatchingScore, EvaluationSurvey
)

# -----------------
# Views
# -----------------
def homepage(request):
    if request.method == 'POST':
        form = UserInfoForm(request.POST)
        if form.is_valid():
            next_action = form.cleaned_data['next_action']
            user_info = form.save()  # Save the user info to the database

            if next_action == 'match':
                return redirect('matching_survey', user_info_id=user_info.id)
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

    if not criteria_list:
        return HttpResponse("No criteria available for evaluation.")

    # Dynamic form for evaluation (score 1-5)
    class EvaluationForm(forms.Form):
        score = forms.IntegerField(
            min_value=1,
            max_value=5,
            label='Điểm số',
            widget=forms.Select(choices=[(i, f'{i} sao') for i in range(1, 6)])
        )

    EvaluationSurveyFormSet = formset_factory(
        EvaluationForm,
        extra=len(criteria_list),
        can_delete=False
    )

    if request.method == 'POST':
        formset = EvaluationSurveyFormSet(request.POST)

        if formset.is_valid():
            # Use bulk_create for better performance
            evaluations = []
            for i, form in enumerate(formset):
                score = form.cleaned_data.get('score')
                if score:
                    evaluations.append(EvaluationSurvey(
                        user=user_info,
                        province=user_info.province,
                        criteria=criteria_list[i],
                        score=score,
                    ))

            if evaluations:
                EvaluationSurvey.objects.bulk_create(evaluations)
                # Update province average score after new evaluations
                update_province_avg_score(user_info.province)

            return redirect('homepage')
    else:
        formset = EvaluationSurveyFormSet()

    return render(request, 'evaluation_survey.html', {
        'formset': formset,
        'criteria_list': criteria_list,
        'user_info': user_info
    })


def matching_survey_view(request, user_info_id):
    user_info = get_object_or_404(UserInfo, id=user_info_id)
    criteria_list = Criteria.objects.all().order_by('name')

    if not criteria_list:
        return HttpResponse("No criteria available for matching.")

    # Dynamic form for matching (priority ranking)
    class MatchingForm(forms.Form):
        priority = forms.IntegerField(
            min_value=1,
            max_value=len(criteria_list),
            label='Thứ tự ưu tiên',
            widget=forms.Select(choices=[(i, f'Thứ {i}') for i in range(1, len(criteria_list) + 1)]),
            help_text='1 = Quan trọng nhất'
        )

    MatchingSurveyFormSet = formset_factory(
        MatchingForm,
        extra=len(criteria_list),
        can_delete=False
    )

    if request.method == 'POST':
        formset = MatchingSurveyFormSet(request.POST)

        if formset.is_valid():
            # Validate that all priorities are unique
            priorities = []
            for form in formset:
                priority = form.cleaned_data.get('priority')
                if priority:
                    priorities.append(priority)

            if len(set(priorities)) != len(priorities):
                return render(request, 'matching_survey.html', {
                    'formset': formset,
                    'criteria_list': criteria_list,
                    'user_info': user_info,
                    'error': 'Mỗi thứ tự ưu tiên chỉ được chọn một lần!'
                })

            # Store user preferences in session (no database save)
            user_preferences = {}
            for i, form in enumerate(formset):
                priority = form.cleaned_data.get('priority')
                if priority:
                    user_preferences[criteria_list[i].id] = {
                        'criteria_id': criteria_list[i].id,
                        'criteria_name': criteria_list[i].name,
                        'priority': priority
                    }

            # Store preferences in session
            request.session[f'preferences_{user_info_id}'] = user_preferences

            # Calculate matching scores and redirect to results
            return redirect('matching_results', user_info_id=user_info.id)
    else:
        formset = MatchingSurveyFormSet()

    return render(request, 'matching_survey.html', {
        'formset': formset,
        'criteria_list': criteria_list,
        'user_info': user_info
    })


def matching_results_view(request, user_info_id):
    user_info = get_object_or_404(UserInfo, id=user_info_id)

    # Get user preferences from session
    preferences_key = f'preferences_{user_info_id}'
    user_preferences = request.session.get(preferences_key)

    if not user_preferences:
        return redirect('matching_survey', user_info_id=user_info.id)

    # Calculate matching scores for all provinces
    matching_results = calculate_province_matching_scores(user_preferences)

    # Sort by matching score (descending)
    matching_results = sorted(matching_results, key=lambda x: x['score'], reverse=True)

    return render(request, 'matching_results.html', {
        'user_info': user_info,
        'matching_results': matching_results,
        'user_preferences': sorted(user_preferences.values(), key=lambda x: x['priority'])
    })


# -----------------
# Functions
# -----------------
def normalize_score(raw_value, min_value, max_value):
    if max_value == min_value:
        return 1  # Avoid division by zero

    score = (raw_value - min_value) / (max_value - min_value) * 4 + 1
    return max(1, min(5, round(score, 1)))


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
    """Update average scores from user evaluations"""
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


def calculate_province_matching_scores(user_preferences):
    """
    Calculate matching scores for all provinces based on user preferences
    Formula: (D1×P1 + D2×P2 + ...) / (P1 + P2 + ...)
    Where D = Data (province score), P = Preference weight
    """
    provinces = Province.objects.all()

    matching_results = []

    for province in provinces:
        total_weighted_score = 0
        total_weight = 0
        criteria_details = []

        for criteria_id, preference_data in user_preferences.items():
            # Convert priority to weight (lower priority number = higher weight)
            max_priority = len(user_preferences)
            weight = max_priority - preference_data['priority'] + 1

            # Get criteria object
            try:
                criteria = Criteria.objects.get(id=criteria_id)
            except Criteria.DoesNotExist:
                continue

            # Get province score for this criteria
            # Try to get from ProvinceMatchingScore (user evaluations) first
            try:
                province_score_obj = ProvinceMatchingScore.objects.get(
                    province=province,
                    criteria=criteria
                )
                province_score = province_score_obj.avg_score
            except ProvinceMatchingScore.DoesNotExist:
                # Fallback to base score if no user evaluations
                try:
                    base_score_obj = ProvinceBaseScore.objects.get(
                        province=province,
                        criteria=criteria
                    )
                    province_score = base_score_obj.base_score
                except ProvinceBaseScore.DoesNotExist:
                    province_score = 1.0  # Default score

            total_weighted_score += province_score * weight
            total_weight += weight

            criteria_details.append({
                'criteria_name': preference_data['criteria_name'],
                'priority': preference_data['priority'],
                'weight': weight,
                'province_score': province_score,
                'weighted_score': province_score * weight
            })

        # Calculate final matching score
        matching_score = total_weighted_score / total_weight if total_weight > 0 else 0

        matching_results.append({
            'province': province,
            'score': round(matching_score, 2),
            'criteria_details': criteria_details
        })

    return matching_results


def get_province_matching_details(request, user_info_id, province_id):
    """API endpoint to get detailed matching information for a specific province"""
    province = get_object_or_404(Province, id=province_id)

    # Get user preferences from session
    preferences_key = f'preferences_{user_info_id}'
    user_preferences = request.session.get(preferences_key)

    if not user_preferences:
        return JsonResponse({'error': 'No preferences found'}, status=400)

    details = []
    max_priority = len(user_preferences)

    for criteria_id, preference_data in user_preferences.items():
        weight = max_priority - preference_data['priority'] + 1

        # Get criteria object
        try:
            criteria = Criteria.objects.get(id=criteria_id)
        except Criteria.DoesNotExist:
            continue

        # Get province score
        try:
            province_score_obj = ProvinceMatchingScore.objects.get(
                province=province,
                criteria=criteria
            )
            province_score = province_score_obj.avg_score
            score_source = "Đánh giá của người dùng"
        except ProvinceMatchingScore.DoesNotExist:
            try:
                base_score_obj = ProvinceBaseScore.objects.get(
                    province=province,
                    criteria=criteria
                )
                province_score = base_score_obj.base_score
                score_source = "Dữ liệu cơ sở"
            except ProvinceBaseScore.DoesNotExist:
                province_score = 1.0
                score_source = "Điểm mặc định"

        details.append({
            'criteria_name': preference_data['criteria_name'],
            'priority': preference_data['priority'],
            'weight': weight,
            'province_score': province_score,
            'weighted_score': province_score * weight,
            'score_source': score_source
        })

    return JsonResponse({
        'province_name': province.name,
        'details': details
    })