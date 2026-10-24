from rest_framework import mixins, parsers, viewsets
from rest_framework.permissions import IsAuthenticated

from uploader.models import Document, Image
from uploader.serializers import DocumentSerializer, DocumentUploadSerializer, ImageUploadSerializer


class CreateViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    pass


class DocumentUploadViewSet(mixins.RetrieveModelMixin, CreateViewSet):
    queryset = Document.objects.all()  # pylint: disable=no-member
    lookup_field = 'public_id'
    serializer_class = DocumentUploadSerializer
    parser_classes = [parsers.FormParser, parsers.MultiPartParser]
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return DocumentUploadSerializer
        return DocumentSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Document.objects.none()
        queryset = (
            Document.objects
            .filter(
                documento__tarefa__projeto__participantes=self.request.user,
            )
            .distinct()
            .order_by('-uploaded_on', 'pk')
        )
        projeto_id = self.request.query_params.get('projeto')
        if projeto_id:
            queryset = queryset.filter(documento__tarefa__projeto_id=projeto_id)
        return queryset


class ImageUploadViewSet(CreateViewSet):
    queryset = Image.objects.all()  # pylint: disable=no-member
    serializer_class = ImageUploadSerializer
    parser_classes = [parsers.FormParser, parsers.MultiPartParser]
    permission_classes = [IsAuthenticated]
