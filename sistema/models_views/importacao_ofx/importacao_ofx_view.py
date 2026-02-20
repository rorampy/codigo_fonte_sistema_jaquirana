from datetime import datetime
from sistema import app, requires_roles, db
from werkzeug.utils import secure_filename
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required
from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx
from sistema.models_views.importacao_ofx.importacao_ofx_service import ImportacaoOfxService
from sistema.models_views.configuracoes_gerais.conta_bancaria.conta_bancaria_model import ContaBancariaModel
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

    conta_bancaria_selecionada_id = request.args.get('conta_bancaria_id', type=int)

    stats_transacoes = ImportacaoOfxService.obter_estatisticas_transacoes()
    contas_bancarias = ContaBancariaModel.obter_contas_bancarias_ativas()
    
    total_transacoes_existentes = stats_transacoes.get('total', 0)
    transacoes_conciliadas = stats_transacoes.get('conciliadas', 0) 
    transacoes_nao_conciliadas = stats_transacoes.get('nao_conciliadas', 0)

    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    dados_corretos = {}
    gravar_banco = True

    if request.method == "POST":
        arquivo = request.files.get('arquivo_ofx')
        conta_bancaria_id = request.form.get('conta_bancaria')
        
        campos = {
            "arquivo_ofx": ["Arquivo OFX", arquivo.filename if arquivo else ""],
            "conta_bancaria": ["Conta Bancária", conta_bancaria_id]
        }

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            dados_corretos = request.form.to_dict()
            flash(("Verifique os campos destacados em vermelho!", "warning"))

        if arquivo and arquivo.filename:
            if not allowed_file(arquivo.filename):
                gravar_banco = False
                dados_corretos = request.form.to_dict()
                validacao_campos_erros["arquivo_ofx"] = "Formato de arquivo não suportado! Use apenas .ofx ou .qfx"
            
            if arquivo.content_length and arquivo.content_length > 10 * 1024 * 1024:
                gravar_banco = False
                dados_corretos = request.form.to_dict()
                validacao_campos_erros["arquivo_ofx"] = "Arquivo muito grande! Máximo permitido: 10MB"

        if conta_bancaria_id:
            conta_existe = ContaBancariaModel.query.filter_by(id=conta_bancaria_id, ativo=True).first()
            if not conta_existe:
                gravar_banco = False
                dados_corretos = request.form.to_dict()
                validacao_campos_erros["conta_bancaria"] = "Conta bancária selecionada não é válida ou está inativa"

        if gravar_banco == True and arquivo:
            dados_corretos = request.form.to_dict()
            
            try:
                arquivo_conteudo = arquivo.read()
                
                if len(arquivo_conteudo) > 10 * 1024 * 1024:
                    gravar_banco = False
                    dados_corretos = request.form.to_dict()
                    validacao_campos_erros["arquivo_ofx"] = "Arquivo muito grande! Máximo permitido: 10MB"
                
                if not arquivo_conteudo or b'<OFX>' not in arquivo_conteudo:
                    gravar_banco = False
                    dados_corretos = request.form.to_dict()
                    validacao_campos_erros["arquivo_ofx"] = "Arquivo não parece ser um OFX válido!"
                
                if gravar_banco == True:
                    processor = OFXProcessor()
                    sucesso, mensagem = processor.processar_arquivo(arquivo_conteudo)
                    
                    if sucesso:
                        resumo = processor.get_resumo()
                        transacoes = processor.get_transacoes()
                        
                        if not transacoes:
                            gravar_banco = False
                            dados_corretos = request.form.to_dict()
                            validacao_campos_erros["arquivo_ofx"] = "Arquivo OFX válido, mas não contém transações!"
                        
                        if gravar_banco == True:
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
                            
                            sucesso_bd, resultado = ImportacaoOfxService.inserir_transacoes_lote(
                                transacoes_completas, 
                                arquivo_info,
                                conta_bancaria_id
                            )
                            
                            if sucesso_bd:
                                total_inseridas = resultado.get('total', 0) if isinstance(resultado, dict) else resultado
                                batch_id = resultado.get('batch_id') if isinstance(resultado, dict) else None
                                duplicadas = resultado.get('duplicadas', 0) if isinstance(resultado, dict) else 0
                                mensagem_duplicadas = resultado.get('mensagem_duplicadas', '') if isinstance(resultado, dict) else ''
                                
                                if total_inseridas == 0 and duplicadas > 0:
                                    flash((
                                        f'Nenhuma transação nova encontrada. {mensagem_duplicadas}',
                                        'warning'
                                    ))
                                    return redirect(url_for('importar_ofx'))
                                
                                resumo_bd = ImportacaoOfxService.obter_resumo_importacao(batch_id)
                                
                                if resumo_bd:
                                    total = resumo_bd.get('total_transacoes', 0)
                                    creditos = resumo_bd.get('creditos_formatado', 'R$ 0,00')
                                    debitos = resumo_bd.get('debitos_formatado', 'R$ 0,00')
                                    
                                    mensagem_sucesso = f'Arquivo importado com sucesso! {total} transações processadas e salvas no banco de dados. Créditos: {creditos} | Débitos: {debitos}'
                                    
                                    if duplicadas > 0:
                                        mensagem_sucesso += f'. {mensagem_duplicadas}'
                                    
                                    flash((mensagem_sucesso, 'success'))
                                else:
                                    mensagem_sucesso = f'Arquivo importado com sucesso! {total_inseridas} transações processadas e salvas no banco de dados.'
                                    
                                    if duplicadas > 0:
                                        mensagem_sucesso += f' {mensagem_duplicadas}'
                                    
                                    flash((mensagem_sucesso, 'success'))
                                
                                session['current_batch_id'] = batch_id
                                session.modified = True
                                
                                return redirect(url_for('conciliacao_ofx', conta_id=conta_bancaria_id))
                                
                            else:
                                gravar_banco = False
                                dados_corretos = request.form.to_dict()
                                validacao_campos_erros["arquivo_ofx"] = f"Erro ao salvar dados no banco: {resultado}"
                                
                    else:
                        gravar_banco = False
                        dados_corretos = request.form.to_dict()
                        validacao_campos_erros["arquivo_ofx"] = f"Erro ao processar arquivo: {mensagem}"
                        
            except Exception as e:
                gravar_banco = False
                dados_corretos = request.form.to_dict()
                validacao_campos_erros["arquivo_ofx"] = f"Erro inesperado ao processar arquivo: {str(e)}"

    return render_template("financeiro/importar_ofx/importar_ofx.html",
        total_transacoes_existentes=total_transacoes_existentes,
        transacoes_conciliadas=transacoes_conciliadas,
        transacoes_nao_conciliadas=transacoes_nao_conciliadas,
        contas_bancarias=contas_bancarias,
        conta_bancaria_selecionada_id=conta_bancaria_selecionada_id,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=dados_corretos if request.method == "POST" else {}
    )

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
        
        if dados.get('tem_diferenca'):
            pass
        
        session.pop('dados_conciliacao', None)
        
        session.modified = True

def verificar_e_limpar_conciliacao_incorreta(tipo_esperado):
    """Limpa a sessão se a conciliação não for do tipo esperado ou se houver dados de diferença órfãos"""
    dados_conciliacao = session.get('dados_conciliacao', {})
    
    if not dados_conciliacao:
        return
    
    tipo_ativo = dados_conciliacao.get('tipo_conciliacao')
    tem_diferenca = dados_conciliacao.get('tem_diferenca', False)
    
    
    if tem_diferenca and tipo_esperado != 'outros_pagamentos':
        limpar_dados_conciliacao()
        return
    
    if tipo_ativo and tipo_ativo != tipo_esperado:
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
        flash((f'Erro ao processar transação: {str(e)}', 'error'))
        return redirect(url_for('listagem_ofx'))

@app.route("/financeiro/ignorar-movimentacao/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def ignorar_movimentacao_ofx(id):
    """Rota para ignorar/deletar uma movimentação OFX com justificativa"""
    try:
        transacao = ImportacaoOfxService.obter_transacao_por_fitid(id)
        justificativa = request.form.get('justificativa', '').strip()
        
        if not transacao:
            flash(('Transação não encontrada', 'danger'))
            return redirect(url_for('listagem_ofx'))
            
        if not justificativa:
            flash(('Justificativa é obrigatória', 'danger'))
            return redirect(url_for('listagem_ofx'))
            
        if len(justificativa) > 50:
            flash(('Justificativa deve ter no máximo 50 caracteres', 'danger'))
            return redirect(url_for('listagem_ofx'))
            
        if transacao.conciliado:
            flash(('Não é possível ignorar uma transação já conciliada', 'warning'))
            return redirect(url_for('listagem_ofx'))
        
        transacao.ofx_deletada = True
        transacao.ofx_justificativa_deletada = justificativa
        
        db.session.commit()
        
        flash(('Movimentação ignorada com sucesso', 'success'))
        return redirect(url_for('listagem_ofx'))
        
    except Exception as e:
        db.session.rollback()
        flash(('Erro interno do servidor', 'danger'))
        return redirect(url_for('listagem_ofx'))

def allowed_file(filename):
    """Verifica se o arquivo tem extensão permitida"""
    ALLOWED_EXTENSIONS = {'ofx', 'qfx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS