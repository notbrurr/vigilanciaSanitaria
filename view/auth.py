from django.shortcuts import render
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from model.models import Empresa, Visita, Documento

class AuthView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True

@login_required
def home_view(request):
    hoje = timezone.now().date()
    context = {
        'total_empresas': Empresa.objects.count(),
        'visitas_pendentes': Visita.objects.filter(realizada=False).count(),
        'docs_vencidos': Documento.objects.filter(data_vencimento__lt=hoje).count(),
        'docs_regulares': Documento.objects.filter(data_vencimento__gte=hoje).count(),
    }
    return render(request, 'home.html', context)
