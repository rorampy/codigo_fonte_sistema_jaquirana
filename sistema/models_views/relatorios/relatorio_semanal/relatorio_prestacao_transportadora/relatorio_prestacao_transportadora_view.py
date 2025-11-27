from datetime import datetime, timedelta, date
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem, formatar_float_para_brl, formatar_data_para_brl, formatar_float_para_brl_sem_cifrao
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema._utilitarios import *


@app.route(
    "/relatorios/relatorio-semanal/relatorio-prestacao-transportadora",
    methods=["GET", "POST"],
)
@login_required
@requires_roles
def relatorio_prestacao_transportadora():
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    dataHoje = datetime.now().strftime("%d-%m-%Y")

    semanas_disponiveis = UtilitariosSemana.obter_semanas_do_mes_atual()
    produto = ProdutoModel.listar_produtos()
    bitola = BitolaModel.listar_bitolas_ativas()

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

    # Para exportações (POST), usar os dados do formulário
    if request.method == "POST":
        if any(request.form.values()) and not (request.form.get("exportar_pdf") or request.form.get("exportar_excel")):
            tipo_filtro = request.form.get("tipo_filtro", "semanal")
            semana_selecionada = request.form.get("semanaSelecionada", "")
            data_inicio_form = request.form.get("dataInicio")
            data_fim_form = request.form.get("dataFim")
            fornecedor = request.form.get("fornecedorCargaCliente", "")
            numero_nf = request.form.get("numeroNfCliente", "")
            clienteFiltro = request.form.get("clienteFiltro", "")
            origemFiltro = request.form.get("origemFiltro", "")
            transportadoraFiltro = request.form.get("transportadoraFiltro", "")
            placaFiltro = request.form.get("placaFiltro", "")
            produtoFiltro = request.form.get("produtoFiltro", "")
            bitolaFiltro = request.form.get("bitolaFiltro", "")

            # Determinar data_inicio e data_fim baseado no tipo de filtro
            if tipo_filtro == "data" and data_inicio_form and data_fim_form:
                data_inicio = datetime.strptime(data_inicio_form, "%Y-%m-%d").date()
                data_fim = datetime.strptime(data_fim_form, "%Y-%m-%d").date()
            else:
                # Usar filtro semanal
                data_inicio, data_fim = UtilitariosSemana.processar_semana_selecionada(
                    semana_selecionada or valor_padrao_semana
                )

            registros = RegistroOperacionalModel.filtrar_registros_carga_transportadora(
                data_inicio=data_inicio,
                data_fim=data_fim,
                fornecedor=fornecedor,
                numero_nf=numero_nf,
                produto=produtoFiltro,
                cliente=clienteFiltro,
                bitola=bitolaFiltro,
                origem=origemFiltro,
                transportadora=transportadoraFiltro,
                placa=placaFiltro
            )
            dados_corretos = request.form
        else:
            # Para exportações, reaplicar os filtros baseados nos hidden fields do form
            tipo_filtro = request.form.get("tipo_filtro", "semanal")
            semana_selecionada = request.form.get("semanaSelecionada", "")
            data_inicio_form = request.form.get("dataInicio")
            data_fim_form = request.form.get("dataFim")
            fornecedor = request.form.get("fornecedorCargaCliente", "")
            numero_nf = request.form.get("numeroNfCliente", "")
            clienteFiltro = request.form.get("clienteFiltro", "")
            origemFiltro = request.form.get("origemFiltro", "")
            transportadoraFiltro = request.form.get("transportadoraFiltro", "")
            placaFiltro = request.form.get("placaFiltro", "")
            produtoFiltro = request.form.get("produtoFiltro", "")
            bitolaFiltro = request.form.get("bitolaFiltro", "")

            if any([tipo_filtro, semana_selecionada, data_inicio_form, data_fim_form, fornecedor, numero_nf, clienteFiltro, origemFiltro, transportadoraFiltro, placaFiltro, produtoFiltro, bitolaFiltro]):
                # Determinar data_inicio e data_fim baseado no tipo de filtro
                if tipo_filtro == "data" and data_inicio_form and data_fim_form:
                    data_inicio = datetime.strptime(data_inicio_form, "%Y-%m-%d").date()
                    data_fim = datetime.strptime(data_fim_form, "%Y-%m-%d").date()
                else:
                    # Usar filtro semanal
                    data_inicio, data_fim = UtilitariosSemana.processar_semana_selecionada(
                        semana_selecionada or valor_padrao_semana
                    )

                registros = RegistroOperacionalModel.filtrar_registros_carga_transportadora(
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    fornecedor=fornecedor,
                    numero_nf=numero_nf,
                    produto=produtoFiltro,
                    cliente=clienteFiltro,
                    bitola=bitolaFiltro,
                    origem=origemFiltro,
                    transportadora=transportadoraFiltro,
                    placa=placaFiltro
                )
            else:
                # Usar semana atual como padrão para exportações
                tipo_filtro = "semanal"
                if semana_atual_info:
                    data_inicio = semana_atual_info["inicio"]
                    data_fim = semana_atual_info["fim"]
                else:
                    data_inicio, data_fim = UtilitariosSemana.obter_datas_mes_atual()

                registros = RegistroOperacionalModel.filtrar_registros_carga_transportadora(
                    data_inicio=data_inicio, data_fim=data_fim
                )
            dados_corretos = request.form
    else:
        # Para GET, usar args
        if any(request.args.values()):
            tipo_filtro = request.args.get("tipo_filtro", "semanal")
            semana_selecionada = request.args.get("semanaSelecionada", "")
            data_inicio_form = request.args.get("dataInicio")
            data_fim_form = request.args.get("dataFim")
            fornecedor = request.args.get("fornecedorCargaCliente", "")
            numero_nf = request.args.get("numeroNfCliente", "")
            clienteFiltro = request.args.get("clienteFiltro", "")
            origemFiltro = request.args.get("origemFiltro", "")
            transportadoraFiltro = request.args.get("transportadoraFiltro", "")
            placaFiltro = request.args.get("placaFiltro", "")
            produtoFiltro = request.args.get("produtoFiltro", "")
            bitolaFiltro = request.args.get("bitolaFiltro", "")

            # Determinar data_inicio e data_fim baseado no tipo de filtro
            if tipo_filtro == "data" and data_inicio_form and data_fim_form:
                data_inicio = datetime.strptime(data_inicio_form, "%Y-%m-%d").date()
                data_fim = datetime.strptime(data_fim_form, "%Y-%m-%d").date()
            else:
                # Usar filtro semanal
                data_inicio, data_fim = UtilitariosSemana.processar_semana_selecionada(
                    semana_selecionada or valor_padrao_semana
                )

            registros = RegistroOperacionalModel.filtrar_registros_carga_transportadora(
                data_inicio=data_inicio,
                data_fim=data_fim,
                fornecedor=fornecedor,
                numero_nf=numero_nf,
                produto=produtoFiltro,
                cliente=clienteFiltro,
                bitola=bitolaFiltro,
                origem=origemFiltro,
                transportadora=transportadoraFiltro,
                placa=placaFiltro
            )
            dados_corretos = request.args
        else:
            # GET sem parâmetros - usar semana atual como padrão
            tipo_filtro = "semanal"
            if semana_atual_info:
                data_inicio = semana_atual_info["inicio"]
                data_fim = semana_atual_info["fim"]
            else:
                data_inicio, data_fim = UtilitariosSemana.obter_datas_mes_atual()

            registros = RegistroOperacionalModel.filtrar_registros_carga_transportadora(
                data_inicio=data_inicio, data_fim=data_fim
            )

            dados_corretos = {
                "tipo_filtro": tipo_filtro,
                "semanaSelecionada": valor_padrao_semana,
                "dataInicio": data_inicio.strftime("%Y-%m-%d") if data_inicio else "",
                "dataFim": data_fim.strftime("%Y-%m-%d") if data_fim else "",
                "fornecedorCargaCliente": "",
                "numeroNfCliente": "",
                "produtoFiltro": "",
                "clienteFiltro": "",
                "bitolaFiltro": "",
                "transportadoraFiltro": "",
                "placaFiltro": "",
                "origemFiltro": ""
            }

    if request.method == "POST" and request.form.get("exportar_pdf"):
        logo_path = obter_url_absoluta_de_imagem("logo.png")
        html = render_template(
            "/relatorios/relatorio_semanal/relatorio_prestacao_transportadora/exportar_relatorio_prestacao_transportadora_pdf.html",
            logo_path=logo_path,
            dataHoje=dataHoje,
            registros=registros,
            dados_corretos=dados_corretos,
            changelog=changelog,
            semanas_disponiveis=semanas_disponiveis,
        )

        nome_arquivo_saida = f"relatorio-prestacao-contas-transportadora-pdf-{dataHoje}"
        resposta = ManipulacaoArquivos.gerar_pdf_from_html(
            html, nome_arquivo_saida)
        return resposta

    if request.method == "POST" and request.form.get("exportar_excel"):
        dados_excel = []
        
        registros_por_transportadora = {}
        totais_por_transportadora = {}
        
        for item in registros:
            transportadora = item.get("transportadora", "Sem transportadora")
            valor_frete = item.get("valor_frete", 0)
            
            if transportadora not in registros_por_transportadora:
                registros_por_transportadora[transportadora] = []
                totais_por_transportadora[transportadora] = 0
                
            registros_por_transportadora[transportadora].append(item)
            totais_por_transportadora[transportadora] += valor_frete

        for transportadora in sorted(registros_por_transportadora.keys()):
            registros_transportadora = registros_por_transportadora[transportadora]
            
            dados_excel.append(
                {
                    "Data Entrega e Transportadora": transportadora.upper(),
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
            
            for item in registros_transportadora:
                registro = item["registro"]
                origem = item.get("origem", "")
                produto = item.get("produto", "")
                bitola = item.get("bitola", "")
                valor_frete_por_produto = item.get("valor_frete_por_produto", 0)
                valor_frete = item.get("valor_frete", 0)
                cliente = item.get("cliente", "")

                dados_excel.append(
                    {
                        "Data Entrega e Transportadora": (
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
                        "Origem": origem,
                        "Cliente": (
                            cliente.identificacao
                            if hasattr(cliente, "identificacao") and cliente.identificacao
                            else str(cliente) if cliente else ""
                        ),
                        "Produto/Bitola": (
                            f"{produto} | {bitola}"
                            if produto and bitola
                            else produto or bitola or ""
                        ),
                        "NF": f"{registro.numero_nota_fiscal_estorno} *" or "" if registro.estorno_nf else registro.numero_nota_fiscal or "",
                        "Peso Liquido (Ton)": registro.peso_liquido_ticket or 0,
                        "Valor Frete/Ton": round(valor_frete_por_produto / 100, 2) if valor_frete_por_produto else 0,
                        "Total Frete": round(valor_frete / 100, 2) if valor_frete else 0,
                    }
                )
                            
            if registros_transportadora:
                dados_excel.append(
                    {
                        "Data Entrega e Transportadora": "",
                        "Placa": "",
                        "Origem": "",
                        "Cliente": "",
                        "Produto/Bitola": "",
                        "NF": "",
                        "Peso Liquido (Ton)": "",
                        "Valor Frete/Ton": "Total a pagar    R$",
                        "Total Frete": round(totais_por_transportadora[transportadora] / 100, 2),
                    }
                )
                
                dados_excel.append(
                    {
                        "Data Entrega e Transportadora": "",
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

        nome_arquivo_saida = (
            f"relatorio-prestacao-contas-transportadora-excel-{dataHoje}"
        )
        resposta = ManipulacaoArquivos.exportar_excel(dados_excel, nome_arquivo_saida)
        return resposta

    # Determinar tipo_filtro para o template
    if request.method == "GET":
        tipo_filtro = request.args.get("tipo_filtro", "semanal")
    else:
        tipo_filtro = request.form.get("tipo_filtro", "semanal")

    return render_template(
        "/relatorios/relatorio_semanal/relatorio_prestacao_transportadora/relatorio_prestacao_transportadora.html",
        registros=registros,
        dados_corretos=dados_corretos,
        changelog=changelog,
        semanas_disponiveis=semanas_disponiveis,
        produto=produto,
        bitola=bitola,
        tipo_filtro=tipo_filtro,
        dataInicio=data_inicio,
        dataFim=data_fim
    )