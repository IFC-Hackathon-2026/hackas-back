from django.db import models

from core.models.projeto import Projeto


class Categoria(models.Model):
    nome = models.CharField(max_length=50)
    cor = models.CharField(max_length=7, default='#808080')
    projeto = models.ForeignKey(
        Projeto,
        on_delete=models.CASCADE,
        related_name='categorias',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['projeto', 'nome'],
                name='categoria_unica_por_projeto',
            )
        ]

    def __str__(self):
        return self.nome