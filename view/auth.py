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
    trinta_dias = hoje + timezone.timedelta(days=30)
    
    # Documentos que vencem nos próximos 30 dias (e que não venceram ainda)
    docs_a_vencer = Documento.objects.filter(data_vencimento__gte=hoje, data_vencimento__lte=trinta_dias).select_related('empresa', 'tipo')
    
    # Criar alertas de documentos vencendo
    alertas = []
    for doc in docs_a_vencer:
        dias_restantes = (doc.data_vencimento - hoje).days
        alertas.append({
            'documento': doc,
            'empresa': doc.empresa.razao_social,
            'descricao': doc.tipo.descricao,
            'dias_restantes': dias_restantes,
            'data_vencimento': doc.data_vencimento.strftime('%d/%m/%Y'),
            'classe': 'danger' if dias_restantes <= 7 else 'warning'
        })
        
    # Calcular histórico de visitas por mês nos últimos 6 meses
    from django.db.models import Count
    from django.db.models.functions import ExtractMonth, ExtractYear
    
    visitas_por_mes = Visita.objects.annotate(
        mes=ExtractMonth('data_agendamento'),
        ano=ExtractYear('data_agendamento')
    ).values('ano', 'mes').annotate(total=Count('id')).order_by('ano', 'mes')
    
    nomes_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    chart_labels = []
    chart_data = []
    
    for i in range(5, -1, -1):
        ano_atual = hoje.year
        mes_atual = hoje.month - i
        while mes_atual <= 0:
            mes_atual += 12
            ano_atual -= 1
            
        label = f"{nomes_meses[mes_atual - 1]}/{ano_atual}"
        chart_labels.append(label)
        
        count = 0
        for item in visitas_por_mes:
            if item['mes'] == mes_atual and item['ano'] == ano_atual:
                count = item['total']
                break
        chart_data.append(count)
        
    # Calcular visitas programadas (pendentes) ordenadas
    visitas_pendentes_lista = Visita.objects.filter(realizada=False).select_related('empresa', 'categoria').order_by('data_agendamento')
    visitas_alertas = []
    for vis in visitas_pendentes_lista:
        data_local = timezone.localtime(vis.data_agendamento) if timezone.is_aware(vis.data_agendamento) else vis.data_agendamento
        dias_ate = (data_local.date() - hoje).days
        
        if dias_ate < 0:
            classe = 'danger'
            desc_tempo = f"Atrasada há {abs(dias_ate)} dias"
        elif dias_ate == 0:
            classe = 'warning'
            desc_tempo = "Hoje!"
        elif dias_ate <= 3:
            classe = 'info'
            desc_tempo = f"Em {dias_ate} dias"
        else:
            classe = 'success'
            desc_tempo = f"Em {dias_ate} dias"
            
        visitas_alertas.append({
            'empresa': vis.empresa.razao_social,
            'categoria': vis.categoria.descricao,
            'data': data_local.strftime('%d/%m/%Y às %H:%M'),
            'classe': classe,
            'desc_tempo': desc_tempo
        })
        
    context = {
        'total_empresas': Empresa.objects.count(),
        'visitas_pendentes': Visita.objects.filter(realizada=False).count(),
        'docs_vencidos': Documento.objects.filter(data_vencimento__lt=hoje).count(),
        'docs_regulares': Documento.objects.filter(data_vencimento__gte=hoje).count(),
        'alertas': alertas,
        'visitas_alertas': visitas_alertas,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }
    return render(request, 'home.html', context)
