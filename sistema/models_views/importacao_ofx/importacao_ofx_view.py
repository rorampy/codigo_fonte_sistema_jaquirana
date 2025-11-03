from datetime import datetime
from sqlalchemy import func, and_
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem
from werkzeug.utils import secure_filename
from flask import render_template, request, redirect, url_for, flash, session, jsonify, Response
from flask_login import login_required, current_user
from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx
from sistema._utilitarios import *

@app.route("/financeiro/movimentacoes-financeiras/importar-ofx", methods=["GET", "POST"])
@login_required
@requires_roles
def importar_ofx():
    chaves_ofx = ['ofx_transacoes', 'ofx_resumo', 'arquivo_nome', 'data_importacao']
    for key in chaves_ofx:
        if key in session:
            del session[key]
    
    session.modified = True

    stats_transacoes = ImportacaoOfx.obter_estatisticas_transacoes()
    
    total_transacoes_existentes = stats_transacoes.get('total', 0)
    transacoes_conciliadas = stats_transacoes.get('conciliadas', 0) 
    transacoes_nao_conciliadas = stats_transacoes.get('nao_conciliadas', 0)

    if request.method == "POST":
        
        if 'arquivo_ofx' not in request.files:
            flash(('Nenhum arquivo foi selecionado!', 'danger'))
            return redirect(request.url)
        
        arquivo = request.files['arquivo_ofx']
        
        if arquivo.filename == '':
            flash(('Nenhum arquivo foi selecionado!', 'danger'))
            return redirect(request.url)
        
        # Validação de tamanho (10MB)
        if arquivo.content_length and arquivo.content_length > 10 * 1024 * 1024:
            flash(('Arquivo muito grande! Máximo permitido: 10MB', 'danger'))
            return redirect(request.url)
        
        if not allowed_file(arquivo.filename):
            flash(('Formato de arquivo não suportado! Use apenas .ofx ou .qfx', 'danger'))
            return redirect(request.url)
        
        try:
            # Ler conteúdo do arquivo
            arquivo_conteudo = arquivo.read()
            
            # Validação adicional de tamanho após leitura
            if len(arquivo_conteudo) > 10 * 1024 * 1024:
                flash(('Arquivo muito grande! Máximo permitido: 10MB', 'danger'))
                return redirect(request.url)
            
            # Validação básica de formato OFX
            if not arquivo_conteudo or b'<OFX>' not in arquivo_conteudo:
                flash(('Arquivo não parece ser um OFX válido!', 'danger'))
                return redirect(request.url)
            
            # Processar arquivo
            processor = OFXProcessor()
            sucesso, mensagem = processor.processar_arquivo(arquivo_conteudo)
            
            if sucesso:
                resumo = processor.get_resumo()
                transacoes = processor.get_transacoes()
                
                # Verificar se há transações
                if not transacoes:
                    flash(('Arquivo OFX válido, mas não contém transações!', 'warning'))
                    return redirect(request.url)
                
                # Preparar dados das transações com todos os campos necessários
                transacoes_completas = []
                for t in transacoes:
                    transacao_data = {
                        'date': t.get('date'),
                        'amount': t.get('amount'),
                        'memo': t.get('memo'),
                        'tipo_movimento': t.get('tipo_movimento'),
                        'categoria_automatica': t.get('categoria_automatica'),
                        'descricao_limpa': t.get('descricao_limpa'),
                        'valor_formatado': t.get('valor_formatado'),
                        'fitid': t.get('fitid'),
                        'refnum': t.get('refnum')
                    }
                    transacoes_completas.append(transacao_data)
                
                # Preparar informações do arquivo para gravação no banco
                arquivo_info = {
                    'arquivo_nome': secure_filename(arquivo.filename),
                    'data_importacao': datetime.now().isoformat(),
                    'resumo': {
                        'total_transacoes': resumo.get('total_transacoes', 0),
                        'totais': resumo.get('totais', {}),
                        'conta': resumo.get('conta', {}),
                        'instituicao': resumo.get('instituicao', {}),
                        'periodo': resumo.get('periodo', {}),
                        'moeda': resumo.get('moeda', 'BRL'),
                        'data_processamento': resumo.get('data_processamento', '')
                    }
                }
                
                # Gravar transações no banco de dados
                sucesso_bd, resultado = ImportacaoOfx.inserir_transacoes_lote(
                    transacoes_completas, 
                    arquivo_info
                )
                
                if sucesso_bd:
                    total_inseridas = resultado.get('total', 0) if isinstance(resultado, dict) else resultado
                    batch_id = resultado.get('batch_id') if isinstance(resultado, dict) else None
                    
                    resumo_bd = ImportacaoOfx.obter_resumo_importacao(batch_id)
                    
                    if resumo_bd:
                        total = resumo_bd.get('total_transacoes', 0)
                        creditos = resumo_bd.get('creditos_formatado', 'R$ 0,00')
                        debitos = resumo_bd.get('debitos_formatado', 'R$ 0,00')
                        
                        flash((
                            f'Arquivo importado com sucesso! {total} transações processadas e salvas no banco de dados. '
                            f'Créditos: {creditos} | Débitos: {debitos}', 
                            'success'
                        ))
                    else:
                        flash((
                            f'Arquivo importado com sucesso! {total_inseridas} transações processadas e salvas no banco de dados.', 
                            'success'
                        ))
                    
                    session['current_batch_id'] = batch_id
                    session.modified = True
                    
                    return redirect(url_for('listagem_ofx'))
                    
                else:
                    flash((f'Erro ao salvar dados no banco: {resultado}', 'danger'))
                    return redirect(request.url)
                    
            else:
                flash((f'Erro ao processar arquivo: {mensagem}', 'danger'))
                return redirect(request.url)
        
        except Exception as e:
            flash((f'Erro inesperado ao processar arquivo: {str(e)}', 'danger'))
            return redirect(request.url)
            
    return render_template("financeiro/importar_ofx/importar_ofx.html",
        total_transacoes_existentes=total_transacoes_existentes,
        transacoes_conciliadas=transacoes_conciliadas,
        transacoes_nao_conciliadas=transacoes_nao_conciliadas)

@app.route("/cancelar-conciliacao", methods=["GET", "POST"])
@login_required
@requires_roles
def cancelar_conciliacao():
    try:
        limpar_dados_conciliacao()
        flash(('Conciliação cancelada com sucesso!', 'success'))
        return redirect(url_for('listagem_ofx'))
    except:
        flash(('Erro ao tentar cancelar conciliação', 'danger'))
        return redirect(url_for('listagem_ofx'))

def limpar_dados_conciliacao():
    """Remove dados de conciliação e diferenças da sessão"""
    if 'dados_conciliacao' in session:
        dados = session['dados_conciliacao']
        
        # Log específico se há diferenças sendo removidas
        if dados.get('tem_diferenca'):
            print("[DEBUG] Removendo dados de diferença de conciliação da sessão")
        
        session.pop('dados_conciliacao', None)
        print("[DEBUG] Dados de conciliação removidos da sessão")
        
        # Garantir que a sessão seja modificada
        session.modified = True

def verificar_e_limpar_conciliacao_incorreta(tipo_esperado):
    """Limpa a sessão se a conciliação não for do tipo esperado ou se houver dados de diferença órfãos"""
    dados_conciliacao = session.get('dados_conciliacao', {})
    
    if not dados_conciliacao:
        return
    
    tipo_ativo = dados_conciliacao.get('tipo_conciliacao')
    tem_diferenca = dados_conciliacao.get('tem_diferenca', False)
    
    print(f"[DEBUG] tipo_ativo: {tipo_ativo}, tem_diferenca: {tem_diferenca}, tipo_esperado: {tipo_esperado}")
    
    # Se há dados de diferença mas estamos em qualquer página QUE NÃO SEJA outros_pagamentos
    if tem_diferenca and tipo_esperado != 'outros_pagamentos':
        print(f"[DEBUG] Limpando dados de diferença - usuário saiu da página de diferenças")
        limpar_dados_conciliacao()
        return
    
    # Se o tipo ativo é diferente do esperado (apenas quando há tipo_ativo)
    if tipo_ativo and tipo_ativo != tipo_esperado:
        print(f"[DEBUG] Limpando conciliação incorreta - Esperado: {tipo_esperado}, Ativo: {tipo_ativo}")
        limpar_dados_conciliacao()
        return



@app.route("/financeiro/conciliar-transacao/<int:transacao_id>/<tipo>")
@login_required
@requires_roles
def conciliar_transacao(transacao_id, tipo):
    transacao = ImportacaoOfx.query.get_or_404(transacao_id)
    
    redirects = {
        'pagamento_frete': 'listagem_fretes_a_pagar',
        'pagamento_fornecedor': 'listagem_fornecedores_a_pagar', 
        'pagamento_extrator': 'listagem_extratores_a_pagar',
        'outros_pagamentos': 'nova_movimentacao_financeira',
        'outros_recebimentos': 'nova_movimentacao_financeira',  
        'a_receber': 'listagem_a_receber'
    }
    
    if tipo not in redirects:
        flash((f'Tipo de conciliação "{tipo}" não reconhecido!', 'error'))
        return redirect(url_for('listagem_ofx'))
    
    try:
        dados_base = {
            'transacao_id': transacao_id,
            'valor': transacao.valor_formatado or 'R$ 0,00',
            'data': transacao.data_transacao.strftime('%Y-%m-%d') if transacao.data_transacao else '',
            'descricao': transacao.descricao_limpa or transacao.memo or 'Sem descrição',
            'fitid': transacao.fitid or '',
            'tipo_movimento': transacao.tipo_movimento or '',
            'categoria': transacao.categoria_automatica or 'OUTROS',
            'tipo_conciliacao': tipo
        }
        
        if tipo == 'outros_pagamentos':
            dados_base.update({
                'tipo_movimentacao_predefinido': 'despesa',  
                'valor_sem_formatacao': abs(transacao.valor) if transacao.valor else 0, 
                'descricao_sugerida': transacao.descricao_limpa or transacao.memo or 'Pagamento via OFX',
                'valor_input': ValoresMonetarios.converter_string_brl_para_float(transacao.valor_formatado)
            })
        
        elif tipo == 'outros_recebimentos':  
            dados_base.update({
                'tipo_movimentacao_predefinido': 'receita', 
                'valor_sem_formatacao': abs(transacao.valor) if transacao.valor else 0,
                'descricao_sugerida': transacao.descricao_limpa or transacao.memo or 'Recebimento via OFX',
                'valor_input': ValoresMonetarios.converter_string_brl_para_float(transacao.valor_formatado)
            })
        
        elif tipo == 'a_receber':
            dados_base.update({
                'tipo_movimentacao_predefinido': 'receita',  
                'valor_sem_formatacao': abs(transacao.valor) if transacao.valor else 0,
                'descricao_sugerida': transacao.descricao_limpa or transacao.memo or 'Recebimento via OFX',
                'valor_input': ValoresMonetarios.converter_string_brl_para_float(transacao.valor_formatado),
                'valor_transacao_100': int(abs(transacao.valor * 100)) if transacao.valor else 0,
                'data_transacao': transacao.data_transacao,
                'memo_original': transacao.memo or '',
                'valor_absoluto': abs(transacao.valor) if transacao.valor else 0,
                'valor_original_ofx': abs(transacao.valor) if transacao.valor else 0,
                'fitid_original': transacao.fitid,
                'verificar_diferenca': True
            })
        
        session['dados_conciliacao'] = dados_base
        
        return redirect(url_for(redirects[tipo]))
        
    except Exception as e:
        print(f"[ERROR] Erro detalhado na conciliação: {str(e)}")
        flash((f'Erro ao processar transação: {str(e)}', 'error'))
        return redirect(url_for('listagem_ofx'))

def allowed_file(filename):
    """Verifica se o arquivo tem extensão permitida"""
    ALLOWED_EXTENSIONS = {'ofx', 'qfx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS