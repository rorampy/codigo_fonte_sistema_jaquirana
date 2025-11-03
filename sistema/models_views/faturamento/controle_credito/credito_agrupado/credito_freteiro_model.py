from ....base_model import BaseModel, db
from sqlalchemy import desc


class CreditoFreteiroModel(BaseModel):
    """
    Model para aguardar créditos de freteiros
    """

    __tablename__ = "cre_credito_freteiro"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    data_movimentacao = db.Column(db.Date, nullable=False)

    transportadora_id = db.Column( db.Integer, db.ForeignKey("transp_transportadora.id"), nullable=True)
    transportadora = db.relationship(
        "TransportadoraModel",
        backref=db.backref("credito_total_transportadora", lazy=True),
    )

    valor_total_credito_100 = db.Column(db.Integer, nullable=False)

    ativo = db.Column(db.Boolean, default=True, nullable=False)

    def __init__(
        self, data_movimentacao, transportadora_id, valor_total_credito_100, ativo=True
    ):
        self.data_movimentacao = data_movimentacao
        self.transportadora_id = transportadora_id
        self.valor_total_credito_100 = valor_total_credito_100
        self.ativo = ativo

    def soma_valor_credito_disponivel(id):
        credito = CreditoFreteiroModel.query.filter(
            CreditoFreteiroModel.deletado == 0,
            CreditoFreteiroModel.ativo == True,
            CreditoFreteiroModel.transportadora_id == id,
        ).all()

        return sum(c.valor_total_credito_100 for c in credito) or 0

    def obtem_registro_id(id):
        registro = CreditoFreteiroModel.query.filter(
            CreditoFreteiroModel.deletado == 0,
            CreditoFreteiroModel.ativo == 1,
            CreditoFreteiroModel.transportadora_id == id,
        ).first()

        return registro

    def soma_credito_atual_com_novo_credito(id, novo_credito_100):
        """
        Soma todos os créditos já existentes para a transportadora com um novo valor informado.
        """
        credito_atual = CreditoFreteiroModel.query.filter(
            CreditoFreteiroModel.deletado == 0,
            CreditoFreteiroModel.ativo == True,
            CreditoFreteiroModel.transportadora_id == id,
        ).all()

        total_atual = sum(c.valor_total_credito_100 for c in credito_atual) or 0

        return total_atual + novo_credito_100
