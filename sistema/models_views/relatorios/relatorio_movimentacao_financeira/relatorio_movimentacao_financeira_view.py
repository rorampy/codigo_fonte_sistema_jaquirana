from datetime import datetime
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


@app.route("/financeiro/movimentacoes-financeiras/exportar", methods=["GET"])
@login_required
@requires_roles
def exportar_movimentacaoes_financeiras():
    """Exporta relatório PDF das movimentações financeiras.
    
    Usa os mesmos métodos da view principal para garantir consistência dos valores.
    """
    conta_selecionada_id = request.args.get("conta_bancaria_id", type=int)
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    data_hoje = datetime.now().strftime("%d-%m-%Y")

    # Obter conta selecionada
    conta_obj = None
    conta_label = "Todas as contas"
    if conta_selecionada_id and conta_selecionada_id != 0:
        conta_obj = ContaBancariaModel.obter_conta_por_id(conta_selecionada_id)
        if conta_obj:
            conta_label = conta_obj.identificacao

    # Obter movimentações (mesmos métodos da view principal)
    movimentacoes = MovimentacaoFinanceiraModel.listagem_movimentacoes_financeiras_por_conta(conta_selecionada_id)
    
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
        total_recebido=total_recebido
    )

    nome_arquivo_saida = f"movimentacoes_financeiras-{data_hoje}"
    resposta = ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida)
    return resposta