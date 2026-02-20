from datetime import datetime
from sqlalchemy import desc
from ...base_model import BaseModel, db
from .transacao_credito_model import TipoPessoa


class FaturamentoCreditoVinculoModel(BaseModel):
    """
    Model para vincular transações de crédito a faturamentos.
    
    Substitui o campo JSON `detalhes_json.credito_fornecedor[]`, 
    `detalhes_json.credito_transportadora[]` e `detalhes_json.credito_extrator[]`
    do FaturamentoModel por relacionamentos normalizados.
    
    Benefícios:
    - Queries SQL diretas (JOIN) em vez de busca em JSON
    - Integridade referencial garantida via FK
    - Performance otimizada com índices
    - Facilita relatórios e auditoria
    """
    __tablename__ = 'cre_faturamento_credito_vinculo'
    
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    
    faturamento_id = db.Column(db.Integer, db.ForeignKey("fin_faturamento.id"), nullable=False, index=True)
    faturamento = db.relationship("FaturamentoModel", backref=db.backref("vinculos_credito", lazy="dynamic"))
    
    transacao_credito_id = db.Column(db.Integer, db.ForeignKey("cre_transacao_credito.id"), nullable=True, index=True)
    transacao_credito = db.relationship("TransacaoCreditoModel", backref=db.backref("vinculos_faturamento", lazy="dynamic"))
    
    extrato_credito_fornecedor_id = db.Column(db.Integer, db.ForeignKey("ex_extrato_credito_fornecedor.id"), nullable=True)
    extrato_credito_fornecedor = db.relationship("ExtratoCreditoFornecedorModel", 
                                                  backref=db.backref("vinculos_faturamento", lazy="dynamic"))
    
    extrato_credito_freteiro_id = db.Column(db.Integer, db.ForeignKey("ex_extrato_credito_freteiro.id"), nullable=True)
    extrato_credito_freteiro = db.relationship("ExtratoCreditoFreteiroModel", 
                                                backref=db.backref("vinculos_faturamento", lazy="dynamic"))
    
    extrato_credito_extrator_id = db.Column(db.Integer, db.ForeignKey("ex_extrato_credito_extrator.id"), nullable=True)
    extrato_credito_extrator = db.relationship("ExtratoCreditoExtratorModel", 
                                                backref=db.backref("vinculos_faturamento", lazy="dynamic"))
    
    tipo_pessoa = db.Column(db.Integer, nullable=False, index=True)
    
    fornecedor_id = db.Column(db.Integer, db.ForeignKey("for_fornecedor_cadastro.id"), nullable=True, index=True)
    fornecedor = db.relationship("FornecedorCadastroModel", backref=db.backref("vinculos_credito_faturamento", lazy="dynamic"))
    
    transportadora_id = db.Column(db.Integer, db.ForeignKey("transp_transportadora.id"), nullable=True, index=True)
    transportadora = db.relationship("TransportadoraModel", backref=db.backref("vinculos_credito_faturamento", lazy="dynamic"))
    
    extrator_id = db.Column(db.Integer, db.ForeignKey("ext_extrator.id"), nullable=True, index=True)
    extrator = db.relationship("ExtratorModel", backref=db.backref("vinculos_credito_faturamento", lazy="dynamic"))
    
    valor_aplicado_100 = db.Column(db.Integer, nullable=False)
    
    data_vinculo = db.Column(db.DateTime, default=datetime.now, nullable=False)
    
    descricao = db.Column(db.String(500), nullable=True)
    
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    usuario = db.relationship('UsuarioModel', backref=db.backref('vinculos_credito_faturamento', lazy='dynamic'))
    
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    __table_args__ = (
        db.Index('idx_vinculo_faturamento_tipo', 'faturamento_id', 'tipo_pessoa'),
        db.Index('idx_vinculo_transacao', 'transacao_credito_id', 'ativo'),
        db.Index('idx_vinculo_pessoa', 'tipo_pessoa', 'fornecedor_id', 'transportadora_id', 'extrator_id'),
    )
    
    def __init__(
        self,
        faturamento_id: int,
        tipo_pessoa: int,
        valor_aplicado_100: int,
        usuario_id: int,
        transacao_credito_id: int = None,
        extrato_credito_fornecedor_id: int = None,
        extrato_credito_freteiro_id: int = None,
        extrato_credito_extrator_id: int = None,
        fornecedor_id: int = None,
        transportadora_id: int = None,
        extrator_id: int = None,
        descricao: str = None,
        ativo: bool = True
    ):
        self.faturamento_id = faturamento_id
        self.tipo_pessoa = tipo_pessoa
        self.valor_aplicado_100 = valor_aplicado_100
        self.usuario_id = usuario_id
        self.transacao_credito_id = transacao_credito_id
        self.extrato_credito_fornecedor_id = extrato_credito_fornecedor_id
        self.extrato_credito_freteiro_id = extrato_credito_freteiro_id
        self.extrato_credito_extrator_id = extrato_credito_extrator_id
        self.fornecedor_id = fornecedor_id
        self.transportadora_id = transportadora_id
        self.extrator_id = extrator_id
        self.descricao = descricao
        self.ativo = ativo
    
    
    def obter_pessoa_id(self) -> int:
        """Retorna o ID da pessoa conforme o tipo"""
        if self.tipo_pessoa == TipoPessoa.FORNECEDOR:
            return self.fornecedor_id
        elif self.tipo_pessoa == TipoPessoa.FRETEIRO:
            return self.transportadora_id
        elif self.tipo_pessoa == TipoPessoa.EXTRATOR:
            return self.extrator_id
        return None
    
    def obter_pessoa_nome(self) -> str:
        """Retorna o nome/identificação da pessoa"""
        if self.tipo_pessoa == TipoPessoa.FORNECEDOR and self.fornecedor:
            return self.fornecedor.identificacao
        elif self.tipo_pessoa == TipoPessoa.FRETEIRO and self.transportadora:
            return self.transportadora.identificacao
        elif self.tipo_pessoa == TipoPessoa.EXTRATOR and self.extrator:
            return self.extrator.identificacao
        return "N/A"
    
    def obter_tipo_pessoa_descricao(self) -> str:
        """Descrição legível do tipo de pessoa"""
        descricoes = {
            TipoPessoa.FORNECEDOR: "Fornecedor",
            TipoPessoa.FRETEIRO: "Transportadora",
            TipoPessoa.EXTRATOR: "Extrator"
        }
        return descricoes.get(self.tipo_pessoa, "Desconhecido")
    
    
    def buscar_por_faturamento(faturamento_id: int, tipo_pessoa: int = None) -> list:
        """
        Busca todos os vínculos de crédito de um faturamento.
        
        Args:
            faturamento_id: ID do faturamento
            tipo_pessoa: Filtrar por tipo de pessoa (opcional)
            
        Returns:
            Lista de vínculos
        """
        query = FaturamentoCreditoVinculoModel.query.filter(
            FaturamentoCreditoVinculoModel.faturamento_id == faturamento_id,
            FaturamentoCreditoVinculoModel.ativo == True
        )
        
        if tipo_pessoa:
            query = query.filter(FaturamentoCreditoVinculoModel.tipo_pessoa == tipo_pessoa)
        
        return query.all()
    
    def buscar_por_transacao_credito(transacao_credito_id: int) -> list:
        """
        Busca todos os faturamentos onde uma transação de crédito foi aplicada.
        
        Args:
            transacao_credito_id: ID da transação de crédito
            
        Returns:
            Lista de vínculos
        """
        return FaturamentoCreditoVinculoModel.query.filter(
            FaturamentoCreditoVinculoModel.transacao_credito_id == transacao_credito_id,
            FaturamentoCreditoVinculoModel.ativo == True
        ).order_by(desc(FaturamentoCreditoVinculoModel.data_vinculo)).all()
    
    def buscar_por_pessoa(tipo_pessoa: int, pessoa_id: int, faturamento_id: int = None) -> list:
        """
        Busca todos os vínculos de crédito de uma pessoa.
        
        Args:
            tipo_pessoa: TipoPessoa
            pessoa_id: ID da pessoa
            faturamento_id: Filtrar por faturamento (opcional)
            
        Returns:
            Lista de vínculos
        """
        if tipo_pessoa == TipoPessoa.FORNECEDOR:
            filtro_pessoa = FaturamentoCreditoVinculoModel.fornecedor_id == pessoa_id
        elif tipo_pessoa == TipoPessoa.FRETEIRO:
            filtro_pessoa = FaturamentoCreditoVinculoModel.transportadora_id == pessoa_id
        elif tipo_pessoa == TipoPessoa.EXTRATOR:
            filtro_pessoa = FaturamentoCreditoVinculoModel.extrator_id == pessoa_id
        else:
            return []
        
        query = FaturamentoCreditoVinculoModel.query.filter(
            filtro_pessoa,
            FaturamentoCreditoVinculoModel.tipo_pessoa == tipo_pessoa,
            FaturamentoCreditoVinculoModel.ativo == True
        )
        
        if faturamento_id:
            query = query.filter(FaturamentoCreditoVinculoModel.faturamento_id == faturamento_id)
        
        return query.order_by(desc(FaturamentoCreditoVinculoModel.data_vinculo)).all()
    
    def total_credito_aplicado_faturamento(faturamento_id: int, tipo_pessoa: int = None) -> int:
        """
        Calcula o total de créditos aplicados em um faturamento.
        
        Args:
            faturamento_id: ID do faturamento
            tipo_pessoa: Filtrar por tipo de pessoa (opcional)
            
        Returns:
            Total em centavos
        """
        from sqlalchemy import func
        
        query = db.session.query(
            func.coalesce(func.sum(FaturamentoCreditoVinculoModel.valor_aplicado_100), 0)
        ).filter(
            FaturamentoCreditoVinculoModel.faturamento_id == faturamento_id,
            FaturamentoCreditoVinculoModel.ativo == True
        )
        
        if tipo_pessoa:
            query = query.filter(FaturamentoCreditoVinculoModel.tipo_pessoa == tipo_pessoa)
        
        return query.scalar() or 0
    
    def criar_vinculo_fornecedor(faturamento_id: int, fornecedor_id: int, valor_aplicado_100: int,
                                  usuario_id: int, transacao_credito_id: int = None,
                                  extrato_credito_fornecedor_id: int = None, descricao: str = None) -> 'FaturamentoCreditoVinculoModel':
        """
        Cria vínculo de crédito de fornecedor.
        
        Helper method para facilitar criação de vínculos de fornecedor.
        """
        return FaturamentoCreditoVinculoModel(
            faturamento_id=faturamento_id,
            tipo_pessoa=TipoPessoa.FORNECEDOR,
            fornecedor_id=fornecedor_id,
            valor_aplicado_100=valor_aplicado_100,
            usuario_id=usuario_id,
            transacao_credito_id=transacao_credito_id,
            extrato_credito_fornecedor_id=extrato_credito_fornecedor_id,
            descricao=descricao
        )
    
    def criar_vinculo_transportadora(faturamento_id: int, transportadora_id: int, valor_aplicado_100: int,
                                      usuario_id: int, transacao_credito_id: int = None,
                                      extrato_credito_freteiro_id: int = None, descricao: str = None) -> 'FaturamentoCreditoVinculoModel':
        """
        Cria vínculo de crédito de transportadora.
        
        Helper method para facilitar criação de vínculos de transportadora.
        """
        return FaturamentoCreditoVinculoModel(
            faturamento_id=faturamento_id,
            tipo_pessoa=TipoPessoa.FRETEIRO,
            transportadora_id=transportadora_id,
            valor_aplicado_100=valor_aplicado_100,
            usuario_id=usuario_id,
            transacao_credito_id=transacao_credito_id,
            extrato_credito_freteiro_id=extrato_credito_freteiro_id,
            descricao=descricao
        )
    
    def criar_vinculo_extrator(faturamento_id: int, extrator_id: int, valor_aplicado_100: int,
                                usuario_id: int, transacao_credito_id: int = None,
                                extrato_credito_extrator_id: int = None, descricao: str = None) -> 'FaturamentoCreditoVinculoModel':
        """
        Cria vínculo de crédito de extrator.
        
        Helper method para facilitar criação de vínculos de extrator.
        """
        return FaturamentoCreditoVinculoModel(
            faturamento_id=faturamento_id,
            tipo_pessoa=TipoPessoa.EXTRATOR,
            extrator_id=extrator_id,
            valor_aplicado_100=valor_aplicado_100,
            usuario_id=usuario_id,
            transacao_credito_id=transacao_credito_id,
            extrato_credito_extrator_id=extrato_credito_extrator_id,
            descricao=descricao
        )
    
    def to_dict(self) -> dict:
        """Serializa vínculo para dicionário"""
        return {
            'id': self.id,
            'faturamento_id': self.faturamento_id,
            'transacao_credito_id': self.transacao_credito_id,
            'tipo_pessoa': self.tipo_pessoa,
            'tipo_pessoa_descricao': self.obter_tipo_pessoa_descricao(),
            'pessoa_id': self.obter_pessoa_id(),
            'pessoa_nome': self.obter_pessoa_nome(),
            'valor_aplicado_100': self.valor_aplicado_100,
            'data_vinculo': self.data_vinculo.strftime('%d/%m/%Y %H:%M:%S') if self.data_vinculo else None,
            'descricao': self.descricao,
            'usuario_id': self.usuario_id,
            'ativo': self.ativo
        }
    
    def __repr__(self):
        return f"<FaturamentoCreditoVinculoModel FAT:{self.faturamento_id} -> {self.tipo_pessoa_descricao} - R$ {self.valor_aplicado_100/100:.2f}>"
