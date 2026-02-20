from datetime import datetime
from sistema import app, requires_roles, db, current_user, obter_url_absoluta_de_imagem
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.faturamento.cargas_a_receber.nf_complementar.nf_complementar_model import NfComplementarModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema.models_views.parametros.status_emissao_nf_complementar.status_emissao_nf_complementar_model import StatusEmissaoNfComplementarModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema.models_views.upload_arquivo.upload_arquivo_model import UploadArquivoModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema._utilitarios import *

@app.route("/controle-cargas/nfs-complementares", methods=["GET"])
@login_required
@requires_roles
def listagem_nf_complementar():
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    dataHoje = datetime.now().strftime('%d-%m-%Y')
    statusNfComplementar = StatusEmissaoNfComplementarModel.listar_status_ativos()
    clientes = ClienteModel.listar_clientes_ativos()

    if any(request.args.values()):
        registros = RegistroOperacionalModel.filtrar_registros_carga_cliente(
            data_inicio=request.args.get('dataInicio'),
            data_fim=request.args.get('dataFim'),
            numero_nf=request.args.get('numeroNfComplementar'),
            cliente=request.args.get('clienteNfComplementar'),
            status_nf_complementar=request.args.get('statusNfComplementarEmitida')
        )
    else:
        registros = RegistroOperacionalModel.obter_registros_carga_agrupados()

    return render_template(
        "controle_carga/nf_complementar/nf_complementar_listagem.html",
        registros=registros,
        clientes=clientes,
        dados_corretos=request.args,
        statusNfComplementar=statusNfComplementar,
        changelog=changelog,
        dataHoje=dataHoje
    )

@app.route("/controle-cargas/nfs-complementares/exportar-excel", methods=["POST"])
@login_required
@requires_roles
def exportar_nf_complementar_listagem_excel():
    """Exporta NFs complementares filtradas para Excel"""
    try:
        dataHoje = datetime.now().strftime('%d-%m-%Y')
        
        data_inicio = request.form.get('dataInicioExport')
        data_fim = request.form.get('dataFimExport')
        cliente_id = request.form.get('clienteExport')
        
        if data_inicio or data_fim or cliente_id:
            cliente_nome = None
            if cliente_id:
                cliente_obj = ClienteModel.query.get(int(cliente_id))
                if cliente_obj:
                    cliente_nome = cliente_obj.identificacao
            
            registros = RegistroOperacionalModel.filtrar_registros_carga_cliente(
                data_inicio=data_inicio,
                data_fim=data_fim,
                numero_nf=None,
                cliente=cliente_nome,
                status_nf_complementar=None
            )
        else:
            registros = RegistroOperacionalModel.obter_registros_carga_agrupados()
        
        linhas = []
        for item in registros:
            registro = item['registro']
            
            peso_nf = registro.peso_ton_nf if registro.peso_ton_nf else 0
            peso_ticket = registro.peso_liquido_ticket if registro.peso_liquido_ticket else 0
            diferenca = round(peso_nf - peso_ticket, 2)
            
            linha = {
                'Data Emissão': registro.destinatario_data_emissao.strftime('%d/%m/%Y') if registro.destinatario_data_emissao else '-',
                'Cliente': item.get('cliente', '-'),
                'Número NF': f"{registro.numero_nota_fiscal_estorno} *" if registro.estorno_nf else (registro.numero_nota_fiscal or '-'),
                'Peso NF': f"{peso_nf} Ton." if peso_nf > 0 else '-',
                'Peso Ticket': f"{peso_ticket} Ton." if peso_ticket > 0 else '-',
                'Diferença': f"{diferenca} Ton.",
                'Status': registro.status_emissao_nf_complementar.status if registro.status_emissao_nf_complementar else '-'
            }
            linhas.append(linha)
        
        nome_arquivo_saida = f'nf-complementar_{dataHoje}'
        return ManipulacaoArquivos.exportar_excel(linhas, nome_arquivo_saida)
        
    except Exception as e:
        flash((f"Erro ao exportar relatório! Contate o suporte.", "error"))
        return redirect(url_for('listagem_nf_complementar'))

@app.route("/controle-cargas/nfs-complementares/exportar-pdf", methods=["POST"])
@login_required
@requires_roles
def exportar_nf_complementar_listagem_pdf():
    """Exporta NFs complementares filtradas para PDF"""
    try:
        dataHoje = datetime.now().strftime('%d-%m-%Y')
        
        data_inicio = request.form.get('dataInicioExport')
        data_fim = request.form.get('dataFimExport')
        cliente_id = request.form.get('clienteExport')
        
        if data_inicio or data_fim or cliente_id:
            cliente_nome = None
            if cliente_id:
                cliente_obj = ClienteModel.query.get(int(cliente_id))
                if cliente_obj:
                    cliente_nome = cliente_obj.identificacao
            
            registros = RegistroOperacionalModel.filtrar_registros_carga_cliente(
                data_inicio=data_inicio,
                data_fim=data_fim,
                numero_nf=None,
                cliente=cliente_nome,
                status_nf_complementar=None
            )
        else:
            registros = RegistroOperacionalModel.obter_registros_carga_agrupados()
            cliente_nome = None
        
        changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
        logo_path = obter_url_absoluta_de_imagem('logo.png')
        html = render_template(
            "relatorios/relatorio_de_cargas/relatorio_controle_nf_complementar/exportar_relatorio_controle_complementar.html",
            logo_path=logo_path,
            dataHoje=dataHoje,
            registros=registros,
            dados_corretos=request.form,
            changelog=changelog,
            cliente_nome=cliente_nome
        )
        
        nome_arquivo_saida = f'nf-complementar_{dataHoje}'
        return ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida)
        
    except Exception as e:
        flash((f"Erro ao exportar relatório! Contate o suporte.", "error"))
        return redirect(url_for('listagem_nf_complementar'))
    

@app.route("/controle-cargas/nfs-complementares/emitir-nfs-complementares", methods=["POST"])
@login_required
@requires_roles
def emitir_nfs_complementares_em_massa():
    """Processa formulário de criação de NF Complementar com upload de arquivo"""
    validacao_campos_obrigatorios = {}
    gravar_banco = True
    if request.method == "POST":
        try:
            cliente_id = request.form.get('cliente_id')
            ids_registros = request.form.getlist('ids_registros')
            arquivo_nf = request.files.get('arquivo_nf_complementar')
            
            campos = {
                "cliente_id": ["Cliente", cliente_id],
            }
            
            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

            if not "validado" in validacao_campos_obrigatorios:
                gravar_banco = False
                flash((f"Verifique os campos destacados em vermelho!", "warning"))
                
            if not ids_registros:
                gravar_banco = False
                flash(('Nenhum registro operacional foi selecionado.', 'error'))
                
                
            if not arquivo_nf:
                gravar_banco = False
                flash(('Arquivo da NF Complementar é obrigatório.', 'error'))
                return redirect(url_for('listagem_nf_complementar'))

            if gravar_banco:
                
                registros = RegistroOperacionalModel.query.filter(
                    RegistroOperacionalModel.id.in_(ids_registros)
                ).all()
                
                if not registros:
                    flash('Nenhum registro operacional encontrado com os IDs fornecidos.', 'error')
                    return redirect(url_for('listagem_nf_complementar'))
                
                clientes_registros = set(reg.solicitacao.cliente.id for reg in registros 
                    if reg.solicitacao and reg.solicitacao.cliente)

                if len(clientes_registros) > 1 or (clientes_registros and int(cliente_id) not in clientes_registros):
                    flash(('Todos os registros devem ser do mesmo cliente selecionado.', 'error'))
                    return redirect(url_for('listagem_nf_complementar'))
                
                if arquivo_nf.mimetype != "application/pdf":
                    flash(('Arquivo deve ser um PDF válido.', 'error'))
                    return redirect(url_for('listagem_nf_complementar'))
                
                detalhes_registros = []
                for registro in registros:
                    detalhes_registros.append({
                        'registro_id': registro.id,
                        'solicitacao_id': registro.solicitacao_nf_id
                    })
                
                nf_complementar = NfComplementarModel(
                    cliente_id=int(cliente_id),
                    nf_complementar_detalhes={'registros_operacionais': detalhes_registros},
                    situacao_financeira_id = 2,
                )
                
                db.session.add(nf_complementar)
                db.session.flush()
                
                objeto_nf = upload_arquivo(arquivo_nf, "UPLOAD_NOTA_COMPLEMENTAR", f"{nf_complementar.id}")
                
                dados_nota = ExtrairTextoNotaFiscal.nf_extrair_dados_nota(objeto_nf.caminho)
                if (not dados_nota["destinatario"] or not dados_nota["emissor"] or not dados_nota["calculo_imposto"]):
                    flash(("Arquivo enviado não é uma NF válida. Entre em contato com o suporte!", "warning"))
                    db.session.rollback()
                    return redirect(url_for("listagem_nf_complementar"))
                
                dados_nf = RegistroOperacionalModel.extrair_dados_nf_pdf(dados_nota)
                peso_nf = dados_nf["peso_ton_nf"]
                preco_un = dados_nf["preco_un_nf"]
                
                if peso_nf is None or peso_nf < 0 or peso_nf == "":
                    flash(("O peso extraído da nota fiscal é inválido! Entre em contato com o suporte!", "warning"))
                    db.session.rollback()
                    return redirect(url_for("listagem_nf_complementar"))
                
                destinatario_data_emissao = dados_nf["destinatario_data_emissao"]
                if destinatario_data_emissao:
                    destinatario_data_emissao = DataHora.converter_data_str_br_em_objeto_date(destinatario_data_emissao)
                valor_total_nota = dados_nf["valor_total_nota_100"]
                if valor_total_nota:
                    valor_total_nota_float = ValoresMonetarios.converter_string_brl_para_float(valor_total_nota)
                    valor_total_nota_100 = valor_total_nota_float * 100
                else:
                    valor_total_nota_100 = None
                    
                nf_complementar.numero_nota_fiscal=dados_nf.get("numero_nota_fiscal", "")
                nf_complementar.serie_nota=dados_nf.get("serie_nota", "")
                nf_complementar.peso_ton_nf = peso_nf
                nf_complementar.chave_acesso=dados_nf.get("chave_acesso", "")
                nf_complementar.destinatario_nome=dados_nf.get("destinatario_nome", "")
                nf_complementar.destinatario_cnpj_cpf=dados_nf.get("destinatario_cnpj_cpf", "")
                nf_complementar.destinatario_insc_estadual=dados_nf.get("destinatario_insc_estadual", "")
                nf_complementar.destinatario_data_emissao=destinatario_data_emissao
                nf_complementar.valor_total_nota_100=valor_total_nota_100
                nf_complementar.preco_un_nf = preco_un
                nf_complementar.transportador_nome=dados_nf.get("transportador_nome", "")
                nf_complementar.transportador_cnpj_cpf=dados_nf.get("transportador_cnpj_cpf", "")
                nf_complementar.transportador_insc_estadual=dados_nf.get("transportador_insc_estadual", "")
                nf_complementar.placa_nf=dados_nf["placa_nf"]
                nf_complementar.motorista_nf=dados_nf["motorista_nf"]
                nf_complementar.arquivo_nota_id=objeto_nf.id

                if nf_complementar and nf_complementar.arquivo_nota_id is not None:
                    for registro in registros:
                        registro.status_emissao_nf_complementar_id = 1
                        PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                            current_user.id,
                            TipoAcaoEnum.CADASTRO,
                            TipoAcaoEnum.CADASTRO.pontos,
                            modulo='marcar_nf_complementar'
                        )
                    db.session.commit()
                    flash((f'NF Complementar {nf_complementar.numero_nota_fiscal} criada com sucesso! ', 'success'))
                else:
                    db.session.rollback()
                    flash(('Erro ao criar NF Complementar. Tente novamente.', 'error'))
        except Exception as e:
            
            db.session.rollback()
            flash(('Erro inesperado ao processar NF Complementar. Tente novamente.', 'error'))
        return redirect(url_for('listagem_nf_complementar'))