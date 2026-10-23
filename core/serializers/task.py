from django.utils import timezone
from rest_framework import serializers

from core.models import StatusTask, Task


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['criado_por', 'criado_em', 'atualizado_em', 'concluido_em']
        extra_kwargs = {'status': {'required': False}}

    def validate(self, dados):
        projeto = dados.get('projeto', getattr(self.instance, 'projeto', None))
        categoria = dados.get('categoria', getattr(self.instance, 'categoria', None))
        responsavel = dados.get('responsavel', getattr(self.instance, 'responsavel', None))
        status = dados.get('status', getattr(self.instance, 'status', None))
        usuario = self.context['request'].user

        if not projeto.participantes.filter(id=usuario.id).exists():
            raise serializers.ValidationError('Você não participa deste projeto.')

        if categoria and categoria.projeto_id != projeto.id:
            raise serializers.ValidationError({'categoria': 'A categoria deve pertencer ao projeto da tarefa.'})

        if responsavel and not projeto.participantes.filter(id=responsavel.id).exists():
            raise serializers.ValidationError({'responsavel': 'O responsável deve participar do projeto.'})

        if status and status.projeto_id != projeto.id:
            raise serializers.ValidationError({'status': 'O status deve pertencer ao projeto da tarefa.'})

        return dados

    def create(self, dados_validados):
        if not dados_validados.get('status'):
            dados_validados['status'] = StatusTask.objects.filter(
                projeto=dados_validados['projeto'],
            ).first()

        if not dados_validados['status']:
            raise serializers.ValidationError({'status': 'O projeto não possui status cadastrados.'})

        if dados_validados['status'].finaliza_task:
            dados_validados['concluido_em'] = timezone.now()
        return super().create(dados_validados)

    def update(self, task, dados_validados):
        novo_status = dados_validados.get('status', task.status)
        if novo_status.finaliza_task and not task.concluido_em:
            dados_validados['concluido_em'] = timezone.now()
        elif not novo_status.finaliza_task:
            dados_validados['concluido_em'] = None
        return super().update(task, dados_validados)
