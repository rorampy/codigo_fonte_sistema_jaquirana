from sistema import app, requires_roles, db, current_user
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema._utilitarios import *


@app.route("/parametros/bitola/cadastrar", methods=["GET", "POST"])
@login_required
@requires_roles
def cadastrar_bitola():
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    if request.method == "POST":
        bitolaParametro = request.form["bitolaParametro"]
        campos = {
            "bitolaParametro": ["Bitola", bitolaParametro],
        }

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))

        if gravar_banco == True:
            parametro = BitolaModel(bitola=bitolaParametro)
            db.session.add(parametro)
            db.session.commit()
            acao = TipoAcaoEnum.CADASTRO
            PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                current_user.id,
                acao,
                acao.pontos,
                modulo='bitola'
            )
            flash(("Bitola cadastrada com sucesso!", "success"))
            return redirect(url_for("listar_bitolas"))
    return render_template(
        "parametros/bitola/bitola_cadastrar.html",
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
    )


@app.route("/parametros/bitolas", methods=["GET", "POST"])
@login_required
@requires_roles
def listar_bitolas():
    parametros = BitolaModel.listar_bitolas()
    return render_template("parametros/bitola/bitola_listar.html", parametros=parametros)


@app.route("/gerenciar/parametro/editar/bitola/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_bitola(id):
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    parametro = BitolaModel.obter_bitola_por_id(id)

    if parametro is None:
        flash(("Bitola não encontrada!", "warning"))
        return redirect(url_for("listar_bitolas"))

    if request.method == "POST":
        bitolaParametro = request.form["bitolaParametro"]
        campos = {
            "bitolaParametro": ["Bitola", bitolaParametro],
        }

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))

        if gravar_banco == True:

            obj1 = {
                "bitola": parametro.bitola.strip() if parametro.bitola else ""
            }

            obj2 = {
                "bitola": bitolaParametro.strip()   
            }

            diferencas = Gameficacao.compara_objetos(obj1, obj2)
            if diferencas:
                acao = TipoAcaoEnum.EDICAO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    acao,
                    acao.pontos,
                    modulo='bitola'
                )

            parametro.bitola = bitolaParametro
            db.session.commit()
            flash(("Bitola editada com sucesso!", "success"))
            return redirect(url_for("listar_bitolas"))
    return render_template(
        "parametros/bitola/bitola_editar.html",
        parametro=parametro,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
    )


@app.route("/gerenciar/parametro/desativar/bitola/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def desativar_bitola(id):
    parametro = BitolaModel.obter_bitola_por_id(id)

    if parametro is None:
        flash(("Bitola não encontrada!", "warning"))
    
    parametro.ativo = 0
    db.session.commit()
    flash(("Bitola excluida com sucesso!", "success"))
    return redirect(url_for("listar_bitolas"))

@app.route("/gerenciar/parametro/ativar/bitola/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def ativar_bitola(id):
    parametro = BitolaModel.obter_bitola_por_id(id)

    if parametro is None:
        flash(("Bitola não encontrada!", "warning"))
    
    parametro.ativo = 1
    db.session.commit()
    flash(("Bitola excluida com sucesso!", "success"))
    return redirect(url_for("listar_bitolas"))