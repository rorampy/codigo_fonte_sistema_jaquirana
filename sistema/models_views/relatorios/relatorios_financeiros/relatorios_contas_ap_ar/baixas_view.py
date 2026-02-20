"""
Relatório de Baixas — AP: Pagamentos / AR: Recebimentos.

Rotas:
  GET  /relatorios/contas-a-pagar/pagamentos        → listagem AP
  POST /relatorios/contas-a-pagar/pagamentos/pdf     → exportar PDF AP
  POST /relatorios/contas-a-pagar/pagamentos/excel   → exportar Excel AP
  GET  /relatorios/contas-a-receber/recebimentos       → listagem AR
  POST /relatorios/contas-a-receber/recebimentos/pdf   → exportar PDF AR
  POST /relatorios/contas-a-receber/recebimentos/excel → exportar Excel AR
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



def _extrair_filtros():
    source = request.form if request.method == 'POST' else request.args
    return {
        'data_inicio': source.get('dataInicio') or None,
        'data_fim': source.get('dataFim') or None,
        'pessoa_id': source.get('pessoaId') or None,
        'plano_contas_id': source.get('planoContasId') or None,
        'centro_custo_id': source.get('centroCustoId') or None,
        'situacao_id': source.get('situacaoId') or None,
        'codigo_faturamento': source.get('codigoFaturamento') or None,
        'nota_fiscal': source.get('notaFiscal') or None,
        'descricao_avulso': source.get('descricaoAvulso') or None,
        'conta_bancaria_id': source.get('contaBancariaId') or None,
    }


def _contexto_base(direcao='ap'):
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



@app.route('/relatorios/contas-a-pagar/pagamentos', methods=['GET'])
@login_required
@requires_roles
def relatorio_ap_pagamentos():
    filtros = _extrair_filtros()
    registros = ContasAPARService.obter_baixas('ap', filtros)
    grupos = ContasAPARService.agrupar_baixas_por_faturamento(registros)
    totais = ContasAPARService.totalizar(registros)

    return render_template(
        'relatorios/relatorios_financeiros/relatorios_contas_ap_ar/baixas/listar.html',
        registros=registros,
        grupos=grupos,
        totais=totais,
        direcao='ap',
        titulo_relatorio='AP – Pagamentos',
        label_entidade='Entidade',
        label_baixa='Data Pagamento',
        label_valor_baixa='Valor Pago',
        tipo_relatorio='baixas',
        dados_corretos=request.args,
        **_contexto_base('ap'),
    )


@app.route('/relatorios/contas-a-pagar/pagamentos/pdf', methods=['POST'])
@login_required
@requires_roles
def relatorio_ap_pagamentos_pdf():
    filtros = _extrair_filtros()
    registros = ContasAPARService.obter_baixas('ap', filtros)
    grupos = ContasAPARService.agrupar_baixas_por_faturamento(registros)
    totais = ContasAPARService.totalizar(registros)

    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    logo_path = obter_url_absoluta_de_imagem('logo.png')
    data_hoje = datetime.now().strftime('%d-%m-%Y')
    data_geracao = datetime.now().strftime('%d/%m/%Y %H:%M')

    html = render_template(
        'relatorios/relatorios_financeiros/relatorios_contas_ap_ar/baixas/pdf.html',
        registros=registros,
        grupos=grupos,
        totais=totais,
        direcao='ap',
        titulo_relatorio='AP – Pagamentos',
        label_entidade='Entidade',
        label_baixa='Data Pagamento',
        label_valor_baixa='Valor Pago',
        logo_path=logo_path,
        changelog=changelog,
        dados_corretos=request.form,
        data_geracao=data_geracao,
    )
    return ManipulacaoArquivos.gerar_pdf_from_html(html, f'ap_pagamentos_{data_hoje}', 'Landscape', abrir_em_nova_aba=False)


@app.route('/relatorios/contas-a-pagar/pagamentos/excel', methods=['POST'])
@login_required
@requires_roles
def relatorio_ap_pagamentos_excel():
    filtros = _extrair_filtros()
    registros = ContasAPARService.obter_baixas('ap', filtros)
    grupos = ContasAPARService.agrupar_baixas_por_faturamento(registros)
    data_hoje = datetime.now().strftime('%d-%m-%Y')
    return ManipulacaoArquivos.exportar_excel_agrupado_ap_pagamentos(
        grupos,
        f'ap_pagamentos_{data_hoje}',
        titulo_planilha='AP – Pagamentos'
    )



@app.route('/relatorios/contas-a-receber/recebimentos', methods=['GET'])
@login_required
@requires_roles
def relatorio_ar_recebimentos():
    filtros = _extrair_filtros()
    registros = ContasAPARService.obter_baixas('ar', filtros)
    grupos = ContasAPARService.agrupar_baixas_por_faturamento(registros)
    totais = ContasAPARService.totalizar(registros)

    return render_template(
        'relatorios/relatorios_financeiros/relatorios_contas_ap_ar/baixas/listar.html',
        registros=registros,
        grupos=grupos,
        totais=totais,
        direcao='ar',
        titulo_relatorio='AR – Recebimentos',
        label_entidade='Cliente',
        label_baixa='Data Recebimento',
        label_valor_baixa='Valor Recebido',
        tipo_relatorio='baixas',
        dados_corretos=request.args,
        **_contexto_base('ar'),
    )


@app.route('/relatorios/contas-a-receber/recebimentos/pdf', methods=['POST'])
@login_required
@requires_roles
def relatorio_ar_recebimentos_pdf():
    filtros = _extrair_filtros()
    registros = ContasAPARService.obter_baixas('ar', filtros)
    grupos = ContasAPARService.agrupar_baixas_por_faturamento(registros)
    totais = ContasAPARService.totalizar(registros)

    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    logo_path = obter_url_absoluta_de_imagem('logo.png')
    data_hoje = datetime.now().strftime('%d-%m-%Y')
    data_geracao = datetime.now().strftime('%d/%m/%Y %H:%M')

    html = render_template(
        'relatorios/relatorios_financeiros/relatorios_contas_ap_ar/baixas/pdf.html',
        registros=registros,
        grupos=grupos,
        totais=totais,
        direcao='ar',
        titulo_relatorio='AR – Recebimentos',
        label_entidade='Cliente',
        label_baixa='Data Recebimento',
        label_valor_baixa='Valor Recebido',
        logo_path=logo_path,
        changelog=changelog,
        dados_corretos=request.form,
        data_geracao=data_geracao,
    )
    return ManipulacaoArquivos.gerar_pdf_from_html(html, f'ar_recebimentos_{data_hoje}', 'Landscape', abrir_em_nova_aba=False)


@app.route('/relatorios/contas-a-receber/recebimentos/excel', methods=['POST'])
@login_required
@requires_roles
def relatorio_ar_recebimentos_excel():
    filtros = _extrair_filtros()
    registros = ContasAPARService.obter_baixas('ar', filtros)
    grupos = ContasAPARService.agrupar_baixas_por_faturamento(registros)
    data_hoje = datetime.now().strftime('%d-%m-%Y')
    return ManipulacaoArquivos.exportar_excel_agrupado_ap_pagamentos(
        grupos,
        f'ar_recebimentos_{data_hoje}',
        titulo_planilha='AR – Recebimentos',
        direcao='ar'
    )
