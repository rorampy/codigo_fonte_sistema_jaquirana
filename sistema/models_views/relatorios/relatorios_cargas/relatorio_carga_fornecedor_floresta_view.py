from datetime import datetime
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem, formatar_float_para_brl, formatar_data_para_brl, formatar_float_para_brl_sem_cifrao
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required
from sistema.models_views.controle_carga.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema._utilitarios import *


@app.route("/relatorios/relatorio-cargas/cargas-fornecedor-floresta", methods=["GET", "POST"])
@login_required
@requires_roles
def relatorio_cargas_fornecedor_floresta():
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    dataHoje = datetime.now().strftime('%d-%m-%Y')

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

            registros = RegistroOperacionalModel.filtrar_registros_carga_fornecedor_floresta_produto(
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
                registros = RegistroOperacionalModel.filtrar_registros_carga_fornecedor_floresta_produto(
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
                registros = RegistroOperacionalModel.obter_registros_carga_fornecedor_floresta_produto()
            dados_corretos = request.form
    else:
        # Para GET, usar args
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

            registros = RegistroOperacionalModel.filtrar_registros_carga_fornecedor_floresta_produto(
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
            registros = RegistroOperacionalModel.obter_registros_carga_fornecedor_floresta_produto()
            dados_corretos = {}

    if request.method == "POST" and request.form.get('exportar_pdf'):
        logo_path = obter_url_absoluta_de_imagem('logo.png')
        html = render_template(
            "relatorios/relatorio_de_cargas/relatorio_cargas_fornecedor_floresta/exportar_relatorio_cargas_fornecedor_floresta_pdf.html",
            logo_path=logo_path,
            dataHoje=dataHoje,
            registros=registros,
            dados_corretos=dados_corretos,
            changelog=changelog
        )

        nome_arquivo_saida = f'relatorio-cargas-fornecedor-floresta_{dataHoje}'
        resposta = ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida)
        return resposta

    if request.method == "POST" and request.form.get('exportar_excel'):
        dados_excel = []
        
        registros_por_origem = {}
        totais_por_origem = {}
        
        for item in registros:
            registro = item['registro']
            origem = item.get('origem', 'Origem não identificada')
            valor_pagar = item.get('valor_pagar', 0)
            
            if origem not in registros_por_origem:
                registros_por_origem[origem] = []
                totais_por_origem[origem] = 0
                
            registros_por_origem[origem].append(item)
            totais_por_origem[origem] += valor_pagar

        for origem in sorted(registros_por_origem.keys()):
            registros_origem = registros_por_origem[origem]
            
            # Linha de cabeçalho da origem
            dados_excel.append(
                {
                    "Data Entrega": origem.upper(),
                    "Origem": "",
                    "Produto": "",
                    "Bitola": "",
                    "Placa": "",
                    "Peso Líquido (Ton)": "",
                    "Motorista": "",
                    "Transportadora": "",
                    "NF": "",
                    "Valor a Pagar Fornecedor (R$)": "",
                }
            )
            
            # Dados da origem
            for item in registros_origem:
                registro = item['registro']
                origem = item.get('origem', '')
                produto = item.get('produto', '')
                bitola = item.get('bitola', '')
                valor_pagar = item.get('valor_pagar', 0)

                dados_excel.append(
                    {
                        "Data Entrega": (
                            formatar_data_para_brl(registro.data_entrega_ticket)
                            if registro.data_entrega_ticket
                            else ""
                        ),
                        "Origem": origem,
                        "Produto": produto,
                        "Bitola": bitola,
                        "Placa": registro.placa_ticket or "",
                        "Peso Líquido (Ton)": registro.peso_liquido_ticket or "",
                        "Motorista": registro.motorista_ticket or "",
                        "Transportadora": (
                            registro.solicitacao.transportadora_exibicao.identificacao
                            if registro.solicitacao and registro.solicitacao.transportadora_exibicao
                            else ""
                        ),
                        "NF": f"{registro.numero_nota_fiscal_estorno} *" if registro.estorno_nf else (registro.numero_nota_fiscal or ""),
                        "Valor a Pagar Fornecedor (R$)": round(valor_pagar / 100, 2),
                    }
                )
                            
            # Linha de total por origem
            if registros_origem:
                dados_excel.append(
                    {
                        "Data Entrega": "",
                        "Origem": "",
                        "Produto": "",
                        "Bitola": "",
                        "Placa": "",
                        "Peso Líquido (Ton)": "",
                        "Motorista": "",
                        "Transportadora": "Total a pagar    R$",
                        "NF": "",
                        "Valor a Pagar Fornecedor (R$)": round(totais_por_origem[origem] / 100, 2),
                    }
                )
                
                # Linha em branco para separar origens
                dados_excel.append(
                    {
                        "Data Entrega": "",
                        "Origem": "",
                        "Produto": "",
                        "Bitola": "",
                        "Placa": "",
                        "Peso Líquido (Ton)": "",
                        "Motorista": "",
                        "Transportadora": "",
                        "NF": "",
                        "Valor a Pagar Fornecedor (R$)": "",
                    }
                )

        nome_arquivo_saida = f'relatorio-cargas-fornecedor-floresta-{dataHoje}'
        resposta = ManipulacaoArquivos.exportar_excel(dados_excel, nome_arquivo_saida)
        return resposta

    return render_template(
        "/relatorios/relatorio_de_cargas/relatorio_cargas_fornecedor_floresta/relatorio_cargas_fornecedor_floresta.html",
        registros=registros, 
        dados_corretos=dados_corretos, 
        changelog=changelog
    )