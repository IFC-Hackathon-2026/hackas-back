from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from core.models import ParticipacaoProjeto, PedidoParticipacao, Projeto, User


class PedidoDeleteTests(TestCase):
    def setUp(self):
        self.founder = User.objects.create_user(email='founder@example.com')
        self.candidate = User.objects.create_user(email='candidate@example.com')
        self.member = User.objects.create_user(email='member@example.com')
        self.organizer = User.objects.create_user(email='organizer@example.com')
        self.project = Projeto.objects.create(nome='Projeto', criador=self.founder)
        for user, role in (
            (self.founder, ParticipacaoProjeto.Cargo.FUNDADOR),
            (self.organizer, ParticipacaoProjeto.Cargo.ORGANIZADOR),
            (self.member, ParticipacaoProjeto.Cargo.MEMBRO),
        ):
            ParticipacaoProjeto.objects.create(projeto=self.project, usuario=user, cargo=role)
        self.client = APIClient()

    def create_request(self, request_status=PedidoParticipacao.Status.PENDENTE):
        return PedidoParticipacao.objects.create(
            projeto=self.project,
            usuario=self.candidate,
            criado_por=self.candidate,
            tipo=PedidoParticipacao.Tipo.SOLICITACAO,
            status=request_status,
        )

    def delete_request(self, request):
        return self.client.delete(f'/api/pedidos-participacao/{request.pk}/')

    def test_candidate_founder_and_organizer_can_delete(self):
        for user in (self.candidate, self.founder, self.organizer):
            with self.subTest(user=user.email):
                request = self.create_request()
                self.client.force_authenticate(user)
                assert self.delete_request(request).status_code == status.HTTP_204_NO_CONTENT
                assert not PedidoParticipacao.objects.filter(pk=request.pk).exists()

    def test_other_members_and_outsiders_cannot_delete(self):
        outsider = User.objects.create_user(email='outsider@example.com')
        request = self.create_request()
        for user in (self.member, outsider):
            with self.subTest(user=user.email):
                self.client.force_authenticate(user)
                assert self.delete_request(request).status_code == status.HTTP_404_NOT_FOUND
                assert PedidoParticipacao.objects.filter(pk=request.pk).exists()

    def test_authentication_is_required(self):
        request = self.create_request()
        assert self.delete_request(request).status_code == status.HTTP_401_UNAUTHORIZED
        assert PedidoParticipacao.objects.filter(pk=request.pk).exists()

    def test_deleting_accepted_request_preserves_membership(self):
        request = self.create_request(PedidoParticipacao.Status.ACEITO)
        membership = ParticipacaoProjeto.objects.create(
            projeto=self.project,
            usuario=self.candidate,
            cargo=ParticipacaoProjeto.Cargo.MEMBRO,
        )
        self.client.force_authenticate(self.candidate)
        assert self.delete_request(request).status_code == status.HTTP_204_NO_CONTENT
        assert ParticipacaoProjeto.objects.filter(pk=membership.pk).exists()
