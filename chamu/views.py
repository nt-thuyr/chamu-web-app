from django.db.models import Avg
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .forms import (
    UserInfoForm, EvaluationSurveyForm, MatchingSurveyForm
)
from .models import (
    UserInfo, EvaluationSurvey, City, Nationality, LocalShop, CityScore
)


# Views cũ không cần sửa
def homepage(request):
    if request.method == 'POST':
        form = UserInfoForm(request.POST)
        if form.is_valid():
            next_action = form.cleaned_data['next_action']
            print("User Info:", form.cleaned_data)
            if next_action == 'match':
                return redirect('matching_survey')
            elif next_action == 'evaluate':
                form.save()
                return redirect('evaluation_survey', user_info_id=form.instance.id)
            else:
                return HttpResponse("Invalid choice.")
    else:
        form = UserInfoForm()
    return render(request, 'homepage.html', {'form': form})

def update_city_average(city, nationality):
    """
    Cập nhật điểm trung bình của thành phố trong model CityScore
    dựa trên các khảo sát của người dùng cùng quốc tịch.
    """
    # Lấy bản ghi CityScore của thành phố và quốc tịch này
    try:
        city_score = CityScore.objects.get(city=city, nationality=nationality)
    except CityScore.DoesNotExist:
        # Nếu chưa có, tạo mới và dùng base score làm điểm khởi đầu
        city_score = CityScore.objects.create(
            city=city,
            nationality=nationality,
            avg_cost_of_living=0.0,
            avg_local_shops=0.0,
            avg_temperature=0.0,
            avg_crime_rate=0.0,
            avg_population=0.0
        )

    # Lọc tất cả các khảo sát cho thành phố và quốc tịch này
    surveys = EvaluationSurvey.objects.filter(city=city, user__nationality=nationality)
    total_surveys = surveys.count()

    # Lấy điểm gốc về Local Shop từ bảng LocalShop
    try:
        base_local_shops = LocalShop.objects.get(city=city, nationality=nationality).shop_number
    except LocalShop.DoesNotExist:
        base_local_shops = 0.0

    if total_surveys > 0:
        avg_scores = surveys.aggregate(
            Avg('cost_of_living_score'),
            Avg('local_shops_score'),
            Avg('temperature_score'),
            Avg('crime_rate_score'),
            Avg('population_score'),
        )

        # Áp dụng công thức: base * 0.6 + avg_survey * 0.4
        city_score.avg_cost_of_living = (city.base_cost_of_living * 0.6) + (avg_scores['cost_of_living_score__avg'] * 0.4)
        city_score.avg_local_shops = (base_local_shops * 0.6) + (avg_scores['local_shops_score__avg'] * 0.4)
        city_score.avg_temperature = (city.base_temperature * 0.6) + (avg_scores['temperature_score__avg'] * 0.4)
        city_score.avg_crime_rate = (city.base_crime_rate * 0.6) + (avg_scores['crime_rate_score__avg'] * 0.4)
        city_score.avg_population = (city.base_population * 0.6) + (avg_scores['population_score__avg'] * 0.4)

        city_score.save()
    else:
        # Nếu chưa có khảo sát, điểm final sẽ bằng điểm base
        city_score.avg_cost_of_living = city.base_cost_of_living
        city_score.avg_local_shops = base_local_shops
        city_score.avg_temperature = city.base_temperature
        city_score.avg_crime_rate = city.base_crime_rate
        city_score.avg_population = city.base_population
        city_score.save()


def evaluation_survey(request, user_info_id):
    user_info = get_object_or_404(UserInfo, id=user_info_id)
    current_city = user_info.city

    if request.method == 'POST':
        form = EvaluationSurveyForm(request.POST)
        if form.is_valid():
            survey = form.save(commit=False)
            survey.user = user_info
            survey.city = current_city
            survey.save()

            # Lấy đối tượng Nationality từ UserInfo
            nationality = user_info.nationality

            # Gọi hàm cập nhật điểm trung bình
            update_city_average(current_city, nationality)

            return redirect('homepage')
    else:
        form = EvaluationSurveyForm()
    return render(request, 'evaluation_survey.html', {'form': form, 'user_info': user_info})


def matching_survey(request):
    if request.method == 'POST':
        form = MatchingSurveyForm(request.POST)
        if form.is_valid():
            user_preferences = {
                'cost_of_living_score': int(form.cleaned_data['cost_of_living_score']),
                'local_shops_score': int(form.cleaned_data['local_shops_score']),
                'temperature_score': int(form.cleaned_data['temperature_score']),
                'crime_rate_score': int(form.cleaned_data['crime_rate_score']),
                'population_score': int(form.cleaned_data['population_score']),
            }

            # Lấy tất cả các bản ghi điểm số của các thành phố
            city_scores = CityScore.objects.all()

            matching_results = []
            for city_score in city_scores:
                # Lấy điểm cuối cùng từ bảng CityScore, không phải từ City
                matching_score = abs(user_preferences['cost_of_living_score'] - city_score.avg_cost_of_living) + \
                                 abs(user_preferences['local_shops_score'] - city_score.avg_local_shops) + \
                                 abs(user_preferences['temperature_score'] - city_score.avg_temperature) + \
                                 abs(user_preferences['crime_rate_score'] - city_score.avg_crime_rate) + \
                                 abs(user_preferences['population_score'] - city_score.avg_population)

                matching_results.append({
                    'city': city_score.city,
                    'score': matching_score
                })

            matching_results.sort(key=lambda x: x['score'])

            return render(request, 'matching_results.html', {'results': matching_results})
    else:
        form = MatchingSurveyForm()
    return render(request, 'matching_survey.html', {'form': form})