from sistema import app, requires_roles, db, current_user
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from sistema.models_views.parametros.nome_grupo_whats.nome_grupo_whats_model import NomeGrupoWhatsModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema._utilitarios import *


@app.route("/parametros/grupos/cadastrar", methods=["GET", "POST"])
@login_required
@requires_roles
def cadastrar_grupo():
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    if request.method == "POST":
        nomeGrupo = request.form["nomeGrupo"]
        campos = {
            "nomeGrupo": ["Nome Grupo", nomeGrupo],
        }

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))

        if gravar_banco == True:
            parametro = NomeGrupoWhatsModel(nome_grupo_whats=nomeGrupo, ativo=True)
            db.session.add(parametro)
            db.session.commit()
            acao = TipoAcaoEnum.CADASTRO
            PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                current_user.id,
                acao,
                acao.pontos,
                modulo='grupo_whatsapp'
            )
            flash(("Grupo cadastrado com sucesso!", "success"))
            return redirect(url_for("listar_grupos"))
    return render_template(
        "parametros/nome_grupo_whats/nome_grupo_whats_cadastrar.html",
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
    )


@app.route("/parametros/grupos/whatsapp", methods=["GET", "POST"])
@login_required
@requires_roles
def listar_grupos():
    grupos = NomeGrupoWhatsModel.listar_grupos()
    return render_template(
        "parametros/nome_grupo_whats/nome_grupo_whats_listar.html", grupos=grupos
    )


@app.route("/gerenciar/parametro/editar/grupo/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_grupo(id):
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    grupo = NomeGrupoWhatsModel.obter_grupo_por_id(id)

    if grupo is None:
        flash(("Grupo não encontrado!", "warning"))
        return redirect(url_for("listar_grupos"))

    if grupo.ativo == 0:
        flash(("Este grupo não pode ser editado, pois está desativado!", "warning"))
        return redirect(url_for("listar_grupos"))

    dados_corretos = {"nomeGrupo": grupo.nome_grupo_whats}

    if request.method == "POST":
        nomeGrupo = request.form["nomeGrupo"]
        campos = {
            "nomeGrupo": ["Nome Grupo", nomeGrupo],
        }

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))

        if gravar_banco == True:
            
            obj1 = {
                "nomeGrupo": grupo.nome_grupo_whats.strip() if grupo.nome_grupo_whats else "",
            }

            obj2 = {
                "nomeGrupo": nomeGrupo.strip(),
            }

            diferencas = Gameficacao.compara_objetos(obj1, obj2)
            if diferencas:
                acao = TipoAcaoEnum.EDICAO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    acao,
                    acao.pontos,
                    modulo='grupo_whatsapp'
                )

            grupo.nome_grupo_whats = nomeGrupo
            db.session.commit()
            
            flash(("Grupo editado com sucesso!", "success"))
            return redirect(url_for("listar_grupos"))
    return render_template(
        "parametros/nome_grupo_whats/nome_grupo_whats_editar.html",
        grupo=grupo,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=dados_corretos,
    )


@app.route("/gerenciar/parametro/desativar/grupo/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def desativar_grupo(id):
    grupo = NomeGrupoWhatsModel.obter_grupo_por_id(id)

    if grupo is None:
        flash(("Grupo não encontrado!", "warning"))

    grupo.ativo = 0
    db.session.commit()
    flash(("Grupo desativado com sucesso!", "success"))
    return redirect(url_for("listar_grupos"))


@app.route("/gerenciar/parametro/ativar/grupo/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def ativar_grupo(id):
    grupo = NomeGrupoWhatsModel.obter_grupo_por_id(id)

    if grupo is None:
        flash(("Grupo não encontrado!", "warning"))

    grupo.ativo = 1
    db.session.commit()
    flash(("Grupo ativado com sucesso!", "success"))
    return redirect(url_for("listar_grupos"))
