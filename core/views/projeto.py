from django.db import transaction
from django.db.models import Count, Q
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet

from core.models import (
    CATEGORIAS_EVENTO, CATEGORIAS_EVENTO_FILHAS, ParticipacaoProjeto, Projeto, StatusTask,
)
from core.serializers import ProjetoDestaqueSerializer, ProjetoSerializer


class ProjetoViewSet(ModelViewSet):
    serializer_class = ProjetoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['nome', 'descricao']

    def get_queryset(self):
        queryset = Projeto.objects.all()
        if self.request.query_params.get('meus') == 'true':
            queryset = queryset.filter(participantes=self.request.user)
        categorias = self.request.query_params.get('categorias')
        if categorias:
            recebidas = {item for item in categorias.split(',') if item}
            validas = {valor for valor, _ in CATEGORIAS_EVENTO} | set(CATEGORIAS_EVENTO_FILHAS)
            invalidas = recebidas - validas
            if invalidas:
                raise ValidationError({
                    'categorias': f"Filtros inválidos: {', '.join(sorted(invalidas))}.",
                })

            selecionadas = set(recebidas)
            pendentes = list(selecionadas)
            while pendentes:
                categoria = pendentes.pop()
                for filha in CATEGORIAS_EVENTO_FILHAS.get(categoria, ()):
                    if filha not in selecionadas:
                        selecionadas.add(filha)
                        pendentes.append(filha)

            filtro = Q()
            for categoria in selecionadas:
                filtro |= Q(categorias_evento__contains=f'|{categoria}|')
            queryset = queryset.filter(filtro)
        return queryset.distinct()

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[AllowAny],
        url_path='destaques',
    )
    def destaques(self, request):
        projetos = (
            Projeto.objects
            .annotate(total_participantes_anotado=Count('participacoes'))
            .order_by('-total_participantes_anotado', '-atualizado_em', 'id')[:3]
        )
        serializer = ProjetoDestaqueSerializer(
            projetos,
            many=True,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

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
