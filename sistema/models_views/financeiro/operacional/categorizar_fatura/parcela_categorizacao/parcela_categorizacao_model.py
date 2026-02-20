from .....base_model import BaseModel, db

class ParcelaCategorizacaoModel(BaseModel):
    __tablename__ = 'fin_parcela_categorizacao'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    agendamento_id = db.Column(db.Integer, db.ForeignKey('fin_agendamento_pagamento.id'), nullable=False)
    agendamento = db.relationship('AgendamentoPagamentoModel', backref=db.backref('parcelas', lazy=True, cascade='all, delete-orphan'))
    
    numero_parcela = db.Column(db.Integer, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    valor_parcela = db.Column(db.Integer, nullable=False) 
    descricao = db.Column(db.Text, nullable=True)
    referencia = db.Column(db.String(200), nullable=True)
    
    situacao_pagamento_id = db.Column(db.Integer, db.ForeignKey("fin_situacao_pagamento.id"), nullable=True)
    situacao = db.relationship("SituacaoPagamentoModel", backref=db.backref("parcelas", lazy=True))
    
    data_pagamento = db.Column(db.Date, nullable=True)
    valor_pago_100 = db.Column(db.Integer, nullable=True) 
    observacoes_pagamento = db.Column(db.Text, nullable=True)
    
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(self, agendamento_id, numero_parcela, data_vencimento, valor_parcela, descricao=None, referencia=None, situacao_pagamento_id=None, data_pagamento=None, valor_pago_100=None, observacoes_pagamento=None, ativo=True):
        self.agendamento_id = agendamento_id
        self.numero_parcela = numero_parcela
        self.data_vencimento = data_vencimento
        self.valor_parcela = valor_parcela
        self.descricao = descricao
        self.referencia = referencia
        self.situacao_pagamento_id = situacao_pagamento_id
        self.data_pagamento = data_pagamento
        self.valor_pago_100 = valor_pago_100
        self.observacoes_pagamento = observacoes_pagamento
        self.ativo = ativo
    
    @classmethod
    def obter_parcelas_por_agendamento(cls, agendamento_id):
        """Obtém todas as parcelas de um agendamento específico"""
        return cls.query.filter_by(agendamento_id=agendamento_id, ativo=True).order_by(cls.numero_parcela).all()
    
    @classmethod
    def obter_parcela_por_id(cls, id):
        """Obtém uma parcela específica por ID"""
        return cls.query.filter_by(id=id, ativo=True).first()
    
    