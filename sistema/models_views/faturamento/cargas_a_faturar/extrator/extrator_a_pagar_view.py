from datetime import datetime
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem
from flask import render_template, request, redirect, url_for, flash, session, jsonify, json
from flask_login import login_required, current_user
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.faturamento.cargas_a_faturar.extrator.extrator_a_pagar_model import ExtratorPagarModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
from sistema.models_views.configuracoes_gerais.situacao_pagamento.situacao_pagamento_model import SituacaoPagamentoModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.upload_arquivo.upload_arquivo_model import UploadArquivoModel
from sistema.models_views.faturamento.controle_credito.credito_agrupado.credito_extrator_model import CreditoExtratorModel
from sistema.models_views.faturamento.controle_credito.extrato_credito.extrato_credito_extrator_model import ExtratoCreditoExtratorModel
from sistema.models_views.financeiro.movimentacao_financeira.movimentacao_financeira_model import MovimentacaoFinanceiraModel
from sistema.models_views.financeiro.movimentacao_financeira.saldo_movimentacao_financeira_model import SaldoMovimentacaoFinanceiraModel
from sistema.models_views.configuracoes_gerais.conta_bancaria.conta_bancaria_model import ContaBancariaModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_view import (inicializar_categorias_padrao, obter_subcategorias_recursivo)
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_view import (inicializar_categorias_padrao_categorizacao_fiscal, obter_subcategorias_recursivo_categorizacao_fiscal)
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_model import CategorizacaoFiscalModel
from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx
from sistema.models_views.importacao_ofx.importacao_ofx_view import limpar_dados_conciliacao
from sistema.models_views.importacao_ofx.importacao_ofx_view import verificar_e_limpar_conciliacao_incorreta
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
from sistema._utilitarios import *
from sistema._utilitarios.utilitario_semanal import UtilitariosSemana


@app.route("/financeiro/extratores-a-pagar", methods=["GET"])
@login_required
@requires_roles
def listagem_extratores_a_pagar():
    from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
    from sistema.models_views.gerenciar.fornecedor.fornecedor_cadastro_model import FornecedorCadastroModel
    from sistema.models_views.gerenciar.motorista.motorista_model import MotoristaModel
    from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
    from sistema.models_views.gerenciar.extrator.extrator_model import ExtratorModel
    
    bitolas = BitolaModel.listar_bitolas_ativas()
    produtos = ProdutoModel.listar_produtos()
    statusPagamentos = SituacaoPagamentoModel.listar_status_filtro()
    transportadoras = TransportadoraModel.listar_transportadoras_ativas()
    fornecedores = FornecedorCadastroModel.listar_fornecedores_ativos()
    motoristas = MotoristaModel.listar_motoristas_ativos()
    clientes = ClienteModel.listar_clientes_ativos()
    extratores = ExtratorModel.listar_extratores_ativos()

    verificar_e_limpar_conciliacao_incorreta('pagamento_extrator') 

    # Recuperar dados de conciliação da sessão
    dados_conciliacao = session.get('dados_conciliacao', {})
    
    # Extrair dados para o template
    conciliar_transacao_id = dados_conciliacao.get('transacao_id')
    valor_conciliar = dados_conciliacao.get('valor')
    data_conciliar = dados_conciliacao.get('data')
    descricao_conciliar = dados_conciliacao.get('descricao')
    fitid_conciliar = dados_conciliacao.get('fitid')

    # Obter semanas disponíveis
    semanas_disponiveis = UtilitariosSemana.obter_semanas_do_mes_atual()
    valor_padrao_semana = None
    
    if semanas_disponiveis:
        valor_padrao_semana = semanas_disponiveis[0]["valor"]

    parametros_filtro = ["tipo_filtro", "semanaSelecionada", "dataInicio", "dataFim", "numeroNF", "placaCarga", "motoristaCarga",
                        "produtoCarga", "bitolaCarga", "extratorCarga", "fornecedorCarga", 
                        "clienteCarga", "statusPagamentoCarga"]
    
    tem_filtros = any(request.args.get(param) for param in parametros_filtro)

    if tem_filtros:
        tipo_filtro = request.args.get("tipo_filtro", "semanal")
        semana_selecionada = request.args.get("semanaSelecionada")
        data_inicio_form = request.args.get("dataInicio")
        data_fim_form = request.args.get("dataFim")
        numero_nf = request.args.get("numeroNF")
        placa = request.args.get("placaCarga")
        motorista = request.args.get("motoristaCarga")
        produto = request.args.get("produtoCarga")
        bitola = request.args.get("bitolaCarga")
        extrator = request.args.get("extratorCarga")
        fornecedor = request.args.get("fornecedorCarga")
        cliente = request.args.get("clienteCarga")
        statusPagamento = request.args.get("statusPagamentoCarga")

        # Determinar data_inicio e data_fim baseado no tipo de filtro
        if tipo_filtro == "data" and data_inicio_form and data_fim_form:
            from datetime import datetime
            data_inicio = datetime.strptime(data_inicio_form, "%Y-%m-%d").date()
            data_fim = datetime.strptime(data_fim_form, "%Y-%m-%d").date()
        else:
            # Usar filtro semanal
            data_inicio, data_fim = UtilitariosSemana.processar_semana_selecionada(
                semana_selecionada or valor_padrao_semana
            )

        registros = ExtratorPagarModel.filtrar_extratores_agrupados(
            data_inicio=data_inicio,
            data_fim=data_fim,
            numero_nf=numero_nf,
            placa=placa,
            motorista=motorista,
            produto=produto,
            bitola=bitola,
            extrator=extrator,
            fornecedor=fornecedor,
            cliente=cliente,
            statusPagamento=statusPagamento,
        )
        
        # for registro_dict in registros:
        #     registro = registro_dict.get('registro')
        #     faturamento_codigo = FaturamentoModel.buscar_faturamento_origem_por_carga_pagar_id(registro.id, 'extrator')
        #     registro_dict['cod_faturamento'] = faturamento_codigo
    else:
        registros = ExtratorPagarModel.obter_extratores_agrupados()
        # for registro_dict in registros:
        #     registro = registro_dict.get('registro')
        #     faturamento_codigo = FaturamentoModel.buscar_faturamento_origem_por_carga_pagar_id(registro.id, 'extrator')
        #     registro_dict['cod_faturamento'] = faturamento_codigo
        
    return render_template(
        "/financeiro/extrator_a_pagar_listagem.html",
        registros=registros,
        bitolas=bitolas,
        produtos=produtos,
        statusPagamentos=statusPagamentos,
        transportadoras=transportadoras,
        fornecedores=fornecedores,
        motoristas=motoristas,
        clientes=clientes,
        extratores=extratores,
        dados_corretos=request.args,
        semanas_disponiveis=semanas_disponiveis,
        tipo_filtro=request.args.get("tipo_filtro", "semanal"),
        conciliar_transacao_id=conciliar_transacao_id,
        valor_conciliar=valor_conciliar,
        data_conciliar=data_conciliar,
        descricao_conciliar=descricao_conciliar,
        fitid_conciliar=fitid_conciliar
    )

@app.route("/financeiro/a-pagar/extrator-a-pagar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def extrator_a_pagar(id):
    try:
        campos_obrigatorios = {}
        campos_erros = {}
        gravar_banco = True

        verificar_e_limpar_conciliacao_incorreta('pagamento_extrator') 

        dados_conciliacao = session.get('dados_conciliacao', {})
        conciliar_transacao_id = dados_conciliacao.get('transacao_id')

        registro = ExtratorPagarModel.obter_extrator_a_pagar_id(id)
        if not registro:
            flash(("Registro não encontrado", "warning"))
            return redirect(url_for("listagem_extratores_a_pagar"))

        if registro.valor_total_a_pagar_100 == None:
            flash(("Não é possível informar faturamento de valor nulo", "warning"))
            return redirect(url_for("listagem_extratores_a_pagar"))
        if registro.situacao_pagamento_id == 5:
            flash(("Registro já consta como faturado!", "warning"))
            return redirect(url_for("listagem_extratores_a_pagar"))

        saldo_credito = CreditoExtratorModel.obtem_registro_extrator_id(registro.obter_extrator_id())
        credito_disponivel = (
            saldo_credito.valor_total_credito_100 if saldo_credito else 0
        )

        creditos_individuais = ExtratoCreditoExtratorModel.obter_creditos_disponiveis_extrator(
            registro.obter_extrator_id()
        )

        registro_oper = RegistroOperacionalModel.obter_registro_solicitacao_por_id(
            registro.solicitacao_id
        )
        if not registro_oper:
            flash(("Registro operacional não encontrado", "warning"))
            return redirect(url_for("listagem_extratores_a_pagar"))
        
        transacao_ofx = None
        if conciliar_transacao_id:
            transacao_ofx = ImportacaoOfx.query.get(conciliar_transacao_id)

        if request.method == "POST":
            valor_total_calculado = request.form.get("valor_total_calculado", "")
            preco_custo_atualizado = request.form.get("preco_custo_atualizado", "")

            if preco_custo_atualizado:
                try:
                    preco_custo_float = float(preco_custo_atualizado)
                    registro.preco_custo_bitola_100 = preco_custo_float * 100
                except (ValueError, TypeError) as e:
                    flash(("Erro no formato do preço custo! Entre em contato com o suporte.", "warning"))
                    return redirect(request.url)

            if valor_total_calculado:
                try:
                    valor_total_float = float(valor_total_calculado)
                    registro.valor_total_a_pagar_100 = valor_total_float * 100
                except (ValueError, TypeError) as e:
                    flash(("Erro no formato do valor total! Entre em contato com o suporte.", "warning"))
                    return redirect(request.url)

            usar_credito = request.form.get("usar_credito")
            
            print(usar_credito)

            creditos_selecionados_json = request.form.get("creditos_selecionados", "{}")
            try:
                creditos_selecionados = json.loads(creditos_selecionados_json) if creditos_selecionados_json else {}
            except json.JSONDecodeError:
                creditos_selecionados = {}

            valor_pendente = registro.valor_total_a_pagar_100

            detalhes_creditos_utilizados = []
            total_credito_aplicado = 0

            if usar_credito == "sim":
                total_creditos_selecionados = 0
                
                if 'extrator' in creditos_selecionados:
                    for extrator_id_str, credito_ids in creditos_selecionados['extrator'].items():
                        if int(extrator_id_str) == registro.obter_extrator_id():
                            for credito_id in credito_ids:
                                credito = ExtratoCreditoExtratorModel.query.get(credito_id)
                                if credito:
                                    total_creditos_selecionados += credito.valor_credito_100
                
                if not creditos_selecionados or 'extrator' not in creditos_selecionados:
                    flash(("Nenhum crédito selecionado para aplicar!", "warning"))
                    gravar_banco = False
                if total_creditos_selecionados == 0:
                    flash(("Não Há créditos disponíveis para usar!", "warning"))
                    gravar_banco = False
                else:
                    credito_restante_para_usar = valor_pendente
                    
                    if 'extrator' in creditos_selecionados:
                        for extrator_id_str, credito_ids in creditos_selecionados['extrator'].items():
                            if int(extrator_id_str) == registro.obter_extrator_id():
                                
                                for credito_id in credito_ids:
                                    if credito_restante_para_usar <= 0:
                                        break
                                        
                                    credito_individual = ExtratoCreditoExtratorModel.query.filter_by(id=credito_id, ativo=True, credito_utilizado=False).first()
                                    if credito_individual:  # Permite tanto créditos quanto débitos
                                        
                                        # Calcular quanto deste crédito será realmente utilizado para permitir uso parcial
                                        valor_credito_a_usar = min(abs(credito_individual.valor_credito_100), credito_restante_para_usar)
                                        if credito_individual.valor_credito_100 < 0:
                                            valor_credito_a_usar = -valor_credito_a_usar  # Manter sinal negativo para débitos

                                        credito_individual.credito_utilizado = True
                                        db.session.add(credito_individual)
                                        
                                        # Se há uso parcial, criar registro para o valor restante
                                        if abs(valor_credito_a_usar) < abs(credito_individual.valor_credito_100):
                                            valor_restante = credito_individual.valor_credito_100 - valor_credito_a_usar
                                            
                                            credito_restante = ExtratoCreditoExtratorModel(
                                                tipo_movimentacao=1,  # Entrada
                                                descricao=f"Crédito restante após uso parcial individual - Original: {credito_individual.descricao}",
                                                data_movimentacao=datetime.now(),
                                                extrator_id=registro.obter_extrator_id(),
                                                valor_credito_100=valor_restante,
                                                usuario_id=current_user.id,
                                                ativo=True
                                            )
                                            db.session.add(credito_restante)
                                        
                                        # Atualizar credito restante para usar
                                        credito_restante_para_usar -= abs(valor_credito_a_usar)
                                        
                                        # Criar extrato com o valor que será utilizado (permite créditos negativos)
                                        tipo_mov = 2 if valor_credito_a_usar > 0 else 1  # Saída para crédito positivo, Entrada para débito
                                        descricao_mov = f"{'Débito' if valor_credito_a_usar > 0 else 'Crédito'} {credito_individual.descricao} para faturamento individual."
                                        extrato_extrator = ExtratoCreditoExtratorModel(
                                            tipo_movimentacao=tipo_mov,
                                            descricao=descricao_mov,
                                            data_movimentacao=datetime.now(),
                                            extrator_id=registro.obter_extrator_id(),
                                            valor_credito_100=abs(valor_credito_a_usar),  # Sempre positivo no extrato
                                            usuario_id=current_user.id,
                                            ativo=True,
                                            credito_utilizado=True,
                                        )
                                        db.session.add(extrato_extrator)
                                        
                                        if saldo_credito:
                                            saldo_atual_extrator = saldo_credito.valor_total_credito_100 or 0
                                            saldo_credito.valor_total_credito_100 = saldo_atual_extrator - valor_credito_a_usar
                                        
                                        detalhes_creditos_utilizados.append({
                                            'credito_id': credito_id,
                                            'extrator_id': registro.obter_extrator_id(),
                                            'valor': valor_credito_a_usar,
                                            'valor_original': credito_individual.valor_credito_100,
                                            'descricao': credito_individual.descricao,
                                            'data_movimentacao': credito_individual.data_movimentacao.strftime('%Y-%m-%d'),
                                            'uso_parcial': abs(valor_credito_a_usar) < abs(credito_individual.valor_credito_100)
                                        })
                                        
                                        total_credito_aplicado += valor_credito_a_usar

                    if total_credito_aplicado != 0:  # Permite tanto créditos positivos quanto negativos
                        registro.utiliza_credito = 1
                        registro.valor_credito_100 = total_credito_aplicado
                    else:
                        registro.utiliza_credito = 0
                        registro.valor_credito_100 = 0
            else:
                registro.utiliza_credito = 0
                registro.valor_credito_100 = 0

            if gravar_banco:
                registro.situacao_pagamento_id = 5

                valor_bruto = registro.valor_total_a_pagar_100 or 0
                valor_credito = registro.valor_credito_100 or 0
                valor_liquido = max(0, valor_bruto - valor_credito)

                novo_faturamento = FaturamentoModel(
                    usuario_id=current_user.id,
                    codigo_faturamento=FaturamentoModel.gerar_codigo_novo_faturamento(),
                    valor_total=valor_liquido,
                    ids_fornecedores=None,
                    ids_extratores=str(registro.id),
                    utilizou_credito=(usar_credito == "sim"),
                    situacao_pagamento_id=7,
                    tipo_operacao=1,
                    direcao_financeira=2
                )
                
                if hasattr(novo_faturamento, 'valor_bruto_total'):
                    novo_faturamento.valor_bruto_total = valor_bruto
                if hasattr(novo_faturamento, 'valor_credito_aplicado'):
                    novo_faturamento.valor_credito_aplicado = valor_credito
                if hasattr(novo_faturamento, 'valor_fornecedor'):
                    novo_faturamento.valor_fornecedor = None
                if hasattr(novo_faturamento, 'valor_extrator'):
                    novo_faturamento.valor_extrator = valor_bruto

                valor_bruto_registro = registro.valor_total_a_pagar_100 or 0
                valor_credito_registro = registro.valor_credito_100 or 0
                valor_faturado = max(0, valor_bruto_registro - valor_credito_registro)
                preco_custo_registro = registro.preco_custo_bitola_100 or 0

                numero_nf = ""
                if registro_oper:
                    if registro_oper.estorno_nf and registro_oper.numero_nota_fiscal_estorno:
                        numero_nf = f"{registro_oper.numero_nota_fiscal_estorno} *"
                    elif registro_oper.numero_nota_fiscal:
                        numero_nf = registro_oper.numero_nota_fiscal

                detalhes_extratores = [{
                    "extrator_a_pagar_id": registro.id,
                    "extrator_id": registro.obter_extrator_id(),
                    "solicitacao_id": registro.solicitacao_id if registro.solicitacao else "",
                    "extrator_identificacao": registro.obter_extrator().identificacao if registro.obter_extrator() else str(registro.obter_extrator_id() or ""),
                    "cliente": registro.solicitacao.cliente.identificacao if registro.solicitacao and registro.solicitacao.cliente else "",
                    "valor_bruto": valor_bruto_registro,
                    "valor_credito": valor_credito_registro,
                    "valor_faturado": valor_faturado,
                    "nota_fiscal": numero_nf,
                    "peso_ticket": f"{registro_oper.peso_liquido_ticket}" if registro_oper and registro_oper.peso_liquido_ticket else "",
                    "preco_custo": preco_custo_registro,
                    "produto": registro.solicitacao.produto.nome if registro.solicitacao and registro.solicitacao.produto else "",
                    "bitola": registro.solicitacao.bitola.bitola if registro.solicitacao and registro.solicitacao.bitola else "",
                    "data_entrega": registro.data_entrega_ticket.strftime('%d/%m/%Y') if registro.data_entrega_ticket else "",
                    "utiliza_credito": registro.utiliza_credito or 0,
                    "registro_operacional_id": registro_oper.id if registro_oper else "",
                    "placa_veiculo": registro.solicitacao.veiculo.placa_veiculo if registro.solicitacao and registro.solicitacao.veiculo else "",
                    "motorista": registro.solicitacao.motorista.nome_completo if registro.solicitacao and registro.solicitacao.motorista else "",
                    "transportadora_id": registro_oper.solicitacao.transportadora_id if registro_oper.solicitacao else "",
                    "transportadora_identificacao": registro_oper.solicitacao.transportadora_exibicao.identificacao if registro_oper.solicitacao else "",
                    "fornecedor_id": registro_oper.solicitacao.fornecedor_id if registro_oper.solicitacao else "",
                    "fornecedor_identificacao": registro_oper.solicitacao.fornecedor.identificacao if registro_oper.solicitacao and registro_oper.solicitacao.fornecedor else ""
                }]

                novo_faturamento.salvar_detalhes(
                    fornecedores=[], 
                    transportadoras=[],
                    extratores=detalhes_extratores,
                    credito_fornecedor=[],
                    credito_transportadora=[],
                    credito_extrator=detalhes_creditos_utilizados
                )

                db.session.add(novo_faturamento)

                if transacao_ofx and not transacao_ofx.conciliado:
                    transacao_ofx.conciliado = True
                    transacao_ofx.tipo_conciliacao = 'faturamento_extrator'
                    transacao_ofx.pagamento_id = registro.id
                    transacao_ofx.data_conciliacao = datetime.now()
                    transacao_ofx.usuario_conciliacao_id = current_user.id
                    transacao_ofx.observacoes_conciliacao = f"Conciliado com faturamento de extrator ID {registro.id}"

                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    TipoAcaoEnum.CADASTRO,
                    TipoAcaoEnum.CADASTRO.pontos,
                    modulo="informar_faturamento_extrator",
                )

                db.session.commit()
                if conciliar_transacao_id:
                    limpar_dados_conciliacao()
                    flash(("Faturamento informado e transação OFX conciliada com sucesso!", "success"))
                    return redirect(url_for("listagem_ofx"))
                else:
                    flash(("Faturamento informado com sucesso!", "success"))
                    return redirect(url_for("listagem_extratores_a_pagar"))

        # Obter o extrator para passar ao template
        extrator = registro.obter_extrator()
        extrator_id = registro.obter_extrator_id()

        return render_template(
            "/financeiro/informar_pagamento/informar_pagamento_extrator.html",
            campos_obrigatorios=campos_obrigatorios,
            campos_erros=campos_erros,
            dados_corretos=request.form,
            registro=registro,
            registro_operacional=registro_oper,
            extrator=extrator,
            extrator_id=extrator_id,
            saldo_credito=credito_disponivel,
            creditos_individuais=creditos_individuais,
            conciliar_transacao_id=conciliar_transacao_id,
            valor_conciliar=dados_conciliacao.get('valor'),
            data_conciliar=dados_conciliacao.get('data'),
            descricao_conciliar=dados_conciliacao.get('descricao'),
            fitid_conciliar=dados_conciliacao.get('fitid')
        )

    except Exception as e:
        print("[ERROR extrator_a_pagar]", e)
        db.session.rollback()
        dados_conciliacao = session.get('dados_conciliacao', {})
        if dados_conciliacao.get('transacao_id'):
            limpar_dados_conciliacao()
        flash(("Erro ao informar faturamento do extrator! Entre em contato com o suporte.", "warning"))
        return redirect(url_for("listagem_extratores_a_pagar"))
    
@app.route("/financeiro/a-pagar/extrator-a-pagar-massa", methods=["GET", "POST"])
@login_required
@requires_roles
def extrator_a_pagar_massa():
    try:
        verificar_e_limpar_conciliacao_incorreta('pagamento_extrator') 
        campos_obrigatorios = {}
        campos_erros = {}
        gravar_banco = True
        creditos_selecionados = {}
        
        dados_conciliacao = session.get('dados_conciliacao', {})
        conciliar_transacao_id = dados_conciliacao.get('transacao_id')

        if request.method == "GET":
            ids_selecionados = request.args.get('ids', '')
            if not ids_selecionados:
                flash(("Nenhum registro foi selecionado para faturamento!", "warning"))
                return redirect(url_for("listagem_extratores_a_pagar"))
            
            try:
                ids_list = [int(id.strip()) for id in ids_selecionados.split(',') if id.strip()]
            except ValueError:
                flash(("IDs inválidos selecionados!", "warning"))
                return redirect(url_for("listagem_extratores_a_pagar"))

        else:
            ids_selecionados = request.form.get('ids_registros', '')
            if not ids_selecionados:
                flash(("Nenhum registro foi selecionado para faturamento!", "warning"))
                return redirect(url_for("listagem_extratores_a_pagar"))
            
            try:
                ids_list = [int(id.strip()) for id in ids_selecionados.split(',') if id.strip()]
            except ValueError:
                flash(("IDs inválidos selecionados!", "warning"))
                return redirect(url_for("listagem_extratores_a_pagar"))

        # Busca registros operacionais associados aos extratores
        registros = ExtratorPagarModel.query.filter(
            ExtratorPagarModel.id.in_(ids_list),
            ExtratorPagarModel.situacao_pagamento_id == 2
        ).all()

        if not registros:
            flash(("Nenhum registro válido encontrado para faturamento!", "warning"))
            return redirect(url_for("listagem_extratores_a_pagar"))
        
        # Verificar transação OFX para conciliação
        transacao_ofx = None
        if conciliar_transacao_id:
            transacao_ofx = ImportacaoOfx.query.get(conciliar_transacao_id)
            print(f"[DEBUG] transacao_ofx encontrada: {transacao_ofx}")

        # Verificar se algum registro já foi faturado
        if len(registros) != len(ids_list):
            flash(("Alguns registros selecionados não estão disponíveis para faturamento!", "warning"))

        # Atribui registro operacional a cada registro de extrator
        for registro in registros:
            if not hasattr(registro, 'registro_operacional') or registro.registro_operacional is None:
                registro_oper = RegistroOperacionalModel.obter_registro_solicitacao_por_id(registro.solicitacao_id)
                registro.registro_operacional = registro_oper

        # Processamento de extratores
        extratores_dict = {}
        valor_total_geral = 0
        
        for registro in registros:
            if registro.valor_total_a_pagar_100 is None:
                continue
            
            # Obter o extrator id
            extrator_id = registro.obter_extrator_id()
            valor_total_geral += registro.valor_total_a_pagar_100

            # Se o extrator ainda não estiver no dicionário
            if extrator_id not in extratores_dict:
                saldo_credito = CreditoExtratorModel.obtem_registro_extrator_id(extrator_id)
                credito_disponivel = saldo_credito.valor_total_credito_100 if saldo_credito else 0
                
                # Buscar créditos individuais disponíveis do extrator
                creditos_individuais_extrator = ExtratoCreditoExtratorModel.obter_creditos_disponiveis_extrator(extrator_id)
                
                extratores_dict[extrator_id] = {
                    'registros': [],
                    'valor_total': 0,
                    'credito_disponivel': credito_disponivel or 0,
                    'creditos_individuais': creditos_individuais_extrator,
                    'saldo_credito_obj': saldo_credito or 0,
                    'extrator': None
                }
            
            extratores_dict[extrator_id]['registros'].append(registro)
            extratores_dict[extrator_id]['valor_total'] += registro.valor_total_a_pagar_100
            
            # Associar extrator
            if not extratores_dict[extrator_id]['extrator']:
                extrator_obj = registro.obter_extrator()
                if extrator_obj:
                    extratores_dict[extrator_id]['extrator'] = extrator_obj

        # Cálculo do total de crédito disponível
        total_credito_disponivel = sum(e['credito_disponivel'] for e in extratores_dict.values())

        # Processamento de confirmação de faturação
        if request.method == "POST":
            usar_credito = request.form.get("usar_credito")
            
            # Processar créditos selecionados individualmente
            creditos_selecionados_json = request.form.get("creditos_selecionados", "{}")
            try:
                creditos_selecionados = json.loads(creditos_selecionados_json) if creditos_selecionados_json else {}
            except json.JSONDecodeError:
                creditos_selecionados = {}
            
            # Processamento de valores editados pelo usuario
            valores_calculados_json = request.form.get("valores_calculados", "")
            valores_calculados = {}

            alteracoes_detectadas = False
            
            if valores_calculados_json:
                try:
                    valores_calculados = json.loads(valores_calculados_json)
                    print(f"[DEBUG] Valores calculados recebidos: {valores_calculados}")
                except json.JSONDecodeError as e:
                    print(f"[ERROR] Erro ao decodificar JSON de valores calculados: {e}")
                    flash(("Erro nos valores calculados!", "warning"))
                    return redirect(request.url)

            # Atualizar registros de extratores com valores calculados
            for registro in registros:
                registro_id_str = str(registro.id)
                if registro_id_str in valores_calculados:
                    dados_calculo = valores_calculados[registro_id_str]
                    try:
                        # Verificar se o preço de custo foi alterado
                        if 'preco_custo' in dados_calculo:
                            preco_custo_frontend = float(dados_calculo['preco_custo'])
                            preco_custo_frontend_100 = preco_custo_frontend * 100
                            
                            # Comparar com valor original do banco
                            preco_original = registro.preco_custo_bitola_100 or 0
                            if preco_custo_frontend_100 != preco_original:
                                registro.preco_custo_bitola_100 = preco_custo_frontend_100
                                alteracoes_detectadas = True
                        
                        # Verificar se o valor total foi alterado
                        if 'valor_total' in dados_calculo:
                            valor_total_frontend = float(dados_calculo['valor_total'])
                            valor_total_frontend_100 = valor_total_frontend * 100
                            
                            # Comparar com valor original do banco
                            valor_original = registro.valor_total_a_pagar_100 or 0
                            if valor_total_frontend_100 != valor_original:
                                registro.valor_total_a_pagar_100 = valor_total_frontend_100
                                alteracoes_detectadas = True
                                
                    except (ValueError, TypeError) as e:
                        print(f"[ERROR] Erro ao processar valores do registro {registro.id}: {e}")
                        flash(f"Erro nos valores do registro {registro.id}!", "warning")
                        return redirect(request.url)

            # Salva as alterações de preço de custo e valores totais, se houver
            if alteracoes_detectadas:
                db.session.commit()
                print("[DEBUG] Alterações de preço custo e valores totais salvas")

            # Recalcula totais após a verificação de edição de valores
            valor_total_geral = 0
            for extrator_id, dados in extratores_dict.items():
                dados['valor_total'] = 0  
                for registro in dados['registros']:
                    valor_registro = registro.valor_total_a_pagar_100 or 0
                    if valor_registro > 0:
                        dados['valor_total'] += valor_registro
                        valor_total_geral += valor_registro

            # Processamento de créditos selecionados
            total_credito_aplicado = 0
            valor_final_extratores = valor_total_geral

            # Variável para armazenar detalhes dos créditos utilizados
            detalhes_creditos_utilizados = {
                'extratores': []
            }

            if usar_credito == "sim":
                # Verificar se há créditos selecionados
                total_creditos_selecionados = 0
                
                # Calcular total de créditos selecionados
                for tipo_entidade, entidades in creditos_selecionados.items():
                    for entidade_id, credito_ids in entidades.items():
                        for credito_id in credito_ids:
                            if tipo_entidade == 'extrator':
                                credito = ExtratoCreditoExtratorModel.query.get(credito_id)
                                if credito:
                                    total_creditos_selecionados += credito.valor_credito_100
                
                if total_creditos_selecionados == 0:
                    flash(("Nenhum crédito selecionado para aplicar!", "warning"))
                    return redirect(request.url)
                
                # Calcular crédito disponível e valor total da fatura
                credito_restante_para_usar = valor_total_geral  # Não usar mais crédito que o necessário
                
                # Processar créditos selecionados por extrator
                if 'extrator' in creditos_selecionados and credito_restante_para_usar > 0:
                    for extrator_id_str, credito_ids in creditos_selecionados['extrator'].items():
                        extrator_id = int(extrator_id_str)
                        
                        for credito_id in credito_ids:
                            if credito_restante_para_usar <= 0:
                                break
                                
                            credito_individual = ExtratoCreditoExtratorModel.query.filter_by(id=credito_id, ativo=True, credito_utilizado=False).first()
                            if credito_individual:  # Permite tanto créditos quanto débitos
                                
                                # Calcular quanto deste crédito será realmente utilizado para permitir uso parcial
                                valor_credito_a_usar = min(abs(credito_individual.valor_credito_100), credito_restante_para_usar)
                                if credito_individual.valor_credito_100 < 0:
                                    valor_credito_a_usar = -valor_credito_a_usar  # Manter sinal negativo para débitos

                                credito_individual.credito_utilizado = True
                                db.session.add(credito_individual)
                                
                                # Se há uso parcial, criar registro para o valor restante
                                if abs(valor_credito_a_usar) < abs(credito_individual.valor_credito_100):
                                    valor_restante = credito_individual.valor_credito_100 - valor_credito_a_usar
                                    
                                    credito_restante = ExtratoCreditoExtratorModel(
                                        tipo_movimentacao=1,  # Entrada
                                        descricao=f"Crédito restante após uso parcial em faturamento massa - Original: {credito_individual.descricao}",
                                        data_movimentacao=datetime.now(),
                                        extrator_id=extrator_id,
                                        valor_credito_100=valor_restante,
                                        usuario_id=current_user.id,
                                        ativo=True
                                    )
                                    db.session.add(credito_restante)
                                
                                # Atualizar credito restante para usar
                                credito_restante_para_usar -= abs(valor_credito_a_usar)
                                
                                # Criar extrato com o valor que será utilizado (permite créditos negativos)
                                tipo_mov = 2 if valor_credito_a_usar > 0 else 1  # Saída para crédito positivo, Entrada para débito
                                descricao_mov = f"{'Débito' if valor_credito_a_usar > 0 else 'Crédito'} {credito_individual.descricao} para faturamento em massa."
                                extrato_extrator = ExtratoCreditoExtratorModel(
                                    tipo_movimentacao=tipo_mov,
                                    descricao=descricao_mov,
                                    data_movimentacao=datetime.now(),
                                    extrator_id=extrator_id,
                                    valor_credito_100=abs(valor_credito_a_usar),  # Sempre positivo no extrato
                                    usuario_id=current_user.id,
                                    credito_utilizado=True,
                                )
                                db.session.add(extrato_extrator)
                                
                                # Atualizar saldo do extrator
                                dados_extrator = extratores_dict.get(extrator_id)
                                if dados_extrator and dados_extrator.get('saldo_credito_obj'):
                                    saldo_atual_extrator = dados_extrator['saldo_credito_obj'].valor_total_credito_100 or 0
                                    dados_extrator['saldo_credito_obj'].valor_total_credito_100 = saldo_atual_extrator - valor_credito_a_usar
                                
                                # Armazenar detalhes do crédito utilizado
                                detalhes_creditos_utilizados['extratores'].append({
                                    'credito_id': credito_id,
                                    'extrator_id': extrator_id,
                                    'valor': valor_credito_a_usar,
                                    'valor_original': credito_individual.valor_credito_100,
                                    'descricao': credito_individual.descricao,
                                    'data_movimentacao': credito_individual.data_movimentacao.strftime('%Y-%m-%d'),
                                    'uso_parcial': abs(valor_credito_a_usar) < abs(credito_individual.valor_credito_100)
                                })
                                
                                total_credito_aplicado += valor_credito_a_usar

                # Calcular valor final permitindo créditos negativos (débitos somam ao valor)
                valor_final_a_faturar = valor_total_geral - total_credito_aplicado
                
                # Garantir que valor final nunca seja negativo
                if valor_final_a_faturar < 0:
                    valor_final_a_faturar = 0
                
                # Marcar todos os registros como utilizando crédito se houve aplicação
                if total_credito_aplicado != 0:  # Permite tanto créditos positivos quanto negativos
                    for extrator_id, dados_extrator in extratores_dict.items():
                        for registro in dados_extrator['registros']:
                            registro.utiliza_credito = 1
                            registro.valor_credito_100 = 0  # Será calculado proporcionalmente se necessário
            else:
                # Não usar crédito
                valor_final_a_faturar = valor_total_geral
                for dados_extrator in extratores_dict.values():
                    for registro in dados_extrator['registros']:
                        registro.utiliza_credito = 0
                        registro.valor_credito_100 = 0

            # Atualizar status de todos os registros
            for registro in registros:
                registro.situacao_pagamento_id = 5

            # Marcar transação OFX como conciliada se existe
            if transacao_ofx and not transacao_ofx.conciliado:
                transacao_ofx.conciliado = True
                transacao_ofx.tipo_conciliacao = 'faturamento_extrator'
                transacao_ofx.pagamento_id = registros[0].id
                transacao_ofx.data_conciliacao = datetime.now()
                transacao_ofx.usuario_conciliacao_id = current_user.id
                transacao_ofx.observacoes_conciliacao = f"Conciliado com faturamento de extratores em massa - {len(registros)} registros"

            # Criando detalhes json para frontend
            detalhes_extratores = []
            for extrator_id, dados in extratores_dict.items():
                for reg in dados['registros']:
                    if reg.valor_total_a_pagar_100 is None:
                        continue
                        
                    registro_oper = reg.registro_operacional
                    valor_bruto_registro = reg.valor_total_a_pagar_100 or 0
                    valor_credito_registro = getattr(reg, 'valor_credito_100', 0) or 0
                    valor_faturado = max(0, valor_bruto_registro - valor_credito_registro)
                    preco_custo_registro = reg.preco_custo_bitola_100 or 0

                    numero_nf = ""
                    if registro_oper:
                        if registro_oper.estorno_nf and registro_oper.numero_nota_fiscal_estorno:
                            numero_nf = f"{registro_oper.numero_nota_fiscal_estorno} *"
                        elif registro_oper.numero_nota_fiscal:
                            numero_nf = registro_oper.numero_nota_fiscal
                        else:
                            numero_nf = ""

                    detalhes_extratores.append({
                        "extrator_a_pagar_id": reg.id,
                        "extrator_id": extrator_id,
                        "solicitacao_id": reg.solicitacao_id if reg.solicitacao else "",
                        "extrator_identificacao": dados['extrator'].identificacao if dados.get('extrator') else str(extrator_id),
                        "cliente": reg.solicitacao.cliente.identificacao if reg.solicitacao and reg.solicitacao.cliente else "",
                        "valor_bruto": valor_bruto_registro,
                        "valor_credito": valor_credito_registro,
                        "valor_faturado": valor_faturado,
                        "nota_fiscal": numero_nf,
                        "peso_ticket": f"{registro_oper.peso_liquido_ticket}" if registro_oper and registro_oper.peso_liquido_ticket else "",
                        "preco_custo": preco_custo_registro,
                        "produto": reg.solicitacao.produto.nome if reg.solicitacao and reg.solicitacao.produto else "",
                        "bitola": reg.solicitacao.bitola.bitola if reg.solicitacao and reg.solicitacao.bitola else "",
                        "data_entrega": reg.data_entrega_ticket.strftime('%d/%m/%Y') if reg.data_entrega_ticket else "",
                        "utiliza_credito": getattr(reg, 'utiliza_credito', 0) or 0,
                        "registro_operacional_id": registro_oper.id if registro_oper else "",
                        "placa_veiculo": reg.solicitacao.veiculo.placa_veiculo if reg.solicitacao and reg.solicitacao.veiculo else "",
                        "motorista": reg.solicitacao.motorista.nome_completo if reg.solicitacao and reg.solicitacao.motorista else "",
                        "transportadora_id": registro_oper.solicitacao.transportadora_id if registro_oper.solicitacao else "",
                        "transportadora_identificacao": registro_oper.solicitacao.transportadora_exibicao.identificacao if registro_oper.solicitacao else "",
                        "fornecedor_id": registro_oper.solicitacao.fornecedor_id if registro_oper.solicitacao else "",
                        "fornecedor_identificacao": registro_oper.solicitacao.fornecedor.identificacao if registro_oper.solicitacao and registro_oper.solicitacao.fornecedor else "",
                    })
                    
                    # Pontuação do usuário
                    PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                        current_user.id,
                        TipoAcaoEnum.CADASTRO,
                        TipoAcaoEnum.CADASTRO.pontos,
                        modulo=f"informar_faturamento_extrator_massa_{reg.id}",
                    )

            # Criação de novo faturamento
            novo_faturamento = FaturamentoModel(
                usuario_id=current_user.id,
                codigo_faturamento=FaturamentoModel.gerar_codigo_novo_faturamento(),
                valor_total=valor_final_a_faturar,
                ids_fornecedores=None,
                ids_extratores=ids_selecionados,
                utilizou_credito=(usar_credito == "sim"),
                situacao_pagamento_id=7,
                tipo_operacao=1, # carga
                direcao_financeira=2 # despesa
            )

            # Campos extras do faturamento
            if hasattr(novo_faturamento, 'valor_bruto_total'):
                novo_faturamento.valor_bruto_total = valor_total_geral
            if hasattr(novo_faturamento, 'valor_credito_aplicado'):
                novo_faturamento.valor_credito_aplicado = total_credito_aplicado
            if hasattr(novo_faturamento, 'valor_fornecedor'):
                novo_faturamento.valor_fornecedor = None
            if hasattr(novo_faturamento, 'valor_extrator'):
                novo_faturamento.valor_extrator = valor_total_geral

            # Salvar detalhes com créditos utilizados
            novo_faturamento.salvar_detalhes(
                fornecedores=[], 
                transportadoras=[],
                extratores=detalhes_extratores,
                credito_fornecedor=[],
                credito_transportadora=[],
                credito_extrator=detalhes_creditos_utilizados['extratores']
            )

            db.session.add(novo_faturamento)

            db.session.commit()

            if conciliar_transacao_id:
                limpar_dados_conciliacao()
                flash(("Faturamentos informados e transação OFX conciliada com sucesso!", "success"))
                return redirect(url_for("listagem_ofx"))
            else:
                flash(("Faturamentos informados com sucesso!", "success"))
                return redirect(url_for("listagem_extratores_a_pagar"))

        return render_template(
            "financeiro/informar_pagamento/informar_pagamento_extrator_massa.html",
            campos_obrigatorios=campos_obrigatorios,
            campos_erros=campos_erros,
            dados_corretos=request.form,
            registros=registros,
            extratores_dict=extratores_dict,
            valor_total_geral=valor_total_geral,
            total_credito_disponivel=total_credito_disponivel,
            ids_selecionados=ids_selecionados,
            creditos_selecionados=creditos_selecionados,
            conciliar_transacao_id=conciliar_transacao_id,
            valor_conciliar=dados_conciliacao.get('valor'),
            data_conciliar=dados_conciliacao.get('data'),
            descricao_conciliar=dados_conciliacao.get('descricao'),
            fitid_conciliar=dados_conciliacao.get('fitid')
        )

    except Exception as e:
        print(f"[ERROR] Erro interno: {e}")
        db.session.rollback()
        dados_conciliacao = session.get('dados_conciliacao', {})
        if dados_conciliacao.get('transacao_id'):
            limpar_dados_conciliacao()
            print("[DEBUG] Dados de conciliação limpos devido ao erro")
        flash((f"Erro interno: {str(e)}", "error"))
        return redirect(url_for("listagem_extratores_a_pagar"))

@app.route("/financeiro/a-pagar/extrator-a-pagar/cancelar-informe/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def cancelar_pagamento_extrator(id):
    try:
        registro = ExtratorPagarModel.obter_extrator_a_pagar_id(id)
        if not registro:
            flash(("Registro não encontrado", "warning"))
            return redirect(url_for("listagem_extratores_a_pagar"))

        if registro.situacao_pagamento_id != 1:
            flash(("Só é possível cancelar faturamentos já informados.", "warning"))
            return redirect(url_for("listagem_extratores_a_pagar"))

        valor_credito = registro.valor_credito_100 or 0
        valor_saldo = registro.valor_saldo_debitado_100 or 0
        usou_credito = bool(registro.utiliza_credito)
        usou_saldo = bool(registro.utiliza_saldo_movimentacao)

        registro.situacao_pagamento_id = 2

        mov_orig = MovimentacaoFinanceiraModel.query.filter_by(
            extrator_pagamento_id=registro.id, deletado=False
        ).first()
        if mov_orig:
            mov_orig.deletado = True

        
        if usou_credito and valor_credito != 0:  # Permite tanto créditos positivos quanto negativos
            estorno_cred = ExtratoCreditoExtratorModel(
                tipo_movimentacao=4, 
                descricao="Estorno de crédito por cancelamento de faturamento",
                data_movimentacao=datetime.now(),
                extrator_id=registro.obter_extrator_id(),
                usuario_id=current_user.id,
                valor_credito_100=valor_credito,
            )
            db.session.add(estorno_cred)
            db.session.flush()

            
            saldo_credito = CreditoExtratorModel.obtem_registro_extrator_id(registro.obter_extrator_id())
            if saldo_credito:
                saldo_credito.valor_total_credito_100 += valor_credito

            mov_est_cred = MovimentacaoFinanceiraModel(
                tipo_movimentacao=4,
                usuario_id=current_user.id,
                data_movimentacao=datetime.now(),
                credito_extrator_id=estorno_cred.id,
                movimentacao_extra=1,
                valor_movimentacao_100=valor_credito,
                conta_bancaria_id=registro.conta_bancaria_id
            )
            db.session.add(mov_est_cred)
            db.session.flush()

        if usou_saldo and valor_saldo > 0:
            mov_est_din = MovimentacaoFinanceiraModel(
                tipo_movimentacao=5,
                usuario_id=current_user.id,
                data_movimentacao=datetime.now(),
                extrator_pagamento_id=registro.id,
                movimentacao_extra=1,
                valor_movimentacao_100=valor_saldo,
                conta_bancaria_id=registro.conta_bancaria_id
            )
            db.session.add(mov_est_din)

            
            saldo_total = SaldoMovimentacaoFinanceiraModel.obter_registro_conta_bancaria(registro.conta_bancaria_id)
            if saldo_total is None:
                novo_saldo = SaldoMovimentacaoFinanceiraModel(
                    data_movimentacao=datetime.now(), valor_total_saldo_100=valor_saldo,
                    conta_bancaria_id=registro.conta_bancaria_id
                )
                db.session.add(novo_saldo)
            else:
                saldo_total.valor_total_saldo_100 += valor_saldo
                saldo_total.data_movimentacao = datetime.now()
                saldo_total.conta_bancaria_id = registro.conta_bancaria_id

        
        for comp_id in (
            registro.comprovante_pagamento_complementar_id,
            registro.comprovante_pagamento_id,
        ):
            if comp_id:
                arq = UploadArquivoModel.obter_arquivo_por_id(comp_id)
                if arq:
                    arq.deletado = True

        registro.comprovante_pagamento_complementar_id = None
        registro.comprovante_pagamento_id = None
        registro.utiliza_credito = False
        registro.utiliza_saldo_movimentacao = False
        registro.valor_credito_100 = None
        registro.valor_saldo_debitado_100 = None
        registro.plano_conta_id = None
        registro.categorizacao_fiscal_id = None
        registro.data_liquidacao = None
        registro.movimentacao_financeira_id = None

        db.session.commit()
        flash(("Cancelamento efetuado e saldos ajustados com sucesso!", "success"))

    except Exception as e:
        print("[ERROR cancelar_faturamento_extrator]", e)
        db.session.rollback()
        flash(("Erro ao cancelar informe de faturamento! Contate o suporte.", "warning"))

    return redirect(url_for("listagem_extratores_a_pagar"))


@app.route("/sincronizar/precos/extratores", methods=["GET", "POST"])
@login_required
@requires_roles
def atualizar_precos_extrator():
    """
    Rota para atualizar preços de extratores a pagar.
    Utiliza tarefa assíncrona para processar a atualização.
    """
    try:
        from servidor_huey.tarefas import sincronizar_precos_extratores
        from datetime import datetime
        
        if request.method == 'POST':
            data_inicio = request.form.get('data_inicio')
            data_fim = request.form.get('data_fim')
            extrator_id = request.form.get('extrator_id')
            
            if not data_inicio or not data_fim:
                flash(("Por favor, informe o período para atualização dos valores!", "warning"))
                return redirect(url_for("listagem_extratores_a_pagar"))
            
            try:
                # Validar formato das datas
                data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
                
                if data_inicio_obj > data_fim_obj:
                    flash(("A data de início não pode ser maior que a data fim!", "warning"))
                    return redirect(url_for("listagem_extratores_a_pagar"))
                
            except ValueError:
                flash(("Formato de data inválido!", "warning"))
                return redirect(url_for("listagem_extratores_a_pagar"))
        else:
            return redirect(url_for("listagem_extratores_a_pagar"))
        
        # Converter extrator_id para None se for "todos"
        extrator_filtro = None if extrator_id == "todos" else extrator_id
        
        task = sincronizar_precos_extratores(data_inicio, data_fim, extrator_filtro)
        
        try:
            resultado = task(blocking=True, timeout=120)  
            if resultado['sucesso']:
                if resultado['sincronizados'] > 0:
                    flash((f"{resultado['sincronizados']} valores sincronizados com sucesso!", "success"))
                else:
                    flash((f"Todos os extratores do período informado já estão sincronizados", "warning"))
            else:
                flash(("Não foi possível atualizar os registros no período informado", "warning"))
                
        except Exception as e:
            flash((f"Processo de atualização iniciado para o período. Pode levar alguns minutos para concluir.", "warning"))
            
        return redirect(url_for("listagem_extratores_a_pagar"))
        
    except Exception as e:
        flash(("Não foi possível iniciar a sincronização", "warning"))
        return redirect(url_for("listagem_extratores_a_pagar"))
