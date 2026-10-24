from django.conf import settings
from django.db import models


class PedidoParticipacao(models.Model):
    class Tipo(models.TextChoices):
        SOLICITACAO = 'solicitacao', 'Solicitação de entrada'
        CONVITE = 'convite', 'Convite do projeto'

    class Status(models.TextChoices):
        PENDENTE = 'pendente', 'Pendente'
        ACEITO = 'aceito', 'Aceito'
        RECUSADO = 'recusado', 'Recusado'
        REMOVIDO = 'removido', 'Removido da equipe'

    projeto = models.ForeignKey('core.Projeto', on_delete=models.CASCADE, related_name='pedidos_participacao')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pedidos_participacao',
    )
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pedidos_participacao_criados',
    )
    tipo = models.CharField(max_length=12, choices=Tipo.choices)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDENTE)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-criado_em',)
        constraints = [
            models.UniqueConstraint(
                fields=('projeto', 'usuario'),
                condition=models.Q(status='pendente'),
                name='pedido_pendente_unico_por_projeto_usuario',
            ),
        ]

    def __str__(self):
        return f'{self.get_tipo_display()}: {self.usuario} - {self.projeto}'
