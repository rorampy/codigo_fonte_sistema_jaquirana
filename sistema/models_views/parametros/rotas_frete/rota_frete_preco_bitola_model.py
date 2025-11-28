from ...base_model import BaseModel, db


class RotaFretePrecoBitolaModel(BaseModel):
    """
    Model para registro normalizado de preços de frete por bitola de produto em rotas
    """
    __tablename__ = 'z_sys_rota_frete_preco_bitola'
    
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    
    # Relacionamento com a rota de frete
    rota_frete_id = db.Column(db.Integer, db.ForeignKey('z_sys_rota_frete.id'), nullable=False)
    rota_frete = db.relationship('RotaFreteModel', backref=db.backref('precos_bitola', lazy=True))
    
    # Produto e bitola (usando os nomes corretos das tabelas)
    produto_id = db.Column(db.Integer, db.ForeignKey('prod_produto.id'), nullable=False)
    produto = db.relationship('ProdutoModel', backref=db.backref('rota_frete_precos', lazy=True))
    
    bitola_id = db.Column(db.Integer, db.ForeignKey('z_sys_bitola.id'), nullable=False)
    bitola = db.relationship('BitolaModel', backref=db.backref('rota_frete_precos', lazy=True))
    
    # Preço de frete (em centavos)
    preco_frete_100 = db.Column(db.Integer, nullable=True)
    
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(self, rota_frete_id, produto_id, bitola_id, preco_frete_100, ativo=True):
        self.rota_frete_id = rota_frete_id
        self.produto_id = produto_id
        self.bitola_id = bitola_id
        self.preco_frete_100 = preco_frete_100
        self.ativo = ativo
    
    @staticmethod
    def listar_precos_rota(rota_frete_id):
        """
        Lista todos os preços de frete por bitola de uma rota específica
        """
        precos = RotaFretePrecoBitolaModel.query.filter_by(
            rota_frete_id=rota_frete_id,
            ativo=True,
            deletado=False
        ).all()
        return precos
    
    @staticmethod
    def obter_preco_por_produto_bitola(rota_frete_id, produto_id, bitola_id):
        """
        Obtém o preço de frete específico para uma combinação de rota, produto e bitola
        """
        preco = RotaFretePrecoBitolaModel.query.filter_by(
            rota_frete_id=rota_frete_id,
            produto_id=produto_id,
            bitola_id=bitola_id,
            ativo=True,
            deletado=False
        ).first()
        return preco
