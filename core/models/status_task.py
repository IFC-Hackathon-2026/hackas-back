from django.db import models

from core.models.projeto import Projeto


class StatusTask(models.Model):
    STATUS_PADRAO = (
        {'nome': 'A fazer', 'cor': '#E53D00', 'ordem': 1, 'finaliza_task': False},
        {'nome': 'Em andamento', 'cor': '#FFBE33', 'ordem': 2, 'finaliza_task': False},
        {'nome': 'Concluída', 'cor': '#429E5E', 'ordem': 3, 'finaliza_task': True},
    )

    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='status_tasks')
    nome = models.CharField(max_length=50)
    cor = models.CharField(max_length=7, default='#808080')
    ordem = models.PositiveSmallIntegerField(default=1)
    finaliza_task = models.BooleanField(default=False)

    class Meta:
        ordering = ('ordem',)
        constraints = [
            models.UniqueConstraint(
                fields=('projeto', 'nome'),
                name='status_unico_por_projeto',
            ),
        ]
        verbose_name = 'Status de tarefa'
        verbose_name_plural = 'Status de tarefas'

    def __str__(self):
        return self.nome

    @classmethod
    def criar_status_padrao(classe, projeto):
        for dados in classe.STATUS_PADRAO:
            classe.objects.get_or_create(projeto=projeto, nome=dados['nome'], defaults=dados)

    @classmethod
    def atualizar_status_final(classe, projeto):
        ultimo_status = (
            classe.objects
            .filter(projeto=projeto)
            .order_by('-ordem', '-pk')
            .first()
        )

        classe.objects.filter(projeto=projeto).update(
            finaliza_task=False
        )

        if ultimo_status:
            classe.objects.filter(pk=ultimo_status.pk).update(
                finaliza_task=True
            )
