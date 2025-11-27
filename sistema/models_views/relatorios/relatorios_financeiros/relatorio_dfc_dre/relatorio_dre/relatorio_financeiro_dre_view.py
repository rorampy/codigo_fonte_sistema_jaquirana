from datetime import datetime, date
import calendar
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem, formatar_float_para_brl, formatar_data_para_brl, formatar_float_para_brl_sem_cifrao
from sistema._utilitarios.data_e_hora import DataHora
from flask import render_template, request, redirect, url_for, flash, session, jsonify, make_response, send_file
from flask_login import login_required
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.financeiro.operacional.categorizar_fatura.categorizacao_model import AgendamentoPagamentoModel
from sistema.models_views.relatorios.relatorios_financeiros.relatorio_dfc_dre.relatorio_dre.dre_model import DREModel
from sistema._utilitarios import *
import json
import os

@app.route('/relatorios/relatorios-financeiros/dre-analitico', methods=['GET', 'POST'])
@login_required
@requires_roles
def dre_analitico():
    """
    Rota para exibir DRE Analítico com filtros por período
    """
    try:
        # Valores padrão - mês atual
        data_fim_default = date.today()
        data_inicio_default = date(data_fim_default.year, data_fim_default.month, 1)  # Primeiro dia do mês atual
        exercicio_default = DataHora.obter_exercicio_mes_atual()  # Exercício do mês atual
        
        # Coletar dados do formulário
        dados_form = {
            'data_inicio': request.form.get('data_inicio') or request.args.get('data_inicio', data_inicio_default.strftime('%Y-%m-%d')),
            'data_fim': request.form.get('data_fim') or request.args.get('data_fim', data_fim_default.strftime('%Y-%m-%d')),
            'exercicio': request.form.get('exercicio') or request.args.get('exercicio', exercicio_default),
            'exportar_pdf': request.form.get('exportar_pdf'),
            'exportar_excel': request.form.get('exportar_excel')
        }
        
        # Processar datas - SEMPRE usar dados do formulário primeiro
        if dados_form['exercicio'] and dados_form['exercicio'] != exercicio_default:
            try:
                # Usar a função dos utilitários para obter período completo
                data_inicio, data_fim = DataHora.obter_periodo_completo_mes(dados_form['exercicio'])
                
                # Atualizar dados_form
                dados_form['data_inicio'] = data_inicio.strftime('%Y-%m-%d')
                dados_form['data_fim'] = data_fim.strftime('%Y-%m-%d')
                
            except ValueError as e:
                flash((str(e), 'error'))
                # Usar dados do formulário como fallback
                try:
                    data_inicio = datetime.strptime(dados_form['data_inicio'], '%Y-%m-%d').date()
                    data_fim = datetime.strptime(dados_form['data_fim'], '%Y-%m-%d').date()
                except ValueError:
                    data_inicio = data_inicio_default
                    data_fim = data_fim_default
                    dados_form['data_inicio'] = data_inicio.strftime('%Y-%m-%d')
                    dados_form['data_fim'] = data_fim.strftime('%Y-%m-%d')
                dados_form['exercicio'] = ''
        else:
            # Converter strings de data para objetos date - PRIORIZAR dados do form
            try:
                data_inicio = datetime.strptime(dados_form['data_inicio'], '%Y-%m-%d').date()
                data_fim = datetime.strptime(dados_form['data_fim'], '%Y-%m-%d').date()
                
                # Debug: log das datas processadas do range
                print(f"DEBUG DRE Analítico - Range manual processado: Data início: {data_inicio}, Data fim: {data_fim}")
                
            except ValueError:
                flash(('Datas inválidas fornecidas!', 'error'))
                data_inicio = data_inicio_default
                data_fim = data_fim_default
                dados_form['data_inicio'] = data_inicio.strftime('%Y-%m-%d')
                dados_form['data_fim'] = data_fim.strftime('%Y-%m-%d')
            
            # Verificar se as datas são válidas
            if data_inicio > data_fim:
                flash(('Data de início não pode ser maior que data de fim!', 'error'))
                data_inicio = data_inicio_default
                data_fim = data_fim_default
                dados_form['data_inicio'] = data_inicio.strftime('%Y-%m-%d')
                dados_form['data_fim'] = data_fim.strftime('%Y-%m-%d')
        
        # Gerar DRE analítico com as datas processadas
        dre_dados = DREModel.gerar_dre_analitico(data_inicio, data_fim)
        
        if dados_form['exportar_pdf']:
            print(f"DEBUG: Exportando PDF DRE Analítico com data_inicio: {data_inicio}, data_fim: {data_fim}")
            return exportar_dre_pdf(dre_dados, data_inicio, data_fim)
        

        return render_template(
            'relatorios/relatorios_financeiros/relatorio_dfc_dre/dre/dre_analitico.html',
            dre_dados=dre_dados,
            dados_form=dados_form,
            exercicios_disponiveis=DataHora.obter_exercicios_disponiveis_ano_atual(),
            formatar_float_para_brl=formatar_float_para_brl,
            formatar_data_para_brl=formatar_data_para_brl
        )
        
    except Exception as e:
        flash((f'Erro ao gerar DRE Analítico: {str(e)}', 'error'))
        return render_template(
            'relatorios/relatorios_financeiros/relatorio_dfc_dre/dre/dre_analitico.html',
            dre_dados=None,
            dados_form={'data_inicio': data_inicio_default.strftime('%Y-%m-%d'), 'data_fim': data_fim_default.strftime('%Y-%m-%d')},
            exercicios_disponiveis=DataHora.obter_exercicios_disponiveis_ano_atual(),
            formatar_float_para_brl=formatar_float_para_brl,
            formatar_data_para_brl=formatar_data_para_brl
        )

@app.route('/relatorios/relatorios-financeiros/dre-sintetico', methods=['GET', 'POST'])
@login_required
@requires_roles
def dre_sintetico():
    """
    Rota para exibir DRE Sintético com filtros por período
    """
    try:
        # Valores padrão - mês atual
        data_fim_default = date.today()
        data_inicio_default = date(data_fim_default.year, data_fim_default.month, 1)  # Primeiro dia do mês atual
        exercicio_default = DataHora.obter_exercicio_mes_atual()  # Exercício do mês atual
        
        # Coletar dados do formulário
        dados_form = {
            'data_inicio': request.form.get('data_inicio') or request.args.get('data_inicio', data_inicio_default.strftime('%Y-%m-%d')),
            'data_fim': request.form.get('data_fim') or request.args.get('data_fim', data_fim_default.strftime('%Y-%m-%d')),
            'exercicio': request.form.get('exercicio') or request.args.get('exercicio', exercicio_default),
            'exportar_pdf': request.form.get('exportar_pdf'),
            'exportar_excel': request.form.get('exportar_excel')
        }
        
        # Debug: log dos dados capturados do formulário
        print(f"DEBUG DRE Sintético - Dados do form: data_inicio={dados_form['data_inicio']}, data_fim={dados_form['data_fim']}, exercicio={dados_form['exercicio']}")
        print(f"DEBUG DRE Sintético - Request form: {dict(request.form)}")
        print(f"DEBUG DRE Sintético - Request args: {dict(request.args)}")
        
        # Processar datas - SEMPRE usar dados do formulário primeiro
        if dados_form['exercicio'] and dados_form['exercicio'] != exercicio_default:
            try:
                # Usar a função dos utilitários para obter período completo
                data_inicio, data_fim = DataHora.obter_periodo_completo_mes(dados_form['exercicio'])
                
                # Atualizar dados_form
                dados_form['data_inicio'] = data_inicio.strftime('%Y-%m-%d')
                dados_form['data_fim'] = data_fim.strftime('%Y-%m-%d')
                
                # Debug: log das datas processadas do exercício
                print(f"DEBUG DRE Sintético - Exercício processado: {dados_form['exercicio']}, Data início: {data_inicio}, Data fim: {data_fim}")
                
            except ValueError as e:
                flash((str(e), 'error'))
                # Usar dados do formulário como fallback
                try:
                    data_inicio = datetime.strptime(dados_form['data_inicio'], '%Y-%m-%d').date()
                    data_fim = datetime.strptime(dados_form['data_fim'], '%Y-%m-%d').date()
                except ValueError:
                    data_inicio = data_inicio_default
                    data_fim = data_fim_default
                    dados_form['data_inicio'] = data_inicio.strftime('%Y-%m-%d')
                    dados_form['data_fim'] = data_fim.strftime('%Y-%m-%d')
                dados_form['exercicio'] = ''
        else:
            # Converter strings de data para objetos date - PRIORIZAR dados do form
            try:
                data_inicio = datetime.strptime(dados_form['data_inicio'], '%Y-%m-%d').date()
                data_fim = datetime.strptime(dados_form['data_fim'], '%Y-%m-%d').date()
                
                # Debug: log das datas processadas do range
                print(f"DEBUG DRE Sintético - Range manual processado: Data início: {data_inicio}, Data fim: {data_fim}")
                
            except ValueError:
                flash(('Datas inválidas fornecidas!', 'error'))
                data_inicio = data_inicio_default
                data_fim = data_fim_default
                dados_form['data_inicio'] = data_inicio.strftime('%Y-%m-%d')
                dados_form['data_fim'] = data_fim.strftime('%Y-%m-%d')
            
            # Verificar se as datas são válidas
            if data_inicio > data_fim:
                flash(('Data de início não pode ser maior que data de fim!', 'error'))
                data_inicio = data_inicio_default
                data_fim = data_fim_default
                dados_form['data_inicio'] = data_inicio.strftime('%Y-%m-%d')
                dados_form['data_fim'] = data_fim.strftime('%Y-%m-%d')
        
        # Gerar DRE sintético com as datas processadas
        print(f"DEBUG: Gerando DRE Sintético com data_inicio: {data_inicio}, data_fim: {data_fim}")
        dre_dados = DREModel.gerar_dre_sintetico(data_inicio, data_fim)
        
        if dados_form['exportar_pdf']:
            print(f"DEBUG: Exportando PDF DRE Sintético com data_inicio: {data_inicio}, data_fim: {data_fim}")
            return exportar_dre_sintetico_pdf(dre_dados, data_inicio, data_fim)
        
        # Log da consulta realizada (opcional)
        # ChangelogModel é usado para versionamento do sistema, não para logs de uso
        
        return render_template(
            'relatorios/relatorios_financeiros/relatorio_dfc_dre/dre/dre_sintetico.html',
            dre_dados=dre_dados,
            dados_form=dados_form,
            exercicios_disponiveis=DataHora.obter_exercicios_disponiveis_ano_atual(),
            formatar_float_para_brl=formatar_float_para_brl,
            formatar_data_para_brl=formatar_data_para_brl
        )
        
    except Exception as e:
        flash((f'Erro ao gerar DRE Sintético: {str(e)}', 'error'))
        return render_template(
            'relatorios/relatorios_financeiros/relatorio_dfc_dre/dre/dre_sintetico.html',
            dre_dados=None,
            dados_form={'data_inicio': data_inicio_default.strftime('%Y-%m-%d'), 'data_fim': data_fim_default.strftime('%Y-%m-%d')},
            exercicios_disponiveis=DataHora.obter_exercicios_disponiveis_ano_atual(),
            formatar_float_para_brl=formatar_float_para_brl,
            formatar_data_para_brl=formatar_data_para_brl
        )

def exportar_dre_pdf(dre_dados, data_inicio, data_fim):
    """
    Exporta DRE Analítico para PDF
    """
    try:
        # Debug: log das datas recebidas na função de exportação
        print(f"DEBUG: exportar_dre_pdf recebeu data_inicio: {data_inicio}, data_fim: {data_fim}")
        
        # Obter data atual como objeto datetime
        data_hoje = datetime.now()
        
        # Obter caminho do logo
        logo_path = obter_url_absoluta_de_imagem('logo.png')
        
        # Renderizar template para PDF
        html = render_template(
            'relatorios/relatorios_financeiros/relatorio_dfc_dre/dre/dre_analitico_pdf.html',
            logo_path=logo_path,
            dataHoje=data_hoje,
            dre_dados=dre_dados,
            data_inicio=data_inicio,
            data_fim=data_fim,
            formatar_float_para_brl=formatar_float_para_brl
        )
        
        # Nome do arquivo de saída
        nome_arquivo_saida = f'dre-analitico_{data_inicio.strftime("%Y%m%d")}_{data_fim.strftime("%Y%m%d")}'
        
        # Gerar PDF usando a função padrão do sistema
        return ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida)
        
    except Exception as e:
        flash((f'Erro ao exportar para PDF: {str(e)}', 'error'))
        return redirect(url_for('dre_analitico'))


def exportar_dre_sintetico_pdf(dre_dados, data_inicio, data_fim):
    """
    Exporta DRE Sintético para PDF
    """
    try:
        # Debug: log das datas recebidas na função de exportação
        print(f"DEBUG: exportar_dre_sintetico_pdf recebeu data_inicio: {data_inicio}, data_fim: {data_fim}")
        
        # Obter data atual como objeto datetime
        data_hoje = datetime.now()
        
        # Obter caminho do logo
        logo_path = obter_url_absoluta_de_imagem('logo.png')
        
        # Renderizar template para PDF
        html = render_template(
            'relatorios/relatorios_financeiros/relatorio_dfc_dre/dre/dre_sintetico_pdf.html',
            logo_path=logo_path,
            dataHoje=data_hoje,
            dre_dados=dre_dados,
            data_inicio=data_inicio,
            data_fim=data_fim,
            formatar_float_para_brl=formatar_float_para_brl
        )
        
        # Nome do arquivo de saída
        nome_arquivo_saida = f'dre-sintetico_{data_inicio.strftime("%Y%m%d")}_{data_fim.strftime("%Y%m%d")}'
        
        # Gerar PDF usando a função padrão do sistema
        return ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida)
        
    except Exception as e:
        flash((f'Erro ao exportar para PDF: {str(e)}', 'error'))
        return redirect(url_for('dre_sintetico'))

@app.route('/relatorios/relatorios-financeiros/dre-categoria-detalhes/<int:categoria_id>', methods=['GET'])
@login_required
@requires_roles
def dre_categoria_detalhes(categoria_id):
    """
    Rota AJAX para buscar detalhes dos registros de uma categoria específica
    Busca dados completos do faturamento e lançamentos avulsos
    """
    try:
        # Obter parâmetros da requisição
        data_inicio_str = request.args.get('data_inicio')
        data_fim_str = request.args.get('data_fim')
        
        if not data_inicio_str or not data_fim_str:
            return jsonify({'error': 'Datas são obrigatórias'}), 400
        
        # Converter datas
        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
        
        # Importar models necessários
        from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
        from sistema.models_views.financeiro.lancamento_avulso.lancamento_avulso_model import LancamentoAvulsoModel
        from sistema.models_views.gerenciar.pessoa_financeiro.pessoa_financeiro_model import PessoaFinanceiroModel
        
        # Buscar registros da categoria no período com joins para obter dados completos
        registros = db.session.query(AgendamentoPagamentoModel)\
            .outerjoin(FaturamentoModel, AgendamentoPagamentoModel.faturamento_id == FaturamentoModel.id)\
            .outerjoin(LancamentoAvulsoModel, AgendamentoPagamentoModel.lancamento_avulso_id == LancamentoAvulsoModel.id)\
            .outerjoin(PessoaFinanceiroModel, AgendamentoPagamentoModel.pessoa_financeiro_id == PessoaFinanceiroModel.id)\
            .filter(
                AgendamentoPagamentoModel.ativo == True,
                AgendamentoPagamentoModel.deletado == False,
                AgendamentoPagamentoModel.situacao_pagamento_id.in_([6, 8, 9]),
                AgendamentoPagamentoModel.data_competencia >= data_inicio,
                AgendamentoPagamentoModel.data_competencia <= data_fim
            ).all()
        
        # Filtrar registros que contêm a categoria específica
        registros_categoria = []
        
        for registro in registros:
            if registro.categorias_json:
                try:
                    categorias = json.loads(registro.categorias_json) if isinstance(registro.categorias_json, str) else registro.categorias_json
                    
                    if isinstance(categorias, list):
                        for categoria_info in categorias:
                            if isinstance(categoria_info, dict) and categoria_info.get('categoria_id') == categoria_id:
                                # Dividir por 100 pois valores estão multiplicados por 100 no banco
                                valor_corrigido = float(categoria_info.get('valor', 0)) / 100.0
                                
                                # Determinar a origem dos dados
                                origem = 'Sistema'
                                tipo_documento = 'Lançamento'
                                codigo_documento = f'AGD-{registro.id}'
                                beneficiario = 'Não informado'
                                observacoes = registro.descricao or ''
                                
                                # Se tem faturamento, buscar detalhes do faturamento
                                if registro.faturamento:
                                    faturamento = registro.faturamento
                                    tipo_documento = 'Faturamento'
                                    codigo_documento = faturamento.codigo_faturamento
                                    
                                    # Determinar tipo de operação
                                    if faturamento.tipo_operacao == 1:  # Carga
                                        origem = 'Faturamento de Carga'
                                    elif faturamento.tipo_operacao == 2:  # Lançamento
                                        if faturamento.direcao_financeira == 1:  # Receita
                                            origem = 'Receita Avulsa'
                                        else:  # Despesa
                                            origem = 'Despesa Avulsa'
                                    elif faturamento.tipo_operacao == 3:  # Crédito
                                        origem = 'Controle de Crédito'
                                    
                                    # Buscar detalhes do JSON do faturamento
                                    if faturamento.detalhes_json:
                                        try:
                                            detalhes = json.loads(faturamento.detalhes_json) if isinstance(faturamento.detalhes_json, str) else faturamento.detalhes_json
                                            if isinstance(detalhes, dict):
                                                # Construir descrição detalhada e explicativa
                                                informacoes_detalhes = []
                                                
                                                # Verificar se o agendamento tem múltiplas categorias
                                                categorias_agendamento = json.loads(registro.categorias_json) if isinstance(registro.categorias_json, str) else registro.categorias_json
                                                tem_multiplas_categorias = len(categorias_agendamento) > 1 if categorias_agendamento else False
                                                
                                                # Adicionar informação sobre categorização múltipla
                                                if tem_multiplas_categorias:
                                                    outras_categorias = [cat.get('categoria', 'N/A') for cat in categorias_agendamento if cat.get('categoria_id') != categoria_id]
                                                    if outras_categorias:
                                                        informacoes_detalhes.append(f"Faturamento rateado entre categorias: {', '.join(outras_categorias[:2])}")
                                                
                                                # ENTIDADES ENVOLVIDAS NO FATURAMENTO
                                                entidades_envolvidas = []
                                                
                                                # FORNECEDORES
                                                if 'fornecedores' in detalhes and detalhes['fornecedores']:
                                                    fornecedores = detalhes['fornecedores'][:3]  # Limitar a 3
                                                    nomes_fornecedores = []
                                                    for f in fornecedores:
                                                        # Buscar identificação em diferentes campos possíveis
                                                        nome = (f.get('fornecedor_identificacao') or 
                                                               f.get('identificacao') or 
                                                               f.get('nome') or 
                                                               f.get('razao_social') or
                                                               f.get('nome_fantasia'))
                                                        if nome and nome.strip():
                                                            nomes_fornecedores.append(nome.strip())
                                                    
                                                    if nomes_fornecedores:
                                                        entidades_envolvidas.append(f"Fornecedores: {', '.join(nomes_fornecedores)}")
                                                    elif len(fornecedores) > 0:
                                                        entidades_envolvidas.append(f"{len(fornecedores)} fornecedor(es) cadastrado(s)")
                                                
                                                # TRANSPORTADORAS
                                                if 'transportadoras' in detalhes and detalhes['transportadoras']:
                                                    transportadoras = detalhes['transportadoras'][:3]  # Limitar a 3
                                                    nomes_transportadoras = []
                                                    for t in transportadoras:
                                                        # Buscar identificação em diferentes campos possíveis
                                                        nome = (t.get('transportadora_identificacao') or 
                                                               t.get('fornecedor_identificacao') or
                                                               t.get('identificacao') or 
                                                               t.get('nome') or 
                                                               t.get('razao_social') or
                                                               t.get('nome_fantasia'))
                                                        if nome and nome.strip():
                                                            nomes_transportadoras.append(nome.strip())
                                                    
                                                    if nomes_transportadoras:
                                                        entidades_envolvidas.append(f"Transportadoras: {', '.join(nomes_transportadoras)}")
                                                    elif len(transportadoras) > 0:
                                                        entidades_envolvidas.append(f"{len(transportadoras)} transportadora(s) cadastrada(s)")
                                                
                                                # EXTRATORES
                                                if 'extratores' in detalhes and detalhes['extratores']:
                                                    extratores = detalhes['extratores'][:3]  # Limitar a 3
                                                    nomes_extratores = []
                                                    for e in extratores:
                                                        # Buscar identificação em diferentes campos possíveis
                                                        nome = (e.get('extrator_identificacao') or 
                                                               e.get('identificacao') or 
                                                               e.get('nome') or 
                                                               e.get('razao_social'))
                                                        if nome and nome.strip():
                                                            nomes_extratores.append(nome.strip())
                                                    
                                                    if nomes_extratores:
                                                        entidades_envolvidas.append(f"Extratores: {', '.join(nomes_extratores)}")
                                                    elif len(extratores) > 0:
                                                        entidades_envolvidas.append(f"{len(extratores)} extrator(es) cadastrado(s)")
                                                
                                                # COMISSIONADOS
                                                if 'comissionados' in detalhes and detalhes['comissionados']:
                                                    comissionados = detalhes['comissionados'][:3]  # Limitar a 3
                                                    nomes_comissionados = []
                                                    for c in comissionados:
                                                        # Buscar identificação em diferentes campos possíveis
                                                        nome = (c.get('comissionado_identificacao') or 
                                                               c.get('identificacao') or 
                                                               c.get('nome') or 
                                                               c.get('razao_social'))
                                                        if nome and nome.strip():
                                                            nomes_comissionados.append(nome.strip())
                                                    
                                                    if nomes_comissionados:
                                                        entidades_envolvidas.append(f"Comissionados: {', '.join(nomes_comissionados)}")
                                                    elif len(comissionados) > 0:
                                                        entidades_envolvidas.append(f"{len(comissionados)} comissionado(s) cadastrado(s)")
                                                
                                                # PRODUTOS/CARGAS
                                                if 'cargas_a_receber' in detalhes and detalhes['cargas_a_receber']:
                                                    cargas = detalhes['cargas_a_receber'][:3]  # Limitar a 3
                                                    nomes_produtos = []
                                                    for c in cargas:
                                                        # Buscar produto em diferentes campos possíveis
                                                        produto = (c.get('produto') or 
                                                                  c.get('nome_produto') or 
                                                                  c.get('descricao') or
                                                                  c.get('produto_nome'))
                                                        if produto and produto.strip():
                                                            nomes_produtos.append(produto.strip())
                                                    
                                                    if nomes_produtos:
                                                        entidades_envolvidas.append(f"Produtos: {', '.join(nomes_produtos)}")
                                                    elif len(cargas) > 0:
                                                        entidades_envolvidas.append(f"{len(cargas)} produto(s) cadastrado(s)")
                                                
                                                # CRÉDITOS UTILIZADOS (com explicação detalhada)
                                                creditos_utilizados = []
                                                if 'credito_fornecedor' in detalhes and detalhes['credito_fornecedor']:
                                                    creditos_fornecedor = detalhes['credito_fornecedor']
                                                    if len(creditos_fornecedor) == 1:
                                                        desc = creditos_fornecedor[0].get('credito_descricao', 'Crédito Fornecedor')
                                                        creditos_utilizados.append(f"Crédito Fornecedor: {desc}")
                                                    else:
                                                        descricoes = [c.get('credito_descricao', f'Crédito {i+1}') for i, c in enumerate(creditos_fornecedor[:2])]
                                                        outros = f" +{len(creditos_fornecedor)-2} outros" if len(creditos_fornecedor) > 2 else ""
                                                        creditos_utilizados.append(f"Créditos Fornecedor: {' | '.join(descricoes)}{outros}")
                                                
                                                if 'credito_transportadora' in detalhes and detalhes['credito_transportadora']:
                                                    creditos_transportadora = detalhes['credito_transportadora']
                                                    if len(creditos_transportadora) == 1:
                                                        desc = creditos_transportadora[0].get('credito_descricao', 'Crédito Transportadora')
                                                        creditos_utilizados.append(f"Crédito Transportadora: {desc}")
                                                    else:
                                                        descricoes = [c.get('credito_descricao', f'Crédito {i+1}') for i, c in enumerate(creditos_transportadora[:2])]
                                                        outros = f" +{len(creditos_transportadora)-2} outros" if len(creditos_transportadora) > 2 else ""
                                                        creditos_utilizados.append(f"Créditos Transportadora: {' | '.join(descricoes)}{outros}")
                                                
                                                if 'credito_extrator' in detalhes and detalhes['credito_extrator']:
                                                    creditos_extrator = detalhes['credito_extrator']
                                                    if len(creditos_extrator) == 1:
                                                        desc = creditos_extrator[0].get('credito_descricao', 'Crédito Extrator')
                                                        creditos_utilizados.append(f"Crédito Extrator: {desc}")
                                                    else:
                                                        descricoes = [c.get('credito_descricao', f'Crédito {i+1}') for i, c in enumerate(creditos_extrator[:2])]
                                                        outros = f" +{len(creditos_extrator)-2} outros" if len(creditos_extrator) > 2 else ""
                                                        creditos_utilizados.append(f"Créditos Extrator: {' | '.join(descricoes)}{outros}")
                                                
                                                # DOCUMENTOS FISCAIS
                                                documentos_fiscais = []
                                                if 'nf_complementar' in detalhes and detalhes['nf_complementar']:
                                                    qtd = len(detalhes['nf_complementar'])
                                                    documentos_fiscais.append(f"{qtd} NF Complementar(es)")
                                                if 'nf_servico' in detalhes and detalhes['nf_servico']:
                                                    qtd = len(detalhes['nf_servico'])
                                                    documentos_fiscais.append(f"{qtd} NF Serviço(s)")
                                                
                                                # Montar descrição final organizada por seções
                                                secoes_descricao = []
                                                
                                                if informacoes_detalhes:  # Info sobre categorização múltipla
                                                    secoes_descricao.extend(informacoes_detalhes)
                                                
                                                if entidades_envolvidas:
                                                    secoes_descricao.extend(entidades_envolvidas)
                                                
                                                if creditos_utilizados:
                                                    secoes_descricao.extend(creditos_utilizados)
                                                
                                                if documentos_fiscais:
                                                    secoes_descricao.extend(documentos_fiscais)
                                                
                                                # Juntar todas as seções
                                                if secoes_descricao:
                                                    observacoes = " • ".join(secoes_descricao)
                                        except (json.JSONDecodeError, TypeError, KeyError):
                                            pass
                                
                                # Se tem lançamento avulso, buscar detalhes
                                if registro.lancamento_avulso:
                                    lancamento = registro.lancamento_avulso
                                    tipo_documento = 'Lançamento Avulso'
                                    codigo_documento = f'LAN-{lancamento.id}'
                                    
                                    if lancamento.tipo_movimentacao == 1:  # Receita
                                        origem = 'Receita Avulsa'
                                    else:  # Despesa
                                        origem = 'Despesa Avulsa'
                                    
                                    observacoes = lancamento.descricao or ''
                                
                                # Buscar beneficiário
                                if registro.pessoa_financeiro:
                                    beneficiario = registro.pessoa_financeiro.identificacao
                                
                                registros_categoria.append({
                                    'id': registro.id,
                                    'data_competencia': registro.data_competencia.strftime('%d/%m/%Y'),
                                    'valor': valor_corrigido,
                                    'valor_formatado': ValoresMonetarios.converter_float_brl_positivo(valor_corrigido),
                                    'detalhamento': categoria_info.get('detalhamento', ''),
                                    'referencia': categoria_info.get('referencia', ''),
                                    'descricao': observacoes,
                                    'beneficiario': beneficiario,
                                    'origem': origem,
                                    'tipo_documento': tipo_documento,
                                    'codigo_documento': codigo_documento,
                                    'situacao_pagamento_id': registro.situacao_pagamento_id,
                                    # Campos adicionais para mais detalhes
                                    'data_vencimento': registro.data_vencimento.strftime('%d/%m/%Y') if registro.data_vencimento else None,
                                    'valor_total_original': registro.valor_total_100 / 100 if registro.valor_total_100 else 0,
                                    'faturamento_id': registro.faturamento_id,
                                    'lancamento_avulso_id': registro.lancamento_avulso_id
                                })
                except (json.JSONDecodeError, TypeError):
                    continue
        
        # Calcular total
        total = sum(reg['valor'] for reg in registros_categoria)
        
        return jsonify({
            'registros': registros_categoria,
            'total': total,
            'total_formatado': ValoresMonetarios.converter_float_brl_positivo(total),
            'quantidade': len(registros_categoria),
            'categoria_id': categoria_id
        })
        
    except Exception as e:
        print(f"Erro em dre_categoria_detalhes: {e}")
        return jsonify({'error': f'Erro ao buscar detalhes: {str(e)}'}), 500