from ..base_model import BaseModel, db
from sqlalchemy import and_, desc


class PedidoCompraModel(BaseModel):
    """
    Model para registro de Pedidos de Compra (Escalas de Pedido).
    
    Um Pedido de Compra agrupa vários itens (cargas) que serão entregues.
    Funciona como uma "escala" que organiza as cargas por fornecedor/floresta.
    
    Attributes:
        id: Identificador único do pedido
        codigo_transacao: Código único no formato PED-XXXXXX para identificação
        usuario_id: ID do usuário que criou o pedido
        ativo: Flag de status ativo/inativo
        
    Relationships:
        usuario: Relacionamento com o usuário que criou
        itens: Relacionamento 1:N com os itens do pedido (lazy='dynamic' permite filtros)
    """
    __tablename__ = 'ped_pedido_compra'
    
    # === Campos Principais ===
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    codigo_transacao = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # === Relacionamento com Usuário ===
    # Usuário que criou o pedido de compra
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    usuario = db.relationship('UsuarioModel', backref=db.backref('pedido_compra', lazy='dynamic'))
    
    # === Status ===
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(self, usuario_id, ativo=True):
        """
        Inicializa um novo Pedido de Compra.
        
        Args:
            usuario_id: ID do usuário que está criando o pedido
            ativo: Status inicial do pedido (default: True)
        """
        # Gera automaticamente o código único do pedido
        self.codigo_transacao = self.gerar_codigo_novo_pedido_compra()
        self.usuario_id = usuario_id
        self.ativo = ativo
        
    @staticmethod
    def gerar_codigo_novo_pedido_compra():
        """
        Gera um código único para o pedido de compra no formato PED-XXXXXX.
        
        O código é sequencial e baseado no último ID existente no banco.
        Exemplo: PED-000001, PED-000002, etc.
        
        Returns:
            str: Código único no formato PED-XXXXXX
        """
        # Busca o último pedido ativo ordenado por ID decrescente
        ultimo_pedido = (
            PedidoCompraModel.query.filter(PedidoCompraModel.ativo == True)
            .order_by(desc(PedidoCompraModel.id))
            .first()
        )

        # Se não existe nenhum pedido, começa do 1
        if not ultimo_pedido:
            codigo = "PED-000001"
        else:
            # Incrementa o ID para gerar o próximo código
            id = str(ultimo_pedido.id + 1)

            # Preenche com zeros à esquerda até ter 6 dígitos
            while len(id) < 6:
                id = "0" + id

            codigo = "PED-" + id

        return codigo
    
    @staticmethod
    def listar_pedidos_compra():
        """
        Lista todos os pedidos de compra ativos e não deletados.
        
        Returns:
            list: Lista de PedidoCompraModel ordenados por ID decrescente (mais recentes primeiro)
        """
        return PedidoCompraModel.query.filter(
            PedidoCompraModel.deletado == False,
            PedidoCompraModel.ativo == True
        ).order_by(desc(PedidoCompraModel.id)).all()
    
    @staticmethod
    def obter_por_id(pedido_id):
        """
        Obtém um pedido de compra específico por ID.
        
        Args:
            pedido_id: ID do pedido a ser buscado
            
        Returns:
            PedidoCompraModel: O pedido encontrado ou None se não existir
        """
        return PedidoCompraModel.query.filter(
            PedidoCompraModel.id == pedido_id,
            PedidoCompraModel.deletado == False
        ).first()
    
    @staticmethod
    def obter_por_codigo(codigo_transacao):
        """
        Obtém um pedido de compra pelo código de transação.
        
        Args:
            codigo_transacao: Código único do pedido (ex: PED-000001)
            
        Returns:
            PedidoCompraModel: O pedido encontrado ou None se não existir
        """
        return PedidoCompraModel.query.filter(
            PedidoCompraModel.codigo_transacao == codigo_transacao,
            PedidoCompraModel.deletado == False
        ).first()
    
    def obter_itens_ativos(self):
        """
        Obtém todos os itens ativos deste pedido de compra.
        
        Returns:
            list: Lista de PedidoCompraItemModel ativos
        """
        return self.itens.filter_by(ativo=True, deletado=False).all()
    
    def obter_itens_agrupados_por_fornecedor(self):
        """
        Agrupa os itens do pedido por fornecedor.
        
        Útil para relatórios onde as cargas precisam ser 
        listadas por fornecedor/floresta.
        
        Returns:
            dict: Dicionário onde a chave é o fornecedor_id e o valor é a lista de itens
        """
        itens = self.obter_itens_ativos()
        agrupados = {}
        
        for item in itens:
            fornecedor_id = item.fornecedor_id or 0  # 0 para itens sem fornecedor
            if fornecedor_id not in agrupados:
                agrupados[fornecedor_id] = []
            agrupados[fornecedor_id].append(item)
        
        return agrupados
    
    def contar_itens(self):
        """
        Conta quantos itens ativos existem neste pedido.
        
        Returns:
            int: Quantidade de itens ativos
        """
        return self.itens.filter_by(ativo=True, deletado=False).count()
    
    def __repr__(self):
        """Representação em string do objeto para debug"""
        return f"<PedidoCompraModel {self.codigo_transacao}>"

