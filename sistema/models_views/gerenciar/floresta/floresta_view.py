from sistema import app, requires_roles, db, current_user
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from sistema.models_views.gerenciar.floresta.floresta_model import FlorestaModel
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema._utilitarios import *


@app.route("/gerenciar/florestas/cadastrar", methods=["GET", "POST"])
@login_required
@requires_roles
def cadastrar_floresta():
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    if request.method == "POST":
        identificacaoFloresta = request.form["identificacaoFloresta"]
        rodoviaFloresta = request.form["rodoviaFloresta"]
        kmRodovia = request.form["kmRodovia"]
        cidadeFloresta = request.form["cidadeFloresta"]
        estadoFloresta = request.form["estadoFloresta"]
        contratoFloresta = request.files.get("contratoFloresta")
        creditoFloresta = request.form["creditoFloresta"]
        campos = {
            "identificacaoFloresta": ["Identificação", identificacaoFloresta],
            "cidadeFloresta": ["Cidade", cidadeFloresta],
            "contratoFloresta": ["Contrato", contratoFloresta],
            "estadoFloresta": ["Estado", estadoFloresta],
        }

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))

        credito_floresta_float = ValoresMonetarios.converter_string_brl_para_float(
            creditoFloresta
        )
        credito_floresta_100 = credito_floresta_float * 100

        if gravar_banco == True:
            floresta = FlorestaModel(
                identificacao=identificacaoFloresta,
                rodovia=rodoviaFloresta,
                km=kmRodovia,
                cidade=cidadeFloresta,
                estado=estadoFloresta,
                contrato_floresta_id=None,
                credito_100=credito_floresta_100 if creditoFloresta else None,
                ativo=True
            )
            db.session.add(floresta)
            db.session.flush()

            if contratoFloresta and contratoFloresta.filename:
                if contratoFloresta.mimetype == "application/pdf":
                    contrato_upload = upload_arquivo(
                        contratoFloresta, "UPLOAD_CONTRATO_FLORESTA", f"{floresta.id}"
                    )
                    floresta.contrato_floresta_id = contrato_upload.id
                    db.session.commit()
                else:
                    flash(("O contrato da floresta deve estar em formato PDF.", "warning"))
                    return redirect(url_for("cadastrar_floresta"))

            flash(("Floresta cadastrada com sucesso!", "success"))
            acao = TipoAcaoEnum.CADASTRO
            PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                current_user.id,
                acao,
                acao.pontos,
                modulo='floresta'
            )
            return redirect(url_for("listar_florestas"))
    return render_template(
        "gerenciar/florestas/floresta_cadastrar.html",
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
    )


@app.route("/gerenciar/florestas", methods=["GET", "POST"])
@login_required
@requires_roles
def listar_florestas():
    if request.method == 'POST':    
        florestas = FlorestaModel.filtrar_floresta(
            identficacao=request.form.get('identificacao'),
            rodovia=request.form.get('rodovia'),
            km=request.form.get('km'),
            cidade=request.form.get('cidade'),
            estado=request.form.get('estado')
        )
    else:
        florestas = FlorestaModel.listar_floresta()
    return render_template("gerenciar/florestas/florestas_listar.html", florestas=florestas, dados_corretos=request.form)


@app.route("/gerenciar/floresta/editar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_floresta(id):
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    floresta = FlorestaModel.obter_floresta_por_id(id)
    if floresta is None:
        flash(("Floresta não encontrada!", "warning"))
        return redirect(url_for("listar_florestas"))

    if request.method == "POST":
        identificacaoFloresta = request.form["identificacaoFloresta"]
        rodoviaFloresta = request.form["rodoviaFloresta"]
        kmRodovia = request.form["kmRodovia"]
        cidadeFloresta = request.form["cidadeFloresta"]
        estadoFloresta = request.form["estadoFloresta"]
        creditoFloresta = request.form["creditoFloresta"]
        contratoFloresta = request.files.get("contratoFloresta")
        campos = {
            "identificacaoFloresta": ["Identificação", identificacaoFloresta],
            "cidadeFloresta": ["Cidade", cidadeFloresta],
            "estadoFloresta": ["Estado", estadoFloresta],
        }

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))

        credito_floresta_float = ValoresMonetarios.converter_string_brl_para_float(
            creditoFloresta
        )
        credito_floresta_100 = credito_floresta_float * 100

        if gravar_banco == True:

            obj1 = {
                "identificacao": floresta.identificacao or "",
                "rodovia": floresta.rodovia or "",
                "km": floresta.km or "",
                "cidade": floresta.cidade or "",
                "estado": floresta.estado or "",
                "credito_100": floresta.credito_100,
            }

            obj2 = {
                "identificacao": identificacaoFloresta.strip(),
                "rodovia": rodoviaFloresta.strip(),
                "km": kmRodovia.strip(),
                "cidade": cidadeFloresta.strip(),
                "estado": estadoFloresta.strip(),
                "credito_100": credito_floresta_100,
            }

            diferencas = Gameficacao.compara_objetos(obj1, obj2)
            if diferencas:
                acao = TipoAcaoEnum.EDICAO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    acao,
                    acao.pontos,
                    modulo='floresta'
                )

            floresta.identificacao=identificacaoFloresta,
            floresta.rodovia=rodoviaFloresta,
            floresta.km=kmRodovia,
            floresta.cidade=cidadeFloresta,
            floresta.estado=estadoFloresta,
            floresta.credito_100=credito_floresta_100 if creditoFloresta else None,

            if contratoFloresta and contratoFloresta.filename:
                if contratoFloresta.mimetype == "application/pdf":
                    contrato_upload = upload_arquivo(
                        contratoFloresta, "UPLOAD_CONTRATO_FLORESTA", f"{floresta.id}"
                    )
                    floresta.contrato_floresta_id = contrato_upload.id
                    db.session.commit()

                else:
                    flash(("O contrato da floresta deve estar em formato PDF.", "warning"))
                    return redirect(url_for("editar_floresta", id=floresta.id))
            db.session.commit()
            flash(("Floresta editada com sucesso!", "success"))
            return redirect(url_for("listar_florestas"))
    return render_template(
        "gerenciar/florestas/floresta_editar.html",
        floresta=floresta,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
    )


@app.route("/gerenciar/desativar/floresta/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def desativar_floresta(id):
    floresta = FlorestaModel.obter_floresta_por_id(id)
    if floresta is None:
        flash(("Floresta não encontrada!", "warning"))
    floresta.ativo = 0
    db.session.commit()
    flash(("Floresta desativada com sucesso!", "success"))
    return redirect(url_for("listar_florestas"))


@app.route("/gerenciar/ativar/floresta/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def ativar_floresta(id):
    floresta = FlorestaModel.obter_floresta_por_id(id)
    if floresta is None:
        flash(("Floresta não encontrada!", "warning"))
    floresta.ativo = 1
    db.session.commit()
    flash(("Floresta ativada com sucesso!", "success"))
    return redirect(url_for("listar_florestas"))

