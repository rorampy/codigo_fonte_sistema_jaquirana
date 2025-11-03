from ...base_model import BaseModel, db
from sqlalchemy import and_, desc


class EmpresaEmissoraModel(BaseModel):
    """
    Model para registro empresa emissora
    """

    __tablename__ = "em_empresa_emissora"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    identificacao = db.Column(db.String(200), nullable=False)
    numero_documento = db.Column(db.String(20), nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    def __init__(self, identificacao, numero_documento, ativo=True):
        self.identificacao = identificacao
        self.numero_documento = numero_documento
        self.ativo = ativo

    def obter_empresas_emissoras_ativas():
        """
        Obtém todas as empresas emissoras ativas e não deletadas.
        
        Returns:
            list: Lista de empresas emissoras ordenadas por ID decrescente
        """
        return (
            EmpresaEmissoraModel.query
            .filter_by(deletado=False, ativo=True)
            .order_by(desc(EmpresaEmissoraModel.id))
            .all()
        )

    def obter_empresa_emissora_por_id(id):
        """
        Obtém uma empresa emissora específica pelo ID.
        
        Args:
            id (int): ID da empresa emissora a ser buscada
            
        Returns:
            EmpresaEmissoraModel: Empresa emissora encontrada ou None se não existir
        """
        empresa = EmpresaEmissoraModel.query.filter(
            EmpresaEmissoraModel.id == id,
            EmpresaEmissoraModel.deletado == False,
            EmpresaEmissoraModel.ativo == True
        ).first()
        
        return empresa
