from ....base_model import BaseModel, db
from sqlalchemy import desc

class CreditoFornecedorModel(BaseModel):
    """
    Model para aguardar créditos de fornecedores
    """
    __tablename__ = 'cre_credito_fornecedor'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    data_movimentacao = db.Column(db.Date, nullable=False)

    fornecedor_id = db.Column(db.Integer, db.ForeignKey("for_fornecedor_cadastro.id"), nullable=False)
    fornecedor = db.relationship("FornecedorCadastroModel", backref=db.backref("credito_total_fornecedor", lazy=True))

    valor_total_credito_100 = db.Column(db.Integer, nullable=False)

    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(
            self, data_movimentacao, fornecedor_id, valor_total_credito_100, ativo=True
    ):
        self.data_movimentacao = data_movimentacao
        self.fornecedor_id = fornecedor_id
        self.valor_total_credito_100 = valor_total_credito_100
        self.ativo = ativo

    def valor_credito_disponivel(id):
        credito = CreditoFornecedorModel.query.filter(
            CreditoFornecedorModel.deletado == 0,
            CreditoFornecedorModel.ativo == True,
            CreditoFornecedorModel.fornecedor_id == id
        ).first()

        return credito
    
    def obtem_registro_id(id):
        registro = CreditoFornecedorModel.query.filter(
            CreditoFornecedorModel.deletado == 0,
            CreditoFornecedorModel.ativo == 1,
            CreditoFornecedorModel.fornecedor_id == id
        ).first()

        return registro
    
    def soma_credito_atual_com_novo_credito(id, novo_credito_100):
        """
        Soma todos os créditos já existentes para o fornecedor com um novo valor informado.
        """
        credito_atual = CreditoFornecedorModel.query.filter(
            CreditoFornecedorModel.deletado == 0,
            CreditoFornecedorModel.ativo == True,
            CreditoFornecedorModel.fornecedor_id == id
        ).all()

        total_atual = sum(c.valor_total_credito_100 for c in credito_atual) or 0

        return total_atual + novo_credito_100