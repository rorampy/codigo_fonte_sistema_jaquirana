from sistema import app, requires_roles, db, current_user
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from sistema.models_views.gerenciar.fornecedor.fornecedor_model import FornecedorModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_madeira_posta_model import FornecedorMadeiraPostaModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_comissionado_model import FornecedorComissionadoModel
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.upload_arquivo.upload_arquivo_model import UploadArquivoModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.faturamento.cargas_a_pagar.fornecedor.fornecedor_a_pagar_model import FornecedorPagarModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.controle_carga.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.gerenciar.extrator.extrator_model import ExtratorModel
from sistema.models_views.gerenciar.comissionado.comissionado_model import ComissionadoModel
from sistema.models_views.parametros.instituicoes_financeiras.instituicao_financeira_model import InstituicoesFinanceirasModel
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema._utilitarios import *


@app.route("/gerenciar/fornecedores", methods=["GET"])
@login_required
@requires_roles
def listar_fornecedores():
    if any(request.args.values()):
        numeroDoc = request.args.get("numeroDocumento")
        numeroDocFormatado = ValidaDocs.somente_numeros(numeroDoc) if numeroDoc else None

        celular = request.args.get("celular")
        celularFormatado = ValidaDocs.somente_numeros(celular) if celular else None
        
        fornecedores = FornecedorModel.filtrar_fornecedores(
            identificacao=request.args.get("identificacao"),
            numero_documento=numeroDocFormatado,
            celular=celularFormatado,
        )
    else:
        fornecedores = FornecedorModel.listar_fornecedores()
        
    return render_template(
        "gerenciar/fornecedores/fornecedores_listar.html",
        fornecedores=fornecedores,
        dados_corretos=request.args,
    )

@app.route("/gerenciar/fornecedores/cadastrar", methods=["GET", "POST"])
@login_required
@requires_roles
def cadastrar_fornecedor():
    try:
        validacao_campos_obrigatorios = {}
        validacao_campos_erros = {}
        gravar_banco = True

        extratores = ExtratorModel.listar_extratores_ativos()
        clientes = ClienteModel.listar_clientes_ativos()
        transportadoras = TransportadoraModel.listar_transportadoras_ativas()
        comissionados = ComissionadoModel.listar_comissionados_ativos()
        bancos = InstituicoesFinanceirasModel.obter_todos_bancos()

        if request.method == "POST":

            tipoContribuicao = request.form.get("tipoContribuicao", "")
            declaracaoSenar = request.files.get("declaracaoSenar")
            classeFornecedor = request.form.get("classeFornecedor")
            controleEntrada = request.form.get("controleEntrada")
            valorContrato = request.form.get("valorContrato")
            tipo_cadastro = request.form.get("tipoCadastro", "")
            custoExtracao = request.form.get("custoExtracao", "")
            nome_completo = request.form.get("nomeCompleto", "").strip()
            razao_social = request.form.get("razaoSocial", "").strip()
            cpf = request.form.get("cpf", "").strip()
            cnpj = request.form.get("cnpj", "").strip()
            telefone = request.form.get("telefone", "").strip()

            instituicao_financeira = request.form["instituicao_financeira"]
            agencia_bancaria = request.form["agencia_bancaria"]
            conta_bancaria = request.form["conta_bancaria"]
            chave_pix = request.form["chave_pix"]

            eucaPrecoCusto1 = request.form.get("eucaPrecoCusto1", "0")
            eucaPrecoCusto2 = request.form.get("eucaPrecoCusto2", "0")
            eucaPrecoCusto3 = request.form.get("eucaPrecoCusto3", "0")
            eucaPrecoCusto4 = request.form.get("eucaPrecoCusto4", "0")

            pinusPrecoCusto1 = request.form.get("pinusPrecoCusto1", "0")
            pinusPrecoCusto2 = request.form.get("pinusPrecoCusto2", "0")
            pinusPrecoCusto3 = request.form.get("pinusPrecoCusto3", "0")
            pinusPrecoCusto4 = request.form.get("pinusPrecoCusto4", "0")
            pinusPrecoCusto5 = request.form.get("pinusPrecoCusto5", "0")

            bioPrecoCusto5 = request.form.get("bioPrecoCusto5", "0")
            bioPrecoCusto7 = request.form.get("bioPrecoCusto7", "0")

            credito_fornecedor = request.form.get("credito_fornecedor", "0")
            contratoFornecedor = request.files.get("contratoFornecedor")

            campos = {
                "telefone": ["Telefone", telefone]
            }
            
            if classeFornecedor == "sim":
                campos["valorContrato"] = ["Valor do Contrato", valorContrato]

            if tipo_cadastro == "cpf":
                campos["nomeCompleto"] = ["Nome Completo", nome_completo]
                campos["cpf"] = ["CPF", cpf]
            else:  
                campos["razaoSocial"] = ["Razão Social", razao_social]
                campos["cnpj"] = ["CNPJ", cnpj]

            if tipoContribuicao == "senar":
                campos["declaracaoSenar"] = ["Declaração Senar", declaracaoSenar]

            if custoExtracao == 'possui':
                extratorNome = request.form.get("extratorNome", "")
                eucaCustoExtracao1 = request.form.get("eucaCustoExtracao1", "0")
                eucaCustoExtracao2 = request.form.get("eucaCustoExtracao2", "0")
                eucaCustoExtracao3 = request.form.get("eucaCustoExtracao3", "0")
                eucaCustoExtracao4 = request.form.get("eucaCustoExtracao4", "0")
                pinusCustoExtracao1 = request.form.get("pinusCustoExtracao1", "0")
                pinusCustoExtracao2 = request.form.get("pinusCustoExtracao2", "0")
                pinusCustoExtracao3 = request.form.get("pinusCustoExtracao3", "0")
                pinusCustoExtracao4 = request.form.get("pinusCustoExtracao4", "0")
                pinusCustoExtracao5 = request.form.get("pinusCustoExtracao5", "0")
                bioCustoExtracao5 = request.form.get("bioCustoExtracao5", "0")
                bioCustoExtracao7 = request.form.get("bioCustoExtracao7", "0")

                campos["extratorNome"] = ["Extrator", extratorNome]

            madeira_posta = True if request.form.get("madeiraPosta") == "possui" else False
            possui_comissionado = True if request.form.get("possuiComissionado") == "possui" else False

            if madeira_posta:
                lista_clientes_mp = request.form.getlist("clienteMadeiraPosta[]")
                if not lista_clientes_mp or all(not cid for cid in lista_clientes_mp):
                    campos["clienteMadeiraPosta"] = ["Cliente", ""]

                lista_transportadora_mp = request.form.getlist("transportadoraMadeiraPosta[]")
                if not lista_transportadora_mp or all(not cid for cid in lista_transportadora_mp):
                    campos["transportadoraMadeiraPosta"] = ["Transportadora", ""]

            # Validação de campos obrigatórios
            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
            if "validado" not in validacao_campos_obrigatorios:
                gravar_banco = False
                flash(("Verifique os campos destacados em vermelho!", "warning"))

            # Validação de CPF / CNPJ
            if tipo_cadastro == "cpf":
                verificacao_cpf = ValidaForms.validar_cpf(cpf)
                if "validado" not in verificacao_cpf:
                    gravar_banco = False
                    validacao_campos_erros.update(verificacao_cpf)

                cpf_tratado = ValidaDocs.remove_pontuacao_cpf(cpf)
                pesquisa_cpf_banco = FornecedorModel.query.filter_by(
                    numero_documento=cpf_tratado
                ).first()
                if pesquisa_cpf_banco:
                    gravar_banco = False
                    validacao_campos_erros["cpf"] = "O CPF informado já existe no banco de dados!"

            else:  
                verificacao_cnpj = ValidaForms.validar_cnpj(cnpj)
                if "validado" not in verificacao_cnpj:
                    gravar_banco = False
                    validacao_campos_erros.update(verificacao_cnpj)

                cnpj_tratado = ValidaDocs.remove_pontuacao_cnpj(cnpj)
                pesquisa_cnpj_banco = FornecedorModel.query.filter_by(
                    numero_documento=cnpj_tratado
                ).first()
                if pesquisa_cnpj_banco:
                    gravar_banco = False
                    validacao_campos_erros["cnpj"] = "O CNPJ informado já existe no banco de dados!"

            if gravar_banco:
                telefone_tratado = Tels.remove_pontuacao_telefone_celular_br(telefone)

                euca_preco_custo_1_100 = int(ValoresMonetarios.converter_string_brl_para_float(eucaPrecoCusto1) * 100)
                euca_preco_custo_2_100 = int(ValoresMonetarios.converter_string_brl_para_float(eucaPrecoCusto2) * 100)
                euca_preco_custo_3_100 = int(ValoresMonetarios.converter_string_brl_para_float(eucaPrecoCusto3) * 100)
                euca_preco_custo_4_100 = int(ValoresMonetarios.converter_string_brl_para_float(eucaPrecoCusto4) * 100)

                pinus_preco_custo_1_100 = int(ValoresMonetarios.converter_string_brl_para_float(pinusPrecoCusto1) * 100)
                pinus_preco_custo_2_100 = int(ValoresMonetarios.converter_string_brl_para_float(pinusPrecoCusto2) * 100)
                pinus_preco_custo_3_100 = int(ValoresMonetarios.converter_string_brl_para_float(pinusPrecoCusto3) * 100)
                pinus_preco_custo_4_100 = int(ValoresMonetarios.converter_string_brl_para_float(pinusPrecoCusto4) * 100)
                pinus_preco_custo_5_100 = int(ValoresMonetarios.converter_string_brl_para_float(pinusPrecoCusto5) * 100)

                bio_preco_custo_5_100 = int(ValoresMonetarios.converter_string_brl_para_float(bioPrecoCusto5) * 100)
                bio_preco_custo_7_100 = int(ValoresMonetarios.converter_string_brl_para_float(bioPrecoCusto7) * 100)
                

                # Converter custos de extração (se houver)
                if custoExtracao == 'possui':
                    
                    euca_custo_extracao_1_100 = int(ValoresMonetarios.converter_string_brl_para_float(eucaCustoExtracao1) * 100)

                    euca_custo_extracao_2_100 = int(ValoresMonetarios.converter_string_brl_para_float(eucaCustoExtracao2) * 100)

                    euca_custo_extracao_3_100 = int(ValoresMonetarios.converter_string_brl_para_float(eucaCustoExtracao3) * 100)
                
                    euca_custo_extracao_4_100 = int(ValoresMonetarios.converter_string_brl_para_float(eucaCustoExtracao4) * 100)

                
                    pinus_custo_extracao_1_100 = int(ValoresMonetarios.converter_string_brl_para_float(pinusCustoExtracao1) * 100)
                
                    pinus_custo_extracao_2_100 = int(ValoresMonetarios.converter_string_brl_para_float(pinusCustoExtracao2) * 100)
                
                    pinus_custo_extracao_3_100 = int(ValoresMonetarios.converter_string_brl_para_float(pinusCustoExtracao3) * 100)
                
                    pinus_custo_extracao_4_100 = int(ValoresMonetarios.converter_string_brl_para_float(pinusCustoExtracao4) * 100)

                    pinus_custo_extracao_5_100 = int(ValoresMonetarios.converter_string_brl_para_float(pinusCustoExtracao5) * 100)
                    
                    bio_custo_extracao_5_100 = int(ValoresMonetarios.converter_string_brl_para_float(bioCustoExtracao5) * 100)
                    bio_custo_extracao_7_100 = int(ValoresMonetarios.converter_string_brl_para_float(bioCustoExtracao7) * 100)

                else:
                    euca_custo_extracao_1_100 = euca_custo_extracao_2_100 = None
                    euca_custo_extracao_3_100 = euca_custo_extracao_4_100 = None
                    pinus_custo_extracao_1_100 = pinus_custo_extracao_2_100 = None
                    pinus_custo_extracao_3_100 = pinus_custo_extracao_4_100 = None
                    pinus_custo_extracao_5_100 = None
                    bio_custo_extracao_5_100 = None
                    bio_custo_extracao_7_100 = None

                credito_fornecedor_ton_100 = int(ValoresMonetarios.converter_string_brl_para_float(credito_fornecedor) * 100)
                
                if classeFornecedor == "sim":
                    valor_contrato = int(ValoresMonetarios.converter_string_brl_para_float(valorContrato) * 100)
                
                if tipo_cadastro == "cpf":
                    fatura_via_cpf = True
                    identificacao = nome_completo
                    numero_documento = cpf_tratado
                else:
                    fatura_via_cpf = False
                    identificacao = razao_social
                    numero_documento = cnpj_tratado

                fornecedor = FornecedorModel(
                    fatura_via_cpf=fatura_via_cpf,
                    identificacao=identificacao,
                    numero_documento=numero_documento,
                    telefone=telefone_tratado,
                    funrural = True if tipoContribuicao == 'funrural' else False,
                    senar = True if tipoContribuicao == 'senar' else False,
                    imposto_id=1 if tipoContribuicao == 'funrural' else 2,
                    extrator_id=(request.form.get("extratorNome") if custoExtracao == 'possui' else None),
                    custo_extracao=(1 if custoExtracao == 'possui' else 0),
                    # Bitolas e preços Eucalipto
                    euca_bitola_1_id=1,
                    euca_bitola_2_id=2,
                    euca_bitola_3_id=3,
                    euca_bitola_4_id=4,
                    euca_preco_custo_bitola_1_100=euca_preco_custo_1_100,
                    euca_preco_custo_bitola_2_100=euca_preco_custo_2_100,
                    euca_preco_custo_bitola_3_100=euca_preco_custo_3_100,
                    euca_preco_custo_bitola_4_100=euca_preco_custo_4_100,
                    # Bitolas e preços Pinus
                    pinus_bitola_1_id=1,
                    pinus_bitola_2_id=2,
                    pinus_bitola_3_id=3,
                    pinus_bitola_4_id=4,
                    pinus_bitola_5_id=6, # Madeira Serrada
                    pinus_preco_custo_bitola_1_100=pinus_preco_custo_1_100,
                    pinus_preco_custo_bitola_2_100=pinus_preco_custo_2_100,
                    pinus_preco_custo_bitola_3_100=pinus_preco_custo_3_100,
                    pinus_preco_custo_bitola_4_100=pinus_preco_custo_4_100,
                    pinus_preco_custo_bitola_5_100=pinus_preco_custo_5_100,
                    # Bitola e preço Biomassa
                    bio_bitola_5_id=5,
                    bio_preco_custo_bitola_5_100=bio_preco_custo_5_100,
                    bio_bitola_7_id=7, # Madeira Biomassa
                    bio_preco_custo_bitola_7_100=bio_preco_custo_7_100,
                    # Custo extração
                    euca_custo_extracao_bitola_1_100=euca_custo_extracao_1_100,
                    euca_custo_extracao_bitola_2_100=euca_custo_extracao_2_100,
                    euca_custo_extracao_bitola_3_100=euca_custo_extracao_3_100,
                    euca_custo_extracao_bitola_4_100=euca_custo_extracao_4_100,
                    pinus_custo_extracao_bitola_1_100=pinus_custo_extracao_1_100,
                    pinus_custo_extracao_bitola_2_100=pinus_custo_extracao_2_100,
                    pinus_custo_extracao_bitola_3_100=pinus_custo_extracao_3_100,
                    pinus_custo_extracao_bitola_4_100=pinus_custo_extracao_4_100,
                    pinus_custo_extracao_bitola_5_100=pinus_custo_extracao_5_100,

                    bio_custo_extracao_bitola_5_100=bio_custo_extracao_5_100,
                    bio_custo_extracao_bitola_7_100=bio_custo_extracao_7_100,
                    contrato_fornecedor_id=None,
                    credito_100=credito_fornecedor_ton_100,
                    instituicao_financeira_id=instituicao_financeira if instituicao_financeira else None,
                    agencia_bancaria=agencia_bancaria if agencia_bancaria else None,
                    conta_bancaria=conta_bancaria if conta_bancaria else None,
                    chave_pix=chave_pix if chave_pix else None,
                    classe_fornecedor=(True if classeFornecedor == "sim" else False),
                    valor_contrato_100=(valor_contrato if classeFornecedor == "sim" else None),
                    controle_entrada=(True if controleEntrada == "sim" else False),
                    ativo=True,
                )

                # Flag de madeira posta
                fornecedor.madeira_posta = madeira_posta
                # Flag de possui comissionado
                fornecedor.possui_comissionado = possui_comissionado

                db.session.add(fornecedor)
                db.session.flush()  

                # Se a contribuição for senar e tiver dados
                if tipoContribuicao == "senar" and declaracaoSenar and declaracaoSenar.filename:
                    print('Entrei aqu')
                    if declaracaoSenar.mimetype in ["application/pdf", "image/jpeg", "image/png"]:
                        declaracao_upload = upload_arquivo(
                            declaracaoSenar,
                            "UPLOAD_DECLARACAO_SENAR",
                            f"{fornecedor.id}",
                        )
                        fornecedor.arquivo_senar_id = declaracao_upload.id
                        db.session.flush()
                    else:
                        flash(("A declaração senar deve estar em formato PDF ou JPG ou JPGE ou PNG.", "warning"))
                        return redirect(url_for("cadastrar_fornecedor"))

                # Salvar contrato se houver
                if contratoFornecedor and contratoFornecedor.filename:
                    if contratoFornecedor.mimetype == "application/pdf":
                        contrato_upload = upload_arquivo(
                            contratoFornecedor,
                            "UPLOAD_CONTRATO_FORNECEDOR",
                            f"{fornecedor.id}",
                        )
                        fornecedor.contrato_fornecedor_id = contrato_upload.id
                        db.session.flush()
                    else:
                        flash(("O contrato do fornecedor deve estar em formato PDF.", "warning"))
                        return redirect(url_for("cadastrar_fornecedor"))

                # Inserir entradas de “Madeira Posta” se marcado
                if madeira_posta:
                    # Capturar listas do formulário
                    cliente_ids_list = request.form.getlist("clienteMadeiraPosta[]")
                    transportadora_ids_list = request.form.getlist("transportadoraMadeiraPosta[]")
                    euca1_list = request.form.getlist("eucaMadeiraPosta1[]")
                    euca2_list = request.form.getlist("eucaMadeiraPosta2[]")
                    euca3_list = request.form.getlist("eucaMadeiraPosta3[]")
                    euca4_list = request.form.getlist("eucaMadeiraPosta4[]")
                    pinus1_list = request.form.getlist("pinusMadeiraPosta1[]")
                    pinus2_list = request.form.getlist("pinusMadeiraPosta2[]")
                    pinus3_list = request.form.getlist("pinusMadeiraPosta3[]")
                    pinus4_list = request.form.getlist("pinusMadeiraPosta4[]")
                    pinus5_list = request.form.getlist("pinusMadeiraPosta5[]")
                    bio5_list = request.form.getlist("bioMadeiraPosta5[]")
                    bio7_list = request.form.getlist("bioMadeiraPosta7[]")

                    for idx, cid_str in enumerate(cliente_ids_list):
                        try:
                            cid = int(cid_str)
                        except ValueError:
                            continue
                        
                        # Obter transportadora correspondente (mesmo índice)
                        tid = None
                        if idx < len(transportadora_ids_list):
                            try:
                                tid = int(transportadora_ids_list[idx]) if transportadora_ids_list[idx] else None
                            except (ValueError, IndexError):
                                tid = None

                        e1 = int(ValoresMonetarios.converter_string_brl_para_float(euca1_list[idx]) * 100)
                    
                        e2 = int(ValoresMonetarios.converter_string_brl_para_float(euca2_list[idx]) * 100)
                    
                        e3 = int(ValoresMonetarios.converter_string_brl_para_float(euca3_list[idx]) * 100)
                    
                        e4 = int(ValoresMonetarios.converter_string_brl_para_float(euca4_list[idx]) * 100)
                    
                        p1 = int(ValoresMonetarios.converter_string_brl_para_float(pinus1_list[idx]) * 100)
                    
                        p2 = int(ValoresMonetarios.converter_string_brl_para_float(pinus2_list[idx]) * 100)
                    
                        p3 = int(ValoresMonetarios.converter_string_brl_para_float(pinus3_list[idx]) * 100)
                    
                        p4 = int(ValoresMonetarios.converter_string_brl_para_float(pinus4_list[idx]) * 100)

                        p5 = int(ValoresMonetarios.converter_string_brl_para_float(pinus5_list[idx]) * 100)

                        b5 = int(ValoresMonetarios.converter_string_brl_para_float(bio5_list[idx]) * 100)
                        
                        b7 = int(ValoresMonetarios.converter_string_brl_para_float(bio7_list[idx]) * 100)
                        
                        mp = FornecedorMadeiraPostaModel(
                            fornecedor_id=fornecedor.id,
                            cliente_id=cid,
                            transportadora_id=tid,
                            euca_bitola_1_id=1,
                            euca_bitola_2_id=2,
                            euca_bitola_3_id=3,
                            euca_bitola_4_id=4,
                            pinus_bitola_1_id=1,
                            pinus_bitola_2_id=2,
                            pinus_bitola_3_id=3,
                            pinus_bitola_4_id=4,
                            pinus_bitola_5_id=6, 
                            bio_bitola_5_id=5,
                            euca_bitola_1_preco_100=e1,
                            euca_bitola_2_preco_100=e2,
                            euca_bitola_3_preco_100=e3,
                            euca_bitola_4_preco_100=e4,
                            pinus_bitola_1_preco_100=p1,
                            pinus_bitola_2_preco_100=p2,
                            pinus_bitola_3_preco_100=p3,
                            pinus_bitola_4_preco_100=p4,
                            pinus_bitola_5_preco_100=p5,
                            bio_bitola_5_preco_100=b5,
                            bio_bitola_7_id=7,
                            bio_bitola_7_preco_100=b7,
                        )
                        db.session.add(mp)

                # Processar comissionados vinculados ao fornecedor (apenas se possui_comissionado = True)
                if possui_comissionado:
                    comissionados_list = request.form.getlist("comissionados[]")
                    valores_comissao_list = request.form.getlist("valorComissaoTon[]")

                    # Criar registros de FornecedorComissionadoModel
                    for idx, comissionado_id in enumerate(comissionados_list):
                        if comissionado_id and comissionado_id.strip():
                            valor_comissao_str = valores_comissao_list[idx] if idx < len(valores_comissao_list) else '0'
                            valor_comissao_100 = int(ValoresMonetarios.converter_string_brl_para_float(valor_comissao_str) * 100)
                            
                            fornecedor_comissionado = FornecedorComissionadoModel(
                                fornecedor_id=fornecedor.id,
                                comissionado_id=int(comissionado_id),
                                valor_comissao_ton_100=valor_comissao_100
                            )
                            db.session.add(fornecedor_comissionado)

                # Registrar pontuação de cadastro
                acao = TipoAcaoEnum.CADASTRO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id, acao, acao.pontos, modulo="fornecedor"
                )
                db.session.commit()

                flash(("Fornecedor cadastrado com sucesso!", "success"))
                return redirect(url_for("listar_fornecedores"))

    except Exception as e:
        print(f'Erro ao tentar cadastrar fornecedor: {e}')
        flash(('Houve um erro ao tentar cadastrar fornecedor! Entre em contato com o suporte.', 'warning'))
        return redirect(url_for('cadastrar_fornecedor'))

    # Definir valores padrão para o primeiro acesso (GET)
    dados_corretos_padrao = dict(request.form)
    if request.method == 'GET':
        dados_corretos_padrao['possuiComissionado'] = 'nao_possui'

    return render_template(
        "gerenciar/fornecedores/fornecedor_cadastrar.html",
        campos_obrigatorios=validacao_campos_obrigatorios,
        extratores=extratores,
        bancos=bancos,
        clientes=clientes,
        transportadoras=transportadoras,
        comissionados=comissionados,
        campos_erros=validacao_campos_erros,
        dados_corretos=dados_corretos_padrao,
    )


@app.route("/gerenciar/fornecedor/editar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_fornecedor(id):
    try:
        fornecedor = FornecedorModel.obter_fornecedor_por_id(id)
        if fornecedor is None:
            flash(("Fornecedor não encontrado!", "warning"))
            return redirect(url_for("listar_fornecedores"))

        validacao_campos_obrigatorios = {}
        validacao_campos_erros = {}
        gravar_banco = True
        extratores = ExtratorModel.listar_extratores_ativos()
        clientes = ClienteModel.listar_clientes_ativos()
        transportadoras = TransportadoraModel.listar_transportadoras_ativas()
        comissionados = ComissionadoModel.listar_comissionados_ativos()

        bancos = InstituicoesFinanceirasModel.obter_todos_bancos()

        # Carregar entradas existentes de madeira posta ativas
        madeiras_existentes = [mp for mp in fornecedor.madeiras_posta if mp.ativo]

        # Carregar comissionados existentes
        fornecedor_comissionados = FornecedorComissionadoModel.listar_por_fornecedor(fornecedor.id)

        # Preparar listas para dados_corretos (valores em centavos)
        lista_clientes_mp = []
        lista_transportadoras_mp = []
        lista_euca1_mp = []
        lista_euca2_mp = []
        lista_euca3_mp = []
        lista_euca4_mp = []
        lista_pinus1_mp = []
        lista_pinus2_mp = []
        lista_pinus3_mp = []
        lista_pinus4_mp = []
        lista_pinus5_mp = []
        lista_bio5_mp = []
        lista_bio7_mp = []

        for mp in madeiras_existentes:
            lista_clientes_mp.append(mp.cliente_id)
            lista_transportadoras_mp.append(mp.transportadora_id)
            lista_euca1_mp.append(mp.euca_bitola_1_preco_100 or 0)
            lista_euca2_mp.append(mp.euca_bitola_2_preco_100 or 0)
            lista_euca3_mp.append(mp.euca_bitola_3_preco_100 or 0)
            lista_euca4_mp.append(mp.euca_bitola_4_preco_100 or 0)
            lista_pinus1_mp.append(mp.pinus_bitola_1_preco_100 or 0)
            lista_pinus2_mp.append(mp.pinus_bitola_2_preco_100 or 0)
            lista_pinus3_mp.append(mp.pinus_bitola_3_preco_100 or 0)
            lista_pinus4_mp.append(mp.pinus_bitola_4_preco_100 or 0)
            lista_pinus5_mp.append(mp.pinus_bitola_5_preco_100 or 0)
            lista_bio5_mp.append(mp.bio_bitola_5_preco_100 or 0)
            lista_bio7_mp.append(mp.bio_bitola_7_preco_100 or 0)

        # Preencher valores iniciais em dados_corretos
        dados_corretos = {
            "tipoContribuicao": "funrural" if fornecedor.funrural == 1 else "senar",
            "classeFornecedor": "sim" if fornecedor.classe_fornecedor else "nao",
            "controleEntrada": "sim" if fornecedor.controle_entrada else "nao",
            "valorContrato": fornecedor.valor_contrato_100 if fornecedor.classe_fornecedor == 1 else 0,  
            "tipoCadastro": "cpf" if fornecedor.fatura_via_cpf == 1 else "cnpj",
            "razaoSocial": fornecedor.identificacao if fornecedor.fatura_via_cpf == 0 else "",
            "nomeCompleto": fornecedor.identificacao if fornecedor.fatura_via_cpf == 1 else "",
            "cpf": fornecedor.numero_documento if fornecedor.fatura_via_cpf == 1 else "",
            "cnpj": fornecedor.numero_documento if fornecedor.fatura_via_cpf == 0 else "",
            "telefone": fornecedor.telefone or "",
            "credito_fornecedor": fornecedor.credito_100 or 0,
            "eucaPrecoCusto1": fornecedor.euca_preco_custo_bitola_1_100 or 0,
            "bioPrecoCusto5": fornecedor.bio_preco_custo_bitola_5_100 or 0,
            "bioPrecoCusto7": fornecedor.bio_preco_custo_bitola_7_100 or 0,
            "eucaPrecoCusto2": fornecedor.euca_preco_custo_bitola_2_100 or 0,
            "eucaPrecoCusto3": fornecedor.euca_preco_custo_bitola_3_100 or 0,
            "eucaPrecoCusto4": fornecedor.euca_preco_custo_bitola_4_100 or 0,
            "pinusPrecoCusto1": fornecedor.pinus_preco_custo_bitola_1_100 or 0,
            "pinusPrecoCusto2": fornecedor.pinus_preco_custo_bitola_2_100 or 0,
            "pinusPrecoCusto3": fornecedor.pinus_preco_custo_bitola_3_100 or 0,
            "pinusPrecoCusto4": fornecedor.pinus_preco_custo_bitola_4_100 or 0,
            "pinusPrecoCusto5": fornecedor.pinus_preco_custo_bitola_5_100 or 0,
            "custoExtracao": "possui" if fornecedor.custo_extracao == 1 else "nao_possui",
            "eucaCustoExtracao1": fornecedor.euca_custo_extracao_bitola_1_100 or 0,
            "eucaCustoExtracao2": fornecedor.euca_custo_extracao_bitola_2_100 or 0,
            "eucaCustoExtracao3": fornecedor.euca_custo_extracao_bitola_3_100 or 0,
            "eucaCustoExtracao4": fornecedor.euca_custo_extracao_bitola_4_100 or 0,
            "pinusCustoExtracao1": fornecedor.pinus_custo_extracao_bitola_1_100 or 0,
            "pinusCustoExtracao2": fornecedor.pinus_custo_extracao_bitola_2_100 or 0,
            "pinusCustoExtracao3": fornecedor.pinus_custo_extracao_bitola_3_100 or 0,
            "pinusCustoExtracao4": fornecedor.pinus_custo_extracao_bitola_4_100 or 0,
            "pinusCustoExtracao5": fornecedor.pinus_custo_extracao_bitola_5_100 or 0,
            "bioCustoExtracao5": fornecedor.bio_custo_extracao_bitola_5_100 or 0,
            "madeiraPosta": "possui" if fornecedor.madeira_posta else "nao_possui",
            "possuiComissionado": "possui" if fornecedor.possui_comissionado else "nao_possui",
            # Listas para preencher campos dinâmicos
            "clienteMadeiraPosta": lista_clientes_mp,
            "transportadoraMadeiraPosta": lista_transportadoras_mp,
            "eucaMadeiraPosta1": lista_euca1_mp,
            "eucaMadeiraPosta2": lista_euca2_mp,
            "eucaMadeiraPosta3": lista_euca3_mp,
            "eucaMadeiraPosta4": lista_euca4_mp,
            "pinusMadeiraPosta1": lista_pinus1_mp,
            "pinusMadeiraPosta2": lista_pinus2_mp,
            "pinusMadeiraPosta3": lista_pinus3_mp,
            "pinusMadeiraPosta4": lista_pinus4_mp,
            "pinusMadeiraPosta5": lista_pinus5_mp,
            "bioMadeiraPosta5": lista_bio5_mp,
            "bioMadeiraPosta7": lista_bio7_mp,
            "instituicao_financeira": fornecedor.instituicao_financeira_id or "",
            "agencia_bancaria": fornecedor.agencia_bancaria or "",
            "conta_bancaria": fornecedor.conta_bancaria or "",
            "chave_pix": fornecedor.chave_pix or "",
        }

        if request.method == "POST":
            # -----------------------------------------------------------------
            tipoContribuicao = request.form.get("tipoContribuicao", "")
            declaracaoSenar = request.files.get("declaracaoSenar")
            tipo_cadastro = request.form.get("tipoCadastro", "")
            classeFornecedor = request.form.get("classeFornecedor")
            valorContrato = request.form.get("valorContrato")
            controleEntrada = request.form.get("controleEntrada")
            custoExtracao = request.form.get("custoExtracao", "")
            nome_completo = request.form.get("nomeCompleto", "").strip()
            razao_social = request.form.get("razaoSocial", "").strip()
            cpf = request.form.get("cpf", "").strip()
            cnpj = request.form.get("cnpj", "").strip()
            telefone = request.form.get("telefone", "").strip()

            eucaPrecoCusto1 = request.form.get("eucaPrecoCusto1", "0")
            eucaPrecoCusto2 = request.form.get("eucaPrecoCusto2", "0")
            eucaPrecoCusto3 = request.form.get("eucaPrecoCusto3", "0")
            eucaPrecoCusto4 = request.form.get("eucaPrecoCusto4", "0")

            pinusPrecoCusto1 = request.form.get("pinusPrecoCusto1", "0")
            pinusPrecoCusto2 = request.form.get("pinusPrecoCusto2", "0")
            pinusPrecoCusto3 = request.form.get("pinusPrecoCusto3", "0")
            pinusPrecoCusto4 = request.form.get("pinusPrecoCusto4", "0")
            pinusPrecoCusto5 = request.form.get("pinusPrecoCusto5", "0")

            bioPrecoCusto5 = request.form.get("bioPrecoCusto5", "0")
            bioPrecoCusto7 = request.form.get("bioPrecoCusto7", "0")

            extratorNome = request.form.get("extratorNome", "")
            credito_fornecedor = request.form.get("credito_fornecedor", "0")
            contratoFornecedor = request.files.get("contratoFornecedor")


            instituicao_financeira = request.form["instituicao_financeira"]
            agencia_bancaria = request.form["agencia_bancaria"]
            conta_bancaria = request.form["conta_bancaria"]
            chave_pix = request.form["chave_pix"]
            
            # Montar dicionário de campos obrigatórios
            campos = {
                "telefone": ["Telefone", telefone]
            }

            if classeFornecedor == "sim":
                campos["valorContrato"] = ["Valor do Contrato", valorContrato]

            if tipo_cadastro == "cpf":
                campos["nomeCompleto"] = ["Nome Completo", nome_completo]
                campos["cpf"] = ["CPF", cpf]
            else:  
                campos["razaoSocial"] = ["Razão Social", razao_social]
                campos["cnpj"] = ["CNPJ", cnpj]

            if tipoContribuicao == "senar" and declaracaoSenar.filename == '' and fornecedor.arquivo_senar_id == None:
                campos["declaracaoSenar"] = ["Declaração Senar", declaracaoSenar]

            # Se tiver custo de extração, adicionar extrator ao campos
            if custoExtracao == 'possui':
                campos["extratorNome"] = ["Extrator", extratorNome]

            # Flag de Madeira Posta
            madeira_posta = True if request.form.get("madeiraPosta") == "possui" else False
            # Flag de Possui Comissionado
            possui_comissionado = True if request.form.get("possuiComissionado") == "possui" else False

            # Se possuir madeira posta, validar ao menos um cliente selecionado
            if madeira_posta:
                lista_clientes_mp = request.form.getlist("clienteMadeiraPosta[]")
                if not lista_clientes_mp or all(not cid for cid in lista_clientes_mp):
                    campos["clienteMadeiraPosta"] = ["Cliente", ""]

                lista_transportadoras_mp = request.form.getlist("transportadoraMadeiraPosta[]")
                if not lista_transportadoras_mp or all(not cid for cid in lista_transportadoras_mp):
                    campos["transportadoraMadeiraPosta"] = ["Transportadora", ""]

            # Validação de campos obrigatórios
            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
            if "validado" not in validacao_campos_obrigatorios:
                gravar_banco = False
                flash(("Verifique os campos destacados em vermelho!", "warning"))

            # Validação de CPF / CNPJ e existência
            if tipo_cadastro == "cpf":
                verificacao_cpf = ValidaForms.validar_cpf(cpf)
                if "validado" not in verificacao_cpf:
                    gravar_banco = False
                    validacao_campos_erros.update(verificacao_cpf)

                cpf_tratado = ValidaDocs.remove_pontuacao_cpf(cpf)
                if fornecedor.numero_documento != cpf_tratado:
                    pesquisa_cpf_banco = FornecedorModel.query.filter_by(
                        numero_documento=cpf_tratado
                    ).first()
                    if pesquisa_cpf_banco:
                        gravar_banco = False
                        validacao_campos_erros["cpf"] = "O CPF informado já existe no banco de dados!"
            else:
                verificacao_cnpj = ValidaForms.validar_cnpj(cnpj)
                if "validado" not in verificacao_cnpj:
                    gravar_banco = False
                    validacao_campos_erros.update(verificacao_cnpj)

                cnpj_tratado = ValidaDocs.remove_pontuacao_cnpj(cnpj)
                if fornecedor.numero_documento != cnpj_tratado:
                    pesquisa_cnpj_banco = FornecedorModel.query.filter_by(
                        numero_documento=cnpj_tratado
                    ).first()
                    if pesquisa_cnpj_banco:
                        gravar_banco = False
                        validacao_campos_erros["cnpj"] = "O CNPJ informado já existe no banco de dados!"

            # -----------------------------------------------------------------
            # Se tudo validado, atualizar no banco
            if gravar_banco:
                telefone_tratado = Tels.remove_pontuacao_telefone_celular_br(telefone)

                euca_preco_custo_1_100 = int(ValoresMonetarios.converter_string_brl_para_float(eucaPrecoCusto1) * 100)
                euca_preco_custo_2_100 = int(ValoresMonetarios.converter_string_brl_para_float(eucaPrecoCusto2) * 100)
                euca_preco_custo_3_100 = int(ValoresMonetarios.converter_string_brl_para_float(eucaPrecoCusto3) * 100)
                euca_preco_custo_4_100 = int(ValoresMonetarios.converter_string_brl_para_float(eucaPrecoCusto4) * 100)

                pinus_preco_custo_1_100 = int(ValoresMonetarios.converter_string_brl_para_float(pinusPrecoCusto1) * 100)
                pinus_preco_custo_2_100 = int(ValoresMonetarios.converter_string_brl_para_float(pinusPrecoCusto2) * 100)
                pinus_preco_custo_3_100 = int(ValoresMonetarios.converter_string_brl_para_float(pinusPrecoCusto3) * 100)
                pinus_preco_custo_4_100 = int(ValoresMonetarios.converter_string_brl_para_float(pinusPrecoCusto4) * 100)
                pinus_preco_custo_5_100 = int(ValoresMonetarios.converter_string_brl_para_float(pinusPrecoCusto5) * 100)

                bio_preco_custo_5_100 = int(ValoresMonetarios.converter_string_brl_para_float(bioPrecoCusto5) * 100)
                bio_preco_custo_7_100 = int(ValoresMonetarios.converter_string_brl_para_float(bioPrecoCusto7) * 100)

                # Converter custos de extração inline
                if custoExtracao == 'possui':
                    euca_custo_extracao_1_100 = int(ValoresMonetarios.converter_string_brl_para_float(request.form.get("eucaCustoExtracao1", "0")) * 100)
                    euca_custo_extracao_2_100 = int(ValoresMonetarios.converter_string_brl_para_float(request.form.get("eucaCustoExtracao2", "0")) * 100)
                    euca_custo_extracao_3_100 = int(ValoresMonetarios.converter_string_brl_para_float(request.form.get("eucaCustoExtracao3", "0")) * 100)
                    euca_custo_extracao_4_100 = int(ValoresMonetarios.converter_string_brl_para_float(request.form.get("eucaCustoExtracao4", "0")) * 100)
                    pinus_custo_extracao_1_100 = int(ValoresMonetarios.converter_string_brl_para_float(request.form.get("pinusCustoExtracao1", "0")) * 100)
                    pinus_custo_extracao_2_100 = int(ValoresMonetarios.converter_string_brl_para_float(request.form.get("pinusCustoExtracao2", "0")) * 100)
                    pinus_custo_extracao_3_100 = int(ValoresMonetarios.converter_string_brl_para_float(request.form.get("pinusCustoExtracao3", "0")) * 100)
                    pinus_custo_extracao_4_100 = int(ValoresMonetarios.converter_string_brl_para_float(request.form.get("pinusCustoExtracao4", "0")) * 100)
                    pinus_custo_extracao_5_100 = int(ValoresMonetarios.converter_string_brl_para_float(request.form.get("pinusCustoExtracao5", "0")) * 100)
                    bio_custo_extracao_5_100 = int(ValoresMonetarios.converter_string_brl_para_float(request.form.get("bioCustoExtracao5", "0")) * 100)
                    bio_custo_extracao_7_100 = int(ValoresMonetarios.converter_string_brl_para_float(request.form.get("bioCustoExtracao7", "0")) * 100)
                else:
                    euca_custo_extracao_1_100 = euca_custo_extracao_2_100 = None
                    euca_custo_extracao_3_100 = euca_custo_extracao_4_100 = None
                    pinus_custo_extracao_1_100 = pinus_custo_extracao_2_100 = None
                    pinus_custo_extracao_3_100 = pinus_custo_extracao_4_100 = None
                    pinus_custo_extracao_5_100 = None
                    bio_custo_extracao_5_100 = None
                    bio_custo_extracao_7_100 = None

                credito_fornecedor_ton_100 = int(ValoresMonetarios.converter_string_brl_para_float(credito_fornecedor) * 100)

                # Ajustar fatura_via_cpf e número do documento
                fatura_via_cpf = True if request.form["tipoCadastro"] == "cpf" else False
                
                if classeFornecedor == "sim":
                    valor_contrato = int(ValoresMonetarios.converter_string_brl_para_float(valorContrato) * 100)
                    print(valor_contrato)

                if request.form["tipoCadastro"] == "cpf":
                    identificacao = nome_completo
                    numero_documento = cpf_tratado
                else:  
                    identificacao = razao_social
                    numero_documento = cnpj_tratado

                # Comparar objeto original (obj1) e novo (obj2) para pontuação
                obj1 = {
                    "tipoContribuicao": "funrural" if fornecedor.funrural == 1 else "senar",
                    "classeFornecedor": "sim" if fornecedor.classe_fornecedor == 1 else "nao",
                    "controleEntrada": "sim" if fornecedor.controle_entrada == 1 else "nao",
                    "valorContrato": fornecedor.valor_contrato_100 if fornecedor.classe_fornecedor == 1 else 0,
                    "tipoCadastro": "cpf" if fornecedor.fatura_via_cpf == 1 else "cnpj",
                    "custoExtracao": "possui" if fornecedor.custo_extracao == 1 else "nao_possui",
                    "razaoSocial": (fornecedor.identificacao if fornecedor.fatura_via_cpf == 0 else ""),
                    "nomeCompleto": (fornecedor.identificacao if fornecedor.fatura_via_cpf == 1 else ""),
                    "cpf": (fornecedor.numero_documento if fornecedor.fatura_via_cpf == 1 else ""),
                    "cnpj": (fornecedor.numero_documento if fornecedor.fatura_via_cpf == 0 else ""),
                    "telefone": fornecedor.telefone or "",
                    "credito_fornecedor": fornecedor.credito_100 or 0,
                    "eucaPrecoCusto1": fornecedor.euca_preco_custo_bitola_1_100 or 0,
                    "eucaPrecoCusto2": fornecedor.euca_preco_custo_bitola_2_100 or 0,
                    "eucaPrecoCusto3": fornecedor.euca_preco_custo_bitola_3_100 or 0,
                    "eucaPrecoCusto4": fornecedor.euca_preco_custo_bitola_4_100 or 0,
                    "bioPrecoCusto5": fornecedor.bio_preco_custo_bitola_5_100 or 0,
                    "pinusPrecoCusto1": fornecedor.pinus_preco_custo_bitola_1_100 or 0,
                    "pinusPrecoCusto2": fornecedor.pinus_preco_custo_bitola_2_100 or 0,
                    "pinusPrecoCusto3": fornecedor.pinus_preco_custo_bitola_3_100 or 0,
                    "pinusPrecoCusto4": fornecedor.pinus_preco_custo_bitola_4_100 or 0,
                    "pinusPrecoCusto5": fornecedor.pinus_preco_custo_bitola_5_100 or 0,
                    "eucaCustoExtracao1": fornecedor.euca_custo_extracao_bitola_1_100 or 0,
                    "eucaCustoExtracao2": fornecedor.euca_custo_extracao_bitola_2_100 or 0,
                    "eucaCustoExtracao3": fornecedor.euca_custo_extracao_bitola_3_100 or 0,
                    "eucaCustoExtracao4": fornecedor.euca_custo_extracao_bitola_4_100 or 0,
                    "pinusCustoExtracao1": fornecedor.pinus_custo_extracao_bitola_1_100 or 0,
                    "pinusCustoExtracao2": fornecedor.pinus_custo_extracao_bitola_2_100 or 0,
                    "pinusCustoExtracao3": fornecedor.pinus_custo_extracao_bitola_3_100 or 0,
                    "pinusCustoExtracao4": fornecedor.pinus_custo_extracao_bitola_4_100 or 0,
                    "pinusCustoExtracao5": fornecedor.pinus_custo_extracao_bitola_5_100 or 0,
                    "madeiraPosta": "possui" if fornecedor.madeira_posta else "nao_possui",
                    "instituicaoFinanceira": fornecedor.instituicao_financeira_id or "",
                    "agenciaBancaria": fornecedor.agencia_bancaria or "",
                    "contaBancaria": fornecedor.conta_bancaria or "",
                    "chavePix": fornecedor.chave_pix or "",
                }

                obj2 = {
                    "tipoContribuicao": "funrural" if tipoContribuicao == 1 else "senar",
                    "classeFornecedor": "sim" if classeFornecedor == "sim" else "nao",
                    "controleEntrada": "sim" if controleEntrada == "sim" else "nao",
                    "valorContrato": valor_contrato if classeFornecedor == "sim" else 0,
                    "tipoCadastro": "cpf" if tipo_cadastro == 1 else "cnpj",
                    "custoExtracao": "possui" if custoExtracao == 'possui' else "nao_possui",
                    "razaoSocial": razao_social if tipo_cadastro == 0 else "",
                    "nomeCompleto": nome_completo if tipo_cadastro == 1 else "",
                    "cpf": cpf_tratado if tipo_cadastro == 1 else "",
                    "cnpj": cnpj_tratado if tipo_cadastro == 0 else "",
                    "telefone": telefone_tratado,
                    "credito_fornecedor": credito_fornecedor_ton_100,
                    "eucaPrecoCusto1": euca_preco_custo_1_100,
                    "eucaPrecoCusto2": euca_preco_custo_2_100,
                    "eucaPrecoCusto3": euca_preco_custo_3_100,
                    "eucaPrecoCusto4": euca_preco_custo_4_100,
                    "pinusPrecoCusto1": pinus_preco_custo_1_100,
                    "pinusPrecoCusto2": pinus_preco_custo_2_100,
                    "pinusPrecoCusto3": pinus_preco_custo_3_100,
                    "pinusPrecoCusto4": pinus_preco_custo_4_100,
                    "pinusPrecoCusto5": pinus_preco_custo_5_100,
                    "bioPrecoCusto5": bio_preco_custo_5_100,
                    "bioPrecoCusto7": bio_preco_custo_7_100,
                    "eucaCustoExtracao1": euca_custo_extracao_1_100 if custoExtracao == 'possui' else None,
                    "eucaCustoExtracao2": euca_custo_extracao_2_100 if custoExtracao == 'possui' else None,
                    "eucaCustoExtracao3": euca_custo_extracao_3_100 if custoExtracao == 'possui' else None,
                    "eucaCustoExtracao4": euca_custo_extracao_4_100 if custoExtracao == 'possui' else None,
                    "pinusCustoExtracao1": pinus_custo_extracao_1_100 if custoExtracao == 'possui' else None,
                    "pinusCustoExtracao2": pinus_custo_extracao_2_100 if custoExtracao == 'possui' else None,
                    "pinusCustoExtracao3": pinus_custo_extracao_3_100 if custoExtracao == 'possui' else None,
                    "pinusCustoExtracao4": pinus_custo_extracao_4_100 if custoExtracao == 'possui' else None,
                    "pinusCustoExtracao5": pinus_custo_extracao_5_100 if custoExtracao == 'possui' else None,
                    "madeiraPosta": "possui" if madeira_posta else "nao_possui",
                    "instituicaoFinanceira": int(instituicao_financeira) if instituicao_financeira else "",
                    "agenciaBancaria": agencia_bancaria,
                    "contaBancaria": conta_bancaria,
                    "chavePix": chave_pix,
                }

                diferencas = Gameficacao.compara_objetos(obj1, obj2)
                if diferencas:
                    acao = TipoAcaoEnum.EDICAO
                    PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                        current_user.id, acao, acao.pontos, modulo="fornecedor"
                    )

                fornecedor.madeira_posta = madeira_posta
                # Flag de possui comissionado
                fornecedor.possui_comissionado = possui_comissionado

                if fornecedor.senar and tipoContribuicao == 'funrural':
                    arquivo = UploadArquivoModel.obter_arquivo_por_id(fornecedor.arquivo_senar_id)
                    fornecedor.arquivo_senar_id = None
                    arquivo.deletado = True


                fornecedor.funrural = 1 if tipoContribuicao == 'funrural' else 0
                fornecedor.senar = 1 if tipoContribuicao == 'senar' else 0
                fornecedor.imposto_id = 1 if tipoContribuicao == 'funrural' else 2
                
                fornecedor.classe_fornecedor = 1 if classeFornecedor == "sim" else 0
                
                if classeFornecedor == "sim":
                    fornecedor.valor_contrato_100 = valor_contrato
                else:
                    fornecedor.valor_contrato_100 = None

                fornecedor.controle_entrada = 1 if controleEntrada == "sim" else 0
                
                # Atualizar fornecedor
                fornecedor.fatura_via_cpf = fatura_via_cpf
                fornecedor.identificacao = identificacao
                fornecedor.numero_documento = numero_documento
                fornecedor.telefone = telefone_tratado

                # Atualizar preços Eucalipto
                fornecedor.euca_bitola_1_id = 1
                fornecedor.euca_bitola_2_id = 2
                fornecedor.euca_bitola_3_id = 3
                fornecedor.euca_bitola_4_id = 4
                fornecedor.euca_preco_custo_bitola_1_100 = euca_preco_custo_1_100
                fornecedor.euca_preco_custo_bitola_2_100 = euca_preco_custo_2_100
                fornecedor.euca_preco_custo_bitola_3_100 = euca_preco_custo_3_100
                fornecedor.euca_preco_custo_bitola_4_100 = euca_preco_custo_4_100
                fornecedor.bio_preco_custo_bitola_5_100 = bio_preco_custo_5_100
                fornecedor.bio_preco_custo_bitola_7_100 = bio_preco_custo_7_100

                # Atualizar custo de extração
                fornecedor.custo_extracao = 1 if custoExtracao == 'possui' else 0
                fornecedor.extrator_id = extratorNome if custoExtracao == 'possui' else None
                fornecedor.euca_custo_extracao_bitola_1_100 = euca_custo_extracao_1_100 or 0
                fornecedor.euca_custo_extracao_bitola_2_100 = euca_custo_extracao_2_100 or 0
                fornecedor.euca_custo_extracao_bitola_3_100 = euca_custo_extracao_3_100 or 0
                fornecedor.euca_custo_extracao_bitola_4_100 = euca_custo_extracao_4_100 or 0
                fornecedor.pinus_custo_extracao_bitola_1_100 = pinus_custo_extracao_1_100 or 0
                fornecedor.pinus_custo_extracao_bitola_2_100 = pinus_custo_extracao_2_100 or 0
                fornecedor.pinus_custo_extracao_bitola_3_100 = pinus_custo_extracao_3_100 or 0
                fornecedor.pinus_custo_extracao_bitola_4_100 = pinus_custo_extracao_4_100 or 0
                fornecedor.bio_custo_extracao_bitola_5_100 = bio_custo_extracao_5_100 or 0
                fornecedor.bio_custo_extracao_bitola_7_100 = bio_custo_extracao_7_100 or 0

                # Atualizar preços Pinus
                fornecedor.pinus_bitola_1_id = 1
                fornecedor.pinus_bitola_2_id = 2
                fornecedor.pinus_bitola_3_id = 3
                fornecedor.pinus_bitola_4_id = 4
                fornecedor.pinus_bitola_5_id = 6
                fornecedor.pinus_preco_custo_bitola_1_100 = pinus_preco_custo_1_100
                fornecedor.pinus_preco_custo_bitola_2_100 = pinus_preco_custo_2_100
                fornecedor.pinus_preco_custo_bitola_3_100 = pinus_preco_custo_3_100
                fornecedor.pinus_preco_custo_bitola_4_100 = pinus_preco_custo_4_100
                fornecedor.pinus_preco_custo_bitola_5_100 = pinus_preco_custo_5_100

                # Dados bancários
                fornecedor.instituicao_financeira_id = int(instituicao_financeira) if instituicao_financeira else None
                fornecedor.agencia_bancaria = agencia_bancaria or None
                fornecedor.conta_bancaria = conta_bancaria or None
                fornecedor.chave_pix = chave_pix or None

                fornecedor.credito_100 = credito_fornecedor_ton_100
                fornecedor.ativo = True

                # Se a contribuição for senar e tiver dados
                if tipoContribuicao == "senar" and declaracaoSenar and declaracaoSenar.filename:
                    if declaracaoSenar.mimetype in ["application/pdf", "image/jpeg", "image/png"]:
                        declaracao_upload = upload_arquivo(
                            declaracaoSenar,
                            "UPLOAD_DECLARACAO_SENAR",
                            f"{fornecedor.id}",
                        )
                        fornecedor.arquivo_senar_id = declaracao_upload.id
                        db.session.flush()
                    else:
                        flash(("A declaração senar deve estar em formato PDF ou JPG ou JPGE ou PNG.", "warning"))
                        return redirect(url_for("editar_fornecedor", id=fornecedor.id))

                # Atualizar contrato se houver
                if contratoFornecedor and contratoFornecedor.filename:
                    if contratoFornecedor.mimetype == "application/pdf":
                        contrato_upload = upload_arquivo(
                            contratoFornecedor,
                            "UPLOAD_CONTRATO_FORNECEDOR",
                            f"{fornecedor.id}",
                        )
                        fornecedor.contrato_fornecedor_id = contrato_upload.id
                        db.session.flush()
                    else:
                        flash(("O contrato do fornecedor deve estar em formato PDF.", "warning"))
                        return redirect(url_for("editar_fornecedor", id=fornecedor.id))

                # “Desativa” todas as entradas de madeira posta vinculadas a este fornecedor
                FornecedorMadeiraPostaModel.query.filter_by(fornecedor_id=fornecedor.id, ativo=True).update(
                        {"ativo": False}
                )
                db.session.flush()

                if not madeira_posta:
                    FornecedorMadeiraPostaModel.query.filter_by(
                        fornecedor_id=fornecedor.id,
                        ativo=True
                    ).update({"ativo": False}, synchronize_session=False)
                    db.session.flush()

                else:
                    cliente_ids_list = request.form.getlist("clienteMadeiraPosta[]")
                    transportadora_ids_list = request.form.getlist("transportadoraMadeiraPosta[]")
                    euca1_list = request.form.getlist("eucaMadeiraPosta1[]")
                    euca2_list = request.form.getlist("eucaMadeiraPosta2[]")
                    euca3_list = request.form.getlist("eucaMadeiraPosta3[]")
                    euca4_list = request.form.getlist("eucaMadeiraPosta4[]")
                    pinus1_list = request.form.getlist("pinusMadeiraPosta1[]")
                    pinus2_list = request.form.getlist("pinusMadeiraPosta2[]")
                    pinus3_list = request.form.getlist("pinusMadeiraPosta3[]")
                    pinus4_list = request.form.getlist("pinusMadeiraPosta4[]")
                    pinus5_list = request.form.getlist("pinusMadeiraPosta5[]")
                    bio5_list = request.form.getlist("bioMadeiraPosta5[]")
                    bio7_list = request.form.getlist("bioMadeiraPosta7[]")

                    for idx, cid_str in enumerate(cliente_ids_list):
                        try:
                            cid = int(cid_str)
                        except ValueError:
                            continue
                        
                        # Obter transportadora correspondente (mesmo índice)
                        tid = None
                        if idx < len(transportadora_ids_list):
                            try:
                                tid = int(transportadora_ids_list[idx]) if transportadora_ids_list[idx] else None
                            except (ValueError, IndexError):
                                tid = None

                        e1 = int(ValoresMonetarios.converter_string_brl_para_float(euca1_list[idx]) * 100)
                        e2 = int(ValoresMonetarios.converter_string_brl_para_float(euca2_list[idx]) * 100)
                        e3 = int(ValoresMonetarios.converter_string_brl_para_float(euca3_list[idx]) * 100)
                        e4 = int(ValoresMonetarios.converter_string_brl_para_float(euca4_list[idx]) * 100)

                        p1 = int(ValoresMonetarios.converter_string_brl_para_float(pinus1_list[idx]) * 100)
                        p2 = int(ValoresMonetarios.converter_string_brl_para_float(pinus2_list[idx]) * 100)
                        p3 = int(ValoresMonetarios.converter_string_brl_para_float(pinus3_list[idx]) * 100)
                        p4 = int(ValoresMonetarios.converter_string_brl_para_float(pinus4_list[idx]) * 100)
                        p5 = int(ValoresMonetarios.converter_string_brl_para_float(pinus5_list[idx]) * 100)
                        b5 = int(ValoresMonetarios.converter_string_brl_para_float(bio5_list[idx]) * 100)
                        b7 = int(ValoresMonetarios.converter_string_brl_para_float(bio7_list[idx]) * 100)

                        mp = FornecedorMadeiraPostaModel(
                            fornecedor_id=fornecedor.id,
                            cliente_id=cid,
                            transportadora_id=tid,
                            euca_bitola_1_id=1,
                            euca_bitola_2_id=2,
                            euca_bitola_3_id=3,
                            euca_bitola_4_id=4,
                            pinus_bitola_1_id=1,
                            pinus_bitola_2_id=2,
                            pinus_bitola_3_id=3,
                            pinus_bitola_4_id=4,
                            pinus_bitola_5_id=6, 
                            bio_bitola_5_id=5,
                            bio_bitola_7_id=7,
                            euca_bitola_1_preco_100=e1,
                            euca_bitola_2_preco_100=e2,
                            euca_bitola_3_preco_100=e3,
                            euca_bitola_4_preco_100=e4,
                            pinus_bitola_1_preco_100=p1,
                            pinus_bitola_2_preco_100=p2,
                            pinus_bitola_3_preco_100=p3,
                            pinus_bitola_4_preco_100=p4,
                            pinus_bitola_5_preco_100=p5,
                            bio_bitola_5_preco_100=b5,
                            bio_bitola_7_preco_100=b7,
                        )
                        db.session.add(mp)

                # Processar comissionados vinculados ao fornecedor (edição)
                # Primeiro, remover comissionados existentes
                FornecedorComissionadoModel.query.filter_by(fornecedor_id=fornecedor.id, ativo=True).update(
                    {"ativo": False, "deletado": True}
                )
                db.session.flush()

                # Processar novos comissionados (apenas se possui_comissionado = True)
                if possui_comissionado:
                    comissionados_list = request.form.getlist("comissionados[]")
                    valores_comissao_list = request.form.getlist("valorComissaoTon[]")

                    # Criar novos registros de FornecedorComissionadoModel
                    for idx, comissionado_id in enumerate(comissionados_list):
                        if comissionado_id and comissionado_id.strip():
                            valor_comissao_str = valores_comissao_list[idx] if idx < len(valores_comissao_list) else '0'
                            valor_comissao_100 = int(ValoresMonetarios.converter_string_brl_para_float(valor_comissao_str) * 100)
                            
                            fornecedor_comissionado = FornecedorComissionadoModel(
                                fornecedor_id=fornecedor.id,
                                comissionado_id=int(comissionado_id),
                                valor_comissao_ton_100=valor_comissao_100
                            )
                            db.session.add(fornecedor_comissionado)

                db.session.commit()
                flash(("Fornecedor editado com sucesso!", "success"))
                return redirect(url_for("listar_fornecedores"))
    except Exception as e:
        print(f'Erro ao tentar editar fornecedor: {e}')
        flash(('Houve um erro ao tentar editar fornecedor! Entre em contato com o suporte.', 'warning'))
        return redirect(url_for('editar_fornecedor', id=id))

    return render_template(
        "gerenciar/fornecedores/fornecedor_editar.html",
        fornecedor=fornecedor,
        bancos=bancos,
        clientes=clientes,
        transportadoras=transportadoras,
        extratores=extratores,
        comissionados=comissionados,
        fornecedor_comissionados=fornecedor_comissionados,
        madeiras_existentes=madeiras_existentes,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=dados_corretos,
    )


@app.route("/gerenciar/desativar/fornecedor/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def desativar_fornecedor(id):
    fornecedor = FornecedorModel.obter_fornecedor_por_id(id)
    if fornecedor is None:
        flash(("Fornecedor não encontrado!", "warning"))

    fornecedor.ativo = 0
    db.session.commit()
    flash(("Fornecedor desativado com sucesso!", "success"))
    return redirect(url_for("listar_fornecedores"))


@app.route("/gerenciar/ativar/fornecedor/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def ativar_fornecedor(id):
    fornecedor = FornecedorModel.obter_fornecedor_por_id(id)
    if fornecedor is None:
        flash(("Fornecedor não encontrado!", "warning"))

    fornecedor.ativo = 1
    db.session.commit()
    flash(("Fornecedor ativado com sucesso!", "success"))
    return redirect(url_for("listar_fornecedores"))


@app.route("/sincronizar/precos/fornecedores", methods=["GET", "POST"])
@login_required
@requires_roles
def atualizar_precos_fornecedor_floresta():
    try:
        from servidor_huey.tarefas import sincronizar_precos_fornecedores
        from datetime import datetime
        
        if request.method == 'POST':
            data_inicio = request.form.get('data_inicio')
            data_fim = request.form.get('data_fim')
            fornecedor_id = request.form.get('fornecedor_id')
            
            if not data_inicio or not data_fim:
                flash(("Por favor, informe o período para atualização dos valores!", "warning"))
                return redirect(url_for("listagem_fornecedores_a_pagar"))
            
            try:
                # Validar formato das datas
                data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
                
                if data_inicio_obj > data_fim_obj:
                    flash(("A data de início não pode ser maior que a data fim!", "warning"))
                    return redirect(url_for("listagem_fornecedores_a_pagar"))
                
            except ValueError:
                flash(("Formato de data inválido!", "warning"))
                return redirect(url_for("listagem_fornecedores_a_pagar"))
        else:
            return redirect(url_for("listagem_fornecedores_a_pagar"))
        
        # Converter fornecedor_id para None se for "todos"
        fornecedor_filtro = None if fornecedor_id == "todos" else fornecedor_id

        print(fornecedor_filtro)
        
        task = sincronizar_precos_fornecedores(data_inicio, data_fim, fornecedor_filtro)
        
        try:
            resultado = task(blocking=True, timeout=120)  
            if resultado['sucesso']:
                if resultado['sincronizados'] > 0:
                    flash((f"{resultado['sincronizados']} valores sincronizados com sucesso!", "success"))
                else:
                    flash((f"Todos os fornecedores do período informado já estão sincronizados", "warning"))
            else:
                flash(("Não foi possível atualizar os registros no período informado", "warning"))
                
        except Exception as e:
            flash((f"Processo de atualização iniciado para o período. Pode levar alguns minutos para concluir.", "warning"))
            
        return redirect(url_for("listagem_fornecedores_a_pagar"))
        
    except Exception as e:
        flash(("Não foi possível iniciar a sincronização", "warning"))
        return redirect(url_for("listagem_fornecedores_a_pagar"))
