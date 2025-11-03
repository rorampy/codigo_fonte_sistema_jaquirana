from ...base_model import BaseModel, db
from sqlalchemy import and_


class StatusEmissaoNfComplementarModel(BaseModel):
    """
    Model para registro de status de nf complementar (Emitida, Não Emitida, Cancelada)
    """
    __tablename__ = 'z_sys_status_emissao_nf_complementar'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    status = db.Column(db.String(255), nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(
            self, status, ativo=True
    ):
        self.status = status
        self.ativo = ativo

    def listar_status():
        status = StatusEmissaoNfComplementarModel.query.filter(
            StatusEmissaoNfComplementarModel.deletado == 0,
        ).order_by(StatusEmissaoNfComplementarModel.id.desc()).all()

        return status

    def listar_status_ativos():
        status = StatusEmissaoNfComplementarModel.query.filter(
            StatusEmissaoNfComplementarModel.deletado == 0,
            StatusEmissaoNfComplementarModel.ativo == 1
        ).order_by(StatusEmissaoNfComplementarModel.id.desc()).all()

        return status
    
    def listar_status_inativos():
        status = StatusEmissaoNfComplementarModel.query.filter(
            StatusEmissaoNfComplementarModel.deletado == 0,
             StatusEmissaoNfComplementarModel.ativo == 0
        ).all()

        return status
    
    def obter_status_por_id(id):
        status = StatusEmissaoNfComplementarModel.query.filter(
            StatusEmissaoNfComplementarModel.id == id,
            StatusEmissaoNfComplementarModel.deletado == 0
        ).first()

        return status