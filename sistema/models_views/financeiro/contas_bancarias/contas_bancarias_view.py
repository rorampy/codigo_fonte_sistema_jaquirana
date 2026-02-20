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
from sistema.models_views.faturamento.cargas_a_faturar.transportadora.frete_a_pagar_model import FretePagarModel
from sistema.models_views.faturamento.cargas_a_faturar.extrator.extrator_a_pagar_model import ExtratorPagarModel
from sistema.models_views.faturamento.cargas_a_faturar.fornecedor.fornecedor_a_pagar_model import FornecedorPagarModel
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.configuracoes_gerais.conta_bancaria.conta_bancaria_model import ContaBancariaModel
from sistema.models_views.configuracoes_gerais.centro_custo.centro_custo_model import CentroCustoModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_view import (obter_estrutura_com_folhas)
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
from sistema.models_views.gerenciar.pessoa_financeiro.pessoa_financeiro_model import PessoaFinanceiroModel
from sistema.models_views.financeiro.operacional.categorizar_fatura.categorizacao_model import AgendamentoPagamentoModel
from sistema.models_views.financeiro.operacional.categorizar_fatura.parcela_categorizacao.parcela_categorizacao_model import ParcelaCategorizacaoModel
from sistema.models_views.financeiro.lancamento_avulso.lancamento_avulso_model import LancamentoAvulsoModel
from sistema.models_views.importacao_ofx.importacao_ofx_service import ImportacaoOfxService
from sistema._utilitarios import *
from datetime import datetime, date
from sistema._utilitarios import *


def _extrair_filtros_conciliacao(conta_bancaria_id=None):
    """
    Extrai e valida parâmetros de filtro da requisição (igual ao listagem_ofx)
    
    Returns:
        dict: Dicionário com todos os filtros validados
    """
    filtros = {
        'data_inicio': request.args.get('dataInicio', '').strip(),
        'data_fim': request.args.get('dataFim', '').strip(), 
        'conciliado': request.args.get('conciliado', 'nao'),
        'ofx_ignorada': request.args.get('ofx_ignorada', 'nao'),
        'fitid': request.args.get('fitid', '').strip(),
        'descricao': request.args.get('descricao', '').strip(),
        'valor': request.args.get('valor', ''),
        'tipo_movimentacao': request.args.get('tipo_movimentacao', '').strip(),
        'pagina': request.args.get('pagina', 1, type=int),
        'por_pagina': 100,
        'conta_bancaria_id': conta_bancaria_id
    }
    
    if filtros['valor'] == 'R$ 0,00':
        filtros['valor'] = ''
    
    filtros['conciliado_bool'] = filtros['conciliado'] == 'sim'
    filtros['ofx_ignorada_bool'] = filtros['ofx_ignorada'] == 'sim'
    filtros['parcial_bool'] = filtros['conciliado'] == 'parcial'
    
    return filtros


def _buscar_transacoes_com_filtros(filtros):
    """
    Busca transações OFX aplicando filtros e paginação (igual ao listagem_ofx)
    
    Args:
        filtros (dict): Filtros extraídos da requisição
        
    Returns:
        dict: Resultado contendo transações, totais e informações de paginação
    """
    transacoes = ImportacaoOfx.query
    
    transacoes = transacoes.filter(ImportacaoOfx.deletado == False)
    
    if filtros['parcial_bool']:
        transacoes = transacoes.filter(
            ImportacaoOfx.conciliacao_parcial == True,
            ImportacaoOfx.conciliado == False
        )
    else:
        conciliado_val = filtros['conciliado_bool']
        transacoes = transacoes.filter(ImportacaoOfx.conciliado == conciliado_val)
    
    ofx_ignorada_val = filtros['ofx_ignorada_bool']
    transacoes = transacoes.filter(ImportacaoOfx.ofx_deletada == ofx_ignorada_val)
    
    if filtros['data_inicio']:
        transacoes = transacoes.filter(ImportacaoOfx.data_transacao >= filtros['data_inicio'])
    if filtros['data_fim']:
        transacoes = transacoes.filter(ImportacaoOfx.data_transacao <= filtros['data_fim'])
    if filtros['fitid']:
        transacoes = transacoes.filter(ImportacaoOfx.fitid.ilike(f'%{filtros["fitid"]}%'))
    if filtros['valor']:
        transacoes = transacoes.filter(ImportacaoOfx.valor_formatado.ilike(f'%{filtros["valor"]}%'))
    if filtros['descricao']:
        transacoes = transacoes.filter(ImportacaoOfx.descricao_limpa.ilike(f'%{filtros["descricao"]}%'))
    if filtros['conta_bancaria_id']:
        transacoes = transacoes.filter(ImportacaoOfx.conta_bancaria_id == filtros['conta_bancaria_id'])
    
    if filtros['tipo_movimentacao']:
        if filtros['tipo_movimentacao'] == 'entrada':
            transacoes = transacoes.filter(ImportacaoOfx.valor > 0)
        elif filtros['tipo_movimentacao'] == 'saida':
            transacoes = transacoes.filter(ImportacaoOfx.valor < 0)

    total_transacoes = transacoes.count()
    transacoes = transacoes.order_by(ImportacaoOfx.data_transacao.desc(), ImportacaoOfx.id.desc())\
                           .offset((filtros['pagina']-1)*filtros['por_pagina'])\
                           .limit(filtros['por_pagina'])\
                           .all()
    
    total_paginas = (total_transacoes // filtros['por_pagina']) + (1 if total_transacoes % filtros['por_pagina'] else 0)
    return {
        'transacoes': transacoes,
        'total_transacoes': total_transacoes,
        'total_paginas': total_paginas,
        'pagina': filtros['pagina'],
        'por_pagina': filtros['por_pagina']
    }


def _carregar_estruturas_formularios():
    """
    Carrega todas as estruturas de dados necessárias para os formulários
    
    Returns:
        dict: Dicionário com todas as estruturas carregadas
    """
    estruturas = {
        'estrutura_plano_contas': PlanoContaModel.obter_estrutura_plana_hierarquica(),
        'centros_custo': CentroCustoModel.obter_centro_custos_ativos(),
        'contas_bancarias': ContaBancariaModel.obter_contas_bancarias_ativas(),
        'pessoas_financeiro': PessoaFinanceiroModel.listar_pessoas_ativas()
    }
    
    for pessoa in estruturas['pessoas_financeiro']:
        if pessoa.numero_documento and len(pessoa.numero_documento.strip()) > 0:
            if len(pessoa.numero_documento) == 14:
                pessoa.documento_formatado = ValidaDocs.insere_pontuacao_cnpj(pessoa.numero_documento)
            else:
                pessoa.documento_formatado = ValidaDocs.insere_pontuacao_cpf(pessoa.numero_documento)
        else:
            pessoa.documento_formatado = "N/A"
    
    return estruturas


def _processar_categorias_por_transacao(transacoes):
    """
    Processa categorias específicas para cada transação baseada no tipo (receita/despesa)
    
    Args:
        transacoes (list): Lista de transações OFX
        
    Returns:
        dict: Categorias filtradas por ID da transação
    """
    categorias_por_transacao = {}
    
    for transacao in transacoes:
        eh_receita = transacao.valor > 0
        tipos_plano_conta = [1, 3] if eh_receita else [2, 3]
        
        categorias_filtradas = []
        for tipo_individual in tipos_plano_conta:
            categorias_tipo = obter_estrutura_com_folhas([tipo_individual])
            categorias_filtradas.extend(categorias_tipo)
        
        categorias_unicas = []
        ids_vistos = set()
        for cat in categorias_filtradas:
            if cat['id'] not in ids_vistos:
                categorias_unicas.append(cat)
                ids_vistos.add(cat['id'])
        
        categorias_por_transacao[transacao.id] = categorias_unicas
    
    return categorias_por_transacao


def _obter_resumo_importacao(filtros):
    """
    Obtém resumo estatístico da importação aplicando os filtros
    
    Args:
        filtros (dict): Filtros aplicados na consulta
        
    Returns:
        dict: Resumo com estatísticas da importação
    """
    return ImportacaoOfxService.obter_resumo_importacao(
        data_inicio=filtros['data_inicio'] if filtros['data_inicio'] else None,
        data_fim=filtros['data_fim'] if filtros['data_fim'] else None,
        batch_id=None,
        conciliado=filtros['conciliado_bool'],
        ftid=filtros['fitid'] if filtros['fitid'] else None,
        valor=filtros['valor'] if filtros['valor'] else '',
        descricao=filtros['descricao'] if filtros['descricao'] else None,
        tipo_movimentacao=filtros['tipo_movimentacao'] if filtros['tipo_movimentacao'] else None,
        conta_bancaria_id=filtros['conta_bancaria_id'] if filtros['conta_bancaria_id'] else None
    )


def _preparar_dados_conta_instituicao(transacoes):
    """
    Prepara informações da conta bancária e instituição baseada na transação mais recente
    
    Args:
        transacoes (list): Lista de transações OFX
        
    Returns:
        tuple: (conta_info, instituicao_info, periodo_info)
    """
    transacao_mais_recente = transacoes[0] if transacoes else None
    
    if not transacao_mais_recente:
        return {}, {}, {}
    
    conta_info = {
        'bank_id': getattr(transacao_mais_recente, 'banco_id', ''),
        'branch_id': '',
        'account_id': getattr(transacao_mais_recente, 'conta_id', '')
    }
    
    instituicao_info = {
        'organization': getattr(transacao_mais_recente, 'instituicao_org', ''),
        'nome': getattr(transacao_mais_recente, 'instituicao_org', '')
    }
    
    periodo_info = {
        'data_inicio': getattr(transacao_mais_recente, 'data_inicio_extrato', None),
        'data_fim': getattr(transacao_mais_recente, 'data_fim_extrato', None),
        'primeira_transacao': getattr(transacao_mais_recente, 'data_inicio_extrato', None),
        'ultima_transacao': getattr(transacao_mais_recente, 'data_fim_extrato', None)
    }
    
    return conta_info, instituicao_info, periodo_info


def _preparar_estatisticas(resumo_bd):
    """
    Prepara estatísticas formatadas para o template
    
    Args:
        resumo_bd (dict): Dados do resumo da importação
        
    Returns:
        dict: Estatísticas formatadas
    """
    if not resumo_bd:
        return {
            'total_creditos': 0,
            'total_debitos': 0,
            'saldo_liquido': 0,
            'creditos_formatado': 'R$ 0,00',
            'debitos_formatado': 'R$ 0,00',
            'saldo_formatado': 'R$ 0,00'
        }
    
    return {
        'total_creditos': resumo_bd.get('total_creditos', 0),
        'total_debitos': resumo_bd.get('total_debitos', 0),
        'saldo_liquido': resumo_bd.get('saldo_liquido', 0),
        'creditos_formatado': resumo_bd.get('creditos_formatado', 'R$ 0,00'),
        'debitos_formatado': resumo_bd.get('debitos_formatado', 'R$ 0,00'),
        'saldo_formatado': resumo_bd.get('saldo_formatado', 'R$ 0,00')
    }


@app.route("/financeiro/movimentacoes-financeiras/conciliacao-ofx/<int:conta_id>", methods=["GET", "POST"])
@login_required
@requires_roles
def conciliacao_ofx(conta_id):
    """
    Rota principal para conciliação de transações OFX
    Implementa sistema completo de filtros, paginação e estruturas para formulários
    """
    try:
        batch_id = session.get('current_batch_id') or ImportacaoOfxService.obter_ultimo_batch_importacao(conta_bancaria_id=conta_id)
        if not batch_id:
            flash(('Nenhum arquivo OFX foi importado. Importe um arquivo primeiro.', 'warning'))
            return redirect(url_for('importar_ofx'))
        
        filtros = _extrair_filtros_conciliacao(conta_bancaria_id=conta_id)
        
        resultado_paginacao = _buscar_transacoes_com_filtros(filtros)
        
        estruturas = _carregar_estruturas_formularios()
        
        estruturas['estrutura_plano'] = PlanoContaModel.obter_estrutura_plana_hierarquica()
        
        categorias_por_transacao = _processar_categorias_por_transacao(resultado_paginacao['transacoes'])
        
        resumo_bd = _obter_resumo_importacao(filtros)
        
        conta_info, instituicao_info, periodo_info = _preparar_dados_conta_instituicao(resultado_paginacao['transacoes'])
        
        estatisticas = _preparar_estatisticas(resumo_bd)
        
        return render_template("financeiro/contas_bancarias/conciliacao_ofx.html",
            transacoes_ofx=resultado_paginacao['transacoes'],
            
            pagina=resultado_paginacao['pagina'],
            total_paginas=resultado_paginacao['total_paginas'],
            total_transacoes=resultado_paginacao['total_transacoes'],
            por_pagina=resultado_paginacao['por_pagina'],
            batch_id=batch_id,
            
            filtro_conciliado=filtros['conciliado'],
            filtro_ofx_ignorada=filtros['ofx_ignorada'],
            filtro_fitid=filtros['fitid'],
            filtro_valor=filtros['valor'],
            filtro_descricao=filtros['descricao'],
            filtro_tipo_movimentacao=filtros['tipo_movimentacao'],
            filtro_data_inicio=filtros['data_inicio'],
            filtro_data_fim=filtros['data_fim'],
            
            estrutura_plano_contas=estruturas['estrutura_plano_contas'],
            estrutura_plano=estruturas['estrutura_plano'], 
            centros_custo=estruturas['centros_custo'],
            pessoas_financeiro=estruturas['pessoas_financeiro'],
            contas_bancarias=estruturas['contas_bancarias'],
            categorias_por_transacao=categorias_por_transacao,
            
            resumo=resumo_bd or {},
            arquivo_nome=resumo_bd.get('arquivo_nome', '') if resumo_bd else '',
            data_importacao=_formatar_data_importacao(resumo_bd),
            estatisticas=estatisticas,
            
            conta_info=conta_info,
            instituicao_info=instituicao_info,
            periodo_info=periodo_info,
            
            conta_id=conta_id
        )
        
    except Exception as e:
        flash(('Erro ao carregar dados de conciliação OFX. Tente novamente.', 'danger'))
        return redirect(url_for('conciliacao_contas_bancarias'))


@app.route("/financeiro/movimentacoes-financeiras/conciliacao-ofx/exclusao-visualizacao/<int:transacao_id>", methods=["GET","POST"])
@login_required
@requires_roles
def excluir_ativar_transacao_visualizacao(transacao_id):
    """
    Endpoint AJAX para buscar sugestões de agendamentos para conciliação OFX
    Suporta busca individual (transacao_id) ou em lote (transacoes_ids)
    """
    try:
        if transacao_id:
            importacao = ImportacaoOfx.query.filter(
                ImportacaoOfx.id == transacao_id,
                ImportacaoOfx.deletado == False            
            ).first()
            
            mensagem_sucesso = ''
            if importacao.ofx_deletada == False:
                importacao.ofx_deletada = True
                mensagem_sucesso = 'Transação excluída da visualização com sucesso'
            else:
                importacao.ofx_deletada = False
                mensagem_sucesso = 'Transação reativada na visualização com sucesso'
            
            db.session.commit()
            
            flash((mensagem_sucesso, 'success'))
            return redirect(url_for('conciliacao_ofx', conta_id=importacao.conta_bancaria_id))
    except Exception as e:
        flash(('Erro ao processar exclusão/ativação da transação. Tente novamente.', 'danger'))
        db.session.rollback()
        try:
            importacao = ImportacaoOfx.query.get(transacao_id)
            conta_id = importacao.conta_bancaria_id if importacao else None
            if conta_id:
                return redirect(url_for('conciliacao_ofx', conta_id=conta_id))
        except:
            pass
        return redirect(url_for('conciliacao_contas_bancarias'))


@app.route("/api/sugestoes-ofx", methods=["POST"])
@login_required
@requires_roles
def obter_sugestoes_ofx():
    """
    Endpoint AJAX para buscar sugestões de agendamentos para conciliação OFX
    Suporta busca individual (transacao_id) ou em lote (transacoes_ids)
    """
    try:
        data = request.get_json()
        transacao_id = data.get('transacao_id')
        transacoes_ids = data.get('transacoes_ids') 
        
        if transacoes_ids and isinstance(transacoes_ids, list):
            return processar_sugestoes_lote(transacoes_ids)
        elif transacao_id:
            return processar_sugestao_individual(transacao_id)
        else:
            return jsonify({
                'success': False,
                'error': 'transacao_id ou transacoes_ids é obrigatório',
                'sugestoes': []
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor',
            'sugestoes': []
        }), 500

@app.route("/api/buscar-agendamentos", methods=["POST"])
@login_required
@requires_roles
def buscar_agendamentos_para_conciliacao():
    """
    Endpoint AJAX para buscar agendamentos com filtros (últimos 7 dias)
    """
    try:
        data = request.get_json()
        eh_credito = data.get('is_credit', False) == 'true'
        conta_bancaria_id = data.get('conta_bancaria_id')

        if not conta_bancaria_id:
            from sistema.models_views.configuracoes_gerais.conta_bancaria.conta_bancaria_model import ContaBancariaModel
            conta_principal = ContaBancariaModel.verifica_conta_bancaria_principal()
            if conta_principal:
                conta_bancaria_id = conta_principal.id
            else:
                primeira_conta = ContaBancariaModel.query.filter_by(ativo=True, deletado=False).first()
                conta_bancaria_id = primeira_conta.id if primeira_conta else None

        if not conta_bancaria_id:
            return jsonify({
                'success': False,
                'error': 'Nenhuma conta bancária disponível para busca de agendamentos',
                'agendamentos': [],
                'total': 0
            }), 400
        valor_min = data.get('valor_min')
        valor_max = data.get('valor_max')
        data_inicio = data.get('data_inicio')
        data_fim = data.get('data_fim')
        categoria_id = data.get('categoria')
        beneficiario_id = data.get('beneficiario_id')
        descricao = data.get('descricao') or ''
        descricao = descricao.strip() if descricao else ''
        
        try:
            valor_min = float(valor_min) if valor_min and valor_min != '' else None
        except (ValueError, TypeError):
            valor_min = None
            
        try:
            valor_max = float(valor_max) if valor_max and valor_max != '' else None
        except (ValueError, TypeError):
            valor_max = None
    
        
        agendamentos_formatados = AgendamentoPagamentoModel.buscar_agendamentos_com_filtros(
            eh_credito=eh_credito,
            valor_min=valor_min,
            valor_max=valor_max,
            data_inicio=data_inicio,
            data_fim=data_fim,
            categoria_id=categoria_id,
            beneficiario_id=beneficiario_id,
            descricao=descricao
        )
        
        return jsonify({
            'success': True,
            'agendamentos': agendamentos_formatados,
            'total': len(agendamentos_formatados),
            'periodo': {
                'data_inicio': data_inicio,
                'data_fim': data_fim
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro interno do servidor: {str(e)}',
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
        
        transacao_id = data.get('transacao_id')
        agendamentos_ids = data.get('agendamentos_ids', [])
        observacoes = data.get('observacoes', '')
        
        if not transacao_id or not agendamentos_ids:
            return jsonify({
                'success': False,
                'message': 'Dados obrigatórios não fornecidos'
            }), 400
        
        from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx
        transacao = ImportacaoOfx.query.get(transacao_id)
        if not transacao:
            return jsonify({
                'success': False,
                'message': 'Transação não encontrada'
            }), 404
        
        if transacao.conciliado and not transacao.conciliacao_parcial:
            return jsonify({
                'success': False,
                'message': 'Esta transação já foi totalmente conciliada'
            }), 400
        
        agendamentos = AgendamentoPagamentoModel.query.filter(
            AgendamentoPagamentoModel.id.in_(agendamentos_ids),
            AgendamentoPagamentoModel.conta_bancaria_id == transacao.conta_bancaria_id,
        ).all()
        
        if len(agendamentos) != len(agendamentos_ids):
            return jsonify({
                'success': False,
                'message': 'Alguns agendamentos não foram encontrados'
            }), 404
        
        agendamentos_totalmente_conciliados = [ag for ag in agendamentos if ag.situacao_pagamento_id == 8]
        if agendamentos_totalmente_conciliados:
            codigos_conciliados = [str(ag.id) for ag in agendamentos_totalmente_conciliados]
            return jsonify({
                'success': False,
                'message': f'Os seguintes agendamentos já foram totalmente conciliados'
            }), 400
        
        valor_total_agendamentos = sum(
            ag.valor_pendente_conciliacao_100 if ag.situacao_pagamento_id == 10 
            else ag.valor_total_100 
            for ag in agendamentos
        )
        valor_transacao_centavos = int(abs(transacao.valor * 100))
        valor_disponivel_transacao = transacao.valor_disponivel_100
        
        
        if valor_total_agendamentos > valor_disponivel_transacao:
            
            if valor_disponivel_transacao <= 0:
                valor_ja_utilizado = transacao.valor_utilizado_100 or 0
                return jsonify({
                    'success': False,
                    'message': f'Transação não possui valor disponível. '
                              f'Valor total da transação: {ValoresMonetarios.converter_float_brl_positivo(valor_transacao_centavos/100)}. '
                              f'Já utilizado: {ValoresMonetarios.converter_float_brl_positivo(valor_ja_utilizado/100)}.'
                }), 400
            
            fator_proporcional = valor_disponivel_transacao / valor_total_agendamentos
            conciliacao_proporcional = True
            valor_efetivo_conciliado = valor_disponivel_transacao
        else:
            fator_proporcional = 1.0
            conciliacao_proporcional = False
            valor_efetivo_conciliado = valor_total_agendamentos
        
        tipo_movimentacao = 1 if transacao.valor > 0 else 2
        
        from datetime import datetime
        faturamentos_conciliados = []
        lancamentos_conciliados = []
        movimentacoes_criadas = []
        
        for agendamento in agendamentos:
            
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
            
            valor_base_agendamento = (
                agendamento.valor_pendente_conciliacao_100 if agendamento.situacao_pagamento_id == 10 
                else agendamento.valor_total_100
            )
            valor_proporcional_agendamento = int(valor_base_agendamento * fator_proporcional)
            
            valor_diferenca = valor_transacao_centavos - valor_efetivo_conciliado
            valor_diferenca_proporcional = int((valor_proporcional_agendamento / valor_efetivo_conciliado) * valor_diferenca) if valor_diferenca != 0 else 0
            
            nova_movimentacao = MovimentacaoFinanceiraModel(
                tipo_movimentacao=tipo_movimentacao,
                usuario_id=current_user.id,
                data_movimentacao=transacao.data_transacao,
                conta_bancaria_id=agendamento.conta_bancaria_id,
                valor_movimentacao_100=valor_proporcional_agendamento,
                ativo=True,
                conciliacao_bancaria=True,
                
                importacao_ofx_id=transacao_id,
                agendamento_id=agendamento.id,
                
                conciliacao_fitid=transacao.fitid,
                conciliacao_valor_original=valor_transacao_centavos,
                conciliacao_descricao_ofx=transacao.memo or transacao.descricao_limpa,
                conciliacao_data_transacao=transacao.data_transacao,
                conciliacao_tipo_movimento=transacao.tipo_movimento,
                
                conciliacao_data_processamento=datetime.now(),
                conciliacao_observacoes=f'CONCILIAÇÃO EM MASSA {"PROPORCIONAL" if conciliacao_proporcional else "TOTAL"}: {observacoes}' if observacoes else f'CONCILIAÇÃO EM MASSA {"PROPORCIONAL" if conciliacao_proporcional else "TOTAL"}',
                
                conciliacao_faturamento_id=faturamento_id,
                conciliacao_lancamento_avulso_id=lancamento_avulso_id,
                conciliacao_tipo_origem=tipo_origem,
                
                conciliacao_valor_diferenca=valor_diferenca_proporcional
            )
            
            db.session.add(nova_movimentacao)
            movimentacoes_criadas.append(nova_movimentacao)
            
            if not agendamento.adicionar_valor_conciliado(valor_proporcional_agendamento):
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'message': f'Erro interno: não foi possível adicionar valor conciliado ao agendamento {agendamento.id}'
                }), 500
            
            agendamento.situacao_pagamento_id = 8 if agendamento.esta_totalmente_conciliado else 10
            
            db.session.add(agendamento)
            
            
            acao = TipoAcaoEnum.CADASTRO
            PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                current_user.id,
                acao,
                acao.pontos,
                modulo='conciliacao_bancaria'
            )
        
        for faturamento_id in faturamentos_conciliados:
            faturamento = FaturamentoModel.query.get(faturamento_id)
            if faturamento:
                agendamentos_faturamento = AgendamentoPagamentoModel.obter_agendamentos_por_faturamento(faturamento_id)
                todos_conciliados = all(ag.esta_totalmente_conciliado for ag in agendamentos_faturamento)
                
                if todos_conciliados:
                    faturamento.situacao_pagamento_id = 8
                    db.session.add(faturamento)
        
        for lancamento_id in lancamentos_conciliados:
            lancamento_avulso = LancamentoAvulsoModel.query.get(lancamento_id)
            if lancamento_avulso:
                agendamento_lancamento = AgendamentoPagamentoModel.query.filter_by(lancamento_avulso_id=lancamento_id).first()
                if agendamento_lancamento and agendamento_lancamento.esta_totalmente_conciliado:
                    lancamento_avulso.situacao_pagamento_id = 8
                    db.session.add(lancamento_avulso)
        
        if not transacao.adicionar_valor_utilizado(valor_efetivo_conciliado):
            return jsonify({
                'success': False,
                'message': 'Erro interno: não foi possível atualizar valor utilizado da transação'
            }), 500

        movimentacoes_ids = []
        
        db.session.flush()
        for mov in movimentacoes_criadas:
            if mov.id:
                movimentacoes_ids.append(mov.id)
        
        if conciliacao_proporcional:
            tipo_conciliacao = 'AGENDAMENTO_MASSA_PROPORCIONAL'
        else:
            tipo_conciliacao = 'AGENDAMENTO_MASSA_TOTAL' if transacao.esta_totalmente_utilizada else 'AGENDAMENTO_MASSA_PARCIAL'
        
        sucesso_salvamento = ImportacaoOfxService.salvar_dados_conciliacao(
            transacao=transacao,
            tipo_conciliacao=tipo_conciliacao,
            agendamentos_ids=agendamentos_ids,
            faturamentos_ids=faturamentos_conciliados,
            movimentacoes_ids=movimentacoes_ids,
            lancamentos_avulsos_ids=lancamentos_conciliados,
            valor_agendamento=valor_efetivo_conciliado,
            usuario_id=current_user.id,
            observacoes=f'{"MASSA PROPORCIONAL" if conciliacao_proporcional else "MASSA TOTAL"}: {observacoes}' if observacoes else f'{"Conciliação em massa proporcional" if conciliacao_proporcional else "Conciliação em massa total"}'
        )
        
        if not sucesso_salvamento:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Erro ao salvar dados de conciliação para reversão'
            }), 500
        
        obs_conciliacao = f'Conciliação em massa {"PROPORCIONAL" if conciliacao_proporcional else "TOTAL"} com {len(agendamentos)} agendamento(s)'
        
        if conciliacao_proporcional:
            obs_conciliacao += f' - {fator_proporcional*100:.1f}% de cada agendamento (R$ {valor_efetivo_conciliado/100:.2f} de R$ {valor_total_agendamentos/100:.2f})'
        
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
        
        if movimentacoes_criadas:
            primeira_movimentacao = movimentacoes_criadas[0]
            conta_bancaria_id = primeira_movimentacao.conta_bancaria_id
            
            from sistema.models_views.financeiro.movimentacao_financeira.saldo_movimentacao_financeira_model import SaldoMovimentacaoFinanceiraModel
            
            saldo_conta = SaldoMovimentacaoFinanceiraModel.query.filter(
                SaldoMovimentacaoFinanceiraModel.conta_bancaria_id == conta_bancaria_id,
                SaldoMovimentacaoFinanceiraModel.ativo == True,
                SaldoMovimentacaoFinanceiraModel.deletado == False
            ).first()
            
            if not saldo_conta:
                saldo_conta = SaldoMovimentacaoFinanceiraModel(
                    data_movimentacao=transacao.data_transacao,
                    valor_total_saldo_100=0,
                    conta_bancaria_id=conta_bancaria_id,
                    ativo=True
                )
                db.session.add(saldo_conta)
            
            if tipo_movimentacao == 1:
                saldo_conta.valor_total_saldo_100 += valor_efetivo_conciliado
            elif tipo_movimentacao == 2:
                saldo_conta.valor_total_saldo_100 -= valor_efetivo_conciliado
            
            saldo_conta.data_movimentacao = DataHora.obter_data_atual_padrao_en()
            db.session.add(saldo_conta)
        
        db.session.commit()
        
        status_transacao = "totalmente utilizada" if transacao.esta_totalmente_utilizada else f"parcialmente utilizada ({transacao.percentual_utilizado:.1f}%)"
        
        agendamentos_totalmente_conciliados = sum(1 for ag in agendamentos if ag.esta_totalmente_conciliado)
        agendamentos_parcialmente_conciliados = len(agendamentos) - agendamentos_totalmente_conciliados
        
        if conciliacao_proporcional:
            percentual_proporcional = (fator_proporcional * 100)
            mensagem_sucesso = f'Conciliação em massa PROPORCIONAL processada com sucesso! '
            mensagem_sucesso += f'{len(agendamentos)} agendamentos processados ({percentual_proporcional:.1f}% de cada). '
            mensagem_sucesso += f'R$ {valor_efetivo_conciliado/100:.2f} de R$ {valor_total_agendamentos/100:.2f} conciliados. '
            
            if agendamentos_totalmente_conciliados > 0:
                mensagem_sucesso += f'{agendamentos_totalmente_conciliados} agendamentos totalmente conciliados. '
            if agendamentos_parcialmente_conciliados > 0:
                mensagem_sucesso += f'{agendamentos_parcialmente_conciliados} agendamentos parcialmente conciliados. '
        else:
            if agendamentos_totalmente_conciliados == len(agendamentos):
                mensagem_sucesso = f'Conciliação em massa TOTAL processada com sucesso! {len(agendamentos)} agendamentos totalmente conciliados. '
            else:
                mensagem_sucesso = f'Conciliação em massa processada com sucesso! '
                if agendamentos_totalmente_conciliados > 0:
                    mensagem_sucesso += f'{agendamentos_totalmente_conciliados} agendamentos totalmente conciliados. '
                if agendamentos_parcialmente_conciliados > 0:
                    mensagem_sucesso += f'{agendamentos_parcialmente_conciliados} agendamentos parcialmente conciliados. '
        
        mensagem_sucesso += f'Transação {status_transacao}.'
        
        faturamentos_marcados_conciliados = 0
        for faturamento_id in faturamentos_conciliados:
            faturamento = FaturamentoModel.query.get(faturamento_id)
            if faturamento and faturamento.situacao_pagamento_id == 8:
                faturamentos_marcados_conciliados += 1
        
        lancamentos_marcados_conciliados = 0
        for lancamento_id in lancamentos_conciliados:
            lancamento_avulso = LancamentoAvulsoModel.query.get(lancamento_id)
            if lancamento_avulso and lancamento_avulso.situacao_pagamento_id == 8:
                lancamentos_marcados_conciliados += 1
        
        if faturamentos_marcados_conciliados > 0:
            mensagem_sucesso += f' {faturamentos_marcados_conciliados} faturamentos marcados como totalmente conciliados.'
        
        if lancamentos_marcados_conciliados > 0:
            mensagem_sucesso += f' {lancamentos_marcados_conciliados} lançamentos avulsos marcados como totalmente conciliados.'
      
        return jsonify({
            'success': True,
            'message': mensagem_sucesso,
            'dados': {
                'agendamentos_processados': len(agendamentos),
                'agendamentos_totalmente_conciliados': agendamentos_totalmente_conciliados,
                'agendamentos_parcialmente_conciliados': agendamentos_parcialmente_conciliados,
                'faturamentos_conciliados': len(faturamentos_conciliados),
                'lancamentos_conciliados': len(lancamentos_conciliados),
                'valor_total_agendamentos': valor_total_agendamentos,
                'valor_efetivo_conciliado': valor_efetivo_conciliado,
                'valor_transacao': valor_transacao_centavos,
                'valor_disponivel_transacao': valor_disponivel_transacao,
                'conciliacao_proporcional': conciliacao_proporcional,
                'fator_proporcional': fator_proporcional,
                'transacao_totalmente_utilizada': transacao.esta_totalmente_utilizada,
                'transacao_percentual_utilizado': float(transacao.percentual_utilizado),
                'transacao_valor_disponivel': transacao.valor_disponivel_100,
                'diferenca_valor': valor_transacao_centavos - valor_efetivo_conciliado,
                'agendamentos_detalhes': [
                    {
                        'id': ag.id,
                        'valor_total': ag.valor_total_100,
                        'valor_conciliado': ag.valor_conciliado_100,
                        'valor_pendente': ag.valor_pendente_conciliacao_100,
                        'percentual_conciliado': float(ag.percentual_conciliado),
                        'totalmente_conciliado': ag.esta_totalmente_conciliado,
                        'situacao_pagamento_id': ag.situacao_pagamento_id
                    } for ag in agendamentos
                ]
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
        
        transacao_id = data.get('transacao_id')
        agendamento_id = data.get('agendamento_id')
        observacoes = data.get('observacoes', '')

        
        if not transacao_id or not agendamento_id:
            return jsonify({
                'success': False,
                'message': 'Dados obrigatórios não fornecidos'
            }), 400
        
        from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx
        transacao = ImportacaoOfx.query.get(transacao_id)

        if not transacao:
            return jsonify({
                'success': False,
                'message': 'Transação não encontrada'
            }), 404
        
        agendamento = AgendamentoPagamentoModel.query.filter(
            AgendamentoPagamentoModel.id == agendamento_id,
            AgendamentoPagamentoModel.conta_bancaria_id == transacao.conta_bancaria_id
        ).first()
        if not agendamento:
            return jsonify({
                'success': False,
                'message': 'Agendamento não encontrado ou não pertence à mesma conta bancária'
            }), 404
        
        if transacao.conciliado and not transacao.conciliacao_parcial:
            return jsonify({
                'success': False,
                'message': 'Esta transação já foi totalmente conciliada'
            }), 400
        
        if agendamento.situacao_pagamento_id == 8:
            return jsonify({
                'success': False,
                'message': 'Este agendamento já foi totalmente conciliado'
            }), 400
            
        
        if agendamento.situacao_pagamento_id == 10:
            valor_agendamento_centavos = agendamento.valor_pendente_conciliacao_100
        else:
            valor_agendamento_centavos = agendamento.valor_total_100
            
        valor_disponivel_transacao = transacao.valor_disponivel_100
        
        if valor_agendamento_centavos > valor_disponivel_transacao:
            valor_a_conciliar = valor_disponivel_transacao
            conciliacao_parcial = True
            
            if valor_disponivel_transacao <= 0:
                valor_ja_utilizado = transacao.valor_utilizado_100 or 0
                valor_total_transacao = int(abs(transacao.valor * 100))
                
                return jsonify({
                    'success': False,
                    'message': f'Transação não possui valor disponível. '
                              f'Valor total da transação: R$ {valor_total_transacao/100:.2f}. '
                              f'Já utilizado: R$ {valor_ja_utilizado/100:.2f}.'
                }), 400
        else:
            valor_a_conciliar = valor_agendamento_centavos
            conciliacao_parcial = False
        
        tipo_movimentacao = 1 if transacao.valor > 0 else 2
        
        tipo_origem = None
        faturamento_id = None
        lancamento_avulso_id = None
        
        if agendamento.faturamento_id:
            tipo_origem = 'FATURAMENTO'
            faturamento_id = agendamento.faturamento_id
        elif agendamento.lancamento_avulso_id:
            tipo_origem = 'LANCAMENTO_AVULSO'
            lancamento_avulso_id = agendamento.lancamento_avulso_id
        
        valor_diferenca = int(abs(transacao.valor * 100)) - valor_a_conciliar
        
        from datetime import datetime
        nova_movimentacao = MovimentacaoFinanceiraModel(
            tipo_movimentacao=tipo_movimentacao,
            usuario_id=current_user.id,
            data_movimentacao=transacao.data_transacao,
            conta_bancaria_id=agendamento.conta_bancaria_id,
            valor_movimentacao_100=valor_a_conciliar,
            ativo=True,
            conciliacao_bancaria=True,
            
            importacao_ofx_id=transacao_id,
            agendamento_id=agendamento_id,
            
            conciliacao_fitid=transacao.fitid,
            conciliacao_valor_original=int(abs(transacao.valor * 100)),
            conciliacao_descricao_ofx=transacao.memo or transacao.descricao_limpa,
            conciliacao_data_transacao=transacao.data_transacao,
            conciliacao_tipo_movimento=transacao.tipo_movimento,
            
            conciliacao_data_processamento=datetime.now(),
            conciliacao_observacoes=f'{"INDIVIDUAL PARCIAL" if conciliacao_parcial else "INDIVIDUAL TOTAL"}: {observacoes}' if observacoes else f'{"Conciliação individual parcial" if conciliacao_parcial else "Conciliação individual total"}',
            
            conciliacao_faturamento_id=faturamento_id,
            conciliacao_lancamento_avulso_id=lancamento_avulso_id,
            conciliacao_tipo_origem=tipo_origem,
            
            conciliacao_valor_diferenca=valor_diferenca
        )
        
        db.session.add(nova_movimentacao)
        
        if not agendamento.adicionar_valor_conciliado(valor_a_conciliar):
            return jsonify({
                'success': False,
                'message': 'Erro interno: não foi possível adicionar valor conciliado ao agendamento'
            }), 500
        
        agendamento.situacao_pagamento_id = 8 if agendamento.esta_totalmente_conciliado else 10
        
        db.session.add(agendamento)
        
        if not transacao.adicionar_valor_utilizado(valor_a_conciliar):
            return jsonify({
                'success': False,
                'message': 'Erro interno: não foi possível atualizar valor utilizado da transação'
            }), 500
        
        if agendamento.situacao_pagamento_id == 8:
            if faturamento_id:
                faturamento = FaturamentoModel.query.get(faturamento_id)
                if faturamento:
                    agendamentos_faturamento = AgendamentoPagamentoModel.obter_agendamentos_por_faturamento(faturamento_id)
                    todos_conciliados = all(ag.esta_totalmente_conciliado for ag in agendamentos_faturamento)
                    
                    if todos_conciliados:
                        faturamento.situacao_pagamento_id = 8
                        db.session.add(faturamento)
            
            if lancamento_avulso_id:
                lancamento_avulso = LancamentoAvulsoModel.query.get(lancamento_avulso_id)
                if lancamento_avulso:
                    lancamento_avulso.situacao_pagamento_id = 8
                    db.session.add(lancamento_avulso)
        
        faturamentos_ids = []
        movimentacoes_ids = []
        
        if faturamento_id:
            faturamentos_ids.append(faturamento_id)
        
        db.session.flush()
        if nova_movimentacao.id:
            movimentacoes_ids.append(nova_movimentacao.id)
        
        lancamentos_avulsos_ids = []
        if lancamento_avulso_id:
            lancamentos_avulsos_ids.append(lancamento_avulso_id)
        
        sucesso_salvamento = ImportacaoOfxService.salvar_dados_conciliacao(
            transacao=transacao,
            tipo_conciliacao='AGENDAMENTO_INDIVIDUAL_PARCIAL' if conciliacao_parcial else 'AGENDAMENTO',
            agendamentos_ids=[agendamento_id],
            faturamentos_ids=faturamentos_ids,
            movimentacoes_ids=movimentacoes_ids,
            lancamentos_avulsos_ids=lancamentos_avulsos_ids,
            valor_agendamento=valor_a_conciliar,
            usuario_id=current_user.id,
            observacoes=f'{"INDIVIDUAL PARCIAL" if conciliacao_parcial else "INDIVIDUAL TOTAL"}: {observacoes}' if observacoes else f'{"Conciliação individual parcial" if conciliacao_parcial else "Conciliação individual total"}'
        )
        
        if not sucesso_salvamento:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Erro ao salvar dados de conciliação para reversão'
            }), 500
        
        transacao.pagamento_id = agendamento_id
        
        obs_conciliacao = f'Conciliado {"PARCIALMENTE" if conciliacao_parcial else "TOTALMENTE"} com agendamento'
        if conciliacao_parcial:
            obs_conciliacao += f' - {ValoresMonetarios.converter_float_brl_positivo(valor_a_conciliar/100)} de {ValoresMonetarios.converter_float_brl_positivo(valor_agendamento_centavos/100)}'
        
        if tipo_origem == 'FATURAMENTO':
            obs_conciliacao += f' | Faturamento: {agendamento.faturamento.codigo_faturamento if agendamento.faturamento else "N/A"}'
        elif tipo_origem == 'LANCAMENTO_AVULSO':
            obs_conciliacao += f' | Lançamento Avulso: {agendamento.lancamento_avulso.descricao if agendamento.lancamento_avulso else "N/A"}'
            
        transacao.observacoes_conciliacao = obs_conciliacao
        db.session.add(transacao)
        
        from sistema.models_views.financeiro.movimentacao_financeira.saldo_movimentacao_financeira_model import SaldoMovimentacaoFinanceiraModel
        
        saldo_conta = SaldoMovimentacaoFinanceiraModel.query.filter(
            SaldoMovimentacaoFinanceiraModel.conta_bancaria_id == agendamento.conta_bancaria_id,
            SaldoMovimentacaoFinanceiraModel.ativo == True,
            SaldoMovimentacaoFinanceiraModel.deletado == False
        ).first()
        
        if not saldo_conta:
            saldo_conta = SaldoMovimentacaoFinanceiraModel(
                data_movimentacao=transacao.data_transacao,
                valor_total_saldo_100=0,
                conta_bancaria_id=agendamento.conta_bancaria_id,
                ativo=True
            )
            db.session.add(saldo_conta)
        
        if tipo_movimentacao == 1:
            saldo_conta.valor_total_saldo_100 += valor_a_conciliar
        elif tipo_movimentacao == 2:
            saldo_conta.valor_total_saldo_100 -= valor_a_conciliar
        
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
        
        status_transacao = "totalmente utilizada" if transacao.esta_totalmente_utilizada else f"parcialmente utilizada ({transacao.percentual_utilizado:.1f}%)"
        
        if conciliacao_parcial:
            status_agendamento = "parcialmente conciliado" if agendamento.situacao_pagamento_id == 10 else "totalmente conciliado"
            mensagem_sucesso = f'Conciliação individual Parcial processada com sucesso! {ValoresMonetarios.converter_float_brl_positivo(valor_a_conciliar/100)} de {ValoresMonetarios.converter_float_brl_positivo(valor_agendamento_centavos/100)} conciliados. Agendamento {agendamento_id} {status_agendamento}. Transação {status_transacao}.'
        else:
            mensagem_sucesso = f'Conciliação individual Total processada com sucesso! Agendamento {agendamento_id} totalmente conciliado. Transação {status_transacao}.'
        
        if faturamento_id and agendamento.situacao_pagamento_id == 8:
            codigo_faturamento = agendamento.faturamento.codigo_faturamento if agendamento.faturamento else faturamento_id
            mensagem_sucesso += f' Faturamento {codigo_faturamento} também marcado como conciliado.'
        
        if lancamento_avulso_id and agendamento.situacao_pagamento_id == 8:
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
                'valor_diferenca': valor_diferenca,
                'valor_conciliado': valor_a_conciliar,
                'valor_agendamento_total': valor_agendamento_centavos,
                'conciliacao_parcial': conciliacao_parcial,
                'agendamento_totalmente_conciliado': agendamento.esta_totalmente_conciliado,
                'agendamento_percentual_conciliado': float(agendamento.percentual_conciliado),
                'agendamento_valor_pendente': agendamento.valor_pendente_conciliacao_100,
                'transacao_totalmente_utilizada': transacao.esta_totalmente_utilizada,
                'transacao_percentual_utilizado': float(transacao.percentual_utilizado),
                'transacao_valor_disponivel': transacao.valor_disponivel_100,
                'valor_utilizado_total': transacao.valor_utilizado_100
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao processar conciliação: {str(e)}'
        }), 500

@app.route("/api/processar-conciliacao-parcial", methods=["POST"])
@login_required
@requires_roles
def processar_conciliacao_parcial():
    """
    Endpoint para processar conciliação parcial entre uma transação OFX e um agendamento
    """
    try:
        data = request.get_json()
        
        transacao_id = data.get('transacao_id')
        agendamento_id = data.get('agendamento_id')
        valor_parcial = data.get('valor_parcial')
        observacoes = data.get('observacoes', '')

        if not transacao_id or not agendamento_id or not valor_parcial:
            return jsonify({
                'success': False,
                'message': 'Dados obrigatórios não fornecidos (transacao_id, agendamento_id, valor_parcial)'
            }), 400
        
        try:
            valor_parcial = int(valor_parcial)
            if valor_parcial <= 0:
                raise ValueError("Valor deve ser positivo")
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': 'Valor parcial deve ser um número positivo'
            }), 400

        from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx
        transacao = ImportacaoOfx.query.get(transacao_id)
        if not transacao:
            return jsonify({
                'success': False,
                'message': 'Transação não encontrada'
            }), 404

        agendamento = AgendamentoPagamentoModel.query.filter(
            AgendamentoPagamentoModel.id == agendamento_id,
            AgendamentoPagamentoModel.conta_bancaria_id == transacao.conta_bancaria_id
        ).first()
        if not agendamento:
            return jsonify({
                'success': False,
                'message': 'Agendamento não encontrado ou não pertence à mesma conta bancária'
            }), 404

        if transacao.conciliado and not transacao.conciliacao_parcial:
            return jsonify({
                'success': False,
                'message': 'Esta transação já foi totalmente conciliada'
            }), 400

        if agendamento.situacao_pagamento_id == 8:
            return jsonify({
                'success': False,
                'message': 'Este agendamento já está totalmente conciliado'
            }), 400
            
        if not agendamento.pode_conciliar_parcialmente:
            return jsonify({
                'success': False,
                'message': 'Este agendamento já está totalmente conciliado'
            }), 400

        if valor_parcial > agendamento.valor_pendente_conciliacao_100:
            return jsonify({
                'success': False,
                'message': f'Valor parcial (R$ {valor_parcial/100:.2f}) excede o valor pendente (R$ {agendamento.valor_pendente_conciliacao_100/100:.2f})'
            }), 400

        tipo_movimentacao = 1 if transacao.valor > 0 else 2
        
        tipo_origem = None
        faturamento_id = None
        lancamento_avulso_id = None
        
        if agendamento.faturamento_id:
            tipo_origem = 'FATURAMENTO'
            faturamento_id = agendamento.faturamento_id
        elif agendamento.lancamento_avulso_id:
            tipo_origem = 'LANCAMENTO_AVULSO'
            lancamento_avulso_id = agendamento.lancamento_avulso_id

        valor_diferenca = abs(transacao.valor * 100) - valor_parcial

        if not transacao.adicionar_valor_utilizado(valor_parcial):
            return jsonify({
                'success': False,
                'message': f'Valor parcial excede o valor disponível da transação (R$ {transacao.valor_disponivel:.2f})'
            }), 400

        from datetime import datetime
        nova_movimentacao = MovimentacaoFinanceiraModel(
            tipo_movimentacao=tipo_movimentacao,
            usuario_id=current_user.id,
            data_movimentacao=transacao.data_transacao,
            conta_bancaria_id=agendamento.conta_bancaria_id,
            valor_movimentacao_100=valor_parcial,
            ativo=True,
            conciliacao_bancaria=True,
            
            importacao_ofx_id=transacao_id,
            agendamento_id=agendamento_id,
            
            conciliacao_fitid=transacao.fitid,
            conciliacao_valor_original=int(abs(transacao.valor * 100)),
            conciliacao_descricao_ofx=transacao.memo or transacao.descricao_limpa,
            conciliacao_data_transacao=transacao.data_transacao,
            conciliacao_tipo_movimento=transacao.tipo_movimento,
            
            conciliacao_data_processamento=datetime.now(),
            conciliacao_observacoes=f"CONCILIAÇÃO PARCIAL: {observacoes}",
            
            conciliacao_faturamento_id=faturamento_id,
            conciliacao_lancamento_avulso_id=lancamento_avulso_id,
            conciliacao_tipo_origem=tipo_origem,
            
            conciliacao_valor_diferenca=valor_diferenca
        )
        
        db.session.add(nova_movimentacao)

        if not agendamento.adicionar_valor_conciliado(valor_parcial):
            return jsonify({
                'success': False,
                'message': 'Erro interno: não foi possível adicionar valor conciliado'
            }), 500

        if agendamento.esta_totalmente_conciliado:
            agendamento.situacao_pagamento_id = 8
        else:
            agendamento.situacao_pagamento_id = 10

        db.session.add(agendamento)

        if agendamento.esta_totalmente_conciliado:
            agendamento.situacao_pagamento_id = 8
            
            if faturamento_id:
                faturamento = FaturamentoModel.query.get(faturamento_id)
                if faturamento:
                    agendamentos_faturamento = AgendamentoPagamentoModel.obter_agendamentos_por_faturamento(faturamento_id)
                    todos_conciliados = all(ag.esta_totalmente_conciliado for ag in agendamentos_faturamento)
                    
                    if todos_conciliados:
                        faturamento.situacao_pagamento_id = 8
                        db.session.add(faturamento)
            
            if lancamento_avulso_id:
                lancamento_avulso = LancamentoAvulsoModel.query.get(lancamento_avulso_id)
                if lancamento_avulso:
                    lancamento_avulso.situacao_pagamento_id = 8
                    db.session.add(lancamento_avulso)

        faturamentos_ids = []
        movimentacoes_ids = []
        
        if faturamento_id:
            faturamentos_ids.append(faturamento_id)
        
        db.session.flush()
        if nova_movimentacao.id:
            movimentacoes_ids.append(nova_movimentacao.id)

        lancamentos_avulsos_ids = []
        if lancamento_avulso_id:
            lancamentos_avulsos_ids.append(lancamento_avulso_id)

        sucesso_salvamento = ImportacaoOfxService.salvar_dados_conciliacao(
            transacao=transacao,
            tipo_conciliacao='AGENDAMENTO_PARCIAL',
            agendamentos_ids=[agendamento_id],
            faturamentos_ids=faturamentos_ids,
            movimentacoes_ids=movimentacoes_ids,
            lancamentos_avulsos_ids=lancamentos_avulsos_ids,
            valor_agendamento=valor_parcial,
            usuario_id=current_user.id,
            observacoes=f"PARCIAL: {observacoes}"
        )

        if not sucesso_salvamento:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Erro ao salvar dados de conciliação para reversão'
            }), 500

        transacao.pagamento_id = agendamento_id
        
        obs_conciliacao = f'Conciliação PARCIAL - R$ {valor_parcial/100:.2f} de R$ {agendamento.valor_total:.2f}'
        if tipo_origem == 'FATURAMENTO':
            obs_conciliacao += f' | Faturamento: {agendamento.faturamento.codigo_faturamento if agendamento.faturamento else "N/A"}'
        elif tipo_origem == 'LANCAMENTO_AVULSO':
            obs_conciliacao += f' | Lançamento Avulso: {agendamento.lancamento_avulso.descricao if agendamento.lancamento_avulso else "N/A"}'
            
        transacao.observacoes_conciliacao = obs_conciliacao
        db.session.add(transacao)

        from sistema.models_views.financeiro.movimentacao_financeira.saldo_movimentacao_financeira_model import SaldoMovimentacaoFinanceiraModel
        
        saldo_conta = SaldoMovimentacaoFinanceiraModel.query.filter(
            SaldoMovimentacaoFinanceiraModel.conta_bancaria_id == agendamento.conta_bancaria_id,
            SaldoMovimentacaoFinanceiraModel.ativo == True,
            SaldoMovimentacaoFinanceiraModel.deletado == False
        ).first()
        
        if not saldo_conta:
            saldo_conta = SaldoMovimentacaoFinanceiraModel(
                data_movimentacao=transacao.data_transacao,
                valor_total_saldo_100=0,
                conta_bancaria_id=agendamento.conta_bancaria_id,
                ativo=True
            )
            db.session.add(saldo_conta)
        
        if tipo_movimentacao == 1:
            saldo_conta.valor_total_saldo_100 += valor_parcial
        elif tipo_movimentacao == 2:
            saldo_conta.valor_total_saldo_100 -= valor_parcial
        
        saldo_conta.data_movimentacao = DataHora.obter_data_atual_padrao_en()
        db.session.add(saldo_conta)

        db.session.commit()

        acao = TipoAcaoEnum.CADASTRO
        PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
            current_user.id,
            acao,
            acao.pontos,
            modulo='conciliacao_bancaria_parcial'
        )

        status_agendamento = "totalmente conciliado" if agendamento.esta_totalmente_conciliado else f"parcialmente conciliado ({agendamento.percentual_conciliado:.1f}%)"
        mensagem_sucesso = f'Conciliação parcial processada! {ValoresMonetarios.converter_float_brl_positivo(valor_parcial/100)} conciliados. Agendamento {agendamento_id} {status_agendamento}.'

        return jsonify({
            'success': True,
            'message': mensagem_sucesso,
            'dados': {
                'agendamento_id': agendamento_id,
                'faturamento_id': faturamento_id,
                'lancamento_avulso_id': lancamento_avulso_id,
                'tipo_origem': tipo_origem,
                'valor_parcial_conciliado': valor_parcial,
                'valor_diferenca': valor_diferenca,
                'agendamento_totalmente_conciliado': agendamento.esta_totalmente_conciliado,
                'percentual_conciliado': float(agendamento.percentual_conciliado),
                'valor_pendente': agendamento.valor_pendente_conciliacao_100,
                'valor_total': agendamento.valor_total_100,
                'transacao_totalmente_utilizada': transacao.esta_totalmente_utilizada,
                'transacao_percentual_utilizado': float(transacao.percentual_utilizado),
                'transacao_valor_disponivel': transacao.valor_disponivel_100,
                'valor_utilizado_total': transacao.valor_utilizado_100
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao processar conciliação parcial: {str(e)}'
        }), 500

@app.route("/api/detalhes-conciliacao/<int:transacao_id>", methods=["GET"])
@login_required
@requires_roles
def obter_detalhes_conciliacao(transacao_id):
    """
    Endpoint para obter detalhes de uma conciliação específica
    """
    try:
        from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx
        
        transacao = ImportacaoOfx.query.get(transacao_id)
        if not transacao:
            return jsonify({
                'success': False,
                'error': 'Transação não encontrada'
            }), 404
        
        if not transacao.conciliado and not transacao.conciliacao_parcial:
            return jsonify({
                'success': False,
                'error': 'Transação não está conciliada'
            }), 400
        
        detalhes = {
            'tipo_conciliacao': 'Não especificado',
            'data_conciliacao': None,
            'observacoes': None,
            'agendamentos': [],
            'movimentacoes': [],
            'impacto_saldo': None
        }
        
        movimentacoes = MovimentacaoFinanceiraModel.query.filter(
            MovimentacaoFinanceiraModel.importacao_ofx_id == transacao_id,
            MovimentacaoFinanceiraModel.ativo == True
        ).all()
        
        agendamentos_ids_set = set()
        
        for mov in movimentacoes:
            if mov.agendamento_id:
                agendamentos_ids_set.add(mov.agendamento_id)
            
            conta_nome = mov.conta_bancaria.identificacao if mov.conta_bancaria else 'N/A'
            
            detalhes['movimentacoes'].append({
                'id': mov.id,
                'data': mov.data_movimentacao.strftime('%d/%m/%Y') if mov.data_movimentacao else 'N/A',
                'valor': ValoresMonetarios.converter_float_brl_positivo(mov.valor_movimentacao_100 / 100),
                'conta': conta_nome
            })
        
        if agendamentos_ids_set:
            agendamentos = AgendamentoPagamentoModel.query.filter(
                AgendamentoPagamentoModel.id.in_(list(agendamentos_ids_set))
            ).all()
            
            for agendamento in agendamentos:
                tipo_origem = ''
                if agendamento.faturamento_id:
                    tipo_origem = 'Faturamento'
                elif agendamento.lancamento_avulso_id:
                    tipo_origem = 'Agendamento de lançamento avulso'
                else:
                    tipo_origem = 'Nova movimentação na conciliação'
                
                codigo = ''
                
                if agendamento.faturamento_id and agendamento.faturamento:
                    codigo = agendamento.faturamento.codigo_faturamento
                
                if agendamento.lancamento_avulso_id and agendamento.lancamento_avulso:
                    codigo = agendamento.lancamento_avulso_id
                
                valor_conciliado_transacao = sum(
                    mov.valor_movimentacao_100 
                    for mov in movimentacoes 
                    if mov.agendamento_id == agendamento.id
                )
                
                detalhes['agendamentos'].append({
                    'id': agendamento.id,
                    'tipo': tipo_origem,
                    'codigo': codigo,
                    'valor': ValoresMonetarios.converter_float_brl_positivo(valor_conciliado_transacao / 100),
                    'observacoes': f'{tipo_origem} {codigo}' if codigo else tipo_origem
                })
        
        if transacao.dados_conciliacao_json:
            dados_json = transacao.dados_conciliacao_json
            detalhes['tipo_conciliacao'] = dados_json.get('tipo_conciliacao', 'Não especificado').replace('_', ' ').title()
            if dados_json.get('observacoes'):
                detalhes['observacoes'] = dados_json.get('observacoes')
        
        if transacao.data_conciliacao:
            detalhes['data_conciliacao'] = transacao.data_conciliacao.strftime('%d/%m/%Y às %H:%M:%S')
        
        valor_utilizado = transacao.valor_utilizado_100 or int(abs(transacao.valor * 100))
        detalhes['impacto_saldo'] = ValoresMonetarios.converter_float_brl_positivo(valor_utilizado / 100)
        
        if transacao.observacoes_conciliacao:
            detalhes['observacoes'] = transacao.observacoes_conciliacao
        
        return jsonify({
            'success': True,
            'detalhes': detalhes
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro interno do servidor: {str(e)}'
        }), 500


@app.route("/api/salvar-nova-movimentacao", methods=["POST"])
@login_required
@requires_roles
def salvar_nova_movimentacao():
    """
    Endpoint simplificado para salvar nova movimentação via AJAX (seguindo padrão cadastrar_extrator)
    """
    try:
        transacao_ofx_id = request.form.get('transacao_ofx_id')
        valor_transacao_ofx = request.form.get('valor_transacao_ofx')
        descricao = request.form.get('descricao', '').strip()
        data_vencimento = request.form.get('data_vencimento')
        data_competencia = request.form.get('data_competencia')
        conta_bancaria_id = request.form.get('conta_bancaria_id')
        pessoa_financeiro_id = request.form.get('pessoa_financeiro_id')
        categorias_json = request.form.get('categorias_json', '[]')
        
        centros_custo_json = request.form.get('centros_custo_json', '[]')
        valores_detalhados_ativo = request.form.get('valores_detalhados_ativo', 'false').lower() == 'true'
        parcelas_json = request.form.get('parcelas_json', '[]')
        parcelamento_ativo = len(parcelas_json.strip()) > 2 and parcelas_json != '[]'
        
        if not transacao_ofx_id:
            return jsonify({'erro': True, 'mensagem': 'ID da transação OFX não fornecido'}), 400
            
        transacao = ImportacaoOfx.query.get(transacao_ofx_id)
        if not transacao:
            return jsonify({'erro': True, 'mensagem': 'Transação OFX não encontrada'}), 404
            
        if transacao.conciliado:
            return jsonify({'erro': True, 'mensagem': 'Esta transação já foi conciliada'}), 400

        campos = {
            "descricao": ["Descrição", descricao],
            "data_vencimento": ["Data de Vencimento", data_vencimento],
            "conta_bancaria_id": ["Conta Bancária", conta_bancaria_id],
            "pessoa_financeiro_id": ["Beneficiário", pessoa_financeiro_id],
            "categorias_json": ["Categorias", categorias_json]
        }

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
        gravar_banco = "validado" in validacao_campos_obrigatorios

        if not gravar_banco:
            return jsonify({
                'erro': True, 
                'mensagem': 'Campos obrigatórios não preenchidos',
                'campos_obrigatorios': validacao_campos_obrigatorios
            }), 400

        try:
            data_vencimento_obj = datetime.strptime(data_vencimento, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'erro': True, 'mensagem': 'Data de vencimento inválida'}), 400

        data_competencia_obj = None
        if data_competencia:
            try:
                data_competencia_obj = datetime.strptime(f"01/{data_competencia}", '%d/%m/%Y').date()
            except ValueError:
                return jsonify({'erro': True, 'mensagem': 'Data de competência inválida. Use o formato MM/AAAA'}), 400

        try:
            categorias = json.loads(categorias_json)
            if not isinstance(categorias, list) or len(categorias) == 0:
                return jsonify({'erro': True, 'mensagem': 'Pelo menos uma categoria deve ser informada'}), 400
        except json.JSONDecodeError:
            return jsonify({'erro': True, 'mensagem': 'Formato de categorias inválido'}), 400

        valor_centavos = int(abs(transacao.valor) * 100)
        
        eh_receita = transacao.valor > 0
        tipo_movimentacao_lancamento = 1 if eh_receita else 2

        lancamento_avulso = LancamentoAvulsoModel(
            tipo_movimentacao=tipo_movimentacao_lancamento,
            descricao=descricao,
            valor_movimentacao_100=valor_centavos,
            usuario_id=current_user.id,
            situacao_pagamento_id=8
        )
        db.session.add(lancamento_avulso)
        db.session.flush()

        categorias_processadas = []
        for cat in categorias:
            categoria_obj = PlanoContaModel.buscar_por_codigo(cat.get('categoria', '').split(' - ')[0])
            categoria_formatada = {
                'categoria': cat.get('categoria', ''),
                'categoria_id': categoria_obj.id if categoria_obj else None,
                'valor': cat.get('valor', 0),
                'detalhamento': cat.get('detalhamento', ''),
                'referencia': cat.get('referencia', '')
            }
            categorias_processadas.append(categoria_formatada)

        centros_custo_processados = []
        if valores_detalhados_ativo:
            try:
                centros_custo = json.loads(centros_custo_json)
                if isinstance(centros_custo, list):
                    for centro in centros_custo:
                        centro_formatado = {
                            'centro': centro.get('centro', ''),
                            'percentual': centro.get('percentual', ''),
                            'valor': centro.get('valor', 0)
                        }
                        centros_custo_processados.append(centro_formatado)
            except json.JSONDecodeError:
                pass

        parcelas_processadas = []
        try:
            parcelas = json.loads(parcelas_json)
            if isinstance(parcelas, list):
                for parcela in parcelas:
                    parcela_formatada = {
                        'valor': parcela.get('valor', 0),
                        'vencimento': parcela.get('vencimento', ''),
                        'descricao': parcela.get('descricao', ''),
                        'referencia': parcela.get('referencia', '')
                    }
                    parcelas_processadas.append(parcela_formatada)
        except json.JSONDecodeError:
            pass

        agendamento = AgendamentoPagamentoModel(
            lancamento_avulso_id=lancamento_avulso.id,
            pessoa_financeiro_id=int(pessoa_financeiro_id),
            data_vencimento=data_vencimento_obj,
            data_competencia=data_competencia_obj,
            valor_total_100=valor_centavos,
            descricao=descricao,
            categorias_json=categorias_processadas,
            centros_custo_json=centros_custo_processados,
            parcelamento_ativo=parcelamento_ativo,
            numero_parcelas=len(parcelas_processadas) if parcelamento_ativo else None,
            dias_entre_parcelas=30,
            conta_bancaria_id=int(conta_bancaria_id),
            situacao_pagamento_id=8
        )
        db.session.add(agendamento)
        db.session.flush()

        if parcelamento_ativo and parcelas_processadas:
            for i, parcela in enumerate(parcelas_processadas, 1):
                try:
                    data_vencimento_parcela = datetime.strptime(parcela.get('vencimento', ''), '%Y-%m-%d').date() if parcela.get('vencimento') else data_vencimento_obj
                except ValueError:
                    data_vencimento_parcela = data_vencimento_obj
                
                parcela_obj = ParcelaCategorizacaoModel(
                    agendamento_id=agendamento.id,
                    numero_parcela=i,
                    data_vencimento=data_vencimento_parcela,
                    valor_parcela=parcela.get('valor', 0),
                    descricao=parcela.get('descricao', ''),
                    referencia=parcela.get('referencia', ''),
                    situacao_pagamento_id=8
                )
                db.session.add(parcela_obj)

        tipo_movimentacao = 1 if transacao.valor > 0 else 2
        movimentacao_financeira = MovimentacaoFinanceiraModel(
            tipo_movimentacao=tipo_movimentacao,
            usuario_id=current_user.id,
            data_movimentacao=transacao.data_transacao,
            conta_bancaria_id=agendamento.conta_bancaria_id,
            valor_movimentacao_100=agendamento.valor_total_100,
            ativo=True,
            conciliacao_bancaria=True,
            importacao_ofx_id=transacao_ofx_id,
            agendamento_id=agendamento.id,
            conciliacao_fitid=transacao.fitid,
            conciliacao_valor_original=int(abs(transacao.valor * 100)),
            conciliacao_descricao_ofx=transacao.memo or transacao.descricao_limpa,
            conciliacao_data_transacao=transacao.data_transacao,
            conciliacao_tipo_movimento=transacao.tipo_movimento,
            conciliacao_data_processamento=datetime.now(),
            conciliacao_observacoes=f'Nova movimentação criada: {descricao}',
            conciliacao_lancamento_avulso_id=lancamento_avulso.id,
            conciliacao_tipo_origem='LANCAMENTO_AVULSO'
        )
        db.session.add(movimentacao_financeira)
        db.session.flush()

        sucesso_salvamento = ImportacaoOfxService.salvar_dados_conciliacao(
            transacao=transacao,
            tipo_conciliacao='NOVA_MOVIMENTACAO',
            agendamentos_ids=[agendamento.id],
            faturamentos_ids=[],
            movimentacoes_ids=[movimentacao_financeira.id],
            lancamentos_avulsos_ids=[lancamento_avulso.id],
            valor_agendamento=agendamento.valor_total_100,
            usuario_id=current_user.id,
            observacoes=f'Nova movimentação criada: {descricao}'
        )

        if not sucesso_salvamento:
            db.session.rollback()
            return jsonify({'erro': True, 'mensagem': 'Erro ao salvar dados de conciliação'}), 500

        saldo_conta = SaldoMovimentacaoFinanceiraModel.query.filter_by(
            conta_bancaria_id=agendamento.conta_bancaria_id,
            ativo=True,
            deletado=False
        ).first()

        if not saldo_conta:
            saldo_conta = SaldoMovimentacaoFinanceiraModel(
                data_movimentacao=transacao.data_transacao,
                valor_total_saldo_100=0,
                conta_bancaria_id=agendamento.conta_bancaria_id,
                ativo=True
            )
            db.session.add(saldo_conta)

        if tipo_movimentacao == 1:
            saldo_conta.valor_total_saldo_100 += agendamento.valor_total_100
        else:
            saldo_conta.valor_total_saldo_100 -= agendamento.valor_total_100
        
        saldo_conta.data_movimentacao = DataHora.obter_data_atual_padrao_en()

        PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
            current_user.id,
            TipoAcaoEnum.CADASTRO,
            TipoAcaoEnum.CADASTRO.pontos,
            modulo="nova_movimentacao_conciliacao"
        )

        db.session.commit()
        
        mensagem_sucesso = 'Nova movimentação criada e conciliada com sucesso!'
        if valores_detalhados_ativo and centros_custo_processados:
            mensagem_sucesso += f' Processados {len(centros_custo_processados)} centros de custo.'
        if parcelamento_ativo and parcelas_processadas:
            mensagem_sucesso += f' Criadas {len(parcelas_processadas)} parcelas.'
        
        return jsonify({
            'erro': False,
            'mensagem': mensagem_sucesso,
            'transacao_id': transacao_ofx_id,
            'detalhes': {
                'categorias': len(categorias_processadas),
                'centros_custo': len(centros_custo_processados) if valores_detalhados_ativo else 0,
                'parcelas': len(parcelas_processadas) if parcelamento_ativo else 0,
                'parcelamento_ativo': parcelamento_ativo,
                'valores_detalhados_ativo': valores_detalhados_ativo
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': True, 'mensagem': f'Erro ao processar transação: {str(e)}'}), 500

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
        
        transacao = ImportacaoOfx.query.get(transacao_id)
        if not transacao:
            return jsonify({
                'success': False,
                'message': 'Transação não encontrada'
            }), 404
        
        if not transacao.dados_conciliacao_json:
            return jsonify({
                'success': False,
                'message': 'Esta transação não pode ser revertida (não possui dados de reversão)'
            }), 400
        
        sucesso, mensagem = ImportacaoOfxService.reverter_conciliacao(transacao)
        
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


@app.route("/financeiro/listagem-movimentacao-financeira", methods=["GET", "POST"])
@login_required
@requires_roles
def conciliacao_contas_bancarias():
    conta_selecionada_id = request.args.get("conta_bancaria_id", type=int)

    if not conta_selecionada_id:
        conta_principal = ContaBancariaModel.verifica_conta_bancaria_principal()
        if conta_principal:
            conta_selecionada_id = conta_principal.id

    if conta_selecionada_id:
        stats_transacoes = ImportacaoOfxService.obter_estatisticas_transacoes(conta_bancaria_id=conta_selecionada_id)

        transacoes_conta = ImportacaoOfx.query.filter_by(
            conta_bancaria_id=conta_selecionada_id,
            conciliado=False,
            ofx_deletada=False,
            deletado=False
        ).count()
        transacoes_nao_conciliadas = transacoes_conta
    else:
        stats_transacoes = ImportacaoOfxService.obter_estatisticas_transacoes()
        transacoes_nao_conciliadas = stats_transacoes.get('nao_conciliadas', 0)

    movimentacoes = MovimentacaoFinanceiraModel.listagem_movimentacoes_financeiras_por_conta(conta_selecionada_id)
    contas_bancarias = ContaBancariaModel.obter_contas_bancarias_ativas()
    saldo_disponivel = SaldoMovimentacaoFinanceiraModel.obter_registro_saldo_por_conta_bancaria(conta_selecionada_id)
    
    for conta in contas_bancarias:
        conta.saldo_total = SaldoMovimentacaoFinanceiraModel.obter_registro_saldo_por_conta_bancaria(conta.id)
    
    saldo_total_contas = sum(conta.saldo_total for conta in contas_bancarias if conta.saldo_total is not None)
    
    a_pagar_frete = FretePagarModel.obter_valor_total_a_pagar()
    a_pagar_fornecedor = FornecedorPagarModel.obter_valor_total_a_pagar()
    a_pagar_extrator = ExtratorPagarModel.obter_valor_total_a_pagar()

    valor_total_pagar = int(a_pagar_frete + a_pagar_fornecedor + a_pagar_extrator)

    total_a_receber = RegistroOperacionalModel.obter_valor_total_a_receber_por_conta(conta_selecionada_id)
    total_recebido = MovimentacaoFinanceiraModel.obter_valor_total_recebidos(conta_selecionada_id)

    valor_total_pago = MovimentacaoFinanceiraModel.obter_valor_total_saidas(conta_selecionada_id)

    return render_template(
        "financeiro/contas_bancarias/contas_bancarias_novo.html",
        movimentacoes=movimentacoes,
        conta_selecionada_id=conta_selecionada_id,
        dados_corretos=request.form,
        saldo_disponivel=saldo_disponivel,
        valor_total_pagar=valor_total_pagar,
        contas_bancarias=contas_bancarias,
        saldo_total_contas=saldo_total_contas,
        valor_total_pago=valor_total_pago,
        total_a_receber=total_a_receber,
        total_recebido=total_recebido,
        transacoes_nao_conciliadas=transacoes_nao_conciliadas,
        conta_id_para_link=conta_selecionada_id
    )
    

@app.route("/financeiro/movimentacoes-financeiras/listagem-ofx")
@login_required
@requires_roles
def listagem_ofx():
    batch_id = session.get('current_batch_id') or ImportacaoOfxService.obter_ultimo_batch_importacao()

    if not batch_id:
        flash(('Nenhum arquivo OFX foi importado. Importe um arquivo primeiro.', 'warning'))
        return redirect(url_for('importar_ofx'))
    
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
    
    conciliado_val = filtro_conciliado == 'sim'
    transacoes = ImportacaoOfx.query.filter_by(conciliado=conciliado_val)
    
    transacoes = transacoes.filter(ImportacaoOfx.ofx_deletada == False)
    
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
            transacoes = transacoes.filter(ImportacaoOfx.valor > 0)
        elif filtro_tipo_movimentacao == 'saida':
            transacoes = transacoes.filter(ImportacaoOfx.valor < 0)

    total_transacoes = transacoes.count()
    transacoes = transacoes.order_by(ImportacaoOfx.data_transacao.desc(), ImportacaoOfx.id.desc())\
                           .offset((pagina-1)*por_pagina)\
                           .limit(por_pagina)\
                           .all()
    
    total_paginas = (total_transacoes // por_pagina) + (1 if total_transacoes % por_pagina else 0)
    
    resumo_bd = ImportacaoOfxService.obter_resumo_importacao(
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
    pessoas_financeiro = PessoaFinanceiroModel.listar_pessoas_ativas()
    for p in pessoas_financeiro:
        if p.numero_documento and len(p.numero_documento.strip()) > 0:
            p.documento_formatado = ValidaDocs.insere_pontuacao_cnpj(p.numero_documento) if len(p.numero_documento) == 14 else ValidaDocs.insere_pontuacao_cpf(p.numero_documento)
        else:
            p.documento_formatado = "N/A"
    
    sugestoes_por_transacao = {}
    for transacao in transacoes:
        if not transacao.conciliado:
            valor_transacao = int(abs(transacao.valor * 100))
            eh_credito = transacao.valor > 0
            
            sugestoes_formatadas = AgendamentoPagamentoModel.obter_sugestoes_conciliacao_formatadas(
                valor_transacao=valor_transacao,
                eh_credito=eh_credito,
            )
                        
            sugestoes_por_transacao[transacao.id] = sugestoes_formatadas
    
    agendamentos_por_transacao = {}
    for transacao in transacoes:
        if not transacao.conciliado:
            eh_credito = transacao.valor > 0
            
            agendamentos_formatados = AgendamentoPagamentoModel.obter_agendamentos_recentes_formatados(eh_credito)
                        
            agendamentos_por_transacao[transacao.id] = agendamentos_formatados
    
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


        
def processar_sugestao_individual(transacao_id):
    """Processa sugestão para uma única transação (funcionalidade original)"""
    transacao = ImportacaoOfx.query.get(transacao_id)
    if not transacao:
        return jsonify({
            'success': False,
            'error': 'Transação não encontrada',
            'sugestoes': []
        }), 404
    
    sugestoes = AgendamentoPagamentoModel.buscar_sugestoes_ofx(
        valor=transacao.valor,
        tipo_movimento=transacao.tipo_movimento,
        conta_bancaria_id=transacao.conta_bancaria_id
    )
    
    sugestoes_formatadas = formatar_sugestoes_resposta(sugestoes)
    
    return jsonify({
        'success': True,
        'sugestoes': sugestoes_formatadas,
        'total': len(sugestoes_formatadas)
    })


def processar_sugestoes_lote(transacoes_ids):
    """Processa sugestões para múltiplas transações (nova funcionalidade otimizada)"""
    if not transacoes_ids or len(transacoes_ids) == 0:
        return jsonify({
            'success': False,
            'error': 'Lista de IDs de transação não pode estar vazia',
            'sugestoes_por_transacao': {}
        }), 400
    
    transacoes = ImportacaoOfx.query.filter(
        ImportacaoOfx.id.in_(transacoes_ids)
    ).all()
    
    if not transacoes:
        return jsonify({
            'success': False,
            'error': 'Nenhuma transação encontrada',
            'sugestoes_por_transacao': {}
        }), 404
    
    transacoes_dict = {str(t.id): t for t in transacoes}
    
    sugestoes_por_transacao = {}
    
    for transacao_id_str in map(str, transacoes_ids):
        transacao = transacoes_dict.get(transacao_id_str)
        
        if transacao:
            sugestoes = AgendamentoPagamentoModel.buscar_sugestoes_ofx(
                valor=transacao.valor,
                tipo_movimento=transacao.tipo_movimento,
                conta_bancaria_id=transacao.conta_bancaria_id
            )
            
            sugestoes_formatadas = formatar_sugestoes_resposta(sugestoes)
            sugestoes_por_transacao[transacao_id_str] = sugestoes_formatadas
        else:
            sugestoes_por_transacao[transacao_id_str] = []
    
    return jsonify({
        'success': True,
        'sugestoes_por_transacao': sugestoes_por_transacao,
        'total_transacoes': len(transacoes_ids),
        'transacoes_processadas': len([t for t in sugestoes_por_transacao.values() if len(t) > 0])
    })


def formatar_sugestoes_resposta(sugestoes):
    """Formata as sugestões para resposta JSON (código reutilizado)"""
    sugestoes_formatadas = []
    
    for sugestao in sugestoes:
        categorias_lista = []
        if sugestao.categorias_json:
            try:
                if isinstance(sugestao.categorias_json, str):
                    categorias_data = json.loads(sugestao.categorias_json)
                else:
                    categorias_data = sugestao.categorias_json
                
                for categoria_item in categorias_data:
                    categoria_nome = categoria_item.get('categoria', 'Categoria não identificada')
                    categorias_lista.append({
                        'categoria': categoria_nome,
                        'valor': categoria_item.get('valor', 0)
                    })
            except Exception as e:
                pass
        
        origem = 'Lançamento Avulso'
        codigo_origem = 'Lançamento Avulso'
        
        if sugestao.faturamento:
            origem = 'Faturamento'
            codigo_origem = sugestao.faturamento.codigo_faturamento
        
        sugestao_formatada = {
            'id': sugestao.id,
            'descricao': sugestao.descricao or sugestao.referencia or 'Sem descrição',
            'valor_formatado': formatar_float_para_brl(sugestao.valor_total_100),
            'data_vencimento': sugestao.data_vencimento.strftime('%d/%m/%Y') if sugestao.data_vencimento else 'N/A',
            'pessoa_nome': sugestao.pessoa_financeiro.identificacao if sugestao.pessoa_financeiro else 'N/A',
            'origem': origem,
            'codigo_origem': codigo_origem,
            'categorias_json': categorias_lista,
            'faturamento': sugestao.faturamento_id is not None
        }
        sugestoes_formatadas.append(sugestao_formatada)
    
    return sugestoes_formatadas