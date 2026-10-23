from django.db import models


class Documento(models.Model):
    nome = models.CharField(max_length=200)
    url = models.URLField()

    def __str__(self):
        return self.nome
