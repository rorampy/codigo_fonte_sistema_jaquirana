from sistema import app, db, requires_roles
from logs_sistema import flask_logger
from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema._utilitarios import ValidaForms


# Processador de contexto, fornece a consulta em todo o escopo do projeto
@app.context_processor
def get_artigos():
    item_mais_recente = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    
    versao_atual = item_mais_recente.versao if item_mais_recente else '0.0.0'
    data_versao = item_mais_recente.data_lancamento if item_mais_recente else '00/00/0000'

    return {
        'versao_atual': versao_atual,
        'data_versao': data_versao
        }
    
    
@app.route('/changelog')
@login_required
@requires_roles
def changelog_listar():
    
    changelog_sistema = ChangelogModel.obter_changelog_desc_id()
    
    return render_template(
        'configuracao/changelog/changelog_listar.html',
        changelog_sistema = changelog_sistema
    )


@app.route('/changelog/cadastrar', methods=['GET', 'POST'])
@login_required
@requires_roles
def changelog_cadastrar():
    
    validacao_campos_obrigatorios = {}
    gravar_banco = True
    if request.method == 'POST':
        data_lancamento = request.form['dataPublicacao']
        versao = request.form['versao']
        conteudo = request.form['conteudo']
        
        campos = {
                'data_lancamento': ['Data de Publicação', data_lancamento],
                'versao': ['Versão', versao],
                'conteudo': ['Conteúdo', conteudo]
            }
        
        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
            
        if not 'validado' in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f'Todos os campos são obrigatórios!', 'warning'))
            
        if gravar_banco == True:
            ativo = 1
            
            novo_changelog = ChangelogModel(
                data_lancamento=data_lancamento, versao=versao,
                conteudo=conteudo, ativo=ativo
            )
            db.session.add(novo_changelog)
            db.session.commit()
            
            flash((f'Item adicionado com sucesso!', 'success'))
            flask_logger.info(f'Novo item de changelog adicionado pelo usuario com ID={current_user.id}.')
                
            return redirect(url_for('changelog_listar'))
        
    return render_template(
        'configuracao/changelog/changelog_cadastrar.html',
        dados_corretos = request.form
    )