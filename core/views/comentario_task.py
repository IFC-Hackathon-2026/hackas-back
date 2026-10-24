from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from core.models import ComentarioTask
from core.serializers import ComentarioTaskSerializer


class ComentarioTaskViewSet(ModelViewSet):
    serializer_class = ComentarioTaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tarefa_id = self.request.query_params.get('tarefa')
        if not tarefa_id or not tarefa_id.isdigit():
            raise ValidationError({'tarefa': 'Informe uma tarefa válida.'})
        return ComentarioTask.objects.filter(
            tarefa_id=tarefa_id,
            tarefa__projeto__participantes=self.request.user,
        ).select_related('autor', 'autor__foto', 'tarefa')

    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)

    def _exigir_autor(self, comentario):
        if comentario.autor_id != self.request.user.id:
            raise PermissionDenied('Somente o autor pode alterar este comentário.')

    def perform_update(self, serializer):
        self._exigir_autor(serializer.instance)
        serializer.save()

    def perform_destroy(self, comentario):
        self._exigir_autor(comentario)
        comentario.delete()
