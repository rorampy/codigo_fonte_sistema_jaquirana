from datetime import datetime
import io
import json
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem, formatar_float_para_brl
from sistema._utilitarios.data_e_hora import DataHora
from werkzeug.utils import secure_filename
from flask import render_template, request, redirect, url_for, flash, session, jsonify, Response
from flask_login import login_required, current_user
from sistema.models_views.financeiro.movimentacao_financeira.movimentacao_financeira_model import MovimentacaoFinanceiraModel
from sistema.models_views.financeiro.movimentacao_financeira.saldo_movimentacao_financeira_model import SaldoMovimentacaoFinanceiraModel
from sistema.models_views.faturamento.cargas_a_pagar.transportadora.frete_a_pagar_model import FretePagarModel
from sistema.models_views.faturamento.cargas_a_pagar.extrator.extrator_a_pagar_model import ExtratorPagarModel
from sistema.models_views.faturamento.cargas_a_pagar.fornecedor.fornecedor_a_pagar_model import FornecedorPagarModel
from sistema.models_views.controle_carga.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.configuracoes_gerais.conta_bancaria.conta_bancaria_model import ContaBancariaModel
from sistema.models_views.configuracoes_gerais.centro_custo.centro_custo_model import CentroCustoModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_model import CategorizacaoFiscalModel
from sistema.models_views.financeiro.movimentacao_financeira.lancamento_movimentacao_extra_model import LancamentoMovimentacaoExtraModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_view import inicializar_categorias_padrao
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_view import inicializar_categorias_padrao_categorizacao_fiscal, obter_subcategorias_recursivo_categorizacao_fiscal
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx
from sistema.models_views.importacao_ofx.importacao_ofx_view import limpar_dados_conciliacao
from sistema.models_views.importacao_ofx.importacao_ofx_view import verificar_e_limpar_conciliacao_incorreta
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema.models_views.faturamento.faturamento_model import FaturamentoModel
from sistema.models_views.financeiro.situacao_pagamento_model import SituacaoPagamentoModel
from sistema.models_views.gerenciar.pessoa_financeiro.pessoa_financeiro_model import PessoaFinanceiroModel
from sistema.models_views.financeiro.operacional.categorizar_fatura.categorizacao_model import AgendamentoPagamentoModel
from sistema.models_views.financeiro.operacional.categorizar_fatura.parcela_categorizacao.parcela_categorizacao_model import ParcelaCategorizacaoModel
from sistema.models_views.financeiro.lancamento_avulso.lancamento_avulso_model import LancamentoAvulsoModel
from datetime import datetime, date
from sistema._utilitarios import *
    

@app.route("/financeiro/contas-bancarias/conciliacao", methods=["GET", "POST"])
@login_required
@requires_roles
def conciliacao_contas_bancarias():
    conta_selecionada_id = request.args.get("conta_bancaria_id", type=int)

    stats_transacoes = ImportacaoOfx.obter_estatisticas_transacoes()

    transacoes_nao_conciliadas = stats_transacoes.get('nao_conciliadas', 0)

    movimentacoes = MovimentacaoFinanceiraModel.listagem_movimentacoes_financeiras_por_conta(conta_selecionada_id)
    contas_bancarias = ContaBancariaModel.obter_contas_bancarias_ativas()
    saldo = SaldoMovimentacaoFinanceiraModel.obter_registro_saldo_por_conta_bancaria(conta_selecionada_id)
    saldo_disponivel = saldo

    a_pagar_frete = FretePagarModel.obter_valor_total_a_pagar()
    a_pagar_fornecedor = FornecedorPagarModel.obter_valor_total_a_pagar()
    a_pagar_extrator = ExtratorPagarModel.obter_valor_total_a_pagar()

    valor_total_pagar = int(a_pagar_frete + a_pagar_fornecedor + a_pagar_extrator)

    total_a_receber = RegistroOperacionalModel.obter_valor_total_a_receber_por_conta(conta_selecionada_id)
    total_recebido = MovimentacaoFinanceiraModel.obter_valor_total_recebidos(conta_selecionada_id)

    valor_total_pago = MovimentacaoFinanceiraModel.obter_valor_total_saidas(conta_selecionada_id)

    return render_template(
        "financeiro/contas_bancarias/contas_bancarias.html",
        movimentacoes=movimentacoes,
        conta_selecionada_id=conta_selecionada_id,
        dados_corretos=request.form,
        saldo_disponivel=saldo_disponivel,
        valor_total_pagar=valor_total_pagar,
        contas_bancarias=contas_bancarias,
        valor_total_pago=valor_total_pago,
        total_a_receber=total_a_receber,
        total_recebido=total_recebido,
        transacoes_nao_conciliadas=transacoes_nao_conciliadas
    )
    
@app.route("/financeiro/movimentacoes-financeiras/listagem-ofx")
@login_required
@requires_roles
def listagem_ofx():
    batch_id = session.get('current_batch_id') or ImportacaoOfx.obter_ultimo_batch_importacao()

    if not batch_id:
        flash(('Nenhum arquivo OFX foi importado. Importe um arquivo primeiro.', 'warning'))
        return redirect(url_for('importar_ofx'))
    
    # Parâmetros de filtros
    filtro_data_inicio = request.args.get('dataInicio', '').strip()
    filtro_data_fim = request.args.get('dataFim', '').strip()
    filtro_conciliado = request.args.get('conciliado', 'nao')
    filtro_fitid = request.args.get('fitid', '').strip()
    filtro_descricao = request.args.get('descricao', '').strip()
    filtro_valor = request.args.get('valor', '')
    filtro_tipo_movimentacao = request.args.get('tipo_movimentacao', '').strip()
    if filtro_valor == 'R$ 0,00':
        filtro_valor = ''
    
    pagina = int(request.args.get('pagina', 1))
    por_pagina = 200
    
    # Query simples das transações
    conciliado_val = filtro_conciliado == 'sim'
    transacoes = ImportacaoOfx.query.filter_by(conciliado=conciliado_val)
    
    # Aplicar filtros
    if filtro_data_inicio:
        transacoes = transacoes.filter(ImportacaoOfx.data_transacao >= filtro_data_inicio)
    if filtro_data_fim:
        transacoes = transacoes.filter(ImportacaoOfx.data_transacao <= filtro_data_fim)
    if filtro_fitid:
        transacoes = transacoes.filter(ImportacaoOfx.fitid.ilike(f'%{filtro_fitid}%'))
    if filtro_valor:
        transacoes = transacoes.filter(ImportacaoOfx.valor_formatado.ilike(f'%{filtro_valor}%'))
    if filtro_descricao:
        transacoes = transacoes.filter(ImportacaoOfx.descricao_limpa.ilike(f'%{filtro_descricao}%'))
 
    if filtro_tipo_movimentacao:
        if filtro_tipo_movimentacao == 'entrada':
            # Filtrar apenas valores positivos
            transacoes = transacoes.filter(ImportacaoOfx.valor > 0)
        elif filtro_tipo_movimentacao == 'saida':
            # Filtrar apenas valores negativos
            transacoes = transacoes.filter(ImportacaoOfx.valor < 0)

    # Paginação
    total_transacoes = transacoes.count()
    transacoes = transacoes.order_by(ImportacaoOfx.data_transacao.desc(), ImportacaoOfx.id.desc())\
                           .offset((pagina-1)*por_pagina)\
                           .limit(por_pagina)\
                           .all()
    
    total_paginas = (total_transacoes // por_pagina) + (1 if total_transacoes % por_pagina else 0)
    
    # Obter resumo e estrutura
    resumo_bd = ImportacaoOfx.obter_resumo_importacao(
        data_inicio=filtro_data_inicio if filtro_data_inicio else None,
        data_fim=filtro_data_fim if filtro_data_fim else None,
        batch_id=None,
        conciliado=conciliado_val,
        ftid=filtro_fitid if filtro_fitid else None,
        valor=filtro_valor if filtro_valor else '',
        descricao=filtro_descricao if filtro_descricao else None,
        tipo_movimentacao=filtro_tipo_movimentacao if filtro_tipo_movimentacao else None
    )
    
    
    estrutura_plano = PlanoContaModel.obter_estrutura_plana_hierarquica()
    centros_custo = CentroCustoModel.obter_centro_custos_ativos()
    # Carregar dados para os selects
    pessoas_financeiro = PessoaFinanceiroModel.listar_pessoas_ativas()
    # Processar documentos formatados para cada pessoa
    for p in pessoas_financeiro:
        if p.numero_documento and len(p.numero_documento.strip()) > 0:
            p.documento_formatado = ValidaDocs.insere_pontuacao_cnpj(p.numero_documento) if len(p.numero_documento) == 14 else ValidaDocs.insere_pontuacao_cpf(p.numero_documento)
        else:
            p.documento_formatado = "N/A"
    
    # Buscar sugestões para cada transação
    sugestoes_por_transacao = {}
    for transacao in transacoes:
        if not transacao.conciliado:  # Apenas para transações não conciliadas
            valor_transacao = int(abs(transacao.valor * 100))  # Converter para centavos
            eh_credito = transacao.valor > 0
            
            # Buscar sugestões formatadas usando o método do model
            sugestoes_formatadas = AgendamentoPagamentoModel.obter_sugestoes_conciliacao_formatadas(
                valor_transacao=valor_transacao,
                eh_credito=eh_credito,
            )
                        
            sugestoes_por_transacao[transacao.id] = sugestoes_formatadas
    
    # Buscar agendamentos recentes para cada transação (últimos 30 registros por tipo)
    agendamentos_por_transacao = {}
    for transacao in transacoes:
        if not transacao.conciliado:  # Apenas para transações não conciliadas
            eh_credito = transacao.valor > 0
            
            # Buscar agendamentos recentes do mesmo tipo (receitas ou despesas)
            agendamentos_formatados = AgendamentoPagamentoModel.obter_agendamentos_recentes_formatados(eh_credito)
                        
            agendamentos_por_transacao[transacao.id] = agendamentos_formatados
    
    # Dados para o template
    transacao_mais_recente = transacoes[0] if transacoes else None
    
    return render_template("financeiro/contas_bancarias/conciliacao_bancaria.html",
        transacoes=transacoes,
        total_transacoes=total_transacoes,
        pagina=pagina,
        total_paginas=total_paginas,
        por_pagina=por_pagina,
        batch_id=batch_id,
        filtro_conciliado=filtro_conciliado,
        filtro_fitid=filtro_fitid,
        filtro_valor=filtro_valor,
        filtro_descricao=filtro_descricao,
        filtro_tipo_movimentacao=filtro_tipo_movimentacao,
        filtro_data_inicio=filtro_data_inicio,
        filtro_data_fim=filtro_data_fim,
        pessoas_financeiro=pessoas_financeiro,
        centros_custo=centros_custo,
        resumo=resumo_bd or {},
        arquivo_nome=resumo_bd.get('arquivo_nome', '') if resumo_bd else '',
        data_importacao=_formatar_data_importacao(resumo_bd),
        estatisticas={
            'total_creditos': resumo_bd.get('total_creditos', 0) if resumo_bd else 0,
            'total_debitos': resumo_bd.get('total_debitos', 0) if resumo_bd else 0,
            'saldo_liquido': resumo_bd.get('saldo_liquido', 0) if resumo_bd else 0,
            'creditos_formatado': resumo_bd.get('creditos_formatado', 'R$ 0,00') if resumo_bd else 'R$ 0,00',
            'debitos_formatado': resumo_bd.get('debitos_formatado', 'R$ 0,00') if resumo_bd else 'R$ 0,00',
            'saldo_formatado': resumo_bd.get('saldo_formatado', 'R$ 0,00') if resumo_bd else 'R$ 0,00'
        },
        conta_info={
            'bank_id': getattr(transacao_mais_recente, 'banco_id', '') if transacao_mais_recente else '',
            'branch_id': '',
            'account_id': getattr(transacao_mais_recente, 'conta_id', '') if transacao_mais_recente else ''
        },
        instituicao_info={
            'organization': getattr(transacao_mais_recente, 'instituicao_org', '') if transacao_mais_recente else '',
            'nome': getattr(transacao_mais_recente, 'instituicao_org', '') if transacao_mais_recente else ''
        },
        periodo_info={
            'data_inicio': getattr(transacao_mais_recente, 'data_inicio_extrato', None) if transacao_mais_recente else None,
            'data_fim': getattr(transacao_mais_recente, 'data_fim_extrato', None) if transacao_mais_recente else None,
            'primeira_transacao': getattr(transacao_mais_recente, 'data_inicio_extrato', None) if transacao_mais_recente else None,
            'ultima_transacao': getattr(transacao_mais_recente, 'data_fim_extrato', None) if transacao_mais_recente else None
        },
        estrutura_plano=estrutura_plano,
        sugestoes_por_transacao=sugestoes_por_transacao,
        agendamentos_por_transacao=agendamentos_por_transacao
    )

def _formatar_data_importacao(resumo_bd):
    """Formatar data de importação do resumo"""
    if not resumo_bd or not resumo_bd.get('data_importacao'):
        return ''
    
    try:
        dt = datetime.fromisoformat(resumo_bd['data_importacao'])
        return dt.strftime('%d/%m/%Y às %H:%M')
    except:
        return resumo_bd.get('data_importacao', '')

@app.route("/api/sugestoes-conciliacao", methods=["POST"])
@login_required
@requires_roles
def obter_sugestoes_conciliacao():
    """
    Endpoint AJAX para buscar sugestões de agendamentos para conciliação bancária
    """
    try:
        data = request.get_json()
        # Dados da transação OFX
        transacao_id = data.get('transacao_id')
        valor_transacao = int(data.get('valor', 0))
        eh_credito = data.get('is_credit', False) == 'true'
                
        # Buscar sugestões usando o método do model
        sugestoes = AgendamentoPagamentoModel.buscar_sugestoes_conciliacao(
            valor_transacao=valor_transacao,
            eh_credito=eh_credito
        )
        
        # Formatar as sugestões para o frontend
        sugestoes_formatadas = []
        for agendamento in sugestoes:
            # Determinar origem (faturamento ou lançamento avulso)
            origem = 'Faturamento'
            origem_id = agendamento.faturamento_id
            if agendamento.lancamento_avulso_id:
                origem = 'Lançamento Avulso'
                origem_id = agendamento.lancamento_avulso_id
            
            # Formattar valor
            valor_formatado = ValoresMonetarios.converter_float_brl_positivo(agendamento.valor_total_100 / 100)
            
            # Informações da pessoa/fornecedor
            pessoa_nome = agendamento.pessoa_financeiro.identificacao if agendamento.pessoa_financeiro else 'N/A'
            
            # Categorias (do JSON)
            categorias_nomes = []
            if agendamento.categorias_json:
                try:
                    # Se for string, fazer parse do JSON
                    if isinstance(agendamento.categorias_json, str):
                        categorias_data = json.loads(agendamento.categorias_json)
                    else:
                        categorias_data = agendamento.categorias_json
                    
                    # Processar as categorias
                    if isinstance(categorias_data, list):
                        for cat in categorias_data:
                            if isinstance(cat, dict):
                                categorias_nomes.append(cat.get('categoria', 'Categoria não identificada'))
                            else:
                                categorias_nomes.append(str(cat))
                    else:
                        categorias_nomes.append('Categoria não identificada')
                        
                except (json.JSONDecodeError, TypeError, AttributeError) as e:
                    categorias_nomes.append('Categoria não identificada')
            
            sugestao = {
                'id': agendamento.id,
                'valor_formatado': valor_formatado,
                'valor_centavos': agendamento.valor_total_100,
                'data_vencimento': agendamento.data_vencimento.strftime('%d/%m/%Y') if agendamento.data_vencimento else 'N/A',
                'descricao': agendamento.descricao or agendamento.referencia or 'Sem descrição',
                'pessoa_nome': pessoa_nome,
                'origem': origem,
                'faturamento_codigo': agendamento.faturamento.codigo_faturamento if agendamento.faturamento else '',
                'origem_id': origem_id,
                'categorias': categorias_nomes,
                'diferenca_dias': 0  # Calcular diferença de dias se necessário
            }
            sugestoes_formatadas.append(sugestao)
        
        return jsonify({
            'success': True,
            'sugestoes': sugestoes_formatadas,
            'total': len(sugestoes_formatadas)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'sugestoes': [],
            'total': 0
        }), 500


@app.route("/api/buscar-agendamentos", methods=["POST"])
@login_required
@requires_roles
def buscar_agendamentos_para_conciliacao():
    """
    Endpoint AJAX para buscar agendamentos com filtros (últimos 7 dias)
    """
    try:
        from datetime import datetime, timedelta
        from sistema._utilitarios.valores_monetarios import ValoresMonetarios
        
        data = request.get_json()
        
        # Dados da transação OFX
        eh_credito = data.get('is_credit', False) == 'true'
        
        
        # Filtros de busca
        valor_min = data.get('valor_min')
        valor_max = data.get('valor_max')
        data_inicio = data.get('data_inicio')
        data_fim = data.get('data_fim')
        categoria_id = data.get('categoria')  # ID da categoria selecionada
        beneficiario_id = data.get('beneficiario_id')  # ID do beneficiário selecionado
        
        # Converter valores para float se não estiverem vazios
        try:
            valor_min = float(valor_min) if valor_min and valor_min != '' else None
        except (ValueError, TypeError):
            valor_min = None
            
        try:
            valor_max = float(valor_max) if valor_max and valor_max != '' else None
        except (ValueError, TypeError):
            valor_max = None
    
        
        # Buscar agendamentos com filtros
        agendamentos = AgendamentoPagamentoModel.buscar_agendamentos_com_filtros(
            eh_credito=eh_credito,
            valor_min=valor_min,
            valor_max=valor_max,
            data_inicio=data_inicio,
            data_fim=data_fim,
            categoria_id=categoria_id,
            beneficiario_id=beneficiario_id
        )
        
        # Formatar as sugestões (mesmo formato do endpoint de sugestões)
        sugestoes_formatadas = []
        for agendamento in agendamentos:
            # Determinar origem (faturamento ou lançamento avulso)
            origem = 'Faturamento'
            origem_id = agendamento.faturamento_id
            if agendamento.lancamento_avulso_id:
                origem = 'Lançamento Avulso'
                origem_id = agendamento.lancamento_avulso_id
            
            # Formattar valor
            valor_formatado = ValoresMonetarios.converter_float_brl_positivo(agendamento.valor_total_100 / 100)
            
            # Informações da pessoa/fornecedor
            pessoa_nome = agendamento.pessoa_financeiro.identificacao if agendamento.pessoa_financeiro else 'N/A'
            
            # Categorias (do JSON)
            categorias_nomes = []
            if agendamento.categorias_json:
                try:
                    # Se for string, fazer parse do JSON
                    if isinstance(agendamento.categorias_json, str):
                        categorias_data = json.loads(agendamento.categorias_json)
                    else:
                        categorias_data = agendamento.categorias_json
                    
                    # Processar as categorias
                    if isinstance(categorias_data, list):
                        for cat in categorias_data:
                            if isinstance(cat, dict):
                                categorias_nomes.append(cat.get('categoria', 'Categoria não identificada'))
                            else:
                                categorias_nomes.append(str(cat))
                    else:
                        categorias_nomes.append('Categoria não identificada')
                        
                except (json.JSONDecodeError, TypeError, AttributeError) as e:
                    print(f"[WARNING] Erro ao processar categorias_json: {str(e)}")
                    categorias_nomes.append('Categoria não identificada')
            
            sugestao = {
                'id': agendamento.id,
                'valor_formatado': valor_formatado,
                'valor_centavos': agendamento.valor_total_100,
                'data_vencimento': agendamento.data_vencimento.strftime('%d/%m/%Y') if agendamento.data_vencimento else 'N/A',
                'descricao': agendamento.descricao or agendamento.referencia or 'Sem descrição',
                'pessoa_nome': pessoa_nome,
                'origem': origem,
                'faturamento_codigo': agendamento.faturamento.codigo_faturamento if agendamento.faturamento else '',
                'origem_id': origem_id,
                'categorias': categorias_nomes,
                'diferenca_dias': 0  # Calcular diferença de dias se necessário
            }
            sugestoes_formatadas.append(sugestao)
        
        return jsonify({
            'success': True,
            'agendamentos': sugestoes_formatadas,
            'total': len(sugestoes_formatadas),
            'periodo': {
                'data_inicio': data_inicio,
                'data_fim': data_fim
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'agendamentos': [],
            'total': 0
        }), 500


@app.route("/api/processar-conciliacao-massa", methods=["POST"])
@login_required
@requires_roles
def processar_conciliacao_massa():
    """
    Endpoint para processar conciliação em massa entre uma transação OFX e múltiplos agendamentos
    """
    try:
        data = request.get_json()
        
        # Dados recebidos do frontend
        transacao_id = data.get('transacao_id')
        agendamentos_ids = data.get('agendamentos_ids', [])  # Lista de IDs dos agendamentos
        observacoes = data.get('observacoes', '')
        
        if not transacao_id or not agendamentos_ids:
            return jsonify({
                'success': False,
                'message': 'Dados obrigatórios não fornecidos'
            }), 400
        
        # Buscar a transação OFX
        from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx
        transacao = ImportacaoOfx.query.get(transacao_id)
        if not transacao:
            return jsonify({
                'success': False,
                'message': 'Transação não encontrada'
            }), 404
        
        # Validar se transação já foi conciliada
        if transacao.conciliado:
            return jsonify({
                'success': False,
                'message': 'Esta transação já foi conciliada'
            }), 400
        
        # Buscar todos os agendamentos
        agendamentos = AgendamentoPagamentoModel.query.filter(
            AgendamentoPagamentoModel.id.in_(agendamentos_ids)
        ).all()
        
        if len(agendamentos) != len(agendamentos_ids):
            return jsonify({
                'success': False,
                'message': 'Alguns agendamentos não foram encontrados'
            }), 404
        
        # Validar se algum agendamento já foi conciliado
        agendamentos_conciliados = [ag for ag in agendamentos if ag.situacao_pagamento_id == 8]
        if agendamentos_conciliados:
            codigos_conciliados = [str(ag.id) for ag in agendamentos_conciliados]
            return jsonify({
                'success': False,
                'message': f'Os seguintes agendamentos já foram conciliados: {", ".join(codigos_conciliados)}'
            }), 400
        
        # Calcular valor total dos agendamentos selecionados
        valor_total_agendamentos = sum(ag.valor_total_100 for ag in agendamentos)
        valor_transacao_centavos = int(abs(transacao.valor * 100))
        
        # Validar se a soma dos valores não ultrapassa a transação
        if valor_total_agendamentos > valor_transacao_centavos:
            diferenca_total = valor_total_agendamentos - valor_transacao_centavos
            return jsonify({
                'success': False,
                'message': f'A soma dos agendamentos selecionados (R$ {valor_total_agendamentos/100:.2f}) é superior ao valor da transação (R$ {valor_transacao_centavos/100:.2f}). Diferença: R$ {diferenca_total/100:.2f}. Não é possível conciliar valores superiores ao valor da transação.'
            }), 400
        
        # Determinar tipo de movimentação (1=Entrada, 2=Saída)
        tipo_movimentacao = 1 if transacao.valor > 0 else 2
        
        # Processar cada agendamento
        from datetime import datetime
        faturamentos_conciliados = []
        lancamentos_conciliados = []
        movimentacoes_criadas = []
        
        for agendamento in agendamentos:
            # Determinar tipo de origem e IDs
            tipo_origem = None
            faturamento_id = None
            lancamento_avulso_id = None
            
            if agendamento.faturamento_id:
                tipo_origem = 'FATURAMENTO'
                faturamento_id = agendamento.faturamento_id
                if faturamento_id not in faturamentos_conciliados:
                    faturamentos_conciliados.append(faturamento_id)
            elif agendamento.lancamento_avulso_id:
                tipo_origem = 'LANCAMENTO_AVULSO'
                lancamento_avulso_id = agendamento.lancamento_avulso_id
                if lancamento_avulso_id not in lancamentos_conciliados:
                    lancamentos_conciliados.append(lancamento_avulso_id)
            
            # Calcular diferença de valor (positiva se agendamentos menor que transação)
            diferenca_total = valor_transacao_centavos - valor_total_agendamentos
            valor_diferenca_proporcional = int((agendamento.valor_total_100 / valor_total_agendamentos) * diferenca_total) if diferenca_total > 0 else 0
            
            # Criar a movimentação financeira com todos os campos de auditoria
            nova_movimentacao = MovimentacaoFinanceiraModel(
                tipo_movimentacao=tipo_movimentacao,
                usuario_id=current_user.id,
                data_movimentacao=transacao.data_transacao,
                conta_bancaria_id=agendamento.conta_bancaria_id,
                valor_movimentacao_100=agendamento.valor_total_100,
                ativo=True,
                conciliacao_bancaria=True,
                
                # Campos de auditoria da conciliação
                importacao_ofx_id=transacao_id,
                agendamento_id=agendamento.id,
                
                # Dados originais da transação OFX
                conciliacao_fitid=transacao.fitid,
                conciliacao_valor_original=valor_transacao_centavos,
                conciliacao_descricao_ofx=transacao.memo or transacao.descricao_limpa,
                conciliacao_data_transacao=transacao.data_transacao,
                conciliacao_tipo_movimento=transacao.tipo_movimento,
                
                # Auditoria da conciliação
                conciliacao_data_processamento=datetime.now(),
                conciliacao_observacoes=f'CONCILIAÇÃO EM MASSA: {observacoes}' if observacoes else 'CONCILIAÇÃO EM MASSA',
                
                # Referências de origem
                conciliacao_faturamento_id=faturamento_id,
                conciliacao_lancamento_avulso_id=lancamento_avulso_id,
                conciliacao_tipo_origem=tipo_origem,
                
                # Controle de diferenças
                conciliacao_valor_diferenca=valor_diferenca_proporcional
            )
            
            db.session.add(nova_movimentacao)
            movimentacoes_criadas.append(nova_movimentacao)
            
            # Marcar agendamento como conciliado (situacao_pagamento_id = 8)
            agendamento.situacao_pagamento_id = 8
            db.session.add(agendamento)
            
            
            acao = TipoAcaoEnum.CADASTRO
            PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                current_user.id,
                acao,
                acao.pontos,
                modulo='conciliacao_bancaria'
            )
        
        # Marcar faturamentos como conciliados
        for faturamento_id in faturamentos_conciliados:
            faturamento = FaturamentoModel.query.get(faturamento_id)
            if faturamento:
                faturamento.situacao_pagamento_id = 8
                db.session.add(faturamento)
        
        # Marcar lançamentos avulsos como conciliados
        for lancamento_id in lancamentos_conciliados:
            lancamento_avulso = LancamentoAvulsoModel.query.get(lancamento_id)
            if lancamento_avulso:
                lancamento_avulso.situacao_pagamento_id = 8
                db.session.add(lancamento_avulso)
        
        # Marcar transação OFX como conciliada e salvar dados para reversão
        movimentacoes_ids = []
        
        # Commit primeiro para obter os IDs das novas movimentações
        db.session.flush()
        for mov in movimentacoes_criadas:
            if mov.id:
                movimentacoes_ids.append(mov.id)
        
        # Salvar dados da conciliação no formato JSON
        sucesso_salvamento = transacao.salvar_dados_conciliacao(
            tipo_conciliacao='AGENDAMENTO_MASSA',
            agendamentos_ids=agendamentos_ids,
            faturamentos_ids=faturamentos_conciliados,
            movimentacoes_ids=movimentacoes_ids,
            lancamentos_avulsos_ids=lancamentos_conciliados,
            valor_agendamento=valor_total_agendamentos,
            usuario_id=current_user.id,
            observacoes=observacoes
        )
        
        if not sucesso_salvamento:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Erro ao salvar dados de conciliação para reversão'
            }), 500
        
        # Observações detalhadas da conciliação
        obs_conciliacao = f'Conciliação em massa com {len(agendamentos)} agendamento(s)'
        
        if faturamentos_conciliados:
            codigos_faturamentos = []
            for fat_id in faturamentos_conciliados:
                faturamento = FaturamentoModel.query.get(fat_id)
                if faturamento:
                    codigos_faturamentos.append(faturamento.codigo_faturamento)
            if codigos_faturamentos:
                obs_conciliacao += f' | Faturamentos: {", ".join(codigos_faturamentos)}'
        
        if lancamentos_conciliados:
            obs_conciliacao += f' | Lançamentos Avulsos: {len(lancamentos_conciliados)} itens'
        
            
        transacao.observacoes_conciliacao = obs_conciliacao
        db.session.add(transacao)
        
        # Atualizar saldo da conta bancária (usar a primeira movimentação como referência)
        if movimentacoes_criadas:
            primeira_movimentacao = movimentacoes_criadas[0]
            conta_bancaria_id = primeira_movimentacao.conta_bancaria_id
            
            from sistema.models_views.financeiro.movimentacao_financeira.saldo_movimentacao_financeira_model import SaldoMovimentacaoFinanceiraModel
            
            # Buscar o registro de saldo da conta
            saldo_conta = SaldoMovimentacaoFinanceiraModel.query.filter(
                SaldoMovimentacaoFinanceiraModel.conta_bancaria_id == conta_bancaria_id,
                SaldoMovimentacaoFinanceiraModel.ativo == True,
                SaldoMovimentacaoFinanceiraModel.deletado == False
            ).first()
            
            # Se não existir registro de saldo, criar um
            if not saldo_conta:
                saldo_conta = SaldoMovimentacaoFinanceiraModel(
                    data_movimentacao=transacao.data_transacao,
                    valor_total_saldo_100=0,
                    conta_bancaria_id=conta_bancaria_id,
                    ativo=True
                )
                db.session.add(saldo_conta)
            
            # Atualizar o saldo baseado no tipo de movimentação (usar valor total dos agendamentos)
            if tipo_movimentacao == 1:  # Entrada/Crédito - AUMENTA o saldo
                saldo_conta.valor_total_saldo_100 += valor_total_agendamentos
            elif tipo_movimentacao == 2:  # Saída/Débito - DIMINUI o saldo
                saldo_conta.valor_total_saldo_100 -= valor_total_agendamentos
            
            # Atualizar a data da última movimentação do saldo
            saldo_conta.data_movimentacao = DataHora.obter_data_atual_padrao_en()
            db.session.add(saldo_conta)
        
        db.session.commit()
        
        # Preparar mensagem de sucesso detalhada
        mensagem_sucesso = f'Conciliação em massa processada com sucesso! {len(agendamentos)} agendamentos conciliados.'
        
        if faturamentos_conciliados:
            mensagem_sucesso += f' {len(faturamentos_conciliados)} faturamentos marcados como conciliados.'
        
        if lancamentos_conciliados:
            mensagem_sucesso += f' {len(lancamentos_conciliados)} lançamentos avulsos marcados como conciliados.'
      
        return jsonify({
            'success': True,
            'message': mensagem_sucesso,
            'dados': {
                'agendamentos_conciliados': len(agendamentos),
                'faturamentos_conciliados': len(faturamentos_conciliados),
                'lancamentos_conciliados': len(lancamentos_conciliados),
                'valor_total_agendamentos': valor_total_agendamentos,
                'valor_transacao': valor_transacao_centavos,
                'diferenca_total': diferenca_total
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao processar conciliação em massa: {str(e)}'
        }), 500


@app.route("/api/processar-conciliacao", methods=["POST"])
@login_required
@requires_roles
def processar_conciliacao():
    """
    Endpoint para processar a conciliação entre uma transação OFX e um agendamento
    """
    try:
        data = request.get_json()
        
        # Dados recebidos do frontend
        transacao_id = data.get('transacao_id')
        agendamento_id = data.get('agendamento_id')
        observacoes = data.get('observacoes', '')

        
        if not transacao_id or not agendamento_id:
            return jsonify({
                'success': False,
                'message': 'Dados obrigatórios não fornecidos'
            }), 400
        
        # Buscar a transação OFX
        from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx
        transacao = ImportacaoOfx.query.get(transacao_id)
        if not transacao:
            return jsonify({
                'success': False,
                'message': 'Transação não encontrada'
            }), 404
        
        # Buscar o agendamento
        agendamento = AgendamentoPagamentoModel.query.get(agendamento_id)
        if not agendamento:
            return jsonify({
                'success': False,
                'message': 'Agendamento não encontrado'
            }), 404
        
        # Validar se transação já foi conciliada
        if transacao.conciliado:
            return jsonify({
                'success': False,
                'message': 'Esta transação já foi conciliada'
            }), 400
        
        # Validar se agendamento já foi conciliado
        if agendamento.situacao_pagamento_id == 8:
            return jsonify({
                'success': False,
                'message': 'Este agendamento já foi conciliado'
            }), 400
        # Determinar tipo de movimentação (1=Entrada, 2=Saída)
        tipo_movimentacao = 1 if transacao.valor > 0 else 2
        
        # Determinar tipo de origem e IDs
        tipo_origem = None
        faturamento_id = None
        lancamento_avulso_id = None
        
        if agendamento.faturamento_id:
            tipo_origem = 'FATURAMENTO'
            faturamento_id = agendamento.faturamento_id
        elif agendamento.lancamento_avulso_id:
            tipo_origem = 'LANCAMENTO_AVULSO'
            lancamento_avulso_id = agendamento.lancamento_avulso_id
        
        # Calcular diferença de valor entre OFX e agendamento
        valor_diferenca = abs(transacao.valor) - agendamento.valor_total_100
        
        # Criar a movimentação financeira com todos os campos de auditoria
        from datetime import datetime
        nova_movimentacao = MovimentacaoFinanceiraModel(
            tipo_movimentacao=tipo_movimentacao,
            usuario_id=current_user.id,
            data_movimentacao=transacao.data_transacao,
            conta_bancaria_id=agendamento.conta_bancaria_id,  # Usa a conta do agendamento
            valor_movimentacao_100=agendamento.valor_total_100,  # Usa o valor do agendamento/categoria
            ativo=True,
            conciliacao_bancaria=True,
            
            # Campos de auditoria da conciliação
            importacao_ofx_id=transacao_id,
            agendamento_id=agendamento_id,
            
            # Dados originais da transação OFX
            conciliacao_fitid=transacao.fitid,
            conciliacao_valor_original=int(abs(transacao.valor * 100)),
            conciliacao_descricao_ofx=transacao.memo or transacao.descricao_limpa,
            conciliacao_data_transacao=transacao.data_transacao,
            conciliacao_tipo_movimento=transacao.tipo_movimento,
            
            # Auditoria da conciliação
            conciliacao_data_processamento=datetime.now(),
            conciliacao_observacoes=observacoes,
            
            # Referências de origem
            conciliacao_faturamento_id=faturamento_id,
            conciliacao_lancamento_avulso_id=lancamento_avulso_id,
            conciliacao_tipo_origem=tipo_origem,
            
            # Controle de diferenças
            conciliacao_valor_diferenca=valor_diferenca
        )
        
        db.session.add(nova_movimentacao)
        
        # Marcar agendamento como conciliado (situacao_pagamento_id = 8)
        agendamento.situacao_pagamento_id = 8
        db.session.add(agendamento)
        
        # Se o agendamento é de um faturamento, marcar o faturamento como conciliado também
        if faturamento_id:
            faturamento = FaturamentoModel.query.get(faturamento_id)
            if faturamento:
                # Marcar faturamento como conciliado (situacao_pagamento_id = 8)
                faturamento.situacao_pagamento_id = 8
                db.session.add(faturamento)
        
        # Se o agendamento é de um lançamento avulso, marcar o lançamento como conciliado também
        if lancamento_avulso_id:
            lancamento_avulso = LancamentoAvulsoModel.query.get(lancamento_avulso_id)
            if lancamento_avulso:
                # Marcar lançamento avulso como conciliado (situacao_pagamento_id = 8)
                lancamento_avulso.situacao_pagamento_id = 8
                db.session.add(lancamento_avulso)
        
        # Marcar transação OFX como conciliada e salvar dados para reversão
        faturamentos_ids = []
        movimentacoes_ids = []
        
        if faturamento_id:
            faturamentos_ids.append(faturamento_id)
        
        # Commit primeiro para obter o ID da nova movimentação
        db.session.flush()
        if nova_movimentacao.id:
            movimentacoes_ids.append(nova_movimentacao.id)
        
        # Salvar dados da conciliação no formato JSON
        lancamentos_avulsos_ids = []
        if lancamento_avulso_id:
            lancamentos_avulsos_ids.append(lancamento_avulso_id)
        
        sucesso_salvamento = transacao.salvar_dados_conciliacao(
            tipo_conciliacao='AGENDAMENTO',
            agendamentos_ids=[agendamento_id],
            faturamentos_ids=faturamentos_ids,
            movimentacoes_ids=movimentacoes_ids,
            lancamentos_avulsos_ids=lancamentos_avulsos_ids,
            valor_agendamento=agendamento.valor_total_100,
            usuario_id=current_user.id,
            observacoes=observacoes
        )
        
        if not sucesso_salvamento:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Erro ao salvar dados de conciliação para reversão'
            }), 500
        
        # Adicionar campos específicos para compatibilidade
        transacao.pagamento_id = agendamento_id
        
        # Observações detalhadas da conciliação
        obs_conciliacao = f'Conciliado com agendamento'
        if tipo_origem == 'FATURAMENTO':
            obs_conciliacao += f' | Faturamento: {agendamento.faturamento.codigo_faturamento if agendamento.faturamento else "N/A"}'
        elif tipo_origem == 'LANCAMENTO_AVULSO':
            obs_conciliacao += f' | Lançamento Avulso: {agendamento.lancamento_avulso.descricao if agendamento.lancamento_avulso else "N/A"}'
            
        transacao.observacoes_conciliacao = obs_conciliacao
        db.session.add(transacao)
        
        # Atualizar saldo da conta bancária
        from sistema.models_views.financeiro.movimentacao_financeira.saldo_movimentacao_financeira_model import SaldoMovimentacaoFinanceiraModel
        
        # Buscar o registro de saldo da conta
        saldo_conta = SaldoMovimentacaoFinanceiraModel.query.filter(
            SaldoMovimentacaoFinanceiraModel.conta_bancaria_id == agendamento.conta_bancaria_id,
            SaldoMovimentacaoFinanceiraModel.ativo == True,
            SaldoMovimentacaoFinanceiraModel.deletado == False
        ).first()
        
        # Se não existir registro de saldo, criar um
        if not saldo_conta:
            saldo_conta = SaldoMovimentacaoFinanceiraModel(
                data_movimentacao=transacao.data_transacao,
                valor_total_saldo_100=0,
                conta_bancaria_id=agendamento.conta_bancaria_id,
                ativo=True
            )
            db.session.add(saldo_conta)
        
        # Atualizar o saldo baseado no tipo de movimentação
        if tipo_movimentacao == 1:  # Entrada/Crédito - AUMENTA o saldo
            saldo_conta.valor_total_saldo_100 += agendamento.valor_total_100
        elif tipo_movimentacao == 2:  # Saída/Débito - DIMINUI o saldo
            saldo_conta.valor_total_saldo_100 -= agendamento.valor_total_100
        
        # Atualizar a data da última movimentação do saldo
        saldo_conta.data_movimentacao = DataHora.obter_data_atual_padrao_en()
        db.session.add(saldo_conta)
        
        db.session.commit()
        
        
        acao = TipoAcaoEnum.CADASTRO
        PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
            current_user.id,
            acao,
            acao.pontos,
            modulo='conciliacao_bancaria'
        )
        
        # Preparar mensagem de sucesso detalhada
        mensagem_sucesso = f'Conciliação processada com sucesso! Agendamento {agendamento_id} conciliado.'
        
        if faturamento_id:
            codigo_faturamento = agendamento.faturamento.codigo_faturamento if agendamento.faturamento else faturamento_id
            mensagem_sucesso += f' Faturamento {codigo_faturamento} também marcado como conciliado.'
        
        if lancamento_avulso_id:
            descricao_lancamento = agendamento.lancamento_avulso.descricao if agendamento.lancamento_avulso else f'ID {lancamento_avulso_id}'
            mensagem_sucesso += f' Lançamento avulso "{descricao_lancamento}" também marcado como conciliado.'
      
        return jsonify({
            'success': True,
            'message': mensagem_sucesso,
            'dados': {
                'agendamento_id': agendamento_id,
                'faturamento_id': faturamento_id,
                'lancamento_avulso_id': lancamento_avulso_id,
                'tipo_origem': tipo_origem,
                'valor_diferenca': valor_diferenca
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao processar conciliação: {str(e)}'
        }), 500


@app.route("/api/salvar-nova-movimentacao", methods=["POST"])
@login_required
@requires_roles
def salvar_nova_movimentacao():
    """
    Endpoint para salvar uma nova movimentação criada a partir da conciliação bancária
    """
    try:
        data = request.get_json()
        
        # ===== EXTRAÇÃO DOS DADOS =====
        transacao_id = data.get('transacao_id')
        valor_str = data.get('valor', '').replace('R$ ', '').replace('.', '').replace(',', '.')
        descricao = data.get('descricao', '').strip()
        data_vencimento = data.get('data_vencimento')
        data_competencia = data.get('data_competencia')
        conta_bancaria_id = data.get('conta_bancaria_id')
        pessoa_financeiro_id = data.get('pessoa_financeiro_id')
        referencia = data.get('referencia', '').strip()
        categorias_json = data.get('categorias_json')
        centros_custo_json = data.get('centros_custo_json')
        valores_detalhados_ativo = data.get('valores_detalhados_ativo', False)
        parcelamento_ativo = data.get('parcelamento_ativo', False)
        numero_parcelas = data.get('numero_parcelas')
        dias_entre_parcelas = data.get('dias_entre_parcelas', 30)
        parcelas_json = data.get('parcelas_json')
        
        # ===== VALIDAÇÕES =====
        validacao_campos_obrigatorios = {}
        validacao_campos_erros = {}
        gravar_banco = True
        
        print(data_competencia, 'data compe')
        
        # Estrutura de campos obrigatórios
        campos = {
            "descricao": ["Descrição da Movimentação", descricao],
            "valor": ["Valor", valor_str],
            "data_vencimento": ["Data de Vencimento", data_vencimento],
            "pessoa_financeiro_id": ["Beneficiário", pessoa_financeiro_id],
            "conta_bancaria_id": ["Conta Bancária", conta_bancaria_id],
            "categorias_json": ["Categorias", categorias_json]
        }
        
        # Validação de campos obrigatórios
        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
        
        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
        
        # Validações específicas de formato e regras de negócio
        
        # Validar formato do valor
        if valor_str:
            try:
                valor_decimal = float(valor_str)
                valor_centavos = int(valor_decimal * 100)
                if valor_centavos <= 0:
                    gravar_banco = False
                    validacao_campos_erros['valor'] = 'Valor deve ser maior que zero!'
            except (ValueError, TypeError):
                gravar_banco = False
                validacao_campos_erros['valor'] = 'Valor inválido!'
        
        # Validar formato da data de vencimento
        if data_vencimento:
            try:
                data_vencimento_obj = datetime.strptime(data_vencimento, '%Y-%m-%d').date()
            except ValueError:
                gravar_banco = False
                validacao_campos_erros['data_vencimento'] = 'Data de vencimento inválida!'
        
        data_competencia_obj = None
        if data_competencia:
            try:
                data_competencia_obj = datetime.strptime(f"01/{data_competencia}", '%d/%m/%Y').date()
            except ValueError:
                validacao_campos_erros['data_competencia'] = 'Competência inválida'
        
        # Validar se pessoa financeiro existe
        if pessoa_financeiro_id:
            try:
                pessoa_id = int(pessoa_financeiro_id)
                pessoa = PessoaFinanceiroModel.obter_pessoa_por_id(pessoa_id)
                if not pessoa:
                    gravar_banco = False
                    validacao_campos_erros['pessoa_financeiro_id'] = 'Beneficiário não encontrado!'
            except ValueError:
                gravar_banco = False
                validacao_campos_erros['pessoa_financeiro_id'] = 'Beneficiário inválido!'
        
        # Validar se conta bancária existe
        if conta_bancaria_id:
            try:
                conta_id = int(conta_bancaria_id)
                conta = ContaBancariaModel.obter_conta_por_id(conta_id)
                if not conta:
                    gravar_banco = False
                    validacao_campos_erros['conta_bancaria_id'] = 'Conta bancária não encontrada!'
            except ValueError:
                gravar_banco = False
                validacao_campos_erros['conta_bancaria_id'] = 'Conta bancária inválida!'
        
        # Validar estrutura e dados das categorias
        if categorias_json:
            try:
                categorias = json.loads(categorias_json)
                if not isinstance(categorias, list) or len(categorias) == 0:
                    gravar_banco = False
                    validacao_campos_erros['categorias_json'] = 'Pelo menos uma categoria deve ser informada!'
                else:
                    categorias_usadas = set()
                    total_categorias = 0
                    for i, categoria in enumerate(categorias, 1):
                        if not categoria.get('categoria'):
                            gravar_banco = False
                            validacao_campos_erros['categorias_json'] = f'Categoria {i} deve ser selecionada!'
                            break
                        if not categoria.get('valor') or categoria.get('valor') <= 0:
                            gravar_banco = False
                            validacao_campos_erros['categorias_json'] = f'Valor da categoria {i} deve ser maior que zero!'
                            break
                        # Verificar duplicatas
                        categoria_id = categoria.get('categoria')
                        if categoria_id in categorias_usadas:
                            gravar_banco = False
                            validacao_campos_erros['categorias_json'] = 'A categoria não pode ser repetida!'
                            break
                        categorias_usadas.add(categoria_id)
                        total_categorias += categoria.get('valor', 0)
                    
                    # Validar se o total das categorias bate com o valor total
                    if gravar_banco and 'categorias_json' not in validacao_campos_erros and abs(total_categorias - valor_centavos) > 1:
                        gravar_banco = False
                        validacao_campos_erros['categorias_json'] = 'O valor total das categorias deve ser igual ao valor da movimentação!'
            except json.JSONDecodeError:
                gravar_banco = False
                validacao_campos_erros['categorias_json'] = 'Formato de categorias inválido!'
        
        # Validar data de competência se informada
        if data_competencia:
            try:
                # Formato MM/AAAA
                datetime.strptime(data_competencia, '%m/%Y')
            except ValueError:
                validacao_campos_erros['data_competencia'] = 'Data de competência deve estar no formato MM/AAAA!'
        
        # Validar centros de custo se valores detalhados ativo
        if valores_detalhados_ativo:
            if not centros_custo_json:
                gravar_banco = False
                validacao_campos_erros['centros_custo_json'] = 'Pelo menos um centro de custo deve ser informado quando valores detalhados está ativo!'
            else:
                try:
                    centros_custo = json.loads(centros_custo_json)
                    if not isinstance(centros_custo, list) or len(centros_custo) == 0:
                        gravar_banco = False
                        validacao_campos_erros['centros_custo_json'] = 'Pelo menos um centro de custo deve ser informado!'
                    else:
                        for i, centro in enumerate(centros_custo, 1):
                            if not centro.get('centro'):
                                gravar_banco = False
                                validacao_campos_erros['centros_custo_json'] = f'Centro de custo {i} deve ser selecionado!'
                                break
                            if not centro.get('valor') and not centro.get('percentual'):
                                gravar_banco = False
                                validacao_campos_erros['centros_custo_json'] = f'Centro de custo {i} deve ter valor ou percentual informado!'
                                break
                except json.JSONDecodeError:
                    gravar_banco = False
                    validacao_campos_erros['centros_custo_json'] = 'Formato de centros de custo inválido!'
        
        # Validar parcelamento
        if parcelamento_ativo:
            if not numero_parcelas:
                gravar_banco = False
                validacao_campos_erros['numero_parcelas'] = 'Número de parcelas é obrigatório quando parcelamento está ativo!'
            else:
                try:
                    num_parcelas = int(numero_parcelas)
                    if num_parcelas < 2:
                        gravar_banco = False
                        validacao_campos_erros['numero_parcelas'] = 'Número de parcelas deve ser maior que 1!'
                except ValueError:
                    gravar_banco = False
                    validacao_campos_erros['numero_parcelas'] = 'Número de parcelas inválido!'
            
            # Validar dados das parcelas se parcelamento ativo
            if parcelas_json:
                try:
                    parcelas = json.loads(parcelas_json)
                    if not isinstance(parcelas, list) or len(parcelas) == 0:
                        gravar_banco = False
                        validacao_campos_erros['parcelas_json'] = 'Dados de parcelas são obrigatórios quando parcelamento está ativo!'
                    else:
                        for i, parcela in enumerate(parcelas, 1):
                            if not parcela.get('vencimento'):
                                gravar_banco = False
                                validacao_campos_erros['parcelas_json'] = f'Data de vencimento da parcela {i} é obrigatória!'
                                break
                            if not parcela.get('valor') or parcela.get('valor') <= 0:
                                gravar_banco = False
                                validacao_campos_erros['parcelas_json'] = f'Valor da parcela {i} deve ser maior que zero!'
                                break
                except json.JSONDecodeError:
                    gravar_banco = False
                    validacao_campos_erros['parcelas_json'] = 'Formato de parcelas inválido!'
            else:
                gravar_banco = False
                validacao_campos_erros['parcelas_json'] = 'Dados de parcelas são obrigatórios quando parcelamento está ativo!'
        
        # Se há erros de validação, retornar erro com estrutura padronizada
        if not gravar_banco:
            return jsonify({
                'success': False,
                'message': 'Verifique os campos destacados em vermelho!',
                'campos_obrigatorios': validacao_campos_obrigatorios,
                'campos_erros': validacao_campos_erros
            }), 400
        
        # ===== BUSCAR E VALIDAR TRANSAÇÃO OFX =====
        transacao = ImportacaoOfx.query.get(transacao_id) if transacao_id else None
        if not transacao:
            return jsonify({
                'success': False,
                'message': 'Transação OFX não encontrada!'
            }), 404
        
        # Verificar se transação já está conciliada
        if transacao.conciliado:
            return jsonify({
                'success': False,
                'message': 'Esta transação já está conciliada!'
            }), 400
        
        # ===== PROCESSAR CATEGORIAS =====
        categorias_processadas = categorias_json or '[]'
        if categorias_json:
            try:
                categorias = json.loads(categorias_json)
                categorias_enriquecidas = []
                
                for cat in categorias:
                    categoria_codigo = cat.get('categoria')  # Frontend envia o código aqui
                    categoria_nome = categoria_codigo
                    categoria_id = None
                    categoria_codigo_nome = categoria_codigo
                    
                    # Buscar informações completas da categoria pelo código
                    if categoria_codigo:
                        categoria_obj = PlanoContaModel.buscar_por_codigo(categoria_codigo)
                        if categoria_obj:
                            categoria_id = categoria_obj.id
                            categoria_nome = categoria_obj.nome
                            # Combinar código + nome para exibição (formato solicitado)
                            categoria_codigo_nome = f"{categoria_codigo} - {categoria_nome}"
                    
                    # Estrutura no formato solicitado: código+nome, categoria_id, valor, detalhamento, referencia
                    categoria_enriquecida = {
                        'categoria': categoria_codigo_nome,      # "2.01.03.01 - Frete terceiros"
                        'categoria_id': categoria_id,           # 46
                        'valor': cat.get('valor', 0),           # 401426
                        'detalhamento': cat.get('detalhamento', ''),  # ""
                        'referencia': cat.get('referencia', '')      # "" (mesmo que frontend não envie)
                    }
                    categorias_enriquecidas.append(categoria_enriquecida)
                
                categorias_processadas = json.dumps(categorias_enriquecidas)
                
            except (json.JSONDecodeError, ValueError):
                categorias_processadas = categorias_json or '[]'
        
        # ===== PROCESSAR CENTROS DE CUSTO =====
        centros_custo_processados = centros_custo_json or '[]'
        if valores_detalhados_ativo and centros_custo_json:
            try:
                centros_custo = json.loads(centros_custo_json)
                centros_custo_enriquecidos = []
                
                for cc in centros_custo:
                    centro_id = cc.get('centro')
                    centro_nome = centro_id
                    
                    # Se for ID numérico, buscar o nome do centro de custo
                    if str(centro_id).isdigit():
                        centro_custo_obj = CentroCustoModel.obter_centro_custo_por_id(int(centro_id))
                        if centro_custo_obj:
                            centro_nome = centro_custo_obj.nome
                    
                    # Manter estrutura original mas com nome enriquecido
                    centro_enriquecido = {
                        'centro': centro_id,
                        'centro_nome': centro_nome,
                        'percentual': cc.get('percentual', ''),
                        'valor': cc.get('valor', 0)
                    }
                    centros_custo_enriquecidos.append(centro_enriquecido)
                
                centros_custo_processados = json.dumps(centros_custo_enriquecidos)
                
            except (json.JSONDecodeError, ValueError):
                centros_custo_processados = centros_custo_json or '[]'
        
        # ===== CRIAR AGENDAMENTO DE PAGAMENTO =====
        # Converter JSON strings para objetos JSON (usar categorias processadas com informações enriquecidas)
        categorias_obj = json.loads(categorias_processadas) if categorias_processadas else []
        centros_custo_obj = json.loads(centros_custo_processados) if centros_custo_processados else []
        
        agendamento = AgendamentoPagamentoModel(
            faturamento_id=None,
            lancamento_avulso_id=None,
            pessoa_financeiro_id=int(pessoa_financeiro_id),
            data_vencimento=data_vencimento_obj,
            valor_total_100=valor_centavos,
            descricao=descricao,
            referencia=referencia if referencia else None,
            data_competencia=data_competencia_obj,
            categorias_json=categorias_obj,
            centros_custo_json=centros_custo_obj,
            parcelamento_ativo=parcelamento_ativo,
            numero_parcelas=int(numero_parcelas) if numero_parcelas else None,
            dias_entre_parcelas=int(dias_entre_parcelas),
            conta_bancaria_id=int(conta_bancaria_id),
            situacao_pagamento_id=8  # Conciliado
        )
        
        db.session.add(agendamento)
        db.session.flush()  # Para obter o ID
        
        # ===== CRIAR PARCELAS SE NECESSÁRIO =====
        if parcelamento_ativo and parcelas_json:
            try:
                parcelas = json.loads(parcelas_json)
                for i, parcela_data in enumerate(parcelas, 1):
                    data_venc_parcela = datetime.strptime(parcela_data['vencimento'], '%Y-%m-%d').date()
                    nova_parcela = ParcelaCategorizacaoModel(
                        agendamento_id=agendamento.id,
                        numero_parcela=i,
                        data_vencimento=data_venc_parcela,
                        valor_parcela=parcela_data['valor'],
                        descricao=parcela_data.get('descricao', ''),
                        referencia=parcela_data.get('referencia', ''),
                        situacao_pagamento_id=8  # Conciliado
                    )
                    db.session.add(nova_parcela)
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'message': 'Erro ao processar parcelas!',
                    'errors': {'parcelas_json': 'Erro ao processar parcelas!'}
                }), 400
        
        # ===== CONCILIAR TRANSAÇÃO OFX COM DADOS PARA REVERSÃO =====
        # Flush para obter o ID da movimentação
        db.session.flush()
        
        movimentacoes_ids = []
        if movimentacao_financeira.id:
            movimentacoes_ids.append(movimentacao_financeira.id)
        
        # Salvar dados da conciliação no formato JSON
        sucesso_salvamento = transacao.salvar_dados_conciliacao(
            tipo_conciliacao='NOVA_MOVIMENTACAO',
            agendamentos_ids=[agendamento.id],
            faturamentos_ids=[],
            movimentacoes_ids=movimentacoes_ids,
            lancamentos_avulsos_ids=[],
            usuario_id=current_user.id,
            observacoes=f'Nova movimentação criada: {descricao}'
        )
        
        if not sucesso_salvamento:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Erro ao salvar dados de conciliação para reversão'
            }), 500
        
        # Adicionar campo específico para compatibilidade
        transacao.pagamento_id = agendamento.id
        
        # ===== CRIAR MOVIMENTAÇÃO FINANCEIRA =====
        tipo_movimentacao = 1 if transacao.valor > 0 else 2
        
        movimentacao_financeira = MovimentacaoFinanceiraModel(
            tipo_movimentacao=tipo_movimentacao,
            usuario_id=current_user.id,
            data_movimentacao=transacao.data_transacao,
            conta_bancaria_id=agendamento.conta_bancaria_id,
            valor_movimentacao_100=agendamento.valor_total_100,
            ativo=True,
            conciliacao_bancaria=True,
            
            # Campos de auditoria da conciliação
            importacao_ofx_id=transacao_id,
            agendamento_id=agendamento.id,
            
            # Dados originais da transação OFX
            conciliacao_fitid=transacao.fitid,
            conciliacao_valor_original=int(abs(transacao.valor * 100)),
            conciliacao_descricao_ofx=transacao.memo or transacao.descricao_limpa,
            conciliacao_data_transacao=transacao.data_transacao,
            conciliacao_tipo_movimento=transacao.tipo_movimento,
            
            # Auditoria da conciliação
            conciliacao_data_processamento=datetime.now(),
            conciliacao_observacoes=f'Nova movimentação via conciliação: {descricao}',
            
            # Referências de origem
            conciliacao_faturamento_id=None,
            conciliacao_lancamento_avulso_id=None,
            conciliacao_tipo_origem='nova_movimentacao',
            
            # Controle de diferenças
            conciliacao_valor_diferenca=0
        )
        db.session.add(movimentacao_financeira)
        
        # ===== ATUALIZAR SALDO DA CONTA BANCÁRIA =====
        saldo_conta = SaldoMovimentacaoFinanceiraModel.query.filter(
            SaldoMovimentacaoFinanceiraModel.conta_bancaria_id == agendamento.conta_bancaria_id,
            SaldoMovimentacaoFinanceiraModel.ativo == True,
            SaldoMovimentacaoFinanceiraModel.deletado == False
        ).first()
        
        # Criar registro de saldo se não existir
        if not saldo_conta:
            saldo_conta = SaldoMovimentacaoFinanceiraModel(
                data_movimentacao=transacao.data_transacao,
                valor_total_saldo_100=0,
                conta_bancaria_id=agendamento.conta_bancaria_id,
                ativo=True
            )
            db.session.add(saldo_conta)
        
        # Atualizar saldo baseado no tipo de movimentação
        if tipo_movimentacao == 1:  # Entrada/Crédito
            saldo_conta.valor_total_saldo_100 += agendamento.valor_total_100
        elif tipo_movimentacao == 2:  # Saída/Débito
            saldo_conta.valor_total_saldo_100 -= agendamento.valor_total_100
        
        # Atualizar data da movimentação
        saldo_conta.data_movimentacao = DataHora.obter_data_atual_padrao_en()
        db.session.add(saldo_conta)
        
        # ===== COMMIT DAS ALTERAÇÕES =====
        db.session.commit()
        
        # ===== REGISTRAR PONTUAÇÃO PARA GAMIFICAÇÃO =====
        try:
            PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                current_user.id,
                TipoAcaoEnum.CADASTRO,
                TipoAcaoEnum.CADASTRO.pontos,
                modulo="nova_movimentacao_conciliacao",
            )
        except Exception as e_pontuacao:
            print(f"Erro ao registrar pontuação: {e_pontuacao}")
        
        return jsonify({
            'success': True,
            'message': 'Nova movimentação criada e conciliada com sucesso!',
            'agendamento_id': agendamento.id,
            'transacao_id': transacao_id
        })
        
    except Exception as e:
        db.session.rollback()
        print(f'Erro ao salvar nova movimentação: {e}')
        return jsonify({
            'success': False,
            'message': f'Erro interno do servidor: {str(e)}'
        }), 500

@app.route("/api/reverter-conciliacao", methods=["POST"])
@login_required
@requires_roles
def reverter_conciliacao():
    """
    Endpoint para reverter uma conciliação específica
    """
    try:
        data = request.get_json()
        transacao_id = data.get('transacao_id')
        
        if not transacao_id:
            return jsonify({
                'success': False,
                'message': 'ID da transação é obrigatório'
            }), 400
        
        # Buscar a transação OFX
        transacao = ImportacaoOfx.query.get(transacao_id)
        if not transacao:
            return jsonify({
                'success': False,
                'message': 'Transação não encontrada'
            }), 404
        
        # Verificar se pode ser revertida
        if not transacao.conciliado or not transacao.dados_conciliacao_json:
            return jsonify({
                'success': False,
                'message': 'Esta transação não pode ser revertida (não está conciliada ou não possui dados de reversão)'
            }), 400
        
        # Reverter a conciliação
        sucesso, mensagem = transacao.reverter_conciliacao()
        
        if sucesso:
            return jsonify({
                'success': True,
                'message': mensagem
            })
        else:
            return jsonify({
                'success': False,
                'message': mensagem
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao reverter conciliação: {str(e)}'
        }), 500


@app.route("/api/detalhes-conciliacao/<int:transacao_id>", methods=["GET"])
@login_required
@requires_roles
def detalhes_conciliacao(transacao_id):
    """
    Endpoint para obter detalhes da conciliação de uma transação
    Retorna valor total e quantidade de agendamentos conciliados
    """
    try:
        # Buscar a transação OFX
        transacao = ImportacaoOfx.query.get(transacao_id)
        if not transacao:
            return jsonify({
                'success': False,
                'message': 'Transação não encontrada'
            }), 404
        
        # Verificar se a transação está conciliada
        if not transacao.conciliado:
            return jsonify({
                'success': True,
                'valor_total_agendamentos': 'R$ 0,00',
                'quantidade_agendamentos': 0,
                'message': 'Transação não está conciliada'
            })
        
        print(transacao)
        
        # Buscar dados da conciliação
        dados_conciliacao = {}
        if transacao.dados_conciliacao_json:
            if isinstance(transacao.dados_conciliacao_json, dict):
                dados_conciliacao = transacao.dados_conciliacao_json
            else:
                # Se for outro tipo, tentar converter para dict
                dados_conciliacao = {}

        # Obter IDs dos agendamentos conciliados
        agendamentos_ids = []
        if isinstance(dados_conciliacao, dict):
            agendamentos_ids = dados_conciliacao.get('agendamentos_ids', [])
        elif isinstance(dados_conciliacao, list):
            agendamentos_ids = dados_conciliacao
        
        # Se não há dados de conciliação nos dados JSON, tentar buscar pelo campo agendamento_id
        if not agendamentos_ids and hasattr(transacao, 'agendamento_id') and transacao.agendamento_id:
            agendamentos_ids = [transacao.agendamento_id]
        
        # Buscar os agendamentos conciliados
        valor_total_centavos = 0
        quantidade_agendamentos = 0
        
        if agendamentos_ids:
            ids_validos = []
            for id_val in agendamentos_ids:
                try:
                    ids_validos.append(int(id_val))
                except (ValueError, TypeError):
                    continue
            
            if ids_validos:
                agendamentos = AgendamentoPagamentoModel.query.filter(
                    AgendamentoPagamentoModel.id.in_(ids_validos)
                ).all()
                
                quantidade_agendamentos = len(agendamentos)
                
                for agendamento in agendamentos:
                    print(agendamento, 'agendamento')
                    if hasattr(agendamento, 'valor_total_100') and agendamento.valor_total_100:
                        valor_total_centavos += agendamento.valor_total_100

        valor_formatado = ValoresMonetarios.converter_float_brl_positivo(valor_total_centavos / 100) if valor_total_centavos > 0 else 'R$ 0,00'

        return jsonify({
            'success': True,
            'valor_total_agendamentos': valor_formatado,
            'quantidade_agendamentos': quantidade_agendamentos,
            'detalhes': {
                'transacao_conciliada': transacao.conciliado,
                'agendamentos_ids': agendamentos_ids
            }
        })
        
    except Exception as e:
        print(f'Erro ao buscar detalhes da conciliação: {e}')
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar detalhes: {str(e)}'
        }), 500