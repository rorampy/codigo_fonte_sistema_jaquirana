from ...base_model import BaseModel, db
from sqlalchemy import and_


class FornecedorContaBancariaModel(BaseModel):
    __tablename__ = 'for_fornecedor_conta_bancaria'
    
    id = db.Column(db.Integer, primary_key=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('for_fornecedor_cadastro.id'), nullable=True)    
    instituicao_financeira_id = db.Column(db.Integer, db.ForeignKey('z_sys_instituicoes_financeiras.id'), nullable=True)
    instituicao_financeira = db.relationship('InstituicoesFinanceirasModel', backref='fornecedor_conta_bancaria', lazy=True)
    agencia_bancaria = db.Column(db.String(50), nullable=True)
    conta_bancaria = db.Column(db.String(50), nullable=True)
    chave_pix = db.Column(db.String(155), nullable=True)

    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(self, fornecedor_id, instituicao_financeira_id=None, agencia_bancaria=None, conta_bancaria=None, chave_pix=None, ativo=True):
        self.fornecedor_id = fornecedor_id
        self.instituicao_financeira_id = instituicao_financeira_id
        self.agencia_bancaria = agencia_bancaria
        self.conta_bancaria = conta_bancaria
        self.chave_pix = chave_pix
        self.ativo = ativo
    
    
