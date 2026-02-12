"""
Relatório de Pendentes — AP e AR na data de corte.

Rotas:
  GET  /relatorios/contas-a-pagar/pendentes        → listagem AP
  POST /relatorios/contas-a-pagar/pendentes/pdf     → exportar PDF AP
  POST /relatorios/contas-a-pagar/pendentes/excel   → exportar Excel AP
  GET  /relatorios/contas-a-receber/pendentes       → listagem AR
  POST /relatorios/contas-a-receber/pendentes/pdf   → exportar PDF AR
  POST /relatorios/contas-a-receber/pendentes/excel → exportar Excel AR
"""

from datetime import datetime, date
from sistema import app, requires_roles, obter_url_absoluta_de_imagem
from flask import render_template, request, jsonify
from flask_login import login_required
from sistema._utilitarios import ManipulacaoArquivos
from sistema.models_views.configuracoes_gerais.situacao_pagamento.situacao_pagamento_model import SituacaoPagamentoModel
from sistema.models_views.configuracoes_gerais.centro_custo.centro_custo_model import CentroCustoModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
from sistema.models_views.gerenciar.pessoa_financeiro.pessoa_financeiro_model import PessoaFinanceiroModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_cadastro_model import FornecedorCadastroModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel

from .contas_ap_ar_service import ContasAPARService


# =============================================================================
# HELPERS
# =============================================================================

def _extrair_filtros():
    """Extrai filtros do request (GET ou POST)."""
    source = request.form if request.method == 'POST' else request.args
    return {
        'data_inicio': source.get('dataInicio') or None,
        'data_fim': source.get('dataFim') or None,
        'pessoa_id': source.get('pessoaId') or None,
        'plano_contas_id': source.get('planoContasId') or None,
        'centro_custo_id': source.get('centroCustoId') or None,
        'situacao_id': source.get('situacaoId') or None,
    }


def _contexto_base(direcao='ap'):
    """Dados comuns para os templates de filtro.
    Para Pendentes AP: dropdown lista Fornecedores (FornecedorCadastroModel).
    Para Pendentes AR: dropdown lista Clientes (ClienteModel).
    """
    if direcao == 'ap':
        pessoas = FornecedorCadastroModel.listar_fornecedores()
    else:
        pessoas = ClienteModel.listar_clientes()
    return {
        'pessoas': pessoas,
        'planos_contas': PlanoContaModel.listar_todos_planos(),
        'centros_custo': CentroCustoModel.obter_centro_custos_ativos(),
        'situacoes': SituacaoPagamentoModel.listar_status(),
    }


# =============================================================================
# AP — PENDENTES
# =============================================================================

@app.route('/relatorios/contas-a-pagar/pendentes', methods=['GET'])
@login_required
@requires_roles
def relatorio_ap_pendentes():
    filtros = _extrair_filtros()
    registros = ContasAPARService.obter_pendentes('ap', filtros)
    grupos = ContasAPARService.agrupar_pendentes_por_faturamento(registros)
    totais = ContasAPARService.totalizar(registros)

    return render_template(
        'relatorios/relatorios_financeiros/relatorios_contas_ap_ar/pendentes/listar.html',
        registros=registros,
        grupos=grupos,
        totais=totais,
        direcao='ap',
        titulo_relatorio='AP – Pendentes',
        label_entidade='Fornecedor',
        tipo_relatorio='pendentes',
        dados_corretos=request.args,
        **_contexto_base('ap'),
    )


@app.route('/relatorios/contas-a-pagar/pendentes/pdf', methods=['POST'])
@login_required
@requires_roles
def relatorio_ap_pendentes_pdf():
    filtros = _extrair_filtros()
    registros = ContasAPARService.obter_pendentes('ap', filtros)
    grupos = ContasAPARService.agrupar_pendentes_por_faturamento(registros)
    totais = ContasAPARService.totalizar(registros)

    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    logo_path = obter_url_absoluta_de_imagem('logo.png')
    data_hoje = datetime.now().strftime('%d-%m-%Y')
    data_geracao = datetime.now().strftime('%d/%m/%Y %H:%M')

    html = render_template(
        'relatorios/relatorios_financeiros/relatorios_contas_ap_ar/pendentes/pdf.html',
        registros=registros,
        grupos=grupos,
        totais=totais,
        direcao='ap',
        titulo_relatorio='AP – Pendentes',
        label_entidade='Fornecedor',
        logo_path=logo_path,
        changelog=changelog,
        dados_corretos=request.form,
        data_geracao=data_geracao,
    )
    return ManipulacaoArquivos.gerar_pdf_from_html(html, f'ap_pendentes_{data_hoje}', 'Landscape', abrir_em_nova_aba=False)


@app.route('/relatorios/contas-a-pagar/pendentes/excel', methods=['POST'])
@login_required
@requires_roles
def relatorio_ap_pendentes_excel():
    filtros = _extrair_filtros()
    registros = ContasAPARService.obter_pendentes('ap', filtros)
    grupos = ContasAPARService.agrupar_pendentes_por_faturamento(registros)
    data_hoje = datetime.now().strftime('%d-%m-%Y')
    return ManipulacaoArquivos.exportar_excel_agrupado_ap_pendentes(
        grupos,
        f'ap_pendentes_{data_hoje}',
        titulo_planilha='AP – Pendentes'
    )


# =============================================================================
# AR — PENDENTES
# =============================================================================

@app.route('/relatorios/contas-a-receber/pendentes', methods=['GET'])
@login_required
@requires_roles
def relatorio_ar_pendentes():
    filtros = _extrair_filtros()
    registros = ContasAPARService.obter_pendentes('ar', filtros)
    totais = ContasAPARService.totalizar(registros)

    return render_template(
        'relatorios/relatorios_financeiros/relatorios_contas_ap_ar/pendentes/listar.html',
        registros=registros,
        totais=totais,
        direcao='ar',
        titulo_relatorio='AR – Pendentes',
        label_entidade='Cliente',
        tipo_relatorio='pendentes',
        dados_corretos=request.args,
        **_contexto_base('ar'),
    )


@app.route('/relatorios/contas-a-receber/pendentes/pdf', methods=['POST'])
@login_required
@requires_roles
def relatorio_ar_pendentes_pdf():
    filtros = _extrair_filtros()
    registros = ContasAPARService.obter_pendentes('ar', filtros)
    totais = ContasAPARService.totalizar(registros)

    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    logo_path = obter_url_absoluta_de_imagem('logo.png')
    data_hoje = datetime.now().strftime('%d-%m-%Y')

    html = render_template(
        'relatorios/relatorios_financeiros/relatorios_contas_ap_ar/pendentes/pdf.html',
        registros=registros,
        totais=totais,
        direcao='ar',
        titulo_relatorio='AR – Pendentes',
        label_entidade='Cliente',
        logo_path=logo_path,
        changelog=changelog,
        dados_corretos=request.form,
    )
    return ManipulacaoArquivos.gerar_pdf_from_html(html, f'ar_pendentes_{data_hoje}', 'Landscape', abrir_em_nova_aba=False)


@app.route('/relatorios/contas-a-receber/pendentes/excel', methods=['POST'])
@login_required
@requires_roles
def relatorio_ar_pendentes_excel():
    filtros = _extrair_filtros()
    registros = ContasAPARService.obter_pendentes('ar', filtros)
    totais = ContasAPARService.totalizar(registros)
    dados = ContasAPARService.preparar_dados_excel_pendentes(registros, 'ar')
    data_hoje = datetime.now().strftime('%d-%m-%Y')
    return ManipulacaoArquivos.exportar_excel_formatado(
        dados,
        f'ar_pendentes_{data_hoje}',
        titulo_planilha='AR – Pendentes',
        colunas_monetarias=['Valor Original', 'Saldo Pendente'],
        coluna_destaque='Saldo Pendente',
        linha_totais={
            'Valor Original': totais['total_original_100'] / 100,
            'Saldo Pendente': totais['total_saldo_100'] / 100,
        },
    )


# =============================================================================
# AJAX — DETALHES DO FATURAMENTO
# =============================================================================

@app.route('/relatorios/contas-a-pagar/pendentes/detalhes/<int:faturamento_id>', methods=['GET'])
@login_required
@requires_roles
def relatorio_ap_pendentes_detalhes_faturamento(faturamento_id):
    """
    Endpoint AJAX para buscar detalhes das cargas de um faturamento.
    Retorna fornecedores, transportadoras, extratores, comissionados.
    """
    from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
    
    try:
        faturamento = FaturamentoModel.query.get(faturamento_id)
        if not faturamento:
            return jsonify({'success': False, 'message': 'Faturamento não encontrado'}), 404
        
        detalhes = faturamento.obter_detalhes()
        
        return jsonify({
            'success': True,
            'tipo': 'faturamento',
            'codigo_faturamento': faturamento.codigo_faturamento,
            'valor_total': faturamento.valor_total,
            'valor_bruto_total': faturamento.valor_bruto_total,
            'valor_credito_aplicado': faturamento.valor_credito_aplicado or 0,
            'data_cadastro': faturamento.data_cadastro.strftime('%d/%m/%Y %H:%M') if faturamento.data_cadastro else None,
            'fornecedores': detalhes.get('fornecedores', []),
            'transportadoras': detalhes.get('transportadoras', []),
            'extratores': detalhes.get('extratores', []),
            'comissionados': detalhes.get('comissionados', []),
            'cargas_a_receber': detalhes.get('cargas_a_receber', []),
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/relatorios/contas-a-pagar/pendentes/detalhes-lancamento/<int:lancamento_id>', methods=['GET'])
@login_required
@requires_roles
def relatorio_ap_pendentes_detalhes_lancamento(lancamento_id):
    """
    Endpoint AJAX para buscar detalhes de um lançamento avulso.
    """
    from sistema.models_views.financeiro.lancamento_avulso.lancamento_avulso_model import LancamentoAvulsoModel
    
    try:
        lancamento = LancamentoAvulsoModel.query.get(lancamento_id)
        if not lancamento:
            return jsonify({'success': False, 'message': 'Lançamento não encontrado'}), 404
        
        return jsonify({
            'success': True,
            'tipo': 'lancamento_avulso',
            'id': lancamento.id,
            'descricao': lancamento.descricao,
            'valor': lancamento.valor_movimentacao_100,
            'data_cadastro': lancamento.data_cadastro.strftime('%d/%m/%Y %H:%M') if lancamento.data_cadastro else None,
            'pessoa_nome': lancamento.pessoa_financeiro.identificacao if lancamento.pessoa_financeiro else '-',
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

