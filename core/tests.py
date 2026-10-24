from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from core.models import Categoria, Documento, ParticipacaoProjeto, Projeto, StatusTask, Task, User
from uploader.models import Document


class ProjetoTaskApiTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(email='teste@example.com', password='teste12345')
        self.client = APIClient()
        self.client.force_authenticate(self.usuario)
        response = self.client.post('/api/projetos/', {'nome': 'Projeto teste'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.projeto = Projeto.objects.get(pk=response.data['id'])
        self.categoria = Categoria.objects.create(projeto=self.projeto, nome='Categoria')

    def criar_task(self):
        response = self.client.post('/api/tarefas/', {
            'projeto': self.projeto.pk,
            'titulo': 'Tarefa teste',
            'categoria': [self.categoria.pk],
            'responsavel': [self.usuario.pk],
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        return response.data['id']

    def test_criar_editar_e_concluir_task(self):
        task_id = self.criar_task()
        url = f'/api/tarefas/{task_id}/?projeto={self.projeto.pk}'
        response = self.client.patch(url, {'titulo': 'Editada'}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        status_final = self.projeto.status_tasks.get(finaliza_task=True)
        response = self.client.patch(url, {'status': status_final.pk}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIsNotNone(response.data['concluido_em'])

    def test_rejeitar_vinculos_de_outro_projeto(self):
        outro = Projeto.objects.create(nome='Outro', criador=self.usuario)
        categoria = Categoria.objects.create(projeto=outro, nome='Outra')
        terceiro = User.objects.create_user(email='terceiro@example.com')
        for campo, valor in [('categoria', [categoria.pk]), ('responsavel', [terceiro.pk])]:
            with self.subTest(campo=campo):
                response = self.client.post('/api/tarefas/', {
                    'projeto': self.projeto.pk, 'titulo': 'Inválida', campo: valor,
                }, format='json')
                self.assertEqual(response.status_code, 400, response.data)

    def test_excluir_projeto_com_tasks(self):
        self.criar_task()
        response = self.client.delete(f'/api/projetos/{self.projeto.pk}/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Task.objects.exists())
        self.assertFalse(StatusTask.objects.filter(projeto_id=self.projeto.pk).exists())
        self.assertFalse(ParticipacaoProjeto.objects.filter(projeto_id=self.projeto.pk).exists())

    def test_paginacao(self):
        response = self.client.get('/api/projetos/?meus=true')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)

    def test_fundador_promove_e_remove_participante(self):
        membro = User.objects.create_user(email='membro-projeto@example.com')
        response = self.client.post(
            f'/api/projetos/{self.projeto.pk}/participantes/',
            {'usuario': membro.pk, 'cargo': 'membro'}, format='json',
        )
        self.assertEqual(response.status_code, 201, response.data)
        participacao = ParticipacaoProjeto.objects.get(projeto=self.projeto, usuario=membro)
        url = f'/api/projetos/{self.projeto.pk}/participantes/{participacao.pk}/'
        response = self.client.patch(url, {'cargo': 'organizador'}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        participacao.refresh_from_db()
        self.assertEqual(participacao.cargo, ParticipacaoProjeto.Cargo.ORGANIZADOR)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204, response.data)
        self.assertFalse(ParticipacaoProjeto.objects.filter(pk=participacao.pk).exists())

        response = self.client.post(
            f'/api/projetos/{self.projeto.pk}/participantes/',
            {'usuario': membro.pk, 'cargo': 'membro'}, format='json',
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(ParticipacaoProjeto.objects.filter(
            projeto=self.projeto, usuario=membro, cargo=ParticipacaoProjeto.Cargo.MEMBRO,
        ).exists())

        response = self.client.post(
            f'/api/projetos/{self.projeto.pk}/participantes/',
            {'usuario': membro.pk, 'cargo': 'organizador'}, format='json',
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            ParticipacaoProjeto.objects.get(projeto=self.projeto, usuario=membro).cargo,
            ParticipacaoProjeto.Cargo.ORGANIZADOR,
        )

    def test_membro_nao_administra_participantes(self):
        membro = User.objects.create_user(email='sem-permissao@example.com')
        participacao = ParticipacaoProjeto.objects.create(
            projeto=self.projeto, usuario=membro, cargo=ParticipacaoProjeto.Cargo.MEMBRO,
        )
        self.client.force_authenticate(membro)
        response = self.client.patch(
            f'/api/projetos/{self.projeto.pk}/participantes/{participacao.pk}/',
            {'cargo': 'organizador'}, format='json',
        )
        self.assertEqual(response.status_code, 403, response.data)


class TaskMigrationTests(TransactionTestCase):
    def test_preservar_vinculos_ao_converter_para_many_to_many(self):
        anterior = [('core', '0013_merge_documento_status_task')]
        atual = [('core', '0014_remove_task_categoria_remove_task_responsavel_and_more')]
        executor = MigrationExecutor(connection)
        executor.migrate(anterior)
        try:
            apps = executor.loader.project_state(anterior).apps
            usuario = apps.get_model('core', 'User').objects.create(email='migracao@example.com')
            projeto = apps.get_model('core', 'Projeto').objects.create(nome='Migração', criador_id=usuario.pk)
            categoria = apps.get_model('core', 'Categoria').objects.create(nome='Categoria', projeto_id=projeto.pk)
            status = apps.get_model('core', 'StatusTask').objects.create(nome='A fazer', projeto_id=projeto.pk)
            task = apps.get_model('core', 'Task').objects.create(
                titulo='Preservar vínculos', projeto_id=projeto.pk, criado_por_id=usuario.pk,
                categoria_id=categoria.pk, responsavel_id=usuario.pk, status_id=status.pk,
            )
            MigrationExecutor(connection).migrate(atual)
            migrada = Task.objects.get(pk=task.pk)
            self.assertEqual(list(migrada.categoria.values_list('pk', flat=True)), [categoria.pk])
            self.assertEqual(list(migrada.responsavel.values_list('pk', flat=True)), [usuario.pk])
        finally:
            MigrationExecutor(connection).migrate(atual)


class DocumentoApiTests(TestCase):
    def setUp(self):
        self.fundador = User.objects.create_user(email='fundador@example.com')
        self.membro = User.objects.create_user(email='membro@example.com')
        self.visitante = User.objects.create_user(email='visitante@example.com')
        self.projeto = Projeto.objects.create(nome='Projeto', criador=self.fundador)
        ParticipacaoProjeto.objects.create(
            projeto=self.projeto,
            usuario=self.fundador,
            cargo=ParticipacaoProjeto.Cargo.FUNDADOR,
        )
        ParticipacaoProjeto.objects.create(
            projeto=self.projeto,
            usuario=self.membro,
            cargo=ParticipacaoProjeto.Cargo.MEMBRO,
        )
        status = StatusTask.objects.create(nome='A fazer', projeto=self.projeto)
        self.tarefa = Task.objects.create(
            titulo='Tarefa origem', projeto=self.projeto, criado_por=self.fundador, status=status,
        )
        self.arquivo = Document.objects.create(
            description='Arquivo',
            file=SimpleUploadedFile('arquivo.pdf', b'%PDF-1.4 teste', content_type='application/pdf'),
        )

    def test_membro_pode_criar_e_listar_documento_com_tarefa_origem(self):
        client = APIClient()
        client.force_authenticate(self.membro)
        response = client.post('/api/documentos/', {
            'nome': 'Requisitos',
            'tarefa': self.tarefa.pk,
            'arquivo_attachment_key': str(self.arquivo.attachment_key),
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['tarefa_origem']['id'], self.tarefa.pk)
        self.assertEqual(response.data['enviado_por']['id'], self.membro.pk)

        response = client.get(f'/api/documentos/?projeto={self.projeto.pk}&tarefa={self.tarefa.pk}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_membro_envia_pdf_e_cria_documento_em_uma_requisicao(self):
        client = APIClient()
        client.force_authenticate(self.membro)
        response = client.post('/api/documentos/', {
            'nome': 'Ata',
            'tarefa': self.tarefa.pk,
            'descricao_arquivo': 'Ata da reunião',
            'arquivo_upload': SimpleUploadedFile(
                'ata.pdf', b'%PDF-1.4 teste integrado', content_type='application/pdf',
            ),
        }, format='multipart')
        self.assertEqual(response.status_code, 201, response.data)
        documento = Documento.objects.get(pk=response.data['id'])
        self.assertEqual(documento.tarefa_id, self.tarefa.pk)
        self.assertEqual(documento.arquivo.description, 'Ata da reunião')
        self.assertEqual(documento.enviado_por_id, self.membro.pk)

    def test_usuario_de_fora_nao_acessa_nem_cria_documento(self):
        documento = Documento.objects.create(
            nome='Privado', tarefa=self.tarefa, arquivo=self.arquivo, enviado_por=self.membro,
        )
        client = APIClient()
        client.force_authenticate(self.visitante)
        response = client.get(f'/api/documentos/{documento.pk}/')
        self.assertEqual(response.status_code, 404)

        outro_arquivo = Document.objects.create(
            description='Outro',
            file=SimpleUploadedFile('outro.pdf', b'%PDF-1.4 outro', content_type='application/pdf'),
        )
        response = client.post('/api/documentos/', {
            'nome': 'Tentativa',
            'tarefa': self.tarefa.pk,
            'arquivo_attachment_key': str(outro_arquivo.attachment_key),
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_upload_nao_permite_listar_arquivos(self):
        client = APIClient()
        client.force_authenticate(self.membro)
        response = client.get('/api/media/documents/')
        self.assertEqual(response.status_code, 405)
