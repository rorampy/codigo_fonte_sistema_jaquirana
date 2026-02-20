from datetime import datetime
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem, formatar_float_para_brl, formatar_data_para_brl, formatar_float_para_brl_sem_cifrao
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema._utilitarios import *


@app.route("/relatorios/relatorio-cargas/cargas-transportadora", methods=["GET", "POST"])
@login_required
@requires_roles
def relatorio_cargas_transportadora():
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    dataHoje = datetime.now().strftime("%d-%m-%Y")

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

            registros = RegistroOperacionalModel.filtrar_registros_carga_transportadora(
                data_inicio=data_inicio,
                data_fim=data_fim,
                placa=placa,
                motorista=motorista,
                transportadora=transportadora,
                fornecedor=fornecedor,
                cliente=cliente,
                numero_nf=numero_nf,
                produto=produtoFiltro,
            )
            dados_corretos = request.form
        else:
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
                registros = RegistroOperacionalModel.filtrar_registros_carga_transportadora(
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    placa=placa,
                    motorista=motorista,
                    transportadora=transportadora,
                    fornecedor=fornecedor,
                    cliente=cliente,
                    numero_nf=numero_nf,
                    produto=produtoFiltro,
                )
            else:
                registros = RegistroOperacionalModel.obter_registros_carga_transportadora()
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

            registros = RegistroOperacionalModel.filtrar_registros_carga_transportadora(
                data_inicio=data_inicio,
                data_fim=data_fim,
                placa=placa,
                motorista=motorista,
                transportadora=transportadora,
                fornecedor=fornecedor,
                cliente=cliente,
                numero_nf=numero_nf,
                produto=produtoFiltro,
            )
            dados_corretos = request.args
        else:
            registros = RegistroOperacionalModel.obter_registros_carga_transportadora()
            dados_corretos = {}

    if request.method == "POST" and request.form.get("exportar_pdf"):
        logo_path = obter_url_absoluta_de_imagem("logo.png")

        html = render_template(
            "relatorios/relatorio_de_cargas/relatorio_cargas_transportadora/exportar_relatorio_cargas_transportadora_pdf.html",
            logo_path=logo_path,
            dataHoje=dataHoje,
            registros=registros,
            dados_corretos=dados_corretos,
            changelog=changelog,
        )

        nome_arquivo_saida = f"relatorio-cargas-transportadora_{dataHoje}"
        resposta = ManipulacaoArquivos.gerar_pdf_from_html(
            html, nome_arquivo_saida, "Landscape"
        )
        return resposta

    if request.method == "POST" and request.form.get("exportar_excel"):
        registros_por_transportadora = {}
        totais_por_transportadora = {}
        
        for item in registros:
            registro = item["registro"]
            transportadora = item["transportadora"] or "Sem Transportadora"
            produto = item["produto"]
            bitola = item["bitola"]
            valor_pagar = item.get("valor_frete", 0)
            peso_liquido = float(registro.peso_liquido_ticket) if registro.peso_liquido_ticket else 0

            if transportadora not in registros_por_transportadora:
                registros_por_transportadora[transportadora] = []
                totais_por_transportadora[transportadora] = {
                    "peso_total": 0,
                    "valor_total": 0,
                    "quantidade_cargas": 0
                }

            registro_data = {
                "Data Entrega": (
                    formatar_data_para_brl(registro.data_entrega_ticket)
                    if registro.data_entrega_ticket
                    else ""
                ),
                "Transportadora": transportadora,
                "Produto": produto or "",
                "Bitola": bitola or "",
                "Placa": (
                    registro.solicitacao.veiculo.placa_veiculo
                    if registro.solicitacao and registro.solicitacao.veiculo
                    else registro.placa_ticket or ""
                ),
                "Peso Líquido (Ton)": peso_liquido,
                "Motorista": (
                    registro.solicitacao.motorista.nome_completo
                    if registro.solicitacao and registro.solicitacao.motorista
                    else registro.motorista_ticket or ""
                ),
                "Valor a Pagar Transportadora (R$)": (
                    round(valor_pagar / 100, 2) if valor_pagar else 0
                ),
            }
            
            registros_por_transportadora[transportadora].append(registro_data)
            
            totais_por_transportadora[transportadora]["peso_total"] += peso_liquido
            totais_por_transportadora[transportadora]["valor_total"] += round(valor_pagar / 100, 2) if valor_pagar else 0
            totais_por_transportadora[transportadora]["quantidade_cargas"] += 1

        dados_excel = []
        
        for transportadora, registros_transportadora in registros_por_transportadora.items():
            dados_excel.append({
                "Data Entrega": f"TRANSPORTADORA: {transportadora}",
                "Transportadora": "",
                "Produto": "",
                "Bitola": "",
                "Placa": "",
                "Peso Líquido (Ton)": "",
                "Motorista": "",
                "Valor a Pagar Transportadora (R$)": "",
            })
            
            for registro in registros_transportadora:
                dados_excel.append(registro)
            
            totais = totais_por_transportadora[transportadora]
            dados_excel.append({
                "Data Entrega": f"TOTAL {transportadora}:",
                "Transportadora": "",
                "Produto": "",
                "Bitola": "",
                "Placa": f"Qtd Cargas: {totais['quantidade_cargas']}",
                "Peso Líquido (Ton)": f"Peso Total (Ton.): {round(totais['peso_total'], 2)}",
                "Motorista": "",
                "Valor a Pagar Transportadora (R$)": round(totais["valor_total"], 2),
            })
            
            dados_excel.append({
                "Data Entrega": "",
                "Transportadora": "",
                "Produto": "",
                "Bitola": "",
                "Placa": "",
                "Peso Líquido (Ton)": "",
                "Motorista": "",
                "Valor a Pagar Transportadora (R$)": "",
            })

        nome_arquivo_saida = f"relatorio-cargas-transportadora_{dataHoje}"
        resposta = ManipulacaoArquivos.exportar_excel(
            dados_excel, nome_arquivo_saida
        )
        return resposta

    return render_template(
        "/relatorios/relatorio_de_cargas/relatorio_cargas_transportadora/relatorio_cargas_transportadora.html",
        registros=registros,
        dados_corretos=dados_corretos,
        changelog=changelog,
    )
