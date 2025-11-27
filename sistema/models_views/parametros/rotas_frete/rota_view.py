from sistema import app, requires_roles, db, current_user
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from sistema.models_views.gerenciar.floresta.floresta_model import FlorestaModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_model import FornecedorModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema.models_views.parametros.rotas_frete.rota_model import RotaFreteModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema._utilitarios import *


@app.route("/parametros/rotas/cadastrar", methods=["GET", "POST"])
@login_required
@requires_roles
def cadastrar_rota():
    try:
        fornecedores = FornecedorModel.listar_fornecedores_ativos()
        clientes = ClienteModel.listar_clientes_ativos()
        transportadoras = TransportadoraModel.listar_transportadoras_ativas()

        validacao_campos_obrigatorios = {}
        validacao_campos_erros = {}
        gravar_banco = True

        if request.method == "POST":
            fornecedorIdentificacao = request.form["fornecedorIdentificacao"]
            clienteDestino = request.form["clienteDestino"]
            transportadoraFrete = request.form["transportadoraFrete"]
            
            eucaPrecoCusto1 = request.form["eucaPrecoCusto1"]
            eucaPrecoCusto2 = request.form["eucaPrecoCusto2"]
            eucaPrecoCusto3 = request.form["eucaPrecoCusto3"]
            eucaPrecoCusto4 = request.form["eucaPrecoCusto4"]

            pinusPrecoCusto1 = request.form["pinusPrecoCusto1"]
            pinusPrecoCusto2 = request.form["pinusPrecoCusto2"]
            pinusPrecoCusto3 = request.form["pinusPrecoCusto3"]
            pinusPrecoCusto4 = request.form["pinusPrecoCusto4"]
            pinusPrecoCusto5 = request.form["pinusPrecoCusto5"]

            bioPrecoCusto5 = request.form["bioPrecoCusto5"]
            
            # Tratar a opção "Todos" - converter para None
            transportadora_id_final = None if transportadoraFrete == "todos" or not transportadoraFrete else int(transportadoraFrete)
            
            # Campo comuns - validar que pelo menos uma transportadora foi selecionada
            campos = {
                "clienteDestino": ["Cliente destino", clienteDestino],
                "transportadoraFrete": ["Transportadora", transportadoraFrete],
                "fornecedorIdentificacao": ["Fornecedor origem", fornecedorIdentificacao]
            }

            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

            if not "validado" in validacao_campos_obrigatorios:
                gravar_banco = False
                flash((f"Verifique os campos destacados em vermelho!", "warning"))

            if gravar_banco:
                # Query padrão
                query = RotaFreteModel.query.filter_by(
                    cliente_id=clienteDestino,
                    transportadora_id=transportadora_id_final
                )

                query = query.filter_by(fornecedor_id=fornecedorIdentificacao)

                if query.first():
                    gravar_banco = False
                    flash(("Já existe um registro com estas especificações!", "warning"))
            

            if gravar_banco:
                # Conversão dos valores de Eucalipto
                euca_preco_custo_1_float = ValoresMonetarios.converter_string_brl_para_float(eucaPrecoCusto1)
                euca_preco_custo_1_100 = euca_preco_custo_1_float * 100

                euca_preco_custo_2_float = ValoresMonetarios.converter_string_brl_para_float(eucaPrecoCusto2)
                euca_preco_custo_2_100 = euca_preco_custo_2_float * 100

                euca_preco_custo_3_float = ValoresMonetarios.converter_string_brl_para_float(eucaPrecoCusto3)
                euca_preco_custo_3_100 = euca_preco_custo_3_float * 100

                euca_preco_custo_4_float = ValoresMonetarios.converter_string_brl_para_float(eucaPrecoCusto4)
                euca_preco_custo_4_100 = euca_preco_custo_4_float * 100

                # Conversão dos valores de Pinus
                pinus_preco_custo_1_float = ValoresMonetarios.converter_string_brl_para_float(pinusPrecoCusto1)
                pinus_preco_custo_1_100 = pinus_preco_custo_1_float * 100

                pinus_preco_custo_2_float = ValoresMonetarios.converter_string_brl_para_float(pinusPrecoCusto2)
                pinus_preco_custo_2_100 = pinus_preco_custo_2_float * 100

                pinus_preco_custo_3_float = ValoresMonetarios.converter_string_brl_para_float(pinusPrecoCusto3)
                pinus_preco_custo_3_100 = pinus_preco_custo_3_float * 100

                pinus_preco_custo_4_float = ValoresMonetarios.converter_string_brl_para_float(pinusPrecoCusto4)
                pinus_preco_custo_4_100 = pinus_preco_custo_4_float * 100

                pinus_preco_custo_5_float = ValoresMonetarios.converter_string_brl_para_float(pinusPrecoCusto5)
                pinus_preco_custo_5_100 = pinus_preco_custo_5_float * 100

                bio_preco_custo_5_100 = int(ValoresMonetarios.converter_string_brl_para_float(bioPrecoCusto5) * 100)


                rota = RotaFreteModel(
                    floresta_id= None,
                    fornecedor_id=fornecedorIdentificacao,
                    cliente_id=clienteDestino,
                    transportadora_id=transportadora_id_final,
                    # Bitolas e preços de Eucalipto
                    euca_bitola_1_id=1,
                    euca_bitola_2_id=2,
                    euca_bitola_3_id=3,
                    euca_bitola_4_id=4,
                    euca_preco_custo_frete_bitola_1_100=euca_preco_custo_1_100,
                    euca_preco_custo_frete_bitola_2_100=euca_preco_custo_2_100,
                    euca_preco_custo_frete_bitola_3_100=euca_preco_custo_3_100,
                    euca_preco_custo_frete_bitola_4_100=euca_preco_custo_4_100,

                    # Bitolas e preços de Pinus
                    pinus_bitola_1_id=1,
                    pinus_bitola_2_id=2,
                    pinus_bitola_3_id=3,
                    pinus_bitola_4_id=4,
                    pinus_bitola_5_id=6,

                    pinus_preco_custo_frete_bitola_1_100=pinus_preco_custo_1_100,
                    pinus_preco_custo_frete_bitola_2_100=pinus_preco_custo_2_100,
                    pinus_preco_custo_frete_bitola_3_100=pinus_preco_custo_3_100,
                    pinus_preco_custo_frete_bitola_4_100=pinus_preco_custo_4_100,
                    pinus_preco_custo_frete_bitola_5_100=pinus_preco_custo_5_100,

                    bio_bitola_5_id=5,
                    bio_preco_custo_frete_bitola_5_100=bio_preco_custo_5_100,
                    ativo=True
                )
                db.session.add(rota)
                db.session.commit()
                acao = TipoAcaoEnum.CADASTRO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    acao,
                    acao.pontos,
                    modulo='rota_frete'
                )
                flash(("Rota de frete cadastrada com sucesso!", "success"))
                return redirect(url_for("listar_rotas"))
    except Exception as e:
        print(f"Erro ao cadastrar nova rota: {e}")
        flash(('Houve um erro ao tentar cadastrar nova rota! Entre em contato com o suporte!', 'warning'))
        return redirect(url_for('listar_rotas'))
    return render_template(
        "parametros/rotas_frete/rota_cadastrar.html",
        fornecedores=fornecedores,
        clientes=clientes,
        transportadoras=transportadoras,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
    )


@app.route("/parametros/rotas", methods=["GET", "POST"])
@login_required
@requires_roles
def listar_rotas():
    registros = RotaFreteModel.listar_rotas_agrupadas_por_cliente()
    return render_template("parametros/rotas_frete/rota_listar.html", registros=registros)


@app.route("/parametros/rotas/editar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_rota(id):
    try:
        rota = RotaFreteModel.obter_rota_por_id(id)

        if rota is None:
            flash(('Rota de frete não encontrada!', 'warning'))
            return redirect(url_for('listar_rotas'))

        fornecedores = FornecedorModel.listar_fornecedores_ativos()
        clientes = ClienteModel.listar_clientes_ativos()
        transportadoras = TransportadoraModel.listar_transportadoras_ativas()

        validacao_campos_obrigatorios = {}
        validacao_campos_erros = {}
        gravar_banco = True

        if request.method == "POST":
            floresta_id = request.form.get("florestaIdentificacao")
            fornecedor_id = request.form.get("fornecedorIdentificacao")
            cliente_id = request.form.get("clienteDestino")
            transportadora_id = request.form.get("transportadoraFrete")
            
            # Tratar a opção "Todos" - converter para None
            transportadora_id_final = None if transportadora_id == "todos" or not transportadora_id else int(transportadora_id)
            
            eucaPrecoCusto1 = request.form["eucaPrecoCusto1"]
            eucaPrecoCusto2 = request.form["eucaPrecoCusto2"]
            eucaPrecoCusto3 = request.form["eucaPrecoCusto3"]
            eucaPrecoCusto4 = request.form["eucaPrecoCusto4"]

            pinusPrecoCusto1 = request.form["pinusPrecoCusto1"]
            pinusPrecoCusto2 = request.form["pinusPrecoCusto2"]
            pinusPrecoCusto3 = request.form["pinusPrecoCusto3"]
            pinusPrecoCusto4 = request.form["pinusPrecoCusto4"]
            pinusPrecoCusto5 = request.form["pinusPrecoCusto5"]

            bioPrecoCusto5 = request.form["bioPrecoCusto5"]

            # Campos comuns
            campos = {
                "clienteDestino": ["Cliente destino", cliente_id],
                "transportadoraFrete": ["Transportadora", transportadora_id],
                "fornecedorIdentificacao": ["Fornecedor origem", fornecedor_id],
            }

            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

            if "validado" not in validacao_campos_obrigatorios:
                gravar_banco = False
                flash(("Verifique os campos destacados em vermelho!", "warning"))

            if gravar_banco:
                query = RotaFreteModel.query.filter(
                    RotaFreteModel.cliente_id == cliente_id,
                    RotaFreteModel.transportadora_id == transportadora_id_final
                )

                query = query.filter(RotaFreteModel.fornecedor_id == fornecedor_id)

                rota_existente = query.first()
                if rota_existente and rota_existente.id != rota.id:
                    gravar_banco = False
                    flash(("Já existe um registro com estas especificações!", "warning"))

            if gravar_banco:
                # Conversão dos valores de Eucalipto
                euca_preco_custo_1_float = ValoresMonetarios.converter_string_brl_para_float(eucaPrecoCusto1)
                euca_preco_custo_1_100 = euca_preco_custo_1_float * 100

                euca_preco_custo_2_float = ValoresMonetarios.converter_string_brl_para_float(eucaPrecoCusto2)
                euca_preco_custo_2_100 = euca_preco_custo_2_float * 100

                euca_preco_custo_3_float = ValoresMonetarios.converter_string_brl_para_float(eucaPrecoCusto3)
                euca_preco_custo_3_100 = euca_preco_custo_3_float * 100

                euca_preco_custo_4_float = ValoresMonetarios.converter_string_brl_para_float(eucaPrecoCusto4)
                euca_preco_custo_4_100 = euca_preco_custo_4_float * 100

                # Conversão dos valores de Pinus
                pinus_preco_custo_1_float = ValoresMonetarios.converter_string_brl_para_float(pinusPrecoCusto1)
                pinus_preco_custo_1_100 = pinus_preco_custo_1_float * 100

                pinus_preco_custo_2_float = ValoresMonetarios.converter_string_brl_para_float(pinusPrecoCusto2)
                pinus_preco_custo_2_100 = pinus_preco_custo_2_float * 100

                pinus_preco_custo_3_float = ValoresMonetarios.converter_string_brl_para_float(pinusPrecoCusto3)
                pinus_preco_custo_3_100 = pinus_preco_custo_3_float * 100

                pinus_preco_custo_4_float = ValoresMonetarios.converter_string_brl_para_float(pinusPrecoCusto4)
                pinus_preco_custo_4_100 = pinus_preco_custo_4_float * 100

                pinus_preco_custo_5_float = ValoresMonetarios.converter_string_brl_para_float(pinusPrecoCusto5)
                pinus_preco_custo_5_100 = pinus_preco_custo_5_float * 100

                bio_preco_custo_5_100 = int(ValoresMonetarios.converter_string_brl_para_float(bioPrecoCusto5) * 100)

                print('aqui', bio_preco_custo_5_100)

                # === COMPARAÇÃO DE OBJETOS ===#

                obj1 = {
                    "fornecedorIdentificacao": str(rota.fornecedor_id or ""),
                    "clienteDestino": str(rota.cliente_id or ""),
                    "transportadoraFrete": "todos" if rota.transportadora_id is None else str(rota.transportadora_id or ""),
                    "bioPrecoCusto5":rota.bio_preco_custo_frete_bitola_5_100,
                    "eucaPrecoCusto1":rota.euca_preco_custo_frete_bitola_1_100,
                    "eucaPrecoCusto2":rota.euca_preco_custo_frete_bitola_2_100,
                    "eucaPrecoCusto3":rota.euca_preco_custo_frete_bitola_3_100,
                    "eucaPrecoCusto4":rota.euca_preco_custo_frete_bitola_4_100,
                    "pinusPrecoCusto1":rota.pinus_preco_custo_frete_bitola_1_100,
                    "pinusPrecoCusto2":rota.pinus_preco_custo_frete_bitola_2_100,
                    "pinusPrecoCusto3":rota.pinus_preco_custo_frete_bitola_3_100,
                    "pinusPrecoCusto4":rota.pinus_preco_custo_frete_bitola_4_100,
                    "pinusPrecoCusto5":rota.pinus_preco_custo_frete_bitola_5_100,
                }

                obj2 = {
                    "fornecedorIdentificacao": str(fornecedor_id or ""),
                    "clienteDestino": str(cliente_id or ""),
                    "transportadoraFrete": "todos" if transportadora_id_final is None else str(transportadora_id_final or ""),
                    "bioPrecoCusto5":bio_preco_custo_5_100,
                    "eucaPrecoCusto1": euca_preco_custo_1_100,
                    "eucaPrecoCusto2": euca_preco_custo_2_100,
                    "eucaPrecoCusto3": euca_preco_custo_3_100,
                    "eucaPrecoCusto4": euca_preco_custo_4_100,
                    "pinusPrecoCusto1": pinus_preco_custo_1_100,
                    "pinusPrecoCusto2": pinus_preco_custo_2_100,
                    "pinusPrecoCusto3": pinus_preco_custo_3_100,
                    "pinusPrecoCusto4": pinus_preco_custo_4_100,
                    "pinusPrecoCusto5": pinus_preco_custo_5_100,
                }

                diferencas = Gameficacao.compara_objetos(obj1, obj2)
                if diferencas:
                    acao = TipoAcaoEnum.EDICAO
                    PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                        current_user.id,
                        acao,
                        acao.pontos,
                        modulo='rota_frete'
                    )

                rota.floresta_id =  None
                rota.fornecedor_id = fornecedor_id
                rota.cliente_id = cliente_id
                rota.transportadora_id = transportadora_id_final
                # Bitolas e preços de Eucalipto
                rota.euca_bitola_1_id=1
                rota.euca_bitola_2_id=2
                rota.euca_bitola_3_id=3
                rota.euca_bitola_4_id=4
                rota.euca_preco_custo_frete_bitola_1_100=euca_preco_custo_1_100
                rota.euca_preco_custo_frete_bitola_2_100=euca_preco_custo_2_100
                rota.euca_preco_custo_frete_bitola_3_100=euca_preco_custo_3_100
                rota.euca_preco_custo_frete_bitola_4_100=euca_preco_custo_4_100

                # Bitolas e preços de Pinus
                rota.pinus_bitola_1_id=1
                rota.pinus_bitola_2_id=2
                rota.pinus_bitola_3_id=3
                rota.pinus_bitola_4_id=4
                rota.pinus_bitola_5_id=6
                rota.pinus_preco_custo_frete_bitola_1_100=pinus_preco_custo_1_100
                rota.pinus_preco_custo_frete_bitola_2_100=pinus_preco_custo_2_100
                rota.pinus_preco_custo_frete_bitola_3_100=pinus_preco_custo_3_100
                rota.pinus_preco_custo_frete_bitola_4_100=pinus_preco_custo_4_100
                rota.pinus_preco_custo_frete_bitola_5_100=pinus_preco_custo_5_100

                rota.bio_bitola_5_id=5
                rota.bio_preco_custo_frete_bitola_5_100=bio_preco_custo_5_100

                rota.ativo = True

                db.session.commit()
                flash(("Rota de frete atualizada com sucesso!", "success"))
                return redirect(url_for("listar_rotas"))

        dados_corretos = {
            "tipoOrigem": "floresta" if rota.floresta_id else "fornecedor",
            "florestaIdentificacao": rota.floresta_id or "",
            "fornecedorIdentificacao": rota.fornecedor_id or "",
            "clienteDestino": rota.cliente_id,
            "transportadoraFrete": "todos" if rota.transportadora_id is None else rota.transportadora_id,
            "bioPrecoCusto5": rota.bio_preco_custo_frete_bitola_5_100,
            "eucaPrecoCusto1": rota.euca_preco_custo_frete_bitola_1_100,
            "eucaPrecoCusto2": rota.euca_preco_custo_frete_bitola_2_100,
            "eucaPrecoCusto3": rota.euca_preco_custo_frete_bitola_3_100,
            "eucaPrecoCusto4": rota.euca_preco_custo_frete_bitola_4_100,
            "pinusPrecoCusto1": rota.pinus_preco_custo_frete_bitola_1_100,
            "pinusPrecoCusto2": rota.pinus_preco_custo_frete_bitola_2_100,
            "pinusPrecoCusto3": rota.pinus_preco_custo_frete_bitola_3_100,
            "pinusPrecoCusto4": rota.pinus_preco_custo_frete_bitola_4_100,
            "pinusPrecoCusto5": rota.pinus_preco_custo_frete_bitola_5_100,
        }
    except Exception as e:
        flash(('Houve um erro ao tentar editar esta rota! Entre em contato com o suporte.', 'warning'))
        return redirect(url_for('editar_rota', id=id))

    return render_template(
        "parametros/rotas_frete/rota_editar.html",
        fornecedores=fornecedores,
        clientes=clientes,
        transportadoras=transportadoras,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=dados_corretos,
        rota=rota
    )

@app.route("/parametros/rotas/desativar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def desativar_rota(id):
    rota = RotaFreteModel.obter_rota_por_id(id)

    if rota is None:
        flash(('Rota de frente não encontrada!', 'warning'))
    rota.ativo = 0
    db.session.commit()
    flash(('Rota de frente desativada com sucesso!', 'success'))
    return redirect(url_for('listar_rotas'))

@app.route("/parametros/rotas/ativar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def ativar_rota(id):
    rota = RotaFreteModel.obter_rota_por_id(id)

    if rota is None:
        flash(('Rota de frente não encontrada!', 'warning'))
    rota.ativo = 1
    db.session.commit()
    flash(('Rota de frente ativada com sucesso!', 'success'))
    return redirect(url_for('listar_rotas'))


@app.route("/sincronizar/precos/frete", methods=["GET", "POST"])
@login_required
@requires_roles
def atualizar_precos_frete():
    try:
        from servidor_huey.tarefas import sincronizar_precos_transportadoras
        from datetime import datetime
        
        if request.method == 'POST':
            data_inicio = request.form.get('data_inicio')
            data_fim = request.form.get('data_fim')
            transportadora_id = request.form.get('transportadora_id')

            if not data_inicio or not data_fim:
                flash(("Por favor, informe o período para atualização dos valores de frete!", "warning"))
                return redirect(url_for("listagem_fretes_a_pagar"))
            
            try:
                data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
                
                if data_inicio_obj > data_fim_obj:
                    flash(("A data de início não pode ser maior que a data fim!", "warning"))
                    return redirect(url_for("listagem_fretes_a_pagar"))
                
            except ValueError:
                flash(("Formato de data inválido!", "warning"))
                return redirect(url_for("listagem_fretes_a_pagar"))
        else:
            return redirect(url_for("listagem_fretes_a_pagar"))

        # Converter transportadora_id para None se for "todos"
        transportadora_filtro = None if transportadora_id == "todos" else transportadora_id

        print(f"Filtro transportadora: {transportadora_filtro}")

        # Iniciar a tarefa assíncrona
        task = sincronizar_precos_transportadoras(data_inicio, data_fim, transportadora_id=transportadora_filtro)

        try:
            resultado = task(blocking=True, timeout=120) 

            if resultado['sucesso']:
                if resultado['sincronizados'] > 0:
                    flash((f"{resultado['sincronizados']} valores de frete sincronizados!", "success"))
                else:
                    flash((f"Todos os fretes no período informado já estão sincronizados", "warning"))
            else:
                flash(("Não foi possível atualizar os registros de frete no período informado", "warning"))
                
        except Exception as e:
            flash((f"Processo de atualização de fretes  pode levar alguns minutos para concluir.", "warning"))
            
        return redirect(url_for("listagem_fretes_a_pagar"))
        
    except Exception as e:
        flash(("Não foi possível iniciar a sincronização de fretes", "warning"))
        return redirect(url_for("listagem_fretes_a_pagar"))