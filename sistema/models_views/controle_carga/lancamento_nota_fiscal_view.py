from sistema import app, requires_roles, db
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.controle_carga.solicitacao_nf.carga_model import CargaModel
from sistema.models_views.controle_carga.emissao_nota_fiscal_model import LancarEmissaoNotaFiscalModel
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.gerenciar.floresta.floresta_model import FlorestaModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_cadastro_model import FornecedorCadastroModel
from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.gerenciar.certificacoes.certificacoes_model import CertificacoesModel
from sistema._utilitarios import *
import os


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
                print(f"Erro ao limpar arquivo {arquivo}: {cleanup_error}")
    
    try:
        db.session.commit()
    except Exception as e:
        print(f"Erro ao commitar remoção de arquivos: {e}")
        db.session.rollback()

@app.route("/controle-cargas/notas-fiscais/detalhe/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def visualizar_emissao(id):
    emissao = LancarEmissaoNotaFiscalModel.obter_emissao_por_id(id)
    return render_template(
        "/controle_carga/lancamento_nf/lancamento_visualizar.html", emissao=emissao
    )

@app.route("/controle-cargas/notas-fiscais/lancar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def cadastrar_emissao(id):
    solicitacao = CargaModel.obter_solicitacao_por_id(id)
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
        print(f"[DEBUG] Iniciando processamento POST para solicitação: {id}")
        
        arquivo_nf_xml = request.files.get("arquivoNfXml")
        arquivo_nf_pdf = request.files.get("arquivoNfPdf")
        possui_nfe_excesso = request.form.get("possuiNFeExcesso", "nao")
        arquivo_nfe_excesso_xml = request.files.get("arquivoNFeExcessoXml") if possui_nfe_excesso == "sim" else None
        arquivo_nfe_excesso_pdf = request.files.get("arquivoNFeExcessoPdf") if possui_nfe_excesso == "sim" else None
        lancamentoFrf = request.form.get("lancamentoFrf")
        cargaFrf = True if lancamentoFrf == 'lancamentoFrf' else False

        print(f"[DEBUG] Parâmetros recebidos:")
        print(f"  - cargaFrf: {cargaFrf}")
        print(f"  - possui_nfe_excesso: {possui_nfe_excesso}")
        print(f"  - arquivo_nf_xml: {arquivo_nf_xml.filename if arquivo_nf_xml else None}")
        print(f"  - arquivo_nf_pdf: {arquivo_nf_pdf.filename if arquivo_nf_pdf else None}")

        campos = {}
        if cargaFrf:
            print(f"[DEBUG] Extraindo dados FRF do formulário...")
            dados_frf = RegistroOperacionalModel.extrair_dados_frf_form(request)
            print(f"[DEBUG] Dados FRF extraídos: {dados_frf is not None}")
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
        print(f"[DEBUG] Validação campos obrigatórios - resultado: {validacao_campos_obrigatorios}")
        if not "validado" in validacao_campos_obrigatorios:
            print(f"[DEBUG] Campos obrigatórios falharam, não gravando no banco")
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))

        validacao_campos_erros = {}
        if cargaFrf:
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
                print(f"[DEBUG] Iniciando processamento - Solicitação ID: {solicitacao.id}")
                print(f"[DEBUG] Tipo de processamento - cargaFrf: {cargaFrf}")
                print(f"[DEBUG] gravar_banco: {gravar_banco}")
                
                if cargaFrf:
                    print(f"[DEBUG] Processando FRF - dados_frf keys: {list(dados_frf.keys()) if 'dados_frf' in locals() else 'N/A'}")
                    # Conversão dos campos
                    try:
                        print(f"[DEBUG] Convertendo peso: {dados_frf['peso_ton_nf']}")
                        pesoFrf_float = float(str(dados_frf["peso_ton_nf"]).replace(',', '.') if dados_frf["peso_ton_nf"] else 0)
                        print(f"[DEBUG] Peso convertido: {pesoFrf_float}")
                        
                        print(f"[DEBUG] Convertendo valor: {dados_frf['valor_total_nota_100']}")
                        valorTotalFrf_100 = int(ValoresMonetarios.converter_string_brl_para_float(dados_frf["valor_total_nota_100"]) * 100) if dados_frf["valor_total_nota_100"] else 0
                        print(f"[DEBUG] Valor convertido: {valorTotalFrf_100}")
                    except Exception as conv_error:
                        print(f"[ERRO] Erro na conversão de valores FRF: {conv_error}")
                        raise
                    print(f"[DEBUG] Buscando registro operacional para solicitação: {solicitacao.id}")
                    obterRegistro = RegistroOperacionalModel.obter_registro_solicitacao_por_id(solicitacao.id)
                    
                    # Certificação - Atualiza o estoque da certificação associada à carga
                    resultado_atualizacao = CertificacoesModel.atualizar_estoque(pesoFrf_float, solicitacao.certificacao_id)
                    if "erro" in resultado_atualizacao or "invalido" in resultado_atualizacao:
                        if "invalido" in resultado_atualizacao:
                            flash((resultado_atualizacao["invalido"], "warning"))
                        elif "erro" in resultado_atualizacao:
                            flash((resultado_atualizacao["erro"], "warning"))
                        db.session.rollback()
                        return redirect(url_for("cadastrar_emissao", id=solicitacao.id))
                    
                    if obterRegistro:
                        obterRegistro.solicitacao_nf_id = solicitacao.id
                        obterRegistro.numero_nota_fiscal = '000000'
                        obterRegistro.peso_ton_nf = pesoFrf_float
                        obterRegistro.destinatario_nome = dados_frf["destinatario_nome"]
                        obterRegistro.destinatario_cnpj_cpf = numero_documento_destinatario
                        obterRegistro.valor_total_nota_100 = valorTotalFrf_100
                        obterRegistro.transportador_nome = dados_frf["transportador_nome"]
                        obterRegistro.transportador_cnpj_cpf = numero_documento_transportadora
                        obterRegistro.placa_nf = dados_frf["placa_nf"]
                        obterRegistro.motorista_nf = dados_frf["motorista_nf"]
                        obterRegistro.carga_frf = True
                        obterRegistro.situacao_financeira_id = 2
                        obterRegistro.destinatario_data_emissao = dados_frf["destinatario_data_emissao"]
                        obterRegistro.ativo = True
                    else:
                        RegistroOperacionalModel.criar_registro_operacional(
                            solicitacao_nf_id=solicitacao.id,
                            peso_ton_nf=pesoFrf_float,
                            destinatario_nome=dados_frf["destinatario_nome"],
                            destinatario_cnpj_cpf=numero_documento_destinatario,
                            valor_total_nota_100=valorTotalFrf_100,
                            transportador_nome=dados_frf["transportador_nome"],
                            transportador_cnpj_cpf=numero_documento_transportadora,
                            placa_nf=dados_frf["placa_nf"],
                            motorista_nf=dados_frf["motorista_nf"],
                            destinatario_data_emissao=dados_frf["destinatario_data_emissao"],
                            carga_frf=True,
                            situacao_financeira_id=2,
                            ativo=True,
                            numero_nota_fiscal='000000',
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
                    print(f"[DEBUG] Processando NF - XML: {bool(arquivo_nf_xml and arquivo_nf_xml.filename)}, PDF: {bool(arquivo_nf_pdf and arquivo_nf_pdf.filename)}")
                    print(f"[DEBUG] possui_nfe_excesso: {possui_nfe_excesso}")
                    
                    objeto_nf_xml = None
                    objeto_nf_pdf = None
                    
                    if arquivo_nf_xml and arquivo_nf_xml.filename:
                        print(f"[DEBUG] Processando arquivo XML: {arquivo_nf_xml.filename}, mimetype: {arquivo_nf_xml.mimetype}")
                        if arquivo_nf_xml.mimetype in ["application/xml", "text/xml"]:
                            print(f"[DEBUG] Fazendo upload do arquivo XML...")
                            objeto_nf_xml = upload_arquivo(
                                arquivo_nf_xml, "UPLOAD_ARQUIVO_NF", f"{solicitacao.id}_xml"
                            )
                            print(f"[DEBUG] Upload XML concluído, ID: {objeto_nf_xml.id if objeto_nf_xml else 'ERRO'}")
                        else:
                            print(f"[ERRO] Tipo MIME inválido para XML: {arquivo_nf_xml.mimetype}")
                            flash(("O arquivo XML deve ter o tipo correto.", "warning"))
                            return redirect(url_for("cadastrar_emissao", id=solicitacao.id))
                    
                    if arquivo_nf_pdf and arquivo_nf_pdf.filename:
                        print(f"[DEBUG] Processando arquivo PDF: {arquivo_nf_pdf.filename}, mimetype: {arquivo_nf_pdf.mimetype}")
                        if arquivo_nf_pdf.mimetype == "application/pdf":
                            print(f"[DEBUG] Fazendo upload do arquivo PDF...")
                            objeto_nf_pdf = upload_arquivo(
                                arquivo_nf_pdf, "UPLOAD_ARQUIVO_NF", f"{solicitacao.id}_pdf"
                            )
                            print(f"[DEBUG] Upload PDF concluído, ID: {objeto_nf_pdf.id if objeto_nf_pdf else 'ERRO'}")
                        else:
                            print(f"[ERRO] Tipo MIME inválido para PDF: {arquivo_nf_pdf.mimetype}")
                            flash(("O arquivo PDF deve ter o tipo correto.", "warning"))
                            return redirect(url_for("cadastrar_emissao", id=solicitacao.id))
                    
                    
                    try:
                        print(f"[DEBUG] Extraindo dados da NF - objeto_nf_xml: {objeto_nf_xml is not None}")
                        
                        dados_nf = RegistroOperacionalModel.extrair_dados_nota_fiscal(
                            objeto_nf_xml=objeto_nf_xml
                        )
                        print(f"[DEBUG] Dados extraídos com sucesso: {dados_nf is not None}")
                        
                        if dados_nf:
                            print(f"[DEBUG] Dados extraídos da NF:")
                            print(f"  - numero_nota_fiscal: {dados_nf.get('numero_nota_fiscal')}")
                            print(f"  - chave_acesso: {dados_nf.get('chave_acesso')}")
                            print(f"  - razao_social_emissor: {dados_nf.get('razao_social_emissor')}")
                            print(f"  - peso_ton_nf: {dados_nf.get('peso_ton_nf')}")
                            print(f"  - valor_total_nota_100: {dados_nf.get('valor_total_nota_100')}")
                        
                        if not dados_nf:
                            
                            limpar_todos_arquivos_anexados(objeto_nf_xml, objeto_nf_pdf)
                            flash(("Não foi possível extrair dados do arquivo XML. Verifique se é um arquivo XML válido.", "warning"))
                            return redirect(url_for("cadastrar_emissao", id=solicitacao.id))
                        
                        peso_nf = dados_nf["peso_ton_nf"]
                        preco_un = dados_nf["preco_un_nf"]
                        
                        print(f"[DEBUG] Peso NF extraído: {peso_nf}")
                        print(f"[DEBUG] Preço unitário extraído: {preco_un}")
                        
                        if peso_nf is None or peso_nf < 0 or peso_nf == "":
                            print(f"[ERRO] Peso inválido detectado: {peso_nf}")
                            
                            limpar_todos_arquivos_anexados(objeto_nf_xml, objeto_nf_pdf)
                            flash(("O peso extraído da nota fiscal é inválido! Entre em contato com o suporte!", "warning"))
                            return redirect(url_for("cadastrar_emissao", id=solicitacao.id))
                            
                    except Exception as e:
                        print(f"[ERRO] Erro ao extrair dados da NF: {e}")
                        
                        limpar_todos_arquivos_anexados(objeto_nf_xml, objeto_nf_pdf)
                        flash(("O XML da nota fiscal apresentou inconsistências ou está em formato inválido. Por favor, revise o arquivo e envie novamente.", "warning"))
                        return redirect(url_for("cadastrar_emissao", id=solicitacao.id))

                    objeto_nf_excesso_xml = None
                    objeto_nf_excesso_pdf = None
                    numero_nota_excessao = None
                    peso_nf_excesso = 0
                    peso_total_com_excesso = peso_nf
                    
                    if possui_nfe_excesso == "sim" and ((arquivo_nfe_excesso_xml and arquivo_nfe_excesso_xml.filename) or (arquivo_nfe_excesso_pdf and arquivo_nfe_excesso_pdf.filename)):
                        print(f"[DEBUG] Processando NFe de excesso...")
                        
                        if arquivo_nfe_excesso_xml and arquivo_nfe_excesso_xml.filename:
                            print(f"[DEBUG] Processando XML de excesso: {arquivo_nfe_excesso_xml.filename}")
                            if arquivo_nfe_excesso_xml.mimetype in ["application/xml", "text/xml"]:
                                objeto_nf_excesso_xml = upload_arquivo(
                                    arquivo_nfe_excesso_xml, "UPLOAD_ARQUIVO_NF_EXCESSO", f"{solicitacao.id}_excesso_xml"
                                )
                                print(f"[DEBUG] Upload XML excesso concluído, ID: {objeto_nf_excesso_xml.id if objeto_nf_excesso_xml else 'ERRO'}")
                            else:
                                print(f"[ERRO] Tipo MIME inválido para XML de excesso: {arquivo_nfe_excesso_xml.mimetype}")
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
                            dados_excesso = RegistroOperacionalModel.extrair_dados_nota_excesso(
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
                            print(f"[ERRO] Erro ao extrair dados da NFe de excesso: {e}")
                            
                            limpar_todos_arquivos_anexados(objeto_nf_xml, objeto_nf_pdf, objeto_nf_excesso_xml, objeto_nf_excesso_pdf)
                            flash(("Erro ao processar os arquivos da NFe de excesso.", "warning"))
                            return redirect(url_for("cadastrar_emissao", id=solicitacao.id))

                    
                    destinatario_data_emissao = dados_nf["destinatario_data_emissao"]
                    if destinatario_data_emissao:
                        destinatario_data_emissao = DataHora.converter_data_str_br_em_objeto_date(destinatario_data_emissao)
                        
                    
                    valor_total_nota_100 = dados_nf["valor_total_nota_100"]

                    
                    print(f"[DEBUG] Buscando registro operacional para atualização - Solicitação: {solicitacao.id}")
                    obterRegistro = RegistroOperacionalModel.obter_registro_solicitacao_por_id(solicitacao.id)
                    print(f"[DEBUG] Registro para atualização encontrado: {obterRegistro is not None}")
                    if obterRegistro:
                        print(f"[DEBUG] Atualizando registro existente - ID: {obterRegistro.id}")
                        print(f"[DEBUG] Verificando duplicatas antes da atualização:")
                        print(f"  - Novo número NF: {dados_nf['numero_nota_fiscal']}")
                        print(f"  - Nova chave de acesso: {dados_nf['chave_acesso']}")
                        
                        # Verificar se outro registro já tem os mesmos dados (excluindo o atual)
                        conflito_numero = RegistroOperacionalModel.query.filter(
                            RegistroOperacionalModel.numero_nota_fiscal == dados_nf["numero_nota_fiscal"],
                            RegistroOperacionalModel.id != obterRegistro.id
                        ).first()
                        
                        conflito_chave = RegistroOperacionalModel.query.filter(
                            RegistroOperacionalModel.chave_acesso == dados_nf["chave_acesso"],
                            RegistroOperacionalModel.id != obterRegistro.id
                        ).first()
                        
                        print(f"[DEBUG] Conflitos na atualização:")
                        print(f"  - Conflito número NF: {conflito_numero is not None}")
                        print(f"  - Conflito chave de acesso: {conflito_chave is not None}")
                        
                        if conflito_numero:
                            print(f"[ERRO] Conflito: outro registro já tem número NF {dados_nf['numero_nota_fiscal']} - ID: {conflito_numero.id}")
                            flash(("Erro: Número da nota fiscal já existe em outro registro.", "warning"))
                            return redirect(url_for("cadastrar_emissao", id=solicitacao.id))
                            
                        if conflito_chave:
                            print(f"[ERRO] Conflito: outro registro já tem chave de acesso {dados_nf['chave_acesso']} - ID: {conflito_chave.id}")
                            flash(("Erro: Chave de acesso já existe em outro registro.", "warning"))
                            return redirect(url_for("cadastrar_emissao", id=solicitacao.id))
                        
                        obterRegistro.solicitacao_nf_id = solicitacao.id
                        obterRegistro.floresta_id = None
                        obterRegistro.fornecedor_id = None
                        obterRegistro.razao_social_emissor = dados_nf["razao_social_emissor"]
                        obterRegistro.numero_nota_fiscal = dados_nf["numero_nota_fiscal"]
                        obterRegistro.peso_ton_nf = peso_nf
                        obterRegistro.serie_nota = dados_nf["serie_nota"]
                        obterRegistro.chave_acesso = dados_nf["chave_acesso"]
                        obterRegistro.destinatario_nome = dados_nf["destinatario_nome"]
                        obterRegistro.destinatario_cnpj_cpf = dados_nf["destinatario_cnpj_cpf"]
                        obterRegistro.destinatario_insc_estadual = dados_nf["destinatario_insc_estadual"]
                        obterRegistro.destinatario_data_emissao = destinatario_data_emissao
                        obterRegistro.valor_total_nota_100 = valor_total_nota_100
                        obterRegistro.preco_un_nf = preco_un
                        obterRegistro.transportador_nome = dados_nf["transportador_nome"]
                        obterRegistro.transportador_cnpj_cpf = dados_nf["transportador_cnpj_cpf"]
                        obterRegistro.transportador_insc_estadual = dados_nf["transportador_insc_estadual"]
                        obterRegistro.placa_nf = dados_nf["placa_nf"]
                        obterRegistro.motorista_nf = dados_nf["motorista_nf"]
                        obterRegistro.arquivo_nota_id = objeto_nf_pdf.id if objeto_nf_pdf else None  # PDF
                        obterRegistro.arquivo_nota_xml_id = objeto_nf_xml.id if objeto_nf_xml else None  # XML
                        obterRegistro.possui_excesso_carga = (possui_nfe_excesso == "sim")
                        obterRegistro.situacao_financeira_id = 2
                        
                        if possui_nfe_excesso == "sim":
                            obterRegistro.arquivo_nota_excesso_id = objeto_nf_excesso_pdf.id if objeto_nf_excesso_pdf else None  # PDF excesso
                            obterRegistro.arquivo_nota_excesso_xml_id = objeto_nf_excesso_xml.id if objeto_nf_excesso_xml else None  # XML excesso
                            obterRegistro.peso_ton_nf_excesso = peso_nf_excesso if peso_nf_excesso > 0 else None
                            obterRegistro.peso_nf_ton_com_excecao = peso_total_com_excesso
                            obterRegistro.numero_nota_fiscal_excessao = numero_nota_excessao
                        obterRegistro.ativo = True
                        
                    else:
                        print(f"[DEBUG] Criando novo registro operacional para solicitação: {solicitacao.id}")
                        print(f"[DEBUG] Dados para criação:")
                        print(f"  - numero_nota_fiscal: {dados_nf['numero_nota_fiscal']}")
                        print(f"  - chave_acesso: {dados_nf['chave_acesso']}")
                        print(f"  - razao_social_emissor: {dados_nf['razao_social_emissor']}")
                        print(f"  - destinatario_cnpj_cpf: {dados_nf['destinatario_cnpj_cpf']}")
                        
                        # Verificar se já existe registro com mesmo número de NF ou chave de acesso
                        print(f"[DEBUG] Verificando duplicatas ANTES de criar registro...")
                        
                        registro_existente_nf = RegistroOperacionalModel.query.filter_by(
                            numero_nota_fiscal=dados_nf["numero_nota_fiscal"],
                            ativo = True,
                            deletado = False
                        ).first()
                        
                        registro_existente_chave = RegistroOperacionalModel.query.filter_by(
                            chave_acesso=dados_nf["chave_acesso"],
                            ativo = True,
                            deletado = False
                        ).first()
                        
                        print(f"[DEBUG] Verificação de duplicatas:")
                        print(f"  - Registro com mesmo número NF: {registro_existente_nf is not None}")
                        print(f"  - Registro com mesma chave de acesso: {registro_existente_chave is not None}")
                        
                        if registro_existente_nf:
                            print(f"[AVISO] Já existe registro com número NF {dados_nf['numero_nota_fiscal']} - ID: {registro_existente_nf.id}")
                            print(f"[AVISO] Solicitação existente: {registro_existente_nf.solicitacao_nf_id}")
                            print(f"[AVISO] Ativo: {registro_existente_nf.ativo}")
                            
                            # Se o registro existente é da mesma solicitação, atualizar ao invés de criar
                            if registro_existente_nf.solicitacao_nf_id == solicitacao.id:
                                print(f"[DEBUG] Atualizando registro existente da mesma solicitação")
                                obterRegistro = registro_existente_nf
                            else:
                                flash(("Erro: Número da nota fiscal já foi cadastrado em outra solicitação.", "warning"))
                                return redirect(url_for("cadastrar_emissao", id=solicitacao.id))
                        
                        elif registro_existente_chave:
                            print(f"[AVISO] Já existe registro com chave de acesso {dados_nf['chave_acesso']} - ID: {registro_existente_chave.id}")
                            print(f"[AVISO] Solicitação existente: {registro_existente_chave.solicitacao_nf_id}")
                            
                            # Se o registro existente é da mesma solicitação, atualizar ao invés de criar
                            if registro_existente_chave.solicitacao_nf_id == solicitacao.id:
                                print(f"[DEBUG] Atualizando registro existente da mesma solicitação")
                                obterRegistro = registro_existente_chave
                            else:
                                flash(("Erro: Chave de acesso da nota fiscal já foi cadastrada em outra solicitação.", "warning"))
                                return redirect(url_for("cadastrar_emissao", id=solicitacao.id))
                        
                        # Se não encontrou duplicatas, buscar registro normal da solicitação
                        if not obterRegistro:
                            obterRegistro = RegistroOperacionalModel.obter_registro_solicitacao_por_id(solicitacao.id)
                        
                        print(f"[DEBUG] Registro para processamento: {obterRegistro is not None}")
                        if obterRegistro:
                            print(f"[DEBUG] Atualizando registro existente - ID: {obterRegistro.id}")
                            obterRegistro.solicitacao_nf_id = solicitacao.id
                            obterRegistro.floresta_id = None
                            obterRegistro.fornecedor_id = None
                            obterRegistro.razao_social_emissor = dados_nf["razao_social_emissor"]
                            obterRegistro.numero_nota_fiscal = dados_nf["numero_nota_fiscal"]
                            obterRegistro.peso_ton_nf = peso_nf
                            obterRegistro.serie_nota = dados_nf["serie_nota"]
                            obterRegistro.chave_acesso = dados_nf["chave_acesso"]
                            obterRegistro.destinatario_nome = dados_nf["destinatario_nome"]
                            obterRegistro.destinatario_cnpj_cpf = dados_nf["destinatario_cnpj_cpf"]
                            obterRegistro.destinatario_insc_estadual = dados_nf["destinatario_insc_estadual"]
                            obterRegistro.destinatario_data_emissao = destinatario_data_emissao
                            obterRegistro.valor_total_nota_100 = valor_total_nota_100
                            obterRegistro.preco_un_nf = preco_un
                            obterRegistro.transportador_nome = dados_nf["transportador_nome"]
                            obterRegistro.transportador_cnpj_cpf = dados_nf["transportador_cnpj_cpf"]
                            obterRegistro.transportador_insc_estadual = dados_nf["transportador_insc_estadual"]
                            obterRegistro.placa_nf = dados_nf["placa_nf"]
                            obterRegistro.motorista_nf = dados_nf["motorista_nf"]
                            obterRegistro.arquivo_nota_id = objeto_nf_pdf.id if objeto_nf_pdf else None  # PDF
                            obterRegistro.arquivo_nota_xml_id = objeto_nf_xml.id if objeto_nf_xml else None  # XML
                            obterRegistro.possui_excesso_carga = (possui_nfe_excesso == "sim")
                            obterRegistro.situacao_financeira_id = 2
                            
                            if possui_nfe_excesso == "sim":
                                obterRegistro.arquivo_nota_excesso_id = objeto_nf_excesso_pdf.id if objeto_nf_excesso_pdf else None  # PDF excesso
                                obterRegistro.arquivo_nota_excesso_xml_id = objeto_nf_excesso_xml.id if objeto_nf_excesso_xml else None  # XML excesso
                                obterRegistro.peso_ton_nf_excesso = peso_nf_excesso if peso_nf_excesso > 0 else None
                                obterRegistro.peso_nf_ton_com_excecao = peso_total_com_excesso
                                obterRegistro.numero_nota_fiscal_excessao = numero_nota_excessao
                            obterRegistro.ativo = True
                            
                        else:
                            print(f"[DEBUG] Criando novo registro operacional para solicitação: {solicitacao.id}")
                            RegistroOperacionalModel.criar_registro_operacional(
                            solicitacao_nf_id=solicitacao.id,
                            floresta_id=None,
                            fornecedor_id=None,
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
                            arquivo_nota_id=objeto_nf_pdf.id if objeto_nf_pdf else None,  # PDF
                            arquivo_nota_xml_id=objeto_nf_xml.id if objeto_nf_xml else None,  # XML
                            status_emissao_nf_complementar_id=2,
                            situacao_financeira_id=2,
                            possui_excesso_carga=(possui_nfe_excesso == "sim"),
                            arquivo_nota_excesso_id=objeto_nf_excesso_pdf.id if objeto_nf_excesso_pdf and possui_nfe_excesso == "sim" else None,  # PDF excesso
                            arquivo_nota_excesso_xml_id=objeto_nf_excesso_xml.id if objeto_nf_excesso_xml and possui_nfe_excesso == "sim" else None,  # XML excesso
                            peso_ton_nf_excesso=peso_nf_excesso if peso_nf_excesso > 0 and possui_nfe_excesso == "sim" else None,
                            peso_nf_ton_com_excecao=peso_total_com_excesso if possui_nfe_excesso == "sim" else None,
                            numero_nota_fiscal_excessao=numero_nota_excessao if possui_nfe_excesso == "sim" else None,
                            ativo=True,
                        )

                    
                    print(f"[DEBUG] Marcando solicitação como NF emitida - ID: {solicitacao.id}")
                    solicitacao.nf_emitida = True
                    print(f"[DEBUG] Iniciando commit da transação")
                    db.session.commit()
                    print(f"[DEBUG] Commit realizado com sucesso")
                    
                    
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
                print(f"[ERRO] Erro geral ao tentar lançar NF: {e}")
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

@app.route("/controle-cargas/notas-fiscais/lancadas", methods=["GET", "POST"])
@login_required
@requires_roles
def listar_emissoes():
    emissoes = LancarEmissaoNotaFiscalModel.listar_emissoes()
    if request.method == "POST":
        emissoes = LancarEmissaoNotaFiscalModel.filtrar_emissoes(
            motorista_nf=request.form.get("motoristaNf"),
            nome_cliente=request.form.get("nomeCliente"),
            numero_nf=request.form.get("numeroNf"),
            placa_nf=request.form.get("placaNf"),
            placa_solicitacao=request.form.get("placaSolicitacao"),
        )
    else:
        emissoes = LancarEmissaoNotaFiscalModel.listar_emissoes()
    return render_template(
        "/controle_carga/lancamento_nf/lancamentos_listar.html",
        emissoes=emissoes,
        dados_corretos=request.form,
    )


@app.route("/controle-cargas/notas-fiscais/editar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_emissao(id):
    registro = RegistroOperacionalModel.obter_por_id(id)

    if not registro:
        flash(("Registro não encontrado!", "warning"))
        return redirect(url_for("listar_emissoes"))

    florestas = FlorestaModel.listar_florestas_ativas()
    fornecedores = FornecedorCadastroModel.listar_fornecedores_ativos()

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
                        "destinatario_nome": registro.destinatario_nome or "",
                        "destinatario_cnpj_cpf": registro.destinatario_cnpj_cpf or "",
                        "destinatario_data_emissao": str(registro.destinatario_data_emissao or ""),
                        "transportador_nome": registro.transportador_nome or "",
                        "transportador_cnpj_cpf": registro.transportador_cnpj_cpf or "",
                        "placa_nf": registro.placa_nf or "",
                        "motorista_nf": registro.motorista_nf or "",
                        "peso_ton_nf": float(registro.peso_ton_nf or 0),
                        "valor_total_nota_100": int(registro.valor_total_nota_100 or 0),
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
                    
                    if registro.solicitacao.certificacao_id:
                        certificacao = CertificacoesModel.obter_certificacao_por_id_ativos_inativos(registro.solicitacao.certificacao_id)
                        
                        if certificacao and certificacao.ativo and not certificacao.deletado:
                            peso_anterior_total = registro.peso_ton_nf or 0
                            novo_peso_frf = float(pesoFrf.replace(',', '.')) if pesoFrf else 0
                            
                            if peso_anterior_total > 0:
                                certificacao_estoque_reverter = CertificacoesModel.atualizar_estoque_positivo(
                                    peso_anterior_total, 
                                    registro.solicitacao.certificacao_id
                                )
                                if "erro" in certificacao_estoque_reverter:
                                    flash((certificacao_estoque_reverter["erro"], "warning"))
                                    db.session.rollback()
                                    return redirect(url_for("editar_emissao", id=registro.id))
                                
                                db.session.commit()
                            
                            if novo_peso_frf > 0:
                                resultado_atualizacao = CertificacoesModel.atualizar_estoque(
                                    novo_peso_frf, 
                                    registro.solicitacao.certificacao_id
                                )
                                if "erro" in resultado_atualizacao:
                                    flash((resultado_atualizacao.get("erro", "Erro ao atualizar estoque do certificado"), "warning"))
                                    db.session.rollback()
                                    return redirect(url_for("editar_emissao", id=registro.id))
                                
                                if "invalido" in resultado_atualizacao:
                                    flash((resultado_atualizacao["invalido"], "warning"))
                                    db.session.rollback()
                                    return redirect(url_for("editar_emissao", id=registro.id))

                    diferencas = Gameficacao.compara_objetos(obj1, obj2)
                    if diferencas:
                        acao = TipoAcaoEnum.EDICAO
                        PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                            current_user.id,
                            acao,
                            acao.pontos,
                            modulo='lancamento_nf'
                        )

                    # Atualizar registro com dados FRF
                    registro.destinatario_nome = destinatarioFrf
                    registro.destinatario_cnpj_cpf = numero_documento_destinatario
                    registro.destinatario_data_emissao = dataLancamentoFrf if dataLancamentoFrf else None
                    registro.transportador_nome = transportadorFrf
                    registro.transportador_cnpj_cpf = numero_documento_transportadora
                    registro.placa_nf = placaFrf
                    registro.motorista_nf = motoristaFrf
                    registro.peso_ton_nf = pesoFrf.replace(',', '.') if pesoFrf else None
                    registro.valor_total_nota_100 = ValoresMonetarios.converter_string_brl_para_float(valorTotalFrf) * 100 if valorTotalFrf else None
                    registro.carga_frf = True
                    registro.numero_nota_fiscal = '000000'

                    # Limpar campos que não se aplicam ao FRF
                    registro.razao_social_emissor = None
                    registro.serie_nota = None
                    registro.chave_acesso = None
                    registro.destinatario_insc_estadual = None
                    registro.transportador_insc_estadual = None
                    registro.arquivo_nota_id = None
                    registro.possui_excesso_carga = False
                    registro.arquivo_nota_excesso_id = None
                    registro.peso_ton_nf_excesso = None
                    registro.peso_nf_ton_com_excecao = None
                    registro.numero_nota_fiscal_excessao = None
                    registro.estorno_nf = False
                    registro.arquivo_nota_estorno_id = None
                    registro.numero_nota_fiscal_estorno = None

                    db.session.commit()
                    flash(("FRF editado com sucesso!", "success"))
                    return redirect(url_for("listagem_registros_operacionais"))

                except Exception as e:
                    print(f"[ERRO] Erro ao editar FRF: {e}")
                    flash(("Erro ao processar os dados FRF. Verifique os valores informados.", "warning"))
                    return redirect(url_for("editar_emissao", id=registro.id))
            
            else:
                # Processamento original para NF (código existente)
                peso_nf_atual = registro.peso_ton_nf
                peso_excesso_atual = registro.peso_ton_nf_excesso or 0
                
                
                if opcao_nf == "nova":
                    arquivo_nf_nova_pdf = arquivo_nf_nova
                    arquivo_nf_nova_xml = request.files.get("arquivoNfNovaXml")
                    
                    objeto_nf_xml = None
                    objeto_nf_pdf = None
                    
                   
                    if arquivo_nf_nova_pdf and arquivo_nf_nova_pdf.filename:
                        if arquivo_nf_nova_pdf.mimetype == "application/pdf":
                            objeto_nf_pdf = upload_arquivo(arquivo_nf_nova_pdf, "UPLOAD_ARQUIVO_NF", f"{registro.id}_nova_pdf")
                        else:
                            flash(("O arquivo PDF deve ter o tipo correto.", "warning"))
                            return redirect(url_for("editar_emissao", id=registro.id))
                    
                    
                    if arquivo_nf_nova_xml and arquivo_nf_nova_xml.filename:
                        if arquivo_nf_nova_xml.mimetype in ["application/xml", "text/xml"]:
                            try:
                                objeto_nf_xml = upload_arquivo(arquivo_nf_nova_xml, "UPLOAD_ARQUIVO_NF", f"{registro.id}_nova_xml")

                                
                                dados_nota = RegistroOperacionalModel.extrair_dados_nota_fiscal(objeto_nf_xml=objeto_nf_xml)

                                if not dados_nota:
                                    
                                    if objeto_nf_xml and hasattr(objeto_nf_xml, 'caminho') and os.path.exists(objeto_nf_xml.caminho):
                                        os.remove(objeto_nf_xml.caminho)
                                    if objeto_nf_xml:
                                        db.session.delete(objeto_nf_xml)
                                        db.session.commit()
                                    
                                    flash(("Arquivo XML enviado não é uma NF válida. Entre em contato com o suporte!", "warning"))
                                    return redirect(url_for("editar_emissao", id=registro.id))

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
                                    
                                    if objeto_nf_xml and hasattr(objeto_nf_xml, 'caminho') and os.path.exists(objeto_nf_xml.caminho):
                                        os.remove(objeto_nf_xml.caminho)
                                    if objeto_nf_xml:
                                        db.session.delete(objeto_nf_xml)
                                        db.session.commit()
                                        
                                    flash(("O peso extraído da nota fiscal é inválido! Entre em contato com o suporte!", "warning"))
                                    return redirect(url_for("editar_emissao", id=registro.id))

                                
                                obj1 = {
                                    "razao_social_emissor": registro.razao_social_emissor or "",
                                    "numero_nota_fiscal": registro.numero_nota_fiscal or "",
                                    "serie_nota": registro.serie_nota or "",
                                    "chave_acesso": registro.chave_acesso or "",
                                    "destinatario_nome": registro.destinatario_nome or "",
                                    "destinatario_cnpj_cpf": registro.destinatario_cnpj_cpf or "",
                                    "destinatario_insc_estadual": registro.destinatario_insc_estadual or "",
                                    "destinatario_data_emissao": str(registro.destinatario_data_emissao or ""),
                                    "valor_total_nota_100": int(registro.valor_total_nota_100 or 0),
                                    "transportador_nome": registro.transportador_nome or "",
                                    "transportador_cnpj_cpf": registro.transportador_cnpj_cpf or "",
                                    "transportador_insc_estadual": registro.transportador_insc_estadual or "",
                                    "placa_nf": registro.placa_nf or "",
                                    "motorista_nf": registro.motorista_nf or "",
                                    "peso_nf": float(registro.peso_ton_nf or 0),
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
                                registro.razao_social_emissor = razao_social_emissor or None
                                registro.numero_nota_fiscal = numero_nota or None
                                registro.serie_nota = serie or None
                                registro.chave_acesso = chave_acesso or None
                                registro.destinatario_nome = destinatario or None
                                registro.destinatario_cnpj_cpf = destinatario_cpf_cnpj or None
                                registro.destinatario_insc_estadual = destinatario_insc_estadual or None
                                registro.destinatario_data_emissao = destinatario_data_emissao or None
                                registro.valor_total_nota_100 = valor_total_nota
                                registro.preco_un_nf = preco_un
                                registro.transportador_nome = transportador or None
                                registro.transportador_cnpj_cpf = transportador_cpf_cnpj or None
                                registro.transportador_insc_estadual = transportador_insc_estadual or None
                                registro.placa_nf = placa or None
                                registro.motorista_nf = motorista or None
                                registro.peso_ton_nf = peso_nf if peso_nf else None
                                registro.carga_frf = False
                                
                                # Limpar dados de estorno caso existam
                                registro.estorno_nf = False
                                registro.arquivo_nota_estorno_id = None
                                registro.numero_nota_fiscal_estorno = None

                                peso_nf_atual = peso_nf

                            except Exception as e:
                                print(f"[ERRO] Erro ao processar XML da nova NF: {e}")
                                
                                # Remove o arquivo que foi feito upload em caso de erro
                                if 'objeto_nf_xml' in locals() and objeto_nf_xml:
                                    try:
                                        if hasattr(objeto_nf_xml, 'caminho') and os.path.exists(objeto_nf_xml.caminho):
                                            os.remove(objeto_nf_xml.caminho)
                                        db.session.delete(objeto_nf_xml)
                                        db.session.commit()
                                    except:
                                        pass
                                        
                                flash(("Erro ao processar o arquivo XML. Verifique se é um arquivo XML válido de nota fiscal.", "warning"))
                                return redirect(url_for("editar_emissao", id=registro.id))
                        else:
                            flash(("O arquivo XML deve ter o tipo correto.", "warning"))
                            return redirect(url_for("editar_emissao", id=registro.id))
                    
                    # Atualizar as referências dos arquivos
                    if objeto_nf_xml:
                        registro.arquivo_nota_xml_id = objeto_nf_xml.id
                    
                    if objeto_nf_pdf:
                        registro.arquivo_nota_id = objeto_nf_pdf.id

                # Tratamento para ESTORNO de nota fiscal
                elif opcao_nf == "estorno":
                    arquivo_nf_estorno_pdf = arquivo_nf_estorno
                    arquivo_nf_estorno_xml = request.files.get("arquivoNfEstornoXml")
                    
                    objeto_nf_estorno_xml = None
                    objeto_nf_estorno_pdf = None
                    
                    # Upload do PDF se fornecido
                    if arquivo_nf_estorno_pdf and arquivo_nf_estorno_pdf.filename:
                        if arquivo_nf_estorno_pdf.mimetype == "application/pdf":
                            objeto_nf_estorno_pdf = upload_arquivo(arquivo_nf_estorno_pdf, "UPLOAD_ARQUIVO_ESTORNO", f"{registro.id}_estorno_pdf")
                        else:
                            flash(("O arquivo PDF de estorno deve ter o tipo correto.", "warning"))
                            return redirect(url_for("editar_emissao", id=registro.id))
                    
                    # Upload e processamento do XML (obrigatório)
                    if arquivo_nf_estorno_xml and arquivo_nf_estorno_xml.filename:
                        if arquivo_nf_estorno_xml.mimetype in ["application/xml", "text/xml"]:
                            try:
                                objeto_nf_estorno_xml = upload_arquivo(arquivo_nf_estorno_xml, "UPLOAD_ARQUIVO_ESTORNO", f"{registro.id}_estorno_xml")

                                # Extrair dados do XML para validação
                                dados_nota = RegistroOperacionalModel.extrair_dados_nota_fiscal(objeto_nf_xml=objeto_nf_estorno_xml)

                                if not dados_nota:
                                    # Remove o arquivo que foi feito upload
                                    if objeto_nf_estorno_xml and hasattr(objeto_nf_estorno_xml, 'caminho') and os.path.exists(objeto_nf_estorno_xml.caminho):
                                        os.remove(objeto_nf_estorno_xml.caminho)
                                    if objeto_nf_estorno_xml:
                                        db.session.delete(objeto_nf_estorno_xml)
                                        db.session.commit()
                                    
                                    flash(("Arquivo XML de estorno enviado não é uma NF válida. Entre em contato com o suporte!", "warning"))
                                    return redirect(url_for("editar_emissao", id=registro.id))

                                # Extrair dados do XML de estorno
                                razao_social_emissor = dados_nota["razao_social_emissor"]
                                numero_nota_estorno = dados_nota["numero_nota_fiscal"]
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
                                    # Remove o arquivo que foi feito upload
                                    if objeto_nf_estorno_xml and hasattr(objeto_nf_estorno_xml, 'caminho') and os.path.exists(objeto_nf_estorno_xml.caminho):
                                        os.remove(objeto_nf_estorno_xml.caminho)
                                    if objeto_nf_estorno_xml:
                                        db.session.delete(objeto_nf_estorno_xml)
                                        db.session.commit()
                                        
                                    flash(("O peso extraído da nota fiscal de estorno é inválido! Entre em contato com o suporte!", "warning"))
                                    return redirect(url_for("editar_emissao", id=registro.id))

                                # Comparação para gamificação
                                obj1 = {
                                    "razao_social_emissor": registro.razao_social_emissor or "",
                                    "numero_nota_fiscal_estorno": registro.numero_nota_fiscal_estorno or "",
                                    "serie_nota": registro.serie_nota or "",
                                    "chave_acesso": registro.chave_acesso or "",
                                    "destinatario_nome": registro.destinatario_nome or "",
                                    "destinatario_cnpj_cpf": registro.destinatario_cnpj_cpf or "",
                                    "destinatario_insc_estadual": registro.destinatario_insc_estadual or "",
                                    "destinatario_data_emissao": str(registro.destinatario_data_emissao or ""),
                                    "valor_total_nota_100": int(registro.valor_total_nota_100 or 0),
                                    "transportador_nome": registro.transportador_nome or "",
                                    "transportador_cnpj_cpf": registro.transportador_cnpj_cpf or "",
                                    "transportador_insc_estadual": registro.transportador_insc_estadual or "",
                                    "placa_nf": registro.placa_nf or "",
                                    "motorista_nf": registro.motorista_nf or "",
                                    "peso_nf": float(registro.peso_ton_nf or 0),
                                }

                                obj2 = {
                                    "razao_social_emissor": razao_social_emissor or "",
                                    "numero_nota_fiscal_estorno": numero_nota_estorno or "",
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

                                # Atualizar dados da nota de estorno
                                registro.razao_social_emissor = razao_social_emissor or None
                                registro.numero_nota_fiscal_estorno = numero_nota_estorno or None
                                registro.serie_nota = serie or None
                                registro.chave_acesso = chave_acesso or None
                                registro.destinatario_nome = destinatario or None
                                registro.destinatario_cnpj_cpf = destinatario_cpf_cnpj or None
                                registro.destinatario_insc_estadual = destinatario_insc_estadual or None
                                registro.destinatario_data_emissao = destinatario_data_emissao or None
                                registro.valor_total_nota_100 = valor_total_nota
                                registro.preco_un_nf = preco_un
                                registro.transportador_nome = transportador or None
                                registro.transportador_cnpj_cpf = transportador_cpf_cnpj or None
                                registro.transportador_insc_estadual = transportador_insc_estadual or None
                                registro.placa_nf = placa or None
                                registro.motorista_nf = motorista or None
                                registro.peso_ton_nf = peso_nf if peso_nf else None
                                registro.estorno_nf = True
                                registro.carga_frf = False

                                peso_nf_atual = peso_nf

                            except Exception as e:
                                print(f"[ERRO] Erro ao processar XML de estorno: {e}")
                                
                                # Remove o arquivo que foi feito upload em caso de erro
                                if 'objeto_nf_estorno_xml' in locals() and objeto_nf_estorno_xml:
                                    try:
                                        if hasattr(objeto_nf_estorno_xml, 'caminho') and os.path.exists(objeto_nf_estorno_xml.caminho):
                                            os.remove(objeto_nf_estorno_xml.caminho)
                                        db.session.delete(objeto_nf_estorno_xml)
                                        db.session.commit()
                                    except:
                                        pass
                                        
                                flash(("Erro ao processar o arquivo XML de estorno. Verifique se é um arquivo XML válido de nota fiscal.", "warning"))
                                return redirect(url_for("editar_emissao", id=registro.id))
                        else:
                            flash(("O arquivo XML de estorno deve ter o tipo correto.", "warning"))
                            return redirect(url_for("editar_emissao", id=registro.id))
                    
                    # Atualizar as referências dos arquivos de estorno
                    # Para estorno, substitui o XML principal e também salva como estorno
                    if objeto_nf_estorno_xml:
                        registro.arquivo_nota_xml_id = objeto_nf_estorno_xml.id
                    
                    if objeto_nf_estorno_pdf:
                        # Para estorno, substitui o PDF principal e também salva como estorno
                        registro.arquivo_nota_id = objeto_nf_estorno_pdf.id
                        registro.arquivo_nota_estorno_id = objeto_nf_estorno_pdf.id

                peso_excesso_final = 0
                objeto_nf_excesso = None

                if opcao_excesso == "nao":
                    registro.possui_excesso_carga = False
                    registro.arquivo_nota_excesso_id = None
                    registro.peso_ton_nf_excesso = None
                    registro.peso_nf_ton_com_excecao = None
                    registro.numero_nota_fiscal_excessao = None
                    
                elif opcao_excesso == "manter":
                    peso_excesso_final = peso_excesso_atual
                    if opcao_nf in ["estorno", "nova"]:
                        registro.peso_nf_ton_com_excecao = peso_nf_atual + peso_excesso_final
                        
                elif opcao_excesso == "novo":
                    arquivo_nfe_excesso_pdf = arquivo_nfe_excesso
                    arquivo_nfe_excesso_xml = request.files.get("arquivoNfExcessoXml")
                    
                    objeto_nf_excesso_xml = None
                    objeto_nf_excesso_pdf = None
                    peso_excesso_final = 0
                    
                    # Upload do PDF se fornecido
                    if arquivo_nfe_excesso_pdf and arquivo_nfe_excesso_pdf.filename:
                        if arquivo_nfe_excesso_pdf.mimetype == "application/pdf":
                            objeto_nf_excesso_pdf = upload_arquivo(arquivo_nfe_excesso_pdf, "UPLOAD_ARQUIVO_NF_EXCESSO", f"{registro.id}_excesso_pdf")
                        else:
                            flash(("O arquivo PDF de excesso deve ter o tipo correto.", "warning"))
                            return redirect(url_for("editar_emissao", id=registro.id))
                    
                    # Upload e processamento do XML (obrigatório)
                    if arquivo_nfe_excesso_xml and arquivo_nfe_excesso_xml.filename:
                        if arquivo_nfe_excesso_xml.mimetype in ["application/xml", "text/xml"]:
                            try:
                                objeto_nf_excesso_xml = upload_arquivo(arquivo_nfe_excesso_xml, "UPLOAD_ARQUIVO_NF_EXCESSO", f"{registro.id}_excesso_xml")

                                # Extrair dados do XML para validação
                                dados_nota_excesso = RegistroOperacionalModel.extrair_dados_nota_excesso(objeto_nf_excesso_xml=objeto_nf_excesso_xml)

                                if not dados_nota_excesso:
                                    # Remove o arquivo que foi feito upload
                                    if objeto_nf_excesso_xml and hasattr(objeto_nf_excesso_xml, 'caminho') and os.path.exists(objeto_nf_excesso_xml.caminho):
                                        os.remove(objeto_nf_excesso_xml.caminho)
                                    if objeto_nf_excesso_xml:
                                        db.session.delete(objeto_nf_excesso_xml)
                                        db.session.commit()
                                    
                                    flash(("Arquivo XML de excesso enviado não é uma NF válida. Entre em contato com o suporte!", "warning"))
                                    return redirect(url_for("editar_emissao", id=registro.id))

                                peso_excesso_final = dados_nota_excesso["peso_ton_nf_excesso"]
                                numero_nota_excessao = dados_nota_excesso["numero_nota_fiscal_excessao"]
                                
                                # Verificar se o peso é válido
                                if peso_excesso_final is None or peso_excesso_final <= 0:
                                    # Remove o arquivo que foi feito upload
                                    if objeto_nf_excesso_xml and hasattr(objeto_nf_excesso_xml, 'caminho') and os.path.exists(objeto_nf_excesso_xml.caminho):
                                        os.remove(objeto_nf_excesso_xml.caminho)
                                    if objeto_nf_excesso_xml:
                                        db.session.delete(objeto_nf_excesso_xml)
                                        db.session.commit()
                                        
                                    flash(("O peso extraído da NFe de excesso é inválido! Entre em contato com o suporte!", "warning"))
                                    return redirect(url_for("editar_emissao", id=registro.id))

                                # Atualizar registro
                                registro.possui_excesso_carga = True
                                registro.peso_ton_nf_excesso = peso_excesso_final if peso_excesso_final > 0 else None
                                registro.peso_nf_ton_com_excecao = peso_nf_atual + peso_excesso_final
                                registro.numero_nota_fiscal_excessao = numero_nota_excessao

                            except Exception as e:
                                print(f"[ERRO] Erro ao processar XML de excesso: {e}")
                                
                                # Remove o arquivo que foi feito upload em caso de erro
                                if 'objeto_nf_excesso_xml' in locals() and objeto_nf_excesso_xml:
                                    try:
                                        if hasattr(objeto_nf_excesso_xml, 'caminho') and os.path.exists(objeto_nf_excesso_xml.caminho):
                                            os.remove(objeto_nf_excesso_xml.caminho)
                                        db.session.delete(objeto_nf_excesso_xml)
                                        db.session.commit()
                                    except:
                                        pass
                                        
                                flash(("Erro ao processar o arquivo XML de excesso. Verifique se é um arquivo XML válido de nota fiscal.", "warning"))
                                return redirect(url_for("editar_emissao", id=registro.id))
                        else:
                            flash(("O arquivo XML de excesso deve ter o tipo correto.", "warning"))
                            return redirect(url_for("editar_emissao", id=registro.id))
                    
                    # Atualizar as referências dos arquivos de excesso
                    if objeto_nf_excesso_xml:
                        registro.arquivo_nota_excesso_xml_id = objeto_nf_excesso_xml.id
                    
                    if objeto_nf_excesso_pdf:
                        registro.arquivo_nota_excesso_id = objeto_nf_excesso_pdf.id

                db.session.commit()

                if opcao_nf == "nova" and opcao_excesso == "novo":
                    flash((f"NF atualizada e NFe de excesso atualizada com sucesso! Peso total: {registro.peso_nf_ton_com_excecao} (Normal: {peso_nf_atual} + Excesso: {peso_excesso_final})", "success"))
                elif opcao_nf == "nova":
                    flash((f"NF atualizada com sucesso!", "success"))
                elif opcao_nf == "estorno" and opcao_excesso == "novo":
                    flash((f"NF estornada e NFe de excesso atualizada com sucesso! Peso total: {registro.peso_nf_ton_com_excecao} (Normal: {peso_nf_atual} + Excesso: {peso_excesso_final})", "success"))
                elif opcao_nf == "estorno":
                    flash((f"Lançamento de estorno de NF executado com sucesso!", "success"))
                elif opcao_excesso == "novo":
                    flash((f"NFe de excesso atualizada com sucesso! Peso total: {registro.peso_nf_ton_com_excecao} (Normal: {peso_nf_atual} + Excesso: {peso_excesso_final})", "success"))
                elif opcao_excesso == "nao":
                    flash(("NFe de excesso removida com sucesso!", "success"))
                else:
                    flash(("Emissão editada com sucesso!", "success"))
                    
                return redirect(url_for("listagem_registros_operacionais"))

    dados_corretos = {}
    
    if request.method == "POST":
        dados_corretos = request.form
    else:
        dados_corretos = {
            'lancamentoFrf': 'lancamentoFrf' if getattr(registro, 'carga_frf', False) else '',
            'destinatarioFrf': registro.destinatario_nome or '',
            'destinatarioNumeroDocumento': registro.destinatario_cnpj_cpf or '',
            'dataLancamentoFrf': registro.destinatario_data_emissao if registro.destinatario_data_emissao else '',
            'transportadorFrf': registro.transportador_nome or '',
            'transportadoraNumeroDocumento': registro.transportador_cnpj_cpf or '',
            'placaFrf': registro.placa_nf or '',
            'motoristaFrf': registro.motorista_nf or '',
            'pesoFrf': registro.peso_ton_nf,
            'valorTotalFrf': registro.valor_total_nota_100,
        }

    return render_template(
        "/controle_carga/lancamento_nf/lancamento_editar.html",
        emissao=registro,
        florestas=florestas,
        fornecedores=fornecedores,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=dados_corretos,
    )

@app.route("/controle-cargas/registro-operacional/split/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def split_carga(id):
    registro = RegistroOperacionalModel.obter_por_id(id)
         
    if not registro:
        flash(("Registro não encontrado!", "warning"))
        return redirect(url_for("vendas_em_transito"))
    
    if registro.realizado_split:
        flash(("Não é possível realizar split para este registro!", "warning"))
        if registro.solicitacao.ticket_emitido:
            return redirect(url_for("vendas_entregues"))
        else:
            return redirect(url_for("vendas_em_transito"))
    
    produtos = ProdutoModel.listar_produtos()
    bitolas = BitolaModel.listar_bitolas_ativas()
         
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    if request.method == "POST":
        produto_novo = request.form.get("produto_novo")
        bitola_nova = request.form.get("bitola_nova")
        peso_normal_novo = request.form.get("peso_normal_novo")
        
        # Peso excesso novo só é capturado se o registro atual tem excesso
        peso_excesso_novo = request.form.get("peso_excesso_novo", "0") if registro.possui_excesso_carga else "0"
                 
        # Verificar se registro tem excesso para determinar campos obrigatórios
        if registro.possui_excesso_carga:
            peso_normal_atual = request.form.get("peso_normal_atual")
            peso_excesso_atual = request.form.get("peso_excesso_atual")
                         
            campos = {
                "produto_novo": ["Produto", produto_novo],
                "bitola_nova": ["Bitola", bitola_nova],
                "peso_normal_atual": ["Peso Normal Atual", peso_normal_atual],
                "peso_excesso_atual": ["Peso Excesso Atual", peso_excesso_atual],
                "peso_normal_novo": ["Peso Normal Novo", peso_normal_novo],
                "peso_excesso_novo": ["Peso Excesso Novo", peso_excesso_novo]
            }
        else:
            peso_atual = request.form.get("peso_atual")
                         
            campos = {
                "produto_novo": ["Produto", produto_novo],
                "bitola_nova": ["Bitola", bitola_nova],
                "peso_atual": ["Peso Atual", peso_atual],
                "peso_normal_novo": ["Peso Normal Novo", peso_normal_novo]
            }

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))

        if gravar_banco:
            try:
                peso_original = (registro.peso_ton_nf or 0) + (registro.peso_ton_nf_excesso or 0)
                                 
                if registro.peso_ton_nf_excesso:
                    peso_normal_atual_float = float(peso_normal_atual or 0)
                    peso_excesso_atual_float = float(peso_excesso_atual or 0)
                    peso_total_atual = peso_normal_atual_float + peso_excesso_atual_float
                else:
                    peso_total_atual = float(peso_atual or 0)
                                 
                peso_normal_novo_float = float(peso_normal_novo or 0)
                # Peso excesso novo só é considerado se o registro atual tem excesso
                peso_excesso_novo_float = float(peso_excesso_novo or 0) if registro.peso_ton_nf_excesso else 0
                peso_total_novo = peso_normal_novo_float + peso_excesso_novo_float
                                 
                peso_total_split = peso_total_atual + peso_total_novo
                                 
                # Verificar se os pesos conferem (tolerância de 0.01)
                if abs(peso_total_split - peso_original) > 0.01:
                    gravar_banco = False
                    flash((f"Erro: A soma dos pesos ({peso_total_split:.2f}) não confere com o peso original ({peso_original:.2f})!", "warning"))
                                 
                # Verificar se pelo menos os pesos normais são positivos
                if peso_total_atual <= 0 or peso_normal_novo_float <= 0:
                    gravar_banco = False
                    flash(("Erro: Os pesos normais devem ser maiores que zero!", "warning"))
                                 
            except (ValueError, TypeError):
                gravar_banco = False
                flash(("Erro: Valores de peso inválidos!", "warning"))

        if gravar_banco:
            try:
                # Criar nova solicitação baseada na atual
                nova_solicitacao = CargaModel(
                    empresa_emissora_id=registro.solicitacao.empresa_emissora_id,
                    cliente_id=registro.solicitacao.cliente_id,
                    bitola_id=bitola_nova,
                    produto_id=produto_novo,
                    motorista_id=registro.solicitacao.motorista_id,
                    transportadora_id=registro.solicitacao.transportadora_id,
                    veiculo_id=registro.solicitacao.veiculo_id,
                    floresta_id=registro.solicitacao.floresta_id,
                    fornecedor_id=registro.solicitacao.fornecedor_id,
                    data_hora_msg_whats=registro.solicitacao.data_hora_msg_whats,
                    usuario_id=current_user.id,
                    grupo_whats_id=registro.solicitacao.grupo_whats_id,
                    nf_emitida=True,  
                    cancelada=False,
                    realizado_split=True,
                    ativo=True,
                )
                db.session.add(nova_solicitacao)
                db.session.flush()  # Para obter o ID

                # Criar novo registro operacional
                novo_registro = RegistroOperacionalModel(
                    solicitacao_nf_id=nova_solicitacao.id,
                    fornecedor_id=registro.fornecedor_id,
                                         
                    # Copiar dados da NF original
                    razao_social_emissor=registro.razao_social_emissor,
                    numero_nota_fiscal=registro.numero_nota_fiscal,
                    serie_nota=registro.serie_nota,
                    chave_acesso=registro.chave_acesso,
                    destinatario_nome=registro.destinatario_nome,
                    destinatario_cnpj_cpf=registro.destinatario_cnpj_cpf,
                    destinatario_insc_estadual=registro.destinatario_insc_estadual,
                    destinatario_data_emissao=registro.destinatario_data_emissao,
                    valor_total_nota_100=registro.valor_total_nota_100,
                                         
                    # Dados do transportador
                    transportador_nome=registro.transportador_nome,
                    transportador_cnpj_cpf=registro.transportador_cnpj_cpf,
                    transportador_insc_estadual=registro.transportador_insc_estadual,
                                         
                    # Dados de transporte
                    placa_nf=registro.placa_nf,
                    motorista_nf=registro.motorista_nf,
                    placa_ticket=registro.placa_ticket,
                    motorista_ticket=registro.motorista_ticket,
                    data_entrega_ticket=registro.data_entrega_ticket,
                                         
                    # Novos pesos
                    peso_ton_nf=peso_normal_novo_float,
                    peso_ton_nf_excesso=peso_excesso_novo_float if peso_excesso_novo_float > 0 else None,
                    peso_nf_ton_com_excecao=peso_total_novo if peso_excesso_novo_float > 0 else peso_normal_novo_float,
                    possui_excesso_carga=(peso_excesso_novo_float > 0),
                                         
                    # Dados do ticket
                    numero_nota_fiscal_ticket=registro.numero_nota_fiscal_ticket,
                    peso_liquido_ticket=registro.peso_liquido_ticket,
                                         
                    # Arquivos (referência aos mesmos)
                    arquivo_nota_id=registro.arquivo_nota_id,
                    arquivo_ticket_id=registro.arquivo_ticket_id,
                    arquivo_nota_excesso_id=registro.arquivo_nota_excesso_id if peso_excesso_novo_float > 0 else None,
                                         
                    # Status e situação
                    status_emissao_nf_complementar_id=registro.status_emissao_nf_complementar_id,
                    situacao_financeira_id=registro.situacao_financeira_id,
                                         
                    # Dados de estorno
                    estorno_nf=registro.estorno_nf,
                    arquivo_nota_estorno_id=registro.arquivo_nota_estorno_id,
                    numero_nota_fiscal_estorno=registro.numero_nota_fiscal_estorno,
                    realizado_split=True,                      
                    ativo=True
                )
                db.session.add(novo_registro)

                # Atualizar registro atual
                registro.realizado_split = True
                registro.solicitacao.realizado_split = True
                if registro.peso_ton_nf_excesso:
                    registro.peso_ton_nf = peso_normal_atual_float
                    registro.peso_ton_nf_excesso = peso_excesso_atual_float if peso_excesso_atual_float > 0 else None
                    registro.peso_nf_ton_com_excecao = peso_total_atual
                    registro.possui_excesso_carga = (peso_excesso_atual_float > 0)
                    if peso_excesso_atual_float <= 0:
                        registro.arquivo_nota_excesso_id = None
                else:
                    registro.peso_ton_nf = peso_total_atual
                    registro.peso_nf_ton_com_excecao = peso_total_atual

                db.session.commit()

                # Registrar gamificação
                acao = TipoAcaoEnum.EDICAO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    acao,
                    acao.pontos,
                    modulo='split_carga'
                )

                flash((f"Split de carga realizado com sucesso! Criado novo registro operacional #{novo_registro.id}", "success"))
                if registro.solicitacao.ticket_emitido:
                    return redirect(url_for("vendas_entregues"))
                else:
                    return redirect(url_for("vendas_em_transito"))

            except Exception as e:
                db.session.rollback()
                flash((f"Erro ao realizar split: {str(e)}", "danger"))

    return render_template(
        "controle_carga/registro_operacional/split_carga/split_carga.html",
        registro=registro,
        produtos=produtos,
        bitolas=bitolas,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
    )