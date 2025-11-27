from datetime import datetime
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem
from flask import render_template, request, redirect, url_for, flash, session, jsonify, json
from flask_login import login_required, current_user
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.faturamento.cargas_a_faturar.transportadora.frete_a_pagar_model import FretePagarModel
from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
from sistema.models_views.configuracoes_gerais.situacao_pagamento.situacao_pagamento_model import SituacaoPagamentoModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.faturamento.controle_credito.credito_agrupado.credito_freteiro_model import CreditoFreteiroModel
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.faturamento.controle_credito.extrato_credito.extrato_credito_freteiro_model import ExtratoCreditoFreteiroModel
from sistema.models_views.financeiro.movimentacao_financeira.movimentacao_financeira_model import MovimentacaoFinanceiraModel
from sistema.models_views.financeiro.movimentacao_financeira.saldo_movimentacao_financeira_model import SaldoMovimentacaoFinanceiraModel
from sistema.models_views.upload_arquivo.upload_arquivo_model import UploadArquivoModel
from sistema.models_views.configuracoes_gerais.conta_bancaria.conta_bancaria_model import ContaBancariaModel
from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx
from sistema.models_views.importacao_ofx.importacao_ofx_view import limpar_dados_conciliacao
from sistema.models_views.importacao_ofx.importacao_ofx_view import verificar_e_limpar_conciliacao_incorreta
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema._utilitarios import *
from sistema._utilitarios.utilitario_semanal import UtilitariosSemana


@app.route("/financeiro/fretes-a-faturar", methods=["GET"])
@login_required
@requires_roles
def listagem_fretes_a_pagar():
    from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
    from sistema.models_views.gerenciar.fornecedor.fornecedor_model import FornecedorModel
    from sistema.models_views.gerenciar.motorista.motorista_model import MotoristaModel
    
    bitolas = BitolaModel.listar_bitolas_ativas()
    produtos = ProdutoModel.listar_produtos()
    statusPagamentos = SituacaoPagamentoModel.listar_status_filtro()
    transportadoras = TransportadoraModel.listar_transportadoras_ativas()
    fornecedores = FornecedorModel.listar_fornecedores_ativos()
    motoristas = MotoristaModel.listar_motoristas_ativos()
    clientes = ClienteModel.listar_clientes_ativos()

    verificar_e_limpar_conciliacao_incorreta('pagamento_frete')

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
    semana_atual_info = None
    valor_padrao_semana = None
    
    if semanas_disponiveis:
        valor_padrao_semana = semanas_disponiveis[0]["valor"]
        semana_atual_info = semanas_disponiveis[0]

    parametros_filtro = ["tipo_filtro", "semanaSelecionada", "dataInicio", "dataFim", "numeroNF", "placaCarga", "motoristaCarga",
                        "produtoCarga", "bitolaCarga", "transportadoraCarga", "fornecedorCarga", 
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
        transportadora = request.args.get("transportadoraCarga")
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
        
        registros = FretePagarModel.filtrar_frete_transportadora_agrupados(
            data_inicio=data_inicio,
            data_fim=data_fim,
            numero_nf=numero_nf,
            placa=placa,
            motorista=motorista,
            produto=produto,
            bitola=bitola,
            transportadora=transportadora,
            fornecedor=fornecedor,
            cliente=cliente,
            statusPagamento=statusPagamento
        )
        
        # for registro_dict in registros:
        #     registro = registro_dict.get('registro')
        #     faturamento_codigo = FaturamentoModel.buscar_faturamento_origem_por_carga_pagar_id(registro.id, 'transportadora')
        #     registro_dict['cod_faturamento'] = faturamento_codigo
        
    else:
        registros = FretePagarModel.obter_frete_transportadora_agrupados()
        
        # for registro_dict in registros:
        #     registro = registro_dict.get('registro')
        #     faturamento_codigo = FaturamentoModel.buscar_faturamento_origem_por_carga_pagar_id(registro.id, 'transportadora')
        #     registro_dict['cod_faturamento'] = faturamento_codigo
        
    return render_template(
        "/financeiro/fretes_a_pagar_listagem.html",
        registros=registros,
        transportadoras=transportadoras,
        bitolas=bitolas,
        produtos=produtos,
        statusPagamentos=statusPagamentos,
        fornecedores=fornecedores,
        motoristas=motoristas,
        clientes=clientes,
        dados_corretos=request.args,
        semanas_disponiveis=semanas_disponiveis,
        tipo_filtro=request.args.get("tipo_filtro", "semanal"),
        conciliar_transacao_id=conciliar_transacao_id,
        valor_conciliar=valor_conciliar,
        data_conciliar=data_conciliar,
        descricao_conciliar=descricao_conciliar,
        fitid_conciliar=fitid_conciliar
    )


@app.route("/financeiro/a-pagar/frete-a-pagar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def frete_a_pagar(id):
    try:
        campos_obrigatorios = {}
        campos_erros = {}
        gravar_banco = True

        verificar_e_limpar_conciliacao_incorreta('pagamento_frete')

        dados_conciliacao = session.get('dados_conciliacao', {})
        conciliar_transacao_id = dados_conciliacao.get('transacao_id')

        registro = FretePagarModel.obter_frete_a_pagar_id(id)
        if not registro:
            flash(("Registro não encontrado", "warning"))
            return redirect(url_for("listagem_fretes_a_pagar"))

        if registro.valor_total_a_pagar_100 == None:
            flash(("Não é possível informar faturamento de valor nulo", "warning"))
            return redirect(url_for("listagem_fretes_a_pagar"))
        if registro.situacao_pagamento_id == 5:
            flash(("Registro já consta como faturado!", "warning"))
            return redirect(url_for("listagem_fretes_a_pagar"))

        # Crédito disponível do freteiro (total)
        saldo_credito = CreditoFreteiroModel.obtem_registro_id(
            registro.transportadora_id
        )
        credito_disponivel = (
            saldo_credito.valor_total_credito_100 if saldo_credito else 0
        )

        # Buscar créditos individuais disponíveis da transportadora
        creditos_individuais = ExtratoCreditoFreteiroModel.obter_creditos_disponiveis_transportadora(
            registro.transportadora_id
        )

        registro_oper = RegistroOperacionalModel.obter_registro_solicitacao_por_id(
            registro.solicitacao_id
        )
        if not registro_oper:
            flash(("Registro operacional não encontrado", "warning"))
            return redirect(url_for("listagem_fretes_a_pagar"))
        
        transacao_ofx = None
        if conciliar_transacao_id:
            transacao_ofx = ImportacaoOfx.query.get(conciliar_transacao_id)
            print(f"[DEBUG] transacao_ofx encontrada: {transacao_ofx}")

        if request.method == "POST":
            valor_total_calculado = request.form.get("valor_total_calculado", "")
            preco_custo_atualizado = request.form.get("preco_custo_atualizado", "")

            if preco_custo_atualizado:
                try:
                    preco_custo_float = float(preco_custo_atualizado)
                    registro.preco_custo_bitola_100 = preco_custo_float * 100
                    print(registro.preco_custo_bitola_100)
                except (ValueError, TypeError) as e:
                    print(f"[ERROR] Preço custo: {preco_custo_atualizado} - {e}")
                    flash(("Erro no formato do preço custo! Entre em contato com o suporte.", "warning"))
                    return redirect(request.url)

            if valor_total_calculado:
                valor_total_float = float(valor_total_calculado)
                registro.valor_total_a_pagar_100 = valor_total_float * 100
               
            usar_credito = request.form.get("usar_credito")

            # Processar créditos selecionados individualmente
            creditos_selecionados_json = request.form.get("creditos_selecionados", "{}")
            try:
                creditos_selecionados = json.loads(creditos_selecionados_json) if creditos_selecionados_json else {}
            except json.JSONDecodeError:
                creditos_selecionados = {}

            valor_pendente = registro.valor_total_a_pagar_100

            # Variável para armazenar detalhes dos créditos utilizados
            detalhes_creditos_utilizados = []
            total_credito_aplicado = 0

            if usar_credito == "sim":
                # Verificar se há créditos selecionados
                total_creditos_selecionados = 0
                
                # Calcular total de créditos selecionados para esta transportadora
                if 'transportadora' in creditos_selecionados:
                    for transportadora_id_str, credito_ids in creditos_selecionados['transportadora'].items():
                        if int(transportadora_id_str) == registro.transportadora_id:
                            for credito_id in credito_ids:
                                credito = ExtratoCreditoFreteiroModel.query.get(credito_id)
                                if credito:
                                    total_creditos_selecionados += credito.valor_credito_100
                
                if not creditos_selecionados or 'transportadora' not in creditos_selecionados:
                    flash(("Nenhum crédito selecionado para aplicar!", "warning"))
                    gravar_banco = False
                elif total_creditos_selecionados == 0:
                    flash(("O total dos créditos selecionados é zero!", "warning"))
                    gravar_banco = False
                else:
                    # Processar créditos selecionados (permite valores negativos)
                    
                    # Processar créditos selecionados da transportadora
                    if 'transportadora' in creditos_selecionados:
                        for transportadora_id_str, credito_ids in creditos_selecionados['transportadora'].items():
                            if int(transportadora_id_str) == registro.transportadora_id:
                                
                                for credito_id in credito_ids:
                                    credito_individual = ExtratoCreditoFreteiroModel.query.filter_by(id=credito_id, ativo=True, credito_utilizado=False).first()
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
                                            
                                            credito_restante = ExtratoCreditoFreteiroModel(
                                                tipo_movimentacao=1,  # Entrada
                                                descricao=f"Crédito restante após uso parcial individual - Original: {credito_individual.descricao}",
                                                data_movimentacao=datetime.now(),
                                                transportadora_id=registro.transportadora_id,
                                                valor_credito_100=valor_restante,
                                                usuario_id=current_user.id,
                                                ativo=True
                                            )
                                            db.session.add(credito_restante)
                                        
                                        # Criar extrato com o valor que será utilizado (permite créditos negativos)
                                        tipo_mov = 2 if valor_credito_a_usar > 0 else 1  # Saída para crédito positivo, Entrada para débito
                                        descricao_mov = f"{'Débito' if valor_credito_a_usar > 0 else 'Crédito'} referente ao credito {credito_individual.descricao}."
                                        extrato_transportadora = ExtratoCreditoFreteiroModel(
                                            tipo_movimentacao=tipo_mov,
                                            descricao=descricao_mov,
                                            data_movimentacao=datetime.now(),
                                            transportadora_id=registro.transportadora_id,
                                            valor_credito_100=abs(valor_credito_a_usar),
                                            usuario_id=current_user.id,
                                            credito_utilizado=True
                                        )
                                        db.session.add(extrato_transportadora)
                                        
                                        # Atualizar saldo da transportadora
                                        if saldo_credito:
                                            saldo_atual_transp = saldo_credito.valor_total_credito_100 or 0
                                            saldo_credito.valor_total_credito_100 = saldo_atual_transp - valor_credito_a_usar
                                        
                                        # Atualizar credito restante para usar
                                        credito_restante_para_usar -= abs(valor_credito_a_usar)
                                        
                                        # Armazenar detalhes do crédito utilizado
                                        detalhes_creditos_utilizados.append({
                                            'credito_id': credito_id,
                                            'transportadora_id': registro.transportadora_id,
                                            'valor': valor_credito_a_usar,
                                            'valor_original': credito_individual.valor_credito_100,
                                            'descricao': credito_individual.descricao,
                                            'data_movimentacao': credito_individual.data_movimentacao.strftime('%Y-%m-%d'),
                                            'uso_parcial': abs(valor_credito_a_usar) < abs(credito_individual.valor_credito_100)
                                        })
                                        
                                        total_credito_aplicado += valor_credito_a_usar

                    # Aplicar crédito no registro (permite créditos negativos)
                    if total_credito_aplicado != 0:
                        registro.utiliza_credito = 1
                        registro.valor_credito_100 = total_credito_aplicado
                    else:
                        registro.utiliza_credito = 0
                        registro.valor_credito_100 = 0
            else:
                # Não usar crédito
                registro.utiliza_credito = 0
                registro.valor_credito_100 = 0

            if gravar_banco:
                registro.situacao_pagamento_id = 5

                # Calcular valor líquido após crédito
                valor_bruto = registro.valor_total_a_pagar_100 or 0
                valor_credito = registro.valor_credito_100 or 0
                # Se crédito é negativo, ele deve somar ao valor (débito): valor_bruto + abs(credito_negativo)  
                # Se crédito é positivo, ele deve subtrair do valor (crédito): valor_bruto - credito_positivo
                if valor_credito < 0:
                    valor_liquido = valor_bruto + abs(valor_credito)  # Soma débito (crédito negativo)
                else:
                    valor_liquido = valor_bruto - valor_credito       # Subtrai crédito (crédito positivo)

                # Criação do faturamento para o registro individual
                novo_faturamento = FaturamentoModel(
                    usuario_id=current_user.id,
                    codigo_faturamento=FaturamentoModel.gerar_codigo_novo_faturamento(),
                    valor_total=valor_liquido,
                    ids_fornecedores=None,
                    ids_fretes=str(registro.id),
                    utilizou_credito=(usar_credito == "sim"),
                    situacao_pagamento_id=7,
                    tipo_operacao=1,
                    direcao_financeira=2
                )
                if hasattr(novo_faturamento, 'valor_bruto_total'):
                    novo_faturamento.valor_bruto_total = registro.valor_total_a_pagar_100 or 0
                if hasattr(novo_faturamento, 'valor_credito_aplicado'):
                    novo_faturamento.valor_credito_aplicado = registro.valor_credito_100 or 0
                if hasattr(novo_faturamento, 'valor_fornecedor'):
                    novo_faturamento.valor_fornecedor = 0
                if hasattr(novo_faturamento, 'valor_transportadora'):
                    novo_faturamento.valor_transportadora = valor_liquido

                valor_bruto_registro = registro.valor_total_a_pagar_100 or 0
                valor_credito_registro = registro.valor_credito_100 or 0
                # Créditos negativos devem somar ao valor total
                valor_faturado = valor_bruto_registro - valor_credito_registro
                preco_custo_registro = registro.preco_custo_bitola_100 or 0

                numero_nf = ""
                if registro_oper:
                    if registro_oper.estorno_nf and registro_oper.numero_nota_fiscal_estorno:
                        numero_nf = f"{registro_oper.numero_nota_fiscal_estorno} *"
                    elif registro_oper.numero_nota_fiscal:
                        numero_nf = registro_oper.numero_nota_fiscal

                detalhes_transportadoras = [{
                    "frete_a_pagar_id": registro.id,
                    "transportadora_id": registro.transportadora_id,
                    "solicitacao_id": registro.solicitacao_id if registro.solicitacao else "",
                    "transportadora_identificacao": registro.transportadora.identificacao if registro.transportadora else str(registro.transportadora_id),
                    "fornecedor_identificacao": registro.fornecedor.identificacao if registro.fornecedor else 'Não informado',
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
                    "motorista": registro.solicitacao.motorista.nome_completo if registro.solicitacao and registro.solicitacao.motorista else ""
                }]

                novo_faturamento.salvar_detalhes(
                    fornecedores=[], 
                    transportadoras=detalhes_transportadoras,
                    credito_fornecedor=[],
                    credito_transportadora=detalhes_creditos_utilizados
                )
                
                db.session.add(novo_faturamento)

                # Marcar transação OFX como conciliada se existe
                if transacao_ofx and not transacao_ofx.conciliado:
                    transacao_ofx.conciliado = True
                    transacao_ofx.data_conciliacao = datetime.now()
                    transacao_ofx.frete_pagamento_id = registro.id
                    transacao_ofx.usuario_conciliacao_id = current_user.id
                    db.session.add(transacao_ofx)

                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    TipoAcaoEnum.CADASTRO,
                    TipoAcaoEnum.CADASTRO.pontos,
                    modulo="informar_faturamento_freteiro",
                )
                db.session.commit()
                if conciliar_transacao_id:
                    limpar_dados_conciliacao()
                    flash(("Faturamento informado e transação conciliada com sucesso!", "success"))
                else:
                    flash(("Faturamento informado com sucesso!", "success"))
                return redirect(url_for("listagem_faturamentos_cargas_a_pagar"))
        return render_template(
            "financeiro/informar_pagamento/informar_pagamento_freteiro.html",
            campos_obrigatorios=campos_obrigatorios,
            campos_erros=campos_erros,
            dados_corretos=request.form,
            registro=registro,
            registro_operacional=registro_oper,
            saldo_credito=credito_disponivel,
            creditos_individuais=creditos_individuais,
            conciliar_transacao_id=conciliar_transacao_id,
            valor_conciliar=dados_conciliacao.get('valor'),
            data_conciliar=dados_conciliacao.get('data'),
            descricao_conciliar=dados_conciliacao.get('descricao'),
            fitid_conciliar=dados_conciliacao.get('fitid')
        )

    except Exception as e:
        print("[ERROR frete_a_pagar]", e)
        db.session.rollback()
        flash(
            (
                "Erro ao informar faturamento do freteiro! Entre em contato com o suporte",
                "warning",
            )
        )
        return redirect(url_for("listagem_fretes_a_pagar"))
    
@app.route("/financeiro/a-pagar/frete-a-pagar-massa", methods=["GET", "POST"])
@login_required
@requires_roles
def frete_a_pagar_massa():
    try:
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
                return redirect(url_for("listagem_fretes_a_pagar"))
            
            try:
                ids_list = [int(id.strip()) for id in ids_selecionados.split(',') if id.strip()]
            except ValueError:
                flash(("IDs inválidos selecionados!", "warning"))
                return redirect(url_for("listagem_fretes_a_pagar"))

        else:  
            ids_selecionados = request.form.get('ids_registros', '')
            if not ids_selecionados:
                flash(("Nenhum registro foi selecionado para faturamento!", "warning"))
                return redirect(url_for("listagem_fretes_a_pagar"))
            
            try:
                ids_list = [int(id.strip()) for id in ids_selecionados.split(',') if id.strip()]
            except ValueError:
                flash(("IDs inválidos selecionados!", "warning"))
                return redirect(url_for("listagem_fretes_a_pagar"))

        registros = FretePagarModel.query.filter(
            FretePagarModel.id.in_(ids_list),
            FretePagarModel.situacao_pagamento_id == 2  
        ).all()

        if not registros:
            flash(("Nenhum registro válido encontrado para faturamento!", "warning"))
            return redirect(url_for("listagem_fretes_a_pagar"))
        
        transacao_ofx = None
        if conciliar_transacao_id:
            transacao_ofx = ImportacaoOfx.query.get(conciliar_transacao_id)
            print(f"[DEBUG] transacao_ofx encontrada: {transacao_ofx}")

        if len(registros) != len(ids_list):
            flash(("Alguns registros selecionados não estão disponíveis para faturamento!", "warning"))
        
        # Atribuir registro operacional a cada registro
        for registro in registros:
            if not hasattr(registro, 'registro_operacional') or registro.registro_operacional is None:
                registro_oper = RegistroOperacionalModel.obter_registro_solicitacao_por_id(registro.solicitacao_id)
                registro.registro_operacional = registro_oper

        # Processamento de transportadoras
        transportadoras_dict = {}
        valor_total_geral = 0
        
        for registro in registros:
            if registro.valor_total_a_pagar_100 is None:
                continue
                
            transportadora_id = registro.transportadora_id
            valor_total_geral += registro.valor_total_a_pagar_100
            
            if transportadora_id not in transportadoras_dict:
                saldo_credito = CreditoFreteiroModel.obtem_registro_id(transportadora_id)
                credito_disponivel = saldo_credito.valor_total_credito_100 if saldo_credito else 0
                
                # Buscar créditos individuais disponíveis da transportadora
                creditos_individuais_transp = ExtratoCreditoFreteiroModel.obter_creditos_disponiveis_transportadora(transportadora_id)
                
                transportadoras_dict[transportadora_id] = {
                    'registros': [],
                    'valor_total': 0,
                    'credito_disponivel': credito_disponivel or 0,
                    'creditos_individuais': creditos_individuais_transp,
                    'saldo_credito_obj': saldo_credito or 0,
                    'transportadora': None
                }
            
            transportadoras_dict[transportadora_id]['registros'].append(registro)
            transportadoras_dict[transportadora_id]['valor_total'] += registro.valor_total_a_pagar_100
            
            if not transportadoras_dict[transportadora_id]['transportadora']:
                if registro.registro_operacional and registro.registro_operacional.solicitacao and registro.registro_operacional.solicitacao.transportadora_exibicao:
                    transportadoras_dict[transportadora_id]['transportadora'] = registro.registro_operacional.solicitacao.transportadora_exibicao

        # Cálculo do total de crédito disponível
        total_credito_disponivel = sum(t['credito_disponivel'] for t in transportadoras_dict.values())

        if request.method == "POST":
            usar_credito = request.form.get("usar_credito")
            
            # Processar créditos selecionados individualmente
            creditos_selecionados_json = request.form.get("creditos_selecionados", "{}")
            try:
                creditos_selecionados = json.loads(creditos_selecionados_json) if creditos_selecionados_json else {}
            except json.JSONDecodeError:
                creditos_selecionados = {}

            # Processamento de valores editados pelo usuário
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

            # Atualizar registros com valores calculados
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

            # Salva as alterações se houver
            if alteracoes_detectadas:
                db.session.commit()
                print("[DEBUG] Alterações de preço custo e valores totais salvas")

            # Recalcula totais após edições
            valor_total_geral = 0
            for transportadora_id, dados in transportadoras_dict.items():
                dados['valor_total'] = 0
                for registro in dados['registros']:
                    valor_registro = registro.valor_total_a_pagar_100 or 0
                    if valor_registro > 0:
                        dados['valor_total'] += valor_registro
                        valor_total_geral += valor_registro

            # Processamento de créditos selecionados
            total_credito_aplicado = 0
            valor_final_transportadoras = valor_total_geral

            # Variável para armazenar detalhes dos créditos utilizados
            detalhes_creditos_utilizados = {
                'transportadoras': []
            }

            if usar_credito == "sim":
                # Verificar se há créditos selecionados
                total_creditos_selecionados = 0
                
                # Calcular total de créditos selecionados
                for tipo_entidade, entidades in creditos_selecionados.items():
                    for entidade_id, credito_ids in entidades.items():
                        for credito_id in credito_ids:
                            if tipo_entidade == 'transportadora':
                                credito = ExtratoCreditoFreteiroModel.query.get(credito_id)
                                if credito:
                                    total_creditos_selecionados += credito.valor_credito_100
                
                if not creditos_selecionados or ('transportadora' not in creditos_selecionados and len(creditos_selecionados) == 0):
                    flash(("Nenhum crédito selecionado para aplicar!", "warning"))
                    return redirect(request.url)
                
                # Calcular crédito disponível e valor total da fatura
                credito_restante_para_usar = valor_total_geral  # Não usar mais crédito que o necessário
                
                # Processar créditos selecionados por transportadora (permite créditos negativos)
                if 'transportadora' in creditos_selecionados:
                    for transportadora_id_str, credito_ids in creditos_selecionados['transportadora'].items():
                        transportadora_id = int(transportadora_id_str)
                        
                        for credito_id in credito_ids:
                                
                            credito_individual = ExtratoCreditoFreteiroModel.query.get(credito_id)
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
                                    
                                    credito_restante = ExtratoCreditoFreteiroModel(
                                        tipo_movimentacao=1,  # Entrada
                                        descricao=f"Crédito restante após uso parcial em faturamento massa - Original: {credito_individual.descricao}",
                                        data_movimentacao=datetime.now(),
                                        transportadora_id=transportadora_id,
                                        valor_credito_100=valor_restante,
                                        usuario_id=current_user.id,
                                        ativo=True
                                    )
                                    db.session.add(credito_restante)
                                
                                # Criar extrato com o valor que será utilizado (permite créditos negativos)
                                tipo_mov = 2 if valor_credito_a_usar > 0 else 1  # Saída para crédito positivo, Entrada para débito
                                descricao_mov = f"{'Débito' if valor_credito_a_usar > 0 else 'Crédito'} referente ao credito {credito_individual.descricao}."
                                extrato_transportadora = ExtratoCreditoFreteiroModel(
                                    tipo_movimentacao=tipo_mov,
                                    descricao=descricao_mov,
                                    data_movimentacao=datetime.now(),
                                    transportadora_id=transportadora_id,
                                    valor_credito_100=abs(valor_credito_a_usar),
                                    usuario_id=current_user.id,
                                    credito_utilizado=True
                                )
                                db.session.add(extrato_transportadora)
                                
                                # Atualizar saldo da transportadora (considera créditos negativos)
                                dados_transportadora = transportadoras_dict.get(transportadora_id)
                                if dados_transportadora and dados_transportadora.get('saldo_credito_obj'):
                                    saldo_atual_transp = dados_transportadora['saldo_credito_obj'].valor_total_credito_100 or 0
                                    dados_transportadora['saldo_credito_obj'].valor_total_credito_100 = saldo_atual_transp - valor_credito_a_usar
                                
                                # Atualizar credito restante para usar
                                credito_restante_para_usar -= abs(valor_credito_a_usar)
                                
                                # Armazenar detalhes do crédito utilizado
                                detalhes_creditos_utilizados['transportadoras'].append({
                                    'credito_id': credito_id,
                                    'transportadora_id': transportadora_id,
                                    'valor': valor_credito_a_usar,
                                    'valor_original': credito_individual.valor_credito_100,
                                    'descricao': credito_individual.descricao,
                                    'data_movimentacao': credito_individual.data_movimentacao.strftime('%Y-%m-%d'),
                                    'uso_parcial': abs(valor_credito_a_usar) < abs(credito_individual.valor_credito_100)
                                })
                                
                                total_credito_aplicado += valor_credito_a_usar

                # APLICAR DESCONTO GLOBAL: Permite créditos negativos
                total_credito_utilizado = total_credito_aplicado
                
                # Calcular valor final - Se crédito é negativo, ele deve somar ao valor (débito)
                # Se crédito é positivo, ele deve subtrair do valor (crédito)
                if total_credito_utilizado < 0:
                    valor_final_a_faturar = valor_total_geral + abs(total_credito_utilizado)  # Soma débito (crédito negativo)
                else:
                    valor_final_a_faturar = valor_total_geral - total_credito_utilizado       # Subtrai crédito (crédito positivo)
                
                # Atualizar o total de crédito aplicado para refletir o valor utilizado
                total_credito_aplicado = total_credito_utilizado
                
                # Marcar todos os registros como utilizando crédito (permite créditos negativos)
                if total_credito_aplicado != 0:
                    for transportadora_id, dados_transp in transportadoras_dict.items():
                        for registro in dados_transp['registros']:
                            registro.utiliza_credito = 1
                            registro.valor_credito_100 = 0  # Será calculado proporcionalmente se necessário
            else:
                # Não usar crédito
                valor_final_a_faturar = valor_total_geral
                for dados_transp in transportadoras_dict.values():
                    for registro in dados_transp['registros']:
                        registro.utiliza_credito = 0
                        registro.valor_credito_100 = 0

            # Atualizar status de todos os registros
            for registro in registros:
                registro.situacao_pagamento_id = 5

            # Marcar transação OFX como conciliada se existe
            if transacao_ofx and not transacao_ofx.conciliado:
                transacao_ofx.conciliado = True
                transacao_ofx.tipo_conciliacao = 'faturamento_frete'
                transacao_ofx.pagamento_id = registros[0].id
                transacao_ofx.data_conciliacao = datetime.now()
                transacao_ofx.usuario_conciliacao_id = current_user.id
                transacao_ofx.observacoes_conciliacao = f"Conciliado com faturamento de fretes em massa - {len(registros)} registros"

            # Criar detalhes das transportadoras
            detalhes_transportadoras = []
            for transp_id, dados in transportadoras_dict.items():
                for registro in dados['registros']:
                    if registro.valor_total_a_pagar_100 is None:
                        continue
                        
                    registro_oper = registro.registro_operacional
                    valor_bruto_registro = registro.valor_total_a_pagar_100 or 0
                    valor_credito_registro = getattr(registro, 'valor_credito_100', 0) or 0
                    # Créditos negativos devem somar ao valor total
                    valor_faturado = valor_bruto_registro - valor_credito_registro
                    preco_custo_registro = registro.preco_custo_bitola_100 or 0

                    numero_nf = ""
                    if registro_oper:
                        if registro_oper.estorno_nf and registro_oper.numero_nota_fiscal_estorno:
                            numero_nf = f"{registro_oper.numero_nota_fiscal_estorno} *"
                        elif registro_oper.numero_nota_fiscal:
                            numero_nf = registro_oper.numero_nota_fiscal
                        else:
                            numero_nf = ""

                    detalhes_transportadoras.append({
                        "frete_a_pagar_id": registro.id,
                        "transportadora_id": registro.transportadora_id,
                        "solicitacao_id": registro.solicitacao_id if registro.solicitacao else "",
                        "transportadora_identificacao": registro_oper.solicitacao.transportadora_exibicao.identificacao if registro_oper and registro_oper.solicitacao and registro_oper.solicitacao.transportadora_exibicao else str(registro.transportadora_id),
                        "fornecedor_identificacao": registro.fornecedor.identificacao if registro.fornecedor else 'Não informado',
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
                        "utiliza_credito": getattr(registro, 'utiliza_credito', 0) or 0,
                        "registro_operacional_id": registro_oper.id if registro_oper else "",
                        "placa_veiculo": registro.solicitacao.veiculo.placa_veiculo if registro.solicitacao and registro.solicitacao.veiculo else "",
                        "motorista": registro.solicitacao.motorista.nome_completo if registro.solicitacao and registro.solicitacao.motorista else ""
                    })
                    
                    # Pontuação do usuário
                    PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                        current_user.id,
                        TipoAcaoEnum.CADASTRO,
                        TipoAcaoEnum.CADASTRO.pontos,
                        modulo=f"informar_faturamento_freteiro_massa_{registro.id}",
                    )

            # Criação do faturamento em massa
            novo_faturamento = FaturamentoModel(
                usuario_id=current_user.id,
                codigo_faturamento=FaturamentoModel.gerar_codigo_novo_faturamento(),
                valor_total=valor_final_a_faturar,
                ids_fornecedores=None,
                ids_fretes=ids_selecionados,
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
                novo_faturamento.valor_fornecedor = 0
            if hasattr(novo_faturamento, 'valor_transportadora'):
                novo_faturamento.valor_transportadora = valor_final_a_faturar

            # Salvar detalhes com créditos utilizados
            novo_faturamento.salvar_detalhes(
                fornecedores=[], 
                transportadoras=detalhes_transportadoras,
                credito_fornecedor=[],
                credito_transportadora=detalhes_creditos_utilizados['transportadoras']
            )
            
            db.session.add(novo_faturamento)

            db.session.commit()
            
            if conciliar_transacao_id:
                limpar_dados_conciliacao()
                flash(("Faturamentos informados e transação OFX conciliada com sucesso!", "success"))
                return redirect(url_for("listagem_ofx"))
            else:
                flash(("Faturamentos informados com sucesso!", "success"))
                return redirect(url_for("listagem_faturamentos_cargas_a_pagar"))

        return render_template(
            "financeiro/informar_pagamento/informar_pagamento_frete_massa.html",
            campos_obrigatorios=campos_obrigatorios,
            campos_erros=campos_erros,
            dados_corretos=request.form,
            registros=registros,
            transportadoras_dict=transportadoras_dict,
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
        flash((f"Erro interno: {str(e)}", "error"))
        return redirect(url_for("listagem_fretes_a_pagar"))
    
@app.route("/financeiro/a-pagar/frete-a-pagar/cancelar-informe/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def cancelar_pagamento_freteiro(id):
    try:
        registro = FretePagarModel.obter_frete_a_pagar_id(id)
        if not registro:
            flash(("Registro não encontrado", "warning"))
            return redirect(url_for("listagem_fretes_a_pagar"))

        if registro.situacao_pagamento_id != 1:
            flash(("Só é possível cancelar faturamentos já informados.", "warning"))
            return redirect(url_for("listagem_fretes_a_pagar"))

        # valores originais
        valor_credito = registro.valor_credito_100 or 0
        valor_saldo = registro.valor_saldo_debitado_100 or 0
        usou_credito = bool(registro.utiliza_credito)
        usou_saldo = bool(registro.utiliza_saldo_movimentacao)

        registro.situacao_pagamento_id = 2


        mov_antiga = MovimentacaoFinanceiraModel.query.filter_by(
            freteiro_pagamento_id=registro.id, deletado=False
        ).first()
        if mov_antiga:
            mov_antiga.deletado = True

        if usou_credito and valor_credito != 0:  # Permite tanto créditos positivos quanto negativos

            estorno_cred = ExtratoCreditoFreteiroModel(
                tipo_movimentacao=4,
                descricao=f"Estorno de crédito por cancelamento de faturamento",
                data_movimentacao=datetime.now(),
                transportadora_id=registro.transportadora_id,
                usuario_id=current_user.id,
                valor_credito_100=valor_credito,
            )
            db.session.add(estorno_cred)
            db.session.flush()

            saldo_credito = CreditoFreteiroModel.obtem_registro_id(registro.transportadora_id)
            if saldo_credito:
                saldo_credito.valor_total_credito_100 += valor_credito

            mov_est_cred = MovimentacaoFinanceiraModel(
                tipo_movimentacao=4,
                usuario_id=current_user.id,
                data_movimentacao=datetime.now(),
                movimentacao_extra=1,
                valor_movimentacao_100=valor_credito,
                credito_freteiro_id=estorno_cred.id,
                conta_bancaria_id=registro.conta_bancaria_id
            )
            db.session.add(mov_est_cred)
            db.session.flush()

        if usou_saldo and valor_saldo > 0:
            mov_est_din = MovimentacaoFinanceiraModel(
                tipo_movimentacao=5,
                usuario_id=current_user.id,
                data_movimentacao=datetime.now(),
                freteiro_pagamento_id=registro.id,
                movimentacao_extra=1,
                valor_movimentacao_100=valor_saldo,
                conta_bancaria_id=registro.conta_bancaria_id
            )
            db.session.add(mov_est_din)

            saldo_total = SaldoMovimentacaoFinanceiraModel.obter_registro_conta_bancaria(registro.conta_bancaria_id)
            if saldo_total is None:
                novo_saldo = SaldoMovimentacaoFinanceiraModel(
                    data_movimentacao=datetime.now(),
                    valor_total_saldo_100=valor_saldo,
                    conta_bancaria_id=registro.conta_bancaria_id
                )
                db.session.add(novo_saldo)
            else:
                saldo_total.data_movimentacao = datetime.now()
                saldo_total.valor_total_saldo_100 += valor_saldo
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
        print(f"[ERROR cancelar_faturamento_freteiro] {e}")
        db.session.rollback()
        flash(("Erro ao cancelar informe de faturamento! Contate o suporte.", "warning"))

    return redirect(url_for("listagem_fretes_a_pagar"))
