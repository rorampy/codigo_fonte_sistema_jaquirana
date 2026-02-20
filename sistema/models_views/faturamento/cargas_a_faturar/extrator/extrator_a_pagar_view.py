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

from sistema.models_views.financeiro.controle_adiantamentos.servico_creditos import ServicoCreditos
from sistema.models_views.financeiro.controle_adiantamentos.transacao_credito_model import (
    TransacaoCreditoModel, TipoTransacaoCredito, TipoPessoa
)
from sistema.models_views.financeiro.controle_adiantamentos.faturamento_credito_vinculo_model import FaturamentoCreditoVinculoModel
from sistema.models_views.financeiro.controle_adiantamentos.historico_transacao_model import HistoricoTransacaoCreditoModel, AcaoHistoricoCredito


@app.route("/financeiro/extratores-a-pagar", methods=["GET"])
@login_required
@requires_roles
def listagem_extratores_a_pagar():
    from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
    from sistema.models_views.gerenciar.fornecedor.fornecedor_model import FornecedorModel
    from sistema.models_views.gerenciar.motorista.motorista_model import MotoristaModel
    from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
    from sistema.models_views.gerenciar.extrator.extrator_model import ExtratorModel
    
    bitolas = BitolaModel.listar_bitolas_ativas()
    produtos = ProdutoModel.listar_produtos()
    statusPagamentos = SituacaoPagamentoModel.listar_status_filtro()
    transportadoras = TransportadoraModel.listar_transportadoras_ativas()
    fornecedores = FornecedorModel.listar_fornecedores_ativos()
    motoristas = MotoristaModel.listar_motoristas_ativos()
    clientes = ClienteModel.listar_clientes_ativos()
    extratores = ExtratorModel.listar_extratores_ativos()

    verificar_e_limpar_conciliacao_incorreta('pagamento_extrator') 

    dados_conciliacao = session.get('dados_conciliacao', {})
    
    conciliar_transacao_id = dados_conciliacao.get('transacao_id')
    valor_conciliar = dados_conciliacao.get('valor')
    data_conciliar = dados_conciliacao.get('data')
    descricao_conciliar = dados_conciliacao.get('descricao')
    fitid_conciliar = dados_conciliacao.get('fitid')

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

        if tipo_filtro == "data" and data_inicio_form and data_fim_form:
            from datetime import datetime
            data_inicio = datetime.strptime(data_inicio_form, "%Y-%m-%d").date()
            data_fim = datetime.strptime(data_fim_form, "%Y-%m-%d").date()
        else:
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
            tipo_data_filtro=request.args.get("tipoDataFiltro", "data_entrega"),
        )

    else:
        registros = ExtratorPagarModel.obter_extratores_agrupados()
        
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


@app.route("/sincronizar/precos/extrator", methods=["GET", "POST"])
@login_required
@requires_roles
def atualizar_precos_extrator():
    """
    Sincroniza os preços de extração para os registros dentro do período informado.
    """
    try:
        from servidor_huey.tarefas import sincronizar_precos_extratores
        
        if request.method == 'POST':
            data_inicio = request.form.get('data_inicio')
            data_fim = request.form.get('data_fim')
            extrator_id = request.form.get('extrator_id')

            if not data_inicio or not data_fim:
                flash(("Por favor, informe o período para atualização dos valores de extração!", "warning"))
                return redirect(url_for("listagem_extratores_a_pagar"))
            
            try:
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

        extrator_filtro = None if extrator_id == "todos" else extrator_id

        task = sincronizar_precos_extratores(data_inicio, data_fim, extrator_id=extrator_filtro)

        try:
            resultado = task(blocking=True, timeout=120) 

            if resultado['sucesso']:
                if resultado['sincronizados'] > 0:
                    flash((f"{resultado['sincronizados']} valores de extração sincronizados!", "success"))
                else:
                    flash(("Todos os extratores no período informado já estão sincronizados", "warning"))
            else:
                flash(("Não foi possível atualizar os registros de extração no período informado", "warning"))
                
        except Exception as e:
            flash(("Processo de atualização de extratores pode levar alguns minutos para concluir.", "warning"))
            
        return redirect(url_for("listagem_extratores_a_pagar"))
        
    except Exception as e:
        flash(("Não foi possível iniciar a sincronização de extratores", "warning"))
        return redirect(url_for("listagem_extratores_a_pagar"))


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

        extrator_id_registro = registro.obter_extrator_id()
        extrator_obj = registro.obter_extrator()
        credito_disponivel = ServicoCreditos.obter_saldo_extrator(extrator_id_registro)
        
        creditos_individuais = ServicoCreditos.obter_creditos_disponiveis_extrator(
            extrator_id_registro
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

            creditos_selecionados_json = request.form.get("creditos_selecionados", "{}")
            try:
                creditos_selecionados = json.loads(creditos_selecionados_json) if creditos_selecionados_json else {}
            except json.JSONDecodeError:
                creditos_selecionados = {}

            valor_pendente = registro.valor_total_a_pagar_100
            extrator_id = extrator_id_registro

            detalhes_creditos_utilizados = []
            total_credito_aplicado = 0

            if usar_credito == "sim":
                creditos_ids = []
                total_creditos_selecionados = 0
                
                if 'extrator' in creditos_selecionados:
                    for extrator_id_str, ids_list in creditos_selecionados['extrator'].items():
                        if int(extrator_id_str) == extrator_id:
                            for credito_id in ids_list:
                                credito = TransacaoCreditoModel.query.get(credito_id)
                                saldo_credito = credito.obter_saldo_disponivel_100() if credito else 0
                                if credito and saldo_credito != 0:
                                    creditos_ids.append(int(credito_id))
                                    total_creditos_selecionados += saldo_credito
                                    
                                    detalhes_creditos_utilizados.append({
                                        'credito_id': credito_id,
                                        'extrator_id': extrator_id,
                                        'valor': saldo_credito,
                                        'valor_original': saldo_credito,
                                        'descricao': credito.descricao,
                                        'data_movimentacao': credito.data_movimentacao.strftime('%Y-%m-%d') if credito.data_movimentacao else '',
                                        'uso_parcial': False
                                    })
                
                if not creditos_ids:
                    flash(("Nenhum crédito selecionado para aplicar!", "warning"))
                    gravar_banco = False
                elif total_creditos_selecionados == 0:
                    flash(("Não há créditos disponíveis para usar!", "warning"))
                    gravar_banco = False
                else:
                    if total_creditos_selecionados < 0:
                        valor_credito_a_usar = total_creditos_selecionados
                    else:
                        valor_credito_a_usar = min(total_creditos_selecionados, valor_pendente)
                    
            else:
                registro.utiliza_credito = 0
                registro.valor_credito_100 = 0

            if gravar_banco:
                registro.situacao_pagamento_id = 5

                valor_bruto = registro.valor_total_a_pagar_100 or 0
                valor_liquido = valor_bruto

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
                    novo_faturamento.valor_credito_aplicado = 0
                
                db.session.add(novo_faturamento)
                db.session.flush()
                
                resultado_creditos = None
                if usar_credito == "sim" and creditos_ids:
                    resultado_creditos = ServicoCreditos.processar_utilizacao_creditos(
                        tipo='extrator',
                        pessoa_id=extrator_id,
                        creditos_ids=creditos_ids,
                        valor_maximo_100=abs(valor_credito_a_usar),
                        usuario_id=current_user.id,
                        faturamento_id=novo_faturamento.id,
                        descricao_base=None
                    )
                    
                    if resultado_creditos['sucesso']:
                        total_credito_aplicado = resultado_creditos['total_utilizado_100']
                        
                        registro.utiliza_credito = 1
                        registro.valor_credito_100 = total_credito_aplicado
                        
                        valor_liquido = valor_bruto - total_credito_aplicado
                        novo_faturamento.valor_total = valor_liquido
                        
                        if hasattr(novo_faturamento, 'valor_credito_aplicado'):
                            novo_faturamento.valor_credito_aplicado = total_credito_aplicado
                        
                        for i, proc in enumerate(resultado_creditos.get('creditos_processados', [])):
                            if i < len(detalhes_creditos_utilizados):
                                detalhes_creditos_utilizados[i]['valor'] = proc.get('valor_utilizado', 0)
                                detalhes_creditos_utilizados[i]['uso_parcial'] = (
                                    proc.get('valor_utilizado', 0) < detalhes_creditos_utilizados[i].get('valor_original', 0)
                                )
                    else:
                        db.session.rollback()
                        flash((f"Erro ao processar créditos: {resultado_creditos.get('mensagem', 'Erro desconhecido')}", "warning"))
                        gravar_banco = False
                
                if hasattr(novo_faturamento, 'valor_bruto_total'):
                    novo_faturamento.valor_bruto_total = valor_bruto
                if hasattr(novo_faturamento, 'valor_credito_aplicado'):
                    novo_faturamento.valor_credito_aplicado = total_credito_aplicado
                if hasattr(novo_faturamento, 'valor_fornecedor'):
                    novo_faturamento.valor_fornecedor = None
                if hasattr(novo_faturamento, 'valor_extrator'):
                    novo_faturamento.valor_extrator = valor_bruto

                valor_bruto_registro = registro.valor_total_a_pagar_100 or 0
                valor_credito_registro = registro.valor_credito_100 or 0
                valor_faturado = valor_bruto_registro - valor_credito_registro
                preco_custo_registro = registro.preco_custo_bitola_100 or 0

                numero_nf = ""
                if registro_oper:
                    if registro_oper.estorno_nf and registro_oper.numero_nota_fiscal_estorno:
                        numero_nf = f"{registro_oper.numero_nota_fiscal_estorno} *"
                    elif registro_oper.numero_nota_fiscal:
                        numero_nf = registro_oper.numero_nota_fiscal

                detalhes_extratores = [{
                    "extrator_a_pagar_id": registro.id,
                    "extrator_id": extrator_id_registro,
                    "solicitacao_id": registro.solicitacao_id if registro.solicitacao else "",
                    "extrator_identificacao": extrator_obj.identificacao if extrator_obj else str(extrator_id_registro),
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
                
                if novo_faturamento.valor_total == 0:
                    novo_faturamento.situacao_pagamento_id = 8
                else:
                    novo_faturamento.situacao_pagamento_id = 7


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

        return render_template(
            "/financeiro/informar_pagamento/informar_pagamento_extrator.html",
            campos_obrigatorios=campos_obrigatorios,
            campos_erros=campos_erros,
            dados_corretos=request.form,
            registro=registro,
            registro_operacional=registro_oper,
            saldo_credito=credito_disponivel,
            creditos_individuais=creditos_individuais,
            extrator_id=extrator_id_registro,
            extrator=extrator_obj,
            conciliar_transacao_id=conciliar_transacao_id,
            valor_conciliar=dados_conciliacao.get('valor'),
            data_conciliar=dados_conciliacao.get('data'),
            descricao_conciliar=dados_conciliacao.get('descricao'),
            fitid_conciliar=dados_conciliacao.get('fitid')
        )

    except Exception as e:
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
    """Processa faturamento em massa de extratores.
    
    Permite faturar múltiplos pagamentos de extratores simultaneamente,
    com suporte a aplicação de créditos/débitos via nova arquitetura TransacaoCreditoModel.
    """
    try:
        if not current_user or not current_user.is_authenticated:
            flash(("Sessão expirada. Faça login novamente.", "warning"))
            return redirect(url_for("login"))
        
        from sistema.models_views.autenticacao.usuario_model import UsuarioModel
        usuario_existe = UsuarioModel.query.filter_by(id=current_user.id).first()
        if not usuario_existe:
            flash(("Usuário não encontrado no sistema.", "warning"))
            return redirect(url_for("logout"))
        
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

        registros = ExtratorPagarModel.query.filter(
            ExtratorPagarModel.id.in_(ids_list),
            ExtratorPagarModel.situacao_pagamento_id == 2
        ).all()

        if not registros:
            flash(("Nenhum registro válido encontrado para faturamento!", "warning"))
            return redirect(url_for("listagem_extratores_a_pagar"))

        if len(registros) != len(ids_list):
            flash(("Alguns registros selecionados não estão disponíveis para faturamento!", "warning"))

        for registro in registros:
            if not hasattr(registro, 'registro_operacional') or registro.registro_operacional is None:
                registro_oper = RegistroOperacionalModel.obter_registro_solicitacao_por_id(registro.solicitacao_id)
                registro.registro_operacional = registro_oper

        extratores_dict = {}
        valor_total_geral = 0
        
        for registro in registros:
            if registro.valor_total_a_pagar_100 is None:
                continue
            
            extrator_id = registro.obter_extrator_id()
            valor_total_geral += registro.valor_total_a_pagar_100

            if extrator_id not in extratores_dict:
                credito_disponivel = ServicoCreditos.obter_saldo_extrator(extrator_id)
                
                creditos_individuais_extrator = ServicoCreditos.obter_creditos_disponiveis_extrator(extrator_id)
                
                extratores_dict[extrator_id] = {
                    'registros': [],
                    'valor_total': 0,
                    'credito_disponivel': credito_disponivel or 0,
                    'creditos_individuais': creditos_individuais_extrator,
                    'extrator': None
                }
            
            extratores_dict[extrator_id]['registros'].append(registro)
            
            extratores_dict[extrator_id]['valor_total'] += registro.valor_total_a_pagar_100
            
            if not extratores_dict[extrator_id]['extrator']:
                extratores_dict[extrator_id]['extrator'] = registro.obter_extrator()

        def calcular_totais():
            """Centraliza todos os cálculos de totais (valores e créditos).
            
            Returns:
                dict: Dicionário com todos os totais calculados
            """
            valor_total_extratores = sum(e['valor_total'] for e in extratores_dict.values())
            
            total_registros = sum(len(e['registros']) for e in extratores_dict.values())
            
            credito_total = sum(e['credito_disponivel'] for e in extratores_dict.values())
            
            return {
                'valor_total_geral': valor_total_extratores,
                'total_registros': total_registros,
                'total_credito_disponivel': credito_total
            }
        
        totais = calcular_totais()
        valor_total_geral = totais['valor_total_geral']
        total_credito_disponivel = totais['total_credito_disponivel']

        if request.method == "POST":
            usar_credito = request.form.get("usar_credito")
            
            creditos_selecionados_json = request.form.get("creditos_selecionados", "{}")
            try:
                creditos_selecionados = json.loads(creditos_selecionados_json) if creditos_selecionados_json else {}
            except json.JSONDecodeError:
                creditos_selecionados = {}
            
            valores_calculados_json = request.form.get("valores_calculados", "")
            valores_calculados = {}

            alteracoes_detectadas = False
            
            if valores_calculados_json:
                try:
                    valores_calculados = json.loads(valores_calculados_json)
                except json.JSONDecodeError as e:
                    flash(("Erro nos valores calculados!", "warning"))
                    return redirect(request.url)

            for registro in registros:
                registro_id_str = str(registro.id)
                if registro_id_str in valores_calculados:
                    dados_calculo = valores_calculados[registro_id_str]
                    try:
                        if 'preco_custo' in dados_calculo:
                            preco_custo_frontend = float(dados_calculo['preco_custo'])
                            preco_custo_frontend_100 = preco_custo_frontend * 100
                            
                            preco_original = registro.preco_custo_bitola_100 or 0
                            if preco_custo_frontend_100 != preco_original:
                                registro.preco_custo_bitola_100 = preco_custo_frontend_100
                                alteracoes_detectadas = True
                        
                        if 'valor_total' in dados_calculo:
                            valor_total_frontend = float(dados_calculo['valor_total'])
                            valor_total_frontend_100 = valor_total_frontend * 100
                            
                            valor_original = registro.valor_total_a_pagar_100 or 0
                            if valor_total_frontend_100 != valor_original:
                                registro.valor_total_a_pagar_100 = valor_total_frontend_100
                                alteracoes_detectadas = True
                                
                    except (ValueError, TypeError) as e:
                        flash(f"Erro nos valores do registro {registro.id}!", "warning")
                        return redirect(request.url)

            if alteracoes_detectadas:
                db.session.commit()

            valor_total_geral = 0
            for extrator_id, dados in extratores_dict.items():
                dados['valor_total'] = 0
                
                for registro in dados['registros']:
                    valor_registro = registro.valor_total_a_pagar_100 or 0
                    if valor_registro > 0:
                        dados['valor_total'] += valor_registro
                        valor_total_geral += valor_registro

            valor_final_a_faturar = valor_total_geral
            
            novo_faturamento = FaturamentoModel(
                usuario_id=current_user.id,
                codigo_faturamento=FaturamentoModel.gerar_codigo_novo_faturamento(),
                valor_total=valor_final_a_faturar,
                ids_fornecedores=None,
                ids_extratores=ids_selecionados,
                utilizou_credito=(usar_credito == "sim"),
                situacao_pagamento_id=7,
                tipo_operacao=1,
                direcao_financeira=2
            )

            if hasattr(novo_faturamento, 'valor_bruto_total'):
                novo_faturamento.valor_bruto_total = valor_total_geral
            if hasattr(novo_faturamento, 'valor_credito_aplicado'):
                novo_faturamento.valor_credito_aplicado = 0
            if hasattr(novo_faturamento, 'valor_fornecedor'):
                novo_faturamento.valor_fornecedor = None
            if hasattr(novo_faturamento, 'valor_extrator'):
                novo_faturamento.valor_extrator = valor_total_geral
            
            db.session.add(novo_faturamento)
            db.session.flush()

            total_credito_aplicado = 0
            detalhes_creditos_utilizados = {
                'extratores': []
            }

            if usar_credito == "sim":
                total_creditos_selecionados = 0
                
                for tipo_entidade, entidades in creditos_selecionados.items():
                    for entidade_id, credito_ids in entidades.items():
                        for credito_id in credito_ids:
                            if tipo_entidade == 'extrator':
                                credito = TransacaoCreditoModel.query.get(credito_id)
                                if credito:
                                    total_creditos_selecionados += credito.obter_saldo_disponivel_100()
                
                if not creditos_selecionados or ('extrator' not in creditos_selecionados and len(creditos_selecionados) == 0):
                    db.session.rollback()
                    flash(("Nenhum crédito selecionado para aplicar!", "warning"))
                    return redirect(request.url)
                
                credito_restante_para_usar = float('inf') if total_creditos_selecionados < 0 else valor_total_geral
                
                if 'extrator' in creditos_selecionados:
                    for extrator_id_str, credito_ids in creditos_selecionados['extrator'].items():
                        extrator_id = int(extrator_id_str)
                        
                        resultado_utilizacao = ServicoCreditos.processar_utilizacao_creditos(
                            tipo='extrator',
                            pessoa_id=extrator_id,
                            creditos_ids=credito_ids,
                            valor_maximo_100=int(credito_restante_para_usar) if credito_restante_para_usar != float('inf') else 999999999,
                            usuario_id=current_user.id,
                            faturamento_id=novo_faturamento.id,
                            descricao_base=None
                        )
                        
                        if resultado_utilizacao.get('sucesso'):
                            valor_utilizado = resultado_utilizacao.get('total_utilizado_100', 0)
                            total_credito_aplicado += valor_utilizado
                            credito_restante_para_usar -= valor_utilizado
                            
                            for cred_proc in resultado_utilizacao.get('creditos_processados', []):
                                detalhes_creditos_utilizados['extratores'].append({
                                    'credito_id': cred_proc.get('credito_id'),
                                    'extrator_id': extrator_id,
                                    'valor': cred_proc.get('valor_utilizado', 0),
                                    'descricao': cred_proc.get('descricao', ''),
                                    'data_movimentacao': cred_proc.get('data_movimentacao', '')
                                })

                total_credito_utilizado = total_credito_aplicado
                valor_final_a_faturar = valor_total_geral - total_credito_utilizado
                
                novo_faturamento.valor_total = valor_final_a_faturar
                if hasattr(novo_faturamento, 'valor_credito_aplicado'):
                    novo_faturamento.valor_credito_aplicado = total_credito_aplicado
                if hasattr(novo_faturamento, 'valor_extrator'):
                    novo_faturamento.valor_extrator = valor_final_a_faturar
                
                if total_credito_aplicado != 0:
                    for extrator_id, dados_ext in extratores_dict.items():
                        for registro in dados_ext['registros']:
                            registro.utiliza_credito = 1
                            registro.valor_credito_100 = 0

            else:
                valor_final_a_faturar = valor_total_geral
                for dados_extrator in extratores_dict.values():
                    for registro in dados_extrator['registros']:
                        registro.utiliza_credito = 0
                        registro.valor_credito_100 = 0

            for registro in registros:
                registro.situacao_pagamento_id = 5

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
                    
                    PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                        current_user.id,
                        TipoAcaoEnum.CADASTRO,
                        TipoAcaoEnum.CADASTRO.pontos,
                        modulo=f"informar_faturamento_extrator_massa_{reg.id}",
                    )

            novo_faturamento.salvar_detalhes(
                fornecedores=[],
                transportadoras=[],
                extratores=detalhes_extratores,
                credito_fornecedor=[],
                credito_transportadora=[],
                credito_extrator=detalhes_creditos_utilizados['extratores']
            )
            
            if novo_faturamento.valor_total == 0:
                novo_faturamento.situacao_pagamento_id = 8
            else:
                novo_faturamento.situacao_pagamento_id = 7
            

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
        db.session.rollback()
        dados_conciliacao = session.get('dados_conciliacao', {})
        if dados_conciliacao.get('transacao_id'):
            limpar_dados_conciliacao()
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

        if usou_credito and valor_credito != 0:
            faturamento = FaturamentoModel.query.filter(
                FaturamentoModel.ids_extratores.contains(str(registro.id))
            ).first()
            
            if faturamento:
                resultado_estorno = ServicoCreditos.estornar_utilizacao_creditos(
                    faturamento_id=faturamento.id,
                    usuario_id=current_user.id,
                    motivo=f"Cancelamento de pagamento de extrator ID {registro.id}"
                )
                if not resultado_estorno.get('sucesso'):
                    pass

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
        db.session.rollback()
        flash(("Erro ao cancelar informe de faturamento! Contate o suporte.", "warning"))

    return redirect(url_for("listagem_extratores_a_pagar"))
