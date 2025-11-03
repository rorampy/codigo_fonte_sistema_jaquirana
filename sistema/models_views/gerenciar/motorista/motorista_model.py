from ...base_model import BaseModel, db
from sqlalchemy import and_, desc
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel


class MotoristaModel(BaseModel):
    """
    Model para registro de motoristas
    """
    __tablename__ = 'transp_motorista'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    # =========================> DESCONTINUADO <=========================
    # Tabela legada, usada somente para pegar informações que foram cadastradas antes da nova implementação
    transportadora_id = db.Column(db.Integer, db.ForeignKey('transp_transportadora.id'), nullable=True)
    transportadora = db.relationship('TransportadoraModel', backref=db.backref('transportadora_motorista', lazy=True))
    # ===================================================================

    nome_completo = db.Column(db.String(255), nullable=False)
    cpf = db.Column(db.String(20), nullable=False)
    celular = db.Column(db.String(20), nullable=False)

    transportadora_associacoes = db.relationship('TransportadoraMotoristaAssocModel', back_populates='motorista',lazy=True)


    ativo = db.Column(db.Boolean, default=True, nullable=False)
        
    def __init__(
            self, nome_completo, cpf, celular, transportadora_id=None, ativo=True
    ):
        self.transportadora_id = transportadora_id
        self.nome_completo = nome_completo
        self.cpf = cpf
        self.celular = celular
        self.ativo = ativo
    

    def listar_motoristas():
        """
        Lista todos os motoristas não deletados, ordenados por ID decrescente.
        
        Returns:
            list: Lista de objetos MotoristaModel não deletados
        """
        motoristas = MotoristaModel.query.filter(
            MotoristaModel.deletado == 0,
        ).order_by(MotoristaModel.nome_completo.asc()).all()

        return motoristas


    def listar_motoristas_ativos():
        """
        Lista todos os motoristas ativos e não deletados, ordenados por ID decrescente.
        
        Returns:
            list: Lista de objetos MotoristaModel ativos e não deletados
        """
        motoristas = MotoristaModel.query.filter(
            MotoristaModel.deletado == 0,
            MotoristaModel.ativo == 1
        ).order_by(MotoristaModel.id.desc()).all()

        return motoristas


    def listar_motoristas_inativos():
        """
        Lista todos os motoristas inativos e deletados.
        
        Returns:
            list: Lista de objetos MotoristaModel inativos e deletados
        """
        motoristas = MotoristaModel.query.filter(
            MotoristaModel.deletado == 1,
            MotoristaModel.ativo == 0
        ).all()

        return motoristas


    def obter_motorista_por_id(id):
        """
        Obtém um motorista específico por ID, apenas se não estiver deletado.
        
        Args:
            id (int): ID do motorista
        
        Returns:
            MotoristaModel: Objeto do motorista encontrado ou None se não encontrar
        """
        motorista = MotoristaModel.query.filter(
            MotoristaModel.id == id,
            MotoristaModel.deletado == 0
        ).first()

        return motorista


    def filtrar_motoristas(
        transportadora=None,
        nome_completo=None,
        numero_documento=None,
    ):
        """
        Filtra motoristas ativos por transportadora, nome completo ou número de documento.
        
        Args:
            transportadora (str, optional): Nome/identificação da transportadora
            nome_completo (str, optional): Nome completo do motorista
            numero_documento (str, optional): CPF do motorista
        
        Returns:
            list: Lista de objetos MotoristaModel que atendem aos critérios de filtro
        """
        query = MotoristaModel.query.filter(
            MotoristaModel.deletado == False,
            MotoristaModel.ativo == True
        ).join(MotoristaModel.transportadora)

        if transportadora:
            query = query.filter(
                TransportadoraModel.identificacao.ilike(f"%{transportadora}%")
            )

        if nome_completo:
            query = query.filter(
                MotoristaModel.nome_completo.ilike(f"%{nome_completo}%")
            )

        if numero_documento:
            query = query.filter(
                MotoristaModel.cpf.ilike(f"%{numero_documento}%")
            )

        return query.order_by(MotoristaModel.id.desc()).all()


    def obter_motoristas_por_transportadora(transportadora_id):
        """
        Obtém todos os motoristas ativos de uma transportadora específica.
        
        Args:
            transportadora_id (int): ID da transportadora
        
        Returns:
            list: Lista de objetos MotoristaModel da transportadora especificada, ordenados por ID decrescente
        """
        motoristas = MotoristaModel.query.filter(
            MotoristaModel.deletado == False,
            MotoristaModel.ativo == True,
            MotoristaModel.transportadora_id == transportadora_id
        ).order_by(desc(MotoristaModel.id)).all()

        return motoristas