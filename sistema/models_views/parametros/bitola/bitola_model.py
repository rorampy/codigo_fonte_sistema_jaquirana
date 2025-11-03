from ...base_model import BaseModel, db
from sqlalchemy import and_


class BitolaModel(BaseModel):
    """
    Model para registro de bitola
    """
    __tablename__ = 'z_sys_bitola'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    bitola = db.Column(db.String(200), nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(
            self, bitola, ativo=True
    ):
        self.bitola = bitola
        self.ativo = ativo

    def listar_bitolas():
        bitolas = BitolaModel.query.filter(
            BitolaModel.deletado == 0,
        ).order_by(BitolaModel.id.desc()).all()

        return bitolas

    def listar_bitolas_ativas():
        bitolas = BitolaModel.query.filter(
            BitolaModel.deletado == 0,
            BitolaModel.ativo == 1
        ).order_by(BitolaModel.id.desc()).all()

        return bitolas
    
    def listar_bitolas_inativas():
        bitolas = BitolaModel.query.filter(
            BitolaModel.deletado == 0,
             BitolaModel.ativo == 0
        ).all()

        return bitolas
    
    def obter_bitola_por_id(id):
        parametro = BitolaModel.query.filter(
            BitolaModel.id == id,
            BitolaModel.deletado == 0
        ).first()

        return parametro