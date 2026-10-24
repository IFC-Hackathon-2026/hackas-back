from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models.categoria import Categoria
from core.models.projeto import Projeto
from core.models.status_task import StatusTask


class Task(models.Model):
    class Prioridade(models.TextChoices):
        BAIXA = 'baixa', 'Baixa'
        MEDIA = 'media', 'Média'
        ALTA = 'alta', 'Alta'
        URGENTE = 'urgente', 'Urgente'

    class Situacao(models.TextChoices):
        PENDENTE = 'pendente', 'Pendente'
        ATRASADA = 'atrasada', 'Atrasada'
        CONCLUIDA = 'concluida', 'Concluída'

    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='tasks')

    titulo = models.CharField(max_length=150)

    descricao = models.TextField(blank=True)

    categoria = models.ManyToManyField(
        Categoria,
        related_name='tasks',
        blank=True,
    )

    prioridade = models.CharField(max_length=10, choices=Prioridade.choices, default=Prioridade.MEDIA)

    status = models.ForeignKey(StatusTask, on_delete=models.PROTECT, related_name='tasks')

    prazo = models.DateTimeField(null=True, blank=True)

    responsavel = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='tasks_atribuidas',
        blank=True,
    )

    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='tasks_criadas',
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    atualizado_em = models.DateTimeField(auto_now=True)

    concluido_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-criado_em',)
        verbose_name = 'Tarefa'
        verbose_name_plural = 'Tarefas'

    def __str__(self):
        return self.titulo

    @property
    def situacao(self):
        if self.concluido_em:
            return self.Situacao.CONCLUIDA
        if self.prazo and self.prazo < timezone.now():
            return self.Situacao.ATRASADA
        return self.Situacao.PENDENTE
