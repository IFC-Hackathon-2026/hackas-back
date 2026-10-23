import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0006_user_foto'),
    ]

    operations = [
        migrations.CreateModel(
            name='Projeto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=150)),
                ('descricao', models.TextField(blank=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                (
                    'criador',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='projetos_criados',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'verbose_name': 'Projeto',
                'verbose_name_plural': 'Projetos',
                'ordering': ('-atualizado_em',),
            },
        ),
        migrations.CreateModel(
            name='ParticipacaoProjeto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'cargo',
                    models.CharField(
                        choices=[('fundador', 'Fundador'), ('organizador', 'Organizador'), ('membro', 'Membro')],
                        default='membro',
                        max_length=12,
                    ),
                ),
                ('entrou_em', models.DateTimeField(auto_now_add=True)),
                (
                    'projeto',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='participacoes',
                        to='core.projeto',
                    ),
                ),
                (
                    'usuario',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='participacoes_em_projetos',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'verbose_name': 'Participação em projeto',
                'verbose_name_plural': 'Participações em projetos',
                'ordering': ('entrou_em',),
            },
        ),
        migrations.AddField(
            model_name='projeto',
            name='participantes',
            field=models.ManyToManyField(
                related_name='projetos',
                through='core.ParticipacaoProjeto',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddConstraint(
            model_name='participacaoprojeto',
            constraint=models.UniqueConstraint(
                fields=('projeto', 'usuario'),
                name='participacao_unica_por_projeto',
            ),
        ),
    ]
