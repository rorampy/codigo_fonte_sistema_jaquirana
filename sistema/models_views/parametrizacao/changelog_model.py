from ..base_model import BaseModel, db
from sqlalchemy import and_, desc


class ChangelogModel(BaseModel):
    """
    Model base para registro do histórico de versões do sistema.
    """
    __tablename__ = 'z_sys_changelog'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    data_lancamento = db.Column(db.String(14), nullable=False)
    versao = db.Column(db.String(25), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    
    
    def __init__(
        self, data_lancamento, versao, conteudo, ativo
    ):
        self.data_lancamento = data_lancamento
        self.versao = versao
        self.conteudo = conteudo
        self.ativo = ativo
        
    
    def obter_changelog_desc_id():
        changelog_sistema = ChangelogModel.query.filter(and_(
            ChangelogModel.ativo == 1,
            ChangelogModel.deletado == 0
        )).order_by(
            desc(ChangelogModel.id)
        ).all()
        
        return changelog_sistema
    
    
    def obter_numero_versao_changelog_mais_recente():
        versao_recente = ChangelogModel.query.filter(and_(
            ChangelogModel.ativo == 1,
            ChangelogModel.deletado == 0
        )).order_by(
            desc(ChangelogModel.id)
        ).first()
        
        return versao_recente