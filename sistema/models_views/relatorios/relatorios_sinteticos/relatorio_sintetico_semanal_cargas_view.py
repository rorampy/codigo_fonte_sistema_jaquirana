from datetime import datetime, timedelta, date
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required
from sistema.models_views.controle_carga.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema._utilitarios import *

@app.route("/relatorios/relatorio-sintetico/semanal-cargas", methods=["GET", "POST"])
@login_required
@requires_roles
def relatorio_sintetico_semanal_cargas():
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    dataHoje = datetime.now().strftime("%d-%m-%Y")

    # Obter as semanas do período atual 
    semanas_disponiveis = UtilitariosSemana.obter_semanas_do_mes_atual()

    # Valor padrão: semana atual (buscar na lista)
    valor_padrao_semana = ""
    semana_atual_info = None
    
    # Procurar a semana atual na lista
    for semana in semanas_disponiveis:
        if semana.get("is_atual", False):
            valor_padrao_semana = semana["valor"]
            semana_atual_info = semana
            break
    
    # Se não encontrar semana atual, usar a primeira opção disponível
    if not valor_padrao_semana and semanas_disponiveis:
        valor_padrao_semana = semanas_disponiveis[0]["valor"]
        semana_atual_info = semanas_disponiveis[0]

    if request.method == "POST":
        semana_selecionada = request.form.get("semanaSelecionada")

        # Processar semana selecionada
        data_inicio, data_fim = UtilitariosSemana.processar_semana_selecionada(semana_selecionada)

        registros = (
            RegistroOperacionalModel.registros_carga_fornecedor_floresta_produto(
                data_inicio=data_inicio,
                data_fim=data_fim,
            )
        )

        dados_corretos = {
            "semanaSelecionada": semana_selecionada,
            "dataInicio": data_inicio.strftime("%Y-%m-%d") if data_inicio else "",
            "dataFim": data_fim.strftime("%Y-%m-%d") if data_fim else "",
        }
    else:
        # Carregar dados da semana atual por padrão
        if semana_atual_info:
            data_inicio = semana_atual_info["inicio"]
            data_fim = semana_atual_info["fim"]
        else:
            # Fallback para o mês atual se não encontrar semana atual
            data_inicio, data_fim = UtilitariosSemana.obter_datas_mes_atual()
        
        registros = (
            RegistroOperacionalModel.registros_carga_fornecedor_floresta_produto(
                data_inicio=data_inicio,
                data_fim=data_fim,
            )
        )
        
        dados_corretos = {
            "semanaSelecionada": valor_padrao_semana,
            "dataInicio": data_inicio.strftime("%Y-%m-%d") if data_inicio else "",
            "dataFim": data_fim.strftime("%Y-%m-%d") if data_fim else "",
        }

    # Detecta exportação de PDF
    if request.method == "POST" and request.form.get("exportar_pdf"):
        logo_path = obter_url_absoluta_de_imagem("logo.png")
        html = render_template(
            "/relatorios/relatorios_sinteticos/relatorio_sintetico_semanal_cargas/exportar_relatorio_sintetico_semanal_cargas_pdf.html",
            logo_path=logo_path,
            dataHoje=dataHoje,
            registros=registros,
            dados_corretos=dados_corretos,
            changelog=changelog,
        )

        nome_arquivo_saida = f"relatorio-sintetico-semanal-cargas_{dataHoje}"
        resposta = ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida)
        return resposta

    # Detecta exportação de Excel
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

        # Montar lista final para exportação
        dados_excel = []
        for origem, dados in sorted(dados_agrupados.items()):
            linha = {
                "Origem (Fornecedor/Floresta)": origem,
                "Total de Cargas": dados["total_cargas"],
                "Peso Total (Ton)": round(dados["peso_total"], 2),
                "Total a Pagar (R$)": round(dados["total_pagar"] / 100, 2),
            }
            dados_excel.append(linha)

        nome_arquivo_saida = f"relatorio-sintetico-semanal-cargas-{dataHoje}"
        resposta = ManipulacaoArquivos.exportar_excel(dados_excel, nome_arquivo_saida)
        return resposta

    return render_template(
        "/relatorios/relatorios_sinteticos/relatorio_sintetico_semanal_cargas/relatorio_sintetico_semanal_cargas.html",
        registros=registros,
        dados_corretos=dados_corretos,
        changelog=changelog,
        semanas_disponiveis=semanas_disponiveis,
    )