from sistema import app, db, requires_roles, current_user
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from sistema.models_views.gerenciar.motorista.motorista_model import MotoristaModel
from sistema.models_views.gerenciar.motorista.transportadora_motorista_associado_model import TransportadoraMotoristaAssocModel
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema._utilitarios import *


@app.route('/gerenciar/motoristas', methods=['GET', 'POST'])
@login_required
@requires_roles
def listar_motoristas():
    if any(request.args.values()):
        numeroDoc = request.args.get('cpf')
        numeroDocFormatado = ValidaDocs.somente_numeros(numeroDoc) if numeroDoc else None
        
        motoristas = MotoristaModel.filtrar_motoristas(
            transportadora=request.args.get('transportadora'),
            nome_completo=request.args.get('nomeCompleto'),
            numero_documento=numeroDocFormatado
        )
    else:
        motoristas = MotoristaModel.listar_motoristas()
        
    return render_template(
        'gerenciar/motoristas/motoristas_listar.html',
        motoristas=motoristas,
        dados_corretos=request.args
    )

@app.route('/gerenciar/motoristas/cadastrar', methods=['GET', 'POST'])
@login_required
@requires_roles
def cadastrar_motorista():
    transportadoras = TransportadoraModel.listar_transportadoras_ativas()
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    if request.method == "POST":
        transportadoras_ids = request.form.getlist("transportadoras[]")
        nomeCompleto = request.form["nomeCompleto"]
        cpf = request.form["cpf"]
        celular = request.form["celular"]

        transportadoras_ids = [t for t in transportadoras_ids if t.strip().isdigit()]

        campos = {
            "nomeCompleto": ["Nome completo", nomeCompleto],
            "cpf": ["CPF", cpf],
            "celular": ["Celular", celular],
        }

        if transportadoras_ids == [""]:
            gravar_banco = False
            flash((f"Transportadora é obrigatório!", "warning"))

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))

        verificacao_cpf = ValidaForms.validar_cpf(cpf)
        if not "validado" in verificacao_cpf:
            gravar_banco = False
            validacao_campos_erros.update(verificacao_cpf)

        cpf_tratado = ValidaDocs.remove_pontuacao_cpf(cpf)
        pesquisa_cpf_banco = MotoristaModel.query.filter_by(
            cpf=cpf_tratado
        ).first()
        if pesquisa_cpf_banco:
            gravar_banco = False
            validacao_campos_erros["cpf"] = (
                f"O CPF informado já existe no banco de dados!"
            )

        if gravar_banco == True:
            celular_tratado = Tels.remove_pontuacao_telefone_celular_br(celular)
            motorista = MotoristaModel(
                nome_completo=nomeCompleto,
                cpf=cpf_tratado,
                celular=celular_tratado,
                ativo=True
            )
            db.session.add(motorista)
            db.session.flush()

            for id_transportadora in transportadoras_ids:
                motorista_associado = TransportadoraMotoristaAssocModel(
                    transportadora_id=id_transportadora, motorista_id=motorista.id, ativo=True
                )
                db.session.add(motorista_associado)

            db.session.commit()
            acao = TipoAcaoEnum.CADASTRO
            PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                current_user.id,
                acao,
                acao.pontos,
                modulo='motorista'
            )
            flash(("Motorista cadastrado com sucesso!", "success"))
            return redirect(url_for("listar_motoristas"))
    return render_template('gerenciar/motoristas/motorista_cadastrar.html', transportadoras=transportadoras,
                           campos_obrigatorios=validacao_campos_obrigatorios,
                           campos_erros=validacao_campos_erros,
                           dados_corretos=request.form)


@app.route('/gerenciar/motorista/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requires_roles
def editar_motorista(id):
    motorista = MotoristaModel.obter_motorista_por_id(id)

    if motorista is None:
        flash(('Motorista não encontrado!', 'warning'))
        return redirect(url_for('listar_motoristas'))

    transportadoras = TransportadoraModel.listar_transportadoras_ativas()
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    motoristasAssociados = TransportadoraMotoristaAssocModel.obter_transportadoras_assoc_motorista_id(motorista.id)
    associacoes_atuais = { str(assoc.id): assoc for assoc in motoristasAssociados }

    if not motoristasAssociados and motorista.transportadora_id:
        assoc_simulada = TransportadoraMotoristaAssocModel(
            transportadora_id=motorista.transportadora_id,
            motorista_id=motorista.id,
            ativo=True
        )
        transportadoras_atuais = [assoc_simulada]
    else:
        transportadoras_atuais = list(associacoes_atuais.values())

    if request.method == "POST":
        nomeCompleto = request.form["nomeCompleto"]
        cpf = request.form["cpf"]
        celular = request.form["celular"]

        id_list = request.form.getlist("idTransportadora[]")
        transportadora_id_list = request.form.getlist("transportadoras[]")

        transportadora_id_list = [t for t in transportadora_id_list if t.strip().isdigit()]

        campo_transportadora = ", ".join(transportadora_id_list) if transportadora_id_list else ""

        campos = {
            "transportadoraMotorista": ["Transportadora", campo_transportadora],
            "nomeCompleto": ["Nome completo", nomeCompleto],
            "cpf": ["CPF", cpf],
            "celular": ["Celular", celular],
        }

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))

        verificacao_cpf = ValidaForms.validar_cpf(cpf)
        if not "validado" in verificacao_cpf:
            gravar_banco = False
            validacao_campos_erros.update(verificacao_cpf)

        cpf_tratado = ValidaDocs.remove_pontuacao_cpf(cpf)
        if motorista.cpf != cpf_tratado:
            pesquisa_cpf_banco = MotoristaModel.query.filter_by(
                cpf=cpf_tratado
            ).first()
            if pesquisa_cpf_banco:
                gravar_banco = False
                validacao_campos_erros["cpf"] = (
                    f"O CPF informado já existe no banco de dados!"
                )

        if gravar_banco == True:
            celular_tratado = Tels.remove_pontuacao_telefone_celular_br(celular)

            obj1 = {
                "transportadora_ids": [str(a.transportadora_id) for a in associacoes_atuais.values()],
                "nome_completo": motorista.nome_completo.strip(),
                "cpf": motorista.cpf,
                "celular": motorista.celular.strip(),
            }

            obj2 = {
                "transportadora_ids": transportadora_id_list,
                "nome_completo": nomeCompleto.strip(),
                "cpf": cpf_tratado,
                "celular": celular_tratado.strip(),
            }

            diferenca = Gameficacao.compara_objetos(obj1, obj2)
            if diferenca:
                acao = TipoAcaoEnum.EDICAO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    acao,
                    acao.pontos,
                    modulo='motorista'
                )

            motorista.nome_completo=nomeCompleto
            motorista.cpf=cpf_tratado
            motorista.celular=celular_tratado

            ids_recebidos = set()

            for assoc_id, transportadora_id in zip(id_list, transportadora_id_list):
                if transportadora_id.strip():
                    ids_recebidos.add(assoc_id)

                    if assoc_id and assoc_id in associacoes_atuais:
                        assoc = associacoes_atuais[assoc_id]
                        assoc.transportadora_id = int(transportadora_id)
                        assoc.ativo = True
                        assoc.deletado = False
                    else:
                        nova = TransportadoraMotoristaAssocModel(
                            motorista_id=motorista.id,
                            transportadora_id=int(transportadora_id),
                            ativo=True                        )
                        db.session.add(nova)

            for assoc_id, assoc in associacoes_atuais.items():
                if assoc_id not in ids_recebidos:
                    assoc.ativo = False
                    assoc.deletado = True

            db.session.commit()
            
            flash(("Motorista ediitado com sucesso!", "success"))
            return redirect(url_for("listar_motoristas"))
    return render_template('gerenciar/motoristas/motorista_editar.html',
                           motorista=motorista,
                           transportadoras=transportadoras,
                           transportadoras_atuais=transportadoras_atuais,
                           campos_obrigatorios=validacao_campos_obrigatorios,
                           campos_erros=validacao_campos_erros)

@app.route('/gerenciar/desativar/motorista/<int:id>', methods=['GET', 'POST'])
@login_required
@requires_roles
def desativar_motorista(id):
    motorista = MotoristaModel.obter_motorista_por_id(id)
    if motorista is None:
        flash(('Motorista não encontrado!', 'warning'))
        return redirect(url_for('listar_motoristas'))
    
    motorista.ativo = 0
    db.session.commit()
    flash(('Motorista desativado com sucesso!', 'success'))
    return redirect(url_for('listar_motoristas'))

@app.route('/gerenciar/ativar/motorista/<int:id>', methods=['GET', 'POST'])
@login_required
@requires_roles
def ativar_motorista(id):
    motorista = MotoristaModel.obter_motorista_por_id(id)
    if motorista is None:
        flash(('Motorista não encontrado!', 'warning'))
        return redirect(url_for('listar_motoristas'))
    
    motorista.ativo = 1
    db.session.commit()
    flash(('Motorista ativado com sucesso!', 'success'))
    return redirect(url_for('listar_motoristas'))


