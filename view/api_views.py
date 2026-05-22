import re
import json
from django.http import JsonResponse
from django.views.decorators.http import require_GET

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
