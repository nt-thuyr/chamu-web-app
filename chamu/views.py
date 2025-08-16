import requests
from django import forms
from django.db.models import Avg
from django.forms import formset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
import wikipedia, folium, geopy, geopy.distance, re
from django.views.decorators.http import require_GET

from .forms import (
    BaseUserInfoForm, MatchInfoForm, EvaluateInfoForm,
)
from .models import (
    Criteria, UserInfo, Municipality,
    MunicipalityScore, EvaluationSurvey, Prefecture
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

def about_view(request):
    """About page view"""
    return render(request, 'about.html')


# ----------------- LUỒNG 1: MATCHING SURVEY -----------------
def match_info_view(request):
    user_info = None
    # Lấy ID từ session thay vì đối tượng
    user_info_id = request.session.get('user_info_id')

    if user_info_id:
        try:
            # Truy vấn cơ sở dữ liệu để lấy đối tượng UserInfo
            user_info = UserInfo.objects.get(id=user_info_id)
        except UserInfo.DoesNotExist:
            del request.session['user_info_id']

    if request.method == 'POST':
        form = MatchInfoForm(request.POST, instance=user_info)
        if form.is_valid():
            new_user_info = form.save()
            # Lưu ID của đối tượng vào session
            request.session['user_info_id'] = new_user_info.id

            target_prefecture = form.cleaned_data['target_prefecture']
            return redirect('matching_survey', user_info_id=new_user_info.id,
                            target_prefecture_id=target_prefecture.id)
    else:
        # Tự động điền form với dữ liệu từ user_info đã có
        initial_data = {}
        if user_info:
            initial_data['name'] = user_info.name
            if user_info.country:
                initial_data['country'] = user_info.country.id

        form = MatchInfoForm(instance=user_info, initial=initial_data)

    return render(request, 'match_info.html', {'form': form})

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

    target_prefecture = get_object_or_404(Prefecture, id=target_prefecture_id)

    return render(request, 'matching_results.html', {
        'user_info': user_info,
        'matching_results': matching_results,
        'user_preferences': user_preferences_for_template,
        'target_prefecture': target_prefecture,
    })

def municipality_details_view(request, municipality_id, user_info_id=None):
    municipality = get_object_or_404(Municipality, id=municipality_id)
    prefecture = municipality.prefecture

    # Handle the back button logic from the previous conversation
    # If user_info_id is passed, use it. Otherwise, try to get from session.
    if not user_info_id:
        user_info_id = request.session.get('user_info_id')
        if not user_info_id:
            return redirect('match_info')

    try:
        user_info = UserInfo.objects.get(id=user_info_id)
        country = user_info.country
    except UserInfo.DoesNotExist:
        return redirect('match_info')

    # Fetch user preferences from the session to calculate scores
    preferences_key = f'preferences_{user_info_id}'
    user_preferences = request.session.get(preferences_key, {})

    criteria_details = []
    if user_preferences:
        # Fetch scores for this municipality and the user's criteria
        criteria_ids = [int(cid) for cid in user_preferences.values()]

        scores = MunicipalityScore.objects.filter(
            municipality=municipality,
            criteria__id__in=criteria_ids,
            country=country
        ).select_related('criteria')

        # Iterate through preferences to build the details list
        scores_map = {s.criteria_id: s for s in scores}
        criteria_map = {c.id: c.name for c in Criteria.objects.filter(id__in=criteria_ids)}

        for rank_str, criteria_id in user_preferences.items():
            rank = int(rank_str)
            score_obj = scores_map.get(criteria_id)
            if score_obj:
                display_score = score_obj.final_score if score_obj.final_score and score_obj.final_score != 0 else score_obj.base_score
                criteria_details.append({
                    'criteria_name': criteria_map.get(criteria_id, 'N/A'),
                    'priority': rank,
                    'municipality_score': display_score,
                })

    description, image_url, wiki_url = get_municipality_info_from_wiki(municipality.name, prefecture.name)

    # Create map by folium when there is coordinates
    municipality_map = None
    if municipality.latitude and municipality.longitude:
        map_center = [float(municipality.latitude), float(municipality.longitude)]
        m = folium.Map(location=map_center, zoom_start=12)
        folium.Marker(map_center, tooltip=municipality.name).add_to(m)
        municipality_map = m._repr_html_()

    return render(request, 'municipality_details.html', {
        'municipality': municipality,
        'prefecture': prefecture,
        'user_info_id': user_info_id,
        'criteria_details': criteria_details,
        'municipality_description': description,  # Placeholder description
        'image_url': image_url,  # Placeholder image URL
        'wiki_url': wiki_url,  # Placeholder Wikipedia URL
        'municipality_map': municipality_map,  # Folium map HTML
    })


# ----------------- LUỒNG 2: EVALUATION SURVEY -----------------
def evaluate_info_view(request):
    user_info = None
    # Lấy ID từ session thay vì đối tượng
    user_info_id = request.session.get('user_info_id')

    if user_info_id:
        try:
            # Truy vấn cơ sở dữ liệu để lấy đối tượng UserInfo
            user_info = UserInfo.objects.get(id=user_info_id)
        except UserInfo.DoesNotExist:
            del request.session['user_info_id']

    if request.method == 'POST':
        form = EvaluateInfoForm(request.POST, instance=user_info)
        if form.is_valid():
            new_user_info = form.save()
            # Lưu ID của đối tượng vào session
            request.session['user_info_id'] = new_user_info.id
            return redirect('evaluation_survey', user_info_id=new_user_info.id)
    else:
        # Tự động điền form với dữ liệu từ user_info đã có
        initial_data = {}
        if user_info:
            initial_data['name'] = user_info.name
            if user_info.country:
                initial_data['country'] = user_info.country.id

        form = EvaluateInfoForm(instance=user_info, initial=initial_data)

    return render(request, 'evaluate_info.html', {'form': form})

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

        if formset.is_valid():
            EvaluationSurvey.objects.filter(
                user=user_info,
                municipality=user_info.municipality
            ).delete()
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
                update_municipality_score(user_info.municipality, user_info.country)

            return redirect('thank_you', user_info_id=user_info.id)
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


def thank_you_view(request, user_info_id):
    """Trang cảm ơn sau khi làm khảo sát đánh giá."""
    user_info = get_object_or_404(UserInfo, id=user_info_id)
    municipality = user_info.municipality
    prefecture = municipality.prefecture

    # Lấy điểm đánh giá của người dùng
    user_evaluations = EvaluationSurvey.objects.filter(
        user=user_info,
        municipality=municipality
    ).order_by('criteria__name').select_related('criteria')

    # Lấy điểm cuối cùng hiện tại của thành phố
    all_municipality_scores = MunicipalityScore.objects.filter(
        municipality=municipality,
        country=user_info.country
    )
    # Tạo một map chứa cả base_score và final_score
    scores_map = {
        score.criteria_id: {'final': score.final_score, 'base': score.base_score}
        for score in all_municipality_scores
    }

    # Kết hợp điểm người dùng và điểm cuối cùng để hiển thị
    score_details = []
    for evaluation in user_evaluations:
        # Lấy bản ghi điểm tương ứng từ map
        scores = scores_map.get(evaluation.criteria_id)

        # Logic lấy điểm hiện tại
        if scores:
            current_score = scores['final'] if scores['final'] and scores['final'] != 0 else scores['base']
        else:
            current_score = 3.0

        score_details.append({
            'criteria_name': evaluation.criteria.name,
            'user_score': evaluation.score,
            'current_score': round(current_score, 2)
        })

    # Lấy thông tin từ Wikipedia
    description, image_url, wiki_url = get_municipality_info_from_wiki(municipality.name, prefecture.name)

    # Tạo bản đồ Folium
    municipality_map = None
    if municipality.latitude and municipality.longitude:
        map_center = [float(municipality.latitude), float(municipality.longitude)]
        m = folium.Map(location=map_center, zoom_start=12)
        folium.Marker(map_center, tooltip=municipality.name).add_to(m)
        municipality_map = m._repr_html_()

    return render(request, 'thank_you.html', {
        'user_info': user_info,
        'municipality': municipality,
        'prefecture': prefecture,
        'score_details': score_details,
        'municipality_description': description,
        'image_url': image_url,
        'wiki_url': wiki_url,
        'municipality_map': municipality_map,
    })

# -----------------
# Functions
# -----------------
# ----------------- CALCULATING AND UPDATING SCORES -----------------
def update_municipality_score(municipality, country):
    """
    Update avg_score and final_score for a municipality.
    """
    criteria_list = Criteria.objects.all()

    for criteria in criteria_list:
        try:
            # 1. Lấy bản ghi MunicipalityScore đã có
            score_obj = MunicipalityScore.objects.get(
                municipality=municipality,
                criteria=criteria,
                country=country
            )

            # 2. Tính avg_score từ EvaluationSurvey
            avg_score_data = EvaluationSurvey.objects.filter(
                municipality=municipality,
                criteria=criteria,
                user__country=country
            ).aggregate(Avg('score'))
            avg_score = avg_score_data['score__avg'] if avg_score_data['score__avg'] is not None else 3.0

            # 3. Cập nhật avg_score
            score_obj.avg_score = avg_score

            # 4. Tính final_score dựa trên base_score và avg_score hiện tại
            final_score = score_obj.base_score * 0.6 + avg_score * 0.4
            score_obj.final_score = final_score

            # 5. Lưu đối tượng
            score_obj.save()

        except MunicipalityScore.DoesNotExist:
            print(f"Record for {municipality} - {criteria} does not exist. Skipping update.")

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
    municipality_scores_qs = MunicipalityScore.objects.filter(
        criteria__id__in=criteria_ids,
        municipality__in=prefecture_municipalities,
        country=country
    )
    scores_map = {}
    for score in municipality_scores_qs:
        key = (score.municipality_id, score.criteria_id)
        scores_map[key] = score

    # 3. Get all municipalities and prefetch related data
    municipalities = prefecture_municipalities.order_by('name')

    # 4.Calculate matching scores
    matching_results = []

    for municipality in municipalities:
        total_weighted_score = 0
        total_weight = 0
        criteria_details = []

        # Loop through user preferences
        for rank_str, criteria_id in user_preferences.items():
            rank = int(rank_str)

            criteria = criteria_map.get(criteria_id)
            if not criteria:
                continue

            # Calculate using final scores if available, otherwise use base scores
            score_key = (municipality.id, criteria.id)
            score_obj = scores_map.get(score_key)

            # Lấy final_score, nếu không có thì lấy base_score
            if score_obj:
                municipality_score = score_obj.final_score or score_obj.base_score
            else:
                municipality_score = 3.0  # Điểm mặc định nếu không có dữ liệu

            total_weighted_score += municipality_score * rank
            total_weight += rank

            criteria_details.append({
                'criteria_name': criteria.name,
                'priority': rank,
                'municipality_score': municipality_score,
                'weighted_score': municipality_score * rank
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
    score = max(min_score, min(max_score, score))
    # Calculate percentage based on the score range
    percentage = (max_score - score) / (max_score - min_score) * 100
    return round(percentage, 2)

# ----------------- GET FUNCTIONS -----------------
def get_municipality_info_from_wiki(municipality_name, prefecture_name):
    """
    Get description, image and link from Wikipedia using a more specific query.
    """
    wikipedia.set_lang("ja")

    # Gọi hàm mới để lấy URL ảnh chính
    image_url = get_municipality_info_via_api(municipality_name)
    if not image_url:
        image_url = "https://via.placeholder.com/600x400"  # Ảnh mặc định nếu API không tìm thấy

    # Bắt đầu tìm kiếm thông tin trên Wikipedia
    full_name_query = f"{municipality_name} ({prefecture_name})"
    try:
        page = wikipedia.page(full_name_query, auto_suggest=False, redirect=True)
        description = page.summary
        wiki_url = page.url

        return description, image_url, wiki_url
    except wikipedia.exceptions.PageError:
        # Nếu không tìm thấy trang cụ thể, thử lại với tên chung hơn
        try:
            page = wikipedia.page(municipality_name, auto_suggest=True, redirect=True)
            description = page.summary
            wiki_url = page.url
            # Dọn dẹp mô tả nếu cần
            description = re.sub(r'\"(.+?)\" có thể đề cập đến:', '', description, flags=re.IGNORECASE).strip()

            return description, image_url, wiki_url
        except (wikipedia.exceptions.PageError, wikipedia.exceptions.DisambiguationError) as e:
            print(f"Error trying to get information from Wikipedia for {municipality_name}: {e}")
            return "Description is being updated", image_url, None
    except wikipedia.exceptions.DisambiguationError as e:
        print(f"Disambiguation error for {municipality_name}. Options: {e.options}")
        return "Description is being updated due to multiple matches.", image_url, None


def get_municipality_info_via_api(municipality_name):
    """
    Sử dụng API của Wikipedia để tìm ảnh chính của bài viết.
    """
    url = "https://ja.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "pageimages",
        "titles": municipality_name,
        "pithumbsize": 600,  # Kích thước hình ảnh thu nhỏ mong muốn
        "redirects": 1
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()
        pages = data['query']['pages']
        for page_id, page_data in pages.items():
            if 'thumbnail' in page_data:
                return page_data['thumbnail']['source']  # Trả về URL của ảnh chính
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Wikipedia API: {e}")

    return None  # Trả về None nếu không tìm thấy ảnh

@require_GET
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

# ------------- HÀM LẤY TỌA ĐỘ ĐỂ LÀM MAP INFO PAGE --------------
# Các hàm mới theo cùng pattern
@require_GET
def get_prefectures(request):
    """Lấy danh sách tất cả prefectures với tọa độ trung bình từ municipalities"""
    try:
        prefectures_data = []
        prefectures = Prefecture.objects.all()

        for prefecture in prefectures:
            # Tính tọa độ trung bình từ municipalities
            avg_coords = Municipality.objects.filter(
                prefecture=prefecture,
                latitude__isnull=False,
                longitude__isnull=False
            ).aggregate(
                avg_lat=Avg('latitude'),
                avg_lng=Avg('longitude')
            )

            prefectures_data.append({
                'id': prefecture.id,
                'name': prefecture.name,
                'latitude': avg_coords['avg_lat'],
                'longitude': avg_coords['avg_lng']
            })

        return JsonResponse(prefectures_data, safe=False)
    except Exception:
        return JsonResponse([], safe=False)


@require_GET
def get_prefecture_coords(request):
    """Lấy tọa độ trung bình của prefecture từ municipalities"""
    prefecture_id = request.GET.get('prefecture_id')
    if not prefecture_id:
        return JsonResponse({'error': 'Prefecture ID is required'}, status=400)

    try:
        prefecture = get_object_or_404(Prefecture, id=prefecture_id)

        # Tính tọa độ trung bình từ municipalities
        avg_coords = Municipality.objects.filter(
            prefecture=prefecture,
            latitude__isnull=False,
            longitude__isnull=False
        ).aggregate(
            avg_lat=Avg('latitude'),
            avg_lng=Avg('longitude')
        )

        if avg_coords['avg_lat'] is None or avg_coords['avg_lng'] is None:
            return JsonResponse({'error': 'No coordinate data available for this prefecture'}, status=404)

        return JsonResponse({
            'latitude': avg_coords['avg_lat'],
            'longitude': avg_coords['avg_lng'],
            'name': prefecture.name
        })
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid prefecture ID'}, status=400)


@require_GET
def get_municipality_coords(request):
    """Lấy tọa độ của municipality theo ID"""
    municipality_id = request.GET.get('municipality_id')
    if not municipality_id:
        return JsonResponse({'error': 'Municipality ID is required'}, status=400)

    try:
        municipality = get_object_or_404(Municipality, id=municipality_id)

        if not municipality.latitude or not municipality.longitude:
            return JsonResponse({'error': 'No coordinate data available for this municipality'}, status=404)

        return JsonResponse({
            'latitude': municipality.latitude,
            'longitude': municipality.longitude,
            'name': municipality.name
        })
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid municipality ID'}, status=400)


@require_GET
def get_location_by_coords(request):
    """
    Tìm municipality gần nhất dựa trên tọa độ, prefecture sẽ được suy ra từ municipality
    """
    lat_str = request.GET.get('lat')
    lng_str = request.GET.get('lng')

    if not lat_str or not lng_str:
        return JsonResponse({'error': 'Latitude and longitude are required'}, status=400)

    try:
        target_lat = float(lat_str)
        target_lng = float(lng_str)

        municipalities = Municipality.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False
        ).select_related('prefecture')

        if not municipalities.exists():
            return JsonResponse({'error': 'No municipalities with coordinate data found'}, status=404)

        closest_municipality = None
        min_distance = float('inf')

        for municipality in municipalities:
            distance = geopy.distance.geodesic(
                (municipality.latitude, municipality.longitude),
                (target_lat, target_lng)
            ).km
            if distance < min_distance:
                min_distance = distance
                closest_municipality = municipality

        if not closest_municipality:
            return JsonResponse({'error': 'No municipality found'}, status=404)

        return JsonResponse({
            'prefecture_id': closest_municipality.prefecture.id,
            'prefecture_name': closest_municipality.prefecture.name,
            'municipality_id': closest_municipality.id,
            'municipality_name': closest_municipality.name,
            'distance_km': round(min_distance, 2)
        })

    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid coordinates'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)