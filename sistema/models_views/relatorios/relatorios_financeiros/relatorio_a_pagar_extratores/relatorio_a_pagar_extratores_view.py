from datetime import datetime
from sistema import app, requires_roles, obter_url_absoluta_de_imagem
from flask import render_template, request
from flask_login import login_required
from sistema.models_views.faturamento.cargas_a_faturar.extrator.extrator_a_pagar_model import ExtratorPagarModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
from sistema.models_views.configuracoes_gerais.situacao_pagamento.situacao_pagamento_model import SituacaoPagamentoModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema._utilitarios import ManipulacaoArquivos


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def calcular_totalizadores_extrator(registros):
    """
    Calcula totalizadores por extrator e geral.
    
    Args:
        registros (list): Lista de registros
        
    Returns:
        dict: {
            'por_extrator': {extrator_id: {toneladas: float, valor_100: int}},
            'geral': {toneladas: float, valor_100: int},
            'quantidade_extratores': int
        }
    """
    totalizadores = {
        'por_extrator': {},
        'geral': {'toneladas': 0.0, 'valor_100': 0},
        'quantidade_extratores': 0
    }
    
    if not registros:
        return totalizadores
    
    extratores_unicos = set()
    
    for item in registros:
        # Identificar extrator
        extrator_obj = item.get('extrator')
        extrator_id = extrator_obj.identificacao if extrator_obj else 'Sem extrator'
        extratores_unicos.add(extrator_id)
        
        # Inicializar totalizador do extrator se não existir
        if extrator_id not in totalizadores['por_extrator']:
            totalizadores['por_extrator'][extrator_id] = {
                'toneladas': 0.0,
                'valor_100': 0
            }
        
        # Obter toneladas
        registro_op = item.get('registro_operacional')
        toneladas = 0.0
        if registro_op and registro_op.peso_liquido_ticket:
            toneladas = float(registro_op.peso_liquido_ticket)
        
        # Obter valor
        registro = item.get('registro')
        valor_100 = 0
        if registro and registro.valor_total_a_pagar_100:
            valor_100 = int(registro.valor_total_a_pagar_100)
        
        # Acumular no extrator
        totalizadores['por_extrator'][extrator_id]['toneladas'] += toneladas
        totalizadores['por_extrator'][extrator_id]['valor_100'] += valor_100
        
        # Acumular no geral
        totalizadores['geral']['toneladas'] += toneladas
        totalizadores['geral']['valor_100'] += valor_100
    
    totalizadores['quantidade_extratores'] = len(extratores_unicos)
    
    return totalizadores


def obter_filtros_extrator():
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
        "extrator": source.get("extratorCargaCliente"),
        "fornecedor": source.get("fornecedorCargaCliente"),
        "cliente": source.get("clienteCarga"),
        "numero_nf": source.get("numeroNfCliente"),
        "status_pagamento": source.get("statusPagamento"),
        "incompleto": source.get("registroIncompleto"),
    }


def obter_filtros_extrator_ativos(filtros):
    """
    Verifica se há algum filtro ativo.
    
    Args:
        filtros (dict): Dicionário de filtros
        
    Returns:
        bool: True se houver filtros ativos
    """
    return any(v for v in filtros.values() if v)


def buscar_registros_extrator(filtros):
    """
    Busca registros de extratores a pagar com base nos filtros.
    
    Args:
        filtros (dict): Dicionário com os filtros
        
    Returns:
        list: Lista de registros encontrados
    """
    if obter_filtros_extrator_ativos(filtros):
        return ExtratorPagarModel.filtrar_extratores_agrupados(
            data_inicio=filtros["data_inicio"],
            data_fim=filtros["data_fim"],
            placa=filtros["placa"],
            motorista=filtros["motorista"],
            transportadora=filtros["transportadora"],
            fornecedor=filtros["fornecedor"],
            cliente=filtros["cliente"],
            extrator=filtros["extrator"],
            numero_nf=filtros["numero_nf"],
            statusPagamento=filtros["status_pagamento"],
            incompleto=filtros["incompleto"],
        )
    else:
        return ExtratorPagarModel.obter_extratores_agrupados()


def preparar_dados_excel_extrator(registros):
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
            "Extrator": "Nenhum registro encontrado",
            "Data Entrega": "", "Transportadora": "", "Fornecedor": "",
            "Produto/Bitola": "", "Peso Ticket": "", "Preço Extração (Ton.)": "",
            "A pagar extrator": "", "Status pagamento": "",
        })
        return dados_excel
    
    registros_por_extrator = {}
    
    # Agrupar por extrator e produto
    for item in registros:
        extrator_obj = item.get("extrator")
        extrator_id = extrator_obj.identificacao if extrator_obj else "Sem extrator"
        
        if extrator_id not in registros_por_extrator:
            registros_por_extrator[extrator_id] = {}
            
        produto = item.get("produto", "Sem produto")
        if produto not in registros_por_extrator[extrator_id]:
            registros_por_extrator[extrator_id][produto] = []
            
        registros_por_extrator[extrator_id][produto].append(item)

    # Totalizadores gerais
    total_geral_toneladas = 0.0
    total_geral_valor = 0.0
    
    # Gerar linhas do Excel
    for extrator_id in sorted(registros_por_extrator.keys()):
        produtos_extrator = registros_por_extrator[extrator_id]
        
        # Cabeçalho do extrator
        dados_excel.append({
            "Extrator": f"EXTRATOR: {extrator_id.upper()}",
            "Data Entrega": "", "Transportadora": "", "Fornecedor": "",
            "Produto/Bitola": "", "Peso Ticket": "", "Preço Extração (Ton.)": "",
            "A pagar extrator": "", "Status pagamento": "",
        })
        
        total_extrator_toneladas = 0.0
        total_extrator_valor = 0.0
        
        for produto in sorted(produtos_extrator.keys()):
            registros_produto = produtos_extrator[produto]
            
            # Cabeçalho do produto
            dados_excel.append({
                "Extrator": f"  Produto: {produto}",
                "Data Entrega": "", "Transportadora": "", "Fornecedor": "",
                "Produto/Bitola": "", "Peso Ticket": "", "Preço Extração (Ton.)": "",
                "A pagar extrator": "", "Status pagamento": "",
            })
            
            total_produto_toneladas = 0.0
            total_produto_valor = 0.0
            
            for item in registros_produto:
                registro = item["registro"]
                registro_op = item.get("registro_operacional")
                
                # Formatar data entrega
                data_entrega = registro.data_entrega_ticket.strftime("%d/%m/%Y") if registro.data_entrega_ticket else "-"
                
                # Formatar transportadora
                transportadora = "-"
                if (registro.solicitacao and 
                    registro.solicitacao.transportadora_exibicao and 
                    registro.solicitacao.transportadora_exibicao.identificacao):
                    transportadora = registro.solicitacao.transportadora_exibicao.identificacao
                
                # Formatar fornecedor
                fornecedor = "-"
                if (registro.solicitacao and 
                    registro.solicitacao.fornecedor and 
                    registro.solicitacao.fornecedor.identificacao):
                    fornecedor = registro.solicitacao.fornecedor.identificacao
                
                # Formatar produto/bitola
                produto_nome = "-"
                bitola_nome = "-"
                if (registro.solicitacao and 
                    registro.solicitacao.produto and 
                    registro.solicitacao.produto.nome):
                    produto_nome = registro.solicitacao.produto.nome
                
                if (registro.solicitacao and 
                    registro.solicitacao.bitola and 
                    registro.solicitacao.bitola.bitola):
                    bitola_nome = registro.solicitacao.bitola.bitola
                
                produto_bitola = f"{produto_nome} | {bitola_nome}" if produto_nome != "-" or bitola_nome != "-" else "-"
                
                # Formatar peso
                peso_ticket = "Sem peso"
                toneladas = 0.0
                if registro_op and registro_op.peso_liquido_ticket:
                    toneladas = float(registro_op.peso_liquido_ticket)
                    peso_ticket = f"{toneladas:.2f} Ton."
                    total_produto_toneladas += toneladas
                
                # Formatar preço extração
                preco_extracao = "-"
                if registro.preco_custo_bitola_100:
                    preco_extracao = f"R$ {(registro.preco_custo_bitola_100 / 100):,.2f}"
                
                # Calcular valor
                valor_pagar_num = 0.0
                if registro.valor_total_a_pagar_100:
                    valor_pagar_num = registro.valor_total_a_pagar_100 / 100
                    total_produto_valor += valor_pagar_num
                
                status = registro.situacao.situacao if registro.situacao else "Pendente"
                
                dados_excel.append({
                    "Extrator": "",
                    "Data Entrega": data_entrega,
                    "Transportadora": transportadora,
                    "Fornecedor": fornecedor,
                    "Produto/Bitola": produto_bitola,
                    "Peso Ticket": peso_ticket,
                    "Preço Extração (Ton.)": preco_extracao,
                    "A pagar extrator": f"R$ {valor_pagar_num:,.2f}" if valor_pagar_num > 0 else "-",
                    "Status pagamento": status,
                })
            
            # Acumular totais do extrator
            total_extrator_toneladas += total_produto_toneladas
            total_extrator_valor += total_produto_valor
            
            # Total do produto (com toneladas)
            if registros_produto and (total_produto_toneladas > 0 or total_produto_valor > 0):
                dados_excel.append({
                    "Extrator": "", "Data Entrega": "", "Transportadora": "", "Fornecedor": "",
                    "Produto/Bitola": "", 
                    "Peso Ticket": f"TOTAL PRODUTO: {total_produto_toneladas:.2f} Ton.", 
                    "Preço Extração (Ton.)": "",
                    "A pagar extrator": f"R$ {total_produto_valor:,.2f}", 
                    "Status pagamento": "",
                })
            
            # Linha em branco após produto
            dados_excel.append({k: "" for k in ["Extrator", "Data Entrega", "Transportadora", "Fornecedor", "Produto/Bitola", "Peso Ticket", "Preço Extração (Ton.)", "A pagar extrator", "Status pagamento"]})
        
        # Acumular totais gerais
        total_geral_toneladas += total_extrator_toneladas
        total_geral_valor += total_extrator_valor
        
        # Total do extrator (com toneladas)
        if total_extrator_toneladas > 0 or total_extrator_valor > 0:
            dados_excel.append({
                "Extrator": "", "Data Entrega": "", "Transportadora": "", "Fornecedor": "",
                "Produto/Bitola": "", 
                "Peso Ticket": f"TOTAL EXTRATOR: {total_extrator_toneladas:.2f} Ton.", 
                "Preço Extração (Ton.)": "",
                "A pagar extrator": f"R$ {total_extrator_valor:,.2f}", 
                "Status pagamento": "",
            })
        
        # Linha em branco após extrator
        dados_excel.append({k: "" for k in ["Extrator", "Data Entrega", "Transportadora", "Fornecedor", "Produto/Bitola", "Peso Ticket", "Preço Extração (Ton.)", "A pagar extrator", "Status pagamento"]})

    # Total geral (apenas se houver mais de 1 extrator)
    if len(registros_por_extrator) > 1 and (total_geral_toneladas > 0 or total_geral_valor > 0):
        dados_excel.append({
            "Extrator": "", "Data Entrega": "", "Transportadora": "", "Fornecedor": "",
            "Produto/Bitola": "", 
            "Peso Ticket": f"TOTAL GERAL: {total_geral_toneladas:.2f} Ton.", 
            "Preço Extração (Ton.)": "",
            "A pagar extrator": f"R$ {total_geral_valor:,.2f}", 
            "Status pagamento": "",
        })

    return dados_excel


# ============================================================================
# VIEWS
# ============================================================================

@app.route("/relatorios/relatorios-financeiros/a-pagar-extrator", methods=["GET"])
@login_required
@requires_roles
def relatorio_a_pagar_extratores():
    """
    View principal: Listagem e filtro de extratores a pagar.
    """
    bitola = BitolaModel.listar_bitolas_ativas()
    produtos = ProdutoModel.listar_produtos()
    statusPagamentos = SituacaoPagamentoModel.listar_status()
    
    # Obter filtros e dados
    filtros = obter_filtros_extrator()
    registros = buscar_registros_extrator(filtros)
    totalizadores = calcular_totalizadores_extrator(registros)
    
    return render_template(
        "relatorios/relatorios_financeiros/relatorio_a_pagar_extrator/relatorio_a_pagar_extrator.html",
        registros=registros,
        bitola=bitola,
        produtos=produtos,
        statusPagamentos=statusPagamentos,
        dados_corretos=request.args,
        totalizadores=totalizadores,
    )


@app.route("/relatorios/relatorios-financeiros/a-pagar-extrator/exportar-pdf", methods=["POST"])
@login_required
@requires_roles
def relatorio_a_pagar_extratores_exportar_pdf():
    """
    View para exportação em PDF.
    """
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    dataHoje = datetime.now().strftime("%d-%m-%Y")
    
    # Obter filtros e dados
    filtros = obter_filtros_extrator()
    registros = buscar_registros_extrator(filtros)
    totalizadores = calcular_totalizadores_extrator(registros)
    
    logo_path = obter_url_absoluta_de_imagem("logo.png")
    html = render_template(
        "relatorios/relatorios_financeiros/relatorio_a_pagar_extrator/exportar_relatorio_a_pagar_extrator_pdf.html",
        logo_path=logo_path,
        changelog=changelog,
        dataHoje=dataHoje,
        dados_corretos=request.form,
        registros=registros,
        totalizadores=totalizadores
    )

    nome_arquivo_saida = f"relacao_extratores_a_pagar_{dataHoje}"
    return ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida, "Landscape")


@app.route("/relatorios/relatorios-financeiros/a-pagar-extrator/exportar-excel", methods=["POST"])
@login_required
@requires_roles
def relatorio_a_pagar_extratores_exportar_excel():
    """
    View para exportação em Excel.
    """
    dataHoje = datetime.now().strftime("%d-%m-%Y")
    
    # Obter filtros e dados
    filtros = obter_filtros_extrator()
    registros = buscar_registros_extrator(filtros)
    
    # Preparar dados para Excel
    dados_excel = preparar_dados_excel_extrator(registros)
    
    nome_arquivo_saida = f"relatorio-extratores-a-pagar-{dataHoje}"
    return ManipulacaoArquivos.exportar_excel(dados_excel, nome_arquivo_saida)

