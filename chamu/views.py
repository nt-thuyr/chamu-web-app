from django import forms
from django.db.models import Avg
from django.forms import formset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from .forms import (
    UserInfoForm,
)
from .models import (
    Criteria, UserInfo, Municipality,
    MunicipalityBaseScore, MunicipalityMatchingScore, EvaluationSurvey
)

# -----------------
# Views
# -----------------
def homepage(request):
    country_choices = UserInfoForm.base_fields['country'].choices
    municipality_choices = Municipality.objects.all()
    userinfo = None
    if request.user.is_authenticated:
        try:
            userinfo = UserInfo.objects.get(user=request.user)
        except UserInfo.DoesNotExist:
            userinfo = None
    context = {
        'country_choices': country_choices,
        'municipality_choices': municipality_choices,
        'userinfo': userinfo,
    }
    return render(request, "homepage.html", context)

def ajax_login(request):
    if request.method == "POST":
            username = request.POST.get("username")
            password = request.POST.get("password")
             # Xác thực người dùng
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return JsonResponse({"success": True})
            else:
                return JsonResponse({"success": False, "error": "Tên đăng nhập hoặc mật khẩu không đúng."})
    return JsonResponse({"success": False, "error": "Chỉ nhận POST."})

def ajax_logout(request):
    if request.user.is_authenticated:
        logout(request)
    return JsonResponse({"success": True})

def ajax_signup(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        password2 = request.POST.get("password2")
        # Kiểm tra username trùng
        if User.objects.filter(username=username).exists():
            return JsonResponse({"success": False, "error": "Tên đăng nhập đã tồn tại."})
        # Kiểm tra mật khẩu nhập lại
        if password != password2:
            return JsonResponse({"success": False, "error": "Mật khẩu nhập lại không khớp."})
        # Kiểm tra độ dài mật khẩu
        if len(password) < 6:
            return JsonResponse({"success": False, "error": "Mật khẩu phải có ít nhất 6 ký tự."})
        # Có thể bổ sung kiểm tra khác tại đây (vd: ký tự đặc biệt...)

        user = User.objects.create_user(username=username, password=password)
        user.save()
        # Đăng nhập luôn
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
        return JsonResponse({"success": True})
    return JsonResponse({"success": False, "error": "Chỉ nhận POST."})

@login_required
def ajax_update(request):
    if request.method == "POST":
        current_password = request.POST.get("current_password")
        new_username = request.POST.get("username")
        new_password = request.POST.get("password")

        user = authenticate(request, username=request.user.username, password=current_password)
        if not user:
            return JsonResponse({"success": False, "error": "Current password is incorrect"})

        if new_username:
            user.username = new_username
        if new_password:
            user.set_password(new_password)
        user.save()

        # Login lại nếu đổi password
        if new_password:
            user = authenticate(request, username=user.username, password=new_password)
            if user:
                login(request, user)

        return JsonResponse({"success": True, "username": user.username})
    return None


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
            label='Score',
            widget=forms.Select(choices=[(i, f'{i} star(s)') for i in range(1, 6)])
        )

    evaluation_survey_form_set = formset_factory(
        EvaluationForm,
        extra=len(criteria_list),
        can_delete=False
    )

    if request.method == 'POST':
        print("POST data:", request.POST)
        formset = evaluation_survey_form_set(request.POST)
        print("Formset valid?", formset.is_valid())
        print("Formset errors:", formset.errors)
        formset = evaluation_survey_form_set(request.POST)
        print(user_info.country)

        if formset.is_valid():
            # Use bulk_create for better performance
            evaluations = []
            for i, form in enumerate(formset):
                score = form.cleaned_data.get('score')
                if score:
                    evaluations.append(EvaluationSurvey(
                        user=user_info,
                        municipality=user_info.municipality,
                        criteria=criteria_list[i],
                        score=score,
                    ))

            if evaluations:
                EvaluationSurvey.objects.bulk_create(evaluations)
                # Update municipality average score after new evaluations
                update_municipality_avg_score(user_info.municipality, user_info.country)

            return redirect('homepage')
    else:
        formset = evaluation_survey_form_set()

    # Zip formset with criteria for rendering
    form_criteria = zip(formset.forms, criteria_list)

    return render(request, 'evaluation_survey.html', {
        'formset': formset,
        'criteria_list': criteria_list,
        'form_criteria': form_criteria,
        'user_info': user_info
    })

def matching_survey_view(request, user_info_id):
    user_info = get_object_or_404(UserInfo, id=user_info_id)
    criteria_list = Criteria.objects.all().order_by('name')
    ranks = range(1, len(criteria_list) + 1)

    if request.method == 'POST':
        selected_criteria = {}
        for rank in ranks:
            cid = request.POST.get(f'rank_{rank}')
            if cid:
                selected_criteria[rank] = int(cid)

        # Kiểm tra nếu người dùng đã chọn một tiêu chí nhiều lần
        if len(set(selected_criteria.values())) != len(selected_criteria.values()):
            return render(request, 'matching_survey.html', {
                'criteria_list': criteria_list,
                'ranks': ranks,
                'error': 'Mỗi tiêu chí chỉ được chọn một lần.'
            })

        # Lưu kết quả vào session
        request.session[f'preferences_{user_info_id}'] = selected_criteria
        return redirect('matching_results', user_info_id=user_info.id)

    return render(request, 'matching_survey.html', {
        'criteria_list': criteria_list,
        'ranks': ranks,
    })

def matching_results_view(request, user_info_id):
    user_info = get_object_or_404(UserInfo, id=user_info_id)

    # Get user preferences from session
    preferences_key = f'preferences_{user_info_id}'
    user_preferences = request.session.get(preferences_key)

    if not user_preferences:
        return redirect('matching_survey', user_info_id=user_info.id)

    # Calculate matching scores for all municipalities
    matching_results = calculate_municipality_matching_scores(user_preferences, user_info.country)

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
def update_municipality_avg_score(municipality, country):
    """Update average scores from user evaluations"""
    criteria_list = Criteria.objects.all()
    for criteria in criteria_list:
        avg_score = EvaluationSurvey.objects.filter(
            municipality=municipality, criteria=criteria
        ).aggregate(Avg('score'))['score__avg'] or 0.0

        MunicipalityMatchingScore.objects.update_or_create(
            municipality=municipality,
            criteria=criteria,
            country=country,
            defaults={'avg_score': avg_score}
        )
    # Update final scores after recalculating averages
    update_municipality_final_score(municipality, country)

def update_municipality_final_score(municipality, country):
    criteria_list = Criteria.objects.all()
    for criteria in criteria_list:
        try:
            base_score_obj = MunicipalityBaseScore.objects.get(municipality=municipality, criteria=criteria, country=country)
            base_score = base_score_obj.base_score
        except MunicipalityBaseScore.DoesNotExist:
            base_score = 1.0

        try:
            avg_score_obj = MunicipalityMatchingScore.objects.get(municipality=municipality, criteria=criteria, country=country)
            avg_score = avg_score_obj.avg_score
        except MunicipalityMatchingScore.DoesNotExist:
            avg_score = None

        if avg_score is not None:
            final_score = base_score * 0.6 + avg_score * 0.4
        else:
            final_score = base_score

        MunicipalityMatchingScore.objects.update_or_create(
            municipality=municipality,
            criteria=criteria,
            country=country,
            defaults={'final_score': final_score}
        )

def calculate_municipality_matching_scores(user_preferences, country):
    """
    Calculate matching scores for all municipalities based on user preferences
    Formula: (D1×P1 + D2×P2 + ...) / (P1 + P2 + ...)
    Where D = Data (municipality score), P = Preference weight
    """
    municipalities = Municipality.objects.all()

    matching_results = []

    for municipality in municipalities:
        total_weighted_score = 0
        total_weight = 0
        criteria_details = []

        for criteria_id, preference_data in user_preferences.items():
            # Convert priority to weight (lower priority number = higher weight)
            max_priority = len(user_preferences) + 1
            weight = max_priority - preference_data['priority']

            # Get criteria object
            try:
                criteria = Criteria.objects.get(id=criteria_id)
            except Criteria.DoesNotExist:
                continue

            # Get municipality score for this criteria
            # Try to get from MunicipalityMatchingScore (user evaluations) first
            try:
                municipality_score_obj = MunicipalityMatchingScore.objects.get(
                    municipality=municipality,
                    criteria=criteria,
                    country=country,
                )
                municipality_score = municipality_score_obj.final_score
            except MunicipalityMatchingScore.DoesNotExist:
                # Fallback to base score if no user evaluations
                try:
                    base_score_obj = MunicipalityBaseScore.objects.get(
                        municipality=municipality,
                        criteria=criteria,
                        country=country,
                    )
                    municipality_score = base_score_obj.base_score
                except MunicipalityBaseScore.DoesNotExist:
                    municipality_score = 1.0  # Default score

            total_weighted_score += municipality_score * weight
            total_weight += weight

            criteria_details.append({
                'criteria_name': preference_data['criteria_name'],
                'priority': preference_data['priority'],
                'weight': weight,
                'municipality_score': municipality_score,
                'weighted_score': municipality_score * weight
            })

        # Calculate final matching score
        matching_score = total_weighted_score / total_weight if total_weight > 0 else 0

        matching_results.append({
            'municipality': municipality,
            'score': round(matching_score, 2),
            'criteria_details': criteria_details
        })

    return matching_results


def get_municipality_matching_details(request, user_info_id, municipality_id):
    """API endpoint to get detailed matching information for a specific municipality"""
    municipality = get_object_or_404(Municipality, id=municipality_id)

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

        # Get municipality score
        try:
            municipality_score_obj = MunicipalityMatchingScore.objects.get(
                municipality=municipality,
                criteria=criteria
            )
            municipality_score = municipality_score_obj.avg_score
            score_source = "Đánh giá của người dùng"
        except MunicipalityMatchingScore.DoesNotExist:
            try:
                base_score_obj = MunicipalityBaseScore.objects.get(
                    municipality=municipality,
                    criteria=criteria
                )
                municipality_score = base_score_obj.base_score
                score_source = "Dữ liệu cơ sở"
            except MunicipalityBaseScore.DoesNotExist:
                municipality_score = 1.0
                score_source = "Điểm mặc định"

        details.append({
            'criteria_name': preference_data['criteria_name'],
            'priority': preference_data['priority'],
            'weight': weight,
            'municipality_score': municipality_score,
            'weighted_score': municipality_score * weight,
            'score_source': score_source
        })

    return JsonResponse({
        'municipality_name': municipality.name,
        'details': details
    })