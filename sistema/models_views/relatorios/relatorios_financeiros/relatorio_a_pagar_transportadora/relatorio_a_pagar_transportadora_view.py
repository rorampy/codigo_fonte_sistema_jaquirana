from datetime import datetime
from sistema import app, requires_roles, obter_url_absoluta_de_imagem
from flask import render_template, request
from flask_login import login_required
from sistema.models_views.faturamento.cargas_a_faturar.transportadora.frete_a_pagar_model import FretePagarModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
from sistema.models_views.configuracoes_gerais.situacao_pagamento.situacao_pagamento_model import SituacaoPagamentoModel
from sistema.models_views.importacao_ofx.importacao_ofx_view import verificar_e_limpar_conciliacao_incorreta
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema._utilitarios import *

@app.route("/relatorios/relatorios-financeiros/a-pagar-frete", methods=["GET", "POST"])
@login_required
@requires_roles
def relatorio_a_pagar_fretes():
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    dataHoje = datetime.now().strftime("%d-%m-%Y")
    bitola = BitolaModel.listar_bitolas_ativas()
    produtos = ProdutoModel.listar_produtos()
    statusPagamentos = SituacaoPagamentoModel.listar_status()

    verificar_e_limpar_conciliacao_incorreta('pagamento_frete') 
    
    def obter_registros_com_filtros():
        filtros_source = request.form if request.method == "POST" and any(request.form.values()) else request.args
        
        if any(filtros_source.values()):
            data_inicio_str = filtros_source.get("dataInicio")
            data_fim_str = filtros_source.get("dataFim")
            placa = filtros_source.get("placaCargaCliente")
            motorista = filtros_source.get("motoristaCargaCliente")
            transportadora = filtros_source.get("tranpostadoraCargaCliente")
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
            
            return FretePagarModel.filtrar_frete_transportadora_agrupados(
                data_inicio=data_inicio,
                data_fim=data_fim,
                placa=placa,
                motorista=motorista,
                transportadora=transportadora,
                fornecedor=fornecedor,
                cliente=cliente,
                numero_nf=numero_nf,
                statusPagamento=statusPagamento
            )
        else:
            return FretePagarModel.obter_frete_transportadora_agrupados()
    
    if request.method == "POST":
        dados_corretos = request.form if any(request.form.get(k) for k in ['dataInicio', 'dataFim', 'placaCargaCliente', 'motoristaCargaCliente', 'tranpostadoraCargaCliente', 'fornecedorCargaCliente', 'clienteCarga', 'numeroNfCliente', 'registroIncompleto', 'statusPagamento']) else request.args
    else:
        dados_corretos = request.args
    
    registros = obter_registros_com_filtros()
    
    if request.method == "POST":
        registros_exportacao = registros  

        if request.form.get("exportar_pdf"):
            logo_path = obter_url_absoluta_de_imagem("logo.png")
            html = render_template(
                "relatorios/relatorios_financeiros/relatorio_a_pagar_frete/exportar_relatorio_a_pagar_frete_pdf.html",
                logo_path=logo_path,
                changelog=changelog,
                dataHoje=dataHoje,
                dados_corretos=dados_corretos,
                registros=registros_exportacao
            )

            nome_arquivo_saida = f"relacao_fretes_a_pagar_{dataHoje}"
            return ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida, "Landscape")
        
        if request.form.get("exportar_excel"):
            dados_excel = []
            
            if not registros_exportacao:
                dados_excel.append({
                    "Frete": "Nenhum registro encontrado",
                    "Data Entrega": "",
                    "Fornecedor": "",
                    "Bitola": "",
                    "Número NF": "",
                    "A pagar frete": "",
                    "Status pagamento": "",
                    "Placa/Motorista": "",
                    "Incompleto": "",
                })
            else:
                registros_por_origem = {}
                
                for item in registros_exportacao:
                    origem = item.get("origem", "Sem origem")
                    
                    if origem not in registros_por_origem:
                        registros_por_origem[origem] = {}
                        
                    produto = item.get("produto", "Sem produto")
                    
                    if produto not in registros_por_origem[origem]:
                        registros_por_origem[origem][produto] = []
                        
                    registros_por_origem[origem][produto].append(item)

                for origem in sorted(registros_por_origem.keys()):
                    produtos_origem = registros_por_origem[origem]
                    
                    dados_excel.append({
                        "Frete": f"FRETE: {origem.upper()}",
                        "Data Entrega": "",
                        "Fornecedor": "",
                        "Bitola": "",
                        "Número NF": "",
                        "A pagar frete": "",
                        "Status pagamento": "",
                        "Placa/Motorista": "",
                        "Incompleto": "",
                    })
                    
                    for produto in sorted(produtos_origem.keys()):
                        registros_produto = produtos_origem[produto]
                        
                        dados_excel.append({
                            "Frete": f"  Produto: {produto}",
                            "Data Entrega": "",
                            "Fornecedor": "",
                            "Bitola": "",
                            "Número NF": "",
                            "A pagar frete": "",
                            "Status pagamento": "",
                            "Placa/Motorista": "",
                            "Incompleto": "",
                        })
                        
                        total_produto = 0
                        
                        for item in registros_produto:
                            registro = item["registro"]
                            
                            data_entrega = "-"
                            if registro.data_entrega_ticket:
                                data_entrega = registro.data_entrega_ticket.strftime("%d/%m/%Y")
                            
                            fornecedor = "-"
                            if (registro.solicitacao and 
                                registro.solicitacao.fornecedor and 
                                registro.solicitacao.fornecedor.identificacao):
                                fornecedor = registro.solicitacao.fornecedor.identificacao
                            
                            bitola = "-"
                            if (registro.solicitacao and 
                                registro.solicitacao.bitola and 
                                registro.solicitacao.bitola.bitola):
                                bitola = registro.solicitacao.bitola.bitola
                            
                            numero_nf = "-"
                            registro_op = item.get("registro_operacional")
                            if registro_op and registro_op.estorno_nf:
                                numero_nf = f"{registro_op.numero_nota_fiscal_estorno} *"
                            elif registro_op and registro_op.numero_nota_fiscal:
                                numero_nf = str(registro_op.numero_nota_fiscal)
                            else:
                                numero_nf = "-"
                            
                            valor_pagar = 0
                            if registro.valor_total_a_pagar_100:
                                valor_pagar = registro.valor_total_a_pagar_100 / 100
                                total_produto += valor_pagar
                            
                            status = "Pendente"
                            if registro.situacao:
                                status = registro.situacao.situacao
                            
                            placa = "-"
                            motorista = ""
                            
                            if (registro.solicitacao and 
                                registro.solicitacao.veiculo and 
                                registro.solicitacao.veiculo.placa_veiculo):
                                placa = registro.solicitacao.veiculo.placa_veiculo
                            
                            if (registro.solicitacao and 
                                registro.solicitacao.motorista and 
                                registro.solicitacao.motorista.nome_completo):
                                nome_split = registro.solicitacao.motorista.nome_completo.split()
                                if len(nome_split) > 1:
                                    motorista = f"{nome_split[0]} {nome_split[1][0]}."
                                elif len(nome_split) >= 1:
                                    motorista = nome_split[0]
                            
                            placa_motorista = f"{placa} | {motorista}" if motorista else placa
                            incompleto = "Sim" if registro.incompleto else "Não"
                            
                            dados_excel.append({
                                "Frete": "",
                                "Data Entrega": data_entrega,
                                "Fornecedor": fornecedor,
                                "Bitola": bitola,
                                "Número NF": numero_nf,
                                "A pagar frete": f"R$ {valor_pagar:,.2f}" if valor_pagar > 0 else "-",
                                "Status pagamento": status,
                                "Placa/Motorista": placa_motorista,
                                "Incompleto": incompleto,
                            })
                        
                        if registros_produto and total_produto > 0:
                            dados_excel.append({
                                "Frete": "",
                                "Data Entrega": "",
                                "Fornecedor": "",
                                "Bitola": "",
                                "Número NF": "",
                                "A pagar frete": f"TOTAL A PAGAR: R$ {total_produto:,.2f}",
                                "Status pagamento": "",
                                "Placa/Motorista": "",
                                "Incompleto": "",
                            })
                        
                        dados_excel.append({
                            "Frete": "",
                            "Data Entrega": "",
                            "Fornecedor": "",
                            "Bitola": "",
                            "Número NF": "",
                            "A pagar frete": "",
                            "Status pagamento": "",
                            "Placa/Motorista": "",
                            "Incompleto": "",
                        })
                    
                    dados_excel.append({
                        "Frete": "",
                        "Data Entrega": "",
                        "Fornecedor": "",
                        "Bitola": "",
                        "Número NF": "",
                        "A pagar frete": "",
                        "Status pagamento": "",
                        "Placa/Motorista": "",
                        "Incompleto": "",
                    })

            nome_arquivo_saida = f"relatorio-fretes-a-pagar-{dataHoje}"
            return ManipulacaoArquivos.exportar_excel(dados_excel, nome_arquivo_saida)

    return render_template(
        "relatorios/relatorios_financeiros/relatorio_a_pagar_frete/relatorio_a_pagar_frete.html",
        registros=registros,
        bitola=bitola,
        produtos=produtos,
        statusPagamentos=statusPagamentos,
        dados_corretos=dados_corretos,
    )

