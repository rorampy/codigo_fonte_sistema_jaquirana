from ...base_model import BaseModel, db
from sqlalchemy import and_, or_, func
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema.models_views.gerenciar.motorista.motorista_model import MotoristaModel
from sistema.models_views.gerenciar.veiculo.veiculo_model import VeiculoModel
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel


class SolicitacaoPedidoVendaModel(BaseModel):
    """
    Model para registro do controle de cargas.
    """

    __tablename__ = "spv_solicitacao_pedido_venda"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    empresa_emissora_id = db.Column(db.Integer, db.ForeignKey("em_empresa_emissora.id"), default=None, nullable=True)
    empresa_emissora = db.relationship("EmpresaEmissoraModel", backref=db.backref("solicitacao_empresa_emissora", lazy=True))

    cliente_id = db.Column(db.Integer, db.ForeignKey("cli_cliente.id"), nullable=False)
    cliente = db.relationship("ClienteModel", backref=db.backref("solicitacao_cliente", lazy=True))
    
    bitola_id = db.Column(db.Integer, db.ForeignKey("z_sys_bitola.id"), nullable=False)
    bitola = db.relationship("BitolaModel", backref=db.backref("solicitacao_bitola", lazy=True))

    produto_id = db.Column(db.Integer, db.ForeignKey("prod_produto.id"), nullable=False)
    produto = db.relationship("ProdutoModel", backref=db.backref("solicitacao_produto", lazy=True))

    grupo_whats_id = db.Column(db.Integer, db.ForeignKey("z_sys_nome_grupo.id"), nullable=True)
    grupo_whats = db.relationship("NomeGrupoWhatsModel", backref=db.backref("solicitacao_grupo", lazy=True))
    
    certificacao_id = db.Column(db.Integer, db.ForeignKey("est_certificacao_estoque.id"), nullable=True)
    certificacao = db.relationship("CertificacoesModel", backref=db.backref("solicitacao_certificacao", lazy=True))
    
    veiculo_id = db.Column(db.Integer, db.ForeignKey("transp_veiculo.id"), nullable=False)
    veiculo = db.relationship("VeiculoModel", backref=db.backref("solicitacao_veiculo", lazy=True))
    
    transportadora_id = db.Column(db.Integer, db.ForeignKey("transp_transportadora.id"), nullable=False)
    transportadora = db.relationship("TransportadoraModel", backref=db.backref("solicitacao_transportadora", lazy=True))

    motorista_id = db.Column(db.Integer, db.ForeignKey("transp_motorista.id"), nullable=False)
    motorista = db.relationship("MotoristaModel", backref=db.backref("solicitacao_motorista", lazy=True))

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    usuario = db.relationship("UsuarioModel", backref=db.backref("solicitacao_usuario", lazy=True))

    nf_emitida = db.Column(db.Boolean, default=False, nullable=False)
    ticket_emitido = db.Column(db.Boolean, default=False, nullable=False)

    cancelada = db.Column(db.Boolean, default=False, nullable=False)
    realizado_split = db.Column(db.Boolean, default=False, nullable=True) 
    
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    def __init__(
        self,
        empresa_emissora_id,
        cliente_id,
        bitola_id,
        produto_id,
        grupo_whats_id,
        certificacao_id,
        veiculo_id,
        transportadora_id,
        motorista_id,
        usuario_id,
        nf_emitida=False,
        ticket_emitido=False,
        cancelada=False,
        realizado_split=False,
        ativo=True,
    ):
        self.empresa_emissora_id = empresa_emissora_id
        self.cliente_id = cliente_id
        self.bitola_id = bitola_id
        self.produto_id = produto_id
        self.grupo_whats_id = grupo_whats_id
        self.certificacao_id = certificacao_id
        self.veiculo_id = veiculo_id
        self.transportadora_id = transportadora_id
        self.motorista_id = motorista_id
        self.usuario_id = usuario_id
        self.nf_emitida = nf_emitida
        self.ticket_emitido = ticket_emitido
        self.cancelada = cancelada
        self.realizado_split = realizado_split
        self.ativo = ativo

    @staticmethod
    def obter_solicitacao_por_id(id):
        """
        Obtém uma solicitação específica pelo ID.
        
        Args:
            id (int): ID da solicitação a ser buscada
            
        Returns:
            SolicitacaoPedidoVendaModel: Solicitação encontrada ou None se não existir
        
        Example:
            >>> solicitacao = SolicitacaoPedidoVendaModel.obter_solicitacao_por_id(1)
            >>> if solicitacao:
            ...     print(solicitacao.obter_identificacao_completa())
        """
        solicitacao = SolicitacaoPedidoVendaModel.query.filter(
            SolicitacaoPedidoVendaModel.id == id,
            SolicitacaoPedidoVendaModel.ativo == True,
            SolicitacaoPedidoVendaModel.deletado == False
        ).first()
        
        return solicitacao

    @staticmethod
    def obter_solicitacoes_em_aberto_desc_id():
        """
        Obtém solicitações em aberto (sem NF emitida).
        
        Returns:
            list: Lista de solicitações em aberto ordenadas por ID decrescente
        
        Example:
            >>> solicitacoes = SolicitacaoPedidoVendaModel.obter_solicitacoes_em_aberto_desc_id()
            >>> for sol in solicitacoes:
            ...     print(sol.obter_identificacao_completa())
        """
        solicitacoes = (
            SolicitacaoPedidoVendaModel.query.filter(
                SolicitacaoPedidoVendaModel.ativo == True,
                SolicitacaoPedidoVendaModel.deletado == False,
                SolicitacaoPedidoVendaModel.nf_emitida != True,
            )
            .order_by(SolicitacaoPedidoVendaModel.id.desc())
            .all()
        )
        
        return solicitacoes

    @staticmethod
    def filtrar_solicitacoes(
        cliente_nome=None,
        motorista_nome=None,
        placa=None,
    ):
        """
        Filtra solicitações em aberto por múltiplos critérios.
        
        Args:
            cliente_nome (str, optional): Nome do cliente
            motorista_nome (str, optional): Nome do motorista
            placa (str, optional): Placa do veículo
            
        Returns:
            list: Lista de solicitações filtradas ordenadas por ID decrescente
        
        Example:
            >>> solicitacoes = SolicitacaoPedidoVendaModel.filtrar_solicitacoes(
            ...     cliente_nome='Silva',
            ...     placa='ABC'
            ... )
        """
        query = (
            SolicitacaoPedidoVendaModel.query
            .join(SolicitacaoPedidoVendaModel.cliente)
            .join(SolicitacaoPedidoVendaModel.veiculo)
            .join(SolicitacaoPedidoVendaModel.motorista)
        )
        
        if cliente_nome:
            query = query.filter(ClienteModel.identificacao.like(f"%{cliente_nome}%"))
        
        if motorista_nome:
            query = query.filter(
                MotoristaModel.nome_completo.like(f"%{motorista_nome}%")
            )
        
        if placa:
            query = query.filter(VeiculoModel.placa_veiculo.like(f"%{placa.lower()}%"))
        
        query = query.filter(
            SolicitacaoPedidoVendaModel.ativo == True,
            SolicitacaoPedidoVendaModel.deletado == False,
            SolicitacaoPedidoVendaModel.nf_emitida != True,
        )
        
        return query.order_by(SolicitacaoPedidoVendaModel.id.desc()).all()

    @staticmethod
    def cadastrar_solicitacao(
        empresa_emissora_id,
        cliente_id,
        bitola_id,
        produto_id,
        motorista_id,
        transportadora_id,
        veiculo_id,
        certificacao_id=None,
        usuario_id=None,
        grupo_whats_id=None,
        nf_emitida=False,
        cancelada=False,
        ativo=True,
    ):
        """
        Cria e cadastra uma nova solicitação no banco de dados.
        
        Args:
            empresa_emissora_id (int): ID da empresa emissora
            cliente_id (int): ID do cliente
            bitola_id (int): ID da bitola
            produto_id (int): ID do produto
            motorista_id (int): ID do motorista
            transportadora_id (int): ID da transportadora
            veiculo_id (int): ID do veículo
            certificacao_id (int, opcional): ID da certificação
            floresta_id (int, opcional): ID da floresta
            fornecedor_id (int, opcional): ID do fornecedor
            usuario_id (int, opcional): ID do usuário responsável
            grupo_whats_id (int, opcional): ID do grupo do WhatsApp
            nf_emitida (bool, opcional): Indica se a NF já foi emitida
            cancelada (bool, opcional): Indica se a solicitação está cancelada
            ativo (bool, opcional): Indica se a solicitação está ativa
            
        Returns:
            SolicitacaoPedidoVendaModel: Instância da solicitação criada e salva no banco de dados
        
        Example:
            >>> nova_solicitacao = SolicitacaoPedidoVendaModel.cadastrar_solicitacao(
            ...     empresa_emissora_id=1,
            ...     cliente_id=5,
            ...     bitola_id=2,
            ...     produto_id=3,
            ...     motorista_id=10,
            ...     transportadora_id=4,
            ...     veiculo_id=8,
            ...     usuario_id=1
            ... )
        """
        solicitacao = SolicitacaoPedidoVendaModel(
            empresa_emissora_id=empresa_emissora_id,
            cliente_id=cliente_id,
            bitola_id=bitola_id,
            produto_id=produto_id,
            motorista_id=motorista_id,
            veiculo_id=veiculo_id,
            usuario_id=usuario_id,
            certificacao_id=certificacao_id,
            transportadora_id=transportadora_id,
            grupo_whats_id=grupo_whats_id,
            nf_emitida=nf_emitida,
            cancelada=cancelada,
            ativo=ativo,
        )
        db.session.add(solicitacao)
        db.session.commit()
        return solicitacao

    @staticmethod
    def listar_cargas():
        """
        Lista solicitações em aberto (sem NF e sem ticket emitidos).
        
        Returns:
            list: Lista de solicitações em aberto ordenadas por ID decrescente
        
        Example:
            >>> solicitacoes = SolicitacaoPedidoVendaModel.listar_cargas()
            >>> print(f"Total em aberto: {len(solicitacoes)}")
        """
        solicitacoes = (
            SolicitacaoPedidoVendaModel.query.filter(
                SolicitacaoPedidoVendaModel.nf_emitida == False,
                SolicitacaoPedidoVendaModel.ticket_emitido == False,
                SolicitacaoPedidoVendaModel.ativo == True,
                SolicitacaoPedidoVendaModel.deletado == False,
            )
            .order_by(SolicitacaoPedidoVendaModel.id.desc())
            .all()
        )
        
        return solicitacoes

    
