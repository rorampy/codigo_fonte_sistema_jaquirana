from ....base_model import BaseModel, db
from sqlalchemy import desc

class ExtratoCreditoExtratorModel(BaseModel):
    """
    Model para aguardar créditos de extratores
    """
    __tablename__ = 'ex_extrato_credito_extrator'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    # 1 - Entrada | 2 - Saída | 3 - Cancelamento | 4 - Estorno
    tipo_movimentacao = db.Column(db.Integer, nullable=True)

    plano_conta_id = db.Column(db.Integer, db.ForeignKey("plan_plano_conta.id"), nullable=True)
    plano_conta = db.relationship("PlanoContaModel", foreign_keys=[plano_conta_id], backref=db.backref("plano_conta_extrator", lazy=True))

    categorizacao_fiscal_id = db.Column(db.Integer, db.ForeignKey("ca_categorizacao_fiscal.id"), nullable=True)
    categorizacao_fiscal = db.relationship("CategorizacaoFiscalModel", foreign_keys=[categorizacao_fiscal_id], backref=db.backref("categorizacao_fiscal_extrator", lazy=True))

    descricao = db.Column(db.String(255), nullable=False)
    data_movimentacao = db.Column(db.Date, nullable=False)

    extrator_id = db.Column(db.Integer, db.ForeignKey("ext_extrator.id"), nullable=False)
    extrator = db.relationship("ExtratorModel", backref=db.backref("extrator_credito", lazy=True))

    valor_credito_100 = db.Column(db.Integer, nullable=False)

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    usuario = db.relationship('UsuarioModel', backref=db.backref('usuario_credito_extrator', lazy=True))

    upload_documentacao_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    upload_documentacao = db.relationship("UploadArquivoModel", foreign_keys=[upload_documentacao_id], backref=db.backref("credito_documentacao", lazy=True))

    upload_comprovante_bancario_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    upload_comprovante_bancario = db.relationship("UploadArquivoModel", foreign_keys=[upload_comprovante_bancario_id], backref=db.backref("credito_comprovante_bancario", lazy=True))
    
    credito_utilizado = db.Column(db.Boolean, default=False, nullable=False)

    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(
            self, data_movimentacao, descricao, extrator_id, valor_credito_100, usuario_id, upload_comprovante_bancario_id=upload_comprovante_bancario_id, upload_documentacao_id=upload_documentacao_id,
            tipo_movimentacao=tipo_movimentacao, plano_conta_id=None, categorizacao_fiscal_id=None, credito_utilizado=None, ativo=True
    ):
        self.plano_conta_id = plano_conta_id
        self.categorizacao_fiscal_id = categorizacao_fiscal_id
        self.data_movimentacao = data_movimentacao
        self.descricao = descricao
        self.extrator_id = extrator_id
        self.valor_credito_100 = valor_credito_100
        self.usuario_id = usuario_id
        self.upload_comprovante_bancario_id = upload_comprovante_bancario_id
        self.upload_documentacao_id = upload_documentacao_id
        self.tipo_movimentacao = tipo_movimentacao
        self.credito_utilizado = credito_utilizado
        self.ativo = ativo
    
    def listagem_historico_por_extrator(id):
        extrato = ExtratoCreditoExtratorModel.query.filter(
            ExtratoCreditoExtratorModel.deletado == False,
            ExtratoCreditoExtratorModel.ativo == True,
            ExtratoCreditoExtratorModel.extrator_id == id
        ).order_by(desc(
            ExtratoCreditoExtratorModel.id
        )).all()

        return extrato
    
    
    def obter_creditos_disponiveis_extrator(extrator_id):
        """
        Busca todos os créditos individuais disponíveis para um extrator
        """
        try:
            creditos = ExtratoCreditoExtratorModel.query.filter(
                ExtratoCreditoExtratorModel.deletado == False,
                ExtratoCreditoExtratorModel.ativo == True,
                ExtratoCreditoExtratorModel.extrator_id == extrator_id,
                ExtratoCreditoExtratorModel.credito_utilizado == False,
            ).order_by(ExtratoCreditoExtratorModel.data_movimentacao.desc()).all()
            
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
            print(f"[ERROR obter_creditos_disponiveis_extrator] {e}")
            return []
