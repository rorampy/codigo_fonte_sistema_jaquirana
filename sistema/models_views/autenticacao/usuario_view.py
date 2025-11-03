import os
from sistema import app, db, requires_roles
from logs_sistema import flask_logger
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user, logout_user
from werkzeug.utils import secure_filename
from sistema.models_views.autenticacao.usuario_model import UsuarioModel
from sistema.models_views.autenticacao.role_model import RoleModel
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema._utilitarios import *


@app.route('/usuarios')
@login_required
@requires_roles
def usuarios_listar():
    usuarios = UsuarioModel.obter_usuarios_desc_id()

    for usuario in usuarios:
        usuario.telefone = Tels.insere_pontuacao_telefone_celular_br(usuario.telefone)
        usuario.cpf = ValidaDocs.insere_pontuacao_cpf(usuario.cpf)

    flask_logger.info(f'Funcionario {current_user.nome} {current_user.sobrenome} acessou a tela de usuarios!')
    return render_template(
        'autenticacao/usuario/usuarios_listar.html',
        usuarios = usuarios
    )


@app.route('/usuario/cadastrar', methods=['GET', 'POST'])
@login_required
@requires_roles
def usuario_cadastrar():
    roles = RoleModel.obter_roles_desc_id()

    validacao_campos_obrigatorios = {}
    # chave é o name="", valor é o erro.
    validacao_campos_erros = {}
    gravar_banco = True

    if request.method == 'POST':
        nome = request.form['nomeUsuario']
        sobrenome = request.form['sobrenomeUsuario']
        cpf = request.form['cpfUsuario']
        telefone = request.form['telefoneUsuario']
        email = request.form['emailUsuario']
        senha = request.form['senhaUsuario']
        cargo = request.form['cargoUsuario']
        
        # "chave": ["Label", valor_input]
        campos = {
            'nome': ['Nome', nome],
            'sobrenome': ['Sobrenome', sobrenome],
            'cpf': ['CPF', cpf],
            'telefone': ['Telefone', telefone],
            'email': ['E-mail', email],
            'senhaUsuario': ['Senha', senha],
            'cargoUsuario': ['Cargo', cargo]
        }
            
        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not 'validado' in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f'Verifique os campos destacados em vermelho!', 'warning'))

        verificacao_email = ValidaForms.validar_email(email)
        if not 'validado' in verificacao_email:
            gravar_banco = False
            validacao_campos_erros.update(verificacao_email)

        if UsuarioModel.verificar_email_existente(email):
            gravar_banco = False
            validacao_campos_erros['email'] = f'O e-mail informado não pode ser utilizado. ERRO 01!'

        if UsuarioModel.verificar_email_existente_excluido(email):
            gravar_banco = False
            validacao_campos_erros['email'] = f'O e-mail informado não pode ser utilizado. ERRO 02!'

        verificacao_cpf = ValidaForms.validar_cpf(cpf)
        if not 'validado' in verificacao_cpf:
            gravar_banco = False
            validacao_campos_erros.update(verificacao_cpf)

        cpf_tratado = ValidaDocs.remove_pontuacao_cpf(cpf)
        pesquisa_cpf_banco = UsuarioModel.query.filter_by(cpf=cpf_tratado).first()
        if pesquisa_cpf_banco:
            gravar_banco = False
            validacao_campos_erros['cpf'] = f'O CPF informado já existe no banco de dados!'
            
        if gravar_banco == True:
            #senha = UsuarioModel.gerar_senha_aleatoria_sem_cripto(8)
            telefone_tratado = Tels.remove_pontuacao_telefone_celular_br(telefone)
            ativo = 1

            foto_perfil_id = 1

            usuario = UsuarioModel(
                nome=nome, sobrenome=sobrenome, cpf=cpf_tratado, 
                foto_perfil_id=foto_perfil_id, telefone=telefone_tratado,
                email=email, senha=senha, role_id=cargo, ativo=ativo
            )
            db.session.add(usuario)
            db.session.commit()

            flask_logger.info(f'Usuario {usuario.nome} {usuario.sobrenome} foi cadastrado no banco!')
            
            flash((f'Usuário cadastrado com sucesso!', 'success'))
            
            return redirect(url_for('usuarios_listar'))

    return render_template(
        'autenticacao/usuario/usuario_cadastrar.html',
        campos_obrigatorios = validacao_campos_obrigatorios,
        campos_erros = validacao_campos_erros,
        dados_corretos = request.form,
        roles = roles
    )


@app.route('/usuario/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requires_roles
def usuario_editar(id):
    roles = RoleModel.obter_roles_desc_id()
    usuario = UsuarioModel.obter_usuario_por_id(id)

    validacao_campos_obrigatorios = {}
    # chave é o name="", valor é o erro.
    validacao_campos_erros = {}
    gravar_banco = True

    if request.method == 'POST':
        nome = request.form['nomeUsuario']
        sobrenome = request.form['sobrenomeUsuario']
        telefone = request.form['telefoneUsuario']
        email = request.form['emailUsuario']
        cargo = request.form['cargoUsuario']

        # "chave": ["Label", valor_input]
        campos = {
            'nome': ['Nome', nome],
            'sobrenome': ['Sobreome', sobrenome],
            'telefone': ['Telefone', telefone],
            'email': ['E-mail', email]
        }
            
        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not 'validado' in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f'Verifique os campos destacados em vermelho!', 'warning'))

        verificacao_email = ValidaForms.validar_email(email)
        if not 'validado' in verificacao_email:
            gravar_banco = False
            validacao_campos_erros.update(verificacao_email)

        consulta_email_banco = UsuarioModel.verificar_email_existente(email)
        if consulta_email_banco and email != usuario.email:
            gravar_banco = False
            validacao_campos_erros['email'] = f'O e-mail informado não pode ser utilizado. ERRO 01!'

        consulta_email_del_banco = UsuarioModel.verificar_email_existente_excluido(email)
        if consulta_email_del_banco and email != usuario.email:
            gravar_banco = False
            validacao_campos_erros['email'] = f'O e-mail informado não pode ser utilizado. ERRO 02!'
            
        if gravar_banco == True:
            telefone_tratado = Tels.remove_pontuacao_telefone_celular_br(telefone)
            usuario.nome = nome
            usuario.sobrenome = sobrenome
            usuario.email = email
            usuario.role_id = cargo
            usuario.telefone = telefone_tratado
            db.session.commit()

            flask_logger.info(f'Funcionario {current_user.nome} {current_user.sobrenome} editou usuario com ID = {id}!')
            flash((f'Usuário alterado com sucesso!', 'success'))
            
            return redirect(url_for('usuarios_listar'))
        
    return render_template(
        'autenticacao/usuario/usuario_editar.html',
        campos_obrigatorios = validacao_campos_obrigatorios,
        campos_erros = validacao_campos_erros,
        usuario = usuario,
        roles = roles
    )


@app.route('/usuario/desativar/<int:id>', methods=['GET', 'POST'])
@login_required
@requires_roles
def usuario_desativar(id):
    usuario = UsuarioModel.obter_usuario_por_id(id)
    usuario.ativo = 0
    db.session.commit()
    
    flask_logger.info(f'Funcionario {current_user.nome} {current_user.sobrenome} desativou usuario com ID = {id}!')

    return redirect(url_for('usuarios_listar'))


@app.route('/usuario/ativar/<int:id>', methods=['GET', 'POST'])
@login_required
@requires_roles
def usuario_ativar(id):
    usuario = UsuarioModel.obter_usuario_por_id(id)
    usuario.ativo = 1
    db.session.commit()
    
    flask_logger.info(f'Funcionario {current_user.nome} {current_user.sobrenome} ativou usuario com ID = {id}!')
    
    return redirect(url_for('usuarios_listar'))


@app.route('/usuario/minha_conta/<int:id>', methods=['GET', 'POST'])
@login_required
@requires_roles
def usuario_minha_conta(id):
    usuario = UsuarioModel.obter_usuario_por_id(id)

    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    if request.method == 'POST':
        nome = request.form['nomeUsuario']
        sobrenome = request.form['sobrenomeUsuario']
        telefone = request.form['telefoneUsuario']
        foto_perfil = request.files['fotoPerfilUsuario']
        senha_atual = request.form['senhaAtualUsuario']
        nova_senha = request.form['novaSenhaUsuario']
        repertir_nova_senha = request.form['repetirNovaSenhaUsuario']
        
        # "chave": ["Label", valor_input]
        campos = {
            'nome': ['Nome', nome],
            'sobrenome': ['Sobrenome', sobrenome],
            'telefone': ['Telefone', telefone],
        }
            
        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
        if not 'validado' in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f'Verifique os campos destacados em vermelho!', 'warning'))

        if senha_atual or nova_senha or repertir_nova_senha:
            validacao_senha_atual = usuario.verificar_senha(senha_atual)
            
            if not senha_atual:
                gravar_banco = False
                validacao_campos_erros['senha_atual'] = 'Campo Obrigatório!'
                flash((f'Verifique os campos destacados em vermelho!', 'warning'))

            elif not nova_senha:
                gravar_banco = False
                validacao_campos_erros['nova_senha'] = 'Campo Obrigatório!'
                flash((f'Verifique os campos destacados em vermelho!', 'warning'))

            elif not repertir_nova_senha:
                gravar_banco = False
                validacao_campos_erros['repetir_nova_senha'] = 'Campo Obrigatório!'
                flash((f'Verifique os campos destacados em vermelho!', 'warning'))

            elif validacao_senha_atual == False:
                gravar_banco = False
                validacao_campos_erros['senha_atual'] = 'A senha atual está incorreta!'
                flash((f'Verifique os campos destacados em vermelho!', 'warning'))
            
            elif len(nova_senha) < 8:
                gravar_banco = False
                validacao_campos_erros['nova_senha'] = 'A nova senha deve ter pelo menos 8 caracteres!'
                flash((f'Verifique os campos destacados em vermelho!', 'warning'))

            elif nova_senha != repertir_nova_senha:
                gravar_banco = False
                validacao_campos_erros['nova_senha'] = '"Nova Senha" deve ser igual a "Repetir nova Senha"!'
                validacao_campos_erros['repetir_nova_senha'] = '"Repetir nova Senha" deve ser igual a "Nova Senha"!'
            
            else:
                senha = UsuarioModel.gerar_hash_senha(nova_senha)

        else:
            senha = usuario.senha
        
        if foto_perfil.filename:
            arquivo_foto_perfil = upload_arquivo(foto_perfil, 'UPLOADED_USERS', 'usuario')

        if gravar_banco == True:
            telefone = Tels.remove_pontuacao_telefone_celular_br(telefone)
            
            usuario.nome = nome
            usuario.sobrenome = sobrenome
            usuario.telefone = telefone
            usuario.foto_perfil_id = arquivo_foto_perfil.id if foto_perfil.filename else usuario.foto_perfil_id
            usuario.senha = senha
            db.session.commit()

            flash((f'Seus dados foram atualizados com sucesso!', 'success'))
            return redirect(url_for('principal'))


    return render_template(
        'autenticacao/minha_conta/usuarios_minha_conta.html',
        usuario = usuario,
        campos_obrigatorios = validacao_campos_obrigatorios,
        campos_erros = validacao_campos_erros,
        dados_informados=request.form
    )