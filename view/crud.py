from django.urls import path
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

from model.models import Empresa, ResponsavelTecnico, TipoDocumento, CategoriaVisita, Documento, Visita, Colaborador, NecessidadeDocumento

MODELS_TO_CRUD = [
    Empresa, ResponsavelTecnico, TipoDocumento, CategoriaVisita, 
    Documento, Visita, Colaborador, NecessidadeDocumento
]

class GenericListView(LoginRequiredMixin, ListView):
    template_name = 'generic_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()
        context['model_name_plural'] = self.model._meta.verbose_name_plural.title()
        context['create_url'] = f"{self.model._meta.model_name}_create"
        context['update_url_name'] = f"{self.model._meta.model_name}_update"
        context['delete_url_name'] = f"{self.model._meta.model_name}_delete"
        
        # Select first 5 non-primary key fields to show in the table
        fields = [f for f in self.model._meta.fields if not f.primary_key][:5]
        context['headers'] = [f.verbose_name.title() if hasattr(f, 'verbose_name') else f.name for f in fields]
        
        rows = []
        for obj in context['object_list']:
            row = []
            for f in fields:
                val = getattr(obj, f.name)
                # Formatar valor (se for Foreign Key ele chama __str__)
                row.append(str(val) if val is not None else '')
            rows.append({'obj': obj, 'cells': row})
        context['rows'] = rows
        return context

class GenericCreateView(LoginRequiredMixin, CreateView):
    template_name = 'generic_form.html'
    fields = '__all__'
    
    def get_success_url(self):
        return reverse_lazy(f"{self.model._meta.model_name}_list")
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Cadastro de {self.model._meta.verbose_name.title()}"
        context['list_url'] = f"{self.model._meta.model_name}_list"
        return context

class GenericUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'generic_form.html'
    fields = '__all__'
    
    def get_success_url(self):
        return reverse_lazy(f"{self.model._meta.model_name}_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Edição de {self.model._meta.verbose_name.title()}"
        context['list_url'] = f"{self.model._meta.model_name}_list"
        return context

class GenericDeleteView(LoginRequiredMixin, DeleteView):
    template_name = 'generic_confirm_delete.html'
    
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
