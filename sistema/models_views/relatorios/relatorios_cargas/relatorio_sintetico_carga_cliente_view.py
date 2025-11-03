from datetime import datetime
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem, formatar_float_para_brl, formatar_data_para_brl, formatar_float_para_brl_sem_cifrao
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required
from sistema.models_views.controle_carga.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema.models_views.controle_carga.produto_model import ProdutoModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema._utilitarios import *


@app.route("/relatorios/relatorio-cargas/relatorio-sintetico-cliente", methods=["GET", "POST"])
@login_required
@requires_roles
def relatorio_sintetico_cliente():
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    dataHoje = datetime.now().strftime("%d-%m-%Y")

    produto = ProdutoModel.listar_produtos()
    bitola = BitolaModel.listar_bitolas_ativas()

    # Para exportações (POST), usar os dados do formulário
    if request.method == "POST":
        if any(request.form.values()) and not (request.form.get("exportar_pdf") or request.form.get("exportar_excel")):
            data_inicio = request.form.get("dataInicio")
            data_fim = request.form.get("dataFim")
            clienteFiltro = request.form.get("clienteFiltro", "")
            produtoFiltro = request.form.get("produtoFiltro", "")
            bitolaFiltro = request.form.get("bitolaFiltro", "")
            fornecedorFiltro = request.form.get("fornecedorFiltro", "")
            transportadoraFiltro = request.form.get("transportadoraFiltro", "")

            registros = RegistroOperacionalModel.filtrar_registros_carga_cliente(
                data_inicio=data_inicio,
                data_fim=data_fim,
                cliente=clienteFiltro,
                produto=produtoFiltro,
                bitola=bitolaFiltro,
                fornecedor=fornecedorFiltro,
                transportadora=transportadoraFiltro
            )
            dados_corretos = request.form
        else:
            # Para exportações, reaplicar os filtros baseados nos hidden fields do form
            data_inicio = request.form.get("dataInicio")
            data_fim = request.form.get("dataFim")
            clienteFiltro = request.form.get("clienteFiltro", "")
            produtoFiltro = request.form.get("produtoFiltro", "")
            bitolaFiltro = request.form.get("bitolaFiltro", "")
            fornecedorFiltro = request.form.get("fornecedorFiltro", "")
            transportadoraFiltro = request.form.get("transportadoraFiltro", "")

            if any([data_inicio, data_fim, clienteFiltro, produtoFiltro, bitolaFiltro, fornecedorFiltro, transportadoraFiltro]):
                registros = RegistroOperacionalModel.filtrar_registros_carga_cliente(
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    cliente=clienteFiltro,
                    produto=produtoFiltro,
                    bitola=bitolaFiltro,
                    fornecedor=fornecedorFiltro,
                    transportadora=transportadoraFiltro
                )
            else:
                registros = RegistroOperacionalModel.obter_registros_carga_agrupados()
            dados_corretos = request.form
    else:
        # Para GET, usar args
        if any(request.args.values()):
            data_inicio = request.args.get("dataInicio")
            data_fim = request.args.get("dataFim")
            clienteFiltro = request.args.get("clienteFiltro", "")
            produtoFiltro = request.args.get("produtoFiltro", "")
            bitolaFiltro = request.args.get("bitolaFiltro", "")
            fornecedorFiltro = request.args.get("fornecedorFiltro", "")
            transportadoraFiltro = request.args.get("transportadoraFiltro", "")

            registros = RegistroOperacionalModel.filtrar_registros_carga_cliente(
                data_inicio=data_inicio,
                data_fim=data_fim,
                cliente=clienteFiltro,
                produto=produtoFiltro,
                bitola=bitolaFiltro,
                fornecedor=fornecedorFiltro,
                transportadora=transportadoraFiltro
            )
            dados_corretos = request.args
        else:
            registros = RegistroOperacionalModel.obter_registros_carga_agrupados()
            dados_corretos = {}

    if request.method == "POST" and request.form.get("exportar_pdf"):
        logo_path = obter_url_absoluta_de_imagem("logo.png")
        
        # Agrupar por cliente primeiro para calcular totalizadores corretos
        clientes_agrupados = {}
        for item in registros:
            cliente = item["cliente"]
            registro = item["registro"]

            if cliente not in clientes_agrupados:
                clientes_agrupados[cliente] = {
                    "total_cargas": 0,
                    "peso_total": 0.0,
                    "valor_total": 0.0
                }

            grupo = clientes_agrupados[cliente]
            grupo["total_cargas"] += 1
            grupo["peso_total"] += registro.peso_liquido_ticket or 0
            grupo["valor_total"] += registro.valor_total_nota_100 or 0
        
        # Calcular totalizadores gerais a partir dos grupos
        total_cargas = sum(dados["total_cargas"] for dados in clientes_agrupados.values())
        total_toneladas = sum(dados["peso_total"] for dados in clientes_agrupados.values())
        total_valores = sum(dados["valor_total"] for dados in clientes_agrupados.values())
        
        html = render_template(
            "/relatorios/relatorio_de_cargas/relatorio_sintetico_cliente/exportar_relatorio_sintetico_cliente_pdf.html",
            logo_path=logo_path,
            dataHoje=dataHoje,
            registros=registros,
            dados_corretos=dados_corretos,
            changelog=changelog,
            total_cargas=total_cargas,
            total_toneladas=round(total_toneladas, 2),
            total_valores=round(total_valores, 2),
        )

        nome_arquivo_saida = f"relatorio-sintetico-cliente-{dataHoje}"
        resposta = ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida)
        return resposta

    if request.method == "POST" and request.form.get("exportar_excel"):
        linhas = []

        # Agrupar por cliente
        clientes_agrupados = {}
        
        for item in registros:
            cliente = item["cliente"]
            registro = item["registro"]

            if cliente not in clientes_agrupados:
                clientes_agrupados[cliente] = {
                    "total_cargas": 0,
                    "peso_total": 0.0,
                    "valor_total": 0.0
                }

            grupo = clientes_agrupados[cliente]
            grupo["total_cargas"] += 1
            grupo["peso_total"] += registro.peso_liquido_ticket or 0
            grupo["valor_total"] += registro.valor_total_nota_100 or 0

        # Calcular totais gerais a partir dos grupos (não dos registros individuais)
        total_geral_cargas = sum(dados["total_cargas"] for dados in clientes_agrupados.values())
        total_geral_toneladas = sum(dados["peso_total"] for dados in clientes_agrupados.values())
        total_geral_valores = sum(dados["valor_total"] for dados in clientes_agrupados.values())

        # Montar linhas para exportar
        for cliente, dados in clientes_agrupados.items():
            linha = {
                "Cliente": cliente,
                "Total de Cargas": dados["total_cargas"],
                "Peso Total (Ton)": round(dados["peso_total"], 2),
                "Valor Total NF's (R$)": round(dados["valor_total"] / 100, 2)
            }
            linhas.append(linha)

        # Adicionar linha em branco
        linhas.append({
            "Cliente": "",
            "Total de Cargas": "",
            "Peso Total (Ton)": "",
            "Valor Total NF's (R$)": ""
        })
        
        # Adicionar totalizadores gerais
        linhas.append({
            "Cliente": "TOTAIS GERAIS:",
            "Total de Cargas": total_geral_cargas,
            "Peso Total (Ton)": round(total_geral_toneladas, 2),
            "Valor Total NF's (R$)": round(total_geral_valores / 100, 2)
        })

        nome_arquivo_saida = f"relatorio-sintetico-cliente-{dataHoje}"
        resposta = ManipulacaoArquivos.exportar_excel(linhas, nome_arquivo_saida)
        return resposta

    return render_template(
        "/relatorios/relatorio_de_cargas/relatorio_sintetico_cliente/relatorio_sintetico_cliente.html",
        registros=registros,
        dados_corretos=dados_corretos,
        changelog=changelog,
        produto=produto,
        bitola=bitola
    )