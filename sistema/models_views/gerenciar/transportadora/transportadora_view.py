from sistema import app, db, requires_roles, current_user
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.parametros.instituicoes_financeiras.instituicao_financeira_model import InstituicoesFinanceirasModel
from sistema.models_views.gerenciar.pessoa_financeiro.pessoa_financeiro_model import PessoaFinanceiroModel
from sqlalchemy.orm.attributes import flag_modified  
import json  
from sistema._utilitarios import *


@app.route("/gerenciar/transportadoras", methods=["GET"])
@login_required
@requires_roles
def listar_transportadoras():
    if any(request.args.values()):
        numero_documento = request.args.get('numeroDocumento')
        telefone = request.args.get('telefone')
        
        numeroDocumento = ValidaDocs.somente_numeros(numero_documento) if numero_documento else None
        numeroTelefone = ValidaDocs.somente_numeros(telefone) if telefone else None

        transportadoras = TransportadoraModel.filtrar_transportadoras(
            identificacao=request.args.get('identificacao'),
            numero_documento=numeroDocumento,
            telefone=numeroTelefone
        )
    else:
        transportadoras = TransportadoraModel.listar_transportadoras()
        
    return render_template(
        "gerenciar/transportadoras/transportadoras_listar.html",
        transportadoras=transportadoras,
        dados_corretos=request.args
    )

@app.route("/gerenciar/transportadora/cadastrar", methods=["GET", "POST"])
@login_required
@requires_roles
def cadastrar_transportadora():
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    bancos = InstituicoesFinanceirasModel.obter_todos_bancos()

    if request.method == "POST":
        tipoCadastro = request.form["tipoCadastro"]
        criar_pessoa_financeiro = request.form.get("criarPessoaFinanceiro", "nao")
        nomeTransportadora = request.form["nomeTransportadora"]
        cpfTransportadora = request.form["cpfTransportadora"]
        razao_social = request.form["razaoSocial"]
        cnpj = request.form["cnpj"]
        instituicao_financeira = request.form["instituicao_financeira"]
        agencia_bancaria = request.form["agencia_bancaria"]
        conta_bancaria = request.form["conta_bancaria"]
        chave_pix = request.form["chave_pix"]
        telefone = request.form["telefone"]
        campos = {
            "telefone": ["Telefone", telefone],
        }

        if tipoCadastro == 'cpf':
            campos['nomeTransportadora'] = ["Nome Completo", nomeTransportadora]
            campos["cpfTransportadora"] = ["CPF", cpfTransportadora]
        
        if tipoCadastro == 'cnpj':
            campos['razaoSocial'] = ["Razão Social", razao_social]
            campos["cnpj"] = ["CNPJ", cnpj]

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))

        if tipoCadastro == 'cpf':
            verificacao_cpf = ValidaForms.validar_cpf(cpfTransportadora)
            if not "validado" in verificacao_cpf:
                gravar_banco = False
                validacao_campos_erros.update(verificacao_cpf)

            numeroDocumento = ValidaDocs.remove_pontuacao_cpf(cpfTransportadora)
            pesquisa_nr_documento_banco = TransportadoraModel.query.filter_by(
                numero_documento=numeroDocumento
            ).first()
            if pesquisa_nr_documento_banco:
                gravar_banco = False
                validacao_campos_erros["cpfTransportadora"] = (
                    f"O CPF informado já existe no banco de dados!"
                )
            identificacaoTransportadora = nomeTransportadora
            tipoCadastroTransportadora = 1

        if tipoCadastro == 'cnpj':
            verificacao_cnpj = ValidaForms.validar_cnpj(cnpj)
            if not "validado" in verificacao_cnpj:
                gravar_banco = False
                validacao_campos_erros.update(verificacao_cnpj)

            numeroDocumento = ValidaDocs.remove_pontuacao_cnpj(cnpj)
            pesquisa_nr_documento_banco = TransportadoraModel.query.filter_by(
                numero_documento=numeroDocumento
            ).first()
            if pesquisa_nr_documento_banco:
                gravar_banco = False
                validacao_campos_erros["cnpj"] = (
                    f"O CNPJ informado já existe no banco de dados!"
                )
            identificacaoTransportadora = razao_social
            tipoCadastroTransportadora = 0

        if gravar_banco == True:
            telefone_tratado = Tels.remove_pontuacao_telefone_celular_br(telefone)
            transportadora = TransportadoraModel(
                tipo_cadastro=tipoCadastroTransportadora,
                identificacao=identificacaoTransportadora,
                numero_documento=numeroDocumento,
                telefone=telefone_tratado,
                instituicao_financeira_id=instituicao_financeira if instituicao_financeira else None,
                agencia_bancaria=agencia_bancaria if agencia_bancaria else None,
                conta_bancaria=conta_bancaria if conta_bancaria else None,
                chave_pix=chave_pix if chave_pix else None,
                ativo=True
            )
            db.session.add(transportadora)
            db.session.commit()

            if criar_pessoa_financeiro == "sim":
                try:
                    vinculos_operacionais = {
                        "transportadora": [{
                            "id": transportadora.id,
                            "identificacao": transportadora.identificacao
                        }]
                    }

                    vinculos_json = json.dumps(vinculos_operacionais)
                    tem_fornecedor, tem_transportadora, tem_extrator, tem_comissionado, vinculos_data = \
                        PessoaFinanceiroModel.processar_vinculos(vinculos_json)
                    
                    pessoa_financeira = PessoaFinanceiroModel(
                        tipo_cadastro=True if tipoCadastroTransportadora == 1 else False,
                        identificacao=identificacaoTransportadora,
                        numero_documento=numeroDocumento,
                        telefone=telefone_tratado,
                        instituicao_financeira_id=int(instituicao_financeira) if instituicao_financeira else None,
                        agencia_bancaria=agencia_bancaria if agencia_bancaria else None,
                        conta_bancaria=conta_bancaria if conta_bancaria else None,
                        chave_pix=chave_pix if chave_pix else None,
                        tem_vinculo_fornecedor=tem_fornecedor,
                        tem_vinculo_transportadora=tem_transportadora,
                        tem_vinculo_extrator=tem_extrator,
                        tem_vinculo_comissionado=tem_comissionado,
                        vinculos_operacionais=vinculos_data,
                        ativo=True
                    )

                    db.session.add(pessoa_financeira)
                    db.session.flush()

                    flash(("Transportadora e Pessoa Financeira cadastradas com sucesso!", "success"))

                except Exception as e:
                    db.session.rollback()
                    print(f"Erro ao criar Pessoa Financeira: {e}")
                    import traceback
                    traceback.print_exc()
                    flash((f"Transportadora cadastrada, mas houve erro ao criar Pessoa Financeira: {str(e)}", "warning"))
                    return redirect(url_for("listar_transportadoras"))
            else:
                flash(("Transportadora cadastrada com sucesso!", "success"))



            acao = TipoAcaoEnum.CADASTRO
            PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                current_user.id,
                acao,
                acao.pontos,
                modulo='transportadora'
            )
            flash(("Transportadora cadastrada com sucesso!", "success"))
            return redirect(url_for("listar_transportadoras"))
    return render_template(
        "gerenciar/transportadoras/transportadora_cadastrar.html",
        campos_obrigatorios=validacao_campos_obrigatorios,
        bancos=bancos,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
    )


@app.route("/gerenciar/transportadora/editar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_transportadora(id):
    transportadora = TransportadoraModel.obter_transportadora_por_id(id)

    if transportadora is None:
        flash(("Transportadora não encontrada", "warning"))
        return redirect(url_for("listar_transportadoras"))
    
    if transportadora.ativo == 0:
        flash((f"Esta transportadora não pode ser editada, pois está desativada!", "warning"))
        return redirect(url_for("listar_transportadoras"))

    bancos = InstituicoesFinanceirasModel.obter_todos_bancos()

    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    dados_corretos = {
        "tipoCadastro": "cpf" if transportadora.tipo_cadastro == 1 else "cnpj",
        "razaoSocial": transportadora.identificacao or "",
        "nomeTransportadora": transportadora.identificacao or "",
        "cnpj": transportadora.numero_documento,
        "cpfTransportadora": transportadora.numero_documento,
        "telefone": transportadora.telefone,
        "instituicao_financeira": transportadora.instituicao_financeira_id or "",
        "agencia_bancaria": transportadora.agencia_bancaria or "",
        "conta_bancaria": transportadora.conta_bancaria or "",
        "chave_pix": transportadora.chave_pix or "",
    }

    if request.method == "POST":
        tipoCadastro = request.form["tipoCadastro"]
        nomeTransportadora = request.form["nomeTransportadora"]
        cpfTransportadora = request.form["cpfTransportadora"]
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
            campos['nomeTransportadora'] = ["Nome Completo", nomeTransportadora]
            campos["cpfTransportadora"] = ["CPF", cpfTransportadora]
        
        if tipoCadastro == 'cnpj':
            campos['razaoSocial'] = ["Razão Social", razao_social]
            campos["cnpj"] = ["CNPJ", cnpj]

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))

        if tipoCadastro == 'cpf':
            verificacao_cpf = ValidaForms.validar_cpf(cpfTransportadora)
            if not "validado" in verificacao_cpf:
                gravar_banco = False
                validacao_campos_erros.update(verificacao_cpf)

            numeroDocumento = ValidaDocs.remove_pontuacao_cpf(cpfTransportadora)
            if transportadora.numero_documento != numeroDocumento:
                pesquisa_nr_documento_banco = TransportadoraModel.query.filter_by(
                    numero_documento=numeroDocumento
                ).first()
                if pesquisa_nr_documento_banco:
                    gravar_banco = False
                    validacao_campos_erros["cpfTransportadora"] = (
                        f"O CPF informado já existe no banco de dados!"
                    )
            identificacaoTransportadora = nomeTransportadora
            tipoCadastroTransportadora = 1

        if tipoCadastro == 'cnpj':
            verificacao_cnpj = ValidaForms.validar_cnpj(cnpj)
            if not "validado" in verificacao_cnpj:
                gravar_banco = False
                validacao_campos_erros.update(verificacao_cnpj)

            numeroDocumento = ValidaDocs.remove_pontuacao_cnpj(cnpj)
            if transportadora.numero_documento != numeroDocumento:
                pesquisa_nr_documento_banco = TransportadoraModel.query.filter_by(
                    numero_documento=numeroDocumento
                ).first()
                if pesquisa_nr_documento_banco:
                    gravar_banco = False
                    validacao_campos_erros["cnpj"] = (
                        f"O CNPJ informado já existe no banco de dados!"
                    )
            identificacaoTransportadora = razao_social
            tipoCadastroTransportadora = 0

        if gravar_banco == True:
            telefone_tratado = Tels.remove_pontuacao_telefone_celular_br(telefone)

            # === Comparação de Objetos ===

            obj2 = {
                "tipoCadastro": tipoCadastro,
                "razaoSocial": razao_social.strip() if tipoCadastro == "cnpj" else transportadora.identificacao,
                "nomeTransportadora": nomeTransportadora.strip() if tipoCadastro == "cpf" else transportadora.identificacao,
                "cnpj": numeroDocumento if tipoCadastro == "cnpj" else transportadora.numero_documento,
                "cpfTransportadora": numeroDocumento if tipoCadastro == "cpf" else transportadora.numero_documento,
                "telefone": telefone_tratado.strip(),
                "instituicao_financeira": instituicao_financeira.strip(),
                "agencia_bancaria": agencia_bancaria.strip(),
                "conta_bancaria": conta_bancaria.strip(),
                "chave_pix": chave_pix.strip(),
            }


            diferencas = Gameficacao.compara_objetos(dados_corretos, obj2)
            if diferencas:
                acao = TipoAcaoEnum.EDICAO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    acao,
                    acao.pontos,
                    modulo='transportadora'
                )

            transportadora.tipo_cadastro = tipoCadastroTransportadora
            transportadora.identificacao = identificacaoTransportadora
            transportadora.numero_documento = numeroDocumento
            transportadora.telefone = telefone_tratado
            transportadora.instituicao_financeira_id = instituicao_financeira if instituicao_financeira else None
            transportadora.agencia_bancaria = agencia_bancaria if agencia_bancaria else None
            transportadora.conta_bancaria = conta_bancaria if conta_bancaria else None
            transportadora.chave_pix = chave_pix if chave_pix else None

            pessoa_financeira = PessoaFinanceiroModel.query.filter_by(
                numero_documento=numeroDocumento,
                ativo=True,
                deletado=False
            ).first()

            if pessoa_financeira:
                try:
                     # Atualizar dados básicos
                    pessoa_financeira.tipo_cadastro = True if tipoCadastroTransportadora == 1 else False
                    pessoa_financeira.identificacao = identificacaoTransportadora
                    pessoa_financeira.numero_documento = numeroDocumento
                    pessoa_financeira.telefone = telefone_tratado
                    pessoa_financeira.instituicao_financeira_id = int(instituicao_financeira) if instituicao_financeira else None
                    pessoa_financeira.agencia_bancaria = agencia_bancaria if agencia_bancaria else None
                    pessoa_financeira.conta_bancaria = conta_bancaria if conta_bancaria else None
                    pessoa_financeira.chave_pix = chave_pix if chave_pix else None

                    vinculos_atuais = pessoa_financeira.vinculos_operacionais or {}
                    vinculos_atuais['transportadora'] = [{
                        "id": str(transportadora.id),
                        "identificacao": identificacaoTransportadora
                    }]

                    pessoa_financeira.vinculos_operacionais = vinculos_atuais
                    flag_modified(pessoa_financeira, "vinculos_operacionais")

                    db.session.flush()

                except Exception as e:
                    print(f"Erro ao atualizar Pessoa Financeira: {e}")
                    import traceback
                    traceback.print_exc()

            db.session.commit()
            flash(("Transportadora editada com sucesso!", "success"))
            return redirect(url_for("listar_transportadoras"))

    return render_template(
        "gerenciar/transportadoras/transportadora_editar.html", transportadora=transportadora,
                                                    bancos=bancos,      
                                                    campos_obrigatorios=validacao_campos_obrigatorios,
                                                    dados_corretos=dados_corretos,
                                                    campos_erros=validacao_campos_erros)


@app.route("/gerenciar/transportadora/desativar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def desativar_transportadora(id):
    transportadora = TransportadoraModel.obter_transportadora_por_id(id)

    if transportadora is None:
        flash(("Transportadora não encontrada", "warning"))
    transportadora.ativo = False
    db.session.commit()
    flash(("Transportadora desativada com sucesso!", "success"))
    return redirect(url_for("listar_transportadoras"))

@app.route("/gerenciar/transportadora/ativar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def ativar_transportadora(id):
    transportadora = TransportadoraModel.obter_transportadora_por_id(id)

    if transportadora is None:
        flash(("Transportadora não encontrada", "warning"))
    transportadora.ativo = True
    db.session.commit()
    flash(("Transportadora ativada com sucesso!", "success"))
    return redirect(url_for("listar_transportadoras"))

