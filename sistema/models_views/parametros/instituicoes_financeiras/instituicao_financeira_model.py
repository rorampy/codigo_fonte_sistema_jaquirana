from ...base_model import BaseModel, db


class InstituicoesFinanceirasModel(BaseModel):
    """
    Model base para registro de instituições financeiras.
    """
    __tablename__ = 'z_sys_instituicoes_financeiras'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    cod =  db.Column(db.String(25), nullable=False)
    nome = db.Column(db.String(255), nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    
    
    def __init__(
        self, cod, nome, ativo
    ):
        self.cod = cod
        self.nome = nome
        self.ativo = ativo
    
    def obter_todos_bancos():
        bancos = InstituicoesFinanceirasModel.query.all()

        return bancos