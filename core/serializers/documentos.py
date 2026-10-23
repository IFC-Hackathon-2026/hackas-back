from rest_framework.serializers import ModelSerializer

from core.models import Documento


class DocumentoSerializer(ModelSerializer):
    class Meta:
        model = Documento
        fields = '__all__'
