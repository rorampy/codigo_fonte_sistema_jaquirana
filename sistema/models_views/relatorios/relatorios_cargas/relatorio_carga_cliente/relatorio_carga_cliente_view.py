from datetime import datetime
from sistema import app, requires_roles, obter_url_absoluta_de_imagem, formatar_data_para_brl
from flask import render_template, request
from flask_login import login_required
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema._utilitarios import *

@app.route("/relatorios/relatorio-cargas/cargas-cliente", methods=["GET", "POST"])
@login_required
@requires_roles
def relatorio_cargas_cliente():
    """
    Exibe relatório de cargas por cliente com opções de filtro e exportação (PDF/Excel).
    Consolida dados de NF principal e NF complementar.
    """
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    data_hoje = datetime.now().strftime("%d-%m-%Y")

    # Obter fonte de dados (form para POST, args para GET)
    dados_request = request.form if request.method == "POST" else request.args
    filtros = obter_filtros_relatorio(dados_request)
    
    # Verificar se há algum filtro aplicado
    tem_filtros = any(filtros.values())
    
    # Buscar registros com ou sem filtro
    if tem_filtros:
        registros = RegistroOperacionalModel.filtrar_registros_carga_cliente(**filtros)
    else:
        registros = RegistroOperacionalModel.obter_registros_carga_agrupados()
    
    # Processar registros para garantir formato correto (2 casas decimais)
    registros = processar_registros_formatacao(registros)
    
    # Exportar PDF
    if request.method == "POST" and request.form.get("exportar_pdf"):
        logo_path = obter_url_absoluta_de_imagem("logo.png")
        html = render_template(
            "relatorios/relatorio_de_cargas/relatorio_cargas_cliente/exportar_relatorio_cargas_cliente_pdf.html",
            logo_path=logo_path,
            dataHoje=data_hoje,
            registros=registros,
            dados_corretos=dados_request,
            changelog=changelog,
        )
        nome_arquivo_saida = f"relatorio-cargas-cliente-{data_hoje}"
        resposta = ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida, 'landscape')
        return resposta

    # Exportar Excel
    if request.method == "POST" and request.form.get("exportar_excel"):
        dados_excel = preparar_dados_excel(registros)
        nome_arquivo_saida = f"relatorio-cargas-cliente-{data_hoje}"
        resposta = ManipulacaoArquivos.exportar_excel(dados_excel, nome_arquivo_saida)
        return resposta

    # Renderizar template HTML
    return render_template(
        "/relatorios/relatorio_de_cargas/relatorio_cargas_cliente/relatorio_cargas_cliente.html",
        registros=registros,
        dados_corretos=dados_request,
        changelog=changelog,
    )

def obter_filtros_relatorio(dados):
    """
    Extrai e retorna os filtros do relatório a partir de request.form ou request.args.
    
    Args:
        dados: request.form ou request.args
        
    Returns:
        dict: Dicionário com os filtros extraídos
    """
    return {
        'data_inicio': dados.get('dataInicio'),
        'data_fim': dados.get('dataFim'),
        'placa': dados.get('placaCargaCliente'),
        'motorista': dados.get('motoristaCargaCliente'),
        'transportadora': dados.get('tranpostadoraCargaCliente'),
        'fornecedor': dados.get('fornecedorCargaCliente'),
        'cliente': dados.get('clienteCarga'),
        'numero_nf': dados.get('numeroNfCliente'),
        'produto': dados.get('produtoFiltro')
    }


def obter_cliente_nome(registro):
    """
    Retorna o nome/identificação do cliente do registro.
    
    Args:
        registro: Objeto RegistroOperacionalModel
        
    Returns:
        str: Nome do cliente ou mensagem padrão
    """
    if registro.solicitacao and registro.solicitacao.cliente_id:
        return registro.solicitacao.cliente.identificacao
    return "Cliente não identificado"


def processar_registros_formatacao(registros):
    """
    Processa registros para garantir formatação correta (2 casas decimais).
    
    Args:
        registros: Lista de registros operacionais
        
    Returns:
        list: Registros com valores formatados
    """
    for item in registros:
        # Arredondar peso_complementar e valor_complementar para 2 casas decimais
        if 'peso_complementar' in item and item['peso_complementar'] is not None:
            item['peso_complementar'] = round(float(item['peso_complementar']), 2)
        if 'valor_complementar' in item and item['valor_complementar'] is not None:
            item['valor_complementar'] = round(float(item['valor_complementar']), 2)
    
    return registros


def calcular_totais_registro(registro, item):
    """
    Calcula os totais de peso e venda do registro (NF + Complementar).
    Garante arredondamento de 2 casas decimais para peso e venda.
    
    Args:
        registro: Objeto RegistroOperacionalModel
        item: Dict contendo dados complementares
        
    Returns:
        tuple: (total_peso, total_venda) - ambos com 2 casas decimais
    """
    peso_nf = float(registro.peso_ton_nf or 0)
    peso_complementar = float(item.get('peso_complementar', 0) or 0)
    total_peso = round(peso_nf + peso_complementar, 2)
    
    valor_nf = float(registro.valor_total_nota_100 or 0)
    valor_complementar = float(item.get('valor_complementar', 0) or 0)
    total_venda = (valor_nf + valor_complementar) / 100
    
    return total_peso, total_venda


def montar_linha_dados_excel(registro, item, cliente_nome):
    """
    Monta uma linha de dados para exportação Excel.
    
    Args:
        registro: Objeto RegistroOperacionalModel
        item: Dict contendo dados complementares
        cliente_nome: Nome do cliente
        
    Returns:
        dict: Linha formatada para o Excel
    """
    total_peso, total_venda = calcular_totais_registro(registro, item)
    
    return {
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
        "Cliente": cliente_nome,
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
        "Total Peso (Ton)": total_peso,
        "Total Venda": total_venda,
    }


def preparar_dados_excel(registros):
    """
    Prepara os dados para exportação Excel agrupados por cliente.
    
    Args:
        registros: Lista de registros operacionais
        
    Returns:
        list: Dados formatados para exportação Excel
    """
    dados_excel = []
    registros_por_cliente = {}
    totais_por_cliente = {}
    
    # Agrupar registros por cliente
    for item in registros:
        registro = item["registro"]
        cliente_nome = obter_cliente_nome(registro)
        valor_frete = registro.valor_total_nota_100 or 0
        
        if cliente_nome not in registros_por_cliente:
            registros_por_cliente[cliente_nome] = []
            totais_por_cliente[cliente_nome] = 0
            
        registros_por_cliente[cliente_nome].append(item)
        totais_por_cliente[cliente_nome] += valor_frete

    # Montar linhas do Excel
    for cliente in sorted(registros_por_cliente.keys()):
        registros_cliente = registros_por_cliente[cliente]
        
        # Linha de cabeçalho do cliente
        dados_excel.append({
            "Data Entrega e Cliente": cliente.upper(),
            "Placa": "",
            "Origem": "",
            "Cliente": "",
            "Produto/Bitola": "",
            "NF": "",
            "Peso Liquido (Ton)": "",
            "Valor Frete/Ton": "",
            "Total Frete": "",
            "Total Peso (Ton)": "",
            "Total Venda": "",
        })
        
        # Dados do cliente
        for item in registros_cliente:
            registro = item["registro"]
            linha_dados = montar_linha_dados_excel(registro, item, cliente)
            dados_excel.append(linha_dados)
                        
        # Linha de total por cliente
        if registros_cliente:
            dados_excel.append({
                "Data Entrega e Cliente": "",
                "Placa": "",
                "Origem": "",
                "Cliente": "",
                "Produto/Bitola": "",
                "NF": "",
                "Peso Liquido (Ton)": "",
                "Valor Frete/Ton": "Total a receber    R$",
                "Total Frete": round(totais_por_cliente[cliente] / 100, 2),
                "Total Peso (Ton)": "",
                "Total Venda": "",
            })
            
            # Linha em branco para separar clientes
            dados_excel.append({
                "Data Entrega e Cliente": "",
                "Placa": "",
                "Origem": "",
                "Cliente": "",
                "Produto/Bitola": "",
                "NF": "",
                "Peso Liquido (Ton)": "",
                "Valor Frete/Ton": "",
                "Total Frete": "",
                "Total Peso (Ton)": "",
                "Total Venda": "",
            })
    
    return dados_excel