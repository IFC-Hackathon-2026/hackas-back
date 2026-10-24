from rest_framework import serializers

from core.models import ComentarioTask, Task
from core.serializers.projeto import UsuarioResumidoSerializer


class ComentarioTaskSerializer(serializers.ModelSerializer):
    autor = UsuarioResumidoSerializer(read_only=True)
    tarefa = serializers.PrimaryKeyRelatedField(queryset=Task.objects.all())

    class Meta:
        model = ComentarioTask
        fields = ('id', 'tarefa', 'autor', 'conteudo', 'criado_em', 'atualizado_em')
        read_only_fields = ('autor', 'criado_em', 'atualizado_em')

    def validate_conteudo(self, conteudo):
        conteudo = conteudo.strip()
        if not conteudo:
            raise serializers.ValidationError('Escreva um comentário.')
        return conteudo

    def validate_tarefa(self, tarefa):
        request = self.context['request']
        if not tarefa.projeto.participantes.filter(pk=request.user.pk).exists():
            raise serializers.ValidationError('Você não participa do projeto desta tarefa.')
        if self.instance and self.instance.tarefa_id != tarefa.pk:
            raise serializers.ValidationError('Não é possível mover um comentário para outra tarefa.')
        return tarefa
