import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0020_substituir_categorias_por_filtros_fixos'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ComentarioTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('conteudo', models.TextField(max_length=5000)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('autor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='comentarios_em_tasks', to=settings.AUTH_USER_MODEL)),
                ('tarefa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comentarios', to='core.task')),
            ],
            options={
                'verbose_name': 'Comentário de tarefa',
                'verbose_name_plural': 'Comentários de tarefas',
                'ordering': ('criado_em', 'id'),
            },
        ),
    ]
