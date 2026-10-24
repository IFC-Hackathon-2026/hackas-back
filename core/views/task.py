from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import BooleanField, Case, Value, When
from django.utils import timezone
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
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
        if self.action in ('list', 'atrasadas'):
            return TaskListSerializer
        return TaskSerializer

    def get_queryset(self):
        projeto_id = self.request.query_params.get('projeto')
        if not projeto_id:
            return Task.objects.none()

        queryset = Task.objects.filter(
            projeto_id=projeto_id,
            projeto__participantes=self.request.user,
        )
        if self.request.query_params.get('atrasadas') == 'true':
            queryset = queryset.filter(
                prazo__lt=timezone.now(),
                concluido_em__isnull=True,
            )

        return queryset.annotate(
            atrasada_ordem=Case(
                When(prazo__lt=timezone.now(), concluido_em__isnull=True, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            ),
        ).order_by('-atrasada_ordem', 'prazo', '-criado_em')

    @action(detail=False, methods=['get'])
    def atrasadas(self, request):
        queryset = self.get_queryset().filter(
            prazo__lt=timezone.now(),
            concluido_em__isnull=True,
        )
        pagina = self.paginate_queryset(queryset)
        if pagina is not None:
            serializer = self.get_serializer(pagina, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(self.get_serializer(queryset, many=True).data)

    def perform_create(self, serializer):
        serializer.save(criado_por=self.request.user)
