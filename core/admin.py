"""
Django admin customization.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from core import models


class UserAdmin(BaseUserAdmin):
    """Define the admin pages for users."""

    ordering = ('id',)
    list_display = ('email', 'name')
    search_fields = ('email', 'name', 'groups__name')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields': ('name', 'foto')}),
        (
            _('Permissions'),
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                )
            },
        ),
        (_('Important dates'), {'fields': ('last_login',)}),
        (_('Groups'), {'fields': ('groups',)}),
        (_('User Permissions'), {'fields': ('user_permissions',)}),
    )
    readonly_fields = ['last_login']
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'email',
                    'password1',
                    'password2',
                    'name',
                    'is_active',
                    'is_staff',
                    'is_superuser',
                ),
            },
        ),
    )


@admin.register(models.Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'projeto', 'cor')
    search_fields = ('nome', 'projeto__nome')


class ParticipacaoProjetoInline(admin.TabularInline):
    model = models.ParticipacaoProjeto
    extra = 0
    autocomplete_fields = ('usuario',)


@admin.register(models.Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'criador', 'criado_em', 'atualizado_em')
    list_filter = ('criado_em', 'atualizado_em')
    search_fields = ('nome', 'descricao', 'criador__name', 'criador__email')
    autocomplete_fields = ('criador',)
    inlines = (ParticipacaoProjetoInline,)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        projeto = form.instance
        if not change:
            models.ParticipacaoProjeto.objects.update_or_create(
                projeto=projeto,
                usuario=projeto.criador,
                defaults={'cargo': models.ParticipacaoProjeto.Cargo.FUNDADOR},
            )
            models.StatusTask.criar_status_padrao(projeto)


@admin.register(models.ParticipacaoProjeto)
class ParticipacaoProjetoAdmin(admin.ModelAdmin):
    list_display = ('projeto', 'usuario', 'cargo', 'entrou_em')
    list_filter = ('cargo', 'entrou_em')
    search_fields = ('projeto__nome', 'usuario__name', 'usuario__email')
    autocomplete_fields = ('projeto', 'usuario')


@admin.register(models.PedidoParticipacao)
class PedidoParticipacaoAdmin(admin.ModelAdmin):
    list_display = ('projeto', 'usuario', 'tipo', 'status', 'criado_em')
    list_filter = ('tipo', 'status')
    search_fields = ('projeto__nome', 'usuario__name', 'usuario__email')
    autocomplete_fields = ('projeto', 'usuario', 'criado_por')


@admin.register(models.Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'projeto', 'responsaveis', 'prioridade', 'status', 'prazo')
    list_filter = ('status', 'prioridade', 'categoria')
    search_fields = ('titulo', 'descricao', 'projeto__nome')
    autocomplete_fields = ('projeto', 'categoria', 'responsavel', 'criado_por')

    @admin.display(description='Responsáveis')
    def responsaveis(self, task):
        return ', '.join(usuario.name or usuario.email for usuario in task.responsavel.all()) or '-'

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('responsavel')


@admin.register(models.StatusTask)
class StatusTaskAdmin(admin.ModelAdmin):
    list_display = ('nome', 'projeto', 'ordem', 'cor', 'finaliza_task')
    list_filter = ('finaliza_task',)
    search_fields = ('nome', 'projeto__nome')


@admin.register(models.Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tarefa', 'enviado_por', 'criado_em')
    list_filter = ('criado_em', 'tarefa__projeto')
    search_fields = ('nome', 'tarefa__titulo', 'tarefa__projeto__nome')
    autocomplete_fields = ('tarefa', 'arquivo', 'enviado_por')


admin.site.register(models.User, UserAdmin)
