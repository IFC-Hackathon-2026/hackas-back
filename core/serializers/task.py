from django.utils import timezone
from rest_framework import serializers

from core.models import StatusTask, Task


class TaskListSerializer(serializers.ModelSerializer):
    situacao = serializers.ChoiceField(choices=Task.Situacao.choices, read_only=True)

    class Meta:
        model = Task
        fields = ('id', 'titulo', 'prioridade', 'criado_em', 'prazo', 'categoria', 'situacao')
        read_only_fields = fields


class TaskSerializer(serializers.ModelSerializer):
    atrasada = serializers.SerializerMethodField()
    situacao = serializers.ChoiceField(choices=Task.Situacao.choices, read_only=True)

    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['criado_por', 'criado_em', 'atualizado_em', 'concluido_em']
        extra_kwargs = {'status': {'required': False}}

    def get_atrasada(self, task):
        return task.situacao == Task.Situacao.ATRASADA

    def validate(self, dados):
        projeto = dados.get('projeto', getattr(self.instance, 'projeto', None))
        categorias = dados.get('categoria')
        responsaveis = dados.get('responsavel')
        if categorias is None:
            categorias = self.instance.categoria.all() if self.instance else []
        if responsaveis is None:
            responsaveis = self.instance.responsavel.all() if self.instance else []
        status = dados.get('status', getattr(self.instance, 'status', None))
        usuario = self.context['request'].user

        if not projeto.participantes.filter(id=usuario.id).exists():
            raise serializers.ValidationError('Você não participa deste projeto.')

        if any(categoria.projeto_id != projeto.id for categoria in categorias):
            raise serializers.ValidationError({'categoria': 'A categoria deve pertencer ao projeto da tarefa.'})

        participantes = set(projeto.participantes.values_list('id', flat=True))
        if any(responsavel.id not in participantes for responsavel in responsaveis):
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
