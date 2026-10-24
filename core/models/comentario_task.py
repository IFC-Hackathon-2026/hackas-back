from django.conf import settings
from django.db import models

from core.models.task import Task


class ComentarioTask(models.Model):
    tarefa = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comentarios',
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='comentarios_em_tasks',
    )
    conteudo = models.TextField(max_length=5000)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('criado_em', 'id')
        verbose_name = 'Comentário de tarefa'
        verbose_name_plural = 'Comentários de tarefas'

    def __str__(self):
        return f'{self.autor} em {self.tarefa}'
