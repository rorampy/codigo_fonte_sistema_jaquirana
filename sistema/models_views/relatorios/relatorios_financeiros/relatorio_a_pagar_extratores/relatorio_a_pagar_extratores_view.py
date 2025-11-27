from datetime import datetime
from sistema import app, requires_roles, obter_url_absoluta_de_imagem
from flask import render_template, request
from flask_login import login_required
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.faturamento.cargas_a_faturar.extrator.extrator_a_pagar_model import ExtratorPagarModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
from sistema.models_views.configuracoes_gerais.situacao_pagamento.situacao_pagamento_model import SituacaoPagamentoModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema._utilitarios import *

@app.route("/relatorios/relatorios-financeiros/a-pagar-extrator", methods=["GET", "POST"])
@login_required
@requires_roles
def relatorio_a_pagar_extratores():
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    dataHoje = datetime.now().strftime("%d-%m-%Y")
    bitola = BitolaModel.listar_bitolas_ativas()
    produtos = ProdutoModel.listar_produtos()
    statusPagamentos = SituacaoPagamentoModel.listar_status()
    
    def obter_registros_com_filtros():
        
        filtros_source = request.form if request.method == "POST" and any(request.form.values()) else request.args
        
        if any(filtros_source.values()):
            data_inicio_str = filtros_source.get("dataInicio")
            data_fim_str = filtros_source.get("dataFim")
            placa = filtros_source.get("placaCargaCliente")
            motorista = filtros_source.get("motoristaCargaCliente")
            transportadora = filtros_source.get("tranpostadoraCargaCliente")
            extrator = filtros_source.get("extratorCargaCliente")
            fornecedor = filtros_source.get("fornecedorCargaCliente")
            cliente = filtros_source.get("clienteCarga")
            numero_nf = filtros_source.get("numeroNfCliente")
            incompleto = filtros_source.get("registroIncompleto")
            statusPagamento = filtros_source.get("statusPagamento") or "Pendente"
            
            
            data_inicio = None
            data_fim = None
            
            if data_inicio_str:
                try:
                    data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d")
                except ValueError:
                    pass
                    
            if data_fim_str:
                try:
                    data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d")
                except ValueError:
                    pass
            
            incompleto_bool = None
            if incompleto == "1":
                incompleto_bool = True
            elif incompleto == "0":
                incompleto_bool = False
            
            return ExtratorPagarModel.filtrar_extratores_agrupados(
                data_inicio=data_inicio,
                data_fim=data_fim,
                placa=placa,
                motorista=motorista,
                transportadora=transportadora,
                fornecedor=fornecedor,
                cliente=cliente,
                extrator=extrator,
                numero_nf=numero_nf,
                statusPagamento=statusPagamento,
                incompleto=incompleto_bool,
            )
        else:
            return ExtratorPagarModel.obter_extratores_agrupados()
    
    
    if request.method == "POST":
        
        dados_corretos = request.form if any(request.form.get(k) for k in ['dataInicio', 'dataFim', 'placaCargaCliente', 'motoristaCargaCliente', 'tranpostadoraCargaCliente', 'extratorCargaCliente', 'fornecedorCargaCliente', 'clienteCarga', 'numeroNfCliente', 'registroIncompleto', 'statusPagamento']) else request.args
    else:
        dados_corretos = request.args
    
    registros = obter_registros_com_filtros()
    
    if request.method == "POST":
        
        registros_exportacao = registros  

        if request.form.get("exportar_pdf"):
            logo_path = obter_url_absoluta_de_imagem("logo.png")
            html = render_template(
                "relatorios/relatorios_financeiros/relatorio_a_pagar_extrator/exportar_relatorio_a_pagar_extrator_pdf.html",
                logo_path=logo_path,
                changelog=changelog,
                dataHoje=dataHoje,
                dados_corretos=dados_corretos,
                registros=registros_exportacao
            )

            nome_arquivo_saida = f"relacao_extratores_a_pagar_{dataHoje}"
            return ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida, "Landscape")
        
        if request.form.get("exportar_excel"):
            dados_excel = []
            
            if not registros_exportacao:
                dados_excel.append({
                    "Extrator": "Nenhum registro encontrado",
                    "Data Entrega": "",
                    "Transportadora": "",
                    "Fornecedor": "",
                    "Produto/Bitola": "",
                    "Peso Ticket": "",
                    "Preço Extração (Ton.)": "",
                    "A pagar extrator": "",
                    "Status pagamento": "",
                })
            else:
                registros_por_extrator = {}
                
                for item in registros_exportacao:
                    extrator_obj = item.get("extrator")
                    extrator_id = extrator_obj.identificacao if extrator_obj else "Sem extrator"
                    
                    if extrator_id not in registros_por_extrator:
                        registros_por_extrator[extrator_id] = {}
                        
                    produto = item.get("produto", "Sem produto")
                    
                    if produto not in registros_por_extrator[extrator_id]:
                        registros_por_extrator[extrator_id][produto] = []
                        
                    registros_por_extrator[extrator_id][produto].append(item)

                for extrator_id in sorted(registros_por_extrator.keys()):
                    produtos_extrator = registros_por_extrator[extrator_id]
                    
                    dados_excel.append({
                        "Extrator": f"EXTRATOR: {extrator_id.upper()}",
                        "Data Entrega": "",
                        "Transportadora": "",
                        "Fornecedor": "",
                        "Produto/Bitola": "",
                        "Peso Ticket": "",
                        "Preço Extração (Ton.)": "",
                        "A pagar extrator": "",
                        "Status pagamento": "",
                    })
                    
                    total_extrator = 0
                    
                    for produto in sorted(produtos_extrator.keys()):
                        registros_produto = produtos_extrator[produto]
                        
                        dados_excel.append({
                            "Extrator": f"  Produto: {produto}",
                            "Data Entrega": "",
                            "Transportadora": "",
                            "Fornecedor": "",
                            "Produto/Bitola": "",
                            "Peso Ticket": "",
                            "Preço Extração (Ton.)": "",
                            "A pagar extrator": "",
                            "Status pagamento": "",
                        })
                        
                        total_produto = 0
                        
                        for item in registros_produto:
                            registro = item["registro"]
                            
                            data_entrega = "-"
                            if registro.data_entrega_ticket:
                                data_entrega = registro.data_entrega_ticket.strftime("%d/%m/%Y")
                            
                            transportadora = "-"
                            if (registro.solicitacao and 
                                registro.solicitacao.transportadora_exibicao and 
                                registro.solicitacao.transportadora_exibicao.identificacao):
                                transportadora = registro.solicitacao.transportadora_exibicao.identificacao
                            
                            fornecedor = "-"
                            if (registro.solicitacao and 
                                registro.solicitacao.fornecedor and 
                                registro.solicitacao.fornecedor.identificacao):
                                fornecedor = registro.solicitacao.fornecedor.identificacao
                            
                            produto_nome = "-"
                            bitola_nome = "-"
                            if (registro.solicitacao and 
                                registro.solicitacao.produto and 
                                registro.solicitacao.produto.nome):
                                produto_nome = registro.solicitacao.produto.nome
                            
                            if (registro.solicitacao and 
                                registro.solicitacao.bitola and 
                                registro.solicitacao.bitola.bitola):
                                bitola_nome = registro.solicitacao.bitola.bitola
                            
                            produto_bitola = f"{produto_nome} | {bitola_nome}" if produto_nome != "-" or bitola_nome != "-" else "-"
                            
                            peso_ticket = "-"
                            try:
                                registro_op = item.get("registro_operacional")
                                if registro_op and registro_op.peso_liquido_ticket:
                                    peso_ticket = f"{registro_op.peso_liquido_ticket}"
                                else:
                                    peso_ticket = "Sem peso"
                            except (KeyError, AttributeError):
                                peso_ticket = "Sem peso"
                            
                            preco_extracao = "-"
                            if registro.preco_custo_bitola_100:
                                preco_extracao = f"{(registro.preco_custo_bitola_100 / 100):,.2f}"
                            
                            valor_pagar_num = 0
                            if registro.valor_total_a_pagar_100:
                                valor_pagar_num = registro.valor_total_a_pagar_100 / 100
                                total_produto += valor_pagar_num
                                total_extrator += valor_pagar_num
                            
                            status = "Pendente"
                            if registro.situacao:
                                status = registro.situacao.situacao
                            
                            dados_excel.append({
                                "Extrator": "",
                                "Data Entrega": data_entrega,
                                "Transportadora": transportadora,
                                "Fornecedor": fornecedor,
                                "Produto/Bitola": produto_bitola,
                                "Peso Ticket": peso_ticket,
                                "Preço Extração (Ton.)": preco_extracao,
                                "A pagar extrator": f"R$ {valor_pagar_num:,.2f}" if valor_pagar_num > 0 else "-",
                                "Status pagamento": status,
                            })
                        
                        if registros_produto and total_produto > 0:
                            dados_excel.append({
                                "Extrator": "",
                                "Data Entrega": "",
                                "Transportadora": "",
                                "Fornecedor": "",
                                "Produto/Bitola": "",
                                "Peso Ticket": "",
                                "Preço Extração (Ton.)": "",
                                "A pagar extrator": f"TOTAL PRODUTO: R$ {total_produto:,.2f}",
                                "Status pagamento": "",
                            })
                        
                        dados_excel.append({
                            "Extrator": "",
                            "Data Entrega": "",
                            "Transportadora": "",
                            "Fornecedor": "",
                            "Produto/Bitola": "",
                            "Peso Ticket": "",
                            "Preço Extração (Ton.)": "",
                            "A pagar extrator": "",
                            "Status pagamento": "",
                        })
                    
                    if total_extrator > 0:
                        dados_excel.append({
                            "Extrator": "",
                            "Data Entrega": "",
                            "Transportadora": "",
                            "Fornecedor": "",
                            "Produto/Bitola": "",
                            "Peso Ticket": "",
                            "Preço Extração (Ton.)": "",
                            "A pagar extrator": f"TOTAL EXTRATOR: R$ {total_extrator:,.2f}",
                            "Status pagamento": "",
                        })
                    
                    dados_excel.append({
                        "Extrator": "",
                        "Data Entrega": "",
                        "Transportadora": "",
                        "Fornecedor": "",
                        "Produto/Bitola": "",
                        "Peso Ticket": "",
                        "Preço Extração (Ton.)": "",
                        "A pagar extrator": "",
                        "Status pagamento": "",
                    })

            nome_arquivo_saida = f"relatorio-extratores-a-pagar-{dataHoje}"
            return ManipulacaoArquivos.exportar_excel(dados_excel, nome_arquivo_saida)

    return render_template(
        "relatorios/relatorios_financeiros/relatorio_a_pagar_extrator/relatorio_a_pagar_extrator.html",
        registros=registros,
        bitola=bitola,
        produtos=produtos,
        statusPagamentos=statusPagamentos,
        dados_corretos=dados_corretos,
    )

