from ...base_model import BaseModel, db
from sistema.models_views.parametros.rotas_frete.rota_model import RotaFreteModel
from sqlalchemy import and_


class TransportadoraModel(BaseModel):
    """
    Model para registro de transportadoras
    """
    __tablename__ = 'transp_transportadora'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    tipo_cadastro = db.Column(db.Boolean, nullable=False)
    identificacao = db.Column(db.String(255), nullable=False)
    numero_documento = db.Column(db.String(20), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)

    instituicao_financeira_id = db.Column(db.Integer, db.ForeignKey('z_sys_instituicoes_financeiras.id'), nullable=True)
    instituicao_financeira = db.relationship('InstituicoesFinanceirasModel', backref='instituicao_financeira_transportadora', lazy=True)

    agencia_bancaria = db.Column(db.String(50), nullable=True)
    conta_bancaria = db.Column(db.String(50), nullable=True)
    chave_pix = db.Column(db.String(155), nullable=True)


    ativo = db.Column(db.Boolean, default=True, nullable=False)
        
    def __init__(
            self, tipo_cadastro, identificacao, numero_documento, telefone, instituicao_financeira_id=None, agencia_bancaria=None, conta_bancaria=None, chave_pix=None, ativo=True
    ):
        self.tipo_cadastro = tipo_cadastro
        self.identificacao = identificacao
        self.numero_documento = numero_documento
        self.telefone = telefone
        self.instituicao_financeira_id = instituicao_financeira_id
        self.agencia_bancaria = agencia_bancaria
        self.conta_bancaria = conta_bancaria
        self.chave_pix = chave_pix
        self.ativo = ativo
        
    
    def listar_transportadoras():
        """
        Lista todas as transportadoras não deletadas, ordenadas por ID decrescente.
        
        Returns:
            list: Lista de objetos TransportadoraModel não deletados
        """
        transportadoras = TransportadoraModel.query.filter(
            TransportadoraModel.deletado == 0,
        ).order_by(TransportadoraModel.identificacao.asc()).all()

        return transportadoras


    def listar_transportadoras_ativas():
        """
        Lista todas as transportadoras ativas e não deletadas, ordenadas por ID decrescente.
        
        Returns:
            list: Lista de objetos TransportadoraModel ativos e não deletados
        """
        transportadoras = TransportadoraModel.query.filter(
            TransportadoraModel.deletado == 0,
            TransportadoraModel.ativo == 1
        ).order_by(TransportadoraModel.id.desc()).all()

        return transportadoras


    def listar_transportadoras_inativas():
        """
        Lista todas as transportadoras inativas (independente se deletadas ou não).
        
        Returns:
            list: Lista de objetos TransportadoraModel inativos
        """
        transportadoras = TransportadoraModel.query.filter(
            TransportadoraModel.ativo == False
        ).all()

        return transportadoras


    def obter_transportadora_por_id(id):
        """
        Obtém uma transportadora específica por ID, apenas se não estiver deletada.
        
        Args:
            id (int): ID da transportadora
        
        Returns:
            TransportadoraModel: Objeto da transportadora encontrada ou None se não encontrar
        """
        transportadora = TransportadoraModel.query.filter(
            TransportadoraModel.id == id,
            TransportadoraModel.deletado == 0
        ).first()

        return transportadora


    def filtrar_transportadoras(
        identificacao=None,
        numero_documento=None,
        telefone=None
    ):
        """
        Filtra transportadoras ativas por identificação, número de documento ou telefone.
        
        Args:
            identificacao (str, optional): Nome/identificação da transportadora
            numero_documento (str, optional): Número do documento da transportadora
            telefone (str, optional): Telefone da transportadora
        
        Returns:
            list: Lista de objetos TransportadoraModel que atendem aos critérios de filtro
        """
        query = TransportadoraModel.query.filter(
            TransportadoraModel.deletado == False,
            TransportadoraModel.ativo == True
        )

        if identificacao:
            query = query.filter(
                TransportadoraModel.identificacao.ilike(f"%{identificacao}%")
            )

        if numero_documento:
            query = query.filter(
                TransportadoraModel.numero_documento.ilike(f"%{numero_documento}%")
            )

        if telefone:
            query = query.filter(
                TransportadoraModel.telefone.ilike(f"%{telefone}%")
            )

        return query.order_by(TransportadoraModel.id.desc()).all()

    def obter_preco_frete(cliente_id, transportadora_id, fornecedor_identificacao, produto, bitola_solicitacao):
        """
        Obtém o preço de frete baseado na rota, produto e bitola usando a tabela normalizada.
        Primeiro tenta encontrar rota específica para a transportadora.
        Se não encontrar, busca a rota "Todos" (transportadora_id = None).
        
        Args:
            cliente_id (int): ID do cliente de destino
            transportadora_id (int): ID da transportadora
            fornecedor_identificacao (str): ID do fornecedor
            produto (str): Tipo do produto ("Eucalipto", "Pinus", "Biomassa")
            bitola_solicitacao (int): ID da bitola solicitada
        
        Returns:
            dict: Dicionário contendo:
                - preco_frete: Preço do frete para a bitola/produto
                - frete_incompleto: Flag indicando se os dados de frete estão incompletos
                - rota_frete: Objeto da rota de frete encontrada
        """
        from sistema.models_views.parametros.rotas_frete.rota_frete_preco_bitola_model import RotaFretePrecoBitolaModel
        from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
        
        rota_frete = RotaFreteModel.query.filter_by(
            cliente_id=cliente_id,
            transportadora_id=transportadora_id,
            fornecedor_id=fornecedor_identificacao,
            ativo=True
        ).filter(RotaFreteModel.deletado == False).first()
        
        if not rota_frete:
            rota_frete = RotaFreteModel.query.filter_by(
                cliente_id=cliente_id,
                transportadora_id=None,
                fornecedor_id=fornecedor_identificacao,
                ativo=True
            ).filter(RotaFreteModel.deletado == False).first()
        
        if not rota_frete:
            return {
                'preco_frete': 0,
                'frete_incompleto': True,
                'rota_frete': None
            }
        
        produto_obj = ProdutoModel.query.filter_by(nome=produto, deletado=False).first()
        if not produto_obj:
            return {
                'preco_frete': 0,
                'frete_incompleto': True,
                'rota_frete': rota_frete
            }
        
        preco_frete_obj = RotaFretePrecoBitolaModel.query.filter_by(
            rota_frete_id=rota_frete.id,
            produto_id=produto_obj.id,
            bitola_id=bitola_solicitacao,
            ativo=True,
            deletado=False
        ).first()
        
        if preco_frete_obj and preco_frete_obj.preco_frete_100:
            preco_frete = preco_frete_obj.preco_frete_100
            frete_incompleto = False
        else:
            preco_frete = 0
            frete_incompleto = True
        
        return {
            'preco_frete': preco_frete,
            'frete_incompleto': frete_incompleto,
            'rota_frete': rota_frete
        }