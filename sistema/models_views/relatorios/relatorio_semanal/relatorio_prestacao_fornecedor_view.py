from datetime import datetime, timedelta, date
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem, formatar_data_para_brl
from flask import render_template, request
from flask_login import login_required
from sistema.models_views.controle_carga.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema.models_views.controle_carga.produto_model import ProdutoModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema._utilitarios import *


@app.route("/relatorios/relatorio-semanal/prestacao-contas-fornecedor", methods=["GET", "POST"])
@login_required
@requires_roles
def relatorio_sintetico_fornecedor():
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

    if request.method == "POST":
        if any(request.form.values()) and not (request.form.get("exportar_pdf") or request.form.get("exportar_excel")):
            tipo_filtro = request.form.get("tipo_filtro", "semanal")
            semana_selecionada = request.form.get("semanaSelecionada")
            data_inicio_form = request.form.get("dataInicio")
            data_fim_form = request.form.get("dataFim")
            fornecedor = request.form.get("fornecedorCargaCliente")
            numero_nf = request.form.get("numeroNfCliente")
            clienteFiltro = request.form.get("clienteFiltro", "")
            produtoFiltro = request.form.get("produtoFiltro", "")
            bitolaFiltro = request.form.get("bitolaFiltro", "")

            if tipo_filtro == "data" and data_inicio_form and data_fim_form:
                data_inicio = datetime.strptime(data_inicio_form, '%Y-%m-%d').date()
                data_fim = datetime.strptime(data_fim_form, '%Y-%m-%d').date()
            else:
                data_inicio, data_fim = UtilitariosSemana.processar_semana_selecionada(
                    semana_selecionada
                )

            registros = RegistroOperacionalModel.filtrar_registros_carga_fornecedor_floresta_produto(
                data_inicio=data_inicio,
                data_fim=data_fim,
                fornecedor=fornecedor,
                numero_nf=numero_nf,
                produto=produtoFiltro,
                cliente=clienteFiltro,
                bitola=bitolaFiltro
            )
            dados_corretos = request.form
        else:
            tipo_filtro = request.form.get("tipo_filtro", "semanal")
            semana_selecionada = request.form.get("semanaSelecionada")
            data_inicio_form = request.form.get("dataInicio")
            data_fim_form = request.form.get("dataFim")
            fornecedor = request.form.get("fornecedorCargaCliente")
            numero_nf = request.form.get("numeroNfCliente")
            clienteFiltro = request.form.get("clienteFiltro", "")
            produtoFiltro = request.form.get("produtoFiltro", "")
            bitolaFiltro = request.form.get("bitolaFiltro", "")

            if any([tipo_filtro, semana_selecionada, data_inicio_form, data_fim_form, fornecedor, numero_nf, clienteFiltro, produtoFiltro, bitolaFiltro]):
                if tipo_filtro == "data" and data_inicio_form and data_fim_form:
                    data_inicio = datetime.strptime(data_inicio_form, '%Y-%m-%d').date()
                    data_fim = datetime.strptime(data_fim_form, '%Y-%m-%d').date()
                else:
                    data_inicio, data_fim = UtilitariosSemana.processar_semana_selecionada(
                        semana_selecionada
                    )

                registros = RegistroOperacionalModel.filtrar_registros_carga_fornecedor_floresta_produto(
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    fornecedor=fornecedor,
                    numero_nf=numero_nf,
                    produto=produtoFiltro,
                    cliente=clienteFiltro,
                    bitola=bitolaFiltro
                )
            else:
                tipo_filtro = "semanal"
                if semana_atual_info:
                    data_inicio = semana_atual_info["inicio"]
                    data_fim = semana_atual_info["fim"]
                else:
                    data_inicio, data_fim = UtilitariosSemana.obter_datas_mes_atual()

                registros = RegistroOperacionalModel.filtrar_registros_carga_fornecedor_floresta_produto(
                    data_inicio=data_inicio, data_fim=data_fim
                )
            dados_corretos = request.form
    else:
        if any(request.args.values()):
            tipo_filtro = request.args.get("tipo_filtro", "semanal")
            semana_selecionada = request.args.get("semanaSelecionada")
            data_inicio_form = request.args.get("dataInicio")
            data_fim_form = request.args.get("dataFim")
            fornecedor = request.args.get("fornecedorCargaCliente")
            numero_nf = request.args.get("numeroNfCliente")
            clienteFiltro = request.args.get("clienteFiltro", "")
            produtoFiltro = request.args.get("produtoFiltro", "")
            bitolaFiltro = request.args.get("bitolaFiltro", "")

            if tipo_filtro == "data" and data_inicio_form and data_fim_form:
                data_inicio = datetime.strptime(data_inicio_form, '%Y-%m-%d').date()
                data_fim = datetime.strptime(data_fim_form, '%Y-%m-%d').date()
            else:
                data_inicio, data_fim = UtilitariosSemana.processar_semana_selecionada(
                    semana_selecionada
                )

            registros = RegistroOperacionalModel.filtrar_registros_carga_fornecedor_floresta_produto(
                data_inicio=data_inicio,
                data_fim=data_fim,
                fornecedor=fornecedor,
                numero_nf=numero_nf,
                produto=produtoFiltro,
                cliente=clienteFiltro,
                bitola=bitolaFiltro
            )
            dados_corretos = request.args
        else:
            tipo_filtro = "semanal"
            if semana_atual_info:
                data_inicio = semana_atual_info["inicio"]
                data_fim = semana_atual_info["fim"]
            else:
                data_inicio, data_fim = UtilitariosSemana.obter_datas_mes_atual()

            registros = RegistroOperacionalModel.filtrar_registros_carga_fornecedor_floresta_produto(
                data_inicio=data_inicio, data_fim=data_fim
            )

            dados_corretos = {
                "tipo_filtro": tipo_filtro,
                "semanaSelecionada": valor_padrao_semana,
                "dataInicio": "",
                "dataFim": "",
                "fornecedorCargaCliente": "",
                "numeroNfCliente": "",
                "produtoFiltro": "",
                "clienteFiltro": "",
                "bitolaFiltro": "",
            }

    if request.method == "POST" and request.form.get("exportar_pdf"):
        logo_path = obter_url_absoluta_de_imagem("logo.png")
        html = render_template(
            "/relatorios/relatorio_semanal/relatorio_prestacao_fornecedor/exportar_relatorio_prestacao_fornecedor_pdf.html",
            logo_path=logo_path,
            dataHoje=dataHoje,
            registros=registros,
            dados_corretos=dados_corretos,
            changelog=changelog,
            semanas_disponiveis=semanas_disponiveis,
        )

        nome_arquivo_saida = f"relatorio-prestacao-contas-fornecedor-pdf-{dataHoje}"
        resposta = ManipulacaoArquivos.gerar_pdf_from_html(
            html, nome_arquivo_saida)
        return resposta

    if request.method == "POST" and request.form.get("exportar_excel"):
        dados_excel = []
        
        registros_por_origem = {}
        totais_por_origem = {}
        
        for item in registros:
            origem = item.get("origem", "Sem origem")
            valor_pagar = item.get("valor_pagar", 0)
            
            if origem not in registros_por_origem:
                registros_por_origem[origem] = []
                totais_por_origem[origem] = 0
                
            registros_por_origem[origem].append(item)
            totais_por_origem[origem] += valor_pagar

        for origem in sorted(registros_por_origem.keys()):
            registros_origem = registros_por_origem[origem]
            
            dados_excel.append(
                {
                    "Data Entrega e Origem": origem.upper(),
                    "Placa": "",
                    "Cliente": "",
                    "Produto/Bitola": "",
                    "NF": "",
                    "Peso Liquido (Ton)": "",
                    "Valor/Ton": "",
                    "Total Fornecedor": "",
                }
            )
            
            for item in registros_origem:
                registro = item["registro"]
                produto = item.get("produto", "")
                bitola = item.get("bitola", "")
                valor_pagar = item.get("valor_pagar", 0)
                valor_ton = item.get("valor_ton", 0)
                cliente = item.get("cliente", "")

                dados_excel.append(
                    {
                        "Data Entrega e Origem": (
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
                        "Valor/Ton": valor_ton / 100 if valor_ton else 0,
                        "Total Fornecedor": round(valor_pagar / 100, 2) if valor_pagar else 0,
                    }
                )
            
            if registros_origem:
                dados_excel.append(
                    {
                        "Data Entrega e Origem": "",
                        "Placa": "",
                        "Cliente": "",
                        "Produto/Bitola": "",
                        "NF": "",
                        "Peso Liquido (Ton)": "",
                        "Valor/Ton": "Total a pagar    R$",
                        "Total Fornecedor": round(totais_por_origem[origem] / 100, 2),
                    }
                )
                
                dados_excel.append(
                    {
                        "Data Entrega e Origem": "",
                        "Placa": "",
                        "Cliente": "",
                        "Produto/Bitola": "",
                        "NF": "",
                        "Peso Liquido (Ton)": "",
                        "Valor/Ton": "",
                        "Total Fornecedor": "",
                    }
                )

        nome_arquivo_saida = f"relatorio-prestacao-contas-fornecedor-excel-{dataHoje}"
        resposta = ManipulacaoArquivos.exportar_excel(dados_excel, nome_arquivo_saida)
        return resposta

    if request.method == "GET":
        tipo_filtro = request.args.get("tipo_filtro", "semanal")
    else:
        tipo_filtro = request.form.get("tipo_filtro", "semanal")

    return render_template(
        "/relatorios/relatorio_semanal/relatorio_prestacao_fornecedor/relatorio_prestacao_fornecedor.html",
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