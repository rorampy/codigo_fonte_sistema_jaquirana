from datetime import datetime
from sistema import app, requires_roles, db
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.gerenciar.extrator.extrator_model import ExtratorModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.financeiro.movimentacao_financeira.movimentacao_financeira_model import MovimentacaoFinanceiraModel
from sistema.models_views.financeiro.movimentacao_financeira.saldo_movimentacao_financeira_model import SaldoMovimentacaoFinanceiraModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_model import CategorizacaoFiscalModel
from sistema.models_views.configuracoes_gerais.conta_bancaria.conta_bancaria_model import ContaBancariaModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_view import inicializar_categorias_padrao, obter_subcategorias_recursivo
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_view import inicializar_categorias_padrao_categorizacao_fiscal, obter_subcategorias_recursivo_categorizacao_fiscal
from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
from sistema._utilitarios import *

from sistema.models_views.financeiro.controle_adiantamentos.servico_creditos import ServicoCreditos
from sistema.models_views.financeiro.controle_adiantamentos.transacao_credito_model import (TransacaoCreditoModel, TipoTransacaoCredito, TipoPessoa)
from sistema.models_views.financeiro.controle_adiantamentos.faturamento_credito_vinculo_model import FaturamentoCreditoVinculoModel
from sistema.models_views.financeiro.controle_adiantamentos.historico_transacao_model import HistoricoTransacaoCreditoModel, AcaoHistoricoCredito

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
        e.valor_credito_100 = ServicoCreditos.obter_saldo_extrator(e.id)
        
    return render_template(
        "financeiro/extrato_terceiros/listagem_terceiros/listagem_extratores.html",
        extratores=extratores,
        dados_corretos=request.args
    )

@app.route("/financeiro/extrato_terceiros/extratores/extrato-extrator/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def extrato_extrator(id):
    extrato = ServicoCreditos.obter_historico_extrator(id)
    extrator = ExtratorModel.obter_extrator_por_id(id)
    
    if extrator is None:
        flash(('Este extrator nâo possui dados a serem mostrados!', 'warning'))
        return redirect(url_for('saldo_extratores'))
    
    saldo_credito_valor = ServicoCreditos.obter_saldo_extrator(id)

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
        saldo_credito_valor = ServicoCreditos.obter_saldo_extrator(extrator.id)

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

                valor_credito_formatado = int(ValoresMonetarios.converter_string_brl_para_float(valor_credito) * 100)
                
                if tipo_valor == "negativo":
                    valor_credito_formatado = -1 * valor_credito_formatado

                resultado_lancamento = ServicoCreditos.lancar_credito_extrator(
                    extrator_id=extrator.id,
                    valor_100=valor_credito_formatado,
                    descricao=descricao,
                    usuario_id=current_user.id,
                    data_movimentacao=datetime.strptime(data_movimentacao, '%Y-%m-%d').date() if isinstance(data_movimentacao, str) else data_movimentacao,
                    tipo_valor=tipo_valor,
                    conta_bancaria_id=int(contaBancaria) if contaBancaria else None,
                )

                acao = TipoAcaoEnum.CADASTRO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id, acao, acao.pontos, modulo="lancamento_credito_extrator"
                )

                valor_faturamento = abs(valor_credito_formatado)
                if tipo_valor == "positivo":
                    tipo_operacao = 3
                    direcao_financeira = 2
                    valor_despesa = valor_faturamento
                    valor_receita = 0
                else:
                    tipo_operacao = 4
                    direcao_financeira = 1
                    valor_despesa = 0
                    valor_receita = valor_faturamento
                
                faturamento = FaturamentoModel(
                    usuario_id=current_user.id,
                    valor_total=valor_faturamento,
                    valor_bruto_total=valor_faturamento,
                    valor_despesa=valor_despesa,
                    valor_receita=valor_receita,
                    codigo_faturamento=FaturamentoModel.gerar_codigo_novo_faturamento(),
                    tipo_operacao=tipo_operacao,
                    direcao_financeira=direcao_financeira,
                    situacao_pagamento_id=7,
                )
                
                db.session.add(faturamento) 
                db.session.flush()
                
                transacao_nova_id = resultado_lancamento.get('novo_id')
                if transacao_nova_id:
                    transacao = TransacaoCreditoModel.query.get(transacao_nova_id)
                    if transacao:
                        transacao.faturamento_origem_id = faturamento.id
                
                conta_identificacao = ContaBancariaModel.obter_conta_por_id(contaBancaria)
                
                extrato_legado_id = resultado_lancamento.get('legado_id')
                
                detalhes_credito_extrator = [{
                    "extrator_id": extrator.id,
                    "extrator_identificacao": extrator.identificacao,
                    "data_movimentacao": data_movimentacao,
                    "credito_descricao": descricao,
                    "valor_credito_100": int(valor_faturamento),
                    "extrato_credito_extrator_id": extrato_legado_id,
                    "transacao_credito_id": transacao_nova_id,
                    "conta_bancaria_id": conta_identificacao.identificacao if conta_identificacao else "Sem informação",
                }]

                faturamento.salvar_detalhes(credito_extrator=detalhes_credito_extrator)
                if transacao_nova_id:
                    vinculo = FaturamentoCreditoVinculoModel(
                        faturamento_id=faturamento.id,
                        transacao_credito_id=transacao_nova_id,
                        tipo_pessoa=TipoPessoa.EXTRATOR,
                        valor_aplicado_100=valor_faturamento,
                        usuario_id=current_user.id,
                        extrato_credito_extrator_id=extrato_legado_id,
                        extrator_id=extrator.id
                    )
                    db.session.add(vinculo)
                    if transacao_nova_id:
                        vinculo = FaturamentoCreditoVinculoModel(
                            faturamento_id=faturamento.id,
                            transacao_credito_id=transacao_nova_id,
                            tipo_pessoa=TipoPessoa.EXTRATOR,
                            valor_aplicado_100=valor_faturamento,
                            usuario_id=current_user.id,
                            extrato_credito_extrator_id=extrato_legado_id,
                            extrator_id=extrator.id
                        )
                        db.session.add(vinculo)

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


@app.route("/financeiro/extrato-terceiros/extratores/excluir-credito/<int:credito_id>", methods=["POST"])
@login_required
@requires_roles
def excluir_credito_extrator(credito_id):
    """
    Exclui um lançamento de crédito de extrator.
    Utiliza ServicoCreditos para operação unificada.
    """
    try:
        motivo = request.form.get("motivo", "")
        extrator_id = request.form.get("extrator_id")
        
        resultado = ServicoCreditos.excluir_credito(
            tipo='extrator',
            credito_id=credito_id,
            usuario_id=current_user.id,
            motivo=motivo
        )
        
        if resultado['sucesso']:
            flash((resultado['mensagem'], "success"))
        else:
            flash((resultado['mensagem'], "warning"))
        
        if extrator_id:
            return redirect(url_for("extrato_extrator", id=extrator_id))
        return redirect(url_for("saldo_extratores"))
        
    except Exception as e:
        flash(("Erro ao excluir crédito. Entre em contato com o suporte.", "danger"))
        return redirect(url_for("saldo_extratores"))


@app.route("/financeiro/extrato-terceiros/extratores/editar-credito/<int:credito_id>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_credito_extrator(credito_id):
    """
    Edita um lançamento de crédito de extrator.
    GET: Exibe formulário de edição
    POST: Processa a edição
    """
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    
    try:
        credito = TransacaoCreditoModel.query.get(credito_id)
        if not credito:
            flash(("Crédito não encontrado!", "warning"))
            return redirect(url_for("saldo_extratores"))
        
        extrator = ExtratorModel.obter_extrator_por_id(credito.extrator_id)
        if not extrator:
            flash(("Extrator não encontrado!", "warning"))
            return redirect(url_for("saldo_extratores"))
        
        if credito.valor_utilizado_100 and credito.valor_utilizado_100 > 0:
            flash(("Este crédito já foi utilizado e não pode ser editado!", "warning"))
            return redirect(url_for("extrato_extrator", id=extrator.id))
        
        saldo_credito_valor = ServicoCreditos.obter_saldo_extrator(extrator.id)
        
        if request.method == "GET":
            return render_template(
                "financeiro/extrato_terceiros/lancamento_credito_terceiros/editar_credito_extrator.html",
                credito=credito,
                extrator=extrator,
                saldo=saldo_credito_valor,
                campos_obrigatorios=validacao_campos_obrigatorios,
                campos_erros=validacao_campos_erros,
                dados_corretos={},
            )
        
        valor_credito = request.form.get("valor_credito")
        descricao = request.form.get("descricao")
        data_movimentacao = request.form.get("data_movimentacao")
        extrator_id = request.form.get("extrator_id")
        tipo_valor = request.form.get("tipo_valor", "positivo")
        
        campos = {
            "data_movimentacao": ["Data movimentação", data_movimentacao],
            "valor_credito": ["Valor", valor_credito],
            "descricao": ["Descrição", descricao],
            "tipo_valor": ["Tipo de valor", tipo_valor],
        }
        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
        
        if not "validado" in validacao_campos_obrigatorios:
            flash(("Verifique os campos destacados em vermelho!", "warning"))
            return render_template(
                "financeiro/extrato_terceiros/lancamento_credito_terceiros/editar_credito_extrator.html",
                credito=credito,
                extrator=extrator,
                saldo=saldo_credito_valor,
                campos_obrigatorios=validacao_campos_obrigatorios,
                campos_erros=validacao_campos_erros,
                dados_corretos=request.form,
            )
        
        valor_100 = None
        if valor_credito:
            valor_100 = int(ValoresMonetarios.converter_string_brl_para_float(valor_credito) * 100)
            if tipo_valor == "negativo":
                valor_100 = -abs(valor_100)
            else:
                valor_100 = abs(valor_100)
        
        data_mov = None
        if data_movimentacao:
            data_mov = datetime.strptime(data_movimentacao, '%Y-%m-%d').date()
        
        resultado = ServicoCreditos.editar_credito_extrator(
            credito_id=credito_id,
            valor_100=valor_100,
            descricao=descricao if descricao else None,
            data_movimentacao=data_mov,
            tipo_valor=tipo_valor,
            usuario_id=current_user.id
        )
        
        if resultado['sucesso']:
            flash((resultado['mensagem'], "success"))
            
            try:
                PontuacaoUsuarioModel.registrar_acao(
                    usuario_id=current_user.id,
                    tipo_acao=TipoAcaoEnum.ATUALIZAR,
                    pontos=5,
                    descricao=f"Edição de lançamento de crédito ID {credito_id}"
                )
            except:
                pass
        else:
            flash((resultado['mensagem'], "warning"))
        
        if extrator_id:
            return redirect(url_for("extrato_extrator", id=extrator_id))
        return redirect(url_for("saldo_extratores"))
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(("Erro ao editar crédito. Entre em contato com o suporte.", "danger"))
        return redirect(url_for("saldo_extratores"))