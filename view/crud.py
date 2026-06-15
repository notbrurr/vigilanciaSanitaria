from django.urls import path
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

from model.models import Empresa, ResponsavelTecnico, TipoDocumento, CategoriaVisita, Documento, Visita, Colaborador, NecessidadeDocumento, User

MODELS_TO_CRUD = [
    Empresa, ResponsavelTecnico, TipoDocumento, CategoriaVisita, 
    Documento, Visita, Colaborador, NecessidadeDocumento, User
]

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
                import datetime
                hoje = datetime.date.today()
                if status_filtro == 'vencido':
                    queryset = queryset.filter(documentos__data_vencimento__lt=hoje).distinct()
                elif status_filtro == 'regular':
                    empresas_com_vencidos = Empresa.objects.filter(documentos__data_vencimento__lt=hoje).values_list('id', flat=True)
                    queryset = queryset.exclude(id__in=empresas_com_vencidos)
                
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
        if self.model in [TipoDocumento, CategoriaVisita]:
            show_extra_companies = True
            context['headers'].append("Empresas Relacionadas")
        if self.model == ResponsavelTecnico:
            show_rt_empresas = True
            context['headers'].append("Empresas sob Responsabilidade")
            
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
        from view.forms import UserForm, ResponsavelTecnicoForm, NecessidadeDocumentoForm, DocumentoForm
        forms_map = {
            User: UserForm,
            ResponsavelTecnico: ResponsavelTecnicoForm,
            NecessidadeDocumento: NecessidadeDocumentoForm,
            Documento: DocumentoForm,
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
        from view.forms import UserForm, ResponsavelTecnicoForm, NecessidadeDocumentoForm, DocumentoForm
        forms_map = {
            User: UserForm,
            ResponsavelTecnico: ResponsavelTecnicoForm,
            NecessidadeDocumento: NecessidadeDocumentoForm,
            Documento: DocumentoForm,
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
