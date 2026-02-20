from ...base_model import BaseModel, db
from sqlalchemy import desc

class MovimentacaoFinanceiraModel(BaseModel):    
    """
    Model para aguardar as movimentações financeiras
    """
    __tablename__ = 'mov_movimentacao_financeira'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    
    tipo_movimentacao = db.Column(db.Integer, nullable=False)

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    usuario = db.relationship('UsuarioModel', backref=db.backref('usuario_movimentacao', lazy=True))

    valor_movimentacao_100 = db.Column(db.Integer, nullable=True)

    data_movimentacao = db.Column(db.Date, nullable=False)

    conta_bancaria_id = db.Column(db.Integer, db.ForeignKey("con_conta_bancaria.id"), nullable=True)
    conta_bancaria = db.relationship("ContaBancariaModel", foreign_keys=[conta_bancaria_id], backref=db.backref("conta_bancaria_movimentacao", lazy=True))

    observacao_movimentacao = db.Column(db.String(255), nullable=True)

    ativo = db.Column(db.Boolean, default=True, nullable=False)

    conciliacao_bancaria = db.Column(db.Boolean, default=False, nullable=False)

    importacao_ofx_id = db.Column(db.Integer, db.ForeignKey('im_importacao_ofx.id'), nullable=True)
    importacao_ofx = db.relationship('ImportacaoOfx', foreign_keys=[importacao_ofx_id], backref=db.backref('movimentacoes_conciliadas_ofx', lazy=True))

    agendamento_id = db.Column(db.Integer, db.ForeignKey('fin_agendamento_pagamento.id'), nullable=True)
    agendamento = db.relationship('AgendamentoPagamentoModel', foreign_keys=[agendamento_id], backref=db.backref('movimentacoes_conciliadas_agendamento', lazy=True))
    
    conciliacao_fitid = db.Column(db.String(255), nullable=True)
    conciliacao_valor_original = db.Column(db.Integer, nullable=True)
    conciliacao_descricao_ofx = db.Column(db.Text, nullable=True)
    conciliacao_data_transacao = db.Column(db.Date, nullable=True)
    conciliacao_tipo_movimento = db.Column(db.String(50), nullable=True)
    
    conciliacao_data_processamento = db.Column(db.DateTime, nullable=True)
    conciliacao_observacoes = db.Column(db.Text, nullable=True)
    
    conciliacao_faturamento_id = db.Column(db.Integer, db.ForeignKey('fin_faturamento.id'), nullable=True)
    conciliacao_faturamento = db.relationship('FaturamentoModel', foreign_keys=[conciliacao_faturamento_id], backref=db.backref('movimentacoes_conciliadas_faturamento', lazy=True))
    
    conciliacao_lancamento_avulso_id = db.Column(db.Integer, db.ForeignKey('lan_lancamento_avulso.id'), nullable=True)
    conciliacao_lancamento_avulso = db.relationship('LancamentoAvulsoModel', foreign_keys=[conciliacao_lancamento_avulso_id], backref=db.backref('movimentacoes_conciliadas_lancamento', lazy=True))
    
    conciliacao_tipo_origem = db.Column(db.String(50), nullable=True)
    
    conciliacao_valor_diferenca = db.Column(db.Integer, nullable=True)
    
    def __init__(
        self, tipo_movimentacao, usuario_id, data_movimentacao, valor_movimentacao_100=None, conta_bancaria_id=None, observacao_movimentacao=None, ativo=True,
        conciliacao_bancaria=False, importacao_ofx_id=None, agendamento_id=None, conciliacao_fitid=None, conciliacao_valor_original=None, 
        conciliacao_descricao_ofx=None, conciliacao_data_transacao=None, conciliacao_tipo_movimento=None,
        conciliacao_data_processamento=None, conciliacao_observacoes=None, conciliacao_faturamento_id=None, conciliacao_lancamento_avulso_id=None,
        conciliacao_tipo_origem=None, conciliacao_valor_diferenca=None
    ):
        self.tipo_movimentacao = tipo_movimentacao
        self.usuario_id = usuario_id
        self.data_movimentacao = data_movimentacao
        self.valor_movimentacao_100 = valor_movimentacao_100
        self.conta_bancaria_id = conta_bancaria_id
        self.observacao_movimentacao = observacao_movimentacao
        self.ativo = ativo
        self.conciliacao_bancaria = conciliacao_bancaria
        self.importacao_ofx_id = importacao_ofx_id
        
        self.agendamento_id = agendamento_id
        self.conciliacao_fitid = conciliacao_fitid
        self.conciliacao_valor_original = conciliacao_valor_original
        self.conciliacao_descricao_ofx = conciliacao_descricao_ofx
        self.conciliacao_data_transacao = conciliacao_data_transacao
        self.conciliacao_tipo_movimento = conciliacao_tipo_movimento
        self.conciliacao_data_processamento = conciliacao_data_processamento
        self.conciliacao_observacoes = conciliacao_observacoes
        self.conciliacao_faturamento_id = conciliacao_faturamento_id
        self.conciliacao_lancamento_avulso_id = conciliacao_lancamento_avulso_id
        self.conciliacao_tipo_origem = conciliacao_tipo_origem
        self.conciliacao_valor_diferenca = conciliacao_valor_diferenca
    
    def obter_valor_total_recebidos(conta_id=None):
        """
        Retorna o valor total de recebimentos (tipo_movimentacao 1).
        Se conta_id for informado, filtra pela conta. Caso contrário, soma de todas as contas.
        """
        query = db.session.query(
            db.func.coalesce(db.func.sum(MovimentacaoFinanceiraModel.valor_movimentacao_100), 0)
        ).filter(
            MovimentacaoFinanceiraModel.ativo == True,
            MovimentacaoFinanceiraModel.deletado == False,
            MovimentacaoFinanceiraModel.tipo_movimentacao == 1
        )
        
        if conta_id and conta_id != 0:
            query = query.filter(MovimentacaoFinanceiraModel.conta_bancaria_id == conta_id)
        
        return query.scalar() or 0

    def obter_valor_total_saidas(conta_id=None):
        """
        Retorna o valor total de pagamentos/saídas (tipo_movimentacao 2).
        Se conta_id for informado, filtra pela conta. Caso contrário, soma de todas as contas.
        """
        query = db.session.query(
            db.func.coalesce(db.func.sum(MovimentacaoFinanceiraModel.valor_movimentacao_100), 0)
        ).filter(
            MovimentacaoFinanceiraModel.ativo == True,
            MovimentacaoFinanceiraModel.deletado == False,
            MovimentacaoFinanceiraModel.tipo_movimentacao == 2
        )
        
        if conta_id and conta_id != 0:
            query = query.filter(MovimentacaoFinanceiraModel.conta_bancaria_id == conta_id)
        
        return query.scalar() or 0

    def obter_valor_total_saldo():
        saldo = MovimentacaoFinanceiraModel.query.filter(
            MovimentacaoFinanceiraModel.deletado == 0,
            MovimentacaoFinanceiraModel.ativo == 1
        ).all()

        return sum(
            s.recebimento.valor_total_recebimento_100 if s.recebimento and s.recebimento.valor_total_recebimento_100 else 0
            for s in saldo
        ) or 0


    def obter_valor_total_creditos():
        registros = MovimentacaoFinanceiraModel.query.filter(
            MovimentacaoFinanceiraModel.deletado == 0,
            MovimentacaoFinanceiraModel.ativo == 1
        ).all()

        return sum(
            (r.credito_fornecedor.valor_credito_100 if r.credito_fornecedor and r.credito_fornecedor.valor_credito_100 else 0) +
            (r.credito_freteiro.valor_credito_100 if r.credito_freteiro and r.credito_freteiro.valor_credito_100 else 0) +
            (r.credito_extrator.valor_credito_100 if r.credito_extrator and r.credito_extrator.valor_credito_100 else 0)
            for r in registros
        ) or 0


    def obter_recebimento_por_id(id):
        """
        Busca uma movimentação financeira por ID (presumindo que seja uma movimentação de entrada/recebimento)
        """
        recebimento = MovimentacaoFinanceiraModel.query.filter(
            MovimentacaoFinanceiraModel.deletado == False,
            MovimentacaoFinanceiraModel.ativo == True,
            MovimentacaoFinanceiraModel.id == id,
            MovimentacaoFinanceiraModel.tipo_movimentacao == 1
        ).first()

        return recebimento
    
    def listagem_movimentacoes_financeiras():
        movimentacoes = MovimentacaoFinanceiraModel.query.filter(
            MovimentacaoFinanceiraModel.ativo == 1
        ).order_by(
            desc(MovimentacaoFinanceiraModel.id)
        ).all()

        return movimentacoes
    
    def listagem_movimentacoes_financeiras_por_conta(conta_id=None):
        """
        Lista movimentações financeiras.
        Se conta_id for informado, filtra pela conta. Caso contrário, lista de todas as contas.
        """
        query = MovimentacaoFinanceiraModel.query.filter(
            MovimentacaoFinanceiraModel.ativo == True,
            MovimentacaoFinanceiraModel.deletado == False
        )

        if conta_id and conta_id != 0:
            query = query.filter(
                MovimentacaoFinanceiraModel.conta_bancaria_id == conta_id
            )

        movimentacoes = (
            query
            .order_by(desc(MovimentacaoFinanceiraModel.id))
            .limit(200)
            .all()
        )

        return movimentacoes
    
    def listagem_movimentacoes_financeiras_relatorio(conta_id=None, data_inicio=None, data_fim=None):
        """Lista movimentações para relatório com filtro de período e ordenação decrescente.
        Inclui eager loading de todos os relacionamentos necessários para cálculo de valores.
        """
        from sqlalchemy.orm import joinedload
        
        query = MovimentacaoFinanceiraModel.query.filter(
            MovimentacaoFinanceiraModel.ativo == True,
            MovimentacaoFinanceiraModel.deletado == False
        )

        query = query.options(
            joinedload(MovimentacaoFinanceiraModel.conta_bancaria),
            joinedload(MovimentacaoFinanceiraModel.importacao_ofx),
            joinedload(MovimentacaoFinanceiraModel.conciliacao_lancamento_avulso),
            joinedload(MovimentacaoFinanceiraModel.conciliacao_faturamento),
            joinedload(MovimentacaoFinanceiraModel.agendamento)
        )

        if conta_id and conta_id != 0:
            query = query.filter(MovimentacaoFinanceiraModel.conta_bancaria_id == conta_id)

        if data_inicio:
            query = query.filter(MovimentacaoFinanceiraModel.data_movimentacao >= data_inicio)
        if data_fim:
            query = query.filter(MovimentacaoFinanceiraModel.data_movimentacao <= data_fim)

        movimentacoes = query.order_by(
            desc(MovimentacaoFinanceiraModel.data_movimentacao),
            desc(MovimentacaoFinanceiraModel.id)
        ).all()

        return movimentacoes
    
    def obter_movimentacoes_por_id(id):
        """
        Retorna uma movimentação financeira específica pelo ID
        """
        movimentacoes = MovimentacaoFinanceiraModel.query.filter(
            MovimentacaoFinanceiraModel.id == id,
            MovimentacaoFinanceiraModel.ativo == True,
            MovimentacaoFinanceiraModel.deletado == False
        ).first()

        return movimentacoes

