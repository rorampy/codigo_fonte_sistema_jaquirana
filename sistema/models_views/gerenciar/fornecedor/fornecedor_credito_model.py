from ...base_model import BaseModel, db


class FornecedorCreditoModel(BaseModel):
    __tablename__ = 'for_fornecedor_credito'
    
    id = db.Column(db.Integer, primary_key=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('for_fornecedor_cadastro.id'), nullable=False)    
    credito_100 = db.Column(db.Integer, nullable=True)  # Crédito em centavos por tonelada

    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(self, fornecedor_id, credito_100=None, ativo=True):
        self.fornecedor_id = fornecedor_id
        self.credito_100 = credito_100
        self.ativo = ativo

    @staticmethod
    def obter_credito_por_fornecedor(fornecedor_id):
        """
        Obtém o crédito de um fornecedor específico.
        
        Args:
            fornecedor_id (int): ID do fornecedor
            
        Returns:
            FornecedorCreditoModel: Registro encontrado ou None
        """
        return FornecedorCreditoModel.query.filter(
            FornecedorCreditoModel.fornecedor_id == fornecedor_id,
            FornecedorCreditoModel.ativo == True,
            FornecedorCreditoModel.deletado == False
        ).first()

    @staticmethod
    def atualizar_ou_criar_credito(fornecedor_id, credito_100=None):
        """
        Atualiza um registro existente ou cria um novo se não existir.
        
        Args:
            fornecedor_id (int): ID do fornecedor
            credito_100 (int, optional): Crédito em centavos
            
        Returns:
            FornecedorCreditoModel: Registro atualizado ou criado
        """
        registro = FornecedorCreditoModel.obter_credito_por_fornecedor(fornecedor_id)
        
        if registro:
            # Atualiza registro existente - NÃO CRIA NOVO!
            if credito_100 is not None:
                registro.credito_100 = credito_100
        else:
            # Cria novo registro APENAS se não existir
            registro = FornecedorCreditoModel(
                fornecedor_id=fornecedor_id,
                credito_100=credito_100
            )
            db.session.add(registro)
        
        return registro