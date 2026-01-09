from ...base_model import BaseModel, db

class PedidoVendaDadosNfModel(BaseModel):

    __tablename__ = "ped_pedido_venda_dados_nf"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    pedido_venda_id = db.Column(db.Integer, db.ForeignKey("ped_pedido_venda.id"), nullable=True)
    pedido_venda = db.relationship("PedidoVendaModel", backref=db.backref("pedido_venda_dados_nf", lazy=True))

    razao_social_emissor = db.Column(db.String(200), nullable=True)
    numero_nota_fiscal = db.Column(db.String(20), nullable=True)
    peso_ton_nf = db.Column(db.Float, nullable=True)
    serie_nota = db.Column(db.String(5), nullable=True)
    chave_acesso = db.Column(db.String(255), nullable=True)
    destinatario_nome = db.Column(db.String(200), nullable=True)
    destinatario_cnpj_cpf = db.Column(db.String(20), nullable=True)
    destinatario_insc_estadual = db.Column(db.String(50), nullable=True)
    destinatario_data_emissao = db.Column(db.Date, nullable=True)
    valor_total_nota_100 = db.Column(db.Integer, nullable=True)
    preco_un_nf = db.Column(db.Integer, nullable=True)

    # Dados do transportador (nota fiscal)
    transportador_nome = db.Column(db.String(200), nullable=True)
    transportador_cnpj_cpf = db.Column(db.String(20), nullable=True)
    transportador_insc_estadual = db.Column(db.String(50), nullable=True)

    # Dados transporte NF
    placa_nf = db.Column(db.String(50), nullable=True)
    motorista_nf = db.Column(db.String(200), nullable=True)

    # Arquivos PDF 
    arquivo_nota_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    arquivo_nota = db.relationship("UploadArquivoModel",foreign_keys=[arquivo_nota_id], backref=db.backref("pedido_venda_arquivo_nota", lazy=True))

    # Arquivos XML
    arquivo_nota_xml_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    arquivo_nota_xml = db.relationship("UploadArquivoModel",foreign_keys=[arquivo_nota_xml_id], backref=db.backref("pedido_venda_arquivo_nota_xml", lazy=True))
    
    # Arquivos de excesso
    possui_excesso_carga = db.Column(db.Boolean, default=False, nullable=False) 

    # Excesso PDF
    arquivo_nota_excesso_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    arquivo_nota_excesso = db.relationship("UploadArquivoModel",foreign_keys=[arquivo_nota_excesso_id], backref=db.backref("pedido_venda_arquivo_nota_excesso", lazy=True))
    
    # Excesso XML
    arquivo_nota_excesso_xml_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    arquivo_nota_excesso_xml = db.relationship("UploadArquivoModel",foreign_keys=[arquivo_nota_excesso_xml_id], backref=db.backref("pedido_venda_arquivo_nota_excesso_xml", lazy=True))
    
    status_emissao_nf_complementar_id = db.Column(db.Integer, db.ForeignKey("z_sys_status_emissao_nf_complementar.id"), nullable=True)
    status_emissao_nf_complementar = db.relationship("StatusEmissaoNfComplementarModel",foreign_keys=[status_emissao_nf_complementar_id],backref=db.backref("pedido_venda_nf_status_emissao_nf_complementar", lazy=True))

    peso_ton_nf_excesso = db.Column(db.Float, nullable=True)
    peso_nf_ton_com_excecao = db.Column(db.Float, nullable=True)
    numero_nota_fiscal_excessao = db.Column(db.String(20), nullable=True)

    estorno_nf = db.Column(db.Boolean, default=False, nullable=False) 
    
    arquivo_nota_estorno_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    arquivo_nota_estorno = db.relationship("UploadArquivoModel",foreign_keys=[arquivo_nota_estorno_id], backref=db.backref("pedido_venda_arquivo_nota_estorno", lazy=True))
    
    numero_nota_fiscal_estorno = db.Column(db.String(20), nullable=True)
    
    realizado_split = db.Column(db.Boolean, default=False, nullable=True) 

    carga_frf = db.Column(db.Boolean, default=False, nullable=False) 
    
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    def __init__(self, pedido_venda_id=None, razao_social_emissor=None, numero_nota_fiscal=None, peso_ton_nf=None, serie_nota=None, chave_acesso=None, destinatario_nome=None,
                 destinatario_cnpj_cpf=None, destinatario_insc_estadual=None, destinatario_data_emissao=None,
                 valor_total_nota_100=None, preco_un_nf=None, transportador_nome=None, transportador_cnpj_cpf=None,
                 transportador_insc_estadual=None, placa_nf=None, motorista_nf=None, arquivo_nota_id=None,
                 status_emissao_nf_complementar_id=None, arquivo_nota_xml_id=None, possui_excesso_carga=False, arquivo_nota_excesso_id=None, arquivo_nota_excesso_xml_id=None,
                 peso_ton_nf_excesso=None, peso_nf_ton_com_excecao=None, numero_nota_fiscal_excessao=None,
                 estorno_nf=False, arquivo_nota_estorno_id=None, numero_nota_fiscal_estorno=None, realizado_split=False, carga_frf=False, ativo=True):
        
        self.pedido_venda_id = pedido_venda_id
        self.razao_social_emissor = razao_social_emissor
        self.numero_nota_fiscal = numero_nota_fiscal
        self.peso_ton_nf = peso_ton_nf
        self.serie_nota = serie_nota
        self.chave_acesso = chave_acesso
        self.destinatario_nome = destinatario_nome
        self.destinatario_cnpj_cpf = destinatario_cnpj_cpf
        self.destinatario_insc_estadual = destinatario_insc_estadual
        self.destinatario_data_emissao = destinatario_data_emissao
        self.valor_total_nota_100 = valor_total_nota_100
        self.preco_un_nf = preco_un_nf
        self.transportador_nome = transportador_nome
        self.transportador_cnpj_cpf = transportador_cnpj_cpf
        self.transportador_insc_estadual = transportador_insc_estadual
        self.placa_nf = placa_nf
        self.motorista_nf = motorista_nf
        self.arquivo_nota_id = arquivo_nota_id
        self.status_emissao_nf_complementar_id = status_emissao_nf_complementar_id
        self.arquivo_nota_xml_id = arquivo_nota_xml_id
        self.possui_excesso_carga = possui_excesso_carga
        self.arquivo_nota_excesso_id = arquivo_nota_excesso_id
        self.arquivo_nota_excesso_xml_id = arquivo_nota_excesso_xml_id
        self.peso_ton_nf_excesso = peso_ton_nf_excesso
        self.peso_nf_ton_com_excecao = peso_nf_ton_com_excecao
        self.numero_nota_fiscal_excessao = numero_nota_fiscal_excessao
        self.estorno_nf = estorno_nf
        self.arquivo_nota_estorno_id = arquivo_nota_estorno_id
        self.numero_nota_fiscal_estorno = numero_nota_fiscal_estorno
        self.realizado_split = realizado_split
        self.carga_frf = carga_frf
        self.ativo = ativo
    
    @property
    def solicitacao_pedido_venda(self):
        """
        Acesso conveniente à solicitação através do pedido_venda.
        
        Returns:
            SolicitacaoPedidoVendaModel: Solicitação associada ou None
        """
        if self.pedido_venda:
            return self.pedido_venda.solicitacao
        return None
    
    @staticmethod
    def criar_dados_nf(**kwargs):
        """
        Cria um novo registro de dados de NF.
        
        Args:
            **kwargs: Parâmetros para criar o registro
            
        Returns:
            PedidoVendaDadosNfModel: Instância criada e salva
        """
        dados_nf = PedidoVendaDadosNfModel(**kwargs)
        db.session.add(dados_nf)
        db.session.flush()
        return dados_nf
    
    @staticmethod
    def obter_dados_nf_por_pedido_venda_id(pedido_venda_id):
        """
        Obtém os dados da NF por ID do pedido de venda.
        
        Args:
            pedido_venda_id (int): ID do pedido de venda
            
        Returns:
            PedidoVendaDadosNfModel: Dados encontrados ou None
        """
        return PedidoVendaDadosNfModel.query.filter_by(
            pedido_venda_id=pedido_venda_id,
            ativo=True,
            deletado=False
        ).first()
  