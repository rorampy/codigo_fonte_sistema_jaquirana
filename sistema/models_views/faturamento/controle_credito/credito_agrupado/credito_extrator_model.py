from ....base_model import BaseModel, db
from sqlalchemy import desc

class CreditoExtratorModel(BaseModel):
    """
    Model para aguardar créditos de extratores
    """
    __tablename__ = 'cre_credito_extrator'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    data_movimentacao = db.Column(db.Date, nullable=False)

    extrator_id = db.Column(db.Integer, db.ForeignKey("ext_extrator.id"), nullable=False)
    extrator = db.relationship("ExtratorModel", backref=db.backref("credito_total_extrator", lazy=True))

    valor_total_credito_100 = db.Column(db.Integer, nullable=False)

    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(
            self, data_movimentacao, extrator_id, valor_total_credito_100, ativo=True
    ):
        self.data_movimentacao = data_movimentacao
        self.extrator_id = extrator_id
        self.valor_total_credito_100 = valor_total_credito_100
        self.ativo = ativo

    def soma_valor_credito_disponivel(id):
        credito = CreditoExtratorModel.query.filter(
            CreditoExtratorModel.deletado == 0,
            CreditoExtratorModel.ativo == True,
            CreditoExtratorModel.extrator_id == id
        ).all()

        return sum(c.valor_credito_100 for c in credito) or 0
    
    def obtem_registro_extrator_id(id):
        extrator = CreditoExtratorModel.query.filter(
            CreditoExtratorModel.deletado == 0,
            CreditoExtratorModel.ativo == 1,
            CreditoExtratorModel.extrator_id == id
        ).first()

        return extrator
        

    def soma_credito_atual_com_novo_credito(id, novo_credito_100):
        """
        Soma todos os créditos já existentes para o extrator com um novo valor informado.
        """
        credito_atual = CreditoExtratorModel.query.filter(
            CreditoExtratorModel.deletado == 0,
            CreditoExtratorModel.ativo == True,
            CreditoExtratorModel.extrator_id == id
        ).all()

        total_atual = sum(c.valor_total_credito_100 for c in credito_atual) or 0

        return total_atual + novo_credito_100