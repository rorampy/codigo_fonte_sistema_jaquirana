from sistema import db
from sistema.models_views.base_model import BaseModel
from sqlalchemy import desc

class TransportadoraVeiculoAssocModel(BaseModel):
    __tablename__ = 'transp_transportadora_veiculo_assoc'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    transportadora_id = db.Column(db.Integer, db.ForeignKey('transp_transportadora.id'), nullable=False)
    transportadora = db.relationship('TransportadoraModel', backref=db.backref('veiculo_associacoes', lazy=True))

    veiculo_id = db.Column(db.Integer, db.ForeignKey('transp_veiculo.id'), nullable=False)
    veiculo = db.relationship('VeiculoModel', backref=db.backref('transportadora_associacoes', lazy=True))

    ativo = db.Column(db.Boolean, default=True, nullable=False)
    deletado = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(self, transportadora_id, veiculo_id, ativo):
        self.transportadora_id = transportadora_id
        self.veiculo_id = veiculo_id
        self.ativo = ativo

    def obter_transportadoras_assoc_veiculo_id(veiculo_id):
        return TransportadoraVeiculoAssocModel.query.filter(
            TransportadoraVeiculoAssocModel.veiculo_id == veiculo_id,
            TransportadoraVeiculoAssocModel.deletado == 0,
            TransportadoraVeiculoAssocModel.ativo == 1
        ).order_by(desc(TransportadoraVeiculoAssocModel.id)).all()
