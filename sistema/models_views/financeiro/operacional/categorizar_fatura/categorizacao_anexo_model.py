from ....base_model import BaseModel, db
from sistema._utilitarios import *

class AgendamentoAnexoPagamentoModel(BaseModel):
    __tablename__ = 'fin_agendamento_pagamento_anexo'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    agendamento_id = db.Column(db.Integer, db.ForeignKey('fin_agendamento_pagamento.id'), nullable=False)
    agendamento = db.relationship('AgendamentoPagamentoModel', backref=db.backref('anexos', lazy=True))
    
    upload_arquivo_id = db.Column(db.Integer, db.ForeignKey('upload_arquivo.id'), nullable=False)
    upload_arquivo = db.relationship('UploadArquivoModel', backref=db.backref('anexos_agendamento', lazy=True))
    
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(self, agendamento_id, upload_arquivo_id):
        self.agendamento_id = agendamento_id
        self.upload_arquivo_id = upload_arquivo_id
        
    
    
    def obter_todos_anexos_por_agendamento(agendamento_id):
        """
        Obtém todos os anexos ativos e não deletados associados a um agendamento específico.
        Args:
            agendamento_id (int): ID do agendamento para buscar os anexos relacionados.
        Returns:
            list: Lista de objetos AgendamentoAnexoPagamentoModel que correspondem aos 
                  critérios de filtro (ativo=True, deletado=False) para o agendamento 
                  especificado.
        Example:
            >>> anexos = obter_todos_anexos_por_agendamento(123)
            >>> len(anexos)
            5
        """
        
        anexos = AgendamentoAnexoPagamentoModel.query.filter_by(
            agendamento_id=agendamento_id,
            ativo=True,
            deletado=False
        ).all()
        return anexos