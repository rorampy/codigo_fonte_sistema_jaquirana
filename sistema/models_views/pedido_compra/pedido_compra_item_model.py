from ..base_model import BaseModel, db
from sqlalchemy import and_, desc


class PedidoCompraItemModel(BaseModel):
    """
    Model para registro dos itens (cargas) de um Pedido de Compra.
    
    Cada item representa uma carga/entrega individual dentro de uma escala de pedido.
    Contém informações sobre datas, fornecedor, transportadora, motorista, veículo e extrator.
    
    Attributes:
        id: Identificador único do item
        pedido_compra_id: FK para o pedido de compra pai
        data_carga: Data em que a carga será feita
        data_entrega: Data prevista de entrega
        fornecedor_id: FK para o fornecedor/floresta
        transportadora_id: FK para a transportadora
        motorista_id: FK para o motorista
        veiculo_id: FK para o veículo (placa)
        extrator_id: FK para o extrator/corte
        usuario_id: ID do usuário que criou o item
        ativo: Flag de status ativo/inativo
        
    Relationships:
        pedido_compra: Relacionamento N:1 com PedidoCompraModel
        fornecedor: Relacionamento com FornecedorCadastroModel
        transportadora: Relacionamento com TransportadoraModel
        motorista: Relacionamento com MotoristaModel
        veiculo: Relacionamento com VeiculoModel
        extrator: Relacionamento com ExtratorModel
        usuario: Relacionamento com UsuarioModel
    """
    __tablename__ = 'ped_pedido_compra_item'
    
    # === Campos Principais ===
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    
    # === Relacionamento com Pedido de Compra (pai) ===
    # Cada item pertence a um pedido de compra
    # lazy='dynamic' permite fazer queries adicionais nos itens
    pedido_compra_id = db.Column(db.Integer, db.ForeignKey('ped_pedido_compra.id'), nullable=False)
    pedido_compra = db.relationship('PedidoCompraModel', backref=db.backref('itens', lazy='dynamic'))
    
    # === Datas ===
    data_carga = db.Column(db.Date, nullable=False)      # Data que a carga será realizada
    data_entrega = db.Column(db.Date, nullable=False)    # Data prevista de entrega ao cliente
    
    # === Relacionamento com Fornecedor/Floresta ===
    # Fornecedor de onde a madeira será retirada
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('for_fornecedor_cadastro.id'), nullable=True)
    fornecedor = db.relationship('FornecedorCadastroModel', backref=db.backref('pedido_compra_for_itens', lazy='dynamic'))
    
    # === Relacionamento com Transportadora ===
    # Empresa responsável pelo transporte
    transportadora_id = db.Column(db.Integer, db.ForeignKey('transp_transportadora.id'), nullable=True)
    transportadora = db.relationship('TransportadoraModel', backref=db.backref('pedido_compra_transp_itens', lazy='dynamic'))
    
    # === Relacionamento com Motorista ===
    # Motorista que fará o transporte
    motorista_id = db.Column(db.Integer, db.ForeignKey('transp_motorista.id'), nullable=True)
    motorista = db.relationship('MotoristaModel', backref=db.backref('pedido_compra_moto_itens', lazy='dynamic'))
    
    # === Relacionamento com Veículo ===
    # Placa do veículo que fará o transporte
    veiculo_id = db.Column(db.Integer, db.ForeignKey('transp_veiculo.id'), nullable=True)
    veiculo = db.relationship('VeiculoModel', backref=db.backref('pedido_compra_veic_itens', lazy='dynamic'))
    
    # === Relacionamento com Extrator ===
    # Empresa/pessoa responsável pelo corte/extração
    extrator_id = db.Column(db.Integer, db.ForeignKey('ext_extrator.id'), nullable=True)
    extrator = db.relationship('ExtratorModel', backref=db.backref('pedido_compra_extrator_itens', lazy='dynamic'))
    
    # === Relacionamento com Usuário ===
    # Usuário que criou este item
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    usuario = db.relationship('UsuarioModel', backref=db.backref('pedido_compra_usuario_itens', lazy='dynamic'))
    
    # === Status ===
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(
        self, 
        pedido_compra_id, 
        data_carga, 
        data_entrega, 
        fornecedor_id=None, 
        transportadora_id=None, 
        motorista_id=None, 
        veiculo_id=None, 
        extrator_id=None, 
        usuario_id=None, 
        ativo=True
    ):
        """
        Inicializa um novo item de Pedido de Compra.
        
        Args:
            pedido_compra_id: ID do pedido de compra pai (obrigatório)
            data_carga: Data da carga (obrigatório)
            data_entrega: Data de entrega (obrigatório)
            fornecedor_id: ID do fornecedor/floresta (opcional)
            transportadora_id: ID da transportadora (opcional)
            motorista_id: ID do motorista (opcional)
            veiculo_id: ID do veículo/placa (opcional)
            extrator_id: ID do extrator/corte (opcional)
            usuario_id: ID do usuário que criou (opcional)
            ativo: Status inicial do item (default: True)
        """
        self.pedido_compra_id = pedido_compra_id
        self.data_carga = data_carga
        self.data_entrega = data_entrega
        self.fornecedor_id = fornecedor_id
        self.transportadora_id = transportadora_id
        self.motorista_id = motorista_id
        self.veiculo_id = veiculo_id
        self.extrator_id = extrator_id
        self.usuario_id = usuario_id
        self.ativo = ativo
    
    @staticmethod
    def listar_por_pedido(pedido_compra_id):
        """
        Lista todos os itens ativos de um pedido de compra específico.
        
        Args:
            pedido_compra_id: ID do pedido de compra
            
        Returns:
            list: Lista de PedidoCompraItemModel ativos e não deletados
        """
        return PedidoCompraItemModel.query.filter(
            PedidoCompraItemModel.pedido_compra_id == pedido_compra_id,
            PedidoCompraItemModel.deletado == False,
            PedidoCompraItemModel.ativo == True
        ).order_by(PedidoCompraItemModel.data_carga).all()
    
    @staticmethod
    def obter_por_id(item_id):
        """
        Obtém um item específico por ID.
        
        Args:
            item_id: ID do item a ser buscado
            
        Returns:
            PedidoCompraItemModel: O item encontrado ou None se não existir
        """
        return PedidoCompraItemModel.query.filter(
            PedidoCompraItemModel.id == item_id,
            PedidoCompraItemModel.deletado == False
        ).first()
    
    def obter_nome_fornecedor(self):
        """
        Obtém o nome do fornecedor de forma segura.
        
        Returns:
            str: Nome/identificação do fornecedor ou 'Não informado'
        """
        if self.fornecedor:
            return self.fornecedor.identificacao
        return 'Não informado'
    
    def obter_nome_transportadora(self):
        """
        Obtém o nome da transportadora de forma segura.
        
        Returns:
            str: Nome/identificação da transportadora ou 'Não informada'
        """
        if self.transportadora:
            return self.transportadora.identificacao
        return 'Não informada'
    
    def obter_nome_motorista(self):
        """
        Obtém o nome do motorista de forma segura.
        
        Returns:
            str: Nome do motorista ou 'Não informado'
        """
        if self.motorista:
            return self.motorista.nome_completo
        return 'Não informado'
    
    def obter_placa_veiculo(self):
        """
        Obtém a placa do veículo de forma segura.
        
        Returns:
            str: Placa do veículo ou 'Não informada'
        """
        if self.veiculo:
            return self.veiculo.placa_veiculo
        return 'Não informada'
    
    def obter_nome_extrator(self):
        """
        Obtém o nome do extrator de forma segura.
        
        Returns:
            str: Nome/identificação do extrator ou 'Não informado'
        """
        if self.extrator:
            return self.extrator.identificacao
        return 'Não informado'
    
    @staticmethod
    def listar_itens_ativos_agrupados_por_fornecedor():
        """
        Lista todos os itens ativos de pedidos de compra agrupados por fornecedor.
        
        Busca todos os itens de pedidos ativos e os agrupa por fornecedor_id,
        retornando um dicionário onde a chave é o fornecedor_id e o valor
        é um dict com 'fornecedor' (objeto) e 'itens' (lista).
        
        Returns:
            dict: Dicionário com estrutura:
                {
                    fornecedor_id: {
                        'fornecedor': FornecedorCadastroModel ou None,
                        'itens': [PedidoCompraItemModel, ...]
                    },
                    ...
                }
        """
        from sistema.models_views.pedido_compra.pedido_compra_model import PedidoCompraModel
        
        # Busca todos os itens de pedidos ativos
        itens = PedidoCompraItemModel.query.join(
            PedidoCompraModel, PedidoCompraItemModel.pedido_compra_id == PedidoCompraModel.id
        ).filter(
            PedidoCompraModel.deletado == False,
            PedidoCompraModel.ativo == True,
            PedidoCompraItemModel.deletado == False
        ).order_by(
            PedidoCompraItemModel.fornecedor_id,
            PedidoCompraItemModel.data_carga.desc()
        ).all()
        
        # Agrupa itens por fornecedor
        itens_por_fornecedor = {}
        for item in itens:
            fornecedor_id = item.fornecedor_id or 0  # 0 para itens sem fornecedor
            if fornecedor_id not in itens_por_fornecedor:
                itens_por_fornecedor[fornecedor_id] = {
                    'fornecedor': item.fornecedor,
                    'itens': []
                }
            itens_por_fornecedor[fornecedor_id]['itens'].append(item)
        
        return itens_por_fornecedor
    
    def __repr__(self):
        """Representação em string do objeto para debug"""
        return f"<PedidoCompraItemModel {self.id} - Pedido: {self.pedido_compra_id}>"

