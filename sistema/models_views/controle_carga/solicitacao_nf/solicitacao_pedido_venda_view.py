from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem
from flask import render_template, request, redirect, url_for, flash, jsonify
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from flask_login import login_required, current_user
from sistema.models_views.controle_carga.solicitacao_nf.solicitacao_pedido_venda_model import SolicitacaoPedidoVendaModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema.models_views.gerenciar.motorista.motorista_model import MotoristaModel
from sistema.models_views.gerenciar.motorista.transportadora_motorista_associado_model import TransportadoraMotoristaAssocModel
from sistema.models_views.gerenciar.veiculo.veiculo_model import VeiculoModel
from sistema.models_views.gerenciar.veiculo.veiculo_transportadora_veiculo_associado_model import TransportadoraVeiculoAssocModel
from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.parametros.nome_grupo_whats.nome_grupo_whats_model import NomeGrupoWhatsModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.configuracoes_gerais.empresa_emissora.empresa_emissora_model import EmpresaEmissoraModel
from sistema.models_views.faturamento.cargas_a_faturar.transportadora.frete_a_pagar_model import FretePagarModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.gerenciar.certificacoes.certificacoes_model import CertificacoesModel
from sistema.models_views.controle_carga.registro_operacional.pedido_venda_model import PedidoVendaModel
from sistema.models_views.controle_carga.registro_operacional.pedido_venda_dados_nf_model import PedidoVendaDadosNfModel
from sistema._utilitarios import *

def limpar_todos_arquivos_anexados(objeto_nf_xml=None, objeto_nf_pdf=None, objeto_nf_excesso_xml=None, objeto_nf_excesso_pdf=None):
    """Remove todos os arquivos anexados do banco e do sistema de arquivos"""
    import os
    arquivos = [objeto_nf_xml, objeto_nf_pdf, objeto_nf_excesso_xml, objeto_nf_excesso_pdf]
    
    for arquivo in arquivos:
        if arquivo:
            try:
                if hasattr(arquivo, 'caminho') and os.path.exists(arquivo.caminho):
                    os.remove(arquivo.caminho)
                db.session.delete(arquivo)
            except Exception as cleanup_error:
                print(f"[ERRO] Erro ao limpar arquivo: {cleanup_error}")
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[ERRO] Erro ao commitar remoção de arquivos: {e}")

@app.route("/veiculo/<int:veiculo_id>/dados")
@login_required
@requires_roles
def buscar_dados_por_veiculo(veiculo_id):
    veiculo = VeiculoModel.obter_veiculo_por_id(veiculo_id)
    if not veiculo:
        return jsonify({"erro": "Veículo não encontrado"}), 404

    transpAssociadas = TransportadoraVeiculoAssocModel.obter_transportadoras_assoc_veiculo_id(veiculo_id)

    if transpAssociadas:
        transportadoras = [
            {
                "id": assoc.transportadora.id,
                "nome": assoc.transportadora.identificacao
            }
            for assoc in transpAssociadas
        ]
    elif veiculo.transportadora:
        transportadoras = [{
            "id": veiculo.transportadora.id,
            "nome": veiculo.transportadora.identificacao
        }]
    else:
        transportadoras = []

    ids_transportadoras = [t["id"] for t in transportadoras]

    motoristas = MotoristaModel.query.filter(
        MotoristaModel.transportadora_id.in_(ids_transportadoras),
        MotoristaModel.ativo == True,
        MotoristaModel.deletado == False
    ).all()

    return jsonify({
        "transportadoras": transportadoras,
        "motoristas": [{"id": m.id, "nome": m.nome_completo} for m in motoristas],
        "capacidade_carga": veiculo.capacidade_ton
    })

@app.route("/motorista/<int:transportadora_id>/dados")
@login_required
@requires_roles
def buscar_motoristas_por_transportadora(transportadora_id):
    motorista = TransportadoraMotoristaAssocModel.obter_motoristas_assoc_transportadora_id(transportadora_id)
    
    if not motorista:
        return jsonify({"erro": "Motorista não encontrado"}), 404
    return jsonify({
        "motoristas": [{"id": m.id, "nome": m.nome_completo} for m in motorista],
    })

@app.route("/produto/<int:produto_id>/bitolas")
@login_required
@requires_roles
def buscar_bitolas_por_produto(produto_id):
    """Retorna as bitolas associadas a um produto específico"""
    from sistema.models_views.parametros.produto_bitola.produto_bitola_model import ProdutoBitolaModel
    
    bitolas = ProdutoBitolaModel.listar_bitolas_por_produto(produto_id)
    
    if not bitolas:
        return jsonify({"bitolas": []})
    
    return jsonify({
        "bitolas": [{"id": b.id, "nome": b.bitola} for b in bitolas]
    })


@app.route("/controle-cargas/solicitacao/detalhes/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def detalhes_solicitacao(id):    
    solicitacao = SolicitacaoPedidoVendaModel.obter_solicitacao_por_id(id)
    return render_template(
        "/controle_carga/solicitacao/solicitacao_detalhes.html",
        solicitacao=solicitacao
    )


@app.route("/controle-cargas/listar/solicitacoes/nf", methods=["GET", "POST"])
@login_required
@requires_roles
def listagem_solicitacoes():    
    if request.method == "POST":
        solicitacao = SolicitacaoPedidoVendaModel.filtrar_solicitacoes(
            cliente_nome=request.form.get("cliente"),
            motorista_nome=request.form.get("motorista"),
            placa=request.form.get("placa"),
        )
    else:
        solicitacao = SolicitacaoPedidoVendaModel.obter_solicitacoes_em_aberto_desc_id()
    return render_template(
        "/controle_carga/solicitacao/solicitacao_listar.html",
        solicitacao=solicitacao, dados_corretos=request.form
    )

@app.route("/controle-cargas/cadastrar/solicitacao", methods=["GET", "POST"])
@login_required
@requires_roles
def cadastrar_solicitacao():
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    cliente = ClienteModel.listar_clientes_ativos()
    empresas = EmpresaEmissoraModel.obter_empresas_emissoras_ativas()
    transportadora = TransportadoraModel.listar_transportadoras_ativas()
    veiculo = VeiculoModel.listar_veiculos_ativos()
    bitola = BitolaModel.listar_bitolas_ativas()
    produtos = ProdutoModel.listar_produtos()
    grupo_whats = NomeGrupoWhatsModel.listar_grupos_ativos()
    certificacoes = CertificacoesModel.listar_certificacoes_ativas()

    if request.method == "POST":
        empresaEmissora = request.form["empresaEmissora"]
        clienteSolicitacao = request.form["clienteSolicitacao"]
        bitolaSolicitacao = request.form["bitolaSolicitacao"]
        produtoSolicitacao = request.form["produtoSolicitacao"]
        transportadoraSolicitacao = request.form["transportadoraSolicitacao"]
        motoristaSolicitacao = request.form["motoristaSolicitacao"]
        placaVeiculo = request.form["placaVeiculo"]
        nomeGrupo = request.form["nomeGrupo"]
        certificacao_solicitacao = request.form["certificacao_solicitacao"]
        
        campos = {
            "empresaEmissora": ["Empresa Emissora", empresaEmissora],
            "clienteSolicitacao": ["Cliente", clienteSolicitacao],
            "bitolaSolicitacao": ["Bitola", bitolaSolicitacao],
            "produtoSolicitacao": ["Produto", produtoSolicitacao],
            "transportadoraSolicitacao": ["Transportadora", transportadoraSolicitacao],
            "motoristaSolicitacao": ["Motorista", motoristaSolicitacao],
            "placaVeiculo": ["Placa", placaVeiculo],
        }

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))

        if gravar_banco == True:
            try:
                SolicitacaoPedidoVendaModel.cadastrar_solicitacao(
                    empresa_emissora_id=empresaEmissora,
                    cliente_id=clienteSolicitacao,
                    bitola_id=bitolaSolicitacao,
                    produto_id=produtoSolicitacao,
                    motorista_id=motoristaSolicitacao,
                    transportadora_id=transportadoraSolicitacao,
                    veiculo_id=placaVeiculo,
                    certificacao_id=certificacao_solicitacao if certificacao_solicitacao else None,
                    usuario_id=current_user.id,
                    grupo_whats_id=nomeGrupo if nomeGrupo else None,
                    nf_emitida=False,
                    cancelada=False,
                    ativo=True,
                )
                acao = TipoAcaoEnum.CADASTRO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    acao,
                    acao.pontos,
                    modulo='solicitacao_nf'
                )
                flash(("Solicitação cadastrada com sucesso!", "success"))
                return redirect(url_for("listagem_solicitacoes"))
            except Exception as e:
                print(e)
                db.session.rollback()
                flash((f"Erro ao cadastrar solicitação! Entre em contato com o suporte.", "error"))

    return render_template(
        "/controle_carga/solicitacao/solicitacao_cadastrar.html",
        produtos=produtos,
        veiculo=veiculo,
        empresas=empresas,
        grupo_whats=grupo_whats,
        cliente=cliente,
        transportadora=transportadora,
        bitola=bitola,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
        certificacoes=certificacoes
    )

@app.route("/controle-cargas/editar/solicitacao/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_solicitacao(id):
    solicitacao = SolicitacaoPedidoVendaModel.obter_solicitacao_por_id(id)

    if solicitacao is None:
        flash(("Solicitação não encontrada!", "warning"))
        return redirect(url_for("listagem_solicitacoes"))

    empresas = EmpresaEmissoraModel.obter_empresas_emissoras_ativas()
    cliente = ClienteModel.listar_clientes_ativos()
    transportadora = TransportadoraModel.listar_transportadoras_ativas()
    bitola = BitolaModel.listar_bitolas_ativas()
    produtos = ProdutoModel.listar_produtos()
    grupo_whats = NomeGrupoWhatsModel.listar_grupos_ativos()
    veiculos = VeiculoModel.listar_veiculos_ativos()
    certificacoes = CertificacoesModel.listar_certificacoes_ativas()
    
    campos_obrigatorios = {}

    if request.method == "POST":
        empresaEmissora = request.form["empresaEmissora"]
        clienteSolicitacao = request.form.get("clienteSolicitacao")
        bitolaSolicitacao = request.form.get("bitolaSolicitacao")
        produtoSolicitacao = request.form.get('produtoSolicitacao')
        transportadoraSolicitacao = request.form.get("transportadoraSolicitacao")
        motoristaSolicitacao = request.form.get("motoristaSolicitacao")
        placaVeiculo = request.form.get("placaVeiculo")
        nomeGrupo = request.form.get("nomeGrupo")
        certificacao_solicitacao = request.form["certificacao_solicitacao"]


        campos = {
            "empresaEmissora": ["Empresa Emissora", empresaEmissora],
            "clienteSolicitacao": ["Cliente", clienteSolicitacao],
            "bitolaSolicitacao": ["Bitola", bitolaSolicitacao],
            "produtoSolicitacao": ["Produto", produtoSolicitacao],
            "transportadoraSolicitacao": ["Transportadora", transportadoraSolicitacao],
            "motoristaSolicitacao": ["Motorista", motoristaSolicitacao],
            "placaVeiculo": ["Placa", placaVeiculo],
        }

        campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if "validado" in campos_obrigatorios:

            obj1 = {
                "empresaEmissora": str(solicitacao.empresa_emissora_id),
                "clienteSolicitacao": str(solicitacao.cliente_id),
                "bitolaSolicitacao": str(solicitacao.bitola_id),
                "produtoSolicitacao": str(solicitacao.produto_id),
                "motoristaSolicitacao": str(solicitacao.motorista_id),
                "placaVeiculo": str(solicitacao.veiculo_id),
                "nomeGrupo": str(solicitacao.grupo_whats_id) if solicitacao.grupo_whats_id else "",
                "certificacao_solicitacao": str(solicitacao.certificacao_id) if solicitacao.certificacao_id else "",
            }

            obj2 = {
                "empresaEmissora": empresaEmissora,
                "clienteSolicitacao": clienteSolicitacao,
                "bitolaSolicitacao": bitolaSolicitacao,
                "produtoSolicitacao": produtoSolicitacao,
                "motoristaSolicitacao": motoristaSolicitacao,
                "placaVeiculo": placaVeiculo,
                "nomeGrupo": nomeGrupo if nomeGrupo else "",
                "certificacao_solicitacao": certificacao_solicitacao,
            }

            diferencas = Gameficacao.compara_objetos(obj1, obj2)
            if diferencas:
                acao = TipoAcaoEnum.EDICAO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    acao,
                    acao.pontos,
                    modulo='solicitacao_nf'
                )

            # Verifica se possui frete a pagar
            frete = FretePagarModel.obter_frete_por_solicitacao_id(solicitacao.id)
            if frete:
                frete.transportadora_id = transportadoraSolicitacao
                frete.bitola_id = bitolaSolicitacao
                
            solicitacao.empresa_emissora_id = empresaEmissora
            solicitacao.cliente_id = clienteSolicitacao
            solicitacao.bitola_id = bitolaSolicitacao
            solicitacao.produto_id = produtoSolicitacao
            solicitacao.motorista_id = motoristaSolicitacao
            solicitacao.veiculo_id = placaVeiculo
            solicitacao.transportadora_id = transportadoraSolicitacao
            solicitacao.grupo_whats_id = nomeGrupo if nomeGrupo else None
            solicitacao.usuario_id = current_user.id
            solicitacao.certificacao_id = certificacao_solicitacao if certificacao_solicitacao else None

            db.session.commit()
            flash(("Solicitação editada com sucesso!", "success"))
            return redirect(url_for("listagem_solicitacoes"))
        else:
            flash(("Verifique os campos destacados em vermelho!", "warning"))

    dados_corretos = {
        "clienteSolicitacao": solicitacao.cliente_id,
        "bitolaSolicitacao": solicitacao.bitola_id,
        "produtoSolicitacao": solicitacao.produto_id,
        "transportadoraSolicitacao": solicitacao.transportadora_id,
        "motoristaSolicitacao": solicitacao.motorista_id,
        "placaVeiculo": solicitacao.veiculo_id,
        "nomeGrupo": solicitacao.grupo_whats_id,
        "certificacao_solicitacao": solicitacao.certificacao_id
    }

    return render_template(
        "/controle_carga/solicitacao/solicitacao_editar.html",
        solicitacao=solicitacao,
        empresas=empresas,
        produtos=produtos,
        cliente=cliente,
        transportadora=transportadora,
        bitola=bitola,
        grupo_whats=grupo_whats,
        veiculos=veiculos,
        campos_obrigatorios=campos_obrigatorios,
        campos_erros={},
        dados_corretos=dados_corretos,
        certificacoes=certificacoes
    )

@app.route("/controle-cargas/cancelar/solicitacao/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def cancelar_solicitacao(id):
    solicitacao = SolicitacaoPedidoVendaModel.obter_solicitacao_por_id(id)

    if solicitacao is None:
        flash(("Solicitação não encontrada!", "warning"))
    solicitacao.cancelada = True
    solicitacao.ativo = False
    db.session.commit()
    flash(("Solicitação cancelada com sucesso!", "success"))
    return redirect(url_for("listagem_solicitacoes"))


@app.route("/controle-cargas/relatorio/solicitacao-lancamento/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def relatorio_solicitacoes_lancamentos(id):
    dataHoje = DataHora.obter_data_atual_padrao_br()
    carga = SolicitacaoPedidoVendaModel.obter_solicitacao_por_id(id)
    cargas_relacionadas = SolicitacaoPedidoVendaModel.listar_cargas()
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()

    logo_path = obter_url_absoluta_de_imagem('logo.png')
    html =  render_template(
        "relatorios/relatorio_solicitacao/relatorio_solicitacao_lancamento.html",logo_path=logo_path, dataHoje=dataHoje,
                                                                    carga=carga,
                                                                    changelog=changelog, cargas_relacionadas=cargas_relacionadas)

    nome_arquivo_saida = f'solicitacao-{dataHoje}'
    resposta = ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida)

    return resposta

@app.route("/controle-cargas/notas-fiscais/lancar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def cadastrar_emissao(id):
    print('to aqui')
    solicitacao = SolicitacaoPedidoVendaModel.obter_solicitacao_por_id(id)
    if solicitacao is None:
        flash(("A solicitação da Nota Fiscal não foi encontrada!", "warning"))
        return redirect(url_for("listagem_solicitacoes"))

    if solicitacao.nf_emitida == 1:
        flash(("Nota Fiscal já emitida!", "warning"))
        return redirect(url_for("listagem_solicitacoes"))

    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    if request.method == "POST":
        
        arquivo_nf_xml = request.files.get("arquivoNfXml")
        arquivo_nf_pdf = request.files.get("arquivoNfPdf")
        possui_nfe_excesso = request.form.get("possuiNFeExcesso", "nao")
        arquivo_nfe_excesso_xml = request.files.get("arquivoNFeExcessoXml") if possui_nfe_excesso == "sim" else None
        arquivo_nfe_excesso_pdf = request.files.get("arquivoNFeExcessoPdf") if possui_nfe_excesso == "sim" else None
        lancamentoFrf = request.form.get("lancamentoFrf")
        cargaFrf = True if lancamentoFrf == 'lancamentoFrf' else False
        
        campos = {}
        if cargaFrf:
            dados_frf = PedidoVendaModel.extrair_dados_frf_form(request)
            campos = {
                "destinatarioFrf": ["Destinatário", dados_frf["destinatario_nome"]],
                "destinatarioNumeroDocumento": ["CPF/CNPJ", dados_frf["destinatario_cnpj_cpf"]],
                "dataLancamentoFrf": ["Data lançamento", dados_frf["destinatario_data_emissao"]],
                "transportadorFrf": ["Transportador", dados_frf["transportador_nome"]],
                "transportadoraNumeroDocumento": ["CPF/CNPJ", dados_frf["transportador_cnpj_cpf"]],
                "placaFrf": ["Placa", dados_frf["placa_nf"]],
                "motoristaFrf": ["motorista", dados_frf["motorista_nf"]],
                "pesoFrf": ["Peso", dados_frf["peso_ton_nf"]],
                "valorTotalFrf": ["Valor", dados_frf["valor_total_nota_100"]],
            }
        else:
            # Validar se pelo menos um arquivo (XML ou PDF) foi enviado
            if not ((arquivo_nf_xml and arquivo_nf_xml.filename) or (arquivo_nf_pdf and arquivo_nf_pdf.filename)):
                campos["arquivoNf"] = ["Arquivo NF (XML ou PDF)", None]
        if possui_nfe_excesso == "sim":
            # Validar se pelo menos um arquivo de excesso (XML ou PDF) foi enviado
            if not ((arquivo_nfe_excesso_xml and arquivo_nfe_excesso_xml.filename) or (arquivo_nfe_excesso_pdf and arquivo_nfe_excesso_pdf.filename)):
                campos["arquivoNFeExcesso"] = ["Arquivo NFe de Excesso (XML ou PDF)", None]

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
        gravar_banco = True
        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))

        validacao_campos_erros = {}
        if cargaFrf:
            print('to qui')
            # Validação CPF/CNPJ Destinatário
            numero_documento_destinatario = ValidaDocs.somente_numeros(dados_frf["destinatario_cnpj_cpf"])
            if len(numero_documento_destinatario) > 11:
                valida_documento_destinatario = ValidaForms.validar_cnpj(numero_documento_destinatario)
                if not 'validado' in valida_documento_destinatario:
                    gravar_banco = False
                    validacao_campos_erros['destinatarioNumeroDocumento'] = valida_documento_destinatario.get('cnpj', 'Erro na validação do CNPJ')
            else:
                valida_documento_destinatario = ValidaForms.validar_cpf(numero_documento_destinatario)
                if not 'validado' in valida_documento_destinatario:
                    gravar_banco = False
                    validacao_campos_erros['destinatarioNumeroDocumento'] = valida_documento_destinatario.get('cpf', 'Erro na validação do CPF')

            # Validação CPF/CNPJ Transportadora
            numero_documento_transportadora = ValidaDocs.somente_numeros(dados_frf["transportador_cnpj_cpf"])
            if len(numero_documento_transportadora) > 11:
                valida_documento_transportadora = ValidaForms.validar_cnpj(numero_documento_transportadora)
                if not 'validado' in valida_documento_transportadora:
                    gravar_banco = False
                    validacao_campos_erros['transportadoraNumeroDocumento'] = valida_documento_transportadora.get('cnpj', 'Erro na validação do CNPJ')
            else:
                valida_documento_transportadora = ValidaForms.validar_cpf(numero_documento_transportadora)
                if not 'validado' in valida_documento_transportadora:
                    gravar_banco = False
                    validacao_campos_erros['transportadoraNumeroDocumento'] = valida_documento_transportadora.get('cpf', 'Erro na validação do CPF')

        if gravar_banco:
            try:
            
                if cargaFrf:
                    # Conversão dos campos
                    try:
                        pesoFrf_float = float(str(dados_frf["peso_ton_nf"]).replace(',', '.') if dados_frf["peso_ton_nf"] else 0)
                        valorTotalFrf_100 = int(ValoresMonetarios.converter_string_brl_para_float(dados_frf["valor_total_nota_100"]) * 100) if dados_frf["valor_total_nota_100"] else 0
                       
                    except Exception as conv_error:
                        raise
                   
                    pedido_venda = PedidoVendaModel.obter_pedido_venda_por_solicitacao_id(solicitacao.id)
                    
                    if solicitacao.certificacao_id:
                        # Certificação - Atualiza o estoque da certificação associada à carga
                        resultado_atualizacao = CertificacoesModel.atualizar_estoque(pesoFrf_float, solicitacao.certificacao_id)
                        if "erro" in resultado_atualizacao or "invalido" in resultado_atualizacao:
                            if "invalido" in resultado_atualizacao:
                                flash((resultado_atualizacao["invalido"], "warning"))
                            elif "erro" in resultado_atualizacao:
                                flash((resultado_atualizacao["erro"], "warning"))
                            db.session.rollback()
                            return redirect(url_for("cadastrar_emissao", id=solicitacao.id))
                    
                    if pedido_venda:
                        # Atualizar pedido existente
                        pedido_venda.situacao_financeira_id = 2
                        
                        # Buscar ou criar dados da NF
                        dados_nf_existente = PedidoVendaDadosNfModel.obter_dados_nf_por_pedido_venda_id(pedido_venda.id)
                        if dados_nf_existente:
                            dados_nf_existente.numero_nota_fiscal = '000000'
                            dados_nf_existente.peso_ton_nf = pesoFrf_float
                            dados_nf_existente.destinatario_nome = dados_frf["destinatario_nome"]
                            dados_nf_existente.destinatario_cnpj_cpf = numero_documento_destinatario
                            dados_nf_existente.valor_total_nota_100 = valorTotalFrf_100
                            dados_nf_existente.transportador_nome = dados_frf["transportador_nome"]
                            dados_nf_existente.transportador_cnpj_cpf = numero_documento_transportadora
                            dados_nf_existente.placa_nf = dados_frf["placa_nf"]
                            dados_nf_existente.motorista_nf = dados_frf["motorista_nf"]
                            dados_nf_existente.carga_frf = True
                            dados_nf_existente.destinatario_data_emissao = dados_frf["destinatario_data_emissao"]
                        else:
                            PedidoVendaDadosNfModel.criar_dados_nf(
                                pedido_venda_id=pedido_venda.id,
                                numero_nota_fiscal='000000',
                                peso_ton_nf=pesoFrf_float,
                                destinatario_nome=dados_frf["destinatario_nome"],
                                destinatario_cnpj_cpf=numero_documento_destinatario,
                                valor_total_nota_100=valorTotalFrf_100,
                                status_emissao_nf_complementar_id=2,
                                transportador_nome=dados_frf["transportador_nome"],
                                transportador_cnpj_cpf=numero_documento_transportadora,
                                placa_nf=dados_frf["placa_nf"],
                                motorista_nf=dados_frf["motorista_nf"],
                                destinatario_data_emissao=dados_frf["destinatario_data_emissao"],
                                carga_frf=True
                            )
                    else:
                        # Criar novo pedido de venda
                        pedido_venda = PedidoVendaModel.criar_pedido_venda(
                            solicitacao_pedido_venda_id=solicitacao.id,
                            situacao_financeira_id=2
                        )
                        
                        # Criar dados da NF
                        PedidoVendaDadosNfModel.criar_dados_nf(
                            pedido_venda_id=pedido_venda.id,
                            numero_nota_fiscal='000000',
                            peso_ton_nf=pesoFrf_float,
                            destinatario_nome=dados_frf["destinatario_nome"],
                            destinatario_cnpj_cpf=numero_documento_destinatario,
                            valor_total_nota_100=valorTotalFrf_100,
                            transportador_nome=dados_frf["transportador_nome"],
                            transportador_cnpj_cpf=numero_documento_transportadora,
                            status_emissao_nf_complementar_id=2,
                            placa_nf=dados_frf["placa_nf"],
                            motorista_nf=dados_frf["motorista_nf"],
                            destinatario_data_emissao=dados_frf["destinatario_data_emissao"],
                            carga_frf=True
                        )
                    solicitacao.nf_emitida = True
                    db.session.commit()
                    acao = TipoAcaoEnum.CADASTRO
                    PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                        current_user.id,
                        acao,
                        acao.pontos,
                        modulo='lancamento_nf'
                    )
                    flash((f"FRF lançado com sucesso!", "success"))
                    return redirect(url_for("listagem_solicitacoes"))
                elif (arquivo_nf_xml and arquivo_nf_xml.filename) or (arquivo_nf_pdf and arquivo_nf_pdf.filename):
                   
                    objeto_nf_xml = None
                    objeto_nf_pdf = None
                    
                    if arquivo_nf_xml and arquivo_nf_xml.filename:
                       
                        if arquivo_nf_xml.mimetype in ["application/xml", "text/xml"]:
                           
                            objeto_nf_xml = upload_arquivo(
                                arquivo_nf_xml, "UPLOAD_ARQUIVO_NF", f"{solicitacao.id}_xml"
                            )
                           
                        else:
                           
                            flash(("O arquivo XML deve ter o tipo correto.", "warning"))
                            return redirect(url_for("cadastrar_emissao", id=solicitacao.id))
                    
                    if arquivo_nf_pdf and arquivo_nf_pdf.filename:
                       
                        if arquivo_nf_pdf.mimetype == "application/pdf":
                           
                            objeto_nf_pdf = upload_arquivo(
                                arquivo_nf_pdf, "UPLOAD_ARQUIVO_NF", f"{solicitacao.id}_pdf"
                            )
                           
                        else:
                           
                            flash(("O arquivo PDF deve ter o tipo correto.", "warning"))
                            return redirect(url_for("cadastrar_emissao", id=solicitacao.id))
                    try:

                        if not objeto_nf_xml:
                           
                            limpar_todos_arquivos_anexados(objeto_nf_xml, objeto_nf_pdf)
                            flash(("Para finalizar o lançamento, é preciso enviar o arquivo XML da nota fiscal. O PDF é opcional e pode ser usado para visualização.","warning"))
                            return redirect(url_for("cadastrar_emissao", id=solicitacao.id))

                        dados_nf = PedidoVendaModel.extrair_dados_nota_fiscal(
                            objeto_nf_xml=objeto_nf_xml
                        )
                        
                        if not dados_nf:
                            
                            limpar_todos_arquivos_anexados(objeto_nf_xml, objeto_nf_pdf)
                            flash(("Não foi possível extrair dados do arquivo XML. Verifique se é um arquivo XML válido.", "warning"))
                            return redirect(url_for("cadastrar_emissao", id=solicitacao.id))
                        
                        peso_nf = dados_nf["peso_ton_nf"]
                        preco_un = dados_nf["preco_un_nf"]
                        
                        if peso_nf is None or peso_nf < 0 or peso_nf == "":
                            limpar_todos_arquivos_anexados(objeto_nf_xml, objeto_nf_pdf)
                            flash(("O peso extraído da nota fiscal é inválido! Entre em contato com o suporte!", "warning"))
                            return redirect(url_for("cadastrar_emissao", id=solicitacao.id))
                            
                    except Exception as e:
                        limpar_todos_arquivos_anexados(objeto_nf_xml, objeto_nf_pdf)
                        flash(("O XML da nota fiscal apresentou inconsistências ou está em formato inválido. Por favor, revise o arquivo e envie novamente.", "warning"))
                        return redirect(url_for("cadastrar_emissao", id=solicitacao.id))

                    objeto_nf_excesso_xml = None
                    objeto_nf_excesso_pdf = None
                    numero_nota_excessao = None
                    peso_nf_excesso = 0
                    peso_total_com_excesso = peso_nf
                    
                    if possui_nfe_excesso == "sim" and ((arquivo_nfe_excesso_xml and arquivo_nfe_excesso_xml.filename) or (arquivo_nfe_excesso_pdf and arquivo_nfe_excesso_pdf.filename)):
                        if not (arquivo_nfe_excesso_xml and arquivo_nfe_excesso_xml.filename):
                           
                            limpar_todos_arquivos_anexados(objeto_nf_xml, objeto_nf_pdf)
                            flash(("Para lançar o excesso, é necessário enviar o arquivo XML da nota de excesso. O PDF é opcional.", "warning"))
                            return redirect(url_for("cadastrar_emissao", id=solicitacao.id))
                        
                        if arquivo_nfe_excesso_xml and arquivo_nfe_excesso_xml.filename:
                           
                            if arquivo_nfe_excesso_xml.mimetype in ["application/xml", "text/xml"]:
                                objeto_nf_excesso_xml = upload_arquivo(
                                    arquivo_nfe_excesso_xml, "UPLOAD_ARQUIVO_NF_EXCESSO", f"{solicitacao.id}_excesso_xml"
                                )
                               
                            else:
                               
                                flash(("O arquivo XML de excesso deve ter o tipo correto.", "warning"))
                                return redirect(url_for("cadastrar_emissao", id=solicitacao.id))
                        
                        if arquivo_nfe_excesso_pdf and arquivo_nfe_excesso_pdf.filename:
                            if arquivo_nfe_excesso_pdf.mimetype == "application/pdf":
                                objeto_nf_excesso_pdf = upload_arquivo(
                                    arquivo_nfe_excesso_pdf, "UPLOAD_ARQUIVO_NF_EXCESSO", f"{solicitacao.id}_excesso_pdf"
                                )
                            else:
                                flash(("O arquivo PDF de excesso deve ter o tipo correto.", "warning"))
                                return redirect(url_for("cadastrar_emissao", id=solicitacao.id))
                        try:
                            dados_excesso = PedidoVendaModel.extrair_dados_nota_excesso(
                                objeto_nf_excesso_xml=objeto_nf_excesso_xml
                            )
                            
                            if not dados_excesso:
                                
                                limpar_todos_arquivos_anexados(objeto_nf_xml, objeto_nf_pdf, objeto_nf_excesso_xml, objeto_nf_excesso_pdf)
                                flash(("Não foi possível extrair dados do arquivo XML de excesso. Verifique se é um arquivo XML válido.", "warning"))
                                return redirect(url_for("cadastrar_emissao", id=solicitacao.id))
                            
                            peso_nf_excesso = dados_excesso["peso_ton_nf_excesso"]
                            numero_nota_excessao = dados_excesso["numero_nota_fiscal_excessao"]
                            peso_total_com_excesso = peso_nf + peso_nf_excesso
                            
                            
                            if peso_nf_excesso is None or peso_nf_excesso < 0 or peso_nf_excesso == "":
                                
                                limpar_todos_arquivos_anexados(objeto_nf_xml, objeto_nf_pdf, objeto_nf_excesso_xml, objeto_nf_excesso_pdf)
                                flash(("O peso extraído da nota fiscal de excesso é inválido! Entre em contato com o suporte!", "warning"))
                                db.session.rollback()
                                return redirect(url_for("cadastrar_emissao", id=solicitacao.id))
                                
                        except Exception as e:
                            limpar_todos_arquivos_anexados(objeto_nf_xml, objeto_nf_pdf, objeto_nf_excesso_xml, objeto_nf_excesso_pdf)
                            flash(("Erro ao processar os arquivos da NFe de excesso.", "warning"))
                            return redirect(url_for("cadastrar_emissao", id=solicitacao.id))

                    
                    destinatario_data_emissao = dados_nf["destinatario_data_emissao"]
                    if destinatario_data_emissao:
                        destinatario_data_emissao = DataHora.converter_data_str_br_em_objeto_date(destinatario_data_emissao)
                        
                    valor_total_nota_100 = dados_nf["valor_total_nota_100"]
                    pedido_venda = PedidoVendaModel.obter_pedido_venda_por_solicitacao_id(solicitacao.id)
                   
                    if pedido_venda:
                        # Verificar se outro registro já tem os mesmos dados (excluindo o atual)
                        conflito_numero = PedidoVendaDadosNfModel.query.filter(
                            PedidoVendaDadosNfModel.numero_nota_fiscal == dados_nf["numero_nota_fiscal"],
                            PedidoVendaDadosNfModel.pedido_venda_id != pedido_venda.id,
                            PedidoVendaDadosNfModel.ativo == True,
                            PedidoVendaDadosNfModel.deletado == False
                        ).first()
                        
                        conflito_chave = PedidoVendaDadosNfModel.query.filter(
                            PedidoVendaDadosNfModel.chave_acesso == dados_nf["chave_acesso"],
                            PedidoVendaDadosNfModel.pedido_venda_id != pedido_venda.id,
                            PedidoVendaDadosNfModel.ativo == True,
                            PedidoVendaDadosNfModel.deletado == False
                        ).first()
                        
                        if conflito_numero:
                            flash(("Erro: Número da nota fiscal já existe em outro registro.", "warning"))
                            return redirect(url_for("cadastrar_emissao", id=solicitacao.id))
                            
                        if conflito_chave:
                            flash(("Erro: Chave de acesso já existe em outro registro.", "warning"))
                            return redirect(url_for("cadastrar_emissao", id=solicitacao.id))
                        
                        # Atualizar situação do pedido
                        pedido_venda.situacao_financeira_id = 2
                        
                        # Buscar ou criar dados da NF
                        dados_nf_existente = PedidoVendaDadosNfModel.obter_dados_nf_por_pedido_venda_id(pedido_venda.id)
                        if dados_nf_existente:
                            dados_nf_existente.razao_social_emissor = dados_nf["razao_social_emissor"]
                            dados_nf_existente.numero_nota_fiscal = dados_nf["numero_nota_fiscal"]
                            dados_nf_existente.peso_ton_nf = peso_nf
                            dados_nf_existente.serie_nota = dados_nf["serie_nota"]
                            dados_nf_existente.chave_acesso = dados_nf["chave_acesso"]
                            dados_nf_existente.destinatario_nome = dados_nf["destinatario_nome"]
                            dados_nf_existente.destinatario_cnpj_cpf = dados_nf["destinatario_cnpj_cpf"]
                            dados_nf_existente.destinatario_insc_estadual = dados_nf["destinatario_insc_estadual"]
                            dados_nf_existente.destinatario_data_emissao = destinatario_data_emissao
                            dados_nf_existente.valor_total_nota_100 = valor_total_nota_100
                            dados_nf_existente.preco_un_nf = preco_un
                            dados_nf_existente.transportador_nome = dados_nf["transportador_nome"]
                            dados_nf_existente.transportador_cnpj_cpf = dados_nf["transportador_cnpj_cpf"]
                            dados_nf_existente.transportador_insc_estadual = dados_nf["transportador_insc_estadual"]
                            dados_nf_existente.placa_nf = dados_nf["placa_nf"]
                            dados_nf_existente.motorista_nf = dados_nf["motorista_nf"]
                            dados_nf_existente.arquivo_nota_id = objeto_nf_pdf.id if objeto_nf_pdf else None
                            dados_nf_existente.arquivo_nota_xml_id = objeto_nf_xml.id if objeto_nf_xml else None
                            dados_nf_existente.possui_excesso_carga = (possui_nfe_excesso == "sim")
                            
                            if possui_nfe_excesso == "sim":
                                dados_nf_existente.arquivo_nota_excesso_id = objeto_nf_excesso_pdf.id if objeto_nf_excesso_pdf else None
                                dados_nf_existente.arquivo_nota_excesso_xml_id = objeto_nf_excesso_xml.id if objeto_nf_excesso_xml else None
                                dados_nf_existente.peso_ton_nf_excesso = peso_nf_excesso if peso_nf_excesso > 0 else None
                                dados_nf_existente.peso_nf_ton_com_excecao = peso_total_com_excesso
                                dados_nf_existente.numero_nota_fiscal_excessao = numero_nota_excessao
                        else:
                            PedidoVendaDadosNfModel.criar_dados_nf(
                                pedido_venda_id=pedido_venda.id,
                                razao_social_emissor=dados_nf["razao_social_emissor"],
                                numero_nota_fiscal=dados_nf["numero_nota_fiscal"],
                                peso_ton_nf=peso_nf,
                                serie_nota=dados_nf["serie_nota"],
                                chave_acesso=dados_nf["chave_acesso"],
                                destinatario_nome=dados_nf["destinatario_nome"],
                                destinatario_cnpj_cpf=dados_nf["destinatario_cnpj_cpf"],
                                destinatario_insc_estadual=dados_nf["destinatario_insc_estadual"],
                                destinatario_data_emissao=destinatario_data_emissao,
                                valor_total_nota_100=valor_total_nota_100,
                                preco_un_nf=preco_un,
                                transportador_nome=dados_nf["transportador_nome"],
                                transportador_cnpj_cpf=dados_nf["transportador_cnpj_cpf"],
                                transportador_insc_estadual=dados_nf["transportador_insc_estadual"],
                                placa_nf=dados_nf["placa_nf"],
                                motorista_nf=dados_nf["motorista_nf"],
                                status_emissao_nf_complementar_id=2,
                                arquivo_nota_id=objeto_nf_pdf.id if objeto_nf_pdf else None,
                                arquivo_nota_xml_id=objeto_nf_xml.id if objeto_nf_xml else None,
                                possui_excesso_carga=(possui_nfe_excesso == "sim"),
                                arquivo_nota_excesso_id=objeto_nf_excesso_pdf.id if objeto_nf_excesso_pdf and possui_nfe_excesso == "sim" else None,
                                arquivo_nota_excesso_xml_id=objeto_nf_excesso_xml.id if objeto_nf_excesso_xml and possui_nfe_excesso == "sim" else None,
                                peso_ton_nf_excesso=peso_nf_excesso if peso_nf_excesso > 0 and possui_nfe_excesso == "sim" else None,
                                peso_nf_ton_com_excecao=peso_total_com_excesso if possui_nfe_excesso == "sim" else None,
                                numero_nota_fiscal_excessao=numero_nota_excessao if possui_nfe_excesso == "sim" else None
                            )
                        
                    else:
                        # Verificar se já existe registro com mesmo número de NF ou chave de acesso
                        registro_existente_nf = PedidoVendaDadosNfModel.query.filter_by(
                            numero_nota_fiscal=dados_nf["numero_nota_fiscal"],
                            ativo=True,
                            deletado=False
                        ).first()
                        
                        registro_existente_chave = PedidoVendaDadosNfModel.query.filter_by(
                            chave_acesso=dados_nf["chave_acesso"],
                            ativo=True,
                            deletado=False
                        ).first()
                        
                        if registro_existente_nf:
                            flash(("Erro: Número da nota fiscal já foi cadastrado em outra solicitação.", "warning"))
                            return redirect(url_for("cadastrar_emissao", id=solicitacao.id))
                        
                        if registro_existente_chave:
                            flash(("Erro: Chave de acesso da nota fiscal já foi cadastrada em outra solicitação.", "warning"))
                            return redirect(url_for("cadastrar_emissao", id=solicitacao.id))
                        
                        # Criar novo pedido de venda
                        pedido_venda = PedidoVendaModel.criar_pedido_venda(
                            solicitacao_pedido_venda_id=solicitacao.id,
                            situacao_financeira_id=2
                        )
                        
                        # Criar dados da NF
                        PedidoVendaDadosNfModel.criar_dados_nf(
                            pedido_venda_id=pedido_venda.id,
                            razao_social_emissor=dados_nf["razao_social_emissor"],
                            numero_nota_fiscal=dados_nf["numero_nota_fiscal"],
                            peso_ton_nf=peso_nf,
                            serie_nota=dados_nf["serie_nota"],
                            chave_acesso=dados_nf["chave_acesso"],
                            destinatario_nome=dados_nf["destinatario_nome"],
                            destinatario_cnpj_cpf=dados_nf["destinatario_cnpj_cpf"],
                            destinatario_insc_estadual=dados_nf["destinatario_insc_estadual"],
                            destinatario_data_emissao=destinatario_data_emissao,
                            valor_total_nota_100=valor_total_nota_100,
                            preco_un_nf=preco_un,
                            transportador_nome=dados_nf["transportador_nome"],
                            transportador_cnpj_cpf=dados_nf["transportador_cnpj_cpf"],
                            transportador_insc_estadual=dados_nf["transportador_insc_estadual"],
                            placa_nf=dados_nf["placa_nf"],
                            motorista_nf=dados_nf["motorista_nf"],
                            status_emissao_nf_complementar_id=2,
                            arquivo_nota_id=objeto_nf_pdf.id if objeto_nf_pdf else None,
                            arquivo_nota_xml_id=objeto_nf_xml.id if objeto_nf_xml else None,
                            possui_excesso_carga=(possui_nfe_excesso == "sim"),
                            arquivo_nota_excesso_id=objeto_nf_excesso_pdf.id if objeto_nf_excesso_pdf and possui_nfe_excesso == "sim" else None,
                            arquivo_nota_excesso_xml_id=objeto_nf_excesso_xml.id if objeto_nf_excesso_xml and possui_nfe_excesso == "sim" else None,
                            peso_ton_nf_excesso=peso_nf_excesso if peso_nf_excesso > 0 and possui_nfe_excesso == "sim" else None,
                            peso_nf_ton_com_excecao=peso_total_com_excesso if possui_nfe_excesso == "sim" else None,
                            numero_nota_fiscal_excessao=numero_nota_excessao if possui_nfe_excesso == "sim" else None
                        )
                    solicitacao.nf_emitida = True
                   
                    db.session.commit()
                    acao = TipoAcaoEnum.CADASTRO
                    PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                        current_user.id,
                        acao,
                        acao.pontos,
                        modulo='lancamento_nf'
                    )
                    
                    if possui_nfe_excesso == "sim":
                        flash((f"Nota Fiscal lançada com sucesso! Peso total: {peso_total_com_excesso} (Normal: {peso_nf} + Excesso: {peso_nf_excesso})", "success"))
                    else:
                        flash(("Nota Fiscal lançada com sucesso!", "success"))
                    return redirect(url_for("listagem_solicitacoes"))

                else:
                    flash(("É necessário enviar pelo menos um arquivo (XML ou PDF) da Nota Fiscal.", "warning"))
                    return redirect(url_for("cadastrar_emissao", id=solicitacao.id))
            except Exception as e:
                db.session.rollback()
                flash(("Erro inesperado ao processar os dados. Entre em contato com o suporte.", "warning"))
                return redirect(url_for("cadastrar_emissao", id=solicitacao.id))
    return render_template(
        "/controle_carga/lancamento_nf/lancamento_cadastrar.html",
        solicitacao=solicitacao,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
    )
    
@app.route("/controle-cargas/notas-fiscais/editar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_emissao(id):
    # Buscar pedido de venda pelo ID
    pedido_venda = PedidoVendaModel.query.filter_by(id=id, ativo=True, deletado=False).first()
    
    if not pedido_venda:
        flash(("Registro não encontrado!", "warning"))
        return redirect(url_for("listagem_solicitacoes"))
    
    # Buscar dados da NF associados
    dados_nf = PedidoVendaDadosNfModel.obter_dados_nf_por_pedido_venda_id(pedido_venda.id)
    
    if not dados_nf:
        flash(("Dados da nota fiscal não encontrados!", "warning"))
        return redirect(url_for("listagem_solicitacoes"))

    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    if request.method == "POST":
        # Captura dados FRF
        lancamentoFrf = request.form.get("lancamentoFrf")
        cargaFrf = True if lancamentoFrf == 'lancamentoFrf' else False
        
        # Campos FRF
        destinatarioFrf = request.form.get("destinatarioFrf", "")
        destinatarioNumeroDocumento = request.form.get("destinatarioNumeroDocumento", "")
        dataLancamentoFrf = request.form.get("dataLancamentoFrf", "")
        transportadorFrf = request.form.get("transportadorFrf", "")
        transportadoraNumeroDocumento = request.form.get("transportadoraNumeroDocumento", "")
        placaFrf = request.form.get("placaFrf", "")
        motoristaFrf = request.form.get("motoristaFrf", "")
        pesoFrf = request.form.get("pesoFrf", "")
        valorTotalFrf = request.form.get("valorTotalFrf", "")
        
        # Campos originais
        opcao_nf = request.form.get("opcaoNf")
        opcao_excesso = request.form.get("opcaoExcesso")
        
        arquivo_nf_nova = request.files.get("arquivoNfNova")
        arquivo_nf_nova_xml = request.files.get("arquivoNfNovaXml")
        arquivo_nf_estorno = request.files.get("arquivoNfEstorno") 
        arquivo_nf_estorno_xml = request.files.get("arquivoNfEstornoXml")
        arquivo_nfe_excesso = request.files.get("arquivoNfExcesso") 
        arquivo_nfe_excesso_xml = request.files.get("arquivoNfExcessoXml") 

        campos = {}

        if cargaFrf:
            campos["destinatarioFrf"] = ["Destinatário", destinatarioFrf]
            campos["destinatarioNumeroDocumento"] = ["CPF/CNPJ Destinatário", destinatarioNumeroDocumento]
            campos["dataLancamentoFrf"] = ["Data lançamento", dataLancamentoFrf]
            campos["transportadorFrf"] = ["Transportador", transportadorFrf]
            campos["transportadoraNumeroDocumento"] = ["CPF/CNPJ Transportador", transportadoraNumeroDocumento]
            campos["placaFrf"] = ["Placa", placaFrf]
            campos["motoristaFrf"] = ["Motorista", motoristaFrf]
            campos["pesoFrf"] = ["Peso", pesoFrf]
            campos["valorTotalFrf"] = ["Valor Total", valorTotalFrf]
        else:
            if opcao_nf == "nova":
                # XML é obrigatório para nova NF
                if not (arquivo_nf_nova_xml and arquivo_nf_nova_xml.filename):
                    campos["arquivoNfNovaXml"] = ["Arquivo NF Nova (XML)", arquivo_nf_nova_xml]
            
            if opcao_nf == "estorno":
                # XML é obrigatório para estorno de NF
                if not (arquivo_nf_estorno_xml and arquivo_nf_estorno_xml.filename):
                    campos["arquivoNfEstornoXml"] = ["Arquivo NF de Estorno (XML)", arquivo_nf_estorno_xml]
            
            if opcao_excesso == "novo":
                # XML é obrigatório para novo excesso
                if not (arquivo_nfe_excesso_xml and arquivo_nfe_excesso_xml.filename):
                    campos["arquivoNfExcessoXml"] = ["Arquivo NFe de Excesso (XML)", arquivo_nfe_excesso_xml]

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))

        if cargaFrf:
            # Validação CPF/CNPJ Destinatário
            numero_documento_destinatario = ValidaDocs.somente_numeros(destinatarioNumeroDocumento)
            if len(numero_documento_destinatario) > 11:
                valida_documento_destinatario = ValidaForms.validar_cnpj(numero_documento_destinatario)
                if not 'validado' in valida_documento_destinatario:
                    gravar_banco = False
                    validacao_campos_erros['destinatarioNumeroDocumento'] = valida_documento_destinatario.get('cnpj', 'Erro na validação do CNPJ')
            else:
                valida_documento_destinatario = ValidaForms.validar_cpf(numero_documento_destinatario)
                if not 'validado' in valida_documento_destinatario:
                    gravar_banco = False
                    validacao_campos_erros['destinatarioNumeroDocumento'] = valida_documento_destinatario.get('cpf', 'Erro na validação do CPF')

            # Validação CPF/CNPJ Transportadora
            numero_documento_transportadora = ValidaDocs.somente_numeros(transportadoraNumeroDocumento)
            if len(numero_documento_transportadora) > 11:
                valida_documento_transportadora = ValidaForms.validar_cnpj(numero_documento_transportadora)
                if not 'validado' in valida_documento_transportadora:
                    gravar_banco = False
                    validacao_campos_erros['transportadoraNumeroDocumento'] = valida_documento_transportadora.get('cnpj', 'Erro na validação do CNPJ')
            else:
                valida_documento_transportadora = ValidaForms.validar_cpf(numero_documento_transportadora)
                if not 'validado' in valida_documento_transportadora:
                    gravar_banco = False
                    validacao_campos_erros['transportadoraNumeroDocumento'] = valida_documento_transportadora.get('cpf', 'Erro na validação do CPF')

        if gravar_banco:
            if cargaFrf:
                # Processamento para FRF
                try:
                    # Preparar dados para comparação (gamificação)
                    obj1 = {
                        "destinatario_nome": dados_nf.destinatario_nome or "",
                        "destinatario_cnpj_cpf": dados_nf.destinatario_cnpj_cpf or "",
                        "destinatario_data_emissao": str(dados_nf.destinatario_data_emissao or ""),
                        "transportador_nome": dados_nf.transportador_nome or "",
                        "transportador_cnpj_cpf": dados_nf.transportador_cnpj_cpf or "",
                        "placa_nf": dados_nf.placa_nf or "",
                        "motorista_nf": dados_nf.motorista_nf or "",
                        "peso_ton_nf": float(dados_nf.peso_ton_nf or 0),
                        "valor_total_nota_100": int(dados_nf.valor_total_nota_100 or 0),
                    }

                    obj2 = {
                        "destinatario_nome": destinatarioFrf or "",
                        "destinatario_cnpj_cpf": numero_documento_destinatario or "",
                        "destinatario_data_emissao": dataLancamentoFrf or "",
                        "transportador_nome": transportadorFrf or "",
                        "transportador_cnpj_cpf": numero_documento_transportadora or "",
                        "placa_nf": placaFrf or "",
                        "motorista_nf": motoristaFrf or "",
                        "peso_ton_nf": float(pesoFrf.replace(',', '.') if pesoFrf else 0),
                        "valor_total_nota_100": int(ValoresMonetarios.converter_string_brl_para_float(valorTotalFrf) * 100 if valorTotalFrf else 0),
                    }
                    
                    # Certificação - Reverter e aplicar novo estoque
                    if pedido_venda.solicitacao.certificacao_id:
                        certificacao = CertificacoesModel.obter_certificacao_por_id_ativos_inativos(
                            pedido_venda.solicitacao.certificacao_id
                        )
                        
                        if certificacao and certificacao.ativo and not certificacao.deletado:
                            peso_anterior_total = dados_nf.peso_ton_nf or 0
                            novo_peso_frf = float(pesoFrf.replace(',', '.')) if pesoFrf else 0
                            
                            if peso_anterior_total > 0:
                                certificacao_estoque_reverter = CertificacoesModel.atualizar_estoque_positivo(
                                    peso_anterior_total, 
                                    pedido_venda.solicitacao.certificacao_id
                                )
                                if "erro" in certificacao_estoque_reverter:
                                    flash((certificacao_estoque_reverter["erro"], "warning"))
                                    db.session.rollback()
                                    return redirect(url_for("editar_emissao", id=pedido_venda.id))
                                
                                db.session.commit()
                            
                            if novo_peso_frf > 0:
                                resultado_atualizacao = CertificacoesModel.atualizar_estoque(
                                    novo_peso_frf, 
                                    pedido_venda.solicitacao.certificacao_id
                                )
                                if "erro" in resultado_atualizacao:
                                    flash((resultado_atualizacao.get("erro", "Erro ao atualizar estoque do certificado"), "warning"))
                                    db.session.rollback()
                                    return redirect(url_for("editar_emissao", id=pedido_venda.id))
                                
                                if "invalido" in resultado_atualizacao:
                                    flash((resultado_atualizacao["invalido"], "warning"))
                                    db.session.rollback()
                                    return redirect(url_for("editar_emissao", id=pedido_venda.id))

                    diferencas = Gameficacao.compara_objetos(obj1, obj2)
                    if diferencas:
                        acao = TipoAcaoEnum.EDICAO
                        PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                            current_user.id,
                            acao,
                            acao.pontos,
                            modulo='lancamento_nf'
                        )

                    # Atualizar dados da NF com valores FRF
                    dados_nf.numero_nota_fiscal = '000000'
                    dados_nf.destinatario_nome = destinatarioFrf
                    dados_nf.destinatario_cnpj_cpf = numero_documento_destinatario
                    dados_nf.destinatario_data_emissao = dataLancamentoFrf if dataLancamentoFrf else None
                    dados_nf.transportador_nome = transportadorFrf
                    dados_nf.transportador_cnpj_cpf = numero_documento_transportadora
                    dados_nf.placa_nf = placaFrf
                    dados_nf.motorista_nf = motoristaFrf
                    dados_nf.peso_ton_nf = float(pesoFrf.replace(',', '.')) if pesoFrf else None
                    dados_nf.valor_total_nota_100 = int(ValoresMonetarios.converter_string_brl_para_float(valorTotalFrf) * 100) if valorTotalFrf else None
                    dados_nf.carga_frf = True

                    # Limpar campos que não se aplicam ao FRF
                    dados_nf.razao_social_emissor = None
                    dados_nf.serie_nota = None
                    dados_nf.chave_acesso = None
                    dados_nf.destinatario_insc_estadual = None
                    dados_nf.transportador_insc_estadual = None
                    dados_nf.preco_un_nf = None
                    dados_nf.arquivo_nota_id = None
                    dados_nf.arquivo_nota_xml_id = None
                    dados_nf.possui_excesso_carga = False
                    dados_nf.arquivo_nota_excesso_id = None
                    dados_nf.arquivo_nota_excesso_xml_id = None
                    dados_nf.peso_ton_nf_excesso = None
                    dados_nf.peso_nf_ton_com_excecao = None
                    dados_nf.numero_nota_fiscal_excessao = None

                    db.session.commit()
                    flash(("FRF editado com sucesso!", "success"))
                    return redirect(url_for("listagem_solicitacoes"))

                except Exception as e:
                    db.session.rollback()
                    flash(("Erro ao processar os dados FRF. Verifique os valores informados.", "warning"))
                    return redirect(url_for("editar_emissao", id=pedido_venda.id))
            
            else:
                # Processamento para NF com XML
                peso_nf_atual = dados_nf.peso_ton_nf
                peso_excesso_atual = dados_nf.peso_ton_nf_excesso or 0
                
                
                if opcao_nf == "nova":
                    arquivo_nf_nova_pdf = arquivo_nf_nova
                    arquivo_nf_nova_xml = request.files.get("arquivoNfNovaXml")
                    
                    objeto_nf_xml = None
                    objeto_nf_pdf = None
                    
                   
                    if arquivo_nf_nova_pdf and arquivo_nf_nova_pdf.filename:
                        if arquivo_nf_nova_pdf.mimetype == "application/pdf":
                            objeto_nf_pdf = upload_arquivo(arquivo_nf_nova_pdf, "UPLOAD_ARQUIVO_NF", f"{pedido_venda.id}_nova_pdf")
                        else:
                            flash(("O arquivo PDF deve ter o tipo correto.", "warning"))
                            return redirect(url_for("editar_emissao", id=pedido_venda.id))
                    
                    
                    if arquivo_nf_nova_xml and arquivo_nf_nova_xml.filename:
                        if arquivo_nf_nova_xml.mimetype in ["application/xml", "text/xml"]:
                            try:
                                objeto_nf_xml = upload_arquivo(arquivo_nf_nova_xml, "UPLOAD_ARQUIVO_NF", f"{pedido_venda.id}_nova_xml")

                                
                                dados_nota = PedidoVendaModel.extrair_dados_nota_fiscal(objeto_nf_xml=objeto_nf_xml)

                                if not dados_nota:
                                    limpar_todos_arquivos_anexados(objeto_nf_xml=objeto_nf_xml)
                                    flash(("Arquivo XML enviado não é uma NF válida. Entre em contato com o suporte!", "warning"))
                                    return redirect(url_for("editar_emissao", id=pedido_venda.id))

                                # Extrair dados do XML
                                razao_social_emissor = dados_nota["razao_social_emissor"]
                                numero_nota = dados_nota["numero_nota_fiscal"]
                                serie = dados_nota["serie_nota"]
                                chave_acesso = dados_nota["chave_acesso"]
                                destinatario = dados_nota["destinatario_nome"]
                                destinatario_cpf_cnpj = dados_nota["destinatario_cnpj_cpf"]
                                destinatario_insc_estadual = dados_nota["destinatario_insc_estadual"]
                                destinatario_data_emissao = dados_nota["destinatario_data_emissao"]
                                valor_total_nota = dados_nota["valor_total_nota_100"]
                                transportador = dados_nota["transportador_nome"]
                                transportador_cpf_cnpj = dados_nota["transportador_cnpj_cpf"]
                                transportador_insc_estadual = dados_nota["transportador_insc_estadual"]
                                placa = dados_nota["placa_nf"]
                                motorista = dados_nota["motorista_nf"]
                                peso_nf = dados_nota["peso_ton_nf"]
                                preco_un = dados_nota["preco_un_nf"]

                                if destinatario_data_emissao:
                                    destinatario_data_emissao = DataHora.converter_data_str_br_em_objeto_date(destinatario_data_emissao)

                                # Verificar se o peso é válido
                                if peso_nf is None or peso_nf <= 0:
                                    limpar_todos_arquivos_anexados(objeto_nf_xml=objeto_nf_xml)
                                    flash(("O peso extraído da nota fiscal é inválido! Entre em contato com o suporte!", "warning"))
                                    return redirect(url_for("editar_emissao", id=pedido_venda.id))

                                
                                obj1 = {
                                    "razao_social_emissor": dados_nf.razao_social_emissor or "",
                                    "numero_nota_fiscal": dados_nf.numero_nota_fiscal or "",
                                    "serie_nota": dados_nf.serie_nota or "",
                                    "chave_acesso": dados_nf.chave_acesso or "",
                                    "destinatario_nome": dados_nf.destinatario_nome or "",
                                    "destinatario_cnpj_cpf": dados_nf.destinatario_cnpj_cpf or "",
                                    "destinatario_insc_estadual": dados_nf.destinatario_insc_estadual or "",
                                    "destinatario_data_emissao": str(dados_nf.destinatario_data_emissao or ""),
                                    "valor_total_nota_100": int(dados_nf.valor_total_nota_100 or 0),
                                    "transportador_nome": dados_nf.transportador_nome or "",
                                    "transportador_cnpj_cpf": dados_nf.transportador_cnpj_cpf or "",
                                    "transportador_insc_estadual": dados_nf.transportador_insc_estadual or "",
                                    "placa_nf": dados_nf.placa_nf or "",
                                    "motorista_nf": dados_nf.motorista_nf or "",
                                    "peso_nf": float(dados_nf.peso_ton_nf or 0),
                                }

                                obj2 = {
                                    "razao_social_emissor": razao_social_emissor or "",
                                    "numero_nota_fiscal": numero_nota or "",
                                    "serie_nota": serie or "",
                                    "chave_acesso": chave_acesso or "",
                                    "destinatario_nome": destinatario or "",
                                    "destinatario_cnpj_cpf": destinatario_cpf_cnpj or "",
                                    "destinatario_insc_estadual": destinatario_insc_estadual or "",
                                    "destinatario_data_emissao": str(destinatario_data_emissao or ""),
                                    "valor_total_nota_100": int(valor_total_nota or 0),
                                    "transportador_nome": transportador or "",
                                    "transportador_cnpj_cpf": transportador_cpf_cnpj or "",
                                    "transportador_insc_estadual": transportador_insc_estadual or "",
                                    "placa_nf": placa or "",
                                    "motorista_nf": motorista or "",
                                    "peso_nf": float(peso_nf or 0),
                                }

                                diferencas = Gameficacao.compara_objetos(obj1, obj2)
                                if diferencas:
                                    acao = TipoAcaoEnum.EDICAO
                                    PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                                        current_user.id,
                                        acao,
                                        acao.pontos,
                                        modulo='lancamento_nf'
                                    )

                                # Atualizar dados da nota principal
                                dados_nf.razao_social_emissor = razao_social_emissor or None
                                dados_nf.numero_nota_fiscal = numero_nota or None
                                dados_nf.serie_nota = serie or None
                                dados_nf.chave_acesso = chave_acesso or None
                                dados_nf.destinatario_nome = destinatario or None
                                dados_nf.destinatario_cnpj_cpf = destinatario_cpf_cnpj or None
                                dados_nf.destinatario_insc_estadual = destinatario_insc_estadual or None
                                dados_nf.destinatario_data_emissao = destinatario_data_emissao or None
                                dados_nf.valor_total_nota_100 = valor_total_nota
                                dados_nf.preco_un_nf = preco_un
                                dados_nf.transportador_nome = transportador or None
                                dados_nf.transportador_cnpj_cpf = transportador_cpf_cnpj or None
                                dados_nf.transportador_insc_estadual = transportador_insc_estadual or None
                                dados_nf.placa_nf = placa or None
                                dados_nf.motorista_nf = motorista or None
                                dados_nf.peso_ton_nf = peso_nf if peso_nf else None
                                dados_nf.carga_frf = False

                                peso_nf_atual = peso_nf

                            except Exception as e:
                                print(f"[ERRO] Erro ao processar XML da nova NF: {e}")
                                
                                # Remove o arquivo que foi feito upload em caso de erro
                                if 'objeto_nf_xml' in locals() and objeto_nf_xml:
                                    limpar_todos_arquivos_anexados(objeto_nf_xml=objeto_nf_xml)
                                        
                                flash(("Erro ao processar o arquivo XML. Verifique se é um arquivo XML válido de nota fiscal.", "warning"))
                                return redirect(url_for("editar_emissao", id=pedido_venda.id))
                        else:
                            flash(("O arquivo XML deve ter o tipo correto.", "warning"))
                            return redirect(url_for("editar_emissao", id=pedido_venda.id))
                    
                    # Atualizar as referências dos arquivos
                    if objeto_nf_xml:
                        dados_nf.arquivo_nota_xml_id = objeto_nf_xml.id
                    
                    if objeto_nf_pdf:
                        dados_nf.arquivo_nota_id = objeto_nf_pdf.id

                # ESTORNO - Processar nota fiscal de estorno
                elif opcao_nf == "estorno":
                    arquivo_nf_estorno_pdf = arquivo_nf_estorno
                    arquivo_nf_estorno_xml = request.files.get("arquivoNfEstornoXml")
                    
                    objeto_nf_estorno_xml = None
                    objeto_nf_estorno_pdf = None
                    
                    # Upload do PDF se fornecido
                    if arquivo_nf_estorno_pdf and arquivo_nf_estorno_pdf.filename:
                        if arquivo_nf_estorno_pdf.mimetype == "application/pdf":
                            objeto_nf_estorno_pdf = upload_arquivo(arquivo_nf_estorno_pdf, "UPLOAD_ARQUIVO_NF", f"{pedido_venda.id}_estorno_pdf")
                        else:
                            flash(("O arquivo PDF de estorno deve ter o tipo correto.", "warning"))
                            return redirect(url_for("editar_emissao", id=pedido_venda.id))
                    
                    # Upload e processamento do XML (obrigatório)
                    if arquivo_nf_estorno_xml and arquivo_nf_estorno_xml.filename:
                        if arquivo_nf_estorno_xml.mimetype in ["application/xml", "text/xml"]:
                            try:
                                objeto_nf_estorno_xml = upload_arquivo(arquivo_nf_estorno_xml, "UPLOAD_ARQUIVO_NF", f"{pedido_venda.id}_estorno_xml")

                                # Extrair dados do XML de estorno
                                dados_nota_estorno = PedidoVendaModel.extrair_dados_nota_fiscal(objeto_nf_xml=objeto_nf_estorno_xml)

                                if not dados_nota_estorno:
                                    limpar_todos_arquivos_anexados(objeto_nf_xml=objeto_nf_estorno_xml)
                                    flash(("Arquivo XML de estorno enviado não é uma NF válida. Entre em contato com o suporte!", "warning"))
                                    return redirect(url_for("editar_emissao", id=pedido_venda.id))

                                # Extrair dados do XML de estorno
                                razao_social_emissor_estorno = dados_nota_estorno["razao_social_emissor"]
                                numero_nota_estorno = dados_nota_estorno["numero_nota_fiscal"]
                                serie_estorno = dados_nota_estorno["serie_nota"]
                                chave_acesso_estorno = dados_nota_estorno["chave_acesso"]
                                destinatario_estorno = dados_nota_estorno["destinatario_nome"]
                                destinatario_cpf_cnpj_estorno = dados_nota_estorno["destinatario_cnpj_cpf"]
                                destinatario_insc_estadual_estorno = dados_nota_estorno["destinatario_insc_estadual"]
                                destinatario_data_emissao_estorno = dados_nota_estorno["destinatario_data_emissao"]
                                valor_total_nota_estorno = dados_nota_estorno["valor_total_nota_100"]
                                transportador_estorno = dados_nota_estorno["transportador_nome"]
                                transportador_cpf_cnpj_estorno = dados_nota_estorno["transportador_cnpj_cpf"]
                                transportador_insc_estadual_estorno = dados_nota_estorno["transportador_insc_estadual"]
                                placa_estorno = dados_nota_estorno["placa_nf"]
                                motorista_estorno = dados_nota_estorno["motorista_nf"]
                                peso_nf_estorno = dados_nota_estorno["peso_ton_nf"]
                                preco_un_estorno = dados_nota_estorno["preco_un_nf"]

                                if destinatario_data_emissao_estorno:
                                    destinatario_data_emissao_estorno = DataHora.converter_data_str_br_em_objeto_date(destinatario_data_emissao_estorno)

                                # Verificar se o peso é válido
                                if peso_nf_estorno is None or peso_nf_estorno < 0:
                                    limpar_todos_arquivos_anexados(objeto_nf_xml=objeto_nf_estorno_xml)
                                    flash(("O peso extraído da nota fiscal de estorno é inválido! Entre em contato com o suporte!", "warning"))
                                    return redirect(url_for("editar_emissao", id=pedido_venda.id))

                                # Preparar dados para gamificação
                                obj1 = {
                                    "razao_social_emissor": dados_nf.razao_social_emissor or "",
                                    "numero_nota_fiscal": dados_nf.numero_nota_fiscal or "",
                                    "serie_nota": dados_nf.serie_nota or "",
                                    "chave_acesso": dados_nf.chave_acesso or "",
                                    "destinatario_nome": dados_nf.destinatario_nome or "",
                                    "destinatario_cnpj_cpf": dados_nf.destinatario_cnpj_cpf or "",
                                    "destinatario_insc_estadual": dados_nf.destinatario_insc_estadual or "",
                                    "destinatario_data_emissao": str(dados_nf.destinatario_data_emissao or ""),
                                    "valor_total_nota_100": int(dados_nf.valor_total_nota_100 or 0),
                                    "transportador_nome": dados_nf.transportador_nome or "",
                                    "transportador_cnpj_cpf": dados_nf.transportador_cnpj_cpf or "",
                                    "transportador_insc_estadual": dados_nf.transportador_insc_estadual or "",
                                    "placa_nf": dados_nf.placa_nf or "",
                                    "motorista_nf": dados_nf.motorista_nf or "",
                                    "peso_nf": float(dados_nf.peso_ton_nf or 0),
                                }

                                obj2 = {
                                    "razao_social_emissor": razao_social_emissor_estorno or "",
                                    "numero_nota_fiscal": numero_nota_estorno or "",
                                    "serie_nota": serie_estorno or "",
                                    "chave_acesso": chave_acesso_estorno or "",
                                    "destinatario_nome": destinatario_estorno or "",
                                    "destinatario_cnpj_cpf": destinatario_cpf_cnpj_estorno or "",
                                    "destinatario_insc_estadual": destinatario_insc_estadual_estorno or "",
                                    "destinatario_data_emissao": str(destinatario_data_emissao_estorno or ""),
                                    "valor_total_nota_100": int(valor_total_nota_estorno or 0),
                                    "transportador_nome": transportador_estorno or "",
                                    "transportador_cnpj_cpf": transportador_cpf_cnpj_estorno or "",
                                    "transportador_insc_estadual": transportador_insc_estadual_estorno or "",
                                    "placa_nf": placa_estorno or "",
                                    "motorista_nf": motorista_estorno or "",
                                    "peso_nf": float(peso_nf_estorno or 0),
                                }

                                diferencas = Gameficacao.compara_objetos(obj1, obj2)
                                if diferencas:
                                    acao = TipoAcaoEnum.EDICAO
                                    PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                                        current_user.id,
                                        acao,
                                        acao.pontos,
                                        modulo='lancamento_nf'
                                    )

                                # Atualizar dados da nota com dados do estorno
                                dados_nf.razao_social_emissor = razao_social_emissor_estorno or None
                                dados_nf.numero_nota_fiscal = numero_nota_estorno or None
                                dados_nf.serie_nota = serie_estorno or None
                                dados_nf.chave_acesso = chave_acesso_estorno or None
                                dados_nf.destinatario_nome = destinatario_estorno or None
                                dados_nf.destinatario_cnpj_cpf = destinatario_cpf_cnpj_estorno or None
                                dados_nf.destinatario_insc_estadual = destinatario_insc_estadual_estorno or None
                                dados_nf.destinatario_data_emissao = destinatario_data_emissao_estorno or None
                                dados_nf.valor_total_nota_100 = valor_total_nota_estorno
                                dados_nf.preco_un_nf = preco_un_estorno
                                dados_nf.transportador_nome = transportador_estorno or None
                                dados_nf.transportador_cnpj_cpf = transportador_cpf_cnpj_estorno or None
                                dados_nf.transportador_insc_estadual = transportador_insc_estadual_estorno or None
                                dados_nf.placa_nf = placa_estorno or None
                                dados_nf.motorista_nf = motorista_estorno or None
                                dados_nf.peso_ton_nf = peso_nf_estorno if peso_nf_estorno else None
                                dados_nf.carga_frf = False

                                # Atualizar referências dos arquivos de estorno
                                if objeto_nf_estorno_xml:
                                    dados_nf.arquivo_nota_xml_id = objeto_nf_estorno_xml.id
                                
                                if objeto_nf_estorno_pdf:
                                    dados_nf.arquivo_nota_id = objeto_nf_estorno_pdf.id

                                # Limpar dados de excesso ao fazer estorno
                                dados_nf.possui_excesso_carga = False
                                dados_nf.arquivo_nota_excesso_id = None
                                dados_nf.arquivo_nota_excesso_xml_id = None
                                dados_nf.peso_ton_nf_excesso = None
                                dados_nf.peso_nf_ton_com_excecao = None
                                dados_nf.numero_nota_fiscal_excessao = None

                                peso_nf_atual = peso_nf_estorno

                            except Exception as e:
                                print(f"[ERRO] Erro ao processar XML de estorno: {e}")
                                
                                # Remove o arquivo que foi feito upload em caso de erro
                                if 'objeto_nf_estorno_xml' in locals() and objeto_nf_estorno_xml:
                                    limpar_todos_arquivos_anexados(objeto_nf_xml=objeto_nf_estorno_xml)
                                        
                                flash(("Erro ao processar o arquivo XML de estorno. Verifique se é um arquivo XML válido de nota fiscal.", "warning"))
                                return redirect(url_for("editar_emissao", id=pedido_venda.id))
                        else:
                            flash(("O arquivo XML de estorno deve ter o tipo correto.", "warning"))
                            return redirect(url_for("editar_emissao", id=pedido_venda.id))

                # Processamento de excesso de carga
                peso_excesso_final = 0

                if opcao_excesso == "nao":
                    dados_nf.possui_excesso_carga = False
                    dados_nf.arquivo_nota_excesso_id = None
                    dados_nf.arquivo_nota_excesso_xml_id = None
                    dados_nf.peso_ton_nf_excesso = None
                    dados_nf.peso_nf_ton_com_excecao = None
                    dados_nf.numero_nota_fiscal_excessao = None
                    
                elif opcao_excesso == "manter":
                    peso_excesso_final = peso_excesso_atual
                    if opcao_nf == "nova":
                        dados_nf.peso_nf_ton_com_excecao = peso_nf_atual + peso_excesso_final
                        
                elif opcao_excesso == "novo":
                    arquivo_nfe_excesso_pdf = arquivo_nfe_excesso
                    arquivo_nfe_excesso_xml = request.files.get("arquivoNfExcessoXml")
                    
                    # Verificar se foi fornecido pelo menos o XML para extração de dados
                    if not (arquivo_nfe_excesso_xml and arquivo_nfe_excesso_xml.filename):
                        flash(("Para adicionar nota de excesso, é necessário enviar o arquivo XML. O PDF é opcional.", "warning"))
                        return redirect(url_for("editar_emissao", id=pedido_venda.id))

                    objeto_nf_excesso_xml = None
                    objeto_nf_excesso_pdf = None
                    peso_excesso_final = 0
                    
                    # Upload do PDF se fornecido
                    if arquivo_nfe_excesso_pdf and arquivo_nfe_excesso_pdf.filename:
                        if arquivo_nfe_excesso_pdf.mimetype == "application/pdf":
                            objeto_nf_excesso_pdf = upload_arquivo(arquivo_nfe_excesso_pdf, "UPLOAD_ARQUIVO_NF_EXCESSO", f"{pedido_venda.id}_excesso_pdf")
                        else:
                            flash(("O arquivo PDF de excesso deve ter o tipo correto.", "warning"))
                            return redirect(url_for("editar_emissao", id=pedido_venda.id))
                    
                    # Upload e processamento do XML (obrigatório)
                    if arquivo_nfe_excesso_xml and arquivo_nfe_excesso_xml.filename:
                        if arquivo_nfe_excesso_xml.mimetype in ["application/xml", "text/xml"]:
                            try:
                                objeto_nf_excesso_xml = upload_arquivo(arquivo_nfe_excesso_xml, "UPLOAD_ARQUIVO_NF_EXCESSO", f"{pedido_venda.id}_excesso_xml")

                                # Extrair dados do XML para validação
                                dados_nota_excesso = PedidoVendaModel.extrair_dados_nota_excesso(objeto_nf_excesso_xml=objeto_nf_excesso_xml)

                                if not dados_nota_excesso:
                                    limpar_todos_arquivos_anexados(objeto_nf_excesso_xml=objeto_nf_excesso_xml)
                                    flash(("Arquivo XML de excesso enviado não é uma NF válida. Entre em contato com o suporte!", "warning"))
                                    return redirect(url_for("editar_emissao", id=pedido_venda.id))

                                peso_excesso_final = dados_nota_excesso["peso_ton_nf_excesso"]
                                numero_nota_excessao = dados_nota_excesso["numero_nota_fiscal_excessao"]
                                
                                # Verificar se o peso é válido
                                if peso_excesso_final is None or peso_excesso_final <= 0:
                                    limpar_todos_arquivos_anexados(objeto_nf_excesso_xml=objeto_nf_excesso_xml)
                                    flash(("O peso extraído da NFe de excesso é inválido! Entre em contato com o suporte!", "warning"))
                                    return redirect(url_for("editar_emissao", id=pedido_venda.id))

                                # Atualizar dados_nf
                                dados_nf.possui_excesso_carga = True
                                dados_nf.peso_ton_nf_excesso = peso_excesso_final if peso_excesso_final > 0 else None
                                dados_nf.peso_nf_ton_com_excecao = peso_nf_atual + peso_excesso_final
                                dados_nf.numero_nota_fiscal_excessao = numero_nota_excessao
                                
                                # Atualizar referências dos arquivos de excesso
                                if objeto_nf_excesso_xml:
                                    dados_nf.arquivo_nota_excesso_xml_id = objeto_nf_excesso_xml.id
                                
                                if objeto_nf_excesso_pdf:
                                    dados_nf.arquivo_nota_excesso_id = objeto_nf_excesso_pdf.id

                            except Exception as e:
                                db.session.rollback()
                                flash(("Erro ao processar o arquivo XML de excesso. Verifique se é um arquivo XML válido de nota fiscal.", "warning"))
                                return redirect(url_for("editar_emissao", id=pedido_venda.id))
                        else:
                            flash(("O arquivo XML de excesso deve ter o tipo correto.", "warning"))
                            return redirect(url_for("editar_emissao", id=pedido_venda.id))

                db.session.commit()

                if opcao_nf == "nova" and opcao_excesso == "novo":
                    flash((f"NF atualizada e NFe de excesso atualizada com sucesso! Peso total: {dados_nf.peso_nf_ton_com_excecao} (Normal: {peso_nf_atual} + Excesso: {peso_excesso_final})", "success"))
                elif opcao_nf == "nova":
                    flash(("NF atualizada com sucesso!", "success"))
                elif opcao_nf == "estorno":
                    flash(("NF de estorno processada com sucesso!", "success"))
                elif opcao_excesso == "novo":
                    flash((f"NFe de excesso atualizada com sucesso! Peso total: {dados_nf.peso_nf_ton_com_excecao} (Normal: {peso_nf_atual} + Excesso: {peso_excesso_final})", "success"))
                elif opcao_excesso == "nao":
                    flash(("NFe de excesso removida com sucesso!", "success"))
                else:
                    flash(("Emissão editada com sucesso!", "success"))
                    
                return redirect(url_for("listagem_solicitacoes"))

    dados_corretos = {}
    
    if request.method == "POST":
        dados_corretos = request.form
    else:
        dados_corretos = {
            'lancamentoFrf': 'lancamentoFrf' if dados_nf.carga_frf else '',
            'destinatarioFrf': dados_nf.destinatario_nome or '',
            'destinatarioNumeroDocumento': dados_nf.destinatario_cnpj_cpf or '',
            'dataLancamentoFrf': dados_nf.destinatario_data_emissao if dados_nf.destinatario_data_emissao else '',
            'transportadorFrf': dados_nf.transportador_nome or '',
            'transportadoraNumeroDocumento': dados_nf.transportador_cnpj_cpf or '',
            'placaFrf': dados_nf.placa_nf or '',
            'motoristaFrf': dados_nf.motorista_nf or '',
            'pesoFrf': dados_nf.peso_ton_nf,
            'valorTotalFrf': dados_nf.valor_total_nota_100,
        }

    return render_template(
        "/controle_carga/lancamento_nf/lancamento_editar.html",
        emissao=dados_nf,
        pedido_venda=pedido_venda,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=dados_corretos,
    )

