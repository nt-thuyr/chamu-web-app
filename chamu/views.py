from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import (
    UserInfoForm, EvaluationSurveyForm
)
from .models import (
    UserInfo, EvaluationSurvey
)

def homepage(request):
    if request.method == 'POST':
        form = UserInfoForm(request.POST)
        if form.is_valid():
            next_action = form.cleaned_data['next_action']
            print("User Info:", form.cleaned_data)
            if next_action == 'match':
                return redirect('matching_survey')  # tên trong urls.py
            elif next_action == 'evaluate':
                # Lưu thông tin người dùng
                form.save()
                return redirect('evaluation_survey', user_info_id=form.instance.id)
            else:
                return HttpResponse("Invalid choice.")
    else:
        form = UserInfoForm()

    return render(request, 'homepage.html', {'form': form})


def user_info(request):
    return HttpResponse("Please submit the form via homepage.")


def matching_survey(request):
    return render(request, 'matching_survey.html')

def evaluation_survey(request, user_info_id):
    user_info = UserInfo.objects.get(id=user_info_id)

    if request.method == 'POST':
        form = EvaluationSurveyForm(request.POST)
        if form.is_valid():
            survey = form.save(commit=False)
            survey.user_info = user_info
            survey.save()
            return redirect('homepage')
    else:
        form = EvaluationSurveyForm()

    return render(request, 'evaluation_survey.html', {'form': form})
