from django import forms
from django.contrib.auth import get_user_model
from model.models import Empresa, ResponsavelTecnico, TipoDocumento, NecessidadeDocumento, Documento

User = get_user_model()

class UserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        required=False,
        label="Senha",
        help_text="Deixe em branco para manter a senha atual se estiver editando."
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active', 'password']
        labels = {
            'username': 'Nome de Usuário',
            'first_name': 'Primeiro Nome',
            'last_name': 'Sobrenome',
            'email': 'E-mail',
            'is_staff': 'Acesso Administrativo (Staff)',
            'is_active': 'Ativo'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['password'].required = True

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class ResponsavelTecnicoForm(forms.ModelForm):
    empresas = forms.ModelMultipleChoiceField(
        queryset=Empresa.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Empresas sob sua Responsabilidade"
    )

    class Meta:
        model = ResponsavelTecnico
        fields = ['nome', 'cpf', 'conselho_classe', 'numero_registro', 'empresas']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Pre-populate the checkbox field with companies currently managed by this RT
            self.fields['empresas'].initial = self.instance.empresas.all()

    def save(self, commit=True):
        rt = super().save(commit=commit)
        if commit:
            # Selected companies in form
            selected_companies = list(self.cleaned_data.get('empresas', []))
            selected_ids = {e.id for e in selected_companies}

            # Reset responsavel_tecnico for companies previously assigned but not selected
            currently_assigned = list(rt.empresas.all())
            for empresa in currently_assigned:
                if empresa.id not in selected_ids:
                    empresa.responsavel_tecnico = None
                    empresa.save()

            # Set this responsavel_tecnico for selected companies
            for empresa in selected_companies:
                empresa.responsavel_tecnico = rt
                empresa.save()

        return rt


class NecessidadeDocumentoForm(forms.ModelForm):
    class Meta:
        model = NecessidadeDocumento
        fields = ['empresa', 'tipo_documento']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclude obligatory document types since they are already required for all companies
        self.fields['tipo_documento'].queryset = TipoDocumento.objects.filter(obrigatorio=False)


class DocumentoForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = ['empresa', 'tipo', 'responsavel_tecnico', 'data_emissao', 'data_vencimento', 'arquivo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter tipo queryset based on selected company (for validation and backend initialization)
        from django.db.models import Q
        if 'empresa' in self.data:
            try:
                empresa_id = int(self.data.get('empresa'))
                self.fields['tipo'].queryset = TipoDocumento.objects.filter(
                    Q(obrigatorio=True) | Q(necessidades_documento__empresa_id=empresa_id)
                ).distinct()
            except (ValueError, TypeError):
                self.fields['tipo'].queryset = TipoDocumento.objects.none()
        elif self.instance.pk and self.instance.empresa:
            self.fields['tipo'].queryset = TipoDocumento.objects.filter(
                Q(obrigatorio=True) | Q(necessidades_documento__empresa=self.instance.empresa)
            ).distinct()
        
        # Filter responsavel_tecnico queryset to only show RTs that are associated with the selected company (optional, but premium detail!)
        if 'empresa' in self.data:
            try:
                empresa_id = int(self.data.get('empresa'))
                self.fields['responsavel_tecnico'].queryset = ResponsavelTecnico.objects.filter(
                    empresas__id=empresa_id
                ).distinct()
            except (ValueError, TypeError):
                self.fields['responsavel_tecnico'].queryset = ResponsavelTecnico.objects.none()
        elif self.instance.pk and self.instance.empresa:
            self.fields['responsavel_tecnico'].queryset = ResponsavelTecnico.objects.filter(
                empresas=self.instance.empresa
            ).distinct()

