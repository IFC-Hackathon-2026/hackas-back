from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Documento, ParticipacaoProjeto, Projeto, StatusTask, Task, User
from uploader.models import Document


class DocumentLinkTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='links@example.com')
        project = Projeto.objects.create(nome='Projeto', criador=self.user)
        ParticipacaoProjeto.objects.create(projeto=project, usuario=self.user, cargo='fundador')
        task_status = StatusTask.objects.create(nome='Aberta', projeto=project)
        self.task = Task.objects.create(titulo='Tarefa', projeto=project, criado_por=self.user, status=task_status)
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.payload = {'nome': 'Referência', 'tarefa': self.task.pk, 'url': 'https://example.com/documento'}

    def test_create_list_and_update_external_link(self):
        response = self.client.post('/api/documentos/', self.payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED, response.data
        document = Documento.objects.get(pk=response.data['id'])
        assert document.url == self.payload['url']
        assert document.arquivo is None
        assert response.data['arquivo'] is None
        response = self.client.get('/api/documentos/')
        assert response.data['results'][0]['url'] == self.payload['url']
        response = self.client.patch(
            f'/api/documentos/{document.pk}/',
            {'url': 'https://example.com/novo'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        document.refresh_from_db()
        assert document.url == 'https://example.com/novo'

    def test_invalid_or_missing_source_is_rejected(self):
        for url in ('', 'isto nao e um link'):
            with self.subTest(url=url):
                response = self.client.post('/api/documentos/', {**self.payload, 'url': url}, format='json')
                assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_link_and_pdf_cannot_be_combined(self):
        file = Document.objects.create(file='documents/test.pdf')
        response = self.client.post(
            '/api/documentos/',
            {**self.payload, 'arquivo_attachment_key': str(file.attachment_key)},
            format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_nonparticipant_cannot_add_link(self):
        outsider = User.objects.create_user(email='outside@example.com')
        self.client.force_authenticate(outsider)
        response = self.client.post('/api/documentos/', self.payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
