from ...base_model import BaseModel, db
from sqlalchemy import and_


class FornecedorPrecoCustoBitolaModel(BaseModel):
    __tablename__ = 'for_fornecedor_preco_custo_bitola'
    
    id = db.Column(db.Integer, primary_key=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('for_fornecedor_cadastro.id'), nullable=False)    
    produto_id = db.Column(db.Integer, db.ForeignKey('prod_produto.id'), nullable=False)
    produto = db.relationship('ProdutoModel', backref='produto_preco_custo_fornecedor', lazy=True)
    bitola_id = db.Column(db.Integer, db.ForeignKey('z_sys_bitola.id'), nullable=False)
    bitola = db.relationship('BitolaModel', backref='bitola_preco_custo_fornecedor', lazy=True)
    valor_preco_custo_100 = db.Column(db.Integer, nullable=True)

    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(self, fornecedor_id, produto_id, bitola_id, valor_preco_custo_100=None, ativo=True):
        self.fornecedor_id = fornecedor_id
        self.produto_id = produto_id
        self.bitola_id = bitola_id
        self.valor_preco_custo_100 = valor_preco_custo_100
        self.ativo = ativo

    @staticmethod
    def obter_preco_custo_por_bitola(fornecedor_id, produto_id, bitola_id):
        """
        Obtém o preço de custo para um fornecedor, produto e bitola específicos.
        
        Args:
            fornecedor_id (int): ID do fornecedor
            produto_id (int): ID do produto
            bitola_id (int): ID da bitola
            
        Returns:
            FornecedorPrecoCustoBitolaModel: Registro encontrado ou None
        """
        return FornecedorPrecoCustoBitolaModel.query.filter(
            FornecedorPrecoCustoBitolaModel.fornecedor_id == fornecedor_id,
            FornecedorPrecoCustoBitolaModel.produto_id == produto_id,
            FornecedorPrecoCustoBitolaModel.bitola_id == bitola_id,
            FornecedorPrecoCustoBitolaModel.ativo == True,
            FornecedorPrecoCustoBitolaModel.deletado == False
        ).first()

    @staticmethod
    def listar_precos_custo_fornecedor(fornecedor_id):
        """
        Lista todos os preços de custo de um fornecedor.
        
        Args:
            fornecedor_id (int): ID do fornecedor
            
        Returns:
            list: Lista de registros FornecedorPrecoCustoBitolaModel
        """
        return FornecedorPrecoCustoBitolaModel.query.filter(
            FornecedorPrecoCustoBitolaModel.fornecedor_id == fornecedor_id,
            FornecedorPrecoCustoBitolaModel.ativo == True,
            FornecedorPrecoCustoBitolaModel.deletado == False
        ).order_by(
            FornecedorPrecoCustoBitolaModel.produto_id.asc(),
            FornecedorPrecoCustoBitolaModel.bitola_id.asc()
        ).all()

    @staticmethod
    def atualizar_ou_criar_preco_custo(fornecedor_id, produto_id, bitola_id, valor_preco_custo_100=None):
        """
        Atualiza um registro existente ou cria um novo se não existir.
        
        Args:
            fornecedor_id (int): ID do fornecedor
            produto_id (int): ID do produto
            bitola_id (int): ID da bitola
            valor_preco_custo_100 (int, optional): Valor por 100
            
        Returns:
            FornecedorPrecoCustoBitolaModel: Registro atualizado ou criado
        """
        registro = FornecedorPrecoCustoBitolaModel.obter_preco_custo_por_bitola(
            fornecedor_id, produto_id, bitola_id
        )
        
        if registro:
            if valor_preco_custo_100 is not None:
                registro.valor_preco_custo_100 = valor_preco_custo_100
        else:
            registro = FornecedorPrecoCustoBitolaModel(
                fornecedor_id=fornecedor_id,
                produto_id=produto_id,
                bitola_id=bitola_id,
                valor_preco_custo_100=valor_preco_custo_100
            )
            db.session.add(registro)
                    
        return registro
    
    
