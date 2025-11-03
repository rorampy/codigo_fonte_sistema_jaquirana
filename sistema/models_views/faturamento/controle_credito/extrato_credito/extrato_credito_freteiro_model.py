from ....base_model import BaseModel, db
from sqlalchemy import desc

class ExtratoCreditoFreteiroModel(BaseModel):
    """
    Model para aguardar créditos de freteiros
    """
    __tablename__ = 'ex_extrato_credito_freteiro'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    # 1 - Entrada | 2 - Saída | 3 - Cancelamento | 4 - Estorno
    tipo_movimentacao = db.Column(db.Integer, nullable=True)

    plano_conta_id = db.Column(db.Integer, db.ForeignKey("plan_plano_conta.id"), nullable=True)
    plano_conta = db.relationship("PlanoContaModel", foreign_keys=[plano_conta_id], backref=db.backref("plano_conta_freteiro", lazy=True))

    categorizacao_fiscal_id = db.Column(db.Integer, db.ForeignKey("ca_categorizacao_fiscal.id"), nullable=True)
    categorizacao_fiscal = db.relationship("CategorizacaoFiscalModel", foreign_keys=[categorizacao_fiscal_id], backref=db.backref("categorizacao_fiscal_freteiro", lazy=True))

    descricao = db.Column(db.String(255), nullable=False)
    data_movimentacao = db.Column(db.Date, nullable=False)

    transportadora_id = db.Column(db.Integer, db.ForeignKey('transp_transportadora.id'), nullable=True)
    transportadora = db.relationship('TransportadoraModel', backref=db.backref('credito_transportadora', lazy=True))

    valor_credito_100 = db.Column(db.Integer, nullable=False)

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    usuario = db.relationship('UsuarioModel', backref=db.backref('usuario_credito_freteiro', lazy=True))

    upload_documentacao_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    upload_documentacao = db.relationship("UploadArquivoModel", foreign_keys=[upload_documentacao_id], backref=db.backref("credito_documentacao_transportadora", lazy=True))

    upload_comprovante_bancario_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    upload_comprovante_bancario = db.relationship("UploadArquivoModel", foreign_keys=[upload_comprovante_bancario_id], backref=db.backref("credito_comprovante_bancario_transportadora", lazy=True))

    credito_utilizado = db.Column(db.Boolean, default=False, nullable=False)
    
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(
            self, data_movimentacao, descricao, transportadora_id, valor_credito_100, usuario_id, upload_comprovante_bancario_id=upload_comprovante_bancario_id, upload_documentacao_id=upload_documentacao_id,  
            tipo_movimentacao=tipo_movimentacao, plano_conta_id=None, categorizacao_fiscal_id=None, credito_utilizado=None, ativo=True
    ):
        self.data_movimentacao = data_movimentacao
        self.plano_conta_id = plano_conta_id
        self.categorizacao_fiscal_id = categorizacao_fiscal_id
        self.descricao = descricao
        self.transportadora_id = transportadora_id
        self.valor_credito_100 = valor_credito_100
        self.usuario_id = usuario_id
        self.upload_comprovante_bancario_id = upload_comprovante_bancario_id
        self.upload_documentacao_id = upload_documentacao_id
        self.tipo_movimentacao = tipo_movimentacao
        self.credito_utilizado = credito_utilizado
        self.ativo = ativo

    def soma_valor_credito_disponivel(id):
        credito = ExtratoCreditoFreteiroModel.query.filter(
            ExtratoCreditoFreteiroModel.deletado == 0,
            ExtratoCreditoFreteiroModel.ativo == True,
            ExtratoCreditoFreteiroModel.transportadora_id == id
        ).all()

        return sum(c.valor_credito_100 for c in credito) or 0
    
    def listagem_historico_por_freteiro(id):
        extrato = ExtratoCreditoFreteiroModel.query.filter(
            ExtratoCreditoFreteiroModel.deletado == False,
            ExtratoCreditoFreteiroModel.ativo == True,
            ExtratoCreditoFreteiroModel.transportadora_id == id
        ).order_by(desc(
            ExtratoCreditoFreteiroModel.id
        )).all()

        return extrato
    
    def obter_creditos_disponiveis_transportadora(transportadora_id):
        """
        Busca todos os créditos individuais disponíveis para uma transportadora
        """
        try:
            creditos = ExtratoCreditoFreteiroModel.query.filter(
                ExtratoCreditoFreteiroModel.deletado == False,
                ExtratoCreditoFreteiroModel.ativo == True,
                ExtratoCreditoFreteiroModel.transportadora_id == transportadora_id,
                # Removido filtro tipo_movimentacao para incluir tanto créditos quanto débitos
                ExtratoCreditoFreteiroModel.credito_utilizado == False  # Apenas créditos não utilizados
            ).order_by(ExtratoCreditoFreteiroModel.data_movimentacao.desc()).all()
            
            creditos_formatados = []
            for credito in creditos:
                creditos_formatados.append({
                    'id': credito.id,
                    'data_movimentacao': credito.data_movimentacao.strftime('%d/%m/%Y'),
                    'descricao': credito.descricao,
                    'valor_credito_100': credito.valor_credito_100,
                    'valor_formatado': f"R$ {credito.valor_credito_100 / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                })
            
            return creditos_formatados
        except Exception as e:
            print(f"[ERROR obter_creditos_disponiveis_transportadora] {e}")
            return []

