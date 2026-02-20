from datetime import datetime
from sistema import app, requires_roles, db, current_user
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.faturamento.cargas_a_receber.nf_servico.nf_servico_model import NfServicoModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema.models_views.parametros.status_emissao_nf_complementar.status_emissao_nf_complementar_model import StatusEmissaoNfComplementarModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema.models_views.upload_arquivo.upload_arquivo_model import UploadArquivoModel
from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema._utilitarios import *
from sistema._utilitarios.extracao_nfs_e import ExtrairDadosNFSe

@app.route("/faturamento/nf-servico", methods=["GET"])
@login_required
@requires_roles
def faturamento_nf_servico():
    """Listagem de NFs de serviço para faturamento, agrupadas por cliente"""
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    dataHoje = datetime.now().strftime('%d-%m-%Y')
    clientes = ClienteModel.listar_clientes_ativos()

    agrupar_cargas_receber = request.args.get('agrupar_cargas_receber')
    if agrupar_cargas_receber:
        nfs_servico = NfServicoModel.query.filter(
            NfServicoModel.ativo == True,
            NfServicoModel.situacao_financeira_id == 2
        ).all()
    else:
        nfs_servico = NfServicoModel.listar_ativas()

    registros_agrupados = []
    for nf in nfs_servico:
        registro_obj = type('obj', (object,), {
            'id': nf.id,
            'cliente': nf.cliente.identificacao if nf.cliente else "Cliente não identificado",
            'data_emissao': nf.data_emissao,
            'carregamento_discriminacao': nf.carregamento_discriminacao or "",
            'discriminacao_servico': nf.discriminacao_servico or "",
            'valor_total_liquido': nf.total_liquido_100 or 0,
            'situacao_financeira': nf.situacao,
            'numero_nota_fiscal': nf.numero_nota_fiscal or "-",
            'servico': nf
        })()
        
        item_agrupado = type('obj', (object,), {
            'cliente': nf.cliente.identificacao if nf.cliente else "Cliente não identificado",
            'registro': registro_obj
        })()
        
        registros_agrupados.append(item_agrupado)

    return render_template(
        "faturamento/cargas_a_receber/nf_servico/faturamento_nf_servico.html",
        registros=registros_agrupados,
        clientes=clientes,
        dados_corretos=request.args,
        changelog=changelog,
        dataHoje=dataHoje,
        agrupar_cargas_receber=agrupar_cargas_receber
    )
    
@app.route('/faturamento/nf-servico/cadastrar-nf-servico', methods=['GET', 'POST'])
@login_required
@requires_roles
def cadastrar_nf_servico():
    """Processa formulário de criação de NF Serviço com upload de arquivo NFS-e"""
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True
    
    if request.method == "POST":
        """Processa emissão via formulário com upload de PDF da NFS-e"""
        try:            
            cliente_id = request.form.get('cliente_id')
            arquivo_nfse = request.files.get('arquivo_nf_servico')
            
            campos = {
                "cliente_id": ["Cliente", cliente_id],
                "arquivo_nf_servico": ["Arquivo NFS-e", arquivo_nfse]
            }
            
            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

            if not "validado" in validacao_campos_obrigatorios:
                gravar_banco = False
                flash((f"Verifique os campos destacados em vermelho!", "warning"))

            if gravar_banco:
                if arquivo_nfse.mimetype != "application/pdf":
                    flash(('Arquivo deve ser um PDF válido.', 'error'))
                    return redirect(url_for('cadastrar_nf_servico'))
                
                objeto_nfse_temp = upload_arquivo(arquivo_nfse, "UPLOAD_NOTA_SERVICO", "temp")
                
                try:
                    dados_nfse = ExtrairDadosNFSe.extrair_dados_nfse_simples(objeto_nfse_temp.caminho)
                                    
                    numero_nota = dados_nfse["cabecalho"].get("numero_nota")
                    tem_prestador = dados_nfse["prestador"].get("cnpj_cpf") or dados_nfse["prestador"].get("identificacao_social")
                    valor_total = dados_nfse["totais"].get("total_liquido") or dados_nfse["totais"].get("total_servicos")
                    
                    if not (numero_nota or tem_prestador) or not valor_total:
                        db.session.delete(objeto_nfse_temp)
                        db.session.commit()
                        flash(("Arquivo não é uma NFS-e válida! Verifique se contém dados obrigatórios.", "warning"))
                        return redirect(url_for("cadastrar_nf_servico"))
                    
                except Exception:
                    db.session.delete(objeto_nfse_temp)
                    db.session.commit()
                    flash(("Erro ao processar arquivo! Verifique se é uma NFS-e válida.", "error"))
                    return redirect(url_for("cadastrar_nf_servico"))
                
                nf_servico = NfServicoModel(
                    cliente_id=int(cliente_id),
                    situacao_financeira_id=2,
                )
                
                db.session.add(nf_servico)
                db.session.flush()
                
                objeto_nfse_temp.nome_original = f"{nf_servico.id}"
                objeto_nfse = objeto_nfse_temp
                
                data_emissao = None
                data_hora_str = dados_nfse["cabecalho"].get("data_hora_emissao")
                if data_hora_str:
                    try:
                        data_emissao = datetime.strptime(data_hora_str.split()[0], "%d/%m/%Y").date()
                    except:
                        pass
                
                def converter_valor(valor_str):
                    if not valor_str:
                        return 0
                    try:
                        valor_limpo = valor_str.replace('.', '').replace(',', '.')
                        return int(float(valor_limpo) * 100)
                    except:
                        return 0
                def truncar_string(valor, max_length):
                    if not valor:
                        return valor
                    return valor[:max_length] if len(valor) > max_length else valor
                
                nf_servico.numero_nota_fiscal = truncar_string(dados_nfse["cabecalho"].get("numero_nota"), 50)
                nf_servico.chave_acesso = truncar_string(dados_nfse["cabecalho"].get("codigo_verificacao"), 500)
                nf_servico.data_emissao = data_emissao
                
                if dados_nfse["cabecalho"].get("data_competencia"):
                    try:
                        nf_servico.data_competencia = datetime.strptime(dados_nfse["cabecalho"]["data_competencia"], '%d/%m/%Y').date()
                    except ValueError:
                        pass
                
                nf_servico.servico_exigivel = dados_nfse.get("dados_servico", {}).get("exigibilidade") or "Exigível"
                nf_servico.municipio_prestacao_servico = dados_nfse.get("dados_servico", {}).get("municipio_prestacao") or "Canela/RS"
                nf_servico.municipio_incidencia = dados_nfse.get("dados_servico", {}).get("municipio_incidencia") or "Canela/RS"
                
                nf_servico.prestador_identificacao_social = truncar_string(dados_nfse["prestador"].get("identificacao_social"), 255)
                nf_servico.prestador_nome_fantasia = truncar_string(dados_nfse["prestador"].get("nome_fantasia"), 255)
                nf_servico.prestador_endereco = truncar_string(dados_nfse["prestador"].get("endereco"), 500)
                nf_servico.prestador_municipio = truncar_string(dados_nfse["prestador"].get("municipio"), 150)
                nf_servico.prestador_cep = truncar_string(dados_nfse["prestador"].get("cep"), 15)
                nf_servico.prestador_cnpj_cpf = truncar_string(dados_nfse["prestador"].get("cnpj_cpf"), 25)
                nf_servico.prestador_inscricao_municipal = truncar_string(dados_nfse["prestador"].get("inscricao_municipal"), 100)
                nf_servico.prestador_inscricao_estadual = truncar_string(dados_nfse["prestador"].get("inscricao_estadual"), 100)
                nf_servico.prestador_telefone = truncar_string(dados_nfse["prestador"].get("telefone"), 100)
                nf_servico.prestador_email = truncar_string(dados_nfse["prestador"].get("email"), 150)
                
                nf_servico.tomador_razao_social = truncar_string(dados_nfse["tomador"].get("razao_social"), 255)
                nf_servico.tomador_endereco = truncar_string(dados_nfse["tomador"].get("endereco"), 500)
                nf_servico.tomador_municipio = truncar_string(dados_nfse["tomador"].get("municipio"), 150)
                nf_servico.tomador_cep = truncar_string(dados_nfse["tomador"].get("cep"), 15)
                nf_servico.tomador_cnpj_cpf = truncar_string(dados_nfse["tomador"].get("cnpj_cpf"), 25)
                nf_servico.tomador_inscricao_municipal = truncar_string(dados_nfse["tomador"].get("inscricao_municipal"), 100)
                nf_servico.tomador_telefone = truncar_string(dados_nfse["tomador"].get("telefone"), 100)
                nf_servico.tomador_email = truncar_string(dados_nfse["tomador"].get("email"), 150)
                
                nf_servico.discriminacao_servico = dados_nfse["discriminacao"].get("discriminacao_servico")
                nf_servico.carregamento_discriminacao = truncar_string(dados_nfse["discriminacao"].get("carregamento_cavaco_biomassa"), 255)
                
                nf_servico.valor_servico_100 = converter_valor(dados_nfse["discriminacao"].get("valor_servico"))
                nf_servico.total_servicos_100 = converter_valor(dados_nfse["totais"].get("total_servicos"))
                nf_servico.total_liquido_100 = converter_valor(dados_nfse["totais"].get("total_liquido"))
                
                if dados_nfse["discriminacao"].get("aliquota_iss"):
                    try:
                        nf_servico.aliquota_servico = float(dados_nfse["discriminacao"]["aliquota_iss"].replace(',', '.'))
                    except ValueError:
                        pass
                
                nf_servico.valor_iss_100 = converter_valor(dados_nfse["discriminacao"].get("valor_iss"))
                
                nf_servico.base_calculo_rs = converter_valor(dados_nfse["discriminacao"].get("base_calculo"))
                nf_servico.valor_desconto_100 = converter_valor(dados_nfse["discriminacao"].get("valor_desconto"))
                nf_servico.desconto_condicional_100 = converter_valor(dados_nfse["discriminacao"].get("desconto_condicional"))
                
                aliquota_str = dados_nfse["discriminacao"].get("aliquota_servico")
                if aliquota_str:
                    try:
                        nf_servico.aliquota_servico = float(aliquota_str.replace(',', '.'))
                    except:
                        pass
                
                nf_servico.pis_valor_100 = converter_valor(dados_nfse["retencoes"].get("pis_valor"))
                nf_servico.cofins_valor_100 = converter_valor(dados_nfse["retencoes"].get("cofins_valor"))
                nf_servico.inss_valor_100 = converter_valor(dados_nfse["retencoes"].get("inss_valor"))
                nf_servico.csll_valor_100 = converter_valor(dados_nfse["retencoes"].get("csll_valor"))
                nf_servico.outras_retencoes_100 = converter_valor(dados_nfse["retencoes"].get("outras_retencoes"))
                
                periodo_inicio, periodo_fim = ExtrairDadosNFSe.extrair_periodo_servico(
                    dados_nfse["discriminacao"].get("discriminacao_servico")
                )
                nf_servico.periodo_inicio = periodo_inicio
                nf_servico.periodo_fim = periodo_fim
                
                nf_servico.arquivo_nota_id = objeto_nfse.id

                db.session.commit()

                flash((f'NFS-e cadastrada com sucesso!', 'success'))
                return redirect(url_for('faturamento_nf_servico')) 
                    
        except Exception as e:
            db.session.rollback()
            flash(('Erro inesperado ao processar NFS-e. Tente novamente.', 'error'))
            
    clientes = ClienteModel.listar_clientes_ativos()
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    
    return render_template(
        'faturamento/cargas_a_receber/nf_servico/faturamento_nova_nf_servico.html',
        clientes=clientes,
        changelog=changelog,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
    )
    
@app.route("/faturamento/nf-servico/informar-faturamento/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def informar_faturamento_nf_servico(id):
    try:
        campos_obrigatorios = {}
        campos_erros = {}
        gravar_banco = True

        registro = NfServicoModel.obter_por_id(id)

        if not registro:
            flash(("Registro não encontrado!", "warning"))
            return redirect(url_for('faturamento_nf_servico'))

        if registro.situacao_financeira_id == 5:
            flash(("Registro já consta como faturado!", "warning"))
            return redirect(url_for('faturamento_nf_servico'))
            
        
        registro_dict = {
            'id': registro.id,
            'cliente': registro.cliente if registro.cliente else None,
            'discriminacao': registro.carregamento_discriminacao or '-',
            'valor_total': registro.total_liquido_100 or 0,
            'situacao': registro.situacao,
            'registro_servico': registro,
            'numero_nota_fiscal': registro.numero_nota_fiscal or "-"
        }
        
        if request.method == "POST":
            if gravar_banco:
                registro.situacao_financeira_id = 5  
                
                novo_faturamento = FaturamentoModel(
                    usuario_id=current_user.id,
                    codigo_faturamento=FaturamentoModel.gerar_codigo_novo_faturamento(),
                    valor_total=registro.total_liquido_100 or 0, 
                    ids_nf_servico=str(registro.id),
                    situacao_pagamento_id=7,
                    tipo_operacao=1,
                    direcao_financeira=1
                )

                detalhes_nf_servico = [{
                    "nf_servico_id": registro.id,
                    "numero_nf": registro.numero_nota_fiscal or "",
                    "cliente_id": registro.cliente.id if registro.cliente else "",
                    "cliente": registro.cliente.identificacao if registro.cliente else "",
                    'discriminacao': registro.carregamento_discriminacao or '-',
                    'valor_total': registro.total_liquido_100 or 0,
                    'data_emissao': registro.data_emissao.strftime('%d/%m/%Y') if registro.data_emissao else None
                }]

                novo_faturamento.salvar_detalhes(nf_servico=detalhes_nf_servico)

                db.session.add(novo_faturamento)
                db.session.commit()
                
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    TipoAcaoEnum.CADASTRO,
                    TipoAcaoEnum.CADASTRO.pontos,
                    modulo="informar_faturamento_nf_servico",
                )
                
                flash(("Faturamento informado com sucesso!", "success"))
                return redirect(url_for('faturamento_nf_servico'))

        return render_template(
            "/faturamento/cargas_a_receber/nf_servico/informar_faturamento_nf_servico.html",
            campos_obrigatorios=campos_obrigatorios,
            campos_erros=campos_erros,
            dados_corretos=request.form,
            registro=registro_dict
        )
    except Exception as e:
        db.session.rollback()
        flash((f"Erro ao informar faturamento de carga: {str(e)}", "danger"))
        return redirect(url_for("faturamento_nf_servico"))

@app.route("/faturamento/nf-servico/informar-faturamento-massa", methods=["GET", "POST"])
@login_required
@requires_roles
def informar_faturamento_nf_servico_massa():
    try:
        campos_obrigatorios = {}
        campos_erros = {}
        gravar_banco = True

        if request.method == "GET":
            ids_selecionados = request.args.get('ids_registros', '')
            if not ids_selecionados:
                flash(("Nenhum registro foi selecionado para faturamento!", "warning"))
                return redirect(url_for("faturamento_nf_servico"))
            
            try:
                ids_list = [int(id.strip()) for id in ids_selecionados.split(',') if id.strip()]
            except ValueError:
                flash(("IDs inválidos selecionados!", "warning"))
                return redirect(url_for("faturamento_nf_servico"))

        else:
            ids_selecionados = request.form.get('ids_registros', '')
            if not ids_selecionados:
                flash(("Nenhum registro foi selecionado para faturamento!", "warning"))
                return redirect(url_for("faturamento_nf_servico"))
            
            try:
                ids_list = [int(id.strip()) for id in ids_selecionados.split(',') if id.strip()]
            except ValueError:
                flash(("IDs inválidos selecionados!", "warning"))
                return redirect(url_for("faturamento_nf_servico"))

        registros = [NfServicoModel.obter_por_id(registro_id) for registro_id in ids_list]
        registros = [r for r in registros if r and r.situacao_financeira_id != 5]

        if not registros:
            flash(("Nenhum registro válido encontrado para recebimento!", "warning"))
            return redirect(url_for("faturamento_nf_servico"))
        
        if len(registros) != len(ids_list):
            flash(("Alguns registros selecionados não estão disponíveis para recebimento!", "warning"))

        clientes_dict = {}
        valor_total_geral = 0
        valores_recebidos_dict = {}

        for registro in registros:
            valor_total_recebimento = registro.total_liquido_100 or 0
            valores_recebidos_dict[registro.id] = valor_total_recebimento

            cliente_id = registro.cliente_id if registro.cliente else 0
            valor_total_geral += valor_total_recebimento

            if cliente_id not in clientes_dict:
                clientes_dict[cliente_id] = {
                    'cliente': registro.cliente if registro.cliente else None,
                    'registros': [],
                    'valor_total': 0
                }

            registro_dict = {
                'id': registro.id,
                'cliente': registro.cliente if registro.cliente else None,
                'discriminacao': registro.carregamento_discriminacao or '-',
                'valor_total': registro.total_liquido_100 or 0,
                'situacao': registro.situacao,
                'registro_servico': registro,
                'numero_nota_fiscal': registro.numero_nota_fiscal or "-",
            }

            clientes_dict[cliente_id]['registros'].append(registro_dict)
            clientes_dict[cliente_id]['valor_total'] += valor_total_recebimento

        if request.method == "POST":
            if gravar_banco:
                try:
                    registros_processados = 0
                    valor_total_processado = 0
                    detalhes_nf_servico = []

                    for registro in registros:
                        valor_recebido = valores_recebidos_dict.get(registro.id, registro.total_liquido_100 or 0)

                        registro.situacao_financeira_id = 5

                        registros_processados += 1
                        valor_total_processado += valor_recebido

                        detalhes_nf_servico.append({
                            "nf_servico_id": registro.id,
                            "numero_nf": registro.numero_nota_fiscal or "",
                            "cliente_id": registro.cliente.id if registro.cliente else "",
                            "cliente": registro.cliente.identificacao if registro.cliente else "",
                            'discriminacao': registro.carregamento_discriminacao or '-',
                            'valor_total': registro.total_liquido_100 or 0,
                            'data_emissao': registro.data_emissao.strftime('%d/%m/%Y') if registro.data_emissao else None
                        })

                    novo_faturamento = FaturamentoModel(
                        usuario_id=current_user.id,
                        codigo_faturamento=FaturamentoModel.gerar_codigo_novo_faturamento(),
                        valor_total=valor_total_processado or 0, 
                        ids_nf_servico=','.join([str(r.id) for r in registros]),
                        situacao_pagamento_id=7,
                        tipo_operacao=1,
                        direcao_financeira=1
                    )

                    novo_faturamento.salvar_detalhes(nf_servico=detalhes_nf_servico)
                    db.session.add(novo_faturamento)

                    PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                        current_user.id,
                        TipoAcaoEnum.CADASTRO,
                        TipoAcaoEnum.CADASTRO.pontos * registros_processados,
                        modulo="informar_faturamento_nf_servico_massa",
                    )

                    db.session.commit()
                    
                    flash((f"Faturamento em massa processado com sucesso!", "success"))
                    return redirect(url_for('faturamento_nf_servico'))

                except Exception as e:
                    db.session.rollback()
                    flash((f"Erro ao processar faturamento em massa: {str(e)}", "error"))
                    return redirect(request.url)

        return render_template(
            "/faturamento/cargas_a_receber/nf_servico/informar_faturamento_nf_servico_massa.html",
            campos_obrigatorios=campos_obrigatorios,
            campos_erros=campos_erros,
            dados_corretos=request.form,
            registros=registros,
            clientes_dict=clientes_dict,
            valor_total=valor_total_geral,
            ids_selecionados=ids_selecionados
        )

    except Exception as e:
        db.session.rollback()
        flash((f"Erro interno: {str(e)}", "error"))
        return redirect(url_for("faturamento_nf_servico"))


@app.route('/faturamento/nf-servico/editar-nf-servico/<int:id>', methods=['GET', 'POST'])
@login_required
@requires_roles
def editar_nf_servico(id):
    """Processa formulário de edição de NF Serviço com upload de arquivo NFS-e"""
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True
    
    nf_servico = NfServicoModel.obter_por_id(id)
    if not nf_servico:
        flash(("Registro não encontrado!", "warning"))
        return redirect(url_for('faturamento_nf_servico'))
    
    if nf_servico.situacao_financeira_id == 5 or nf_servico.situacao_financeira_id == 6 or nf_servico.situacao_financeira_id == 8:
        flash(("Registro não pode ser editado! Entre em contato com o suporte.", "warning"))
        return redirect(url_for('faturamento_nf_servico'))
    
    if request.method == "POST":
        """Processa edição via formulário com upload de PDF da NFS-e"""
        try:            
            cliente_id = request.form.get('cliente_id')
            arquivo_nfse = request.files.get('arquivo_nf_servico')
            
            campos = {
                "cliente_id": ["Cliente", cliente_id]
            }
            
            if not nf_servico.arquivo_nota_id:
                campos["arquivo_nf_servico"] = ["Arquivo NFS-e", arquivo_nfse]
            
            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

            if not "validado" in validacao_campos_obrigatorios:
                gravar_banco = False
                flash((f"Verifique os campos destacados em vermelho!", "warning"))

            if gravar_banco:
                if arquivo_nfse and arquivo_nfse.filename:
                    if arquivo_nfse.mimetype != "application/pdf":
                        flash(('Arquivo deve ser um PDF válido.', 'error'))
                        return redirect(url_for('editar_nf_servico', id=id))
                    
                    objeto_nfse_temp = upload_arquivo(arquivo_nfse, "UPLOAD_NOTA_SERVICO", "temp")
                    
                    try:
                        dados_nfse = ExtrairDadosNFSe.extrair_dados_nfse_simples(objeto_nfse_temp.caminho)
                                        
                        numero_nota = dados_nfse["cabecalho"].get("numero_nota")
                        tem_prestador = dados_nfse["prestador"].get("cnpj_cpf") or dados_nfse["prestador"].get("identificacao_social")
                        valor_total = dados_nfse["totais"].get("total_liquido") or dados_nfse["totais"].get("total_servicos")
                        
                        if not (numero_nota or tem_prestador) or not valor_total:
                            db.session.rollback()
                            flash(("Arquivo não é uma NFS-e válida! Verifique se contém dados obrigatórios.", "warning"))
                            return redirect(url_for("editar_nf_servico", id=id))
                        
                    except Exception:
                        db.session.rollback()
                        flash(("Erro ao processar arquivo! Verifique se é uma NFS-e válida.", "error"))
                        return redirect(url_for("editar_nf_servico", id=id))
                                        
                    objeto_nfse_temp.nome_original = f"{nf_servico.id}"
                    objeto_nfse = objeto_nfse_temp
                    
                    data_emissao = None
                    data_hora_str = dados_nfse["cabecalho"].get("data_hora_emissao")
                    if data_hora_str:
                        try:
                            data_emissao = datetime.strptime(data_hora_str.split()[0], "%d/%m/%Y").date()
                        except:
                            pass
                    
                    def converter_valor(valor_str):
                        if not valor_str:
                            return 0
                        try:
                            valor_limpo = valor_str.replace('.', '').replace(',', '.')
                            return int(float(valor_limpo) * 100)
                        except:
                            return 0
                    
                    def truncar_string(valor, max_length):
                        if not valor:
                            return valor
                        return valor[:max_length] if len(valor) > max_length else valor
                    
                    nf_servico.numero_nota_fiscal = truncar_string(dados_nfse["cabecalho"].get("numero_nota"), 50)
                    nf_servico.chave_acesso = truncar_string(dados_nfse["cabecalho"].get("codigo_verificacao"), 500)
                    nf_servico.data_emissao = data_emissao
                    
                    if dados_nfse["cabecalho"].get("data_competencia"):
                        try:
                            nf_servico.data_competencia = datetime.strptime(dados_nfse["cabecalho"]["data_competencia"], '%d/%m/%Y').date()
                        except ValueError:
                            pass
                    
                    nf_servico.servico_exigivel = dados_nfse.get("dados_servico", {}).get("exigibilidade") or "Exigível"
                    nf_servico.municipio_prestacao_servico = dados_nfse.get("dados_servico", {}).get("municipio_prestacao") or "Canela/RS"
                    nf_servico.municipio_incidencia = dados_nfse.get("dados_servico", {}).get("municipio_incidencia") or "Canela/RS"
                    
                    nf_servico.prestador_identificacao_social = truncar_string(dados_nfse["prestador"].get("identificacao_social"), 255)
                    nf_servico.prestador_nome_fantasia = truncar_string(dados_nfse["prestador"].get("nome_fantasia"), 255)
                    nf_servico.prestador_endereco = truncar_string(dados_nfse["prestador"].get("endereco"), 500)
                    nf_servico.prestador_municipio = truncar_string(dados_nfse["prestador"].get("municipio"), 150)
                    nf_servico.prestador_cep = truncar_string(dados_nfse["prestador"].get("cep"), 15)
                    nf_servico.prestador_cnpj_cpf = truncar_string(dados_nfse["prestador"].get("cnpj_cpf"), 25)
                    nf_servico.prestador_inscricao_municipal = truncar_string(dados_nfse["prestador"].get("inscricao_municipal"), 100)
                    nf_servico.prestador_inscricao_estadual = truncar_string(dados_nfse["prestador"].get("inscricao_estadual"), 100)
                    nf_servico.prestador_telefone = truncar_string(dados_nfse["prestador"].get("telefone"), 100)
                    nf_servico.prestador_email = truncar_string(dados_nfse["prestador"].get("email"), 150)
                    
                    nf_servico.tomador_razao_social = truncar_string(dados_nfse["tomador"].get("razao_social"), 255)
                    nf_servico.tomador_endereco = truncar_string(dados_nfse["tomador"].get("endereco"), 500)
                    nf_servico.tomador_municipio = truncar_string(dados_nfse["tomador"].get("municipio"), 150)
                    nf_servico.tomador_cep = truncar_string(dados_nfse["tomador"].get("cep"), 15)
                    nf_servico.tomador_cnpj_cpf = truncar_string(dados_nfse["tomador"].get("cnpj_cpf"), 25)
                    nf_servico.tomador_inscricao_municipal = truncar_string(dados_nfse["tomador"].get("inscricao_municipal"), 100)
                    nf_servico.tomador_telefone = truncar_string(dados_nfse["tomador"].get("telefone"), 100)
                    nf_servico.tomador_email = truncar_string(dados_nfse["tomador"].get("email"), 150)
                    
                    nf_servico.discriminacao_servico = dados_nfse["discriminacao"].get("discriminacao_servico")
                    nf_servico.carregamento_discriminacao = truncar_string(dados_nfse["discriminacao"].get("carregamento_cavaco_biomassa"), 255)
                    
                    nf_servico.valor_servico_100 = converter_valor(dados_nfse["discriminacao"].get("valor_servico"))
                    nf_servico.total_servicos_100 = converter_valor(dados_nfse["totais"].get("total_servicos"))
                    nf_servico.total_liquido_100 = converter_valor(dados_nfse["totais"].get("total_liquido"))
                    
                    if dados_nfse["discriminacao"].get("aliquota_iss"):
                        try:
                            nf_servico.aliquota_servico = float(dados_nfse["discriminacao"]["aliquota_iss"].replace(',', '.'))
                        except ValueError:
                            pass
                    
                    nf_servico.valor_iss_100 = converter_valor(dados_nfse["discriminacao"].get("valor_iss"))
                    
                    nf_servico.base_calculo_rs = converter_valor(dados_nfse["discriminacao"].get("base_calculo"))
                    nf_servico.valor_desconto_100 = converter_valor(dados_nfse["discriminacao"].get("valor_desconto"))
                    nf_servico.desconto_condicional_100 = converter_valor(dados_nfse["discriminacao"].get("desconto_condicional"))
                    
                    aliquota_str = dados_nfse["discriminacao"].get("aliquota_servico")
                    if aliquota_str:
                        try:
                            nf_servico.aliquota_servico = float(aliquota_str.replace(',', '.'))
                        except:
                            pass
                    
                    nf_servico.pis_valor_100 = converter_valor(dados_nfse["retencoes"].get("pis_valor"))
                    nf_servico.cofins_valor_100 = converter_valor(dados_nfse["retencoes"].get("cofins_valor"))
                    nf_servico.inss_valor_100 = converter_valor(dados_nfse["retencoes"].get("inss_valor"))
                    nf_servico.csll_valor_100 = converter_valor(dados_nfse["retencoes"].get("csll_valor"))
                    nf_servico.outras_retencoes_100 = converter_valor(dados_nfse["retencoes"].get("outras_retencoes"))
                    
                    periodo_inicio, periodo_fim = ExtrairDadosNFSe.extrair_periodo_servico(
                        dados_nfse["discriminacao"].get("discriminacao_servico")
                    )
                    nf_servico.periodo_inicio = periodo_inicio
                    nf_servico.periodo_fim = periodo_fim
                    
                    nf_servico.arquivo_nota_id = objeto_nfse.id

                nf_servico.cliente_id = int(cliente_id)

                db.session.commit()

                flash((f'NFS-e editada com sucesso!', 'success'))
                return redirect(url_for('faturamento_nf_servico')) 
                    
        except Exception as e:
            db.session.rollback()
            flash(('Erro inesperado ao editar NFS-e. Tente novamente.', 'error'))
            
    clientes = ClienteModel.listar_clientes_ativos()
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    
    return render_template(
        'faturamento/cargas_a_receber/nf_servico/faturamento_editar_nf_servico.html',
        clientes=clientes,
        changelog=changelog,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
        nf_servico=nf_servico,
    )

@app.route("/faturamento/excluir-nf-servico/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def excluir_nf_servico(id):
    try:
        gravar_banco = True

        registro = NfServicoModel.obter_por_id(id)

        if not registro:
            flash(("Registro não encontrado! Entre em contato com o suporte.", "warning"))
            return redirect(url_for('faturamento_nf_servico'))

        if registro.deletado == True or registro.ativo == False:
            flash(("Registro já consta como excluído! Entre em contato com o suporte.", "warning"))
            return redirect(url_for('faturamento_nf_servico'))
        
        if registro.situacao_financeira_id == 5 or registro.situacao_financeira_id == 6 or registro.situacao_financeira_id == 8:
            flash(("Registro não pode ser excluído! Entre em contato com o suporte.", "warning"))
            return redirect(url_for('faturamento_nf_servico'))
        
        if request.method == "POST":
            if gravar_banco:
                registro.deletado = True
                registro.ativo = False
                
                db.session.commit()
                db.session.commit()
                
                flash(("NF de serviço excluído com sucesso!", "success"))
                return redirect(url_for('faturamento_nf_servico'))
        flash(("Não foi possível excluir o NF de serviço. Entre em contato com o suporte.", "warning"))
        return redirect(url_for('faturamento_nf_servico'))
    except Exception as e:
        db.session.rollback()
        flash((f"Erro ao excluir NF de serviço! Entre em contato com o suporte.", "danger"))
        return redirect(url_for("faturamento_nf_servico"))
