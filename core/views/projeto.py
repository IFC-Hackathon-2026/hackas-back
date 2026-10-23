from django.db import transaction
from rest_framework import filters
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from core.models import ParticipacaoProjeto, Projeto
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

    def destroy(self, request, *args, **kwargs):
        projeto = self.get_object()
        if projeto.criador_id != request.user.id:
            raise PermissionDenied('Somente o fundador pode excluir o projeto.')
        return super().destroy(request, *args, **kwargs)
