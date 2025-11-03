from sistema import app, db, requires_roles, current_user
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.parametros.instituicoes_financeiras.instituicao_financeira_model import InstituicoesFinanceirasModel
from sistema._utilitarios import *

@app.route("/gerenciar/clientes", methods=["GET"])
@login_required
@requires_roles
def listar_clientes():
    if any(request.args.values()):
        celular = request.args.get('celular')
        celularFormatado = ValidaDocs.somente_numeros(celular) if celular else None
        
        clientes = ClienteModel.filtrar_clientes(
            identificacao=request.args.get('identificacao'),
            celular=celularFormatado
        )
    else:
        clientes = ClienteModel.listar_clientes()
        
    return render_template(
        "gerenciar/clientes/clientes_listar.html",
        clientes=clientes,
        dados_corretos=request.args
    )

@app.route("/gerenciar/cliente/cadastrar", methods=["GET", "POST"])
@login_required
@requires_roles
def cadastrar_cliente():
    usuarioId = current_user.id
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    bancos = InstituicoesFinanceirasModel.obter_todos_bancos()

    if request.method == "POST":
        tipo_cadastro = request.form["tipoCadastro"]
        nome_completo = request.form["nomeCompleto"]
        razao_social = request.form["razaoSocial"]
        cpf = request.form["cpf"]
        cnpj = request.form["cnpj"]
        telefone = request.form["telefone"]

        instituicao_financeira = request.form["instituicao_financeira"]
        agencia_bancaria = request.form["agencia_bancaria"]
        conta_bancaria = request.form["conta_bancaria"]
        chave_pix = request.form["chave_pix"]

        eucaPrecoVenda1 = request.form["eucaPrecoVenda1"]
        eucaPrecoVenda2 = request.form["eucaPrecoVenda2"]
        eucaPrecoVenda3 = request.form["eucaPrecoVenda3"]
        eucaPrecoVenda4 = request.form["eucaPrecoVenda4"]

        pinusPrecoVenda1 = request.form["pinusPrecoVenda1"]
        pinusPrecoVenda2 = request.form["pinusPrecoVenda2"]
        pinusPrecoVenda3 = request.form["pinusPrecoVenda3"]
        pinusPrecoVenda4 = request.form["pinusPrecoVenda4"]
        pinusPrecoVenda5 = request.form["pinusPrecoVenda5"]

        bioPrecoVenda5 = request.form["bioPrecoVenda5"]
        
        campos = {
            "telefone": ["Telefone", telefone]
        }

        if tipo_cadastro == "cpf":
            campos["nomeCompleto"] = ["Nome Completo", nome_completo]
            campos["cpf"] = ["CPF", cpf]

        if tipo_cadastro == "cnpj":
            campos["razaoSocial"] = ["Razão Social", razao_social]
            campos["cnpj"] = ["CNPJ", cnpj]

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))

        if tipo_cadastro == "cpf":
            verificacao_cpf = ValidaForms.validar_cpf(cpf)
            if not "validado" in verificacao_cpf:
                gravar_banco = False
                validacao_campos_erros.update(verificacao_cpf)

            cpf_tratado = ValidaDocs.remove_pontuacao_cpf(cpf)
            pesquisa_cpf_banco = ClienteModel.query.filter_by(
                numero_documento=cpf_tratado
            ).first()
            if pesquisa_cpf_banco:
                gravar_banco = False
                validacao_campos_erros["cpf"] = (
                    f"O CPF informado já existe no banco de dados!"
                )

        if tipo_cadastro == "cnpj":
            verificacao_cnpj = ValidaForms.validar_cnpj(cnpj)
            if not "validado" in verificacao_cnpj:
                gravar_banco = False
                validacao_campos_erros.update(verificacao_cnpj)

            cnpj_tratado = ValidaDocs.remove_pontuacao_cnpj(cnpj)
            pesquisa_cnpj_banco = ClienteModel.query.filter_by(
                numero_documento=cnpj_tratado
            ).first()
            if pesquisa_cnpj_banco:
                gravar_banco = False
                validacao_campos_erros["cnpj"] = (
                    f"O CNPJ informado já existe no banco de dados!"
                )

        if gravar_banco == True:
            telefone_tratado = Tels.remove_pontuacao_telefone_celular_br(telefone)
            
            # Conversão dos valores de Eucalipto
            euca_preco_venda_1_float = ValoresMonetarios.converter_string_brl_para_float(eucaPrecoVenda1)
            euca_preco_venda_1_100 = euca_preco_venda_1_float * 100

            euca_preco_venda_2_float = ValoresMonetarios.converter_string_brl_para_float(eucaPrecoVenda2)
            euca_preco_venda_2_100 = euca_preco_venda_2_float * 100

            euca_preco_venda_3_float = ValoresMonetarios.converter_string_brl_para_float(eucaPrecoVenda3)
            euca_preco_venda_3_100 = euca_preco_venda_3_float * 100

            euca_preco_venda_4_float = ValoresMonetarios.converter_string_brl_para_float(eucaPrecoVenda4)
            euca_preco_venda_4_100 = euca_preco_venda_4_float * 100

            # Conversão dos valores de Pinus
            pinus_preco_venda_1_float = ValoresMonetarios.converter_string_brl_para_float(pinusPrecoVenda1)
            pinus_preco_venda_1_100 = pinus_preco_venda_1_float * 100

            pinus_preco_venda_2_float = ValoresMonetarios.converter_string_brl_para_float(pinusPrecoVenda2)
            pinus_preco_venda_2_100 = pinus_preco_venda_2_float * 100

            pinus_preco_venda_3_float = ValoresMonetarios.converter_string_brl_para_float(pinusPrecoVenda3)
            pinus_preco_venda_3_100 = pinus_preco_venda_3_float * 100

            pinus_preco_venda_4_float = ValoresMonetarios.converter_string_brl_para_float(pinusPrecoVenda4)
            pinus_preco_venda_4_100 = pinus_preco_venda_4_float * 100

            pinus_preco_venda_5_float = ValoresMonetarios.converter_string_brl_para_float(pinusPrecoVenda5)
            pinus_preco_venda_5_100 = pinus_preco_venda_5_float * 100

            bio_preco_venda_5_100 = int(ValoresMonetarios.converter_string_brl_para_float(bioPrecoVenda5) * 100)

            if tipo_cadastro == "cpf":
                tipo_cadastro = 1
                identificacao = nome_completo
                numero_documento = cpf_tratado
                

            if tipo_cadastro == "cnpj":
                tipo_cadastro = 0
                identificacao = razao_social
                numero_documento = cnpj_tratado

            cliente = ClienteModel(
                fatura_via_cpf=tipo_cadastro,
                identificacao=identificacao,
                numero_documento=numero_documento,
                telefone=telefone_tratado,
                # Bitolas e preços de Eucalipto
                euca_bitola_1_id=1,
                euca_bitola_2_id=2,
                euca_bitola_3_id=3,
                euca_bitola_4_id=4,
                euca_preco_venda_bitola_1_100=euca_preco_venda_1_100,
                euca_preco_venda_bitola_2_100=euca_preco_venda_2_100,
                euca_preco_venda_bitola_3_100=euca_preco_venda_3_100,
                euca_preco_venda_bitola_4_100=euca_preco_venda_4_100,

                # Bitolas e preços de Pinus
                pinus_bitola_1_id=1,
                pinus_bitola_2_id=2,
                pinus_bitola_3_id=3,
                pinus_bitola_4_id=4,
                pinus_bitola_5_id=6,
                pinus_preco_venda_bitola_1_100=pinus_preco_venda_1_100,
                pinus_preco_venda_bitola_2_100=pinus_preco_venda_2_100,
                pinus_preco_venda_bitola_3_100=pinus_preco_venda_3_100,
                pinus_preco_venda_bitola_4_100=pinus_preco_venda_4_100,
                pinus_preco_venda_bitola_5_100=pinus_preco_venda_5_100,

                bio_bitola_5_id=5,
                bio_preco_venda_bitola_5_100=bio_preco_venda_5_100,
                instituicao_financeira_id=instituicao_financeira if instituicao_financeira else None,
                agencia_bancaria=agencia_bancaria if agencia_bancaria else None,
                conta_bancaria=conta_bancaria if conta_bancaria else None,
                chave_pix=chave_pix if chave_pix else None,
                ativo=True
            )
            db.session.add(cliente)
            db.session.commit()

            acao = TipoAcaoEnum.CADASTRO
            PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                usuarioId,
                acao,
                acao.pontos,
                modulo='cliente'
            )

            flash(("Cliente cadastrado com sucesso!", "success"))
            return redirect(url_for("listar_clientes"))

    return render_template(
        "gerenciar/clientes/cliente_cadastrar.html",
        bancos=bancos,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
    )


@app.route("/gerenciar/cliente/editar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_cliente(id):
    cliente = ClienteModel.obter_cliente_por_id(id)
    if cliente is None:
        flash(("Cliente não encontrado!", "warning"))
        return redirect(url_for("listar_clientes"))

    if cliente.ativo == 0:
        flash(("Este cliente não pode ser editado, pois está desativado!", "warning"))
        return redirect(url_for("listar_clientes"))
    
    bancos = InstituicoesFinanceirasModel.obter_todos_bancos()
    
    dados_corretos = {
        "tipoCadastro": "cpf" if cliente.fatura_via_cpf == 1 else "cnpj",
        "razaoSocial": cliente.identificacao or "",
        "nomeCompleto": cliente.identificacao or "",
        "cpf": cliente.numero_documento,
        "cnpj": cliente.numero_documento,
        "telefone": cliente.telefone,
        "instituicao_financeira": cliente.instituicao_financeira_id or "",
        "agencia_bancaria": cliente.agencia_bancaria or "",
        "conta_bancaria": cliente.conta_bancaria or "",
        "chave_pix": cliente.chave_pix or "",
        "bioPrecoVenda5": cliente.bio_preco_venda_bitola_5_100,
        "eucaPrecoVenda1": cliente.euca_preco_venda_bitola_1_100,
        "eucaPrecoVenda2": cliente.euca_preco_venda_bitola_2_100,
        "eucaPrecoVenda3": cliente.euca_preco_venda_bitola_3_100,
        "eucaPrecoVenda4": cliente.euca_preco_venda_bitola_4_100,
        "pinusPrecoVenda1": cliente.pinus_preco_venda_bitola_1_100,
        "pinusPrecoVenda2": cliente.pinus_preco_venda_bitola_2_100,
        "pinusPrecoVenda3": cliente.pinus_preco_venda_bitola_3_100,
        "pinusPrecoVenda4": cliente.pinus_preco_venda_bitola_4_100,
        "pinusPrecoVenda4": cliente.pinus_preco_venda_bitola_5_100,
    }

    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    if request.method == "POST":
        tipo_cadastro = request.form["tipoCadastro"]
        nome_completo = request.form["nomeCompleto"]
        razao_social = request.form["razaoSocial"]
        cpf = request.form["cpf"]
        cnpj = request.form["cnpj"]
        telefone = request.form["telefone"]

        instituicao_financeira = request.form["instituicao_financeira"]
        agencia_bancaria = request.form["agencia_bancaria"]
        conta_bancaria = request.form["conta_bancaria"]
        chave_pix = request.form["chave_pix"]

        eucaPrecoVenda1 = request.form["eucaPrecoVenda1"]
        eucaPrecoVenda2 = request.form["eucaPrecoVenda2"]
        eucaPrecoVenda3 = request.form["eucaPrecoVenda3"]
        eucaPrecoVenda4 = request.form["eucaPrecoVenda4"]

        pinusPrecoVenda1 = request.form["pinusPrecoVenda1"]
        pinusPrecoVenda2 = request.form["pinusPrecoVenda2"]
        pinusPrecoVenda3 = request.form["pinusPrecoVenda3"]
        pinusPrecoVenda4 = request.form["pinusPrecoVenda4"]
        pinusPrecoVenda5 = request.form["pinusPrecoVenda5"]

        bioPrecoVenda5 = request.form["bioPrecoVenda5"]
        
        campos = {
            "telefone": ["Telefone", telefone]
        }

        if tipo_cadastro == "cpf":
            campos["nomeCompleto"] = ["Nome Completo", nome_completo]
            campos["cpf"] = ["CPF", cpf]

        if tipo_cadastro == "cnpj":
            campos["razaoSocial"] = ["Razão Social", razao_social]
            campos["cnpj"] = ["CNPJ", cnpj]

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))

        if tipo_cadastro == "cpf":
            verificacao_cpf = ValidaForms.validar_cpf(cpf)
            if not "validado" in verificacao_cpf:
                gravar_banco = False
                validacao_campos_erros.update(verificacao_cpf)

            cpf_tratado = ValidaDocs.remove_pontuacao_cpf(cpf)
            if cliente.numero_documento != cpf_tratado:
                pesquisa_cpf_banco = ClienteModel.query.filter_by(
                    numero_documento=cpf_tratado
                ).first()
                if pesquisa_cpf_banco:
                    gravar_banco = False
                    validacao_campos_erros["cpf"] = (
                        f"O CPF informado já existe no banco de dados!"
                    )

        if tipo_cadastro == "cnpj":
            verificacao_cnpj = ValidaForms.validar_cnpj(cnpj)
            if not "validado" in verificacao_cnpj:
                gravar_banco = False
                validacao_campos_erros.update(verificacao_cnpj)

            cnpj_tratado = ValidaDocs.remove_pontuacao_cnpj(cnpj)
            if cliente.numero_documento != cnpj_tratado:
                pesquisa_cnpj_banco = ClienteModel.query.filter_by(
                    numero_documento=cnpj_tratado
                ).first()
                if pesquisa_cnpj_banco:
                    gravar_banco = False
                    validacao_campos_erros["cnpj"] = (
                        f"O CNPJ informado já existe no banco de dados!"
                    )

        if gravar_banco == True:

            telefone_tratado = Tels.remove_pontuacao_telefone_celular_br(telefone)
            
            # Conversão dos valores de Eucalipto
            euca_preco_venda_1_float = ValoresMonetarios.converter_string_brl_para_float(eucaPrecoVenda1)
            euca_preco_venda_1_100 = euca_preco_venda_1_float * 100

            euca_preco_venda_2_float = ValoresMonetarios.converter_string_brl_para_float(eucaPrecoVenda2)
            euca_preco_venda_2_100 = euca_preco_venda_2_float * 100

            euca_preco_venda_3_float = ValoresMonetarios.converter_string_brl_para_float(eucaPrecoVenda3)
            euca_preco_venda_3_100 = euca_preco_venda_3_float * 100

            euca_preco_venda_4_float = ValoresMonetarios.converter_string_brl_para_float(eucaPrecoVenda4)
            euca_preco_venda_4_100 = euca_preco_venda_4_float * 100

            # Conversão dos valores de Pinus
            pinus_preco_venda_1_float = ValoresMonetarios.converter_string_brl_para_float(pinusPrecoVenda1)
            pinus_preco_venda_1_100 = pinus_preco_venda_1_float * 100

            pinus_preco_venda_2_float = ValoresMonetarios.converter_string_brl_para_float(pinusPrecoVenda2)
            pinus_preco_venda_2_100 = pinus_preco_venda_2_float * 100

            pinus_preco_venda_3_float = ValoresMonetarios.converter_string_brl_para_float(pinusPrecoVenda3)
            pinus_preco_venda_3_100 = pinus_preco_venda_3_float * 100

            pinus_preco_venda_4_float = ValoresMonetarios.converter_string_brl_para_float(pinusPrecoVenda4)
            pinus_preco_venda_4_100 = pinus_preco_venda_4_float * 100

            pinus_preco_venda_5_float = ValoresMonetarios.converter_string_brl_para_float(pinusPrecoVenda5)
            pinus_preco_venda_5_100 = pinus_preco_venda_5_float * 100

            bio_preco_venda_5_100 = int(ValoresMonetarios.converter_string_brl_para_float(bioPrecoVenda5) * 100)

            if tipo_cadastro == "cpf":
                tipo_cadastro = 1
                identificacao = nome_completo
                numero_documento = cpf_tratado
                

            if tipo_cadastro == "cnpj":
                tipo_cadastro = 0
                identificacao = razao_social
                numero_documento = cnpj_tratado
            
            # === Comparação de objetos ===
            obj1 = {
                "tipoCadastro": "cpf" if cliente.fatura_via_cpf == 1 else "cnpj",
                "razaoSocial": cliente.identificacao if cliente.fatura_via_cpf == 0 else "",
                "nomeCompleto": cliente.identificacao if cliente.fatura_via_cpf == 1 else "",
                "cpf": cliente.numero_documento if cliente.fatura_via_cpf == 1 else "",
                "cnpj": cliente.numero_documento if cliente.fatura_via_cpf == 0 else "",
                "telefone": cliente.telefone.strip(),
                "bioPrecoVenda5": cliente.bio_preco_venda_bitola_5_100,
                "eucaPrecoVenda1": cliente.euca_preco_venda_bitola_1_100,
                "eucaPrecoVenda2": cliente.euca_preco_venda_bitola_2_100,
                "eucaPrecoVenda3": cliente.euca_preco_venda_bitola_3_100,
                "eucaPrecoVenda4": cliente.euca_preco_venda_bitola_4_100,
                "pinusPrecoVenda1": cliente.pinus_preco_venda_bitola_1_100,
                "pinusPrecoVenda2": cliente.pinus_preco_venda_bitola_2_100,
                "pinusPrecoVenda3": cliente.pinus_preco_venda_bitola_3_100,
                "pinusPrecoVenda4": cliente.pinus_preco_venda_bitola_4_100,
                "pinusPrecoVenda5": cliente.pinus_preco_venda_bitola_5_100,
                "instituicaoFinanceira": cliente.instituicao_financeira,
                "agenciaBancaria": cliente.agencia_bancaria,
                "contaBancaria": cliente.conta_bancaria,
                "chavePix": cliente.chave_pix,
            }

            obj2 = {
                "tipoCadastro": "cpf" if tipo_cadastro == 1 else "cnpj",
                "razaoSocial": razao_social.strip() if tipo_cadastro == 0 else "",
                "nomeCompleto": nome_completo.strip() if tipo_cadastro == 1 else "",
                "cpf": cpf_tratado if tipo_cadastro == 1 else "",
                "cnpj": cnpj_tratado if tipo_cadastro == 0 else "",
                "telefone": telefone_tratado.strip(),
                "bioPrecoVenda5": bio_preco_venda_5_100,
                "eucaPrecoVenda1": euca_preco_venda_1_100,
                "eucaPrecoVenda2": euca_preco_venda_2_100,
                "eucaPrecoVenda3": euca_preco_venda_3_100,
                "eucaPrecoVenda4": euca_preco_venda_4_100,
                "pinusPrecoVenda1": pinus_preco_venda_1_100,
                "pinusPrecoVenda2": pinus_preco_venda_2_100,
                "pinusPrecoVenda3": pinus_preco_venda_3_100,
                "pinusPrecoVenda4": pinus_preco_venda_4_100,
                "pinusPrecoVenda5": pinus_preco_venda_5_100,
                "instituicaoFinanceira": int(instituicao_financeira) if instituicao_financeira else None,
                "agenciaBancaria": agencia_bancaria.strip() if agencia_bancaria else None,
                "contaBancaria": conta_bancaria.strip() if conta_bancaria else None,
                "chavePix": chave_pix.strip() if chave_pix else None,
            }

            # === Registra Pontuação ===

            diferencas = Gameficacao.compara_objetos(obj1, obj2)
            if diferencas == True:
                acao = TipoAcaoEnum.EDICAO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    acao,
                    acao.pontos,
                    modulo='cliente'
                )

            cliente.fatura_via_cpf=tipo_cadastro
            cliente.identificacao=identificacao
            cliente.numero_documento=numero_documento
            cliente.telefone=telefone_tratado
            cliente.instituicao_financeira_id=instituicao_financeira if instituicao_financeira else None
            cliente.agencia_bancaria=agencia_bancaria if agencia_bancaria else None
            cliente.conta_bancaria=conta_bancaria if conta_bancaria else None
            cliente.chave_pix=chave_pix if chave_pix else None
            # Bitolas e preços de Eucalipto
            cliente.euca_bitola_1_id=1
            cliente.euca_bitola_2_id=2
            cliente.euca_bitola_3_id=3
            cliente.euca_bitola_4_id=4
            cliente.euca_preco_venda_bitola_1_100=euca_preco_venda_1_100
            cliente.euca_preco_venda_bitola_2_100=euca_preco_venda_2_100
            cliente.euca_preco_venda_bitola_3_100=euca_preco_venda_3_100
            cliente.euca_preco_venda_bitola_4_100=euca_preco_venda_4_100
            cliente.bio_bitola_5_id=5
            cliente.pinus_bitola_1_id=1
            cliente.pinus_bitola_2_id=2
            cliente.pinus_bitola_3_id=3
            cliente.pinus_bitola_4_id=4
            cliente.pinus_bitola_5_id=6
            cliente.bio_preco_venda_bitola_5_100=bio_preco_venda_5_100
            cliente.pinus_preco_venda_bitola_1_100=pinus_preco_venda_1_100
            cliente.pinus_preco_venda_bitola_2_100=pinus_preco_venda_2_100
            cliente.pinus_preco_venda_bitola_3_100=pinus_preco_venda_3_100
            cliente.pinus_preco_venda_bitola_4_100=pinus_preco_venda_4_100
            cliente.pinus_preco_venda_bitola_5_100=pinus_preco_venda_5_100
            cliente.ativo=True

            db.session.commit()

            flash(("Cliente editado com sucesso!", "success"))
            return redirect(url_for("listar_clientes"))

    return render_template(
        "gerenciar/clientes/cliente_editar.html",
        cliente=cliente,
        bancos=bancos,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=dados_corretos
    )


@app.route("/gerenciar/cliente/desativar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def desativar_cliente(id):
    cliente = ClienteModel.obter_cliente_por_id(id)
    if cliente is None:
        flash(("Cliente não encontrado!", "warning"))
    cliente.ativo = 0
    db.session.commit()
    flash(('Cliente desativado com sucesso!', 'success'))
    return redirect(url_for("listar_clientes"))


@app.route("/gerenciar/cliente/ativar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def ativar_cliente(id):
    cliente = ClienteModel.obter_cliente_por_id(id)
    if cliente is None:
        flash(("Cliente não encontrado!", "warning"))
    cliente.ativo = 1
    db.session.commit()
    flash(('Cliente ativado com sucesso!', 'success'))
    return redirect(url_for("listar_clientes"))
