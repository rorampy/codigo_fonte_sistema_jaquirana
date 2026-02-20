from ..base_model import BaseModel, db
from datetime import datetime


class ImportacaoOfx(BaseModel):
    """
    Model para armazenar transações importadas de arquivos OFX.
    
    Lógica de negócio, queries complexas e operações de conciliação
    estão centralizadas em ImportacaoOfxService (importacao_ofx_service.py).
    """
    
    __tablename__ = "im_importacao_ofx"
    
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    
    fitid = db.Column(db.String(50), nullable=False)
    refnum = db.Column(db.String(50), nullable=True)
    data_transacao = db.Column(db.Date, nullable=False)
    valor = db.Column(db.Numeric(15, 2), nullable=False)
    valor_formatado = db.Column(db.String(20), nullable=True)
    tipo_movimento = db.Column(db.String(10), nullable=False)
    memo = db.Column(db.Text, nullable=True)
    descricao_limpa = db.Column(db.Text, nullable=True)
    categoria_automatica = db.Column(db.String(100), nullable=True)
    
    arquivo_nome = db.Column(db.String(255), nullable=False)
    data_importacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    batch_importacao = db.Column(db.String(50), nullable=False, index=True)
    
    banco_id = db.Column(db.String(10), nullable=True)
    conta_id = db.Column(db.String(50), nullable=True)
    tipo_conta = db.Column(db.String(20), nullable=True)
    moeda = db.Column(db.String(3), nullable=True, default='BRL')
    
    instituicao_org = db.Column(db.String(100), nullable=True)
    instituicao_fid = db.Column(db.String(100), nullable=True)
    
    data_inicio_extrato = db.Column(db.String(10), nullable=True)
    data_fim_extrato = db.Column(db.String(10), nullable=True)
    
    processado = db.Column(db.Boolean, default=False, nullable=False)
    categoria_manual = db.Column(db.String(100), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)

    conciliado = db.Column(db.Boolean, default=False, nullable=False)
    tipo_conciliacao = db.Column(db.String(50), nullable=True)
    pagamento_id = db.Column(db.Integer, nullable=True)
    data_conciliacao = db.Column(db.DateTime, nullable=True)
    usuario_conciliacao_id = db.Column(db.Integer, nullable=True)
    observacoes_conciliacao = db.Column(db.Text, nullable=True)
    
    valor_utilizado_100 = db.Column(db.Integer, nullable=True)
    conciliacao_parcial = db.Column(db.Boolean, default=False)
    
    dados_conciliacao_json = db.Column(db.JSON, nullable=True)
    
    ofx_deletada = db.Column(db.Boolean, default=False, nullable=False)
    ofx_justificativa_deletada = db.Column(db.String(50), nullable=True)
    
    conta_bancaria_id = db.Column(db.Integer, db.ForeignKey("con_conta_bancaria.id"), nullable=True)
    conta_bancaria = db.relationship("ContaBancariaModel", foreign_keys=[conta_bancaria_id], backref=db.backref("transacoes_ofx", lazy=True))
    
    __table_args__ = (
        db.Index('idx_ofx_fitid', 'fitid'),
        db.Index('idx_ofx_data_transacao', 'data_transacao'),
        db.Index('idx_ofx_tipo_movimento', 'tipo_movimento'),
        db.Index('idx_ofx_data_importacao', 'data_importacao'),
        db.Index('idx_ofx_batch_importacao', 'batch_importacao'),
    )
    
    def __repr__(self):
        return f'<OfxTransacao {self.fitid}: {self.valor_formatado} - {self.descricao_limpa[:50] if self.descricao_limpa else self.memo[:50]}...>'
    

    @property
    def categoria_final(self):
        """Retorna a categoria final (manual tem prioridade sobre automática)"""
        return self.categoria_manual if self.categoria_manual else self.categoria_automatica
    
    @property
    def descricao_final(self):
        """Retorna a descrição final (limpa tem prioridade sobre memo)"""
        return self.descricao_limpa if self.descricao_limpa else self.memo
    
    @property
    def valor_disponivel(self):
        """Retorna o valor ainda disponível para conciliação"""
        valor_total = abs(self.valor) * 100
        valor_usado = self.valor_utilizado_100 or 0
        return (valor_total - valor_usado) / 100
    
    @property
    def valor_disponivel_100(self):
        """Retorna o valor ainda disponível em centavos"""
        valor_total = int(abs(self.valor) * 100)
        valor_usado = self.valor_utilizado_100 or 0
        return valor_total - valor_usado
    
    @property
    def percentual_utilizado(self):
        """Retorna o percentual já utilizado da transação"""
        valor_total = int(abs(self.valor) * 100)
        if valor_total == 0:
            return 0
        valor_usado = self.valor_utilizado_100 or 0
        return (valor_usado / valor_total) * 100
    
    @property
    def pode_conciliar_valor(self):
        """Verifica se ainda há valor disponível para conciliação"""
        return self.valor_disponivel_100 > 0
    
    @property
    def esta_totalmente_utilizada(self):
        """Verifica se a transação foi totalmente utilizada"""
        return self.valor_disponivel_100 <= 0
    

    def adicionar_valor_utilizado(self, valor_centavos):
        """
        Adiciona um valor ao total já utilizado.
        
        Args:
            valor_centavos (int): Valor em centavos para adicionar
            
        Returns:
            bool: True se adicionado com sucesso, False se exceder o valor total
        """
        if not isinstance(valor_centavos, int) or valor_centavos <= 0:
            return False
            
        valor_total_100 = int(abs(self.valor) * 100)
        novo_valor_utilizado = (self.valor_utilizado_100 or 0) + valor_centavos
        
        if novo_valor_utilizado > valor_total_100:
            return False
            
        self.valor_utilizado_100 = novo_valor_utilizado
        self.conciliacao_parcial = novo_valor_utilizado < valor_total_100
        
        if novo_valor_utilizado >= valor_total_100:
            self.conciliado = True
        
        return True
    
    def resetar_utilizacao(self):
        """Reset da utilização parcial"""
        self.valor_utilizado_100 = None
        self.conciliacao_parcial = False
        self.conciliado = False
        