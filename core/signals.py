from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from core.models import PedidoParticipacao, ParticipacaoProjeto


@receiver(post_save, sender=ParticipacaoProjeto)
def aceitar_pedido_ao_entrar_na_equipe(sender, instance, created, **kwargs):
    if created:
        PedidoParticipacao.objects.filter(
            projeto_id=instance.projeto_id,
            usuario_id=instance.usuario_id,
            status=PedidoParticipacao.Status.PENDENTE,
        ).update(status=PedidoParticipacao.Status.ACEITO)


@receiver(post_delete, sender=ParticipacaoProjeto)
def remover_pedido_ao_sair_da_equipe(sender, instance, **kwargs):
    PedidoParticipacao.objects.filter(
        projeto_id=instance.projeto_id,
        usuario_id=instance.usuario_id,
        status__in=[PedidoParticipacao.Status.PENDENTE, PedidoParticipacao.Status.ACEITO],
    ).update(status=PedidoParticipacao.Status.REMOVIDO)
