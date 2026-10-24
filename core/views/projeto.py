from django.db import transaction
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet

from core.models import ParticipacaoProjeto, Projeto, StatusTask, User
from core.serializers import ProjetoSerializer


class ProjetoViewSet(ModelViewSet):
    serializer_class = ProjetoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['nome', 'descricao']

    def get_queryset(self):
        queryset = Projeto.objects.all()
        if self.request.query_params.get('meus') == 'true':
            queryset = queryset.filter(participantes=self.request.user)
        return queryset

    @transaction.atomic
    def perform_create(self, serializer):
        projeto = serializer.save(criador=self.request.user)
        ParticipacaoProjeto.objects.create(
            projeto=projeto,
            usuario=self.request.user,
            cargo=ParticipacaoProjeto.Cargo.FUNDADOR,
        )
        StatusTask.criar_status_padrao(projeto)

    def update(self, request, *args, **kwargs):
        projeto = self.get_object()
        pode_editar = projeto.participacoes.filter(
            usuario=request.user,
            cargo__in=[
                ParticipacaoProjeto.Cargo.FUNDADOR,
                ParticipacaoProjeto.Cargo.ORGANIZADOR,
            ],
        ).exists()

        if not pode_editar:
            raise PermissionDenied('Somente organizadores podem editar o projeto.')

        return super().update(request, *args, **kwargs)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        projeto = self.get_object()
        if projeto.criador_id != request.user.id:
            raise PermissionDenied('Somente o fundador pode excluir o projeto.')
        # As tarefas protegem seus status; exclua-as antes da cascata do projeto.
        projeto.tasks.all().delete()
        return super().destroy(request, *args, **kwargs)

    def _exigir_fundador(self, projeto):
        if projeto.criador_id != self.request.user.id:
            raise PermissionDenied('Somente o fundador pode administrar participantes.')

    @action(detail=True, methods=['post'], url_path='participantes')
    def adicionar_participante(self, request, pk=None):
        projeto = self.get_object()
        self._exigir_fundador(projeto)
        usuario_id = request.data.get('usuario')
        try:
            usuario = User.objects.get(pk=usuario_id)
        except (User.DoesNotExist, ValueError, TypeError) as exc:
            raise ValidationError({'usuario': 'Usuário não encontrado.'}) from exc

        cargo = request.data.get('cargo', ParticipacaoProjeto.Cargo.MEMBRO)
        if cargo not in {
            ParticipacaoProjeto.Cargo.MEMBRO,
            ParticipacaoProjeto.Cargo.ORGANIZADOR,
        }:
            raise ValidationError({'cargo': 'Use membro ou organizador.'})
        if usuario.id == projeto.criador_id:
            raise ValidationError({'usuario': 'O fundador já participa do projeto.'})
        participacao, criada = ParticipacaoProjeto.objects.update_or_create(
            projeto=projeto,
            usuario=usuario,
            defaults={'cargo': cargo},
        )
        projeto.refresh_from_db()
        resposta_status = status.HTTP_201_CREATED if criada else status.HTTP_200_OK
        return Response(self.get_serializer(projeto).data, status=resposta_status)

    @action(
        detail=True,
        methods=['patch', 'delete'],
        url_path=r'participantes/(?P<participacao_id>[^/.]+)',
    )
    def participante(self, request, pk=None, participacao_id=None):
        projeto = self.get_object()
        self._exigir_fundador(projeto)
        try:
            participacao = projeto.participacoes.select_related('usuario').get(pk=participacao_id)
        except ParticipacaoProjeto.DoesNotExist as exc:
            raise ValidationError({'participacao': 'Participante não encontrado neste projeto.'}) from exc

        if participacao.usuario_id == projeto.criador_id:
            raise ValidationError({'participacao': 'O fundador não pode ser alterado ou removido.'})

        if request.method == 'DELETE':
            participacao.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        cargo = request.data.get('cargo')
        cargos_permitidos = {
            ParticipacaoProjeto.Cargo.MEMBRO,
            ParticipacaoProjeto.Cargo.ORGANIZADOR,
        }
        if cargo not in cargos_permitidos:
            raise ValidationError({'cargo': 'Use membro ou organizador.'})
        participacao.cargo = cargo
        participacao.save(update_fields=['cargo'])
        projeto.refresh_from_db()
        return Response(self.get_serializer(projeto).data)
