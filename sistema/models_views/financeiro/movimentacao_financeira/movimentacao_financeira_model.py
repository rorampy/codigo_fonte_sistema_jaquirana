from ...base_model import BaseModel, db
from sqlalchemy import desc

class MovimentacaoFinanceiraModel(BaseModel):    
    """
    Model para aguardar as movimentações financeiras
    """
    __tablename__ = 'mov_movimentacao_financeira'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    
    # 1 - Entrada | 2 - Saída | 3 - Cancelamento | 4 - Estorno credito | 5 - Estorno de saldo de conta
    tipo_movimentacao = db.Column(db.Integer, nullable=False)

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    usuario = db.relationship('UsuarioModel', backref=db.backref('usuario_movimentacao', lazy=True))

    valor_movimentacao_100 = db.Column(db.Integer, nullable=True)

    data_movimentacao = db.Column(db.Date, nullable=False)

    conta_bancaria_id = db.Column(db.Integer, db.ForeignKey("con_conta_bancaria.id"), nullable=True)
    conta_bancaria = db.relationship("ContaBancariaModel", foreign_keys=[conta_bancaria_id], backref=db.backref("conta_bancaria_movimentacao", lazy=True))

    observacao_movimentacao = db.Column(db.String(255), nullable=True)

    ativo = db.Column(db.Boolean, default=True, nullable=False)

    # Indica se a movimentação foi gerada por conciliação bancária (pagamento em massa OFX)
    conciliacao_bancaria = db.Column(db.Boolean, default=False, nullable=False)

    # Vínculo com a transação OFX (importacao_ofx) usada na conciliação bancária
    importacao_ofx_id = db.Column(db.Integer, db.ForeignKey('im_importacao_ofx.id'), nullable=True)
    importacao_ofx = db.relationship('ImportacaoOfx', foreign_keys=[importacao_ofx_id], backref=db.backref('movimentacoes_conciliadas_ofx', lazy=True))

    # Campos de referências importantes para auditoria da conciliação bancária
    agendamento_id = db.Column(db.Integer, db.ForeignKey('fin_agendamento_pagamento.id'), nullable=True)
    agendamento = db.relationship('AgendamentoPagamentoModel', foreign_keys=[agendamento_id], backref=db.backref('movimentacoes_conciliadas_agendamento', lazy=True))
    
    # Dados originais da transação OFX para auditoria
    conciliacao_fitid = db.Column(db.String(255), nullable=True)  # FITID da transação OFX original
    conciliacao_valor_original = db.Column(db.Integer, nullable=True)  # Valor original da transação OFX em centavos
    conciliacao_descricao_ofx = db.Column(db.Text, nullable=True)  # Descrição original da transação OFX
    conciliacao_data_transacao = db.Column(db.Date, nullable=True)  # Data da transação original do OFX
    conciliacao_tipo_movimento = db.Column(db.String(50), nullable=True)  # Tipo do movimento (DEBIT/CREDIT)
    
    # Auditoria de quem e quando fez a conciliação
    conciliacao_data_processamento = db.Column(db.DateTime, nullable=True)  # Data/hora do processamento da conciliação
    conciliacao_observacoes = db.Column(db.Text, nullable=True)  # Observações sobre a conciliação
    
    # Referências para diferentes tipos de origem do agendamento
    conciliacao_faturamento_id = db.Column(db.Integer, db.ForeignKey('fin_faturamento.id'), nullable=True)  # ID do faturamento se origem for faturamento
    conciliacao_faturamento = db.relationship('FaturamentoModel', foreign_keys=[conciliacao_faturamento_id], backref=db.backref('movimentacoes_conciliadas_faturamento', lazy=True))
    
    conciliacao_lancamento_avulso_id = db.Column(db.Integer, db.ForeignKey('lan_lancamento_avulso.id'), nullable=True)  # ID do lançamento avulso se origem for lançamento
    conciliacao_lancamento_avulso = db.relationship('LancamentoAvulsoModel', foreign_keys=[conciliacao_lancamento_avulso_id], backref=db.backref('movimentacoes_conciliadas_lancamento', lazy=True))
    
    conciliacao_tipo_origem = db.Column(db.String(50), nullable=True)  # 'FATURAMENTO' ou 'LANCAMENTO_AVULSO'
    
    # Dados adicionais para controle
    conciliacao_valor_diferenca = db.Column(db.Integer, nullable=True)  # Diferença entre valor OFX e agendamento
    
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
        
        # Campos de auditoria da conciliação
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
    
    def obter_valor_total_recebidos(conta_id=1):
        """
        Retorna o valor total de recebimentos (tipo_movimentacao 1) para uma conta bancária específica.
        Soma o campo valor_movimentacao_100 das movimentações ativas e não deletadas.
        """
        if conta_id is None:
            conta_id = 1
        total = (
            db.session.query(
                db.func.coalesce(db.func.sum(MovimentacaoFinanceiraModel.valor_movimentacao_100), 0)
            )
            .filter(
                MovimentacaoFinanceiraModel.ativo == True,
                MovimentacaoFinanceiraModel.deletado == False,
                MovimentacaoFinanceiraModel.tipo_movimentacao == 1,
                MovimentacaoFinanceiraModel.conta_bancaria_id == conta_id
            )
            .scalar()
        )
        return total or 0

    def obter_valor_total_saidas(conta_id=1):
        """
        Retorna o valor total de pagamentos/saídas (tipo_movimentacao 2) para uma conta bancária específica.
        Soma o campo valor_movimentacao_100 das movimentações ativas e não deletadas.
        """
        if conta_id is None:
            conta_id = 1
        total = (
            db.session.query(
                db.func.coalesce(db.func.sum(MovimentacaoFinanceiraModel.valor_movimentacao_100), 0)
            )
            .filter(
                MovimentacaoFinanceiraModel.ativo == True,
                MovimentacaoFinanceiraModel.deletado == False,
                MovimentacaoFinanceiraModel.tipo_movimentacao == 2,
                MovimentacaoFinanceiraModel.conta_bancaria_id == conta_id
            )
            .scalar()
        )
        return total or 0

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
            MovimentacaoFinanceiraModel.tipo_movimentacao == 1  # Apenas entradas/recebimentos
        ).first()

        return recebimento
    
    def listagem_movimentacoes_financeiras():
        movimentacoes = MovimentacaoFinanceiraModel.query.filter(
            MovimentacaoFinanceiraModel.ativo == 1
        ).order_by(
            desc(MovimentacaoFinanceiraModel.id)
        ).all()

        return movimentacoes
    
    def listagem_movimentacoes_financeiras_por_conta(conta_id = 1):
        if conta_id is None:
            conta_id = 1

        # base da query: somente movimentações ativas
        query = MovimentacaoFinanceiraModel.query.filter(
            MovimentacaoFinanceiraModel.ativo == True
        )

        # se filtrou uma conta específica, aplica o filtro
        if conta_id and conta_id != 0:
            query = query.filter(
                MovimentacaoFinanceiraModel.conta_bancaria_id == conta_id
            )

        # ordena e retorna, limitando a 200 transações
        movimentacoes = (
            query
            .order_by(desc(MovimentacaoFinanceiraModel.id))
            .limit(200)
            .all()
        )

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

