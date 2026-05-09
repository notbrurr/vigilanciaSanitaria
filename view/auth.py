from django.shortcuts import render
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required

class AuthView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True

@login_required
def home_view(request):
    return render(request, 'home.html')
