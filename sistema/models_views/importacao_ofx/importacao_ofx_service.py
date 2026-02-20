"""
Service para operações de Importação OFX.

Centraliza toda a lógica de negócio, queries complexas e operações
de conciliação do módulo OFX, mantendo o model focado apenas em
definição de colunas, relacionamentos e properties.
"""

from datetime import datetime
from sqlalchemy import and_, or_, func
from sistema.models_views.base_model import db
from sistema._utilitarios import *


class ImportacaoOfxService:
    """Service com métodos estáticos para operações de Importação OFX."""


    @staticmethod
    def obter_transacao_por_fitid(fitid):
        """Retorna a transação OFX pelo fitid (não deletada e não conciliada)."""
        from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx
        return db.session.query(ImportacaoOfx).filter(
            ImportacaoOfx.fitid == fitid,
            ImportacaoOfx.ofx_deletada == False,
            ImportacaoOfx.conciliado == False
        ).first()

    @staticmethod
    def obter_transacoes_com_filtros():
        """Retorna todas as transações não deletadas."""
        from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx
        return db.session.query(ImportacaoOfx).filter(
            ImportacaoOfx.ofx_deletada == False
        ).all()

    @staticmethod
    def obter_transacoes_query_com_filtros(pagina=1, por_pagina=50):
        """
        Retorna transações não deletadas e não conciliadas com paginação otimizada.
        Retorna um dicionário com as transações, total e dados de paginação.
        """
        from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx

        query = db.session.query(ImportacaoOfx).filter(
            ImportacaoOfx.ofx_deletada == False,
            ImportacaoOfx.conciliado == False,
            ImportacaoOfx.processado == False
        )

        total_transacoes = query.count()

        offset = (pagina - 1) * por_pagina
        transacoes = query.order_by(
            ImportacaoOfx.data_transacao.desc(),
            ImportacaoOfx.id.desc()
        ).offset(offset).limit(por_pagina).all()

        total_paginas = (total_transacoes + por_pagina - 1) // por_pagina

        return {
            'transacoes': transacoes,
            'total_transacoes': total_transacoes,
            'pagina': pagina,
            'total_paginas': total_paginas,
            'por_pagina': por_pagina
        }

    @staticmethod
    def filtrar_por_conciliacao(conciliado=None, batch_id=None):
        """
        Filtra transações por status de conciliação (True, False ou None para todos).
        Pode filtrar também por batch_id se informado.
        """
        from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx

        query = db.session.query(ImportacaoOfx)
        if conciliado is not None:
            query = query.filter(ImportacaoOfx.conciliado == conciliado)
        if batch_id:
            query = query.filter(ImportacaoOfx.batch_importacao == batch_id)
        return query.order_by(
            ImportacaoOfx.data_transacao.desc(),
            ImportacaoOfx.id.desc()
        ).limit(10).all()

    @staticmethod
    def obter_transacoes_por_periodo(data_inicio=None, data_fim=None):
        """Retorna transações filtradas por período."""
        from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx

        query = db.session.query(ImportacaoOfx)
        if data_inicio:
            query = query.filter(ImportacaoOfx.data_transacao >= data_inicio)
        if data_fim:
            query = query.filter(ImportacaoOfx.data_transacao <= data_fim)
        return query.order_by(
            ImportacaoOfx.data_transacao.desc(),
            ImportacaoOfx.id.desc()
        ).all()

    @staticmethod
    def obter_transacoes_por_tipo(tipo_movimento):
        """Retorna transações filtradas por tipo (CREDITO ou DEBITO)."""
        from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx

        return db.session.query(ImportacaoOfx).filter(
            ImportacaoOfx.tipo_movimento == tipo_movimento
        ).order_by(
            ImportacaoOfx.data_transacao.desc(),
            ImportacaoOfx.id.desc()
        ).all()

    @staticmethod
    def obter_transacoes_nao_processadas():
        """Retorna transações que ainda não foram processadas/categorizadas."""
        from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx

        return db.session.query(ImportacaoOfx).filter(
            ImportacaoOfx.processado == False
        ).order_by(
            ImportacaoOfx.data_transacao.desc(),
            ImportacaoOfx.id.desc()
        ).all()

    @staticmethod
    def obter_conciliacoes_reversiveis(batch_id=None, limit=50):
        """Retorna lista de transações conciliadas que podem ser revertidas."""
        from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx

        query = ImportacaoOfx.query.filter(
            ImportacaoOfx.dados_conciliacao_json.isnot(None)
        )
        if batch_id:
            query = query.filter(ImportacaoOfx.batch_importacao == batch_id)
        return query.order_by(ImportacaoOfx.data_conciliacao.desc()).limit(limit).all()


    @staticmethod
    def obter_ultimo_batch_importacao(conta_bancaria_id=None):
        """Retorna o batch_importacao mais recente."""
        from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx

        try:
            query = db.session.query(ImportacaoOfx).filter(
                ImportacaoOfx.ofx_deletada == False
            )
            if conta_bancaria_id:
                query = query.filter(ImportacaoOfx.conta_bancaria_id == conta_bancaria_id)

            ultima_transacao = query.order_by(ImportacaoOfx.data_importacao.desc()).first()
            return ultima_transacao.batch_importacao if ultima_transacao else None
        except Exception as e:
            return None

    @staticmethod
    def truncar_tabela():
        """
        Remove todas as transações da tabela para nova importação.
        Usa TRUNCATE para redefinir até os IDs (auto_increment).
        """
        from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx

        try:
            db.session.execute(db.text(f"TRUNCATE TABLE {ImportacaoOfx.__tablename__}"))
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            try:
                db.session.query(ImportacaoOfx).delete()
                try:
                    db.session.execute(db.text(f"ALTER TABLE {ImportacaoOfx.__tablename__} AUTO_INCREMENT = 1"))
                except:
                    pass
                db.session.commit()
                return True
            except Exception as e2:
                db.session.rollback()
                return False

    @staticmethod
    def inserir_transacoes_lote(transacoes_data, arquivo_info, conta_bancaria_id=None):
        """Insere transações OFX em lote, ignorando duplicatas por fitid na mesma conta."""
        from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx

        try:
            if not transacoes_data:
                return False, "Nenhuma transação para inserir"

            from uuid import uuid4
            batch_id = str(uuid4())[:8]

            fitids_para_importar = [t.get('fitid') for t in transacoes_data if t.get('fitid')]

            fitids_ja_existentes = set()
            if fitids_para_importar and conta_bancaria_id:
                fitids_ja_existentes = {row[0] for row in db.session.query(ImportacaoOfx.fitid).filter(
                    ImportacaoOfx.fitid.in_(fitids_para_importar),
                    ImportacaoOfx.conta_bancaria_id == conta_bancaria_id
                ).all()}

            transacoes_filtradas = [
                t for t in transacoes_data
                if t.get('fitid') not in fitids_ja_existentes
            ]

            if not transacoes_filtradas:
                total_duplicadas = len(transacoes_data) - len(transacoes_filtradas)
                if total_duplicadas > 0:
                    return True, {
                        'total': 0,
                        'batch_id': batch_id,
                        'duplicadas': total_duplicadas,
                        'mensagem': f'{total_duplicadas} transação(ões) já existe(m) nesta conta bancária e foi(ram) ignorada(s)'
                    }
                return True, {'total': 0, 'batch_id': batch_id}

            resumo = arquivo_info.get('resumo', {})
            conta_info = resumo.get('conta', {})
            instituicao_info = resumo.get('instituicao', {})
            periodo_info = resumo.get('periodo', {})

            transacoes_obj = []
            for transacao in transacoes_filtradas:
                data_transacao = transacao.get('date')

                transacao_obj = ImportacaoOfx(
                    fitid=transacao.get('fitid'),
                    refnum=transacao.get('refnum'),
                    data_transacao=data_transacao,
                    valor=float(transacao.get('amount', 0)),
                    valor_formatado=transacao.get('valor_formatado'),
                    tipo_movimento=transacao.get('tipo_movimento'),
                    memo=transacao.get('memo'),
                    descricao_limpa=transacao.get('descricao_limpa'),
                    categoria_automatica=transacao.get('categoria_automatica'),
                    batch_importacao=batch_id,
                    arquivo_nome=arquivo_info.get('arquivo_nome'),
                    data_importacao=datetime.fromisoformat(arquivo_info.get('data_importacao')),
                    banco_id=conta_info.get('routing_number') or conta_info.get('banco_id') or conta_info.get('bank_id'),
                    conta_id=conta_info.get('account_id') or conta_info.get('conta_id') or conta_info.get('acct_id'),
                    tipo_conta=conta_info.get('account_type') or conta_info.get('tipo_conta') or conta_info.get('acct_type'),
                    moeda=resumo.get('moeda', 'BRL'),
                    instituicao_org=instituicao_info.get('organization') or instituicao_info.get('org') or instituicao_info.get('nome'),
                    instituicao_fid=instituicao_info.get('fid') or instituicao_info.get('fi_id'),
                    data_inicio_extrato=periodo_info.get('primeira_transacao'),
                    data_fim_extrato=periodo_info.get('ultima_transacao'),
                    conta_bancaria_id=conta_bancaria_id
                )
                transacoes_obj.append(transacao_obj)

            db.session.add_all(transacoes_obj)
            db.session.commit()

            total_inseridas = len(transacoes_obj)
            total_duplicadas = len(transacoes_data) - total_inseridas

            if total_duplicadas > 0:
                pass

            resultado = {'total': total_inseridas, 'batch_id': batch_id}
            if total_duplicadas > 0:
                resultado['duplicadas'] = total_duplicadas
                resultado['mensagem_duplicadas'] = f'{total_duplicadas} transação(ões) já existia(m) nesta conta e foi(ram) ignorada(s)'

            return True, resultado

        except Exception as e:
            db.session.rollback()
            return False, str(e)


    @staticmethod
    def obter_resumo_importacao(data_inicio=None, data_fim=None, batch_id=None, conciliado=None,
                                 ftid=None, valor='', descricao=None, tipo_movimentacao=None,
                                 conta_bancaria_id=None):
        """
        Retorna resumo estatístico das transações importadas com filtros diversos.
        Se batch_id for None e conciliado==True, retorna resumo de todas as transações conciliadas.
        """
        from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx

        try:
            query = db.session.query(ImportacaoOfx)

            if conta_bancaria_id is not None:
                query = query.filter(ImportacaoOfx.conta_bancaria_id == conta_bancaria_id)
            if data_inicio is not None:
                query = query.filter(ImportacaoOfx.data_transacao >= data_inicio)
            if data_fim is not None:
                query = query.filter(ImportacaoOfx.data_transacao <= data_fim)
            if batch_id is not None:
                query = query.filter(ImportacaoOfx.batch_importacao == batch_id)
            if conciliado is not None:
                query = query.filter(ImportacaoOfx.conciliado == conciliado)
            if ftid:
                query = query.filter(ImportacaoOfx.fitid.ilike(f'%{ftid}%'))
            if valor and valor.strip() and valor.strip() != 'R$ 0,00':
                query = query.filter(ImportacaoOfx.valor_formatado.ilike(f'%{valor}%'))
            if descricao and descricao.strip():
                query = query.filter(or_(
                    ImportacaoOfx.descricao_limpa.ilike(f'%{descricao}%'),
                    ImportacaoOfx.memo.ilike(f'%{descricao}%')
                ))
            if tipo_movimentacao:
                if tipo_movimentacao == 'entrada':
                    query = query.filter(ImportacaoOfx.valor > 0)
                elif tipo_movimentacao == 'saida':
                    query = query.filter(ImportacaoOfx.valor < 0)

            total_transacoes = query.count()
            total_creditos = query.filter(ImportacaoOfx.valor > 0).with_entities(func.sum(ImportacaoOfx.valor)).scalar() or 0
            soma_debitos = query.filter(ImportacaoOfx.valor < 0).with_entities(func.sum(ImportacaoOfx.valor)).scalar() or 0

            creditos_valor = float(total_creditos)
            debitos_valor = abs(float(soma_debitos))
            saldo_liquido = creditos_valor - debitos_valor

            ultima_importacao = query.order_by(ImportacaoOfx.data_importacao.desc()).first()

            resumo = {
                'batch_id': batch_id,
                'total_transacoes': total_transacoes,
                'total_creditos': creditos_valor,
                'total_debitos': debitos_valor,
                'saldo_liquido': saldo_liquido,
                'creditos_formatado': f"R$ {creditos_valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                'debitos_formatado': f"R$ {debitos_valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                'saldo_formatado': f"R$ {saldo_liquido:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            }

            if ultima_importacao:
                resumo.update({
                    'arquivo_nome': ultima_importacao.arquivo_nome,
                    'data_importacao': ultima_importacao.data_importacao.isoformat() if ultima_importacao.data_importacao else '',
                    'banco': ultima_importacao.instituicao_org,
                    'banco_id': ultima_importacao.banco_id,
                    'conta': ultima_importacao.conta_id,
                    'tipo_conta': ultima_importacao.tipo_conta,
                    'periodo_inicio': ultima_importacao.data_inicio_extrato,
                    'periodo_fim': ultima_importacao.data_fim_extrato
                })

            return resumo
        except Exception as e:
            return None

    @staticmethod
    def obter_historico_importacoes():
        """Retorna histórico de importações agrupado por batch."""
        from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx

        try:
            batches = db.session.query(
                ImportacaoOfx.batch_importacao,
                ImportacaoOfx.arquivo_nome,
                ImportacaoOfx.data_importacao,
                func.count(ImportacaoOfx.id).label('total_transacoes'),
                func.sum(func.case([(ImportacaoOfx.tipo_movimento == 'CREDITO', ImportacaoOfx.valor)], else_=0)).label('total_creditos'),
                func.sum(func.case([(ImportacaoOfx.tipo_movimento == 'DEBITO', func.abs(ImportacaoOfx.valor))], else_=0)).label('total_debitos')
            ).group_by(
                ImportacaoOfx.batch_importacao, ImportacaoOfx.arquivo_nome, ImportacaoOfx.data_importacao
            ).order_by(ImportacaoOfx.data_importacao.desc()).all()

            historico = []
            for batch in batches:
                historico.append({
                    'batch_id': batch.batch_importacao,
                    'arquivo_nome': batch.arquivo_nome,
                    'data_importacao': batch.data_importacao,
                    'total_transacoes': batch.total_transacoes,
                    'total_creditos': float(batch.total_creditos or 0),
                    'total_debitos': float(batch.total_debitos or 0)
                })
            return historico

        except Exception as e:
            return []

    @staticmethod
    def obter_estatisticas_por_categoria():
        """Retorna estatísticas agrupadas por categoria."""
        from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx

        try:
            categoria_final = func.coalesce(ImportacaoOfx.categoria_manual, ImportacaoOfx.categoria_automatica, 'Sem Categoria')
            resultado = db.session.query(
                categoria_final.label('categoria'),
                func.count(ImportacaoOfx.id).label('quantidade'),
                func.sum(ImportacaoOfx.valor).label('total'),
                ImportacaoOfx.tipo_movimento
            ).group_by(categoria_final, ImportacaoOfx.tipo_movimento).all()
            return resultado
        except Exception as e:
            return []

    @staticmethod
    def obter_estatisticas_transacoes(batch_id=None, conta_bancaria_id=None):
        """Retorna estatísticas das transações importadas (total, conciliadas, não conciliadas)."""
        from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx

        try:
            query = ImportacaoOfx.query

            if batch_id:
                query = query.filter(ImportacaoOfx.batch_importacao == batch_id)
            elif batch_id is None:
                ultimo_batch = ImportacaoOfxService.obter_ultimo_batch_importacao()
                if ultimo_batch:
                    query = query.filter(ImportacaoOfx.batch_importacao == ultimo_batch)

            if conta_bancaria_id:
                query = query.filter(ImportacaoOfx.conta_bancaria_id == conta_bancaria_id)

            total = query.count()
            conciliadas = query.filter(ImportacaoOfx.conciliado == True).count()
            nao_conciliadas = query.filter(ImportacaoOfx.conciliado == False).count()

            return {
                'total': total,
                'conciliadas': conciliadas,
                'nao_conciliadas': nao_conciliadas
            }

        except Exception as e:
            return {'total': 0, 'conciliadas': 0, 'nao_conciliadas': 0}


    @staticmethod
    def calcular_diferenca(valor_ofx, valores_conciliados):
        """
        Calcula diferença entre valor OFX e valores conciliados.
        Retorna apenas a diferença se for positiva.
        """
        try:
            total_conciliado = sum(valores_conciliados)
            diferenca = float(valor_ofx) - float(total_conciliado)
            return diferenca if diferenca > 0.01 else 0
        except:
            return 0


    @staticmethod
    def marcar_como_processado(transacao, categoria_manual=None, observacoes=None):
        """Marca a transação como processada."""
        try:
            transacao.processado = True
            if categoria_manual:
                transacao.categoria_manual = categoria_manual
            if observacoes:
                transacao.observacoes = observacoes
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            return False

    @staticmethod
    def salvar_dados_conciliacao(transacao, tipo_conciliacao, agendamentos_ids=None,
                                 faturamentos_ids=None, movimentacoes_ids=None,
                                 lancamentos_avulsos_ids=None, valor_agendamento=None,
                                 usuario_id=None, observacoes=None):
        """Salva os dados da conciliação em formato JSON para permitir reversão posterior."""
        try:
            dados_conciliacao = {
                'fitid': transacao.fitid,
                'tipo_conciliacao': tipo_conciliacao,
                'data_conciliacao': DataHora.obter_data_atual_padrao_en(),
                'usuario_conciliacao_id': usuario_id,
                'observacoes': observacoes,
                'agendamentos_ids': agendamentos_ids or [],
                'faturamentos_ids': faturamentos_ids or [],
                'movimentacoes_ids': movimentacoes_ids or [],
                'lancamentos_avulsos_ids': lancamentos_avulsos_ids or [],
                'valor_transacao': float(transacao.valor),
                'valor_agendamento': int(valor_agendamento) if valor_agendamento else 0,
                'data_transacao': transacao.data_transacao.isoformat() if transacao.data_transacao else None
            }

            transacao.dados_conciliacao_json = dados_conciliacao

            if not transacao.conciliacao_parcial:
                transacao.conciliado = True

            transacao.tipo_conciliacao = tipo_conciliacao
            transacao.data_conciliacao = DataHora.obter_data_atual_padrao_en()
            transacao.usuario_conciliacao_id = usuario_id
            transacao.observacoes_conciliacao = observacoes

            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            return False

    @staticmethod
    def reverter_conciliacao(transacao):
        """
        Reverte uma conciliação, restaurando o estado anterior dos registros.
        Suporta reversão de conciliações totais e parciais.
        """
        try:
            if not transacao.dados_conciliacao_json:
                return False, "Transação não possui dados para reversão"

            dados = transacao.dados_conciliacao_json

            from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
            from sistema.models_views.financeiro.operacional.categorizar_fatura.categorizacao_model import AgendamentoPagamentoModel
            from sistema.models_views.financeiro.movimentacao_financeira.movimentacao_financeira_model import MovimentacaoFinanceiraModel
            from sistema.models_views.financeiro.lancamento_avulso.lancamento_avulso_model import LancamentoAvulsoModel

            if dados.get('agendamentos_ids'):
                for agendamento_id in dados['agendamentos_ids']:
                    agendamento = AgendamentoPagamentoModel.obter_agendamento_por_id(agendamento_id)
                    if agendamento:
                        agendamento.situacao_pagamento_id = 6
                        agendamento.valor_conciliado_100 = None
                        db.session.add(agendamento)

            if dados.get('faturamentos_ids'):
                for faturamento_id in dados['faturamentos_ids']:
                    faturamento = FaturamentoModel.obter_faturamento_por_id(faturamento_id)
                    if faturamento:
                        faturamento.situacao_pagamento_id = 6
                        db.session.add(faturamento)

            if dados.get('lancamentos_avulsos_ids'):
                for lancamento_id in dados['lancamentos_avulsos_ids']:
                    lancamento = LancamentoAvulsoModel.obter_lancamento_por_id(lancamento_id)
                    if lancamento:
                        lancamento.situacao_pagamento_id = 6
                        db.session.add(lancamento)

            if dados.get('movimentacoes_ids'):
                conta_bancaria_id = None

                for movimentacao_id in dados['movimentacoes_ids']:
                    movimentacao = MovimentacaoFinanceiraModel.obter_movimentacoes_por_id(movimentacao_id)
                    if movimentacao:
                        if conta_bancaria_id is None:
                            conta_bancaria_id = movimentacao.conta_bancaria_id
                        movimentacao.ativo = False
                        movimentacao.deletado = True

                valor_agendamento = dados.get('valor_agendamento', 0)
                if valor_agendamento > 0 and conta_bancaria_id:
                    if transacao.valor > 0:
                        tipo_movimentacao_reversao = 2
                        descricao_reversao = f"Reversão de conciliação OFX - Débito de ajuste (FITID: {transacao.fitid})"
                    else:
                        tipo_movimentacao_reversao = 1
                        descricao_reversao = f"Reversão de conciliação OFX - Crédito de ajuste (FITID: {transacao.fitid})"

                    movimentacao_reversao = MovimentacaoFinanceiraModel(
                        conta_bancaria_id=conta_bancaria_id,
                        valor_movimentacao_100=valor_agendamento,
                        observacao_movimentacao=descricao_reversao,
                        tipo_movimentacao=tipo_movimentacao_reversao,
                        data_movimentacao=DataHora.obter_data_atual_padrao_en(),
                        usuario_id=dados.get('usuario_conciliacao_id')
                    )
                    db.session.add(movimentacao_reversao)

            from sistema.models_views.financeiro.movimentacao_financeira.saldo_movimentacao_financeira_model import SaldoMovimentacaoFinanceiraModel

            valor_agendamento = dados.get('valor_agendamento', 0)
            if valor_agendamento > 0 and dados.get('agendamentos_ids'):
                primeiro_agendamento = AgendamentoPagamentoModel.obter_agendamento_por_id(dados['agendamentos_ids'][0])
                if primeiro_agendamento:
                    saldo_conta = SaldoMovimentacaoFinanceiraModel.query.filter(
                        SaldoMovimentacaoFinanceiraModel.conta_bancaria_id == primeiro_agendamento.conta_bancaria_id,
                        SaldoMovimentacaoFinanceiraModel.ativo == True,
                        SaldoMovimentacaoFinanceiraModel.deletado == False
                    ).first()

                    if saldo_conta:
                        if transacao.valor > 0:
                            saldo_conta.valor_total_saldo_100 -= valor_agendamento
                        else:
                            saldo_conta.valor_total_saldo_100 += valor_agendamento

                        saldo_conta.data_movimentacao = DataHora.obter_data_atual_padrao_en()
                        db.session.add(saldo_conta)

            transacao.tipo_conciliacao = None
            transacao.pagamento_id = None
            transacao.data_conciliacao = None
            transacao.usuario_conciliacao_id = None
            transacao.observacoes_conciliacao = None
            transacao.dados_conciliacao_json = None
            transacao.resetar_utilizacao()

            db.session.commit()
            return True, "Conciliação revertida com sucesso"

        except Exception as e:
            db.session.rollback()
            error_msg = f"Erro ao reverter conciliação: {str(e)}"
            return False, error_msg
