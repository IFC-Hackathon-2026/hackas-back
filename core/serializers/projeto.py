from rest_framework import serializers
from rest_framework.serializers import SlugRelatedField

from core.models import ParticipacaoProjeto, Projeto, User
from uploader.models import Image
from uploader.serializers import ImageSerializer


class UsuarioResumidoSerializer(serializers.ModelSerializer):
    foto = ImageSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'foto')
        read_only_fields = fields


class ParticipacaoProjetoSerializer(serializers.ModelSerializer):
    usuario = UsuarioResumidoSerializer(read_only=True)

    class Meta:
        model = ParticipacaoProjeto
        fields = ('id', 'usuario', 'cargo', 'entrou_em')
        read_only_fields = fields


class ProjetoSerializer(serializers.ModelSerializer):
    foto_attachment_key = SlugRelatedField(
        source='foto',
        queryset=Image.objects.all(),
        slug_field='attachment_key',
        required=False,
        allow_null=True,
        write_only=True,
    )
    foto = ImageSerializer(read_only=True)
    criador = UsuarioResumidoSerializer(read_only=True)
    participacoes = ParticipacaoProjetoSerializer(many=True, read_only=True)
    total_participantes = serializers.SerializerMethodField()
    meu_cargo = serializers.SerializerMethodField()

    class Meta:
        model = Projeto
        fields = (
            'id',
            'nome',
            'descricao',
            'foto',
            'foto_attachment_key',
            'criador',
            'participacoes',
            'total_participantes',
            'meu_cargo',
            'criado_em',
            'atualizado_em',
        )
        read_only_fields = ('criador', 'participacoes', 'criado_em', 'atualizado_em')

    def get_total_participantes(self, projeto):
        return projeto.participacoes.count()

    def get_meu_cargo(self, projeto):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None

        for participacao in projeto.participacoes.all():
            if participacao.usuario_id == request.user.id:
                return participacao.cargo
        return None
