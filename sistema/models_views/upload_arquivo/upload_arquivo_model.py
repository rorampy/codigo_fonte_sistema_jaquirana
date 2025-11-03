from sistema.models_views.base_model import BaseModel, db
from config import *
from sqlalchemy import and_


class UploadArquivoModel(BaseModel):
    """
    Model base para registro de arquivos e imagens.
    """
    __tablename__ = 'upload_arquivo'
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


    def validar_extensao_imagem(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in EXTENSOES_IMAGENS


    def validar_extensao_arquivo(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in EXTENSOES_DOCS
    
    
    def obter_arquivo_por_id(id):
        arquivo = UploadArquivoModel.query.filter(and_(
            UploadArquivoModel.deletado == 0
        )).first()
        
        return arquivo
    