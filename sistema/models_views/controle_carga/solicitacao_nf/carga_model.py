from ...base_model import BaseModel, db
from sqlalchemy import and_, or_, func
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema.models_views.gerenciar.motorista.motorista_model import MotoristaModel
from sistema.models_views.gerenciar.veiculo.veiculo_model import VeiculoModel
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel


class CargaModel(BaseModel):
    """
    Model para registro do controle de cargas.
    """

    __tablename__ = "car_carga"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    empresa_emissora_id = db.Column(db.Integer, db.ForeignKey("em_empresa_emissora.id"), default=None, nullable=True)
    empresa_emissora = db.relationship("EmpresaEmissoraModel", backref=db.backref("empresa_emissora_carga", lazy=True))

    cliente_id = db.Column(db.Integer, db.ForeignKey("cli_cliente.id"), nullable=False)
    cliente = db.relationship("ClienteModel", backref=db.backref("car_carga", lazy=True))

    floresta_id = db.Column(db.Integer, db.ForeignKey("flor_floresta.id"), nullable=True)
    floresta = db.relationship("FlorestaModel", backref=db.backref("car_carga", lazy=True))

    transportadora_id = db.Column(db.Integer, nullable=True)

    fornecedor_id = db.Column(db.Integer, db.ForeignKey("for_fornecedor_cadastro.id"), nullable=True)
    fornecedor = db.relationship("FornecedorCadastroModel", backref=db.backref("car_carga_fornecedor", lazy=True))

    bitola_id = db.Column(db.Integer, db.ForeignKey("z_sys_bitola.id"), nullable=False)
    bitola = db.relationship("BitolaModel", backref=db.backref("car_carga", lazy=True))

    produto_id = db.Column(db.Integer, db.ForeignKey("prod_produto.id"), nullable=False)
    produto = db.relationship("ProdutoModel", backref=db.backref("car_carga_produto", lazy=True))

    motorista_id = db.Column(db.Integer, db.ForeignKey("transp_motorista.id"), nullable=False)
    motorista = db.relationship("MotoristaModel", backref=db.backref("car_carga_motorista", lazy=True))

    veiculo_id = db.Column(db.Integer, db.ForeignKey("transp_veiculo.id"), nullable=False)
    veiculo = db.relationship("VeiculoModel", backref=db.backref("car_carga_veiculo", lazy=True))

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    usuario = db.relationship("UsuarioModel", backref=db.backref("car_carga_usuario", lazy=True))
    
    certificacao_id = db.Column(db.Integer, db.ForeignKey("est_certificacao_estoque.id"), nullable=True)
    certificacao = db.relationship("CertificacoesModel", backref=db.backref("car_carga_certificacao", lazy=True))

    grupo_whats_id = db.Column(db.Integer, db.ForeignKey("z_sys_nome_grupo.id"), nullable=True)
    grupo_whats = db.relationship("NomeGrupoWhatsModel", backref=db.backref("car_carga_grupo", lazy=True))

    data_hora_msg_whats = db.Column(db.DateTime, nullable=True)

    nf_emitida = db.Column(db.Boolean, default=False, nullable=False)
    ticket_emitido = db.Column(db.Boolean, default=False, nullable=False)

    cancelada = db.Column(db.Boolean, default=False, nullable=False)
    realizado_split = db.Column(db.Boolean, default=False, nullable=True) 

    transportadora_veiculo_assoc = db.relationship(
        "TransportadoraVeiculoAssocModel",
        foreign_keys=[transportadora_id],
        primaryjoin="CargaModel.transportadora_id == TransportadoraVeiculoAssocModel.transportadora_id"
    )

    ativo = db.Column(db.Boolean, default=True, nullable=False)

    def __init__(
        self,
        cliente_id,
        bitola_id,
        produto_id,
        motorista_id,
        veiculo_id,
        usuario_id,
        certificacao_id = None,
        transportadora_id = None,
        floresta_id=None,
        fornecedor_id=None,
        grupo_whats_id=None,
        data_hora_msg_whats=None,
        ticket_emitido=False,
        nf_emitida=False,
        cancelada=False,
        empresa_emissora_id=None,
        realizado_split=False,
        ativo=True,
    ):
        self.cliente_id = cliente_id
        self.transportadora_id = transportadora_id
        self.bitola_id = bitola_id
        self.produto_id = produto_id
        self.motorista_id = motorista_id
        self.veiculo_id = veiculo_id
        self.data_hora_msg_whats = data_hora_msg_whats
        self.certificacao_id = certificacao_id
        self.usuario_id = usuario_id
        self.floresta_id = floresta_id
        self.fornecedor_id = fornecedor_id
        self.grupo_whats_id = grupo_whats_id
        self.nf_emitida = nf_emitida
        self.ticket_emitido = ticket_emitido
        self.cancelada = cancelada
        self.empresa_emissora_id = empresa_emissora_id
        self.realizado_split = realizado_split
        self.ativo = ativo

    @property
    def transportadora_exibicao(self):
        """
        Retorna a transportadora para exibição.
        
        Returns:
            TransportadoraModel: Transportadora da carga ou transportadora do motorista
        """
        if self.transportadora_id:
            return TransportadoraModel.obter_transportadora_por_id(self.transportadora_id)
        return self.motorista.transportadora

    def cadastrar_solicitacao(
        empresa_emissora_id,
        cliente_id,
        bitola_id,
        produto_id,
        motorista_id,
        transportadora_id,
        veiculo_id,
        certificacao_id=None,
        floresta_id=None,
        fornecedor_id=None,
        data_hora_msg_whats=None,
        usuario_id=None,
        grupo_whats_id=None,
        nf_emitida=False,
        cancelada=False,
        ativo=True,
    ):
        """
        Cria e cadastra uma nova solicitação de carga no banco de dados.

        Args:
            empresa_emissora_id (int): ID da empresa emissora (opcional)
            cliente_id (int): ID do cliente
            bitola_id (int): ID da bitola
            produto_id (int): ID do produto
            motorista_id (int): ID do motorista
            transportadora_id (int): ID da transportadora (opcional)
            veiculo_id (int): ID do veículo
            floresta_id (int, opcional): ID da floresta
            fornecedor_id (int, opcional): ID do fornecedor
            data_hora_msg_whats (datetime, opcional): Data/hora da mensagem do WhatsApp
            usuario_id (int, opcional): ID do usuário responsável
            grupo_whats_id (int, opcional): ID do grupo do WhatsApp
            nf_emitida (bool, opcional): Indica se a NF já foi emitida
            cancelada (bool, opcional): Indica se a solicitação está cancelada
            ativo (bool, opcional): Indica se a solicitação está ativa

        Returns:
            CargaModel: Instância da solicitação criada e salva no banco de dados
        """
        solicitacao = CargaModel(
            cliente_id=cliente_id,
            bitola_id=bitola_id,
            produto_id=produto_id,
            motorista_id=motorista_id,
            veiculo_id=veiculo_id,
            usuario_id=usuario_id,
            certificacao_id=certificacao_id,
            transportadora_id=transportadora_id,
            floresta_id=floresta_id,
            fornecedor_id=fornecedor_id,
            grupo_whats_id=grupo_whats_id,
            data_hora_msg_whats=data_hora_msg_whats,
            nf_emitida=nf_emitida,
            cancelada=cancelada,
            empresa_emissora_id=empresa_emissora_id,
            ativo=ativo,
        )
        db.session.add(solicitacao)
        db.session.commit()
        return solicitacao

    def listar_cargas_encerradas():
        """
        Lista todas as cargas encerradas (com NF e ticket emitidos).
        
        Returns:
            list: Lista de cargas encerradas ordenadas por ID decrescente
        """
        solicitacoes = (
            CargaModel.query.filter(
                CargaModel.nf_emitida == 1,
                CargaModel.ticket_emitido == 1,
                CargaModel.ativo == 1,
            )
            .order_by(CargaModel.id.desc())
            .all()
        )

        return solicitacoes

    def listar_cargas():
        """
        Lista cargas em aberto (sem NF e sem ticket emitidos).
        
        Returns:
            list: Lista de cargas em aberto ordenadas por ID decrescente
        """
        solicitacoes = (
            CargaModel.query.filter(
                CargaModel.nf_emitida == 0,
                CargaModel.ticket_emitido == 0,
                CargaModel.ativo == 1,
                CargaModel.deletado == 0,
            )
            .order_by(CargaModel.id.desc())
            .all()
        )

        return solicitacoes

    def listar_nfs_nao_emitidas():
        """
        Lista cargas com nota fiscal não emitida.
        
        Returns:
            list: Lista de cargas sem NF emitida ordenadas por ID decrescente
        """
        solicitacoes = (
            CargaModel.query.filter(CargaModel.nf_emitida == 0, CargaModel.ativo == 1)
            .order_by(CargaModel.id.desc())
            .all()
        )

        return solicitacoes

    def listar_tickets_nao_lancados():
        """
        Lista cargas com ticket não lançado.
        
        Returns:
            list: Lista de cargas sem ticket emitido ordenadas por ID decrescente
        """
        solicitacoes = (
            CargaModel.query.filter(
                CargaModel.ticket_emitido == 0, CargaModel.ativo == 1
            )
            .order_by(CargaModel.id.desc())
            .all()
        )

        return solicitacoes

    def obter_solicitacao_por_id(id):
        """
        Obtém uma solicitação de carga específica pelo ID.
        
        Args:
            id (int): ID da solicitação a ser buscada
            
        Returns:
            CargaModel: Solicitação encontrada ou None se não existir
        """
        solicitacao = CargaModel.query.filter(
            CargaModel.id == id, CargaModel.ativo == 1, CargaModel.deletado == 0
        ).first()

        return solicitacao

    def obter_solicitacoes_em_aberto_desc_id():
        """
        Obtém solicitações em aberto (sem NF emitida).
        
        Returns:
            list: Lista de solicitações em aberto ordenadas por ID decrescente
        """
        solicitacoes = (
            CargaModel.query.filter(
                CargaModel.ativo == 1,
                CargaModel.deletado == 0,
                CargaModel.nf_emitida != True,
            )
            .order_by(CargaModel.id.desc())
            .all()
        )

        return solicitacoes

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
        """
        query = (
            CargaModel.query.join(CargaModel.cliente)
            .join(CargaModel.veiculo)
            .join(CargaModel.motorista)
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
            CargaModel.ativo == True,
            CargaModel.deletado == False,
            CargaModel.nf_emitida != True,
        )

        return query.order_by(CargaModel.id.desc()).all()

    def obter_solicitacoes_em_aberto_ticket_desc_id():
        """
        Obtém solicitações com NF emitida mas sem ticket lançado.
        
        Returns:
            list: Lista de tuplas (CargaModel, RegistroOperacionalModel) ordenadas por ID decrescente
        """
        from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import (
            RegistroOperacionalModel,
        )

        query = (
            db.session.query(CargaModel, RegistroOperacionalModel)
            .join(
                RegistroOperacionalModel,
                RegistroOperacionalModel.solicitacao_nf_id == CargaModel.id,
            )
            .filter(
                CargaModel.ativo == True,
                CargaModel.deletado == False,
                CargaModel.nf_emitida == True,
                CargaModel.ticket_emitido == False,
            )
            .order_by(CargaModel.id.desc())
        )

        return query.all()

    def filtrar_solicitacoes_ticket(cliente_nome=None, motorista_nome=None, placa=None):
        """
        Filtra solicitações pendentes de ticket por múltiplos critérios.
        
        Args:
            cliente_nome (str, optional): Nome do cliente
            motorista_nome (str, optional): Nome do motorista
            placa (str, optional): Placa do veículo
            
        Returns:
            list: Lista de tuplas (CargaModel, RegistroOperacionalModel) filtradas ordenadas por ID decrescente
        """
        from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import (
            RegistroOperacionalModel,
        )

        query = (
            db.session.query(CargaModel, RegistroOperacionalModel)
            .join(
                RegistroOperacionalModel,
                RegistroOperacionalModel.solicitacao_nf_id == CargaModel.id,
            )
            .join(CargaModel.cliente)
            .join(CargaModel.veiculo)
            .join(CargaModel.motorista)
        )

        if cliente_nome:
            query = query.filter(ClienteModel.identificacao.ilike(f"%{cliente_nome}%"))

        if motorista_nome:
            query = query.filter(
                MotoristaModel.nome_completo.ilike(f"%{motorista_nome}%")
            )

        if placa:
            query = query.filter(VeiculoModel.placa_veiculo.ilike(f"%{placa.lower()}%"))

        query = query.filter(
            CargaModel.ativo == True,
            CargaModel.deletado == False,
            CargaModel.nf_emitida == True,
            CargaModel.ticket_emitido == False,
        ).order_by(CargaModel.id.desc())

        return query.all()

    def listar_cargas_com_origem_nao_identificada():
        """
        Lista cargas com ticket emitido mas sem origem identificada (sem fornecedor nem floresta).
        
        Returns:
            list: Lista de cargas sem origem identificada
        """
        cargas = CargaModel.query.filter(
            CargaModel.floresta_id == None,
            CargaModel.fornecedor_id == None,
            CargaModel.ticket_emitido == True,
            CargaModel.ativo == True,
            CargaModel.cancelada == False,
            CargaModel.deletado == False,
        ).all()

        return cargas