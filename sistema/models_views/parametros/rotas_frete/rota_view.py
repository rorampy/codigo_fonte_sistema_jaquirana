from sistema import app, requires_roles, db, current_user
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from sistema.models_views.gerenciar.floresta.floresta_model import FlorestaModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_cadastro_model import FornecedorCadastroModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema.models_views.parametros.rotas_frete.rota_model import RotaFreteModel
from sistema.models_views.parametros.rotas_frete.rota_frete_preco_bitola_model import RotaFretePrecoBitolaModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.parametros.produto_bitola.produto_bitola_model import ProdutoBitolaModel
from sistema._utilitarios import *


@app.route("/parametros/rotas/cadastrar", methods=["GET", "POST"])
@login_required
@requires_roles
def cadastrar_rota():
    try:
        fornecedores = FornecedorCadastroModel.listar_fornecedores_ativos()
        clientes = ClienteModel.listar_clientes_ativos()
        transportadoras = TransportadoraModel.listar_transportadoras_ativas()
        
        produtos_bitolas = ProdutoBitolaModel.obter_produtos_com_bitolas()

        validacao_campos_obrigatorios = {}
        validacao_campos_erros = {}
        gravar_banco = True

        if request.method == "POST":
            fornecedorIdentificacao = request.form["fornecedorIdentificacao"]
            clienteDestino = request.form["clienteDestino"]
            transportadoraFrete = request.form["transportadoraFrete"]
            
            precos_frete_dados = {}
            for produto_id, produto_data in produtos_bitolas.items():
                produto_name = produto_data['nome']
                bitolas = produto_data['bitolas']
                
                if produto_name.lower() == 'eucalipto':
                    prefix = 'euca'
                elif produto_name.lower() == 'pinus':
                    prefix = 'pinus'
                elif produto_name.lower() == 'biomassa':
                    prefix = 'bio'
                else:
                    prefix = produto_name.lower()[:5]
                    
                for idx, bitola in enumerate(bitolas, 1):
                    campo_nome = f"{prefix}PrecoCusto{idx}"
                    valor = request.form.get(campo_nome, "0")
                    precos_frete_dados[campo_nome] = {
                        'produto_id': produto_id,
                        'bitola_id': bitola['id'],
                        'valor': valor
                    }
            
            transportadora_id_final = None if transportadoraFrete == "todos" or not transportadoraFrete else int(transportadoraFrete)
            
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
                query = RotaFreteModel.query.filter_by(
                    cliente_id=clienteDestino,
                    transportadora_id=transportadora_id_final
                )

                query = query.filter_by(fornecedor_id=fornecedorIdentificacao)

                if query.first():
                    gravar_banco = False
                    flash(("Já existe um registro com estas especificações!", "warning"))
            

            if gravar_banco:
                precos_frete_convertidos = {}
                for campo_nome, dados in precos_frete_dados.items():
                    valor_float = ValoresMonetarios.converter_string_brl_para_float(dados['valor'])
                    valor_100 = int(valor_float * 100)
                    precos_frete_convertidos[campo_nome] = {
                        'produto_id': dados['produto_id'],
                        'bitola_id': dados['bitola_id'],
                        'valor_100': valor_100
                    }

                rota = RotaFreteModel(
                    floresta_id=None,
                    fornecedor_id=int(fornecedorIdentificacao),
                    cliente_id=int(clienteDestino),
                    transportadora_id=transportadora_id_final,
                    ativo=True
                )
                db.session.add(rota)
                db.session.flush()
                
                for campo_nome, dados in precos_frete_convertidos.items():
                    preco_frete = RotaFretePrecoBitolaModel(
                        rota_frete_id=rota.id,
                        produto_id=dados['produto_id'],
                        bitola_id=dados['bitola_id'],
                        preco_frete_100=dados['valor_100']
                    )
                    db.session.add(preco_frete)
                
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
        produtos_bitolas=produtos_bitolas,
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

        fornecedores = FornecedorCadastroModel.listar_fornecedores_ativos()
        clientes = ClienteModel.listar_clientes_ativos()
        transportadoras = TransportadoraModel.listar_transportadoras_ativas()
        
        produtos_bitolas = ProdutoBitolaModel.obter_produtos_com_bitolas()
        
        precos_frete = RotaFretePrecoBitolaModel.listar_precos_rota(rota.id)
        
        precos_dict = {}
        for preco in precos_frete:
            key = f"produto_{preco.produto_id}_bitola_{preco.bitola_id}"
            precos_dict[key] = preco.preco_frete_100 or 0

        validacao_campos_obrigatorios = {}
        validacao_campos_erros = {}
        gravar_banco = True

        if request.method == "POST":
            floresta_id = request.form.get("florestaIdentificacao")
            fornecedor_id = request.form.get("fornecedorIdentificacao")
            cliente_id = request.form.get("clienteDestino")
            transportadora_id = request.form.get("transportadoraFrete")
            
            transportadora_id_final = None if transportadora_id == "todos" or not transportadora_id else int(transportadora_id)
            
            precos_frete_dados = {}
            for produto_id, produto_data in produtos_bitolas.items():
                produto_name = produto_data['nome']
                bitolas = produto_data['bitolas']
                
                if produto_name.lower() == 'eucalipto':
                    prefix = 'euca'
                elif produto_name.lower() == 'pinus':
                    prefix = 'pinus'
                elif produto_name.lower() == 'biomassa':
                    prefix = 'bio'
                else:
                    prefix = produto_name.lower()[:5]
                    
                for idx, bitola in enumerate(bitolas, 1):
                    campo_nome = f"{prefix}PrecoCusto{idx}"
                    valor = request.form.get(campo_nome, "0")
                    precos_frete_dados[campo_nome] = {
                        'produto_id': produto_id,
                        'bitola_id': bitola['id'],
                        'valor': valor
                    }

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
                precos_frete_convertidos = {}
                for campo_nome, dados in precos_frete_dados.items():
                    valor_float = ValoresMonetarios.converter_string_brl_para_float(dados['valor'])
                    valor_100 = int(valor_float * 100)
                    precos_frete_convertidos[campo_nome] = {
                        'produto_id': dados['produto_id'],
                        'bitola_id': dados['bitola_id'],
                        'valor_100': valor_100
                    }

                obj1 = {
                    "fornecedorIdentificacao": str(rota.fornecedor_id or ""),
                    "clienteDestino": str(rota.cliente_id or ""),
                    "transportadoraFrete": "todos" if rota.transportadora_id is None else str(rota.transportadora_id or ""),
                }
                
                for preco in precos_frete:
                    produto_nome = preco.produto.nome.lower()
                    if produto_nome == 'eucalipto':
                        prefix = 'euca'
                    elif produto_nome == 'pinus':
                        prefix = 'pinus'
                    elif produto_nome == 'biomassa':
                        prefix = 'bio'
                    else:
                        prefix = produto_nome[:5]
                    
                    bitola_idx = 1
                    for idx, b in enumerate(produtos_bitolas[preco.produto_id]['bitolas'], 1):
                        if b['id'] == preco.bitola_id:
                            bitola_idx = idx
                            break
                    
                    campo_nome = f"{prefix}PrecoCusto{bitola_idx}"
                    obj1[campo_nome] = preco.preco_frete_100

                obj2 = {
                    "fornecedorIdentificacao": str(fornecedor_id or ""),
                    "clienteDestino": str(cliente_id or ""),
                    "transportadoraFrete": "todos" if transportadora_id_final is None else str(transportadora_id_final or ""),
                }
                
                for campo_nome, dados in precos_frete_convertidos.items():
                    obj2[campo_nome] = dados['valor_100']

                diferencas = Gameficacao.compara_objetos(obj1, obj2)
                if diferencas:
                    acao = TipoAcaoEnum.EDICAO
                    PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                        current_user.id,
                        acao,
                        acao.pontos,
                        modulo='rota_frete'
                    )

                rota.floresta_id = None
                rota.fornecedor_id = int(fornecedor_id)
                rota.cliente_id = int(cliente_id)
                rota.transportadora_id = transportadora_id_final
                rota.ativo = True
                
                for preco_antigo in precos_frete:
                    preco_antigo.ativo = False
                
                for campo_nome, dados in precos_frete_convertidos.items():
                    preco_frete = RotaFretePrecoBitolaModel(
                        rota_frete_id=rota.id,
                        produto_id=dados['produto_id'],
                        bitola_id=dados['bitola_id'],
                        preco_frete_100=dados['valor_100']
                    )
                    db.session.add(preco_frete)

                db.session.commit()
                flash(("Rota de frete atualizada com sucesso!", "success"))
                return redirect(url_for("listar_rotas"))

        dados_corretos = {
            "tipoOrigem": "floresta" if rota.floresta_id else "fornecedor",
            "florestaIdentificacao": rota.floresta_id or "",
            "fornecedorIdentificacao": rota.fornecedor_id or "",
            "clienteDestino": rota.cliente_id,
            "transportadoraFrete": "todos" if rota.transportadora_id is None else rota.transportadora_id,
        }
        
        for produto_id, produto_data in produtos_bitolas.items():
            produto_name = produto_data['nome']
            bitolas = produto_data['bitolas']
            
            if produto_name.lower() == 'eucalipto':
                prefix = 'euca'
            elif produto_name.lower() == 'pinus':
                prefix = 'pinus'
            elif produto_name.lower() == 'biomassa':
                prefix = 'bio'
            else:
                prefix = produto_name.lower()[:5]
                
            for idx, bitola in enumerate(bitolas, 1):
                campo_nome = f"{prefix}PrecoCusto{idx}"
                chave_dict = f'produto_{produto_id}_bitola_{bitola["id"]}'
                dados_corretos[campo_nome] = precos_dict.get(chave_dict, 0)
                
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
        rota=rota,
        produtos_bitolas=produtos_bitolas
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

        transportadora_filtro = None if transportadora_id == "todos" else transportadora_id


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