from ...base_model import BaseModel, db


class FornecedorExtratorModel(BaseModel):
    """
    Tabela auxiliar: vincula múltiplos extratores a um fornecedor.
    Cada linha representa uma relação fornecedor ↔ extrator.
    """

    __tablename__ = 'for_fornecedor_extrator'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    
    # Relacionamentos
    fornecedor_id = db.Column(db.Integer, db.ForeignKey("for_fornecedor_cadastro.id", ondelete="CASCADE"), nullable=False)
    fornecedor = db.relationship("FornecedorCadastroModel", backref=db.backref("extratores_vinculados", lazy=True))
    
    extrator_id = db.Column(db.Integer, db.ForeignKey("ext_extrator.id"), nullable=False)
    extrator = db.relationship("ExtratorModel", backref=db.backref("vinculos_fornecedor", lazy=True))
    
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(self, fornecedor_id, extrator_id, ativo=True):
        self.fornecedor_id = fornecedor_id
        self.extrator_id = extrator_id
        self.ativo = ativo

    @staticmethod
    def listar_por_fornecedor(fornecedor_id):
        """
        Lista todos os extratores vinculados a um fornecedor específico.
        
        Args:
            fornecedor_id (int): ID do fornecedor
        
        Returns:
            list: Lista de objetos FornecedorExtratorModel ativos
        """
        return FornecedorExtratorModel.query.filter(
            FornecedorExtratorModel.fornecedor_id == fornecedor_id,
            FornecedorExtratorModel.deletado == False,
            FornecedorExtratorModel.ativo == True
        ).all()

    @staticmethod
    def obter_por_fornecedor_extrator(fornecedor_id, extrator_id):
        """
        Obtém o vínculo entre um fornecedor e extrator específicos.
        
        Args:
            fornecedor_id (int): ID do fornecedor
            extrator_id (int): ID do extrator
        
        Returns:
            FornecedorExtratorModel: Objeto encontrado ou None
        """
        return FornecedorExtratorModel.query.filter(
            FornecedorExtratorModel.fornecedor_id == fornecedor_id,
            FornecedorExtratorModel.extrator_id == extrator_id,
            FornecedorExtratorModel.deletado == False,
            FornecedorExtratorModel.ativo == True
        ).first()

    @staticmethod
    def obter_por_id(id):
        """
        Obtém um vínculo específico por ID.
        
        Args:
            id (int): ID do vínculo
        
        Returns:
            FornecedorExtratorModel: Objeto encontrado ou None
        """
        return FornecedorExtratorModel.query.filter(
            FornecedorExtratorModel.id == id,
            FornecedorExtratorModel.deletado == False
        ).first()
