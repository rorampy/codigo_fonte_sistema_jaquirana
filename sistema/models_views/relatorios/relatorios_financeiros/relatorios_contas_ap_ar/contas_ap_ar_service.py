"""
Service centralizado para Contas a Pagar (AP) e Contas a Receber (AR).

Lógica IDÊNTICA ao DRE para garantir consistência de valores:
- Custos operacionais (2.01.01-2.01.04): tabelas operacionais
- Despesas/Receitas via agendamentos: categorias_json com situação 6/8/9

Regras:
- AP = tipo 2 (Despesa)
- AR = tipo 1 (Receita)  
- Valores em centavos (*_100)
"""

import json as json_lib
from datetime import date
from sqlalchemy import func, and_, or_

from sistema import db
from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
from sistema.models_views.financeiro.operacional.categorizar_fatura.categorizacao_model import AgendamentoPagamentoModel
from sistema.models_views.financeiro.operacional.categorizar_fatura.parcela_categorizacao.parcela_categorizacao_model import ParcelaCategorizacaoModel
from sistema.models_views.configuracoes_gerais.situacao_pagamento.situacao_pagamento_model import SituacaoPagamentoModel
from sistema.models_views.gerenciar.pessoa_financeiro.pessoa_financeiro_model import PessoaFinanceiroModel
from sistema.models_views.financeiro.lancamento_avulso.lancamento_avulso_model import LancamentoAvulsoModel
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.controle_carga.solicitacao_nf.carga_model import CargaModel
from sistema.models_views.faturamento.cargas_a_receber.nf_complementar.nf_complementar_model import NfComplementarModel
from sistema.models_views.faturamento.cargas_a_faturar.fornecedor.fornecedor_a_pagar_model import FornecedorPagarModel
from sistema.models_views.faturamento.cargas_a_faturar.transportadora.frete_a_pagar_model import FretePagarModel
from sistema.models_views.faturamento.cargas_a_faturar.extrator.extrator_a_pagar_model import ExtratorPagarModel
from sistema.models_views.faturamento.cargas_a_faturar.comissionado.comissionado_a_pagar_model import ComissionadoPagarModel


# =============================================================================
# CONSTANTES
# =============================================================================

DIRECAO_AP = 2
DIRECAO_AR = 1
SITUACOES_PENDENTES = [5, 6, 7]
SITUACOES_LIQUIDADAS = [8, 9]
SITUACOES_RECEBIDAS_AR = [3, 8, 9]
SITUACAO_VENDA_PENDENTE = 2
SITUACAO_VENDA_RECEBIDA = 3

# Categorias automáticas - buscadas diretamente das tabelas operacionais (igual DRE)
CATEGORIAS_AUTOMATICAS_AP = {
    '2.01.01': {'model': 'FornecedorPagarModel', 'campo_valor': 'valor_total_a_pagar_100', 'campo_data': 'data_entrega_ticket', 'filtro_operacional': 'solicitacao_id', 'descricao': 'Compra de Madeira'},
    '2.01.02': {'model': 'FretePagarModel', 'campo_valor': 'valor_total_a_pagar_100', 'campo_data': 'data_entrega_ticket', 'filtro_operacional': 'solicitacao_id', 'descricao': 'Fretes'},
    '2.01.03': {'model': 'ExtratorPagarModel', 'campo_valor': 'valor_total_a_pagar_100', 'campo_data': 'data_entrega_ticket', 'filtro_operacional': 'solicitacao_id', 'descricao': 'Extração de Madeira'},
    '2.01.04': {'model': 'ComissionadoPagarModel', 'campo_valor': 'valor_total_a_pagar_100', 'campo_data': 'data_entrega_ticket', 'filtro_operacional': 'solicitacao_id', 'descricao': 'Comissões'},
}

CATEGORIAS_AUTOMATICAS_AR = {
    '1.01.01': {'model': 'RegistroOperacionalModel', 'campo_valor': 'valor_total_nota_100', 'campo_data': 'data_entrega_ticket', 'filtro_operacional': 'solicitacao_nf_id', 'descricao': 'Vendas NFe Peso Padrão'},
    '1.01.03': {'model': 'NfComplementarModel', 'campo_valor': 'valor_total_nota_100', 'campo_data': 'destinatario_data_emissao', 'filtro_operacional': 'cliente_id', 'descricao': 'Vendas de NFe Complementares'},
}

# Códigos ignorados no DRE (não impactam resultado)
CODIGOS_IGNORADOS = ['2.01.05', '3.']

# =============================================================================
# CLASSE SERVICE
# =============================================================================

class ContasAPARService:
    """Motor de consultas parametrizado por direção (AP / AR)."""

    # --------------------------------------------------------------------- #
    #  HELPERS INTERNOS
    # --------------------------------------------------------------------- #

    @staticmethod
    def _direcao_int(direcao_str):
        """Converte 'ap'/'ar' para o inteiro correspondente."""
        return DIRECAO_AP if direcao_str == 'ap' else DIRECAO_AR

    @staticmethod
    def _base_query(direcao_str):
        """Query base para Agendamentos filtrados por direção (AP/AR)."""
        direcao = ContasAPARService._direcao_int(direcao_str)
        
        query = (
            db.session.query(AgendamentoPagamentoModel)
            .outerjoin(
                FaturamentoModel,
                AgendamentoPagamentoModel.faturamento_id == FaturamentoModel.id,
            )
            .outerjoin(
                LancamentoAvulsoModel,
                AgendamentoPagamentoModel.lancamento_avulso_id == LancamentoAvulsoModel.id,
            )
            .filter(
                AgendamentoPagamentoModel.deletado == False,
                AgendamentoPagamentoModel.ativo == True,
                or_(
                    and_(
                        AgendamentoPagamentoModel.faturamento_id.isnot(None),
                        FaturamentoModel.deletado == False,
                        FaturamentoModel.ativo == True,
                        FaturamentoModel.direcao_financeira == direcao,
                    ),
                    and_(
                        AgendamentoPagamentoModel.faturamento_id.is_(None),
                        AgendamentoPagamentoModel.lancamento_avulso_id.isnot(None),
                        LancamentoAvulsoModel.deletado == False,
                        LancamentoAvulsoModel.ativo == True,
                        LancamentoAvulsoModel.tipo_movimentacao == direcao,
                    ),
                ),
            )
        )
        return query

    @staticmethod
    def _aplicar_filtros(query, filtros):
        """Aplica filtros opcionais à query base."""
        data_campo = filtros.get('data_campo', 'data_cadastro')

        if data_campo == 'data_vencimento':
            campo_data = AgendamentoPagamentoModel.data_vencimento
        elif data_campo == 'data_pagamento':
            campo_data = None
        else:
            campo_data = AgendamentoPagamentoModel.data_cadastro

        if filtros.get('data_inicio') and campo_data is not None:
            query = query.filter(campo_data >= filtros['data_inicio'])
        if filtros.get('data_fim') and campo_data is not None:
            query = query.filter(campo_data <= filtros['data_fim'])

        # Filtro por data_pagamento via subquery de parcelas
        if data_campo == 'data_pagamento':
            if filtros.get('data_inicio') or filtros.get('data_fim'):
                subquery = db.session.query(ParcelaCategorizacaoModel.agendamento_id).filter(
                    ParcelaCategorizacaoModel.deletado == False,
                    ParcelaCategorizacaoModel.ativo == True,
                    ParcelaCategorizacaoModel.data_pagamento.isnot(None),
                )
                if filtros.get('data_inicio'):
                    subquery = subquery.filter(ParcelaCategorizacaoModel.data_pagamento >= filtros['data_inicio'])
                if filtros.get('data_fim'):
                    subquery = subquery.filter(ParcelaCategorizacaoModel.data_pagamento <= filtros['data_fim'])
                query = query.filter(AgendamentoPagamentoModel.id.in_(subquery))

        if filtros.get('pessoa_id'):
            query = query.filter(AgendamentoPagamentoModel.pessoa_financeiro_id == filtros['pessoa_id'])

        # Filtro por plano de contas (busca em categorias_json)
        if filtros.get('plano_contas_id'):
            pc_id = int(filtros['plano_contas_id'])
            from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
            pc_obj = PlanoContaModel.query.get(pc_id)

            cast_col = db.cast(AgendamentoPagamentoModel.categorias_json, db.Text)
            conditions = [
                func.json_contains(
                    AgendamentoPagamentoModel.categorias_json,
                    json_lib.dumps({'categoria_id': pc_id})
                ),
            ]
            if pc_obj and pc_obj.codigo:
                conditions.append(cast_col.like(f'%"categoria": "{pc_obj.codigo}%'))
            query = query.filter(or_(*conditions))

        # Filtro por centro de custo (busca em centros_custo_json)
        if filtros.get('centro_custo_id'):
            cc_id = str(filtros['centro_custo_id'])
            query = query.filter(
                func.json_contains(
                    AgendamentoPagamentoModel.centros_custo_json,
                    json_lib.dumps({'centro': cc_id})
                )
            )

        if filtros.get('situacao_id'):
            query = query.filter(AgendamentoPagamentoModel.situacao_pagamento_id == filtros['situacao_id'])

        return query

    @staticmethod
    def _serializar_agendamento(ag):
        """Converte um AgendamentoPagamentoModel em dict para os templates."""
        fat = None
        if ag.faturamento_id:
            fat = FaturamentoModel.obter_faturamento_por_id(ag.faturamento_id)
        
        lav = None
        if not fat and ag.lancamento_avulso_id:
            lav = ag.lancamento_avulso

        pessoa = ag.pessoa_financeiro if ag.pessoa_financeiro_id else None
        parcelas = ParcelaCategorizacaoModel.obter_parcelas_por_agendamento(ag.id) if ag.id else []

        # Valor original vem da origem (Faturamento ou Lançamento Avulso)
        if fat:
            valor_original = fat.valor_total or 0
        elif lav:
            valor_original = lav.valor_movimentacao_100 or 0
        else:
            valor_original = ag.valor_total_100 or 0

        total_pago = ag.valor_conciliado_100 if ag.valor_conciliado_100 is not None else (ag.valor_total_100 or 0)
        saldo = valor_original - total_pago

        situacao_nome = ag.situacao.situacao if ag.situacao else 'Sem situação'
        situacao_id = ag.situacao_pagamento_id

        centros_custo_str = ContasAPARService._extrair_centros_custo(ag.centros_custo_json)
        plano_contas_str = ContasAPARService._extrair_plano_contas(ag.categorias_json)

        TIPOS_OPERACAO = {1: 'Carga', 2: 'Lançamento', 3: 'Crédito'}
        tipo_operacao_label = TIPOS_OPERACAO.get(fat.tipo_operacao, '-') if fat else 'Avulso'

        if fat:
            codigo = fat.codigo_faturamento
        elif lav:
            codigo = f'LAV - {ag.lancamento_avulso_id}'
        else:
            codigo = '-'

        descricao = ag.descricao or (lav.descricao if lav else None) or codigo

        return {
            'id': ag.id,
            'codigo_faturamento': codigo,
            'tipo_operacao': tipo_operacao_label,
            'descricao': descricao,
            'pessoa_nome': pessoa.identificacao if pessoa else '-',
            'pessoa_id': ag.pessoa_financeiro_id,
            'data_emissao': ag.data_cadastro,
            'data_vencimento': ag.data_vencimento or ag.data_alteracao,
            'data_pagamento': ag.data_alteracao,
            'valor_original_100': valor_original,
            'valor_pago_100': total_pago,
            'saldo_100': saldo,
            'situacao': situacao_nome,
            'situacao_id': situacao_id,
            'centro_custo': centros_custo_str,
            'plano_contas': plano_contas_str,
            'referencia_agendamento': ag.referencia or '-',
            'parcelas': [
                {
                    'numero': p.numero_parcela,
                    'vencimento': p.data_vencimento,
                    'valor_100': p.valor_parcela,
                    'data_pagamento': p.data_pagamento,
                    'valor_pago_100': p.valor_pago_100,
                }
                for p in parcelas
            ],
        }

    @staticmethod
    def _extrair_plano_contas(json_data):
        """Extrai nomes do plano de contas a partir de categorias_json."""
        if not json_data:
            return '-'
        try:
            dados = json_lib.loads(json_data) if isinstance(json_data, str) else json_data
            if not isinstance(dados, list):
                return '-'
            nomes = []
            for item in dados:
                if not isinstance(item, dict):
                    continue
                nome = item.get('nome') or item.get('categoria') or ''
                if nome:
                    nomes.append(str(nome))
            return ', '.join(nomes) or '-'
        except Exception:
            return '-'

    @staticmethod
    def _extrair_centros_custo(json_data):
        """Extrai nomes dos centros de custo a partir de centros_custo_json."""
        if not json_data:
            return '-'
        try:
            dados = json_lib.loads(json_data) if isinstance(json_data, str) else json_data
            if not isinstance(dados, list):
                return '-'
            nomes = []
            centros_map = None
            for item in dados:
                if not isinstance(item, dict):
                    continue
                nome = item.get('centro_nome', '')
                if not nome:
                    centro_val = str(item.get('centro', ''))
                    if centro_val.isdigit():
                        if centros_map is None:
                            from sistema.models_views.configuracoes_gerais.centro_custo.centro_custo_model import CentroCustoModel
                            todos = CentroCustoModel.query.filter_by(deletado=False).all()
                            centros_map = {str(cc.id): cc.nome for cc in todos}
                        nome = centros_map.get(centro_val, centro_val)
                    else:
                        nome = centro_val
                if nome:
                    nomes.append(nome)
            return ', '.join(nomes) or '-'
        except Exception:
            return '-'

    # --------------------------------------------------------------------- #
    #  SERIALIZAÇÃO — REGISTROS _A_PAGAR (AP)
    # --------------------------------------------------------------------- #

    @staticmethod
    def _serializar_registro_a_pagar(record, tipo_label):
        """
        Serializa um registro dos models _a_pagar (Fornecedor/Frete/Extrator/Comissionado)
        no formato padrão do relatório de pendentes.

        Mapeia os campos específicos destes models para o dict padronizado
        que os templates já esperam.
        """
        # Identificação da entidade a pagar — varia por tipo
        if tipo_label == 'Frete' and hasattr(record, 'transportadora') and record.transportadora:
            pessoa_nome = record.transportadora.identificacao
        elif tipo_label == 'Comissionado' and hasattr(record, 'comissionado') and record.comissionado:
            pessoa_nome = record.comissionado.identificacao
        else:
            # Fornecedor e Extrator usam record.fornecedor
            pessoa_nome = record.fornecedor.identificacao if record.fornecedor else '-'

        # Plano de contas (FK direto, não JSON)
        plano_contas_str = '-'
        if record.plano_conta_id and record.plano_conta:
            pc = record.plano_conta
            plano_contas_str = f"{pc.codigo} - {pc.nome}" if hasattr(pc, 'codigo') and pc.codigo else (pc.nome or '-')

        # Situação
        situacao_nome = record.situacao.situacao if record.situacao else 'Sem situação'

        valor = record.valor_total_a_pagar_100 or 0

        return {
            'id': record.id,
            'codigo_faturamento': f'{tipo_label[:3].upper()}-{record.id}',
            'tipo_operacao': tipo_label,
            'descricao': tipo_label,
            'pessoa_nome': pessoa_nome,
            'pessoa_id': None,
            'data_emissao': record.data_cadastro,
            'data_vencimento': record.data_entrega_ticket or record.data_cadastro,
            'data_pagamento': record.data_liquidacao,
            'valor_original_100': valor,
            'valor_pago_100': 0,
            'saldo_100': valor,
            'situacao': situacao_nome,
            'situacao_id': record.situacao_pagamento_id,
            'centro_custo': '-',
            'plano_contas': plano_contas_str,
            'referencia_agendamento': '-',
            'parcelas': [],
        }

    @staticmethod
    def _obter_pendentes_tabela_operacional(codigo, config, filtros, direcao='ap'):
        """Busca pendentes das tabelas operacionais (situação != 8, 9, 10)."""
        Model = ContasAPARService._obter_model_por_nome(config['model'])
        if not Model:
            return []

        campo_valor = config['campo_valor']
        campo_data = config['campo_data']
        filtro_op = config['filtro_operacional']
        descricao = config['descricao']

        # Situações que NÃO são pendentes: 8 (Conciliado), 9 (Conc. Parcial), 10 (Cancelado)
        SITUACOES_NAO_PENDENTES = [8, 9, 10]

        try:
            query = Model.query.filter(
                Model.ativo == True,
                Model.deletado == False,
                getattr(Model, campo_data).isnot(None),
                getattr(Model, filtro_op).isnot(None)
            )

            # Filtro por pendentes (exclui liquidadas e canceladas)
            if hasattr(Model, 'situacao_pagamento_id'):
                query = query.filter(~Model.situacao_pagamento_id.in_(SITUACOES_NAO_PENDENTES))
            elif hasattr(Model, 'situacao_financeira_id'):
                query = query.filter(~Model.situacao_financeira_id.in_(SITUACOES_NAO_PENDENTES))

            # Filtro por período de datas
            if filtros.get('data_inicio'):
                data_inicio = date.fromisoformat(filtros['data_inicio']) if isinstance(filtros['data_inicio'], str) else filtros['data_inicio']
                query = query.filter(getattr(Model, campo_data) >= data_inicio)
            if filtros.get('data_fim'):
                data_fim = date.fromisoformat(filtros['data_fim']) if isinstance(filtros['data_fim'], str) else filtros['data_fim']
                query = query.filter(getattr(Model, campo_data) <= data_fim)

            # Filtro por situação específica
            if filtros.get('situacao_id'):
                if hasattr(Model, 'situacao_pagamento_id'):
                    query = query.filter(Model.situacao_pagamento_id == int(filtros['situacao_id']))
                elif hasattr(Model, 'situacao_financeira_id'):
                    query = query.filter(Model.situacao_financeira_id == int(filtros['situacao_id']))

            # Filtro por pessoa
            if filtros.get('pessoa_id'):
                pessoa_id = filtros['pessoa_id']
                
                if direcao == 'ar':
                    # AR: filtrar por cliente (direto ou via carga)
                    if hasattr(Model, 'cliente_id'):
                        query = query.filter(Model.cliente_id == int(pessoa_id))
                    elif hasattr(Model, 'solicitacao_nf_id'):
                        query = query.join(CargaModel, Model.solicitacao_nf_id == CargaModel.id)
                        query = query.filter(CargaModel.cliente_id == int(pessoa_id))
                else:
                    # AP: filtrar por fornecedor/transportadora/extrator/comissionado (ID direto)
                    if hasattr(Model, 'fornecedor_id'):
                        query = query.filter(Model.fornecedor_id == int(pessoa_id))
                    elif hasattr(Model, 'transportadora_id'):
                        query = query.filter(Model.transportadora_id == int(pessoa_id))
                    elif hasattr(Model, 'extrator_id'):
                        query = query.filter(Model.extrator_id == int(pessoa_id))
                    elif hasattr(Model, 'comissionado_id'):
                        query = query.filter(Model.comissionado_id == int(pessoa_id))

            registros = query.order_by(getattr(Model, campo_data).asc()).all()

            resultado = []
            for reg in registros:
                valor = getattr(reg, campo_valor) or 0
                data_emissao = getattr(reg, campo_data) if hasattr(reg, campo_data) else reg.data_cadastro

                # Identificar pessoa baseado na direção
                pessoa_nome = '-'
                if direcao == 'ar':
                    # AR: priorizar cliente
                    if hasattr(reg, 'cliente') and reg.cliente:
                        pessoa_nome = reg.cliente.identificacao if hasattr(reg.cliente, 'identificacao') else str(reg.cliente)
                    elif hasattr(reg, 'solicitacao') and reg.solicitacao and reg.solicitacao.cliente:
                        pessoa_nome = reg.solicitacao.cliente.identificacao
                    elif hasattr(reg, 'destinatario_nome') and reg.destinatario_nome:
                        pessoa_nome = reg.destinatario_nome
                else:
                    # AP: priorizar fornecedor/transportadora/extrator/comissionado
                    if hasattr(reg, 'fornecedor') and reg.fornecedor:
                        pessoa_nome = reg.fornecedor.identificacao
                    elif hasattr(reg, 'transportadora') and reg.transportadora:
                        pessoa_nome = reg.transportadora.identificacao
                    elif hasattr(reg, 'extrator') and reg.extrator:
                        pessoa_nome = reg.extrator.identificacao
                    elif hasattr(reg, 'comissionado') and reg.comissionado:
                        pessoa_nome = reg.comissionado.identificacao

                # Situação
                situacao = reg.situacao if hasattr(reg, 'situacao') and reg.situacao else None
                situacao_nome = situacao.situacao if situacao else 'Sem situação'
                situacao_id = None
                if hasattr(reg, 'situacao_pagamento_id'):
                    situacao_id = reg.situacao_pagamento_id
                elif hasattr(reg, 'situacao_financeira_id'):
                    situacao_id = reg.situacao_financeira_id

                # Código identificador
                if hasattr(reg, 'numero_nota_fiscal') and reg.numero_nota_fiscal:
                    codigo_fat = f'NF-{reg.numero_nota_fiscal}'
                elif hasattr(reg, 'solicitacao_id') and reg.solicitacao_id:
                    prefixos = {
                        'FornecedorPagarModel': 'FOR',
                        'FretePagarModel': 'FRE',
                        'ExtratorPagarModel': 'EXT',
                        'ComissionadoPagarModel': 'COM',
                    }
                    prefixo = prefixos.get(config['model'], 'OP')
                    codigo_fat = f'{prefixo}-{reg.solicitacao_id}'
                else:
                    codigo_fat = f'LAN-{reg.id}'

                # Dias de atraso (baseado na data atual)
                vencimento = data_emissao
                hoje = date.today()
                dias_atraso = 0
                if vencimento and vencimento < hoje:
                    dias_atraso = (hoje - vencimento).days

                resultado.append({
                    'id': reg.id,
                    'codigo_faturamento': codigo_fat,
                    'tipo_operacao': descricao,
                    'descricao': descricao,
                    'pessoa_nome': pessoa_nome,
                    'pessoa_id': None,
                    'data_emissao': data_emissao,
                    'data_vencimento': data_emissao,
                    'data_pagamento': None,
                    'valor_original_100': valor,
                    'valor_pago_100': 0,
                    'saldo_100': valor,
                    'situacao': situacao_nome,
                    'situacao_id': situacao_id,
                    'centro_custo': '-',
                    'plano_contas': f'{codigo} - {descricao}',
                    'referencia_agendamento': '-',
                    'parcelas': [],
                    'dias_atraso': dias_atraso,
                })

            return resultado

        except Exception as e:
            print(f"[ContasAPARService] Erro ao buscar pendentes categoria {codigo}: {e}")
            return []

    @staticmethod
    def _obter_pendentes_agendamentos(filtros, tipo_categoria, plano_contas_id_filtro=None, ids_excluir=None):
        """Busca pendentes via categorias_json (situação != 8, 9, 10). Usa data_inicio/data_fim dos filtros."""
        from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
        
        ids_excluir = ids_excluir or set()
        SITUACOES_NAO_PENDENTES = [8, 9, 10]
        
        query = AgendamentoPagamentoModel.query.filter(
            AgendamentoPagamentoModel.ativo == True,
            AgendamentoPagamentoModel.deletado == False,
            ~AgendamentoPagamentoModel.situacao_pagamento_id.in_(SITUACOES_NAO_PENDENTES),
            AgendamentoPagamentoModel.categorias_json.isnot(None)
        )
        
        # Filtro por período de datas
        if filtros.get('data_inicio'):
            data_inicio = date.fromisoformat(filtros['data_inicio']) if isinstance(filtros['data_inicio'], str) else filtros['data_inicio']
            query = query.filter(AgendamentoPagamentoModel.data_competencia >= data_inicio)
        if filtros.get('data_fim'):
            data_fim = date.fromisoformat(filtros['data_fim']) if isinstance(filtros['data_fim'], str) else filtros['data_fim']
            query = query.filter(AgendamentoPagamentoModel.data_competencia <= data_fim)
        
        # Filtro por situação
        if filtros.get('situacao_id'):
            query = query.filter(AgendamentoPagamentoModel.situacao_pagamento_id == int(filtros['situacao_id']))
        
        # Filtro por pessoa
        if filtros.get('pessoa_id'):
            query = query.filter(AgendamentoPagamentoModel.pessoa_financeiro_id == int(filtros['pessoa_id']))
        
        # Filtro por centro de custo
        if filtros.get('centro_custo_id'):
            cc_id = str(filtros['centro_custo_id'])
            query = query.filter(
                func.json_contains(
                    AgendamentoPagamentoModel.centros_custo_json,
                    json_lib.dumps({'centro': cc_id})
                )
            )
        
        resultado = []
        hoje = date.today()
        for ag in query.all():
            try:
                categorias = json_lib.loads(ag.categorias_json) if isinstance(ag.categorias_json, str) else ag.categorias_json
                for cat_info in categorias or []:
                    cat_id = cat_info.get('categoria_id')
                    valor = cat_info.get('valor', 0)
                    
                    if plano_contas_id_filtro and cat_id != plano_contas_id_filtro:
                        continue
                    if cat_id in ids_excluir:
                        continue
                    
                    cat = PlanoContaModel.query.get(cat_id)
                    if not cat or cat.tipo != tipo_categoria:
                        continue
                    if any(cat.codigo.startswith(ign) for ign in CODIGOS_IGNORADOS):
                        continue
                    
                    pessoa = ag.pessoa_financeiro if ag.pessoa_financeiro_id else None
                    codigo = ag.referencia if ag.referencia else f'LAN-{ag.id}'
                    
                    # Dias de atraso (baseado na data atual)
                    vencimento = ag.data_vencimento or ag.data_cadastro
                    dias_atraso = 0
                    if vencimento and vencimento < hoje:
                        dias_atraso = (hoje - vencimento).days
                    
                    resultado.append({
                        'id': ag.id,
                        'codigo_faturamento': codigo,
                        'tipo_operacao': cat.nome,
                        'descricao': ag.descricao or cat.nome,
                        'pessoa_nome': pessoa.identificacao if pessoa else '-',
                        'pessoa_id': ag.pessoa_financeiro_id,
                        'data_emissao': ag.data_competencia or ag.data_cadastro,
                        'data_vencimento': ag.data_vencimento or ag.data_cadastro,
                        'data_pagamento': None,
                        'valor_original_100': valor,
                        'valor_pago_100': 0,
                        'saldo_100': valor,
                        'situacao': ag.situacao.situacao if ag.situacao else 'Sem situação',
                        'situacao_id': ag.situacao_pagamento_id,
                        'centro_custo': ContasAPARService._extrair_centros_custo(ag.centros_custo_json),
                        'plano_contas': f'{cat.codigo} - {cat.nome}',
                        'referencia_agendamento': ag.referencia or '-',
                        'parcelas': [],
                        'dias_atraso': dias_atraso,
                    })
            except (json_lib.JSONDecodeError, TypeError):
                continue
        return resultado

    @staticmethod
    def _obter_pendentes_ap(filtros):
        """Pendentes AP: situação diferente de 8, 9 e 10 (excluindo liquidadas e canceladas)."""
        from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
        
        filtros = filtros or {}
        plano_contas_id = filtros.get('plano_contas_id')
        categorias_map = CATEGORIAS_AUTOMATICAS_AP
        tipo_categoria = 2  # despesas
        resultado = []
        
        # Filtro por plano de contas específico
        if plano_contas_id:
            codigo = ContasAPARService._obter_codigo_plano_contas(plano_contas_id)
            if codigo and codigo in categorias_map:
                return ContasAPARService._obter_pendentes_tabela_operacional(codigo, categorias_map[codigo], filtros, 'ap')
            return ContasAPARService._obter_pendentes_agendamentos(filtros, tipo_categoria, plano_contas_id_filtro=int(plano_contas_id))
        
        # Buscar tudo: tabelas operacionais + agendamentos
        for codigo, config in categorias_map.items():
            resultado.extend(ContasAPARService._obter_pendentes_tabela_operacional(codigo, config, filtros, 'ap'))
        
        ids_excluir = ContasAPARService._obter_ids_categorias_automaticas(categorias_map)
        resultado.extend(ContasAPARService._obter_pendentes_agendamentos(filtros, tipo_categoria, ids_excluir=ids_excluir))
        
        # Ordenar por data de vencimento (mais antigo primeiro - maior atraso)
        resultado.sort(key=lambda x: (x.get('data_vencimento') or date.min))
        return resultado

    # --------------------------------------------------------------------- #
    #  SERIALIZAÇÃO — VENDAS ENTREGUES (AR)
    # --------------------------------------------------------------------- #

    @staticmethod
    def _serializar_venda_entregue(registro):
        """Serializa um RegistroOperacionalModel para o formato padrão de pendentes AR."""
        carga = registro.solicitacao
        cliente = carga.cliente if carga else None
        produto = carga.produto if carga else None
        bitola = carga.bitola if carga else None

        situacao_nome = registro.situacao.situacao if registro.situacao else 'Sem situação'
        valor = registro.valor_total_nota_100 or 0

        descricao_parts = []
        if produto:
            descricao_parts.append(produto.nome)
        if bitola:
            descricao_parts.append(bitola.bitola)
        descricao = ' | '.join(descricao_parts) or 'Venda'

        return {
            'id': registro.id,
            'codigo_faturamento': registro.numero_nota_fiscal or f'VND-{registro.id}',
            'tipo_operacao': 'Venda',
            'descricao': descricao,
            'pessoa_nome': cliente.identificacao if cliente else '-',
            'pessoa_id': None,
            'data_emissao': registro.data_cadastro,
            'data_vencimento': registro.data_entrega_ticket or registro.data_cadastro,
            'data_pagamento': None,
            'valor_original_100': valor,
            'valor_pago_100': 0,
            'saldo_100': valor,
            'situacao': situacao_nome,
            'situacao_id': registro.situacao_financeira_id,
            'centro_custo': '-',
            'plano_contas': '-',
            'referencia_agendamento': '-',
            'parcelas': [],
        }

    @staticmethod
    def _obter_pendentes_ar(filtros):
        """Pendentes AR: mesma lógica de AR-Emissões, situação != 8 e 9."""
        from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
        
        filtros = filtros or {}
        plano_contas_id = filtros.get('plano_contas_id')
        categorias_map = CATEGORIAS_AUTOMATICAS_AR
        tipo_categoria = 1  # receitas
        resultado = []
        
        # Filtro por plano de contas específico
        if plano_contas_id:
            codigo = ContasAPARService._obter_codigo_plano_contas(plano_contas_id)
            if codigo and codigo in categorias_map:
                return ContasAPARService._obter_pendentes_tabela_operacional(codigo, categorias_map[codigo], filtros, 'ar')
            return ContasAPARService._obter_pendentes_agendamentos(filtros, tipo_categoria, plano_contas_id_filtro=int(plano_contas_id))
        
        # Buscar tudo: tabelas operacionais + agendamentos
        for codigo, config in categorias_map.items():
            resultado.extend(ContasAPARService._obter_pendentes_tabela_operacional(codigo, config, filtros, 'ar'))
        
        ids_excluir = ContasAPARService._obter_ids_categorias_automaticas(categorias_map)
        resultado.extend(ContasAPARService._obter_pendentes_agendamentos(filtros, tipo_categoria, ids_excluir=ids_excluir))
        
        # Ordenar por data de vencimento (mais antigo primeiro - maior atraso)
        resultado.sort(key=lambda x: (x.get('data_vencimento') or date.min))
        return resultado

    # --------------------------------------------------------------------- #
    #  CONSULTAS PÚBLICAS
    # --------------------------------------------------------------------- #

    @staticmethod
    def _obter_model_por_nome(nome_model):
        """Retorna a classe do model pelo nome."""
        modelos = {
            'RegistroOperacionalModel': RegistroOperacionalModel,
            'NfComplementarModel': NfComplementarModel,
            'FornecedorPagarModel': FornecedorPagarModel,
            'FretePagarModel': FretePagarModel,
            'ExtratorPagarModel': ExtratorPagarModel,
            'ComissionadoPagarModel': ComissionadoPagarModel,
        }
        return modelos.get(nome_model)

    @staticmethod
    def _obter_codigo_plano_contas(plano_contas_id):
        """Retorna o código do plano de contas pelo ID."""
        if not plano_contas_id:
            return None
        from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
        plano = PlanoContaModel.query.get(int(plano_contas_id))
        return plano.codigo if plano else None

    @staticmethod
    def _obter_ids_vinculo_pessoa(pessoa_id, tipo_vinculo):
        """
        Retorna os IDs de vínculo operacional de uma PessoaFinanceiro.
        tipo_vinculo: 'fornecedor', 'transportadora', 'extrator', 'comissionado'
        """
        if not pessoa_id:
            return []
        from sistema.models_views.gerenciar.pessoa_financeiro.pessoa_financeiro_model import PessoaFinanceiroModel
        pessoa = PessoaFinanceiroModel.query.get(int(pessoa_id))
        if not pessoa or not pessoa.vinculos_operacionais:
            return []
        try:
            vinculos = pessoa.vinculos_operacionais if isinstance(pessoa.vinculos_operacionais, dict) else json_lib.loads(pessoa.vinculos_operacionais)
            ids = vinculos.get(tipo_vinculo, [])
            return [int(v['id']) for v in ids if v.get('id')]
        except (json_lib.JSONDecodeError, TypeError, KeyError):
            return []

    @staticmethod
    def _obter_emissoes_tabela_operacional(codigo, config, filtros, direcao='ap'):
        """
        Busca registros das tabelas operacionais para categorias automáticas do DRE.
        """
        Model = ContasAPARService._obter_model_por_nome(config['model'])
        if not Model:
            return []

        campo_valor = config['campo_valor']
        campo_data = config['campo_data']
        filtro_op = config['filtro_operacional']
        descricao = config['descricao']

        try:
            # Filtros base IGUAIS ao DRE
            query = Model.query.filter(
                Model.ativo == True,
                Model.deletado == False,
                getattr(Model, campo_data).isnot(None),  # Data preenchida (igual DRE)
                getattr(Model, filtro_op).isnot(None)    # Só operacionais (igual DRE)
            )

            # Filtro por período de datas
            if filtros.get('data_inicio'):
                query = query.filter(getattr(Model, campo_data) >= filtros['data_inicio'])
            if filtros.get('data_fim'):
                query = query.filter(getattr(Model, campo_data) <= filtros['data_fim'])

            # Filtro por situação
            if filtros.get('situacao_id'):
                if hasattr(Model, 'situacao_pagamento_id'):
                    query = query.filter(Model.situacao_pagamento_id == int(filtros['situacao_id']))
                elif hasattr(Model, 'situacao_financeira_id'):
                    query = query.filter(Model.situacao_financeira_id == int(filtros['situacao_id']))

            # Filtro por pessoa
            if filtros.get('pessoa_id'):
                pessoa_id = filtros['pessoa_id']
                
                if direcao == 'ar':
                    # AR: filtrar por cliente (direto ou via carga)
                    if hasattr(Model, 'cliente_id'):
                        query = query.filter(Model.cliente_id == int(pessoa_id))
                    elif hasattr(Model, 'solicitacao_nf_id'):
                        query = query.join(CargaModel, Model.solicitacao_nf_id == CargaModel.id)
                        query = query.filter(CargaModel.cliente_id == int(pessoa_id))
                else:
                    # AP: filtrar por fornecedor/transportadora/extrator/comissionado (ID direto)
                    if hasattr(Model, 'fornecedor_id'):
                        query = query.filter(Model.fornecedor_id == int(pessoa_id))
                    elif hasattr(Model, 'transportadora_id'):
                        query = query.filter(Model.transportadora_id == int(pessoa_id))
                    elif hasattr(Model, 'extrator_id'):
                        query = query.filter(Model.extrator_id == int(pessoa_id))
                    elif hasattr(Model, 'comissionado_id'):
                        query = query.filter(Model.comissionado_id == int(pessoa_id))

            registros = query.order_by(getattr(Model, campo_data).desc()).all()

            resultado = []
            for reg in registros:
                valor = getattr(reg, campo_valor) or 0
                data_emissao = getattr(reg, campo_data) if hasattr(reg, campo_data) else reg.data_cadastro

                # Identificar pessoa baseado na direção
                pessoa_nome = '-'
                if direcao == 'ar':
                    # AR: priorizar cliente
                    if hasattr(reg, 'cliente') and reg.cliente:
                        pessoa_nome = reg.cliente.identificacao if hasattr(reg.cliente, 'identificacao') else str(reg.cliente)
                    elif hasattr(reg, 'solicitacao') and reg.solicitacao and reg.solicitacao.cliente:
                        pessoa_nome = reg.solicitacao.cliente.identificacao
                    elif hasattr(reg, 'destinatario_nome') and reg.destinatario_nome:
                        pessoa_nome = reg.destinatario_nome
                else:
                    # AP: priorizar fornecedor/transportadora/extrator/comissionado
                    if hasattr(reg, 'fornecedor') and reg.fornecedor:
                        pessoa_nome = reg.fornecedor.identificacao
                    elif hasattr(reg, 'transportadora') and reg.transportadora:
                        pessoa_nome = reg.transportadora.identificacao
                    elif hasattr(reg, 'extrator') and reg.extrator:
                        pessoa_nome = reg.extrator.identificacao
                    elif hasattr(reg, 'comissionado') and reg.comissionado:
                        pessoa_nome = reg.comissionado.identificacao

                # Situação
                situacao = reg.situacao if hasattr(reg, 'situacao') and reg.situacao else None
                situacao_nome = situacao.situacao if situacao else 'Sem situação'
                situacao_id = None
                if hasattr(reg, 'situacao_pagamento_id'):
                    situacao_id = reg.situacao_pagamento_id
                elif hasattr(reg, 'situacao_financeira_id'):
                    situacao_id = reg.situacao_financeira_id

                # Código identificador baseado no tipo de registro
                if hasattr(reg, 'numero_nota_fiscal') and reg.numero_nota_fiscal:
                    codigo_fat = f'NF-{reg.numero_nota_fiscal}'
                elif hasattr(reg, 'solicitacao_id') and reg.solicitacao_id:
                    # Tabelas operacionais vinculadas a carga
                    prefixos = {
                        'FornecedorPagarModel': 'FOR',
                        'FretePagarModel': 'FRE', 
                        'ExtratorPagarModel': 'EXT',
                        'ComissionadoPagarModel': 'COM',
                    }
                    prefixo = prefixos.get(config['model'], 'OP')
                    codigo_fat = f'{prefixo}-{reg.solicitacao_id}'
                else:
                    codigo_fat = f'LAN-{reg.id}'

                resultado.append({
                    'id': reg.id,
                    'codigo_faturamento': codigo_fat,
                    'tipo_operacao': descricao,
                    'descricao': descricao,
                    'pessoa_nome': pessoa_nome,
                    'pessoa_id': None,
                    'data_emissao': data_emissao,
                    'data_vencimento': data_emissao,
                    'data_pagamento': getattr(reg, 'data_liquidacao', None),
                    'valor_original_100': valor,
                    'valor_pago_100': 0,
                    'saldo_100': valor,
                    'situacao': situacao_nome,
                    'situacao_id': situacao_id,
                    'centro_custo': '-',
                    'plano_contas': f'{codigo} - {descricao}',
                    'referencia_agendamento': '-',
                    'parcelas': [],
                })

            return resultado

        except Exception as e:
            print(f"[ContasAPARService] Erro ao buscar categoria automática {codigo}: {e}")
            return []

    @staticmethod
    def obter_emissoes(direcao_str, filtros=None):
        """Emissões no período - lógica idêntica ao DRE."""
        from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
        
        filtros = filtros or {}
        plano_contas_id = filtros.get('plano_contas_id')
        categorias_map = CATEGORIAS_AUTOMATICAS_AP if direcao_str == 'ap' else CATEGORIAS_AUTOMATICAS_AR
        tipo_categoria = 2 if direcao_str == 'ap' else 1
        resultado = []
        
        # Filtro por plano de contas específico
        if plano_contas_id:
            codigo = ContasAPARService._obter_codigo_plano_contas(plano_contas_id)
            if codigo and codigo in categorias_map:
                return ContasAPARService._obter_emissoes_tabela_operacional(codigo, categorias_map[codigo], filtros, direcao_str)
            return ContasAPARService._obter_emissoes_agendamentos(filtros, tipo_categoria, plano_contas_id_filtro=int(plano_contas_id))
        
        # Buscar tudo: tabelas operacionais + agendamentos
        for codigo, config in categorias_map.items():
            resultado.extend(ContasAPARService._obter_emissoes_tabela_operacional(codigo, config, filtros, direcao_str))
        
        ids_excluir = ContasAPARService._obter_ids_categorias_automaticas(categorias_map)
        resultado.extend(ContasAPARService._obter_emissoes_agendamentos(filtros, tipo_categoria, ids_excluir=ids_excluir))
        
        # Ordenar por data (mais recente primeiro)
        resultado.sort(key=lambda x: (x.get('data_emissao') or date.min), reverse=True)
        return resultado

    @staticmethod
    def _obter_ids_categorias_automaticas(categorias_map):
        """IDs das categorias automáticas para excluir dos agendamentos."""
        from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
        ids = set()
        for codigo in categorias_map.keys():
            cat = PlanoContaModel.query.filter_by(codigo=codigo, ativo=True, deletado=False).first()
            if cat:
                ids.add(cat.id)
        return ids

    @staticmethod
    def _obter_emissoes_agendamentos(filtros, tipo_categoria, plano_contas_id_filtro=None, ids_excluir=None):
        """Busca emissões via categorias_json (igual DRE)."""
        from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
        
        ids_excluir = ids_excluir or set()
        
        # Query: situação 6/8/9 + data_competencia (igual DRE)
        query = AgendamentoPagamentoModel.query.filter(
            AgendamentoPagamentoModel.ativo == True,
            AgendamentoPagamentoModel.deletado == False,
            AgendamentoPagamentoModel.situacao_pagamento_id.in_([6, 8, 9]),
            AgendamentoPagamentoModel.categorias_json.isnot(None)
        )
        
        # Filtro por período
        if filtros.get('data_inicio'):
            query = query.filter(AgendamentoPagamentoModel.data_competencia >= filtros['data_inicio'])
        if filtros.get('data_fim'):
            query = query.filter(AgendamentoPagamentoModel.data_competencia <= filtros['data_fim'])
        
        # Filtro por situação
        if filtros.get('situacao_id'):
            query = query.filter(AgendamentoPagamentoModel.situacao_pagamento_id == int(filtros['situacao_id']))
        
        # Filtro por pessoa
        if filtros.get('pessoa_id'):
            query = query.filter(AgendamentoPagamentoModel.pessoa_financeiro_id == int(filtros['pessoa_id']))
        
        # Filtro por centro de custo (busca dentro do JSON — campo 'centro' armazena ID como string)
        if filtros.get('centro_custo_id'):
            cc_id = str(filtros['centro_custo_id'])
            query = query.filter(
                func.json_contains(
                    AgendamentoPagamentoModel.centros_custo_json,
                    json_lib.dumps({'centro': cc_id})
                )
            )
        
        resultado = []
        for ag in query.all():
            try:
                categorias = json_lib.loads(ag.categorias_json) if isinstance(ag.categorias_json, str) else ag.categorias_json
                for cat_info in categorias or []:
                    cat_id = cat_info.get('categoria_id')
                    valor = cat_info.get('valor', 0)
                    
                    # Validações
                    if plano_contas_id_filtro and cat_id != plano_contas_id_filtro:
                        continue
                    if cat_id in ids_excluir:
                        continue
                    
                    cat = PlanoContaModel.query.get(cat_id)
                    if not cat or cat.tipo != tipo_categoria:
                        continue
                    if any(cat.codigo.startswith(ign) for ign in CODIGOS_IGNORADOS):
                        continue
                    
                    pessoa = ag.pessoa_financeiro if ag.pessoa_financeiro_id else None
                    
                    # Código: referência do agendamento ou LAN-{id}
                    codigo = ag.referencia if ag.referencia else f'LAN-{ag.id}'
                    
                    resultado.append({
                        'id': ag.id,
                        'codigo_faturamento': codigo,
                        'tipo_operacao': cat.nome,
                        'descricao': ag.descricao or cat.nome,
                        'pessoa_nome': pessoa.identificacao if pessoa else '-',
                        'pessoa_id': ag.pessoa_financeiro_id,
                        'data_emissao': ag.data_competencia or ag.data_cadastro,
                        'data_vencimento': ag.data_vencimento or ag.data_cadastro,
                        'data_pagamento': ag.data_alteracao,
                        'valor_original_100': valor,
                        'valor_pago_100': 0,
                        'saldo_100': valor,
                        'situacao': ag.situacao.situacao if ag.situacao else 'Sem situação',
                        'situacao_id': ag.situacao_pagamento_id,
                        'centro_custo': ContasAPARService._extrair_centros_custo(ag.centros_custo_json),
                        'plano_contas': f'{cat.codigo} - {cat.nome}',
                        'referencia_agendamento': ag.referencia or '-',
                        'parcelas': [],
                    })
            except (json_lib.JSONDecodeError, TypeError):
                continue
        return resultado

    @staticmethod
    def _obter_baixas_tabela_operacional(codigo, config, filtros, direcao='ap'):
        """
        Busca pagamentos das tabelas operacionais (situação 8 ou 9).
        Mesma lógica de _obter_emissoes_tabela_operacional mas filtra por situação liquidada.
        """
        Model = ContasAPARService._obter_model_por_nome(config['model'])
        if not Model:
            return []

        campo_valor = config['campo_valor']
        campo_data = config['campo_data']
        filtro_op = config['filtro_operacional']
        descricao = config['descricao']

        try:
            # Filtros base
            query = Model.query.filter(
                Model.ativo == True,
                Model.deletado == False,
                getattr(Model, campo_data).isnot(None),
                getattr(Model, filtro_op).isnot(None)
            )

            # Filtro por situação liquidada/recebida
            situacoes_filtro = SITUACOES_RECEBIDAS_AR if direcao == 'ar' else SITUACOES_LIQUIDADAS
            if hasattr(Model, 'situacao_pagamento_id'):
                query = query.filter(Model.situacao_pagamento_id.in_(situacoes_filtro))
            elif hasattr(Model, 'situacao_financeira_id'):
                query = query.filter(Model.situacao_financeira_id.in_(situacoes_filtro))

            # Filtro por período de datas (data_liquidacao para baixas)
            if filtros.get('data_inicio'):
                if hasattr(Model, 'data_liquidacao'):
                    query = query.filter(Model.data_liquidacao >= filtros['data_inicio'])
                else:
                    query = query.filter(getattr(Model, campo_data) >= filtros['data_inicio'])
            if filtros.get('data_fim'):
                if hasattr(Model, 'data_liquidacao'):
                    query = query.filter(Model.data_liquidacao <= filtros['data_fim'])
                else:
                    query = query.filter(getattr(Model, campo_data) <= filtros['data_fim'])

            # Filtro por situação específica
            if filtros.get('situacao_id'):
                if hasattr(Model, 'situacao_pagamento_id'):
                    query = query.filter(Model.situacao_pagamento_id == int(filtros['situacao_id']))
                elif hasattr(Model, 'situacao_financeira_id'):
                    query = query.filter(Model.situacao_financeira_id == int(filtros['situacao_id']))

            # Filtro por pessoa
            if filtros.get('pessoa_id'):
                pessoa_id = filtros['pessoa_id']
                
                if direcao == 'ar':
                    # AR: filtrar por cliente (direto ou via carga)
                    if hasattr(Model, 'cliente_id'):
                        query = query.filter(Model.cliente_id == int(pessoa_id))
                    elif hasattr(Model, 'solicitacao_nf_id'):
                        query = query.join(CargaModel, Model.solicitacao_nf_id == CargaModel.id)
                        query = query.filter(CargaModel.cliente_id == int(pessoa_id))
                else:
                    # AP: filtrar por fornecedor/transportadora/extrator/comissionado (ID direto)
                    if hasattr(Model, 'fornecedor_id'):
                        query = query.filter(Model.fornecedor_id == int(pessoa_id))
                    elif hasattr(Model, 'transportadora_id'):
                        query = query.filter(Model.transportadora_id == int(pessoa_id))
                    elif hasattr(Model, 'extrator_id'):
                        query = query.filter(Model.extrator_id == int(pessoa_id))
                    elif hasattr(Model, 'comissionado_id'):
                        query = query.filter(Model.comissionado_id == int(pessoa_id))

            registros = query.order_by(getattr(Model, campo_data).desc()).all()

            resultado = []
            for reg in registros:
                valor = getattr(reg, campo_valor) or 0
                data_emissao = getattr(reg, campo_data) if hasattr(reg, campo_data) else reg.data_cadastro
                data_pagamento = getattr(reg, 'data_liquidacao', None) or data_emissao

                # Identificar pessoa baseado na direção
                pessoa_nome = '-'
                if direcao == 'ar':
                    # AR: priorizar cliente
                    if hasattr(reg, 'cliente') and reg.cliente:
                        pessoa_nome = reg.cliente.identificacao if hasattr(reg.cliente, 'identificacao') else str(reg.cliente)
                    elif hasattr(reg, 'solicitacao') and reg.solicitacao and reg.solicitacao.cliente:
                        pessoa_nome = reg.solicitacao.cliente.identificacao
                    elif hasattr(reg, 'destinatario_nome') and reg.destinatario_nome:
                        pessoa_nome = reg.destinatario_nome
                else:
                    # AP: priorizar fornecedor/transportadora/extrator/comissionado
                    if hasattr(reg, 'fornecedor') and reg.fornecedor:
                        pessoa_nome = reg.fornecedor.identificacao
                    elif hasattr(reg, 'transportadora') and reg.transportadora:
                        pessoa_nome = reg.transportadora.identificacao
                    elif hasattr(reg, 'extrator') and reg.extrator:
                        pessoa_nome = reg.extrator.identificacao
                    elif hasattr(reg, 'comissionado') and reg.comissionado:
                        pessoa_nome = reg.comissionado.identificacao

                # Situação
                situacao = reg.situacao if hasattr(reg, 'situacao') and reg.situacao else None
                situacao_nome = situacao.situacao if situacao else 'Sem situação'
                situacao_id = None
                if hasattr(reg, 'situacao_pagamento_id'):
                    situacao_id = reg.situacao_pagamento_id
                elif hasattr(reg, 'situacao_financeira_id'):
                    situacao_id = reg.situacao_financeira_id

                # Código identificador
                if hasattr(reg, 'numero_nota_fiscal') and reg.numero_nota_fiscal:
                    codigo_fat = f'NF-{reg.numero_nota_fiscal}'
                elif hasattr(reg, 'solicitacao_id') and reg.solicitacao_id:
                    prefixos = {
                        'FornecedorPagarModel': 'FOR',
                        'FretePagarModel': 'FRE',
                        'ExtratorPagarModel': 'EXT',
                        'ComissionadoPagarModel': 'COM',
                    }
                    prefixo = prefixos.get(config['model'], 'OP')
                    codigo_fat = f'{prefixo}-{reg.solicitacao_id}'
                else:
                    codigo_fat = f'LAN-{reg.id}'

                resultado.append({
                    'id': reg.id,
                    'codigo_faturamento': codigo_fat,
                    'tipo_operacao': descricao,
                    'descricao': descricao,
                    'pessoa_nome': pessoa_nome,
                    'pessoa_id': None,
                    'data_emissao': data_emissao,
                    'data_vencimento': data_emissao,
                    'data_pagamento': data_pagamento,
                    'valor_original_100': valor,
                    'valor_pago_100': valor,
                    'saldo_100': 0,
                    'situacao': situacao_nome,
                    'situacao_id': situacao_id,
                    'centro_custo': '-',
                    'plano_contas': f'{codigo} - {descricao}',
                    'referencia_agendamento': '-',
                    'parcelas': [],
                })

            return resultado

        except Exception as e:
            print(f"[ContasAPARService] Erro ao buscar baixas categoria {codigo}: {e}")
            return []

    @staticmethod
    def _obter_baixas_agendamentos(filtros, tipo_categoria, direcao='ap', plano_contas_id_filtro=None, ids_excluir=None):
        """Busca pagamentos via categorias_json (situação liquidada/recebida)."""
        from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
        
        ids_excluir = ids_excluir or set()
        
        # Query: situações liquidadas (AP: 8,9 | AR: 3,8,9)
        situacoes_filtro = SITUACOES_RECEBIDAS_AR if direcao == 'ar' else SITUACOES_LIQUIDADAS
        query = AgendamentoPagamentoModel.query.filter(
            AgendamentoPagamentoModel.ativo == True,
            AgendamentoPagamentoModel.deletado == False,
            AgendamentoPagamentoModel.situacao_pagamento_id.in_(situacoes_filtro),
            AgendamentoPagamentoModel.categorias_json.isnot(None)
        )
        
        # Filtro por período (data_competencia)
        if filtros.get('data_inicio'):
            query = query.filter(AgendamentoPagamentoModel.data_competencia >= filtros['data_inicio'])
        if filtros.get('data_fim'):
            query = query.filter(AgendamentoPagamentoModel.data_competencia <= filtros['data_fim'])
        
        # Filtro por situação
        if filtros.get('situacao_id'):
            query = query.filter(AgendamentoPagamentoModel.situacao_pagamento_id == int(filtros['situacao_id']))
        
        # Filtro por pessoa
        if filtros.get('pessoa_id'):
            query = query.filter(AgendamentoPagamentoModel.pessoa_financeiro_id == int(filtros['pessoa_id']))
        
        # Filtro por centro de custo
        if filtros.get('centro_custo_id'):
            cc_id = str(filtros['centro_custo_id'])
            query = query.filter(
                func.json_contains(
                    AgendamentoPagamentoModel.centros_custo_json,
                    json_lib.dumps({'centro': cc_id})
                )
            )
        
        resultado = []
        for ag in query.all():
            try:
                categorias = json_lib.loads(ag.categorias_json) if isinstance(ag.categorias_json, str) else ag.categorias_json
                for cat_info in categorias or []:
                    cat_id = cat_info.get('categoria_id')
                    valor = cat_info.get('valor', 0)
                    
                    if plano_contas_id_filtro and cat_id != plano_contas_id_filtro:
                        continue
                    if cat_id in ids_excluir:
                        continue
                    
                    cat = PlanoContaModel.query.get(cat_id)
                    if not cat or cat.tipo != tipo_categoria:
                        continue
                    if any(cat.codigo.startswith(ign) for ign in CODIGOS_IGNORADOS):
                        continue
                    
                    pessoa = ag.pessoa_financeiro if ag.pessoa_financeiro_id else None
                    codigo = ag.referencia if ag.referencia else f'LAN-{ag.id}'
                    
                    resultado.append({
                        'id': ag.id,
                        'codigo_faturamento': codigo,
                        'tipo_operacao': cat.nome,
                        'descricao': ag.descricao or cat.nome,
                        'pessoa_nome': pessoa.identificacao if pessoa else '-',
                        'pessoa_id': ag.pessoa_financeiro_id,
                        'data_emissao': ag.data_competencia or ag.data_cadastro,
                        'data_vencimento': ag.data_vencimento or ag.data_cadastro,
                        'data_pagamento': ag.data_alteracao,
                        'valor_original_100': valor,
                        'valor_pago_100': valor,
                        'saldo_100': 0,
                        'situacao': ag.situacao.situacao if ag.situacao else 'Sem situação',
                        'situacao_id': ag.situacao_pagamento_id,
                        'centro_custo': ContasAPARService._extrair_centros_custo(ag.centros_custo_json),
                        'plano_contas': f'{cat.codigo} - {cat.nome}',
                        'referencia_agendamento': ag.referencia or '-',
                        'parcelas': [],
                    })
            except (json_lib.JSONDecodeError, TypeError):
                continue
        return resultado

    @staticmethod
    def obter_baixas(direcao_str, filtros=None):
        """Pagamentos no período - mesma lógica do DRE, situação 8 ou 9."""
        from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
        
        filtros = filtros or {}
        plano_contas_id = filtros.get('plano_contas_id')
        categorias_map = CATEGORIAS_AUTOMATICAS_AP if direcao_str == 'ap' else CATEGORIAS_AUTOMATICAS_AR
        tipo_categoria = 2 if direcao_str == 'ap' else 1
        resultado = []
        
        # Filtro por plano de contas específico
        if plano_contas_id:
            codigo = ContasAPARService._obter_codigo_plano_contas(plano_contas_id)
            if codigo and codigo in categorias_map:
                return ContasAPARService._obter_baixas_tabela_operacional(codigo, categorias_map[codigo], filtros, direcao_str)
            return ContasAPARService._obter_baixas_agendamentos(filtros, tipo_categoria, direcao_str, plano_contas_id_filtro=int(plano_contas_id))
        
        # Buscar tudo: tabelas operacionais + agendamentos
        for codigo, config in categorias_map.items():
            resultado.extend(ContasAPARService._obter_baixas_tabela_operacional(codigo, config, filtros, direcao_str))
        
        ids_excluir = ContasAPARService._obter_ids_categorias_automaticas(categorias_map)
        resultado.extend(ContasAPARService._obter_baixas_agendamentos(filtros, tipo_categoria, direcao_str, ids_excluir=ids_excluir))
        
        # Ordenar por data (mais recente primeiro)
        resultado.sort(key=lambda x: (x.get('data_pagamento') or x.get('data_emissao') or date.min), reverse=True)
        return resultado

    @staticmethod
    def obter_pendentes(direcao_str, filtros=None):
        """Títulos pendentes filtrados por período. AP usa tabelas operacionais, AR usa RegistroOperacional."""
        filtros = filtros or {}
        if direcao_str == 'ap':
            return ContasAPARService._obter_pendentes_ap(filtros)
        return ContasAPARService._obter_pendentes_ar(filtros)

    # --------------------------------------------------------------------- #
    #  TOTALIZADORES
    # --------------------------------------------------------------------- #

    @staticmethod
    def totalizar(registros):
        """Retorna totais a partir de uma lista de registros serializados."""
        total_original = sum(r.get('valor_original_100', 0) for r in registros)
        total_pago = sum(r.get('valor_pago_100', 0) for r in registros)
        total_saldo = sum(r.get('saldo_100', 0) for r in registros)

        return {
            'total_original_100': total_original,
            'total_pago_100': total_pago,
            'total_saldo_100': total_saldo,
            'quantidade': len(registros),
        }

    # --------------------------------------------------------------------- #
    #  EXCEL — preparação de dados
    # --------------------------------------------------------------------- #

    @staticmethod
    def preparar_dados_excel_emissoes(registros, direcao_str):
        """Converte registros de emissões em lista de dicts para Excel."""
        label_entidade = 'Fornecedor' if direcao_str == 'ap' else 'Cliente'
        label_valor = 'Valor a Pagar' if direcao_str == 'ap' else 'Valor a Receber'
        dados = []
        for r in registros:
            dados.append({
                'Código': r['codigo_faturamento'],
                label_entidade: r['pessoa_nome'],
                'Descrição': r['descricao'],
                'Data Emissão': r['data_emissao'].strftime('%d/%m/%Y') if r['data_emissao'] else '-',
                'Vencimento': r['data_vencimento'].strftime('%d/%m/%Y') if r['data_vencimento'] else '-',
                label_valor: round((r['valor_original_100'] or 0) / 100, 2),
                'Situação': r['situacao'],
                'Plano de Contas': r['plano_contas'],
                'Centro de Custo': r['centro_custo'],
            })
        return dados

    @staticmethod
    def preparar_dados_excel_baixas(registros, direcao_str):
        """Converte registros de baixas em lista de dicts para Excel."""
        label_entidade = 'Fornecedor' if direcao_str == 'ap' else 'Cliente'
        label_baixa = 'Data Pagamento' if direcao_str == 'ap' else 'Data Recebimento'
        label_valor_pago = 'Valor Pago' if direcao_str == 'ap' else 'Valor Recebido'
        dados = []
        for r in registros:
            dados.append({
                'Código': r['codigo_faturamento'],
                label_entidade: r['pessoa_nome'],
                'Descrição': r['descricao'],
                'Vencimento': r['data_vencimento'].strftime('%d/%m/%Y') if r['data_vencimento'] else '-',
                label_baixa: r['data_pagamento'].strftime('%d/%m/%Y') if r['data_pagamento'] else '-',
                'Valor Original': round((r['valor_original_100'] or 0) / 100, 2),
                label_valor_pago: round((r['valor_pago_100'] or 0) / 100, 2),
                'Saldo': round((r.get('saldo_100') or 0) / 100, 2),
                'Situação': r['situacao'],
                'Plano de Contas': r['plano_contas'],
                'Centro de Custo': r['centro_custo'],
            })
        return dados

    @staticmethod
    def preparar_dados_excel_pendentes(registros, direcao_str):
        """Converte registros de pendentes em lista de dicts para Excel."""
        label_entidade = 'Fornecedor' if direcao_str == 'ap' else 'Cliente'
        dados = []
        for r in registros:
            dados.append({
                'Código': r['codigo_faturamento'],
                label_entidade: r['pessoa_nome'],
                'Descrição': r['descricao'],
                'Data Emissão': r['data_emissao'].strftime('%d/%m/%Y') if r['data_emissao'] else '-',
                'Vencimento': r['data_vencimento'].strftime('%d/%m/%Y') if r['data_vencimento'] else '-',
                'Valor Original': round((r['valor_original_100'] or 0) / 100, 2),
                'Saldo Pendente': round((r.get('saldo_100') or 0) / 100, 2),
                'Dias Atraso': r.get('dias_atraso', 0),
                'Situação': r['situacao'],
            })
        return dados
