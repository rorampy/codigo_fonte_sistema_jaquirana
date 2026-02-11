from datetime import datetime
from sistema import app, requires_roles, obter_url_absoluta_de_imagem
from flask import render_template, request
from flask_login import login_required
from sistema.models_views.faturamento.cargas_a_faturar.fornecedor.fornecedor_a_pagar_model import FornecedorPagarModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
from sistema.models_views.configuracoes_gerais.situacao_pagamento.situacao_pagamento_model import SituacaoPagamentoModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema._utilitarios import ManipulacaoArquivos
from itertools import groupby
from operator import itemgetter


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def calcular_totalizadores(registros):
    """
    Calcula os totalizadores por fornecedor e o total geral.
    
    Args:
        registros (list): Lista de registros
        
    Returns:
        dict: Dicionário com totais por fornecedor e total geral
              Os valores monetários são armazenados em centavos (valor_100)
              para uso com o filtro formatar_float_para_brl
    """
    totais_fornecedor = {}
    total_geral = {
        "toneladas": 0,
        "valor_100": 0,
    }
    
    for item in registros:
        origem = item.get("origem", "Sem origem")
        registro = item.get("registro")
        registro_operacional = item.get("registro_operacional")
        
        if origem not in totais_fornecedor:
            totais_fornecedor[origem] = {
                "toneladas": 0,
                "valor_100": 0,
            }
        
        # Somar toneladas
        if registro_operacional and registro_operacional.peso_liquido_ticket:
            try:
                peso = float(registro_operacional.peso_liquido_ticket)
                totais_fornecedor[origem]["toneladas"] += peso
                total_geral["toneladas"] += peso
            except (ValueError, TypeError):
                pass
        
        # Somar valor (já está em centavos no banco)
        if registro and registro.valor_total_a_pagar_100:
            try:
                valor_100 = int(registro.valor_total_a_pagar_100)
                totais_fornecedor[origem]["valor_100"] += valor_100
                total_geral["valor_100"] += valor_100
            except (ValueError, TypeError):
                pass
    
    return {
        "por_fornecedor": totais_fornecedor,
        "geral": total_geral,
        "quantidade_fornecedores": len(totais_fornecedor),
    }


def obter_filtros():
    """
    Extrai os filtros do request (GET ou POST).
    
    Returns:
        dict: Dicionário com todos os filtros
    """
    source = request.form if request.method == "POST" else request.args
    
    return {
        "data_inicio": source.get("dataInicio"),
        "data_fim": source.get("dataFim"),
        "placa": source.get("placaCargaCliente"),
        "motorista": source.get("motoristaCargaCliente"),
        "transportadora": source.get("tranpostadoraCargaCliente"),
        "fornecedor": source.get("fornecedorCargaCliente"),
        "cliente": source.get("clienteCarga"),
        "numero_nf": source.get("numeroNfCliente"),
        "status_pagamento": source.get("statusPagamento"),
        "incompleto": source.get("registroIncompleto"),
    }


def obter_filtros_ativos(filtros):
    """
    Verifica se há algum filtro ativo.
    
    Args:
        filtros (dict): Dicionário de filtros
        
    Returns:
        bool: True se houver filtros ativos
    """
    return any(v for v in filtros.values() if v)


def buscar_registros(filtros):
    """
    Busca registros de fornecedores a pagar com base nos filtros.
    
    Args:
        filtros (dict): Dicionário com os filtros
        
    Returns:
        list: Lista de registros encontrados
    """
    if obter_filtros_ativos(filtros):
        return FornecedorPagarModel.filtrar_fornecedores_agrupados(
            data_inicio=filtros["data_inicio"],
            data_fim=filtros["data_fim"],
            placa=filtros["placa"],
            motorista=filtros["motorista"],
            transportadora=filtros["transportadora"],
            fornecedor=filtros["fornecedor"],
            cliente=filtros["cliente"],
            numero_nf=filtros["numero_nf"],
            statusPagamento=filtros["status_pagamento"]
        )
    else:
        return FornecedorPagarModel.obter_fornecedores_agrupados()


def formatar_valor_brl(valor):
    """
    Formata um valor numérico para o padrão brasileiro (R$ 1.234,56).
    
    Args:
        valor (float): Valor a ser formatado
        
    Returns:
        str: Valor formatado no padrão brasileiro
    """
    valor_str = "{:,.2f}".format(valor)
    # Substitui ',' por '.' e vice-versa
    valor_str = valor_str.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"R$ {valor_str}"


def preparar_dados_excel(registros):
    """
    Prepara os dados para exportação em Excel.
    
    Args:
        registros (list): Lista de registros
        
    Returns:
        list: Lista de dicionários formatados para Excel
    """
    dados_excel = []
    registros_por_origem = {}
    
    # Colunas do Excel
    colunas = ["Origem", "Data Entrega", "Placa/Motorista", "Transportadora", "Bitola", "Preço/Ton", "Peso Ticket", "Número NF", "A pagar fornecedor", "Status pagamento", "Incompleto"]
    
    # Totalizadores gerais
    total_geral_toneladas = 0
    total_geral_valor = 0
    
    # Agrupar por origem e produto
    for item in registros:
        origem = item.get("origem", "Sem origem")
        if origem not in registros_por_origem:
            registros_por_origem[origem] = {}
            
        produto = item.get("produto", "Sem produto")
        if produto not in registros_por_origem[origem]:
            registros_por_origem[origem][produto] = []
            
        registros_por_origem[origem][produto].append(item)

    # Gerar linhas do Excel
    for origem in sorted(registros_por_origem.keys()):
        produtos_origem = registros_por_origem[origem]
        
        # Cabeçalho da origem
        dados_excel.append({
            "Origem": origem.upper(),
            "Data Entrega": "",
            "Placa/Motorista": "",
            "Transportadora": "",
            "Bitola": "",
            "Preço/Ton": "",
            "Peso Ticket": "",
            "Número NF": "",
            "A pagar fornecedor": "",
            "Status pagamento": "",
            "Incompleto": "",
        })
        
        # Totalizadores do fornecedor
        total_fornecedor_toneladas = 0
        total_fornecedor_valor = 0
        
        for produto in sorted(produtos_origem.keys()):
            registros_produto = produtos_origem[produto]
            
            # Cabeçalho do produto
            dados_excel.append({
                "Origem": f"  PRODUTO: {produto}",
                "Data Entrega": "",
                "Placa/Motorista": "",
                "Transportadora": "",
                "Bitola": "",
                "Preço/Ton": "",
                "Peso Ticket": "",
                "Número NF": "",
                "A pagar fornecedor": "",
                "Status pagamento": "",
                "Incompleto": "",
            })
            
            total_produto = 0
            total_produto_toneladas = 0
            
            for item in registros_produto:
                registro = item["registro"]
                registro_operacional = item.get("registro_operacional")
                
                # Formatar motorista
                motorista_nome = ""
                if (registro.solicitacao and 
                    registro.solicitacao.motorista and 
                    registro.solicitacao.motorista.nome_completo):
                    nome_split = registro.solicitacao.motorista.nome_completo.split()
                    if len(nome_split) > 1:
                        motorista_nome = f"{nome_split[0]} {nome_split[1][0]}."
                    else:
                        motorista_nome = nome_split[0]
                
                # Formatar placa
                placa = (registro.solicitacao.veiculo.placa_veiculo 
                        if registro.solicitacao and registro.solicitacao.veiculo 
                        and registro.solicitacao.veiculo.placa_veiculo else "")
                placa_motorista = f"{placa} | {motorista_nome}" if motorista_nome else placa
                
                # Formatar transportadora
                transportadora = ""
                if (registro.solicitacao and 
                    registro.solicitacao.transportadora_exibicao and 
                    registro.solicitacao.transportadora_exibicao.identificacao):
                    transportadora = registro.solicitacao.transportadora_exibicao.identificacao
                
                # Formatar bitola
                bitola = ""
                if (registro.solicitacao and 
                    registro.solicitacao.bitola and 
                    registro.solicitacao.bitola.bitola):
                    bitola = registro.solicitacao.bitola.bitola
                
                # Formatar preço por bitola
                preco_bitola = ""
                if registro.preco_custo_bitola_100:
                    preco_bitola = formatar_valor_brl(registro.preco_custo_bitola_100 / 100)
                
                # Formatar peso
                peso_ticket = "Sem peso"
                peso_valor = 0
                if registro_operacional and registro_operacional.peso_liquido_ticket:
                    try:
                        peso_valor = float(registro_operacional.peso_liquido_ticket)
                        peso_ticket = f"{peso_valor:.2f}".replace('.', ',') + " Ton."
                        total_produto_toneladas += peso_valor
                        total_fornecedor_toneladas += peso_valor
                        total_geral_toneladas += peso_valor
                    except (ValueError, TypeError):
                        peso_ticket = f"{registro_operacional.peso_liquido_ticket} Ton."
                
                # Formatar número NF
                numero_nf = ""
                if registro_operacional:
                    if registro_operacional.estorno_nf:
                        numero_nf = f"{registro_operacional.numero_nota_fiscal_estorno} *"
                    elif registro_operacional.numero_nota_fiscal:
                        numero_nf = registro_operacional.numero_nota_fiscal
                
                # Calcular valor
                valor_pagar = 0
                if registro.valor_total_a_pagar_100:
                    valor_pagar = registro.valor_total_a_pagar_100 / 100
                    total_produto += valor_pagar
                    total_fornecedor_valor += valor_pagar
                    total_geral_valor += valor_pagar
                
                status = registro.situacao.situacao if registro.situacao else "Pendente"
                incompleto = "Sim" if registro.incompleto else "Não"
                
                dados_excel.append({
                    "Origem": "",
                    "Data Entrega": (registro.data_entrega_ticket.strftime("%d/%m/%Y") 
                                if registro.data_entrega_ticket else ""),
                    "Placa/Motorista": placa_motorista,
                    "Transportadora": transportadora,
                    "Bitola": bitola,
                    "Preço/Ton": preco_bitola,
                    "Peso Ticket": peso_ticket,
                    "Número NF": numero_nf,
                    "A pagar fornecedor": formatar_valor_brl(valor_pagar) if valor_pagar > 0 else "",
                    "Status pagamento": status,
                    "Incompleto": incompleto,
                })
            
            # Total do produto
            if registros_produto and total_produto > 0:
                dados_excel.append({
                    "Origem": "",
                    "Data Entrega": "",
                    "Placa/Motorista": "",
                    "Transportadora": "",
                    "Bitola": "",
                    "Preço/Ton": "",
                    "Peso Ticket": f"TOTAL: {total_produto_toneladas:.2f} Ton.".replace('.', ','),
                    "Número NF": "",
                    "A pagar fornecedor": f"TOTAL: {formatar_valor_brl(total_produto)}",
                    "Status pagamento": "",
                    "Incompleto": "",
                })
            
            # Linha em branco após produto
            dados_excel.append({k: "" for k in colunas})
        
        # Totalizador do fornecedor
        dados_excel.append({
            "Origem": f"TOTAL {origem.upper()}",
            "Data Entrega": "",
            "Placa/Motorista": "",
            "Transportadora": "",
            "Bitola": "",
            "Preço/Ton": "",
            "Peso Ticket": f"{total_fornecedor_toneladas:.2f} Ton.".replace('.', ','),
            "Número NF": "",
            "A pagar fornecedor": formatar_valor_brl(total_fornecedor_valor),
            "Status pagamento": "",
            "Incompleto": "",
        })
        
        # Linha em branco após origem
        dados_excel.append({k: "" for k in colunas})
    
    # Totalizador geral (somente se houver mais de um fornecedor)
    if len(registros_por_origem) > 1:
        dados_excel.append({
            "Origem": "TOTAL GERAL",
            "Data Entrega": "",
            "Placa/Motorista": "",
            "Transportadora": "",
            "Bitola": "",
            "Preço/Ton": "",
            "Peso Ticket": f"{total_geral_toneladas:.2f} Ton.".replace('.', ','),
            "Número NF": "",
            "A pagar fornecedor": formatar_valor_brl(total_geral_valor),
            "Status pagamento": "",
            "Incompleto": "",
        })

    return dados_excel


# ============================================================================
# VIEWS
# ============================================================================

@app.route("/relatorios/relatorios-financeiros/a-pagar-fornecedores", methods=["GET"])
@login_required
@requires_roles
def relatorio_a_pagar_fornecedores():
    """
    View principal: Listagem e filtro de fornecedores a pagar.
    """
    bitola = BitolaModel.listar_bitolas_ativas()
    produtos = ProdutoModel.listar_produtos()
    statusPagamentos = SituacaoPagamentoModel.listar_status()
    
    # Obter filtros e dados
    filtros = obter_filtros()
    registros = buscar_registros(filtros)
    
    # Calcular totalizadores
    totalizadores = calcular_totalizadores(registros)
    
    return render_template(
        "relatorios/relatorios_financeiros/relatorio_a_pagar_fornecedor/relatorio_a_pagar_fornecedor.html",
        registros=registros,
        bitola=bitola,
        produtos=produtos,
        statusPagamentos=statusPagamentos,
        dados_corretos=request.args,
        totalizadores=totalizadores,
    )


@app.route("/relatorios/relatorios-financeiros/a-pagar-fornecedores/exportar-pdf", methods=["POST"])
@login_required
@requires_roles
def relatorio_a_pagar_fornecedores_exportar_pdf():
    """
    View para exportação em PDF.
    """
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    dataHoje = datetime.now().strftime("%d-%m-%Y")
    
    # Obter filtros e dados
    filtros = obter_filtros()
    registros = buscar_registros(filtros)
    
    # Calcular totalizadores
    totalizadores = calcular_totalizadores(registros)
    
    logo_path = obter_url_absoluta_de_imagem("logo.png")
    html = render_template(
        "relatorios/relatorios_financeiros/relatorio_a_pagar_fornecedor/exportar_relatorio_a_pagar_fornecedor_pdf.html",
        logo_path=logo_path,
        changelog=changelog,
        dataHoje=dataHoje,
        dados_corretos=request.form,
        registros=registros,
        totalizadores=totalizadores,
    )

    nome_arquivo_saida = f"relacao_fornecedores_a_pagar_{dataHoje}"
    return ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida, "Landscape")


@app.route("/relatorios/relatorios-financeiros/a-pagar-fornecedores/exportar-excel", methods=["POST"])
@login_required
@requires_roles
def relatorio_a_pagar_fornecedores_exportar_excel():
    """
    View para exportação em Excel.
    """
    dataHoje = datetime.now().strftime("%d-%m-%Y")
    
    # Obter filtros e dados
    filtros = obter_filtros()
    registros = buscar_registros(filtros)
    
    # Preparar dados para Excel
    dados_excel = preparar_dados_excel(registros)
    
    nome_arquivo_saida = f"relatorio-fornecedores-a-pagar-{dataHoje}"
    return ManipulacaoArquivos.exportar_excel(dados_excel, nome_arquivo_saida)

