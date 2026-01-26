from sistema._utilitarios import DataHora
from enum import IntEnum
from datetime import datetime
from sqlalchemy import desc, func, and_
from ...base_model import BaseModel, db
from sistema._utilitarios import *


class TipoTransacaoCredito(IntEnum):
    """Tipos de transação de crédito"""
    LANCAMENTO = 1      # Entrada de crédito (adiantamento)
    UTILIZACAO = 2      # Saída/consumo do crédito
    ESTORNO = 3         # Estorno de utilização (devolve crédito)
    CANCELAMENTO = 4    # Cancelamento de lançamento


class TipoPessoa(IntEnum):
    """Tipos de pessoa/terceiro"""
    FORNECEDOR = 1
    FRETEIRO = 2        
    EXTRATOR = 3


class TransacaoCreditoModel(BaseModel):
    """
    Model unificado para transações de crédito de terceiros.
    
    Centraliza o controle de créditos de fornecedores, freteiros e extratores
    em uma única tabela com rastreamento completo de origem e utilização.
    
    Benefícios:
    - Rastreamento direto de origem/destino via FK (sem busca em JSON)
    - Suporte a utilização parcial de créditos
    - Audit trail completo via HistoricoTransacaoCreditoModel
    - Queries otimizadas com índices apropriados
    """
    __tablename__ = 'cre_transacao_credito'
    
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    
    # === Identificação da Transação ===
    codigo_transacao = db.Column(db.String(20), unique=True, nullable=False, index=True)
    tipo_transacao = db.Column(db.Integer, nullable=False, index=True)  # TipoTransacaoCredito
    tipo_pessoa = db.Column(db.Integer, nullable=False, index=True)      # TipoPessoa
    
    # === Dados da Movimentação ===
    data_movimentacao = db.Column(db.Date, nullable=False, index=True)
    descricao = db.Column(db.String(500), nullable=False)
    observacao = db.Column(db.Text, nullable=True)
    tipo_valor = db.Column(db.String(10), nullable=True, default='positivo')  # 'positivo' ou 'negativo'
    
    # === Pessoa/Terceiro (apenas um será preenchido) ===
    fornecedor_id = db.Column(db.Integer, db.ForeignKey("for_fornecedor_cadastro.id"), nullable=True, index=True)
    fornecedor = db.relationship("FornecedorCadastroModel", backref=db.backref("transacoes_credito", lazy="dynamic"))
    
    transportadora_id = db.Column(db.Integer, db.ForeignKey("transp_transportadora.id"), nullable=True, index=True)
    transportadora = db.relationship("TransportadoraModel", backref=db.backref("transacoes_credito", lazy="dynamic"))
    
    extrator_id = db.Column(db.Integer, db.ForeignKey("ext_extrator.id"), nullable=True, index=True)
    extrator = db.relationship("ExtratorModel", backref=db.backref("transacoes_credito", lazy="dynamic"))
    
    # === Valores (em centavos) ===
    valor_original_100 = db.Column(db.Integer, nullable=False)
    valor_utilizado_100 = db.Column(db.Integer, default=0, nullable=False)
    
    # === Rastreamento de Origem ===
    # Transação que originou esta (para UTILIZACAO/ESTORNO/CANCELAMENTO)
    transacao_origem_id = db.Column(db.Integer, db.ForeignKey("cre_transacao_credito.id"), nullable=True, index=True)
    transacao_origem = db.relationship("TransacaoCreditoModel", remote_side=[id], backref=db.backref("transacoes_derivadas", lazy="dynamic"))
    
    # Faturamento que originou o lançamento de crédito
    faturamento_origem_id = db.Column(db.Integer, db.ForeignKey("fin_faturamento.id"), nullable=True, index=True)
    faturamento_origem = db.relationship("FaturamentoModel", foreign_keys=[faturamento_origem_id], backref=db.backref("creditos_lancados", lazy="dynamic"))
    
    # Pagamento onde o crédito foi utilizado
    pagamento_destino_id = db.Column(db.Integer, nullable=True, index=True)
    pagamento_destino_tipo = db.Column(db.String(50), nullable=True)  # 'fin_fornecedor_a_pagar', 'fin_frete_a_pagar', 'fin_extrator_a_pagar'
    
    # Faturamento onde o crédito foi aplicado
    faturamento_destino_id = db.Column(db.Integer, db.ForeignKey("fin_faturamento.id"), nullable=True, index=True)
    faturamento_destino = db.relationship("FaturamentoModel", foreign_keys=[faturamento_destino_id], backref=db.backref("creditos_aplicados", lazy="dynamic"))
    
    # === Conta Bancária (opcional) ===
    conta_bancaria_id = db.Column(db.Integer, db.ForeignKey("con_conta_bancaria.id"), nullable=True)
    conta_bancaria = db.relationship("ContaBancariaModel", backref=db.backref("transacoes_credito", lazy="dynamic"))
    
    # === Usuário responsável ===
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    usuario = db.relationship('UsuarioModel', backref=db.backref('transacoes_credito', lazy='dynamic'))
    
    # === Migração (referência ao registro legado) ===
    extrato_legado_id = db.Column(db.Integer, nullable=True)
    extrato_legado_tipo = db.Column(db.String(50), nullable=True)  # 'fornecedor', 'freteiro', 'extrator'
    
    # === Status ===
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    # === Índices compostos para queries frequentes ===
    __table_args__ = (
        db.Index('idx_transacao_pessoa_saldo', 'tipo_pessoa', 'fornecedor_id', 'transportadora_id', 'extrator_id', 'ativo'),
        db.Index('idx_transacao_data', 'data_movimentacao', 'tipo_transacao'),
        db.Index('idx_transacao_faturamento', 'faturamento_origem_id', 'faturamento_destino_id'),
    )
    
    def __init__(
        self,
        tipo_transacao: int,
        tipo_pessoa: int,
        data_movimentacao,
        descricao: str,
        valor_original_100: int,
        usuario_id: int,
        tipo_valor: str = 'positivo',
        fornecedor_id: int = None,
        transportadora_id: int = None,
        extrator_id: int = None,
        transacao_origem_id: int = None,
        faturamento_origem_id: int = None,
        faturamento_destino_id: int = None,
        pagamento_destino_id: int = None,
        pagamento_destino_tipo: str = None,
        conta_bancaria_id: int = None,
        observacao: str = None,
        valor_utilizado_100: int = 0,
        ativo: bool = True,
        extrato_legado_id: int = None,
        extrato_legado_tipo: str = None
    ):
        self.tipo_transacao = tipo_transacao
        self.tipo_pessoa = tipo_pessoa
        self.data_movimentacao = data_movimentacao
        self.descricao = descricao
        self.valor_original_100 = valor_original_100
        self.valor_utilizado_100 = valor_utilizado_100
        self.tipo_valor = tipo_valor
        self.usuario_id = usuario_id
        self.fornecedor_id = fornecedor_id
        self.transportadora_id = transportadora_id
        self.extrator_id = extrator_id
        self.transacao_origem_id = transacao_origem_id
        self.faturamento_origem_id = faturamento_origem_id
        self.faturamento_destino_id = faturamento_destino_id
        self.pagamento_destino_id = pagamento_destino_id
        self.pagamento_destino_tipo = pagamento_destino_tipo
        self.conta_bancaria_id = conta_bancaria_id
        self.observacao = observacao
        self.ativo = ativo
        self.extrato_legado_id = extrato_legado_id
        self.extrato_legado_tipo = extrato_legado_tipo
        
        # Gerar código de transação após definir tipo_pessoa
        self.codigo_transacao = self.gerar_codigo_transacao()
    
    # === Métodos de Instância ===
    
    def obter_saldo_disponivel_100(self):
        """Retorna o saldo disponível (positivo ou negativo) em centavos."""
        return self.valor_original_100 - self.valor_utilizado_100
    
    def verificar_credito_totalmente_utilizado(self):
        """Verifica se o crédito/débito foi completamente utilizado."""
        return self.obter_saldo_disponivel_100() == 0
    
    def obter_pessoa_id(self):
        """Retorna o ID da pessoa conforme o tipo"""
        if self.tipo_pessoa == TipoPessoa.FORNECEDOR:
            return self.fornecedor_id
        elif self.tipo_pessoa == TipoPessoa.FRETEIRO:
            return self.transportadora_id
        elif self.tipo_pessoa == TipoPessoa.EXTRATOR:
            return self.extrator_id
        return None
    
    def obter_pessoa_nome(self):
        """Retorna o nome/identificação da pessoa"""
        if self.tipo_pessoa == TipoPessoa.FORNECEDOR and self.fornecedor:
            return self.fornecedor.identificacao
        elif self.tipo_pessoa == TipoPessoa.FRETEIRO and self.transportadora:
            return self.transportadora.identificacao
        elif self.tipo_pessoa == TipoPessoa.EXTRATOR and self.extrator:
            return self.extrator.identificacao
        return "N/A"
    
    def obter_tipo_transacao_descricao(self):
        """Descrição legível do tipo de transação"""
        descricoes = {
            TipoTransacaoCredito.LANCAMENTO: "Lançamento",
            TipoTransacaoCredito.UTILIZACAO: "Utilização",
            TipoTransacaoCredito.ESTORNO: "Estorno",
            TipoTransacaoCredito.CANCELAMENTO: "Cancelamento"
        }
        return descricoes.get(self.tipo_transacao, "Desconhecido")
    
    def obter_tipo_pessoa_descricao(self):
        """Descrição legível do tipo de pessoa"""
        descricoes = {
            TipoPessoa.FORNECEDOR: "Fornecedor",
            TipoPessoa.FRETEIRO: "Transportadora",
            TipoPessoa.EXTRATOR: "Extrator"
        }
        return descricoes.get(self.tipo_pessoa, "Desconhecido")
    
    # === Métodos Estáticos (Queries) ===
    
    def gerar_codigo_transacao(self) -> str:
        """Gera código único para a transação no formato ADFOR-XXXXX, ADFRE-XXXXX, ADEXT-XXXXX"""
        prefixo = {
            TipoPessoa.FORNECEDOR: 'ADFOR',
            TipoPessoa.FRETEIRO: 'ADFRE',
            TipoPessoa.EXTRATOR: 'ADEXT'
        }.get(self.tipo_pessoa, 'ADGER')  # ADGER como fallback genérico
        
        # Busca último código com esse prefixo
        ultimo = TransacaoCreditoModel.query.filter(
            TransacaoCreditoModel.codigo_transacao.like(f'{prefixo}-%')
        ).order_by(desc(TransacaoCreditoModel.id)).first()
        
        if ultimo:
            try:
                ultimo_seq = int(ultimo.codigo_transacao.split('-')[-1])
                novo_seq = ultimo_seq + 1
            except (ValueError, IndexError):
                novo_seq = 1
        else:
            novo_seq = 1
        
        return f"{prefixo}-{novo_seq:05d}"
    
    def obter_saldo_pessoa(tipo_pessoa: int, pessoa_id: int) -> int:
        """
        Calcula o saldo total de créditos disponíveis para uma pessoa.
        Considera apenas créditos positivos (exclui débitos do saldo disponível).
        
        Args:
            tipo_pessoa: TipoPessoa (FORNECEDOR, FRETEIRO, EXTRATOR)
            pessoa_id: ID da pessoa
            
        Returns:
            Saldo total de créditos positivos disponíveis em centavos
        """
        filtro_pessoa = TransacaoCreditoModel._filtro_pessoa(tipo_pessoa, pessoa_id)
        
        # Soma apenas créditos positivos (valor_original_100 >= 0)
        # Débitos negativos são excluídos do saldo disponível
        resultado = db.session.query(
            func.coalesce(func.sum(TransacaoCreditoModel.valor_original_100 - TransacaoCreditoModel.valor_utilizado_100), 0)
        ).filter(
            filtro_pessoa,
            TransacaoCreditoModel.tipo_transacao == TipoTransacaoCredito.LANCAMENTO,
            TransacaoCreditoModel.ativo == True
        ).scalar()
        
        return resultado or 0
    
    def obter_creditos_disponiveis(tipo_pessoa: int, pessoa_id: int) -> list:
        """
        Busca todos os créditos/débitos com saldo disponível.
        
        Retorna tanto valores positivos (créditos) quanto negativos (débitos)
        que ainda não foram totalmente utilizados.
        
        Args:
            tipo_pessoa: TipoPessoa (FORNECEDOR, FRETEIRO, EXTRATOR)
            pessoa_id: ID da pessoa
            
        Returns:
            Lista de dicts contendo dados dos créditos/débitos disponíveis,
            ordenados por data de movimentação (FIFO)
        """
        filtro_pessoa = TransacaoCreditoModel._filtro_pessoa(tipo_pessoa, pessoa_id)
        
        creditos = TransacaoCreditoModel.query.filter(
            filtro_pessoa,
            TransacaoCreditoModel.tipo_transacao == TipoTransacaoCredito.LANCAMENTO,
            TransacaoCreditoModel.ativo == True,
            (TransacaoCreditoModel.valor_original_100 - TransacaoCreditoModel.valor_utilizado_100) != 0
        ).order_by(TransacaoCreditoModel.data_movimentacao.asc()).all()
        
        return [
            {
                'id': c.id,
                'codigo_transacao': c.codigo_transacao,
                'data_movimentacao': c.data_movimentacao.strftime('%d/%m/%Y'),
                'descricao': c.descricao,
                'valor_original_100': c.valor_original_100,
                'valor_utilizado_100': c.valor_utilizado_100,
                'saldo_disponivel_100': c.obter_saldo_disponivel_100(),
                'valor_credito_100': c.obter_saldo_disponivel_100(),  # Alias para compatibilidade com templates
                'valor_formatado': f"R$ {c.obter_saldo_disponivel_100() / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            }
            for c in creditos
        ]
    
    def obter_historico_pessoa(tipo_pessoa: int, pessoa_id: int, limite: int = None) -> list:
        """
        Busca histórico completo de transações de uma pessoa.
        
        Args:
            tipo_pessoa: TipoPessoa
            pessoa_id: ID da pessoa
            limite: Número máximo de registros (opcional)
            
        Returns:
            Lista de transações ordenadas por data desc
        """
        filtro_pessoa = TransacaoCreditoModel._filtro_pessoa(tipo_pessoa, pessoa_id)
        
        query = TransacaoCreditoModel.query.filter(
            filtro_pessoa,
            TransacaoCreditoModel.ativo == True
        ).order_by(desc(TransacaoCreditoModel.data_movimentacao), desc(TransacaoCreditoModel.id))
        
        if limite:
            query = query.limit(limite)
        
        return query.all()
    
    def _filtro_pessoa(tipo_pessoa: int, pessoa_id: int):
        """Retorna filtro SQLAlchemy para a pessoa"""
        if tipo_pessoa == TipoPessoa.FORNECEDOR:
            return and_(TransacaoCreditoModel.tipo_pessoa == tipo_pessoa, TransacaoCreditoModel.fornecedor_id == pessoa_id)
        elif tipo_pessoa == TipoPessoa.FRETEIRO:
            return and_(TransacaoCreditoModel.tipo_pessoa == tipo_pessoa, TransacaoCreditoModel.transportadora_id == pessoa_id)
        elif tipo_pessoa == TipoPessoa.EXTRATOR:
            return and_(TransacaoCreditoModel.tipo_pessoa == tipo_pessoa, TransacaoCreditoModel.extrator_id == pessoa_id)
        raise ValueError(f"Tipo de pessoa inválido: {tipo_pessoa}")
    
    # === Métodos de Instância (Operações) ===
    def utilizar_credito(self, valor_100: int, usuario_id: int, faturamento_destino_id: int = None,
                         pagamento_destino_id: int = None, pagamento_destino_tipo: str = None,
                         descricao: str = None) -> 'TransacaoCreditoModel':
        """
        Utiliza (parcial ou totalmente) este crédito.
        
        Args:
            valor_100: Valor a utilizar em centavos
            usuario_id: ID do usuário que está utilizando
            faturamento_destino_id: ID do faturamento onde será aplicado
            pagamento_destino_id: ID do pagamento específico
            pagamento_destino_tipo: Tipo da tabela de pagamento
            descricao: Descrição da utilização
            
        Returns:
            Nova transação de UTILIZACAO criada
        """
        saldo_atual = self.obter_saldo_disponivel_100()
        
        # Validação ajustada para suportar débitos (créditos negativos)
        # Para créditos positivos: valor_100 não pode exceder saldo_atual
        # Para débitos negativos: utilizar o valor absoluto disponível
        if saldo_atual >= 0:
            # Crédito positivo normal
            if valor_100 > saldo_atual:
                raise ValueError(f"Valor de utilização ({valor_100}) excede saldo disponível ({saldo_atual})")
        else:
            # Débito (saldo negativo) - validar pelo valor absoluto
            if valor_100 > abs(saldo_atual):
                raise ValueError(f"Valor de utilização ({valor_100}) excede débito disponível ({abs(saldo_atual)})")
        
        if self.tipo_transacao != TipoTransacaoCredito.LANCAMENTO:
            raise ValueError("Apenas créditos do tipo LANCAMENTO podem ser utilizados")
        
        # Atualiza valor utilizado mantendo o sinal correto
        # Para créditos positivos: soma valor positivo
        # Para débitos negativos: soma valor negativo
        if saldo_atual < 0:
            # Débito: valor_utilizado deve ser negativo também
            self.valor_utilizado_100 -= valor_100  # Subtrai para tornar mais negativo
        else:
            # Crédito normal: soma positivo
            self.valor_utilizado_100 += valor_100
        
        # Determinar o valor da utilização mantendo o sinal original
        # Se o crédito original é negativo (débito), a utilização também deve ser negativa
        valor_utilizacao = -valor_100 if saldo_atual < 0 else valor_100
        
        # Cria transação de utilização
        utilizacao = TransacaoCreditoModel(
            tipo_transacao=TipoTransacaoCredito.UTILIZACAO,
            tipo_pessoa=self.tipo_pessoa,
            data_movimentacao=datetime.now().date(),
            descricao=descricao or f"Acerto de adiantamento {self.descricao or self.codigo_transacao} - {DataHora.obter_data_atual_padrao_br()}",
            valor_original_100=valor_utilizacao,
            valor_utilizado_100=valor_utilizacao,  # Utilização já nasce "consumida"
            usuario_id=usuario_id,
            fornecedor_id=self.fornecedor_id,
            transportadora_id=self.transportadora_id,
            extrator_id=self.extrator_id,
            transacao_origem_id=self.id,
            faturamento_destino_id=faturamento_destino_id,
            pagamento_destino_id=pagamento_destino_id,
            pagamento_destino_tipo=pagamento_destino_tipo
        )
        
        db.session.add(utilizacao)
        return utilizacao
    
    def estornar(self, usuario_id: int, descricao: str = None) -> 'TransacaoCreditoModel':
        """
        Estorna uma utilização de crédito, devolvendo o valor ao crédito original.
        
        Args:
            usuario_id: ID do usuário que está estornando
            descricao: Motivo do estorno
            
        Returns:
            Nova transação de ESTORNO criada
        """
        if self.tipo_transacao != TipoTransacaoCredito.UTILIZACAO:
            raise ValueError("Apenas transações de UTILIZACAO podem ser estornadas")
        
        # Devolve valor ao crédito original
        if self.transacao_origem:
            self.transacao_origem.valor_utilizado_100 -= self.valor_original_100
        
        # Cria transação de estorno (mantém a mesma data da utilização)
        estorno = TransacaoCreditoModel(
            tipo_transacao=TipoTransacaoCredito.ESTORNO,
            tipo_pessoa=self.tipo_pessoa,
            data_movimentacao=self.data_movimentacao,
            descricao=descricao or f"Estorno da utilização {self.codigo_transacao}",
            valor_original_100=self.valor_original_100,
            valor_utilizado_100=self.valor_original_100,
            usuario_id=usuario_id,
            fornecedor_id=self.fornecedor_id,
            transportadora_id=self.transportadora_id,
            extrator_id=self.extrator_id,
            transacao_origem_id=self.id
        )
        
        # Marca utilização original como inativa
        self.ativo = False
        
        db.session.add(estorno)
        return estorno
    
    def cancelar(self, usuario_id: int, descricao: str = None) -> 'TransacaoCreditoModel':
        """
        Cancela um lançamento de crédito.
        
        Args:
            usuario_id: ID do usuário que está cancelando
            descricao: Motivo do cancelamento
            
        Returns:
            Nova transação de CANCELAMENTO criada
        """
        if self.tipo_transacao != TipoTransacaoCredito.LANCAMENTO:
            raise ValueError("Apenas transações de LANCAMENTO podem ser canceladas")
        
        if self.valor_utilizado_100 > 0:
            raise ValueError(f"Crédito já possui {self.valor_utilizado_100} centavos utilizados. Estorne as utilizações primeiro.")
        
        # Cria transação de cancelamento
        cancelamento = TransacaoCreditoModel(
            tipo_transacao=TipoTransacaoCredito.CANCELAMENTO,
            tipo_pessoa=self.tipo_pessoa,
            data_movimentacao=datetime.now().date(),
            descricao=descricao or f"Cancelamento do crédito {self.codigo_transacao}",
            valor_original_100=self.valor_original_100,
            valor_utilizado_100=self.valor_original_100,
            usuario_id=usuario_id,
            fornecedor_id=self.fornecedor_id,
            transportadora_id=self.transportadora_id,
            extrator_id=self.extrator_id,
            transacao_origem_id=self.id
        )
        
        # Marca lançamento original como inativo
        self.ativo = False
        
        db.session.add(cancelamento)
        return cancelamento
    
    # === Métodos de Compatibilidade com Sistema Legado ===
    
    @classmethod
    def obter_creditos_disponiveis_fornecedor(cls, fornecedor_id: int) -> list:
        """Compatibilidade: replica interface do ExtratoCreditoFornecedorModel"""
        return cls.obter_creditos_disponiveis(TipoPessoa.FORNECEDOR, fornecedor_id)
    
    @classmethod
    def obter_creditos_disponiveis_transportadora(cls, transportadora_id: int) -> list:
        """Compatibilidade: replica interface do ExtratoCreditoFreteiroModel"""
        return cls.obter_creditos_disponiveis(TipoPessoa.FRETEIRO, transportadora_id)
    
    @classmethod
    def obter_creditos_disponiveis_extrator(cls, extrator_id: int) -> list:
        """Compatibilidade: replica interface do ExtratoCreditoExtratorModel"""
        return cls.obter_creditos_disponiveis(TipoPessoa.EXTRATOR, extrator_id)
    
    @classmethod
    def soma_valor_credito_disponivel_fornecedor(cls, fornecedor_id: int) -> int:
        """Compatibilidade: soma créditos disponíveis de fornecedor"""
        return cls.obter_saldo_pessoa(TipoPessoa.FORNECEDOR, fornecedor_id)
    
    @classmethod
    def soma_valor_credito_disponivel_transportadora(cls, transportadora_id: int) -> int:
        """Compatibilidade: soma créditos disponíveis de transportadora"""
        return cls.obter_saldo_pessoa(TipoPessoa.FRETEIRO, transportadora_id)
    
    @classmethod
    def soma_valor_credito_disponivel_extrator(cls, extrator_id: int) -> int:
        """Compatibilidade: soma créditos disponíveis de extrator"""
        return cls.obter_saldo_pessoa(TipoPessoa.EXTRATOR, extrator_id)
    
    @classmethod
    def listagem_historico_por_fornecedor(cls, fornecedor_id: int) -> list:
        """Compatibilidade: histórico de fornecedor"""
        return cls.obter_historico_pessoa(TipoPessoa.FORNECEDOR, fornecedor_id)
    
    @classmethod
    def listagem_historico_por_freteiro(cls, transportadora_id: int) -> list:
        """Compatibilidade: histórico de transportadora"""
        return cls.obter_historico_pessoa(TipoPessoa.FRETEIRO, transportadora_id)
    
    @classmethod
    def listagem_historico_por_extrator(cls, extrator_id: int) -> list:
        """Compatibilidade: histórico de extrator"""
        return cls.obter_historico_pessoa(TipoPessoa.EXTRATOR, extrator_id)
    
    def to_dict(self) -> dict:
        """Serializa transação para dicionário"""
        return {
            'id': self.id,
            'codigo_transacao': self.codigo_transacao,
            'tipo_transacao': self.tipo_transacao,
            'tipo_transacao_descricao': self.obter_tipo_transacao_descricao(),
            'tipo_pessoa': self.tipo_pessoa,
            'tipo_pessoa_descricao': self.obter_tipo_pessoa_descricao(),
            'pessoa_id': self.obter_pessoa_id(),
            'pessoa_nome': self.obter_pessoa_nome(),
            'data_movimentacao': self.data_movimentacao.strftime('%d/%m/%Y') if self.data_movimentacao else None,
            'descricao': self.descricao,
            'tipo_valor': self.tipo_valor,
            'valor_original_100': self.valor_original_100,
            'valor_utilizado_100': self.valor_utilizado_100,
            'saldo_disponivel_100': self.obter_saldo_disponivel_100(),
            'transacao_origem_id': self.transacao_origem_id,
            'faturamento_origem_id': self.faturamento_origem_id,
            'faturamento_destino_id': self.faturamento_destino_id,
            'usuario_id': self.usuario_id,
            'data_cadastro': self.data_cadastro.strftime('%d/%m/%Y %H:%M:%S') if self.data_cadastro else None,
            'ativo': self.ativo
        }
    
    def __repr__(self):
        return f"<TransacaoCreditoModel {self.codigo_transacao} - {self.tipo_transacao_descricao} - R$ {self.valor_original_100/100:.2f}>"
