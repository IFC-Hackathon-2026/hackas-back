from rest_framework import serializers

from core.models import CategoriaProjeto


class CategoriaProjetoSerializer(serializers.ModelSerializer):
    subcategorias = serializers.SerializerMethodField()

    class Meta:
        model = CategoriaProjeto
        fields = ('id', 'nome', 'categoria_pai', 'subcategorias')
        read_only_fields = fields

    def get_subcategorias(self, categoria):
        return CategoriaProjetoSerializer(categoria.subcategorias.all(), many=True).data
