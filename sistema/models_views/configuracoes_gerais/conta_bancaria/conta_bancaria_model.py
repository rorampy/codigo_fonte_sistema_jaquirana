from ...base_model import BaseModel, db
from sqlalchemy import and_, desc


class ContaBancariaModel(BaseModel):
    """
    Model para registro de contas bancarias
    """
    __tablename__ = 'con_conta_bancaria'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    identificacao = db.Column(db.String(255), nullable=False)  
    nome_banco = db.Column(db.String(100), nullable=False)     
    agencia = db.Column(db.String(20), nullable=False)         
    conta = db.Column(db.String(20), nullable=False)          
    conta_principal = db.Column(db.Boolean, default=False, nullable=False)  
    saldo_inicial_100 = db.Column(db.Integer, default=False, nullable=True)  
    ativo = db.Column(db.Boolean, default=True, nullable=False)             
    deletado = db.Column(db.Boolean, default=False, nullable=False)         

    def __init__(self, identificacao, nome_banco, agencia, conta, conta_principal=False, saldo_inicial_100=None, ativo=True):
        self.identificacao = identificacao
        self.nome_banco = nome_banco
        self.agencia = agencia
        self.conta = conta
        self.conta_principal = conta_principal
        self.saldo_inicial_100 = saldo_inicial_100
        self.ativo = ativo
        self.deletado = False

    def obter_contas_bancarias_ativas():
        """
        Obtém todas as contas bancárias ativas e não deletadas.
        
        Returns:
            list: Lista de contas bancárias ordenadas por ID decrescente
        """
        return (
            ContaBancariaModel.query
            .filter_by(deletado=False, ativo=True)
            .order_by(desc(ContaBancariaModel.conta_principal))
            .all()
        )

    def obter_conta_por_id(id):
        """
        Obtém uma conta bancária específica pelo ID.
        
        Args:
            id (int): ID da conta bancária a ser buscada
            
        Returns:
            ContaBancariaModel: Conta bancária encontrada ou None se não existir
        """
        return (
            ContaBancariaModel.query
            .filter(
                ContaBancariaModel.id == id,
                ContaBancariaModel.deletado == False,
                ContaBancariaModel.ativo == True
            )
            .first()
        )

    def verifica_conta_bancaria_principal():
        """
        Verifica se existe uma conta bancária principal ativa.
        
        Returns:
            ContaBancariaModel: Conta bancária principal encontrada ou None se não existir
        """
        principal = ContaBancariaModel.query.filter(
            ContaBancariaModel.ativo == True,
            ContaBancariaModel.deletado == False,
            ContaBancariaModel.conta_principal == True
        ).first()
        
        return principal
