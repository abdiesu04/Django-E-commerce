from django.shortcuts import render

# Create your views here.
def home(request):
    """
    Home page view for the e-commerce store
    """
    context = {
        'title': 'Welcome to Our E-commerce Store'
    }
    return render(request, 'store/home.html', context)
