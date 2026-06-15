from django.db import models
from django.contrib.auth.models import AbstractUser
import datetime
import calendar

def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return datetime.date(year, month, day)

class User(AbstractUser):
    # O C4 Model menciona UserModel com idUsuario, username, passwordHash
    # O AbstractUser do Django já possui id, username e password.

    class Meta(AbstractUser.Meta):
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

class Empresa(models.Model):
    cnpj = models.CharField(max_length=20, unique=True, verbose_name="CNPJ")
    razao_social = models.CharField(max_length=255, verbose_name="Razão Social")
    nome_fantasia = models.CharField(max_length=255, verbose_name="Nome Fantasia", blank=True, null=True)
    endereco = models.CharField(max_length=255, verbose_name="Endereço")
    telefone = models.CharField(max_length=20, verbose_name="Telefone", blank=True, null=True)
    email = models.EmailField(verbose_name="E-mail", blank=True, null=True)
    responsavel_tecnico = models.ForeignKey('ResponsavelTecnico', on_delete=models.SET_NULL, null=True, blank=True, related_name='empresas', verbose_name="Responsável Técnico")

    def __str__(self):
        return f"{self.razao_social} ({self.cnpj})"

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"

class ResponsavelTecnico(models.Model):
    nome = models.CharField(max_length=255, verbose_name="Nome Completo")
    cpf = models.CharField(max_length=11, unique=True, verbose_name="CPF")
    conselho_classe = models.CharField(max_length=50, verbose_name="Conselho de Classe (Ex: CRM, CRF)")
    numero_registro = models.CharField(max_length=50, verbose_name="Número de Registro")

    def __str__(self):
        return f"{self.nome} - {self.conselho_classe} {self.numero_registro}"

    class Meta:
        verbose_name = "Responsável Técnico"
        verbose_name_plural = "Responsáveis Técnicos"

class TipoDocumento(models.Model):
    descricao = models.CharField(max_length=100, verbose_name="Descrição")
    validade_meses = models.IntegerField(blank=True, null=True, verbose_name="Validade Padrão (meses)")
    obrigatorio = models.BooleanField(default=False, verbose_name="Obrigatório")

    def __str__(self):
        return self.descricao

    class Meta:
        verbose_name = "Tipo de Documento"
        verbose_name_plural = "Tipos de Documento"

class CategoriaVisita(models.Model):
    PRIORIDADE_CHOICES = [
        ('BAIXA', 'Baixa'),
        ('MEDIA', 'Média'),
        ('ALTA', 'Alta'),
    ]
    descricao = models.CharField(max_length=100, verbose_name="Descrição")
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE_CHOICES, default='MEDIA', verbose_name="Prioridade")

    def __str__(self):
        return f"{self.descricao} ({self.get_prioridade_display()})"

    class Meta:
        verbose_name = "Categoria de Visita"
        verbose_name_plural = "Categorias de Visita"

class Documento(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='documentos', verbose_name="Empresa")
    tipo = models.ForeignKey(TipoDocumento, on_delete=models.RESTRICT, related_name='documentos', verbose_name="Tipo de Documento")
    data_emissao = models.DateField(verbose_name="Data de Emissão")
    data_vencimento = models.DateField(blank=True, null=True, verbose_name="Data de Vencimento")
    arquivo = models.FileField(upload_to='documentos/', blank=True, null=True, verbose_name="Arquivo Anexo")
    responsavel_tecnico = models.ForeignKey('ResponsavelTecnico', on_delete=models.SET_NULL, null=True, blank=True, related_name='documentos', verbose_name="Responsável Técnico")

    def save(self, *args, **kwargs):
        if not self.data_vencimento and self.tipo.validade_meses and self.data_emissao:
            self.data_vencimento = add_months(self.data_emissao, self.tipo.validade_meses)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tipo.descricao} - {self.empresa.razao_social}"

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"

class Visita(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='visitas', verbose_name="Empresa")
    categoria = models.ForeignKey(CategoriaVisita, on_delete=models.RESTRICT, related_name='visitas', verbose_name="Categoria da Visita")
    fiscal = models.ForeignKey(User, on_delete=models.RESTRICT, related_name='visitas_realizadas', verbose_name="Fiscal Responsável")
    data_agendamento = models.DateTimeField(verbose_name="Data e Hora do Agendamento")
    data_realizacao = models.DateTimeField(blank=True, null=True, verbose_name="Data e Hora da Realização")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    realizada = models.BooleanField(default=False, verbose_name="Visita Realizada")
    responsavel_tecnico = models.ForeignKey('ResponsavelTecnico', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Responsável Técnico (Época)")

    def save(self, *args, **kwargs):
        if not self.responsavel_tecnico and self.empresa:
            self.responsavel_tecnico = self.empresa.responsavel_tecnico
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Visita: {self.empresa.razao_social} ({self.categoria.descricao})"

    class Meta:
        verbose_name = "Visita"
        verbose_name_plural = "Visitas"

class Colaborador(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='colaboradores', verbose_name="Empresa")
    nome = models.CharField(max_length=255, verbose_name="Nome do Colaborador")
    cpf = models.CharField(max_length=11, unique=True, verbose_name="CPF")
    data_entrada = models.DateField(verbose_name="Data de Entrada")
    data_vencimento = models.DateField(blank=True, null=True, verbose_name="Data de Vencimento (1 Ano)")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    def save(self, *args, **kwargs):
        if not self.data_vencimento and self.data_entrada:
            try:
                self.data_vencimento = self.data_entrada.replace(year=self.data_entrada.year + 1)
            except ValueError:
                self.data_vencimento = self.data_entrada + datetime.timedelta(days=365)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome} - {self.empresa.razao_social}"

    class Meta:
        verbose_name = "Colaborador"
        verbose_name_plural = "Colaboradores"

class NecessidadeDocumento(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='necessidades_documento', verbose_name="Empresa")
    tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.CASCADE, related_name='necessidades_documento', verbose_name="Tipo de Documento")

    def __str__(self):
        return f"{self.empresa.razao_social} - {self.tipo_documento.descricao}"

    class Meta:
        verbose_name = "Necessidade de Documento"
        verbose_name_plural = "Necessidades de Documentos"
        unique_together = ('empresa', 'tipo_documento')

class LogAuditoria(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Usuário")
    fk_registro = models.IntegerField(verbose_name="ID do Registro Afetado", blank=True, null=True)
    tipo = models.CharField(max_length=50, verbose_name="Tipo de Ação")
    data_hora = models.DateTimeField(auto_now_add=True, verbose_name="Data e Hora")
    descricao = models.TextField(verbose_name="Descrição")

    def __str__(self):
        return f"Log {self.id} - {self.tipo}"

    class Meta:
        verbose_name = "Log de Auditoria"
        verbose_name_plural = "Logs de Auditoria"
