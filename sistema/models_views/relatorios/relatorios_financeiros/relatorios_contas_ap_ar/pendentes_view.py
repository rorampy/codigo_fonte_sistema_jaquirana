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
from flask import render_template, request
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
    source = request.form if request.method == 'POST' else request.args
    return {
        'pessoa_id': source.get('pessoaId') or None,
        'plano_contas_id': source.get('planoContasId') or None,
        'centro_custo_id': source.get('centroCustoId') or None,
        'situacao_id': source.get('situacaoId') or None,
    }


def _extrair_data_referencia():
    """Extrai data de referência (corte). Se não informada, usa hoje."""
    source = request.form if request.method == 'POST' else request.args
    data_ref_str = source.get('dataReferencia')
    if data_ref_str:
        try:
            return date.fromisoformat(data_ref_str)
        except (ValueError, TypeError):
            pass
    return date.today()


def _contexto_base(direcao='ap'):
    """Dados comuns para os templates de filtro.
    Para Pendentes AP: dropdown lista Fornecedores (FornecedorCadastroModel).
    Para Pendentes AR: dropdown lista Clientes (ClienteModel).
    """
    if direcao == 'ap':
        pessoas = FornecedorCadastroModel.listar_fornecedores_ativos()
    else:
        pessoas = ClienteModel.listar_clientes_ativos()
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
    data_referencia = _extrair_data_referencia()
    registros = ContasAPARService.obter_pendentes('ap', data_referencia, filtros)
    totais = ContasAPARService.totalizar(registros)

    return render_template(
        'relatorios/relatorios_financeiros/relatorios_contas_ap_ar/pendentes/listar.html',
        registros=registros,
        totais=totais,
        direcao='ap',
        titulo_relatorio='AP – Pendentes',
        label_entidade='Fornecedor',
        data_referencia=data_referencia,
        tipo_relatorio='pendentes',
        dados_corretos=request.args,
        **_contexto_base('ap'),
    )


@app.route('/relatorios/contas-a-pagar/pendentes/pdf', methods=['POST'])
@login_required
@requires_roles
def relatorio_ap_pendentes_pdf():
    filtros = _extrair_filtros()
    data_referencia = _extrair_data_referencia()
    registros = ContasAPARService.obter_pendentes('ap', data_referencia, filtros)
    totais = ContasAPARService.totalizar(registros)

    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    logo_path = obter_url_absoluta_de_imagem('logo.png')
    data_hoje = datetime.now().strftime('%d-%m-%Y')

    html = render_template(
        'relatorios/relatorios_financeiros/relatorios_contas_ap_ar/pendentes/pdf.html',
        registros=registros,
        totais=totais,
        direcao='ap',
        titulo_relatorio='AP – Pendentes',
        label_entidade='Fornecedor',
        data_referencia=data_referencia,
        logo_path=logo_path,
        changelog=changelog,
        dados_corretos=request.form,
    )
    return ManipulacaoArquivos.gerar_pdf_from_html(html, f'ap_pendentes_{data_hoje}', 'Landscape', abrir_em_nova_aba=False)


@app.route('/relatorios/contas-a-pagar/pendentes/excel', methods=['POST'])
@login_required
@requires_roles
def relatorio_ap_pendentes_excel():
    filtros = _extrair_filtros()
    data_referencia = _extrair_data_referencia()
    registros = ContasAPARService.obter_pendentes('ap', data_referencia, filtros)
    totais = ContasAPARService.totalizar(registros)
    dados = ContasAPARService.preparar_dados_excel_pendentes(registros, 'ap')
    data_hoje = datetime.now().strftime('%d-%m-%Y')
    return ManipulacaoArquivos.exportar_excel_formatado(
        dados,
        f'ap_pendentes_{data_hoje}',
        titulo_planilha=f'AP – Pendentes ({data_referencia.strftime("%d/%m/%Y")})',
        colunas_monetarias=['Valor Original', 'Saldo Pendente'],
        coluna_destaque='Saldo Pendente',
        linha_totais={
            'Valor Original': totais['total_original_100'] / 100,
            'Saldo Pendente': totais['total_saldo_100'] / 100,
        },
    )


# =============================================================================
# AR — PENDENTES
# =============================================================================

@app.route('/relatorios/contas-a-receber/pendentes', methods=['GET'])
@login_required
@requires_roles
def relatorio_ar_pendentes():
    filtros = _extrair_filtros()
    data_referencia = _extrair_data_referencia()
    registros = ContasAPARService.obter_pendentes('ar', data_referencia, filtros)
    totais = ContasAPARService.totalizar(registros)

    return render_template(
        'relatorios/relatorios_financeiros/relatorios_contas_ap_ar/pendentes/listar.html',
        registros=registros,
        totais=totais,
        direcao='ar',
        titulo_relatorio='AR – Pendentes',
        label_entidade='Cliente',
        data_referencia=data_referencia,
        tipo_relatorio='pendentes',
        dados_corretos=request.args,
        **_contexto_base('ar'),
    )


@app.route('/relatorios/contas-a-receber/pendentes/pdf', methods=['POST'])
@login_required
@requires_roles
def relatorio_ar_pendentes_pdf():
    filtros = _extrair_filtros()
    data_referencia = _extrair_data_referencia()
    registros = ContasAPARService.obter_pendentes('ar', data_referencia, filtros)
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
        data_referencia=data_referencia,
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
    data_referencia = _extrair_data_referencia()
    registros = ContasAPARService.obter_pendentes('ar', data_referencia, filtros)
    totais = ContasAPARService.totalizar(registros)
    dados = ContasAPARService.preparar_dados_excel_pendentes(registros, 'ar')
    data_hoje = datetime.now().strftime('%d-%m-%Y')
    return ManipulacaoArquivos.exportar_excel_formatado(
        dados,
        f'ar_pendentes_{data_hoje}',
        titulo_planilha=f'AR – Pendentes ({data_referencia.strftime("%d/%m/%Y")})',
        colunas_monetarias=['Valor Original', 'Saldo Pendente'],
        coluna_destaque='Saldo Pendente',
        linha_totais={
            'Valor Original': totais['total_original_100'] / 100,
            'Saldo Pendente': totais['total_saldo_100'] / 100,
        },
    )
