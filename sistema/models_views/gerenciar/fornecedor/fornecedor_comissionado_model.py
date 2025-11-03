from ...base_model import BaseModel, db


class FornecedorComissionadoModel(BaseModel):
    """
    Tabela auxiliar: quando fornecedor tem comissionados vinculados,
    cada linha representa uma relação fornecedor ↔ comissionado com valor de comissão.
    """

    __tablename__ = 'for_fornecedor_comissionado'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    
    # Relacionamentos
    fornecedor_id = db.Column(db.Integer, db.ForeignKey("for_fornecedor.id", ondelete="CASCADE"), nullable=False)
    fornecedor = db.relationship("FornecedorModel", backref=db.backref("comissionados_vinculados", lazy=True))
    
    comissionado_id = db.Column(db.Integer, db.ForeignKey("com_comissionado.id"), nullable=False)
    comissionado = db.relationship("ComissionadoModel", backref=db.backref("vinculos_fornecedor", lazy=True))
    
    # Valor da comissão por tonelada (em centavos)
    valor_comissao_ton_100 = db.Column(db.Integer, nullable=False)
    
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(self, fornecedor_id, comissionado_id, valor_comissao_ton_100, ativo=True):
        self.fornecedor_id = fornecedor_id
        self.comissionado_id = comissionado_id
        self.valor_comissao_ton_100 = valor_comissao_ton_100
        self.ativo = ativo

    @staticmethod
    def listar_por_fornecedor(fornecedor_id):
        """
        Lista todos os comissionados vinculados a um fornecedor específico.
        
        Args:
            fornecedor_id (int): ID do fornecedor
        
        Returns:
            list: Lista de objetos FornecedorComissionadoModel ativos
        """
        return FornecedorComissionadoModel.query.filter(
            FornecedorComissionadoModel.fornecedor_id == fornecedor_id,
            FornecedorComissionadoModel.deletado == False,
            FornecedorComissionadoModel.ativo == True
        ).all()

    @staticmethod
    def obter_por_fornecedor_comissionado(fornecedor_id, comissionado_id):
        """
        Obtém o vínculo entre um fornecedor e comissionado específicos.
        
        Args:
            fornecedor_id (int): ID do fornecedor
            comissionado_id (int): ID do comissionado
        
        Returns:
            FornecedorComissionadoModel: Objeto encontrado ou None
        """
        return FornecedorComissionadoModel.query.filter(
            FornecedorComissionadoModel.fornecedor_id == fornecedor_id,
            FornecedorComissionadoModel.comissionado_id == comissionado_id,
            FornecedorComissionadoModel.deletado == False,
            FornecedorComissionadoModel.ativo == True
        ).first()

    @staticmethod
    def obter_por_id(id):
        """
        Obtém um vínculo específico por ID.
        
        Args:
            id (int): ID do vínculo
        
        Returns:
            FornecedorComissionadoModel: Objeto encontrado ou None
        """
        return FornecedorComissionadoModel.query.filter(
            FornecedorComissionadoModel.id == id,
            FornecedorComissionadoModel.deletado == False
        ).first()
