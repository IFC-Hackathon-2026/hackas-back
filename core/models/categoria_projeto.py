from django.db import models


class CategoriaProjeto(models.Model):
    nome = models.CharField(max_length=80)
    categoria_pai = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='subcategorias',
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ('nome',)
        constraints = [
            models.UniqueConstraint(
                fields=('nome', 'categoria_pai'),
                name='categoria_projeto_unica_por_nivel',
            ),
        ]
        verbose_name = 'Categoria de projeto'
        verbose_name_plural = 'Categorias de projeto'

    def __str__(self):
        return self.nome
