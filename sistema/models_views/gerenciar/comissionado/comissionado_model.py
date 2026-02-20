from ...base_model import BaseModel, db
from sqlalchemy import and_


class ComissionadoModel(BaseModel):
    """
    Model para registro de comissionados
    """
    __tablename__ = 'com_comissionado'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    tipo_cadastro = db.Column(db.Boolean, nullable=False)
    identificacao = db.Column(db.String(255), nullable=False)
    numero_documento = db.Column(db.String(20), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    instituicao_financeira_id = db.Column(db.Integer, db.ForeignKey('z_sys_instituicoes_financeiras.id'), nullable=True)
    instituicao_financeira = db.relationship('InstituicoesFinanceirasModel', backref='instituicao_financeira_comissionado', lazy=True)

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
        
    
    def listar_comissionados():
        """
        Lista todos os comissionados não deletados, ordenados por ID decrescente.
        
        Returns:
            list: Lista de objetos ComissionadoModel não deletados
        """
        comissionados = ComissionadoModel.query.filter(
            ComissionadoModel.deletado == 0,
        ).order_by(ComissionadoModel.id.desc()).all()

        return comissionados


    def listar_comissionados_ativos():
        """
        Lista todos os comissionados ativos e não deletados, ordenados por ID decrescente.
        
        Returns:
            list: Lista de objetos ComissionadoModel ativos e não deletados
        """
        comissionados = ComissionadoModel.query.filter(
            ComissionadoModel.deletado == 0,
            ComissionadoModel.ativo == 1
        ).order_by(ComissionadoModel.id.desc()).all()

        return comissionados


    def listar_comissionados_inativos():
        """
        Lista todos os comissionados inativos (independente se deletados ou não).
        
        Returns:
            list: Lista de objetos ComissionadoModel inativos
        """
        comissionados = ComissionadoModel.query.filter(
            ComissionadoModel.ativo == False
        ).all()

        return comissionados


    def obter_comissionado_por_id(id):
        """
        Obtém um comissionado específico por ID, apenas se não estiver deletado.
        
        Args:
            id (int): ID do comissionado
        
        Returns:
            ComissionadoModel: Objeto do comissionado encontrado ou None se não encontrar
        """
        comissionado = ComissionadoModel.query.filter(
            ComissionadoModel.id == id,
            ComissionadoModel.deletado == 0
        ).first()

        return comissionado


    def filtrar_comissionados(
        identificacao=None,
        numero_documento=None,
        telefone=None
    ):
        """
        Filtra comissionados ativos por identificação, número de documento ou telefone.
        
        Args:
            identificacao (str, optional): Nome/identificação do comissionado
            numero_documento (str, optional): Número do documento do comissionado
            telefone (str, optional): Telefone do comissionado
        
        Returns:
            list: Lista de objetos ComissionadoModel que atendem aos critérios de filtro
        """
        query = ComissionadoModel.query.filter(
            ComissionadoModel.deletado == False,
            ComissionadoModel.ativo == True
        )

        if identificacao:
            query = query.filter(
                ComissionadoModel.identificacao.ilike(f"%{identificacao}%")
            )

        if numero_documento:
            query = query.filter(
                ComissionadoModel.numero_documento.ilike(f"%{numero_documento}%")
            )

        if telefone:
            query = query.filter(
                ComissionadoModel.telefone.ilike(f"%{telefone}%")
            )

        return query.order_by(ComissionadoModel.id.desc()).all()
