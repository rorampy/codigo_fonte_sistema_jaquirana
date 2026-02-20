from datetime import datetime, date
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem, formatar_float_para_brl, formatar_data_para_brl
from sistema._utilitarios.data_e_hora import DataHora
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.financeiro.operacional.categorizar_fatura.categorizacao_model import AgendamentoPagamentoModel
from sistema.models_views.relatorios.relatorios_financeiros.relatorio_dfc_dre.relatorio_dre.dre_model import DREModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
from sistema._utilitarios import *
import json

@app.route('/relatorios/relatorios-financeiros/dre-analitico', methods=['GET', 'POST'])
@login_required
@requires_roles
def dre_analitico():
    """
    Rota para exibir DRE Analítico com filtros por período
    """
    try:
        data_fim_default = date.today()
        data_inicio_default = date(data_fim_default.year, data_fim_default.month, 1)
        exercicio_default = DataHora.obter_exercicio_mes_atual()
        
        dados_form = {
            'data_inicio': request.form.get('data_inicio') or request.args.get('data_inicio', data_inicio_default.strftime('%Y-%m-%d')),
            'data_fim': request.form.get('data_fim') or request.args.get('data_fim', data_fim_default.strftime('%Y-%m-%d')),
            'exercicio': request.form.get('exercicio') or request.args.get('exercicio', exercicio_default),
            'exportar_pdf': request.form.get('exportar_pdf'),
            'exportar_excel': request.form.get('exportar_excel')
        }
        
        if dados_form['exercicio'] and dados_form['exercicio'] != exercicio_default:
            try:
                data_inicio, data_fim = DataHora.obter_periodo_completo_mes(dados_form['exercicio'])
                
                dados_form['data_inicio'] = data_inicio.strftime('%Y-%m-%d')
                dados_form['data_fim'] = data_fim.strftime('%Y-%m-%d')
                
            except ValueError as e:
                flash((str(e), 'error'))
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
            try:
                data_inicio = datetime.strptime(dados_form['data_inicio'], '%Y-%m-%d').date()
                data_fim = datetime.strptime(dados_form['data_fim'], '%Y-%m-%d').date()
                
                
            except ValueError:
                flash(('Datas inválidas fornecidas!', 'error'))
                data_inicio = data_inicio_default
                data_fim = data_fim_default
                dados_form['data_inicio'] = data_inicio.strftime('%Y-%m-%d')
                dados_form['data_fim'] = data_fim.strftime('%Y-%m-%d')
            
            if data_inicio > data_fim:
                flash(('Data de início não pode ser maior que data de fim!', 'error'))
                data_inicio = data_inicio_default
                data_fim = data_fim_default
                dados_form['data_inicio'] = data_inicio.strftime('%Y-%m-%d')
                dados_form['data_fim'] = data_fim.strftime('%Y-%m-%d')
        
        dre_dados = DREModel.gerar_dre_analitico(data_inicio, data_fim)
        
        if dados_form['exportar_pdf']:
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
        data_fim_default = date.today()
        data_inicio_default = date(data_fim_default.year, data_fim_default.month, 1)
        exercicio_default = DataHora.obter_exercicio_mes_atual()
        
        dados_form = {
            'data_inicio': request.form.get('data_inicio') or request.args.get('data_inicio', data_inicio_default.strftime('%Y-%m-%d')),
            'data_fim': request.form.get('data_fim') or request.args.get('data_fim', data_fim_default.strftime('%Y-%m-%d')),
            'exercicio': request.form.get('exercicio') or request.args.get('exercicio', exercicio_default),
            'exportar_pdf': request.form.get('exportar_pdf'),
            'exportar_excel': request.form.get('exportar_excel')
        }
        
        
        if dados_form['exercicio'] and dados_form['exercicio'] != exercicio_default:
            try:
                data_inicio, data_fim = DataHora.obter_periodo_completo_mes(dados_form['exercicio'])
                
                dados_form['data_inicio'] = data_inicio.strftime('%Y-%m-%d')
                dados_form['data_fim'] = data_fim.strftime('%Y-%m-%d')
                
                
            except ValueError as e:
                flash((str(e), 'error'))
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
            try:
                data_inicio = datetime.strptime(dados_form['data_inicio'], '%Y-%m-%d').date()
                data_fim = datetime.strptime(dados_form['data_fim'], '%Y-%m-%d').date()
                
                
            except ValueError:
                flash(('Datas inválidas fornecidas!', 'error'))
                data_inicio = data_inicio_default
                data_fim = data_fim_default
                dados_form['data_inicio'] = data_inicio.strftime('%Y-%m-%d')
                dados_form['data_fim'] = data_fim.strftime('%Y-%m-%d')
            
            if data_inicio > data_fim:
                flash(('Data de início não pode ser maior que data de fim!', 'error'))
                data_inicio = data_inicio_default
                data_fim = data_fim_default
                dados_form['data_inicio'] = data_inicio.strftime('%Y-%m-%d')
                dados_form['data_fim'] = data_fim.strftime('%Y-%m-%d')
        
        dre_dados = DREModel.gerar_dre_sintetico(data_inicio, data_fim)
        
        if dados_form['exportar_pdf']:
            return exportar_dre_sintetico_pdf(dre_dados, data_inicio, data_fim)
        
        
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
        
        data_hoje = datetime.now()
        
        logo_path = obter_url_absoluta_de_imagem('logo.png')
        
        html = render_template(
            'relatorios/relatorios_financeiros/relatorio_dfc_dre/dre/dre_analitico_pdf.html',
            logo_path=logo_path,
            dataHoje=data_hoje,
            dre_dados=dre_dados,
            data_inicio=data_inicio,
            data_fim=data_fim,
            formatar_float_para_brl=formatar_float_para_brl
        )
        
        nome_arquivo_saida = f'dre-analitico_{data_inicio.strftime("%Y%m%d")}_{data_fim.strftime("%Y%m%d")}'
        
        return ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida)
        
    except Exception as e:
        flash((f'Erro ao exportar para PDF: {str(e)}', 'error'))
        return redirect(url_for('dre_analitico'))


def exportar_dre_sintetico_pdf(dre_dados, data_inicio, data_fim):
    """
    Exporta DRE Sintético para PDF
    """
    try:
        
        data_hoje = datetime.now()
        
        logo_path = obter_url_absoluta_de_imagem('logo.png')
        
        html = render_template(
            'relatorios/relatorios_financeiros/relatorio_dfc_dre/dre/dre_sintetico_pdf.html',
            logo_path=logo_path,
            dataHoje=data_hoje,
            dre_dados=dre_dados,
            data_inicio=data_inicio,
            data_fim=data_fim,
            formatar_float_para_brl=formatar_float_para_brl
        )
        
        nome_arquivo_saida = f'dre-sintetico_{data_inicio.strftime("%Y%m%d")}_{data_fim.strftime("%Y%m%d")}'
        
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
        data_inicio_str = request.args.get('data_inicio')
        data_fim_str = request.args.get('data_fim')
        
        if not data_inicio_str or not data_fim_str:
            return jsonify({'error': 'Datas são obrigatórias'}), 400
        
        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
        
        from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
        from sistema.models_views.financeiro.lancamento_avulso.lancamento_avulso_model import LancamentoAvulsoModel
        from sistema.models_views.gerenciar.pessoa_financeiro.pessoa_financeiro_model import PessoaFinanceiroModel
        from sistema.models_views.faturamento.cargas_a_faturar.fornecedor.fornecedor_a_pagar_model import FornecedorPagarModel
        from sistema.models_views.faturamento.cargas_a_faturar.transportadora.frete_a_pagar_model import FretePagarModel
        from sistema.models_views.faturamento.cargas_a_faturar.extrator.extrator_a_pagar_model import ExtratorPagarModel
        from sistema.models_views.faturamento.cargas_a_faturar.comissionado.comissionado_a_pagar_model import ComissionadoPagarModel
        from sistema.models_views.faturamento.cargas_a_receber.nf_complementar.nf_complementar_model import NfComplementarModel
        
        categoria = PlanoContaModel.query.filter_by(id=categoria_id, ativo=True, deletado=False).first()
        if not categoria:
            return jsonify({'error': 'Categoria não encontrada'}), 404
        
        registros = db.session.query(AgendamentoPagamentoModel)\
            .outerjoin(FaturamentoModel, AgendamentoPagamentoModel.faturamento_id == FaturamentoModel.id)\
            .outerjoin(LancamentoAvulsoModel, AgendamentoPagamentoModel.lancamento_avulso_id == LancamentoAvulsoModel.id)\
            .outerjoin(PessoaFinanceiroModel, AgendamentoPagamentoModel.pessoa_financeiro_id == PessoaFinanceiroModel.id)\
            .filter(
                AgendamentoPagamentoModel.ativo == True,
                AgendamentoPagamentoModel.deletado == False,
                AgendamentoPagamentoModel.situacao_pagamento_id.in_([6, 8, 9, 10]),
                AgendamentoPagamentoModel.data_competencia >= data_inicio,
                AgendamentoPagamentoModel.data_competencia <= data_fim
            ).all()
        
        registros_categoria = []
        
        for registro in registros:
            if registro.categorias_json:
                try:
                    categorias = json.loads(registro.categorias_json) if isinstance(registro.categorias_json, str) else registro.categorias_json
                    
                    if isinstance(categorias, list):
                        for categoria_info in categorias:
                            if isinstance(categoria_info, dict) and categoria_info.get('categoria_id') == categoria_id:
                                valor_corrigido = float(categoria_info.get('valor', 0)) / 100.0
                                
                                origem = 'Sistema'
                                tipo_documento = 'Lançamento'
                                codigo_documento = f'AGD-{registro.id}'
                                beneficiario = 'Não informado'
                                observacoes = registro.descricao or ''
                                
                                if registro.faturamento:
                                    faturamento = registro.faturamento
                                    tipo_documento = 'Faturamento'
                                    codigo_documento = faturamento.codigo_faturamento
                                    
                                    if faturamento.tipo_operacao == 1:
                                        origem = 'Faturamento de Carga'
                                    elif faturamento.tipo_operacao == 2:
                                        if faturamento.direcao_financeira == 1:
                                            origem = 'Receita Avulsa'
                                        else:
                                            origem = 'Despesa Avulsa'
                                    elif faturamento.tipo_operacao == 3:
                                        origem = 'Controle de Crédito'
                                    
                                    if faturamento.detalhes_json:
                                        try:
                                            detalhes = json.loads(faturamento.detalhes_json) if isinstance(faturamento.detalhes_json, str) else faturamento.detalhes_json
                                            if isinstance(detalhes, dict):
                                                informacoes_detalhes = []
                                                
                                                categorias_agendamento = json.loads(registro.categorias_json) if isinstance(registro.categorias_json, str) else registro.categorias_json
                                                tem_multiplas_categorias = len(categorias_agendamento) > 1 if categorias_agendamento else False
                                                
                                                if tem_multiplas_categorias:
                                                    outras_categorias = [cat.get('categoria', 'N/A') for cat in categorias_agendamento if cat.get('categoria_id') != categoria_id]
                                                    if outras_categorias:
                                                        informacoes_detalhes.append(f"Faturamento rateado entre categorias: {', '.join(outras_categorias[:2])}")
                                                
                                                entidades_envolvidas = []
                                                
                                                if 'fornecedores' in detalhes and detalhes['fornecedores']:
                                                    fornecedores = detalhes['fornecedores'][:3]
                                                    nomes_fornecedores = []
                                                    for f in fornecedores:
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
                                                
                                                if 'transportadoras' in detalhes and detalhes['transportadoras']:
                                                    transportadoras = detalhes['transportadoras'][:3]
                                                    nomes_transportadoras = []
                                                    for t in transportadoras:
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
                                                
                                                if 'extratores' in detalhes and detalhes['extratores']:
                                                    extratores = detalhes['extratores'][:3]
                                                    nomes_extratores = []
                                                    for e in extratores:
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
                                                
                                                if 'comissionados' in detalhes and detalhes['comissionados']:
                                                    comissionados = detalhes['comissionados'][:3]
                                                    nomes_comissionados = []
                                                    for c in comissionados:
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
                                                
                                                if 'cargas_a_receber' in detalhes and detalhes['cargas_a_receber']:
                                                    cargas = detalhes['cargas_a_receber'][:3]
                                                    nomes_produtos = []
                                                    for c in cargas:
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
                                                
                                                documentos_fiscais = []
                                                if 'nf_complementar' in detalhes and detalhes['nf_complementar']:
                                                    qtd = len(detalhes['nf_complementar'])
                                                    documentos_fiscais.append(f"{qtd} NF Complementar(es)")
                                                if 'nf_servico' in detalhes and detalhes['nf_servico']:
                                                    qtd = len(detalhes['nf_servico'])
                                                    documentos_fiscais.append(f"{qtd} NF Serviço(s)")
                                                
                                                secoes_descricao = []
                                                
                                                if informacoes_detalhes:
                                                    secoes_descricao.extend(informacoes_detalhes)
                                                
                                                if entidades_envolvidas:
                                                    secoes_descricao.extend(entidades_envolvidas)
                                                
                                                if creditos_utilizados:
                                                    secoes_descricao.extend(creditos_utilizados)
                                                
                                                if documentos_fiscais:
                                                    secoes_descricao.extend(documentos_fiscais)
                                                
                                                if secoes_descricao:
                                                    observacoes = " • ".join(secoes_descricao)
                                        except (json.JSONDecodeError, TypeError, KeyError):
                                            pass
                                
                                if registro.lancamento_avulso:
                                    lancamento = registro.lancamento_avulso
                                    tipo_documento = 'Lançamento Avulso'
                                    codigo_documento = f'LAN-{lancamento.id}'
                                    
                                    if lancamento.tipo_movimentacao == 1:
                                        origem = 'Receita Avulsa'
                                    else:
                                        origem = 'Despesa Avulsa'
                                    
                                    observacoes = lancamento.descricao or ''
                                
                                if registro.pessoa_financeiro:
                                    beneficiario = registro.pessoa_financeiro.identificacao
                                
                                if categoria.codigo == '1.01.01' and origem in ['Receita Avulsa', 'Faturamento de Carga']:
                                    continue
                                if categoria.codigo == '2.01.01' and origem in ['Despesa Avulsa', 'Faturamento de Carga']:
                                    continue
                                if categoria.codigo == '2.01.02' and origem in ['Despesa Avulsa', 'Faturamento de Carga']:
                                    continue
                                if categoria.codigo == '2.01.03' and origem in ['Despesa Avulsa', 'Faturamento de Carga']:
                                    continue
                                if categoria.codigo == '2.01.04' and origem in ['Despesa Avulsa', 'Faturamento de Carga']:
                                    continue
                                
                                valor_total_agd = registro.valor_total_100 or 0
                                total_categorizado = sum(c.get('valor', 0) for c in (categorias or []) if isinstance(c, dict))
                                categorizacao_incompleta = abs(valor_total_agd - total_categorizado) > 1
                                valor_nao_categorizado = (valor_total_agd - total_categorizado) / 100.0 if categorizacao_incompleta else 0
                                
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
                                    'data_vencimento': registro.data_vencimento.strftime('%d/%m/%Y') if registro.data_vencimento else None,
                                    'valor_total_original': registro.valor_total_100 / 100 if registro.valor_total_100 else 0,
                                    'faturamento_id': registro.faturamento_id,
                                    'lancamento_avulso_id': registro.lancamento_avulso_id,
                                    'categorizacao_incompleta': categorizacao_incompleta,
                                    'valor_nao_categorizado': valor_nao_categorizado
                                })
                except (json.JSONDecodeError, TypeError):
                    continue
        
        if categoria.codigo in ['2.01.01', '2.01.02', '2.01.03', '2.01.04', '1.01.01', '1.01.03']:
            mapeamento_a_pagar = {
                '2.01.01': {
                    'model': FornecedorPagarModel,
                    'tipo': 'Fornecedor',
                    'origem': 'Compra de Madeira',
                    'relacionamento': 'fornecedor'
                },
                '2.01.02': {
                    'model': FretePagarModel,
                    'tipo': 'Frete',
                    'origem': 'Transporte',
                    'relacionamento': 'fornecedor'
                },
                '2.01.03': {
                    'model': ExtratorPagarModel,
                    'tipo': 'Extrator',
                    'origem': 'Extração de Madeira',
                    'relacionamento': 'fornecedor'
                },
                '2.01.04': {
                    'model': ComissionadoPagarModel,
                    'tipo': 'Comissionado',
                    'origem': 'Comissão',
                    'relacionamento': 'fornecedor'
                },
                '1.01.01': {
                    'model': RegistroOperacionalModel,
                    'tipo': 'Venda',
                    'origem': 'Venda de Madeira',
                    'relacionamento': 'solicitacao'
                },
                '1.01.03': {
                    'model': NfComplementarModel,
                    'tipo': 'NF Complementar',
                    'origem': 'Venda NFe Complementar',
                    'relacionamento': 'cliente'
                }
            }
            
            config = mapeamento_a_pagar.get(categoria.codigo)
            if config:
                Model = config['model']
                
                if categoria.codigo == '1.01.03':
                    query_nfc = RegistroOperacionalModel.query.filter(
                        RegistroOperacionalModel.ativo == True,
                        RegistroOperacionalModel.deletado == False,
                        RegistroOperacionalModel.solicitacao_nf_id.isnot(None),
                        RegistroOperacionalModel.peso_ton_nf.isnot(None),
                        RegistroOperacionalModel.peso_liquido_ticket.isnot(None),
                        RegistroOperacionalModel.preco_un_nf > 0,
                        RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                        RegistroOperacionalModel.peso_liquido_ticket != RegistroOperacionalModel.peso_ton_nf
                    )
                    
                    if data_inicio:
                        query_nfc = query_nfc.filter(RegistroOperacionalModel.data_entrega_ticket >= data_inicio)
                    if data_fim:
                        query_nfc = query_nfc.filter(RegistroOperacionalModel.data_entrega_ticket <= data_fim)
                    
                    registros_nfc = query_nfc.all()
                    
                    for reg in registros_nfc:
                        diferenca = (reg.peso_liquido_ticket or 0) - (reg.peso_ton_nf or 0)
                        valor = round(diferenca * (reg.preco_un_nf or 0)) / 100.0
                        
                        beneficiario = 'Não informado'
                        if hasattr(reg, 'solicitacao') and reg.solicitacao and hasattr(reg.solicitacao, 'cliente') and reg.solicitacao.cliente:
                            beneficiario = reg.solicitacao.cliente.identificacao
                        elif reg.destinatario_nome:
                            beneficiario = reg.destinatario_nome
                        
                        numero_nf = reg.numero_nota_fiscal or ''
                        detalhes_obs = []
                        
                        detalhes_obs.append(f"Peso NF: {reg.peso_ton_nf} Ton")
                        detalhes_obs.append(f"Peso Ticket: {reg.peso_liquido_ticket} Ton")
                        sinal = '+' if diferenca > 0 else ''
                        detalhes_obs.append(f"Diferença: {sinal}{diferenca:.2f} Ton")
                        
                        if reg.preco_un_nf:
                            detalhes_obs.append(f"Preço: R$ {reg.preco_un_nf/100:.2f}")
                        
                        if reg.placa_ticket:
                            detalhes_obs.append(f"Placa: {reg.placa_ticket}")
                        
                        is_emitida = reg.status_emissao_nf_complementar_id == 1
                        if is_emitida:
                            detalhes_obs.append("NF Compl. Emitida")
                        
                        observacoes = ' • '.join(detalhes_obs)
                        
                        data_competencia = reg.data_entrega_ticket
                        
                        sinal_valor = 'positiva' if diferenca > 0 else 'negativa'
                        valor_fmt = f"+ {ValoresMonetarios.converter_float_brl_positivo(abs(valor))}" if valor >= 0 else f"- {ValoresMonetarios.converter_float_brl_positivo(abs(valor))}"
                        
                        tipo_label = 'Positiva' if diferenca > 0 else 'Negativa'
                        status_label = 'Emitida' if is_emitida else 'Não Emitida'
                        
                        registros_categoria.append({
                            'id': reg.id,
                            'data_competencia': data_competencia.strftime('%d/%m/%Y') if data_competencia else '-',
                            'valor': valor,
                            'valor_formatado': valor_fmt,
                            'detalhamento': f'NF Complementar {status_label} ({tipo_label})',
                            'referencia': numero_nf or f"REG-{reg.id}",
                            'descricao': observacoes,
                            'beneficiario': beneficiario,
                            'origem': f'NF Compl. {status_label} ({tipo_label})',
                            'tipo_documento': 'NF Complementar' if is_emitida else 'Pendente de Emissão',
                            'codigo_documento': f"NF-{numero_nf}" if numero_nf else f"REG-{reg.id}",
                            'situacao_pagamento_id': None,
                            'data_vencimento': None,
                            'valor_total_original': valor,
                            'faturamento_id': None,
                            'lancamento_avulso_id': None,
                            'origem_automatica': True,
                            'nao_emitida': not is_emitida,
                            'tipo_nf_complementar': sinal_valor
                        })
                else:
                    query_a_pagar = Model.query.filter(
                        Model.ativo == True,
                        Model.deletado == False,
                        Model.data_entrega_ticket.isnot(None)
                    )
                
                    if categoria.codigo in ['2.01.01', '2.01.02', '2.01.03', '2.01.04']:
                        query_a_pagar = query_a_pagar.filter(
                            Model.solicitacao_id.isnot(None),
                            Model.valor_total_a_pagar_100 > 0
                        )
                    elif categoria.codigo == '1.01.01':
                        query_a_pagar = query_a_pagar.filter(Model.solicitacao_nf_id.isnot(None))
                    
                    if data_inicio:
                        query_a_pagar = query_a_pagar.filter(Model.data_entrega_ticket >= data_inicio)
                    if data_fim:
                        query_a_pagar = query_a_pagar.filter(Model.data_entrega_ticket <= data_fim)
                    
                    registros_a_pagar = query_a_pagar.all()
                    
                    _mapa_fornecedor_extrator = {}
                    if categoria.codigo == '2.01.03':
                        from sistema.models_views.gerenciar.fornecedor.fornecedor_preco_custo_extracao_model import FornecedorPrecoCustoExtracaoModel
                        fornecedor_ids_ext = list(set(r.fornecedor_id for r in registros_a_pagar if r.fornecedor_id))
                        if fornecedor_ids_ext:
                            configs_ext = FornecedorPrecoCustoExtracaoModel.query.filter(
                                FornecedorPrecoCustoExtracaoModel.fornecedor_id.in_(fornecedor_ids_ext),
                                FornecedorPrecoCustoExtracaoModel.ativo == True,
                                FornecedorPrecoCustoExtracaoModel.deletado == False,
                                FornecedorPrecoCustoExtracaoModel.extrator_id.isnot(None)
                            ).all()
                            for cfg in configs_ext:
                                if cfg.fornecedor_id not in _mapa_fornecedor_extrator and cfg.extrator:
                                    _mapa_fornecedor_extrator[cfg.fornecedor_id] = cfg.extrator.identificacao
                    
                    for registro in registros_a_pagar:
                        if categoria.codigo == '1.01.01':
                            valor = (registro.valor_total_nota_100 or 0) / 100.0
                            
                            beneficiario = registro.destinatario_nome or 'Não informado'
                            
                            observacoes = ''
                            numero_nf = registro.numero_nota_fiscal or ''
                            if hasattr(registro, 'solicitacao') and registro.solicitacao:
                                solicitacao = registro.solicitacao
                                detalhes_obs = []
                                
                                if hasattr(solicitacao, 'produto') and solicitacao.produto:
                                    detalhes_obs.append(f"Produto: {solicitacao.produto.nome}")
                                
                                if hasattr(solicitacao, 'bitola') and solicitacao.bitola:
                                    detalhes_obs.append(f"Bitola: {solicitacao.bitola.bitola}")
                                
                                if hasattr(solicitacao, 'cliente') and solicitacao.cliente:
                                    beneficiario = solicitacao.cliente.identificacao
                                
                                if hasattr(solicitacao, 'motorista') and solicitacao.motorista:
                                    detalhes_obs.append(f"Motorista: {solicitacao.motorista.nome_completo}")
                                
                                if hasattr(solicitacao, 'veiculo') and solicitacao.veiculo:
                                    detalhes_obs.append(f"Veículo: {solicitacao.veiculo.placa_veiculo}")
                                
                                observacoes = ' • '.join(detalhes_obs)
                            
                            registros_categoria.append({
                                'id': registro.id,
                                'data_competencia': registro.data_entrega_ticket.strftime('%d/%m/%Y'),
                                'valor': valor,
                                'valor_formatado': ValoresMonetarios.converter_float_brl_positivo(valor),
                                'detalhamento': config['tipo'],
                                'referencia': numero_nf or f"{config['tipo']}-{registro.id}",
                                'descricao': observacoes,
                                'beneficiario': beneficiario,
                                'origem': config['origem'],
                                'tipo_documento': 'Nota Fiscal',
                                'codigo_documento': f"NF-{numero_nf}" if numero_nf else f"REG-{registro.id}",
                                'situacao_pagamento_id': registro.situacao_financeira_id if hasattr(registro, 'situacao_financeira_id') else None,
                                'data_vencimento': None,
                                'valor_total_original': valor,
                                'faturamento_id': None,
                                'lancamento_avulso_id': None,
                                'origem_automatica': True
                            })
                        elif categoria.codigo in ['2.01.01', '2.01.02', '2.01.03', '2.01.04']:
                            valor = (registro.valor_total_a_pagar_100 or 0) / 100.0
                            
                            beneficiario = 'Não informado'
                            if categoria.codigo == '2.01.02' and hasattr(registro, 'transportadora') and registro.transportadora:
                                beneficiario = registro.transportadora.identificacao
                            elif categoria.codigo == '2.01.03':
                                if hasattr(registro, 'extrator') and registro.extrator:
                                    beneficiario = registro.extrator.identificacao
                                elif registro.fornecedor_id and registro.fornecedor_id in _mapa_fornecedor_extrator:
                                    beneficiario = _mapa_fornecedor_extrator[registro.fornecedor_id]
                            elif categoria.codigo == '2.01.04' and hasattr(registro, 'comissionado') and registro.comissionado:
                                beneficiario = registro.comissionado.identificacao
                            elif hasattr(registro, 'fornecedor') and registro.fornecedor:
                                beneficiario = registro.fornecedor.identificacao if hasattr(registro.fornecedor, 'identificacao') else str(registro.fornecedor)
                            
                            observacoes = ''
                            numero_nf = ''
                            detalhes_obs = []
                            
                            if hasattr(registro, 'solicitacao') and registro.solicitacao:
                                solicitacao = registro.solicitacao
                                
                                if hasattr(solicitacao, 'produto') and solicitacao.produto:
                                    detalhes_obs.append(f"Produto: {solicitacao.produto.nome}")
                                
                                if hasattr(solicitacao, 'bitola') and solicitacao.bitola:
                                    detalhes_obs.append(f"Bitola: {solicitacao.bitola.bitola}")
                                
                                if hasattr(solicitacao, 'cliente') and solicitacao.cliente:
                                    detalhes_obs.append(f"Cliente: {solicitacao.cliente.identificacao}")
                                
                                if hasattr(solicitacao, 'motorista') and solicitacao.motorista:
                                    detalhes_obs.append(f"Motorista: {solicitacao.motorista.nome_completo}")
                                
                                if hasattr(solicitacao, 'veiculo') and solicitacao.veiculo:
                                    detalhes_obs.append(f"Veículo: {solicitacao.veiculo.placa_veiculo}")
                            
                            if hasattr(registro, 'numero_nota_fiscal'):
                                numero_nf = registro.numero_nota_fiscal or ''
                            
                            observacoes = ' • '.join(detalhes_obs)
                            
                            registros_categoria.append({
                                'id': registro.id,
                                'data_competencia': registro.data_entrega_ticket.strftime('%d/%m/%Y') if registro.data_entrega_ticket else '-',
                                'valor': valor,
                                'valor_formatado': ValoresMonetarios.converter_float_brl_positivo(valor),
                                'detalhamento': config['tipo'],
                                'referencia': numero_nf or f"{config['tipo']}-{registro.id}",
                                'descricao': observacoes,
                                'beneficiario': beneficiario,
                                'origem': config['origem'],
                                'tipo_documento': config['tipo'],
                                'codigo_documento': f"NF-{numero_nf}" if numero_nf else f"REG-{registro.id}",
                                'situacao_pagamento_id': registro.situacao_financeira_id if hasattr(registro, 'situacao_financeira_id') else None,
                                'data_vencimento': None,
                                'valor_total_original': valor,
                                'faturamento_id': None,
                                'lancamento_avulso_id': None,
                                'origem_automatica': True
                            })

        
        registros_categoria.sort(key=lambda r: (r.get('beneficiario') or '').lower())
        
        total = sum(reg['valor'] for reg in registros_categoria)
        
        categorias_automaticas = ['1.01.01', '1.01.03', '2.01.01', '2.01.02', '2.01.03', '2.01.04']
        
        subtotais_nfc = None
        if categoria.codigo == '1.01.03':
            total_positivas = sum(r['valor'] for r in registros_categoria if r.get('tipo_nf_complementar') == 'positiva')
            total_negativas = sum(r['valor'] for r in registros_categoria if r.get('tipo_nf_complementar') == 'negativa')
            qtd_positivas = sum(1 for r in registros_categoria if r.get('tipo_nf_complementar') == 'positiva')
            qtd_negativas = sum(1 for r in registros_categoria if r.get('tipo_nf_complementar') == 'negativa')
            sinal_total = '+' if total >= 0 else '-'
            subtotais_nfc = {
                'total_positivas': total_positivas,
                'total_positivas_fmt': f"+ {ValoresMonetarios.converter_float_brl_positivo(total_positivas)}",
                'qtd_positivas': qtd_positivas,
                'total_negativas': total_negativas,
                'total_negativas_fmt': f"- {ValoresMonetarios.converter_float_brl_positivo(abs(total_negativas))}",
                'qtd_negativas': qtd_negativas,
                'total_liquido': total,
                'total_liquido_fmt': f"{sinal_total} {ValoresMonetarios.converter_float_brl_positivo(abs(total))}",
            }
        
        registros_incompletos = [r for r in registros_categoria if r.get('categorizacao_incompleta')]
        total_nao_categorizado = sum(r.get('valor_nao_categorizado', 0) for r in registros_incompletos)
        
        resposta = {
            'registros': registros_categoria,
            'total': total,
            'total_formatado': ValoresMonetarios.converter_float_brl_positivo(abs(total)) if categoria.codigo == '1.01.03' else ValoresMonetarios.converter_float_brl_positivo(total),
            'quantidade': len(registros_categoria),
            'categoria_id': categoria_id,
            'categoria_codigo': categoria.codigo,
            'permite_exportacao': categoria.codigo in categorias_automaticas,
            'categorizacao_incompleta': {
                'tem_incompletos': len(registros_incompletos) > 0,
                'quantidade': len(registros_incompletos),
                'total_nao_categorizado': total_nao_categorizado,
                'total_nao_categorizado_fmt': ValoresMonetarios.converter_float_brl_positivo(total_nao_categorizado)
            } if registros_incompletos else None
        }
        
        if subtotais_nfc:
            resposta['subtotais_nfc'] = subtotais_nfc
        
        return jsonify(resposta)
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar detalhes: {str(e)}'}), 500


def _buscar_detalhes_categoria_para_exportacao(categoria_id, data_inicio_str, data_fim_str):
    """
    Função auxiliar que busca detalhes de uma categoria para exportação PDF/Excel.
    Retorna tuple: (categoria, registros, total, data_inicio, data_fim, erro)
    """
    try:
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        
        from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
        from sistema.models_views.financeiro.lancamento_avulso.lancamento_avulso_model import LancamentoAvulsoModel
        from sistema.models_views.gerenciar.pessoa_financeiro.pessoa_financeiro_model import PessoaFinanceiroModel
        from sistema.models_views.faturamento.cargas_a_faturar.fornecedor.fornecedor_a_pagar_model import FornecedorPagarModel
        from sistema.models_views.faturamento.cargas_a_faturar.transportadora.frete_a_pagar_model import FretePagarModel
        from sistema.models_views.faturamento.cargas_a_faturar.extrator.extrator_a_pagar_model import ExtratorPagarModel
        from sistema.models_views.faturamento.cargas_a_faturar.comissionado.comissionado_a_pagar_model import ComissionadoPagarModel
        from sistema.models_views.faturamento.cargas_a_receber.nf_complementar.nf_complementar_model import NfComplementarModel
        
        categoria = PlanoContaModel.query.filter_by(id=categoria_id, ativo=True, deletado=False).first()
        if not categoria:
            return None, [], 0, data_inicio, data_fim, 'Categoria não encontrada'
        
        registros_categoria = []
        
        mapeamento_a_pagar = {
            '2.01.01': {'model': FornecedorPagarModel, 'tipo': 'Fornecedor', 'origem': 'Compra de Madeira'},
            '2.01.02': {'model': FretePagarModel, 'tipo': 'Frete', 'origem': 'Transporte'},
            '2.01.03': {'model': ExtratorPagarModel, 'tipo': 'Extrator', 'origem': 'Extração de Madeira'},
            '2.01.04': {'model': ComissionadoPagarModel, 'tipo': 'Comissionado', 'origem': 'Comissão'},
            '1.01.01': {'model': RegistroOperacionalModel, 'tipo': 'Venda', 'origem': 'Venda de Madeira'},
            '1.01.03': {'model': NfComplementarModel, 'tipo': 'NF Complementar', 'origem': 'Venda NFe Complementar'}
        }
        
        if categoria.codigo in mapeamento_a_pagar:
            config = mapeamento_a_pagar.get(categoria.codigo)
            Model = config['model']
            
            if categoria.codigo == '1.01.03':
                query_nfc = RegistroOperacionalModel.query.filter(
                    RegistroOperacionalModel.ativo == True,
                    RegistroOperacionalModel.deletado == False,
                    RegistroOperacionalModel.solicitacao_nf_id.isnot(None),
                    RegistroOperacionalModel.peso_ton_nf.isnot(None),
                    RegistroOperacionalModel.peso_liquido_ticket.isnot(None),
                    RegistroOperacionalModel.preco_un_nf > 0,
                    RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                    RegistroOperacionalModel.peso_liquido_ticket != RegistroOperacionalModel.peso_ton_nf,
                    RegistroOperacionalModel.data_entrega_ticket >= data_inicio,
                    RegistroOperacionalModel.data_entrega_ticket <= data_fim
                ).all()
                
                for reg in query_nfc:
                    diferenca = (reg.peso_liquido_ticket or 0) - (reg.peso_ton_nf or 0)
                    valor = round(diferenca * (reg.preco_un_nf or 0)) / 100.0
                    
                    tipo_nfc = 'positiva' if diferenca > 0 else 'negativa'
                    sinal_valor = '+' if valor >= 0 else '-'
                    valor_fmt = f"{sinal_valor} {ValoresMonetarios.converter_float_brl_positivo(abs(valor))}"
                    tipo_label = 'Positiva' if diferenca > 0 else 'Negativa'
                    
                    beneficiario = 'Não informado'
                    if hasattr(reg, 'solicitacao') and reg.solicitacao and hasattr(reg.solicitacao, 'cliente') and reg.solicitacao.cliente:
                        beneficiario = reg.solicitacao.cliente.identificacao
                    elif reg.destinatario_nome:
                        beneficiario = reg.destinatario_nome
                    
                    numero_nf = reg.numero_nota_fiscal or ''
                    sinal = '+' if diferenca > 0 else ''
                    is_emitida = reg.status_emissao_nf_complementar_id == 1
                    status_label = 'Emitida' if is_emitida else 'Não Emitida'
                    detalhes_obs = [
                        f"Peso NF: {reg.peso_ton_nf} Ton",
                        f"Peso Ticket: {reg.peso_liquido_ticket} Ton",
                        f"Diferença: {sinal}{diferenca:.2f} Ton"
                    ]
                    if reg.preco_un_nf:
                        detalhes_obs.append(f"Preço: R$ {reg.preco_un_nf/100:.2f}")
                    if reg.placa_ticket:
                        detalhes_obs.append(f"Placa: {reg.placa_ticket}")
                    if is_emitida:
                        detalhes_obs.append("NF Compl. Emitida")
                    
                    registros_categoria.append({
                        'id': reg.id,
                        'data_competencia': reg.data_entrega_ticket.strftime('%d/%m/%Y') if reg.data_entrega_ticket else '-',
                        'valor': valor,
                        'valor_formatado': valor_fmt,
                        'tipo_nf_complementar': tipo_nfc,
                        'referencia': numero_nf or f"REG-{reg.id}",
                        'descricao': ' • '.join(detalhes_obs),
                        'beneficiario': beneficiario,
                        'origem': f'NF Compl. {status_label} ({tipo_label})',
                        'tipo_documento': 'NF Complementar' if is_emitida else 'Pendente de Emissão',
                        'codigo_documento': f"NF-{numero_nf}" if numero_nf else f"REG-{reg.id}"
                    })
            else:
                query_a_pagar = Model.query.filter(
                    Model.ativo == True,
                    Model.deletado == False,
                    Model.data_entrega_ticket.isnot(None)
                )
                
                if categoria.codigo in ['2.01.01', '2.01.02', '2.01.03', '2.01.04']:
                    query_a_pagar = query_a_pagar.filter(
                        Model.solicitacao_id.isnot(None),
                        Model.valor_total_a_pagar_100 > 0
                    )
                elif categoria.codigo == '1.01.01':
                    query_a_pagar = query_a_pagar.filter(Model.solicitacao_nf_id.isnot(None))
                
                query_a_pagar = query_a_pagar.filter(
                    Model.data_entrega_ticket >= data_inicio,
                    Model.data_entrega_ticket <= data_fim
                )
                
                registros_a_pagar = query_a_pagar.all()
                
                _mapa_fornecedor_extrator_exp = {}
                if categoria.codigo == '2.01.03':
                    from sistema.models_views.gerenciar.fornecedor.fornecedor_preco_custo_extracao_model import FornecedorPrecoCustoExtracaoModel
                    fornecedor_ids_ext = list(set(r.fornecedor_id for r in registros_a_pagar if r.fornecedor_id))
                    if fornecedor_ids_ext:
                        configs_ext = FornecedorPrecoCustoExtracaoModel.query.filter(
                            FornecedorPrecoCustoExtracaoModel.fornecedor_id.in_(fornecedor_ids_ext),
                            FornecedorPrecoCustoExtracaoModel.ativo == True,
                            FornecedorPrecoCustoExtracaoModel.deletado == False,
                            FornecedorPrecoCustoExtracaoModel.extrator_id.isnot(None)
                        ).all()
                        for cfg in configs_ext:
                            if cfg.fornecedor_id not in _mapa_fornecedor_extrator_exp and cfg.extrator:
                                _mapa_fornecedor_extrator_exp[cfg.fornecedor_id] = cfg.extrator.identificacao
                
                for registro in registros_a_pagar:
                    if categoria.codigo == '1.01.01':
                        valor = (registro.valor_total_nota_100 or 0) / 100.0
                        beneficiario = registro.destinatario_nome or 'Não informado'
                        numero_nf = registro.numero_nota_fiscal or ''
                        observacoes = ''
                        
                        if hasattr(registro, 'solicitacao') and registro.solicitacao:
                            solicitacao = registro.solicitacao
                            detalhes_obs = []
                            if hasattr(solicitacao, 'produto') and solicitacao.produto:
                                detalhes_obs.append(f"Produto: {solicitacao.produto.nome}")
                            if hasattr(solicitacao, 'bitola') and solicitacao.bitola:
                                detalhes_obs.append(f"Bitola: {solicitacao.bitola.bitola}")
                            if hasattr(solicitacao, 'cliente') and solicitacao.cliente:
                                beneficiario = solicitacao.cliente.identificacao
                            observacoes = ' • '.join(detalhes_obs)
                        
                        registros_categoria.append({
                            'id': registro.id,
                            'data_competencia': registro.data_entrega_ticket.strftime('%d/%m/%Y'),
                            'valor': valor,
                            'valor_formatado': ValoresMonetarios.converter_float_brl_positivo(valor),
                            'referencia': numero_nf or f"{config['tipo']}-{registro.id}",
                            'descricao': observacoes,
                            'beneficiario': beneficiario,
                            'origem': config['origem'],
                            'tipo_documento': 'Nota Fiscal',
                            'codigo_documento': f"NF-{numero_nf}" if numero_nf else f"REG-{registro.id}"
                        })
                    else:
                        valor = (registro.valor_total_a_pagar_100 or 0) / 100.0
                        beneficiario = 'Não informado'
                        
                        if categoria.codigo == '2.01.02' and hasattr(registro, 'transportadora') and registro.transportadora:
                            beneficiario = registro.transportadora.identificacao
                        elif categoria.codigo == '2.01.03':
                            if hasattr(registro, 'extrator') and registro.extrator:
                                beneficiario = registro.extrator.identificacao
                            elif registro.fornecedor_id and registro.fornecedor_id in _mapa_fornecedor_extrator_exp:
                                beneficiario = _mapa_fornecedor_extrator_exp[registro.fornecedor_id]
                        elif categoria.codigo == '2.01.04' and hasattr(registro, 'comissionado') and registro.comissionado:
                            beneficiario = registro.comissionado.identificacao
                        elif hasattr(registro, 'fornecedor') and registro.fornecedor:
                            beneficiario = registro.fornecedor.identificacao
                        
                        observacoes = ''
                        numero_ticket = ''
                        if hasattr(registro, 'solicitacao') and registro.solicitacao:
                            solicitacao = registro.solicitacao
                            detalhes_obs = []
                            if hasattr(solicitacao, 'produto') and solicitacao.produto:
                                detalhes_obs.append(f"Produto: {solicitacao.produto.nome}")
                            if hasattr(registro, 'bitola') and registro.bitola:
                                detalhes_obs.append(f"Bitola: {registro.bitola.bitola}")
                            if hasattr(solicitacao, 'numero_ticket') and solicitacao.numero_ticket:
                                numero_ticket = solicitacao.numero_ticket
                            observacoes = ' • '.join(detalhes_obs)
                        
                        registros_categoria.append({
                            'id': registro.id,
                            'data_competencia': registro.data_entrega_ticket.strftime('%d/%m/%Y'),
                            'valor': valor,
                            'valor_formatado': ValoresMonetarios.converter_float_brl_positivo(valor),
                            'referencia': numero_ticket or f"{config['tipo']}-{registro.id}",
                            'descricao': observacoes,
                            'beneficiario': beneficiario,
                            'origem': config['origem'],
                            'tipo_documento': f'{config["tipo"]} a Pagar',
                            'codigo_documento': f"{config['tipo'].upper()[:3]}-{registro.id}"
                        })
        
        if categoria.codigo not in mapeamento_a_pagar:
            agendamentos = AgendamentoPagamentoModel.query.filter(
                AgendamentoPagamentoModel.ativo == True,
                AgendamentoPagamentoModel.deletado == False,
                AgendamentoPagamentoModel.situacao_pagamento_id.in_([6, 8, 9, 10]),
                AgendamentoPagamentoModel.data_competencia >= data_inicio,
                AgendamentoPagamentoModel.data_competencia <= data_fim
            ).all()
            
            for agendamento in agendamentos:
                if not agendamento.categorias_json:
                    continue
                
                try:
                    categorias_agd = json.loads(agendamento.categorias_json) if isinstance(agendamento.categorias_json, str) else agendamento.categorias_json
                    
                    if not isinstance(categorias_agd, list):
                        continue
                    
                    for cat_info in categorias_agd:
                        if not isinstance(cat_info, dict) or cat_info.get('categoria_id') != categoria_id:
                            continue
                        
                        valor = float(cat_info.get('valor', 0)) / 100.0
                        
                        origem = 'Sistema'
                        beneficiario = 'Não informado'
                        observacoes = agendamento.descricao or ''
                        codigo_documento = f'AGD-{agendamento.id}'
                        
                        if agendamento.lancamento_avulso:
                            lancamento = agendamento.lancamento_avulso
                            origem = 'Receita Avulsa' if lancamento.tipo_movimentacao == 1 else 'Despesa Avulsa'
                            codigo_documento = f'LAN-{lancamento.id}'
                            observacoes = lancamento.descricao or ''
                        elif agendamento.faturamento:
                            faturamento = agendamento.faturamento
                            codigo_documento = faturamento.codigo_faturamento
                            if faturamento.tipo_operacao == 1:
                                origem = 'Faturamento de Carga'
                            elif faturamento.tipo_operacao == 2:
                                origem = 'Receita Avulsa' if faturamento.direcao_financeira == 1 else 'Despesa Avulsa'
                            elif faturamento.tipo_operacao == 3:
                                origem = 'Controle de Crédito'
                        
                        if agendamento.pessoa_financeiro:
                            beneficiario = agendamento.pessoa_financeiro.identificacao
                        
                        registros_categoria.append({
                            'id': agendamento.id,
                            'data_competencia': agendamento.data_competencia.strftime('%d/%m/%Y'),
                            'valor': valor,
                            'valor_formatado': ValoresMonetarios.converter_float_brl_positivo(valor),
                            'referencia': cat_info.get('referencia', codigo_documento),
                            'descricao': observacoes,
                            'beneficiario': beneficiario,
                            'origem': origem,
                            'tipo_documento': 'Agendamento',
                            'codigo_documento': codigo_documento
                        })
                except (json.JSONDecodeError, TypeError):
                    continue
        
        registros_categoria.sort(key=lambda r: (r.get('beneficiario') or '').lower())
        
        total = sum(reg['valor'] for reg in registros_categoria)
        return categoria, registros_categoria, total, data_inicio, data_fim, None
        
    except Exception as e:
        return None, [], 0, None, None, str(e)


@app.route('/relatorios/relatorios-financeiros/dre-categoria-detalhes/<int:categoria_id>/excel', methods=['GET'])
@login_required
@requires_roles
def dre_categoria_detalhes_excel(categoria_id):
    """
    Exporta os detalhes de uma categoria DRE para Excel
    """
    try:
        data_inicio_str = request.args.get('data_inicio')
        data_fim_str = request.args.get('data_fim')
        
        if not data_inicio_str or not data_fim_str:
            flash(('Datas são obrigatórias para exportação.', 'error'))
            return redirect(url_for('dre_analitico'))
        
        categoria, registros, total, data_inicio, data_fim, erro = _buscar_detalhes_categoria_para_exportacao(
            categoria_id, data_inicio_str, data_fim_str
        )
        
        if erro:
            flash((f'Erro ao exportar: {erro}', 'error'))
            return redirect(url_for('dre_analitico'))
        
        if not registros:
            flash(('Nenhum registro encontrado para exportação.', 'warning'))
            return redirect(url_for('dre_analitico'))
        
        is_nfc = categoria.codigo == '1.01.03'
        dados_excel = []
        for reg in registros:
            linha = {
                'Data': reg['data_competencia'],
                'Documento': reg['codigo_documento'],
                'Origem': reg['origem'],
                'Beneficiário': reg['beneficiario'],
                'Descrição': reg['descricao'].replace(' • ', ' | ') if reg['descricao'] else '',
                'Referência': reg['referencia'],
                'Valor (R$)': reg['valor']
            }
            if is_nfc:
                tipo = reg.get('tipo_nf_complementar', '')
                linha['Tipo'] = 'POSITIVA' if tipo == 'positiva' else ('NEGATIVA' if tipo == 'negativa' else '')
                linha_ordenada = {
                    'Data': linha['Data'],
                    'Documento': linha['Documento'],
                    'Origem': linha['Origem'],
                    'Beneficiário': linha['Beneficiário'],
                    'Descrição': linha['Descrição'],
                    'Referência': linha['Referência'],
                    'Tipo': linha['Tipo'],
                    'Valor (R$)': linha['Valor (R$)']
                }
                dados_excel.append(linha_ordenada)
            else:
                dados_excel.append(linha)
        
        if is_nfc:
            total_positivas = sum(r['valor'] for r in registros if r.get('tipo_nf_complementar') == 'positiva')
            total_negativas = sum(r['valor'] for r in registros if r.get('tipo_nf_complementar') == 'negativa')
            qtd_pos = sum(1 for r in registros if r.get('tipo_nf_complementar') == 'positiva')
            qtd_neg = sum(1 for r in registros if r.get('tipo_nf_complementar') == 'negativa')
            
            dados_excel.append({k: '' for k in dados_excel[0].keys()})
            
            linha_pos = {k: '' for k in dados_excel[0].keys()}
            linha_pos['Referência'] = f'SUBTOTAL POSITIVAS ({qtd_pos} registros)'
            linha_pos['Tipo'] = 'POSITIVA'
            linha_pos['Valor (R$)'] = total_positivas
            dados_excel.append(linha_pos)
            
            linha_neg = {k: '' for k in dados_excel[0].keys()}
            linha_neg['Referência'] = f'SUBTOTAL NEGATIVAS ({qtd_neg} registros)'
            linha_neg['Tipo'] = 'NEGATIVA'
            linha_neg['Valor (R$)'] = total_negativas
            dados_excel.append(linha_neg)
            
            linha_liq = {k: '' for k in dados_excel[0].keys()}
            linha_liq['Referência'] = f'TOTAL LÍQUIDO ({len(registros)} registros)'
            linha_liq['Valor (R$)'] = total
            dados_excel.append(linha_liq)
        else:
            dados_excel.append({
                'Data': '',
                'Documento': '',
                'Origem': '',
                'Beneficiário': '',
                'Descrição': '',
                'Referência': 'TOTAL',
                'Valor (R$)': total
            })
        
        nome_arquivo = f"DRE_Detalhes_{categoria.nome.replace(' ', '_')}_{data_inicio.strftime('%d%m%Y')}_{data_fim.strftime('%d%m%Y')}"
        
        return ManipulacaoArquivos.exportar_excel(dados_excel, nome_arquivo)
        
    except Exception as e:
        flash((f'Erro ao exportar para Excel: {str(e)}', 'error'))
        return redirect(url_for('dre_analitico'))


@app.route('/relatorios/relatorios-financeiros/dre-categoria-detalhes/<int:categoria_id>/pdf', methods=['GET'])
@login_required
@requires_roles
def dre_categoria_detalhes_pdf(categoria_id):
    """
    Exporta os detalhes de uma categoria DRE para PDF
    """
    try:
        data_inicio_str = request.args.get('data_inicio')
        data_fim_str = request.args.get('data_fim')
        
        if not data_inicio_str or not data_fim_str:
            flash(('Datas são obrigatórias para exportação.', 'error'))
            return redirect(url_for('dre_analitico'))
        
        categoria, registros, total, data_inicio, data_fim, erro = _buscar_detalhes_categoria_para_exportacao(
            categoria_id, data_inicio_str, data_fim_str
        )
        
        if erro:
            flash((f'Erro ao exportar: {erro}', 'error'))
            return redirect(url_for('dre_analitico'))
        
        if not registros:
            flash(('Nenhum registro encontrado para exportação.', 'warning'))
            return redirect(url_for('dre_analitico'))
        
        logo_path = obter_url_absoluta_de_imagem('logo.png')
        
        is_nfc = categoria.codigo == '1.01.03'
        subtotais_nfc = None
        if is_nfc:
            total_positivas = sum(r['valor'] for r in registros if r.get('tipo_nf_complementar') == 'positiva')
            total_negativas = sum(r['valor'] for r in registros if r.get('tipo_nf_complementar') == 'negativa')
            qtd_positivas = sum(1 for r in registros if r.get('tipo_nf_complementar') == 'positiva')
            qtd_negativas = sum(1 for r in registros if r.get('tipo_nf_complementar') == 'negativa')
            sinal_total = '+' if total >= 0 else '-'
            subtotais_nfc = {
                'total_positivas': total_positivas,
                'total_positivas_fmt': f"+ {ValoresMonetarios.converter_float_brl_positivo(total_positivas)}",
                'qtd_positivas': qtd_positivas,
                'total_negativas': total_negativas,
                'total_negativas_fmt': f"- {ValoresMonetarios.converter_float_brl_positivo(abs(total_negativas))}",
                'qtd_negativas': qtd_negativas,
                'total_liquido': total,
                'total_liquido_fmt': f"{sinal_total} {ValoresMonetarios.converter_float_brl_positivo(abs(total))}",
            }
        
        html = render_template(
            'relatorios/relatorios_financeiros/relatorio_dfc_dre/dre/dre_categoria_detalhes_pdf.html',
            categoria=categoria,
            registros=registros,
            total=total,
            total_formatado=ValoresMonetarios.converter_float_brl_positivo(abs(total)) if is_nfc else ValoresMonetarios.converter_float_brl_positivo(total),
            quantidade=len(registros),
            data_inicio=data_inicio,
            data_fim=data_fim,
            data_geracao=datetime.now(),
            logo_path=logo_path,
            is_nf_complementar=is_nfc,
            subtotais_nfc=subtotais_nfc
        )
        
        nome_arquivo = f"DRE_Detalhes_{categoria.nome.replace(' ', '_')}_{data_inicio.strftime('%d%m%Y')}_{data_fim.strftime('%d%m%Y')}"
        
        return ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo, 'landscape')
        
    except Exception as e:
        flash((f'Erro ao exportar para PDF: {str(e)}', 'error'))
        return redirect(url_for('dre_analitico'))