from sistema import app, db, requires_roles, current_user
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from sistema.models_views.configuracoes_gerais.conta_bancaria.conta_bancaria_model import ContaBancariaModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.financeiro.movimentacao_financeira.saldo_movimentacao_financeira_model import SaldoMovimentacaoFinanceiraModel
from sistema._utilitarios import *


@app.route("/configuracoes/gerais/conta-bancaria/listar", methods=["GET"])
@login_required
@requires_roles
def listar_conta_bancaria():
    conta_bancaria = ContaBancariaModel.obter_contas_bancarias_ativas()
    return render_template(
        "configuracoes_gerais/conta_bancaria/conta_bancaria_listar.html", conta_bancaria=conta_bancaria
    )


@app.route("/configuracoes/gerais/conta-bancaria/cadastrar", methods=["GET", "POST"])
@login_required
@requires_roles
def cadastrar_conta_bancaria():
    try:
        validacao_campos_obrigatorios = {}
        validacao_campos_erros = {}
        gravar_banco = True


        if request.method == "POST":
            identificacao = request.form["identificacao"]
            nome_banco = request.form["nome_banco"]
            agencia = ValidaDocs.somente_numeros(request.form["agencia"])
            conta = ValidaDocs.somente_numeros(request.form["conta"])
            conta_principal = bool(request.form.get("conta_principal"))
            saldoInicial = request.form.get("saldoInicial")

            campos = {
                "identificacao": ["Identificação", identificacao],
                "nome_banco": ["Banco", nome_banco],
                "agencia": ["Agência", agencia],
                "conta": ["Conta", conta],
                "conta_principal": ["Conta Principal", conta_principal]
            }
            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
            if not "validado" in validacao_campos_obrigatorios:
                gravar_banco = False
                flash(("Verifique os campos destacados em vermelho!", "warning"))

            verifica_conta_principal = ContaBancariaModel.verifica_conta_bancaria_principal()
            if verifica_conta_principal and conta_principal == True:
                gravar_banco=False
                flash(('Não é possível cadastrar mais de uma conta principal!', 'warning'))

            if gravar_banco == True:

                nova = ContaBancariaModel(
                    identificacao=identificacao,
                    nome_banco=nome_banco,
                    agencia=agencia,
                    conta=conta,
                    conta_principal=conta_principal,
                    saldo_inicial_100=int(ValoresMonetarios.converter_string_brl_para_float(saldoInicial) * 100)
                )
                db.session.add(nova)
                db.session.flush()
                
                saldo = SaldoMovimentacaoFinanceiraModel(
                    data_movimentacao=DataHora.obter_data_atual_padrao_en(),
                    valor_total_saldo_100=int(ValoresMonetarios.converter_string_brl_para_float(saldoInicial) * 100),
                    conta_bancaria_id=nova.id
                )
                
                db.session.add(saldo)
                db.session.commit()
                
                TipoAcaoEnum.CADASTRO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    TipoAcaoEnum.CADASTRO,
                    TipoAcaoEnum.CADASTRO.pontos,
                    modulo="conta_bancaria",
                )

                flash(("Conta bancária cadastrada com sucesso!", "success"))
                return redirect(url_for("listar_conta_bancaria"))
    except Exception as e:
        flash(("Erro ao tentar cadastrar Conta Bancária! Entre em contato com o suporte.", "warning"))
        return redirect(url_for("listar_conta_bancaria"))

    return render_template(
        "configuracoes_gerais/conta_bancaria/conta_bancaria_cadastrar.html",
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
    )


@app.route(
    "/configuracoes/gerais/conta-bancaria/editar/<int:id>", methods=["GET", "POST"]
)
@login_required
@requires_roles
def editar_conta_bancaria(id):
    try:
        validacao_campos_obrigatorios = {}
        validacao_campos_erros = {}
        gravar_banco = True

        conta = ContaBancariaModel.obter_conta_por_id(id)
        if not conta:
            flash(("Conta não encontrada!", "warning"))
            return redirect(url_for("listar_conta_bancaria"))

        dados_corretos = {
            "identificacao": conta.identificacao,
            "nome_banco": conta.nome_banco,
            "agencia": conta.agencia,
            "conta": conta.conta,
            "conta_principal": conta.conta_principal,
            "saldoInicial": conta.saldo_inicial_100
        }

        if request.method == "POST":
            identificacao = request.form["identificacao"]
            nome_banco = request.form["nome_banco"]
            agencia = request.form["agencia"]
            conta_form = request.form["conta"]
            conta_principal = bool(request.form.get("conta_principal"))
            saldoInicial = request.form.get("saldoInicial")

            campos = {
                "identificacao": ["Identificação", identificacao],
                "nome_banco": ["Banco", nome_banco],
                "agencia": ["Agência", agencia],
                "conta": ["Conta", conta_form],
            }
            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
            if not "validado" in validacao_campos_obrigatorios:
                flash(("Verifique os campos destacados em vermelho!", "warning"))

            verifica_conta_principal = ContaBancariaModel.verifica_conta_bancaria_principal()
            if verifica_conta_principal.id != conta.id and conta_principal:
                gravar_banco=False
                flash(('Não é possível cadastrar mais de uma conta principal!', 'warning'))

            if gravar_banco == True:
                conta.identificacao = identificacao
                conta.nome_banco = nome_banco
                conta.agencia = agencia
                conta.conta = conta_form
                conta.conta_principal = conta_principal
                conta.saldo_inicial_100 = int(ValoresMonetarios.converter_string_brl_para_float(saldoInicial) * 100)

                saldo = SaldoMovimentacaoFinanceiraModel.obter_registro_conta_bancaria(conta.id)
                if saldo:
                    saldo.valor_total_saldo_100 = int(ValoresMonetarios.converter_string_brl_para_float(saldoInicial) * 100)
                
                db.session.commit()

                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    TipoAcaoEnum.EDICAO,
                    TipoAcaoEnum.EDICAO.pontos,
                    modulo="conta_bancaria",
                )

                flash(("Conta bancária editada com sucesso!", "success"))
                return redirect(url_for("listar_conta_bancaria"))
    except Exception as e:
        flash(("Erro ao tentar editar Conta Bancária! Entre em contato com o suporte.", "warning"))
        return redirect(url_for("listar_conta_bancaria"))

    return render_template(
        "configuracoes_gerais/conta_bancaria/conta_bancaria_editar.html",
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=dados_corretos,
        conta=conta
    )


@app.route("/configuracoes/gerais/conta-bancaria/excluir/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def excluir_conta_bancaria(id):
    try:
        conta = ContaBancariaModel.obter_conta_por_id(id)
        if not conta:
            flash(("Conta não encontrada!", "warning"))
        else:
            conta.ativo = False
            conta.deletado = True
            
            saldo = SaldoMovimentacaoFinanceiraModel.obter_registro_conta_bancaria(conta.id)
            if saldo:
                saldo.ativo = False
                saldo.deletado = True 
            
            db.session.commit()
            flash(("Conta bancária excluída com sucesso!", "success"))
        return redirect(url_for("listar_conta_bancaria"))
    
    except Exception as e:
        flash(("Erro ao tentar excluir Conta Bancária! Entre em contato com o suporte.", "warning"))
        return redirect(url_for("listar_conta_bancaria"))
