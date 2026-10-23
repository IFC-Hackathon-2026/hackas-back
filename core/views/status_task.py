from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from core.models import StatusTask
from core.serializers import StatusTaskSerializer


class StatusTaskViewSet(ModelViewSet):
    serializer_class = StatusTaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        projeto_id = self.request.query_params.get('projeto')
        if not projeto_id:
            return StatusTask.objects.none()

        return StatusTask.objects.filter(
            projeto_id=projeto_id,
            projeto__participantes=self.request.user,
        )

    def perform_destroy(self, instance):
        if instance.tasks.exists():
            raise ValidationError('Não é possível excluir um status que possui tarefas.')
        instance.delete()
