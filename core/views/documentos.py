from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from core.models import Documento, ParticipacaoProjeto
from core.serializers import DocumentoSerializer


class DocumentoViewSet(ModelViewSet):
    serializer_class = DocumentoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tarefa']
    search_fields = ['nome', 'tarefa__titulo']
    ordering_fields = ['nome', 'criado_em']

    def get_queryset(self):
        queryset = Documento.objects.filter(
            tarefa__projeto__participantes=self.request.user,
        ).select_related('tarefa__projeto', 'arquivo', 'enviado_por').distinct()

        projeto_id = self.request.query_params.get('projeto')
        if projeto_id:
            queryset = queryset.filter(tarefa__projeto_id=projeto_id)
        return queryset

    def perform_create(self, serializer):
        # A validação da tarefa garante que qualquer participante, inclusive membro,
        # possa anexar arquivos somente às tarefas dos seus projetos.
        serializer.save(enviado_por=self.request.user)

    def _pode_alterar(self, documento):
        if documento.enviado_por_id == self.request.user.id:
            return True
        return documento.tarefa.projeto.participacoes.filter(
            usuario=self.request.user,
            cargo__in=[
                ParticipacaoProjeto.Cargo.FUNDADOR,
                ParticipacaoProjeto.Cargo.ORGANIZADOR,
            ],
        ).exists()

    def perform_update(self, serializer):
        if not self._pode_alterar(self.get_object()):
            raise PermissionDenied('Somente o autor ou organizadores podem editar este documento.')
        serializer.save()

    def perform_destroy(self, instance):
        if not self._pode_alterar(instance):
            raise PermissionDenied('Somente o autor ou organizadores podem excluir este documento.')
        instance.delete()
