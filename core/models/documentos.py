from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models.task import Task
from uploader.models import Document


class Documento(models.Model):
    nome = models.CharField(max_length=200)
    # Mantidos opcionais para que registros legados não bloqueiem a migração.
    tarefa = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='documentos',
        null=True,
        blank=True,
    )
    arquivo = models.OneToOneField(
        Document,
        on_delete=models.PROTECT,
        related_name='documento',
        null=True,
        blank=True,
    )
    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='documentos_enviados',
        null=True,
        blank=True,
    )
    url = models.URLField(blank=True)
    criado_em = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ('-criado_em',)

    def __str__(self):
        return self.nome
