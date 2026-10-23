from django.conf import settings
from django.db import models

from uploader.models import Image


class Projeto(models.Model):
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    foto = models.ForeignKey(
        Image,
        related_name='projetos',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
    )
    criador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='projetos_criados',
    )
    participantes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ParticipacaoProjeto',
        related_name='projetos',
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-atualizado_em',)
        verbose_name = 'Projeto'
        verbose_name_plural = 'Projetos'

    def __str__(self):
        return self.nome


class ParticipacaoProjeto(models.Model):
    class Cargo(models.TextChoices):
        FUNDADOR = 'fundador', 'Fundador'
        ORGANIZADOR = 'organizador', 'Organizador'
        MEMBRO = 'membro', 'Membro'

    projeto = models.ForeignKey(
        Projeto,
        on_delete=models.CASCADE,
        related_name='participacoes',
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='participacoes_em_projetos',
    )
    cargo = models.CharField(max_length=12, choices=Cargo.choices, default=Cargo.MEMBRO)
    entrou_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('entrou_em',)
        constraints = [
            models.UniqueConstraint(
                fields=('projeto', 'usuario'),
                name='participacao_unica_por_projeto',
            ),
        ]
        verbose_name = 'Participação em projeto'
        verbose_name_plural = 'Participações em projetos'

    def __str__(self):
        return f'{self.usuario} em {self.projeto} ({self.get_cargo_display()})'
