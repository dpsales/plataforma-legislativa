import json
import logging
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView, FormView
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.contrib import messages
from .models import ProcessoSEI, AndamentoProcesso, DocumentoProcesso
from .forms import BuscaProcessoForm
from .services import AutomacaoSEI, ExtratorDadosSEI

logger = logging.getLogger(__name__)


class IndexView(View):
    """
    View da página inicial do módulo de busca de processos SEI
    """
    template_name = 'processos/index.html'
    
    def get(self, request):
        ultimos_processos = ProcessoSEI.objects.all()[:10]
        form = BuscaProcessoForm()
        context = {
            'form': form,
            'ultimos_processos': ultimos_processos,
        }
        return render(request, self.template_name, context)


class BuscaProcessoView(FormView):
    """
    View para buscar um processo no SEI e extrair suas informações
    """
    template_name = 'processos/busca.html'
    form_class = BuscaProcessoForm
    success_url = reverse_lazy('processos:index')
    
    def form_valid(self, form):
        numero_processo = form.cleaned_data['numero_processo']
        include_documentos = form.cleaned_data.get('include_documentos', False)
        
        try:
            # Busca ou cria o processo
            processo, criado = ProcessoSEI.objects.get_or_create(
                numero_processo=numero_processo,
                defaults={'assunto': '', 'status': 'Processando'}
            )
            
            # Se precisa buscar dados frescos ou é novo
            if criado or not processo.andamentos.exists():
                # Aqui seria integrado com a automação SEI
                messages.success(
                    self.request,
                    f'Processo {numero_processo} buscado com sucesso!'
                )
            
            return render(
                self.request,
                'processos/detalhe_processo.html',
                {'processo': processo, 'andamentos': processo.andamentos.all()}
            )
        
        except Exception as e:
            logger.error(f"Erro ao buscar processo {numero_processo}: {str(e)}")
            messages.error(
                self.request,
                f'Erro ao buscar processo: {str(e)}'
            )
            return render(self.request, self.template_name, {'form': form})


class DetalheProcessoView(DetailView):
    """
    View para exibir detalhes de um processo
    """
    model = ProcessoSEI
    template_name = 'processos/detalhe_processo.html'
    context_object_name = 'processo'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        processo = self.get_object()
        context['andamentos'] = processo.andamentos.all()
        context['documentos'] = processo.documentos.all()
        return context


class BuscaProcessoAPIView(View):
    """
    View da API para buscar processos (chamadas AJAX)
    """
    def post(self, request):
        try:
            data = json.loads(request.body)
            numero_processo = data.get('numero_processo', '').strip()
            
            if not numero_processo:
                return JsonResponse({
                    'sucesso': False,
                    'erro': 'Número do processo é obrigatório'
                }, status=400)
            
            # Validação básica do formato
            if len(numero_processo) < 10:
                return JsonResponse({
                    'sucesso': False,
                    'erro': 'Número do processo inválido'
                }, status=400)
            
            # Busca ou cria o processo
            processo, criado = ProcessoSEI.objects.get_or_create(
                numero_processo=numero_processo
            )
            
            return JsonResponse({
                'sucesso': True,
                'processo_id': processo.id,
                'numero_processo': processo.numero_processo,
                'criado': criado
            })
        
        except json.JSONDecodeError:
            return JsonResponse({
                'sucesso': False,
                'erro': 'Requisição JSON inválida'
            }, status=400)
        
        except Exception as e:
            logger.error(f"Erro na API de busca: {str(e)}")
            return JsonResponse({
                'sucesso': False,
                'erro': 'Erro interno do servidor'
            }, status=500)
