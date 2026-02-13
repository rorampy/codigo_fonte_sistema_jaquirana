from ...base_model import BaseModel, db
from sqlalchemy import desc


class SaldoMovimentacaoFinanceiraModel(BaseModel):
    """
    Model para aguardar saldo de movimentacoes financeiras
    """

    __tablename__ = "sa_saldo_movimentacao"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    data_movimentacao = db.Column(db.Date, nullable=False)
    valor_total_saldo_100 = db.Column(db.Integer, nullable=False)
    conta_bancaria_id = db.Column(
        db.Integer, db.ForeignKey("con_conta_bancaria.id"), nullable=True
    )
    conta_bancaria = db.relationship(
        "ContaBancariaModel",
        foreign_keys=[conta_bancaria_id],
        backref=db.backref("conta_bancaria_saldo", lazy=True),
    )
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    def __init__(
        self,
        data_movimentacao,
        valor_total_saldo_100,
        conta_bancaria_id=None,
        ativo=True,
    ):
        self.data_movimentacao = data_movimentacao
        self.valor_total_saldo_100 = valor_total_saldo_100
        self.conta_bancaria_id = conta_bancaria_id
        self.ativo = ativo
    
    def obter_registro_conta_bancaria(id_conta=1):
        conta = SaldoMovimentacaoFinanceiraModel.query.filter(
            SaldoMovimentacaoFinanceiraModel.deletado ==0,
            SaldoMovimentacaoFinanceiraModel.ativo == 1,
            SaldoMovimentacaoFinanceiraModel.conta_bancaria_id == id_conta
        ).first()

        return conta

    def obter_registro_saldo_por_conta_bancaria(id_conta=None):
        """
        Retorna o saldo total.
        Se id_conta for informado, retorna o saldo da conta. Caso contrário, soma de todas as contas.
        """
        query = SaldoMovimentacaoFinanceiraModel.query.filter(
            SaldoMovimentacaoFinanceiraModel.deletado == False,
            SaldoMovimentacaoFinanceiraModel.ativo == True,
        )

        if id_conta and id_conta != 0:
            registro = query.filter(
                SaldoMovimentacaoFinanceiraModel.conta_bancaria_id == id_conta
            ).first()
            saldos = [registro] if registro else []
        else:
            saldos = query.all()

        total_centavos = 0
        for s in saldos:
            total_centavos += s.valor_total_saldo_100

        return total_centavos
