from ...base_model import BaseModel, db
from sqlalchemy import desc

class LancamentoMovimentacaoExtraModel(BaseModel):
    """
    Model para aguardar as movimentações financeiras
    """
    __tablename__ = 'lan_lancamento_movimentacao_extra'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    # 1 - Receitas | 2 - Despesas
    tipo_movimentacao = db.Column(db.Integer, nullable=False)

    vencimento = db.Column(db.Date, nullable=False)
    descricao = db.Column(db.String(255), nullable=False)
    mes_ano = db.Column(db.String(10), nullable=False)
    valor_movimentacao_100 = db.Column(db.Integer, nullable=True)

    plano_conta_id = db.Column(db.Integer, db.ForeignKey("plan_plano_conta.id"), nullable=True)
    plano_conta = db.relationship("PlanoContaModel", foreign_keys=[plano_conta_id], backref=db.backref("plano_conta", lazy=True))

    categorizacao_fiscal_id = db.Column(db.Integer, db.ForeignKey("ca_categorizacao_fiscal.id"), nullable=True)
    categorizacao_fiscal = db.relationship("CategorizacaoFiscalModel", foreign_keys=[categorizacao_fiscal_id], backref=db.backref("categorizacao_fiscal", lazy=True))

    conta_bancaria_id = db.Column(db.Integer, db.ForeignKey("con_conta_bancaria.id"), nullable=True)
    conta_bancaria = db.relationship("ContaBancariaModel", foreign_keys=[conta_bancaria_id], backref=db.backref("conta_bancaria", lazy=True))

    centro_custo_id = db.Column(db.Integer, db.ForeignKey("ce_centro_custo.id"), nullable=True)
    centro_custo = db.relationship("CentroCustoModel", foreign_keys=[centro_custo_id], backref=db.backref("centro_custo", lazy=True))

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    usuario = db.relationship('UsuarioModel', backref=db.backref('usuario_movimentacao_extra', lazy=True))

    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(
        self,
        tipo_movimentacao,
        vencimento,
        descricao,
        mes_ano,
        valor_movimentacao_100=None,
        plano_conta_id=None,
        categorizacao_fiscal_id=None,
        categoria_fiscal=None,
        conta_bancaria_id=None,
        centro_custo_id=None,
        usuario_id=None,
        ativo=True
    ):
        self.tipo_movimentacao = tipo_movimentacao
        self.vencimento = vencimento
        self.descricao = descricao
        self.mes_ano = mes_ano
        self.valor_movimentacao_100 = valor_movimentacao_100

        self.plano_conta_id = plano_conta_id
        self.categorizacao_fiscal_id = categorizacao_fiscal_id
        self.categoria_fiscal = categoria_fiscal
        self.conta_bancaria_id = conta_bancaria_id
        self.centro_custo_id = centro_custo_id

        self.usuario_id = usuario_id
        self.ativo = ativo