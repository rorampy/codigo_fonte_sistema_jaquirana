from datetime import datetime
from sistema import app, requires_roles, obter_url_absoluta_de_imagem
from flask import render_template, request
from flask_login import login_required
from sistema.models_views.faturamento.cargas_a_faturar.transportadora.frete_a_pagar_model import FretePagarModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
from sistema.models_views.configuracoes_gerais.situacao_pagamento.situacao_pagamento_model import SituacaoPagamentoModel
from sistema.models_views.importacao_ofx.importacao_ofx_view import verificar_e_limpar_conciliacao_incorreta
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema._utilitarios import ManipulacaoArquivos


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def calcular_totalizadores_frete(registros):
    """
    Calcula os totalizadores por transportadora e o total geral.
    
    Args:
        registros (list): Lista de registros
        
    Returns:
        dict: Dicionário com totais por transportadora e total geral
              Os valores monetários são armazenados em centavos (valor_100)
              para uso com o filtro formatar_float_para_brl
    """
    totais_transportadora = {}
    total_geral = {
        "toneladas": 0,
        "valor_100": 0,
    }
    
    for item in registros:
        origem = item.get("origem", "Sem origem")
        registro = item.get("registro")
        registro_operacional = item.get("registro_operacional")
        
        if origem not in totais_transportadora:
            totais_transportadora[origem] = {
                "toneladas": 0,
                "valor_100": 0,
            }
        
        # Somar toneladas
        if registro_operacional and registro_operacional.peso_liquido_ticket:
            try:
                peso = float(registro_operacional.peso_liquido_ticket)
                totais_transportadora[origem]["toneladas"] += peso
                total_geral["toneladas"] += peso
            except (ValueError, TypeError):
                pass
        
        # Somar valor (já está em centavos no banco)
        if registro and registro.valor_total_a_pagar_100:
            try:
                valor_100 = int(registro.valor_total_a_pagar_100)
                totais_transportadora[origem]["valor_100"] += valor_100
                total_geral["valor_100"] += valor_100
            except (ValueError, TypeError):
                pass
    
    return {
        "por_transportadora": totais_transportadora,
        "geral": total_geral,
        "quantidade_transportadoras": len(totais_transportadora),
    }


def obter_filtros_frete():
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


def obter_filtros_frete_ativos(filtros):
    """
    Verifica se há algum filtro ativo.
    
    Args:
        filtros (dict): Dicionário de filtros
        
    Returns:
        bool: True se houver filtros ativos
    """
    return any(v for v in filtros.values() if v)


def buscar_registros_frete(filtros):
    """
    Busca registros de fretes a pagar com base nos filtros.
    
    Args:
        filtros (dict): Dicionário com os filtros
        
    Returns:
        list: Lista de registros encontrados
    """
    if obter_filtros_frete_ativos(filtros):
        return FretePagarModel.filtrar_frete_transportadora_agrupados(
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
        return FretePagarModel.obter_frete_transportadora_agrupados()


def preparar_dados_excel_frete(registros):
    """
    Prepara os dados para exportação em Excel.
    
    Args:
        registros (list): Lista de registros
        
    Returns:
        list: Lista de dicionários formatados para Excel
    """
    dados_excel = []
    
    if not registros:
        dados_excel.append({
            "Frete": "Nenhum registro encontrado",
            "Data Entrega": "", "Fornecedor": "", "Bitola": "", "Preço/Ton": "", "Peso Ticket": "",
            "Número NF": "", "A pagar frete": "", "Status pagamento": "",
            "Placa/Motorista": "", "Incompleto": "",
        })
        return dados_excel
    
    registros_por_origem = {}
    total_geral_valor = 0
    total_geral_toneladas = 0
    
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
            "Frete": f"FRETE: {origem.upper()}",
            "Data Entrega": "", "Fornecedor": "", "Bitola": "", "Preço/Ton": "", "Peso Ticket": "",
            "Número NF": "", "A pagar frete": "", "Status pagamento": "",
            "Placa/Motorista": "", "Incompleto": "",
        })
        
        total_transportadora_valor = 0
        total_transportadora_toneladas = 0
        
        for produto in sorted(produtos_origem.keys()):
            registros_produto = produtos_origem[produto]
            
            # Cabeçalho do produto
            dados_excel.append({
                "Frete": f"  Produto: {produto}",
                "Data Entrega": "", "Fornecedor": "", "Bitola": "", "Preço/Ton": "", "Peso Ticket": "",
                "Número NF": "", "A pagar frete": "", "Status pagamento": "",
                "Placa/Motorista": "", "Incompleto": "",
            })
            
            total_produto = 0
            total_produto_toneladas = 0
            
            for item in registros_produto:
                registro = item["registro"]
                registro_op = item.get("registro_operacional")
                
                # Formatar data entrega
                data_entrega = registro.data_entrega_ticket.strftime("%d/%m/%Y") if registro.data_entrega_ticket else "-"
                
                # Formatar fornecedor
                fornecedor = "-"
                if (registro.solicitacao and 
                    registro.solicitacao.fornecedor and 
                    registro.solicitacao.fornecedor.identificacao):
                    fornecedor = registro.solicitacao.fornecedor.identificacao
                
                # Formatar bitola
                bitola = "-"
                if (registro.solicitacao and 
                    registro.solicitacao.bitola and 
                    registro.solicitacao.bitola.bitola):
                    bitola = registro.solicitacao.bitola.bitola
                
                # Formatar preço por bitola
                preco_bitola = "-"
                if registro.preco_custo_bitola_100:
                    preco_bitola = f"R$ {registro.preco_custo_bitola_100 / 100:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                
                # Formatar peso
                peso_ticket = "Sem peso"
                peso_valor = 0
                if registro_op and registro_op.peso_liquido_ticket:
                    try:
                        peso_valor = float(registro_op.peso_liquido_ticket)
                        peso_ticket = f"{peso_valor:.2f}".replace('.', ',') + " Ton."
                        total_produto_toneladas += peso_valor
                        total_transportadora_toneladas += peso_valor
                        total_geral_toneladas += peso_valor
                    except (ValueError, TypeError):
                        peso_ticket = f"{registro_op.peso_liquido_ticket} Ton."
                
                # Formatar número NF
                numero_nf = "-"
                if registro_op and registro_op.estorno_nf:
                    numero_nf = f"{registro_op.numero_nota_fiscal_estorno} *"
                elif registro_op and registro_op.numero_nota_fiscal:
                    numero_nf = str(registro_op.numero_nota_fiscal)
                
                # Calcular valor
                valor_pagar = 0
                if registro.valor_total_a_pagar_100:
                    valor_pagar = registro.valor_total_a_pagar_100 / 100
                    total_produto += valor_pagar
                    total_transportadora_valor += valor_pagar
                    total_geral_valor += valor_pagar
                
                # Formatar placa e motorista
                placa = "-"
                motorista = ""
                if (registro.solicitacao and 
                    registro.solicitacao.veiculo and 
                    registro.solicitacao.veiculo.placa_veiculo):
                    placa = registro.solicitacao.veiculo.placa_veiculo
                
                if (registro.solicitacao and 
                    registro.solicitacao.motorista and 
                    registro.solicitacao.motorista.nome_completo):
                    nome_split = registro.solicitacao.motorista.nome_completo.split()
                    if len(nome_split) > 1:
                        motorista = f"{nome_split[0]} {nome_split[1][0]}."
                    elif len(nome_split) >= 1:
                        motorista = nome_split[0]
                
                placa_motorista = f"{placa} | {motorista}" if motorista else placa
                status = registro.situacao.situacao if registro.situacao else "Pendente"
                incompleto = "Sim" if registro.incompleto else "Não"
                
                dados_excel.append({
                    "Frete": "",
                    "Data Entrega": data_entrega,
                    "Fornecedor": fornecedor,
                    "Bitola": bitola,
                    "Preço/Ton": preco_bitola,
                    "Peso Ticket": peso_ticket,
                    "Número NF": numero_nf,
                    "A pagar frete": f"R$ {valor_pagar:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if valor_pagar > 0 else "-",
                    "Status pagamento": status,
                    "Placa/Motorista": placa_motorista,
                    "Incompleto": incompleto,
                })
            
            # Total do produto
            if registros_produto and total_produto > 0:
                dados_excel.append({
                    "Frete": "", "Data Entrega": "", "Fornecedor": "", "Bitola": "", "Preço/Ton": "",
                    "Peso Ticket": f"{total_produto_toneladas:.2f} Ton.".replace('.', ','),
                    "Número NF": "", "A pagar frete": f"TOTAL: R$ {total_produto:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                    "Status pagamento": "", "Placa/Motorista": "", "Incompleto": "",
                })
            
            # Linha em branco após produto
            dados_excel.append({k: "" for k in ["Frete", "Data Entrega", "Fornecedor", "Bitola", "Preço/Ton", "Peso Ticket", "Número NF", "A pagar frete", "Status pagamento", "Placa/Motorista", "Incompleto"]})
        
        # Totalizador da transportadora
        dados_excel.append({
            "Frete": f"TOTAL {origem.upper()}",
            "Data Entrega": "", "Fornecedor": "", "Bitola": "", "Preço/Ton": "",
            "Peso Ticket": f"{total_transportadora_toneladas:.2f} Ton.".replace('.', ','),
            "Número NF": "", "A pagar frete": f"R$ {total_transportadora_valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            "Status pagamento": "", "Placa/Motorista": "", "Incompleto": "",
        })
        
        # Linha em branco após origem
        dados_excel.append({k: "" for k in ["Frete", "Data Entrega", "Fornecedor", "Bitola", "Preço/Ton", "Peso Ticket", "Número NF", "A pagar frete", "Status pagamento", "Placa/Motorista", "Incompleto"]})
    
    # Totalizador geral (somente se houver mais de uma transportadora)
    if len(registros_por_origem) > 1:
        dados_excel.append({
            "Frete": "TOTAL GERAL",
            "Data Entrega": "", "Fornecedor": "", "Bitola": "", "Preço/Ton": "",
            "Peso Ticket": f"{total_geral_toneladas:.2f} Ton.".replace('.', ','),
            "Número NF": "", "A pagar frete": f"R$ {total_geral_valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            "Status pagamento": "", "Placa/Motorista": "", "Incompleto": "",
        })

    return dados_excel


# ============================================================================
# VIEWS
# ============================================================================

@app.route("/relatorios/relatorios-financeiros/a-pagar-frete", methods=["GET"])
@login_required
@requires_roles
def relatorio_a_pagar_fretes():
    """
    View principal: Listagem e filtro de fretes a pagar.
    """
    bitola = BitolaModel.listar_bitolas_ativas()
    produtos = ProdutoModel.listar_produtos()
    statusPagamentos = SituacaoPagamentoModel.listar_status()

    verificar_e_limpar_conciliacao_incorreta('pagamento_frete') 
    
    # Obter filtros e dados
    filtros = obter_filtros_frete()
    registros = buscar_registros_frete(filtros)
    
    # Calcular totalizadores
    totalizadores = calcular_totalizadores_frete(registros)
    
    return render_template(
        "relatorios/relatorios_financeiros/relatorio_a_pagar_frete/relatorio_a_pagar_frete.html",
        registros=registros,
        bitola=bitola,
        produtos=produtos,
        statusPagamentos=statusPagamentos,
        dados_corretos=request.args,
        totalizadores=totalizadores,
    )


@app.route("/relatorios/relatorios-financeiros/a-pagar-frete/exportar-pdf", methods=["POST"])
@login_required
@requires_roles
def relatorio_a_pagar_fretes_exportar_pdf():
    """
    View para exportação em PDF.
    """
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    dataHoje = datetime.now().strftime("%d-%m-%Y")
    
    # Obter filtros e dados
    filtros = obter_filtros_frete()
    registros = buscar_registros_frete(filtros)
    
    # Calcular totalizadores
    totalizadores = calcular_totalizadores_frete(registros)
    
    logo_path = obter_url_absoluta_de_imagem("logo.png")
    html = render_template(
        "relatorios/relatorios_financeiros/relatorio_a_pagar_frete/exportar_relatorio_a_pagar_frete_pdf.html",
        logo_path=logo_path,
        changelog=changelog,
        dataHoje=dataHoje,
        dados_corretos=request.form,
        registros=registros,
        totalizadores=totalizadores,
    )

    nome_arquivo_saida = f"relacao_fretes_a_pagar_{dataHoje}"
    return ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida, "Landscape")


@app.route("/relatorios/relatorios-financeiros/a-pagar-frete/exportar-excel", methods=["POST"])
@login_required
@requires_roles
def relatorio_a_pagar_fretes_exportar_excel():
    """
    View para exportação em Excel.
    """
    dataHoje = datetime.now().strftime("%d-%m-%Y")
    
    # Obter filtros e dados
    filtros = obter_filtros_frete()
    registros = buscar_registros_frete(filtros)
    
    # Preparar dados para Excel
    dados_excel = preparar_dados_excel_frete(registros)
    
    nome_arquivo_saida = f"relatorio-fretes-a-pagar-{dataHoje}"
    return ManipulacaoArquivos.exportar_excel(dados_excel, nome_arquivo_saida)

