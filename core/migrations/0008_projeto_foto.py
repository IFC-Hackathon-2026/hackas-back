import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0007_projeto_participacaoprojeto'),
        ('uploader', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='projeto',
            name='foto',
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='projetos',
                to='uploader.image',
            ),
        ),
    ]
