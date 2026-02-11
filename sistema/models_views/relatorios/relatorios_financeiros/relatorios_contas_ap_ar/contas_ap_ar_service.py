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
        """
        Query base: Agendamento JOIN Faturamento + JOIN LancamentoAvulso,
        filtrado pela direção e excluindo registros deletados/inativos.

        Direção é determinada por:
          - FaturamentoModel.direcao_financeira (1=AR, 2=AP)  → cargas, lançamentos, créditos
          - LancamentoAvulsoModel.tipo_movimentacao (1=AR, 2=AP) → avulsos sem faturamento (OFX, etc.)

        Agendamentos sem nenhum vínculo (faturamento=None E lancamento=None) são excluídos.
        """
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
                    # Cenário 1: tem faturamento → direção pelo faturamento
                    and_(
                        AgendamentoPagamentoModel.faturamento_id.isnot(None),
                        FaturamentoModel.deletado == False,
                        FaturamentoModel.ativo == True,
                        FaturamentoModel.direcao_financeira == direcao,
                    ),
                    # Cenário 2: sem faturamento, tem lançamento avulso → direção pelo lançamento
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
        """
        Aplica filtros opcionais à query base.

        filtros (dict):
            data_inicio      - str 'YYYY-MM-DD' (data de emissão >=)
            data_fim          - str 'YYYY-MM-DD' (data de emissão <=)
            pessoa_id         - int  (pessoa_financeiro_id)
            plano_contas_id   - int  (busca dentro do JSON plano_contas_json)
            centro_custo_id   - int  (busca dentro do JSON centros_custo_json)
            situacao_id       - int  (situacao_pagamento_id)
            data_campo        - str  nome do campo de data a filtrar (default: data_cadastro)
        """
        data_campo = filtros.get('data_campo', 'data_cadastro')

        # Determina o campo de data a usar na filtragem
        if data_campo == 'data_vencimento':
            campo_data = AgendamentoPagamentoModel.data_vencimento
        elif data_campo == 'data_pagamento':
            campo_data = None  # tratado via subquery de parcelas
        else:
            campo_data = AgendamentoPagamentoModel.data_cadastro

        # Filtro por período de datas
        if filtros.get('data_inicio') and campo_data is not None:
            query = query.filter(campo_data >= filtros['data_inicio'])
        if filtros.get('data_fim') and campo_data is not None:
            query = query.filter(campo_data <= filtros['data_fim'])

        # Filtro por data_pagamento (parcela) — caso especial
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

        # Filtro por pessoa (fornecedor / cliente)
        if filtros.get('pessoa_id'):
            query = query.filter(
                AgendamentoPagamentoModel.pessoa_financeiro_id == filtros['pessoa_id']
            )

        # Filtro por plano de contas (busca dentro do JSON — campo real: categorias_json)
        # Estrutura real: [{"categoria_id": 5, "categoria": "2.01 - Frete", "nome": "Frete", ...}]
        if filtros.get('plano_contas_id'):
            pc_id = int(filtros['plano_contas_id'])
            from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
            pc_obj = PlanoContaModel.query.get(pc_id)

            cast_col = db.cast(AgendamentoPagamentoModel.categorias_json, db.Text)
            conditions = [
                # Busca por categoria_id (int) — lançamentos avulsos e OFX
                func.json_contains(
                    AgendamentoPagamentoModel.categorias_json,
                    json_lib.dumps({'categoria_id': pc_id})
                ),
            ]
            # Busca por código do plano de contas — categorizar fatura
            if pc_obj and pc_obj.codigo:
                conditions.append(cast_col.like(f'%"categoria": "{pc_obj.codigo}%'))
            query = query.filter(or_(*conditions))

        # Filtro por centro de custo (busca dentro do JSON — campo 'centro' armazena ID como string)
        # Estrutura real: [{"centro": "3", "centro_nome": "Vendas", "percentual": "70", ...}]
        if filtros.get('centro_custo_id'):
            cc_id = str(filtros['centro_custo_id'])
            query = query.filter(
                func.json_contains(
                    AgendamentoPagamentoModel.centros_custo_json,
                    json_lib.dumps({'centro': cc_id})
                )
            )

        # Filtro por situação de pagamento
        if filtros.get('situacao_id'):
            query = query.filter(
                AgendamentoPagamentoModel.situacao_pagamento_id == filtros['situacao_id']
            )

        return query

    @staticmethod
    def _serializar_agendamento(ag):
        """
        Converte um AgendamentoPagamentoModel em dict plano para os templates.

        Origem do agendamento:
          - Cenário 1: ag.faturamento_id → dados vêm do FaturamentoModel
          - Cenário 2: ag.lancamento_avulso_id (sem faturamento) → dados vêm do LancamentoAvulsoModel
        """
        # Dados do faturamento vinculado (se existir)
        fat = None
        if ag.faturamento_id:
            fat = FaturamentoModel.obter_faturamento_por_id(ag.faturamento_id)
        # Dados do lançamento avulso vinculado (quando não há faturamento)
        lav = None
        if not fat and ag.lancamento_avulso_id:
            lav = ag.lancamento_avulso  # lazy-load via relationship

        # Dados da pessoa (beneficiário)
        pessoa = ag.pessoa_financeiro if ag.pessoa_financeiro_id else None

        # Parcelas do agendamento (para detalhamento, não para cálculo de totais)
        parcelas = ParcelaCategorizacaoModel.obter_parcelas_por_agendamento(ag.id) if ag.id else []

        # Valor original vem da ORIGEM (Faturamento ou Lançamento Avulso),
        # não do agendamento — o agendamento pode ter valor parcial/rateado.
        if fat:
            valor_original = fat.valor_total or 0
        elif lav:
            valor_original = lav.valor_movimentacao_100 or 0
        else:
            # Fallback: usa o valor do próprio agendamento
            valor_original = ag.valor_total_100 or 0

        # Total pago: prioridade valor_conciliado_100 (fluxo de conciliação),
        # fallback valor_total_100 do agendamento (quando conciliado sem esse campo preenchido)
        if ag.valor_conciliado_100 is not None:
            total_pago = ag.valor_conciliado_100
        else:
            total_pago = ag.valor_total_100 or 0

        saldo = valor_original - total_pago

        # Situação
        situacao_nome = ag.situacao.situacao if ag.situacao else 'Sem situação'
        situacao_id = ag.situacao_pagamento_id

        # Centro de custo e plano de contas (parse do JSON real)
        centros_custo_str = ContasAPARService._extrair_centros_custo(ag.centros_custo_json)
        plano_contas_str = ContasAPARService._extrair_plano_contas(ag.categorias_json)

        # Tipo de operação (para contexto no template)
        TIPOS_OPERACAO = {1: 'Carga', 2: 'Lançamento', 3: 'Crédito'}
        if fat:
            tipo_operacao_label = TIPOS_OPERACAO.get(fat.tipo_operacao, '-')
        else:
            tipo_operacao_label = 'Avulso'

        # Código de identificação: Faturamento > Lançamento Avulso > '-'
        if fat:
            codigo = fat.codigo_faturamento
        elif lav:
            codigo = f'LAV - {ag.lancamento_avulso_id}'
        else:
            codigo = '-'

        # Descrição: prioridade ag.descricao → lav.descricao → código
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
        """
        Extrai nomes do plano de contas a partir de categorias_json.
        Formato real: [{"categoria_id": 5, "nome": "Frete", "categoria": "2.01 - Frete", ...}]
        Tenta 'nome' primeiro, depois 'categoria' como fallback.
        """
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
        """
        Extrai nomes dos centros de custo a partir de centros_custo_json.
        Formato real: [{"centro": "3", "centro_nome": "Vendas", "percentual": "70", ...}]
        Tenta 'centro_nome' (enriquecido) primeiro, senão resolve 'centro' (ID) via model.
        """
        if not json_data:
            return '-'
        try:
            dados = json_lib.loads(json_data) if isinstance(json_data, str) else json_data
            if not isinstance(dados, list):
                return '-'
            nomes = []
            centros_map = None  # carregamento lazy (no máximo 1 query)
            for item in dados:
                if not isinstance(item, dict):
                    continue
                nome = item.get('centro_nome', '')
                if not nome:
                    centro_val = str(item.get('centro', ''))
                    if centro_val.isdigit():
                        # Resolve o nome pelo ID via CentroCustoModel
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
    def _obter_pendentes_ap(data_referencia, filtros):
        """
        Pendentes AP: consulta as 4 tabelas de origem.

        Fontes:
          - fin_fornecedor_a_pagar  (fornecedores-a-faturar)
          - fin_frete_a_pagar       (fretes-a-faturar)
          - fin_extrator_a_pagar    (extratores-a-pagar)
          - fin_comissionado_a_pagar (comissionados-a-pagar)

        Critério de pendência: situacao_pagamento_id == 2 (Pendente)
        """
        from sistema.models_views.faturamento.cargas_a_faturar.fornecedor.fornecedor_a_pagar_model import FornecedorPagarModel
        from sistema.models_views.faturamento.cargas_a_faturar.transportadora.frete_a_pagar_model import FretePagarModel
        from sistema.models_views.faturamento.cargas_a_faturar.extrator.extrator_a_pagar_model import ExtratorPagarModel
        from sistema.models_views.faturamento.cargas_a_faturar.comissionado.comissionado_a_pagar_model import ComissionadoPagarModel

        SITUACAO_PENDENTE = 2

        models_config = [
            (FornecedorPagarModel, 'Fornecedor'),
            (FretePagarModel, 'Frete'),
            (ExtratorPagarModel, 'Extrator'),
            (ComissionadoPagarModel, 'Comissionado'),
        ]

        resultado = []

        for Model, tipo_label in models_config:
            query = Model.query.filter(
                Model.deletado == False,
                Model.ativo == True,
                Model.situacao_pagamento_id == SITUACAO_PENDENTE,
            )

            # Emitidos até a data de referência
            if data_referencia:
                query = query.filter(Model.data_cadastro <= data_referencia)

            # Filtro por fornecedor (FK direto em todas as 4 tabelas _a_pagar)
            if filtros.get('pessoa_id'):
                query = query.filter(Model.fornecedor_id == filtros['pessoa_id'])

            # Filtro por plano de contas (FK direto)
            if filtros.get('plano_contas_id'):
                query = query.filter(Model.plano_conta_id == filtros['plano_contas_id'])

            # Filtro por situação (sobrescreve o padrão se informado)
            if filtros.get('situacao_id'):
                query = query.filter(Model.situacao_pagamento_id == filtros['situacao_id'])

            records = query.all()

            for record in records:
                item = ContasAPARService._serializar_registro_a_pagar(record, tipo_label)

                # Dias de atraso
                vencimento = record.data_entrega_ticket
                if vencimento and vencimento < data_referencia:
                    item['dias_atraso'] = (data_referencia - vencimento).days
                else:
                    item['dias_atraso'] = 0

                if item['saldo_100'] > 0:
                    resultado.append(item)

        # Ordenar por data de vencimento ascendente
        resultado.sort(key=lambda x: x['data_vencimento'] or date.min)
        return resultado

    # --------------------------------------------------------------------- #
    #  SERIALIZAÇÃO — VENDAS ENTREGUES (AR)
    # --------------------------------------------------------------------- #

    @staticmethod
    def _serializar_venda_entregue(registro):
        """
        Serializa um RegistroOperacionalModel (venda entregue) no formato
        padrão dos relatórios de pendentes AR.

        Campos mapeados:
          - valor_original: valor_total_nota_100 da NF de venda
          - pessoa: cliente da carga (CargaModel.cliente)
          - vencimento: data_entrega_ticket
          - situação: situacao_financeira do registro operacional
        """
        carga = registro.solicitacao
        cliente = carga.cliente if carga else None
        produto = carga.produto if carga else None
        bitola = carga.bitola if carga else None

        # Situação financeira
        situacao_nome = registro.situacao.situacao if registro.situacao else 'Sem situação'

        valor = registro.valor_total_nota_100 or 0

        # Descrição: Produto | Bitola (quando disponível)
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
    def _obter_pendentes_ar(data_referencia, filtros):
        """
        Pendentes AR: consulta vendas entregues (RegistroOperacionalModel)
        que ainda não foram recebidas.

        Fonte: re_registro_operacional JOIN car_carga
          - CargaModel.ticket_emitido == True (entregue)
          - situacao_financeira_id == 2 (Pendente)
        """
        query = (
            db.session.query(RegistroOperacionalModel)
            .join(CargaModel, RegistroOperacionalModel.solicitacao_nf_id == CargaModel.id)
            .filter(
                RegistroOperacionalModel.deletado == False,
                RegistroOperacionalModel.ativo == True,
                CargaModel.deletado == False,
                CargaModel.ativo == True,
                CargaModel.ticket_emitido == True,
                RegistroOperacionalModel.situacao_financeira_id == SITUACAO_VENDA_PENDENTE,
            )
        )

        # Emitidos até a data de referência
        if data_referencia:
            query = query.filter(RegistroOperacionalModel.data_cadastro <= data_referencia)

        # Filtro por cliente (FK em CargaModel)
        if filtros.get('pessoa_id'):
            query = query.filter(CargaModel.cliente_id == filtros['pessoa_id'])

        # Filtro por situação específica
        if filtros.get('situacao_id'):
            query = query.filter(
                RegistroOperacionalModel.situacao_financeira_id == filtros['situacao_id']
            )

        query = query.order_by(RegistroOperacionalModel.data_entrega_ticket.asc())
        registros = query.all()

        resultado = []
        for registro in registros:
            item = ContasAPARService._serializar_venda_entregue(registro)

            if item['saldo_100'] > 0:
                # Dias de atraso (baseado na data de entrega do ticket)
                vencimento = registro.data_entrega_ticket
                if vencimento and vencimento < data_referencia:
                    item['dias_atraso'] = (data_referencia - vencimento).days
                else:
                    item['dias_atraso'] = 0

                resultado.append(item)

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
    def _obter_emissoes_tabela_operacional(codigo, config, filtros):
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

            # Filtro por pessoa: buscar IDs de vínculo operacional
            if filtros.get('pessoa_id'):
                pessoa_id = filtros['pessoa_id']
                if hasattr(Model, 'fornecedor_id'):
                    ids_vinculo = ContasAPARService._obter_ids_vinculo_pessoa(pessoa_id, 'fornecedor')
                    if ids_vinculo:
                        query = query.filter(Model.fornecedor_id.in_(ids_vinculo))
                    else:
                        return []  # Pessoa sem vínculo com fornecedor
                elif hasattr(Model, 'transportadora_id'):
                    ids_vinculo = ContasAPARService._obter_ids_vinculo_pessoa(pessoa_id, 'transportadora')
                    if ids_vinculo:
                        query = query.filter(Model.transportadora_id.in_(ids_vinculo))
                    else:
                        return []  # Pessoa sem vínculo com transportadora
                elif hasattr(Model, 'extrator_id'):
                    ids_vinculo = ContasAPARService._obter_ids_vinculo_pessoa(pessoa_id, 'extrator')
                    if ids_vinculo:
                        query = query.filter(Model.extrator_id.in_(ids_vinculo))
                    else:
                        return []  # Pessoa sem vínculo com extrator
                elif hasattr(Model, 'comissionado_id'):
                    ids_vinculo = ContasAPARService._obter_ids_vinculo_pessoa(pessoa_id, 'comissionado')
                    if ids_vinculo:
                        query = query.filter(Model.comissionado_id.in_(ids_vinculo))
                    else:
                        return []  # Pessoa sem vínculo com comissionado

            registros = query.order_by(getattr(Model, campo_data).desc()).all()

            resultado = []
            for reg in registros:
                valor = getattr(reg, campo_valor) or 0
                data_emissao = getattr(reg, campo_data) if hasattr(reg, campo_data) else reg.data_cadastro

                # Identificar a pessoa
                pessoa_nome = '-'
                if hasattr(reg, 'destinatario_nome') and reg.destinatario_nome:
                    pessoa_nome = reg.destinatario_nome
                elif hasattr(reg, 'cliente') and reg.cliente:
                    pessoa_nome = reg.cliente.identificacao if hasattr(reg.cliente, 'identificacao') else str(reg.cliente)
                elif hasattr(reg, 'fornecedor') and reg.fornecedor:
                    pessoa_nome = reg.fornecedor.identificacao
                elif hasattr(reg, 'transportadora') and reg.transportadora:
                    pessoa_nome = reg.transportadora.identificacao
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
                return ContasAPARService._obter_emissoes_tabela_operacional(codigo, categorias_map[codigo], filtros)
            return ContasAPARService._obter_emissoes_agendamentos(filtros, tipo_categoria, plano_contas_id_filtro=int(plano_contas_id))
        
        # Buscar tudo: tabelas operacionais + agendamentos
        for codigo, config in categorias_map.items():
            resultado.extend(ContasAPARService._obter_emissoes_tabela_operacional(codigo, config, filtros))
        
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
    def obter_baixas(direcao_str, filtros=None):
        """
        Pagamentos/Recebimentos realizados (conciliados) no período.
        Filtro de data aplicado sobre data_pagamento (parcela).
        Retorna apenas agendamentos com situação Conciliado (ID 8).
        """
        filtros = filtros or {}
        filtros['data_campo'] = 'data_pagamento'

        query = ContasAPARService._base_query(direcao_str)
        query = ContasAPARService._aplicar_filtros(query, filtros)

        # Somente títulos conciliados (efetivamente pagos/recebidos)
        query = query.filter(
            AgendamentoPagamentoModel.situacao_pagamento_id.in_(SITUACOES_LIQUIDADAS)
        )

        query = query.order_by(AgendamentoPagamentoModel.data_vencimento.desc())

        agendamentos = query.all()
        return [ContasAPARService._serializar_agendamento(ag) for ag in agendamentos]

    @staticmethod
    def obter_pendentes(direcao_str, data_referencia=None, filtros=None):
        """
        Títulos pendentes na data de referência.
        Se data_referencia não fornecida, usa a data atual.

        AP: consulta diretamente as 4 tabelas de origem
            (fornecedor, frete, extrator, comissionado _a_pagar)
        AR: consulta AgendamentoPagamentoModel com situação 5/6/7
        """
        filtros = filtros or {}
        if not data_referencia:
            data_referencia = date.today()
        # --- AP: dados vêm das 4 tabelas de origem ---
        if direcao_str == 'ap':
            return ContasAPARService._obter_pendentes_ap(data_referencia, filtros)

        # --- AR: dados vêm das vendas entregues (RegistroOperacionalModel) ---
        return ContasAPARService._obter_pendentes_ar(data_referencia, filtros)

    # --------------------------------------------------------------------- #
    #  TOTALIZADORES
    # --------------------------------------------------------------------- #

    @staticmethod
    def totalizar(registros):
        """
        Retorna totais a partir de uma lista de registros serializados.
        """
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
