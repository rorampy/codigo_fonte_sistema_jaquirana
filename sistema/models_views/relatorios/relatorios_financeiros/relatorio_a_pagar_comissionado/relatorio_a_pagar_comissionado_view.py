from datetime import datetime
from sistema import app, requires_roles, obter_url_absoluta_de_imagem
from flask import render_template, request
from flask_login import login_required
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
from sistema.models_views.configuracoes_gerais.situacao_pagamento.situacao_pagamento_model import SituacaoPagamentoModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema.models_views.faturamento.cargas_a_faturar.comissionado.comissionado_a_pagar_model import ComissionadoPagarModel
from sistema._utilitarios import ManipulacaoArquivos


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def calcular_totalizadores_comissionado(registros):
    """
    Calcula totalizadores por comissionado e geral.
    
    Args:
        registros (list): Lista de registros
        
    Returns:
        dict: {
            'por_comissionado': {comissionado_id: {toneladas: float, valor_100: int}},
            'geral': {toneladas: float, valor_100: int},
            'quantidade_comissionados': int
        }
    """
    totalizadores = {
        'por_comissionado': {},
        'geral': {'toneladas': 0.0, 'valor_100': 0},
        'quantidade_comissionados': 0
    }
    
    if not registros:
        return totalizadores
    
    comissionados_unicos = set()
    
    for item in registros:
        # Identificar comissionado
        comissionado_obj = item.get('comissionado')
        comissionado_id = comissionado_obj.identificacao if comissionado_obj else 'Sem comissionado'
        comissionados_unicos.add(comissionado_id)
        
        # Inicializar totalizador do comissionado se não existir
        if comissionado_id not in totalizadores['por_comissionado']:
            totalizadores['por_comissionado'][comissionado_id] = {
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
        
        # Acumular no comissionado
        totalizadores['por_comissionado'][comissionado_id]['toneladas'] += toneladas
        totalizadores['por_comissionado'][comissionado_id]['valor_100'] += valor_100
        
        # Acumular no geral
        totalizadores['geral']['toneladas'] += toneladas
        totalizadores['geral']['valor_100'] += valor_100
    
    totalizadores['quantidade_comissionados'] = len(comissionados_unicos)
    
    return totalizadores


def obter_filtros_comissionado(filtros_source):
    """
    Extrai e processa os filtros do request (form ou args).
    Retorna um dicionário com os filtros processados.
    """
    data_inicio_str = filtros_source.get("dataInicio")
    data_fim_str = filtros_source.get("dataFim")
    placa = filtros_source.get("placaCargaCliente")
    motorista = filtros_source.get("motoristaCargaCliente")
    transportadora = filtros_source.get("tranpostadoraCargaCliente")
    comissionado = filtros_source.get("comissionadoCargaCliente")
    fornecedor = filtros_source.get("fornecedorCargaCliente")
    cliente = filtros_source.get("clienteCarga")
    numero_nf = filtros_source.get("numeroNfCliente")
    incompleto = filtros_source.get("registroIncompleto")
    statusPagamento = filtros_source.get("statusPagamento")
    
    data_inicio = None
    data_fim = None
    
    if data_inicio_str:
        try:
            data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d")
        except ValueError:
            pass
            
    if data_fim_str:
        try:
            data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d")
        except ValueError:
            pass
    
    incompleto_bool = None
    if incompleto == "1":
        incompleto_bool = True
    elif incompleto == "0":
        incompleto_bool = False
    
    return {
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "placa": placa,
        "motorista": motorista,
        "transportadora": transportadora,
        "comissionado": comissionado,
        "fornecedor": fornecedor,
        "cliente": cliente,
        "numero_nf": numero_nf,
        "statusPagamento": statusPagamento,
        "incompleto": incompleto_bool,
    }


def obter_filtros_comissionado_ativos(filtros_source):
    """
    Verifica se há filtros ativos no request.
    """
    campos_filtro = [
        'dataInicio', 'dataFim', 'placaCargaCliente', 'motoristaCargaCliente',
        'tranpostadoraCargaCliente', 'comissionadoCargaCliente', 'fornecedorCargaCliente',
        'clienteCarga', 'numeroNfCliente', 'registroIncompleto', 'statusPagamento'
    ]
    return any(filtros_source.get(k) for k in campos_filtro)


def buscar_registros_comissionado(filtros_source):
    """
    Busca os registros de comissionados aplicando os filtros se houver.
    """
    filtros = obter_filtros_comissionado(filtros_source)
    
    # Verifica se há algum filtro ativo (exceto valores None/vazios)
    tem_filtros = any(v for v in filtros.values() if v is not None and v != "")
    
    if tem_filtros:
        return ComissionadoPagarModel.filtrar_comissionados_agrupados(
            data_inicio=filtros["data_inicio"],
            data_fim=filtros["data_fim"],
            placa=filtros["placa"],
            motorista=filtros["motorista"],
            transportadora=filtros["transportadora"],
            fornecedor=filtros["fornecedor"],
            cliente=filtros["cliente"],
            comissionado=filtros["comissionado"],
            numero_nf=filtros["numero_nf"],
            statusPagamento=filtros["statusPagamento"],
            incompleto=filtros["incompleto"],
        )
    else:
        return ComissionadoPagarModel.obter_comissionados_agrupados()


def preparar_dados_excel_comissionado(registros):
    """
    Prepara os dados para exportação em Excel, agrupados por comissionado e produto.
    Inclui totais por produto e por comissionado.
    """
    dados_excel = []
    
    if not registros:
        dados_excel.append({
            "Comissionado": "Nenhum registro encontrado",
            "Data Entrega": "",
            "Transportadora": "",
            "Fornecedor": "",
            "Produto/Bitola": "",
            "Peso Ticket": "",
            "Preço Comissão (Ton.)": "",
            "A pagar comissionado": "",
            "Status pagamento": "",
        })
        return dados_excel
    
    # Agrupar registros por comissionado e produto
    registros_por_comissionado = {}
    
    for item in registros:
        comissionado_obj = item.get("comissionado")
        comissionado_id = comissionado_obj.identificacao if comissionado_obj else "Sem comissionado"
        
        if comissionado_id not in registros_por_comissionado:
            registros_por_comissionado[comissionado_id] = {}
            
        produto = item.get("produto", "Sem produto")
        
        if produto not in registros_por_comissionado[comissionado_id]:
            registros_por_comissionado[comissionado_id][produto] = []
            
        registros_por_comissionado[comissionado_id][produto].append(item)

    total_geral_toneladas = 0.0
    total_geral_valor = 0.0
    
    for comissionado_id in sorted(registros_por_comissionado.keys()):
        produtos_comissionado = registros_por_comissionado[comissionado_id]
        
        dados_excel.append({
            "Comissionado": f"COMISSIONADO: {comissionado_id.upper()}",
            "Data Entrega": "",
            "Transportadora": "",
            "Fornecedor": "",
            "Produto/Bitola": "",
            "Peso Ticket": "",
            "Preço Comissão (Ton.)": "",
            "A pagar comissionado": "",
            "Status pagamento": "",
        })
        
        total_comissionado_toneladas = 0.0
        total_comissionado_valor = 0.0
        
        for produto in sorted(produtos_comissionado.keys()):
            registros_produto = produtos_comissionado[produto]
            
            dados_excel.append({
                "Comissionado": f"  Produto: {produto}",
                "Data Entrega": "",
                "Transportadora": "",
                "Fornecedor": "",
                "Produto/Bitola": "",
                "Peso Ticket": "",
                "Preço Comissão (Ton.)": "",
                "A pagar comissionado": "",
                "Status pagamento": "",
            })
            
            total_produto_toneladas = 0.0
            total_produto_valor = 0.0
            
            for item in registros_produto:
                registro = item["registro"]
                
                data_entrega = "-"
                if registro.data_entrega_ticket:
                    data_entrega = registro.data_entrega_ticket.strftime("%d/%m/%Y")
                
                transportadora = "-"
                if (registro.solicitacao and 
                    registro.solicitacao.transportadora_exibicao and 
                    registro.solicitacao.transportadora_exibicao.identificacao):
                    transportadora = registro.solicitacao.transportadora_exibicao.identificacao
                
                fornecedor = "-"
                if (registro.solicitacao and 
                    registro.solicitacao.fornecedor and 
                    registro.solicitacao.fornecedor.identificacao):
                    fornecedor = registro.solicitacao.fornecedor.identificacao
                
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
                
                peso_ticket = "Sem peso"
                toneladas = 0.0
                try:
                    registro_op = item.get("registro_operacional")
                    if registro_op and registro_op.peso_liquido_ticket:
                        toneladas = float(registro_op.peso_liquido_ticket)
                        peso_ticket = f"{toneladas:.2f} Ton."
                        total_produto_toneladas += toneladas
                except (KeyError, AttributeError):
                    peso_ticket = "Sem peso"
                
                preco_comissao = "-"
                if registro.preco_custo_bitola_100:
                    preco_comissao = f"R$ {(registro.preco_custo_bitola_100 / 100):,.2f}"
                
                valor_pagar_num = 0.0
                if registro.valor_total_a_pagar_100:
                    valor_pagar_num = registro.valor_total_a_pagar_100 / 100
                    total_produto_valor += valor_pagar_num
                
                status = "Pendente"
                if registro.situacao:
                    status = registro.situacao.situacao
                
                dados_excel.append({
                    "Comissionado": "",
                    "Data Entrega": data_entrega,
                    "Transportadora": transportadora,
                    "Fornecedor": fornecedor,
                    "Produto/Bitola": produto_bitola,
                    "Peso Ticket": peso_ticket,
                    "Preço Comissão (Ton.)": preco_comissao,
                    "A pagar comissionado": f"R$ {valor_pagar_num:,.2f}" if valor_pagar_num > 0 else "-",
                    "Status pagamento": status,
                })
            
            # Acumular totais do comissionado
            total_comissionado_toneladas += total_produto_toneladas
            total_comissionado_valor += total_produto_valor
            
            # Total por produto (com toneladas)
            dados_excel.append({
                "Comissionado": f"    SUBTOTAL {produto}:",
                "Data Entrega": "",
                "Transportadora": "",
                "Fornecedor": "",
                "Produto/Bitola": "",
                "Peso Ticket": f"{total_produto_toneladas:.2f} Ton.",
                "Preço Comissão (Ton.)": "",
                "A pagar comissionado": f"R$ {total_produto_valor:,.2f}",
                "Status pagamento": "",
            })
        
        # Acumular totais gerais
        total_geral_toneladas += total_comissionado_toneladas
        total_geral_valor += total_comissionado_valor
        
        # Total por comissionado (com toneladas)
        dados_excel.append({
            "Comissionado": f"TOTAL {comissionado_id.upper()}:",
            "Data Entrega": "",
            "Transportadora": "",
            "Fornecedor": "",
            "Produto/Bitola": "",
            "Peso Ticket": f"{total_comissionado_toneladas:.2f} Ton.",
            "Preço Comissão (Ton.)": "",
            "A pagar comissionado": f"R$ {total_comissionado_valor:,.2f}",
            "Status pagamento": "",
        })
        
        # Linha em branco para separar comissionados
        dados_excel.append({
            "Comissionado": "",
            "Data Entrega": "",
            "Transportadora": "",
            "Fornecedor": "",
            "Produto/Bitola": "",
            "Peso Ticket": "",
            "Preço Comissão (Ton.)": "",
            "A pagar comissionado": "",
            "Status pagamento": "",
        })
    
    # Total geral (apenas se houver mais de 1 comissionado)
    if len(registros_por_comissionado) > 1:
        dados_excel.append({
            "Comissionado": "TOTAL GERAL:",
            "Data Entrega": "",
            "Transportadora": "",
            "Fornecedor": "",
            "Produto/Bitola": "",
            "Peso Ticket": f"{total_geral_toneladas:.2f} Ton.",
            "Preço Comissão (Ton.)": "",
            "A pagar comissionado": f"R$ {total_geral_valor:,.2f}",
            "Status pagamento": "",
        })
    
    return dados_excel


# ============================================================================
# ROTAS
# ============================================================================

@app.route("/relatorios/relatorios-financeiros/a-pagar-comissionado", methods=["GET"])
@login_required
@requires_roles
def relatorio_a_pagar_comissionados():
    """
    Rota principal para exibição do relatório de comissionados a pagar.
    Aceita apenas GET - exibe a listagem com filtros aplicados.
    """
    bitola = BitolaModel.listar_bitolas_ativas()
    produtos = ProdutoModel.listar_produtos()
    statusPagamentos = SituacaoPagamentoModel.listar_status()
    
    filtros_source = request.args
    dados_corretos = filtros_source
    
    registros = buscar_registros_comissionado(filtros_source)
    totalizadores = calcular_totalizadores_comissionado(registros)

    return render_template(
        "relatorios/relatorios_financeiros/relatorio_a_pagar_comissionado/relatorio_a_pagar_comissionado.html",
        registros=registros,
        bitola=bitola,
        produtos=produtos,
        statusPagamentos=statusPagamentos,
        dados_corretos=dados_corretos,
        totalizadores=totalizadores,
    )


@app.route("/relatorios/relatorios-financeiros/a-pagar-comissionado/exportar-pdf", methods=["POST"])
@login_required
@requires_roles
def relatorio_a_pagar_comissionados_exportar_pdf():
    """
    Rota para exportação do relatório em PDF.
    Aceita apenas POST com os filtros do formulário.
    """
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    dataHoje = datetime.now().strftime("%d-%m-%Y")
    
    filtros_source = request.form if obter_filtros_comissionado_ativos(request.form) else request.args
    dados_corretos = filtros_source
    
    registros = buscar_registros_comissionado(filtros_source)
    totalizadores = calcular_totalizadores_comissionado(registros)
    
    logo_path = obter_url_absoluta_de_imagem("logo.png")
    html = render_template(
        "relatorios/relatorios_financeiros/relatorio_a_pagar_comissionado/exportar_relatorio_a_pagar_comissionado_pdf.html",
        logo_path=logo_path,
        changelog=changelog,
        dataHoje=dataHoje,
        dados_corretos=dados_corretos,
        registros=registros,
        totalizadores=totalizadores
    )

    nome_arquivo_saida = f"relacao_comissionados_a_pagar_{dataHoje}"
    return ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida, "Landscape")


@app.route("/relatorios/relatorios-financeiros/a-pagar-comissionado/exportar-excel", methods=["POST"])
@login_required
@requires_roles
def relatorio_a_pagar_comissionados_exportar_excel():
    """
    Rota para exportação do relatório em Excel.
    Aceita apenas POST com os filtros do formulário.
    """
    dataHoje = datetime.now().strftime("%d-%m-%Y")
    
    filtros_source = request.form if obter_filtros_comissionado_ativos(request.form) else request.args
    
    registros = buscar_registros_comissionado(filtros_source)
    
    dados_excel = preparar_dados_excel_comissionado(registros)
    
    nome_arquivo_saida = f"relatorio-comissionados-a-pagar-{dataHoje}"
    return ManipulacaoArquivos.exportar_excel(dados_excel, nome_arquivo_saida)

