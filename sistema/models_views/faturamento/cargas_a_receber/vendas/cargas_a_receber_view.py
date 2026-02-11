from datetime import datetime
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem, formatar_float_para_brl, formatar_data_para_brl, formatar_float_para_brl_sem_cifrao
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.faturamento.cargas_a_receber.vendas.recebimento_model import RecebimentoModel
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.upload_arquivo.upload_arquivo_model import UploadArquivoModel
from sistema.models_views.configuracoes_gerais.conta_bancaria.conta_bancaria_model import ContaBancariaModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_view import (inicializar_categorias_padrao, obter_subcategorias_recursivo)
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_view import (inicializar_categorias_padrao_categorizacao_fiscal, obter_subcategorias_recursivo_categorizacao_fiscal)
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_model import CategorizacaoFiscalModel
from sistema.models_views.financeiro.movimentacao_financeira.movimentacao_financeira_model import MovimentacaoFinanceiraModel
from sistema.models_views.financeiro.movimentacao_financeira.saldo_movimentacao_financeira_model import SaldoMovimentacaoFinanceiraModel
from sistema.models_views.configuracoes_gerais.situacao_pagamento.situacao_pagamento_model import SituacaoPagamentoModel
from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx
from sistema.models_views.importacao_ofx.importacao_ofx_view import limpar_dados_conciliacao
from sistema.models_views.importacao_ofx.importacao_ofx_view import verificar_e_limpar_conciliacao_incorreta
from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
from sistema._utilitarios import *
from sistema._utilitarios.utilitario_semanal import UtilitariosSemana


@app.context_processor
def inject_situacoes_financeiras():
    situacoes_pagamento= []
    try:
        if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            situacoes_pagamento = SituacaoPagamentoModel.listar_status()
    except Exception:
        situacoes_pagamento = []
    return {"situacoes_pagamento": situacoes_pagamento}

@app.route("/financeiro/cargas-a-receber/listagem", methods=["GET"])
@login_required
@requires_roles
def listagem_a_receber():
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()

    # Carregar apenas entidades necessárias para os selects que ainda são selects
    statusPagamentos = SituacaoPagamentoModel.listar_status_filtro()

    # Obter semanas disponíveis para o filtro semanal
    semanas_disponiveis = UtilitariosSemana.obter_semanas_do_mes_atual()

    verificar_e_limpar_conciliacao_incorreta('a_receber') 

    dados_conciliacao = session.get('dados_conciliacao', {})
    conciliar_transacao_id = dados_conciliacao.get('transacao_id')
    valor_conciliar = dados_conciliacao.get('valor')
    data_conciliar = dados_conciliacao.get('data')
    descricao_conciliar = dados_conciliacao.get('descricao')
    fitid_conciliar = dados_conciliacao.get('fitid')

    if any(request.args.values()):
        # Verificar o tipo de filtro (semanal ou data)
        tipo_filtro = request.args.get("tipo_filtro", "semanal")
        semana_selecionada = request.args.get("semanaSelecionada")
        data_inicio_form = request.args.get("dataInicio")
        data_fim_form = request.args.get("dataFim")
        
        # Determinar data_inicio e data_fim baseado no tipo de filtro
        if tipo_filtro == "data" and data_inicio_form and data_fim_form:
            from datetime import datetime
            data_inicio = datetime.strptime(data_inicio_form, "%Y-%m-%d").date()
            data_fim = datetime.strptime(data_fim_form, "%Y-%m-%d").date()
        else:
            # Usar filtro semanal
            valor_padrao_semana = next((semana['valor'] for semana in semanas_disponiveis if semana.get('is_atual')), None)
            data_inicio, data_fim = UtilitariosSemana.processar_semana_selecionada(
                semana_selecionada or valor_padrao_semana
            )
        
        placa = request.args.get("placaCarga")
        motorista = request.args.get("motoristaCarga")
        transportadora = request.args.get("transportadoraCarga")
        fornecedor = request.args.get("fornecedorCarga")
        cliente = request.args.get("clienteCarga")
        numero_nf = request.args.get("numeroNF")
        produto = request.args.get("produtoCarga")
        bitola = request.args.get("bitolaCarga")
        status_pagamento = request.args.get("statusPagamentoCarga")
        tipo_data_filtro = request.args.get("tipoDataFiltro", "data_entrega")

        registros = RegistroOperacionalModel.filtrar_registros_carga_cliente(
            data_inicio=data_inicio,
            data_fim=data_fim,
            placa=placa,
            motorista=motorista,
            transportadora=transportadora,
            fornecedor=fornecedor,
            cliente=cliente,
            numero_nf=numero_nf,
            produto=produto,
            bitola=bitola,
            status_pagamento=status_pagamento,
            tipo_data_filtro=tipo_data_filtro
        )
    else:
        registros = RegistroOperacionalModel.obter_registros_carga_agrupados()

    return render_template(
        "/financeiro/cargas_a_receber/cargas_a_receber.html",
        registros=registros,
        dados_corretos=request.args,
        changelog=changelog,
        statusPagamentos=statusPagamentos,
        semanas_disponiveis=semanas_disponiveis,
        conciliar_transacao_id=conciliar_transacao_id,
        valor_conciliar=valor_conciliar,
        data_conciliar=data_conciliar,
        descricao_conciliar=descricao_conciliar,
        fitid_conciliar=fitid_conciliar
    )

@app.route("/financeiro/cargas-a-receber/informar-recebimento/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def informar_recebimento_carga(id):
    try:
        campos_obrigatorios = {}
        campos_erros = {}
        gravar_banco = True

        verificar_e_limpar_conciliacao_incorreta('a_receber')
        dados_conciliacao = session.get('dados_conciliacao', {})
        conciliar_transacao_id = dados_conciliacao.get('transacao_id')

        registro = RegistroOperacionalModel.obter_por_id(id)
        contas_bancarias = ContaBancariaModel.obter_contas_bancarias_ativas()
        if not registro:
            flash(("Registro não encontrado!", "warning"))
            return redirect(url_for('listagem_a_receber'))

        if registro.situacao_financeira_id == 5:
            flash(("Registro já consta como faturado!", "warning"))
            return redirect(url_for('listagem_a_receber'))

        transacao_ofx = None
        if conciliar_transacao_id:
            transacao_ofx = ImportacaoOfx.query.get(conciliar_transacao_id)
            print(f"[DEBUG] transacao_ofx encontrada: {transacao_ofx}")

        valor_total_recebimento = registro.valor_total_nota_100 or 0
            
        saldo_conta_atual = 0
        conta_padrao_id = request.form.get("contaBancaria") or (contas_bancarias[0].id if contas_bancarias else None)
        if conta_padrao_id:
            saldo_obj = SaldoMovimentacaoFinanceiraModel.obter_registro_conta_bancaria(conta_padrao_id)
            if saldo_obj:
                saldo_conta_atual = saldo_obj.valor_total_saldo_100
        
        registro_dict = {
            'id': registro.id,
            'cliente': registro.solicitacao.cliente if registro.solicitacao else None,
            'numero_nota_fiscal': registro.numero_nota_fiscal,
            'produto': registro.solicitacao.produto if registro.solicitacao and hasattr(registro.solicitacao, 'produto') else None,
            'quantidade': registro.peso_liquido_ticket if registro.peso_liquido_ticket else 0,
            'valor_unitario_100': registro.preco_un_nf if registro.preco_un_nf else 0,
            'valor_total_recebimento_100': valor_total_recebimento,
        }
        
        if request.method == "POST":
            valor_total_calculado = request.form.get("valor_total_calculado", "")
            valor_recebido = 0
            if valor_total_calculado:
                valor_limpo = ValoresMonetarios.converter_string_brl_para_float(valor_total_calculado)
                valor_recebido = int(float(valor_limpo))
            else:
                valor_recebido = valor_total_recebimento if valor_total_recebimento else 0

            if gravar_banco:
                novo_recebimento = RecebimentoModel(
                    cliente_id=registro.solicitacao.cliente_id,
                    registro_operacional_id=registro.id,
                    usuario_id=current_user.id,
                    numero_nota_fiscal=registro.numero_nota_fiscal,
                    valor_total_recebimento_100=valor_recebido,
                    data_recebimento=DataHora.obter_data_atual_padrao_en()
                )
                db.session.add(novo_recebimento)
                db.session.flush()

                registro.situacao_financeira_id = 5  # 
                registro.valor_total_nota_100 = valor_recebido

                # Calcular valor líquido após crédito
                valor_bruto = valor_recebido
                valor_credito = 0
                valor_liquido = valor_recebido

                # Criação do faturamento para o registro individual (adaptado para extrator)
                novo_faturamento = FaturamentoModel(
                    usuario_id=current_user.id,
                    codigo_faturamento=FaturamentoModel.gerar_codigo_novo_faturamento(),
                    valor_total=valor_liquido,  # Valor líquido após crédito
                    ids_fornecedores=None,  # Para extrator não usa ids_registros
                    ids_a_receber=str(registro.id),  # Para extrator usa ids_extratores
                    utilizou_credito=0,
                    situacao_pagamento_id=7,
                    tipo_operacao=1,
                    direcao_financeira=1
                )
                if hasattr(novo_faturamento, 'valor_bruto_total'):
                    novo_faturamento.valor_bruto_total = valor_bruto
                if hasattr(novo_faturamento, 'valor_credito_aplicado'):
                    novo_faturamento.valor_credito_aplicado = valor_credito
                if hasattr(novo_faturamento, 'valor_fornecedor'):
                    novo_faturamento.valor_fornecedor = 0  # Para extrator, valor fornecedor é 0
                if hasattr(novo_faturamento, 'valor_transportadora'):
                    novo_faturamento.valor_transportadora = 0  # Para extrator, valor transportadora é 0
                if hasattr(novo_faturamento, 'valor_extrator'):
                    novo_faturamento.valor_extrator = 0  # Valor vai para extrator
                if hasattr(novo_faturamento, 'valor_comissionado'):
                    novo_faturamento.valor_comissionado = 0  # Para extrator, valor comissionado é 0
                if hasattr(novo_faturamento, 'valor_receita'):
                    novo_faturamento.valor_receita = valor_liquido  # Valor vai para receber
                
                # Preparar detalhes do faturamento para extrator
                valor_bruto_registro = valor_bruto
                valor_credito_registro = valor_credito
                valor_faturado = valor_liquido
                preco_custo_registro = registro.preco_un_nf or 0

                numero_nf = ""
                if registro:
                    if registro.estorno_nf and registro.numero_nota_fiscal_estorno:
                        numero_nf = f"{registro.numero_nota_fiscal_estorno} *"
                    elif registro.numero_nota_fiscal:
                        numero_nf = registro.numero_nota_fiscal
                

                # Detalhes para extrator (vai no array de extratores)
                detalhes_extratores = [{
                    "carga_a_receber_id": registro.id,
                    "solicitacao_id": registro.solicitacao_nf_id if registro.solicitacao else "",
                    "fornecedor_identificacao": registro.solicitacao.fornecedor.identificacao if registro and registro.solicitacao and registro.solicitacao.fornecedor else str(registro.fornecedor_id),
                    "cliente_id": registro.solicitacao.cliente.id if registro.solicitacao and registro.solicitacao.cliente else "",
                    "cliente": registro.solicitacao.cliente.identificacao if registro.solicitacao and registro.solicitacao.cliente else "",
                    "valor_bruto": valor_bruto_registro,
                    "valor_credito": valor_credito_registro,
                    "valor_faturado": valor_faturado,
                    "nota_fiscal": numero_nf,
                    "peso_ticket": f"{registro.peso_liquido_ticket}" if registro and registro.peso_liquido_ticket else "",
                    "preco_custo": preco_custo_registro,
                    "produto": registro.solicitacao.produto.nome if registro.solicitacao and registro.solicitacao.produto else "",
                    "bitola": registro.solicitacao.bitola.bitola if registro.solicitacao and registro.solicitacao.bitola else "",
                    "data_entrega": registro.data_entrega_ticket.strftime('%d/%m/%Y') if registro.data_entrega_ticket else "",
                    "utiliza_credito": 0,
                    "registro_operacional_id": registro.id if registro else "",
                    "placa_veiculo": registro.solicitacao.veiculo.placa_veiculo if registro.solicitacao and registro.solicitacao.veiculo else "",
                    "motorista": registro.solicitacao.motorista.nome_completo if registro.solicitacao and registro.solicitacao.motorista else "",
                    "transportadora_id": registro.solicitacao.transportadora_id if registro.solicitacao else "",
                    "transportadora_identificacao": registro.solicitacao.transportadora_exibicao.identificacao if registro.solicitacao else "",
                }]

                # Salvar detalhes (array vazio para fornecedores, detalhes_extratores)
                novo_faturamento.salvar_detalhes(cargas_a_receber=detalhes_extratores)

                db.session.add(novo_faturamento)
                
                if transacao_ofx and not transacao_ofx.conciliado:
                    transacao_ofx.conciliado = True
                    transacao_ofx.tipo_conciliacao = 'recebimento_cliente_individual'
                    transacao_ofx.pagamento_id = novo_recebimento.id 
                    transacao_ofx.data_conciliacao = datetime.now()
                    transacao_ofx.usuario_conciliacao_id = current_user.id
                    transacao_ofx.observacoes_conciliacao = f"Conciliado com recebimento individual ID {novo_recebimento.id}"

                    if dados_conciliacao.get('verificar_diferenca'):
                        valor_ofx_centavos = int(transacao_ofx.valor * 100) if transacao_ofx.valor else 0
                        diferenca_centavos = valor_ofx_centavos - valor_recebido
                        
                        print(f"Valor OFX: {valor_ofx_centavos} centavos")
                        print(f"Valor Recebido: {valor_recebido} centavos")
                        print(f"Diferença: {diferenca_centavos} centavos")
                        
                        if diferenca_centavos > 0:
                            db.session.commit()
                            diferenca_reais = diferenca_centavos / 100
                            
                            dados_diferenca = {
                                'tipo_movimentacao_predefinido': 'receita',
                                'valor_sem_formatacao': diferenca_reais,  
                                'descricao_sugerida': f'Diferença de conciliação - {transacao_ofx.fitid}',
                                'vencimento': datetime.now().strftime('%Y-%m-%d'),
                                'mesAno': datetime.now().strftime('%m/%Y'),
                                'tem_diferenca': True,
                                'transacao_ofx_id': transacao_ofx.id,
                                'registro_recebimento_id': registro.id
                            }

                            session['dados_conciliacao'] = dados_diferenca
                            session.modified = True

                            flash((f'Recebimento informado! Detectada diferença de {ValoresMonetarios.converter_float_brl_positivo(diferenca_reais)} para lançamento.', 'success'))
                            return redirect(url_for('nova_movimentacao_financeira'))
                
                db.session.commit()
                
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    TipoAcaoEnum.CADASTRO,
                    TipoAcaoEnum.CADASTRO.pontos,
                    modulo="informar_recebimento_carga",
                )

                if conciliar_transacao_id:
                    limpar_dados_conciliacao()
                    flash(("Faturamento informado e transação OFX conciliada com sucesso!", "success"))
                    return redirect(url_for("listagem_ofx"))
                else:
                    flash(("Faturamento informado com sucesso!", "success"))
                    return redirect(url_for("listagem_a_receber"))

        return render_template(
            "financeiro/informar_recebimento/informar_recebimento_cliente.html",
            campos_obrigatorios=campos_obrigatorios,
            campos_erros=campos_erros,
            dados_corretos=request.form,
            contas_bancarias=contas_bancarias,
            registro=registro_dict,
            saldo_conta_atual=saldo_conta_atual,
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
        flash((f"Erro ao informar faturamento de carga: {str(e)}", "danger"))
        return redirect(url_for("listagem_a_receber"))

@app.route("/api/conta-bancaria/<int:conta_id>/saldo", methods=["GET"])
@login_required
@requires_roles
def obter_saldo_conta_api(conta_id):
    """API endpoint para obter saldo de uma conta bancária"""
    try:
        saldo_obj = SaldoMovimentacaoFinanceiraModel.obter_registro_conta_bancaria(conta_id)
        saldo = 0
        if saldo_obj:
            saldo = saldo_obj.valor_total_saldo_100
        
        return jsonify({
            'success': True,
            'saldo': saldo,
            'saldo_formatado': saldo
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route("/financeiro/cargas-a-receber/informar-recebimento-massa", methods=["GET", "POST"])
@login_required
@requires_roles
def informar_recebimento_massa():
    try:
        campos_obrigatorios = {}
        campos_erros = {}
        gravar_banco = True

        verificar_e_limpar_conciliacao_incorreta('a_receber')
        dados_conciliacao = session.get('dados_conciliacao', {})
        conciliar_transacao_id = dados_conciliacao.get('transacao_id')

        if request.method == "GET":
            ids_selecionados = request.args.get('ids_registros', '') or request.args.get('ids_cargas', '')
            ids_nfs_complementares = request.args.get('ids_nfs_complementares', '') or request.args.get('ids_nf_complementar', '')
            ids_nfs_servico = request.args.get('ids_nfs_servico', '') or request.args.get('ids_nf_servico', '')
            
            if not ids_selecionados:
                flash(("Nenhum registro foi selecionado para recebimento!", "warning"))
                return redirect(url_for("listagem_a_receber"))
            
            try:
                ids_list = [int(id.strip()) for id in ids_selecionados.split(',') if id.strip()]
            except ValueError:
                flash(("IDs inválidos selecionados!", "warning"))
                return redirect(url_for("listagem_a_receber"))

        else:  # POST
            ids_selecionados = request.form.get('ids_registros', '') or request.form.get('ids_cargas', '')
            ids_nfs_complementares = request.form.get('ids_nfs_complementares', '') or request.form.get('ids_nf_complementar', '')
            ids_nfs_servico = request.form.get('ids_nfs_servico', '') or request.form.get('ids_nf_servico', '')
            
            if not ids_selecionados:
                flash(("Nenhum registro foi selecionado para recebimento!", "warning"))
                return redirect(url_for("listagem_a_receber"))
            
            try:
                ids_list = [int(id.strip()) for id in ids_selecionados.split(',') if id.strip()]
            except ValueError:
                flash(("IDs inválidos selecionados!", "warning"))
                return redirect(url_for("listagem_a_receber"))

        registros = [RegistroOperacionalModel.obter_por_id(registro_id) for registro_id in ids_list]
        registros = [r for r in registros if r and r.situacao_financeira_id != 5]  # Filtrar já recebidos

        if not registros:
            flash(("Nenhum registro válido encontrado para recebimento!", "warning"))
            return redirect(url_for("listagem_a_receber"))
        
        transacao_ofx = None
        if conciliar_transacao_id:
            transacao_ofx = ImportacaoOfx.query.get(conciliar_transacao_id)

        if len(registros) != len(ids_list):
            flash(("Alguns registros selecionados não estão disponíveis para recebimento!", "warning"))

        clientes_dict = {}
        valor_total_geral = 0
        valores_recebidos_dict = {}  # id do registro -> valor editado (centavos)

        for registro in registros:
            if request.method == "POST":
                valor_hidden = request.form.get(f"valor_registro_{registro.id}")
                if valor_hidden is None:
                   continue
                try:
                    valor_total_recebimento = int(valor_hidden)
                except (TypeError, ValueError):
                    valor_total_recebimento = registro.valor_total_nota_100 or 0
            else:
                valor_total_recebimento = registro.valor_total_nota_100 or 0

            valores_recebidos_dict[registro.id] = valor_total_recebimento

            cliente_id = registro.solicitacao.cliente_id if registro.solicitacao else 0
            valor_total_geral += valor_total_recebimento

            if cliente_id not in clientes_dict:
                clientes_dict[cliente_id] = {
                    'cliente': registro.solicitacao.cliente if registro.solicitacao else None,
                    'registros': [],
                    'credito_disponivel': 0,
                    'valor_total': 0
                }

            registro_dict = {
                'id': registro.id,
                'registro_operacional': registro,
                'numero_nota_fiscal': registro.numero_nota_fiscal,
                'solicitacao': registro.solicitacao if registro.solicitacao else None,
                'produto': registro.solicitacao.produto if registro.solicitacao and hasattr(registro.solicitacao, 'produto') else None,
                'quantidade': registro.peso_liquido_ticket if registro.peso_liquido_ticket else 0,
                'valor_unitario_100': registro.preco_un_nf if registro.preco_un_nf else 0,
                'valor_total_recebimento_100': valor_total_recebimento,
            }

            clientes_dict[cliente_id]['registros'].append(registro_dict)
            clientes_dict[cliente_id]['valor_total'] += valor_total_recebimento

        # Processar NFs complementares agrupadas (se houver)
        nfs_complementares_dict = {}
        if ids_nfs_complementares:
            try:
                from sistema.models_views.faturamento.cargas_a_receber.nf_complementar.nf_complementar_model import NfComplementarModel
                ids_nfs_comp = [int(id.strip()) for id in ids_nfs_complementares.split(',') if id.strip()]
                nfs_complementares = [NfComplementarModel.obter_por_id(nf_id) for nf_id in ids_nfs_comp]
                nfs_complementares = [nf for nf in nfs_complementares if nf and nf.situacao_financeira_id != 5]
                
                for nf in nfs_complementares:
                    cliente_id = nf.cliente_id if nf.cliente else 0
                    if cliente_id not in nfs_complementares_dict:
                        nfs_complementares_dict[cliente_id] = {
                            'cliente': nf.cliente if nf.cliente else None,
                            'nfs': [],
                            'valor_total': 0
                        }
                    
                    nfs_complementares_dict[cliente_id]['nfs'].append(nf)
                    nfs_complementares_dict[cliente_id]['valor_total'] += (nf.valor_total_nota_100 or 0)
                    valor_total_geral += (nf.valor_total_nota_100 or 0)
            except Exception as e:
                print(f"[ERROR] Erro ao processar NFs complementares: {e}")

        # Processar NFs de serviço agrupadas (se houver)
        nfs_servico_dict = {}
        if ids_nfs_servico:
            try:
                from sistema.models_views.faturamento.cargas_a_receber.nf_servico.nf_servico_model import NfServicoModel
                ids_nfs_serv = [int(id.strip()) for id in ids_nfs_servico.split(',') if id.strip()]
                nfs_servico = [NfServicoModel.obter_por_id(nf_id) for nf_id in ids_nfs_serv]
                nfs_servico = [nf for nf in nfs_servico if nf and nf.situacao_financeira_id != 5]
                
                for nf in nfs_servico:
                    cliente_id = nf.cliente_id if nf.cliente else 0
                    if cliente_id not in nfs_servico_dict:
                        nfs_servico_dict[cliente_id] = {
                            'cliente': nf.cliente if nf.cliente else None,
                            'nfs': [],
                            'valor_total': 0
                        }
                    
                    nfs_servico_dict[cliente_id]['nfs'].append(nf)
                    nfs_servico_dict[cliente_id]['valor_total'] += (nf.total_liquido_100 or 0)
                    valor_total_geral += (nf.total_liquido_100 or 0)
            except Exception as e:
                print(f"[ERROR] Erro ao processar NFs de serviço: {e}")

        contas_bancarias = ContaBancariaModel.obter_contas_bancarias_ativas()
        
        saldo_conta_atual = 0
        conta_padrao_id = request.form.get("contaBancaria") or (contas_bancarias[0].id if contas_bancarias else None)
        if conta_padrao_id:
            saldo_obj = SaldoMovimentacaoFinanceiraModel.obter_registro_conta_bancaria(conta_padrao_id)
            if saldo_obj:
                saldo_conta_atual = saldo_obj.valor_total_saldo_100


        if request.method == "POST":
            if gravar_banco:
                try:
                    registros_processados = 0
                    valor_total_processado = 0
                    detalhes_faturamento = []
                    detalhes_nf_complementar = []
                    detalhes_nf_servico = []

                    # Processar cargas a receber
                    for registro in registros:
                        valor_recebido = valores_recebidos_dict.get(registro.id, registro.valor_total_nota_100 or 0)

                        novo_recebimento = RecebimentoModel(
                            cliente_id=registro.solicitacao.cliente_id,
                            registro_operacional_id=registro.id,
                            usuario_id=current_user.id,
                            numero_nota_fiscal=registro.numero_nota_fiscal,
                            valor_total_recebimento_100=valor_recebido,
                            data_recebimento=DataHora.obter_data_atual_padrao_en()
                        )
                        db.session.add(novo_recebimento)
                        db.session.flush()

                        registro.situacao_financeira_id = 5
                        registro.valor_total_nota_100 = valor_recebido

                        registros_processados += 1
                        valor_total_processado += valor_recebido

                        preco_custo_registro = registro.preco_un_nf or 0
                        numero_nf = ""
                        if registro:
                            if getattr(registro, 'estorno_nf', False) and getattr(registro, 'numero_nota_fiscal_estorno', None):
                                numero_nf = f"{registro.numero_nota_fiscal_estorno} *"
                            elif registro.numero_nota_fiscal:
                                numero_nf = registro.numero_nota_fiscal

                        detalhes_faturamento.append({
                            "carga_a_receber_id": registro.id,
                            "solicitacao_id": getattr(registro, 'solicitacao_nf_id', None) if getattr(registro, 'solicitacao', None) else "",
                            "fornecedor_identificacao": registro.solicitacao.fornecedor.identificacao if registro and registro.solicitacao and hasattr(registro.solicitacao, 'fornecedor') and registro.solicitacao.fornecedor else str(getattr(registro, 'fornecedor_id', '')),
                            "cliente_id": registro.solicitacao.cliente.id if registro.solicitacao and hasattr(registro.solicitacao, 'cliente') and registro.solicitacao.cliente else "",
                            "cliente": registro.solicitacao.cliente.identificacao if registro.solicitacao and hasattr(registro.solicitacao, 'cliente') and registro.solicitacao.cliente else "",
                            "valor_bruto": valor_recebido,
                            "valor_credito": 0,
                            "valor_faturado": valor_recebido,
                            "nota_fiscal": numero_nf,
                            "peso_ticket": f"{registro.peso_liquido_ticket}" if registro and getattr(registro, 'peso_liquido_ticket', None) else "",
                            "preco_custo": preco_custo_registro,
                            "produto": registro.solicitacao.produto.nome if registro.solicitacao and hasattr(registro.solicitacao, 'produto') and registro.solicitacao.produto else "",
                            "bitola": registro.solicitacao.bitola.bitola if registro.solicitacao and hasattr(registro.solicitacao, 'bitola') and registro.solicitacao.bitola else "",
                            "data_entrega": registro.data_entrega_ticket.strftime('%d/%m/%Y') if getattr(registro, 'data_entrega_ticket', None) else "",
                            "utiliza_credito": 0,
                            "registro_operacional_id": registro.id if registro else "",
                            "placa_veiculo": registro.solicitacao.veiculo.placa_veiculo if registro.solicitacao and hasattr(registro.solicitacao, 'veiculo') and registro.solicitacao.veiculo else "",
                            "motorista": registro.solicitacao.motorista.nome_completo if registro.solicitacao and hasattr(registro.solicitacao, 'motorista') and registro.solicitacao.motorista else "",
                            "transportadora_id": registro.solicitacao.transportadora_id if registro.solicitacao else "",
                            "transportadora_identificacao": registro.solicitacao.transportadora_exibicao.identificacao if registro.solicitacao else "",
                        })

                    # Processar NFs complementares agrupadas
                    if ids_nfs_complementares:
                        from sistema.models_views.faturamento.cargas_a_receber.nf_complementar.nf_complementar_model import NfComplementarModel
                        ids_nfs_comp = [int(id.strip()) for id in ids_nfs_complementares.split(',') if id.strip()]
                        for nf_id in ids_nfs_comp:
                            nf_complementar = NfComplementarModel.obter_por_id(nf_id)
                            if nf_complementar and nf_complementar.situacao_financeira_id != 5:
                                nf_complementar.situacao_financeira_id = 5
                                valor_total_processado += (nf_complementar.valor_total_nota_100 or 0)
                                
                                detalhes_nf_complementar.append({
                                    "nf_complementar_id": nf_complementar.id,
                                    "numero_nf": nf_complementar.numero_nota_fiscal or "",
                                    "cliente_id": nf_complementar.cliente.id if nf_complementar.cliente else "",
                                    "cliente": nf_complementar.cliente.identificacao if nf_complementar.cliente else "",
                                    "valor_total_nota_100": nf_complementar.valor_total_nota_100 or 0,
                                    "peso_ton_nf": nf_complementar.peso_ton_nf or 0,
                                    "preco_un_nf": nf_complementar.preco_un_nf or 0,
                                    "destinatario_data_emissao": nf_complementar.destinatario_data_emissao.strftime('%d/%m/%Y') if nf_complementar.destinatario_data_emissao else None,
                                })

                    # Processar NFs de serviço agrupadas  
                    if ids_nfs_servico:
                        from sistema.models_views.faturamento.cargas_a_receber.nf_servico.nf_servico_model import NfServicoModel
                        ids_nfs_serv = [int(id.strip()) for id in ids_nfs_servico.split(',') if id.strip()]
                        for nf_id in ids_nfs_serv:
                            nf_servico = NfServicoModel.obter_por_id(nf_id)
                            if nf_servico and nf_servico.situacao_financeira_id != 5:
                                nf_servico.situacao_financeira_id = 5
                                valor_total_processado += (nf_servico.total_liquido_100 or 0)
                                
                                detalhes_nf_servico.append({
                                    "nf_servico_id": nf_servico.id,
                                    "numero_nf": nf_servico.numero_nota_fiscal or "",
                                    "cliente_id": nf_servico.cliente.id if nf_servico.cliente else "",
                                    "cliente": nf_servico.cliente.identificacao if nf_servico.cliente else "",
                                    "valor_total": nf_servico.total_liquido_100 or 0,
                                    "discriminacao": nf_servico.carregamento_discriminacao or nf_servico.discriminacao_servico or "",
                                    "data_emissao": nf_servico.data_emissao.strftime('%d/%m/%Y') if nf_servico.data_emissao else None,
                                })

                    # Criação do faturamento em massa (um único faturamento para todos os registros)
                    ids_nfs_comp_str = ','.join([str(nf_id) for nf_id in ids_nfs_comp]) if 'ids_nfs_comp' in locals() else ''
                    ids_nfs_serv_str = ','.join([str(nf_id) for nf_id in ids_nfs_serv]) if 'ids_nfs_serv' in locals() else ''
                    
                    novo_faturamento = FaturamentoModel(
                        usuario_id=current_user.id,
                        codigo_faturamento=FaturamentoModel.gerar_codigo_novo_faturamento(),
                        valor_total=valor_total_processado,
                        ids_a_receber=','.join([str(r.id) for r in registros]),
                        ids_nf_complementar=ids_nfs_comp_str,
                        ids_nf_servico=ids_nfs_serv_str,
                        utilizou_credito=0,
                        situacao_pagamento_id=7,
                        tipo_operacao=1,
                        direcao_financeira=1
                    )
                    if hasattr(novo_faturamento, 'valor_bruto_total'):
                        novo_faturamento.valor_bruto_total = valor_total_processado
                    if hasattr(novo_faturamento, 'valor_credito_aplicado'):
                        novo_faturamento.valor_credito_aplicado = 0
                    if hasattr(novo_faturamento, 'valor_fornecedor'):
                        novo_faturamento.valor_fornecedor = 0
                    if hasattr(novo_faturamento, 'valor_transportadora'):
                        novo_faturamento.valor_transportadora = 0
                    if hasattr(novo_faturamento, 'valor_extrator'):
                        novo_faturamento.valor_extrator = 0
                    if hasattr(novo_faturamento, 'valor_comissionado'):
                        novo_faturamento.valor_comissionado = 0
                    if hasattr(novo_faturamento, 'valor_receita'):
                        novo_faturamento.valor_receita = valor_total_processado

                    # Salvar detalhes incluindo cargas a receber, NFs complementares e NFs de serviço
                    novo_faturamento.salvar_detalhes(
                        cargas_a_receber=detalhes_faturamento,
                        nf_complementar=detalhes_nf_complementar,
                        nf_servico=detalhes_nf_servico
                    )
                    db.session.add(novo_faturamento)

                    if transacao_ofx and not transacao_ofx.conciliado:
                        transacao_ofx.conciliado = True
                        transacao_ofx.tipo_conciliacao = 'recebimento_cliente_massa'
                        transacao_ofx.data_conciliacao = datetime.now()
                        transacao_ofx.usuario_conciliacao_id = current_user.id
                        transacao_ofx.observacoes_conciliacao = f"Conciliado com {registros_processados} recebimentos em massa"

                        if dados_conciliacao.get('verificar_diferenca'):
                            valor_ofx_centavos = int(transacao_ofx.valor * 100) if transacao_ofx.valor else 0
                            diferenca_centavos = valor_ofx_centavos - valor_total_processado
                            if diferenca_centavos > 0:
                                db.session.commit()
                                diferenca_reais = diferenca_centavos / 100
                                dados_diferenca = {
                                    'tipo_movimentacao_predefinido': 'receita',
                                    'valor_sem_formatacao': diferenca_reais,
                                    'descricao_sugerida': f'Diferença de conciliação massa - {transacao_ofx.fitid}',
                                    'vencimento': datetime.now().strftime('%Y-%m-%d'),
                                    'mesAno': datetime.now().strftime('%m/%Y'),
                                    'tem_diferenca': True,
                                    'transacao_ofx_id': transacao_ofx.id,
                                    'recebimento_massa_ids': [r.id for r in registros]
                                }
                                session['dados_conciliacao'] = dados_diferenca
                                session.modified = True
                                flash((f'Recebimento em massa informado com sucesso!', 'success'))
                                return redirect(url_for('nova_movimentacao_financeira'))

                    PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                        current_user.id,
                        TipoAcaoEnum.CADASTRO,
                        TipoAcaoEnum.CADASTRO.pontos * registros_processados,
                        modulo="informar_recebimento_massa",
                    )

                    db.session.commit()

                    if conciliar_transacao_id:
                        limpar_dados_conciliacao()
                        flash((f"Faturamento em massa e transação OFX conciliada com sucesso!", "success"))
                        return redirect(url_for("listagem_ofx"))
                    else:
                        flash((f"Faturamento em massa informado com sucesso!", "success"))
                        return redirect(url_for("listagem_a_receber"))

                except Exception as e:
                    print(f"[ERROR] Erro ao processar faturamento em massa: {e}")
                    db.session.rollback()
                    dados_conciliacao = session.get('dados_conciliacao', {})
                    if dados_conciliacao.get('transacao_id'):
                        limpar_dados_conciliacao()
                    flash((f"Erro ao processar faturamento em massa: {str(e)}", "error"))
                    return redirect(request.url)

        return render_template(
            "financeiro/informar_recebimento/informar_recebimento_cliente_massa.html",
            campos_obrigatorios=campos_obrigatorios,
            campos_erros=campos_erros,
            dados_corretos=request.form,
            contas_bancarias=contas_bancarias,
            registros=registros,
            clientes_dict=clientes_dict,
            nfs_complementares_dict=nfs_complementares_dict,
            nfs_servico_dict=nfs_servico_dict,
            valor_total=valor_total_geral,
            ids_selecionados=ids_selecionados,
            ids_nfs_complementares=ids_nfs_complementares,
            ids_nfs_servico=ids_nfs_servico,
            saldo_conta_atual=saldo_conta_atual,
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
        flash((f"Erro interno: {str(e)}", "error"))
        return redirect(url_for("listagem_a_receber"))

@app.route("/financeiro/cargas-a-receber/cancelar-recebimento/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def cancelar_informe_recebimento(id):
    try:
        registro = RegistroOperacionalModel.obter_por_id(id)
        
        if not registro:
            mensagem = "Registro não encontrado!"
            tipo = "warning"
            sucesso = False
        else:
            registro.situacao_financeira_id = 2  # 2 = Pendente

            recebimento = RecebimentoModel.obter_recebimento_pore_registro_id(registro.id)
            if recebimento:
                # Obter conta bancária do recebimento
                conta_bancaria_id = recebimento.conta_bancaria_id
                
                recebimento.deletado = 1
                recebimento.ativo = 0

                valor_recebido_100 = recebimento.valor_total_recebimento_100

                # Cancelar movimentação
                movimentacao = MovimentacaoFinanceiraModel.obter_recebimento_por_id(recebimento.id)
                if movimentacao:
                    movimentacao.deletado = 1
                    movimentacao.ativo = 0
                    movimentacao.usuario_id = current_user.id
                    movimentacao.data_movimentacao = datetime.now()
                    movimentacao.movimentacao_financeira_id = None
                
                # Atualizar saldo (subtrair o valor que havia sido recebido)
                saldo_total = SaldoMovimentacaoFinanceiraModel.obter_registro_conta_bancaria(conta_bancaria_id)
                if saldo_total:
                    saldo_total.valor_total_saldo_100 -= valor_recebido_100
                    saldo_total.data_movimentacao = datetime.now()
                else:
                    novo_saldo = SaldoMovimentacaoFinanceiraModel(
                        data_movimentacao=datetime.now(),
                        valor_total_saldo_100=-valor_recebido_100,
                        conta_bancaria_id=conta_bancaria_id
                    )
                    db.session.add(novo_saldo)
            
            db.session.commit()
            
            # Registrar pontuação
            PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                current_user.id,
                TipoAcaoEnum.EDICAO,
                TipoAcaoEnum.EDICAO.pontos,
                modulo="cancelar_recebimento_cliente",
            )
            
            mensagem = "Recebimento cancelado com sucesso!"
            tipo = "success"
            sucesso = True

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": sucesso, "message": mensagem, "type": tipo})

        flash((mensagem, tipo))
        return redirect(url_for("listagem_a_receber"))

    except Exception as e:
        print(f"Erro ao cancelar recebimento: {e}")
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({
                "success": False,
                "message": "Erro ao cancelar recebimento",
                "type": "danger"
            })

        flash(("Erro ao cancelar recebimento", "danger"))
        return redirect(url_for("listagem_a_receber"))