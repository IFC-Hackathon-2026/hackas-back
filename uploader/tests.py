from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Documento, ParticipacaoProjeto, Projeto, StatusTask, Task, User
from uploader.models import Document


class DocumentReadTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='member@example.com')
        self.outsider = User.objects.create_user(email='outsider@example.com')
        self.project = Projeto.objects.create(nome='Projeto', criador=self.user)
        ParticipacaoProjeto.objects.create(projeto=self.project, usuario=self.user, cargo='fundador')
        status = StatusTask.objects.create(nome='Aberta', projeto=self.project)
        task = Task.objects.create(titulo='Tarefa', projeto=self.project, criado_por=self.user, status=status)
        self.document = Document.objects.create(file='documents/test.pdf', description='Documento')
        self.unattached = Document.objects.create(file='documents/unattached.pdf')
        Documento.objects.create(nome='Documento', tarefa=task, arquivo=self.document, enviado_por=self.user)
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.url = '/api/media/documents/'

    def test_member_can_list_and_retrieve_attached_document(self):
        response = self.client.get(self.url, {'projeto': self.project.pk})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert str(response.data['results'][0]['public_id']) == str(self.document.public_id)
        response = self.client.get(f'{self.url}{self.document.public_id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['url'] == self.document.url

    def test_unattached_document_is_hidden(self):
        response = self.client.get(f'{self.url}{self.unattached.public_id}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_outsider_cannot_read_documents(self):
        self.client.force_authenticate(self.outsider)
        assert self.client.get(self.url).data['count'] == 0
        assert self.client.get(f'{self.url}{self.document.public_id}/').status_code == status.HTTP_404_NOT_FOUND

    def test_authentication_is_required(self):
        self.client.force_authenticate(None)
        assert self.client.get(self.url).status_code == status.HTTP_401_UNAUTHORIZED

    def test_project_filter_is_applied(self):
        other = Projeto.objects.create(nome='Outro', criador=self.user)
        response = self.client.get(self.url, {'projeto': other.pk})
        assert response.data['count'] == 0
