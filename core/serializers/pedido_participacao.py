from rest_framework import serializers

from core.models import PedidoParticipacao, Projeto, User
from core.serializers.projeto import UsuarioResumidoSerializer


class ProjetoPedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Projeto
        fields = ('id', 'nome')
        read_only_fields = fields


class PedidoParticipacaoSerializer(serializers.ModelSerializer):
    projeto_detalhe = ProjetoPedidoSerializer(source='projeto', read_only=True)
    usuario_detalhe = UsuarioResumidoSerializer(source='usuario', read_only=True)
    criado_por = UsuarioResumidoSerializer(read_only=True)
    usuario = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False,
    )

    class Meta:
        model = PedidoParticipacao
        fields = (
            'id', 'projeto', 'projeto_detalhe', 'usuario', 'usuario_detalhe',
            'criado_por', 'tipo', 'status', 'criado_em', 'atualizado_em',
        )
        read_only_fields = ('tipo', 'status', 'criado_por', 'criado_em', 'atualizado_em')
        # A unicidade pendente depende do usuário autenticado quando `usuario`
        # não é enviado e é validada no ViewSet.
        validators = []
