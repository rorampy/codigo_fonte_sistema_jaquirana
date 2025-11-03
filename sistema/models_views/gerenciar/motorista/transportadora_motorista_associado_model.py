from sistema import db
from sistema.models_views.base_model import BaseModel
from sistema.models_views.gerenciar.motorista.motorista_model import MotoristaModel
from sqlalchemy import desc

class TransportadoraMotoristaAssocModel(BaseModel):
    __tablename__ = 'transp_transportadora_motorista_assoc'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    transportadora_id = db.Column(db.Integer, db.ForeignKey('transp_transportadora.id'), nullable=False)
    transportadora = db.relationship('TransportadoraModel', backref=db.backref('motorista_associacoes', lazy=True))

    motorista_id = db.Column(db.Integer, db.ForeignKey('transp_motorista.id'), nullable=False)
    motorista = db.relationship('MotoristaModel', back_populates='transportadora_associacoes')

    ativo = db.Column(db.Boolean, default=True, nullable=False)
    deletado = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(self, transportadora_id, motorista_id, ativo):
        self.transportadora_id = transportadora_id
        self.motorista_id = motorista_id
        self.ativo = ativo

    def obter_transportadoras_assoc_motorista_id(motorista_id):
        return TransportadoraMotoristaAssocModel.query.filter(
            TransportadoraMotoristaAssocModel.motorista_id == motorista_id,
            TransportadoraMotoristaAssocModel.deletado == 0,
            TransportadoraMotoristaAssocModel.ativo == 1
        ).order_by(desc(TransportadoraMotoristaAssocModel.id)).all()
    

    def obter_motoristas_assoc_transportadora_id(transportadora_id):
        """
        Retorna todos os motoristas associados à transportadora via:
          1) a tabela de associação (transp_transportadora_motorista_assoc), desde que ativa e não deletada;
          2) o campo legado motorista.transportadora_id.

        Retorna uma lista de objetos MotoristaModel.
        """

        motoristas_assoc = (
            db.session.query(MotoristaModel)
            .join(
                TransportadoraMotoristaAssocModel,
                MotoristaModel.id == TransportadoraMotoristaAssocModel.motorista_id
            )
            .filter(
                TransportadoraMotoristaAssocModel.transportadora_id == transportadora_id,
                TransportadoraMotoristaAssocModel.ativo.is_(True),
                TransportadoraMotoristaAssocModel.deletado.is_(False)
            )
            .all()
        )


        motoristas_legado = (
            db.session.query(MotoristaModel)
            .filter(
                MotoristaModel.transportadora_id == transportadora_id,
                MotoristaModel.ativo.is_(True),
                MotoristaModel.deletado.is_(False)
            )
            .all()
        )

        # Combinar os dois resultados e remover duplicados pelo atributo 'id'
        todos = {m.id: m for m in motoristas_assoc}

        for m in motoristas_legado:
            if m.id not in todos:
                todos[m.id] = m
        print(list(todos.values()))
        return list(todos.values())
