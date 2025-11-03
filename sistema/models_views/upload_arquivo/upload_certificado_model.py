from sistema.models_views.base_model import BaseModel, db
from config import *
from sqlalchemy import and_


class UploadCertificadoModel(BaseModel):
    """
    Model base para registro de certificados digitais.
    """
    __tablename__ = 'upload_certificado'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255))
    caminho = db.Column(db.String(255))
    extensao = db.Column(db.String(8))
    tamanho = db.Column(db.Float)


    def __init__(self, nome, caminho, extensao, tamanho):
        self.nome = nome
        self.caminho = caminho
        self.extensao = extensao
        self.tamanho = tamanho


    def validar_extensao_certificado(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in EXTENSOES_CERTIFICADOS
    
    
    def obter_arquivo_por_id(id):
        arquivo = UploadCertificadoModel.query.filter(and_(
            UploadCertificadoModel.id == id,
            UploadCertificadoModel.deletado == 0
        )).first()
        
        return arquivo
    