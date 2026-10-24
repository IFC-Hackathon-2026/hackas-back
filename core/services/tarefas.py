from django.db.models import Count, Q
from django.utils import timezone


def resumo_tarefas(queryset):
    resumo = queryset.aggregate(
        total=Count('id', distinct=True),
        concluidas=Count('id', filter=Q(concluido_em__isnull=False), distinct=True),
        nao_concluidas=Count('id', filter=Q(concluido_em__isnull=True), distinct=True),
        atrasadas=Count(
            'id',
            filter=Q(concluido_em__isnull=True, prazo__lt=timezone.now()),
            distinct=True,
        ),
    )
    resumo['progresso'] = round(
        resumo['concluidas'] * 100 / resumo['total']
    ) if resumo['total'] else 0
    return resumo


def desempenho_participantes(projeto):
    return projeto.participantes.select_related('foto').annotate(
        tarefas_concluidas=Count(
            'tasks_atribuidas',
            filter=Q(
                tasks_atribuidas__projeto=projeto,
                tasks_atribuidas__concluido_em__isnull=False,
            ),
            distinct=True,
        ),
        tarefas_atrasadas=Count(
            'tasks_atribuidas',
            filter=Q(
                tasks_atribuidas__projeto=projeto,
                tasks_atribuidas__concluido_em__isnull=True,
                tasks_atribuidas__prazo__lt=timezone.now(),
            ),
            distinct=True,
        ),
    ).order_by('name', 'email')
