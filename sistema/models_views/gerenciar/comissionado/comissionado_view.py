from sistema import app, db, requires_roles, current_user
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from sistema.models_views.gerenciar.comissionado.comissionado_model import ComissionadoModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.parametros.instituicoes_financeiras.instituicao_financeira_model import InstituicoesFinanceirasModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema._utilitarios import *



@app.route("/gerenciar/comissionados", methods=["GET"])
@login_required
@requires_roles
def listar_comissionados():
    if any(request.args.values()):
        numero_documento = request.args.get('numeroDocumento')
        telefone = request.args.get('telefone')
        
        numeroDocumento = ValidaDocs.somente_numeros(numero_documento) if numero_documento else None
        numeroTelefone = ValidaDocs.somente_numeros(telefone) if telefone else None

        comissionados = ComissionadoModel.filtrar_comissionados(
            identificacao=request.args.get('identificacao'),
            numero_documento=numeroDocumento,
            telefone=numeroTelefone
        )
    else:
        comissionados = ComissionadoModel.listar_comissionados()
        
    return render_template(
        "gerenciar/comissionados/comissionados_listar.html",
        comissionados=comissionados,
        dados_corretos=request.args
    )


@app.route("/gerenciar/comissionado/cadastrar", methods=["GET", "POST"])
@login_required
@requires_roles
def cadastrar_comissionado():
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    bancos = InstituicoesFinanceirasModel.obter_todos_bancos()

    if request.method == "POST":
        tipoCadastro = request.form["tipoCadastro"]
        nomeComissionado = request.form["nomeComissionado"]
        cpfComissionado = request.form["cpfComissionado"]
        razao_social = request.form["razaoSocial"]
        cnpj = request.form["cnpj"]
        telefone = request.form["telefone"]
        instituicao_financeira = request.form["instituicao_financeira"]
        agencia_bancaria = request.form["agencia_bancaria"]
        conta_bancaria = request.form["conta_bancaria"]
        chave_pix = request.form["chave_pix"]
        campos = {
            "telefone": ["Telefone", telefone],
        }

        if tipoCadastro == 'cpf':
            campos['nomeComissionado'] = ["Nome Completo", nomeComissionado]
            campos["cpfComissionado"] = ["CPF", cpfComissionado]
        
        if tipoCadastro == 'cnpj':
            campos['razaoSocial'] = ["Razão Social", razao_social]
            campos["cnpj"] = ["CNPJ", cnpj]

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False

        if tipoCadastro == 'cpf':
            verificacao_cpf = ValidaForms.validar_cpf(cpfComissionado)
            if not "validado" in verificacao_cpf:
                gravar_banco = False
                validacao_campos_erros['cpfComissionado'] = "CPF inválido."

            numeroDocumento = ValidaDocs.remove_pontuacao_cpf(cpfComissionado)
            pesquisa_nr_documento_banco = ComissionadoModel.query.filter_by(
                numero_documento=numeroDocumento
            ).first()
            if pesquisa_nr_documento_banco:
                gravar_banco = False
                validacao_campos_erros["cpfComissionado"] = (
                    f"O CPF informado já existe no banco de dados!"
                )
            identificacaoComissionado = nomeComissionado
            tipoCadastroComissionado = 1

        if tipoCadastro == 'cnpj':
            verificacao_cnpj = ValidaForms.validar_cnpj(cnpj)
            if not "validado" in verificacao_cnpj:
                gravar_banco = False
                validacao_campos_erros['cnpj'] = "CNPJ inválido."

            numeroDocumento = ValidaDocs.remove_pontuacao_cnpj(cnpj)
            pesquisa_nr_documento_banco = ComissionadoModel.query.filter_by(
                numero_documento=numeroDocumento
            ).first()
            if pesquisa_nr_documento_banco:
                gravar_banco = False
                validacao_campos_erros["cnpj"] = (
                    f"O CNPJ informado já existe no banco de dados!"
                )
            identificacaoComissionado = razao_social
            tipoCadastroComissionado = 0

        if gravar_banco == True:
            telefone_tratado = Tels.remove_pontuacao_telefone_celular_br(telefone)
            Comissionado = ComissionadoModel(
                tipo_cadastro=tipoCadastroComissionado,
                identificacao=identificacaoComissionado,
                numero_documento=numeroDocumento,
                telefone=telefone_tratado,
                instituicao_financeira_id=instituicao_financeira if instituicao_financeira else None,
                agencia_bancaria=agencia_bancaria if agencia_bancaria else None,
                conta_bancaria=conta_bancaria if conta_bancaria else None,
                chave_pix=chave_pix if chave_pix else None,
                ativo=True
            )
            db.session.add(Comissionado)
            db.session.commit()
            acao = TipoAcaoEnum.CADASTRO
            PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                current_user.id,
                acao,
                acao.pontos,
                modulo='comissionado'
            )
            flash(("Comissionado cadastrado com sucesso!", "success"))
            return redirect(url_for("listar_comissionados"))
    return render_template(
        "gerenciar/comissionados/comissionado_cadastrar.html",
        campos_obrigatorios=validacao_campos_obrigatorios,
        bancos=bancos,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
    )


@app.route("/gerenciar/comissionado/editar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_comissionado(id):
    comissionado = ComissionadoModel.obter_comissionado_por_id(id)

    if comissionado is None:
        flash(("Comissionado não encontrado", "warning"))
        return redirect(url_for("listar_comissionados"))
    
    if comissionado.ativo == 0:
        flash((f"Este comissionado não pode ser editado, pois está desativado!", "warning"))
        return redirect(url_for("listar_comissionados"))

    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    bancos = InstituicoesFinanceirasModel.obter_todos_bancos()

    dados_corretos = {
        "tipoCadastro": "cpf" if comissionado.tipo_cadastro == 1 else "cnpj",
        "razaoSocial": comissionado.identificacao or "",
        "nomeComissionado": comissionado.identificacao or "",
        "cnpj": comissionado.numero_documento,
        "cpfComissionado": comissionado.numero_documento,
        "telefone": comissionado.telefone,
        "instituicao_financeira": comissionado.instituicao_financeira_id if comissionado.instituicao_financeira_id else "",
        "agencia_bancaria": comissionado.agencia_bancaria or "",
        "conta_bancaria": comissionado.conta_bancaria or "",
        "chave_pix": comissionado.chave_pix or "",
    }

    if request.method == "POST":
        tipoCadastro = request.form["tipoCadastro"]
        nomeComissionado = request.form["nomeComissionado"]
        cpfComissionado = request.form["cpfComissionado"]
        razao_social = request.form["razaoSocial"]
        cnpj = request.form["cnpj"]
        telefone = request.form["telefone"]
        instituicao_financeira = request.form["instituicao_financeira"]
        agencia_bancaria = request.form["agencia_bancaria"]
        conta_bancaria = request.form["conta_bancaria"]
        chave_pix = request.form["chave_pix"]
        campos = {
            "telefone": ["Telefone", telefone],
        }

        if tipoCadastro == 'cpf':
            campos['nomeComissionado'] = ["Nome Completo", nomeComissionado]
            campos["cpfComissionado"] = ["CPF", cpfComissionado]
        
        if tipoCadastro == 'cnpj':
            campos['razaoSocial'] = ["Razão Social", razao_social]
            campos["cnpj"] = ["CNPJ", cnpj]

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False

        if tipoCadastro == 'cpf':
            verificacao_cpf = ValidaForms.validar_cpf(cpfComissionado)
            if not "validado" in verificacao_cpf:
                gravar_banco = False
                validacao_campos_erros.update(verificacao_cpf)

            numeroDocumento = ValidaDocs.remove_pontuacao_cpf(cpfComissionado)
            if comissionado.numero_documento != numeroDocumento:
                pesquisa_nr_documento_banco = ComissionadoModel.query.filter_by(
                    numero_documento=numeroDocumento
                ).first()
                if pesquisa_nr_documento_banco:
                    gravar_banco = False
                    validacao_campos_erros["cpfComissionado"] = (
                        f"O CPF informado já existe no banco de dados!"
                    )
            identificacaoComissionado = nomeComissionado
            tipoCadastroComissionado = 1

        if tipoCadastro == 'cnpj':
            verificacao_cnpj = ValidaForms.validar_cnpj(cnpj)
            if not "validado" in verificacao_cnpj:
                gravar_banco = False
                validacao_campos_erros.update(verificacao_cnpj)

            numeroDocumento = ValidaDocs.remove_pontuacao_cnpj(cnpj)
            if comissionado.numero_documento != numeroDocumento:
                pesquisa_nr_documento_banco = ComissionadoModel.query.filter_by(
                    numero_documento=numeroDocumento
                ).first()
                if pesquisa_nr_documento_banco:
                    gravar_banco = False
                    validacao_campos_erros["cnpj"] = (
                        f"O CNPJ informado já existe no banco de dados!"
                    )
            identificacaoComissionado = razao_social
            tipoCadastroComissionado = 0

        if gravar_banco == True:
            telefone_tratado = Tels.remove_pontuacao_telefone_celular_br(telefone)

            # === Comparação de Objetos ===

            obj2 = {
                "tipoCadastro": tipoCadastro,
                "razaoSocial": razao_social.strip() if tipoCadastro == "cnpj" else comissionado.identificacao,
                "nomeComissionado": nomeComissionado.strip() if tipoCadastro == "cpf" else comissionado.identificacao,
                "cnpj": numeroDocumento if tipoCadastro == "cnpj" else comissionado.numero_documento,
                "cpfComissionado": numeroDocumento if tipoCadastro == "cpf" else comissionado.numero_documento,
                "telefone": telefone_tratado.strip(),
                "instituicao_financeira": comissionado.instituicao_financeira_id if comissionado.instituicao_financeira_id else "",
                "agencia_bancaria": comissionado.agencia_bancaria or "",
                "conta_bancaria": comissionado.conta_bancaria or "",
                "chave_pix": comissionado.chave_pix or "",
            }


            diferencas = Gameficacao.compara_objetos(dados_corretos, obj2)
            if diferencas:
                acao = TipoAcaoEnum.EDICAO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    acao,
                    acao.pontos,
                    modulo='comissionado'
                )

            comissionado.tipo_cadastro = tipoCadastroComissionado
            comissionado.identificacao = identificacaoComissionado
            comissionado.numero_documento = numeroDocumento
            comissionado.telefone = telefone_tratado
            comissionado.instituicao_financeira_id = instituicao_financeira if instituicao_financeira else None
            comissionado.agencia_bancaria = agencia_bancaria if agencia_bancaria else None
            comissionado.conta_bancaria = conta_bancaria if conta_bancaria  else None
            comissionado.chave_pix = chave_pix if chave_pix else None

            db.session.commit()
            flash(("Comissionado editado com sucesso!", "success"))
            return redirect(url_for("listar_comissionados"))

    return render_template(
        "gerenciar/comissionados/comissionado_editar.html",
        comissionado=comissionado,
        bancos=bancos,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=dados_corretos,
    )


@app.route("/gerenciar/comissionado/desativar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def desativar_comissionado(id):
    comissionado = ComissionadoModel.obter_comissionado_por_id(id)

    if comissionado is None:
        flash(("Comissionado não encontrado", "warning"))
    comissionado.ativo = False
    db.session.commit()
    flash(("Comissionado desativado com sucesso!", "success"))
    return redirect(url_for("listar_comissionados"))


@app.route("/gerenciar/comissionado/ativar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def ativar_comissionado(id):
    comissionado = ComissionadoModel.obter_comissionado_por_id(id)

    if comissionado is None:
        flash(("Comissionado não encontrado", "warning"))
    comissionado.ativo = True
    db.session.commit()
    flash(("Comissionado ativado com sucesso!", "success"))
    return redirect(url_for("listar_comissionados"))
