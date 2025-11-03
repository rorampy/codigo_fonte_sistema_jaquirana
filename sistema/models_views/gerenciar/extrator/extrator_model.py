from ...base_model import BaseModel, db
from sqlalchemy import and_


class ExtratorModel(BaseModel):
    """
    Model para registro de extratores
    """
    __tablename__ = 'ext_extrator'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    # 1 - PF | 0 - PJ
    tipo_cadastro = db.Column(db.Boolean, nullable=False)
    identificacao = db.Column(db.String(255), nullable=False)
    numero_documento = db.Column(db.String(20), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)

    instituicao_financeira_id = db.Column(db.Integer, db.ForeignKey('z_sys_instituicoes_financeiras.id'), nullable=True)
    instituicao_financeira = db.relationship('InstituicoesFinanceirasModel', backref='instituicao_financeira_extrator', lazy=True)

    agencia_bancaria = db.Column(db.String(50), nullable=True)
    conta_bancaria = db.Column(db.String(50), nullable=True)
    chave_pix = db.Column(db.String(155), nullable=True)

    ativo = db.Column(db.Boolean, default=True, nullable=False)
        
    def __init__(
            self, tipo_cadastro, identificacao, numero_documento, telefone, instituicao_financeira_id=None, agencia_bancaria=None, conta_bancaria=None, chave_pix=None,
             ativo=True
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
        
    
    def listar_extratores():
        """
        Lista todos os extratores não deletados, ordenados por ID decrescente.
        
        Returns:
            list: Lista de objetos ExtratorModel não deletados
        """
        extratores = ExtratorModel.query.filter(
            ExtratorModel.deletado == 0,
        ).order_by(ExtratorModel.id.desc()).all()

        return extratores


    def listar_extratores_ativos():
        """
        Lista todos os extratores ativos e não deletados, ordenados por ID decrescente.
        
        Returns:
            list: Lista de objetos ExtratorModel ativos e não deletados
        """
        extratores = ExtratorModel.query.filter(
            ExtratorModel.deletado == 0,
            ExtratorModel.ativo == 1
        ).order_by(ExtratorModel.id.desc()).all()

        return extratores


    def listar_extratores_inativos():
        """
        Lista todos os extratores inativos (independente se deletados ou não).
        
        Returns:
            list: Lista de objetos ExtratorModel inativos
        """
        extratores = ExtratorModel.query.filter(
            ExtratorModel.ativo == False
        ).all()

        return extratores


    def obter_extrator_por_id(id):
        """
        Obtém um extrator específico por ID, apenas se não estiver deletado.
        
        Args:
            id (int): ID do extrator
        
        Returns:
            ExtratorModel: Objeto do extrator encontrado ou None se não encontrar
        """
        extrator = ExtratorModel.query.filter(
            ExtratorModel.id == id,
            ExtratorModel.deletado == 0
        ).first()

        return extrator


    def filtrar_extratores(
        identificacao=None,
        numero_documento=None,
        telefone=None
    ):
        """
        Filtra extratores ativos por identificação, número de documento ou telefone.
        
        Args:
            identificacao (str, optional): Nome/identificação do extrator
            numero_documento (str, optional): Número do documento do extrator
            telefone (str, optional): Telefone do extrator
        
        Returns:
            list: Lista de objetos ExtratorModel que atendem aos critérios de filtro
        """
        query = ExtratorModel.query.filter(
            ExtratorModel.deletado == False,
            ExtratorModel.ativo == True
        )

        if identificacao:
            query = query.filter(
                ExtratorModel.identificacao.ilike(f"%{identificacao}%")
            )

        if numero_documento:
            query = query.filter(
                ExtratorModel.numero_documento.ilike(f"%{numero_documento}%")
            )

        if telefone:
            query = query.filter(
                ExtratorModel.telefone.ilike(f"%{telefone}%")
            )

        return query.order_by(ExtratorModel.id.desc()).all()