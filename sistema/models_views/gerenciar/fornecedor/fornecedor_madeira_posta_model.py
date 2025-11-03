from ...base_model import BaseModel, db
from sqlalchemy import and_


class FornecedorMadeiraPostaModel(BaseModel):
    """
    Tabela auxiliar: quando fornecedor.madeira_posta == True,
    cada linha representa uma relação fornecedor ↔ cliente, com preços por bitola de Eucalipto e de Pinus.
    """

    __tablename__ = 'for_fornecedor_madeira_posta'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey("for_fornecedor.id", ondelete="CASCADE"),nullable=False)
    fornecedor = db.relationship("FornecedorModel", back_populates="madeiras_posta")
    cliente_id = db.Column(db.Integer, db.ForeignKey("cli_cliente.id"), nullable=False)
    cliente = db.relationship("ClienteModel", backref=db.backref("madeiras_recebidas", lazy=True))
    
    # Condicionado a transportadora 
    transportadora_id = db.Column(db.Integer, db.ForeignKey("transp_transportadora.id"), nullable=True)
    transportadora = db.relationship("TransportadoraModel", backref=db.backref("transportadora_vinculada", lazy=True))

    # preços de Eucalipto por bitola
    euca_bitola_1_id = db.Column(db.Integer, nullable=True)
    euca_bitola_2_id = db.Column(db.Integer, nullable=True)
    euca_bitola_3_id = db.Column(db.Integer, nullable=True)
    euca_bitola_4_id = db.Column(db.Integer, nullable=True)
    euca_bitola_1_preco_100 = db.Column(db.Integer, nullable=True)
    euca_bitola_2_preco_100 = db.Column(db.Integer, nullable=True)
    euca_bitola_3_preco_100 = db.Column(db.Integer, nullable=True)
    euca_bitola_4_preco_100 = db.Column(db.Integer, nullable=True)

    # preços de Pinus por bitola
    pinus_bitola_1_id = db.Column(db.Integer, nullable=True)
    pinus_bitola_2_id = db.Column(db.Integer, nullable=True)
    pinus_bitola_3_id = db.Column(db.Integer, nullable=True)
    pinus_bitola_4_id = db.Column(db.Integer, nullable=True)
    pinus_bitola_5_id = db.Column(db.Integer, nullable=True)
    pinus_bitola_1_preco_100 = db.Column(db.Integer, nullable=True)
    pinus_bitola_2_preco_100 = db.Column(db.Integer, nullable=True)
    pinus_bitola_3_preco_100 = db.Column(db.Integer, nullable=True)
    pinus_bitola_4_preco_100 = db.Column(db.Integer, nullable=True)
    pinus_bitola_5_preco_100 = db.Column(db.Integer, nullable=True)

    bio_bitola_5_id = db.Column(db.Integer, nullable=True)
    bio_bitola_5_preco_100 = db.Column(db.Integer, nullable=True)
    
    bio_bitola_7_id = db.Column(db.Integer, nullable=True)
    bio_bitola_7_preco_100 = db.Column(db.Integer, nullable=True)

    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(
        self, fornecedor_id, cliente_id, transportadora_id=None,
        euca_bitola_1_preco_100=None, euca_bitola_2_preco_100=None,
        euca_bitola_3_preco_100=None, euca_bitola_4_preco_100=None,
        pinus_bitola_1_preco_100=None, pinus_bitola_2_preco_100=None,
        pinus_bitola_3_preco_100=None, pinus_bitola_4_preco_100=None,
        euca_bitola_1_id=None, pinus_bitola_1_id=None,
        euca_bitola_2_id=None, pinus_bitola_2_id=None,
        euca_bitola_3_id=None, pinus_bitola_3_id=None,
        euca_bitola_4_id=None, pinus_bitola_4_id=None,
        pinus_bitola_5_id=None, pinus_bitola_5_preco_100=None,
        bio_bitola_5_id=None, bio_bitola_5_preco_100=None,
        bio_bitola_7_id=None, bio_bitola_7_preco_100=None,
        ativo=True
    ):
        self.fornecedor_id = fornecedor_id
        self.transportadora_id = transportadora_id
        self.cliente_id = cliente_id
        self.euca_bitola_1_id=euca_bitola_1_id
        self.euca_bitola_2_id=euca_bitola_2_id
        self.euca_bitola_3_id=euca_bitola_3_id
        self.euca_bitola_4_id=euca_bitola_4_id
        self.euca_bitola_1_preco_100 = euca_bitola_1_preco_100
        self.euca_bitola_2_preco_100 = euca_bitola_2_preco_100
        self.euca_bitola_3_preco_100 = euca_bitola_3_preco_100
        self.euca_bitola_4_preco_100 = euca_bitola_4_preco_100
        self.pinus_bitola_1_id=pinus_bitola_1_id
        self.pinus_bitola_2_id=pinus_bitola_2_id
        self.pinus_bitola_3_id=pinus_bitola_3_id
        self.pinus_bitola_4_id=pinus_bitola_4_id
        self.pinus_bitola_5_id=pinus_bitola_5_id
        self.pinus_bitola_1_preco_100 = pinus_bitola_1_preco_100
        self.pinus_bitola_2_preco_100 = pinus_bitola_2_preco_100
        self.pinus_bitola_3_preco_100 = pinus_bitola_3_preco_100
        self.pinus_bitola_4_preco_100 = pinus_bitola_4_preco_100
        self.pinus_bitola_5_preco_100 = pinus_bitola_5_preco_100
        self.bio_bitola_5_id = bio_bitola_5_id
        self.bio_bitola_5_preco_100 = bio_bitola_5_preco_100
        self.bio_bitola_7_id = bio_bitola_7_id
        self.bio_bitola_7_preco_100 = bio_bitola_7_preco_100
        self.ativo = ativo

    