from sistema import app, db, requires_roles
from flask import render_template, request, redirect, url_for, flash
from logs_sistema import flask_logger
from flask_login import login_required, current_user
from sistema.models_views.autenticacao.role_model import RoleModel


@app.route('/configuracoes/roles')
@login_required
@requires_roles
def roles_listar():

    roles = RoleModel.obter_roles_desc_id()

    return render_template(
        'configuracao/role/roles_listar.html',
        roles = roles
    )


@app.route('/configuracoes/role/cadastrar', methods=['GET', 'POST'])
@login_required
@requires_roles
def role_cadastrar():

    if request.method == 'POST':
        nome = request.form['nomeRole']
        cargo = request.form['cargoRole']

        if not nome or not cargo:
            flash((f'Todos os campos são obrigatórios!', 'warning'))
        
        else:
            nova_role = RoleModel(nome=nome, cargo=cargo)
            db.session.add(nova_role)
            db.session.commit()

            return redirect(url_for('roles_listar'))

    return render_template(
        'configuracao/role/role_cadastrar.html'
    )


@app.route('/configuracoes/role/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requires_roles
def role_editar(id):
    role = RoleModel.obter_role_por_id(id)

    if request.method == 'POST':
        nome = request.form['nomeRole']
        cargo = request.form['cargoRole']

        if not nome or not cargo:
            flash((f'Todos os campos são obrigatórios!', 'error'))
        
        else:
            role.nome = nome
            role.cargo = cargo
            db.session.commit()

            return redirect(url_for('roles_listar'))

    return render_template(
        'configuracao/role/role_editar.html',
        role = role
    )


@app.route('/configuracoes/role/excluir/<int:id>', methods=['GET', 'POST'])
@login_required
@requires_roles
def role_excluir(id):
    role = RoleModel.obter_role_por_id(id)
    if not role:
        flash(('Role não encontrada!', 'warning'))
        return redirect(url_for('roles_listar'))
    
    role.deletado = 1
    db.session.commit()
    
    flask_logger.info(
        f'Usuario ID = {current_user.id} deletou role ID = {role.id}'
    )
            
    flash(('Role deletada com sucesso!', 'success'))
    return redirect(url_for('roles_listar'))
