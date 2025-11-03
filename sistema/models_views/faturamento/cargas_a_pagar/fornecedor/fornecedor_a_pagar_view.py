from datetime import datetime
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem, formatar_data_para_brl
from flask import render_template, request, redirect, url_for, flash, session, jsonify, json
from flask_login import login_required, current_user
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.upload_arquivo.upload_arquivo_model import UploadArquivoModel
from sistema.models_views.faturamento.cargas_a_pagar.fornecedor.fornecedor_a_pagar_model import FornecedorPagarModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.controle_carga.produto_model import ProdutoModel
from sistema.models_views.financeiro.situacao_pagamento_model import SituacaoPagamentoModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.controle_carga.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.faturamento.controle_credito.credito_agrupado.credito_fornecedor_model import CreditoFornecedorModel
from sistema.models_views.faturamento.controle_credito.credito_agrupado.credito_freteiro_model import CreditoFreteiroModel
from sistema.models_views.faturamento.controle_credito.credito_agrupado.credito_extrator_model import CreditoExtratorModel
from sistema.models_views.faturamento.controle_credito.extrato_credito.extrato_credito_fornecedor_model import ExtratoCreditoFornecedorModel
from sistema.models_views.faturamento.controle_credito.extrato_credito.extrato_credito_freteiro_model import ExtratoCreditoFreteiroModel
from sistema.models_views.faturamento.controle_credito.extrato_credito.extrato_credito_extrator_model import ExtratoCreditoExtratorModel
from sistema.models_views.financeiro.movimentacao_financeira.movimentacao_financeira_model import MovimentacaoFinanceiraModel
from sistema.models_views.financeiro.movimentacao_financeira.saldo_movimentacao_financeira_model import SaldoMovimentacaoFinanceiraModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.configuracoes_gerais.conta_bancaria.conta_bancaria_model import ContaBancariaModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_view import (inicializar_categorias_padrao, obter_subcategorias_recursivo)
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_view import (inicializar_categorias_padrao_categorizacao_fiscal, obter_subcategorias_recursivo_categorizacao_fiscal)
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_model import CategorizacaoFiscalModel
from sistema.models_views.faturamento.cargas_a_pagar.transportadora.frete_a_pagar_model import FretePagarModel
from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx
from sistema.models_views.importacao_ofx.importacao_ofx_view import limpar_dados_conciliacao
from sistema.models_views.importacao_ofx.importacao_ofx_view import verificar_e_limpar_conciliacao_incorreta
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema.models_views.faturamento.faturamento_model import FaturamentoModel
from sistema.models_views.gerenciar.motorista.motorista_model import MotoristaModel
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema._utilitarios import *
from sistema._utilitarios.utilitario_semanal import UtilitariosSemana

@app.route("/financeiro/api/creditos-disponiveis/<tipo_entidade>/<int:entidade_id>", methods=["GET"])
@login_required
@requires_roles
def api_creditos_disponiveis(tipo_entidade, entidade_id):
    """
    API para buscar créditos individuais disponíveis por entidade
    """
    try:
        creditos = []
        
        if tipo_entidade == 'fornecedor':
            creditos = ExtratoCreditoFornecedorModel.obter_creditos_disponiveis_fornecedor(entidade_id)
        elif tipo_entidade == 'transportadora':
            creditos = ExtratoCreditoFreteiroModel.obter_creditos_disponiveis_transportadora(entidade_id)
        elif tipo_entidade == 'extrator':
            creditos = ExtratoCreditoExtratorModel.obter_creditos_disponiveis_extrator(entidade_id)
        else:
            return jsonify({'error': 'Tipo de entidade inválido'}), 400
            
        return jsonify({
            'success': True,
            'creditos': creditos,
            'total_creditos': len(creditos),
            'valor_total': sum(c['valor_credito_100'] for c in creditos)
        })
        
    except Exception as e:
        print(f"[ERROR api_creditos_disponiveis] {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@app.route("/financeiro/fornecedores-a-faturar", methods=["GET"])
@login_required
@requires_roles
def listagem_fornecedores_a_pagar():
    from sistema.models_views.gerenciar.fornecedor.fornecedor_model import FornecedorModel
    
    bitolas = BitolaModel.listar_bitolas_ativas()
    produtos = ProdutoModel.listar_produtos()
    statusPagamentos = SituacaoPagamentoModel.listar_status_filtro()
    fornecedores = FornecedorModel.listar_fornecedores_ativos()
    motoristas = MotoristaModel.listar_motoristas_ativos()
    transportadoras = TransportadoraModel.listar_transportadoras_ativas()
    clientes = ClienteModel.listar_clientes_ativos()
    
    # Obter semanas disponíveis
    semanas_disponiveis = UtilitariosSemana.obter_semanas_do_mes_atual()
    semana_atual_info = None
    valor_padrao_semana = None
    
    if semanas_disponiveis:
        valor_padrao_semana = semanas_disponiveis[0]["valor"]
        semana_atual_info = semanas_disponiveis[0]

    parametros_filtro = ["tipo_filtro", "semanaSelecionada", "dataInicio", "dataFim", "numeroNF", "placaCarga", "motoristaCarga",
                        "produtoCarga", "bitolaCarga", "transportadoraCarga", "fornecedorCarga", "clienteCarga", "statusPagamentoCarga"]
    
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

        registros = FornecedorPagarModel.filtrar_fornecedores_agrupados(
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
    else:
        registros = FornecedorPagarModel.obter_fornecedores_agrupados()

    return render_template(
        "/financeiro/fornecedores_a_pagar_listagem.html",
        registros=registros,
        bitolas=bitolas,
        produtos=produtos,
        motoristas=motoristas,
        transportadoras=transportadoras,
        clientes=clientes,
        statusPagamentos=statusPagamentos,
        fornecedores=fornecedores,
        dados_corretos=request.args,
        semanas_disponiveis=semanas_disponiveis,
        tipo_filtro=request.args.get("tipo_filtro", "semanal")
    )


@app.route("/relatorios/relatorios-financeiros/a-pagar-fornecedores", methods=["GET", "POST"])
@login_required
@requires_roles
def relatorio_a_pagar_fornecedores():
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    dataHoje = datetime.now().strftime("%d-%m-%Y")
    bitola = BitolaModel.listar_bitolas_ativas()
    produtos = ProdutoModel.listar_produtos()
    statusPagamentos = SituacaoPagamentoModel.listar_status()
    
    def obter_registros_com_filtros():
        # Para POST, primeiro verifica se há filtros no form, senão usa args
        filtros_source = request.form if request.method == "POST" and any(request.form.values()) else request.args
        
        if any(filtros_source.values()):
            data_inicio = filtros_source.get("dataInicio")
            data_fim = filtros_source.get("dataFim")
            placa = filtros_source.get("placaCargaCliente")
            motorista = filtros_source.get("motoristaCargaCliente")
            transportadora = filtros_source.get("tranpostadoraCargaCliente")
            fornecedor = filtros_source.get("fornecedorCargaCliente")
            cliente = filtros_source.get("clienteCarga")
            numero_nf = filtros_source.get("numeroNfCliente")
            incompleto = filtros_source.get("registroIncompleto")
            statusPagamento = filtros_source.get("statusPagamento") or "Pendente"
            
            incompleto_bool = None
            if incompleto == "1":
                incompleto_bool = True
            elif incompleto == "0":
                incompleto_bool = False
            
            return FornecedorPagarModel.filtrar_fornecedores_agrupados(
                data_inicio=data_inicio,
                data_fim=data_fim,
                placa=placa,
                motorista=motorista,
                transportadora=transportadora,
                fornecedor=fornecedor,
                cliente=cliente,
                numero_nf=numero_nf,
                statusPagamento=statusPagamento
            )
        else:
            return FornecedorPagarModel.obter_fornecedores_agrupados()
    
    # Obtém os parâmetros de filtro corretos
    if request.method == "POST":
        # Para POST, preserva os filtros do args ou form
        dados_corretos = request.form if any(request.form.get(k) for k in ['dataInicio', 'dataFim', 'placaCargaCliente', 'motoristaCargaCliente', 'tranpostadoraCargaCliente', 'fornecedorCargaCliente', 'clienteCarga', 'numeroNfCliente', 'registroIncompleto', 'statusPagamento']) else request.args
    else:
        dados_corretos = request.args
    
    registros = obter_registros_com_filtros()
    
    if request.method == "POST":
        # Garantir que a exportação use os mesmos filtros
        registros_exportacao = registros  # Reutiliza os registros já filtrados

        if request.form.get("exportar_pdf"):
            logo_path = obter_url_absoluta_de_imagem("logo.png")
            html = render_template(
                "relatorios/relatorios_financeiros/relatorio_a_pagar_fornecedor/exportar_relatorio_a_pagar_fornecedor_pdf.html",
                logo_path=logo_path,
                changelog=changelog,
                dataHoje=dataHoje,
                dados_corretos=dados_corretos,
                registros=registros_exportacao
            )

            nome_arquivo_saida = f"relacao_fornecedores_a_pagar_{dataHoje}"
            return ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida, "Landscape")
        
        if request.form.get("exportar_excel"):
            dados_excel = []
            registros_por_origem = {}
            
            for item in registros_exportacao:
                origem = item.get("origem", "Sem origem")
                if origem not in registros_por_origem:
                    registros_por_origem[origem] = {}
                    
                produto = item.get("produto", "Sem produto")
                if produto not in registros_por_origem[origem]:
                    registros_por_origem[origem][produto] = []
                    
                registros_por_origem[origem][produto].append(item)

            for origem in sorted(registros_por_origem.keys()):
                produtos_origem = registros_por_origem[origem]
                
                dados_excel.append({
                    "Origem": origem.upper(),
                    "Data Entrega": "",
                    "Placa/Motorista": "",
                    "Transportadora": "",
                    "Bitola": "",
                    "Peso Ticket": "",
                    "Número NF": "",
                    "A pagar fornecedor": "",
                    "Status pagamento": "",
                    "Incompleto": "",
                })
                
                for produto in sorted(produtos_origem.keys()):
                    registros_produto = produtos_origem[produto]
                    
                    dados_excel.append({
                        "Origem": f"  PRODUTO: {produto}",
                        "Data Entrega": "",
                        "Placa/Motorista": "",
                        "Transportadora": "",
                        "Bitola": "",
                        "Peso Ticket": "",
                        "Número NF": "",
                        "A pagar fornecedor": "",
                        "Status pagamento": "",
                        "Incompleto": "",
                    })
                    
                    total_produto = 0
                    
                    for item in registros_produto:
                        registro = item["registro"]
                        
                        motorista_nome = ""
                        if (registro.solicitacao and 
                            registro.solicitacao.motorista and 
                            registro.solicitacao.motorista.nome_completo):
                            nome_split = registro.solicitacao.motorista.nome_completo.split()
                            if len(nome_split) > 1:
                                motorista_nome = f"{nome_split[0]} {nome_split[1][0]}."
                            else:
                                motorista_nome = nome_split[0]
                        
                        placa = (registro.solicitacao.veiculo.placa_veiculo 
                                if registro.solicitacao and registro.solicitacao.veiculo 
                                and registro.solicitacao.veiculo.placa_veiculo else "")
                        placa_motorista = f"{placa} | {motorista_nome}" if motorista_nome else placa
                        
                        transportadora = ""
                        if (registro.solicitacao and 
                            registro.solicitacao.transportadora_exibicao and 
                            registro.solicitacao.transportadora_exibicao.identificacao):
                            transportadora = registro.solicitacao.transportadora_exibicao.identificacao
                        else:
                            transportadora = ""
                        
                        bitola = ""
                        if (registro.solicitacao and 
                            registro.solicitacao.bitola and 
                            registro.solicitacao.bitola.bitola):
                            bitola = registro.solicitacao.bitola.bitola
                        else:
                            bitola = ""
                        
                        peso_ticket = ""
                        if hasattr(item, 'registro_operacional') and item.registro_operacional.peso_liquido_ticket:
                            peso_ticket = f"{item.registro_operacional.peso_liquido_ticket} Ton."
                        else:
                            peso_ticket = "Sem peso"
                        
                        numero_nf = ""
                        if hasattr(item, 'registro_operacional'):
                            if item.registro_operacional.estorno_nf:
                                numero_nf = f"{item.registro_operacional.numero_nota_fiscal_estorno} *"
                            elif item.registro_operacional.numero_nota_fiscal:
                                numero_nf = item.registro_operacional.numero_nota_fiscal
                            else:
                                numero_nf = ""
                        else:
                            numero_nf = ""
                        
                        valor_pagar = 0
                        if registro.valor_total_a_pagar_100:
                            valor_pagar = registro.valor_total_a_pagar_100 / 100
                            total_produto += valor_pagar
                        
                        status = registro.situacao.situacao if registro.situacao else "Pendente"
                        incompleto = "Sim" if registro.incompleto else "Não"
                        
                        dados_excel.append({
                            "Origem": "",
                            "Data Entrega": (registro.data_entrega_ticket.strftime("%d/%m/%Y") 
                                        if registro.data_entrega_ticket else ""),
                            "Placa/Motorista": placa_motorista,
                            "Transportadora": transportadora,
                            "Bitola": bitola,
                            "Peso Ticket": peso_ticket,
                            "Número NF": numero_nf,
                            "A pagar fornecedor": f"{valor_pagar:,.2f}" if valor_pagar > 0 else "",
                            "Status pagamento": status,
                            "Incompleto": incompleto,
                        })
                    
                    if registros_produto and total_produto > 0:
                        dados_excel.append({
                            "Origem": "",
                            "Data Entrega": "",
                            "Placa/Motorista": "",
                            "Transportadora": "",
                            "Bitola": "",
                            "Peso Ticket": "",
                            "Número NF": "",
                            "A pagar fornecedor": f"TOTAL A PAGAR: R$ {total_produto:,.2f}",
                            "Status pagamento": "",
                            "Incompleto": "",
                        })
                    
                    dados_excel.append({
                        "Origem": "",
                        "Data Entrega": "",
                        "Placa/Motorista": "",
                        "Transportadora": "",
                        "Bitola": "",
                        "Peso Ticket": "",
                        "Número NF": "",
                        "A pagar fornecedor": "",
                        "Status pagamento": "",
                        "Incompleto": "",
                    })
                
                dados_excel.append({
                    "Origem": "",
                    "Data Entrega": "",
                    "Placa/Motorista": "",
                    "Transportadora": "",
                    "Bitola": "",
                    "Peso Ticket": "",
                    "Número NF": "",
                    "A pagar fornecedor": "",
                    "Status pagamento": "",
                    "Incompleto": "",
                })

            nome_arquivo_saida = f"relatorio-fornecedores-a-pagar-{dataHoje}"
            return ManipulacaoArquivos.exportar_excel(dados_excel, nome_arquivo_saida)

    return render_template(
        "relatorios/relatorios_financeiros/relatorio_a_pagar_fornecedor/relatorio_a_pagar_fornecedor.html",
        registros=registros,
        bitola=bitola,
        produtos=produtos,
        statusPagamentos=statusPagamentos,
        dados_corretos=dados_corretos,
    )


@app.route("/financeiro/a-pagar/fornecedor-a-pagar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def fornecedor_a_pagar(id):
    try:
        verificar_e_limpar_conciliacao_incorreta('pagamento_fornecedor') 
        dados_conciliacao = session.get('dados_conciliacao', {})
        conciliar_transacao_id = dados_conciliacao.get('transacao_id')

        registro = FornecedorPagarModel.obter_fornecedor_a_pagar_id(id)
        if not registro:
            flash(("Registro não encontrado", "warning"))
            return redirect(url_for("listagem_fornecedores_a_pagar"))

        if registro.valor_total_a_pagar_100 == None:
            flash(("Não é possível informar faturamento de valor nulo", "warning"))
            return redirect(url_for("listagem_fornecedores_a_pagar"))
        
        if registro.situacao_pagamento_id == 5:
            flash(("Registro já consta como faturado!", "warning"))
            return redirect(url_for("listagem_fornecedores_a_pagar"))

        saldo_credito = CreditoFornecedorModel.valor_credito_disponivel(registro.fornecedor_id)
        credito_disponivel = (saldo_credito.valor_total_credito_100 if saldo_credito else 0)
        
        creditos_individuais = ExtratoCreditoFornecedorModel.obter_creditos_disponiveis_fornecedor(registro.fornecedor_id)

        registro_oper = RegistroOperacionalModel.obter_registro_solicitacao_por_id(
            registro.solicitacao_id
        )
        if not registro_oper:
            flash(("Registro operacional não encontrado", "warning"))
            return redirect(url_for("listagem_fornecedores_a_pagar"))
        
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
            valor_pendente = registro.valor_total_a_pagar_100

            creditos_selecionados_ids = request.form.getlist("creditos_selecionados")
            
            if usar_credito == "sim" and not creditos_selecionados_ids:
                flash(("Para usar crédito, você deve selecionar pelo menos um crédito disponível!", "warning"))
                return redirect(request.url)
            
            if usar_credito != "sim" and creditos_selecionados_ids:
                flash(("Você selecionou créditos mas não marcou para usar crédito. Marque a opção 'Usar Crédito' ou desmarque os créditos.", "warning"))
                return redirect(request.url)
            
            # Verificar se há créditos disponíveis apenas quando não há seleção individual
            if usar_credito == "sim" and credito_disponivel == 0 and not creditos_selecionados_ids:
                flash(("O fornecedor não possui crédito disponível!", "warning"))
                return redirect(request.url)
            
            detalhes_creditos_utilizados = []
            total_credito_aplicado = 0
            
            if usar_credito == "sim":
                total_creditos_selecionados = 0
                
                if creditos_selecionados_ids:
                    creditos_utilizados = []
                    
                    for credito_id in creditos_selecionados_ids:
                        credito = ExtratoCreditoFornecedorModel.query.filter_by(id=credito_id, ativo=True, credito_utilizado=False).first()
                        if credito and credito.fornecedor_id == registro.fornecedor_id:
                            if credito.valor_credito_100 == 0:
                                flash(f"O crédito selecionado '{credito.descricao}' possui valor zerado e não pode ser utilizado!", "warning")
                                return redirect(request.url)
                            
                            creditos_utilizados.append(credito)
                            total_creditos_selecionados += credito.valor_credito_100
                    if total_creditos_selecionados == 0:
                        flash(("O total dos créditos selecionados é zero.", "warning"))
                        return redirect(request.url)
                    if creditos_utilizados and total_creditos_selecionados != 0:  # Permite créditos negativos
                        # Para créditos negativos, usa o valor total; para positivos, limita ao valor pendente
                        if total_creditos_selecionados < 0:
                            valor_credito_a_usar = total_creditos_selecionados  # Usa valor negativo completo (débito)
                        else:
                            valor_credito_a_usar = min(total_creditos_selecionados, valor_pendente)  # Limita crédito positivo
                        
                        valor_credito_restante = abs(valor_credito_a_usar)  # Trabalha com valor absoluto para controle
                        
                        for credito in creditos_utilizados:
                            if valor_credito_restante <= 0:
                                break
                                
                            # Para créditos negativos, preservar o sinal negativo
                            if credito.valor_credito_100 < 0:
                                valor_a_debitar = -min(abs(credito.valor_credito_100), valor_credito_restante)
                            else:
                                valor_a_debitar = min(abs(credito.valor_credito_100), valor_credito_restante)
                            
                            detalhes_creditos_utilizados.append({
                                'tipo': 'fornecedor',
                                'credito_id': credito.id,
                                'entidade_id': credito.fornecedor_id,
                                'entidade_nome': registro.fornecedor.identificacao if registro.fornecedor else 'N/A',
                                'valor': abs(valor_a_debitar),
                                'descricao': credito.descricao,
                                'data_movimentacao': credito.data_movimentacao.strftime('%d/%m/%Y') if credito.data_movimentacao else ''
                            })
                            
                            credito.credito_utilizado = True
                            db.session.add(credito)
                            
                            if abs(valor_a_debitar) < abs(credito.valor_credito_100):
                                valor_restante = credito.valor_credito_100 - abs(valor_a_debitar) if credito.valor_credito_100 > 0 else credito.valor_credito_100 + abs(valor_a_debitar)
                                
                                credito_restante = ExtratoCreditoFornecedorModel(
                                    tipo_movimentacao=1,
                                    descricao=f"Crédito restante após uso parcial - Original: {credito.descricao}",
                                    data_movimentacao=datetime.now(),
                                    fornecedor_id=registro.fornecedor_id,
                                    valor_credito_100=valor_restante,
                                    usuario_id=current_user.id,
                                    ativo=False
                                )
                                db.session.add(credito_restante)
                            
                            extrato_debito = ExtratoCreditoFornecedorModel(
                                tipo_movimentacao=2,
                                descricao=f"Débito de crédito para faturamento individual - Fornecedor: {registro.fornecedor.identificacao}",
                                data_movimentacao=datetime.now(),
                                fornecedor_id=registro.fornecedor_id,
                                valor_credito_100=abs(valor_a_debitar),
                                usuario_id=current_user.id,
                                ativo=False
                            )
                            db.session.add(extrato_debito)
                            
                            total_credito_aplicado += valor_a_debitar
                            valor_credito_restante -= abs(valor_a_debitar)
                        
                        saldo_consolidado = CreditoFornecedorModel.valor_credito_disponivel(registro.fornecedor_id)
                        if saldo_consolidado:
                            saldo_consolidado.valor_total_credito_100 -= total_credito_aplicado
                            db.session.add(saldo_consolidado)
                        
                        registro.utiliza_credito = 1
                        registro.valor_credito_100 = total_credito_aplicado
                    else:
                        registro.utiliza_credito = 0
                        registro.valor_credito_100 = 0
                else:
                    valor_debito = min(credito_disponivel, valor_pendente)
                    
                    if valor_debito > 0:
                        registro.utiliza_credito = 1
                        registro.valor_credito_100 = valor_debito
                        
                        creditos_disponiveis = ExtratoCreditoFornecedorModel.obter_creditos_disponiveis_fornecedor(registro.fornecedor_id)
                        valor_restante_para_usar = valor_debito
                        
                        for credito_disponivel_obj in creditos_disponiveis:
                            if valor_restante_para_usar <= 0:
                                break
                                
                            valor_credito_a_usar = min(credito_disponivel_obj.valor_credito_100, valor_restante_para_usar)
                            
                            credito_disponivel_obj.credito_utilizado = True
                            db.session.add(credito_disponivel_obj)
                            
                            if valor_credito_a_usar < credito_disponivel_obj.valor_credito_100:
                                valor_restante = credito_disponivel_obj.valor_credito_100 - valor_credito_a_usar
                                
                                credito_restante = ExtratoCreditoFornecedorModel(
                                    tipo_movimentacao=1,
                                    descricao=f"Crédito restante após uso parcial automático - Original: {credito_disponivel_obj.descricao}",
                                    data_movimentacao=datetime.now(),
                                    fornecedor_id=registro.fornecedor_id,
                                    valor_credito_100=valor_restante,
                                    usuario_id=current_user.id,
                                    ativo=True
                                )
                                db.session.add(credito_restante)
                            
                            valor_restante_para_usar -= valor_credito_a_usar
                        
                        extrato = ExtratoCreditoFornecedorModel(
                            tipo_movimentacao=2,
                            descricao="Débito de crédito para faturamento de fornecedor",
                            data_movimentacao=datetime.now(),
                            fornecedor_id=registro.fornecedor_id,
                            valor_credito_100=valor_debito,
                            usuario_id=current_user.id,
                            ativo=True
                        )
                        db.session.add(extrato)
                        
                        saldo_credito_obj = CreditoFornecedorModel.valor_credito_disponivel(registro.fornecedor_id)
                        if saldo_credito_obj:
                            saldo_credito_obj.valor_total_credito_100 = (credito_disponivel - valor_debito)
                    else:
                        registro.utiliza_credito = 0
                        registro.valor_credito_100 = 0
            else:
                registro.utiliza_credito = 0
                registro.valor_credito_100 = 0

            registro.situacao_pagamento_id = 5

            valor_bruto = registro.valor_total_a_pagar_100 or 0
            valor_credito = registro.valor_credito_100 or 0
            # Se crédito é negativo, ele deve somar ao valor (débito): valor_bruto + abs(credito_negativo)  
            # Se crédito é positivo, ele deve subtrair do valor (crédito): valor_bruto - credito_positivo
            if valor_credito < 0:
                valor_liquido = valor_bruto + abs(valor_credito)  # Soma débito (crédito negativo)
            else:
                valor_liquido = valor_bruto - valor_credito       # Subtrai crédito (crédito positivo)

            novo_faturamento = FaturamentoModel(
                usuario_id=current_user.id,
                codigo_faturamento=FaturamentoModel.gerar_codigo_novo_faturamento(),
                valor_total=valor_liquido,
                ids_fornecedores=str(registro.id),
                ids_fretes=None,
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
                novo_faturamento.valor_fornecedor = valor_liquido
            if hasattr(novo_faturamento, 'valor_transportadora'):
                novo_faturamento.valor_transportadora = 0

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

            detalhes_fornecedores = [{
                "fornecedor_a_pagar_id": registro.id,
                "fornecedor_id": registro.fornecedor_id,
                "solicitacao_id": registro.solicitacao_id if registro.solicitacao else "",
                "fornecedor_identificacao": registro_oper.solicitacao.fornecedor.identificacao if registro_oper and registro_oper.solicitacao and registro_oper.solicitacao.fornecedor else str(registro.fornecedor_id),
                "cliente": registro.solicitacao.cliente.identificacao if registro.solicitacao and registro.solicitacao.cliente else "",
                "transportadora_id": registro_oper.solicitacao.transportadora_id if registro_oper and registro_oper.solicitacao else "",
                "transportadora_identificacao": registro_oper.solicitacao.transportadora_exibicao.identificacao if registro_oper and registro_oper.solicitacao and registro_oper.solicitacao.transportadora_exibicao else "",
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
                fornecedores=detalhes_fornecedores, 
                transportadoras=[],
                credito_fornecedor=detalhes_creditos_utilizados,
                credito_transportadora=[]
            )
            
            db.session.add(novo_faturamento)

            if transacao_ofx and not transacao_ofx.conciliado:
                transacao_ofx.conciliado = True
                transacao_ofx.tipo_conciliacao = 'faturamento_fornecedor'
                transacao_ofx.pagamento_id = registro.id
                transacao_ofx.data_conciliacao = datetime.now()
                transacao_ofx.usuario_conciliacao_id = current_user.id
                transacao_ofx.observacoes_conciliacao = f"Conciliado com faturamento de fornecedor ID {registro.id}"

            PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                current_user.id,
                TipoAcaoEnum.CADASTRO,
                TipoAcaoEnum.CADASTRO.pontos,
                modulo="informar_faturamento_fornecedor",
            )
            db.session.commit()
            if conciliar_transacao_id:
                limpar_dados_conciliacao()
                flash(("Faturamento informado e transação OFX conciliada com sucesso!", "success"))
                return redirect(url_for("listagem_ofx"))
            else:
                flash(("Faturamento informado com sucesso!", "success"))
                return redirect(url_for("listagem_fornecedores_a_pagar"))

        return render_template(
            "financeiro/informar_pagamento/informar_pagamento_fornecedor.html",
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
        print("[ERROR fornecedor_a_pagar]", e)
        db.session.rollback()
        dados_conciliacao = session.get('dados_conciliacao', {})
        if dados_conciliacao.get('transacao_id'):
            limpar_dados_conciliacao()
            print("[DEBUG] Dados de conciliação limpos devido ao erro")
        flash(("Erro ao informar faturamento do fornecedor! Contate o suporte.", "warning"))
        return redirect(url_for("listagem_fornecedores_a_pagar"))
       
@app.route("/financeiro/a-pagar/fornecedor-a-pagar-massa", methods=["GET", "POST"])
@login_required
@requires_roles
def fornecedor_a_pagar_massa():
    try:
        campos_obrigatorios = {}
        campos_erros = {}
        
        fretes_dict = {}
        valor_total_fretes = 0
        total_registros_fretes = 0
        creditos_selecionados = {}
      
        if request.method == "GET":
            ids_selecionados = request.args.get('ids', '')
        else:
            ids_selecionados = request.form.get('ids_registros', '')
        
        if not ids_selecionados:
            flash(("Nenhum registro foi selecionado para faturamento!", "warning"))
            return redirect(url_for("listagem_fornecedores_a_pagar"))
        
        ids_list = [int(id.strip()) for id in ids_selecionados.split(',') if id.strip()]

        # ========================
        # PROCESSAR FRETES (GET E POST)
        # ========================
        fretes_selecionados = ''
        if request.method == "GET":
            fretes_selecionados = request.args.get('fretes', '')
        else:  # POST
            fretes_selecionados = request.form.get('ids_fretes', '')  # Pode vir de campo hidden
            # Se não vir do form, tentar pegar da query string novamente
            if not fretes_selecionados:
                fretes_selecionados = request.args.get('fretes', '')
                
        if fretes_selecionados:
            try:
                fretes_ids = [int(id.strip()) for id in fretes_selecionados.split(',') if id.strip()]
                fretes_list = FretePagarModel.query.filter(
                    FretePagarModel.id.in_(fretes_ids),
                    FretePagarModel.situacao_pagamento_id == 2 
                ).all()

                for frete in fretes_list:
                    if not hasattr(frete, 'registro_operacional') or frete.registro_operacional is None:
                        registro_oper = RegistroOperacionalModel.obter_registro_solicitacao_por_id(frete.solicitacao_id)
                        frete.registro_operacional = registro_oper
                
                # Agrupar fretes por transportadora
                for frete in fretes_list:
                    transportadora_id = frete.transportadora_id
                    
                    if transportadora_id not in fretes_dict:
                        saldo_credito_transp = CreditoFreteiroModel.obtem_registro_id(transportadora_id)
                        credito_disponivel_transp = saldo_credito_transp.valor_total_credito_100 if saldo_credito_transp else 0
                        
                        # Buscar créditos individuais disponíveis da transportadora
                        creditos_individuais_transp = ExtratoCreditoFreteiroModel.obter_creditos_disponiveis_transportadora(transportadora_id)
                        
                        fretes_dict[transportadora_id] = {
                            'fretes': [],
                            'registros_operacionais': [],
                            'valor_total': 0,
                            'transportadora': frete.transportadora,
                            'credito_disponivel': credito_disponivel_transp or 0,
                            'creditos_individuais': creditos_individuais_transp,
                            'saldo_credito_obj': saldo_credito_transp or 0
                        }
                    
                    fretes_dict[transportadora_id]['fretes'].append(frete)
                    fretes_dict[transportadora_id]['valor_total'] += frete.valor_total_a_pagar_100 # Soma de todos os valores a pagar de fretes

                    # Adicionar registro operacional correspondente
                    if frete.registro_operacional:
                        fretes_dict[transportadora_id]['registros_operacionais'].append(frete.registro_operacional)
            except ValueError as e:
                flash(("IDs de fretes inválidos!", "warning"))
        
        # Calcular totais dos fretes
        if fretes_dict:
            for transportadora_id, dados_transportadora in fretes_dict.items():
                valor_total_fretes += dados_transportadora['valor_total']
                total_registros_fretes += len(dados_transportadora['fretes'])
        
        # Busca registros operacionais associados aos fornecedores
        registros = FornecedorPagarModel.query.filter(
            FornecedorPagarModel.id.in_(ids_list),
            FornecedorPagarModel.situacao_pagamento_id == 2
        ).all()

        if not registros:
            flash(("Nenhum registro válido encontrado para faturamento!", "warning"))
            return redirect(url_for("listagem_fornecedores_a_pagar"))
        
        # Verificar se algum registro já foi pago
        if len(registros) != len(ids_list):
            flash(("Alguns registros selecionados não estão disponíveis para faturamento!", "warning"))


        # Atribui registro operacional a cada registro de fornecedor
        for registro in registros:
            if not hasattr(registro, 'registro_operacional') or registro.registro_operacional is None:
                registro_oper = RegistroOperacionalModel.obter_registro_solicitacao_por_id(registro.solicitacao_id)
                registro.registro_operacional = registro_oper

        # Processamento de fornecedores
        fornecedores_dict = {}
        valor_total_geral = 0
        
        for registro in registros:
            if registro.valor_total_a_pagar_100 is None:
                continue
            
            # Obter o fornecedor id
            fornecedor_id = registro.fornecedor_id

            # Somar valor total geral
            valor_total_geral += registro.valor_total_a_pagar_100

            # Se o fornecedor ainda não estiver no dicionário
            if fornecedor_id not in fornecedores_dict:
                saldo_credito = CreditoFornecedorModel.valor_credito_disponivel(fornecedor_id)
                credito_disponivel = saldo_credito.valor_total_credito_100 if saldo_credito else 0
                
                # Buscar créditos individuais disponíveis
                creditos_individuais = ExtratoCreditoFornecedorModel.obter_creditos_disponiveis_fornecedor(fornecedor_id)
                
                fornecedores_dict[fornecedor_id] = {
                    'registros': [],
                    'valor_total': 0,
                    'credito_disponivel': credito_disponivel or 0,
                    'creditos_individuais': creditos_individuais,
                    'saldo_credito_obj': saldo_credito or 0,
                    'fornecedor': None
                }
            
            fornecedores_dict[fornecedor_id]['registros'].append(registro)
            fornecedores_dict[fornecedor_id]['valor_total'] += registro.valor_total_a_pagar_100
            
            # Associar fornecedor
            if not fornecedores_dict[fornecedor_id]['fornecedor']:
                if (registro.registro_operacional and 
                    registro.registro_operacional.solicitacao and 
                    registro.registro_operacional.solicitacao.fornecedor):
                    fornecedores_dict[fornecedor_id]['fornecedor'] = registro.registro_operacional.solicitacao.fornecedor
        
        # Calculos totais finais
        valor_total_geral_com_fretes = valor_total_geral + valor_total_fretes
        total_registros_completo = len(registros) + total_registros_fretes

        # Crédito total dos fornecedores
        total_credito_fornecedores = sum(f['credito_disponivel'] for f in fornecedores_dict.values())

        # Crédito total das transportadoras (quando há fretes)
        total_credito_transportadoras = 0
        if fretes_dict:
            total_credito_transportadoras = sum(f['credito_disponivel'] for f in fretes_dict.values())

        # Crédito disponivel geral (fornecedores + transportadoras)
        total_credito_disponivel_geral = total_credito_fornecedores + total_credito_transportadoras

        # Somente de fornecedores
        total_credito_disponivel = total_credito_fornecedores 

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
                valores_calculados = json.loads(valores_calculados_json)

            # Atualizar registros de fornecedores com valores calculados (Registros de fornecedores, FornecedorPagarModel)
            for registro in registros:
                registro_id_str = str(registro.id)
                if registro_id_str in valores_calculados:
                    dados_calculo = valores_calculados[registro_id_str]
                    try:
                        # Verificar se o preço de custo foi alterado
                        if 'preco_custo' in dados_calculo:
                            # Obtem preço de custo do frontend e converte para centavos
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

            # Processamento de valores editados para fretes (FretePagarModel)
            valores_calculados_fretes_json = request.form.get("valores_calculados_fretes", "")
            valores_calculados_fretes = {}
            
            if valores_calculados_fretes_json:
                valores_calculados_fretes = json.loads(valores_calculados_fretes_json)

            # Atualizar fretes com valores calculados
            for transportadora_id, dados_transp in fretes_dict.items():
                for frete in dados_transp['fretes']:
                    frete_id_str = str(frete.id)
                    if frete_id_str in valores_calculados_fretes:
                        dados_calculo_frete = valores_calculados_fretes[frete_id_str]
                        try:
                            # Verificar se o preço de custo do frete foi alterado
                            if 'preco_custo' in dados_calculo_frete:
                                preco_custo_frete_frontend = float(dados_calculo_frete['preco_custo'])
                                preco_custo_frete_frontend_100 = preco_custo_frete_frontend * 100
                                
                                # Comparar com valor original do banco
                                preco_frete_original = frete.preco_custo_bitola_100 or 0
                                if preco_custo_frete_frontend_100 != preco_frete_original:
                                    frete.preco_custo_bitola_100 = preco_custo_frete_frontend_100
                                    alteracoes_detectadas = True
                            
                            # Verificar se o valor total do frete foi alterado
                            if 'valor_total' in dados_calculo_frete:
                                valor_total_frete_frontend = float(dados_calculo_frete['valor_total'])
                                valor_total_frete_frontend_100 = valor_total_frete_frontend * 100
                                
                                # Comparar com valor original do banco
                                valor_frete_original = frete.valor_total_a_pagar_100 or 0
                                if valor_total_frete_frontend_100 != valor_frete_original:
                                    frete.valor_total_a_pagar_100 = valor_total_frete_frontend_100
                                    alteracoes_detectadas = True
                                    
                        except (ValueError, TypeError) as e:
                            flash(f"Erro nos valores calculados para frete {frete.id}: {str(e)}", "warning")
                            return redirect(request.url)
            
            # Salva as alterações de preço de custo e valores totais, se houver
            if alteracoes_detectadas:
                db.session.commit()  # Salva preços de custo e valores totais atualizados

            # Recalcula totais após a verificação de edição de valores
            valor_total_geral = 0 # Inicializa o total geral dos fornecedores

            for fornecedor_id, dados in fornecedores_dict.items():
                # Inicializar valor_total para evitar None
                dados['valor_total'] = 0  

                for registro in dados['registros']:
                    # Valor do registro de total a pagar
                    valor_registro = registro.valor_total_a_pagar_100 or 0
                    if valor_registro > 0:
                        dados['valor_total'] += valor_registro
                        valor_total_geral += valor_registro

            # Recalcula totais após a verificação de edição de valores
            valor_total_fretes = 0 # Inicializa o total geral dos fretes
            for transportadora_id, dados_transp in fretes_dict.items():
                dados_transp['valor_total'] = 0  # Inicializa valor_total para evitar None
                for frete in dados_transp['fretes']:
                    # Tratar valor_total_a_pagar_100 que pode ser None
                    valor_frete = frete.valor_total_a_pagar_100 or 0

                    if valor_frete > 0:
                        dados_transp['valor_total'] += valor_frete
                        valor_total_fretes += valor_frete

            # Total geral atualizado (fornecedores + fretes)
            valor_total_geral_com_fretes = valor_total_geral + valor_total_fretes

            # Calculo de créditos por entidades
            valor_final_fornecedores = valor_total_geral  # Valor total da fatura dos fornecedores
            valor_final_fretes = valor_total_fretes       # Valor total da fatura dos fretes

            total_credito_aplicado = 0  # Inicialização de crédito aplicado

            # Variáveis para armazenar detalhes dos créditos selecionados
            detalhes_creditos_utilizados = {
                'fornecedores': [],
                'transportadoras': []
            }
            
            if usar_credito == "sim":
                # Verificar se há créditos selecionados
                total_creditos_selecionados = 0
                
                # Calcular total de créditos selecionados
                for tipo_entidade, entidades in creditos_selecionados.items():
                    for entidade_id, credito_ids in entidades.items():
                        for credito_id in credito_ids:
                            if tipo_entidade == 'fornecedor':
                                credito = ExtratoCreditoFornecedorModel.query.get(credito_id)
                                if credito:
                                    total_creditos_selecionados += credito.valor_credito_100
                            elif tipo_entidade == 'transportadora':
                                credito = ExtratoCreditoFreteiroModel.query.get(credito_id)
                                if credito:
                                    total_creditos_selecionados += credito.valor_credito_100
                
                # Permite créditos negativos (débitos), só impede se realmente não há nada selecionado
                # Não bloquear quando total é 0 mas há créditos selecionados (podem ser negativos)
                if not creditos_selecionados or (not creditos_selecionados.get('fornecedor') and not creditos_selecionados.get('transportadora')):
                    flash(("Nenhum crédito selecionado para aplicar!", "warning"))
                    redirect_url = url_for("fornecedor_a_pagar_massa", ids=ids_selecionados)
                    if fretes_selecionados:
                        redirect_url += f"&fretes={fretes_selecionados}"
                    return redirect(redirect_url)
                
                # Calcular total da fatura
                valor_total_geral_com_fretes = valor_total_geral + valor_total_fretes
                # Para créditos negativos, não há limitação - eles podem aumentar o valor total
                credito_restante_para_usar = float('inf') if total_creditos_selecionados < 0 else valor_total_geral_com_fretes
                
                # Processar créditos selecionados por fornecedor
                credito_fornecedores_aplicado = 0
                if 'fornecedor' in creditos_selecionados:
                    for fornecedor_id_str, credito_ids in creditos_selecionados['fornecedor'].items():
                        fornecedor_id = int(fornecedor_id_str)
                        
                        for credito_id in credito_ids:
                            # Para créditos negativos (débitos), não há limitação de uso - processa todos
                            # Para créditos positivos, para quando não há mais valor para cobrir
                            if total_creditos_selecionados > 0 and credito_restante_para_usar <= 0:
                                break
                                
                            credito_individual = ExtratoCreditoFornecedorModel.query.get(credito_id)
                            # Permite tanto créditos (tipo 1) quanto débitos (tipo 2 ou negativos)
                            if credito_individual:
                                
                                # Calcular quanto deste crédito será realmente utilizado
                                valor_credito_a_usar = min(credito_individual.valor_credito_100, credito_restante_para_usar)
                                
                                credito_individual.credito_utilizado = True
                                db.session.add(credito_individual)
                                
                                # Criar extrato de débito apenas com o valor que será utilizado
                                extrato_fornecedor = ExtratoCreditoFornecedorModel(
                                    tipo_movimentacao=2,  # Saída
                                    descricao=f"Débito de crédito {credito_individual.descricao} para faturamento em massa.",
                                    data_movimentacao=datetime.now(),
                                    fornecedor_id=fornecedor_id,
                                    valor_credito_100=valor_credito_a_usar,
                                    usuario_id=current_user.id,
                                    credito_utilizado=True
                                )
                                db.session.add(extrato_fornecedor)
                                
                                # Atualizar saldo do fornecedor
                                dados_fornecedor = fornecedores_dict.get(fornecedor_id)
                                if dados_fornecedor and dados_fornecedor.get('saldo_credito_obj'):
                                    saldo_atual = dados_fornecedor['saldo_credito_obj'].valor_total_credito_100 or 0
                                    dados_fornecedor['saldo_credito_obj'].valor_total_credito_100 = saldo_atual - valor_credito_a_usar
                                
                                # Armazenar detalhes do crédito utilizado
                                detalhes_creditos_utilizados['fornecedores'].append({
                                    'credito_id': credito_id,
                                    'fornecedor_id': fornecedor_id,
                                    'valor': valor_credito_a_usar,
                                    'valor_original': credito_individual.valor_credito_100,
                                    'descricao': credito_individual.descricao,
                                    'data_movimentacao': credito_individual.data_movimentacao.strftime('%Y-%m-%d'),
                                    'uso_parcial': valor_credito_a_usar < credito_individual.valor_credito_100
                                })
                                
                                credito_fornecedores_aplicado += valor_credito_a_usar
                                total_credito_aplicado += valor_credito_a_usar
                                credito_restante_para_usar -= valor_credito_a_usar

                # Processar créditos selecionados por transportadora
                credito_transportadoras_aplicado = 0
                if 'transportadora' in creditos_selecionados:
                    for transportadora_id_str, credito_ids in creditos_selecionados['transportadora'].items():
                        transportadora_id = int(transportadora_id_str)
                        
                        for credito_id in credito_ids:
                            # Para créditos negativos (débitos), não há limitação de uso - processa todos
                            # Para créditos positivos, para quando não há mais valor para cobrir
                            if total_creditos_selecionados > 0 and credito_restante_para_usar <= 0:
                                break

                            credito_individual = ExtratoCreditoFreteiroModel.query.filter_by(id=credito_id, ativo=True, credito_utilizado=False).first()
                            # Permite tanto créditos (tipo 1) quanto débitos (tipo 2 ou negativos)
                            if credito_individual:
                                
                                credito_individual.credito_utilizado = True
                                db.session.add(credito_individual)
                                
                                # Calcular quanto deste crédito será realmente utilizado
                                valor_credito_a_usar = min(credito_individual.valor_credito_100, credito_restante_para_usar)
                                
                                # Criar extrato de débito apenas com o valor que será utilizado
                                extrato_transportadora = ExtratoCreditoFreteiroModel(
                                    tipo_movimentacao=2,  # Saída
                                    descricao=f"Débito de crédito {credito_individual.descricao} para faturamento em massa.",
                                    data_movimentacao=datetime.now(),
                                    transportadora_id=transportadora_id,
                                    valor_credito_100=valor_credito_a_usar,
                                    usuario_id=current_user.id,
                                    credito_utilizado=True
                                )
                                db.session.add(extrato_transportadora)
                                
                                # Atualizar saldo da transportadora
                                dados_transportadora = fretes_dict.get(transportadora_id)
                                if dados_transportadora and dados_transportadora.get('saldo_credito_obj'):
                                    saldo_atual_transp = dados_transportadora['saldo_credito_obj'].valor_total_credito_100 or 0
                                    dados_transportadora['saldo_credito_obj'].valor_total_credito_100 = saldo_atual_transp - valor_credito_a_usar
                                
                                # Armazenar detalhes do crédito utilizado
                                detalhes_creditos_utilizados['transportadoras'].append({
                                    'credito_id': credito_id,
                                    'transportadora_id': transportadora_id,
                                    'valor': valor_credito_a_usar,
                                    'valor_original': credito_individual.valor_credito_100,
                                    'descricao': credito_individual.descricao,
                                    'data_movimentacao': credito_individual.data_movimentacao.strftime('%Y-%m-%d'),
                                    'uso_parcial': valor_credito_a_usar < credito_individual.valor_credito_100
                                })
                                
                                credito_transportadoras_aplicado += valor_credito_a_usar
                                total_credito_aplicado += valor_credito_a_usar
                                credito_restante_para_usar -= valor_credito_a_usar

                # APLICAR DESCONTO GLOBAL: Total - Créditos (permite créditos negativos)
                valor_total_geral_com_fretes = valor_total_geral + valor_total_fretes
                # Remove limitação para permitir créditos negativos somarem ao valor
                total_credito_utilizado = total_credito_aplicado
                
                # Calcular valor final (créditos negativos somam ao valor total)
                # Para créditos negativos: valor_total + abs(credito_negativo) = valor_total + (-(-3000)) = valor_total + 3000
                # Para créditos positivos: valor_total - credito_positivo  
                if total_credito_utilizado < 0:
                    valor_final_global = valor_total_geral_com_fretes + abs(total_credito_utilizado)  # Soma débito
                else:
                    valor_final_global = valor_total_geral_com_fretes - total_credito_utilizado      # Subtrai crédito
                
                # Distribuir proporcionalmente entre fornecedores e fretes
                if valor_total_geral_com_fretes > 0:
                    proporcao_fornecedores = valor_total_geral / valor_total_geral_com_fretes
                    proporcao_fretes = valor_total_fretes / valor_total_geral_com_fretes
                    
                    valor_final_fornecedores = valor_final_global * proporcao_fornecedores
                    valor_final_fretes = valor_final_global * proporcao_fretes
                else:
                    valor_final_fornecedores = 0
                    valor_final_fretes = 0
                
                # Atualizar o total de crédito aplicado para refletir apenas o que foi realmente utilizado
                total_credito_aplicado = total_credito_utilizado
                
                # Marcar todos os registros como utilizando crédito (proporcionalmente para relatórios)
                # Inclui tanto créditos positivos quanto negativos (débitos)
                if total_credito_aplicado != 0:
                    # Marcar fornecedores
                    for fornecedor_id, dados in fornecedores_dict.items():
                        for registro in dados['registros']:
                            registro.utiliza_credito = 1
                            # O valor específico será calculado proporcionalmente se necessário
                            registro.valor_credito_100 = 0  # Será atualizado se necessário para relatórios
                    
                    # Marcar transportadoras
                    for transportadora_id, dados_transp in fretes_dict.items():
                        for frete in dados_transp['fretes']:
                            frete.utiliza_credito = 1
                            frete.valor_credito_100 = 0  # Será atualizado se necessário para relatórios

            # Valor final a faturar (fornecedores + fretes)
            valor_final_a_faturar = valor_final_fornecedores + valor_final_fretes

            # Criando detalhes json para frontend
            detalhes_fornecedores = []
            for fornecedor_id, dados in fornecedores_dict.items():
                for reg in dados['registros']:
                    print("DEBUG reg:", reg, "registro_operacional:", getattr(reg, 'registro_operacional', None))
                    # Calcular valor efetivo após crédito aplicado (créditos negativos somam)
                    valor_bruto_registro = reg.valor_total_a_pagar_100 or 0
                    valor_credito_registro = getattr(reg, 'valor_credito_100') or 0
                    # Créditos negativos devem somar ao valor total
                    valor_faturado = valor_bruto_registro - valor_credito_registro
                    preco_custo_registro = reg.preco_custo_bitola_100 or 0

                    numero_nf = ""
                    if reg.registro_operacional:
                        if reg.registro_operacional.estorno_nf and reg.registro_operacional.numero_nota_fiscal_estorno:
                            numero_nf = f"{reg.registro_operacional.numero_nota_fiscal_estorno} *"
                        elif reg.registro_operacional.numero_nota_fiscal:
                            numero_nf = reg.registro_operacional.numero_nota_fiscal
                        else:
                            numero_nf = ""

                    detalhes_fornecedores.append({
                        "fornecedor_a_pagar_id": reg.id,
                        "fornecedor_id": fornecedor_id,
                        "solicitacao_id": reg.solicitacao_id if reg.solicitacao else "",
                        "fornecedor_identificacao": dados['fornecedor'].identificacao if dados.get('fornecedor') else str(fornecedor_id),
                        "cliente": reg.solicitacao.cliente.identificacao if reg.solicitacao and reg.solicitacao.cliente else "",
                        "transportadora_id": reg.registro_operacional.solicitacao.transportadora_id if reg.registro_operacional and reg.registro_operacional.solicitacao else "",
                        "transportadora_identificacao": reg.registro_operacional.solicitacao.transportadora_exibicao.identificacao if reg.registro_operacional and reg.registro_operacional.solicitacao and reg.registro_operacional.solicitacao.transportadora_exibicao else "",
                        "valor_bruto": valor_bruto_registro or 0,               # Valor antes do crédito
                        "valor_credito": valor_credito_registro or 0,           # Crédito aplicado
                        "valor_faturado": valor_faturado or 0,                   # Valor após crédito
                        "nota_fiscal": numero_nf,
                        "peso_ticket": f"{reg.registro_operacional.peso_liquido_ticket}" if reg.registro_operacional and reg.registro_operacional.peso_liquido_ticket else "",
                        "preco_custo": preco_custo_registro,              # Preço atualizado pelo usuário
                        "produto": reg.solicitacao.produto.nome if reg.solicitacao and reg.solicitacao.produto else "",
                        "bitola": reg.solicitacao.bitola.bitola if reg.solicitacao and reg.solicitacao.bitola else "",
                        "data_entrega": reg.data_entrega_ticket.strftime('%d/%m/%Y') if reg.data_entrega_ticket else "",
                        "utiliza_credito": getattr(reg, 'utiliza_credito') or 0,
                        # Dados extras do registro_operacional
                        "registro_operacional_id": reg.registro_operacional.id if reg.registro_operacional else "",
                        "placa_veiculo": reg.solicitacao.veiculo.placa_veiculo if reg.solicitacao and reg.solicitacao.veiculo else "",
                        "motorista": reg.solicitacao.motorista.nome_completo if reg.solicitacao and reg.solicitacao.motorista else ""
                    })
                    
                    # Pontuação do usuário
                    PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                        current_user.id,
                        TipoAcaoEnum.CADASTRO,
                        TipoAcaoEnum.CADASTRO.pontos,
                        modulo=f"informar_faturamento_fornecedor_massa_{reg.id}",
                    )

            detalhes_transportadoras = []
            for transp_id, dados in fretes_dict.items():
                for frete in dados['fretes']:
                    
                    # Calcular valor efetivo após crédito aplicado (créditos negativos somam)
                    valor_bruto_frete = frete.valor_total_a_pagar_100 or 0
                    valor_credito_frete = getattr(frete, 'valor_credito_100') or 0
                    # Créditos negativos devem somar ao valor total
                    valor_efetivo_frete = valor_bruto_frete - valor_credito_frete
                    preco_custo_frete = frete.preco_custo_bitola_100 or 0
                    
                    # Preparar número da NF
                    numero_nf = ""
                    if frete.registro_operacional:
                        if frete.registro_operacional.estorno_nf and frete.registro_operacional.numero_nota_fiscal_estorno:
                            numero_nf = f"{frete.registro_operacional.numero_nota_fiscal_estorno} *"
                        elif frete.registro_operacional.numero_nota_fiscal:
                            numero_nf = frete.registro_operacional.numero_nota_fiscal
                        else:
                            numero_nf = ""
                    
                    detalhes_transportadoras.append({
                        "frete_a_pagar_id": frete.id,
                        "transportadora_id": transp_id,
                        "solicitacao_id": frete.solicitacao_id if frete.solicitacao else "",
                        "transportadora_identificacao": dados['transportadora'].identificacao if dados.get('transportadora') else str(transp_id),
                        "valor_bruto": valor_bruto_frete,                 # Valor antes do crédito
                        "valor_credito": valor_credito_frete or 0,             # Crédito aplicado
                        "valor_faturado": valor_efetivo_frete or 0,             # Valor após crédito
                        "preco_custo": preco_custo_frete or 0,                 # Preço atualizado pelo usuário
                        "data_entrega": frete.data_entrega_ticket.strftime('%d/%m/%Y') if frete.data_entrega_ticket else "",
                        "placa": frete.solicitacao.veiculo.placa_veiculo if frete.solicitacao.veiculo else "",
                        "fornecedor": frete.solicitacao.fornecedor.identificacao if frete.solicitacao.fornecedor else "",
                        "cliente": frete.solicitacao.cliente.identificacao if frete.solicitacao.cliente else "",
                        "bitola": frete.solicitacao.bitola.bitola if frete.solicitacao.bitola else "",
                        "nota_fiscal": numero_nf,
                        "peso_ticket": f"{frete.registro_operacional.peso_liquido_ticket}" if frete.registro_operacional.peso_liquido_ticket else "",
                        "produto": frete.solicitacao.produto.nome if frete.solicitacao and frete.solicitacao.produto else "",
                        "utiliza_credito": getattr(frete, 'utiliza_credito') or 0,
                        # Dados extras do registro_operacional
                        "registro_operacional_id": frete.registro_operacional.id if frete.registro_operacional else "",
                        "placa_veiculo": frete.solicitacao.veiculo.placa_veiculo if frete.solicitacao and frete.solicitacao.veiculo else "",
                        "motorista_registro": frete.solicitacao.motorista.nome_completo if frete.solicitacao and frete.solicitacao.motorista else ""
                    })
                    
                    # Pontuação do usuário
                    PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                        current_user.id,
                        TipoAcaoEnum.CADASTRO,
                        TipoAcaoEnum.CADASTRO.pontos,
                        modulo=f"informar_faturamento_transportadora_com_agrupamento_massa_{reg.id}",
                    )

            # Criação de novo faturamento
            novo_faturamento = FaturamentoModel(
                usuario_id=current_user.id,
                codigo_faturamento=FaturamentoModel.gerar_codigo_novo_faturamento(),
                valor_total=valor_final_a_faturar,           # Valor efetivo após créditos
                ids_fornecedores=ids_selecionados,
                ids_fretes=','.join(str(f["frete_a_pagar_id"]) for f in detalhes_transportadoras) if detalhes_transportadoras else None,
                utilizou_credito=(usar_credito == "sim"),
                situacao_pagamento_id=7,
                tipo_operacao=1, # carga
                direcao_financeira=2 # despesa
            )

            # Se o modelo suporta campos extras, adicionar:
            if hasattr(novo_faturamento, 'valor_bruto_total'):
                novo_faturamento.valor_bruto_total = valor_total_geral_com_fretes
            if hasattr(novo_faturamento, 'valor_credito_aplicado'):
                novo_faturamento.valor_credito_aplicado = total_credito_aplicado
            if hasattr(novo_faturamento, 'valor_fornecedor'):
                novo_faturamento.valor_fornecedor = valor_final_fornecedores
            if hasattr(novo_faturamento, 'valor_transportadora'):
                novo_faturamento.valor_transportadora = valor_final_fretes

            # Preparar detalhes dos créditos utilizados para salvar no JSON
            creditos_detalhes_json = []
            if detalhes_creditos_utilizados['fornecedores']:
                for credito_detalhe in detalhes_creditos_utilizados['fornecedores']:
                    creditos_detalhes_json.append({
                        'tipo': 'fornecedor',
                        'credito_id': credito_detalhe['credito_id'],
                        'entidade_id': credito_detalhe['fornecedor_id'],
                        'valor': credito_detalhe['valor'],
                        'descricao': credito_detalhe['descricao'],
                        'data_movimentacao': credito_detalhe['data_movimentacao']
                    })
            
            if detalhes_creditos_utilizados['transportadoras']:
                for credito_detalhe in detalhes_creditos_utilizados['transportadoras']:
                    creditos_detalhes_json.append({
                        'tipo': 'transportadora',
                        'credito_id': credito_detalhe['credito_id'],
                        'entidade_id': credito_detalhe['transportadora_id'],
                        'valor': credito_detalhe['valor'],
                        'descricao': credito_detalhe['descricao'],
                        'data_movimentacao': credito_detalhe['data_movimentacao']
                    })

            novo_faturamento.salvar_detalhes(
                fornecedores=detalhes_fornecedores, 
                transportadoras=detalhes_transportadoras,
                credito_fornecedor=detalhes_creditos_utilizados['fornecedores'],
                credito_transportadora=detalhes_creditos_utilizados['transportadoras']
            )
            db.session.add(novo_faturamento)

            try:
                # Atualizar situação financeira dos registros de fornecedor a pagar
                for fornecedor_id, dados in fornecedores_dict.items():
                    for reg in dados['registros']:
                        reg.situacao_pagamento_id = 5  # 5 = Faturado

                # Atualizar situação financeira dos registros de frete a pagar (se houver)
                for transp_id, dados in fretes_dict.items():
                    for frete in dados['fretes']:
                        frete.situacao_pagamento_id = 5  # 5 = Faturado

                db.session.commit()

                flash(("Faturamento realizado com sucesso!", "success"))
                return redirect(url_for("listagem_faturamentos_cargas_a_pagar"))
                    
            except Exception as e:
                db.session.rollback()
                flash((f"Erro ao salvar faturamento: {str(e)}", "warning"))
                return redirect(request.url)
        return render_template(
            "financeiro/informar_pagamento/informar_pagamento_fornecedor_massa.html",
            campos_obrigatorios=campos_obrigatorios,
            campos_erros=campos_erros,
            dados_corretos=request.form,
            registros=registros,
            fornecedores_dict=fornecedores_dict,
            valor_total_geral=valor_total_geral,
            valor_total_fretes=valor_total_fretes,
            valor_total_geral_com_fretes=valor_total_geral_com_fretes,
            total_credito_disponivel=total_credito_disponivel,
            total_credito_disponivel_geral=total_credito_disponivel_geral, 
            total_credito_fornecedores=total_credito_fornecedores, 
            total_credito_transportadoras=total_credito_transportadoras, 
            total_registros_completo=total_registros_completo,
            total_registros_fretes=total_registros_fretes,
            ids_selecionados=ids_selecionados,
            fretes_dict=fretes_dict,
            creditos_selecionados=creditos_selecionados,
        )

    except Exception as e:
        print(f"[ERROR] Erro interno: {e}")
        db.session.rollback()
        flash((f"Erro interno: {str(e)}", "error"))
        return redirect(url_for("listagem_fornecedores_a_pagar"))

@app.route("/financeiro/a-pagar/fornecedor-a-pagar/cancelar-informe/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def cancelar_pagamento_fornecedor(id):
    try:
        registro = FornecedorPagarModel.obter_fornecedor_a_pagar_id(id)
        if not registro:
            flash(("Registro não encontrado", "warning"))
            return redirect(url_for("listagem_fornecedores_a_pagar"))

        if registro.situacao_pagamento_id != 5:
            flash(("Só é possível cancelar faturamentos já processados.", "warning"))
            return redirect(url_for("listagem_fornecedores_a_pagar"))

        valor_credito = registro.valor_credito_100 or 0
        valor_saldo = registro.valor_saldo_debitado_100 or 0
        usou_credito = bool(registro.utiliza_credito)
        usou_saldo = bool(registro.utiliza_saldo_movimentacao)

        registro.situacao_pagamento_id = 2

        mov_antiga = MovimentacaoFinanceiraModel.query.filter_by(
            fornecedor_pagamento_id=registro.id, deletado=False
        ).first()
        if mov_antiga:
            mov_antiga.deletado = True

        if usou_credito and valor_credito != 0:  # Permite tanto créditos positivos quanto negativos
            estorno_cred = ExtratoCreditoFornecedorModel(
                tipo_movimentacao=4,
                descricao="Estorno de crédito por cancelamento de faturamento",
                data_movimentacao=datetime.now(),
                fornecedor_id=registro.fornecedor_id,
                usuario_id=current_user.id,
                valor_credito_100=valor_credito,
            )
            db.session.add(estorno_cred)
            db.session.flush()

            saldo_credito = CreditoFornecedorModel.valor_credito_disponivel(registro.fornecedor_id)

            if saldo_credito:
                saldo_credito.valor_total_credito_100 += valor_credito

            mov_est_cred = MovimentacaoFinanceiraModel(
                tipo_movimentacao=4,
                usuario_id=current_user.id,
                data_movimentacao=datetime.now(),
                movimentacao_extra=1,
                valor_movimentacao_100=valor_credito,
                credito_fornecedor_id=estorno_cred.id,
                conta_bancaria_id=registro.conta_bancaria_id
            )
            db.session.add(mov_est_cred)
            db.session.flush()

        if usou_saldo and valor_saldo > 0:
            mov_est_din = MovimentacaoFinanceiraModel(
                tipo_movimentacao=5,
                usuario_id=current_user.id,
                data_movimentacao=datetime.now(),
                fornecedor_pagamento_id=registro.id,
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
        db.session.rollback()
        print(f"[ERROR cancelar_faturamento_fornecedor] {e}")
        flash(("Erro ao cancelar informe de faturamento! Contate o suporte.", "warning"))

    return redirect(url_for("listagem_fornecedores_a_pagar"))
