from sistema import app, db, requires_roles, current_user
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from sistema.models_views.gerenciar.extrator.extrator_model import ExtratorModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.parametros.instituicoes_financeiras.instituicao_financeira_model import InstituicoesFinanceirasModel
from sistema.models_views.gerenciar.pessoa_financeiro.pessoa_financeiro_model import PessoaFinanceiroModel
from sqlalchemy.orm.attributes import flag_modified 
import json
from sistema._utilitarios import *



@app.route("/gerenciar/extratores", methods=["GET"])
@login_required
@requires_roles
def listar_extratores():
    if any(request.args.values()):
        numero_documento = request.args.get('numeroDocumento')
        telefone = request.args.get('telefone')
        
        numeroDocumento = ValidaDocs.somente_numeros(numero_documento) if numero_documento else None
        numeroTelefone = ValidaDocs.somente_numeros(telefone) if telefone else None

        extratores = ExtratorModel.filtrar_extratores(
            identificacao=request.args.get('identificacao'),
            numero_documento=numeroDocumento,
            telefone=numeroTelefone
        )
    else:
        extratores = ExtratorModel.listar_extratores()
        
    return render_template(
        "gerenciar/extratores/extratores_listar.html",
        extratores=extratores,
        dados_corretos=request.args
    )

@app.route("/gerenciar/extrator/cadastrar", methods=["GET", "POST"])
@login_required
@requires_roles
def cadastrar_extrator():
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    bancos = InstituicoesFinanceirasModel.obter_todos_bancos()

    if request.method == "POST":
        tipoCadastro = request.form["tipoCadastro"]
        criar_pessoa_financeiro = request.form.get("criarPessoaFinanceiro", "nao")
        nomeExtrator = request.form["nomeExtrator"]
        cpfExtrator = request.form["cpfExtrator"]
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
            campos['nomeExtrator'] = ["Nome Completo", nomeExtrator]
            campos["cpfExtrator"] = ["CPF", cpfExtrator]
        
        if tipoCadastro == 'cnpj':
            campos['razaoSocial'] = ["Razão Social", razao_social]
            campos["cnpj"] = ["CNPJ", cnpj]

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))

        if tipoCadastro == 'cpf':
            verificacao_cpf = ValidaForms.validar_cpf(cpfExtrator)
            if not "validado" in verificacao_cpf:
                gravar_banco = False
                validacao_campos_erros.update(verificacao_cpf)

            numeroDocumento = ValidaDocs.remove_pontuacao_cpf(cpfExtrator)
            pesquisa_nr_documento_banco = ExtratorModel.query.filter_by(
                numero_documento=numeroDocumento
            ).first()
            if pesquisa_nr_documento_banco:
                gravar_banco = False
                validacao_campos_erros["cpfExtrator"] = (
                    f"O CPF informado já existe no banco de dados!"
                )
            identificacaoExtrator = nomeExtrator
            tipoCadastroExtrator = 1

        if tipoCadastro == 'cnpj':
            verificacao_cnpj = ValidaForms.validar_cnpj(cnpj)
            if not "validado" in verificacao_cnpj:
                gravar_banco = False
                validacao_campos_erros.update(verificacao_cnpj)

            numeroDocumento = ValidaDocs.remove_pontuacao_cnpj(cnpj)
            pesquisa_nr_documento_banco = ExtratorModel.query.filter_by(
                numero_documento=numeroDocumento
            ).first()
            if pesquisa_nr_documento_banco:
                gravar_banco = False
                validacao_campos_erros["cnpj"] = (
                    f"O CNPJ informado já existe no banco de dados!"
                )
            identificacaoExtrator = razao_social
            tipoCadastroExtrator = 0

        if gravar_banco == True:
            telefone_tratado = Tels.remove_pontuacao_telefone_celular_br(telefone)
            extrator = ExtratorModel(
                tipo_cadastro=tipoCadastroExtrator,
                identificacao=identificacaoExtrator,
                numero_documento=numeroDocumento,
                telefone=telefone_tratado,
                instituicao_financeira_id=int(instituicao_financeira) if instituicao_financeira else None,
                agencia_bancaria=agencia_bancaria.strip() if agencia_bancaria else None,
                conta_bancaria=conta_bancaria.strip() if conta_bancaria else None,
                chave_pix=chave_pix.strip() if chave_pix else None,
                ativo=True
            )
            db.session.add(extrator)
            db.session.flush()

            #Cadastrar pessoa financeira
            if criar_pessoa_financeiro == "sim":
                try:
                    vinculos_operacionais = {
                        "extrator": [{
                            "id": str(extrator.id),
                            "identificacao": extrator.identificacao 
                        }]
                    }

                    vinculos_json = json.dumps(vinculos_operacionais)
                    tem_fornecedor, tem_transportadora, tem_extrator_flag, tem_comissionado, vinculos_data = \
                        PessoaFinanceiroModel.processar_vinculos(vinculos_json)
                    
                    pessoa_financeiro = PessoaFinanceiroModel(
                        tipo_cadastro=True if tipoCadastroExtrator == 1 else False,
                        identificacao=identificacaoExtrator,
                        numero_documento=numeroDocumento,
                        telefone=telefone_tratado,
                        instituicao_financeira_id=int(instituicao_financeira) if instituicao_financeira else None,
                        agencia_bancaria=agencia_bancaria if agencia_bancaria else None,
                        conta_bancaria=conta_bancaria if conta_bancaria else None,
                        chave_pix=chave_pix if chave_pix else None,
                        tem_vinculo_fornecedor=tem_fornecedor,
                        tem_vinculo_transportadora=tem_transportadora,
                        tem_vinculo_extrator=tem_extrator_flag,
                        tem_vinculo_comissionado=tem_comissionado,
                        vinculos_operacionais=vinculos_data,
                        ativo=True
                    )

                    db.session.add(pessoa_financeiro)
                    db.session.flush()

                    flash(("Extrator e Pessoa Financeira cadastrados com sucesso!", "success"))
                
                except Exception as e:
                    db.session.rollback()
                    print(f"Erro ao criar Pessoa Financeira: {e}")
                    import traceback
                    traceback.print_exc()
                    flash((f"Extrator cadastrado, mas houve erro ao criar Pessoa Financeira: {str(e)}", "warning"))
                    return redirect(url_for("listar_extratores"))
            else:
                flash(("Extrator cadastrado com sucesso!", "success"))

            acao = TipoAcaoEnum.CADASTRO
            PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                current_user.id,
                acao,
                acao.pontos,
                modulo='extrator'
            )
            return redirect(url_for("listar_extratores"))
    return render_template(
        "gerenciar/extratores/extrator_cadastrar.html",
        campos_obrigatorios=validacao_campos_obrigatorios,
        bancos=bancos,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
    )


@app.route("/gerenciar/extrator/editar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_extrator(id):
    extrator = ExtratorModel.obter_extrator_por_id(id)

    if extrator is None:
        flash(("Extrator não encontrada", "warning"))
        return redirect(url_for("listar_extratores"))
    
    if extrator.ativo == 0:
        flash((f"Este extrator não pode ser editado, pois está desativado!", "warning"))
        return redirect(url_for("listar_extratores"))
    
    bancos = InstituicoesFinanceirasModel.obter_todos_bancos()

    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    dados_corretos = {
        "tipoCadastro": "cpf" if extrator.tipo_cadastro == 1 else "cnpj",
        "razaoSocial": extrator.identificacao or "",
        "nomeExtrator": extrator.identificacao or "",
        "cnpj": extrator.numero_documento,
        "cpfExtrator": extrator.numero_documento,
        "telefone": extrator.telefone,
        "instituicao_financeira": extrator.instituicao_financeira_id or "",
        "agencia_bancaria": extrator.agencia_bancaria or "",
        "conta_bancaria": extrator.conta_bancaria or "",
        "chave_pix": extrator.chave_pix or "",
    }

    if request.method == "POST":
        tipoCadastro = request.form["tipoCadastro"]
        nomeExtrator = request.form["nomeExtrator"]
        cpfExtrator = request.form["cpfExtrator"]
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
            campos['nomeExtrator'] = ["Nome Completo", nomeExtrator]
            campos["cpfExtrator"] = ["CPF", cpfExtrator]
        
        if tipoCadastro == 'cnpj':
            campos['razaoSocial'] = ["Razão Social", razao_social]
            campos["cnpj"] = ["CNPJ", cnpj]

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))

        if tipoCadastro == 'cpf':
            verificacao_cpf = ValidaForms.validar_cpf(cpfExtrator)
            if not "validado" in verificacao_cpf:
                gravar_banco = False
                validacao_campos_erros.update(verificacao_cpf)

            numeroDocumento = ValidaDocs.remove_pontuacao_cpf(cpfExtrator)
            if extrator.numero_documento != numeroDocumento:
                pesquisa_nr_documento_banco = ExtratorModel.query.filter_by(
                    numero_documento=numeroDocumento
                ).first()
                if pesquisa_nr_documento_banco:
                    gravar_banco = False
                    validacao_campos_erros["cpfExtrator"] = (
                        f"O CPF informado já existe no banco de dados!"
                    )
            identificacaoExtrator = nomeExtrator
            tipoCadastroExtrator = 1

        if tipoCadastro == 'cnpj':
            verificacao_cnpj = ValidaForms.validar_cnpj(cnpj)
            if not "validado" in verificacao_cnpj:
                gravar_banco = False
                validacao_campos_erros.update(verificacao_cnpj)

            numeroDocumento = ValidaDocs.remove_pontuacao_cnpj(cnpj)
            if extrator.numero_documento != numeroDocumento:
                pesquisa_nr_documento_banco = ExtratorModel.query.filter_by(
                    numero_documento=numeroDocumento
                ).first()
                if pesquisa_nr_documento_banco:
                    gravar_banco = False
                    validacao_campos_erros["cnpj"] = (
                        f"O CNPJ informado já existe no banco de dados!"
                    )
            identificacaoExtrator = razao_social
            tipoCadastroExtrator = 0

        if gravar_banco == True:
            telefone_tratado = Tels.remove_pontuacao_telefone_celular_br(telefone)

            # === Comparação de Objetos ===

            obj2 = {
                "tipoCadastro": tipoCadastro,
                "razaoSocial": razao_social.strip() if tipoCadastro == "cnpj" else extrator.identificacao,
                "nomeExtrator": nomeExtrator.strip() if tipoCadastro == "cpf" else extrator.identificacao,
                "cnpj": numeroDocumento if tipoCadastro == "cnpj" else extrator.numero_documento,
                "cpfExtrator": numeroDocumento if tipoCadastro == "cpf" else extrator.numero_documento,
                "telefone": telefone_tratado.strip(),
                "instituicao_financeira": int(instituicao_financeira) if instituicao_financeira else extrator.instituicao_financeira_id,
                "agencia_bancaria": agencia_bancaria.strip() if agencia_bancaria else extrator.agencia_bancaria,
                "conta_bancaria": conta_bancaria.strip() if conta_bancaria else extrator.conta_bancaria,
                "chave_pix": chave_pix.strip() if chave_pix else extrator.chave_pix
            }


            diferencas = Gameficacao.compara_objetos(dados_corretos, obj2)
            if diferencas:
                acao = TipoAcaoEnum.EDICAO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    acao,
                    acao.pontos,
                    modulo='extrator'
                )

            extrator.tipo_cadastro = tipoCadastroExtrator
            extrator.identificacao = identificacaoExtrator
            extrator.numero_documento = numeroDocumento
            extrator.telefone = telefone_tratado
            extrator.instituicao_financeira_id = int(instituicao_financeira) if instituicao_financeira else None
            extrator.agencia_bancaria = agencia_bancaria.strip() if agencia_bancaria else None
            extrator.conta_bancaria = conta_bancaria.strip() if conta_bancaria else None
            extrator.chave_pix = chave_pix.strip() if chave_pix else None


            pessoa_financeira = PessoaFinanceiroModel.query.filter_by(
                numero_documento=numero_documento,
                ativo=True,
                deletado=False
            ).first()

            if pessoa_financeira:
                try:
                    print(f"Atualizando Pessoa Financeira ID: {pessoa_financeira.id}")

                    pessoa_financeira.tipo_cadastro = True if tipoCadastroExtrator == 1 else False
                    pessoa_financeira.identificacao = identificacaoExtrator
                    pessoa_financeira.numero_documento = numeroDocumento
                    pessoa_financeira.telefone = telefone_tratado
                    pessoa_financeira.instituicao_financeira_id = int(instituicao_financeira) if instituicao_financeira else None
                    pessoa_financeira.agencia_bancaria = agencia_bancaria.strip() if agencia_bancaria else None
                    pessoa_financeira.conta_bancaria = conta_bancaria.strip() if conta_bancaria else None
                    pessoa_financeira.chave_pix = chave_pix.strip() if chave_pix else None

                    # Atualizar vínculos
                    vinculos_atuais = pessoa_financeira.vinculos_operacionais or {}
                    vinculos_atuais["extrator"] = [{
                        "id": str(extrator.id),
                        "identificacao": identificacaoExtrator
                    }]

                    pessoa_financeira.vinculos_operacionais = vinculos_atuais
                    flag_modified(pessoa_financeira, "vinculos_operacionais")

                    db.session.flush()

                    print(f"Pessoa Financeira atualizada com sucesso!")
                    print(f"Vínculos: {json.dumps(vinculos_atuais, indent=2, ensure_ascii=False)}")

                except Exception as e:
                    print(f"Erro ao atualizar Pessoa Financeira: {e}")
                    import traceback
                    traceback.print_exc()
            
            db.session.commit()
            flash(("Extrator editado com sucesso!", "success"))
            return redirect(url_for("listar_extratores"))

    return render_template(
        "gerenciar/extratores/extrator_editar.html", extrator=extrator,
        bancos=bancos,
        campos_obrigatorios=validacao_campos_obrigatorios,
        dados_corretos=dados_corretos,
        campos_erros=validacao_campos_erros)


@app.route("/gerenciar/extrator/desativar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def desativar_extrator(id):
    extrator = ExtratorModel.obter_extrator_por_id(id)

    if extrator is None:
        flash(("Extrator não encontrado", "warning"))
    extrator.ativo = False
    db.session.commit()
    flash(("Extrator desativado com sucesso!", "success"))
    return redirect(url_for("listar_extratores"))

@app.route("/gerenciar/extrator/ativar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def ativar_extrator(id):
    extrator = ExtratorModel.obter_extrator_por_id(id)

    if extrator is None:
        flash(("Extrator não encontrado", "warning"))
    extrator.ativo = True
    db.session.commit()
    flash(("Extrator ativado com sucesso!", "success"))
    return redirect(url_for("listar_extratores"))

