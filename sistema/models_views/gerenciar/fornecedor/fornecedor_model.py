from ...base_model import BaseModel, db
from sqlalchemy import and_


class FornecedorModel(BaseModel):
    """
    Model para registro de fornecedores
    """
    __tablename__ = 'for_fornecedor'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    fatura_via_cpf = db.Column(db.Boolean, nullable=False, default=False)
    identificacao = db.Column(db.String(200), nullable=False)
    numero_documento = db.Column(db.String(20), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    estimativa_tonelada = db.Column(db.Float, nullable=True)

    funrural = db.Column(db.Boolean, default=True, nullable=False)

    senar = db.Column(db.Boolean, default=False, nullable=False)

    madeira_posta = db.Column(db.Boolean, default=False, nullable=False)

    possui_comissionado = db.Column(db.Boolean, default=False, nullable=False)

    custo_extracao = db.Column(db.Boolean, default=False, nullable=False)

    extrator_id = db.Column(db.Integer, db.ForeignKey("ext_extrator.id"), nullable=True)
    extrator = db.relationship("ExtratorModel", backref=db.backref("extrator_fornecedor", lazy=True))

    euca_custo_extracao_bitola_1_100 = db.Column(db.Integer, nullable=True)
    euca_custo_extracao_bitola_2_100 = db.Column(db.Integer, nullable=True)
    euca_custo_extracao_bitola_3_100 = db.Column(db.Integer, nullable=True)
    euca_custo_extracao_bitola_4_100 = db.Column(db.Integer, nullable=True)

    pinus_custo_extracao_bitola_1_100 = db.Column(db.Integer, nullable=True)
    pinus_custo_extracao_bitola_2_100 = db.Column(db.Integer, nullable=True)
    pinus_custo_extracao_bitola_3_100 = db.Column(db.Integer, nullable=True)
    pinus_custo_extracao_bitola_4_100 = db.Column(db.Integer, nullable=True)
    pinus_custo_extracao_bitola_5_100 = db.Column(db.Integer, nullable=True)

    bio_custo_extracao_bitola_5_100 = db.Column(db.Integer, nullable=True)
    bio_custo_extracao_bitola_7_100 = db.Column(db.Integer, nullable=True)


    euca_bitola_1_id = db.Column(db.Integer, nullable=True)
    euca_preco_custo_bitola_1_100 = db.Column(db.Integer, nullable=True)
    euca_bitola_2_id = db.Column(db.Integer, nullable=True)
    euca_preco_custo_bitola_2_100 = db.Column(db.Integer, nullable=True)
    euca_bitola_3_id = db.Column(db.Integer, nullable=True)
    euca_preco_custo_bitola_3_100 = db.Column(db.Integer, nullable=True)
    euca_bitola_4_id = db.Column(db.Integer, nullable=True)
    euca_preco_custo_bitola_4_100 = db.Column(db.Integer, nullable=True)

    pinus_bitola_1_id = db.Column(db.Integer, nullable=True)
    pinus_preco_custo_bitola_1_100 = db.Column(db.Integer, nullable=True)
    pinus_bitola_2_id = db.Column(db.Integer, nullable=True)
    pinus_preco_custo_bitola_2_100 = db.Column(db.Integer, nullable=True)
    pinus_bitola_3_id = db.Column(db.Integer, nullable=True)
    pinus_preco_custo_bitola_3_100 = db.Column(db.Integer, nullable=True)
    pinus_bitola_4_id = db.Column(db.Integer, nullable=True)
    pinus_preco_custo_bitola_4_100 = db.Column(db.Integer, nullable=True)
    pinus_bitola_5_id = db.Column(db.Integer, nullable=True)
    pinus_preco_custo_bitola_5_100 = db.Column(db.Integer, nullable=True)

    bio_bitola_5_id = db.Column(db.Integer, nullable=True)
    bio_preco_custo_bitola_5_100 = db.Column(db.Integer, nullable=True)
    bio_bitola_7_id = db.Column(db.Integer, nullable=True)
    bio_preco_custo_bitola_7_100 = db.Column(db.Integer, nullable=True)

    contrato_fornecedor_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    contrato_fornecedor = db.relationship("UploadArquivoModel", foreign_keys=[contrato_fornecedor_id], backref=db.backref("contrato_fornecedor", lazy=True))

    imposto_id = db.Column(db.Integer, db.ForeignKey("z_sys_imposto.id"), nullable=True)
    imposto = db.relationship("ImpostoModel", backref=db.backref("imposto_fun_senar", lazy=True))

    arquivo_senar_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    arquivo_senar = db.relationship("UploadArquivoModel", foreign_keys=[arquivo_senar_id], backref=db.backref("arquivo_senar", lazy=True))

    credito_100 = db.Column(db.Integer, nullable=True)    

    instituicao_financeira_id = db.Column(db.Integer, db.ForeignKey('z_sys_instituicoes_financeiras.id'), nullable=True)
    instituicao_financeira = db.relationship('InstituicoesFinanceirasModel', backref='instituicao_financeira_fornecedor', lazy=True)

    agencia_bancaria = db.Column(db.String(50), nullable=True)
    conta_bancaria = db.Column(db.String(50), nullable=True)
    chave_pix = db.Column(db.String(155), nullable=True)
 
    classe_fornecedor = db.Column(db.Boolean, nullable=False, default=False)
    valor_contrato_100 = db.Column(db.Integer, nullable=True)
    
    controle_entrada = db.Column(db.Boolean, default=True)
    
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    madeiras_posta = db.relationship("FornecedorMadeiraPostaModel", back_populates="fornecedor", cascade="all, delete-orphan")
    

    def __init__(
            self, fatura_via_cpf, identificacao, numero_documento, senar,
            telefone, classe_fornecedor, controle_entrada=True, valor_contrato_100=None, credito_100=None, ativo=True, funrural=True, contrato_fornecedor_id=None,
            extrator_id=None, euca_bitola_1_id=None, euca_preco_custo_bitola_1_100=None,
            euca_bitola_2_id=None, euca_preco_custo_bitola_2_100=None,
            euca_bitola_3_id=None, euca_preco_custo_bitola_3_100=None,
            euca_bitola_4_id=None, euca_preco_custo_bitola_4_100=None,
            pinus_bitola_1_id=None, pinus_preco_custo_bitola_1_100=None,
            pinus_bitola_2_id=None, pinus_preco_custo_bitola_2_100=None,
            pinus_bitola_3_id=None, pinus_preco_custo_bitola_3_100=None,
            pinus_bitola_4_id=None, pinus_preco_custo_bitola_4_100=None,
            pinus_bitola_5_id=None, pinus_preco_custo_bitola_5_100=None,
            custo_extracao=None,
            pinus_custo_extracao_bitola_1_100=None, 
            pinus_custo_extracao_bitola_2_100=None, 
            pinus_custo_extracao_bitola_3_100=None, 
            pinus_custo_extracao_bitola_4_100=None, 
            pinus_custo_extracao_bitola_5_100=None,
            euca_custo_extracao_bitola_1_100=None,
            euca_custo_extracao_bitola_2_100=None,
            euca_custo_extracao_bitola_3_100=None,
            euca_custo_extracao_bitola_4_100=None,
            bio_custo_extracao_bitola_5_100=None,
            bio_custo_extracao_bitola_7_100=None,
            bio_bitola_5_id=None,
            bio_bitola_7_id=None,
            bio_preco_custo_bitola_5_100=None, 
            bio_preco_custo_bitola_7_100=None,
            arquivo_senar_id=None,
            imposto_id=None,
            madeira_posta=None,
            instituicao_financeira_id=None,
            agencia_bancaria=None,
            conta_bancaria=None,
            chave_pix=None,
            possui_comissionado=None,
            estimativa_tonelada=None
    ):
        self.funrural = funrural
        self.senar = senar
        self.arquivo_senar_id = arquivo_senar_id
        self.imposto_id = imposto_id

        self.fatura_via_cpf = fatura_via_cpf
        self.identificacao = identificacao
        self.numero_documento = numero_documento
        self.telefone = telefone
        self.controle_entrada = controle_entrada
        self.classe_fornecedor = classe_fornecedor
        self.valor_contrato_100 = valor_contrato_100
        
        self.euca_bitola_1_id = euca_bitola_1_id
        self.euca_preco_custo_bitola_1_100 = euca_preco_custo_bitola_1_100
        self.euca_bitola_2_id = euca_bitola_2_id
        self.euca_preco_custo_bitola_2_100 = euca_preco_custo_bitola_2_100
        self.euca_bitola_3_id = euca_bitola_3_id
        self.euca_preco_custo_bitola_3_100 = euca_preco_custo_bitola_3_100
        self.euca_bitola_4_id = euca_bitola_4_id
        self.euca_preco_custo_bitola_4_100 = euca_preco_custo_bitola_4_100

        self.pinus_bitola_1_id = pinus_bitola_1_id
        self.pinus_preco_custo_bitola_1_100 = pinus_preco_custo_bitola_1_100
        self.pinus_bitola_2_id = pinus_bitola_2_id
        self.pinus_preco_custo_bitola_2_100 = pinus_preco_custo_bitola_2_100
        self.pinus_bitola_3_id = pinus_bitola_3_id
        self.pinus_preco_custo_bitola_3_100 = pinus_preco_custo_bitola_3_100
        self.pinus_bitola_4_id = pinus_bitola_4_id
        self.pinus_preco_custo_bitola_4_100 = pinus_preco_custo_bitola_4_100
        self.pinus_bitola_5_id = pinus_bitola_5_id
        self.pinus_preco_custo_bitola_5_100 = pinus_preco_custo_bitola_5_100
        
        self.custo_extracao = custo_extracao
        self.euca_custo_extracao_bitola_1_100 = euca_custo_extracao_bitola_1_100
        self.euca_custo_extracao_bitola_2_100 = euca_custo_extracao_bitola_2_100
        self.euca_custo_extracao_bitola_3_100 = euca_custo_extracao_bitola_3_100
        self.euca_custo_extracao_bitola_4_100 = euca_custo_extracao_bitola_4_100
        self.pinus_custo_extracao_bitola_1_100 = pinus_custo_extracao_bitola_1_100
        self.pinus_custo_extracao_bitola_2_100 = pinus_custo_extracao_bitola_2_100
        self.pinus_custo_extracao_bitola_3_100 = pinus_custo_extracao_bitola_3_100
        self.pinus_custo_extracao_bitola_4_100 = pinus_custo_extracao_bitola_4_100
        self.pinus_custo_extracao_bitola_5_100 = pinus_custo_extracao_bitola_5_100

        self.bio_custo_extracao_bitola_5_100 = bio_custo_extracao_bitola_5_100
        self.bio_bitola_5_id = bio_bitola_5_id
        self.bio_bitola_7_id = bio_bitola_7_id
        self.bio_custo_extracao_bitola_7_100 = bio_custo_extracao_bitola_7_100
        self.bio_preco_custo_bitola_7_100 = bio_preco_custo_bitola_7_100
        self.bio_preco_custo_bitola_5_100 = bio_preco_custo_bitola_5_100

        self.madeira_posta = madeira_posta
        self.possui_comissionado = possui_comissionado
        self.contrato_fornecedor_id = contrato_fornecedor_id
        self.extrator_id = extrator_id
        self.credito_100 = credito_100

        self.instituicao_financeira_id = instituicao_financeira_id
        self.agencia_bancaria = agencia_bancaria
        self.conta_bancaria = conta_bancaria
        self.chave_pix = chave_pix
        self.ativo = ativo

        self.estimativa_tonelada = estimativa_tonelada

    def listar_fornecedores():
        """
        Lista todos os fornecedores ativos e não deletados, ordenados por ID decrescente.
        
        Returns:
            list: Lista de objetos FornecedorModel ativos e não deletados
        """
        fornecedores = FornecedorModel.query.filter(
            FornecedorModel.deletado == 0,
            FornecedorModel.ativo == True
        ).order_by(FornecedorModel.id.desc()).all()

        return fornecedores


    def listar_fornecedores_ativos():
        """
        Lista todos os fornecedores ativos e não deletados, ordenados por ID decrescente.
        
        Returns:
            list: Lista de objetos FornecedorModel ativos e não deletados
        """
        fornecedores = FornecedorModel.query.filter(
            FornecedorModel.deletado == 0,
            FornecedorModel.ativo == 1
        ).order_by(FornecedorModel.id.desc()).all()

        return fornecedores


    def listar_fornecedores_inativos():
        """
        Lista todos os fornecedores inativos e não deletados.
        
        Returns:
            list: Lista de objetos FornecedorModel inativos e não deletados
        """
        fornecedores = FornecedorModel.query.filter(
            FornecedorModel.deletado == 0,
            FornecedorModel.ativo == 0
        ).all()

        return fornecedores


    def obter_fornecedor_por_id(id):
        """
        Obtém um fornecedor específico por ID, apenas se não estiver deletado.
        
        Args:
            id (int): ID do fornecedor
        
        Returns:
            FornecedorModel: Objeto do fornecedor encontrado ou None se não encontrar
        """
        fornecedor = FornecedorModel.query.filter(
            FornecedorModel.id == id,
            FornecedorModel.deletado == 0
        ).first()

        return fornecedor


    def filtrar_fornecedores(
        identificacao=None,
        numero_documento=None,
        celular=None
    ):
        """
        Filtra fornecedores ativos por identificação, número de documento ou celular.
        
        Args:
            identificacao (str, optional): Nome/identificação do fornecedor
            numero_documento (str, optional): Número do documento do fornecedor
            celular (str, optional): Número de celular/telefone do fornecedor
        
        Returns:
            list: Lista de objetos FornecedorModel que atendem aos critérios de filtro
        """
        query = FornecedorModel.query.filter(
            FornecedorModel.deletado == False,
            FornecedorModel.ativo == True
        )

        if identificacao:
            query = query.filter(
                FornecedorModel.identificacao.ilike(f"%{identificacao}%")
            )

        if numero_documento:
            query = query.filter(
                FornecedorModel.numero_documento.ilike(f"%{numero_documento}%")
            )

        if celular:
            query = query.filter(
                FornecedorModel.telefone.ilike(f"%{celular}%")
            )

        return query.order_by(FornecedorModel.id.desc()).all()