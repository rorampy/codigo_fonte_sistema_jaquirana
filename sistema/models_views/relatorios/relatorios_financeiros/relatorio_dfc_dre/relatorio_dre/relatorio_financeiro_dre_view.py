from datetime import datetime, date
import calendar
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem, formatar_float_para_brl, formatar_data_para_brl, formatar_float_para_brl_sem_cifrao
from sistema._utilitarios.data_e_hora import DataHora
from flask import render_template, request, redirect, url_for, flash, session, jsonify, make_response, send_file
from flask_login import login_required
from sistema.models_views.controle_carga.registro_operacional_model import RegistroOperacionalModel
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
        
        # Debug: log dos dados capturados do formulário
        print(f"DEBUG DRE Analítico - Dados do form: data_inicio={dados_form['data_inicio']}, data_fim={dados_form['data_fim']}, exercicio={dados_form['exercicio']}")
        print(f"DEBUG DRE Analítico - Request form: {dict(request.form)}")
        print(f"DEBUG DRE Analítico - Request args: {dict(request.args)}")
        
        # Processar datas - SEMPRE usar dados do formulário primeiro
        if dados_form['exercicio'] and dados_form['exercicio'] != exercicio_default:
            try:
                # Usar a função dos utilitários para obter período completo
                data_inicio, data_fim = DataHora.obter_periodo_completo_mes(dados_form['exercicio'])
                
                # Atualizar dados_form
                dados_form['data_inicio'] = data_inicio.strftime('%Y-%m-%d')
                dados_form['data_fim'] = data_fim.strftime('%Y-%m-%d')
                
                # Debug: log das datas processadas do exercício
                print(f"DEBUG DRE Analítico - Exercício processado: {dados_form['exercicio']}, Data início: {data_inicio}, Data fim: {data_fim}")
                
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
        print(f"DEBUG: Gerando DRE Analítico com data_inicio: {data_inicio}, data_fim: {data_fim}")
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