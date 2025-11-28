from ...base_model import BaseModel, db
from sqlalchemy import and_


class ProdutoBitolaModel(BaseModel):
    """
    Model para registro do relacionamento entre produtos e bitolas.
    Define quais bitolas são válidas para cada produto.
    """
    __tablename__ = 'prod_produto_bitola'
    
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('prod_produto.id'), nullable=False)
    bitola_id = db.Column(db.Integer, db.ForeignKey('z_sys_bitola.id'), nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relacionamentos
    produto = db.relationship('ProdutoModel', backref='produto_bitolas', lazy=True)
    bitola = db.relationship('BitolaModel', backref='bitola_produtos', lazy=True)
    
    def __init__(self, produto_id, bitola_id, ativo=True):
        self.produto_id = produto_id
        self.bitola_id = bitola_id
        self.ativo = ativo

    @staticmethod
    def listar_bitolas_por_produto(produto_id):
        """
        Lista todas as bitolas ativas disponíveis para um produto específico.
        
        Args:
            produto_id (int): ID do produto
            
        Returns:
            list: Lista de objetos BitolaModel válidos para o produto
        """
        from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
        
        bitolas = db.session.query(BitolaModel)\
            .join(ProdutoBitolaModel, BitolaModel.id == ProdutoBitolaModel.bitola_id)\
            .filter(
                ProdutoBitolaModel.produto_id == produto_id,
                ProdutoBitolaModel.ativo == True,
                ProdutoBitolaModel.deletado == False,
                BitolaModel.ativo == True,
                BitolaModel.deletado == False
            )\
            .order_by(BitolaModel.id)\
            .all()
        
        return bitolas

    @staticmethod
    def obter_produtos_com_bitolas():
        """
        Obtém todos os produtos ativos com suas respectivas bitolas disponíveis.
        
        Returns:
            dict: Dicionário com estrutura {produto_id: {'nome': nome, 'bitolas': [...]}}
        """
        from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
        
        produtos = ProdutoModel.listar_produtos()
        resultado = {}
        
        for produto in produtos:
            bitolas = ProdutoBitolaModel.listar_bitolas_por_produto(produto.id)
            resultado[produto.id] = {
                'nome': produto.nome,
                'bitolas': [{'id': b.id, 'nome': b.bitola} for b in bitolas]
            }
        
        return resultado

    @staticmethod
    def criar_relacionamento(produto_id, bitola_id):
        """
        Cria um novo relacionamento produto-bitola se não existir.
        
        Args:
            produto_id (int): ID do produto
            bitola_id (int): ID da bitola
            
        Returns:
            bool: True se criado com sucesso, False se já existe
        """
        relacionamento_existente = ProdutoBitolaModel.query.filter_by(
            produto_id=produto_id,
            bitola_id=bitola_id,
            deletado=False
        ).first()
        
        if relacionamento_existente:
            # Se existir mas estiver inativo, reativar
            if not relacionamento_existente.ativo:
                relacionamento_existente.ativo = True
                db.session.commit()
                return True
            return False
        
        # Criar novo relacionamento
        novo_relacionamento = ProdutoBitolaModel(produto_id, bitola_id)
        db.session.add(novo_relacionamento)
        db.session.commit()
        return True

    @staticmethod
    def remover_relacionamento(produto_id, bitola_id):
        """
        Remove (desativa) um relacionamento produto-bitola.
        
        Args:
            produto_id (int): ID do produto
            bitola_id (int): ID da bitola
            
        Returns:
            bool: True se removido com sucesso, False se não encontrado
        """
        relacionamento = ProdutoBitolaModel.query.filter_by(
            produto_id=produto_id,
            bitola_id=bitola_id,
            deletado=False
        ).first()
        
        if relacionamento:
            relacionamento.ativo = False
            relacionamento.deletado = True
            db.session.commit()
            return True
        
        return False