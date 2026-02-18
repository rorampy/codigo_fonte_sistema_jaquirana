from datetime import datetime, date
from collections import OrderedDict
from sistema import app, requires_roles, obter_url_absoluta_de_imagem
from flask import render_template, request
from flask_login import login_required
from sistema.models_views.financeiro.movimentacao_financeira.movimentacao_financeira_model import MovimentacaoFinanceiraModel
from sistema.models_views.financeiro.movimentacao_financeira.saldo_movimentacao_financeira_model import SaldoMovimentacaoFinanceiraModel
from sistema.models_views.faturamento.cargas_a_faturar.transportadora.frete_a_pagar_model import FretePagarModel
from sistema.models_views.faturamento.cargas_a_faturar.extrator.extrator_a_pagar_model import ExtratorPagarModel
from sistema.models_views.faturamento.cargas_a_faturar.fornecedor.fornecedor_a_pagar_model import FornecedorPagarModel
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.configuracoes_gerais.conta_bancaria.conta_bancaria_model import ContaBancariaModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema._utilitarios import *


def _calcular_valor_movimentacao(mov):
    """Calcula o valor de uma movimentação usando valor_movimentacao_100.
    Alinhado com obter_valor_total_recebidos/obter_valor_total_saidas que fazem SUM(valor_movimentacao_100).
    """
    return mov.valor_movimentacao_100 or 0


def _calcular_totalizadores(movimentacoes):
    """Calcula totalizadores das movimentações."""
    total_entradas = 0
    total_saidas = 0
    total_cancelamentos = 0
    total_estornos = 0
    qtd_movimentacoes = len(movimentacoes)

    for mov in movimentacoes:
        valor = _calcular_valor_movimentacao(mov)
        if mov.tipo_movimentacao == 1:
            total_entradas += valor
        elif mov.tipo_movimentacao == 2:
            total_saidas += valor
        elif mov.tipo_movimentacao == 3:
            total_cancelamentos += valor
        elif mov.tipo_movimentacao in [4, 5]:
            total_estornos += valor

    return {
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'total_cancelamentos': total_cancelamentos,
        'total_estornos': total_estornos,
        'saldo_periodo': total_entradas - total_saidas,
        'qtd_movimentacoes': qtd_movimentacoes
    }


def _agrupar_movimentacoes_por_dia(movimentacoes):
    """Agrupa movimentações por data e calcula subtotais diários.
    
    Retorna OrderedDict com datas como chave (mais recente primeiro), 
    cada valor contendo as movimentações do dia e totais de entradas/saídas.
    Semelhante à organização de extrato bancário.
    """
    agrupado = OrderedDict()

    for mov in movimentacoes:
        data_mov = mov.data_movimentacao
        if data_mov not in agrupado:
            agrupado[data_mov] = {
                'movimentacoes': [],
                'total_entradas': 0,
                'total_saidas': 0,
                'total_cancelamentos': 0,
                'total_estornos': 0,
                'saldo_dia': 0,
                'qtd': 0
            }

        grupo = agrupado[data_mov]
        grupo['movimentacoes'].append(mov)
        grupo['qtd'] += 1

        valor = _calcular_valor_movimentacao(mov)
        if mov.tipo_movimentacao == 1:
            grupo['total_entradas'] += valor
        elif mov.tipo_movimentacao == 2:
            grupo['total_saidas'] += valor
        elif mov.tipo_movimentacao == 3:
            grupo['total_cancelamentos'] += valor
        elif mov.tipo_movimentacao in [4, 5]:
            grupo['total_estornos'] += valor

    # Calcular saldo do dia para cada grupo
    for data_mov, grupo in agrupado.items():
        grupo['saldo_dia'] = grupo['total_entradas'] - grupo['total_saidas']

    return agrupado


@app.route("/financeiro/movimentacoes-financeiras/exportar", methods=["GET"])
@login_required
@requires_roles
def exportar_movimentacaoes_financeiras():
    """Exporta relatório PDF das movimentações financeiras.
    
    Usa os mesmos métodos da view principal para garantir consistência dos valores.
    """
    conta_selecionada_id = request.args.get("conta_bancaria_id", type=int)
    data_inicio_str = request.args.get("data_inicio")
    data_fim_str = request.args.get("data_fim")
    
    # Converter strings para date
    data_inicio = None
    data_fim = None
    if data_inicio_str:
        try:
            data_inicio = date.fromisoformat(data_inicio_str)
        except ValueError:
            pass
    if data_fim_str:
        try:
            data_fim = date.fromisoformat(data_fim_str)
        except ValueError:
            pass
    
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    data_hoje = datetime.now().strftime("%d-%m-%Y")

    # Obter conta selecionada
    conta_obj = None
    conta_label = "Todas as contas"
    if conta_selecionada_id and conta_selecionada_id != 0:
        conta_obj = ContaBancariaModel.obter_conta_por_id(conta_selecionada_id)
        if conta_obj:
            conta_label = conta_obj.identificacao

    # Obter movimentações com filtro de período e ordenação decrescente
    movimentacoes = MovimentacaoFinanceiraModel.listagem_movimentacoes_financeiras_relatorio(
        conta_selecionada_id,
        data_inicio,
        data_fim
    )
    
    # Calcular totalizadores do período
    totalizadores = _calcular_totalizadores(movimentacoes)
    
    # Agrupar movimentações por dia para totalização diária (padrão extrato bancário)
    movimentacoes_por_dia = _agrupar_movimentacoes_por_dia(movimentacoes)
    
    # Calcular saldo disponível
    # Quando "Todas as contas", soma apenas saldos de contas ATIVAS (igual à listagem de contas bancárias)
    if conta_selecionada_id and conta_selecionada_id != 0:
        saldo_disponivel = SaldoMovimentacaoFinanceiraModel.obter_registro_saldo_por_conta_bancaria(conta_selecionada_id)
    else:
        contas_ativas = ContaBancariaModel.obter_contas_bancarias_ativas()
        saldo_disponivel = sum(
            SaldoMovimentacaoFinanceiraModel.obter_registro_saldo_por_conta_bancaria(conta.id) or 0
            for conta in contas_ativas
        )

    # Calcular totais a pagar (valores pendentes)
    a_pagar_frete = FretePagarModel.obter_valor_total_a_pagar()
    a_pagar_fornecedor = FornecedorPagarModel.obter_valor_total_a_pagar()
    a_pagar_extrator = ExtratorPagarModel.obter_valor_total_a_pagar()
    valor_total_pagar = int(a_pagar_frete + a_pagar_fornecedor + a_pagar_extrator)

    total_a_receber = RegistroOperacionalModel.obter_valor_total_a_receber_por_conta(conta_selecionada_id)

    total_recebido = MovimentacaoFinanceiraModel.obter_valor_total_recebidos(conta_selecionada_id)
    valor_total_pago = MovimentacaoFinanceiraModel.obter_valor_total_saidas(conta_selecionada_id)

    logo_path = obter_url_absoluta_de_imagem("logo.png")
    html = render_template(
        "relatorios/relatorio_movimentacoes_financeiras/relatorio_movimentacoes_financeiras.html",
        logo_path=logo_path,
        changelog=changelog,
        dataHoje=data_hoje,
        conta_obj=conta_obj,
        conta_label=conta_label,
        movimentacoes=movimentacoes,
        conta_selecionada_id=conta_selecionada_id,
        saldo_disponivel=saldo_disponivel,
        valor_total_pagar=valor_total_pagar,
        valor_total_pago=valor_total_pago,
        total_a_receber=total_a_receber,
        total_recebido=total_recebido,
        data_inicio=data_inicio,
        data_fim=data_fim,
        totalizadores=totalizadores,
        movimentacoes_por_dia=movimentacoes_por_dia
    )

    nome_arquivo_saida = f"movimentacoes_financeiras-{data_hoje}"
    resposta = ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida, 'Landscape')
    return resposta