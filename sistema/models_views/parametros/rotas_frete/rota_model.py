from ...base_model import BaseModel, db
from sqlalchemy import and_
from collections import defaultdict
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel


class RotaFreteModel(BaseModel):
    """
    Model para registro de rotas de frete
    """
    __tablename__ = 'z_sys_rota_frete'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    floresta_id = db.Column(db.Integer, db.ForeignKey('flor_floresta.id'), nullable=True)
    floresta = db.relationship('FlorestaModel', backref=db.backref('floresta_rota', lazy=True))

    fornecedor_id = db.Column(db.Integer, db.ForeignKey('for_fornecedor_cadastro.id'), nullable=True)
    fornecedor = db.relationship('FornecedorCadastroModel', backref=db.backref('fornecedor_rota_frete', lazy=True))

    cliente_id = db.Column(db.Integer, db.ForeignKey('cli_cliente.id'), nullable=False)
    cliente = db.relationship('ClienteModel', backref=db.backref('cliente_rota', lazy=True))

    transportadora_id = db.Column(db.Integer, db.ForeignKey('transp_transportadora.id'), nullable=True)
    transportadora = db.relationship('TransportadoraModel', backref=db.backref('transportadora_rota', lazy=True))

    euca_bitola_1_id = db.Column(db.Integer, nullable=True)
    euca_preco_custo_frete_bitola_1_100 = db.Column(db.Integer, nullable=True)
    euca_bitola_2_id = db.Column(db.Integer, nullable=True)
    euca_preco_custo_frete_bitola_2_100 = db.Column(db.Integer, nullable=True)
    euca_bitola_3_id = db.Column(db.Integer, nullable=True)
    euca_preco_custo_frete_bitola_3_100 = db.Column(db.Integer, nullable=True)
    euca_bitola_4_id = db.Column(db.Integer, nullable=True)
    euca_preco_custo_frete_bitola_4_100 = db.Column(db.Integer, nullable=True)

    pinus_bitola_1_id = db.Column(db.Integer, nullable=True)
    pinus_preco_custo_frete_bitola_1_100 = db.Column(db.Integer, nullable=True)
    pinus_bitola_2_id = db.Column(db.Integer, nullable=True)
    pinus_preco_custo_frete_bitola_2_100 = db.Column(db.Integer, nullable=True)
    pinus_bitola_3_id = db.Column(db.Integer, nullable=True)
    pinus_preco_custo_frete_bitola_3_100 = db.Column(db.Integer, nullable=True)
    pinus_bitola_4_id = db.Column(db.Integer, nullable=True)
    pinus_preco_custo_frete_bitola_4_100 = db.Column(db.Integer, nullable=True)
    pinus_bitola_5_id = db.Column(db.Integer, nullable=True)
    pinus_preco_custo_frete_bitola_5_100 = db.Column(db.Integer, nullable=True)

    bio_bitola_5_id = db.Column(db.Integer, nullable=True)
    bio_preco_custo_frete_bitola_5_100 = db.Column(db.Integer, nullable=True)

    ativo = db.Column(db.Boolean, default=True, nullable=False)
        
    def __init__(
            self, cliente_id, transportadora_id, ativo, floresta_id=None, fornecedor_id=None,
            euca_bitola_1_id=None, euca_preco_custo_frete_bitola_1_100=None,
            euca_bitola_2_id=None, euca_preco_custo_frete_bitola_2_100=None,
            euca_bitola_3_id=None, euca_preco_custo_frete_bitola_3_100=None,
            euca_bitola_4_id=None, euca_preco_custo_frete_bitola_4_100=None,
            pinus_bitola_1_id=None, pinus_preco_custo_frete_bitola_1_100=None,
            pinus_bitola_2_id=None, pinus_preco_custo_frete_bitola_2_100=None,
            pinus_bitola_3_id=None, pinus_preco_custo_frete_bitola_3_100=None,
            pinus_bitola_4_id=None, pinus_preco_custo_frete_bitola_4_100=None,
            pinus_bitola_5_id=None, pinus_preco_custo_frete_bitola_5_100=None,
            bio_bitola_5_id=None, bio_preco_custo_frete_bitola_5_100=None
    ):
        self.floresta_id = floresta_id
        self.fornecedor_id = fornecedor_id
        self.cliente_id = cliente_id
        self.transportadora_id = transportadora_id
        self.euca_bitola_1_id = euca_bitola_1_id
        self.euca_preco_custo_frete_bitola_1_100 = euca_preco_custo_frete_bitola_1_100
        self.euca_bitola_2_id = euca_bitola_2_id
        self.euca_preco_custo_frete_bitola_2_100 = euca_preco_custo_frete_bitola_2_100
        self.euca_bitola_3_id = euca_bitola_3_id
        self.euca_preco_custo_frete_bitola_3_100 = euca_preco_custo_frete_bitola_3_100
        self.euca_bitola_4_id = euca_bitola_4_id
        self.euca_preco_custo_frete_bitola_4_100 = euca_preco_custo_frete_bitola_4_100

        self.pinus_bitola_1_id = pinus_bitola_1_id
        self.pinus_preco_custo_frete_bitola_1_100 = pinus_preco_custo_frete_bitola_1_100
        self.pinus_bitola_2_id = pinus_bitola_2_id
        self.pinus_preco_custo_frete_bitola_2_100 = pinus_preco_custo_frete_bitola_2_100
        self.pinus_bitola_3_id = pinus_bitola_3_id
        self.pinus_preco_custo_frete_bitola_3_100 = pinus_preco_custo_frete_bitola_3_100
        self.pinus_bitola_4_id = pinus_bitola_4_id
        self.pinus_preco_custo_frete_bitola_4_100 = pinus_preco_custo_frete_bitola_4_100
        self.pinus_bitola_5_id = pinus_bitola_5_id
        self.pinus_preco_custo_frete_bitola_5_100 = pinus_preco_custo_frete_bitola_5_100

        self.bio_bitola_5_id = bio_bitola_5_id
        self.bio_preco_custo_frete_bitola_5_100 = bio_preco_custo_frete_bitola_5_100
        self.ativo = ativo
        
        
    def listar_rotas():
        rotas = RotaFreteModel.query.filter(
            RotaFreteModel.deletado == 0
        ).order_by(RotaFreteModel.id.desc()).all()

        return rotas
    
    def listar_rotas_inativas():
        rotas = RotaFreteModel.query.filter(
            RotaFreteModel.ativo == 0
        ).order_by(RotaFreteModel.id.desc()).all()

        return rotas
    
    def obter_rota_por_id(id):
        rota = RotaFreteModel.query.filter(
            RotaFreteModel.id == id
        ).first()

        return rota
    
    def listar_rotas_agrupadas_por_cliente():
        query = (
            db.session.query(RotaFreteModel, ClienteModel)
            .join(ClienteModel, RotaFreteModel.cliente)
            .filter(RotaFreteModel.ativo == True)
            .order_by(ClienteModel.identificacao, RotaFreteModel.id.desc())
        )

        registros = query.all()
        agrupados = []

        temp = defaultdict(list)
        for rota, cliente in registros:
            temp[cliente].append(rota)

        for cliente, rotas in temp.items():
            agrupados.append({"cliente": cliente, "rotas": rotas})

        return agrupados
    
    def listar_rotas_ativas():
        rotas = RotaFreteModel.query.filter(
            RotaFreteModel.deletado == 0,
            RotaFreteModel.ativo == 1
        ).order_by(RotaFreteModel.id.desc()).all()

        return rotas
    
    def obter_rotas_relacionadas_transportadora(cliente_id, transportadora_id, fornecedor_id):
        rota = RotaFreteModel.query.filter(
            RotaFreteModel.cliente_id == cliente_id,
            RotaFreteModel.transportadora_id == transportadora_id,
            RotaFreteModel.fornecedor_id == fornecedor_id,
            RotaFreteModel.ativo == 1,
            RotaFreteModel.deletado == 0
        ).first()
        
        if not rota:
            rota = RotaFreteModel.query.filter(
                RotaFreteModel.cliente_id == cliente_id,
                RotaFreteModel.transportadora_id.is_(None),
                RotaFreteModel.fornecedor_id == fornecedor_id,
                RotaFreteModel.ativo == 1,
                RotaFreteModel.deletado == 0
            ).first()

        return rota