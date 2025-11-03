from ...base_model import BaseModel, db

class ImpostoModel(BaseModel):
    """
    Model para registro de imposto, utilizado para guardar o valor de imposto de Funrural e Senar,
    podendo cadastrar mais impostos futuramente
    """
    __tablename__ = 'z_sys_imposto'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    nome_imposto = db.Column(db.String(255), nullable=False)
    porcentagem_imposto = db.Column(db.Float(), nullable=False, default=0.0)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(
            self, nome_imposto, porcentagem_imposto, ativo=True
    ):
        self.nome_imposto = nome_imposto
        self.porcentagem_imposto = porcentagem_imposto
        self.ativo = ativo