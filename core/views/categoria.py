from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from core.models import Categoria
from core.serializers import CategoriaSerializer


class CategoriaViewSet(ModelViewSet):
    serializer_class = CategoriaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        projeto_id = self.request.query_params.get('projeto')

        if not projeto_id:
            return Categoria.objects.none()

        return Categoria.objects.filter(
            projeto_id=projeto_id,
            projeto__participantes=self.request.user,
        )
