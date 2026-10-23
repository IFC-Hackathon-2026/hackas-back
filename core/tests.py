from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from core.models import Categoria, ParticipacaoProjeto, Projeto, StatusTask, Task, User


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
