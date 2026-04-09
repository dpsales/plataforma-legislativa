from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from datetime import timedelta, date
from django.db.models import Q

from .models import EventoLegislativo, AtualizacaoProposicao, AgendaFavorita
from .services import CamaraEventosCollector, SenadoEventosCollector


class AgendaSemanalView(LoginRequiredMixin, TemplateView):
    """Exibe agenda consolidada da semana anterior."""
    
    template_name = 'agenda/semanal.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calcular período (semana anterior)
        hoje = timezone.now().date()
        data_inicio = hoje - timedelta(days=hoje.weekday() + 7)  # Segunda semana anterior
        data_fim = data_inicio + timedelta(days=6)  # Domingo semana anterior
        
        # Eventos Câmara
        eventos_camara = EventoLegislativo.objects.filter(
            casa='Câmara',
            data_evento__gte=data_inicio,
            data_evento__lte=data_fim
        ).order_by('data_evento', 'hora_inicio')
        
        # Eventos Senado
        eventos_senado = EventoLegislativo.objects.filter(
            casa='Senado',
            data_evento__gte=data_inicio,
            data_evento__lte=data_fim
        ).order_by('data_evento', 'hora_inicio')
        
        # Atualizações de proposições
        atualizacoes = AtualizacaoProposicao.obter_atualizacoes_semana_anterior()
        
        # Filtros do usuário
        casa_filter = self.request.GET.get('casa')
        tipo_filter = self.request.GET.get('tipo')
        comissao_filter = self.request.GET.get('comissao')
        
        # Aplicar filtros
        if casa_filter:
            if casa_filter == 'Câmara':
                eventos_camara = eventos_camara.filter(casa='Câmara')
                eventos_senado = EventoLegislativo.objects.none()
            elif casa_filter == 'Senado':
                eventos_senado = eventos_senado.filter(casa='Senado')
                eventos_camara = EventoLegislativo.objects.none()
        
        if tipo_filter:
            eventos_camara = eventos_camara.filter(tipo=tipo_filter)
            eventos_senado = eventos_senado.filter(tipo=tipo_filter)
        
        if comissao_filter:
            eventos_senado = eventos_senado.filter(
                Q(comissao__icontains=comissao_filter) |
                Q(local__icontains=comissao_filter)
            )
        
        # Estatísticas
        context.update({
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'periodo': f"{data_inicio.strftime('%d/%m')} a {data_fim.strftime('%d/%m/%Y')}",
            
            'eventos_camara': eventos_camara,
            'total_camara': eventos_camara.count(),
            
            'eventos_senado': eventos_senado,
            'total_senado': eventos_senado.count(),
            
            'atualizacoes': atualizacoes,
            'total_atualizacoes': atualizacoes.count(),
            
            'tipos': EventoLegislativo.TIPOS_EVENTO,
            'casas': [('Câmara', 'Câmara'), ('Senado', 'Senado')],
            
            'favoritos': self.request.user.comissoes_favoritas.all() if self.request.user.is_authenticated else [],
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        """POST: Sincronizar/atualizar agenda."""
        
        acao = request.POST.get('acao')
        
        if acao == 'sincronizar_camara':
            # Buscar e salvar eventos Câmara
            hoje = timezone.now().date()
            data_inicio = hoje - timedelta(days=hoje.weekday() + 7)
            data_fim = data_inicio + timedelta(days=6)
            
            eventos = CamaraEventosCollector.buscar_eventos_api(data_inicio, data_fim)
            criados = 0
            for evt in eventos:
                evento_obj, created = CamaraEventosCollector.salvar_evento(evt)
                if created:
                    criados += 1
            
            context = self.get_context_data(**kwargs)
            context['mensagem'] = f"✅ {criados} eventos da Câmara sincronizados"
            return render(request, self.template_name, context)
        
        elif acao == 'sincronizar_senado_comissoes':
            # Buscar e salvar eventos Senado (Comissões)
            hoje = timezone.now().date()
            data_inicio = hoje - timedelta(days=hoje.weekday() + 7)
            data_fim = data_inicio + timedelta(days=6)
            
            data = SenadoEventosCollector.buscar_eventos_comissoes(data_inicio, data_fim)
            eventos = SenadoEventosCollector.processar_comissoes(data)
            
            criados = 0
            for evt in eventos:
                evento_obj, created = SenadoEventosCollector.salvar_evento_senado(evt, 'COMISSAO')
                if created:
                    criados += 1
            
            context = self.get_context_data(**kwargs)
            context['mensagem'] = f"✅ {criados} comissões do Senado sincronizadas"
            return render(request, self.template_name, context)
        
        elif acao == 'sincronizar_senado_plenario':
            # Buscar e salvar eventos Senado (Plenário)
            hoje = timezone.now().date()
            data_inicio = hoje - timedelta(days=hoje.weekday() + 7)
            data_fim = data_inicio + timedelta(days=6)
            
            data = SenadoEventosCollector.buscar_eventos_plenario(data_inicio, data_fim)
            eventos = SenadoEventosCollector.processar_plenario(data)
            
            criados = 0
            for evt in eventos:
                evento_obj, created = SenadoEventosCollector.salvar_evento_senado(evt, 'PLENARIO')
                if created:
                    criados += 1
            
            context = self.get_context_data(**kwargs)
            context['mensagem'] = f"✅ {criados} sessões plenárias do Senado sincronizadas"
            return render(request, self.template_name, context)
        
        return super().get(request, *args, **kwargs)


class AdicionarFavoritoView(LoginRequiredMixin, TemplateView):
    """Adiciona comissão aos favoritos do usuário."""
    
    template_name = 'agenda/favorito_adicionado.html'
    
    def post(self, request, *args, **kwargs):
        tipo = request.POST.get('tipo')
        nome = request.POST.get('nome')
        sigla = request.POST.get('sigla', '')
        
        favorito, created = AgendaFavorita.objects.get_or_create(
            usuario=request.user,
            tipo=tipo,
            nome=nome,
            defaults={'sigla': sigla}
        )
        
        return render(request, self.template_name, {
            'nome': nome,
            'criado': created
        })


class RemoverFavoritoView(LoginRequiredMixin, TemplateView):
    """Remove comissão dos favoritos."""
    
    template_name = 'agenda/favorito_removido.html'
    
    def post(self, request, *args, **kwargs):
        favorito_id = request.POST.get('favorito_id')
        
        deletado, _ = AgendaFavorita.objects.filter(
            id=favorito_id,
            usuario=request.user
        ).delete()
        
        return render(request, self.template_name, {
            'deletado': deletado > 0
        })
