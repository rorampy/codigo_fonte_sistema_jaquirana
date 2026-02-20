from ...base_model import BaseModel, db
from sqlalchemy import and_
from sqlalchemy.orm import relationship

class CertificacoesModel(BaseModel):
    """
    Model para registro de certificações florestais
    """
    __tablename__ = 'est_certificacao_estoque'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.String(500), nullable=True)
    descricao_nota = db.Column(db.Text, nullable=True)
    valor_estoque_inicial = db.Column(db.Float, nullable=False, default=0.0)
    valor_estoque_atual = db.Column(db.Float, nullable=False, default=0.0)
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    anexos = relationship("CertificacaoAnexoModel", back_populates="certificacao", cascade="all, delete-orphan")

    def __init__(self, nome, descricao=None, descricao_nota=None, valor_estoque_inicial=0.0, valor_estoque_atual=0.0, ativo=True):
        self.nome = nome
        self.descricao = descricao
        self.descricao_nota = descricao_nota
        self.valor_estoque_inicial = valor_estoque_inicial
        self.valor_estoque_atual = valor_estoque_atual
        self.ativo = ativo

    @classmethod
    def obter_certificacao_por_id(cls, id):
        """Busca uma certificação pelo seu ID."""
        return cls.query.filter(and_(cls.id == id, cls.deletado == False, cls.ativo == True)).first()
    
    @classmethod
    def obter_certificacao_por_id_ativos_inativos(cls, id):
        """Busca uma certificação pelo seu ID."""
        return cls.query.filter(and_(cls.id == id)).first()
    
    def obter_certificacao_inativa_por_id(id):
        """Busca uma certificação inativa pelo seu ID."""
        return CertificacoesModel.query.filter(and_(CertificacoesModel.id == id, CertificacoesModel.ativo == False)).first()

    @classmethod
    def listar_certificacoes(cls):
        """Lista todas as certificações não deletadas"""
        return cls.query.filter(cls.deletado == False).order_by(cls.id.desc()).all()

    @classmethod
    def filtrar_certificacoes(cls, nome=None, descricao=None):
        """Filtra certificações por nome ou descrição"""
        query = cls.query.filter(cls.deletado == False)
        
        if nome:
            query = query.filter(cls.nome.ilike(f"%{nome}%"))
        
        if descricao:
            query = query.filter(cls.descricao.ilike(f"%{descricao}%"))
        
        return query.order_by(cls.id.desc()).all()
    
    def obter_anexos_ativos(self):
        """Retorna os anexos ativos associados a esta certificação."""
        return [anexo for anexo in self.anexos if anexo.deletado == False]
    
    @classmethod
    def listar_certificacoes_ativas(cls):
        """Lista apenas certificações ativas (para uso em selects/combos)"""
        return cls.query.filter(and_(cls.ativo == True, cls.deletado == False)).order_by(cls.id).all()
    
    def atualizar_estoque(quantidade, certificacao_id):
        """Atualiza o estoque atual da certificação."""
        
        resultado = {}
        certificado = CertificacoesModel.obter_certificacao_por_id(certificacao_id)
        if certificado and certificado.ativo:
            if (certificado.valor_estoque_atual == 0.0 or certificado.valor_estoque_atual < quantidade):
                resultado['invalido'] = 'Não foi possível concluir a operação! A quantidade solicitada excede o estoque disponível no momento.'
            if (certificado.valor_estoque_atual > 0.0 and quantidade <= certificado.valor_estoque_atual):
                certificado.valor_estoque_atual -= quantidade
                resultado['sucesso'] = 'A operação foi registrada e os valores foram ajustados corretamente.'
        elif not certificado or certificado.ativo == False:
            resultado['erro'] = 'Certificação não encontrada.'
        
        return resultado
    
    def atualizar_estoque_positivo(quantidade, certificacao_id):
        """Acrescenta o estoque atual da certificação."""
        
        resultado = {}
        certificado = CertificacoesModel.obter_certificacao_por_id(certificacao_id)
        if certificado and certificado.ativo:
            certificado.valor_estoque_atual += quantidade
            resultado['sucesso'] = 'A operação foi registrada e os valores foram ajustados corretamente.'
        elif not certificado or certificado.ativo == False:
            resultado['erro'] = 'Certificação não encontrada.'
        
        return resultado

class CertificacaoAnexoModel(BaseModel):
    """
    Model para anexos das certificações
    """
    __tablename__ = 'est_certificacao_anexos'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    certificacao_id = db.Column(db.Integer, db.ForeignKey('est_certificacao_estoque.id'), nullable=False)
    arquivo_upload_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=False)
    arquivo_upload = db.relationship("UploadArquivoModel", backref=db.backref("certificacao_anexos", lazy=True))
    descricao_anexo = db.Column(db.String(200), nullable=True)
    ordem_exibicao = db.Column(db.Integer, default=1)

    certificacao = relationship("CertificacoesModel", back_populates="anexos")

    def __init__(self, certificacao_id, arquivo_upload_id, descricao_anexo=None, ordem_exibicao=1):
        self.certificacao_id = certificacao_id
        self.arquivo_upload_id = arquivo_upload_id
        self.descricao_anexo = descricao_anexo
        self.ordem_exibicao = ordem_exibicao
    
    def excluir_anexo(self):
        """Marca o anexo como deletado."""
        self.deletado = True
        db.session.commit()
    
    @classmethod
    def obter_anexo_por_id(cls, id):
        """Busca um anexo pelo seu ID."""
        return cls.query.filter(and_(cls.id == id, cls.deletado == False)).first()