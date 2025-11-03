from datetime import datetime
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem
from flask import render_template, request, redirect, url_for, flash, session, jsonify, json
from flask_login import login_required, current_user
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.faturamento.cargas_a_pagar.extrator.extrator_a_pagar_model import ExtratorPagarModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.controle_carga.produto_model import ProdutoModel
from sistema.models_views.financeiro.situacao_pagamento_model import SituacaoPagamentoModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.controle_carga.registro_operacional_model import RegistroOperacionalModel
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
from sistema.models_views.faturamento.cargas_a_pagar.comissionado.comissionado_a_pagar_model import ComissionadoPagarModel
from sistema.models_views.faturamento.faturamento_model import FaturamentoModel
from sistema._utilitarios import *
from sistema._utilitarios.utilitario_semanal import UtilitariosSemana


@app.route("/financeiro/comissionados-a-pagar", methods=["GET"])
@login_required
@requires_roles
def listagem_comissionados_a_pagar():
    from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
    from sistema.models_views.gerenciar.fornecedor.fornecedor_model import FornecedorModel
    from sistema.models_views.gerenciar.motorista.motorista_model import MotoristaModel
    from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
    from sistema.models_views.gerenciar.comissionado.comissionado_model import ComissionadoModel
    
    bitolas = BitolaModel.listar_bitolas_ativas()
    produtos = ProdutoModel.listar_produtos()
    statusPagamentos = SituacaoPagamentoModel.listar_status_filtro()
    transportadoras = TransportadoraModel.listar_transportadoras_ativas()
    fornecedores = FornecedorModel.listar_fornecedores_ativos()
    motoristas = MotoristaModel.listar_motoristas_ativos()
    clientes = ClienteModel.listar_clientes_ativos()
    comissionados = ComissionadoModel.listar_comissionados_ativos()

    verificar_e_limpar_conciliacao_incorreta('pagamento_comissionado') 

    dados_conciliacao = session.get('dados_conciliacao', {})
    
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
                        "produtoCarga", "bitolaCarga", "comissionadoCarga", "fornecedorCarga", 
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
        comissionado = request.args.get("comissionadoCarga")
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

        registros = ComissionadoPagarModel.filtrar_comissionados_agrupados(
            data_inicio=data_inicio,
            data_fim=data_fim,
            numero_nf=numero_nf,
            placa=placa,
            motorista=motorista,
            produto=produto,
            bitola=bitola,
            comissionado=comissionado,
            fornecedor=fornecedor,
            cliente=cliente,
            statusPagamento=statusPagamento,
        )
    else:
        registros = ComissionadoPagarModel.obter_comissionados_agrupados()

    return render_template(
        "/financeiro/comissionado_a_pagar_listagem.html",
        registros=registros,
        bitolas=bitolas,
        produtos=produtos,
        statusPagamentos=statusPagamentos,
        transportadoras=transportadoras,
        fornecedores=fornecedores,
        motoristas=motoristas,
        clientes=clientes,
        comissionados=comissionados,
        dados_corretos=request.args,
        semanas_disponiveis=semanas_disponiveis,
        tipo_filtro=request.args.get("tipo_filtro", "semanal"),
        conciliar_transacao_id=conciliar_transacao_id,
        valor_conciliar=valor_conciliar,
        data_conciliar=data_conciliar,
        descricao_conciliar=descricao_conciliar,
        fitid_conciliar=fitid_conciliar
    )


@app.route("/relatorios/relatorios-financeiros/a-pagar-comissionado", methods=["GET", "POST"])
@login_required
@requires_roles
def relatorio_a_pagar_comissionados():
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    dataHoje = datetime.now().strftime("%d-%m-%Y")
    bitola = BitolaModel.listar_bitolas_ativas()
    produtos = ProdutoModel.listar_produtos()
    statusPagamentos = SituacaoPagamentoModel.listar_status()
    
    def obter_registros_com_filtros():
        filtros_source = request.form if request.method == "POST" and any(request.form.values()) else request.args
        
        if any(filtros_source.values()):
            data_inicio_str = filtros_source.get("dataInicio")
            data_fim_str = filtros_source.get("dataFim")
            placa = filtros_source.get("placaCargaCliente")
            motorista = filtros_source.get("motoristaCargaCliente")
            transportadora = filtros_source.get("tranpostadoraCargaCliente")
            comissionado = filtros_source.get("comissionadoCargaCliente")
            fornecedor = filtros_source.get("fornecedorCargaCliente")
            cliente = filtros_source.get("clienteCarga")
            numero_nf = filtros_source.get("numeroNfCliente")
            incompleto = filtros_source.get("registroIncompleto")
            statusPagamento = filtros_source.get("statusPagamento") or "Pendente"
            
            data_inicio = None
            data_fim = None
            
            if data_inicio_str:
                try:
                    data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d")
                except ValueError:
                    pass
                    
            if data_fim_str:
                try:
                    data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d")
                except ValueError:
                    pass
            
            incompleto_bool = None
            if incompleto == "1":
                incompleto_bool = True
            elif incompleto == "0":
                incompleto_bool = False
            
            return ComissionadoPagarModel.filtrar_comissionados_agrupados(
                data_inicio=data_inicio,
                data_fim=data_fim,
                placa=placa,
                motorista=motorista,
                transportadora=transportadora,
                fornecedor=fornecedor,
                cliente=cliente,
                comissionado=comissionado,
                numero_nf=numero_nf,
                statusPagamento=statusPagamento,
                incompleto=incompleto_bool,
            )
        else:
            return ComissionadoPagarModel.obter_comissionados_agrupados()
    
    if request.method == "POST":
        dados_corretos = request.form if any(request.form.get(k) for k in ['dataInicio', 'dataFim', 'placaCargaCliente', 'motoristaCargaCliente', 'tranpostadoraCargaCliente', 'comissionadoCargaCliente', 'fornecedorCargaCliente', 'clienteCarga', 'numeroNfCliente', 'registroIncompleto', 'statusPagamento']) else request.args
    else:
        dados_corretos = request.args
    
    registros = obter_registros_com_filtros()
    
    if request.method == "POST":
        registros_exportacao = registros  

        if request.form.get("exportar_pdf"):
            logo_path = obter_url_absoluta_de_imagem("logo.png")
            html = render_template(
                "relatorios/relatorios_financeiros/relatorio_a_pagar_comissionado/exportar_relatorio_a_pagar_comissionado_pdf.html",
                logo_path=logo_path,
                changelog=changelog,
                dataHoje=dataHoje,
                dados_corretos=dados_corretos,
                registros=registros_exportacao
            )

            nome_arquivo_saida = f"relacao_comissionados_a_pagar_{dataHoje}"
            return ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida, "Landscape")
        
        if request.form.get("exportar_excel"):
            dados_excel = []
            
            if not registros_exportacao:
                dados_excel.append({
                    "Comissionado": "Nenhum registro encontrado",
                    "Data Entrega": "",
                    "Transportadora": "",
                    "Fornecedor": "",
                    "Produto/Bitola": "",
                    "Peso Ticket": "",
                    "Preço Comissão (Ton.)": "",
                    "A pagar comissionado": "",
                    "Status pagamento": "",
                })
            else:
                registros_por_comissionado = {}
                
                for item in registros_exportacao:
                    comissionado_obj = item.get("comissionado")
                    comissionado_id = comissionado_obj.identificacao if comissionado_obj else "Sem comissionado"
                    
                    if comissionado_id not in registros_por_comissionado:
                        registros_por_comissionado[comissionado_id] = {}
                        
                    produto = item.get("produto", "Sem produto")
                    
                    if produto not in registros_por_comissionado[comissionado_id]:
                        registros_por_comissionado[comissionado_id][produto] = []
                        
                    registros_por_comissionado[comissionado_id][produto].append(item)

                for comissionado_id in sorted(registros_por_comissionado.keys()):
                    produtos_comissionado = registros_por_comissionado[comissionado_id]
                    
                    dados_excel.append({
                        "Comissionado": f"COMISSIONADO: {comissionado_id.upper()}",
                        "Data Entrega": "",
                        "Transportadora": "",
                        "Fornecedor": "",
                        "Produto/Bitola": "",
                        "Peso Ticket": "",
                        "Preço Comissão (Ton.)": "",
                        "A pagar comissionado": "",
                        "Status pagamento": "",
                    })
                    
                    for produto in sorted(produtos_comissionado.keys()):
                        registros_produto = produtos_comissionado[produto]
                        
                        dados_excel.append({
                            "Comissionado": f"  Produto: {produto}",
                            "Data Entrega": "",
                            "Transportadora": "",
                            "Fornecedor": "",
                            "Produto/Bitola": "",
                            "Peso Ticket": "",
                            "Preço Comissão (Ton.)": "",
                            "A pagar comissionado": "",
                            "Status pagamento": "",
                        })
                        
                        for item in registros_produto:
                            registro = item["registro"]
                            
                            data_entrega = "-"
                            if registro.data_entrega_ticket:
                                data_entrega = registro.data_entrega_ticket.strftime("%d/%m/%Y")
                            
                            transportadora = "-"
                            if (registro.solicitacao and 
                                registro.solicitacao.transportadora_exibicao and 
                                registro.solicitacao.transportadora_exibicao.identificacao):
                                transportadora = registro.solicitacao.transportadora_exibicao.identificacao
                            
                            fornecedor = "-"
                            if (registro.solicitacao and 
                                registro.solicitacao.fornecedor and 
                                registro.solicitacao.fornecedor.identificacao):
                                fornecedor = registro.solicitacao.fornecedor.identificacao
                            
                            produto_nome = "-"
                            bitola_nome = "-"
                            if (registro.solicitacao and 
                                registro.solicitacao.produto and 
                                registro.solicitacao.produto.nome):
                                produto_nome = registro.solicitacao.produto.nome
                            
                            if (registro.solicitacao and 
                                registro.solicitacao.bitola and 
                                registro.solicitacao.bitola.bitola):
                                bitola_nome = registro.solicitacao.bitola.bitola
                            
                            produto_bitola = f"{produto_nome} | {bitola_nome}" if produto_nome != "-" or bitola_nome != "-" else "-"
                            
                            peso_ticket = "-"
                            try:
                                registro_op = item.get("registro_operacional")
                                if registro_op and registro_op.peso_liquido_ticket:
                                    peso_ticket = f"{registro_op.peso_liquido_ticket}"
                                else:
                                    peso_ticket = "Sem peso"
                            except (KeyError, AttributeError):
                                peso_ticket = "Sem peso"
                            
                            preco_comissao = "-"
                            if registro.preco_custo_bitola_100:
                                preco_comissao = f"{(registro.preco_custo_bitola_100 / 100):,.2f}"
                            
                            valor_pagar_num = 0
                            if registro.valor_total_a_pagar_100:
                                valor_pagar_num = registro.valor_total_a_pagar_100 / 100
                            
                            status = "Pendente"
                            if registro.situacao:
                                status = registro.situacao.situacao
                            
                            dados_excel.append({
                                "Comissionado": "",
                                "Data Entrega": data_entrega,
                                "Transportadora": transportadora,
                                "Fornecedor": fornecedor,
                                "Produto/Bitola": produto_bitola,
                                "Peso Ticket": peso_ticket,
                                "Preço Comissão (Ton.)": preco_comissao,
                                "A pagar comissionado": f"{valor_pagar_num:,.2f}" if valor_pagar_num > 0 else "-",
                                "Status pagamento": status,
                            })

            nome_arquivo_saida = f"relatorio-comissionados-a-pagar-{dataHoje}"
            return ManipulacaoArquivos.exportar_excel(dados_excel, nome_arquivo_saida)

    return render_template(
        "relatorios/relatorios_financeiros/relatorio_a_pagar_comissionado/relatorio_a_pagar_comissionado.html",
        registros=registros,
        bitola=bitola,
        produtos=produtos,
        statusPagamentos=statusPagamentos,
        dados_corretos=dados_corretos,
    )

@app.route("/financeiro/a-pagar/comissionado-a-pagar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def comissionado_a_pagar(id):
    try:

        verificar_e_limpar_conciliacao_incorreta('pagamento_comissionado') 

        dados_conciliacao = session.get('dados_conciliacao', {})
        conciliar_transacao_id = dados_conciliacao.get('transacao_id')

        registro = ComissionadoPagarModel.obter_comissionado_a_pagar_id(id)
        contas_bancarias = ContaBancariaModel.obter_contas_bancarias_ativas()
        
        if registro.valor_total_a_pagar_100 == None:
            flash(("Não é possível informar faturamento de valor nulo", "warning"))
            return redirect(url_for("listagem_comissionados_a_pagar"))
        if registro.situacao_pagamento_id == 5:
            flash(("Registro já consta como faturado!", "warning"))
            return redirect(url_for("listagem_comissionados_a_pagar"))

        registro_oper = RegistroOperacionalModel.obter_registro_solicitacao_por_id(
            registro.solicitacao_id
        )
        if not registro_oper:
            flash(("Registro operacional não encontrado", "warning"))
            return redirect(url_for("listagem_comissionados_a_pagar"))
        
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
                
            registro.utiliza_credito = 0
            registro.situacao_pagamento_id = 5
            
             # Criação do faturamento para o registro individual (adaptado para extrator)
            novo_faturamento = FaturamentoModel(
                usuario_id=current_user.id,
                codigo_faturamento=FaturamentoModel.gerar_codigo_novo_faturamento(),
                valor_total=registro.valor_total_a_pagar_100,  # Valor líquido após crédito
                ids_comissionados=str(registro.id),  # Para extrator usa ids_extratores
                utilizou_credito=0,
                situacao_pagamento_id=7,
                tipo_operacao=1, # carga
                direcao_financeira=2 # despesa
            )
            if hasattr(novo_faturamento, 'valor_bruto_total'):
                novo_faturamento.valor_bruto_total = registro.valor_total_a_pagar_100 or 0
            if hasattr(novo_faturamento, 'valor_credito_aplicado'):
                novo_faturamento.valor_credito_aplicado =  0
            if hasattr(novo_faturamento, 'valor_fornecedor'):
                novo_faturamento.valor_fornecedor = 0  # Para extrator, valor fornecedor é 0
            if hasattr(novo_faturamento, 'valor_transportadora'):
                novo_faturamento.valor_transportadora = 0  # Para extrator, valor transportadora é 0
            if hasattr(novo_faturamento, 'valor_extrator'):
                novo_faturamento.valor_extrator = 0  # Valor vai para extrator
            if hasattr(novo_faturamento, 'valor_comissionado'):
                novo_faturamento.valor_comissionado = registro.valor_total_a_pagar_100  # Valor vai para comissionado
                
            preco_custo_registro = registro.preco_custo_bitola_100 or 0
            
            numero_nf = ""
            if registro_oper:
                if registro_oper.estorno_nf and registro_oper.numero_nota_fiscal_estorno:
                    numero_nf = f"{registro_oper.numero_nota_fiscal_estorno} *"
                elif registro_oper.numero_nota_fiscal:
                    numero_nf = registro_oper.numero_nota_fiscal

            # Detalhes para extrator (vai no array de fretes)
            detalhes_comissionados = [{
                "comissionado_a_pagar_id": registro.id,
                "comissionado_id": registro.comissionado_id if registro.comissionado_id else None,
                "solicitacao_id": registro.solicitacao_id if registro.solicitacao else "",
                "comissionado_identificacao": registro.comissionado.identificacao if registro and registro.comissionado else str(registro.comissionado_id),
                "cliente": registro.solicitacao.cliente.identificacao if registro.solicitacao and registro.solicitacao.cliente else "",
                "valor_bruto": registro.valor_total_a_pagar_100,
                "valor_credito": 0,
                "valor_faturado": registro.valor_total_a_pagar_100,
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

            # Salvar detalhes (array vazio para fornecedores, detalhes_extratores)
            novo_faturamento.salvar_detalhes([], [], [], detalhes_comissionados)

            db.session.add(novo_faturamento)

            if transacao_ofx and not transacao_ofx.conciliado:
                transacao_ofx.conciliado = True
                transacao_ofx.tipo_conciliacao = 'faturamento_comissionado'
                transacao_ofx.pagamento_id = registro.id
                transacao_ofx.data_conciliacao = datetime.now()
                transacao_ofx.usuario_conciliacao_id = current_user.id
                transacao_ofx.observacoes_conciliacao = f"Conciliado com faturamento de comissionado ID {registro.id}"

            PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                current_user.id,
                TipoAcaoEnum.CADASTRO,
                TipoAcaoEnum.CADASTRO.pontos,
                modulo="informar_faturamento_comissionado",
            )
            db.session.commit()
            if conciliar_transacao_id:
                limpar_dados_conciliacao()
                flash(("Faturamento informado e transação OFX conciliada com sucesso!", "success"))
                return redirect(url_for("listagem_ofx"))
            else:
                flash(("Faturamento informado com sucesso!", "success"))
                return redirect(url_for("listagem_comissionados_a_pagar"))

        return render_template(
            "/financeiro/informar_pagamento/informar_pagamento_comissionado.html",
            dados_corretos=request.form,
            registro=registro,
            contas_bancarias=contas_bancarias,
            registro_operacional=registro_oper,
            conciliar_transacao_id=conciliar_transacao_id,
            valor_conciliar=dados_conciliacao.get('valor'),
            data_conciliar=dados_conciliacao.get('data'),
            descricao_conciliar=dados_conciliacao.get('descricao'),
            fitid_conciliar=dados_conciliacao.get('fitid')
        )

    except Exception as e:
        print(e)
        db.session.rollback()
        dados_conciliacao = session.get('dados_conciliacao', {})
        if dados_conciliacao.get('transacao_id'):
            limpar_dados_conciliacao()
        flash(("Erro ao informar faturamento do comissionado! Contate o suporte.", "warning"))
        return redirect(url_for("listagem_comissionados_a_pagar"))


@app.route("/financeiro/a-pagar/comissionado-a-pagar-massa", methods=["GET", "POST"])
@login_required
@requires_roles
def comissionado_a_pagar_massa():
    try:
        verificar_e_limpar_conciliacao_incorreta('pagamento_comissionado') 

        dados_conciliacao = session.get('dados_conciliacao', {})
        conciliar_transacao_id = dados_conciliacao.get('transacao_id')

        if request.method == "GET":
            ids_selecionados = request.args.get('ids', '')
        else:
            ids_selecionados = request.form.get('ids_registros', '')
        
        if not ids_selecionados:
            flash(("Nenhum registro foi selecionado para faturamento!", "warning"))
            return redirect(url_for("listagem_comissionados_a_pagar"))
        
        ids_list = [int(id.strip()) for id in ids_selecionados.split(',') if id.strip()]

        registros = ComissionadoPagarModel.query.filter(
            ComissionadoPagarModel.id.in_(ids_list),
            ComissionadoPagarModel.situacao_pagamento_id == 2  
        ).all()

        if not registros:
            flash(("Nenhum registro válido encontrado para faturamento!", "warning"))
            return redirect(url_for("listagem_comissionados_a_pagar"))
        
        # Verificar se algum registro já foi faturado
        if len(registros) != len(ids_list):
            flash(("Alguns registros selecionados não estão disponíveis para faturamento!", "warning"))

        # Verificar transação OFX para conciliação
        transacao_ofx = None
        if conciliar_transacao_id:
            transacao_ofx = ImportacaoOfx.query.get(conciliar_transacao_id)

        # Atribui registro operacional a cada registro de comissionado
        for registro in registros:
            if not hasattr(registro, 'registro_operacional') or registro.registro_operacional is None:
                registro_oper = RegistroOperacionalModel.obter_registro_solicitacao_por_id(registro.solicitacao_id)
                registro.registro_operacional = registro_oper
        
        # Processamento de comissionados
        comissionados_dict = {}
        valor_total_geral = 0
        
        for registro in registros:
            if registro.valor_total_a_pagar_100 is None:
                continue
                
            comissionado_id = registro.comissionado_id
            valor_total_geral += registro.valor_total_a_pagar_100
            
            if comissionado_id not in comissionados_dict:
                comissionados_dict[comissionado_id] = {
                    'registros': [],
                    'valor_total': 0,
                    'comissionado': registro.comissionado
                }
        
            comissionados_dict[comissionado_id]['registros'].append(registro)
            comissionados_dict[comissionado_id]['valor_total'] += registro.valor_total_a_pagar_100

        # Processamento de confirmação de faturação
        if request.method == "POST":
            # Processamento de valores editados pelo usuario
            valores_calculados_json = request.form.get("valores_calculados", "")
            valores_calculados = {}

            alteracoes_detectadas = False
            
            if valores_calculados_json:
                valores_calculados = json.loads(valores_calculados_json)

            # Atualizar registros de comissionados com valores calculados
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
                        flash(f"Erro nos valores calculados para registro {registro.id}: {str(e)}", "warning")
                        return redirect(request.url)

            # Salva as alterações de preço de custo e valores totais, se houver
            if alteracoes_detectadas:
                db.session.commit()

            # Recalcula totais após a verificação de edição de valores
            valor_total_geral = 0

            for comissionado_id, dados in comissionados_dict.items():
                dados['valor_total'] = 0  

                for registro in dados['registros']:
                    valor_registro = registro.valor_total_a_pagar_100 or 0
                    if valor_registro > 0:
                        dados['valor_total'] += valor_registro
                        valor_total_geral += valor_registro

            # Valor final a faturar (sem crédito para comissionados)
            valor_final_a_faturar = valor_total_geral

            # Criando detalhes json para frontend
            detalhes_comissionados = []
            for comissionado_id, dados in comissionados_dict.items():
                for reg in dados['registros']:
                    # Para comissionados não há crédito
                    valor_bruto_registro = reg.valor_total_a_pagar_100 or 0
                    valor_credito_registro = 0  # Sempre 0 para comissionados
                    valor_faturado = valor_bruto_registro
                    preco_custo_registro = reg.preco_custo_bitola_100 or 0

                    numero_nf = ""
                    if reg.registro_operacional:
                        if reg.registro_operacional.estorno_nf and reg.registro_operacional.numero_nota_fiscal_estorno:
                            numero_nf = f"{reg.registro_operacional.numero_nota_fiscal_estorno} *"
                        elif reg.registro_operacional.numero_nota_fiscal:
                            numero_nf = reg.registro_operacional.numero_nota_fiscal
                        else:
                            numero_nf = ""

                    detalhes_comissionados.append({
                        "comissionado_a_pagar_id": reg.id,
                        "comissionado_id": comissionado_id,
                        "solicitacao_id": reg.solicitacao_id if reg.solicitacao else "",
                        "comissionado_identificacao": dados['comissionado'].identificacao if dados.get('comissionado') else str(comissionado_id),
                        "cliente": reg.solicitacao.cliente.identificacao if reg.solicitacao and reg.solicitacao.cliente else "",
                        "valor_bruto": valor_bruto_registro or 0,
                        "valor_credito": valor_credito_registro or 0,
                        "valor_faturado": valor_faturado or 0,
                        "nota_fiscal": numero_nf,
                        "peso_ticket": f"{reg.registro_operacional.peso_liquido_ticket}" if reg.registro_operacional and reg.registro_operacional.peso_liquido_ticket else "",
                        "preco_custo": preco_custo_registro,
                        "produto": reg.solicitacao.produto.nome if reg.solicitacao and reg.solicitacao.produto else "",
                        "bitola": reg.solicitacao.bitola.bitola if reg.solicitacao and reg.solicitacao.bitola else "",
                        "data_entrega": reg.data_entrega_ticket.strftime('%d/%m/%Y') if reg.data_entrega_ticket else "",
                        "utiliza_credito": 0,  # Sempre 0 para comissionados
                        "registro_operacional_id": reg.registro_operacional.id if reg.registro_operacional else "",
                        "placa_veiculo": reg.solicitacao.veiculo.placa_veiculo if reg.solicitacao and reg.solicitacao.veiculo else "",
                        "motorista": reg.solicitacao.motorista.nome_completo if reg.solicitacao and reg.solicitacao.motorista else "",
                        "transportadora_id": reg.solicitacao.transportadora_id if reg.solicitacao else "",
                        "transportadora_identificacao": reg.solicitacao.transportadora_exibicao.identificacao if reg.solicitacao else "",
                        "fornecedor_id": reg.solicitacao.fornecedor_id if reg.solicitacao else "",
                        "fornecedor_identificacao": reg.solicitacao.fornecedor.identificacao if reg.solicitacao and reg.solicitacao.fornecedor else ""
                    })
                    
                    PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                        current_user.id,
                        TipoAcaoEnum.CADASTRO,
                        TipoAcaoEnum.CADASTRO.pontos,
                        modulo=f"informar_faturamento_comissionado_{reg.id}_massa",
                    )

            # Criação de novo faturamento
            novo_faturamento = FaturamentoModel(
                usuario_id=current_user.id,
                codigo_faturamento=FaturamentoModel.gerar_codigo_novo_faturamento(),
                valor_total=valor_final_a_faturar,
                ids_comissionados=ids_selecionados,  
                utilizou_credito=False, 
                situacao_pagamento_id=7,
                tipo_operacao=1, # carga
                direcao_financeira=2 # despesa
            )

            # Se o modelo suporta campos extras, adicionar:
            if hasattr(novo_faturamento, 'valor_bruto_total'):
                novo_faturamento.valor_bruto_total = valor_total_geral
            if hasattr(novo_faturamento, 'valor_credito_aplicado'):
                novo_faturamento.valor_credito_aplicado = 0  # Sempre 0 para comissionados
            if hasattr(novo_faturamento, 'valor_fornecedor'):
                novo_faturamento.valor_fornecedor = 0  # Para comissionado, valor fornecedor é 0
            if hasattr(novo_faturamento, 'valor_transportadora'):
                novo_faturamento.valor_transportadora = 0  # Para comissionado, valor transportadora é 0
            if hasattr(novo_faturamento, 'valor_extrator'):
                novo_faturamento.valor_extrator = 0  # Para comissionado, valor extrator é 0
            if hasattr(novo_faturamento, 'valor_comissionado'):
                novo_faturamento.valor_comissionado = valor_final_a_faturar  # Valor vai para comissionado

            # Salvar detalhes (detalhes_comissionados para comissionados, arrays vazios para outros)
            novo_faturamento.salvar_detalhes([], [], [], detalhes_comissionados)
            db.session.add(novo_faturamento)

            if transacao_ofx and not transacao_ofx.conciliado:
                transacao_ofx.conciliado = True
                transacao_ofx.tipo_conciliacao = 'faturamento_comissionado_massa'
                transacao_ofx.pagamento_id = novo_faturamento.id
                transacao_ofx.data_conciliacao = datetime.now()
                transacao_ofx.usuario_conciliacao_id = current_user.id
                transacao_ofx.observacoes_conciliacao = f"Conciliado com faturamento em massa de comissionado ID {novo_faturamento.id}"

            try:
                # Atualizar situação financeira dos registros de comissionado a pagar
                for comissionado_id, dados in comissionados_dict.items():
                    for reg in dados['registros']:
                        reg.utiliza_credito = 0  # Sempre 0 para comissionados
                        reg.valor_credito_100 = 0  # Sempre 0 para comissionados
                        reg.situacao_pagamento_id = 5  # 5 = Faturado

                db.session.commit()

                if conciliar_transacao_id:
                    limpar_dados_conciliacao()
                    flash(("Faturamento em massa e transação OFX conciliada com sucesso!", "success"))
                    return redirect(url_for("listagem_ofx"))
                else:
                    flash(("Faturamento em massa realizado com sucesso!", "success"))
                    return redirect(url_for("listagem_faturamentos_cargas_a_pagar"))
                    
            except Exception as e:
                db.session.rollback()
                flash((f"Erro ao salvar faturamento: {str(e)}", "warning"))
                return redirect(request.url)

        return render_template(
            "financeiro/informar_pagamento/informar_pagamento_comissionado_massa.html",
            dados_corretos=request.form,
            registros=registros,
            comissionados_dict=comissionados_dict,
            valor_total_geral=valor_total_geral,
            ids_selecionados=ids_selecionados,
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
        return redirect(url_for("listagem_comissionados_a_pagar"))


@app.route("/financeiro/a-pagar/comissionado-a-pagar/cancelar-informe/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def cancelar_pagamento_comissionado(id):
    try:
        registro = ComissionadoPagarModel.obter_comissionado_a_pagar_id(id)
        if not registro:
            flash(("Registro não encontrado", "warning"))
            return redirect(url_for("listagem_comissionados_a_pagar"))

        if registro.situacao_pagamento_id != 1:
            flash(("Só é possível cancelar faturamentos já informados.", "warning"))
            return redirect(url_for("listagem_comissionados_a_pagar"))

        valor_saldo = registro.valor_saldo_debitado_100 or 0
        usou_saldo = bool(registro.utiliza_saldo_movimentacao)

        registro.situacao_pagamento_id = 2

        mov_orig = MovimentacaoFinanceiraModel.query.filter_by(
            comissionado_pagamento_id=registro.id, deletado=False
        ).first()
        if mov_orig:
            mov_orig.deletado = True

        if usou_saldo and valor_saldo > 0:
            mov_est_din = MovimentacaoFinanceiraModel(
                tipo_movimentacao=5,
                usuario_id=current_user.id,
                data_movimentacao=datetime.now(),
                comissionado_pagamento_id=registro.id,
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

    return redirect(url_for("listagem_comissionados_a_pagar"))