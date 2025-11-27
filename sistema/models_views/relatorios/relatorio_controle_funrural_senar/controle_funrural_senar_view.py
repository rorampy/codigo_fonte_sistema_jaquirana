from sistema import app, requires_roles, db
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required
from sistema.models_views.faturamento.cargas_a_faturar.fornecedor.fornecedor_a_pagar_model import FornecedorPagarModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
from sistema.models_views.configuracoes_gerais.situacao_pagamento.situacao_pagamento_model import SituacaoPagamentoModel
from sistema._utilitarios import *


@app.route("/relatorios/controle-funrural-senar", methods=["GET", "POST"])
@login_required
@requires_roles
def listagem_controle_funrural_Senar():
    bitola = BitolaModel.listar_bitolas_ativas()
    produtos = ProdutoModel.listar_produtos()
    statusPagamentos = SituacaoPagamentoModel.listar_status()
    if request.method == "POST":
        data_inicio = request.form.get("dataInicio")
        data_fim = request.form.get("dataFim")
        placa = request.form.get("placaCargaCliente")
        motorista = request.form.get("motoristaCargaCliente")
        transportadora = request.form.get("tranpostadoraCargaCliente")
        fornecedor = request.form.get("fornecedorCargaCliente")
        cliente = request.form.get("clienteCarga")
        numero_nf = request.form.get("numeroNfCliente")
        incompleto = request.form.get("registroIncompleto")

        registros = FornecedorPagarModel.fornecedores_agrupados(
            data_inicio=data_inicio,
            data_fim=data_fim,
            placa=placa,
            motorista=motorista,
            transportadora=transportadora,
            fornecedor=fornecedor,
            cliente=cliente,
            numero_nf=numero_nf,
            statusPagamento='Pago',
            incompleto=incompleto,
        )
    else:
        registros = FornecedorPagarModel.fornecedores_agrupados(statusPagamento='Pago')
    return render_template(
        "/relatorios/controle_funrural_senar/controle_funrural_senar.html",
        registros=registros,
        bitola=bitola,
        produtos=produtos,
        statusPagamentos=statusPagamentos,
        dados_corretos=request.form,
    )