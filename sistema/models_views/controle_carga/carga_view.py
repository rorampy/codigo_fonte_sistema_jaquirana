from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sistema.models_views.controle_carga.carga_model import CargaModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema.models_views.gerenciar.motorista.motorista_model import MotoristaModel
from sistema.models_views.gerenciar.motorista.transportadora_motorista_associado_model import TransportadoraMotoristaAssocModel
from sistema.models_views.gerenciar.veiculo.veiculo_model import VeiculoModel
from sistema.models_views.gerenciar.veiculo.veiculo_transportadora_veiculo_associado_model import TransportadoraVeiculoAssocModel
from sistema.models_views.controle_carga.produto_model import ProdutoModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.parametros.nome_grupo_whats.nome_grupo_whats_model import NomeGrupoWhatsModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.configuracoes_gerais.empresa_emissora.empresa_emissora_model import EmpresaEmissoraModel
from sistema.models_views.faturamento.cargas_a_pagar.transportadora.frete_a_pagar_model import FretePagarModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema._utilitarios import *


@app.route("/veiculo/<int:veiculo_id>/dados")
@login_required
@requires_roles
def buscar_dados_por_veiculo(veiculo_id):
    veiculo = VeiculoModel.obter_veiculo_por_id(veiculo_id)
    if not veiculo:
        return jsonify({"erro": "Veículo não encontrado"}), 404

    transpAssociadas = TransportadoraVeiculoAssocModel.obter_transportadoras_assoc_veiculo_id(veiculo_id)

    if transpAssociadas:
        transportadoras = [
            {
                "id": assoc.transportadora.id,
                "nome": assoc.transportadora.identificacao
            }
            for assoc in transpAssociadas
        ]
    elif veiculo.transportadora:
        transportadoras = [{
            "id": veiculo.transportadora.id,
            "nome": veiculo.transportadora.identificacao
        }]
    else:
        transportadoras = []

    ids_transportadoras = [t["id"] for t in transportadoras]

    motoristas = MotoristaModel.query.filter(
        MotoristaModel.transportadora_id.in_(ids_transportadoras),
        MotoristaModel.ativo == True,
        MotoristaModel.deletado == False
    ).all()

    return jsonify({
        "transportadoras": transportadoras,
        "motoristas": [{"id": m.id, "nome": m.nome_completo} for m in motoristas],
        "capacidade_carga": veiculo.capacidade_ton
    })

@app.route("/motorista/<int:transportadora_id>/dados")
@login_required
@requires_roles
def buscar_motoristas_por_transportadora(transportadora_id):
    motorista = TransportadoraMotoristaAssocModel.obter_motoristas_assoc_transportadora_id(transportadora_id)
    
    if not motorista:
        return jsonify({"erro": "Motorista não encontrado"}), 404
    return jsonify({
        "motoristas": [{"id": m.id, "nome": m.nome_completo} for m in motorista],
    })


@app.route("/controle-cargas/solicitacao/detalhes/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def detalhes_solicitacao(id):    
    solicitacao = CargaModel.obter_solicitacao_por_id(id)
    return render_template(
        "/controle_carga/solicitacao/solicitacao_detalhes.html",
        solicitacao=solicitacao
    )


@app.route("/controle-cargas/listar/solicitacoes/nf", methods=["GET", "POST"])
@login_required
@requires_roles
def listagem_solicitacoes():    
    if request.method == "POST":
        solicitacao = CargaModel.filtrar_solicitacoes(
            cliente_nome=request.form.get("cliente"),
            motorista_nome=request.form.get("motorista"),
            placa=request.form.get("placa"),
        )
    else:
        solicitacao = CargaModel.obter_solicitacoes_em_aberto_desc_id()
    return render_template(
        "/controle_carga/solicitacao/solicitacao_listar.html",
        solicitacao=solicitacao, dados_corretos=request.form
    )


@app.route("/controle-cargas/cadastrar/solicitacao", methods=["GET", "POST"])
@login_required
@requires_roles
def cadastrar_solicitacao():
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    cliente = ClienteModel.listar_clientes_ativos()
    empresas = EmpresaEmissoraModel.obter_empresas_emissoras_ativas()
    transportadora = TransportadoraModel.listar_transportadoras_ativas()
    veiculo = VeiculoModel.listar_veiculos_ativos()
    bitola = BitolaModel.listar_bitolas_ativas()
    produtos = ProdutoModel.listar_produtos()
    grupo_whats = NomeGrupoWhatsModel.listar_grupos_ativos()

    if request.method == "POST":
        empresaEmissora = request.form["empresaEmissora"]
        clienteSolicitacao = request.form["clienteSolicitacao"]
        bitolaSolicitacao = request.form["bitolaSolicitacao"]
        produtoSolicitacao = request.form["produtoSolicitacao"]
        transportadoraSolicitacao = request.form["transportadoraSolicitacao"]
        motoristaSolicitacao = request.form["motoristaSolicitacao"]
        placaVeiculo = request.form["placaVeiculo"]
        dataHoraSolicitacao = request.form["dataHoraSolicitacao"]
        nomeGrupo = request.form["nomeGrupo"]
        campos = {
            "empresaEmissora": ["Empresa Emissora", empresaEmissora],
            "clienteSolicitacao": ["Cliente", clienteSolicitacao],
            "bitolaSolicitacao": ["Bitola", bitolaSolicitacao],
            "produtoSolicitacao": ["Produto", produtoSolicitacao],
            "transportadoraSolicitacao": ["Transportadora", transportadoraSolicitacao],
            "motoristaSolicitacao": ["Motorista", motoristaSolicitacao],
            "placaVeiculo": ["Placa", placaVeiculo],
        }

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))

        if gravar_banco == True:
            try:
                CargaModel.cadastrar_solicitacao(
                    empresa_emissora_id=empresaEmissora,
                    cliente_id=clienteSolicitacao,
                    bitola_id=bitolaSolicitacao,
                    produto_id=produtoSolicitacao,
                    motorista_id=motoristaSolicitacao,
                    transportadora_id=transportadoraSolicitacao,
                    veiculo_id=placaVeiculo,
                    floresta_id=None,
                    fornecedor_id=None,
                    data_hora_msg_whats=(dataHoraSolicitacao if dataHoraSolicitacao != "" else None),
                    usuario_id=current_user.id,
                    grupo_whats_id=nomeGrupo if nomeGrupo else None,
                    nf_emitida=False,
                    cancelada=False,
                    ativo=True,
                )
                acao = TipoAcaoEnum.CADASTRO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    acao,
                    acao.pontos,
                    modulo='solicitacao_nf'
                )
                flash(("Solicitação cadastrada com sucesso!", "success"))
                return redirect(url_for("listagem_solicitacoes"))
            except Exception as e:
                db.session.rollback()
                flash((f"Erro ao cadastrar solicitação! Entre em contato com o suporte.", "error"))

    return render_template(
        "/controle_carga/solicitacao/solicitacao_cadastrar.html",
        produtos=produtos,
        veiculo=veiculo,
        empresas=empresas,
        grupo_whats=grupo_whats,
        cliente=cliente,
        transportadora=transportadora,
        bitola=bitola,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
    )

@app.route("/controle-cargas/editar/solicitacao/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_solicitacao(id):
    solicitacao = CargaModel.obter_solicitacao_por_id(id)

    if solicitacao is None:
        flash(("Solicitação não encontrada!", "warning"))
        return redirect(url_for("listagem_solicitacoes"))

    empresas = EmpresaEmissoraModel.obter_empresas_emissoras_ativas()
    cliente = ClienteModel.listar_clientes_ativos()
    transportadora = TransportadoraModel.listar_transportadoras_ativas()
    bitola = BitolaModel.listar_bitolas_ativas()
    produtos = ProdutoModel.listar_produtos()
    grupo_whats = NomeGrupoWhatsModel.listar_grupos_ativos()
    veiculos = VeiculoModel.listar_veiculos_ativos()
    campos_obrigatorios = {}

    if request.method == "POST":
        empresaEmissora = request.form["empresaEmissora"]
        clienteSolicitacao = request.form.get("clienteSolicitacao")
        bitolaSolicitacao = request.form.get("bitolaSolicitacao")
        produtoSolicitacao = request.form.get('produtoSolicitacao')
        transportadoraSolicitacao = request.form.get("transportadoraSolicitacao")
        motoristaSolicitacao = request.form.get("motoristaSolicitacao")
        placaVeiculo = request.form.get("placaVeiculo")
        nomeGrupo = request.form.get("nomeGrupo")
        dataHoraSolicitacao = request.form.get("dataHoraSolicitacao")


        campos = {
            "empresaEmissora": ["Empresa Emissora", empresaEmissora],
            "clienteSolicitacao": ["Cliente", clienteSolicitacao],
            "bitolaSolicitacao": ["Bitola", bitolaSolicitacao],
            "produtoSolicitacao": ["Produto", produtoSolicitacao],
            "transportadoraSolicitacao": ["Transportadora", transportadoraSolicitacao],
            "motoristaSolicitacao": ["Motorista", motoristaSolicitacao],
            "placaVeiculo": ["Placa", placaVeiculo],
        }

        campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if "validado" in campos_obrigatorios:

            obj1 = {
                "empresaEmissora": str(solicitacao.empresa_emissora_id),
                "clienteSolicitacao": str(solicitacao.cliente_id),
                "bitolaSolicitacao": str(solicitacao.bitola_id),
                "produtoSolicitacao": str(solicitacao.produto_id),
                "motoristaSolicitacao": str(solicitacao.motorista_id),
                "placaVeiculo": str(solicitacao.veiculo_id),
                "nomeGrupo": str(solicitacao.grupo_whats_id) if solicitacao.grupo_whats_id else "",
                "dataHoraSolicitacao": str(solicitacao.data_hora_msg_whats) if solicitacao.data_hora_msg_whats else "",
            }

            obj2 = {
                "empresaEmissora": empresaEmissora,
                "clienteSolicitacao": clienteSolicitacao,
                "bitolaSolicitacao": bitolaSolicitacao,
                "produtoSolicitacao": produtoSolicitacao,
                "motoristaSolicitacao": motoristaSolicitacao,
                "placaVeiculo": placaVeiculo,
                "nomeGrupo": nomeGrupo if nomeGrupo else "",
                "dataHoraSolicitacao": dataHoraSolicitacao if dataHoraSolicitacao else "",
            }

            diferencas = Gameficacao.compara_objetos(obj1, obj2)
            if diferencas:
                acao = TipoAcaoEnum.EDICAO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    acao,
                    acao.pontos,
                    modulo='solicitacao_nf'
                )


            # Verifica se possui frete a pagar
            frete = FretePagarModel.obter_frete_por_solicitacao_id(solicitacao.id)
            if frete:
                frete.transportadora_id = transportadoraSolicitacao
                frete.bitola_id = bitolaSolicitacao
                
            
            solicitacao.empresa_emissora_id = empresaEmissora
            solicitacao.cliente_id = clienteSolicitacao
            solicitacao.bitola_id = bitolaSolicitacao
            solicitacao.produto_id = produtoSolicitacao
            solicitacao.motorista_id = motoristaSolicitacao
            solicitacao.veiculo_id = placaVeiculo
            solicitacao.transportadora_id = transportadoraSolicitacao
            solicitacao.grupo_whats_id = nomeGrupo if nomeGrupo else None
            solicitacao.data_hora_msg_whats = (dataHoraSolicitacao if dataHoraSolicitacao != "" else None)
            solicitacao.usuario_id = current_user.id

            db.session.commit()
            flash(("Solicitação editada com sucesso!", "success"))
            return redirect(url_for("listagem_solicitacoes"))
        else:
            flash(("Verifique os campos destacados em vermelho!", "warning"))

    dados_corretos = {
        "clienteSolicitacao": solicitacao.cliente_id,
        "bitolaSolicitacao": solicitacao.bitola_id,
        "produtoSolicitacao": solicitacao.produto_id,
        "transportadoraSolicitacao": solicitacao.transportadora_id,
        "motoristaSolicitacao": solicitacao.motorista_id,
        "placaVeiculo": solicitacao.veiculo_id,
        "nomeGrupo": solicitacao.grupo_whats_id,
        "dataHoraSolicitacao": solicitacao.data_hora_msg_whats,
    }

    return render_template(
        "/controle_carga/solicitacao/solicitacao_editar.html",
        solicitacao=solicitacao,
        empresas=empresas,
        produtos=produtos,
        cliente=cliente,
        transportadora=transportadora,
        bitola=bitola,
        grupo_whats=grupo_whats,
        veiculos=veiculos,
        campos_obrigatorios=campos_obrigatorios,
        campos_erros={},
        dados_corretos=dados_corretos,
    )


@app.route("/controle-cargas/lancar/solicitacao/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def lancar_solicitacao(id):
    solicitacao = CargaModel.obter_solicitacao_por_id(id)

    if solicitacao is None:
        flash(("Solicitação não encontrada!", "warning"))
        return redirect(url_for("listagem_solicitacoes"))


@app.route("/controle-cargas/cancelar/solicitacao/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def cancelar_solicitacao(id):
    solicitacao = CargaModel.obter_solicitacao_por_id(id)

    if solicitacao is None:
        flash(("Solicitação não encontrada!", "warning"))
    solicitacao.cancelada = True
    solicitacao.ativo = False
    db.session.commit()
    flash(("Solicitação cancelada com sucesso!", "success"))
    return redirect(url_for("listagem_solicitacoes"))


@app.route("/controle-cargas/relatorio/solicitacao-lancamento/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def relatorio_solicitacoes_lancamentos(id):
    dataHoje = DataHora.obter_data_atual_padrao_br()
    carga = CargaModel.obter_solicitacao_por_id(id)
    cargas_relacionadas = CargaModel.listar_cargas()
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()

    logo_path = obter_url_absoluta_de_imagem('logo.png')
    html =  render_template(
        "relatorios/relatorio_solicitacao/relatorio_solicitacao_lancamento.html",logo_path=logo_path, dataHoje=dataHoje,
                                                                    carga=carga,
                                                                    changelog=changelog, cargas_relacionadas=cargas_relacionadas)

    nome_arquivo_saida = f'solicitacao-{dataHoje}'
    resposta = ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida)

    return resposta