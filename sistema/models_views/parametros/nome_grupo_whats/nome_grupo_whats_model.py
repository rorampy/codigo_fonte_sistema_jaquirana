from ...base_model import BaseModel, db
from sqlalchemy import and_


class NomeGrupoWhatsModel(BaseModel):
    """
    Model para registro de nome de grupos do whatsapp
    """
    __tablename__ = 'z_sys_nome_grupo'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    nome_grupo_whats = db.Column(db.String(255), nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(
            self, nome_grupo_whats, ativo=True
    ):
        self.nome_grupo_whats = nome_grupo_whats
        self.ativo = ativo

    def listar_grupos():
        grupos = NomeGrupoWhatsModel.query.filter(
            NomeGrupoWhatsModel.deletado == 0,
        ).order_by(NomeGrupoWhatsModel.id.desc()).all()

        return grupos

    def listar_grupos_ativos():
        grupos = NomeGrupoWhatsModel.query.filter(
            NomeGrupoWhatsModel.deletado == 0,
            NomeGrupoWhatsModel.ativo == 1
        ).order_by(NomeGrupoWhatsModel.id.desc()).all()

        return grupos
    
    def listar_grupos_inativos():
        grupos = NomeGrupoWhatsModel.query.filter(
            NomeGrupoWhatsModel.deletado == 0,
             NomeGrupoWhatsModel.ativo == 0
        ).all()

        return grupos
    
    def obter_grupo_por_id(id):
        grupo = NomeGrupoWhatsModel.query.filter(
            NomeGrupoWhatsModel.id == id,
            NomeGrupoWhatsModel.deletado == 0
        ).first()

        return grupo