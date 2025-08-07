from django.shortcuts import (
    render,
    redirect,
)
from django.http import HttpResponse

def home_page(request):
    return render(request, 'home_page.html')

def user_info(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        birthday = request.POST.get('birthday')
        nationality = request.POST.get('nationality')
        current_residence = request.POST.get('current_residence')
        next_action = request.POST.get('next_action')

        # Chuyển hướng đến survey tương ứng
        if next_action == 'match':
            return redirect('matching_survey')  # hoặc dùng URL trực tiếp
        elif next_action == 'evaluate':
            return redirect('evaluation_survey')

        # Nếu không có lựa chọn hợp lệ
        return HttpResponse("Invalid choice.")

    return HttpResponse("Please submit the form.")

def matching_survey(request):
    return render(request, 'matching_survey.html')

def evaluation_survey(request):
    return render(request, 'evaluation_survey.html')
