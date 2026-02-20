from sistema import app, db, requires_roles
from logs_sistema import flask_logger
from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from ...models_views.parametrizacao.changelog_model import ChangelogModel
from ..._utilitarios import ValidaForms


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
        branch = request.form.get('branch', '').strip() or None
        conteudo = request.form['conteudo']
        
        campos = {
                'data_lancamento': ['Data de Publicação', data_lancamento],
                'versao': ['Versão', versao],
                'conteudo': ['Conteúdo', conteudo],
                'branch': ['Branch', branch]
            }
        
        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
            
        if not 'validado' in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f'Todos os campos são obrigatórios!', 'warning'))
            
        if gravar_banco == True:
            ativo = 1
            
            novo_changelog = ChangelogModel(
                data_lancamento=data_lancamento, versao=versao,
                conteudo=conteudo, ativo=ativo, branch=branch
            )
            db.session.add(novo_changelog)
            db.session.commit()
            
            flash((f'Item adicionado com sucesso!', 'success'))
            flask_logger.info(f'Novo item de changelog adicionado pelo usuario com ID={current_user.id}.')
                
            return redirect(url_for('changelog_listar'))
        
    return render_template(
        'configuracao/changelog/changelog_cadastrar.html',
        dados_corretos = request.form,
        campos_obrigatorios = validacao_campos_obrigatorios
    )


@app.route('/changelog/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requires_roles
def changelog_editar(id):
    changelog = ChangelogModel.query.get_or_404(id)
    
    validacao_campos_obrigatorios = {}
    gravar_banco = True
    
    if request.method == 'POST':
        data_lancamento = request.form['dataPublicacao']
        versao = request.form['versao']
        branch = request.form.get('branch', '').strip() or None
        conteudo = request.form['conteudo']
        
        campos = {
            'data_lancamento': ['Data de Publicação', data_lancamento],
            'versao': ['Versão', versao],
            'conteudo': ['Conteúdo', conteudo],
            'branch': ['Branch', branch]
        }
        
        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
        
        if 'validado' not in validacao_campos_obrigatorios:
            gravar_banco = False
            flash(('Todos os campos são obrigatórios!', 'warning'))
        
        if gravar_banco:
            changelog.data_lancamento = data_lancamento
            changelog.versao = versao
            changelog.branch = branch
            changelog.conteudo = conteudo
            
            db.session.commit()
            
            flash(('Changelog atualizado com sucesso!', 'success'))
            flask_logger.info(f'Changelog ID={id} editado pelo usuário com ID={current_user.id}.')
            
            return redirect(url_for('changelog_listar'))
    
    return render_template(
        'configuracao/changelog/changelog_editar.html',
        changelog=changelog,
        campos_obrigatorios=validacao_campos_obrigatorios
    )