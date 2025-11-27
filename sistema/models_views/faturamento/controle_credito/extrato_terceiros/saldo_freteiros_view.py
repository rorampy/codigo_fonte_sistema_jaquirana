from datetime import datetime
from sistema import app, requires_roles, db
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema.models_views.faturamento.controle_credito.extrato_credito.extrato_credito_freteiro_model import ExtratoCreditoFreteiroModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.financeiro.movimentacao_financeira.movimentacao_financeira_model import MovimentacaoFinanceiraModel
from sistema.models_views.faturamento.controle_credito.credito_agrupado.credito_freteiro_model import CreditoFreteiroModel
from sistema.models_views.financeiro.movimentacao_financeira.saldo_movimentacao_financeira_model import SaldoMovimentacaoFinanceiraModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_model import CategorizacaoFiscalModel
from sistema.models_views.configuracoes_gerais.conta_bancaria.conta_bancaria_model import ContaBancariaModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_view import inicializar_categorias_padrao, obter_subcategorias_recursivo
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_view import inicializar_categorias_padrao_categorizacao_fiscal, obter_subcategorias_recursivo_categorizacao_fiscal
from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
from sistema._utilitarios import *


@app.route("/financeiro/extrato-terceiros/freteiros", methods=["GET"])
@login_required
@requires_roles
def saldo_freteiros():
    if any(request.args.values()):
        numero_documento = request.args.get('numeroDocumento')
        telefone = request.args.get('telefone')

        numeroDocumento = ValidaDocs.somente_numeros(numero_documento) if numero_documento else None
        numeroTelefone = ValidaDocs.somente_numeros(telefone) if telefone else None

        transportadoras = TransportadoraModel.filtrar_transportadoras(
            identificacao=request.args.get('identificacao'),
            numero_documento=numeroDocumento,
            telefone=numeroTelefone
        )
    else:
        transportadoras = TransportadoraModel.listar_transportadoras()

    for t in transportadoras:
        credito = CreditoFreteiroModel.obtem_registro_id(t.id)
        t.valor_credito_100 = credito.valor_total_credito_100 if credito else 0

    return render_template(
        "financeiro/extrato_terceiros/listagem_terceiros/listagem_freteiros.html",
        transportadoras=transportadoras,
        dados_corretos=request.args
    )

@app.route("/financeiro/extrato-terceiros/freteiros/extrato-freteiro/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def extrato_freteiro(id):
    extrato = ExtratoCreditoFreteiroModel.listagem_historico_por_freteiro(id)
    transportadora = TransportadoraModel.obter_transportadora_por_id(id)

    if transportadora is None:
        flash(('Esta transportadora nâo possui dados a serem mostrados!', 'warning'))
        return redirect(url_for('saldo_freteiros'))

    saldo = CreditoFreteiroModel.obtem_registro_id(transportadora.id)
    saldo_credito_valor = saldo.valor_total_credito_100 if saldo else 0

    return render_template(
        "/financeiro/extrato_terceiros/extrato_credito_terceiros/extrato_credito_freteiro.html",
        dados_corretos=request.form,
        extrato=extrato, saldo=saldo_credito_valor,
        transportadora=transportadora
    )


@app.route("/financeiro/extrato-terceiros/freteiros/lancar-credito/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def lancar_credito_freteiro(id):
    try:
        validacao_campos_obrigatorios = {}
        validacao_campos_erros = {}
        gravar_banco = True

        transportadora = TransportadoraModel.obter_transportadora_por_id(id)

        if not transportadora:
            flash(("Transportadora informado não existe!", "success"))
            return redirect(url_for("saldo_freteiros"))
        
        contas_bancarias = ContaBancariaModel.obter_contas_bancarias_ativas()
        saldo = CreditoFreteiroModel.obtem_registro_id(transportadora.id)
        saldo_credito_valor = saldo.valor_total_credito_100 if saldo else 0

        if request.method == 'POST':
            data_movimentacao = request.form.get("data_movimentacao")
            valor_credito = request.form.get("valor_credito")
            descricao = request.form.get("descricao")
            contaBancaria = request.form.get("contaBancaria", "")
            tipo_valor = request.form.get("tipo_valor", "positivo")
            
            campos = {
                "data_movimentacao": ["Data movimentação", data_movimentacao],
                "valor_credito": ["Valor", valor_credito],
                "descricao": ["Descrição", descricao],
                "contaBancaria": ["Conta bancária", contaBancaria],
            }

            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

            if not "validado" in validacao_campos_obrigatorios:
                gravar_banco = False
                flash((f"Verifique os campos destacados em vermelho!", "warning"))

            if gravar_banco:

                valor_credito_formatado = (ValoresMonetarios.converter_string_brl_para_float(valor_credito) * 100)
                
                # Se o tipo for negativo, aplicar o sinal negativo ao valor
                if tipo_valor == "negativo":
                    valor_credito_formatado = -valor_credito_formatado
                
                # Determinar tipo de movimentação baseado no tipo de valor
                tipo_movimentacao_db = 1 if tipo_valor == "positivo" else 2

                novo_credito = ExtratoCreditoFreteiroModel (
                    tipo_movimentacao=tipo_movimentacao_db,
                    data_movimentacao = data_movimentacao,
                    descricao = descricao,
                    transportadora_id = transportadora.id,
                    usuario_id = current_user.id,
                    valor_credito_100 = valor_credito_formatado
                )

                db.session.add(novo_credito)
                db.session.flush()

                # Registrar pontuação de cadastro
                acao = TipoAcaoEnum.CADASTRO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id, acao, acao.pontos, modulo="lancamento_credito_freteiro"
                )

                # Atualiza tabela de credito
                verifica_lancamento = CreditoFreteiroModel.obtem_registro_id(transportadora.id)

                if not verifica_lancamento:
                    inclui_credito = CreditoFreteiroModel(
                        data_movimentacao=datetime.now(),
                        transportadora_id=transportadora.id,
                        valor_total_credito_100=valor_credito_formatado
                    )

                    db.session.add(inclui_credito)
                else:
                    credito_total = CreditoFreteiroModel.soma_credito_atual_com_novo_credito(transportadora.id, valor_credito_formatado)
                    verifica_lancamento.valor_total_credito_100 = credito_total

                # Faturamento - usar valor absoluto para o faturamento
                valor_faturamento = abs(valor_credito_formatado)
                
                # Determinar tipo de operação e direção baseado no tipo de valor
                if tipo_valor == "positivo":
                    tipo_operacao = 3  # Crédito
                    direcao_financeira = 2  # Despesa
                    valor_despesa = valor_faturamento
                    valor_receita = 0
                
                    faturamento = FaturamentoModel(
                        usuario_id=current_user.id,
                        valor_total=valor_faturamento,
                        valor_bruto_total=valor_faturamento,
                        valor_despesa=valor_despesa,
                        valor_receita=valor_receita,
                        codigo_faturamento=FaturamentoModel.gerar_codigo_novo_faturamento(),
                        tipo_operacao=tipo_operacao,
                        direcao_financeira=direcao_financeira,
                        situacao_pagamento_id=7, # A categorizar
                    )

                    db.session.add(faturamento)
                    db.session.flush()

                    conta_identificacao = ContaBancariaModel.obter_conta_por_id(contaBancaria)
                    
                    detalhes_credito_transportadora = [{
                        "transportadora_id": transportadora.id,
                        "transportadora_identificacao": transportadora.identificacao,
                        "data_movimentacao": data_movimentacao,
                        "credito_descricao": descricao,
                        "valor_credito_100": int(valor_credito_formatado),  # Usar valor absoluto nos detalhes
                        "extrato_credito_transportadora_id": novo_credito.id,
                        "conta_bancaria_id": conta_identificacao.identificacao if conta_identificacao else "Sem informação",
                    }]

                    faturamento.salvar_detalhes(credito_transportadora=detalhes_credito_transportadora)

                db.session.commit()
                tipo_msg = "Crédito" if tipo_valor == "positivo" else "Débito"
                flash((f"{tipo_msg} lançado com sucesso e faturamento registrado!", "success"))
                return redirect(url_for("saldo_freteiros"))

    except Exception as e:
        print(e)
        flash(('Houve um erro ao tentar cadastrar crédito para o freteiro! Entre em contato com o suporte.', 'warning'))
        return redirect(url_for('saldo_freteiros'))
    return render_template(
        "financeiro/extrato_terceiros/lancamento_credito_terceiros/lancar_credito_freteiro.html", campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
        transportadora=transportadora,
        contas_bancarias=contas_bancarias,
        saldo=saldo_credito_valor
    )
