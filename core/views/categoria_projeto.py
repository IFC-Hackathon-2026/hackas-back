from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from core.models import CategoriaProjeto
from core.serializers import CategoriaProjetoSerializer


class CategoriaProjetoViewSet(ReadOnlyModelViewSet):
    serializer_class = CategoriaProjetoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return CategoriaProjeto.objects.filter(categoria_pai__isnull=True).prefetch_related(
            'subcategorias',
        )
