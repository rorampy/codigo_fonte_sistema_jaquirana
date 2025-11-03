from datetime import datetime
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem, formatar_float_para_brl, formatar_data_para_brl, formatar_float_para_brl_sem_cifrao
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from sistema._utilitarios import *
from sistema.models_views.controle_carga.produto_model import ProdutoModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
from io import BytesIO

def _safe_int(val):
    """Converte valor para inteiro, tratando 'NaN', None, vazios e valores inválidos"""
    try:
        if val is None or val == '' or str(val).lower() == 'nan':
            return 0
        return int(float(val))
    except (ValueError, TypeError):
        return 0

def _safe_float(val):
    """Converte valor para float, tratando 'NaN', None, vazios e valores inválidos"""
    try:
        if val is None or val == '' or str(val).lower() == 'nan':
            return 0.0
        return float(val)
    except (ValueError, TypeError):
        return 0.0

def gerar_graficos_precificacao(dados_precificacao):
    """
    Gera 3 gráficos usando os dados já calculados (resultado_calculo), evitando duplicidade de cálculos.
    """
    # Configuração global
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['axes.facecolor'] = 'white'

    graficos = {}

    resultado = dados_precificacao  

    # === GRÁFICO 1: COMPOSIÇÃO DE CUSTOS ===
    fig1, ax1 = plt.subplots(figsize=(7, 7))
    labels_comp = ['Mercadoria', 'Frete', 'Extração', 'Comissão']
    valores_comp = [
        resultado['operacoes']['compra']['total'],
        resultado['operacoes']['frete']['total'],
        resultado['operacoes']['extracao']['total'],
        resultado['operacoes']['comissao']['total']
    ]
    # Remove operações zeradas
    labels_comp = [l for l, v in zip(labels_comp, valores_comp) if v > 0]
    valores_comp = [v for v in valores_comp if v > 0]
    cores_comp = ['#1b5e20', '#e65100', '#fb8c00', '#81c784']
    ax1.pie(valores_comp, labels=labels_comp, autopct='%1.1f%%', colors=cores_comp[:len(valores_comp)], startangle=90, wedgeprops={'edgecolor': 'white'})
    ax1.set_title('Composição dos Custos', fontsize=14)
    buffer1 = BytesIO()
    plt.savefig(buffer1, format='png', dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    buffer1.seek(0)
    graficos['composicao'] = base64.b64encode(buffer1.getvalue()).decode()
    plt.close(fig1)

    # === GRÁFICO 2: MARGEM ===
    fig2, ax2 = plt.subplots(figsize=(7, 7))
    lucro_liquido = resultado['lucro_liquido']
    restante = resultado['receita_liquida'] - lucro_liquido  # CORRIGIDO: usa receita líquida
    labels_margem = ['Margem Líquida', 'CMV']
    valores_margem = [max(lucro_liquido, 0), max(restante, 0)]
    cores_margem = ['#388e3c', '#d32f2f']
    ax2.pie(valores_margem, labels=labels_margem, autopct='%1.1f%%', colors=cores_margem, startangle=90, wedgeprops={'edgecolor': 'white'})
    ax2.set_title('Margem Líquida sobre Receita Líquida', fontsize=14)
    buffer2 = BytesIO()
    plt.savefig(buffer2, format='png', dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    buffer2.seek(0)
    graficos['margem'] = base64.b64encode(buffer2.getvalue()).decode()
    plt.close(fig2)


    # === GRÁFICO 3: CRÉDITOS FISCAIS ===
    fig3, ax3 = plt.subplots(figsize=(7, 7))
    
    # Usar a fórmula correta: (total credito / total custo) * 100
    total_custos = resultado['cmv']
    total_creditos = resultado['total_impostos_compra']
    
    # Calcular porcentagem correta de créditos
    porcentagem_credito = (total_creditos / total_custos * 100) if total_custos > 0 else 0
    custo_liquido = total_custos - total_creditos
    
    labels_cred = ['Crédito Fiscal', 'Custo']
    valores_cred = [max(total_creditos, 0), max(custo_liquido, 0)]
    cores_cred = ['#4caf50', '#e65100']
    ax3.pie(valores_cred, labels=labels_cred, autopct='%1.1f%%', colors=cores_cred, startangle=90, wedgeprops={'edgecolor': 'white'})
    ax3.set_title('Créditos Fiscais vs Custo', fontsize=14)
    buffer3 = BytesIO()
    plt.savefig(buffer3, format='png', dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    buffer3.seek(0)
    graficos['creditos'] = base64.b64encode(buffer3.getvalue()).decode()
    plt.close(fig3)

    return graficos

@app.route('/financeiro/simular-precificacao', methods=['GET', 'POST'])
@login_required
@requires_roles
def simular_precificacao():
    produtos = ProdutoModel.listar_produtos()
    bitolas = BitolaModel.listar_bitolas()
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()

    if request.method == "POST":
        try:
            dados_precificacao = {
                # === DADOS DO PRODUTO ===
                'produto': request.form.get('produto', ''),
                'bitola': request.form.get('bitola', ''),
                'valor_unitario': _safe_int(request.form.get('valor_unitario', 0)),
                'quantidade': _safe_float(request.form.get('quantidade', 0)),
                'madeira_posta': request.form.get('madeira_posta', 'nao'),
                
                # === COMPRA DE MERCADORIA ===
                'compra': {
                    'emite_nota': request.form.get('emite_nota_compra', 'nao'),
                    'ajuste_fiscal': request.form.get('doc_fiscal_compra', 'nao'),
                    'funrural_senar': request.form.get('funrural', 'funrural'),
                    'funrural_descontado': request.form.get('funrural_descontado', 'sim'),
                    'estado_origem': request.form.get('estado_origem', ''),
                    'estado_destino': request.form.get('estado_destino', ''),
                    'classificacao_fiscal': request.form.get('classificacao_fiscal', ''),
                    'valor_ton': _safe_int(request.form.get('valor_ton_compra', 0)),
                },
                
                # === FRETE ===
                'frete': {
                    'emite_nota': request.form.get('emite_nota_frete', 'nao'),
                    'ajuste_fiscal': request.form.get('doc_fiscal_frete', 'nao'),
                    'origem': request.form.get('origem_frete', ''),
                    'destino': request.form.get('destino_frete', ''),
                    'prestador': request.form.get('prestador_frete', ''),
                    'tipo_nota': request.form.get('tipo_nota_frete', ''),
                    'valor_ton': _safe_int(request.form.get('valor_frete', 0)),
                },
                
                # === EXTRAÇÃO ===
                'extracao': {
                    'emite_nota': request.form.get('emite_nota_extracao', 'nao'),
                    'ajuste_fiscal': request.form.get('doc_fiscal_extracao', 'nao'),
                    'prestador': request.form.get('prestador_extracao', ''),
                    'valor_ton': _safe_int(request.form.get('valor_extracao', 0)),
                },
                
                # === COMISSÃO ===
                'comissao': {
                    'emite_nota': request.form.get('emite_nota_comissao', 'nao'),
                    'ajuste_fiscal': request.form.get('doc_fiscal_comissao', 'nao'),
                    'prestador': request.form.get('prestador_comissao', ''),
                    'valor_ton': _safe_int(request.form.get('valor_comissao', 0)),
                }
            }

            # Processa os cálculos
            resultado_calculo = processar_calculos_precificacao(dados_precificacao)
            graficos_relatorio = gerar_graficos_precificacao(resultado_calculo)
            
            # Prepara dados para o relatório
            logo_path = obter_url_absoluta_de_imagem("logo.png")

            tipo_relatorio = request.form.get('tipo_relatorio', 'detalhado')
            orientacao = ''
            if tipo_relatorio == 'simplificado':
                # Renderiza o relatório simplificado
                html = render_template(
                    "financeiro/precificacao_mbr/relatorio_precificacao/relatorio_precificacao_simplificado.html",
                    dados=dados_precificacao,
                    calculo=resultado_calculo,
                    logo_path=logo_path,
                    changelog=changelog
                )
                nome_arquivo_saida = f"relatorio-precificacao-simplificado"
                orientacao = 'Portrait'
            else:
                html = render_template(
                    "financeiro/precificacao_mbr/relatorio_precificacao/relatorio_precificacao_detalhado.html",
                    dados=dados_precificacao,
                    calculo=resultado_calculo,
                    logo_path=logo_path,
                    changelog=changelog,
                    graficos=graficos_relatorio
                )
                nome_arquivo_saida = f"relatorio-precificacao-detalhado"
                orientacao = 'landscape'
            resposta = ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida, orientacao)
            return resposta
            
        except Exception as e:
            print(f"Erro ao gerar relatório: {str(e)}") 
            flash(('Erro ao gerar relatório. Verifique os dados e tente novamente.', 'error'))
            return redirect(url_for('simular_precificacao'))

    return render_template(
        'financeiro/precificacao_mbr/precificacao_mbr.html', 
        produtos=produtos, 
        bitolas=bitolas,
        changelog=changelog
    )

def processar_calculos_precificacao(dados):
    """
    Processa todos os cálculos conforme as regras do JavaScript
    """
    resultado = {
        'receita_bruta': 0.0,
        'receita_liquida': 0.0,
        'impostos_venda': {},
        'operacoes': {},
        'cmv': 0,
        'lucro_bruto': 0,
        'lucro_liquido': 0,
        'margem_bruta': 0.0,
        'margem_liquida': 0.0,
        'total_despesas': 0,
        'total_impostos_compra': 0,
        'total_despesas_com_impostos': 0
    }
    
    # 1. RECEITA BRUTA 
    valor_unitario_reais = dados['valor_unitario']
    quantidade = dados['quantidade']
    resultado['receita_bruta'] = valor_unitario_reais * quantidade

    # 2. IMPOSTOS SOBRE VENDA
    ICMS_VENDA = 0.12
    PIS_VENDA = 0.0165
    COFINS_VENDA = 0.076
    icms_venda = resultado['receita_bruta'] * ICMS_VENDA
    pis_venda = resultado['receita_bruta'] * PIS_VENDA
    cofins_venda = resultado['receita_bruta'] * COFINS_VENDA
    resultado['impostos_venda'] = {
        'icms': icms_venda,
        'pis': pis_venda,
        'cofins': cofins_venda,
        'total': icms_venda + pis_venda + cofins_venda
    }

    # 3. RECEITA LÍQUIDA = Receita Bruta - Débitos + Créditos
    # Será calculada após processar as operações para ter os créditos disponíveis

    # 4. PROCESSAR CADA OPERAÇÃO
    compra = dados['compra'].copy()
    resultado['operacoes']['compra'] = processar_compra_mercadoria(compra, quantidade)

    frete = dados['frete'].copy()
    if dados['madeira_posta'] == 'nao':
        resultado['operacoes']['frete'] = processar_frete(frete, quantidade)
    else:
        resultado['operacoes']['frete'] = {'total': 0.0, 'icms': 0.0, 'pis': 0.0, 'cofins': 0.0, 'acrescimos': 0.0, 'valor_base': 0.0}

    extracao = dados['extracao'].copy()
    resultado['operacoes']['extracao'] = processar_extracao(extracao, quantidade)

    comissao = dados['comissao'].copy()
    resultado['operacoes']['comissao'] = processar_comissao(comissao, quantidade)

    # 5. SOMAR TOTAIS DAS OPERAÇÕES
    total_todas_operacoes = 0
    total_impostos_creditos = 0
    total_acrescimos = 0
    
    for operacao in resultado['operacoes'].values():
        total_todas_operacoes += operacao.get('total', 0)
        total_impostos_creditos += (operacao.get('icms', 0) + 
                                   operacao.get('pis', 0) + 
                                   operacao.get('cofins', 0))
        total_acrescimos += operacao.get('acrescimos', 0)

    # Custos base (sem impostos, sem acréscimos)
    custos_base = 0
    for operacao in resultado['operacoes'].values():
        custos_base += operacao.get('valor_base', 0)

    # Impostos de débito (sobre venda)
    impostos_venda_total = resultado['impostos_venda']['total']
    
    # Impostos de crédito (das operações de compra)
    icms_compras = (resultado['operacoes']['compra'].get('icms', 0) + 
                    resultado['operacoes']['frete'].get('icms', 0) + 
                    resultado['operacoes']['extracao'].get('icms', 0) + 
                    resultado['operacoes']['comissao'].get('icms', 0))
                    
    pis_compras = (resultado['operacoes']['compra'].get('pis', 0) + 
                   resultado['operacoes']['frete'].get('pis', 0) + 
                   resultado['operacoes']['extracao'].get('pis', 0) + 
                   resultado['operacoes']['comissao'].get('pis', 0))
                   
    cofins_compras = (resultado['operacoes']['compra'].get('cofins', 0) + 
                      resultado['operacoes']['frete'].get('cofins', 0) + 
                      resultado['operacoes']['extracao'].get('cofins', 0) + 
                      resultado['operacoes']['comissao'].get('cofins', 0))
    
    # Diferença de impostos (Débito - Crédito)
    diferenca_icms = resultado['impostos_venda']['icms'] - icms_compras
    diferenca_pis = resultado['impostos_venda']['pis'] - pis_compras  
    diferenca_cofins = resultado['impostos_venda']['cofins'] - cofins_compras
    diferenca_impostos_total = diferenca_icms + diferenca_pis + diferenca_cofins
    
    # 5. RECEITA LÍQUIDA = Receita Bruta - Débitos + Créditos
    total_impostos_credito = icms_compras + pis_compras + cofins_compras
    resultado['receita_liquida'] = resultado['receita_bruta'] - impostos_venda_total + total_impostos_credito
    
    # 6. CMV = Custos Base + Acréscimos (sem diferença de impostos)
    resultado['cmv'] = custos_base + total_acrescimos
    resultado['total_despesas'] = resultado['cmv']
    resultado['total_impostos_compra'] = total_impostos_creditos
    
    total_despesas_com_impostos_reais = custos_base + total_acrescimos
    resultado['total_despesas_com_impostos'] = total_despesas_com_impostos_reais

    # 7. LUCRO BRUTO
    resultado['lucro_bruto'] = resultado['receita_liquida'] - resultado['cmv']

    # 8. IMPOSTOS SOBRE LUCRO - Nova fórmula
    # Lucro Líquido = Lucro Real - (Lucro Real × 0,09) - [(Lucro Real - Lucro Real × 0,09) × 0,15]
    lucro_bruto = resultado['lucro_bruto']
    
    # Converter para reais para o cálculo
    lucro_real = lucro_bruto / 100
    
    total_impostos_lucro = 0
    
    if lucro_real > 0:
        # CSLL: 9% sobre o lucro real
        csll = lucro_real * 0.09
        
        # Base para IRPJ: Lucro Real - CSLL
        base_irpj = lucro_real - csll
        
        # IRPJ: 15% sobre a base (lucro real - CSLL)
        irpj = base_irpj * 0.15
        
        # Total de impostos
        total_impostos_lucro = csll + irpj
        
        # Lucro Líquido = Lucro Real - CSLL - IRPJ
        lucro_liquido_reais = lucro_real - total_impostos_lucro
    else:
        lucro_liquido_reais = lucro_real

    # Converter para centavos
    total_impostos_lucro_centavos = total_impostos_lucro * 100

    # 9. LUCRO LÍQUIDO
    resultado['lucro_liquido'] = lucro_liquido_reais * 100

    # 10. MARGENS CALCULADAS
    if resultado['receita_liquida'] > 0:
        resultado['margem_bruta'] = (resultado['lucro_bruto'] / resultado['receita_liquida']) * 100
        resultado['margem_liquida'] = (resultado['lucro_liquido'] / resultado['receita_liquida']) * 100
    else:
        resultado['margem_bruta'] = 0.0
        resultado['margem_liquida'] = 0.0

    return resultado

def processar_compra_mercadoria(compra, quantidade):
    """Processa cálculos da compra de mercadoria conforme regras do JS - corrigido"""
    valor_base = compra['valor_ton'] * quantidade  
    resultado = {
        'valor_base': valor_base,
        'icms': 0,
        'pis': 0,
        'cofins': 0,
        'acrescimos': 0,
        'total': 0
    }
    
    # LÓGICA DE CRÉDITOS FISCAIS:
    # Se emite_nota = "sim" → Gera créditos fiscais (sem acréscimos)
    # Se emite_nota = "não" E ajuste_fiscal = "sim" → Gera créditos fiscais E acréscimos
    # Se emite_nota = "não" E ajuste_fiscal = "não" → NÃO gera créditos fiscais nem acréscimos
    emite_nota = compra['emite_nota'] == 'sim'
    ajuste_fiscal = compra.get('ajuste_fiscal') == 'sim'
    gera_creditos = emite_nota or (not emite_nota and ajuste_fiscal)
    
    if gera_creditos:
        tipo_fornecedor = compra['classificacao_fiscal']
        
        # Aplica impostos conforme classificação fiscal
        if tipo_fornecedor == 'mei':
            # MEI: sem impostos
            pass
        elif tipo_fornecedor == 'pequeno_produtor':
            # Pequeno produtor: apenas FUNRURAL
            pass
        elif tipo_fornecedor in ['pessoa_fisica', 'pessoa_juridica_normal', 'pessoa_juridica_lucro_presumido']:
            # PF, PJ Normal, PJ Lucro Presumido: todos os impostos
            resultado['icms'] = valor_base * 0.12          # 12%
            resultado['pis'] = valor_base * 0.0165         # 1,65%  
            resultado['cofins'] = valor_base * 0.076       # 7,6%
        else:
            # Outros tipos: todos os impostos também
            resultado['icms'] = valor_base * 0.12          # 12%
            resultado['pis'] = valor_base * 0.0165         # 1,65%  
            resultado['cofins'] = valor_base * 0.076       # 7,6%

    # Funrural / Senar
    funrural_valor = 0
    if compra['funrural_senar'] == 'funrural':
        funrural_valor = valor_base * 0.015  # 1,5% FUNRURAL
    elif compra['funrural_senar'] == 'senar':
        funrural_valor = valor_base * 0.002  # 0,2% SENAR
    
    # Acréscimos fiscais (5% apenas quando sem nota e com ajuste fiscal)
    acrescimos_fiscais = 0
    if not emite_nota and ajuste_fiscal:
        acrescimos_fiscais = valor_base * 0.05
    
    # CÁLCULO DO TOTAL FINAL:
    # Total = valor_base + acréscimos fiscais + funrural/senar (apenas se não descontado)
    total_final = valor_base + acrescimos_fiscais
    
    # Soma Funrural/Senar apenas se descontado = 'nao' (empresa precisa pagar)
    if compra.get('funrural_descontado') == 'nao':
        total_final += funrural_valor
        # Quando incorpora no total, conta como acréscimo
        resultado['acrescimos'] = acrescimos_fiscais + funrural_valor
    else:
        # Quando não incorpora, apenas acréscimo fiscal
        resultado['acrescimos'] = acrescimos_fiscais
    
    resultado['total'] = total_final
    
    return resultado


def processar_frete(frete, quantidade):
    """Processa cálculos do frete conforme regras do JS corrigidas"""
    valor_base = frete['valor_ton'] * quantidade  
    resultado = {
        'valor_base': valor_base,
        'icms': 0,
        'pis': 0,
        'cofins': 0,
        'acrescimos': 0,
        'total': 0
    }
    
    # LÓGICA DE CRÉDITOS FISCAIS:
    # Se emite_nota = "sim" → Gera créditos fiscais (sem acréscimos)
    # Se emite_nota = "não" E ajuste_fiscal = "sim" → Gera créditos fiscais E acréscimos
    # Se emite_nota = "não" E ajuste_fiscal = "não" → NÃO gera créditos fiscais nem acréscimos
    emite_nota = frete['emite_nota'] == 'sim'
    ajuste_fiscal = frete.get('ajuste_fiscal') == 'sim'
    gera_creditos = emite_nota or (not emite_nota and ajuste_fiscal)
    
    if gera_creditos:
        if frete['prestador'] == 'PJ_SIMPLES':
            resultado['icms'] = 0
            if frete['tipo_nota'] == 'CTE':
                resultado['pis'] = valor_base * 0.012375  # 1,2375%
                resultado['cofins'] = valor_base * 0.057   # 5,7%
            elif frete['tipo_nota'] == 'SERVICO':
                resultado['pis'] = valor_base * 0.0165    # 1,65%
                resultado['cofins'] = valor_base * 0.076   # 7,6%
        elif frete['prestador'] == 'PJ_REAL':
            resultado['pis'] = valor_base * 0.0165        # 1,65%
            resultado['cofins'] = valor_base * 0.076       # 7,6%
            
            if frete['tipo_nota'] == 'CTE':
                # ICMS apenas se origem diferente do destino
                if frete['origem'] != frete['destino']:
                    resultado['icms'] = valor_base * 0.12  # 12%
    
    # Verifica acréscimos fiscais (5% apenas quando sem nota e com ajuste fiscal)
    if not emite_nota and ajuste_fiscal:
        resultado['acrescimos'] = valor_base * 0.05
    
    # CÁLCULO DO TOTAL FINAL DO FRETE:
    # Total = valor_base + acréscimos fiscais (ICMS, PIS, COFINS NÃO somam)
    resultado['total'] = valor_base + resultado['acrescimos']
    
    return resultado


def processar_extracao(extracao, quantidade):
    """Processa cálculos da extração conforme regras do JS - corrigido"""
    valor_base = extracao['valor_ton'] * quantidade  
    resultado = {
        'valor_base': valor_base,
        'icms': 0,
        'pis': 0,
        'cofins': 0,
        'acrescimos': 0,
        'total': 0
    }
    
    # LÓGICA DE CRÉDITOS FISCAIS:
    # Se emite_nota = "sim" → Gera créditos fiscais (sem acréscimos)
    # Se emite_nota = "não" E ajuste_fiscal = "sim" → Gera créditos fiscais E acréscimos
    # Se emite_nota = "não" E ajuste_fiscal = "não" → NÃO gera créditos fiscais nem acréscimos
    emite_nota = extracao['emite_nota'] == 'sim'
    ajuste_fiscal = extracao.get('ajuste_fiscal') == 'sim'
    gera_creditos = emite_nota or (not emite_nota and ajuste_fiscal)
    
    if gera_creditos:
        resultado['icms'] = 0  # Sempre 0 para serviços de extração
        resultado['pis'] = valor_base * 0.0165     # 1,65%
        resultado['cofins'] = valor_base * 0.076    # 7,6%
    
    # Verifica acréscimos fiscais (5% apenas quando sem nota e com ajuste fiscal)
    if not emite_nota and ajuste_fiscal:
        resultado['acrescimos'] = valor_base * 0.05
    
    # CÁLCULO DO TOTAL FINAL DA EXTRAÇÃO:
    # Total = valor_base + acréscimos fiscais (ICMS, PIS, COFINS NÃO somam)
    resultado['total'] = valor_base + resultado['acrescimos']
    
    return resultado


def processar_comissao(comissao, quantidade):
    """Processa cálculos da comissão conforme regras do JS - corrigido"""
    valor_base = comissao['valor_ton'] * quantidade  
    resultado = {
        'valor_base': valor_base,
        'icms': 0,
        'pis': 0,
        'cofins': 0,
        'acrescimos': 0,
        'total': 0
    }
    
    # LÓGICA DE CRÉDITOS FISCAIS:
    # Se emite_nota = "sim" → Gera créditos fiscais (sem acréscimos)
    # Se emite_nota = "não" E ajuste_fiscal = "sim" → Gera créditos fiscais E acréscimos
    # Se emite_nota = "não" E ajuste_fiscal = "não" → NÃO gera créditos fiscais nem acréscimos
    emite_nota = comissao['emite_nota'] == 'sim'
    ajuste_fiscal = comissao.get('ajuste_fiscal') == 'sim'
    gera_creditos = emite_nota or (not emite_nota and ajuste_fiscal)
    
    if gera_creditos:
        resultado['icms'] = 0  # Sempre 0 para serviços de comissão
        resultado['pis'] = valor_base * 0.0165     # 1,65%
        resultado['cofins'] = valor_base * 0.076    # 7,6%
    
    # Verifica acréscimos fiscais (5% apenas quando sem nota e com ajuste fiscal)
    if not emite_nota and ajuste_fiscal:
        resultado['acrescimos'] = valor_base * 0.05
    
    # CÁLCULO DO TOTAL FINAL DA COMISSÃO:
    # Total = valor_base + acréscimos fiscais (ICMS, PIS, COFINS NÃO somam)
    resultado['total'] = valor_base + resultado['acrescimos']
    
    return resultado