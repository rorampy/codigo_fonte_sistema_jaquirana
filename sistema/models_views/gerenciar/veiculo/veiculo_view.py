from sistema import app, requires_roles, db, current_user
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from sistema.models_views.gerenciar.veiculo.veiculo_model import VeiculoModel
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema.models_views.gerenciar.veiculo.veiculo_transportadora_veiculo_associado_model import TransportadoraVeiculoAssocModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema._utilitarios import *
from datetime import datetime

@app.route("/gerenciar/veiculos", methods=["GET"])
@login_required
@requires_roles
def listar_veiculos():
    if any(request.args.values()):
        veiculos = VeiculoModel.filtrar_veiculos(
            transportadora=request.args.get("transportadora"),
            placa=request.args.get("placa"),
        )
    else:
        veiculos = VeiculoModel.listar_veiculos()
        
    return render_template(
        "gerenciar/veiculos/veiculos_listar.html",
        veiculos=veiculos,
        dados_corretos=request.args,
    )

@app.route("/gerenciar/veiculos/cadastrar", methods=["GET", "POST"])
@login_required
@requires_roles
def cadastrar_veiculo():
    transportadoras = TransportadoraModel.listar_transportadoras_ativas()
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    if request.method == "POST":
        transportadoras_ids = request.form.getlist("transportadoras[]")
        placa_veiculo = request.form["placaVeiculo"]
        capacidade_veiculo = request.form["capacidadeVeiculo"]

        # Obtem somente as que contem informação
        transportadoras_ids = [t for t in transportadoras_ids if t.strip().isdigit()]

        campos = {
            "placaVeiculo": ["Placa veículo", placa_veiculo],
            "capacidadeVeiculo": ["Capacidade veículo", capacidade_veiculo],
        }

        if transportadoras_ids == [""]:
            gravar_banco = False
            flash((f"Transportadora é obrigatório!", "warning"))

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))

        pesquisa_placa_veiculo = VeiculoModel.query.filter_by(
            placa_veiculo=placa_veiculo
        ).first()
        if pesquisa_placa_veiculo:
            gravar_banco = False
            validacao_campos_erros["placaVeiculo"] = (
                f"A Placa informada já existe no banco de dados!"
            )

        if gravar_banco == True:
            veiculo = VeiculoModel(
                placa_veiculo=placa_veiculo.upper(),
                capacidade_ton=capacidade_veiculo,
                ativo=True
            )
            db.session.add(veiculo)
            db.session.flush()

            for id_transportadora in transportadoras_ids:
                veiculo_associado = TransportadoraVeiculoAssocModel(
                    transportadora_id=id_transportadora, veiculo_id=veiculo.id, ativo=True
                )
                db.session.add(veiculo_associado)

            db.session.commit()

            acao = TipoAcaoEnum.CADASTRO
            PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                current_user.id, acao, acao.pontos, modulo="veículo"
            )
            flash(("Veículo cadastrado com sucesso!", "success"))
            return redirect(url_for("listar_veiculos"))
    return render_template(
        "gerenciar/veiculos/veiculo_cadastrar.html",
        transportadoras=transportadoras,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
    )


@app.route("/gerenciar/veiculo/editar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_veiculo(id):
    transportadoras = TransportadoraModel.listar_transportadoras_ativas()
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    veiculo = VeiculoModel.obter_veiculo_por_id(id)

    if not veiculo:
        flash(("Veículo não encontrado!", "warning"))
        return redirect(url_for("listar_veiculos"))

    if veiculo.ativo == False:
        flash(("Veículo não pode ser editado, pois está inativo!", "warning"))
        return redirect(url_for("listar_veiculos"))

    # Busca todas as associações ativas e não deletadas para esse veículo
    transportadorasAssociadas = TransportadoraVeiculoAssocModel.obter_transportadoras_assoc_veiculo_id(veiculo.id)
    associacoes_atuais = { str(assoc.id): assoc for assoc in transportadorasAssociadas }

    # Se não houver associação nova, mas o veículo ainda tiver o campo legado preenchido
    if not transportadorasAssociadas and veiculo.transportadora_id:
        assoc_simulada = TransportadoraVeiculoAssocModel(
            transportadora_id=veiculo.transportadora_id,
            veiculo_id=veiculo.id,
            ativo=True
        )
        transportadoras_atuais = [assoc_simulada]
    else:
        transportadoras_atuais = list(associacoes_atuais.values())

    if request.method == "POST":
        placa_veiculo = request.form["placaVeiculo"]
        capacidade_veiculo = request.form["capacidadeVeiculo"]

        id_list = request.form.getlist("idTransportadora[]")
        transportadora_id_list = request.form.getlist("transportadoras[]")

        # Obtem somente as que contem informação
        transportadora_id_list = [t for t in transportadora_id_list if t.strip().isdigit()]

        campo_transportadora = ", ".join(transportadora_id_list) if transportadora_id_list else ""

        campos = {
            "transportadoraVeiculo": ["Transportadora", campo_transportadora],
            "placaVeiculo": ["Placa veículo", placa_veiculo],
            "capacidadeVeiculo": ["Capacidade veículo", capacidade_veiculo],
        }

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if "validado" not in validacao_campos_obrigatorios:
            gravar_banco = False
            flash(("Verifique os campos destacados em vermelho!", "warning"))

        if veiculo.placa_veiculo != placa_veiculo:
            placa_existente = VeiculoModel.query.filter(
                VeiculoModel.placa_veiculo == placa_veiculo,
                VeiculoModel.deletado == False,
                VeiculoModel.ativo == True
            ).first()
            if placa_existente:
                gravar_banco = False
                validacao_campos_erros["placaVeiculo"] = "A Placa informada já existe no banco de dados!"

        if gravar_banco:
            obj1 = {
                "placa_veiculo": veiculo.placa_veiculo.strip(),
                "capacidade_ton": str(veiculo.capacidade_ton).strip(),
                "transportadora_ids": [str(a.transportadora_id) for a in associacoes_atuais.values()],
            }

            obj2 = {
                "placa_veiculo": placa_veiculo.strip(),
                "capacidade_ton": capacidade_veiculo.strip(),
                "transportadora_ids": transportadora_id_list,
            }

            diferencas = Gameficacao.compara_objetos(obj1, obj2)
            if diferencas:
                acao = TipoAcaoEnum.EDICAO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id, acao, acao.pontos, modulo="veículo"
                )

            veiculo.placa_veiculo = placa_veiculo.upper()
            veiculo.capacidade_ton = capacidade_veiculo

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
                        nova = TransportadoraVeiculoAssocModel(
                            veiculo_id=veiculo.id,
                            transportadora_id=int(transportadora_id),
                            ativo=True                        )
                        db.session.add(nova)

            for assoc_id, assoc in associacoes_atuais.items():
                if assoc_id not in ids_recebidos:
                    assoc.ativo = False
                    assoc.deletado = True

            db.session.commit()
            flash(("Veículo editado com sucesso!", "success"))
            return redirect(url_for("listar_veiculos"))

    return render_template(
        "gerenciar/veiculos/veiculo_editar.html",
        veiculo=veiculo,
        transportadoras=transportadoras,
        transportadoras_atuais=transportadoras_atuais,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
    )


@app.route("/gerenciar/desativar/veiculo/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def desativar_veiculo(id):
    veiculo = VeiculoModel.obter_veiculo_por_id(id)

    if veiculo is None:
        flash(("Veículo não encontrado!", "warning"))

    veiculo.ativo = 0
    db.session.commit()
    flash(("Veículo desativado com sucesso!", "success"))
    return redirect(url_for("listar_veiculos"))


@app.route("/gerenciar/ativar/veiculo/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def ativar_veiculo(id):
    veiculo = VeiculoModel.obter_veiculo_por_id(id)

    if veiculo is None:
        flash(("Veículo não encontrado!", "warning"))

    veiculo.ativo = 1
    db.session.commit()
    flash(("Veículo ativado com sucesso!", "success"))
    return redirect(url_for("listar_veiculos"))
