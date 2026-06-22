from django.urls import path
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

from model.models import Empresa, ResponsavelTecnico, TipoDocumento, CategoriaVisita, Documento, Visita, Colaborador, NecessidadeDocumento, User

MODELS_TO_CRUD = [
    Empresa, ResponsavelTecnico, TipoDocumento, CategoriaVisita, 
    Documento, Visita, Colaborador, NecessidadeDocumento, User
]

def get_irregular_empresas_ids():
    import datetime
    hoje = datetime.date.today()
    
    # 1. Companies with expired documents
    expired_ids = set(Empresa.objects.filter(documentos__data_vencimento__lt=hoje).values_list('id', flat=True))
    
    # 2. Companies missing required documents
    mandatory_types = set(TipoDocumento.objects.filter(obrigatorio=True).values_list('id', flat=True))
    
    from model.models import NecessidadeDocumento
    necessidades = NecessidadeDocumento.objects.values_list('empresa_id', 'tipo_documento_id')
    
    required_map = {}
    all_empresas = Empresa.objects.all()
    for emp in all_empresas:
        required_map[emp.id] = set(mandatory_types)
        
    for emp_id, tipo_id in necessidades:
        if emp_id in required_map:
            required_map[emp_id].add(tipo_id)
            
    from model.models import Documento
    uploaded = Documento.objects.values_list('empresa_id', 'tipo_id')
    uploaded_map = {}
    for emp_id, tipo_id in uploaded:
        if emp_id not in uploaded_map:
            uploaded_map[emp_id] = set()
        uploaded_map[emp_id].add(tipo_id)
        
    irregular_ids = set(expired_ids)
    for emp_id, req_set in required_map.items():
        up_set = uploaded_map.get(emp_id, set())
        if not req_set.issubset(up_set):
            irregular_ids.add(emp_id)
            
    return list(irregular_ids)


class GenericListView(LoginRequiredMixin, ListView):
    template_name = 'generic_list.html'
    
    def dispatch(self, request, *args, **kwargs):
        if self.model == User and not (request.user.is_staff or request.user.is_superuser):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status')
        if self.model == Visita and status == 'pendente':
            queryset = queryset.filter(realizada=False)
        elif self.model == Documento:
            import datetime
            hoje = datetime.date.today()
            if status == 'vencido':
                queryset = queryset.filter(data_vencimento__lt=hoje)
            elif status == 'regular':
                queryset = queryset.filter(data_vencimento__gte=hoje)
        elif self.model == Empresa:
            status_filtro = self.request.GET.get('status_documento')
            if status_filtro:
                irregular_ids = get_irregular_empresas_ids()
                if status_filtro == 'vencido':
                    queryset = queryset.filter(id__in=irregular_ids)
                elif status_filtro == 'regular':
                    queryset = queryset.exclude(id__in=irregular_ids)
                
        # Ordenar por empresa se o modelo tiver campo relacionado a Empresa
        if hasattr(self.model, 'empresa'):
            queryset = queryset.order_by('empresa__razao_social')
            
        return queryset
        
    def get_context_data(self, **kwargs):
        import datetime
        from django.utils import timezone
        
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()
        context['model_name_plural'] = self.model._meta.verbose_name_plural.title()
        context['create_url'] = f"{self.model._meta.model_name}_create"
        context['update_url_name'] = f"{self.model._meta.model_name}_update"
        context['delete_url_name'] = f"{self.model._meta.model_name}_delete"
        
        # Selecionar campos a exibir (ignora pk)
        fields = [f for f in self.model._meta.fields if not f.primary_key]
        context['headers'] = [f.verbose_name.title() if hasattr(f, 'verbose_name') else f.name for f in fields]
        
        show_extra_companies = False
        show_rt_empresas = False
        show_empresa_compliance = False
        if self.model in [TipoDocumento, CategoriaVisita]:
            show_extra_companies = True
            context['headers'].append("Empresas Relacionadas")
        if self.model == ResponsavelTecnico:
            show_rt_empresas = True
            context['headers'].append("Empresas sob Responsabilidade")
        if self.model == Empresa:
            show_empresa_compliance = True
            context['headers'].append("Status de Conformidade")
            
        rows = []
        for obj in context['object_list']:
            row = []
            for f in fields:
                val = getattr(obj, f.name)
                is_long_text = f.get_internal_type() == 'TextField'
                is_file = f.get_internal_type() == 'FileField'
                url_val = val.url if is_file and val else ''
                
                if isinstance(val, bool):
                    str_val = 'Sim' if val else 'Não'
                elif isinstance(val, datetime.datetime):
                    local_val = timezone.localtime(val) if timezone.is_aware(val) else val
                    str_val = local_val.strftime('%d/%m/%Y às %H:%M')
                elif isinstance(val, datetime.date):
                    str_val = val.strftime('%d/%m/%Y')
                elif is_file and val:
                    str_val = val.name.split('/')[-1]
                else:
                    str_val = str(val) if val is not None else ''
                    
                row.append({
                    'value': str_val,
                    'is_long': is_long_text,
                    'is_file': is_file,
                    'file_url': url_val,
                    'is_bool': isinstance(val, bool),
                    'bool_val': val if isinstance(val, bool) else None,
                    'field_name': f.name,
                })
                
            if show_extra_companies:
                if self.model == TipoDocumento:
                    empresas = Empresa.objects.filter(documentos__tipo=obj).distinct()
                    val_str = ", ".join([emp.razao_social for emp in empresas]) if empresas.exists() else "Nenhuma"
                elif self.model == CategoriaVisita:
                    empresas = Empresa.objects.filter(visitas__categoria=obj).distinct()
                    val_str = ", ".join([emp.razao_social for emp in empresas]) if empresas.exists() else "Nenhuma"
                    
                row.append({
                    'value': val_str,
                    'is_long': len(val_str) > 50,
                    'is_file': False,
                    'file_url': '',
                    'is_bool': False,
                    'bool_val': None,
                    'field_name': '',
                })

            if show_rt_empresas:
                empresas_do_rt = obj.empresas.all()
                val_str = ", ".join([emp.razao_social for emp in empresas_do_rt]) if empresas_do_rt.exists() else "Nenhuma"
                row.append({
                    'value': val_str,
                    'is_long': len(val_str) > 50,
                    'is_file': False,
                    'file_url': '',
                    'is_bool': False,
                    'bool_val': None,
                    'field_name': '',
                })

            if show_empresa_compliance:
                hoje = datetime.date.today()
                has_expired = obj.documentos.filter(data_vencimento__lt=hoje).exists()
                
                from django.db.models import Q
                required_types = TipoDocumento.objects.filter(
                    Q(obrigatorio=True) | Q(necessidades_documento__empresa=obj)
                ).distinct()
                uploaded_types = set(obj.documentos.values_list('tipo_id', flat=True))
                missing_types = [rt.descricao for rt in required_types if rt.id not in uploaded_types]
                
                if has_expired or missing_types:
                    pendencias = []
                    if has_expired:
                        pendencias.append("Docs Vencidos")
                    if missing_types:
                        pendencias.append(f"Faltando: {', '.join(missing_types)}")
                    title_text = "; ".join(pendencias)
                    status_html = f"<span class='status-badge status-vencido' title='{title_text}' style='display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; background: rgba(239, 68, 68, 0.1); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.2);'><i class='bx bx-error-circle'></i> Irregular</span>"
                else:
                    status_html = "<span class='status-badge status-regular' style='display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; background: rgba(16, 185, 129, 0.1); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.2);'><i class='bx bx-check-circle'></i> Regular</span>"
                
                row.append({
                    'value': status_html,
                    'is_long': False,
                    'is_file': False,
                    'file_url': '',
                    'is_bool': False,
                    'bool_val': None,
                    'is_html': True,
                    'field_name': 'status_conformidade',
                })
                
            rows.append({'obj': obj, 'cells': row})
        context['rows'] = rows
        return context

class GenericCreateView(LoginRequiredMixin, CreateView):
    template_name = 'generic_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        if self.model == User and not (request.user.is_staff or request.user.is_superuser):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_form_class(self):
        from view.forms import UserForm, ResponsavelTecnicoForm, NecessidadeDocumentoForm, DocumentoForm, EmpresaForm
        forms_map = {
            User: UserForm,
            ResponsavelTecnico: ResponsavelTecnicoForm,
            NecessidadeDocumento: NecessidadeDocumentoForm,
            Documento: DocumentoForm,
            Empresa: EmpresaForm,
        }
        if self.model in forms_map:
            return forms_map[self.model]
        from django import forms
        class DynamicForm(forms.ModelForm):
            class Meta:
                model = self.model
                fields = '__all__'
        return DynamicForm
    
    def get_success_url(self):
        return reverse_lazy(f"{self.model._meta.model_name}_list")
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Cadastro de {self.model._meta.verbose_name.title()}"
        context['list_url'] = f"{self.model._meta.model_name}_list"
        return context

class GenericUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'generic_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        if self.model == User and not (request.user.is_staff or request.user.is_superuser):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_form_class(self):
        from view.forms import UserForm, ResponsavelTecnicoForm, NecessidadeDocumentoForm, DocumentoForm, EmpresaForm
        forms_map = {
            User: UserForm,
            ResponsavelTecnico: ResponsavelTecnicoForm,
            NecessidadeDocumento: NecessidadeDocumentoForm,
            Documento: DocumentoForm,
            Empresa: EmpresaForm,
        }
        if self.model in forms_map:
            return forms_map[self.model]
        from django import forms
        class DynamicForm(forms.ModelForm):
            class Meta:
                model = self.model
                fields = '__all__'
        return DynamicForm
    
    def get_success_url(self):
        return reverse_lazy(f"{self.model._meta.model_name}_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Edição de {self.model._meta.verbose_name.title()}"
        context['list_url'] = f"{self.model._meta.model_name}_list"
        return context

class GenericDeleteView(LoginRequiredMixin, DeleteView):
    template_name = 'generic_confirm_delete.html'
    
    def dispatch(self, request, *args, **kwargs):
        if self.model == User and not (request.user.is_staff or request.user.is_superuser):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy(f"{self.model._meta.model_name}_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Excluir {self.model._meta.verbose_name.title()}"
        context['list_url'] = f"{self.model._meta.model_name}_list"
        return context

def get_crud_urls():
    urls = []
    for model in MODELS_TO_CRUD:
        model_name = model._meta.model_name
        urls.extend([
            path(f'{model_name}/', GenericListView.as_view(model=model), name=f'{model_name}_list'),
            path(f'{model_name}/novo/', GenericCreateView.as_view(model=model), name=f'{model_name}_create'),
            path(f'{model_name}/<int:pk>/editar/', GenericUpdateView.as_view(model=model), name=f'{model_name}_update'),
            path(f'{model_name}/<int:pk>/excluir/', GenericDeleteView.as_view(model=model), name=f'{model_name}_delete'),
        ])
    return urls
