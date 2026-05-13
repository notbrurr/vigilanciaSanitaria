from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Empresa, ResponsavelTecnico, TipoDocumento, CategoriaVisita, Documento, Visita, Colaborador, NecessidadeDocumento, LogAuditoria


# ==================== CONFIGURAÇÃO GERAL ====================
admin.site.site_header = "Vigilância Sanitária"
admin.site.site_title = "Vigilância Sanitária - Admin"
admin.site.index_title = "Painel de Administração"


# ==================== USUÁRIO ====================
admin.site.register(User, UserAdmin)


# ==================== EMPRESA ====================
@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('razao_social', 'nome_fantasia', 'cnpj', 'telefone', 'email', 'usuario')
    search_fields = ('razao_social', 'nome_fantasia', 'cnpj')
    ordering = ('razao_social',)
    
    # Campos que vão aparecer na tela de cadastro/edição
    fields = ('razao_social', 'nome_fantasia', 'cnpj', 'telefone', 
              'email', 'endereco', 'usuario')


# ==================== RESPONSÁVEL TÉCNICO ====================
@admin.register(ResponsavelTecnico)
class ResponsavelTecnicoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf', 'conselho_classe', 'numero_registro', 'empresa')
    search_fields = ('nome', 'cpf', 'numero_registro')
    list_filter = ('conselho_classe', 'empresa')
    ordering = ('nome',)


# ==================== TIPO DE DOCUMENTO ====================
@admin.register(TipoDocumento)
class TipoDocumentoAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'validade_meses')
    search_fields = ('descricao',)
    list_filter = ('validade_meses',)


# ==================== CATEGORIA DE VISITA ====================
@admin.register(CategoriaVisita)
class CategoriaVisitaAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'prioridade')
    list_filter = ('prioridade',)
    search_fields = ('descricao',)

# ==================== DOCUMENTO ====================
@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'tipo', 'data_emissao', 'data_vencimento')
    list_filter = ('tipo', 'data_emissao')
    search_fields = ('empresa__razao_social', 'empresa__cnpj')
    date_hierarchy = 'data_emissao'

# ==================== VISITA ====================
@admin.register(Visita)
class VisitaAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'categoria', 'fiscal', 'data_agendamento', 'realizada')
    list_filter = ('realizada', 'categoria', 'fiscal')
    search_fields = ('empresa__razao_social', 'empresa__cnpj')
    date_hierarchy = 'data_agendamento'

# ==================== COLABORADOR ====================
@admin.register(Colaborador)
class ColaboradorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf', 'empresa', 'data_entrada', 'ativo')
    list_filter = ('ativo', 'empresa')
    search_fields = ('nome', 'cpf', 'empresa__razao_social')

# ==================== NECESSIDADE DE DOCUMENTO ====================
@admin.register(NecessidadeDocumento)
class NecessidadeDocumentoAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'tipo_documento')
    list_filter = ('tipo_documento',)
    search_fields = ('empresa__razao_social', 'empresa__cnpj')

# ==================== LOG AUDITORIA ====================
@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'usuario', 'fk_registro', 'data_hora')
    list_filter = ('tipo', 'data_hora')
    search_fields = ('descricao', 'usuario__username')
    readonly_fields = ('usuario', 'fk_registro', 'tipo', 'data_hora', 'descricao')