from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, SlugRelatedField

from core.models import Documento, Task
from core.serializers.projeto import UsuarioResumidoSerializer
from uploader.models import Document
from uploader.serializers import DocumentSerializer


class TarefaDocumentoSerializer(ModelSerializer):
    class Meta:
        model = Task
        fields = ('id', 'titulo', 'projeto')
        read_only_fields = fields


class DocumentoSerializer(ModelSerializer):
    arquivo_attachment_key = SlugRelatedField(
        source='arquivo',
        queryset=Document.objects.all(),
        slug_field='attachment_key',
        write_only=True,
    )
    arquivo = DocumentSerializer(read_only=True)
    tarefa_origem = TarefaDocumentoSerializer(source='tarefa', read_only=True)
    enviado_por = UsuarioResumidoSerializer(read_only=True)

    class Meta:
        model = Documento
        fields = (
            'id',
            'nome',
            'tarefa',
            'tarefa_origem',
            'arquivo',
            'arquivo_attachment_key',
            'enviado_por',
            'criado_em',
        )
        read_only_fields = ('enviado_por', 'criado_em')
        extra_kwargs = {'tarefa': {'write_only': True, 'required': True}}

    def validate_tarefa(self, tarefa):
        usuario = self.context['request'].user
        if not tarefa.projeto.participantes.filter(id=usuario.id).exists():
            raise serializers.ValidationError('Você não participa do projeto desta tarefa.')
        return tarefa

    def validate_arquivo_attachment_key(self, arquivo):
        if hasattr(arquivo, 'documento'):
            raise serializers.ValidationError('Este arquivo já está vinculado a um documento.')
        return arquivo
