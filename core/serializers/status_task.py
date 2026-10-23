from rest_framework import serializers

from core.models import StatusTask


class StatusTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusTask
        fields = '__all__'

    def validate_projeto(self, projeto):
        usuario = self.context['request'].user
        if not projeto.participantes.filter(id=usuario.id).exists():
            raise serializers.ValidationError('Você não participa deste projeto.')
        return projeto
