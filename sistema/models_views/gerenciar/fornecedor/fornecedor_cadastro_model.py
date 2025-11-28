from ...base_model import BaseModel, db
from sqlalchemy import and_


class FornecedorCadastroModel(BaseModel):
    """
    Model para registro de fornecedores
    """
    __tablename__ = 'for_fornecedor_cadastro'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    
    # Cadastro funrural 1- Sim | 2- Não
    funrural = db.Column(db.Boolean, default=True, nullable=False)
    # Cadastro senar 1- Sim | 2- Não
    senar = db.Column(db.Boolean, default=False, nullable=False)
    arquivo_senar_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    arquivo_senar = db.relationship("UploadArquivoModel", foreign_keys=[arquivo_senar_id], backref=db.backref("arquivo_senar_fornecedor_cadastro", lazy=True))
    imposto_id = db.Column(db.Integer, db.ForeignKey("z_sys_imposto.id"), nullable=True)
    imposto = db.relationship("ImpostoModel", backref=db.backref("imposto_fornecedor_cadastro", lazy=True))
    
    classe_fornecedor = db.Column(db.Boolean, nullable=False, default=False) # 1- Floresta | 0- Terceiro
    valor_contrato_100 = db.Column(db.Integer, nullable=True)
    estimativa_tonelada = db.Column(db.Float, nullable=True) # Estimativa de Tonelada
    
    controle_entrada = db.Column(db.Boolean, default=True)
    
    fatura_via_cpf = db.Column(db.Boolean, nullable=False, default=False)
    identificacao = db.Column(db.String(200), nullable=False)
    numero_documento = db.Column(db.String(20), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    contrato_fornecedor_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    contrato_fornecedor = db.relationship("UploadArquivoModel", foreign_keys=[contrato_fornecedor_id], backref=db.backref("contrato_fornecedor_cadastro", lazy=True))

    # Possui madeira posta? 1- Sim | 2- Não
    madeira_posta = db.Column(db.Boolean, default=False, nullable=False)

    # Possui comissionado? 1- Sim | 2- Não
    possui_comissionado = db.Column(db.Boolean, default=False, nullable=False)

    # possui custo de extração? 1- Sim | 2- Não
    custo_extracao = db.Column(db.Boolean, default=False, nullable=False)
    
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    # ==================== Relações ====================
    
    # relacionamento 1:N -> cada fornecedor pode ter vários preços de madeira posta normalizados
    fornecedor_madeira_posta = db.relationship("FornecedorMadeiraPostaPrecoBitolaModel", backref="fornecedor_madeira_posta", cascade="all, delete-orphan", lazy=True)
    
    # relacionamento 1:N -> cada fornecedor pode ter várias tags
    fornecedor_tags = db.relationship("FornecedorTag", backref="fornecedor_rel", cascade="all, delete-orphan", lazy=True)
    
    # relacionamento 1:N -> cada fornecedor pode ter vários preços de custo por bitola
    fornecedor_precos_custo_bitolas = db.relationship("FornecedorPrecoCustoBitolaModel", backref="fornecedor", cascade="all, delete-orphan", lazy=True)
    
    # relacionamento 1:N -> cada fornecedor pode ter vários custos de extração por bitola
    fornecedor_custos_extracao = db.relationship("FornecedorPrecoCustoExtracaoModel", backref="fornecedor_extracao", cascade="all, delete-orphan", lazy=True)

    # relacionamento 1:1 -> cada fornecedor pode ter uma conta bancária vinculada
    fornecedor_conta_bancaria = db.relationship("FornecedorContaBancariaModel", backref="fornecedor_rel_conta_bancaria", cascade="all, delete-orphan", uselist=False)

    # relacionamento 1:1 -> cada fornecedor pode ter um crédito definido
    fornecedor_credito = db.relationship("FornecedorCreditoModel", backref="fornecedor_rel_credito", cascade="all, delete-orphan", uselist=False)

    
    def __init__(
            self, 
            fatura_via_cpf, 
            identificacao, 
            numero_documento, 
            telefone, 
            classe_fornecedor,
            senar=False,
            funrural=True,
            controle_entrada=True, 
            valor_contrato_100=None, 
            estimativa_tonelada=None,
            ativo=True,
            arquivo_senar_id=None,
            imposto_id=None,
            contrato_fornecedor_id=None,
            madeira_posta=False,
            possui_comissionado=False,
            custo_extracao=False
    ):
        self.fatura_via_cpf = fatura_via_cpf
        self.identificacao = identificacao
        self.numero_documento = numero_documento
        self.telefone = telefone
        self.classe_fornecedor = classe_fornecedor
        self.senar = senar
        self.funrural = funrural
        self.controle_entrada = controle_entrada
        self.valor_contrato_100 = valor_contrato_100
        self.estimativa_tonelada = estimativa_tonelada
        self.ativo = ativo
        self.arquivo_senar_id = arquivo_senar_id
        self.imposto_id = imposto_id
        self.contrato_fornecedor_id = contrato_fornecedor_id
        self.madeira_posta = madeira_posta
        self.possui_comissionado = possui_comissionado
        self.custo_extracao = custo_extracao

    def listar_fornecedores():
        """
        Lista todos os fornecedores ativos e não deletados, ordenados por ID decrescente.
        
        Returns:
            list: Lista de objetos FornecedorCadastroModel ativos e não deletados
        """
        fornecedores = FornecedorCadastroModel.query.filter(
            FornecedorCadastroModel.deletado == 0,
            FornecedorCadastroModel.ativo == True
        ).order_by(FornecedorCadastroModel.id.desc()).all()

        return fornecedores


    def listar_fornecedores_ativos():
        """
        Lista todos os fornecedores ativos e não deletados, ordenados por ID decrescente.
        
        Returns:
            list: Lista de objetos FornecedorCadastroModel ativos e não deletados
        """
        fornecedores = FornecedorCadastroModel.query.filter(
            FornecedorCadastroModel.deletado == 0,
            FornecedorCadastroModel.ativo == 1
        ).order_by(FornecedorCadastroModel.id.desc()).all()

        return fornecedores


    def listar_fornecedores_inativos():
        """
        Lista todos os fornecedores inativos e não deletados.
        
        Returns:
            list: Lista de objetos FornecedorCadastroModel inativos e não deletados
        """
        fornecedores = FornecedorCadastroModel.query.filter(
            FornecedorCadastroModel.deletado == 0,
            FornecedorCadastroModel.ativo == 0
        ).all()

        return fornecedores


    def obter_fornecedor_por_id(id):
        """
        Obtém um fornecedor específico por ID, apenas se não estiver deletado.
        
        Args:
            id (int): ID do fornecedor
        
        Returns:
            FornecedorCadastroModel: Objeto do fornecedor encontrado ou None se não encontrar
        """
        fornecedor = FornecedorCadastroModel.query.filter(
            FornecedorCadastroModel.id == id,
            FornecedorCadastroModel.deletado == 0
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
            list: Lista de objetos FornecedorCadastroModel que atendem aos critérios de filtro
        """
        query = FornecedorCadastroModel.query.filter(
            FornecedorCadastroModel.deletado == False,
            FornecedorCadastroModel.ativo == True
        )

        if identificacao:
            query = query.filter(
                FornecedorCadastroModel.identificacao.ilike(f"%{identificacao}%")
            )

        if numero_documento:
            query = query.filter(
                FornecedorCadastroModel.numero_documento.ilike(f"%{numero_documento}%")
            )

        if celular:
            query = query.filter(
                FornecedorCadastroModel.telefone.ilike(f"%{celular}%")
            )

        return query.order_by(FornecedorCadastroModel.id.desc()).all()
    
    
    @staticmethod
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
        
        # Obtém o fornecedor da nova tabela normalizada
        fornecedor = FornecedorCadastroModel.obter_fornecedor_por_id(fornecedor_identificacao)
        
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

        # Mapear produto string para produto_id
        produto_map = {
            "Eucalipto": 1,
            "Pinus": 2,
            "Biomassa": 3
        }
        
        produto_id = produto_map.get(produto)
        if not produto_id:
            return {
                'preco_custo': None,
                'preco_custo_extrator': None,
                'origem_incompleta': True,
                'fornecedor': fornecedor
            }

        # Se o fornecedor possui madeira posta, cliente_id foi fornecido e busca preços de madeira posta
        if fornecedor.madeira_posta and cliente_id:
            from sistema.models_views.gerenciar.fornecedor.fornecedor_madeira_posta_preco_bitola_model import FornecedorMadeiraPostaPrecoBitolaModel
            
            # Query para buscar preço de madeira posta
            query = FornecedorMadeiraPostaPrecoBitolaModel.query.filter(
                FornecedorMadeiraPostaPrecoBitolaModel.fornecedor_id == fornecedor.id,
                FornecedorMadeiraPostaPrecoBitolaModel.cliente_id == cliente_id,
                FornecedorMadeiraPostaPrecoBitolaModel.produto_id == produto_id,
                FornecedorMadeiraPostaPrecoBitolaModel.bitola_id == bitola_solicitacao,
                FornecedorMadeiraPostaPrecoBitolaModel.ativo == True,
                FornecedorMadeiraPostaPrecoBitolaModel.deletado == False
            )
            
            # Adiciona filtro de transportadora se fornecida
            if transportadora_id:
                query = query.filter(FornecedorMadeiraPostaPrecoBitolaModel.transportadora_id == transportadora_id)
            
            madeira_posta = query.first()
            
            if madeira_posta and madeira_posta.preco_madeira_posta_100:
                preco_custo = madeira_posta.preco_madeira_posta_100
                # Para madeira posta, não há custo de extração separado
                preco_custo_extrator = 0
            else:
                origem_incompleta = True
        
        # Se não é madeira posta ou não encontrou dados de madeira posta, usa preços normais
        if preco_custo is None:
            from sistema.models_views.gerenciar.fornecedor.fornecedor_preco_custo_bitola_model import FornecedorPrecoCustoBitolaModel
            from sistema.models_views.gerenciar.fornecedor.fornecedor_preco_custo_extracao_model import FornecedorPrecoCustoExtracaoModel
            
            # Busca preço de custo normal
            preco_custo_obj = FornecedorPrecoCustoBitolaModel.query.filter(
                FornecedorPrecoCustoBitolaModel.fornecedor_id == fornecedor.id,
                FornecedorPrecoCustoBitolaModel.produto_id == produto_id,
                FornecedorPrecoCustoBitolaModel.bitola_id == bitola_solicitacao,
                FornecedorPrecoCustoBitolaModel.ativo == True,
                FornecedorPrecoCustoBitolaModel.deletado == False
            ).first()
            
            if preco_custo_obj and preco_custo_obj.valor_preco_custo_100:
                preco_custo = preco_custo_obj.valor_preco_custo_100
            else:
                origem_incompleta = True
            
            # Busca custo de extração se o fornecedor tem extração
            if fornecedor.custo_extracao:
                custo_extracao_obj = FornecedorPrecoCustoExtracaoModel.query.filter(
                    FornecedorPrecoCustoExtracaoModel.fornecedor_id == fornecedor.id,
                    FornecedorPrecoCustoExtracaoModel.produto_id == produto_id,
                    FornecedorPrecoCustoExtracaoModel.bitola_id == bitola_solicitacao,
                    FornecedorPrecoCustoExtracaoModel.ativo == True,
                    FornecedorPrecoCustoExtracaoModel.deletado == False
                ).first()
                
                if custo_extracao_obj and custo_extracao_obj.custo_extracao_100:
                    preco_custo_extrator = custo_extracao_obj.custo_extracao_100
                else:
                    preco_custo_extrator = 0
            else:
                preco_custo_extrator = 0
        
        return {
            'preco_custo': preco_custo,
            'preco_custo_extrator': preco_custo_extrator,
            'origem_incompleta': origem_incompleta,
            'fornecedor': fornecedor
        }