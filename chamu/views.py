from django import forms
from django.db.models import Avg
from django.forms import formset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from .forms import (
    BaseUserInfoForm, MatchInfoForm, EvaluateInfoForm,
)
from .models import (
    Criteria, UserInfo, Municipality,
    MunicipalityBaseScore, MunicipalityMatchingScore, EvaluationSurvey, Prefecture, Country
)

# -----------------
# Views
# -----------------
def homepage(request):
    country_choices = BaseUserInfoForm.base_fields['country'].choices
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
        country_id = request.POST.get("country")
        prefecture_id = request.POST.get("prefecture")
        municipality_id = request.POST.get("municipality")
        errors = []
        # Kiểm tra username trùng
        if User.objects.filter(username=username).exists():
            errors.append("Username already exists.")
        # Kiểm tra mật khẩu nhập lại
        if password != password2:
            errors.append("Passwords do not match.")
        if len(password) < 6:
            errors.append("Your password must have at least 6 characters.")
        # Có thể bổ sung kiểm tra khác tại đây (vd: ký tự đặc biệt...)
        if not country_id or not prefecture_id or not municipality_id:
            errors.append("You must select country, prefecture and municipality.")

        if errors:
            return JsonResponse({"success": False, "errors": errors})
        user = User.objects.create_user(username=username, password=password)
        user.save()

        # Lưu UserInfo
        country = Country.objects.filter(id=country_id).first()
        prefecture = Prefecture.objects.filter(id=prefecture_id).first()
        municipality = Municipality.objects.filter(id=municipality_id).first()
        UserInfo.objects.create(
            user=user,
            name=username,
            country=country,
            municipality=municipality
        )
        # Đăng nhập luôn
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
        return JsonResponse({"success": True})
    return JsonResponse({"success": False, "error": "Chỉ nhận POST."})


@login_required
def ajax_update(request):
    if request.method == "POST":
        user = request.user
        new_username = request.POST.get("username", "").strip()
        new_password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")
        errors = []

        # 1. Kiểm tra đủ trường
        if not new_username or not new_password or not password2:
            errors.append("Please fill in all fields.")

        # 2. Kiểm tra username đã tồn tại (nếu thay đổi)
        if new_username != user.username:
            if User.objects.filter(username=new_username).exclude(pk=user.pk).exists():
                errors.append("Username already exists.")
            if len(new_username) < 1:
                errors.append("Username cannot be empty.")

        # 3. Kiểm tra password
        if len(new_password) < 6:
            errors.append("Your password must have at least 6 characters.")

        # 4. Kiểm tra nhập lại mật khẩu
        if new_password != password2:
            errors.append("Passwords do not match.")

        # 5. Nếu có lỗi thì trả về luôn
        if errors:
            return JsonResponse({"success": False, "errors": errors})

        # 6. Update nếu hợp lệ
        changed = False
        if new_username != user.username:
            user.username = new_username
            changed = True
        if new_password and not check_password(new_password, user.password):
            user.set_password(new_password)
            changed = True

        if changed:
            user.save()
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            return JsonResponse({"success": True, "changed": True, "username": user.username})
        else:
            return JsonResponse({"success": True, "changed": False})
    return JsonResponse({"success": False, "errors": ["Chỉ nhận POST."]})


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

def matching_survey_view(request, user_info_id, target_prefecture_id):
    user_info = get_object_or_404(UserInfo, id=user_info_id)
    criteria_list = Criteria.objects.all().order_by('name')
    ranks = range(1, len(criteria_list) + 1)

    if request.method == 'POST':
        selected_criteria = {}
        for rank in ranks:
            cid = request.POST.get(f'rank_{rank}')
            if cid:
                selected_criteria[rank] = int(cid)

        # Lưu kết quả vào session
        request.session[f'preferences_{user_info_id}'] = selected_criteria
        print(f"User info ID stored in session: {request.session.get('user_info_id')}")
        return redirect('matching_results', user_info_id=user_info.id, target_prefecture_id=target_prefecture_id)

    return render(request, 'matching_survey.html', {
        'criteria_list': criteria_list,
        'ranks': ranks,
    })

def matching_results_view(request, user_info_id, target_prefecture_id):
    user_info = get_object_or_404(UserInfo, id=user_info_id)

    preferences_key = f'preferences_{user_info_id}'
    user_preferences = request.session.get(preferences_key)

    if not user_preferences:
        return redirect('matching_survey', user_info_id=user_info.id, target_prefecture_id=target_prefecture_id)

    # Get all-criteria IDs from user preferences
    criteria_ids = user_preferences.values()
    criteria_map = {
        c.id: c.name for c in Criteria.objects.filter(id__in=criteria_ids)
    }

    matching_results = calculate_municipality_matching_scores(user_preferences, user_info.country, target_prefecture_id)
    matching_results = sorted(matching_results, key=lambda x: x['percentage'], reverse=True)

    # Sort user preferences by rank (key) (make sure keys are integers)
    sorted_user_preferences_items = sorted(user_preferences.items(), key=lambda item: int(item[0]))

    # Create template for matching_results.html
    user_preferences_for_template = []
    for rank, cid in sorted_user_preferences_items:
        user_preferences_for_template.append({
            'priority': int(rank),
            'criteria_id': int(cid),
            # Get criteria name from the map
            'criteria_name': criteria_map.get(int(cid), 'N/A')
        })

    target_prefecture = get_object_or_404(Prefecture, id=target_prefecture_id)

    return render(request, 'matching_results.html', {
        'user_info': user_info,
        'matching_results': matching_results,
        'user_preferences': user_preferences_for_template,
        'target_prefecture': target_prefecture,
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

def calculate_municipality_matching_scores(user_preferences, country, target_prefecture_id):
    """
    Calculate matching scores for municipalities based on user preferences.
    Optimizes by reducing database queries and using in-memory calculations.
    """

    # 1. Prepare input data and user preferences
    # user_preferences format: { '1': 5, '2': 3, ... }

    # Get all criteria and store them in a map for quick access
    criteria_ids = user_preferences.values()
    criteria_map = {c.id: c for c in Criteria.objects.filter(id__in=criteria_ids)}

    prefecture_municipalities = Municipality.objects.filter(prefecture_id=target_prefecture_id)
    # 2. Get scores from the database
    base_scores_qs = MunicipalityBaseScore.objects.filter(
        criteria__id__in=criteria_ids,
        municipality__in=prefecture_municipalities,
        country=country
    )
    base_scores_map = {
        (score.municipality_id, score.criteria_id): score.base_score
        for score in base_scores_qs
    }

    matching_scores_qs = MunicipalityMatchingScore.objects.filter(
        criteria__id__in=criteria_ids,
        municipality__in=prefecture_municipalities,
        country=country
    )
    matching_scores_map = {
        (score.municipality_id, score.criteria_id): score.final_score
        for score in matching_scores_qs
    }

    # 3. Get all municipalities and prefetch related data
    municipalities = prefecture_municipalities.order_by('name')

    # 4.Calculate matching scores
    matching_results = []
    max_priority = len(user_preferences) + 1

    for municipality in municipalities:
        total_weighted_score = 0
        total_weight = 0
        criteria_details = []

        # Loop through user preferences
        for rank_str, criteria_id in user_preferences.items():
            rank = int(rank_str)
            weight = max_priority - rank

            criteria = criteria_map.get(criteria_id)
            if not criteria:
                continue

            # Calculate using final scores if available, otherwise use base scores
            score_tuple = (municipality.id, criteria.id)
            municipality_score = matching_scores_map.get(score_tuple)
            if municipality_score is None:
                municipality_score = base_scores_map.get(score_tuple, 1.0)

            total_weighted_score += municipality_score * weight
            total_weight += weight

            criteria_details.append({
                'criteria_name': criteria.name,
                'priority': rank,
                'weight': weight,
                'municipality_score': municipality_score,
                'weighted_score': municipality_score * weight
            })

        # Calculate mismatching score and percentage
        matching_score = total_weighted_score / total_weight if total_weight > 0 else 0
        matching_percentage = calculate_matching_percentage(matching_score)

        matching_results.append({
            'municipality': municipality,
            'score': round(matching_score, 2),
            'percentage': matching_percentage,
            'criteria_details': criteria_details
        })

    return matching_results

def calculate_matching_percentage(score):
    min_score = 1.0  # Minimum score
    max_score = 5.0

    # Calculate percentage based on the score range
    percentage = (max_score - score) / (max_score - min_score) * 100
    return round(percentage, 2)


#-----------TEST VIEWS FOR INFO SURVEY-----------------
def match_info_view(request):
    if request.method == 'POST':
        form = MatchInfoForm(request.POST)
        if form.is_valid():
            # Save user info and target prefecture
            user_info = form.save()
            target_prefecture = form.cleaned_data['target_prefecture']
            # Save user info to session
            request.session['user_info_id'] = user_info.id
            # Pass parameters to the matching survey
            return redirect('matching_survey', user_info_id=user_info.id, target_prefecture_id=target_prefecture.id)
        else:
            return render(request, 'match_info.html', {'form': form})
    else:
        form = MatchInfoForm()
    return render(request, 'match_info.html', {'form': form})


def evaluate_info_view(request):
    if request.method == 'POST':
        form = EvaluateInfoForm(request.POST)
        if form.is_valid():
            user_info = form.save()
            # Redirect to the evaluation survey with user_info_id
            return redirect('evaluation_survey', user_info_id=user_info.id)
        else:
            return render(request, 'evaluate_info.html', {'form': form})
    else:
        form = EvaluateInfoForm()
    return render(request, 'evaluate_info.html', {'form': form})


def municipality_details_view(request, municipality_id):
    # Get the municipality by ID
    municipality = get_object_or_404(Municipality, id=municipality_id)

    # Get the prefecture and user info ID from session
    prefecture = municipality.prefecture
    user_info_id = request.session.get('user_info_id')
    # If user_info_id is not set, redirect to match_info
    if not user_info_id:
        return redirect('match_info')

    return render(request, 'municipality_details.html', {
        'municipality': municipality,
        'prefecture': prefecture,
        'user_info_id': user_info_id
    })

def get_municipalities(request):
    prefecture_id = request.GET.get('prefecture_id')
    if not prefecture_id:
        return JsonResponse([], safe=False)

    try:
        prefecture = get_object_or_404(Prefecture, id=prefecture_id)
        municipalities = Municipality.objects.filter(prefecture=prefecture).values('id', 'name')
        return JsonResponse(list(municipalities), safe=False)
    except (ValueError, TypeError):
        return JsonResponse([], safe=False)
def get_prefectures(request):
    prefectures = Prefecture.objects.all().values('id', 'name')
    return JsonResponse(list(prefectures), safe=False)