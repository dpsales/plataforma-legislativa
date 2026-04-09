from django.db import models
from django.utils import timezone


class ProcessoSEI(models.Model):
    """
    Model para armazenar informações de processos consultados no SEI
    """
    numero_processo = models.CharField(max_length=50, unique=True, db_index=True)
    assunto = models.CharField(max_length=500, blank=True, null=True)
    interessado = models.CharField(max_length=500, blank=True, null=True)
    secao = models.CharField(max_length=200, blank=True, null=True)
    data_criacao_processo = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=100, blank=True, null=True)
    
    data_consulta = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    dados_brutos = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ["-data_consulta"]
        verbose_name = "Processo SEI"
        verbose_name_plural = "Processos SEI"
    
    def __str__(self):
        return f"{self.numero_processo} - {self.assunto}"


class AndamentoProcesso(models.Model):
    """
    Model para armazenar o histórico de andamentos de um processo
    """
    processo = models.ForeignKey(ProcessoSEI, on_delete=models.CASCADE, related_name="andamentos")
    
    data_andamento = models.DateField(blank=True, null=True)
    tipo_movimentacao = models.CharField(max_length=300, blank=True, null=True)
    descricao = models.TextField(blank=True, null=True)
    responsavel = models.CharField(max_length=200, blank=True, null=True)
    setor = models.CharField(max_length=200, blank=True, null=True)
    
    data_insercao = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-data_andamento"]
        verbose_name = "Andamento de Processo"
        verbose_name_plural = "Andamentos de Processos"
    
    def __str__(self):
        return f"{self.processo.numero_processo} - {self.tipo_movimentacao}"


class DocumentoProcesso(models.Model):
    """
    Model para armazenar referências aos documentos do processo
    """
    processo = models.ForeignKey(ProcessoSEI, on_delete=models.CASCADE, related_name="documentos")
    
    numero_documento = models.CharField(max_length=50, blank=True, null=True)
    tipo_documento = models.CharField(max_length=200, blank=True, null=True)
    descricao = models.TextField(blank=True, null=True)
    data_documento = models.DateField(blank=True, null=True)
    url_documento = models.URLField(blank=True, null=True)
    arquivo = models.FileField(upload_to='documentos_sei/', blank=True, null=True)
    
    data_insercao = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-data_documento"]
        verbose_name = "Documento do Processo"
        verbose_name_plural = "Documentos dos Processos"
    
    def __str__(self):
        return f"{self.numero_documento} - {self.tipo_documento}"
