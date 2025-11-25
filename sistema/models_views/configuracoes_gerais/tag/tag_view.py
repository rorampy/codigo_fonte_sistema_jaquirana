from sistema import app, db, requires_roles, current_user
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.configuracoes_gerais.tag.tag_model import TagModel
from sistema._utilitarios import *


@app.route("/configuracoes/gerais/tags/listar", methods=["GET"])
@login_required
@requires_roles
def listar_tags():
    try:
        tags = TagModel.obter_tags_ativas()
        return render_template(
            "configuracoes_gerais/tag/tag_listar.html", tags=tags   
        )
    except Exception as e:
        flash(("Erro ao tentar listar Tags! Entre em contato com o suporte.", "warning"))
        return render_template(
            "configuracoes_gerais/tag/tag_listar.html", tags=[]   
        )

@app.route("/configuracoes/gerais/tag/cadastrar", methods=["GET", "POST"])
@login_required
@requires_roles
def cadastrar_tag():
    try:
        validacao_campos_obrigatorios = {}
        validacao_campos_erros = {}
        gravar_banco = True


        if request.method == "POST":
            nome_tag = request.form["nome_tag"]

            campos = {
                "nome_tag": ["Nome da Tag", nome_tag],
            }
            
            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
            if not "validado" in validacao_campos_obrigatorios:
                gravar_banco = False
                flash(("Verifique os campos destacados em vermelho!", "warning"))

            if gravar_banco == True:

                nova = TagModel(
                    nome_tag=nome_tag,
                    codigo_tag=TagModel.gerar_codigo_nova_tag()
                )
                
                db.session.add(nova)
                db.session.commit()

                TipoAcaoEnum.CADASTRO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    TipoAcaoEnum.CADASTRO,
                    TipoAcaoEnum.CADASTRO.pontos,
                    modulo="tag",
                )

                flash(("Tag cadastrada com sucesso!", "success"))
                return redirect(url_for("listar_tags"))
    except Exception as e:
        flash(("Erro ao tentar cadastrar Tag! Entre em contato com o suporte.", "warning"))
        return redirect(url_for("listar_tags"))

    return render_template(
        "configuracoes_gerais/tag/tag_cadastrar.html",
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
    )


@app.route("/configuracoes/gerais/tag/editar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_tag(id):
    try:
        validacao_campos_obrigatorios = {}
        validacao_campos_erros = {}
        gravar_banco = True

        tag = TagModel.obter_tag_por_id(id)
        if not tag:
            flash(("Tag não encontrada!", "warning"))
            return redirect(url_for("listar_tags"))

        dados_corretos = {
            "nome_tag": tag.nome_tag,
        }

        if request.method == "POST":
            nome_tag = request.form["nome_tag"]

            campos = {
                "nome_tag": ["Nome da Tag", nome_tag],
            }
            
            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
            if not "validado" in validacao_campos_obrigatorios:
                gravar_banco = False
                flash(("Verifique os campos destacados em vermelho!", "warning"))
            
            if gravar_banco == True:
                tag.nome_tag = nome_tag

                db.session.commit()

                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    TipoAcaoEnum.EDICAO,
                    TipoAcaoEnum.EDICAO.pontos,
                    modulo="tag_editar",
                )

                flash(("Tag editada com sucesso!", "success"))
                return redirect(url_for("listar_tags"))
    except Exception as e:
        flash(("Erro ao tentar editar Tag! Entre em contato com o suporte.", "warning"))
        return redirect(url_for("listar_tags"))

    return render_template(
        "configuracoes_gerais/tag/tag_editar.html",
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=dados_corretos,
        tag=tag
    )


@app.route("/configuracoes/gerais/tag/excluir/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def excluir_tag(id):
    try:
        tag = TagModel.obter_tag_por_id(id)
        
        if not tag:
            flash(("Tag não encontrada!", "warning"))
        else:
            tag.ativo = False
            tag.deletado = True
            
            db.session.commit()
            flash(("Tag excluída com sucesso!", "success"))
        return redirect(url_for("listar_tags"))

    except Exception as e:
        flash(("Erro ao tentar excluir Tag! Entre em contato com o suporte.", "warning"))
        return redirect(url_for("listar_tags"))