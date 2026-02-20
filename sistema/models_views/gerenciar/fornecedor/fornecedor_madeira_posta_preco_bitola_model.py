from ...base_model import BaseModel, db
from sqlalchemy import and_


class FornecedorMadeiraPostaPrecoBitolaModel(BaseModel):
    """
    Tabela normalizada para preços de madeira posta por bitola.
    Cada linha representa um preço específico para uma combinação de:
    fornecedor + cliente + transportadora (opcional) + produto + bitola
    """

    __tablename__ = 'for_fornecedor_madeira_posta_preco_bitola'
    
    id = db.Column(db.Integer, primary_key=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey("for_fornecedor_cadastro.id"), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey("cli_cliente.id"), nullable=False)
    transportadora_id = db.Column(db.Integer, db.ForeignKey("transp_transportadora.id"), nullable=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('prod_produto.id'), nullable=False)
    bitola_id = db.Column(db.Integer, db.ForeignKey('z_sys_bitola.id'), nullable=False)
    preco_madeira_posta_100 = db.Column(db.Integer, nullable=True)

    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    cliente = db.relationship("ClienteModel", backref="madeira_posta_recebida", lazy=True)
    transportadora = db.relationship("TransportadoraModel", backref="madeira_posta_transportada", lazy=True)
    produto = db.relationship("ProdutoModel", backref="madeira_posta_produtos", lazy=True)
    bitola = db.relationship("BitolaModel", backref="madeira_posta_bitolas", lazy=True)

    def __init__(self, fornecedor_id, cliente_id, produto_id, bitola_id, preco_madeira_posta_100=None, 
                 transportadora_id=None, ativo=True):
        self.fornecedor_id = fornecedor_id
        self.cliente_id = cliente_id
        self.transportadora_id = transportadora_id
        self.produto_id = produto_id
        self.bitola_id = bitola_id
        self.preco_madeira_posta_100 = preco_madeira_posta_100
        self.ativo = ativo

    @staticmethod
    def obter_preco_madeira_posta(fornecedor_id, cliente_id, produto_id, bitola_id, transportadora_id=None):
        """
        Obtém o preço de madeira posta para uma combinação específica.
        
        Args:
            fornecedor_id (int): ID do fornecedor
            cliente_id (int): ID do cliente
            produto_id (int): ID do produto
            bitola_id (int): ID da bitola
            transportadora_id (int, optional): ID da transportadora
            
        Returns:
            FornecedorMadeiraPostaPrecoBitolaModel: Registro encontrado ou None
        """
        query = FornecedorMadeiraPostaPrecoBitolaModel.query.filter(
            FornecedorMadeiraPostaPrecoBitolaModel.fornecedor_id == fornecedor_id,
            FornecedorMadeiraPostaPrecoBitolaModel.cliente_id == cliente_id,
            FornecedorMadeiraPostaPrecoBitolaModel.produto_id == produto_id,
            FornecedorMadeiraPostaPrecoBitolaModel.bitola_id == bitola_id,
            FornecedorMadeiraPostaPrecoBitolaModel.ativo == True,
            FornecedorMadeiraPostaPrecoBitolaModel.deletado == False
        )
        
        if transportadora_id:
            query = query.filter(FornecedorMadeiraPostaPrecoBitolaModel.transportadora_id == transportadora_id)
        else:
            query = query.filter(FornecedorMadeiraPostaPrecoBitolaModel.transportadora_id.is_(None))
        
        return query.first()

    @staticmethod
    def listar_precos_madeira_posta_fornecedor(fornecedor_id, cliente_id=None, transportadora_id=None):
        """
        Lista todos os preços de madeira posta de um fornecedor.
        
        Args:
            fornecedor_id (int): ID do fornecedor
            cliente_id (int, optional): Filtrar por cliente específico
            transportadora_id (int, optional): Filtrar por transportadora específica
            
        Returns:
            list: Lista de registros FornecedorMadeiraPostaPrecoBitolaModel
        """
        query = FornecedorMadeiraPostaPrecoBitolaModel.query.filter(
            FornecedorMadeiraPostaPrecoBitolaModel.fornecedor_id == fornecedor_id,
            FornecedorMadeiraPostaPrecoBitolaModel.ativo == True,
            FornecedorMadeiraPostaPrecoBitolaModel.deletado == False
        )
        
        if cliente_id:
            query = query.filter(FornecedorMadeiraPostaPrecoBitolaModel.cliente_id == cliente_id)
            
        if transportadora_id:
            query = query.filter(FornecedorMadeiraPostaPrecoBitolaModel.transportadora_id == transportadora_id)
        
        return query.order_by(
            FornecedorMadeiraPostaPrecoBitolaModel.cliente_id.asc(),
            FornecedorMadeiraPostaPrecoBitolaModel.produto_id.asc(),
            FornecedorMadeiraPostaPrecoBitolaModel.bitola_id.asc()
        ).all()

    @staticmethod
    def atualizar_ou_criar_preco_madeira_posta(fornecedor_id, cliente_id, produto_id, bitola_id, 
                                               preco_madeira_posta_100=None, transportadora_id=None):
        """
        Atualiza um registro existente ou cria um novo se não existir.
        
        Args:
            fornecedor_id (int): ID do fornecedor
            cliente_id (int): ID do cliente
            produto_id (int): ID do produto
            bitola_id (int): ID da bitola
            preco_madeira_posta_100 (int, optional): Preço por 100
            transportadora_id (int, optional): ID da transportadora
            
        Returns:
            FornecedorMadeiraPostaPrecoBitolaModel: Registro atualizado ou criado
        """
        registro = FornecedorMadeiraPostaPrecoBitolaModel.obter_preco_madeira_posta(
            fornecedor_id, cliente_id, produto_id, bitola_id, transportadora_id
        )
        
        if registro:
            if preco_madeira_posta_100 is not None:
                registro.preco_madeira_posta_100 = preco_madeira_posta_100
        else:
            registro = FornecedorMadeiraPostaPrecoBitolaModel(
                fornecedor_id=fornecedor_id,
                cliente_id=cliente_id,
                produto_id=produto_id,
                bitola_id=bitola_id,
                preco_madeira_posta_100=preco_madeira_posta_100,
                transportadora_id=transportadora_id
            )
            db.session.add(registro)
        
        return registro

    @staticmethod
    def listar_por_fornecedor_cliente(fornecedor_id, cliente_id, transportadora_id=None):
        """
        Lista preços para um fornecedor e cliente específicos, agrupados por produto.
        
        Args:
            fornecedor_id (int): ID do fornecedor
            cliente_id (int): ID do cliente
            transportadora_id (int, optional): ID da transportadora
            
        Returns:
            dict: Dicionário com preços agrupados por produto
        """
        query = FornecedorMadeiraPostaPrecoBitolaModel.query.filter(
            FornecedorMadeiraPostaPrecoBitolaModel.fornecedor_id == fornecedor_id,
            FornecedorMadeiraPostaPrecoBitolaModel.cliente_id == cliente_id,
            FornecedorMadeiraPostaPrecoBitolaModel.ativo == True,
            FornecedorMadeiraPostaPrecoBitolaModel.deletado == False
        )
        
        if transportadora_id:
            query = query.filter(FornecedorMadeiraPostaPrecoBitolaModel.transportadora_id == transportadora_id)
        else:
            query = query.filter(FornecedorMadeiraPostaPrecoBitolaModel.transportadora_id.is_(None))
        
        registros = query.all()
        
        resultado = {}
        for registro in registros:
            produto_nome = registro.produto.nome if registro.produto else f"Produto_{registro.produto_id}"
            if produto_nome not in resultado:
                resultado[produto_nome] = []
            
            resultado[produto_nome].append({
                'bitola_id': registro.bitola_id,
                'bitola_nome': registro.bitola.nome if registro.bitola else f"Bitola_{registro.bitola_id}",
                'preco_100': registro.preco_madeira_posta_100
            })
        
        return resultado