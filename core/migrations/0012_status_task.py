import django.db.models.deletion
from django.db import migrations, models


def criar_status_padrao(apps, schema_editor):
    Projeto = apps.get_model('core', 'Projeto')
    StatusTask = apps.get_model('core', 'StatusTask')
    Task = apps.get_model('core', 'Task')

    padroes = {
        'a_fazer': {'nome': 'A fazer', 'cor': '#6B7280', 'ordem': 1, 'finaliza_task': False},
        'em_andamento': {'nome': 'Em andamento', 'cor': '#3B82F6', 'ordem': 2, 'finaliza_task': False},
        'concluida': {'nome': 'Concluída', 'cor': '#22C55E', 'ordem': 3, 'finaliza_task': True},
    }

    for projeto in Projeto.objects.all():
        status_do_projeto = {}
        for chave, dados in padroes.items():
            status_do_projeto[chave] = StatusTask.objects.create(projeto=projeto, **dados)

        for task in Task.objects.filter(projeto=projeto):
            task.status = status_do_projeto[task.status_anterior]
            task.save(update_fields=('status',))


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0011_task'),
    ]

    operations = [
        migrations.RenameField(
            model_name='task',
            old_name='status',
            new_name='status_anterior',
        ),
        migrations.CreateModel(
            name='StatusTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=50)),
                ('cor', models.CharField(default='#808080', max_length=7)),
                ('ordem', models.PositiveSmallIntegerField(default=1)),
                ('finaliza_task', models.BooleanField(default=False)),
                (
                    'projeto',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='status_tasks',
                        to='core.projeto',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Status de tarefa',
                'verbose_name_plural': 'Status de tarefas',
                'ordering': ('ordem',),
                'constraints': [
                    models.UniqueConstraint(
                        fields=('projeto', 'nome'),
                        name='status_unico_por_projeto',
                    ),
                ],
            },
        ),
        migrations.AddField(
            model_name='task',
            name='status',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='tasks',
                to='core.statustask',
            ),
        ),
        migrations.RunPython(criar_status_padrao, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='task',
            name='status_anterior',
        ),
        migrations.AlterField(
            model_name='task',
            name='prioridade',
            field=models.CharField(
                choices=[
                    ('baixa', 'Baixa'),
                    ('media', 'Média'),
                    ('alta', 'Alta'),
                    ('urgente', 'Urgente'),
                ],
                default='media',
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name='task',
            name='status',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='tasks',
                to='core.statustask',
            ),
        ),
    ]
