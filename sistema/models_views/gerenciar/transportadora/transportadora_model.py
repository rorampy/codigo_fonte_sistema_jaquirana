from ...base_model import BaseModel, db
from sistema.models_views.parametros.rotas_frete.rota_model import RotaFreteModel
from sqlalchemy import and_


class TransportadoraModel(BaseModel):
    """
    Model para registro de transportadoras
    """
    __tablename__ = 'transp_transportadora'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    # 1 - PF | 0 - PJ
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
        Obtém o preço de frete baseado na rota, produto e bitola.
        
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
        
        # Busca rota existente
        rota_frete = RotaFreteModel.query.filter_by(
            cliente_id=cliente_id,
            transportadora_id=transportadora_id,
            fornecedor_id=fornecedor_identificacao,
        ).first()
        
        # Se não houver rota cadastrada
        if not rota_frete:
            return {
                'preco_frete': 0,
                'frete_incompleto': True,
                'rota_frete': None
            }
        
        preco_frete = 0
        frete_incompleto = False
        
        # Mapeia as bitolas e preços para cada produto
        if produto == "Eucalipto":
            bitolas_precos = [
                (rota_frete.euca_bitola_1_id, rota_frete.euca_preco_custo_frete_bitola_1_100),
                (rota_frete.euca_bitola_2_id, rota_frete.euca_preco_custo_frete_bitola_2_100),
                (rota_frete.euca_bitola_3_id, rota_frete.euca_preco_custo_frete_bitola_3_100),
                (rota_frete.euca_bitola_4_id, rota_frete.euca_preco_custo_frete_bitola_4_100)
            ]
        
        elif produto == "Pinus":
            bitolas_precos = [
                (rota_frete.pinus_bitola_1_id, rota_frete.pinus_preco_custo_frete_bitola_1_100),
                (rota_frete.pinus_bitola_2_id, rota_frete.pinus_preco_custo_frete_bitola_2_100),
                (rota_frete.pinus_bitola_3_id, rota_frete.pinus_preco_custo_frete_bitola_3_100),
                (rota_frete.pinus_bitola_4_id, rota_frete.pinus_preco_custo_frete_bitola_4_100),
                (rota_frete.pinus_bitola_5_id, rota_frete.pinus_preco_custo_frete_bitola_5_100)
            ]
        
        elif produto == "Biomassa":
            bitolas_precos = [
                (rota_frete.bio_bitola_5_id, rota_frete.bio_preco_custo_frete_bitola_5_100)
            ]
        
        else:
            # Produto não reconhecido
            frete_incompleto = True
            bitolas_precos = []
        
        # Procura pela bitola solicitada
        for bitola_id, preco_frete_bitola in bitolas_precos:
            if bitola_id == bitola_solicitacao:
                preco_frete = preco_frete_bitola
                break
        else:
            # Bitola não encontrada para o produto
            frete_incompleto = True
        
        return {
            'preco_frete': preco_frete,
            'frete_incompleto': frete_incompleto,
            'rota_frete': rota_frete
        }