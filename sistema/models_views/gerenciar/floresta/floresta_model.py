from ...base_model import BaseModel, db
from sqlalchemy import and_

# =========================> ATENÇÃO <=========================
# Tabela descontinuada no projeto, agora é usada somente a tabela de fornecedores
# =============================================================
class FlorestaModel(BaseModel):
    """
    Model para registro de florestas
    """

    __tablename__ = "flor_floresta"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    identificacao = db.Column(db.String(200), nullable=False)
    rodovia = db.Column(db.String(200), nullable=True)
    km = db.Column(db.String(20), nullable=True)
    cidade = db.Column(db.String(150), nullable=False)
    estado = db.Column(db.String(100), nullable=False)
    contrato_floresta_id = db.Column(
        db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True
    )
    contrato_floresta = db.relationship(
        "UploadArquivoModel", backref=db.backref("contrato_floresta", lazy=True)
    )
    credito_100 = db.Column(db.Integer, nullable=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    def __init__(
        self,
        identificacao,
        rodovia,
        km,
        cidade,
        estado,
        ativo,
        credito_100=None,
        contrato_floresta_id=None,
    ):
        self.identificacao = identificacao
        self.rodovia = rodovia
        self.km = km
        self.cidade = cidade
        self.estado = estado
        self.contrato_floresta_id = contrato_floresta_id
        self.credito_100 = credito_100
        self.ativo = ativo

    def listar_floresta():
        florestas = (
            FlorestaModel.query.filter(FlorestaModel.deletado == 0)
            .order_by(FlorestaModel.id.desc())).all()
        
        return florestas

    def listar_florestas_ativas():
        florestas = (
            FlorestaModel.query.filter(FlorestaModel.deletado == 0, FlorestaModel.ativo == 1)
            .order_by(FlorestaModel.id.desc())).all()

        return florestas

    def listar_florestas_inativas():
        florestas = FlorestaModel.query.filter(FlorestaModel.deletado == 1, FlorestaModel.ativo == 0).all()

        return florestas

    def obter_floresta_por_id(id):
        floresta = FlorestaModel.query.filter(
            FlorestaModel.id == id, FlorestaModel.deletado == 0
        ).first()

        return floresta

    def filtrar_floresta(
        identficacao=None,
        rodovia=None,
        km=None,
        cidade=None,
        estado=None
    ):  
        query = FlorestaModel.query.filter(
            FlorestaModel.deletado == False
        )

        if identficacao:
            query = query.filter(
                FlorestaModel.identificacao.ilike(f"%{identficacao}%")
            )

        if rodovia:
            query = query.filter(
                FlorestaModel.rodovia.ilike(f"%{rodovia}%")
            )  

        if km:
            query = query.filter(
                FlorestaModel.km.ilike(f"%{km}%")
            ) 

        if cidade:
            query = query.filter(
                FlorestaModel.cidade.ilike(f"%{cidade}%")
            ) 

        if estado:
            query = query.filter(
                FlorestaModel.estado.ilike(f"%{estado}%")
            )   
            
        return query.order_by(FlorestaModel.id.desc()).all()