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
    MunicipalityBaseScore, MunicipalityMatchingScore, EvaluationSurvey, Prefecture
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

        # Lưu kết quả vào session
        request.session[f'preferences_{user_info_id}'] = selected_criteria
        return redirect('matching_results', user_info_id=user_info.id)

    return render(request, 'matching_survey.html', {
        'criteria_list': criteria_list,
        'ranks': ranks,
    })

def matching_results_view(request, user_info_id):
    user_info = get_object_or_404(UserInfo, id=user_info_id)

    preferences_key = f'preferences_{user_info_id}'
    user_preferences = request.session.get(preferences_key)

    if not user_preferences:
        return redirect('matching_survey', user_info_id=user_info.id)

    # Get all-criteria IDs from user preferences
    criteria_ids = user_preferences.values()
    criteria_map = {
        c.id: c.name for c in Criteria.objects.filter(id__in=criteria_ids)
    }

    matching_results = calculate_municipality_matching_scores(user_preferences, user_info.country)
    matching_results = sorted(matching_results, key=lambda x: x['score'])

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

    return render(request, 'matching_results.html', {
        'user_info': user_info,
        'matching_results': matching_results,
        'user_preferences': user_preferences_for_template,
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
    Tính điểm khớp lệnh cho tất cả các đô thị dựa trên ưu tiên của người dùng.
    Phiên bản này được tối ưu hóa hiệu suất bằng cách truy vấn dữ liệu hàng loạt.
    """

    # 1. Chuẩn bị dữ liệu đầu vào và các tham số
    # user_preferences có định dạng { '1': 5, '2': 3, ... }

    # Lấy danh sách ID các tiêu chí người dùng đã chọn
    criteria_ids = user_preferences.values()

    # Lấy tất cả các tiêu chí đã chọn trong một truy vấn và lưu vào một dictionary
    criteria_map = {c.id: c for c in Criteria.objects.filter(id__in=criteria_ids)}

    # 2. Lấy tất cả điểm số cần thiết trong một vài truy vấn lớn
    base_scores_qs = MunicipalityBaseScore.objects.filter(
        criteria__id__in=criteria_ids,
        country=country
    )
    base_scores_map = {
        (score.municipality_id, score.criteria_id): score.base_score
        for score in base_scores_qs
    }

    matching_scores_qs = MunicipalityMatchingScore.objects.filter(
        criteria__id__in=criteria_ids,
        country=country
    )
    matching_scores_map = {
        (score.municipality_id, score.criteria_id): score.final_score
        for score in matching_scores_qs
    }

    # 3. Lấy tất cả các đô thị và prefetch các điểm số liên quan
    municipalities = Municipality.objects.all().order_by('name')

    # 4. Tính toán điểm số trong bộ nhớ
    matching_results = []
    max_priority = len(user_preferences) + 1

    for municipality in municipalities:
        total_weighted_score = 0
        total_weight = 0
        criteria_details = []

        # Lặp qua các ưu tiên của người dùng
        for rank_str, criteria_id in user_preferences.items():
            rank = int(rank_str)
            weight = max_priority - rank

            # Lấy đối tượng tiêu chí từ map đã tạo
            criteria = criteria_map.get(criteria_id)
            if not criteria:
                continue

            # Lấy điểm số từ map đã tạo, rất nhanh
            # Ưu tiên matching score, nếu không có thì dùng base score
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


#-----------TEST VIEWS FOR INFO SURVEY-----------------
def match_info_view(request):
    if request.method == 'POST':
        form = MatchInfoForm(request.POST)
        if form.is_valid():
            # Lấy đối tượng Prefecture từ form
            target_prefecture = form.cleaned_data['target_prefecture']

            # Ghi lại UserInfo
            user_info = form.save(commit=False)
            user_info.save()

            # TODO: Xử lý với đối tượng target_prefecture ở đây
            # Ví dụ: truyền nó vào một session hoặc redirect đến trang khảo sát
            print(f"Target prefecture đã được chọn: {target_prefecture.name}")

            return redirect('matching_survey', user_info_id=user_info.id)
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
            # Chuyển hướng đến survey của evaluate
            return redirect('evaluation_survey', user_info_id=user_info.id)
        else:
            return render(request, 'evaluate_info.html', {'form': form})
    else:
        form = EvaluateInfoForm()
    return render(request, 'evaluate_info.html', {'form': form})


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