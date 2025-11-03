from ...base_model import BaseModel, db
from sqlalchemy import and_
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel


class VeiculoModel(BaseModel):
    """
    Model para registro de veiculos
    """
    __tablename__ = 'transp_veiculo'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    
    # =========================> DESCONTINUADO <=========================
    # Tabela legada, usada somente para pegar informações que foram cadastradas antes da nova implementação
    transportadora_id = db.Column(db.Integer, db.ForeignKey('transp_transportadora.id'), nullable=True)
    transportadora = db.relationship('TransportadoraModel', backref=db.backref('transportadora_veiculo', lazy=True))
    # ===================================================================
    
    placa_veiculo = db.Column(db.String(20), nullable=False)
    capacidade_ton = db.Column(db.Float, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
        
        
    def __init__(
            self, placa_veiculo, 
            capacidade_ton, ativo=True, transportadora_id=None
    ):
        self.transportadora_id = transportadora_id
        self.placa_veiculo = placa_veiculo
        self.capacidade_ton = capacidade_ton
        self.ativo = ativo


    def listar_veiculos():
        """
        Lista todos os veículos não deletados, ordenados por ID decrescente.
        
        Returns:
            list: Lista de objetos VeiculoModel não deletados
        """
        veiculos = VeiculoModel.query.filter(
            VeiculoModel.deletado == 0,
        ).order_by(VeiculoModel.id.desc()).all()

        return veiculos


    def listar_veiculos_ativos():
        """
        Lista todos os veículos ativos e não deletados, ordenados por ID decrescente.
        
        Returns:
            list: Lista de objetos VeiculoModel ativos e não deletados
        """
        veiculos = VeiculoModel.query.filter(
            VeiculoModel.deletado == 0,
            VeiculoModel.ativo == 1
        ).order_by(VeiculoModel.id.desc()).all()

        return veiculos


    def listar_veiculos_inativos():
        """
        Lista todos os veículos deletados.
        
        Returns:
            list: Lista de objetos VeiculoModel deletados
        """
        veiculos = VeiculoModel.query.filter(
            VeiculoModel.deletado == 1
        ).all()

        return veiculos


    def obter_veiculo_por_id(id):
        """
        Obtém um veículo específico por ID, apenas se não estiver deletado.
        
        Args:
            id (int): ID do veículo
        
        Returns:
            VeiculoModel: Objeto do veículo encontrado ou None se não encontrar
        """
        veiculo = VeiculoModel.query.filter(
            VeiculoModel.id == id,
            VeiculoModel.deletado == 0
        ).first()

        return veiculo


    def filtrar_veiculos(
        transportadora=None,
        placa=None
    ):
        """
        Filtra veículos ativos por transportadora ou placa.
        
        Args:
            transportadora (str, optional): Nome/identificação da transportadora
            placa (str, optional): Placa do veículo
        
        Returns:
            list: Lista de objetos VeiculoModel que atendem aos critérios de filtro
        """
        query = VeiculoModel.query.filter(
            VeiculoModel.deletado == False,
            VeiculoModel.ativo == True
        ).join(VeiculoModel.transportadora)

        if transportadora:
            query = query.filter(TransportadoraModel.identificacao.ilike(f"%{transportadora}%"))

        if placa:
            query = query.filter(VeiculoModel.placa_veiculo.ilike(f"%{placa}%"))

        return query.order_by(VeiculoModel.id.desc()).all()