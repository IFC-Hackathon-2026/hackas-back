import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0010_categoria_categoria_unica_por_projeto'),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=150)),
                ('descricao', models.TextField(blank=True)),
                (
                    'prioridade',
                    models.CharField(
                        choices=[('baixa', 'Baixa'), ('media', 'Média'), ('alta', 'Alta')],
                        default='media',
                        max_length=10,
                    ),
                ),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('a_fazer', 'A fazer'),
                            ('em_andamento', 'Em andamento'),
                            ('concluida', 'Concluída'),
                        ],
                        default='a_fazer',
                        max_length=15,
                    ),
                ),
                ('prazo', models.DateTimeField(blank=True, null=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('concluido_em', models.DateTimeField(blank=True, null=True)),
                (
                    'categoria',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='tasks',
                        to='core.categoria',
                    ),
                ),
                (
                    'criado_por',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='tasks_criadas',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'projeto',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='tasks',
                        to='core.projeto',
                    ),
                ),
                (
                    'responsavel',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='tasks_atribuidas',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'verbose_name': 'Tarefa',
                'verbose_name_plural': 'Tarefas',
                'ordering': ('-criado_em',),
            },
        ),
    ]
