from ...base_model import BaseModel, db
from sqlalchemy import and_, desc


class CentroCustoModel(BaseModel):
    """
    Model para registro de centro de custo
    """
    __tablename__ = 'ce_centro_custo'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    def __init__(
            self, nome, ativo=True
    ):
        self.nome = nome
        self.ativo = ativo

    def obter_centro_custos_ativos():
        """
        Obtém todos os centros de custos ativos e não deletados.
        
        Returns:
            list: Lista de centros de custos ordenados por ID decrescente
        """
        return (
            CentroCustoModel.query
            .filter_by(deletado=False, ativo=True)
            .order_by(desc(CentroCustoModel.id))
            .all()
        )

    @staticmethod
    def obter_centro_custo_por_id(id):
        """
        Obtém um centro de custo específico pelo ID.
        
        Args:
            id (int): ID do centro de custo a ser buscado
            
        Returns:
            CentroCustoModel: Centro de custo encontrado ou None se não existir
        """
        empresa = CentroCustoModel.query.filter(
            CentroCustoModel.id == id,
            CentroCustoModel.deletado == False,
            CentroCustoModel.ativo == True
        ).first()
        
        return empresa
