from datetime import datetime
from sistema import app, requires_roles, obter_url_absoluta_de_imagem
from flask import render_template, request
from flask_login import login_required
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema._utilitarios import *
from sistema._utilitarios.valores_monetarios import ValoresMonetarios
from itertools import groupby

@app.route("/relatorios/relatorios-financeiros/cargas-gerais-cliente", methods=["POST"])
@login_required
@requires_roles
def relatorio_cargas_gerais_cliente():
    """
    Relatório de Cargas Gerais por Clientes com informações detalhadas
    incluindo preço NFe e valor complementar
    """
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    dataHoje = datetime.now().strftime("%d-%m-%Y")
    
    # Obter filtros
    data_inicio = request.form.get("dataInicio")
    data_fim = request.form.get("dataFim")
    cliente = request.form.get("clienteCarga")
    numero_nf = request.form.get("numeroNfCliente")
    produto = request.form.get("produtoFiltro")
    bitola = request.form.get("bitolaFiltro")
    fornecedor = request.form.get("fornecedorCargaCliente")
    exportar_pdf = request.form.get("exportar_pdf")
    exportar_excel = request.form.get("exportar_excel")
    
    # Filtrar registros
    registros = RegistroOperacionalModel.filtrar_registros_carga_cliente(
        data_inicio=data_inicio,
        data_fim=data_fim,
        cliente=cliente,
        numero_nf=numero_nf,
        produto=produto,
        bitola=bitola,
        fornecedor=fornecedor
    )
    
    dados_corretos = request.form
    
    if exportar_pdf or exportar_excel:
        # Processar registros para exportação
        dados_exportacao = []
        
        for item in registros:
            registro = item['registro']
            
            # Calcular valores
            peso_nf = registro.peso_ton_nf if registro.peso_ton_nf else 0
            peso_ticket = registro.peso_liquido_ticket if registro.peso_liquido_ticket else 0
            peso_diferenca = round(peso_nf - peso_ticket, 2)
            
            # Manter preco_nf em centavos para Excel
            preco_nf_centavos = registro.preco_un_nf if registro.preco_un_nf else 0
            preco_nf_float = preco_nf_centavos / 100
            
            # Calcular valores em centavos (para usar formatar_float_para_brl no template)
            valor_total_nf_centavos = round(peso_nf * preco_nf_float * 100)
            valor_complementar_centavos = round(peso_diferenca * preco_nf_float * 100)
            
            # Obter informações adicionais
            placa = registro.solicitacao.veiculo.placa_veiculo if registro.solicitacao and registro.solicitacao.veiculo else '-'
            
            origem = ''
            if registro.solicitacao:
                if registro.solicitacao.fornecedor:
                    origem = registro.solicitacao.fornecedor.identificacao
                elif registro.solicitacao.floresta:
                    origem = registro.solicitacao.floresta.identificacao
                else:
                    origem = '-'
            else:
                origem = '-'
            
            cliente_nome = item.get('cliente', '-')
            
            produto_bitola = ''
            if registro.solicitacao:
                produto_nome = registro.solicitacao.produto.nome if registro.solicitacao.produto else '-'
                bitola_nome = registro.solicitacao.bitola.bitola if registro.solicitacao.bitola else '-'
                produto_bitola = f"{produto_nome} / {bitola_nome}"
            else:
                produto_bitola = '-'
            
            numero_nf = registro.numero_nota_fiscal_estorno if registro.estorno_nf else (registro.numero_nota_fiscal or '-')
            
            dados_exportacao.append({
                'placa': placa,
                'origem': origem,
                'cliente': cliente_nome,
                'produto_bitola': produto_bitola,
                'nf': numero_nf,
                'peso_liquido': peso_ticket,
                'peso_nfe': peso_nf,
                'preco_nfe': preco_nf_centavos,  # Em centavos para template
                'preco_nfe_float': preco_nf_float,  # Float para Excel
                'total_nfe': valor_total_nf_centavos,  # Em centavos para template
                'total_nfe_float': valor_total_nf_centavos / 100,  # Float para Excel
                'valor_complementar': valor_complementar_centavos,  # Em centavos para template
                'valor_complementar_float': valor_complementar_centavos / 100,  # Float para Excel
                'peso_complementar': peso_diferenca
            })
        
        # Agrupar por cliente
        dados_exportacao.sort(key=lambda x: x['cliente'])
        registros_agrupados = []
        
        for cliente_nome, grupo_cliente in groupby(dados_exportacao, key=lambda x: x['cliente']):
            lista_cliente = list(grupo_cliente)
            
            # Calcular totais por cliente
            total_peso_liquido = sum(item['peso_liquido'] for item in lista_cliente)
            total_peso_nfe = sum(item['peso_nfe'] for item in lista_cliente)
            total_nfe = sum(item['total_nfe'] for item in lista_cliente)  # Em centavos
            total_nfe_float = sum(item['total_nfe_float'] for item in lista_cliente)  # Float para Excel
            total_valor_complementar = sum(item['valor_complementar'] for item in lista_cliente)  # Em centavos
            total_valor_complementar_float = sum(item['valor_complementar_float'] for item in lista_cliente)  # Float para Excel
            total_peso_complementar = sum(item['peso_complementar'] for item in lista_cliente)
            
            registros_agrupados.append({
                'cliente': cliente_nome,
                'registros': lista_cliente,
                'totais': {
                    'peso_liquido': total_peso_liquido,
                    'peso_nfe': total_peso_nfe,
                    'total_nfe': total_nfe,  # Em centavos para template
                    'total_nfe_float': total_nfe_float,  # Float para Excel
                    'valor_complementar': total_valor_complementar,  # Em centavos para template
                    'valor_complementar_float': total_valor_complementar_float,  # Float para Excel
                    'peso_complementar': total_peso_complementar
                }
            })
        
        if exportar_pdf:
            logo_path = obter_url_absoluta_de_imagem("logo.png")
            html = render_template(
                "relatorios/relatorios_financeiros/relatorio_cargas_gerais_cliente/exportar_relatorio_cargas_gerais_cliente_pdf.html",
                logo_path=logo_path,
                dataHoje=dataHoje,
                registros_agrupados=registros_agrupados,
                dados_corretos=dados_corretos,
                changelog=changelog,
            )
            nome_arquivo_saida = f"relatorio-cargas-gerais-cliente-{dataHoje}"
            resposta = ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida, "Landscape")
            return resposta
        
        if exportar_excel:
            # Preparar dados para Excel
            linhas_excel = []
            
            # Dados por cliente
            for grupo in registros_agrupados:
                # Registros do cliente
                for idx, reg in enumerate(grupo['registros']):
                    linhas_excel.append({
                        'Placa': reg['placa'],
                        'Origem': reg['origem'],
                        'Cliente': reg['cliente'] if idx == 0 else '',
                        'Produto/Bitola': reg['produto_bitola'],
                        'NF': reg['nf'],
                        'Peso Líquido (Ton)': f"{reg['peso_liquido']:.2f}" if reg['peso_liquido'] else '-',
                        'Peso NFe': f"{reg['peso_nfe']:.2f}" if reg['peso_nfe'] else '-',
                        'Preço NFe': ValoresMonetarios.converter_float_brl_positivo(reg['preco_nfe_float']) if reg['preco_nfe_float'] else '-',
                        'Total NFe': ValoresMonetarios.converter_float_brl_positivo(reg['total_nfe_float']) if reg['total_nfe_float'] else '-',
                        'Valor Complementar': ValoresMonetarios.converter_float_brl_positivo(reg['valor_complementar_float']) if reg['valor_complementar_float'] else '-',
                        'Peso Complementar': f"{reg['peso_complementar']:.2f}" if reg['peso_complementar'] else '-'
                    })
                
                # Linha de totais do cliente
                linhas_excel.append({
                    'Placa': '',
                    'Origem': '',
                    'Cliente': '',
                    'Produto/Bitola': '',
                    'NF': 'Total',
                    'Peso Líquido (Ton)': f"{grupo['totais']['peso_liquido']:.2f} TN",
                    'Peso NFe': f"{grupo['totais']['peso_nfe']:.2f}",
                    'Preço NFe': '',
                    'Total NFe': ValoresMonetarios.converter_float_brl_positivo(grupo['totais']['total_nfe_float']),
                    'Valor Complementar': ValoresMonetarios.converter_float_brl_positivo(grupo['totais']['valor_complementar_float']),
                    'Peso Complementar': f"{grupo['totais']['peso_complementar']:.2f} TN"
                })
                
                # Linha em branco entre clientes
                linhas_excel.append({
                    'Placa': '', 'Origem': '', 'Cliente': '', 'Produto/Bitola': '',
                    'NF': '', 'Peso Líquido (Ton)': '', 'Peso NFe': '', 'Preço NFe': '',
                    'Total NFe': '', 'Total Cliente': '', 'Valor Complementar': '', 'Peso Complementar': ''
                })
            
            nome_arquivo_saida = f"relatorio-cargas-gerais-cliente-{dataHoje}"
            resposta = ManipulacaoArquivos.exportar_excel(linhas_excel, nome_arquivo_saida)
            return resposta
    
    # Se não for exportação, redirecionar
    from flask import redirect, url_for, flash
    flash(("Selecione uma opção de exportação (Excel ou PDF)", "warning"))
    return redirect(url_for('principal'))
