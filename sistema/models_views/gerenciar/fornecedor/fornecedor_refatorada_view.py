from sistema import app, requires_roles, db, current_user
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from sistema.models_views.gerenciar.fornecedor.fornecedor_cadastro_model import FornecedorCadastroModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_preco_custo_bitola_model import FornecedorPrecoCustoBitolaModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_preco_custo_extracao_model import FornecedorPrecoCustoExtracaoModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_madeira_posta_preco_bitola_model import FornecedorMadeiraPostaPrecoBitolaModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_conta_bancaria_model import FornecedorContaBancariaModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_credito_model import FornecedorCreditoModel
from sistema.models_views.parametros.produto_bitola.produto_bitola_model import ProdutoBitolaModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_comissionado_model import FornecedorComissionadoModel
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.gerenciar.extrator.extrator_model import ExtratorModel
from sistema.models_views.gerenciar.comissionado.comissionado_model import ComissionadoModel
from sistema.models_views.parametros.instituicoes_financeiras.instituicao_financeira_model import InstituicoesFinanceirasModel
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema.models_views.configuracoes_gerais.tag.tag_model import TagModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_tag_model import FornecedorTag
from sistema.models_views.gerenciar.pessoa_financeiro.pessoa_financeiro_model import PessoaFinanceiroModel
import json
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
        
        fornecedores = FornecedorCadastroModel.filtrar_fornecedores(
            identificacao=request.args.get("identificacao"),
            numero_documento=numeroDocFormatado,
            celular=celularFormatado,
        )
    else:
        fornecedores = FornecedorCadastroModel.listar_fornecedores()
        
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
        tags = TagModel.obter_tags_ativas()
        
        produtos_bitolas = ProdutoBitolaModel.obter_produtos_com_bitolas()

        if request.method == "POST":

            tipoContribuicao = request.form.get("tipoContribuicao", "")
            declaracaoSenar = request.files.get("declaracaoSenar")
            classeFornecedor = request.form.get("classeFornecedor")
            controleEntrada = request.form.get("controleEntrada")
            valorContrato = request.form.get("valorContrato")
            estimativaTonelada = request.form.get("estimativaTonelada", "")
            tipo_cadastro = request.form.get("tipoCadastro", "")
            custoExtracao = request.form.get("custoExtracao", "")
            nome_completo = request.form.get("nomeCompleto", "").strip()
            razao_social = request.form.get("razaoSocial", "").strip()
            cpf = request.form.get("cpf", "").strip()
            cnpj = request.form.get("cnpj", "").strip()
            telefone = request.form.get("telefone", "").strip()
            
            tags_fornecedor = request.form.getlist("tags_fornecedor")

            instituicao_financeira = request.form["instituicao_financeira"]
            agencia_bancaria = request.form["agencia_bancaria"]
            conta_bancaria = request.form["conta_bancaria"]
            chave_pix = request.form["chave_pix"]

            precos_custo_dados = {}
            produtos_bitolas = ProdutoBitolaModel.obter_produtos_com_bitolas()
            
            for produto_id, produto_data in produtos_bitolas.items():
                produto_name = produto_data['nome']
                bitolas = produto_data['bitolas']
                
                if produto_name.lower() == 'eucalipto':
                    produto_key = 'euca'
                elif produto_name.lower() == 'pinus':
                    produto_key = 'pinus'
                elif produto_name.lower() == 'biomassa':
                    produto_key = 'bio'
                else:
                    produto_key = produto_name.lower()[:5]
                    
                for idx, bitola in enumerate(bitolas, 1):
                    campo_nome = f"{produto_key}PrecoCusto{idx}"
                    valor = request.form.get(campo_nome, "0")
                    precos_custo_dados[campo_nome] = {
                        'valor': valor,
                        'produto_id': produto_id,
                        'bitola_id': bitola['id']
                    }

            credito_fornecedor = request.form.get("credito_fornecedor", "0")
            contratoFornecedor = request.files.get("contratoFornecedor")


            criar_pessoa_financeiro = request.form.get("criarPessoaFinanceiro", "nao")

            campos = {
                "telefone": ["Telefone", telefone]
            }
            
            if classeFornecedor == "sim":
                campos["valorContrato"] = ["Valor do Contrato", valorContrato]
                campos["estimativaTonelada"] = ["Estimativa Tonelada", estimativaTonelada]

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
                campos["extratorNome"] = ["Extrator", extratorNome]

                custos_extracao_dados = {}
                produtos_bitolas = ProdutoBitolaModel.obter_produtos_com_bitolas()
                
                for produto_id, produto_data in produtos_bitolas.items():
                    produto_name = produto_data['nome']
                    bitolas = produto_data['bitolas']
                    
                    if produto_name.lower() == 'eucalipto':
                        produto_key = 'euca'
                    elif produto_name.lower() == 'pinus':
                        produto_key = 'pinus'
                    elif produto_name.lower() == 'biomassa':
                        produto_key = 'bio'
                    else:
                        produto_key = produto_name.lower()[:5]
                        
                    for idx, bitola in enumerate(bitolas, 1):
                        campo_nome = f"{produto_key}CustoExtracao{idx}"
                        valor = request.form.get(campo_nome, "0")
                        custos_extracao_dados[campo_nome] = valor

            madeira_posta = True if request.form.get("madeiraPosta") == "possui" else False
            possui_comissionado = True if request.form.get("possuiComissionado") == "possui" else False

            if madeira_posta:
                lista_clientes_mp = request.form.getlist("clienteMadeiraPosta[]")
                if not lista_clientes_mp or all(not cid for cid in lista_clientes_mp):
                    campos["clienteMadeiraPosta"] = ["Cliente", ""]

            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
            if "validado" not in validacao_campos_obrigatorios:
                gravar_banco = False
                flash(("Verifique os campos destacados em vermelho!", "warning"))
            

            if tipo_cadastro == "cpf":
                verificacao_cpf = ValidaForms.validar_cpf(cpf)
                if "validado" not in verificacao_cpf:
                    gravar_banco = False
                    validacao_campos_erros.update(verificacao_cpf)

                cpf_tratado = ValidaDocs.remove_pontuacao_cpf(cpf)
                pesquisa_cpf_banco = FornecedorCadastroModel.query.filter_by(
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
                pesquisa_cnpj_banco = FornecedorCadastroModel.query.filter_by(
                    numero_documento=cnpj_tratado
                ).first()
                if pesquisa_cnpj_banco:
                    gravar_banco = False
                    validacao_campos_erros["cnpj"] = "O CNPJ informado já existe no banco de dados!"

            if gravar_banco:
                telefone_tratado = Tels.remove_pontuacao_telefone_celular_br(telefone)

                precos_custo_convertidos = {}
                for campo_nome, dados in precos_custo_dados.items():
                    valor_convertido = int(ValoresMonetarios.converter_string_brl_para_float(dados['valor']) * 100)
                    precos_custo_convertidos[campo_nome] = {
                        'valor_100': valor_convertido,
                        'produto_id': dados['produto_id'],
                        'bitola_id': dados['bitola_id']
                    }
                

                custos_extracao_convertidos = {}
                if custoExtracao == 'possui':
                    for campo_nome, valor in custos_extracao_dados.items():
                        custo_convertido = int(ValoresMonetarios.converter_string_brl_para_float(valor) * 100)
                        custos_extracao_convertidos[campo_nome] = custo_convertido

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

                fornecedor = FornecedorCadastroModel(
                    fatura_via_cpf=fatura_via_cpf,
                    identificacao=identificacao,
                    numero_documento=numero_documento,
                    telefone=telefone_tratado,
                    funrural=True if tipoContribuicao == 'funrural' else False,
                    senar=True if tipoContribuicao == 'senar' else False,
                    imposto_id=1 if tipoContribuicao == 'funrural' else 2,
                    classe_fornecedor=True if classeFornecedor == "sim" else False,
                    valor_contrato_100=valor_contrato if classeFornecedor == "sim" else None,
                    estimativa_tonelada=float(estimativaTonelada) if classeFornecedor == "sim" and estimativaTonelada else None,
                    controle_entrada=True if controleEntrada == "sim" else False,
                    madeira_posta=madeira_posta,
                    possui_comissionado=possui_comissionado,
                    custo_extracao=True if custoExtracao == 'possui' else False,
                    ativo=True
                )
                
                db.session.add(fornecedor)
                db.session.flush()
                
                for campo_nome, dados in precos_custo_convertidos.items():
                    FornecedorPrecoCustoBitolaModel.atualizar_ou_criar_preco_custo(
                        fornecedor.id, dados['produto_id'], dados['bitola_id'], dados['valor_100'])
                
                if custoExtracao == 'possui':
                    produtos_bitolas = ProdutoBitolaModel.obter_produtos_com_bitolas()
                    
                    for produto_id, produto_data in produtos_bitolas.items():
                        produto_name = produto_data['nome']
                        bitolas = produto_data['bitolas']
                        
                        if produto_name.lower() == 'eucalipto':
                            produto_key = 'euca'
                        elif produto_name.lower() == 'pinus':
                            produto_key = 'pinus'
                        elif produto_name.lower() == 'biomassa':
                            produto_key = 'bio'
                        else:
                            produto_key = produto_name.lower()[:5]
                            
                        for idx, bitola in enumerate(bitolas, 1):
                            campo_nome = f"{produto_key}CustoExtracao{idx}"
                            custo_convertido = custos_extracao_convertidos.get(campo_nome, 0)
                            
                            FornecedorPrecoCustoExtracaoModel.atualizar_ou_criar_custo_extracao(
                                fornecedor.id, produto_id, bitola['id'], custo_convertido, int(extratorNome))
                
                if instituicao_financeira or agencia_bancaria or conta_bancaria or chave_pix:
                    conta_bancaria_obj = FornecedorContaBancariaModel(
                        fornecedor_id=fornecedor.id,
                        instituicao_financeira_id=int(instituicao_financeira) if instituicao_financeira else None,
                        agencia_bancaria=agencia_bancaria if agencia_bancaria else None,
                        conta_bancaria=conta_bancaria if conta_bancaria else None,
                        chave_pix=chave_pix if chave_pix else None
                    )
                    db.session.add(conta_bancaria_obj)
                
                if credito_fornecedor_ton_100 and credito_fornecedor_ton_100 > 0:
                    FornecedorCreditoModel.atualizar_ou_criar_credito(
                        fornecedor.id, credito_fornecedor_ton_100
                    )  

                if criar_pessoa_financeiro == "sim":
                    try:
                        vinculos_operacionais = {
                            "fornecedor" : [{
                                "id": str(fornecedor.id),
                                "identificacao": fornecedor.identificacao
                            }]
                        }

                        if custoExtracao == 'possui' and extratorNome:
                            extrator = ExtratorModel.obter_extrator_por_id(int(extratorNome))
                            if extrator:
                                vinculos_operacionais["extrator"] = [{
                                    "id": str(extrator.id),
                                    "identificacao": extrator.identificacao
                                }]

                        if madeira_posta:
                            transportadora_ids_list = request.form.getlist("transportadoraMadeiraPosta[]")  
                            transportadoras_unicas = list(set([int(tid) for tid in transportadora_ids_list if tid]))
                            if transportadoras_unicas:
                                vinculos_operacionais["transportadora"] = []
                                for tid in transportadoras_unicas:
                                    transportadora = TransportadoraModel.obter_transportadora_por_id(tid)
                                    if transportadora:
                                        vinculos_operacionais["transportadora"].append({
                                            "id": str(transportadora.id),
                                            "identificacao": transportadora.identificacao
                                        })
                        
                        if possui_comissionado:
                            comissionados_list = request.form.getlist("comissionados[]")
                            comissionados_ids = [int(cid) for cid in comissionados_list if cid and cid.strip()]
                            if comissionados_ids:
                                vinculos_operacionais["comissionado"] = []
                                for cid in comissionados_ids:
                                    comissionado = ComissionadoModel.obter_comissionado_por_id(cid)
                                    if comissionado:
                                        vinculos_operacionais["comissionado"].append({
                                            "id": str(comissionado.id),
                                            "identificacao": comissionado.identificacao
                                        })
                        
                        vinculos_json = json.dumps(vinculos_operacionais)

                        tem_fornecedor, tem_transportadora, tem_extrator, tem_comissionado, vinculos_data = \
                        PessoaFinanceiroModel.processar_vinculos(vinculos_json)

                        pessoa_financeira = PessoaFinanceiroModel(
                            tipo_cadastro=fatura_via_cpf,
                            identificacao=identificacao,
                            numero_documento=numero_documento,
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

                        flash(("Cadastro realizado com sucesso: Fornecedor e Pessoa Financeira foram criados e já estão disponíveis para uso.", "success"))

                    except Exception as e:
                        db.session.rollback()
                        flash((f"O fornecedor foi cadastrado, mas a criação da Pessoa Financeira não pôde ser finalizada. Detalhe: {str(e)}", "warning"))
                        return redirect(url_for("listar_fornecedores"))
                else:
                    flash(("Fornecedor cadastrado com sucesso e todas as informações financeiras foram registradas corretamente.", "success"))


                if tags_fornecedor:
                    tags_fornecedor_ids = [int(tag_id) for tag_id in tags_fornecedor]
                    
                    for tag_id in tags_fornecedor_ids:
                        fornecedor_tag = FornecedorTag(
                            fornecedor_id=fornecedor.id,
                            tag_id=tag_id,
                            ativo=True
                        )
                        db.session.add(fornecedor_tag)
                        db.session.flush()

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
                        return redirect(url_for("cadastrar_fornecedor"))

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

                if madeira_posta:
                    cliente_ids_list = request.form.getlist("clienteMadeiraPosta[]")
                    transportadora_ids_list = request.form.getlist("transportadoraMadeiraPosta[]")
                    
                    madeira_posta_dinamica = {}
                    produtos_bitolas_cadastro = ProdutoBitolaModel.obter_produtos_com_bitolas()
                    
                    for produto_id, produto_data in produtos_bitolas_cadastro.items():
                        produto_name = produto_data['nome']
                        bitolas = produto_data['bitolas']
                        produto_key = produto_name.lower()
                        
                        for idx, bitola in enumerate(bitolas, 1):
                            campo_nome = f"{produto_key}MadeiraPosta{idx}[]"
                            valores_list = request.form.getlist(campo_nome)
                            madeira_posta_dinamica[f'produto_{produto_id}_bitola_{bitola["id"]}'] = valores_list

                    for idx, cid_str in enumerate(cliente_ids_list):
                        try:
                            cid = int(cid_str)
                        except ValueError:
                            continue
                        
                        tid = None
                        if idx < len(transportadora_ids_list):
                            try:
                                tid = int(transportadora_ids_list[idx]) if transportadora_ids_list[idx] else None
                            except (ValueError, IndexError):
                                tid = None

                        for chave_produto_bitola, valores_list in madeira_posta_dinamica.items():
                            if idx < len(valores_list):
                                produto_id = int(chave_produto_bitola.split('_')[1])
                                bitola_id = int(chave_produto_bitola.split('_')[3])
                                valor_str = valores_list[idx] if valores_list[idx] else '0'
                                valor_convertido = int(ValoresMonetarios.converter_string_brl_para_float(valor_str) * 100)
                                
                                if valor_convertido > 0:
                                    FornecedorMadeiraPostaPrecoBitolaModel.atualizar_ou_criar_preco_madeira_posta(
                                        fornecedor.id, cid, produto_id, bitola_id, valor_convertido, tid)

                if possui_comissionado:
                    comissionados_list = request.form.getlist("comissionados[]")
                    valores_comissao_list = request.form.getlist("valorComissaoTon[]")
                    tipos_comissao_list = request.form.getlist("tipoComissao[]")

                    for idx, comissionado_id in enumerate(comissionados_list):
                        if comissionado_id and comissionado_id.strip():
                            valor_comissao_str = valores_comissao_list[idx] if idx < len(valores_comissao_list) else '0'
                            tipo_comissao = tipos_comissao_list[idx] if idx < len(tipos_comissao_list) else 'valor'
                            
                            if tipo_comissao == 'porcentagem':
                                valor_comissao_100 = int(float(valor_comissao_str) * 100)
                            else:
                                valor_comissao_100 = int(ValoresMonetarios.converter_string_brl_para_float(valor_comissao_str) * 100)
                            
                            fornecedor_comissionado = FornecedorComissionadoModel(
                                fornecedor_id=fornecedor.id,
                                comissionado_id=int(comissionado_id),
                                valor_comissao_ton_100=valor_comissao_100,
                                tipo_comissao=1 if tipo_comissao == 'porcentagem' else 0,
                            )
                            db.session.add(fornecedor_comissionado)

                acao = TipoAcaoEnum.CADASTRO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id, acao, acao.pontos, modulo="fornecedor"
                )
                db.session.commit()

                flash(("Fornecedor cadastrado com sucesso!", "success"))
                return redirect(url_for("listar_fornecedores"))

    except Exception as e:
        flash(('Houve um erro ao tentar cadastrar fornecedor! Entre em contato com o suporte.', 'warning'))
        return redirect(url_for('cadastrar_fornecedor'))

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
        tags=tags,
        produtos_bitolas=produtos_bitolas,
    )


@app.route("/gerenciar/fornecedor/editar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_fornecedor(id):
    try:
        fornecedor = FornecedorCadastroModel.obter_fornecedor_por_id(id)
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
        tags = TagModel.obter_tags_ativas()
        bancos = InstituicoesFinanceirasModel.obter_todos_bancos()
        
        produtos_bitolas = ProdutoBitolaModel.obter_produtos_com_bitolas()

        tags_fornecedor_obj = FornecedorTag.query.filter_by(fornecedor_id=fornecedor.id, ativo=True).all()
        tags_fornecedor_selecionadas = [ft.tag_id for ft in tags_fornecedor_obj]

        precos_custo = FornecedorPrecoCustoBitolaModel.listar_precos_custo_fornecedor(fornecedor.id)
        
        custos_extracao = FornecedorPrecoCustoExtracaoModel.listar_custos_extracao_fornecedor(fornecedor.id)
        
        madeiras_posta = FornecedorMadeiraPostaPrecoBitolaModel.listar_precos_madeira_posta_fornecedor(fornecedor.id)
        madeiras_existentes = madeiras_posta
        
        conta_bancaria = FornecedorContaBancariaModel.query.filter_by(
            fornecedor_id=fornecedor.id, ativo=True, deletado=False
        ).first()
        
        credito = FornecedorCreditoModel.query.filter_by(
            fornecedor_id=fornecedor.id, ativo=True, deletado=False
        ).first()

        fornecedor_comissionados = FornecedorComissionadoModel.listar_por_fornecedor(fornecedor.id)

        precos_dict = {}
        for preco in precos_custo:
            key = f"produto_{preco.produto_id}_bitola_{preco.bitola_id}"
            precos_dict[key] = preco.valor_preco_custo_100 or 0

        custos_dict = {}
        extrator_id_extracao = None
        for custo in custos_extracao:
            key = f"produto_{custo.produto_id}_bitola_{custo.bitola_id}"
            custos_dict[key] = custo.custo_extracao_100 or 0
            if custo.extrator_id and not extrator_id_extracao:
                extrator_id_extracao = custo.extrator_id

        madeira_posta_dict = {}
        for mp in madeiras_posta:
            cliente_id = mp.cliente_id
            if cliente_id not in madeira_posta_dict:
                madeira_posta_dict[cliente_id] = {
                    'transportadora_id': mp.transportadora_id,
                    'precos': {}
                }
            key = f"produto_{mp.produto_id}_bitola_{mp.bitola_id}"
            madeira_posta_dict[cliente_id]['precos'][key] = mp.preco_madeira_posta_100 or 0

        lista_clientes_mp = list(madeira_posta_dict.keys())
        lista_transportadoras_mp = [madeira_posta_dict[cid]['transportadora_id'] for cid in lista_clientes_mp]
        
        listas_madeira_posta = {}
        produtos_bitolas_mp = ProdutoBitolaModel.obter_produtos_com_bitolas()
        
        for produto_id, produto_data in produtos_bitolas_mp.items():
            produto_name = produto_data['nome']
            bitolas = produto_data['bitolas']
            produto_key = produto_name.lower()
            
            for idx, bitola in enumerate(bitolas, 1):
                campo_nome = f"{produto_key}MadeiraPosta{idx}"
                chave_produto_bitola = f'produto_{produto_id}_bitola_{bitola["id"]}'
                listas_madeira_posta[campo_nome] = [
                    madeira_posta_dict[cid]['precos'].get(chave_produto_bitola, 0) 
                    for cid in lista_clientes_mp
                ]

        dados_corretos = {
            "tipoContribuicao": "funrural" if fornecedor.funrural else "senar",
            "classeFornecedor": "sim" if fornecedor.classe_fornecedor else "nao",
            "controleEntrada": "sim" if fornecedor.controle_entrada else "nao",
            "valorContrato": fornecedor.valor_contrato_100 if fornecedor.classe_fornecedor else 0,  
            "estimativaTonelada": str(fornecedor.estimativa_tonelada) if fornecedor.estimativa_tonelada else "",
            "tipoCadastro": "cpf" if fornecedor.fatura_via_cpf else "cnpj",
            "razaoSocial": fornecedor.identificacao if not fornecedor.fatura_via_cpf else "",
            "nomeCompleto": fornecedor.identificacao if fornecedor.fatura_via_cpf else "",
            "cpf": fornecedor.numero_documento if fornecedor.fatura_via_cpf else "",
            "cnpj": fornecedor.numero_documento if not fornecedor.fatura_via_cpf else "",
            "telefone": fornecedor.telefone or "",
            "credito_fornecedor": credito.credito_ton_100 if credito else 0,
            
            "custoExtracao": "possui" if fornecedor.custo_extracao else "nao_possui",
            "extratorNome": extrator_id_extracao or "",
        }
        
        produtos_bitolas_dados = ProdutoBitolaModel.obter_produtos_com_bitolas()
        for produto_id, produto_data in produtos_bitolas_dados.items():
            produto_name = produto_data['nome']
            bitolas = produto_data['bitolas']
            
            if produto_name.lower() == 'eucalipto':
                produto_key = 'euca'
            elif produto_name.lower() == 'pinus':
                produto_key = 'pinus'
            elif produto_name.lower() == 'biomassa':
                produto_key = 'bio'
            else:
                produto_key = produto_name.lower()[:5]
                
            for idx, bitola in enumerate(bitolas, 1):
                campo_nome = f"{produto_key}PrecoCusto{idx}"
                chave_dict = f'produto_{produto_id}_bitola_{bitola["id"]}'
                valor_dict = precos_dict.get(chave_dict, 0)
                dados_corretos[campo_nome] = valor_dict
        
        for produto_id, produto_data in produtos_bitolas_dados.items():
            produto_name = produto_data['nome']
            bitolas = produto_data['bitolas']
            
            if produto_name.lower() == 'eucalipto':
                produto_key = 'euca'
            elif produto_name.lower() == 'pinus':
                produto_key = 'pinus'
            elif produto_name.lower() == 'biomassa':
                produto_key = 'bio'
            else:
                produto_key = produto_name.lower()[:5]
                
            for idx, bitola in enumerate(bitolas, 1):
                campo_nome = f"{produto_key}CustoExtracao{idx}"
                chave_dict = f'produto_{produto_id}_bitola_{bitola["id"]}'
                dados_corretos[campo_nome] = custos_dict.get(chave_dict, 0)
        
        dados_corretos.update({
            "madeiraPosta": "possui" if fornecedor.madeira_posta else "nao_possui",
            "possuiComissionado": "possui" if len(fornecedor_comissionados) > 0 else "nao_possui",
            
            "clienteMadeiraPosta": lista_clientes_mp,
            "transportadoraMadeiraPosta": lista_transportadoras_mp,
            
            "instituicao_financeira": conta_bancaria.instituicao_financeira_id if conta_bancaria else "",
            "agencia_bancaria": conta_bancaria.agencia_bancaria if conta_bancaria else "",
            "conta_bancaria": conta_bancaria.conta_bancaria if conta_bancaria else "",
            "chave_pix": conta_bancaria.chave_pix if conta_bancaria else "",
        })
        
        dados_corretos.update(listas_madeira_posta)

        dados_comissionados = []
        for fc in fornecedor_comissionados:
            if fc.tipo_comissao == 1:
                tipo_exibicao = "porcentagem" 
                valor_exibicao = fc.valor_comissao_ton_100 / 100.0
            else:
                tipo_exibicao = "valor"
                valor_exibicao = fc.valor_comissao_ton_100
            
            dados_comissionados.append({
                'id': fc.comissionado_id,
                'tipo': tipo_exibicao,
                'valor': valor_exibicao
            })
        
        dados_corretos['comissionados'] = dados_comissionados



        if request.method == "POST":
            tipoContribuicao = request.form.get("tipoContribuicao", "")
            declaracaoSenar = request.files.get("declaracaoSenar")
            tipo_cadastro = request.form.get("tipoCadastro", "")
            classeFornecedor = request.form.get("classeFornecedor")
            valorContrato = request.form.get("valorContrato")
            controleEntrada = request.form.get("controleEntrada")
            estimativaTonelada = request.form.get("estimativaTonelada", "")
            custoExtracao = request.form.get("custoExtracao", "")
            nome_completo = request.form.get("nomeCompleto", "").strip()
            razao_social = request.form.get("razaoSocial", "").strip()
            cpf = request.form.get("cpf", "").strip()
            cnpj = request.form.get("cnpj", "").strip()
            telefone = request.form.get("telefone", "").strip()
            
            precos_custo_dados_edicao = {}
            produtos_bitolas_edicao = ProdutoBitolaModel.obter_produtos_com_bitolas()
            
            for produto_id, produto_data in produtos_bitolas_edicao.items():
                produto_name = produto_data['nome']
                bitolas = produto_data['bitolas']
                
                if produto_name.lower() == 'eucalipto':
                    produto_key = 'euca'
                elif produto_name.lower() == 'pinus':
                    produto_key = 'pinus'
                elif produto_name.lower() == 'biomassa':
                    produto_key = 'bio'
                else:
                    produto_key = produto_name.lower()[:5]
                    
                for idx, bitola in enumerate(bitolas, 1):
                    campo_nome = f"{produto_key}PrecoCusto{idx}"
                    valor = request.form.get(campo_nome, "0")
                    precos_custo_dados_edicao[campo_nome] = {
                        'valor': valor,
                        'produto_id': produto_id,
                        'bitola_id': bitola['id']
                    }
            
            extratorNome = request.form.get("extratorNome", "")
            
            custos_extracao_dados = {}
            if custoExtracao == 'possui':
                produtos_bitolas = ProdutoBitolaModel.obter_produtos_com_bitolas()
                for produto_id, produto_data in produtos_bitolas.items():
                    produto_name = produto_data['nome']
                    bitolas = produto_data['bitolas']
                    
                    if produto_name.lower() == 'eucalipto':
                        produto_key = 'euca'
                    elif produto_name.lower() == 'pinus':
                        produto_key = 'pinus'
                    elif produto_name.lower() == 'biomassa':
                        produto_key = 'bio'
                    else:
                        produto_key = produto_name.lower()[:5]
                        
                    for idx, bitola in enumerate(bitolas, 1):
                        campo_nome = f"{produto_key}CustoExtracao{idx}"
                        valor = request.form.get(campo_nome, "0")
                        custos_extracao_dados[campo_nome] = valor
            
            credito_fornecedor = request.form.get("credito_fornecedor", "0")
            contratoFornecedor = request.files.get("contratoFornecedor")
            
            tags_fornecedor = request.form.getlist("tags_fornecedor")
            
            instituicao_financeira = request.form["instituicao_financeira"]
            agencia_bancaria = request.form["agencia_bancaria"]
            conta_bancaria = request.form["conta_bancaria"]
            chave_pix = request.form["chave_pix"]
            
            campos = {
                "telefone": ["Telefone", telefone]
            }
            
            if classeFornecedor == "sim":
                campos["valorContrato"] = ["Valor do Contrato", valorContrato]
                campos["estimativaTonelada"] = ["Estimativa Tonelada", estimativaTonelada]

            if tipo_cadastro == "cpf":
                campos["nomeCompleto"] = ["Nome Completo", nome_completo]
                campos["cpf"] = ["CPF", cpf]
            else:  
                campos["razaoSocial"] = ["Razão Social", razao_social]
                campos["cnpj"] = ["CNPJ", cnpj]

            if tipoContribuicao == "senar" and declaracaoSenar and declaracaoSenar.filename == '' and fornecedor.arquivo_senar_id == None:
                campos["declaracaoSenar"] = ["Declaração Senar", declaracaoSenar]

            if custoExtracao == 'possui':
                campos["extratorNome"] = ["Extrator", extratorNome]

            madeira_posta = True if request.form.get("madeiraPosta") == "possui" else False
            possui_comissionado = True if request.form.get("possuiComissionado") == "possui" else False

            if madeira_posta:
                lista_clientes_mp = request.form.getlist("clienteMadeiraPosta[]")
                if not lista_clientes_mp or all(not cid for cid in lista_clientes_mp):
                    campos["clienteMadeiraPosta"] = ["Cliente", ""]

            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
            if "validado" not in validacao_campos_obrigatorios:
                gravar_banco = False
                flash(("Verifique os campos destacados em vermelho!", "warning"))

            if tipo_cadastro == "cpf":
                verificacao_cpf = ValidaForms.validar_cpf(cpf)
                if "validado" not in verificacao_cpf:
                    gravar_banco = False
                    validacao_campos_erros.update(verificacao_cpf)

                cpf_tratado = ValidaDocs.remove_pontuacao_cpf(cpf)
                if fornecedor.numero_documento != cpf_tratado:
                    pesquisa_cpf_banco = FornecedorCadastroModel.query.filter_by(
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
                    pesquisa_cnpj_banco = FornecedorCadastroModel.query.filter_by(
                        numero_documento=cnpj_tratado
                    ).first()
                    if pesquisa_cnpj_banco:
                        gravar_banco = False
                        validacao_campos_erros["cnpj"] = "O CNPJ informado já existe no banco de dados!"

            if gravar_banco:
                telefone_tratado = Tels.remove_pontuacao_telefone_celular_br(telefone)

                precos_custo_convertidos_edicao = {}
                for campo_nome, dados in precos_custo_dados_edicao.items():
                    valor_convertido = int(ValoresMonetarios.converter_string_brl_para_float(dados['valor']) * 100)
                    precos_custo_convertidos_edicao[campo_nome] = {
                        'valor_100': valor_convertido,
                        'produto_id': dados['produto_id'],
                        'bitola_id': dados['bitola_id']
                    }

                custos_extracao_convertidos = {}
                if custoExtracao == 'possui':
                    for campo_nome, valor in custos_extracao_dados.items():
                        custo_convertido = int(ValoresMonetarios.converter_string_brl_para_float(valor) * 100)
                        custos_extracao_convertidos[campo_nome] = custo_convertido

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

                fornecedor.fatura_via_cpf = fatura_via_cpf
                fornecedor.identificacao = identificacao
                fornecedor.numero_documento = numero_documento
                fornecedor.telefone = telefone_tratado
                fornecedor.funrural = True if tipoContribuicao == 'funrural' else False
                fornecedor.senar = True if tipoContribuicao == 'senar' else False
                fornecedor.imposto_id = 1 if tipoContribuicao == 'funrural' else 2
                fornecedor.classe_fornecedor = True if classeFornecedor == "sim" else False
                fornecedor.valor_contrato_100 = valor_contrato if classeFornecedor == "sim" else None
                fornecedor.estimativa_tonelada = float(estimativaTonelada) if classeFornecedor == "sim" and estimativaTonelada else None
                fornecedor.controle_entrada = True if controleEntrada == "sim" else False
                fornecedor.madeira_posta = madeira_posta
                fornecedor.possui_comissionado = possui_comissionado
                fornecedor.custo_extracao = True if custoExtracao == 'possui' else False

                for campo_nome, dados in precos_custo_convertidos_edicao.items():
                    FornecedorPrecoCustoBitolaModel.atualizar_ou_criar_preco_custo(
                        fornecedor.id, dados['produto_id'], dados['bitola_id'], dados['valor_100'])

                if custoExtracao == 'possui':
                    produtos_bitolas = ProdutoBitolaModel.obter_produtos_com_bitolas()
                    
                    for produto_id, produto_data in produtos_bitolas.items():
                        produto_name = produto_data['nome']
                        bitolas = produto_data['bitolas']
                        
                        if produto_name.lower() == 'eucalipto':
                            produto_key = 'euca'
                        elif produto_name.lower() == 'pinus':
                            produto_key = 'pinus'
                        elif produto_name.lower() == 'biomassa':
                            produto_key = 'bio'
                        else:
                            produto_key = produto_name.lower()[:5]
                            
                        for idx, bitola in enumerate(bitolas, 1):
                            campo_nome = f"{produto_key}CustoExtracao{idx}"
                            custo_convertido = custos_extracao_convertidos.get(campo_nome, 0)
                            
                            FornecedorPrecoCustoExtracaoModel.atualizar_ou_criar_custo_extracao(
                                fornecedor.id, produto_id, bitola['id'], custo_convertido, int(extratorNome))
                else:
                    custos_existentes = FornecedorPrecoCustoExtracaoModel.listar_custos_extracao_fornecedor(fornecedor.id)
                    for custo in custos_existentes:
                        custo.ativo = False
                        custo.deletado = True

                conta_bancaria_existente = FornecedorContaBancariaModel.query.filter_by(
                    fornecedor_id=fornecedor.id, ativo=True, deletado=False
                ).first()
                
                if instituicao_financeira or agencia_bancaria or conta_bancaria or chave_pix:
                    if conta_bancaria_existente:
                        conta_bancaria_existente.instituicao_financeira_id = int(instituicao_financeira) if instituicao_financeira else None
                        conta_bancaria_existente.agencia_bancaria = agencia_bancaria if agencia_bancaria else None
                        conta_bancaria_existente.conta_bancaria = conta_bancaria if conta_bancaria else None
                        conta_bancaria_existente.chave_pix = chave_pix if chave_pix else None
                    else:
                        nova_conta = FornecedorContaBancariaModel(
                            fornecedor_id=fornecedor.id,
                            instituicao_financeira_id=int(instituicao_financeira) if instituicao_financeira else None,
                            agencia_bancaria=agencia_bancaria if agencia_bancaria else None,
                            conta_bancaria=conta_bancaria if conta_bancaria else None,
                            chave_pix=chave_pix if chave_pix else None
                        )
                        db.session.add(nova_conta)
                elif conta_bancaria_existente:
                    conta_bancaria_existente.ativo = False
                    conta_bancaria_existente.deletado = True

                if credito_fornecedor_ton_100 and credito_fornecedor_ton_100 > 0:
                    FornecedorCreditoModel.atualizar_ou_criar_credito(fornecedor.id, credito_fornecedor_ton_100)
                else:
                    credito_existente = FornecedorCreditoModel.query.filter_by(
                        fornecedor_id=fornecedor.id, ativo=True, deletado=False
                    ).first()
                    if credito_existente:
                        credito_existente.ativo = False
                        credito_existente.deletado = True

                tags_existentes = FornecedorTag.query.filter_by(fornecedor_id=fornecedor.id, ativo=True).all()
                for tag_existente in tags_existentes:
                    tag_existente.ativo = False

                if tags_fornecedor:
                    tags_fornecedor_ids = [int(tag_id) for tag_id in tags_fornecedor]
                    for tag_id in tags_fornecedor_ids:
                        tag_existente = FornecedorTag.query.filter_by(
                            fornecedor_id=fornecedor.id, tag_id=tag_id
                        ).first()
                        
                        if tag_existente:
                            tag_existente.ativo = True
                        else:
                            nova_tag = FornecedorTag(
                                fornecedor_id=fornecedor.id,
                                tag_id=tag_id,
                                ativo=True
                            )
                            db.session.add(nova_tag)

                if tipoContribuicao == "senar" and declaracaoSenar and declaracaoSenar.filename:
                    if declaracaoSenar.mimetype in ["application/pdf", "image/jpeg", "image/png"]:
                        declaracao_upload = upload_arquivo(
                            declaracaoSenar,
                            "UPLOAD_DECLARACAO_SENAR",
                            f"{fornecedor.id}",
                        )
                        fornecedor.arquivo_senar_id = declaracao_upload.id
                    else:
                        flash(("A declaração senar deve estar em formato PDF ou JPG ou JPGE ou PNG.", "warning"))
                        return redirect(url_for("editar_fornecedor", id=fornecedor.id))

                if contratoFornecedor and contratoFornecedor.filename:
                    if contratoFornecedor.mimetype == "application/pdf":
                        contrato_upload = upload_arquivo(
                            contratoFornecedor,
                            "UPLOAD_CONTRATO_FORNECEDOR",
                            f"{fornecedor.id}",
                        )
                        fornecedor.contrato_fornecedor_id = contrato_upload.id
                    else:
                        flash(("O contrato do fornecedor deve estar em formato PDF.", "warning"))
                        return redirect(url_for("editar_fornecedor", id=fornecedor.id))

                if madeira_posta:
                    cliente_ids_list = request.form.getlist("clienteMadeiraPosta[]")
                    transportadora_ids_list = request.form.getlist("transportadoraMadeiraPosta[]")
                    
                    madeira_posta_dinamica = {}
                    produtos_bitolas_edicao = ProdutoBitolaModel.obter_produtos_com_bitolas()
                    
                    for produto_id, produto_data in produtos_bitolas_edicao.items():
                        produto_name = produto_data['nome']
                        bitolas = produto_data['bitolas']
                        produto_key = produto_name.lower()
                        
                        for idx, bitola in enumerate(bitolas, 1):
                            campo_nome = f"{produto_key}MadeiraPosta{idx}[]"
                            valores_list = request.form.getlist(campo_nome)
                            chave_mapeamento = f'produto_{produto_id}_bitola_{bitola["id"]}'
                            madeira_posta_dinamica[chave_mapeamento] = valores_list

                    for idx, cid_str in enumerate(cliente_ids_list):
                        try:
                            cid = int(cid_str)
                        except ValueError:
                            continue

                        tid = None
                        if idx < len(transportadora_ids_list):
                            try:
                                tid = int(transportadora_ids_list[idx]) if transportadora_ids_list[idx] else None
                            except (ValueError, IndexError):
                                tid = None

                        for chave_produto_bitola, valores_list in madeira_posta_dinamica.items():
                            if idx < len(valores_list):
                                produto_id = int(chave_produto_bitola.split('_')[1])
                                bitola_id = int(chave_produto_bitola.split('_')[3])
                                valor_str = valores_list[idx] if valores_list[idx] else '0'
                                valor_convertido = int(ValoresMonetarios.converter_string_brl_para_float(valor_str) * 100)
                                registro_existente = FornecedorMadeiraPostaPrecoBitolaModel.query.filter_by(
                                    fornecedor_id=fornecedor.id,
                                    cliente_id=cid,
                                    produto_id=produto_id,
                                    bitola_id=bitola_id,
                                    transportadora_id=tid,
                                    ativo=True,
                                    deletado=False
                                ).first()
                                
                                if registro_existente:
                                    registro_existente.preco_madeira_posta_100 = valor_convertido
                                else:
                                    novo_registro = FornecedorMadeiraPostaPrecoBitolaModel(
                                        fornecedor_id=fornecedor.id,
                                        cliente_id=cid,
                                        produto_id=produto_id,
                                        bitola_id=bitola_id,
                                        preco_madeira_posta_100=valor_convertido,
                                        transportadora_id=tid
                                    )
                                    db.session.add(novo_registro)
                else:
                    madeiras_existentes = FornecedorMadeiraPostaPrecoBitolaModel.listar_precos_madeira_posta_fornecedor(fornecedor.id)
                    for mp_existente in madeiras_existentes:
                        mp_existente.ativo = False
                        mp_existente.deletado = True

                if possui_comissionado:
                    comissionados_existentes = FornecedorComissionadoModel.listar_por_fornecedor(fornecedor.id)
                    for com_existente in comissionados_existentes:
                        com_existente.ativo = False
                        com_existente.deletado = True

                    comissionados_list = request.form.getlist("comissionados[]")
                    valores_comissao_list = request.form.getlist("valorComissaoTon[]")
                    tipos_comissao_list = request.form.getlist("tipoComissao[]")

                    for idx, comissionado_id in enumerate(comissionados_list):
                        if comissionado_id and comissionado_id.strip():
                            valor_comissao_str = valores_comissao_list[idx] if idx < len(valores_comissao_list) else '0'
                            tipo_comissao = tipos_comissao_list[idx] if idx < len(tipos_comissao_list) else 'valor'
                            
                            if tipo_comissao == 'porcentagem':
                                valor_comissao_100 = int(float(valor_comissao_str) * 100)
                            else:
                                valor_comissao_100 = int(ValoresMonetarios.converter_string_brl_para_float(valor_comissao_str) * 100)
                            
                            fornecedor_comissionado = FornecedorComissionadoModel(
                                fornecedor_id=fornecedor.id,
                                comissionado_id=int(comissionado_id),
                                valor_comissao_ton_100=valor_comissao_100,
                                tipo_comissao=1 if tipo_comissao == 'porcentagem' else 0,
                            )
                            db.session.add(fornecedor_comissionado)
                else:
                    comissionados_existentes = FornecedorComissionadoModel.listar_por_fornecedor(fornecedor.id)
                    for com_existente in comissionados_existentes:
                        com_existente.ativo = False
                        com_existente.deletado = True

                acao = TipoAcaoEnum.EDICAO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id, acao, acao.pontos, modulo="fornecedor"
                )

                db.session.commit()
                flash(("Fornecedor atualizado com sucesso!", "success"))
                return redirect(url_for("listar_fornecedores"))
    except Exception as e:
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
        tags=tags,
        tags_fornecedor_selecionadas=tags_fornecedor_selecionadas,
        produtos_bitolas=produtos_bitolas
    )


@app.route("/gerenciar/desativar/fornecedor/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def desativar_fornecedor(id):
    fornecedor = FornecedorCadastroModel.obter_fornecedor_por_id(id)
    if fornecedor is None:
        flash(("Fornecedor não encontrado!", "warning"))

    fornecedor.ativo = False
    db.session.commit()
    flash(("Fornecedor desativado com sucesso!", "success"))
    return redirect(url_for("listar_fornecedores"))


@app.route("/gerenciar/ativar/fornecedor/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def ativar_fornecedor(id):
    fornecedor = FornecedorCadastroModel.obter_fornecedor_por_id(id)
    if fornecedor is None:
        flash(("Fornecedor não encontrado!", "warning"))

    fornecedor.ativo = True
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
        
        fornecedor_filtro = None if fornecedor_id == "todos" else fornecedor_id
        
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
