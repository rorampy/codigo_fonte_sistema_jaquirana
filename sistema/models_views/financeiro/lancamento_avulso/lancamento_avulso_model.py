from ...base_model import BaseModel, db
from sqlalchemy import desc

class LancamentoAvulsoModel(BaseModel):
    """
    Model para aguardar as movimentações financeiras avulsas,
    substitui o antigo "lancamento_movimentacao_extra".
    """
    __tablename__ = 'lan_lancamento_avulso'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    tipo_movimentacao = db.Column(db.Integer, nullable=False)
    
    descricao = db.Column(db.String(255), nullable=False)
    valor_movimentacao_100 = db.Column(db.Integer, nullable=True)

    situacao_pagamento_id = db.Column(db.Integer, db.ForeignKey("fin_situacao_pagamento.id"), nullable=True)
    situacao = db.relationship("SituacaoPagamentoModel", backref=db.backref("status_lancamento", lazy=True))
    
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    usuario = db.relationship('UsuarioModel', backref=db.backref('usuario_movimentacao_avulsa', lazy=True))

    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(
        self,
        tipo_movimentacao,
        descricao,
        valor_movimentacao_100=None,
        situacao_pagamento_id=None,
        usuario_id=None,
        ativo=True
    ):
        self.tipo_movimentacao = tipo_movimentacao
        self.descricao = descricao
        self.valor_movimentacao_100 = valor_movimentacao_100
        self.situacao_pagamento_id = situacao_pagamento_id
        self.usuario_id = usuario_id
        self.ativo = ativo
    
    @staticmethod
    def obter_lancamentos_ativos():
        """Obtém todos os lançamentos avulsos ativos"""
        return LancamentoAvulsoModel.query.filter_by(ativo=True).order_by(desc(LancamentoAvulsoModel.id)).all()
    
    @staticmethod
    def obter_lancamento_por_id(id):
        """Obtém um lançamento avulso pelo ID"""
        return LancamentoAvulsoModel.query.filter_by(id=id, ativo=True).first()