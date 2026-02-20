from sistema import app, db, requires_roles
from flask_login import login_required, current_user
from logs_sistema import flask_logger
from flask import render_template, request, redirect, url_for, flash
from sistema.models_views.parametrizacao.variavel_sistema_model import VariavelSistemaModel
from sistema._utilitarios import *


@app.route(
    "/configuracoes/variaveis-sistema/<int:id>", methods=["GET", "POST"]
)
@login_required
@requires_roles
def variaveis_sistema_editar(id):
    configs = VariavelSistemaModel.obter_variaveis_de_sistema_por_id(id)

    if configs is not None and configs.telefone:
        configs.telefone = Tels.insere_pontuacao_telefone_celular_br(configs.telefone)

    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True
    if request.method == "POST":
        nome_projeto = request.form["nomeProjeto"]
        cnpj = request.form["cnpj"]
        telefone = request.form["telefone"]
        email_corporativo = request.form["email"]

        chave_pub_google_recaptcha = request.form["chavePubGoogleRecaptcha"]
        chave_priv_google_recaptcha = request.form["chavePrivGoogleRecaptcha"]

        modo_manutencao = request.form["modoManutencao"]

        cnpj_tratado = ValidaDocs.remove_pontuacao_cnpj(cnpj)
        tel_tratado = Tels.remove_pontuacao_telefone_celular_br(telefone)

        campos = {
            "nomeProjeto": ["Nome do Projeto", nome_projeto],
            "cnpj": ["CNPJ", cnpj_tratado],
            "telefone": ["Telefone", tel_tratado],
            "email": ["E-mail", email_corporativo],
            "chavePubGoogleRecaptcha": [
                "Chave Publica Recaptcha",
                chave_pub_google_recaptcha,
            ],
            "chavePrivGoogleRecaptcha": [
                "Chave Privada Recaptcha",
                chave_priv_google_recaptcha,
            ]
        }

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))

        verificacao_cnpj = ValidaForms.validar_cnpj(cnpj)
        if not "validado" in verificacao_cnpj:
            gravar_banco = False
            validacao_campos_erros.update(verificacao_cnpj)

        if gravar_banco == True:
            if modo_manutencao == "0":
                modo_manutencao = 0

            if modo_manutencao == "1":
                modo_manutencao = 1

            configs.nome_projeto = nome_projeto
            configs.cnpj = cnpj
            configs.telefone = tel_tratado
            configs.email_corporativo = email_corporativo
            configs.chave_pub_google_recaptcha = chave_pub_google_recaptcha
            configs.chave_priv_google_recaptcha = chave_priv_google_recaptcha
            configs.modo_manutencao = modo_manutencao
            db.session.commit()

            flask_logger.info(
                f"Funcionario ID = {current_user.id} " f"alterou variaveis de ambiente!"
            )
            flash((f"Informações alteradas com sucesso!", "success"))

            return redirect(url_for("variaveis_sistema_editar", id=id))

    return render_template(
        "configuracao/variavel_sistema/variavel_sistema_editar.html",
        configs=configs,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
    )
