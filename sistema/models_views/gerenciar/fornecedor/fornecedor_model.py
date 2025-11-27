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
    estimativa_tonelada = db.Column(db.Float, nullable=True) # Estimativa de Tonelada

    # Cadastro funrural 1- Sim | 2- Não
    funrural = db.Column(db.Boolean, default=True, nullable=False)

    # Cadastro senar 1- Sim | 2- Não
    senar = db.Column(db.Boolean, default=False, nullable=False)

    # Possui madeira posta? 1- Sim | 2- Não
    madeira_posta = db.Column(db.Boolean, default=False, nullable=False)

    # Possui comissionado? 1- Sim | 2- Não
    possui_comissionado = db.Column(db.Boolean, default=False, nullable=False)

    # possui custo de extração? 1- Sim | 2- Não
    custo_extracao = db.Column(db.Boolean, default=False, nullable=False)

    extrator_id = db.Column(db.Integer, db.ForeignKey("ext_extrator.id"), nullable=True)
    extrator = db.relationship("ExtratorModel", backref=db.backref("extrator_fornecedor", lazy=True))

    # preços de custo de extração para Eucalipto (opcionais)
    euca_custo_extracao_bitola_1_100 = db.Column(db.Integer, nullable=True)
    euca_custo_extracao_bitola_2_100 = db.Column(db.Integer, nullable=True)
    euca_custo_extracao_bitola_3_100 = db.Column(db.Integer, nullable=True)
    euca_custo_extracao_bitola_4_100 = db.Column(db.Integer, nullable=True)

    # preços de custo de extração para Pinus (opcionais)
    pinus_custo_extracao_bitola_1_100 = db.Column(db.Integer, nullable=True)
    pinus_custo_extracao_bitola_2_100 = db.Column(db.Integer, nullable=True)
    pinus_custo_extracao_bitola_3_100 = db.Column(db.Integer, nullable=True)
    pinus_custo_extracao_bitola_4_100 = db.Column(db.Integer, nullable=True)
    pinus_custo_extracao_bitola_5_100 = db.Column(db.Integer, nullable=True)

    # preços de custo de extração para Biomassa (opcionais)
    bio_custo_extracao_bitola_5_100 = db.Column(db.Integer, nullable=True)
    bio_custo_extracao_bitola_7_100 = db.Column(db.Integer, nullable=True)

    # ===============================================================================|

    # Bitolas e preços de custo para Eucalipto (opcionais)
    euca_bitola_1_id = db.Column(db.Integer, nullable=True)
    euca_preco_custo_bitola_1_100 = db.Column(db.Integer, nullable=True)
    euca_bitola_2_id = db.Column(db.Integer, nullable=True)
    euca_preco_custo_bitola_2_100 = db.Column(db.Integer, nullable=True)
    euca_bitola_3_id = db.Column(db.Integer, nullable=True)
    euca_preco_custo_bitola_3_100 = db.Column(db.Integer, nullable=True)
    euca_bitola_4_id = db.Column(db.Integer, nullable=True)
    euca_preco_custo_bitola_4_100 = db.Column(db.Integer, nullable=True)

    # Bitolas e preços de custo para Pinus (opcionais)
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

    # Bitola e preço de custo para Biomassa (opcionais)
    bio_bitola_5_id = db.Column(db.Integer, nullable=True)
    bio_preco_custo_bitola_5_100 = db.Column(db.Integer, nullable=True)
    bio_bitola_7_id = db.Column(db.Integer, nullable=True) # Madeira Biomassa
    bio_preco_custo_bitola_7_100 = db.Column(db.Integer, nullable=True) # Madeira Biomassa

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
 
    classe_fornecedor = db.Column(db.Boolean, nullable=False, default=False) # 1- Floresta | 0- Terceiro
    valor_contrato_100 = db.Column(db.Integer, nullable=True)
    
    controle_entrada = db.Column(db.Boolean, default=True)
    
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    # relacionamento 1:N -> cada fornecedor pode ter várias entradas de madeira posta
    madeiras_posta = db.relationship("FornecedorMadeiraPostaModel", back_populates="fornecedor", cascade="all, delete-orphan")
    
    # relacionamento 1:N -> cada fornecedor pode ter várias tags
    fornecedor_tags = db.relationship("FornecedorTag", backref="fornecedor_rel", lazy=True)

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
            estimativa_tonelada=None# Estimativa de Tonelada
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
        self.bio_bitola_7_id = bio_bitola_7_id # Madeira Biomassa
        self.bio_custo_extracao_bitola_7_100 = bio_custo_extracao_bitola_7_100
        self.bio_preco_custo_bitola_7_100 = bio_preco_custo_bitola_7_100 # Madeira Biomassa
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

        # Estimativa de Tonelada
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

    def obter_precos_custo_fornecedor(fornecedor_identificacao, produto, bitola_solicitacao, cliente_id=None, transportadora_id=None):
        """
        Obtém os preços de custo e extração para um fornecedor específico baseado no produto e bitola.
        Se o fornecedor possuir madeira posta E houver transportadora vinculada, utiliza os preços da tabela de madeira posta.
        Caso contrário, utiliza os preços normais do fornecedor.
        
        Args:
            fornecedor_identificacao (str): ID do fornecedor
            produto (str): Tipo do produto ("Eucalipto", "Pinus", "Biomassa")
            bitola_solicitacao (int): ID da bitola solicitada
            cliente_id (int, optional): ID do cliente (necessário para madeira posta)
            transportadora_id (int, optional): ID da transportadora (necessário para verificar madeira posta)
        
        Returns:
            dict: Dicionário contendo:
                - preco_custo: Preço de custo para a bitola/produto
                - preco_custo_extrator: Preço de custo de extração (se aplicável)
                - origem_incompleta: Flag indicando se os dados estão incompletos
                - fornecedor: Objeto do fornecedor encontrado
        """
        
        if fornecedor_identificacao == "0":
            return {
                'preco_custo': None,
                'preco_custo_extrator': None,
                'origem_incompleta': True,
                'fornecedor': None
            }
        
        # Obtém o fornecedor
        fornecedor = FornecedorModel.obter_fornecedor_por_id(fornecedor_identificacao)
        
        if not fornecedor:
            return {
                'preco_custo': None,
                'preco_custo_extrator': None,
                'origem_incompleta': True,
                'fornecedor': None
            }
        
        preco_custo = None
        preco_custo_extrator = None
        origem_incompleta = False

        # Se o fornecedor possui madeira posta, cliente_id e transportadora_id foram fornecidos
        # Verifica se há transportadora vinculada para usar preços de madeira posta
        if fornecedor.madeira_posta and cliente_id:
            # Importa aqui para evitar dependência circular
            from sistema.models_views.gerenciar.fornecedor.fornecedor_madeira_posta_model import FornecedorMadeiraPostaModel
            
            # Monta a query base
            query_filters = [
                FornecedorMadeiraPostaModel.fornecedor_id == fornecedor.id,
                FornecedorMadeiraPostaModel.cliente_id == cliente_id,
                FornecedorMadeiraPostaModel.ativo == True,
                FornecedorMadeiraPostaModel.deletado == False
            ]
            
            # Adiciona filtro de transportadora apenas se for fornecida
            if transportadora_id:
                query_filters.append(FornecedorMadeiraPostaModel.transportadora_id == transportadora_id)
            
            madeira_posta = FornecedorMadeiraPostaModel.query.filter(*query_filters).first()
            
            if madeira_posta:
                # Mapeia as bitolas e preços de madeira posta para cada produto
                if produto == "Eucalipto":
                    bitolas_precos_mp = [
                        (madeira_posta.euca_bitola_1_id, madeira_posta.euca_bitola_1_preco_100),
                        (madeira_posta.euca_bitola_2_id, madeira_posta.euca_bitola_2_preco_100),
                        (madeira_posta.euca_bitola_3_id, madeira_posta.euca_bitola_3_preco_100),
                        (madeira_posta.euca_bitola_4_id, madeira_posta.euca_bitola_4_preco_100)
                    ]
                
                elif produto == "Pinus":
                    bitolas_precos_mp = [
                        (madeira_posta.pinus_bitola_1_id, madeira_posta.pinus_bitola_1_preco_100),
                        (madeira_posta.pinus_bitola_2_id, madeira_posta.pinus_bitola_2_preco_100),
                        (madeira_posta.pinus_bitola_3_id, madeira_posta.pinus_bitola_3_preco_100),
                        (madeira_posta.pinus_bitola_4_id, madeira_posta.pinus_bitola_4_preco_100),
                        (madeira_posta.pinus_bitola_5_id, madeira_posta.pinus_bitola_5_preco_100)
                    ]
                
                elif produto == "Biomassa":
                    bitolas_precos_mp = [
                        (madeira_posta.bio_bitola_5_id, madeira_posta.bio_bitola_5_preco_100),
                        (madeira_posta.bio_bitola_7_id, madeira_posta.bio_bitola_7_preco_100) # Madeira Biomassa
                    ]
                
                else:
                    origem_incompleta = True
                    bitolas_precos_mp = []
                
                # Procura pela bitola solicitada na madeira posta
                for bitola_id, preco_madeira_posta in bitolas_precos_mp:
                    if bitola_id == bitola_solicitacao:
                        preco_custo = preco_madeira_posta
                        # Para madeira posta, não há custo de extração separado
                        preco_custo_extrator = 0
                        break
                else:
                    # Bitola não encontrada para madeira posta
                    origem_incompleta = True
            else:
                # Registro de madeira posta não encontrado para este cliente + transportadora
                # Vai usar preços normais abaixo
                origem_incompleta = False
        
        # Se não é madeira posta, não há transportadora vinculada ou não encontrou dados de madeira posta
        # Usa lógica tradicional (preços normais do fornecedor)
        if preco_custo is None:
            # Mapeia as bitolas e preços para cada produto
            if produto == "Eucalipto":
                bitolas_precos = [
                    (fornecedor.euca_bitola_1_id, fornecedor.euca_preco_custo_bitola_1_100, fornecedor.euca_custo_extracao_bitola_1_100),
                    (fornecedor.euca_bitola_2_id, fornecedor.euca_preco_custo_bitola_2_100, fornecedor.euca_custo_extracao_bitola_2_100),
                    (fornecedor.euca_bitola_3_id, fornecedor.euca_preco_custo_bitola_3_100, fornecedor.euca_custo_extracao_bitola_3_100),
                    (fornecedor.euca_bitola_4_id, fornecedor.euca_preco_custo_bitola_4_100, fornecedor.euca_custo_extracao_bitola_4_100)
                ]
            
            elif produto == "Pinus":
                bitolas_precos = [
                    (fornecedor.pinus_bitola_1_id, fornecedor.pinus_preco_custo_bitola_1_100, fornecedor.pinus_custo_extracao_bitola_1_100),
                    (fornecedor.pinus_bitola_2_id, fornecedor.pinus_preco_custo_bitola_2_100, fornecedor.pinus_custo_extracao_bitola_2_100),
                    (fornecedor.pinus_bitola_3_id, fornecedor.pinus_preco_custo_bitola_3_100, fornecedor.pinus_custo_extracao_bitola_3_100),
                    (fornecedor.pinus_bitola_4_id, fornecedor.pinus_preco_custo_bitola_4_100, fornecedor.pinus_custo_extracao_bitola_4_100),
                    (fornecedor.pinus_bitola_5_id, fornecedor.pinus_preco_custo_bitola_5_100, fornecedor.pinus_custo_extracao_bitola_5_100)
                ]
            
            elif produto == "Biomassa":
                bitolas_precos = [
                    (fornecedor.bio_bitola_5_id, fornecedor.bio_preco_custo_bitola_5_100, fornecedor.bio_custo_extracao_bitola_5_100),
                    (fornecedor.bio_bitola_7_id, fornecedor.bio_preco_custo_bitola_7_100, fornecedor.bio_custo_extracao_bitola_7_100) # Madeira Biomassa
                ]
                
            
            else:
                origem_incompleta = True
                bitolas_precos = []
            
            # Procura pela bitola solicitada
            for bitola_id, preco_custo_bitola, custo_extracao_bitola in bitolas_precos:
                if bitola_id == bitola_solicitacao:
                    preco_custo = preco_custo_bitola
                    
                    # Se o fornecedor tem extrator, define o custo de extração
                    if fornecedor.extrator_id is not None:
                        preco_custo_extrator = custo_extracao_bitola
                    break
            else:
                # Bitola não encontrada para o produto
                origem_incompleta = True
        
        return {
            'preco_custo': preco_custo,
            'preco_custo_extrator': preco_custo_extrator,
            'origem_incompleta': origem_incompleta,
            'fornecedor': fornecedor
        }