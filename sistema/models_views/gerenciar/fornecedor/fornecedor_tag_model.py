from ...base_model import BaseModel, db
from sqlalchemy import and_


class FornecedorTag(BaseModel):
    __tablename__ = 'for_fornecedor_tag'
    
    id = db.Column(db.Integer, primary_key=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('for_fornecedor_cadastro.id'), nullable=True)    
    tag_id = db.Column(db.Integer, db.ForeignKey('ta_tag.id'), nullable=True)
    tag = db.relationship('TagModel', backref=db.backref('fornecedor_tags', lazy=True))

    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(self, fornecedor_id, tag_id, ativo=True):
        self.fornecedor_id = fornecedor_id
        self.tag_id = tag_id
        self.ativo = ativo
    
    
