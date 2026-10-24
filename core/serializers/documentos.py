from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, SlugRelatedField

from core.models import Documento, Task
from core.serializers.projeto import UsuarioResumidoSerializer
from uploader.helpers.files import CONTENT_TYPE_PDF, get_content_type
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
        required=False,
    )
    arquivo_upload = serializers.FileField(write_only=True, required=False)
    descricao_arquivo = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        max_length=255,
    )
    arquivo = DocumentSerializer(read_only=True)
    tarefa_origem = TarefaDocumentoSerializer(source='tarefa', read_only=True)
    enviado_por = UsuarioResumidoSerializer(read_only=True)

    class Meta:
        model = Documento
        fields = (
            'id',
            'nome',
            'url',
            'tarefa',
            'tarefa_origem',
            'arquivo',
            'arquivo_attachment_key',
            'arquivo_upload',
            'descricao_arquivo',
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

    def validate_arquivo_upload(self, arquivo):
        if get_content_type(arquivo) != CONTENT_TYPE_PDF:
            raise serializers.ValidationError('Envie um arquivo PDF válido.')
        return arquivo

    def validate(self, attrs):
        if self.instance is None:
            possui_upload = attrs.get('arquivo_upload') is not None
            possui_arquivo = attrs.get('arquivo') is not None
            possui_link = bool(attrs.get('url'))
            if sum((possui_upload, possui_arquivo, possui_link)) != 1:
                raise serializers.ValidationError(
                    'Informe exatamente uma opção: url, arquivo_upload ou arquivo_attachment_key.'
                )
        elif 'url' in attrs or 'arquivo' in attrs:
            arquivo = attrs.get('arquivo', self.instance.arquivo)
            if bool(attrs.get('url', self.instance.url)) == bool(arquivo):
                raise serializers.ValidationError('Informe um link externo ou um arquivo, nunca ambos.')
        return attrs

    def create(self, validated_data):
        arquivo_upload = validated_data.pop('arquivo_upload', None)
        descricao = validated_data.pop('descricao_arquivo', '')
        if arquivo_upload is not None:
            validated_data['arquivo'] = Document.objects.create(
                file=arquivo_upload,
                description=descricao,
            )
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # A troca do arquivo não faz parte da edição dos metadados do documento.
        validated_data.pop('arquivo_upload', None)
        validated_data.pop('descricao_arquivo', None)
        return super().update(instance, validated_data)
