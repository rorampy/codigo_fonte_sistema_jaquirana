from ..base_model import BaseModel, db
from sqlalchemy import and_


class VariavelSistemaModel(BaseModel):
    """
    Model para registro de variáveis padrão do sistema.
    """
    __tablename__ = 'z_sys_variavel_sistema'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    nome_projeto = db.Column(db.String(50))
    telefone = db.Column(db.String(20))
    cnpj = db.Column(db.String(20))
    email_corporativo = db.Column(db.String(150))
    chave_pub_google_recaptcha = db.Column(db.String(255))
    chave_priv_google_recaptcha = db.Column(db.String(255))
    
    modo_manutencao = db.Column(db.Boolean, nullable=False)
    
    def __init__(
            self, nome_projeto, telefone, cnpj, email_corporativo,
            chave_pub_google_recaptcha, chave_priv_google_recaptcha, modo_manutencao
    ):
        self.nome_projeto = nome_projeto
        self.telefone = telefone
        self.cnpj = cnpj
        self.email_corporativo = email_corporativo
        self.chave_pub_google_recaptcha = chave_pub_google_recaptcha
        self.chave_priv_google_recaptcha = chave_priv_google_recaptcha
        self.modo_manutencao = modo_manutencao
        
        
    def obter_variaveis_de_sistema_por_id(id=1):
        variaveis = VariavelSistemaModel.query.filter(and_(
            VariavelSistemaModel.deletado == 0
        )).first()
        
        return variaveis