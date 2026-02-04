from datetime import datetime
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem, formatar_data_para_brl
from flask import render_template, request, redirect, url_for, flash, session, jsonify, json
from flask_login import login_required, current_user
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.upload_arquivo.upload_arquivo_model import UploadArquivoModel
from sistema.models_views.faturamento.cargas_a_faturar.fornecedor.fornecedor_a_pagar_model import FornecedorPagarModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
from sistema.models_views.configuracoes_gerais.situacao_pagamento.situacao_pagamento_model import SituacaoPagamentoModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.financeiro.movimentacao_financeira.movimentacao_financeira_model import MovimentacaoFinanceiraModel
from sistema.models_views.financeiro.movimentacao_financeira.saldo_movimentacao_financeira_model import SaldoMovimentacaoFinanceiraModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.configuracoes_gerais.conta_bancaria.conta_bancaria_model import ContaBancariaModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_view import (inicializar_categorias_padrao, obter_subcategorias_recursivo)
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_view import (inicializar_categorias_padrao_categorizacao_fiscal, obter_subcategorias_recursivo_categorizacao_fiscal)
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_model import CategorizacaoFiscalModel
from sistema.models_views.faturamento.cargas_a_faturar.transportadora.frete_a_pagar_model import FretePagarModel
from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx
from sistema.models_views.importacao_ofx.importacao_ofx_view import limpar_dados_conciliacao
from sistema.models_views.importacao_ofx.importacao_ofx_view import verificar_e_limpar_conciliacao_incorreta
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
from sistema.models_views.gerenciar.motorista.motorista_model import MotoristaModel
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema._utilitarios import *
from sistema._utilitarios.utilitario_semanal import UtilitariosSemana

# === Nova Arquitetura de Créditos ===
from sistema.models_views.financeiro.controle_adiantamentos.servico_creditos import ServicoCreditos
from sistema.models_views.financeiro.controle_adiantamentos.transacao_credito_model import (
    TransacaoCreditoModel, TipoTransacaoCredito, TipoPessoa
)
from sistema.models_views.financeiro.controle_adiantamentos.faturamento_credito_vinculo_model import FaturamentoCreditoVinculoModel
from sistema.models_views.financeiro.controle_adiantamentos.historico_transacao_model import HistoricoTransacaoCreditoModel, AcaoHistoricoCredito

@app.route("/financeiro/api/creditos-disponiveis/<tipo_entidade>/<int:entidade_id>", methods=["GET"])
@login_required
@requires_roles
def api_creditos_disponiveis(tipo_entidade, entidade_id):
    """
    API para buscar créditos individuais disponíveis por entidade
    === Usando nova arquitetura via ServicoCreditos ===
    """
    try:
        creditos = []
        
        if tipo_entidade == 'fornecedor':
            creditos = ServicoCreditos.obter_creditos_disponiveis_fornecedor(entidade_id)
        elif tipo_entidade == 'transportadora':
            creditos = ServicoCreditos.obter_creditos_disponiveis_transportadora(entidade_id)
        elif tipo_entidade == 'extrator':
            creditos = ServicoCreditos.obter_creditos_disponiveis_extrator(entidade_id)
        else:
            return jsonify({'error': 'Tipo de entidade inválido'}), 400
            
        return jsonify({
            'success': True,
            'creditos': creditos,
            'total_creditos': len(creditos),
            'valor_total': sum(c.get('valor_credito_100', c.get('saldo_disponivel_100', 0)) for c in creditos)
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
    valor_padrao_semana = None
    
    if semanas_disponiveis:
        valor_padrao_semana = semanas_disponiveis[0]["valor"]

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

@app.route("/financeiro/a-pagar/fornecedor-a-pagar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def fornecedor_a_pagar(id):
    try:
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

        credito_disponivel = ServicoCreditos.obter_saldo_fornecedor(registro.fornecedor_id)
        
        creditos_individuais = ServicoCreditos.obter_creditos_disponiveis_fornecedor(registro.fornecedor_id)

        registro_oper = RegistroOperacionalModel.obter_registro_solicitacao_por_id(
            registro.solicitacao_id
        )
        
        if not registro_oper:
            flash(("Registro operacional não encontrado", "warning"))
            return redirect(url_for("listagem_fornecedores_a_pagar"))

        if request.method == "POST":
            valor_total_calculado = request.form.get("valor_total_calculado", "")
            preco_custo_atualizado = request.form.get("preco_custo_atualizado", "")

            if preco_custo_atualizado:
                # Formata preço de custo para float e depois para inteiro
                preco_custo_float = float(preco_custo_atualizado)
                registro.preco_custo_bitola_100 = preco_custo_float * 100

            if valor_total_calculado:
                valor_total_float = float(valor_total_calculado)
                registro.valor_total_a_pagar_100 = valor_total_float * 100

            # Pega se irá utilizar o credito
            usar_credito = request.form.get("usar_credito")

            # Valor total do faturamento, sem descontos
            valor_pendente = registro.valor_total_a_pagar_100

            # Obtem os créditos utilizados
            creditos_selecionados_ids = request.form.getlist("creditos_selecionados")
            
            # Tratativa de creditos não selecionados
            if usar_credito == "sim" and not creditos_selecionados_ids:
                flash(("Para usar crédito, você deve selecionar pelo menos um crédito disponível!", "warning"))
                return redirect(request.url)
            
            # Verificar se há créditos disponíveis apenas quando não há seleção individual
            if usar_credito == "sim" and credito_disponivel == 0 and not creditos_selecionados_ids:
                flash(("O fornecedor não possui crédito disponível!", "warning"))
                return redirect(request.url)
            
            # Coloca registro como faturado
            registro.situacao_pagamento_id = 5

            novo_faturamento = FaturamentoModel(
                usuario_id=current_user.id,
                codigo_faturamento=FaturamentoModel.gerar_codigo_novo_faturamento(),
                valor_total=valor_pendente,
                ids_fornecedores=str(registro.id), # Ids da tabela fornecedores a pagar 
                ids_fretes=None,
                utilizou_credito=(usar_credito == "sim"),
                tipo_operacao=1,
                direcao_financeira=2
            )
            if hasattr(novo_faturamento, 'valor_bruto_total'):
                novo_faturamento.valor_bruto_total = valor_pendente
            if hasattr(novo_faturamento, 'valor_credito_aplicado'):
                novo_faturamento.valor_credito_aplicado = 0  # Será atualizado depois
            if hasattr(novo_faturamento, 'valor_fornecedor'):
                novo_faturamento.valor_fornecedor = valor_pendente  # Será atualizado depois
            if hasattr(novo_faturamento, 'valor_transportadora'):
                novo_faturamento.valor_transportadora = 0
            
            db.session.add(novo_faturamento)
            # Obter ID do faturamento ANTES de processar créditos
            db.session.flush()
            
            detalhes_creditos_utilizados = []
            total_credito_aplicado = 0
            resultado_creditos = None
            
            if usar_credito == "sim" and creditos_selecionados_ids:
                # Obtem cada crédito id selecionado como inteiro
                creditos_ids_int = [int(cid) for cid in creditos_selecionados_ids]
                
                # Calcular total disponível nos créditos selecionados usando NOVA ARQUITETURA
                total_creditos_selecionados = 0
                for credito_id in creditos_ids_int:
                    credito = TransacaoCreditoModel.query.get(credito_id)
                    if credito and credito.tipo_pessoa == TipoPessoa.FORNECEDOR:
                        # Obtem saldo disponível do crédito
                        saldo_disponivel = credito.obter_saldo_disponivel_100()
                        if saldo_disponivel == 0:
                            db.session.rollback()
                            flash(f"O crédito selecionado '{credito.descricao}' possui saldo zerado!", "warning")
                            return redirect(request.url)
                        
                        total_creditos_selecionados += saldo_disponivel
                        
                        # Captura detalhes para o faturamento
                        detalhes_creditos_utilizados.append({
                            'tipo': 'fornecedor',
                            'credito_id': credito.id,
                            'entidade_id': credito.fornecedor_id,
                            'entidade_nome': registro.fornecedor.identificacao if registro.fornecedor else 'N/A',
                            'valor': saldo_disponivel,
                            'descricao': credito.descricao,
                            'data_movimentacao': credito.data_movimentacao.strftime('%d/%m/%Y') if credito.data_movimentacao else ''
                        })
                
                if total_creditos_selecionados == 0:
                    db.session.rollback()
                    flash(("O total dos créditos selecionados é zero.", "warning"))
                    return redirect(request.url)
                
                if total_creditos_selecionados < 0:
                    valor_credito_a_usar = total_creditos_selecionados
                else:
                    # Não pode usar mais crédito do que o valor pendente
                    valor_credito_a_usar = min(total_creditos_selecionados, valor_pendente)
                
                # Processar a utilização dos créditos
                resultado_creditos = ServicoCreditos.processar_utilizacao_creditos(
                    tipo='fornecedor',
                    pessoa_id=registro.fornecedor_id,
                    creditos_ids=creditos_ids_int,
                    valor_maximo_100=abs(valor_credito_a_usar),
                    usuario_id=current_user.id,
                    faturamento_id=novo_faturamento.id, # Rastreabilidade de faturamento destino dos créditos
                    descricao_base=None
                )
                
                if resultado_creditos['sucesso']:
                    total_credito_aplicado = resultado_creditos['total_utilizado_100']
                    
                    registro.utiliza_credito = 1
                    registro.valor_credito_100 = total_credito_aplicado
                    
                    # Calcular novo valor líquido após aplicação do crédito
                    valor_liquido = valor_pendente - total_credito_aplicado
                    
                    # Passa o valor real do faturamento (2000 - 1000 = 1000)
                    novo_faturamento.valor_total = valor_liquido
                    
                    if hasattr(novo_faturamento, 'valor_credito_aplicado'):
                        novo_faturamento.valor_credito_aplicado = total_credito_aplicado
                    if hasattr(novo_faturamento, 'valor_fornecedor'):
                        novo_faturamento.valor_fornecedor = valor_liquido
                    
                    # Atualizar valores nos detalhes com os valores efetivamente utilizados
                    for i, proc in enumerate(resultado_creditos.get('creditos_processados', [])):
                        if i < len(detalhes_creditos_utilizados):
                            detalhes_creditos_utilizados[i]['valor'] = proc.get('valor_utilizado', 0)
                else:
                    db.session.rollback()
                    registro.utiliza_credito = 0
                    registro.valor_credito_100 = 0
                    flash((f"Erro ao processar créditos: {resultado_creditos.get('mensagem', 'Erro desconhecido')}", "warning"))
                    return redirect(request.url)
            else:
                registro.utiliza_credito = 0
                registro.valor_credito_100 = 0

            # Preparar detalhes do fornecedor para o faturamento
            valor_bruto_registro = registro.valor_total_a_pagar_100 or 0
            # Recuperar valor do crédito do registro
            valor_credito_registro = registro.valor_credito_100 or 0
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
            
            if novo_faturamento.valor_total == 0:
                novo_faturamento.situacao_pagamento_id = 8 # Conciliado
            else:
                novo_faturamento.situacao_pagamento_id = 7 # Não Categorizado

            PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                current_user.id,
                TipoAcaoEnum.CADASTRO,
                TipoAcaoEnum.CADASTRO.pontos,
                modulo="informar_faturamento_fornecedor",
            )
            db.session.commit()
            
            flash(("Faturamento do fornecedor informado com sucesso!", "success"))
            return redirect(url_for("listagem_fornecedores_a_pagar"))

        return render_template(
            "financeiro/informar_pagamento/informar_pagamento_fornecedor.html",
            dados_corretos=request.form,
            registro=registro,
            registro_operacional=registro_oper,
            saldo_credito=credito_disponivel,
            creditos_individuais=creditos_individuais
        )

    except Exception as e:
        print("[ERROR fornecedor_a_pagar]", e)
        db.session.rollback()
        flash(("Erro ao informar faturamento do fornecedor! Contate o suporte.", "warning"))
        return redirect(url_for("listagem_fornecedores_a_pagar"))
       
@app.route("/financeiro/a-pagar/fornecedor-a-pagar-massa", methods=["GET", "POST"])
@login_required
@requires_roles
def fornecedor_a_pagar_massa():
    """
    Função para faturamento em massa de fornecedores e transportadoras.
    Permite aplicar créditos individuais e editar valores antes de confirmar.
    """
    try:
        # === INICIALIZAÇÃO DE VARIÁVEIS ===
        campos_obrigatorios = {}
        campos_erros = {}
        fretes_dict = {}
        creditos_selecionados = {}
        
        # Capturar datas do período do filtro (da URL)
        data_inicio_filtro_str = request.args.get('dataInicio', '')
        data_fim_filtro_str = request.args.get('dataFim', '')
        tipo_periodo_filtro = request.args.get('tipoFiltro', 'quinzenal')
      
        # Obter IDs selecionados (GET ou POST)
        if request.method == "GET":
            ids_selecionados = request.args.get('ids', '')
        else:
            ids_selecionados = request.form.get('ids_registros', '')
        
        # Validar se há IDs selecionados
        if not ids_selecionados:
            flash(("Nenhum registro foi selecionado para faturamento!", "warning"))
            return redirect(url_for("listagem_fornecedores_a_pagar"))
        
        # Converter IDs para lista de inteiros
        ids_list = [int(id.strip()) for id in ids_selecionados.split(',') if id.strip()]

        # === PROCESSAMENTO DE FRETES (TRANSPORTADORAS) ===
        fretes_selecionados = request.form.get('ids_fretes', '') or request.args.get('fretes', '')
        
        if fretes_selecionados:
            try:
                # Converter IDs de fretes para lista de inteiros
                fretes_ids = [int(id.strip()) for id in fretes_selecionados.split(',') if id.strip()]
                
                # Buscar fretes válidos (situação = 2: Pendente)
                fretes_list = FretePagarModel.query.filter(
                    FretePagarModel.id.in_(fretes_ids),
                    FretePagarModel.situacao_pagamento_id == 2 
                ).all()

                # Agrupar fretes por transportadora
                for frete in fretes_list:
                    # Obter registro operacional associado
                    registro_oper = RegistroOperacionalModel.obter_registro_solicitacao_por_id(frete.solicitacao_id)
                    frete.registro_operacional = registro_oper
                
                    transportadora_id = frete.transportadora_id
                    
                    # Inicializar dados da transportadora se ainda não existe
                    if transportadora_id not in fretes_dict:
                        credito_disponivel_transp = ServicoCreditos.obter_saldo_transportadora(transportadora_id)
                        creditos_individuais_transp = ServicoCreditos.obter_creditos_disponiveis_transportadora(transportadora_id)
                        
                        fretes_dict[transportadora_id] = {
                            'fretes': [],
                            'registros_operacionais': [],
                            'valor_total': 0,
                            'transportadora': frete.transportadora,
                            'credito_disponivel': credito_disponivel_transp or 0,
                            'creditos_individuais': creditos_individuais_transp
                        }
                    
                    # Adicionar frete ao grupo da transportadora
                    fretes_dict[transportadora_id]['fretes'].append(frete)
                    fretes_dict[transportadora_id]['valor_total'] += frete.valor_total_a_pagar_100 or 0

                    if frete.registro_operacional:
                        fretes_dict[transportadora_id]['registros_operacionais'].append(frete.registro_operacional)
                        
            except ValueError as e:
                print(f"[ERROR fornecedor_a_pagar_massa - fretes] {e}")
                flash(("IDs de fretes inválidos!", "warning"))
        
        # === PROCESSAMENTO DE FORNECEDORES ===
        # Buscar registros de fornecedores válidos (situação = 2: Pendente)
        registros = FornecedorPagarModel.query.filter(
            FornecedorPagarModel.id.in_(ids_list),
            FornecedorPagarModel.situacao_pagamento_id == 2
        ).all()

        # Validar se encontrou registros válidos
        if not registros:
            flash(("Nenhum registro válido encontrado para faturamento!", "warning"))
            return redirect(url_for("listagem_fornecedores_a_pagar"))
        
        # Verificar se algum registro já foi pago
        if len(registros) != len(ids_list):
            flash(("Alguns registros selecionados não estão disponíveis para faturamento!", "warning"))

        # Associar registros operacionais a cada fornecedor
        for registro in registros:
            if not hasattr(registro, 'registro_operacional') or registro.registro_operacional is None:
                registro_oper = RegistroOperacionalModel.obter_registro_solicitacao_por_id(registro.solicitacao_id)
                registro.registro_operacional = registro_oper

        # Agrupar fornecedores e calcular totais
        fornecedores_dict = {}
        
        for registro in registros:
            if registro.valor_total_a_pagar_100 is None:
                continue
            
            fornecedor_id = registro.fornecedor_id

            # Inicializar dados do fornecedor se ainda não existe
            if fornecedor_id not in fornecedores_dict:
                credito_disponivel = ServicoCreditos.obter_saldo_fornecedor(fornecedor_id)
                creditos_individuais = ServicoCreditos.obter_creditos_disponiveis_fornecedor(fornecedor_id)
                
                fornecedores_dict[fornecedor_id] = {
                    'registros': [],
                    'valor_total': 0,
                    'credito_disponivel': credito_disponivel or 0,
                    'creditos_individuais': creditos_individuais,
                    'fornecedor': None
                }
            
            # Adicionar registro ao grupo do fornecedor
            fornecedores_dict[fornecedor_id]['registros'].append(registro)
            fornecedores_dict[fornecedor_id]['valor_total'] += registro.valor_total_a_pagar_100
            
            # Associar objeto fornecedor
            if not fornecedores_dict[fornecedor_id]['fornecedor']:
                if (registro.registro_operacional and 
                    registro.registro_operacional.solicitacao and 
                    registro.registro_operacional.solicitacao.fornecedor):
                    fornecedores_dict[fornecedor_id]['fornecedor'] = registro.registro_operacional.solicitacao.fornecedor
        
        def calcular_totais():
            """Calcula todos os totais de forma centralizada"""
            # Total de fornecedores
            valor_total_fornecedores = sum(d['valor_total'] for d in fornecedores_dict.values())
            
            # Total de fretes
            valor_total_fretes = sum(d['valor_total'] for d in fretes_dict.values())
            
            # Total geral
            valor_total_geral = valor_total_fornecedores + valor_total_fretes
            
            # Quantidade de registros
            total_registros_fornecedores = sum(len(d['registros']) for d in fornecedores_dict.values())
            total_registros_fretes = sum(len(d['fretes']) for d in fretes_dict.values())
            total_registros = total_registros_fornecedores + total_registros_fretes
            
            # Créditos disponíveis
            credito_fornecedores = sum(f['credito_disponivel'] for f in fornecedores_dict.values())
            credito_transportadoras = sum(f['credito_disponivel'] for f in fretes_dict.values())
            credito_total = credito_fornecedores + credito_transportadoras
            
            return {
                'valor_total_fornecedores': valor_total_fornecedores,
                'valor_total_fretes': valor_total_fretes,
                'valor_total_geral': valor_total_geral,
                'total_registros': total_registros,
                'total_registros_fornecedores': total_registros_fornecedores,
                'total_registros_fretes': total_registros_fretes,
                'credito_fornecedores': credito_fornecedores,
                'credito_transportadoras': credito_transportadoras,
                'credito_total': credito_total
            }
        
        # Calcular totais iniciais
        totais = calcular_totais()

        # === PROCESSAMENTO POST - CONFIRMAÇÃO DE FATURAMENTO ===
        if request.method == "POST":
            usar_credito = request.form.get("usar_credito")
            
            # Capturar datas do período do filtro
            data_inicio_filtro_str = request.form.get("data_inicio_filtro")
            data_fim_filtro_str = request.form.get("data_fim_filtro")
            tipo_periodo_filtro = request.form.get("tipo_periodo_filtro", "quinzenal")
            
            # Converter strings para date
            data_inicio_filtro = None
            data_fim_filtro = None
            if data_inicio_filtro_str:
                try:
                    data_inicio_filtro = datetime.strptime(data_inicio_filtro_str, "%Y-%m-%d").date()
                except ValueError:
                    pass
            if data_fim_filtro_str:
                try:
                    data_fim_filtro = datetime.strptime(data_fim_filtro_str, "%Y-%m-%d").date()
                except ValueError:
                    pass
            
            # Processar créditos selecionados individualmente
            creditos_selecionados_json = request.form.get("creditos_selecionados", "{}")
            try:
                creditos_selecionados = json.loads(creditos_selecionados_json) if creditos_selecionados_json else {}
            except json.JSONDecodeError:
                creditos_selecionados = {}
            
            # Obter valores editados pelo usuário
            valores_calculados_json = request.form.get("valores_calculados", "")
            valores_calculados = json.loads(valores_calculados_json) if valores_calculados_json else {}

            valores_calculados_fretes_json = request.form.get("valores_calculados_fretes", "")
            valores_calculados_fretes = json.loads(valores_calculados_fretes_json) if valores_calculados_fretes_json else {}

            alteracoes_detectadas = False

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

            # Recalcular totais gerais usando função auxiliar
            totais = calcular_totais()
            valor_total_geral = totais['valor_total_geral']

            # O faturamento precisa ser criado ANTES de processar créditos
            # para que tenhamos um faturamento_id válido para vincular as transações
            novo_faturamento = FaturamentoModel(
                usuario_id=current_user.id,
                codigo_faturamento=FaturamentoModel.gerar_codigo_novo_faturamento(),
                valor_total=valor_total_geral,  # Será atualizado após aplicação de créditos
                ids_fornecedores=ids_selecionados,
                ids_fretes=','.join(str(transp_id) for transp_id in fretes_dict.keys()) if fretes_dict else None,
                utilizou_credito=(usar_credito == "sim"),
                tipo_operacao=1,  # carga
                direcao_financeira=2,  # despesa
                data_inicio_filtro=data_inicio_filtro,
                data_fim_filtro=data_fim_filtro,
                tipo_periodo_filtro=tipo_periodo_filtro
            )

            # Configurar campos adicionais se o modelo suportar
            if hasattr(novo_faturamento, 'valor_bruto_total'):
                novo_faturamento.valor_bruto_total = valor_total_geral
            if hasattr(novo_faturamento, 'valor_credito_aplicado'):
                novo_faturamento.valor_credito_aplicado = 0  # Será atualizado após processar créditos
            if hasattr(novo_faturamento, 'valor_fornecedor'):
                novo_faturamento.valor_fornecedor = totais['valor_total_fornecedores']
            if hasattr(novo_faturamento, 'valor_transportadora'):
                novo_faturamento.valor_transportadora = totais['valor_total_fretes']
            
            # Definir situação inicial
            novo_faturamento.situacao_pagamento_id = 7  # Não Categorizado
            
            db.session.add(novo_faturamento)
            db.session.flush()
            
            # Inicializar variáveis de controle
            total_credito_aplicado = 0
            detalhes_creditos_utilizados = {
                'fornecedores': [],
                'transportadoras': []
            }
            
            if usar_credito == "sim":
                # Verificar créditos selecionados e calcular total disponível
                total_creditos_selecionados = 0
                
                # Somar saldos de todos os créditos selecionados
                for tipo_entidade, entidades in creditos_selecionados.items():
                    for entidade_id, credito_ids in entidades.items():
                        for credito_id in credito_ids:
                            credito = TransacaoCreditoModel.query.get(credito_id)
                            if credito:
                                # Obter saldo disponível (pode ser negativo para débitos)
                                saldo_disponivel = credito.obter_saldo_disponivel_100()
                                total_creditos_selecionados += saldo_disponivel
                
                # Validar se há créditos selecionados
                if not creditos_selecionados or (not creditos_selecionados.get('fornecedor') and not creditos_selecionados.get('transportadora')):
                    db.session.rollback()
                    flash(("Nenhum crédito selecionado para aplicar!", "warning"))
                    redirect_url = url_for("fornecedor_a_pagar_massa", ids=ids_selecionados)
                    if fretes_selecionados:
                        redirect_url += f"&fretes={fretes_selecionados}"
                    return redirect(redirect_url)
                
                # Calcular limite de crédito a usar
                # Para créditos negativos (débitos), não há limite - eles AUMENTAM o valor total
                # Para créditos positivos, limitar ao valor da fatura
                # valor_total_geral já inclui fornecedores + fretes (calculado em calcular_totais())
                valor_total_geral_com_fretes = valor_total_geral  # Já inclui fretes
                credito_restante_para_usar = float('inf') if total_creditos_selecionados < 0 else valor_total_geral_com_fretes
                
                # Processar créditos de FORNECEDORES
                credito_fornecedores_aplicado = 0
                if 'fornecedor' in creditos_selecionados:
                    for fornecedor_id_str, credito_ids in creditos_selecionados['fornecedor'].items():
                        fornecedor_id = int(fornecedor_id_str)
                        
                        # Utilizar ServicoCreditos para processar (vincula ao faturamento_id)
                        resultado_utilizacao = ServicoCreditos.processar_utilizacao_creditos(
                            tipo='fornecedor',
                            pessoa_id=fornecedor_id,
                            creditos_ids=credito_ids,
                            valor_maximo_100=int(credito_restante_para_usar) if credito_restante_para_usar != float('inf') else 999999999,
                            usuario_id=current_user.id,
                            faturamento_id=novo_faturamento.id, # ID válido obtido após flush()
                            descricao_base=None  # Usar descrição padrão
                        )
                        
                        if resultado_utilizacao.get('sucesso'):
                            valor_utilizado = resultado_utilizacao.get('total_utilizado_100', 0)
                            credito_fornecedores_aplicado += valor_utilizado
                            total_credito_aplicado += valor_utilizado
                            credito_restante_para_usar -= valor_utilizado
                            
                            # Armazenar detalhes para registro histórico
                            for cred_proc in resultado_utilizacao.get('creditos_processados', []):
                                detalhes_creditos_utilizados['fornecedores'].append({
                                    'credito_id': cred_proc.get('credito_id'),
                                    'fornecedor_id': fornecedor_id,
                                    'valor': cred_proc.get('valor_utilizado', 0),
                                    'descricao': cred_proc.get('descricao', ''),
                                    'data_movimentacao': cred_proc.get('data_movimentacao', '')
                                })

                # Processar créditos de TRANSPORTADORAS
                credito_transportadoras_aplicado = 0
                if 'transportadora' in creditos_selecionados:
                    for transportadora_id_str, credito_ids in creditos_selecionados['transportadora'].items():
                        transportadora_id = int(transportadora_id_str)
                        
                        # Utilizar ServicoCreditos para processar (vincula ao faturamento_id)
                        resultado_utilizacao = ServicoCreditos.processar_utilizacao_creditos(
                            tipo='freteiro',
                            pessoa_id=transportadora_id,
                            creditos_ids=credito_ids,
                            valor_maximo_100=int(credito_restante_para_usar) if credito_restante_para_usar != float('inf') else 999999999,
                            usuario_id=current_user.id,
                            faturamento_id=novo_faturamento.id,  # ID válido obtido após flush()
                            descricao_base=None  # Usar descrição padrão
                        )
                        
                        if resultado_utilizacao.get('sucesso'):
                            valor_utilizado = resultado_utilizacao.get('total_utilizado_100', 0)
                            credito_transportadoras_aplicado += valor_utilizado
                            total_credito_aplicado += valor_utilizado
                            credito_restante_para_usar -= valor_utilizado
                            
                            # Armazenar detalhes para registro histórico
                            for cred_proc in resultado_utilizacao.get('creditos_processados', []):
                                detalhes_creditos_utilizados['transportadoras'].append({
                                    'credito_id': cred_proc.get('credito_id'),
                                    'transportadora_id': transportadora_id,
                                    'valor': cred_proc.get('valor_utilizado', 0),
                                    'descricao': cred_proc.get('descricao', ''),
                                    'data_movimentacao': cred_proc.get('data_movimentacao', '')
                                })

                # Calcular valor final após aplicação de créditos
                # Observação: Créditos negativos (débitos) AUMENTAM o valor total
                # Exemplo: R$ 3.822,45 - (-R$ 222,22) = R$ 4.044,67
                total_credito_utilizado = total_credito_aplicado
                valor_final_global = valor_total_geral_com_fretes - total_credito_utilizado
                
                # Distribuir valor final proporcionalmente entre fornecedores e fretes
                valor_final_fornecedores = 0
                valor_final_fretes = 0
                if valor_total_geral_com_fretes > 0:
                    # Usar totais['valor_total_fornecedores'] pois valor_total_geral já inclui fretes
                    proporcao_fornecedores = totais['valor_total_fornecedores'] / valor_total_geral_com_fretes
                    proporcao_fretes = totais.get('valor_total_fretes', 0) / valor_total_geral_com_fretes
                    
                    valor_final_fornecedores = valor_final_global * proporcao_fornecedores
                    valor_final_fretes = valor_final_global * proporcao_fretes
                
                # Atualizar valores no faturamento
                novo_faturamento.valor_total = valor_final_global
                if hasattr(novo_faturamento, 'valor_credito_aplicado'):
                    novo_faturamento.valor_credito_aplicado = total_credito_aplicado
                if hasattr(novo_faturamento, 'valor_fornecedor'):
                    novo_faturamento.valor_fornecedor = valor_final_fornecedores
                if hasattr(novo_faturamento, 'valor_transportadora'):
                    novo_faturamento.valor_transportadora = valor_final_fretes
                
                # Marcar registros como usando crédito (para relatórios e auditoria)
                if total_credito_aplicado != 0:
                    # Marcar fornecedores
                    for fornecedor_id, dados in fornecedores_dict.items():
                        for registro in dados['registros']:
                            registro.utiliza_credito = 1
                            registro.valor_credito_100 = 0  # Valor proporcional pode ser calculado depois
                    
                    # Marcar transportadoras
                    for transportadora_id, dados_transp in fretes_dict.items():
                        for frete in dados_transp['fretes']:
                            frete.utiliza_credito = 1
                            frete.valor_credito_100 = 0  # Valor proporcional pode ser calculado depois
            
            # Verificar se faturamento deve ser marcado como conciliado (valor zero)
            if novo_faturamento.valor_total == 0:
                novo_faturamento.situacao_pagamento_id = 8  # Conciliado

            # Criando detalhes json para frontend
            detalhes_fornecedores = []
            for fornecedor_id, dados in fornecedores_dict.items():
                for reg in dados['registros']:
                    print("DEBUG reg:", reg, "registro_operacional:", getattr(reg, 'registro_operacional', None))
                    # Calcular valor efetivo após crédito aplicado (créditos negativos somam)
                    valor_bruto_registro = reg.valor_total_a_pagar_100 or 0
                    valor_credito_registro = getattr(reg, 'valor_credito_100', 0) or 0
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
                        "utiliza_credito": getattr(reg, 'utiliza_credito', 0) or 0,
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
                    valor_credito_frete = getattr(frete, 'valor_credito_100', 0) or 0
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
                        "utiliza_credito": getattr(frete, 'utiliza_credito', 0) or 0,
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
                        modulo=f"informar_faturamento_transportadora_com_agrupamento_massa_{frete.id}",
                    )

            # Salvar detalhes no faturamento
            novo_faturamento.salvar_detalhes(
                fornecedores=detalhes_fornecedores, 
                transportadoras=detalhes_transportadoras,
                credito_fornecedor=detalhes_creditos_utilizados['fornecedores'],
                credito_transportadora=detalhes_creditos_utilizados['transportadoras']
            )

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
        
        # Renderizar página com dados para seleção e confirmação
        return render_template(
            "financeiro/informar_pagamento/informar_pagamento_fornecedor_massa.html",
            campos_obrigatorios=campos_obrigatorios,
            campos_erros=campos_erros,
            dados_corretos=request.form,
            registros=registros,
            fornecedores_dict=fornecedores_dict,
            # Valores calculados pela função auxiliar
            valor_total_geral=totais['valor_total_geral'],
            valor_total_fretes=totais['valor_total_fretes'],
            valor_total_geral_com_fretes=totais['valor_total_geral'],
            # Créditos disponíveis
            total_credito_disponivel=totais['credito_fornecedores'],
            total_credito_disponivel_geral=totais['credito_total'], 
            total_credito_fornecedores=totais['credito_fornecedores'], 
            total_credito_transportadoras=totais['credito_transportadoras'], 
            # Contadores de registros
            total_registros_completo=totais['total_registros'],
            total_registros_fretes=totais['total_registros_fretes'],
            # Outros dados
            ids_selecionados=ids_selecionados,
            fretes_dict=fretes_dict,
            creditos_selecionados=creditos_selecionados,
            # Datas do período do filtro
            data_inicio_filtro=data_inicio_filtro_str,
            data_fim_filtro=data_fim_filtro_str,
            tipo_periodo_filtro=tipo_periodo_filtro,
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

        # Estornar créditos se foram utilizados
        if usou_credito and valor_credito != 0:
            # Buscar o faturamento associado a este pagamento
            faturamento = FaturamentoModel.query.filter(
                FaturamentoModel.ids_fornecedores.contains(str(registro.id))
            ).first()
            
            if faturamento:
                resultado_estorno = ServicoCreditos.estornar_utilizacao_creditos(
                    faturamento_id=faturamento.id,
                    usuario_id=current_user.id,
                    motivo=f"Cancelamento de pagamento de fornecedor ID {registro.id}"
                )
                if not resultado_estorno.get('sucesso'):
                    print(f"[WARN] Erro ao estornar créditos: {resultado_estorno.get('mensagem')}")

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
