from django.shortcuts import render

# Create your views here.
def home_page(request):
    """
    Render the home page of the chamu application.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Rendered home page template.
    """
    return render(request, 'home_page.html')  # Ensure the template exists in the correct directory