from datetime import datetime
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem, formatar_float_para_brl, formatar_data_para_brl, formatar_float_para_brl_sem_cifrao
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required
from sistema.models_views.controle_carga.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema.models_views.controle_carga.produto_model import ProdutoModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema._utilitarios import *


@app.route(
    "/relatorios/relatorio-semanal/sintetico-cargas-fornecedor-floresta",
    methods=["GET", "POST"],
)
@login_required
@requires_roles
def relatorio_sintetico_fornecedor_floresta():
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
            semana_selecionada = request.form.get("semanaSelecionada", "")
            data_inicio_form = request.form.get("dataInicio")
            data_fim_form = request.form.get("dataFim")
            clienteFiltro = request.form.get("clienteFiltro", "")
            produtoFiltro = request.form.get("produtoFiltro", "")
            bitolaFiltro = request.form.get("bitolaFiltro", "")

            if tipo_filtro == "data" and data_inicio_form and data_fim_form:
                data_inicio = datetime.strptime(data_inicio_form, "%Y-%m-%d").date()
                data_fim = datetime.strptime(data_fim_form, "%Y-%m-%d").date()
            else:
                data_inicio, data_fim = UtilitariosSemana.processar_semana_selecionada(
                    semana_selecionada or valor_padrao_semana
                )

            registros = RegistroOperacionalModel.filtrar_registros_carga_fornecedor_floresta_produto(
                data_inicio=data_inicio,
                data_fim=data_fim,
                cliente=clienteFiltro,
                produto=produtoFiltro,
                bitola=bitolaFiltro
            )
            dados_corretos = request.form
        else:
            tipo_filtro = request.form.get("tipo_filtro", "semanal")
            semana_selecionada = request.form.get("semanaSelecionada", "")
            data_inicio_form = request.form.get("dataInicio")
            data_fim_form = request.form.get("dataFim")
            clienteFiltro = request.form.get("clienteFiltro", "")
            produtoFiltro = request.form.get("produtoFiltro", "")
            bitolaFiltro = request.form.get("bitolaFiltro", "")

            if any([tipo_filtro, semana_selecionada, data_inicio_form, data_fim_form, clienteFiltro, produtoFiltro, bitolaFiltro]):
                if tipo_filtro == "data" and data_inicio_form and data_fim_form:
                    data_inicio = datetime.strptime(data_inicio_form, "%Y-%m-%d").date()
                    data_fim = datetime.strptime(data_fim_form, "%Y-%m-%d").date()
                else:
                    data_inicio, data_fim = UtilitariosSemana.processar_semana_selecionada(
                        semana_selecionada or valor_padrao_semana
                    )

                registros = RegistroOperacionalModel.filtrar_registros_carga_fornecedor_floresta_produto(
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    cliente=clienteFiltro,
                    produto=produtoFiltro,
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
                    data_inicio=data_inicio,
                    data_fim=data_fim
                )
            dados_corretos = request.form
    else:
        if any(request.args.values()):
            tipo_filtro = request.args.get("tipo_filtro", "semanal")
            semana_selecionada = request.args.get("semanaSelecionada", "")
            data_inicio_form = request.args.get("dataInicio")
            data_fim_form = request.args.get("dataFim")
            clienteFiltro = request.args.get("clienteFiltro", "")
            produtoFiltro = request.args.get("produtoFiltro", "")
            bitolaFiltro = request.args.get("bitolaFiltro", "")

            if tipo_filtro == "data" and data_inicio_form and data_fim_form:
                data_inicio = datetime.strptime(data_inicio_form, "%Y-%m-%d").date()
                data_fim = datetime.strptime(data_fim_form, "%Y-%m-%d").date()
            else:
                data_inicio, data_fim = UtilitariosSemana.processar_semana_selecionada(
                    semana_selecionada or valor_padrao_semana
                )

            registros = RegistroOperacionalModel.filtrar_registros_carga_fornecedor_floresta_produto(
                data_inicio=data_inicio,
                data_fim=data_fim,
                cliente=clienteFiltro,
                produto=produtoFiltro,
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
                data_inicio=data_inicio, 
                data_fim=data_fim
            )

            dados_corretos = {
                "tipo_filtro": tipo_filtro,
                "semanaSelecionada": valor_padrao_semana,
                "dataInicio": data_inicio.strftime("%Y-%m-%d") if data_inicio else "",
                "dataFim": data_fim.strftime("%Y-%m-%d") if data_fim else "",
                "clienteFiltro": "",
                "produtoFiltro": "",
                "bitolaFiltro": "",
            }

    if request.method == "POST" and request.form.get("exportar_pdf"):
        logo_path = obter_url_absoluta_de_imagem("logo.png")
        html = render_template(
            "/relatorios/relatorio_semanal/relatorio_sintetico_fornecedor_floresta/exportar_relatorio_sintetico_fornecedor_floresta_pdf.html",
            logo_path=logo_path,
            dataHoje=dataHoje,
            registros=registros,
            dados_corretos=dados_corretos,
            changelog=changelog,
            semanas_disponiveis=semanas_disponiveis
        )

        nome_arquivo_saida = f"relatorio-sintetico-fornecedor-floresta_{dataHoje}"
        resposta = ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida)
        return resposta

    if request.method == "POST" and request.form.get("exportar_excel"):
        dados_agrupados = {}

        for item in registros:
            origem = item.get("origem", "") or "Não Informado"
            peso = item["registro"].peso_liquido_ticket or 0
            valor_pagar = item.get("valor_pagar", 0)

            if origem not in dados_agrupados:
                dados_agrupados[origem] = {
                    "total_cargas": 0,
                    "peso_total": 0.0,
                    "total_pagar": 0.0,
                }

            dados_agrupados[origem]["total_cargas"] += 1
            dados_agrupados[origem]["peso_total"] += peso
            dados_agrupados[origem]["total_pagar"] += valor_pagar

        dados_excel = []
        for origem, dados in sorted(dados_agrupados.items()):
            linha = {
                "Origem (Fornecedor/Floresta)": origem,
                "Total de Cargas": dados["total_cargas"],
                "Peso Total (Ton)": round(dados["peso_total"], 2),
                "Total a Pagar (R$)": round(dados["total_pagar"] / 100, 2),
            }
            dados_excel.append(linha)

        nome_arquivo_saida = f"relatorio-sintetico-fornecedor-floresta-{dataHoje}"
        resposta = ManipulacaoArquivos.exportar_excel(dados_excel, nome_arquivo_saida)
        return resposta

    if request.method == "GET":
        tipo_filtro = request.args.get("tipo_filtro", "semanal")
    else:
        tipo_filtro = request.form.get("tipo_filtro", "semanal")

    return render_template(
        "/relatorios/relatorio_semanal/relatorio_sintetico_fornecedor_floresta/relatorio_sintetico_fornecedor_floresta.html",
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