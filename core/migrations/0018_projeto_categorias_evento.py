from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0017_pedidoparticipacao'),
    ]

    operations = [
        migrations.AddField(
            model_name='projeto',
            name='categorias_evento',
            field=models.CharField(blank=True, default='', max_length=500),
        ),
    ]
