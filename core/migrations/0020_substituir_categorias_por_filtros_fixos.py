from django.db import migrations, models


VALORES_POR_NOME = {
    'Educacionais e Profissionais': ('academicos', 'workshops', 'palestras'),
    'Acadêmicos': ('academicos',),
    'Workshops': ('workshops',),
    'Palestras': ('palestras',),
    'Culturais': ('culturais',),
    'Esportivos': ('esportivos',),
}


def converter_categorias(apps, schema_editor):
    Projeto = apps.get_model('core', 'Projeto')
    for projeto in Projeto.objects.prefetch_related('categorias_projeto'):
        valores = [
            valor
            for categoria in projeto.categorias_projeto.all()
            if categoria.nome in VALORES_POR_NOME
            for valor in VALORES_POR_NOME[categoria.nome]
        ]
        projeto.categorias_evento = f"|{'|'.join(dict.fromkeys(valores))}|" if valores else ''
        projeto.save(update_fields=['categorias_evento'])


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0019_categoriaprojeto_projeto_categorias'),
    ]

    operations = [
        migrations.AddField(
            model_name='projeto',
            name='categorias_evento',
            field=models.CharField(blank=True, default='', max_length=500),
        ),
        migrations.RunPython(converter_categorias, migrations.RunPython.noop),
        migrations.RemoveField(model_name='projeto', name='categorias_projeto'),
        migrations.DeleteModel(name='CategoriaProjeto'),
    ]
