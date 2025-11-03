from ..base_model import BaseModel, db
from sqlalchemy import and_


class ProdutoModel(BaseModel):
    """
    Model para registro de produtos da madeireira
    """
    __tablename__ = 'prod_produto'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(
            self, nome, ativo=True
    ):
        self.nome = nome
        self.ativo = ativo

    def listar_produtos():
        """
        Lista todos os produtos não deletados.
        
        Returns:
            list: Lista de produtos ordenados por ID decrescente
        """
        produtos = ProdutoModel.query.filter(
            ProdutoModel.deletado == 0,
        ).order_by(ProdutoModel.id.desc()).all()
        
        return produtos