from ...base_model import BaseModel, db
from sqlalchemy import and_, Numeric
from sistema.models_views.controle_carga.solicitacao_nf.carga_model import CargaModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema.models_views.gerenciar.veiculo.veiculo_model import VeiculoModel
from sistema.models_views.gerenciar.motorista.motorista_model import MotoristaModel


class TicketModel(BaseModel):
    """
    Model para registro de tckets de pesagem
    """
    __tablename__ = 'car_carga_ticket'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    solicitacao_nf_id = db.Column(db.Integer, db.ForeignKey('car_carga.id'), nullable=True)
    solicitacao = db.relationship('CargaModel', backref=db.backref('ccar_carga_ticket', lazy=True))
    
    numero_nota_fiscal = db.Column(db.String(20), nullable=True)
    peso_liquido = db.Column(db.Float, nullable=True)

    placa = db.Column(db.String(50), nullable=True)
    motorista = db.Column(db.String(200), nullable=True)
    
    arquivo_ticket_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    arquivo_ticket = db.relationship("UploadArquivoModel", backref=db.backref("car_carga_ticket", lazy=True))

    ativo = db.Column(db.Boolean, default=True, nullable=False)
        
    def __init__(
            self, solicitacao_nf_id, ativo, numero_nota_fiscal=None,
            peso_liquido=None, placa=None, motorista=None, arquivo_ticket_id=None
        ):
        self.solicitacao_nf_id = solicitacao_nf_id
        self.numero_nota_fiscal = numero_nota_fiscal
        self.peso_liquido = peso_liquido
        self.placa = placa
        self.motorista = motorista
        self.arquivo_ticket_id = arquivo_ticket_id
        self.ativo = ativo
        
        
    def listar_tickets_lancados():
        tickets = TicketModel.query.filter(
            TicketModel.deletado == 0
        ).order_by(
            TicketModel.id.desc()
        ).all()

        return tickets

    def obter_ticket_por_id(id):
        ticket = TicketModel.query.filter(
            TicketModel.id == id,
            TicketModel.deletado == 0
        ).first()

        return ticket
    
    def filtrar_tickets(
        motorista_nf=None,
        motorista_solicitacao=None,
        nome_cliente=None,
        placaTicket=None,
        placa_solicitacao=None,
    ):
        query = (
            TicketModel.query
            .join(TicketModel.solicitacao)
            .join(CargaModel.cliente)
            .join(CargaModel.veiculo)
            .join(CargaModel.motorista)
        )

        if nome_cliente:
            query = query.filter(ClienteModel.identificacao.like(f"%{nome_cliente}%"))

        if motorista_nf:
            query = query.filter(TicketModel.motorista.like(f"%{motorista_nf}%"))

        if motorista_solicitacao:
            query = query.filter(MotoristaModel.nome_completo.like(f"%{motorista_solicitacao}%"))

        if placaTicket:
            query = query.filter(TicketModel.placa.like(f"%{placaTicket}%"))

        if placa_solicitacao:
            query = query.filter(VeiculoModel.placa_veiculo.like(f"%{placa_solicitacao}%"))

        query = query.filter(TicketModel.deletado == False)

        return query.order_by(TicketModel.id.desc()).all()

