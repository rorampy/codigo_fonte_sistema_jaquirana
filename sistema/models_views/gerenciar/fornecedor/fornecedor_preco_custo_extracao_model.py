from ...base_model import BaseModel, db
from sqlalchemy import and_


class FornecedorPrecoCustoExtracaoModel(BaseModel):
    __tablename__ = 'for_fornecedor_preco_custo_extracao'
    
    id = db.Column(db.Integer, primary_key=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('for_fornecedor_cadastro.id'), nullable=False)    
    extrator_id = db.Column(db.Integer, db.ForeignKey("ext_extrator.id"), nullable=True)
    extrator = db.relationship("ExtratorModel", backref=db.backref("extrator_custo_extracao_fornecedor", lazy=True))
    produto_id = db.Column(db.Integer, db.ForeignKey('prod_produto.id'), nullable=False)
    produto = db.relationship('ProdutoModel', backref='produto_custo_extracao_fornecedor', lazy=True)
    bitola_id = db.Column(db.Integer, db.ForeignKey('z_sys_bitola.id'), nullable=False)
    bitola = db.relationship('BitolaModel', backref='bitola_custo_extracao_fornecedor', lazy=True)
    custo_extracao_100 = db.Column(db.Integer, nullable=True)  # Custo de extração por 100 em centavos

    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(self, fornecedor_id, extrator_id, produto_id, bitola_id, custo_extracao_100=None, ativo=True):
        self.fornecedor_id = fornecedor_id
        self.extrator_id = extrator_id
        self.produto_id = produto_id
        self.bitola_id = bitola_id
        self.custo_extracao_100 = custo_extracao_100
        self.ativo = ativo

    @staticmethod
    def obter_custo_extracao_por_bitola(fornecedor_id, produto_id, bitola_id):
        """
        Obtém o custo de extração para um fornecedor, produto e bitola específicos.
        
        Args:
            fornecedor_id (int): ID do fornecedor
            produto_id (int): ID do produto
            bitola_id (int): ID da bitola
            
        Returns:
            FornecedorPrecoCustoExtracaoModel: Registro encontrado ou None
        """
        return FornecedorPrecoCustoExtracaoModel.query.filter(
            FornecedorPrecoCustoExtracaoModel.fornecedor_id == fornecedor_id,
            FornecedorPrecoCustoExtracaoModel.produto_id == produto_id,
            FornecedorPrecoCustoExtracaoModel.bitola_id == bitola_id,
            FornecedorPrecoCustoExtracaoModel.ativo == True,
            FornecedorPrecoCustoExtracaoModel.deletado == False
        ).first()

    @staticmethod
    def listar_custos_extracao_fornecedor(fornecedor_id):
        """
        Lista todos os custos de extração de um fornecedor.
        
        Args:
            fornecedor_id (int): ID do fornecedor
            
        Returns:
            list: Lista de registros FornecedorPrecoCustoExtracaoModel
        """
        return FornecedorPrecoCustoExtracaoModel.query.filter(
            FornecedorPrecoCustoExtracaoModel.fornecedor_id == fornecedor_id,
            FornecedorPrecoCustoExtracaoModel.ativo == True,
            FornecedorPrecoCustoExtracaoModel.deletado == False
        ).order_by(
            FornecedorPrecoCustoExtracaoModel.produto_id.asc(),
            FornecedorPrecoCustoExtracaoModel.bitola_id.asc()
        ).all()

    @staticmethod
    def atualizar_ou_criar_custo_extracao(fornecedor_id, produto_id, bitola_id, custo_extracao_100=None, extrator_id=None):
        """
        Atualiza um registro existente ou cria um novo se não existir.
        
        Args:
            fornecedor_id (int): ID do fornecedor
            produto_id (int): ID do produto
            bitola_id (int): ID da bitola
            custo_extracao_100 (int, optional): Custo de extração por 100
            extrator_id (int, optional): ID do extrator
            
        Returns:
            FornecedorPrecoCustoExtracaoModel: Registro atualizado ou criado
        """
        registro = FornecedorPrecoCustoExtracaoModel.obter_custo_extracao_por_bitola(
            fornecedor_id, produto_id, bitola_id
        )
        
        if registro:
            # Atualiza registro existente
            if custo_extracao_100 is not None:
                registro.custo_extracao_100 = custo_extracao_100
            if extrator_id is not None:
                registro.extrator_id = extrator_id
        else:
            # Cria novo registro
            registro = FornecedorPrecoCustoExtracaoModel(
                extrator_id=extrator_id,
                fornecedor_id=fornecedor_id,
                produto_id=produto_id,
                bitola_id=bitola_id,
                custo_extracao_100=custo_extracao_100
            )
            db.session.add(registro)        
        return registro