from datetime import datetime
from sistema import app, requires_roles, db
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.gerenciar.extrator.extrator_model import ExtratorModel
from sistema.models_views.faturamento.controle_credito.extrato_credito.extrato_credito_extrator_model import ExtratoCreditoExtratorModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.financeiro.movimentacao_financeira.movimentacao_financeira_model import MovimentacaoFinanceiraModel
from sistema.models_views.faturamento.controle_credito.credito_agrupado.credito_extrator_model import CreditoExtratorModel
from sistema.models_views.financeiro.movimentacao_financeira.saldo_movimentacao_financeira_model import SaldoMovimentacaoFinanceiraModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_model import CategorizacaoFiscalModel
from sistema.models_views.configuracoes_gerais.conta_bancaria.conta_bancaria_model import ContaBancariaModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_view import inicializar_categorias_padrao, obter_subcategorias_recursivo
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_view import inicializar_categorias_padrao_categorizacao_fiscal, obter_subcategorias_recursivo_categorizacao_fiscal
from sistema.models_views.faturamento.faturamento_model import FaturamentoModel
from sistema._utilitarios import *

@app.route("/financeiro/extrato-terceiros/extratores", methods=["GET"])
@login_required
@requires_roles
def saldo_extratores():
    if any(request.args.values()):
        numero_documento = request.args.get('numeroDocumento')
        telefone = request.args.get('telefone')
        
        numeroDocumento = ValidaDocs.somente_numeros(numero_documento) if numero_documento else None
        numeroTelefone = ValidaDocs.somente_numeros(telefone) if telefone else None

        extratores = ExtratorModel.filtrar_extratores(
            identificacao=request.args.get('identificacao'),
            numero_documento=numeroDocumento,
            telefone=numeroTelefone
        )
    else:
        extratores = ExtratorModel.listar_extratores()
        
    for e in extratores:
        credito = CreditoExtratorModel.obtem_registro_extrator_id(e.id)
        e.valor_credito_100 = credito.valor_total_credito_100 if credito else 0
        
    return render_template(
        "financeiro/extrato_terceiros/listagem_terceiros/listagem_extratores.html",
        extratores=extratores,
        dados_corretos=request.args
    )

@app.route("/financeiro/extrato_terceiros/extratores/extrato-extrator/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def extrato_extrator(id):
    extrato = ExtratoCreditoExtratorModel.listagem_historico_por_extrator(id)
    extrator = ExtratorModel.obter_extrator_por_id(id)
    if extrator is None:
        flash(('Este extrator nâo possui dados a serem mostrados!', 'warning'))
        return redirect(url_for('saldo_extratores'))
    saldo = CreditoExtratorModel.obtem_registro_extrator_id(id)
    saldo_credito_valor = saldo.valor_total_credito_100 if saldo else 0

    return render_template(
        "/financeiro/extrato_terceiros/extrato_credito_terceiros/extrato_credito_extrator.html",
        dados_corretos=request.form,
        extrato=extrato, saldo=saldo_credito_valor,
        extrator=extrator
    )

@app.route("/financeiro/extrato-terceiros/extratores/lancar-credito/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def lancar_credito_extrator(id):
    try:
        validacao_campos_obrigatorios = {}
        validacao_campos_erros = {}
        gravar_banco = True

        extrator = ExtratorModel.obter_extrator_por_id(id)

        if not extrator:
            flash(("Extrator informado não existe!", "success"))
            return redirect(url_for("saldo_extratores"))
        
        contas_bancarias = ContaBancariaModel.obter_contas_bancarias_ativas()
        saldo = CreditoExtratorModel.obtem_registro_extrator_id(extrator.id)
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

                novo_credito = ExtratoCreditoExtratorModel(
                    data_movimentacao=data_movimentacao,
                    descricao=descricao,
                    extrator_id=extrator.id,
                    usuario_id=current_user.id,
                    tipo_movimentacao=tipo_movimentacao_db,
                    valor_credito_100=valor_credito_formatado,
                )

                db.session.add(novo_credito)
                db.session.flush()

                # Registrar pontuação de cadastro
                acao = TipoAcaoEnum.CADASTRO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id, acao, acao.pontos, modulo="lancamento_credito_extrator"
                )

                # Atualiza tabela de credito
                verifica_lancamento = CreditoExtratorModel.obtem_registro_extrator_id(extrator.id)

                if not verifica_lancamento:
                    inclui_credito = CreditoExtratorModel(
                        data_movimentacao=datetime.now(),
                        extrator_id=extrator.id,
                        valor_total_credito_100=valor_credito_formatado
                    )

                    db.session.add(inclui_credito)
                else:
                    credito_total = CreditoExtratorModel.soma_credito_atual_com_novo_credito(extrator.id, valor_credito_formatado)
                    verifica_lancamento.valor_total_credito_100 = credito_total

                # Faturamento - usar valor absoluto para o faturamento
                valor_faturamento = abs(valor_credito_formatado)
                
                # Determinar tipo de operação e direção baseado no tipo de valor
                if tipo_valor == "positivo":
                    tipo_operacao = 3  # Crédito
                    direcao_financeira = 2  # Despesa (empresa paga crédito ao extrator)
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
                    
                    detalhes_credito_extrator = [{
                        "extrator_id": extrator.id,
                        "extrator_identificacao": extrator.identificacao,
                        "data_movimentacao": data_movimentacao,
                        "credito_descricao": descricao,
                        "valor_credito_100": int(valor_credito_formatado),  # Usar valor absoluto nos detalhes
                        "extrato_credito_extrator_id": novo_credito.id,
                        "conta_bancaria_id": conta_identificacao.identificacao if conta_identificacao else "Sem informação",
                    }]

                    faturamento.salvar_detalhes(credito_extrator=detalhes_credito_extrator)

                db.session.commit()
                tipo_msg = "Crédito" if tipo_valor == "positivo" else "Débito"
                flash((f"{tipo_msg} lançado com sucesso e faturamento atualizado!", "success"))
                return redirect(url_for("saldo_extratores"))

    except Exception as e:
        flash(('Houve um erro ao tentar cadastrar crédito para o extrator! Entre em contato com o suporte.', 'warning'))
        return redirect(url_for('saldo_extratores'))
    return render_template(
        "financeiro/extrato_terceiros/lancamento_credito_terceiros/lancar_credito_extrator.html", campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
        extrator=extrator,
        contas_bancarias=contas_bancarias,
        saldo=saldo_credito_valor
    )