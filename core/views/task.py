from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from core.models import Task
from core.serializers import TaskSerializer


class TaskViewSet(ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['categoria', 'responsavel', 'status', 'prioridade']
    search_fields = ['titulo', 'descricao']
    ordering_fields = ['prazo', 'criado_em', 'atualizado_em']

    def get_queryset(self):
        projeto_id = self.request.query_params.get('projeto')
        if not projeto_id:
            return Task.objects.none()

        return Task.objects.filter(
            projeto_id=projeto_id,
            projeto__participantes=self.request.user,
        )

    def perform_create(self, serializer):
        serializer.save(criado_por=self.request.user)
