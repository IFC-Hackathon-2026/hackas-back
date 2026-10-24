from django.db import transaction
from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.models import PedidoParticipacao, ParticipacaoProjeto
from core.serializers import PedidoParticipacaoSerializer


class PedidoParticipacaoViewSet(ModelViewSet):
    serializer_class = PedidoParticipacaoSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        usuario = self.request.user
        queryset = PedidoParticipacao.objects.filter(
            Q(usuario=usuario)
            | Q(
                projeto__participacoes__usuario=usuario,
                projeto__participacoes__cargo__in=['fundador', 'organizador'],
            )
        ).select_related('projeto', 'usuario', 'criado_por').distinct()
        status_filtro = self.request.query_params.get('status')
        if status_filtro:
            queryset = queryset.filter(status=status_filtro)
        tipo = self.request.query_params.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        projeto = self.request.query_params.get('projeto')
        if projeto:
            queryset = queryset.filter(projeto_id=projeto)
        return queryset

    def _eh_organizador(self, projeto, usuario):
        return projeto.participacoes.filter(
            usuario=usuario,
            cargo__in=[ParticipacaoProjeto.Cargo.FUNDADOR, ParticipacaoProjeto.Cargo.ORGANIZADOR],
        ).exists()

    def perform_create(self, serializer):
        projeto = serializer.validated_data['projeto']
        usuario = serializer.validated_data.get('usuario', self.request.user)
        if projeto.participantes.filter(pk=usuario.pk).exists():
            raise ValidationError({'usuario': 'O usuário já participa deste projeto.'})
        if PedidoParticipacao.objects.filter(
            projeto=projeto, usuario=usuario, status=PedidoParticipacao.Status.PENDENTE,
        ).exists():
            raise ValidationError('Já existe um pedido pendente para este usuário e projeto.')

        if usuario == self.request.user:
            tipo = PedidoParticipacao.Tipo.SOLICITACAO
        else:
            if not self._eh_organizador(projeto, self.request.user):
                raise PermissionDenied('Somente organizadores podem convidar usuários.')
            tipo = PedidoParticipacao.Tipo.CONVITE
        serializer.save(usuario=usuario, criado_por=self.request.user, tipo=tipo)

    def _pode_decidir(self, pedido):
        if pedido.tipo == PedidoParticipacao.Tipo.CONVITE:
            return pedido.usuario_id == self.request.user.id
        return self._eh_organizador(pedido.projeto, self.request.user)

    def _decidir(self, pedido, novo_status):
        if pedido.status != PedidoParticipacao.Status.PENDENTE:
            raise ValidationError({'status': 'Este pedido já foi respondido.'})
        if not self._pode_decidir(pedido):
            raise PermissionDenied('Você não pode responder este pedido.')
        pedido.status = novo_status
        pedido.save(update_fields=['status', 'atualizado_em'])
        return pedido

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def aceitar(self, request, pk=None):
        pedido = self._decidir(self.get_object(), PedidoParticipacao.Status.ACEITO)
        ParticipacaoProjeto.objects.get_or_create(
            projeto=pedido.projeto,
            usuario=pedido.usuario,
            defaults={'cargo': ParticipacaoProjeto.Cargo.MEMBRO},
        )
        return Response(self.get_serializer(pedido).data)

    @action(detail=True, methods=['post'])
    def recusar(self, request, pk=None):
        pedido = self._decidir(self.get_object(), PedidoParticipacao.Status.RECUSADO)
        return Response(self.get_serializer(pedido).data)
