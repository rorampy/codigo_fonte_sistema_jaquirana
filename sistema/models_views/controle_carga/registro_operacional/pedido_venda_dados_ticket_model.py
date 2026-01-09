from ...base_model import BaseModel, db

class PedidoVendaDadosTicketModel(BaseModel):

    __tablename__ = "ped_pedido_venda_dados_ticket"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    pedido_venda_id = db.Column(db.Integer, db.ForeignKey("ped_pedido_venda.id"), nullable=True)
    pedido_venda = db.relationship("PedidoVendaModel", backref=db.backref("pedido_venda_dados_ticket", lazy=True))
    
    placa_ticket = db.Column(db.String(50), nullable=True)
    motorista_ticket = db.Column(db.String(200), nullable=True)
    data_entrega_ticket = db.Column(db.Date, nullable=True)
    numero_nota_fiscal_ticket = db.Column(db.String(20), nullable=True)
    peso_liquido_ticket = db.Column(db.Float, nullable=True)
    
    fornecedor_id = db.Column(db.Integer, db.ForeignKey("for_fornecedor_cadastro.id"), nullable=True)
    fornecedor = db.relationship("FornecedorCadastroModel", foreign_keys=[fornecedor_id], backref=db.backref("pedido_venda_dados_ticket_fornecedor", lazy=True))

    arquivo_ticket_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    arquivo_ticket = db.relationship("UploadArquivoModel", foreign_keys=[arquivo_ticket_id], backref=db.backref("pedido_venda_dados_ticket", lazy=True))

    ativo = db.Column(db.Boolean, default=True, nullable=False)

    def __init__(self, 
            pedido_venda_id=None,
            placa_ticket=None,
            motorista_ticket=None,
            data_entrega_ticket=None,
            numero_nota_fiscal_ticket=None,
            peso_liquido_ticket=None,
            arquivo_ticket_id=None,
            fornecedor_id=None,
            ativo=True
        ):
        
        self.pedido_venda_id = pedido_venda_id
        self.placa_ticket = placa_ticket
        self.motorista_ticket = motorista_ticket
        self.data_entrega_ticket = data_entrega_ticket  
        self.numero_nota_fiscal_ticket = numero_nota_fiscal_ticket
        self.peso_liquido_ticket = peso_liquido_ticket
        self.arquivo_ticket_id = arquivo_ticket_id
        self.fornecedor_id = fornecedor_id
        self.ativo = ativo
        
    @staticmethod
    def obter_dados_ticket_por_pedido_venda_id(pedido_venda_id):
        """
        Obtém os dados do ticket associados a um pedido de venda específico.
        :param pedido_venda_id: ID do pedido de venda.
        :return: Instância de PedidoVendaDadosTicketModel ou None se não encontrado.
        """
        return PedidoVendaDadosTicketModel.query.filter_by(
            pedido_venda_id=pedido_venda_id,
            ativo=True,
            deletado=False
        ).first()
    
    @staticmethod
    def listar_dados_ticket_por_pedido_venda_id(pedido_venda_id):
        """
        Lista todos os dados de ticket associados a um pedido de venda específico.
        :param pedido_venda_id: ID do pedido de venda.
        :return: Lista de instâncias de PedidoVendaDadosTicketModel.
        """
        return PedidoVendaDadosTicketModel.query.filter_by(
            pedido_venda_id=pedido_venda_id,
            ativo=True,
            deletado=False
        ).all()