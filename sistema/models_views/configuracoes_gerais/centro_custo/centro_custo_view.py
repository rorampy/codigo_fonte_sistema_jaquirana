from sistema import app, db, requires_roles, current_user
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required
from sistema.models_views.configuracoes_gerais.centro_custo.centro_custo_model import CentroCustoModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema._utilitarios import *


@app.route("/configuracoes/gerais/centro-custo/listar", methods=["GET", "POST"])
@login_required
@requires_roles
def listar_centro_custo():
    centro_custo = CentroCustoModel.obter_centro_custos_ativos()

    return render_template(
        "configuracoes_gerais/centro_custo/centro_custo_listar.html",
        centro_custo=centro_custo, dados_corretos=request.form
    )


@app.route("/configuracoes/gerais/centro-custo/cadastrar", methods=["GET", "POST"])
@login_required
@requires_roles
def cadastrar_centro_custo():
    try:
        usuarioId= current_user.id
        validacao_campos_obrigatorios = {}
        validacao_campos_erros = {}
        gravar_banco = True

        if request.method == "POST":
            nomeCusto = request.form["nomeCusto"]
            
            campos = {
                "nomeCusto": ["Nome", nomeCusto],
            }

            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

            if not "validado" in validacao_campos_obrigatorios:
                gravar_banco = False
                flash((f"Verifique os campos destacados em vermelho!", "warning"))

            if gravar_banco == True:

                custo = CentroCustoModel(
                    nome=nomeCusto,
                    ativo=True
                )
                db.session.add(custo)
                db.session.commit()

                acao = TipoAcaoEnum.CADASTRO

                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    usuarioId,
                    acao,
                    acao.pontos,
                    modulo='centro_custo'
                )

                flash(("Centro Custo cadastrado com sucesso!", "success"))
                return redirect(url_for("listar_centro_custo"))
    except Exception as e:
        flash(("Erro ao tentar cadastrar Centro de Custo! Entre em contato com o suporte", "warning"))
        return redirect(url_for("listar_centro_custo"))

    return render_template(
        "configuracoes_gerais/centro_custo/centro_custo_cadastrar.html",
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
    )

@app.route("/configuracoes/gerais/centro-custo/editar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_centro_custo(id):
    try:
        usuarioId= current_user.id
        validacao_campos_obrigatorios = {}
        validacao_campos_erros = {}
        gravar_banco = True

        centro = CentroCustoModel.obter_centro_custo_por_id(id)

        if not centro:
            flash(('Centro Custo não encontrada!', 'warning'))
            return redirect(url_for('listar_centro_custo'))
        
        dados_corretos = {
            "nomeCusto": centro.nome,
        }

        if request.method == "POST":
            nomeCusto = request.form["nomeCusto"]
            
            campos = {
                "nomeCusto": ["Nome", nomeCusto],
            }

            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

            if not "validado" in validacao_campos_obrigatorios:
                gravar_banco = False
                flash((f"Verifique os campos destacados em vermelho!", "warning"))

            if gravar_banco == True:

                centro.nome=nomeCusto,
                
                db.session.commit()

                acao = TipoAcaoEnum.EDICAO

                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    usuarioId,
                    acao,
                    acao.pontos,
                    modulo='centro_custo'
                )

                flash(("Centro Custo editado com sucesso!", "success"))
                return redirect(url_for("listar_centro_custo"))
    except Exception as e:
        flash(("Erro ao tentar editar Centro de Custo! Entre em contato com o suporte", "warning"))
        return redirect(url_for("listar_centro_custo"))

    return render_template(
        "configuracoes_gerais/centro_custo/centro_custo_editar.html",
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        centro=centro,
        dados_corretos=dados_corretos,
    )

@app.route("/configuracoes/gerais/centro-custo/excluir/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def excluir_centro_custo(id):
    try:
        centro = CentroCustoModel.obter_centro_custo_por_id(id)

        if not centro:
            flash(('Centro Custo não encontrada!', 'warning'))
            return redirect(url_for('listar_centro_custo'))
        
        centro.ativo = False
        centro.deletado = True

        db.session.commit()

        flash(('Centro Custo excluído com sucesso!', 'success'))
        return redirect(url_for('listar_centro_custo'))
    except Exception as e:
        flash(("Erro ao tentar excluir Centro de Custo! Entre em contato com o suporte", "warning"))
        return redirect(url_for("listar_centro_custo"))

