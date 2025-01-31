from django.shortcuts import render


def welcome_view(request):
    return render(request, 'welcome.html')  # This will render the 'welcome.html' template
