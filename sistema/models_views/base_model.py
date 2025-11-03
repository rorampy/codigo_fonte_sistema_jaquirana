from datetime import datetime
from pytz import timezone
from sistema import db

fuso_horario = timezone('America/Sao_Paulo')

class BaseModel(db.Model):
    """
    Model base para registro de auditoria e exclusão lógica.
    """
    __abstract__ = True
    data_cadastro = db.Column(
        db.DateTime, default=lambda: datetime.now(fuso_horario),
        nullable=False
    )
    data_alteracao = db.Column(
        db.DateTime, default=lambda: datetime.now(fuso_horario),
        onupdate=lambda: datetime.now(fuso_horario), nullable=False
    )
    deletado = db.Column(db.Boolean, default=False, nullable=False)
