from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import BooleanField, Case, Value, When
from django.utils import timezone
from rest_framework import filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from core.models import Task
from core.serializers import TaskListSerializer, TaskSerializer


class TaskViewSet(ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['categoria', 'responsavel', 'status', 'prioridade']
    search_fields = ['titulo', 'descricao']

    def get_serializer_class(self):
        if self.action == 'list':
            return TaskListSerializer
        return TaskSerializer

    def get_queryset(self):
        projeto_id = self.request.query_params.get('projeto')
        if not projeto_id:
            return Task.objects.none()

        return Task.objects.filter(
            projeto_id=projeto_id,
            projeto__participantes=self.request.user,
        ).annotate(
            atrasada_ordem=Case(
                When(prazo__lt=timezone.now(), concluido_em__isnull=True, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            ),
        ).order_by('-atrasada_ordem', 'prazo', '-criado_em')

    def perform_create(self, serializer):
        serializer.save(criado_por=self.request.user)
