from ..base_model import BaseModel, db
from sqlalchemy import and_, or_, func
from sistema._utilitarios import *
from datetime import datetime


class ImportacaoOfx(BaseModel):
    """
    Model para armazenar transações importadas de arquivos OFX.
    A tabela é truncada a cada nova importação.
    """
    
    __tablename__ = "im_importacao_ofx"
    
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    
    # Dados da transação OFX
    fitid = db.Column(db.String(50), nullable=False)
    refnum = db.Column(db.String(50), nullable=True)
    data_transacao = db.Column(db.Date, nullable=False)
    valor = db.Column(db.Numeric(15, 2), nullable=False)
    valor_formatado = db.Column(db.String(20), nullable=True)
    tipo_movimento = db.Column(db.String(10), nullable=False)
    memo = db.Column(db.Text, nullable=True)
    descricao_limpa = db.Column(db.Text, nullable=True)
    categoria_automatica = db.Column(db.String(100), nullable=True)
    
    # Dados do arquivo importado
    arquivo_nome = db.Column(db.String(255), nullable=False)
    data_importacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    batch_importacao = db.Column(db.String(50), nullable=False, index=True)
    
    # Dados da conta bancária (extraídos do arquivo OFX)
    banco_id = db.Column(db.String(10), nullable=True)
    conta_id = db.Column(db.String(50), nullable=True)
    tipo_conta = db.Column(db.String(20), nullable=True)
    moeda = db.Column(db.String(3), nullable=True, default='BRL')
    
    # Dados da instituição financeira (extraídos do arquivo OFX)
    instituicao_org = db.Column(db.String(100), nullable=True)
    instituicao_fid = db.Column(db.String(100), nullable=True)
    
    # Período do extrato
    data_inicio_extrato = db.Column(db.String(10), nullable=True)
    data_fim_extrato = db.Column(db.String(10), nullable=True)
    
    # Controle e processamento
    processado = db.Column(db.Boolean, default=False, nullable=False)
    categoria_manual = db.Column(db.String(100), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)

    #Controle de conciliação
    conciliado = db.Column(db.Boolean, default=False, nullable=False)
    tipo_conciliacao = db.Column(db.String(50), nullable=True)
    pagamento_id = db.Column(db.Integer, nullable=True)
    data_conciliacao = db.Column(db.DateTime, nullable=True)
    usuario_conciliacao_id = db.Column(db.Integer, nullable=True)
    observacoes_conciliacao = db.Column(db.Text, nullable=True)
    
    # Controle de conciliação parcial
    valor_utilizado_100 = db.Column(db.Integer, nullable=True)  # Valor já utilizado em centavos
    conciliacao_parcial = db.Column(db.Boolean, default=False)
    
    # Dados da conciliação em JSON para permitir reversão
    dados_conciliacao_json = db.Column(db.JSON, nullable=True)
    
    # Controle de exclusão/ignorar movimentação
    ofx_deletada = db.Column(db.Boolean, default=False, nullable=False)
    ofx_justificativa_deletada = db.Column(db.String(50), nullable=True)
    
    conta_bancaria_id = db.Column(db.Integer, db.ForeignKey("con_conta_bancaria.id"), nullable=True)
    conta_bancaria = db.relationship("ContaBancariaModel", foreign_keys=[conta_bancaria_id], backref=db.backref("transacoes_ofx", lazy=True))
    
    # Índices para melhor performance
    __table_args__ = (
        db.Index('idx_ofx_fitid', 'fitid'),
        db.Index('idx_ofx_data_transacao', 'data_transacao'),
        db.Index('idx_ofx_tipo_movimento', 'tipo_movimento'),
        db.Index('idx_ofx_data_importacao', 'data_importacao'),
        db.Index('idx_ofx_batch_importacao', 'batch_importacao'),
    )
    
    def __repr__(self):
        return f'<OfxTransacao {self.fitid}: {self.valor_formatado} - {self.descricao_limpa[:50] if self.descricao_limpa else self.memo[:50]}...>'
    
    @property
    def categoria_final(self):
        """Retorna a categoria final (manual tem prioridade sobre automática)"""
        return self.categoria_manual if self.categoria_manual else self.categoria_automatica
    
    @property
    def descricao_final(self):
        """Retorna a descrição final (limpa tem prioridade sobre memo)"""
        return self.descricao_limpa if self.descricao_limpa else self.memo
    
    @property
    def valor_disponivel(self):
        """Retorna o valor ainda disponível para conciliação"""
        from decimal import Decimal
        valor_total = abs(self.valor) * 100  # Convert to centavos
        valor_usado = self.valor_utilizado_100 or 0
        return (valor_total - valor_usado) / 100
    
    @property
    def valor_disponivel_100(self):
        """Retorna o valor ainda disponível em centavos"""
        valor_total = int(abs(self.valor) * 100)
        valor_usado = self.valor_utilizado_100 or 0
        return valor_total - valor_usado
    
    @property
    def percentual_utilizado(self):
        """Retorna o percentual já utilizado da transação"""
        valor_total = int(abs(self.valor) * 100)
        if valor_total == 0:
            return 0
        valor_usado = self.valor_utilizado_100 or 0
        return (valor_usado / valor_total) * 100
    
    @property
    def pode_conciliar_valor(self):
        """Verifica se ainda há valor disponível para conciliação"""
        return self.valor_disponivel_100 > 0
    
    @property
    def esta_totalmente_utilizada(self):
        """Verifica se a transação foi totalmente utilizada"""
        return self.valor_disponivel_100 <= 0
    
    def adicionar_valor_utilizado(self, valor_centavos):
        """
        Adiciona um valor ao total já utilizado
        
        Args:
            valor_centavos (int): Valor em centavos para adicionar
            
        Returns:
            bool: True se adicionado com sucesso, False se exceder o valor total
        """
        if not isinstance(valor_centavos, int) or valor_centavos <= 0:
            return False
            
        valor_total_100 = int(abs(self.valor) * 100)
        novo_valor_utilizado = (self.valor_utilizado_100 or 0) + valor_centavos
        
        # Não permite utilizar mais que o valor total
        if novo_valor_utilizado > valor_total_100:
            return False
            
        self.valor_utilizado_100 = novo_valor_utilizado
        self.conciliacao_parcial = novo_valor_utilizado < valor_total_100
        
        # Se totalmente utilizado, marcar como conciliado
        if novo_valor_utilizado >= valor_total_100:
            self.conciliado = True
        
        return True
    
    def resetar_utilizacao(self):
        """Reset da utilização parcial"""
        self.valor_utilizado_100 = None
        self.conciliacao_parcial = False
        self.conciliado = False
    
    def obter_transacao_por_fitid(self, fitid):
        """
        Retorna a transação OFX pelo fitid
        """
        return db.session.query(ImportacaoOfx).filter(ImportacaoOfx.fitid == fitid, ImportacaoOfx.ofx_deletada == False,
                                                    ImportacaoOfx.conciliado == False).first()
    
    def obter_transacoes_com_filtros():
        return db.session.query(ImportacaoOfx).filter(ImportacaoOfx.ofx_deletada == False).all()
    
    @classmethod
    def obter_transacoes_query_com_filtros(cls, pagina=1, por_pagina=50):
        """
        Retorna transações não deletadas e não conciliadas com paginação otimizada.
        Retorna um dicionário com as transações, total e dados de paginação.
        """
        # Query base para transações não conciliadas
        query = db.session.query(cls).filter(
            cls.ofx_deletada == False,
            cls.conciliado == False,
            cls.processado == False
        )
        
        # Contar total antes da paginação
        total_transacoes = query.count()
        
        # Aplicar ordenação e paginação
        offset = (pagina - 1) * por_pagina
        transacoes = query.order_by(cls.data_transacao.desc(), cls.id.desc())\
                          .offset(offset)\
                          .limit(por_pagina)\
                          .all()
        
        # Calcular informações de paginação
        total_paginas = (total_transacoes + por_pagina - 1) // por_pagina
        
        return {
            'transacoes': transacoes,
            'total_transacoes': total_transacoes,
            'pagina': pagina,
            'total_paginas': total_paginas,
            'por_pagina': por_pagina
        }

    @classmethod
    def filtrar_por_conciliacao(cls, conciliado=None, batch_id=None):
        """
        Filtra transações por status de conciliação (True, False ou None para todos).
        Pode filtrar também por batch_id se informado.
        """
        query = db.session.query(cls)
        if conciliado is not None:
            query = query.filter(cls.conciliado == conciliado)
        if batch_id:
            query = query.filter(cls.batch_importacao == batch_id)
        return query.order_by(cls.data_transacao.desc(), cls.id.desc()).limit(10).all()
    
    @classmethod
    def truncar_tabela(cls):
        """
        Remove todas as transações da tabela para nova importação.
        Usa TRUNCATE para redefinir até os IDs (auto_increment).
        """
        try:
            # Usar TRUNCATE para redefinir completamente a tabela incluindo auto_increment
            db.session.execute(db.text(f"TRUNCATE TABLE {cls.__tablename__}"))
            db.session.commit()
            print("[INFO] Tabela de transações OFX truncada com sucesso (IDs redefinidos)")
            return True
        except Exception as e:
            db.session.rollback()
            # Fallback para DELETE caso TRUNCATE não funcione (algumas restrições de FK)
            try:
                print(f"[WARNING] TRUNCATE falhou, tentando DELETE: {e}")
                db.session.query(cls).delete()
                # Tentar redefinir auto_increment manualmente para MySQL
                try:
                    db.session.execute(db.text(f"ALTER TABLE {cls.__tablename__} AUTO_INCREMENT = 1"))
                except:
                    pass  # Ignorar se não for MySQL
                db.session.commit()
                print("[INFO] Tabela limpa com DELETE e auto_increment redefinido")
                return True
            except Exception as e2:
                db.session.rollback()
                print(f"[ERRO] Erro ao limpar tabela OFX: {e2}")
                return False
    

    @classmethod
    def calcular_diferenca(cls, valor_ofx, valores_conciliados):
        """
        Calcula diferença entre valor OFX e valores conciliados.
        Retorna apenas a diferença se for positiva.
        """
        try:
            total_conciliado = sum(valores_conciliados)
            diferenca = float(valor_ofx) - float(total_conciliado)
            
            # Só considera se diferença for maior que 1 centavo
            if diferenca > 0.01:
                return diferenca
            else:
                return 0
                
        except:
            return 0

    @classmethod
    def obter_ultimo_batch_importacao(cls, conta_bancaria_id=None):
        try:
            query = db.session.query(cls).filter(cls.ofx_deletada == False)
            
            if conta_bancaria_id:
                query = query.filter(cls.conta_bancaria_id == conta_bancaria_id)
            
            ultima_transacao = query.order_by(cls.data_importacao.desc()).first()
            return ultima_transacao.batch_importacao if ultima_transacao else None
        except Exception as e:
            print(f"[ERRO] Erro ao obter último batch: {e}")
            return None

    @classmethod
    def inserir_transacoes_lote(cls, transacoes_data, arquivo_info, conta_bancaria_id=None):
        try:
            if not transacoes_data:
                return False, "Nenhuma transação para inserir"

            from uuid import uuid4
            batch_id = str(uuid4())[:8]

            # Filtrar fitids já existentes na mesma conta bancária
            # IMPORTANTE: Permite importar a mesma transação (mesmo fitid) se for para contas bancárias diferentes
            fitids_para_importar = [t.get('fitid') for t in transacoes_data if t.get('fitid')]

            fitids_ja_existentes = set()
            if fitids_para_importar and conta_bancaria_id:
                # Verificar fitids que já existem NA MESMA conta bancária específica
                fitids_ja_existentes = {row[0] for row in db.session.query(cls.fitid).filter(
                    cls.fitid.in_(fitids_para_importar),
                    cls.conta_bancaria_id == conta_bancaria_id
                ).all()}

            # Filtrar transações que não estão no banco para esta conta específica
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

                transacao_obj = cls(
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
                    
                    # Vincular à conta bancária selecionada no formulário
                    conta_bancaria_id=conta_bancaria_id
                )

                transacoes_obj.append(transacao_obj)

            db.session.add_all(transacoes_obj)
            db.session.commit()

            total_inseridas = len(transacoes_obj)
            total_duplicadas = len(transacoes_data) - total_inseridas
            
            print(f"[INFO] {total_inseridas} transações OFX inseridas com sucesso (Batch: {batch_id})")
            if total_duplicadas > 0:
                print(f"[INFO] {total_duplicadas} transações duplicadas ignoradas para esta conta bancária")
            
            resultado = {
                'total': total_inseridas, 
                'batch_id': batch_id
            }
            
            if total_duplicadas > 0:
                resultado['duplicadas'] = total_duplicadas
                resultado['mensagem_duplicadas'] = f'{total_duplicadas} transação(ões) já existia(m) nesta conta e foi(ram) ignorada(s)'
            
            return True, resultado

        except Exception as e:
            db.session.rollback()
            print(f"[ERRO] Erro ao inserir transações OFX: {e}")
            return False, str(e)

    @classmethod
    def obter_resumo_importacao(cls, data_inicio=None, data_fim=None, batch_id=None, conciliado=None, ftid=None, valor='', descricao=None, tipo_movimentacao=None, conta_bancaria_id=None):
        """
        Se batch_id for None e conciliado==True, retorna resumo de todas as transações conciliadas (de todos os batches).
        Caso contrário, mantém o comportamento padrão (resumo do batch).
        """
        try:
            query = db.session.query(cls)
            filtro_batch = batch_id is not None
            filtro_conciliado = conciliado is not None
        
            filtro_data_inicio = data_inicio is not None
            filtro_data_fim = data_fim is not None
            
            filtro_conta_bancaria = conta_bancaria_id is not None
            
            if filtro_conta_bancaria:
                query = query.filter(cls.conta_bancaria_id == conta_bancaria_id)

            if filtro_data_inicio:
                query = query.filter(cls.data_transacao >= data_inicio)
            if filtro_data_fim:
                query = query.filter(cls.data_transacao <= data_fim)

            if filtro_batch:
                query = query.filter(cls.batch_importacao == batch_id)
            if filtro_conciliado:
                query = query.filter(cls.conciliado == conciliado)
            if ftid:
                query = query.filter(cls.fitid.ilike(f'%{ftid}%'))
            if valor and valor.strip() and valor.strip() != 'R$ 0,00':
                query = query.filter(cls.valor_formatado.ilike(f'%{valor}%'))
            if descricao and descricao.strip():
                query = query.filter(or_(cls.descricao_limpa.ilike(f'%{descricao}%'), cls.memo.ilike(f'%{descricao}%')))
            if tipo_movimentacao:
                if tipo_movimentacao == 'entrada':
                    query = query.filter(cls.valor > 0)
                elif tipo_movimentacao == 'saida':
                    query = query.filter(cls.valor < 0)

            total_transacoes = query.count()
            
            # Calcular créditos e débitos baseado nos valores reais (não no tipo_movimento)
            # Isso garante consistência com os filtros de entrada/saída
            total_creditos = query.filter(cls.valor > 0).with_entities(func.sum(cls.valor)).scalar() or 0
            soma_debitos = query.filter(cls.valor < 0).with_entities(func.sum(cls.valor)).scalar() or 0
            
            creditos_valor = float(total_creditos)
            debitos_valor = abs(float(soma_debitos))  # Converter para positivo para exibição
            saldo_liquido = creditos_valor - debitos_valor

            # Para dados de exibição, pega a última transação do filtro
            ultima_importacao = query.order_by(cls.data_importacao.desc()).first()

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
            print(f"[ERRO] Erro ao obter resumo da importação: {e}")
            return None
        
    @classmethod
    def obter_historico_importacoes(cls):
        try:
            batches = db.session.query(
                cls.batch_importacao,
                cls.arquivo_nome,
                cls.data_importacao,
                func.count(cls.id).label('total_transacoes'),
                func.sum(func.case([(cls.tipo_movimento == 'CREDITO', cls.valor)], else_=0)).label('total_creditos'),
                func.sum(func.case([(cls.tipo_movimento == 'DEBITO', func.abs(cls.valor))], else_=0)).label('total_debitos')
            ).group_by(
                cls.batch_importacao, cls.arquivo_nome, cls.data_importacao
            ).order_by(cls.data_importacao.desc()).all()
            
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
            print(f"[ERRO] Erro ao obter histórico de importações: {e}")
            return []
    
    @classmethod
    def obter_transacoes_por_periodo(cls, data_inicio=None, data_fim=None):
        """
        Retorna transações filtradas por período.
        """
        query = db.session.query(cls)
        
        if data_inicio:
            query = query.filter(cls.data_transacao >= data_inicio)
        if data_fim:
            query = query.filter(cls.data_transacao <= data_fim)
            
        return query.order_by(cls.data_transacao.desc(), cls.id.desc()).all()
    
    @classmethod
    def obter_transacoes_por_tipo(cls, tipo_movimento):
        """
        Retorna transações filtradas por tipo (CREDITO ou DEBITO).
        """
        return db.session.query(cls).filter(
            cls.tipo_movimento == tipo_movimento
        ).order_by(cls.data_transacao.desc(), cls.id.desc()).all()
    
    @classmethod
    def obter_estatisticas_por_categoria(cls):
        """
        Retorna estatísticas agrupadas por categoria.
        """
        try:
            # Usar COALESCE para pegar categoria_manual ou categoria_automatica
            categoria_final = func.coalesce(cls.categoria_manual, cls.categoria_automatica, 'Sem Categoria')
            
            resultado = db.session.query(
                categoria_final.label('categoria'),
                func.count(cls.id).label('quantidade'),
                func.sum(cls.valor).label('total'),
                cls.tipo_movimento
            ).group_by(categoria_final, cls.tipo_movimento).all()
            
            return resultado
            
        except Exception as e:
            print(f"[ERRO] Erro ao obter estatísticas por categoria: {e}")
            return []
    
    @classmethod
    def obter_transacoes_nao_processadas(cls):
        """
        Retorna transações que ainda não foram processadas/categorizadas.
        """
        return db.session.query(cls).filter(cls.processado == False).order_by(
            cls.data_transacao.desc(), cls.id.desc()
        ).all()
    
    def marcar_como_processado(self, categoria_manual=None, observacoes=None):
        """
        Marca a transação como processada.
        """
        try:
            self.processado = True
            if categoria_manual:
                self.categoria_manual = categoria_manual
            if observacoes:
                self.observacoes = observacoes
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"[ERRO] Erro ao marcar transação como processada: {e}")
            return False
        
    @classmethod
    def obter_estatisticas_transacoes(cls, batch_id=None, conta_bancaria_id=None):
        """
        Retorna estatísticas das transações importadas
        """
        try:
            query = cls.query
            
            if batch_id:
                query = query.filter(cls.batch_importacao == batch_id)
            elif batch_id is None:
                ultimo_batch = cls.obter_ultimo_batch_importacao()
                if ultimo_batch:
                    query = query.filter(cls.batch_importacao == ultimo_batch)
                    
            if conta_bancaria_id:
                query = query.filter(cls.conta_bancaria_id == conta_bancaria_id)
            
            total = query.count()
            conciliadas = query.filter(cls.conciliado == True).count()
            nao_conciliadas = query.filter(cls.conciliado == False).count()
            
            return {
                'total': total,
                'conciliadas': conciliadas,
                'nao_conciliadas': nao_conciliadas
            }
            
        except Exception as e:
            print(f"[ERRO] Erro ao obter estatísticas de transações: {str(e)}")
            return {
                'total': 0,
                'conciliadas': 0,
                'nao_conciliadas': 0
            }
    
    def salvar_dados_conciliacao(self, tipo_conciliacao, agendamentos_ids=None, faturamentos_ids=None, 
                                movimentacoes_ids=None, lancamentos_avulsos_ids=None, valor_agendamento=None, usuario_id=None, observacoes=None):
        """
        Salva os dados da conciliação em formato JSON para permitir reversão posterior
        """
        try:
            from datetime import datetime
            
            dados_conciliacao = {
                'fitid': self.fitid,
                'tipo_conciliacao': tipo_conciliacao,
                'data_conciliacao': DataHora.obter_data_atual_padrao_en(),
                'usuario_conciliacao_id': usuario_id,
                'observacoes': observacoes,
                'agendamentos_ids': agendamentos_ids or [],
                'faturamentos_ids': faturamentos_ids or [],
                'movimentacoes_ids': movimentacoes_ids or [],
                'lancamentos_avulsos_ids': lancamentos_avulsos_ids or [],
                'valor_transacao': float(self.valor),
                'valor_agendamento': int(valor_agendamento) or 0,
                'data_transacao': self.data_transacao.isoformat() if self.data_transacao else None
            }
            
            # Salvar dados no campo JSON
            self.dados_conciliacao_json = dados_conciliacao
            
            # Só marcar como conciliado se estiver totalmente utilizada
            # Respeita o estado definido por adicionar_valor_utilizado()
            if not self.conciliacao_parcial:
                self.conciliado = True
            
            self.tipo_conciliacao = tipo_conciliacao
            self.data_conciliacao = DataHora.obter_data_atual_padrao_en()
            self.usuario_conciliacao_id = usuario_id
            self.observacoes_conciliacao = observacoes
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"[ERRO] Erro ao salvar dados de conciliação: {e}")
            return False
    
    def reverter_conciliacao(self):
        """
        Reverte uma conciliação, restaurando o estado anterior dos registros
        Suporta reversão de conciliações totais e parciais
        """
        try:
            # Verificar se existe dados de conciliação (suporta parcial e total)
            if not self.dados_conciliacao_json:
                return False, "Transação não possui dados para reversão"
            
            dados = self.dados_conciliacao_json
            
            # Importar modelos necessários
            from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
            from sistema.models_views.financeiro.operacional.categorizar_fatura.categorizacao_model import AgendamentoPagamentoModel
            from sistema.models_views.financeiro.movimentacao_financeira.movimentacao_financeira_model import MovimentacaoFinanceiraModel
            from sistema.models_views.financeiro.lancamento_avulso.lancamento_avulso_model import LancamentoAvulsoModel
            
            # Restaurar status dos agendamentos para situação 2 (Pendente)
            if dados.get('agendamentos_ids'):
                for agendamento_id in dados['agendamentos_ids']:
                    agendamento = AgendamentoPagamentoModel.obter_agendamento_por_id(agendamento_id)
                    if agendamento:
                        agendamento.situacao_pagamento_id = 2  # Pendente
                        agendamento.valor_conciliado_100 = None
                        db.session.add(agendamento)
            
            # Restaurar status dos faturamentos para situação 6 (Conciliado)
            if dados.get('faturamentos_ids'):
                for faturamento_id in dados['faturamentos_ids']:
                    faturamento = FaturamentoModel.obter_faturamento_por_id(faturamento_id)
                    if faturamento:
                        faturamento.situacao_pagamento_id = 6  # Conciliado
                        db.session.add(faturamento)
            
            # Restaurar status dos lançamentos avulsos para situação 2 (Pendente)
            if dados.get('lancamentos_avulsos_ids'):
                for lancamento_id in dados['lancamentos_avulsos_ids']:
                    lancamento = LancamentoAvulsoModel.obter_lancamento_por_id(lancamento_id)
                    if lancamento:
                        lancamento.situacao_pagamento_id = 2  # Pendente
                        db.session.add(lancamento)
            
            # Marcar movimentações como deletadas e criar UMA movimentação de contrapartida
            if dados.get('movimentacoes_ids'):
                conta_bancaria_id = None
                
                # Loop apenas para marcar como deletadas e capturar conta bancária
                for movimentacao_id in dados['movimentacoes_ids']:
                    movimentacao = MovimentacaoFinanceiraModel.obter_movimentacoes_por_id(movimentacao_id)
                    if movimentacao:
                        if conta_bancaria_id is None:
                            conta_bancaria_id = movimentacao.conta_bancaria_id
                
                # Criar UMA movimentação de contrapartida para reversão (fora do loop)
                valor_agendamento = dados.get('valor_agendamento', 0)
                if valor_agendamento > 0 and conta_bancaria_id:
                    # Determinar o tipo de movimentação de contrapartida
                    if self.valor > 0:  # Transação original era crédito -> criar débito de reversão
                        tipo_movimentacao_reversao = 2
                        descricao_reversao = f"Reversão de conciliação OFX - Débito de ajuste (FITID: {self.fitid})"
                    else:  # Transação original era débito -> criar crédito de reversão
                        tipo_movimentacao_reversao = 1
                        descricao_reversao = f"Reversão de conciliação OFX - Crédito de ajuste (FITID: {self.fitid})"
                    
                    # Criar nova movimentação de reversão
                    movimentacao_reversao = MovimentacaoFinanceiraModel(
                        conta_bancaria_id=conta_bancaria_id,
                        valor_movimentacao_100=valor_agendamento,
                        observacao_movimentacao=descricao_reversao,
                        tipo_movimentacao=tipo_movimentacao_reversao,
                        data_movimentacao=DataHora.obter_data_atual_padrao_en(),
                        usuario_id=dados.get('usuario_conciliacao_id')
                    )
                    
                    db.session.add(movimentacao_reversao)
            
            # Atualizar saldo da conta bancária (reverter o impacto)
            from sistema.models_views.financeiro.movimentacao_financeira.saldo_movimentacao_financeira_model import SaldoMovimentacaoFinanceiraModel
            
            valor_agendamento = dados.get('valor_agendamento', 0)
            if valor_agendamento > 0 and dados.get('agendamentos_ids'):
                # Pegar a conta do primeiro agendamento para atualizar o saldo
                primeiro_agendamento = AgendamentoPagamentoModel.obter_agendamento_por_id(dados['agendamentos_ids'][0])
                if primeiro_agendamento:
                    saldo_conta = SaldoMovimentacaoFinanceiraModel.query.filter(
                        SaldoMovimentacaoFinanceiraModel.conta_bancaria_id == primeiro_agendamento.conta_bancaria_id,
                        SaldoMovimentacaoFinanceiraModel.ativo == True,
                        SaldoMovimentacaoFinanceiraModel.deletado == False
                    ).first()
                    
                    if saldo_conta:
                        # Reverter o impacto no saldo baseado no tipo de movimentação original
                        if self.valor > 0:  # Era entrada/crédito - agora diminui o saldo
                            saldo_conta.valor_total_saldo_100 -= valor_agendamento
                        else:  # Era saída/débito - agora aumenta o saldo
                            saldo_conta.valor_total_saldo_100 += valor_agendamento
                        
                        # Atualizar data da movimentação
                        saldo_conta.data_movimentacao = DataHora.obter_data_atual_padrao_en()
                        db.session.add(saldo_conta)
            
            # Limpar dados da conciliação
           
            self.tipo_conciliacao = None
            self.pagamento_id = None
            self.data_conciliacao = None
            self.usuario_conciliacao_id = None
            self.observacoes_conciliacao = None
            self.dados_conciliacao_json = None
            self.resetar_utilizacao()
            
            db.session.commit()
            return True, "Conciliação revertida com sucesso"
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"Erro ao reverter conciliação: {str(e)}"
            print(f"[ERRO] {error_msg}")
            return False, error_msg
    
    @classmethod
    def obter_conciliacoes_reversiveis(cls, batch_id=None, limit=50):
        """
        Retorna lista de transações conciliadas (total ou parcial) que podem ser revertidas
        """
        try:
            # Buscar transações com dados de conciliação (total ou parcial)
            query = cls.query.filter(
                cls.dados_conciliacao_json.isnot(None)
            )
            
            if batch_id:
                query = query.filter(cls.batch_importacao == batch_id)
            
            return query.order_by(cls.data_conciliacao.desc()).limit(limit).all()
            
        except Exception as e:
            print(f"[ERRO] Erro ao obter conciliações reversíveis: {e}")
            return []
        