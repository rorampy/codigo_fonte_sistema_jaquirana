"""
Relatório de Emissões — Contas a Pagar (AP) e Contas a Receber (AR).

Rotas:
  GET  /relatorios/contas-a-pagar/emissoes        → listagem AP
  POST /relatorios/contas-a-pagar/emissoes/pdf     → exportar PDF AP
  POST /relatorios/contas-a-pagar/emissoes/excel   → exportar Excel AP
  GET  /relatorios/contas-a-receber/emissoes       → listagem AR
  POST /relatorios/contas-a-receber/emissoes/pdf   → exportar PDF AR
  POST /relatorios/contas-a-receber/emissoes/excel → exportar Excel AR
"""

from datetime import datetime
from sistema import app, requires_roles, obter_url_absoluta_de_imagem
from flask import render_template, request
from flask_login import login_required
from sistema._utilitarios import ManipulacaoArquivos
from sistema.models_views.configuracoes_gerais.situacao_pagamento.situacao_pagamento_model import SituacaoPagamentoModel
from sistema.models_views.configuracoes_gerais.centro_custo.centro_custo_model import CentroCustoModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
from sistema.models_views.gerenciar.pessoa_financeiro.pessoa_financeiro_model import PessoaFinanceiroModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_cadastro_model import FornecedorCadastroModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema.models_views.configuracoes_gerais.conta_bancaria.conta_bancaria_model import ContaBancariaModel

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
        'conta_bancaria_id': source.get('contaBancariaId') or None,
    }


def _contexto_base(direcao='ap'):
    """Retorna dados comuns para todos os templates (selects de filtro)."""
    if direcao == 'ar':
        pessoas = ClienteModel.listar_clientes()
    else:
        pessoas = FornecedorCadastroModel.listar_fornecedores()
    return {
        'pessoas': pessoas,
        'planos_contas': PlanoContaModel.listar_todos_planos(),
        'centros_custo': CentroCustoModel.obter_centro_custos_ativos(),
        'situacoes': SituacaoPagamentoModel.listar_status(),
        'contas_bancarias': ContaBancariaModel.obter_contas_bancarias_ativas(),
    }


# =============================================================================
# AP — EMISSÕES
# =============================================================================

@app.route('/relatorios/contas-a-pagar/emissoes', methods=['GET'])
@login_required
@requires_roles
def relatorio_ap_emissoes():
    filtros = _extrair_filtros()
    registros = ContasAPARService.obter_emissoes('ap', filtros)
    totais = ContasAPARService.totalizar(registros)

    return render_template(
        'relatorios/relatorios_financeiros/relatorios_contas_ap_ar/emissoes/listar.html',
        registros=registros,
        totais=totais,
        direcao='ap',
        titulo_relatorio='AP – Emissões',
        label_entidade='Entidade',
        label_valor='A Pagar',
        tipo_relatorio='emissoes',
        dados_corretos=request.args,
        **_contexto_base('ap'),
    )


@app.route('/relatorios/contas-a-pagar/emissoes/pdf', methods=['POST'])
@login_required
@requires_roles
def relatorio_ap_emissoes_pdf():
    filtros = _extrair_filtros()
    registros = ContasAPARService.obter_emissoes('ap', filtros)
    totais = ContasAPARService.totalizar(registros)

    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    logo_path = obter_url_absoluta_de_imagem('logo.png')
    data_hoje = datetime.now().strftime('%d-%m-%Y')

    html = render_template(
        'relatorios/relatorios_financeiros/relatorios_contas_ap_ar/emissoes/pdf.html',
        registros=registros,
        totais=totais,
        direcao='ap',
        titulo_relatorio='AP – Emissões',
        label_entidade='Entidade',
        label_valor='A Pagar',
        logo_path=logo_path,
        changelog=changelog,
        dados_corretos=request.form,
    )
    return ManipulacaoArquivos.gerar_pdf_from_html(html, f'ap_emissoes_{data_hoje}', 'Landscape', abrir_em_nova_aba=False)


@app.route('/relatorios/contas-a-pagar/emissoes/excel', methods=['POST'])
@login_required
@requires_roles
def relatorio_ap_emissoes_excel():
    filtros = _extrair_filtros()
    registros = ContasAPARService.obter_emissoes('ap', filtros)
    totais = ContasAPARService.totalizar(registros)
    dados = ContasAPARService.preparar_dados_excel_emissoes(registros, 'ap')
    data_hoje = datetime.now().strftime('%d-%m-%Y')
    return ManipulacaoArquivos.exportar_excel_formatado(
        dados,
        f'ap_emissoes_{data_hoje}',
        titulo_planilha='AP – Emissões',
        colunas_monetarias=['Valor a Pagar'],
        linha_totais={
            'Valor a Pagar': totais['total_original_100'] / 100,
        },
    )


# =============================================================================
# AR — EMISSÕES
# =============================================================================

@app.route('/relatorios/contas-a-receber/emissoes', methods=['GET'])
@login_required
@requires_roles
def relatorio_ar_emissoes():
    filtros = _extrair_filtros()
    registros = ContasAPARService.obter_emissoes('ar', filtros)
    totais = ContasAPARService.totalizar(registros)

    return render_template(
        'relatorios/relatorios_financeiros/relatorios_contas_ap_ar/emissoes/listar.html',
        registros=registros,
        totais=totais,
        direcao='ar',
        titulo_relatorio='AR – Emissões',
        label_entidade='Cliente',
        label_valor='A Receber',
        tipo_relatorio='emissoes',
        dados_corretos=request.args,
        **_contexto_base('ar'),
    )


@app.route('/relatorios/contas-a-receber/emissoes/pdf', methods=['POST'])
@login_required
@requires_roles
def relatorio_ar_emissoes_pdf():
    filtros = _extrair_filtros()
    registros = ContasAPARService.obter_emissoes('ar', filtros)
    totais = ContasAPARService.totalizar(registros)

    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    logo_path = obter_url_absoluta_de_imagem('logo.png')
    data_hoje = datetime.now().strftime('%d-%m-%Y')

    html = render_template(
        'relatorios/relatorios_financeiros/relatorios_contas_ap_ar/emissoes/pdf.html',
        registros=registros,
        totais=totais,
        direcao='ar',
        titulo_relatorio='AR – Emissões',
        label_entidade='Cliente',
        label_valor='A Receber',
        logo_path=logo_path,
        changelog=changelog,
        dados_corretos=request.form,
    )
    return ManipulacaoArquivos.gerar_pdf_from_html(html, f'ar_emissoes_{data_hoje}', 'Landscape', abrir_em_nova_aba=False)


@app.route('/relatorios/contas-a-receber/emissoes/excel', methods=['POST'])
@login_required
@requires_roles
def relatorio_ar_emissoes_excel():
    filtros = _extrair_filtros()
    registros = ContasAPARService.obter_emissoes('ar', filtros)
    totais = ContasAPARService.totalizar(registros)
    dados = ContasAPARService.preparar_dados_excel_emissoes(registros, 'ar')
    data_hoje = datetime.now().strftime('%d-%m-%Y')
    return ManipulacaoArquivos.exportar_excel_formatado(
        dados,
        f'ar_emissoes_{data_hoje}',
        titulo_planilha='AR – Emissões',
        colunas_monetarias=['Valor a Receber'],
        linha_totais={
            'Valor a Receber': totais['total_original_100'] / 100,
        },
    )
