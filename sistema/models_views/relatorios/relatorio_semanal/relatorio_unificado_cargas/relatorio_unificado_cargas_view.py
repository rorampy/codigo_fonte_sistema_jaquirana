from datetime import datetime, timedelta, date
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem, formatar_float_para_brl, formatar_data_para_brl
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema._utilitarios import *
from sistema.models_views.configuracoes_gerais.situacao_pagamento.situacao_pagamento_model import SituacaoPagamentoModel
from sqlalchemy import case, func, and_, or_


@app.route("/relatorios/relatorio-semanal/unificado-cargas", methods=["GET", "POST"])
@login_required
@requires_roles
def relatorio_unificado_cargas():
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    dataHoje = datetime.now().strftime("%d-%m-%Y")

    semanas_disponiveis = UtilitariosSemana.obter_semanas_do_mes_atual()
    statusPagamentos = SituacaoPagamentoModel.listar_status()

    valor_padrao_semana = ""
    semana_atual_info = None

    for semana in semanas_disponiveis:
        if semana.get("is_atual", False):
            valor_padrao_semana = semana["valor"]
            semana_atual_info = semana
            break

    if not valor_padrao_semana and semanas_disponiveis:
        valor_padrao_semana = semanas_disponiveis[0]["valor"]
        semana_atual_info = semanas_disponiveis[0]

    if request.method == "POST":
        if any(request.form.values()) and not (request.form.get("exportar_pdf") or request.form.get("exportar_excel")):
            tipo_filtro = request.form.get("tipo_filtro", "semanal")
            semana_selecionada = request.form.get("semanaSelecionada")
            data_inicio_form = request.form.get("dataInicio")
            data_fim_form = request.form.get("dataFim")
            placa = request.form.get("placa")
            motorista = request.form.get("motorista")
            transportadora = request.form.get("transportadora")
            fornecedor = request.form.get("fornecedor")
            cliente = request.form.get("cliente")
            numero_nf = request.form.get("numeroNf")
            produto = request.form.get("produto")
            bitola = request.form.get("bitola")
            statusPagamentoCarga = request.form.get("statusPagamentoCarga")

            if tipo_filtro == "data" and data_inicio_form and data_fim_form:
                data_inicio = datetime.strptime(data_inicio_form, "%Y-%m-%d").date()
                data_fim = datetime.strptime(data_fim_form, "%Y-%m-%d").date()
            else:
                data_inicio, data_fim = UtilitariosSemana.processar_semana_selecionada(
                    semana_selecionada or valor_padrao_semana
                )

            registros = RegistroOperacionalModel.filtrar_registros_unificado_cargas(
                data_inicio=data_inicio,
                data_fim=data_fim,
                placa=placa,
                motorista=motorista,
                transportadora=transportadora,
                fornecedor=fornecedor,
                cliente=cliente,
                numero_nf=numero_nf,
                produto=produto,
                bitola=bitola,
                statusPagamentoCarga=statusPagamentoCarga
            )
            dados_corretos = request.form
        else:
            tipo_filtro = request.form.get("tipo_filtro", "semanal")
            semana_selecionada = request.form.get("semanaSelecionada")
            data_inicio_form = request.form.get("dataInicio")
            data_fim_form = request.form.get("dataFim")
            placa = request.form.get("placa")
            motorista = request.form.get("motorista")
            transportadora = request.form.get("transportadora")
            fornecedor = request.form.get("fornecedor")
            cliente = request.form.get("cliente")
            numero_nf = request.form.get("numeroNf")
            produto = request.form.get("produto")
            bitola = request.form.get("bitola")
            statusPagamentoCarga = request.form.get("statusPagamentoCarga")

            if any([tipo_filtro, semana_selecionada, data_inicio_form, data_fim_form, placa, motorista, transportadora, fornecedor, cliente, numero_nf, produto, bitola, statusPagamentoCarga]):
                if tipo_filtro == "data" and data_inicio_form and data_fim_form:
                    data_inicio = datetime.strptime(data_inicio_form, "%Y-%m-%d").date()
                    data_fim = datetime.strptime(data_fim_form, "%Y-%m-%d").date()
                else:
                    data_inicio, data_fim = UtilitariosSemana.processar_semana_selecionada(
                        semana_selecionada or valor_padrao_semana
                    )

                registros = RegistroOperacionalModel.filtrar_registros_unificado_cargas(
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    placa=placa,
                    motorista=motorista,
                    transportadora=transportadora,
                    fornecedor=fornecedor,
                    cliente=cliente,
                    numero_nf=numero_nf,
                    produto=produto,
                    bitola=bitola,
                    statusPagamentoCarga=statusPagamentoCarga
                )
            else:
                tipo_filtro = "semanal"
                if semana_atual_info:
                    data_inicio = semana_atual_info["inicio"]
                    data_fim = semana_atual_info["fim"]
                else:
                    data_inicio, data_fim = UtilitariosSemana.obter_datas_mes_atual()
                    
                registros = RegistroOperacionalModel.obter_registros_unificado_cargas()
            dados_corretos = request.form
    else:
        if any(request.args.values()):
            tipo_filtro = request.args.get("tipo_filtro", "semanal")
            semana_selecionada = request.args.get("semanaSelecionada")
            data_inicio_form = request.args.get("dataInicio")
            data_fim_form = request.args.get("dataFim")
            placa = request.args.get("placa")
            motorista = request.args.get("motorista")
            transportadora = request.args.get("transportadora")
            fornecedor = request.args.get("fornecedor")
            cliente = request.args.get("cliente")
            numero_nf = request.args.get("numeroNf")
            produto = request.args.get("produto")
            bitola = request.args.get("bitola")
            statusPagamentoCarga = request.args.get("statusPagamentoCarga")

            if tipo_filtro == "data" and data_inicio_form and data_fim_form:
                data_inicio = datetime.strptime(data_inicio_form, "%Y-%m-%d").date()
                data_fim = datetime.strptime(data_fim_form, "%Y-%m-%d").date()
            else:
                data_inicio, data_fim = UtilitariosSemana.processar_semana_selecionada(
                    semana_selecionada or valor_padrao_semana
                )

            registros = RegistroOperacionalModel.filtrar_registros_unificado_cargas(
                data_inicio=data_inicio,
                data_fim=data_fim,
                placa=placa,
                motorista=motorista,
                transportadora=transportadora,
                fornecedor=fornecedor,
                cliente=cliente,
                numero_nf=numero_nf,
                produto=produto,
                bitola=bitola,
                statusPagamentoCarga=statusPagamentoCarga
            )
            dados_corretos = request.args
        else:
            tipo_filtro = "semanal"
            if semana_atual_info:
                data_inicio = semana_atual_info["inicio"]
                data_fim = semana_atual_info["fim"]
            else:
                data_inicio, data_fim = UtilitariosSemana.obter_datas_mes_atual()

            registros = RegistroOperacionalModel.filtrar_registros_unificado_cargas(
                data_inicio=data_inicio, data_fim=data_fim
            )

            dados_corretos = {
                "tipo_filtro": tipo_filtro,
                "semanaSelecionada": valor_padrao_semana,
                "dataInicio": "",
                "dataFim": "",
                "placa": "",
                "motorista": "",
                "transportadora": "",
                "fornecedor": "",
                "cliente": "",
                "numeroNf": "",
                "produto": "",
                "bitola": "",
                "statusPagamentoCarga": "",
            }

    if request.method == "POST" and request.form.get("exportar_pdf"):
        logo_path = obter_url_absoluta_de_imagem("logo.png")
        html = render_template(
            "relatorios/relatorio_semanal/relatorio_unificado_cargas/exportar_relatorio_unificado_cargas_pdf.html",
            logo_path=logo_path,
            dataHoje=dataHoje,
            registros=registros,
            dados_corretos=dados_corretos,
            changelog=changelog,
            semanas_disponiveis=semanas_disponiveis,
        )

        nome_arquivo_saida = f"relatorio-unificado-cargas_{dataHoje}"
        resposta = ManipulacaoArquivos.gerar_pdf_from_html(
            html, nome_arquivo_saida, "Landscape"
        )
        return resposta

    if request.method == "POST" and request.form.get("exportar_excel"):
        dados_excel = []

        for item in registros:
            registro = item["registro"]

            dados_excel.append(
                {
                    "Data Entrega": (
                        formatar_data_para_brl(registro.data_entrega_ticket)
                        if registro.data_entrega_ticket
                        else ""
                    ),
                    "Placa": item.get("placa", "") or "",
                    "Transportadora": item.get("transportadora", "") or "",
                    "Origem": item.get("origem", "") or "",
                    "Cliente": item.get("cliente", "") or "",
                    "Produto": item.get("produto", "") or "",
                    "Bitola": item.get("bitola", "") or "",
                    "Número Nota Fiscal": f"{registro.numero_nota_fiscal_estorno} *" or "" if registro.estorno_nf else registro.numero_nota_fiscal or "",
                    "Peso Líquido (Ton)": registro.peso_liquido_ticket or 0,
                    "Valor Ton (R$)": (
                        round(item.get("valor_por_ton", 0) / 100, 2)
                        if item.get("valor_por_ton")
                        else 0
                    ),
                    "Total Fornecedor (R$)": (
                        round(item.get("custo_fornecedor", 0) / 100, 2)
                        if item.get("custo_fornecedor")
                        else 0
                    ),
                    "Valor Frete (R$)": (
                        round(item.get('valor_frete_ton', 0) / 100, 2)
                        if item.get("valor_frete_ton")
                        else 0
                    ),
                    "Custo Frete (R$)": (
                        round(item.get("custo_frete", 0) / 100, 2)
                        if item.get("custo_frete")
                        else 0
                    ),
                }
            )

        nome_arquivo_saida = f"relatorio-unificado-cargas_{dataHoje}"
        resposta = ManipulacaoArquivos.exportar_excel(dados_excel, nome_arquivo_saida)
        return resposta

    if request.method == "GET":
        tipo_filtro = request.args.get("tipo_filtro", "semanal")
    else:
        tipo_filtro = request.form.get("tipo_filtro", "semanal")

    return render_template(
        "relatorios/relatorio_semanal/relatorio_unificado_cargas/relatorio_unificado_cargas.html",
        registros=registros,
        dados_corretos=dados_corretos,
        changelog=changelog,
        semanas_disponiveis=semanas_disponiveis,
        tipo_filtro=tipo_filtro,
        dataInicio=data_inicio,
        statusPagamentos=statusPagamentos,
        dataFim=data_fim
    )