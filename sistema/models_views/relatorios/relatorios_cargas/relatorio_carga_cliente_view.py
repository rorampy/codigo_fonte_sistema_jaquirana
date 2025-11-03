from datetime import datetime
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem, formatar_float_para_brl, formatar_data_para_brl, formatar_float_para_brl_sem_cifrao
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required
from sistema.models_views.controle_carga.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema._utilitarios import *


@app.route("/relatorios/relatorio-cargas/cargas-cliente", methods=["GET", "POST"])
@login_required
@requires_roles
def relatorio_cargas_cliente():
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    dataHoje = datetime.now().strftime("%d-%m-%Y")

    # Para exportações (POST), usar os dados do formulário
    if request.method == "POST":
        if any(request.form.values()) and not (request.form.get("exportar_pdf") or request.form.get("exportar_excel")):
            data_inicio = request.form.get("dataInicio")
            data_fim = request.form.get("dataFim")
            placa = request.form.get("placaCargaCliente")
            motorista = request.form.get("motoristaCargaCliente")
            transportadora = request.form.get("tranpostadoraCargaCliente")
            fornecedor = request.form.get("fornecedorCargaCliente")
            cliente = request.form.get("clienteCarga")
            numero_nf = request.form.get("numeroNfCliente")
            produtoFiltro = request.form.get("produtoFiltro")

            registros = RegistroOperacionalModel.filtrar_registros_carga_cliente(
                data_inicio=data_inicio,
                data_fim=data_fim,
                placa=placa,
                motorista=motorista,
                transportadora=transportadora,
                fornecedor=fornecedor,
                cliente=cliente,
                numero_nf=numero_nf,
                produto=produtoFiltro
            )
            dados_corretos = request.form
        else:
            # Para exportações, reaplicar os filtros baseados nos hidden fields do form
            data_inicio = request.form.get("dataInicio")
            data_fim = request.form.get("dataFim")
            placa = request.form.get("placaCargaCliente")
            motorista = request.form.get("motoristaCargaCliente")
            transportadora = request.form.get("tranpostadoraCargaCliente")
            fornecedor = request.form.get("fornecedorCargaCliente")
            cliente = request.form.get("clienteCarga")
            numero_nf = request.form.get("numeroNfCliente")
            produtoFiltro = request.form.get("produtoFiltro")

            if any([data_inicio, data_fim, placa, motorista, transportadora, fornecedor, cliente, numero_nf, produtoFiltro]):
                registros = RegistroOperacionalModel.filtrar_registros_carga_cliente(
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    placa=placa,
                    motorista=motorista,
                    transportadora=transportadora,
                    fornecedor=fornecedor,
                    cliente=cliente,
                    numero_nf=numero_nf,
                    produto=produtoFiltro
                )
            else:
                registros = RegistroOperacionalModel.obter_registros_carga_agrupados()
            dados_corretos = request.form
    else:
        if any(request.args.values()):
            data_inicio = request.args.get("dataInicio")
            data_fim = request.args.get("dataFim")
            placa = request.args.get("placaCargaCliente")
            motorista = request.args.get("motoristaCargaCliente")
            transportadora = request.args.get("tranpostadoraCargaCliente")
            fornecedor = request.args.get("fornecedorCargaCliente")
            cliente = request.args.get("clienteCarga")
            numero_nf = request.args.get("numeroNfCliente")
            produtoFiltro = request.args.get("produtoFiltro")

            registros = RegistroOperacionalModel.filtrar_registros_carga_cliente(
                data_inicio=data_inicio,
                data_fim=data_fim,
                placa=placa,
                motorista=motorista,
                transportadora=transportadora,
                fornecedor=fornecedor,
                cliente=cliente,
                numero_nf=numero_nf,
                produto=produtoFiltro
            )
            dados_corretos = request.args
        else:
            registros = RegistroOperacionalModel.obter_registros_carga_agrupados()
            dados_corretos = {}

    if request.method == "POST" and request.form.get("exportar_pdf"):
        logo_path = obter_url_absoluta_de_imagem("logo.png")
        html = render_template(
            "relatorios/relatorio_de_cargas/relatorio_cargas_cliente/exportar_relatorio_cargas_cliente_pdf.html",
            logo_path=logo_path,
            dataHoje=dataHoje,
            registros=registros,
            dados_corretos=dados_corretos,
            changelog=changelog,
        )

        nome_arquivo_saida = f"relatorio-cargas-cliente-{dataHoje}"
        resposta = ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida, 'landscape')
        return resposta

    if request.method == "POST" and request.form.get("exportar_excel"):
        dados_excel = []
        
        registros_por_cliente = {}
        totais_por_cliente = {}
        
        for item in registros:
            registro = item["registro"]
            cliente_nome = (
                registro.solicitacao.cliente.identificacao
                if registro.solicitacao.cliente_id
                else "Cliente não identificado"
            )
            valor_frete = registro.valor_total_nota_100 or 0
            
            if cliente_nome not in registros_por_cliente:
                registros_por_cliente[cliente_nome] = []
                totais_por_cliente[cliente_nome] = 0
                
            registros_por_cliente[cliente_nome].append(item)
            totais_por_cliente[cliente_nome] += valor_frete

        for cliente in sorted(registros_por_cliente.keys()):
            registros_cliente = registros_por_cliente[cliente]
            
            # Linha de cabeçalho do cliente
            dados_excel.append(
                {
                    "Data Entrega e Cliente": cliente.upper(),
                    "Placa": "",
                    "Origem": "",
                    "Cliente": "",
                    "Produto/Bitola": "",
                    "NF": "",
                    "Peso Liquido (Ton)": "",
                    "Valor Frete/Ton": "",
                    "Total Frete": "",
                }
            )
            
            # Dados do cliente
            for item in registros_cliente:
                registro = item["registro"]

                dados_excel.append(
                    {
                        "Data Entrega e Cliente": (
                            formatar_data_para_brl(registro.data_entrega_ticket)
                            if registro.data_entrega_ticket
                            else ""
                        ),
                        "Placa": (
                            registro.solicitacao.veiculo.placa_veiculo
                            if registro.solicitacao
                            and registro.solicitacao.veiculo
                            and registro.solicitacao.veiculo.placa_veiculo
                            else ""
                        ),
                        "Origem": (
                            registro.solicitacao.floresta.identificacao
                            if registro.solicitacao.floresta_id
                            else (
                                registro.solicitacao.fornecedor.identificacao
                                if registro.solicitacao.fornecedor_id
                                else ""
                            )
                        ),
                        "Cliente": cliente,
                        "Produto/Bitola": (
                            f"{registro.solicitacao.produto.nome} | {registro.solicitacao.bitola.bitola}"
                            if registro.solicitacao.produto_id and registro.solicitacao.bitola_id
                            else (registro.solicitacao.produto.nome if registro.solicitacao.produto_id else "") + 
                                 (registro.solicitacao.bitola.bitola if registro.solicitacao.bitola_id else "")
                        ),
                        "NF": f"{registro.numero_nota_fiscal_estorno} *" if registro.estorno_nf else (registro.numero_nota_fiscal or ""),
                        "Peso Liquido (Ton)": registro.peso_liquido_ticket or 0,
                        "Valor Frete/Ton": (
                            round(registro.valor_total_nota_100 / 100 / registro.peso_liquido_ticket, 2)
                            if registro.valor_total_nota_100 and registro.peso_liquido_ticket and registro.peso_liquido_ticket > 0
                            else 0
                        ),
                        "Total Frete": round(registro.valor_total_nota_100 / 100, 2) if registro.valor_total_nota_100 else 0,
                    }
                )
                            
            # Linha de total por cliente
            if registros_cliente:
                dados_excel.append(
                    {
                        "Data Entrega e Cliente": "",
                        "Placa": "",
                        "Origem": "",
                        "Cliente": "",
                        "Produto/Bitola": "",
                        "NF": "",
                        "Peso Liquido (Ton)": "",
                        "Valor Frete/Ton": "Total a receber    R$",
                        "Total Frete": round(totais_por_cliente[cliente] / 100, 2),
                    }
                )
                
                # Linha em branco para separar clientes
                dados_excel.append(
                    {
                        "Data Entrega e Cliente": "",
                        "Placa": "",
                        "Origem": "",
                        "Cliente": "",
                        "Produto/Bitola": "",
                        "NF": "",
                        "Peso Liquido (Ton)": "",
                        "Valor Frete/Ton": "",
                        "Total Frete": "",
                    }
                )

        nome_arquivo_saida = f"relatorio-cargas-cliente-{dataHoje}"
        resposta = ManipulacaoArquivos.exportar_excel(dados_excel, nome_arquivo_saida)
        return resposta

    return render_template(
        "/relatorios/relatorio_de_cargas/relatorio_cargas_cliente/relatorio_cargas_cliente.html",
        registros=registros,
        dados_corretos=dados_corretos,
        changelog=changelog,
    )