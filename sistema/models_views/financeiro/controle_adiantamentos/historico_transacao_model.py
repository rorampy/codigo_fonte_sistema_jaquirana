from enum import IntEnum
from datetime import datetime
import json
from sqlalchemy import desc, event
from ...base_model import BaseModel, db


class AcaoHistoricoCredito(IntEnum):
    """Tipos de ação no histórico"""
    CRIACAO = 1
    UTILIZACAO_PARCIAL = 2
    UTILIZACAO_TOTAL = 3
    ESTORNO = 4
    CANCELAMENTO = 5
    ALTERACAO = 6
    REATIVACAO = 7
    INATIVACAO = 8


class HistoricoTransacaoCreditoModel(BaseModel):
    """
    Model para registro de histórico/audit trail de transações de crédito.
    
    Registra automaticamente cada operação realizada nas transações de crédito,
    mantendo snapshot do estado completo para auditoria e compliance.
    
    Benefícios:
    - Rastreabilidade total de alterações
    - Snapshot do estado em cada momento
    - Identificação do usuário responsável por cada ação
    - Suporte a auditoria e compliance
    - Facilita debug e resolução de problemas
    """
    __tablename__ = 'cre_historico_transacao_credito'
    
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    
    transacao_credito_id = db.Column(db.Integer, db.ForeignKey("cre_transacao_credito.id"), nullable=False, index=True)
    transacao_credito = db.relationship("TransacaoCreditoModel", backref=db.backref("historico", lazy="dynamic"))
    
    acao = db.Column(db.Integer, nullable=False, index=True)
    
    valor_original_anterior_100 = db.Column(db.Integer, nullable=True)
    valor_original_posterior_100 = db.Column(db.Integer, nullable=True)
    valor_utilizado_anterior_100 = db.Column(db.Integer, nullable=True)
    valor_utilizado_posterior_100 = db.Column(db.Integer, nullable=True)
    saldo_anterior_100 = db.Column(db.Integer, nullable=True)
    saldo_posterior_100 = db.Column(db.Integer, nullable=True)
    
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    usuario = db.relationship('UsuarioModel', backref=db.backref('historico_transacoes_credito', lazy='dynamic'))
    
    data_hora = db.Column(db.DateTime, default=datetime.now, nullable=False, index=True)
    
    descricao = db.Column(db.String(500), nullable=True)
    motivo = db.Column(db.String(500), nullable=True)
    
    snapshot_json = db.Column(db.JSON, nullable=True)
    
    faturamento_relacionado_id = db.Column(db.Integer, db.ForeignKey("fin_faturamento.id"), nullable=True)
    faturamento_relacionado = db.relationship("FaturamentoModel", backref=db.backref("historico_creditos", lazy="dynamic"))
    
    __table_args__ = (
        db.Index('idx_historico_transacao_data', 'transacao_credito_id', 'data_hora'),
        db.Index('idx_historico_acao_data', 'acao', 'data_hora'),
        db.Index('idx_historico_usuario', 'usuario_id', 'data_hora'),
    )
    
    def __init__(
        self,
        transacao_credito_id: int,
        acao: int,
        usuario_id: int,
        valor_original_anterior_100: int = None,
        valor_original_posterior_100: int = None,
        valor_utilizado_anterior_100: int = None,
        valor_utilizado_posterior_100: int = None,
        saldo_anterior_100: int = None,
        saldo_posterior_100: int = None,
        descricao: str = None,
        motivo: str = None,
        snapshot_json: dict = None,
        faturamento_relacionado_id: int = None
    ):
        self.transacao_credito_id = transacao_credito_id
        self.acao = acao
        self.usuario_id = usuario_id
        self.valor_original_anterior_100 = valor_original_anterior_100
        self.valor_original_posterior_100 = valor_original_posterior_100
        self.valor_utilizado_anterior_100 = valor_utilizado_anterior_100
        self.valor_utilizado_posterior_100 = valor_utilizado_posterior_100
        self.saldo_anterior_100 = saldo_anterior_100
        self.saldo_posterior_100 = saldo_posterior_100
        self.descricao = descricao
        self.motivo = motivo
        self.snapshot_json = snapshot_json
        self.faturamento_relacionado_id = faturamento_relacionado_id
    
    
    def obter_acao_descricao(self):
        """Descrição legível da ação"""
        descricoes = {
            AcaoHistoricoCredito.CRIACAO: "Criação",
            AcaoHistoricoCredito.UTILIZACAO_PARCIAL: "Utilização Parcial",
            AcaoHistoricoCredito.UTILIZACAO_TOTAL: "Utilização Total",
            AcaoHistoricoCredito.ESTORNO: "Estorno",
            AcaoHistoricoCredito.CANCELAMENTO: "Cancelamento",
            AcaoHistoricoCredito.ALTERACAO: "Alteração",
            AcaoHistoricoCredito.REATIVACAO: "Reativação",
            AcaoHistoricoCredito.INATIVACAO: "Inativação"
        }
        return descricoes.get(self.acao, "Desconhecida")
    
    def obter_variacao_saldo_100(self):
        """Calcula variação no saldo (positivo = aumento, negativo = redução)"""
        if self.saldo_anterior_100 is not None and self.saldo_posterior_100 is not None:
            return self.saldo_posterior_100 - self.saldo_anterior_100
        return 0
    
    
    def buscar_por_transacao(transacao_credito_id: int, limite: int = None) -> list:
        """
        Busca histórico de uma transação específica.
        
        Args:
            transacao_credito_id: ID da transação
            limite: Número máximo de registros (opcional)
            
        Returns:
            Lista de registros de histórico ordenados por data desc
        """
        query = HistoricoTransacaoCreditoModel.query.filter(
            HistoricoTransacaoCreditoModel.transacao_credito_id == transacao_credito_id
        ).order_by(desc(HistoricoTransacaoCreditoModel.data_hora))
        
        if limite:
            query = query.limit(limite)
        
        return query.all()
    
    def buscar_por_usuario(usuario_id: int, data_inicio=None, data_fim=None, limite: int = None) -> list:
        """
        Busca histórico de ações de um usuário.
        
        Args:
            usuario_id: ID do usuário
            data_inicio: Data inicial (opcional)
            data_fim: Data final (opcional)
            limite: Número máximo de registros (opcional)
            
        Returns:
            Lista de registros de histórico
        """
        query = HistoricoTransacaoCreditoModel.query.filter(
            HistoricoTransacaoCreditoModel.usuario_id == usuario_id
        )
        
        if data_inicio:
            query = query.filter(HistoricoTransacaoCreditoModel.data_hora >= data_inicio)
        if data_fim:
            query = query.filter(HistoricoTransacaoCreditoModel.data_hora <= data_fim)
        
        query = query.order_by(desc(HistoricoTransacaoCreditoModel.data_hora))
        
        if limite:
            query = query.limit(limite)
        
        return query.all()
    
    def buscar_por_acao(acao: int, data_inicio=None, data_fim=None, limite: int = None) -> list:
        """
        Busca histórico por tipo de ação.
        
        Args:
            acao: AcaoHistoricoCredito
            data_inicio: Data inicial (opcional)
            data_fim: Data final (opcional)
            limite: Número máximo de registros (opcional)
            
        Returns:
            Lista de registros de histórico
        """
        query = HistoricoTransacaoCreditoModel.query.filter(
            HistoricoTransacaoCreditoModel.acao == acao
        )
        
        if data_inicio:
            query = query.filter(HistoricoTransacaoCreditoModel.data_hora >= data_inicio)
        if data_fim:
            query = query.filter(HistoricoTransacaoCreditoModel.data_hora <= data_fim)
        
        query = query.order_by(desc(HistoricoTransacaoCreditoModel.data_hora))
        
        if limite:
            query = query.limit(limite)
        
        return query.all()
    
    def registrar_criacao(transacao, usuario_id: int) -> 'HistoricoTransacaoCreditoModel':
        """
        Registra criação de uma nova transação de crédito.
        
        Args:
            transacao: Instância de TransacaoCreditoModel
            usuario_id: ID do usuário
            
        Returns:
            Registro de histórico criado
        """
        historico = HistoricoTransacaoCreditoModel(
            transacao_credito_id=transacao.id,
            acao=AcaoHistoricoCredito.CRIACAO,
            usuario_id=usuario_id,
            valor_original_posterior_100=transacao.valor_original_100,
            valor_utilizado_posterior_100=0,
            saldo_posterior_100=transacao.valor_original_100,
            descricao=f"Crédito criado: {transacao.descricao}",
            snapshot_json=transacao.to_dict() if hasattr(transacao, 'to_dict') else None,
            faturamento_relacionado_id=transacao.faturamento_origem_id
        )
        
        db.session.add(historico)
        return historico
    
    def registrar_utilizacao(transacao, valor_utilizado_100: int, usuario_id: int,
                             faturamento_id: int = None, descricao: str = None) -> 'HistoricoTransacaoCreditoModel':
        """
        Registra utilização (parcial ou total) de um crédito.
        
        Args:
            transacao: Instância de TransacaoCreditoModel
            valor_utilizado_100: Valor utilizado nesta operação
            usuario_id: ID do usuário
            faturamento_id: ID do faturamento onde foi aplicado (opcional)
            descricao: Descrição personalizada (opcional)
            
        Returns:
            Registro de histórico criado
        """
        is_debito = transacao.valor_original_100 < 0
        
        if is_debito:
            valor_utilizado_anterior = transacao.valor_utilizado_100 + valor_utilizado_100
        else:
            valor_utilizado_anterior = transacao.valor_utilizado_100 - valor_utilizado_100
        
        saldo_anterior = transacao.valor_original_100 - valor_utilizado_anterior
        saldo_posterior = transacao.obter_saldo_disponivel_100()
        
        acao = AcaoHistoricoCredito.UTILIZACAO_TOTAL if saldo_posterior == 0 else AcaoHistoricoCredito.UTILIZACAO_PARCIAL
        
        historico = HistoricoTransacaoCreditoModel(
            transacao_credito_id=transacao.id,
            acao=acao,
            usuario_id=usuario_id,
            valor_original_anterior_100=transacao.valor_original_100,
            valor_original_posterior_100=transacao.valor_original_100,
            valor_utilizado_anterior_100=valor_utilizado_anterior,
            valor_utilizado_posterior_100=transacao.valor_utilizado_100,
            saldo_anterior_100=saldo_anterior,
            saldo_posterior_100=saldo_posterior,
            descricao=descricao or f"Utilização de R$ {valor_utilizado_100/100:.2f} do crédito",
            snapshot_json=transacao.to_dict() if hasattr(transacao, 'to_dict') else None,
            faturamento_relacionado_id=faturamento_id
        )
        
        db.session.add(historico)
        return historico
    
    def registrar_estorno(transacao, valor_estornado_100: int, usuario_id: int,
                          motivo: str = None) -> 'HistoricoTransacaoCreditoModel':
        """
        Registra estorno de uma utilização.
        
        Args:
            transacao: Instância de TransacaoCreditoModel
            valor_estornado_100: Valor estornado
            usuario_id: ID do usuário
            motivo: Motivo do estorno (opcional)
            
        Returns:
            Registro de histórico criado
        """
        valor_utilizado_anterior = transacao.valor_utilizado_100 + valor_estornado_100
        saldo_anterior = transacao.valor_original_100 - valor_utilizado_anterior
        
        historico = HistoricoTransacaoCreditoModel(
            transacao_credito_id=transacao.id,
            acao=AcaoHistoricoCredito.ESTORNO,
            usuario_id=usuario_id,
            valor_original_anterior_100=transacao.valor_original_100,
            valor_original_posterior_100=transacao.valor_original_100,
            valor_utilizado_anterior_100=valor_utilizado_anterior,
            valor_utilizado_posterior_100=transacao.valor_utilizado_100,
            saldo_anterior_100=saldo_anterior,
            saldo_posterior_100=transacao.obter_saldo_disponivel_100(),
            descricao=f"Estorno de R$ {valor_estornado_100/100:.2f}",
            motivo=motivo,
            snapshot_json=transacao.to_dict() if hasattr(transacao, 'to_dict') else None
        )
        
        db.session.add(historico)
        return historico
    
    def registrar_cancelamento(transacao, usuario_id: int, motivo: str = None) -> 'HistoricoTransacaoCreditoModel':
        """
        Registra cancelamento de um crédito.
        
        Args:
            transacao: Instância de TransacaoCreditoModel
            usuario_id: ID do usuário
            motivo: Motivo do cancelamento (opcional)
            
        Returns:
            Registro de histórico criado
        """
        historico = HistoricoTransacaoCreditoModel(
            transacao_credito_id=transacao.id,
            acao=AcaoHistoricoCredito.CANCELAMENTO,
            usuario_id=usuario_id,
            valor_original_anterior_100=transacao.valor_original_100,
            valor_original_posterior_100=transacao.valor_original_100,
            valor_utilizado_anterior_100=transacao.valor_utilizado_100,
            valor_utilizado_posterior_100=transacao.valor_utilizado_100,
            saldo_anterior_100=transacao.obter_saldo_disponivel_100(),
            saldo_posterior_100=0,
            descricao=f"Cancelamento do crédito {transacao.codigo_transacao}",
            motivo=motivo,
            snapshot_json=transacao.to_dict() if hasattr(transacao, 'to_dict') else None,
            faturamento_relacionado_id=transacao.faturamento_origem_id
        )
        
        db.session.add(historico)
        return historico
    
    def to_dict(self) -> dict:
        """Serializa histórico para dicionário"""
        return {
            'id': self.id,
            'transacao_credito_id': self.transacao_credito_id,
            'acao': self.acao,
            'acao_descricao': self.obter_acao_descricao(),
            'valor_original_anterior_100': self.valor_original_anterior_100,
            'valor_original_posterior_100': self.valor_original_posterior_100,
            'valor_utilizado_anterior_100': self.valor_utilizado_anterior_100,
            'valor_utilizado_posterior_100': self.valor_utilizado_posterior_100,
            'saldo_anterior_100': self.saldo_anterior_100,
            'saldo_posterior_100': self.saldo_posterior_100,
            'variacao_saldo_100': self.obter_variacao_saldo_100(),
            'usuario_id': self.usuario_id,
            'data_hora': self.data_hora.strftime('%d/%m/%Y %H:%M:%S') if self.data_hora else None,
            'descricao': self.descricao,
            'motivo': self.motivo,
            'faturamento_relacionado_id': self.faturamento_relacionado_id
        }
    
    def __repr__(self):
        return f"<HistoricoTransacaoCreditoModel {self.id} - {self.acao_descricao} - {self.data_hora}>"