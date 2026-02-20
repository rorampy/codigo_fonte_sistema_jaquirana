from datetime import datetime
from sistema import app, requires_roles, db
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.configuracoes_gerais.conta_bancaria.conta_bancaria_model import ContaBancariaModel
from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_cadastro_model import FornecedorCadastroModel
from sistema._utilitarios import *

from sistema.models_views.financeiro.controle_adiantamentos.servico_creditos import ServicoCreditos
from sistema.models_views.financeiro.controle_adiantamentos.transacao_credito_model import (
    TransacaoCreditoModel, TipoPessoa
)
from sistema.models_views.financeiro.controle_adiantamentos.faturamento_credito_vinculo_model import FaturamentoCreditoVinculoModel
from sistema.models_views.financeiro.controle_adiantamentos.historico_transacao_model import HistoricoTransacaoCreditoModel, AcaoHistoricoCredito


@app.route("/financeiro/extrato_terceiros/fornecedores", methods=["GET"])
@login_required
@requires_roles
def saldo_fornecedores():
    if any(request.args.values()):
        numeroDoc = request.args.get("numeroDocumento")
        numeroDocFormatado = ValidaDocs.somente_numeros(numeroDoc) if numeroDoc else None

        celular = request.args.get("celular")
        celularFormatado = ValidaDocs.somente_numeros(celular) if celular else None
        
        fornecedores = FornecedorCadastroModel.filtrar_fornecedores(
            identificacao=request.args.get("identificacao"),
            numero_documento=numeroDocFormatado,
            celular=celularFormatado,
        )
    else:
        fornecedores = FornecedorCadastroModel.listar_fornecedores()
    for f in fornecedores:
        f.valor_credito_100 = ServicoCreditos.obter_saldo_fornecedor(f.id)
        
    return render_template(
        "/financeiro/extrato_terceiros/listagem_terceiros/listagem_fornecedores.html",
        fornecedores=fornecedores,
        dados_corretos=request.args,
    )


@app.route("/financeiro/extrato_terceiros/fornecedores/extrato-fornecedor/<int:id>",methods=["GET", "POST"],)
@login_required
@requires_roles
def extrato_fornecedor(id):
    extrato = ServicoCreditos.obter_historico_fornecedor(id)
    fornecedor = FornecedorCadastroModel.obter_fornecedor_por_id(id)
    
    if fornecedor is None:
        flash(("Este fornecedor nâo possui dados a serem mostrados!", "warning"))
        return redirect(url_for("saldo_extratores"))
    
    saldo_credito_valor = ServicoCreditos.obter_saldo_fornecedor(fornecedor.id)

    return render_template(
        "/financeiro/extrato_terceiros/extrato_credito_terceiros/extrato_credito_fornecedor.html",
        dados_corretos=request.form,
        extrato=extrato,
        saldo=saldo_credito_valor,
        fornecedor=fornecedor,
    )


@app.route("/financeiro/extrato-terceiros/fornecedores/lancar-credito/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def lancar_credito_fornecedor(id):
    try:
        validacao_campos_obrigatorios = {}
        validacao_campos_erros = {}
        gravar_banco = True

        fornecedor = FornecedorCadastroModel.obter_fornecedor_por_id(id)

        if not fornecedor:
            flash(("Fornecedor informado não existe!", "warning"))
            return redirect(url_for("saldo_fornecedores"))

        contas_bancarias = ContaBancariaModel.obter_contas_bancarias_ativas()
      
      
        saldo_credito_valor = ServicoCreditos.obter_saldo_fornecedor(fornecedor.id)

        if request.method == "POST":
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

                resultado_lancamento = ServicoCreditos.lancar_credito_fornecedor(
                    fornecedor_id=fornecedor.id,
                    valor_100=valor_credito_formatado,
                    descricao=descricao,
                    usuario_id=current_user.id,
                    data_movimentacao=datetime.strptime(data_movimentacao, '%Y-%m-%d').date() if isinstance(data_movimentacao, str) else data_movimentacao,
                    tipo_valor=tipo_valor,
                    conta_bancaria_id=int(contaBancaria) if contaBancaria else None,
                )

                acao = TipoAcaoEnum.CADASTRO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    acao,
                    acao.pontos,
                    modulo="lancamento_credito_fornecedor",
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
                
                detalhes_credito_fornecedor = [{
                    "fornecedor_id": fornecedor.id,
                    "fornecedor_identificacao": fornecedor.identificacao,
                    "data_movimentacao": data_movimentacao,
                    "credito_descricao": descricao,
                    "valor_credito_100": int(valor_faturamento),
                    "extrato_credito_fornecedor_id": extrato_legado_id,
                    "transacao_credito_id": transacao_nova_id,
                    "conta_bancaria_id": conta_identificacao.identificacao if conta_identificacao else "Sem informação",
                }]
                
                faturamento.salvar_detalhes(credito_fornecedor=detalhes_credito_fornecedor)
                
                if transacao_nova_id:
                    vinculo = FaturamentoCreditoVinculoModel(
                        faturamento_id=faturamento.id,
                        transacao_credito_id=transacao_nova_id,
                        tipo_pessoa=TipoPessoa.FORNECEDOR,
                        valor_aplicado_100=valor_faturamento,
                        usuario_id=current_user.id,
                        extrato_credito_fornecedor_id=extrato_legado_id,
                        fornecedor_id=fornecedor.id
                    )
                    db.session.add(vinculo)

                db.session.commit()
                tipo_msg = "Crédito" if tipo_valor == "positivo" else "Débito"
                flash((f"{tipo_msg} lançado com sucesso e faturamento atualizado!", "success"))
                return redirect(url_for("saldo_fornecedores"))

    except Exception as e:
        flash(("Houve um erro ao tentar cadastrar crédito para o fornecedor! Entre em contato com o suporte.", "warning"))
        return redirect(url_for("saldo_fornecedores"))
    return render_template(
        "financeiro/extrato_terceiros/lancamento_credito_terceiros/lancar_credito_fornecedor.html",
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
        fornecedor=fornecedor,
        contas_bancarias=contas_bancarias,
        saldo=saldo_credito_valor,
    )


@app.route("/financeiro/extrato-terceiros/fornecedores/excluir-credito/<int:credito_id>", methods=["POST"])
@login_required
@requires_roles
def excluir_credito_fornecedor(credito_id):
    """
    Exclui um lançamento de crédito de fornecedor.
    Utiliza ServicoCreditos para operação unificada.
    """
    try:
        motivo = request.form.get("motivo", "")
        fornecedor_id = request.form.get("fornecedor_id")
        
        resultado = ServicoCreditos.excluir_credito(
            tipo='fornecedor',
            credito_id=credito_id,
            usuario_id=current_user.id,
            motivo=motivo
        )
        
        if resultado['sucesso']:
            flash((resultado['mensagem'], "success"))
        else:
            flash((resultado['mensagem'], "warning"))
        
        if fornecedor_id:
            return redirect(url_for("extrato_fornecedor", id=fornecedor_id))
        return redirect(url_for("saldo_fornecedores"))
        
    except Exception as e:
        flash(("Erro ao excluir crédito. Entre em contato com o suporte.", "danger"))
        return redirect(url_for("saldo_fornecedores"))


@app.route("/financeiro/extrato-terceiros/fornecedores/editar-credito/<int:credito_id>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_credito_fornecedor(credito_id):
    """
    Edita um lançamento de crédito de fornecedor.
    GET: Exibe formulário de edição
    POST: Processa a edição
    """
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    
    try:
        credito = TransacaoCreditoModel.query.get(credito_id)
        if not credito:
            flash(("Crédito não encontrado!", "warning"))
            return redirect(url_for("saldo_fornecedores"))
        
        fornecedor = FornecedorCadastroModel.obter_fornecedor_por_id(credito.fornecedor_id)
        if not fornecedor:
            flash(("Fornecedor não encontrado!", "warning"))
            return redirect(url_for("saldo_fornecedores"))
        
        if credito.valor_utilizado_100 and credito.valor_utilizado_100 > 0:
            flash(("Este crédito já foi utilizado e não pode ser editado!", "warning"))
            return redirect(url_for("extrato_fornecedor", id=fornecedor.id))
        
        saldo_credito_valor = ServicoCreditos.obter_saldo_fornecedor(fornecedor.id)
        
        if request.method == "GET":
            return render_template(
                "financeiro/extrato_terceiros/lancamento_credito_terceiros/editar_credito_fornecedor.html",
                credito=credito,
                fornecedor=fornecedor,
                saldo=saldo_credito_valor,
                campos_obrigatorios=validacao_campos_obrigatorios,
                campos_erros=validacao_campos_erros,
                dados_corretos={},
            )
        
        valor_credito = request.form.get("valor_credito")
        descricao = request.form.get("descricao")
        data_movimentacao = request.form.get("data_movimentacao")
        fornecedor_id = request.form.get("fornecedor_id")
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
                "financeiro/extrato_terceiros/lancamento_credito_terceiros/editar_credito_fornecedor.html",
                credito=credito,
                fornecedor=fornecedor,
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
        
        resultado = ServicoCreditos.editar_credito_fornecedor(
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
        
        if fornecedor_id:
            return redirect(url_for("extrato_fornecedor", id=fornecedor_id))
        return redirect(url_for("saldo_fornecedores"))
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(("Erro ao editar crédito. Entre em contato com o suporte.", "danger"))
        return redirect(url_for("saldo_fornecedores"))
