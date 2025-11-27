from ...base_model import BaseModel, db
from sqlalchemy import and_, desc


class SituacaoPagamentoModel(BaseModel):
    """
    Model para registro de situações de pagamento
    """
    __tablename__ = 'fin_situacao_pagamento'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    situacao = db.Column(db.String(255), nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(
            self, situacao, ativo=True
    ):
        self.situacao = situacao
        self.ativo = ativo

    @classmethod
    def listar_status(cls):
        status = cls.query.filter(
            cls.ativo == True,
            cls.deletado == False
        ).order_by(cls.id.desc()).all()

        return status

    @classmethod
    def listar_status_filtro(cls):
        status = cls.query.filter(
            cls.ativo == True,
            cls.deletado == False,
            cls.id.in_([2, 5])
        ).order_by(cls.id.desc()).all()

        return status

    @classmethod
    def obter_situacao_por_id(cls, id):
        """Obtém uma situação de pagamento por ID"""
        return cls.query.filter_by(id=id, ativo=True, deletado=False).first()
    
    @classmethod
    def listar_situacoes_faturamento(cls):
        """Lista todas as situações de pagamento ativas"""
        return cls.query.filter(
            and_(
                cls.ativo == True,
                cls.deletado == False,
                cls.id.in_([6, 7])
            )
        ).order_by(desc(cls.situacao)).all()