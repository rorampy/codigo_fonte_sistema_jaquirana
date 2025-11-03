from sistema.models_views.base_model import BaseModel, db
from sqlalchemy import desc

class RoleModel(BaseModel):
    """
    Model para registro da Roles de acesso ao sistema
    """
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    cargo = db.Column(db.String(100), nullable=False)


    def __init__(self, nome, cargo):
        self.nome = nome,
        self.cargo = cargo
        
    
    def obter_roles_desc_id():
        roles = RoleModel.query.filter(
            RoleModel.deletado == 0
        ).order_by(
            desc(RoleModel.id)
        ).all()
        
        return roles
    
    
    def obter_role_por_id(id):
        role = RoleModel.query.filter(
            RoleModel.id == id
        ).first()
        
        return role