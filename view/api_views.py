import re
import json
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.shortcuts import get_object_or_404
from django.utils import timezone
from model.models import Empresa, ResponsavelTecnico, Documento, Visita

def validar_cpf_logica(cpf):
    cpf = re.sub(r'[^0-9]', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for i in range(9, 11):
        value = sum((int(cpf[num]) * ((i + 1) - num) for num in range(0, i)))
        digit = ((value * 10) % 11) % 10
        if str(digit) != cpf[i]:
            return False
    return True

@require_GET
def validate_document_view(request):
    tipo = request.GET.get('tipo', '')
    valor = request.GET.get('valor', '')
    
    if tipo == 'cpf':
        is_valid = validar_cpf_logica(valor)
        return JsonResponse({'valid': is_valid})
        
    elif tipo == 'telefone':
        # Validar formato de telefone brasileiro com DDD (10 ou 11 dígitos)
        telefone = re.sub(r'[^0-9]', '', valor)
        is_valid = len(telefone) in [10, 11]
        return JsonResponse({'valid': is_valid})
        
    return JsonResponse({'error': 'Tipo de validação inválido'}, status=400)

@require_GET
def empresa_details_view(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    hoje = timezone.now().date()
    
    responsaveis = []
    if empresa.responsavel_tecnico:
        rt = empresa.responsavel_tecnico
        responsaveis.append({
            'nome': rt.nome,
            'conselho': rt.conselho_classe,
            'registro': rt.numero_registro
        })
        
    documentos = []
    for doc in empresa.documentos.all():
        status = 'Vencido' if doc.data_vencimento and doc.data_vencimento < hoje else 'Regular'
        documentos.append({
            'tipo': doc.tipo.descricao,
            'emissao': doc.data_emissao.strftime('%d/%m/%Y'),
            'vencimento': doc.data_vencimento.strftime('%d/%m/%Y') if doc.data_vencimento else 'Sem validade',
            'status': status
        })
        
    visitas = []
    for vis in empresa.visitas.all():
        status = 'Realizada' if vis.realizada else 'Pendente'
        data_ag = timezone.localtime(vis.data_agendamento) if timezone.is_aware(vis.data_agendamento) else vis.data_agendamento
        visitas.append({
            'categoria': vis.categoria.descricao,
            'data': data_ag.strftime('%d/%m/%Y às %H:%M'),
            'status': status
        })
        
    data = {
        'razao_social': empresa.razao_social,
        'cnpj': empresa.cnpj,
        'endereco': empresa.endereco,
        'telefone': empresa.telefone or 'Não informado',
        'email': empresa.email or 'Não informado',
        'responsaveis': responsaveis,
        'documentos': documentos,
        'visitas': visitas
    }
    return JsonResponse(data)

@require_GET
def empresa_allowed_documents_view(request, pk):
    from django.db.models import Q
    from model.models import TipoDocumento
    empresa = get_object_or_404(Empresa, pk=pk)
    tipos = TipoDocumento.objects.filter(
        Q(obrigatorio=True) | Q(necessidades_documento__empresa=empresa)
    ).distinct()
    data = [{'id': t.id, 'descricao': t.descricao} for t in tipos]
    
    rt_data = None
    if empresa.responsavel_tecnico:
        rt_data = {
            'id': empresa.responsavel_tecnico.id,
            'nome': empresa.responsavel_tecnico.nome
        }
    return JsonResponse({
        'document_types': data,
        'responsavel_tecnico': rt_data
    })

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from model.models import Colaborador, TipoDocumento

@login_required
def empresa_painel_view(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    hoje = timezone.now().date()
    
    filtro = request.GET.get('filtro', '') # 'vencido' ou ''
    
    # Colaboradores
    colaboradores = Colaborador.objects.filter(empresa=empresa)
    if filtro == 'vencido':
        colaboradores = colaboradores.filter(data_vencimento__lt=hoje, ativo=True)
        
    # Documentos
    documentos = Documento.objects.filter(empresa=empresa).select_related('tipo', 'responsavel_tecnico')
    if filtro == 'vencido':
        documentos = documentos.filter(data_vencimento__lt=hoje)
        
    # Necessidades/Obrigatorios
    from django.db.models import Q
    required_types = TipoDocumento.objects.filter(
        Q(obrigatorio=True) | Q(necessidades_documento__empresa=empresa)
    ).distinct()
    
    # Documentos que estão faltando
    uploaded_types = set(Documento.objects.filter(empresa=empresa).values_list('tipo_id', flat=True))
    missing_required = []
    
    # Se filtro for 'vencido', só listamos os que estão realmente faltando ou vencidos
    for rt in required_types:
        if rt.id not in uploaded_types:
            missing_required.append({
                'tipo': rt,
                'status': 'Faltando'
            })
            
    # Visitas
    visitas = Visita.objects.filter(empresa=empresa).select_related('categoria', 'fiscal', 'responsavel_tecnico')
    if filtro == 'vencido':
        # Visitas agendadas no passado e não realizadas
        visitas = visitas.filter(realizada=False, data_agendamento__lt=timezone.now())
        
    context = {
        'empresa': empresa,
        'colaboradores': colaboradores,
        'documentos': documentos,
        'missing_required': missing_required,
        'visitas': visitas,
        'filtro': filtro,
        'hoje': hoje,
    }
    return render(request, 'empresa_painel.html', context)

