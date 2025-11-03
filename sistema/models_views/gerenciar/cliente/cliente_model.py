from ...base_model import BaseModel, db
from sqlalchemy import and_


class ClienteModel(BaseModel):
    """
    Model para registro de clientes
    """
    __tablename__ = 'cli_cliente'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    fatura_via_cpf = db.Column(db.Boolean, nullable=False, default=False)
    identificacao = db.Column(db.String(200), nullable=False)
    numero_documento = db.Column(db.String(20), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)

    # Bitolas e preços para Eucalipto
    euca_bitola_1_id = db.Column(db.Integer, nullable=True)
    euca_preco_venda_bitola_1_100 = db.Column(db.Integer, nullable=True)
    euca_bitola_2_id = db.Column(db.Integer, nullable=True)
    euca_preco_venda_bitola_2_100 = db.Column(db.Integer, nullable=True)
    euca_bitola_3_id = db.Column(db.Integer, nullable=True)
    euca_preco_venda_bitola_3_100 = db.Column(db.Integer, nullable=True)
    euca_bitola_4_id = db.Column(db.Integer, nullable=True)
    euca_preco_venda_bitola_4_100 = db.Column(db.Integer, nullable=True)

    bio_bitola_5_id = db.Column(db.Integer, nullable=True)
    bio_preco_venda_bitola_5_100 = db.Column(db.Integer, nullable=True)

    # Bitolas e preços para Pinus
    pinus_bitola_1_id = db.Column(db.Integer, nullable=True)
    pinus_preco_venda_bitola_1_100 = db.Column(db.Integer, nullable=True)
    pinus_bitola_2_id = db.Column(db.Integer, nullable=True)
    pinus_preco_venda_bitola_2_100 = db.Column(db.Integer, nullable=True)
    pinus_bitola_3_id = db.Column(db.Integer, nullable=True)
    pinus_preco_venda_bitola_3_100 = db.Column(db.Integer, nullable=True)
    pinus_bitola_4_id = db.Column(db.Integer, nullable=True)
    pinus_preco_venda_bitola_4_100 = db.Column(db.Integer, nullable=True)
    pinus_bitola_5_id = db.Column(db.Integer, nullable=True)
    pinus_preco_venda_bitola_5_100 = db.Column(db.Integer, nullable=True)

    instituicao_financeira_id = db.Column(db.Integer, db.ForeignKey('z_sys_instituicoes_financeiras.id'), nullable=True)
    instituicao_financeira = db.relationship('InstituicoesFinanceirasModel', backref='instituicao_financeira_cliente', lazy=True)

    agencia_bancaria = db.Column(db.String(50), nullable=True)
    conta_bancaria = db.Column(db.String(50), nullable=True)
    chave_pix = db.Column(db.String(155), nullable=True)

    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(
        self, fatura_via_cpf, identificacao, numero_documento, telefone,
        euca_bitola_1_id=None, euca_preco_venda_bitola_1_100=None,
        euca_bitola_2_id=None, euca_preco_venda_bitola_2_100=None,
        euca_bitola_3_id=None, euca_preco_venda_bitola_3_100=None,
        euca_bitola_4_id=None, euca_preco_venda_bitola_4_100=None,
        pinus_bitola_1_id=None, pinus_preco_venda_bitola_1_100=None,
        pinus_bitola_2_id=None, pinus_preco_venda_bitola_2_100=None,
        pinus_bitola_3_id=None, pinus_preco_venda_bitola_3_100=None,
        pinus_bitola_4_id=None, pinus_preco_venda_bitola_4_100=None,
        pinus_bitola_5_id=None, pinus_preco_venda_bitola_5_100=None,
        bio_bitola_5_id=None, bio_preco_venda_bitola_5_100=None,
        instituicao_financeira_id=None, agencia_bancaria=None,
        conta_bancaria=None, chave_pix=None,
        ativo=True
    ):
        self.fatura_via_cpf = fatura_via_cpf
        self.identificacao = identificacao
        self.numero_documento = numero_documento
        self.telefone = telefone
        self.euca_bitola_1_id = euca_bitola_1_id
        self.euca_preco_venda_bitola_1_100 = euca_preco_venda_bitola_1_100
        self.euca_bitola_2_id = euca_bitola_2_id
        self.euca_preco_venda_bitola_2_100 = euca_preco_venda_bitola_2_100
        self.euca_bitola_3_id = euca_bitola_3_id
        self.euca_preco_venda_bitola_3_100 = euca_preco_venda_bitola_3_100
        self.euca_bitola_4_id = euca_bitola_4_id
        self.euca_preco_venda_bitola_4_100 = euca_preco_venda_bitola_4_100

        self.pinus_bitola_1_id = pinus_bitola_1_id
        self.pinus_preco_venda_bitola_1_100 = pinus_preco_venda_bitola_1_100
        self.pinus_bitola_2_id = pinus_bitola_2_id
        self.pinus_preco_venda_bitola_2_100 = pinus_preco_venda_bitola_2_100
        self.pinus_bitola_3_id = pinus_bitola_3_id
        self.pinus_preco_venda_bitola_3_100 = pinus_preco_venda_bitola_3_100
        self.pinus_bitola_4_id = pinus_bitola_4_id
        self.pinus_preco_venda_bitola_4_100 = pinus_preco_venda_bitola_4_100
        self.pinus_bitola_5_id = pinus_bitola_5_id
        self.pinus_preco_venda_bitola_5_100 = pinus_preco_venda_bitola_5_100

        self.bio_bitola_5_id = bio_bitola_5_id
        self.bio_preco_venda_bitola_5_100 = bio_preco_venda_bitola_5_100
        self.instituicao_financeira_id = instituicao_financeira_id
        self.agencia_bancaria = agencia_bancaria
        self.conta_bancaria = conta_bancaria
        self.chave_pix = chave_pix
        self.ativo = ativo

    def listar_clientes():
        """
        Lista todos os clientes não deletados, ordenados por ID decrescente.
        
        Returns:
            list: Lista de objetos ClienteModel não deletados
        """
        clientes = ClienteModel.query.filter(
            ClienteModel.deletado == 0
        ).order_by(ClienteModel.id.desc()).all()

        return clientes


    def listar_clientes_ativos():
        """
        Lista todos os clientes ativos e não deletados, ordenados por ID decrescente.
        
        Returns:
            list: Lista de objetos ClienteModel ativos e não deletados
        """
        clientes = ClienteModel.query.filter(
            ClienteModel.deletado == 0,
            ClienteModel.ativo == 1
        ).order_by(ClienteModel.id.desc()).all()

        return clientes


    def listar_clientes_inativos():
        """
        Lista todos os clientes inativos e não deletados.
        
        Returns:
            list: Lista de objetos ClienteModel inativos e não deletados
        """
        clientes = ClienteModel.query.filter(
            ClienteModel.deletado == 0,
            ClienteModel.ativo == 0
        ).all()

        return clientes


    def obter_cliente_por_id(id):
        """
        Obtém um cliente específico por ID, apenas se não estiver deletado.
        
        Args:
            id (int): ID do cliente
        
        Returns:
            ClienteModel: Objeto do cliente encontrado ou None se não encontrar
        """
        cliente = ClienteModel.query.filter(
            ClienteModel.id == id,
            ClienteModel.deletado == 0
        ).first()

        return cliente


    def filtrar_clientes(
        identificacao=None,
        celular=None
    ):
        """
        Filtra clientes ativos por identificação ou celular.
        
        Args:
            identificacao (str, optional): Nome/identificação do cliente
            celular (str, optional): Número de celular/telefone do cliente
        
        Returns:
            list: Lista de objetos ClienteModel que atendem aos critérios de filtro
        """
        query = ClienteModel.query.filter(
            ClienteModel.deletado == False,
            ClienteModel.ativo == True
        )

        if identificacao:
            query = query.filter(
                ClienteModel.identificacao.ilike(f"%{identificacao}%")
            )

        if celular:
            query = query.filter(
                ClienteModel.telefone.ilike(f"%{celular}%")
            )

        return query.order_by(ClienteModel.id.desc()).all()