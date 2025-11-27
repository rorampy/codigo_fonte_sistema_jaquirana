from ....base_model import BaseModel, db
from sistema._utilitarios import *
from datetime import timedelta, date
from decimal import Decimal

# Import do modelo de anexos para o relacionamento
from .categorizacao_anexo_model import AgendamentoAnexoPagamentoModel

class AgendamentoPagamentoModel(BaseModel):
    __tablename__ = 'fin_agendamento_pagamento'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Relacionamento com faturamento
    faturamento_id = db.Column(db.Integer, db.ForeignKey('fin_faturamento.id'), nullable=True)
    faturamento = db.relationship('FaturamentoModel', backref=db.backref('agendamentos', lazy=True))
    
    # Relacionamento com lançamento
    lancamento_avulso_id = db.Column(db.Integer, db.ForeignKey('lan_lancamento_avulso.id'), nullable=True)
    lancamento_avulso = db.relationship('LancamentoAvulsoModel', backref=db.backref('lancamento_avulso', lazy=True))
    
    # Beneficiário (Pessoa Financeiro)
    pessoa_financeiro_id = db.Column(db.Integer, db.ForeignKey('pe_pessoa_financeiro.id'), nullable=False)
    pessoa_financeiro = db.relationship('PessoaFinanceiroModel', backref=db.backref('agendamentos_pagamento', lazy=True))
    
    conta_bancaria_id = db.Column(db.Integer, db.ForeignKey("con_conta_bancaria.id"), nullable=True)
    conta_bancaria = db.relationship("ContaBancariaModel", foreign_keys=[conta_bancaria_id], backref=db.backref("conta_bancaria_categorizacao", lazy=True))
    
    # Datas
    data_vencimento = db.Column(db.Date, nullable=False)
    data_competencia = db.Column(db.Date, nullable=True)
    
    # Informações básicas
    descricao = db.Column(db.String(255), nullable=True)
    referencia = db.Column(db.String(255), nullable=True)
    
    # MÚLTIPLAS CATEGORIAS E CENTROS DE CUSTO (JSON)
    categorias_json = db.Column(db.JSON, nullable=True)
    # [{"id": 1, "nome": "Venda de Madeira", "detalhamento": "..."}, ...]
    
    centros_custo_json = db.Column(db.JSON, nullable=True)
    # [{"id": 1, "nome": "Vendas", "percentual": 70.0}, {"id": 2, "nome": "Admin", "percentual": 30.0}]
    
    # Parcelamento
    parcelamento_ativo = db.Column(db.Boolean, default=False)
    numero_parcelas = db.Column(db.Integer, nullable=True)
    dias_entre_parcelas = db.Column(db.Integer, nullable=True, default=30)
    
    # Valores
    valor_total_100 = db.Column(db.Integer, nullable=False)  # Em centavos
    
    # Campos para conciliação parcial
    valor_conciliado_100 = db.Column(db.Integer,nullable=True)
    conciliacao_parcial = db.Column(db.Boolean, nullable=True, default=False)
    
    situacao_pagamento_id = db.Column(db.Integer, db.ForeignKey("fin_situacao_pagamento.id"), nullable=True)
    situacao = db.relationship("SituacaoPagamentoModel", backref=db.backref("agendamentos", lazy=True))
    
    # Controle
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(self, pessoa_financeiro_id, data_vencimento, valor_total_100, valor_conciliado_100=None, conciliacao_parcial=False, faturamento_id = None,  conta_bancaria_id=None, lancamento_avulso_id=None, descricao=None, referencia=None, data_competencia=None, categorias_json=None, centros_custo_json=None, parcelamento_ativo=False, numero_parcelas=None, dias_entre_parcelas=30, situacao_pagamento_id=None, ativo=True):
        self.faturamento_id = faturamento_id
        self.conta_bancaria_id = conta_bancaria_id
        self.pessoa_financeiro_id = pessoa_financeiro_id
        self.data_vencimento = data_vencimento
        self.valor_total_100 = valor_total_100
        self.valor_conciliado_100 = valor_conciliado_100
        self.conciliacao_parcial = conciliacao_parcial
        self.lancamento_avulso_id = lancamento_avulso_id
        self.descricao = descricao
        self.referencia = referencia
        self.data_competencia = data_competencia
        self.categorias_json = categorias_json
        self.centros_custo_json = centros_custo_json
        self.parcelamento_ativo = parcelamento_ativo
        self.numero_parcelas = numero_parcelas
        self.dias_entre_parcelas = dias_entre_parcelas
        self.situacao_pagamento_id = situacao_pagamento_id
        self.ativo = ativo
        
    @property
    def valor_conciliado(self):
        """Retorna o valor já conciliado em formato decimal"""
        return Decimal(self.valor_conciliado_100 or 0) / 100
    
    @property
    def valor_pendente_conciliacao(self):
        """Retorna o valor ainda pendente de conciliação"""
        return self.valor_total - self.valor_conciliado
    
    @property
    def valor_pendente_conciliacao_100(self):
        """Retorna o valor ainda pendente de conciliação em centavos"""
        return (self.valor_total_100 or 0) - (self.valor_conciliado_100 or 0)
    
    @property
    def percentual_conciliado(self):
        """Retorna o percentual já conciliado"""
        if not self.valor_total_100 or self.valor_total_100 == 0:
            return Decimal('0')
        return (Decimal(self.valor_conciliado_100 or 0) / Decimal(self.valor_total_100)) * 100
    
    @property
    def esta_totalmente_conciliado(self):
        """Verifica se o agendamento está totalmente conciliado"""
        return (self.valor_conciliado_100 or 0) >= (self.valor_total_100 or 0)
    
    @property
    def pode_conciliar_parcialmente(self):
        """Verifica se ainda pode receber conciliação parcial"""
        return (self.valor_conciliado_100 or 0) < (self.valor_total_100 or 0)
    
    def adicionar_valor_conciliado(self, valor_centavos):
        """
        Adiciona um valor ao total já conciliado
        
        Args:
            valor_centavos (int): Valor em centavos para adicionar
            
        Returns:
            bool: True se adicionado com sucesso, False se exceder o valor total
        """
        if not isinstance(valor_centavos, int) or valor_centavos <= 0:
            return False
            
        novo_total_conciliado = (self.valor_conciliado_100 or 0) + valor_centavos
        
        # Não permite conciliar mais que o valor total
        if novo_total_conciliado > (self.valor_total_100 or 0):
            return False
            
        self.valor_conciliado_100 = novo_total_conciliado
        self.conciliacao_parcial = novo_total_conciliado < (self.valor_total_100 or 0)
        
        return True
    
    def resetar_conciliacao(self):
        """Reset da conciliação parcial"""
        self.valor_conciliado_100 = 0
        self.conciliacao_parcial = False

    @staticmethod
    def listar_agendamentos():
        """
        Lista todos os agendamentos não deletados, ordenados por ID decrescente.
        
        Returns:
            list: Lista de objetos AgendamentoPagamentoModel não deletados
        """
        agendamentos = AgendamentoPagamentoModel.query.filter(
            AgendamentoPagamentoModel.deletado == 0,
        ).order_by(AgendamentoPagamentoModel.id.desc()).all()

        return agendamentos

    @staticmethod
    def listar_agendamentos_ativos():
        """
        Lista todos os agendamentos ativos e não deletados, ordenados por ID decrescente.
        
        Returns:
            list: Lista de objetos AgendamentoPagamentoModel ativos e não deletados
        """
        agendamentos = AgendamentoPagamentoModel.query.filter(
            AgendamentoPagamentoModel.deletado == 0,
            AgendamentoPagamentoModel.ativo == 1
        ).order_by(AgendamentoPagamentoModel.id.desc()).all()

        return agendamentos

    @staticmethod
    def listar_agendamentos_inativos():
        """
        Lista todos os agendamentos inativos (independente se deletados ou não).
        
        Returns:
            list: Lista de objetos AgendamentoPagamentoModel inativos
        """
        agendamentos = AgendamentoPagamentoModel.query.filter(
            AgendamentoPagamentoModel.ativo == False
        ).all()

        return agendamentos

    @staticmethod
    def listar_agendamentos_conciliacao_parcial():
        """
        Lista agendamentos que possuem conciliação parcial ativa.
        
        Returns:
            list: Lista de objetos AgendamentoPagamentoModel com conciliação parcial
        """
        agendamentos = AgendamentoPagamentoModel.query.filter(
            AgendamentoPagamentoModel.deletado == 0,
            AgendamentoPagamentoModel.ativo == 1,
            AgendamentoPagamentoModel.conciliacao_parcial == True
        ).order_by(AgendamentoPagamentoModel.id.desc()).all()

        return agendamentos

    @staticmethod
    def buscar_agendamentos_para_conciliacao_parcial(valor_centavos, margem_tolerancia=0):
        """
        Busca agendamentos que podem receber conciliação parcial para um valor específico.
        
        Args:
            valor_centavos (int): Valor em centavos para conciliar
            margem_tolerancia (int): Margem de tolerância em centavos
            
        Returns:
            list: Lista de agendamentos que podem receber o valor
        """
        agendamentos = AgendamentoPagamentoModel.query.filter(
            AgendamentoPagamentoModel.deletado == 0,
            AgendamentoPagamentoModel.ativo == 1,
            # Valor pendente deve ser >= valor a conciliar (com margem)
            (AgendamentoPagamentoModel.valor_total_100 - 
             db.func.coalesce(AgendamentoPagamentoModel.valor_conciliado_100, 0)) >= 
            (valor_centavos - margem_tolerancia)
        ).order_by(AgendamentoPagamentoModel.data_vencimento.asc()).all()

        return agendamentos

    @staticmethod
    def obter_agendamento_por_id(id):
        """
        Obtém um agendamento específico por ID, apenas se não estiver deletado.
        
        Args:
            id (int): ID do agendamento
        
        Returns:
            AgendamentoPagamentoModel: Objeto do agendamento encontrado ou None se não encontrar
        """
        agendamento = AgendamentoPagamentoModel.query.filter(
            AgendamentoPagamentoModel.id == id,
            AgendamentoPagamentoModel.deletado == 0
        ).first()

        return agendamento
    
    @staticmethod
    def obter_faturamento_por_id(id):
        """
        Obtém um faturamento específico por ID, apenas se não estiver deletado.

        Args:
            id (int): ID do faturamento

        Returns:
            FaturamentoModel: Objeto do faturamento encontrado ou None se não encontrar
        """
        agendamento = AgendamentoPagamentoModel.query.filter(
            AgendamentoPagamentoModel.faturamento_id == id,
            AgendamentoPagamentoModel.ativo == 1,
            AgendamentoPagamentoModel.deletado == 0
        ).first()

        return agendamento

    @staticmethod
    def obter_agendamentos_por_faturamento(faturamento_id):
        """
        Obtém todos os agendamentos de um faturamento específico.
        
        Args:
            faturamento_id (int): ID do faturamento
        
        Returns:
            list: Lista de objetos AgendamentoPagamentoModel do faturamento
        """
        agendamentos = AgendamentoPagamentoModel.query.filter(
            AgendamentoPagamentoModel.faturamento_id == faturamento_id,
            AgendamentoPagamentoModel.deletado == 0
        ).order_by(AgendamentoPagamentoModel.data_vencimento.asc()).all()

        return agendamentos

    @staticmethod
    def obter_agendamentos_por_lancamento(lancamento_avulso_id):
        """
        Obtém todos os agendamentos de um lançamento avulso específico.
        
        Args:
            lancamento_avulso_id (int): ID do lançamento avulso
        
        Returns:
            lançamento avulso
        """
        agendamentos = AgendamentoPagamentoModel.query.filter(
            AgendamentoPagamentoModel.lancamento_avulso_id == lancamento_avulso_id,
            AgendamentoPagamentoModel.deletado == 0,
            AgendamentoPagamentoModel.ativo == True
        ).first()

        return agendamentos

    @staticmethod
    def filtrar_agendamentos(
        pessoa_financeiro_id=None,
        data_vencimento_inicio=None,
        data_vencimento_fim=None,
        situacao_pagamento_id=None,
        descricao=None
    ):
        """
        Filtra agendamentos ativos por diversos critérios.
        
        Args:
            pessoa_financeiro_id (int, optional): ID da pessoa financeiro
            data_vencimento_inicio (date, optional): Data de vencimento inicial
            data_vencimento_fim (date, optional): Data de vencimento final
            situacao_pagamento_id (int, optional): ID da situação de pagamento
            descricao (str, optional): Descrição do agendamento
        
        Returns:
            list: Lista de objetos AgendamentoPagamentoModel que atendem aos critérios de filtro
        """
        query = AgendamentoPagamentoModel.query.filter(
            AgendamentoPagamentoModel.deletado == False,
            AgendamentoPagamentoModel.ativo == True
        )

        if pessoa_financeiro_id:
            query = query.filter(
                AgendamentoPagamentoModel.pessoa_financeiro_id == pessoa_financeiro_id
            )

        if data_vencimento_inicio:
            query = query.filter(
                AgendamentoPagamentoModel.data_vencimento >= data_vencimento_inicio
            )

        if data_vencimento_fim:
            query = query.filter(
                AgendamentoPagamentoModel.data_vencimento <= data_vencimento_fim
            )

        if situacao_pagamento_id:
            query = query.filter(
                AgendamentoPagamentoModel.situacao_pagamento_id == situacao_pagamento_id
            )

        if descricao:
            query = query.filter(
                AgendamentoPagamentoModel.descricao.ilike(f"%{descricao}%")
            )

        return query.order_by(AgendamentoPagamentoModel.data_vencimento.asc()).all()
    
    @staticmethod
    def buscar_sugestoes_ofx(valor, tipo_movimento, conta_bancaria_id=None):
        """
        Busca agendamentos que podem ser conciliados com uma transação OFX.
        """
        from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
        from sistema.models_views.financeiro.lancamento_avulso.lancamento_avulso_model import LancamentoAvulsoModel
        
        # Converter valor para centavos (sempre positivo)
        valor_centavos = abs(int(float(valor) * 100))
        valor_min = int(valor_centavos - 5)  # ±5 centavos
        valor_max = int(valor_centavos + 5)
        
        

        # Determinar tipo (1=receita, 2=despesa)
        eh_credito = tipo_movimento == 'CREDITO'
        direcao_faturamento = 1 if eh_credito else 2
        tipo_lancamento = 1 if eh_credito else 2
        
        # Query simples usando valor absoluto
        query = db.session.query(AgendamentoPagamentoModel).filter(
            db.func.abs(AgendamentoPagamentoModel.valor_total_100).between(valor_min, valor_max),
            AgendamentoPagamentoModel.ativo == True,
            AgendamentoPagamentoModel.deletado == False,
            AgendamentoPagamentoModel.situacao_pagamento_id != 8,  # Não conciliados
            AgendamentoPagamentoModel.situacao_pagamento_id != 9   # Não liquidados
        )
        
        # Filtrar por conta bancária se fornecida
        if conta_bancaria_id:
            query = query.filter(AgendamentoPagamentoModel.conta_bancaria_id == conta_bancaria_id)
        
        # JOINs para filtrar por tipo
        query = query.outerjoin(FaturamentoModel, AgendamentoPagamentoModel.faturamento_id == FaturamentoModel.id)\
                     .outerjoin(LancamentoAvulsoModel, AgendamentoPagamentoModel.lancamento_avulso_id == LancamentoAvulsoModel.id)
        
        # Filtrar por tipo de movimento
        query = query.filter(
            db.or_(
                # Faturamento do tipo correto
                db.and_(
                    AgendamentoPagamentoModel.faturamento_id.isnot(None),
                    FaturamentoModel.direcao_financeira == direcao_faturamento,
                    FaturamentoModel.ativo == True,
                    FaturamentoModel.deletado == False
                ),
                # Lançamento do tipo correto
                db.and_(
                    AgendamentoPagamentoModel.lancamento_avulso_id.isnot(None),
                    LancamentoAvulsoModel.tipo_movimentacao == tipo_lancamento,
                    LancamentoAvulsoModel.ativo == True,
                    LancamentoAvulsoModel.deletado == False
                )
            )
        )
        
        # Retornar resultados limitados
        return query.order_by(AgendamentoPagamentoModel.data_vencimento.asc()).limit(1).all()

    @staticmethod
    def buscar_sugestoes_conciliacao(valor_transacao=None, eh_credito=None):
        """
        Busca agendamentos que podem ser conciliados com uma transação bancária.
        
        Args:
            valor_transacao (int): Valor da transação em centavos
            eh_credito (bool): True se for crédito (entrada), False se for débito (saída)
        
        Returns:
            list: Lista de AgendamentoPagamentoModel que podem ser conciliados
        """
        # Valor já vem em centavos, aplicar margem de ±5 centavos
        valor_centavos = int(valor_transacao)  # Garantir que é inteiro
        margem = 5  # ±5 centavos
        valor_min = int(valor_centavos - margem)  # Converter para inteiro
        valor_max = int(valor_centavos + margem)  # Converter para inteiro
        
        # Determinar direção financeira
        # eh_credito = True  -> Recebimento -> direção 1 (Receber) ou tipo 1 (Receitas)
        # eh_credito = False -> Pagamento  -> direção 2 (Despesa) ou tipo 2 (Despesas)
        direcao_faturamento = 1 if eh_credito else 2
        tipo_lancamento = 1 if eh_credito else 2
        
        # Query base nos agendamentos
        query = db.session.query(AgendamentoPagamentoModel).filter(
            AgendamentoPagamentoModel.valor_total_100.between(valor_min, valor_max),
            AgendamentoPagamentoModel.ativo == True,
            AgendamentoPagamentoModel.deletado == False,
            AgendamentoPagamentoModel.situacao_pagamento_id != 8,  # Excluir totalmente conciliados
            AgendamentoPagamentoModel.situacao_pagamento_id != 9   # Excluir liquidados
            # Permite agendamentos com situacao_pagamento_id = 10 (parcialmente conciliados)
        )
        
        # Usar JOINs simples para filtrar por direção/tipo
        from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
        from sistema.models_views.financeiro.lancamento_avulso.lancamento_avulso_model import LancamentoAvulsoModel
        
        # Adicionar JOINs opcionais
        query = query.outerjoin(FaturamentoModel, AgendamentoPagamentoModel.faturamento_id == FaturamentoModel.id)\
                     .outerjoin(LancamentoAvulsoModel, AgendamentoPagamentoModel.lancamento_avulso_id == LancamentoAvulsoModel.id)
        
        # Filtrar por direção/tipo usando OR simples
        query = query.filter(
            db.or_(
                # Agendamento de faturamento com direção correta
                db.and_(
                    AgendamentoPagamentoModel.faturamento_id.isnot(None),
                    FaturamentoModel.direcao_financeira == direcao_faturamento,
                    FaturamentoModel.ativo == True,
                    FaturamentoModel.deletado == False
                ),
                # Agendamento de lançamento avulso com tipo correto
                db.and_(
                    AgendamentoPagamentoModel.lancamento_avulso_id.isnot(None),
                    LancamentoAvulsoModel.tipo_movimentacao == tipo_lancamento,
                    LancamentoAvulsoModel.ativo == True,
                    LancamentoAvulsoModel.deletado == False
                )
            )
        )
        
        # Ordenar por proximidade do valor e data de vencimento
        query_final = query.order_by(
            AgendamentoPagamentoModel.data_vencimento.asc()
        ).limit(10)
        
        agendamentos = query_final.all()  # Limitar a 10 sugestões
        
        return agendamentos
    
    @staticmethod
    def buscar_agendamentos_com_filtros(eh_credito, valor_min=None, valor_max=None, data_inicio=None, data_fim=None, categoria_id=None, beneficiario_id=None, descricao=None, conta_bancaria_id=None):
        """
        Busca agendamentos - por padrão lista os primeiros 30 registros, se houver filtros aplica apenas eles
        
        Args:
            eh_credito (bool): Se True busca receitas (direcao_financeira=1), se False busca despesas (direcao_financeira=2)
            valor_min (float, optional): Valor mínimo para filtrar
            valor_max (float, optional): Valor máximo para filtrar  
            data_inicio (str, optional): Data início no formato 'YYYY-MM-DD'
            data_fim (str, optional): Data fim no formato 'YYYY-MM-DD'
            categoria_id (int, optional): ID da categoria para filtrar
        
        Returns:
            List[AgendamentoPagamentoModel]: Lista de agendamentos encontrados
        """
        from datetime import datetime
        from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
        from sistema.models_views.financeiro.lancamento_avulso.lancamento_avulso_model import LancamentoAvulsoModel
        from sistema.models_views.gerenciar.pessoa_financeiro.pessoa_financeiro_model import PessoaFinanceiroModel
        
        # Query base otimizada - fazer JOINs apenas quando necessário
        query = db.session.query(AgendamentoPagamentoModel)\
            .filter(
                AgendamentoPagamentoModel.ativo == True,
                AgendamentoPagamentoModel.deletado == False,
                AgendamentoPagamentoModel.situacao_pagamento_id.notin_([8, 9, 10])  # Excluir totalmente conciliados e liquidados e descontos por antecipação
            )
        
        # Aplicar JOINs apenas quando necessário para filtrar por tipo
        if eh_credito:
            query = query.outerjoin(FaturamentoModel, AgendamentoPagamentoModel.faturamento_id == FaturamentoModel.id)\
                         .outerjoin(LancamentoAvulsoModel, AgendamentoPagamentoModel.lancamento_avulso_id == LancamentoAvulsoModel.id)\
                         .filter(
                             db.or_(
                                 db.and_(
                                     AgendamentoPagamentoModel.faturamento_id.isnot(None),
                                     FaturamentoModel.direcao_financeira == 1,
                                     FaturamentoModel.ativo == True,
                                     FaturamentoModel.deletado == False
                                 ),
                                 db.and_(
                                     AgendamentoPagamentoModel.lancamento_avulso_id.isnot(None),
                                     LancamentoAvulsoModel.tipo_movimentacao == 1,
                                     LancamentoAvulsoModel.ativo == True,
                                     LancamentoAvulsoModel.deletado == False
                                 )
                             )
                         )
        else:
            query = query.outerjoin(FaturamentoModel, AgendamentoPagamentoModel.faturamento_id == FaturamentoModel.id)\
                         .outerjoin(LancamentoAvulsoModel, AgendamentoPagamentoModel.lancamento_avulso_id == LancamentoAvulsoModel.id)\
                         .filter(
                             db.or_(
                                 db.and_(
                                     AgendamentoPagamentoModel.faturamento_id.isnot(None),
                                     FaturamentoModel.direcao_financeira == 2,
                                     FaturamentoModel.ativo == True,
                                     FaturamentoModel.deletado == False
                                 ),
                                 db.and_(
                                     AgendamentoPagamentoModel.lancamento_avulso_id.isnot(None),
                                     LancamentoAvulsoModel.tipo_movimentacao == 2,
                                     LancamentoAvulsoModel.ativo == True,
                                     LancamentoAvulsoModel.deletado == False
                                 )
                             )
                         )

        # Converter valores para float se necessário
        try:
            valor_min = float(valor_min) if valor_min is not None and str(valor_min).strip() != '' else None
        except (ValueError, TypeError):
            valor_min = None
            
        try:
            valor_max = float(valor_max) if valor_max is not None and str(valor_max).strip() != '' else None
        except (ValueError, TypeError):
            valor_max = None
            
        tem_filtros = any([
            valor_min is not None and valor_min > 0,
            valor_max is not None and valor_max > 0,
            data_inicio is not None and data_inicio != '',
            data_fim is not None and data_fim != '',
            categoria_id is not None and categoria_id != '' and str(categoria_id).isdigit() and int(categoria_id) > 0,
            beneficiario_id is not None and beneficiario_id != '' and str(beneficiario_id).isdigit() and int(beneficiario_id) > 0,
            descricao is not None and descricao.strip() != '',
            conta_bancaria_id is not None and str(conta_bancaria_id).isdigit() and int(conta_bancaria_id) > 0
        ])
        
        # Sempre aplicar filtro de conta bancária se fornecido
        if conta_bancaria_id is not None and str(conta_bancaria_id).isdigit() and int(conta_bancaria_id) > 0:
            query = query.filter(AgendamentoPagamentoModel.conta_bancaria_id == int(conta_bancaria_id))
            
        if tem_filtros:
            if valor_min is not None and valor_min > 0:
                valor_min_centavos = int(valor_min * 100)
                query = query.filter(db.func.abs(AgendamentoPagamentoModel.valor_total_100) >= valor_min_centavos)
            
            if valor_max is not None and valor_max > 0:
                valor_max_centavos = int(valor_max * 100)
                query = query.filter(db.func.abs(AgendamentoPagamentoModel.valor_total_100) <= valor_max_centavos)

            
            if data_inicio is not None and data_inicio != '':
                try:
                    from datetime import datetime
                    data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                    query = query.filter(AgendamentoPagamentoModel.data_vencimento >= data_inicio_obj)
                except ValueError as e:
                    print(f"Erro ao converter data_inicio: {data_inicio} - {e}")

            if data_fim is not None and data_fim != '':
                try:
                    from datetime import datetime
                    data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
                    query = query.filter(AgendamentoPagamentoModel.data_vencimento <= data_fim_obj)
                except ValueError as e:
                    print(f"Erro ao converter data_fim: {data_fim} - {e}")
           
            if categoria_id is not None:
                query = query.filter(
                    AgendamentoPagamentoModel.categorias_json.like(f'%{categoria_id}%')
                )
                
            if beneficiario_id is not None and beneficiario_id != '' and str(beneficiario_id).isdigit() and int(beneficiario_id) > 0:
                query = query.filter(
                    AgendamentoPagamentoModel.pessoa_financeiro_id == int(beneficiario_id)
                )
            
            # Filtro de descrição
            if descricao is not None and descricao.strip() != '':
                query = query.filter(
                    AgendamentoPagamentoModel.descricao.ilike(f'%{descricao.strip()}%')
                )
                            
            

        # Ordenar e limitar resultados para performance
        if tem_filtros:
            # Com filtros, buscar até 50 registros
            agendamentos = query.order_by(AgendamentoPagamentoModel.data_vencimento.desc()).limit(30).all()
        else:
            # Sem filtros, buscar apenas 15 registros mais recentes
            agendamentos = query.order_by(AgendamentoPagamentoModel.data_vencimento.desc()).limit(30).all()
        
        # Formatar agendamentos usando a mesma estrutura de obter_agendamentos_recentes_formatados
        return AgendamentoPagamentoModel._formatar_agendamentos_para_template(agendamentos)

    @staticmethod
    def listar_receitas_avulsas_agendamentos(pagina=1, por_pagina=200, termo_pesquisa=None, data_inicio=None, data_fim=None):
        """
        Lista agendamentos de receitas avulsas (faturamentos e lançamentos) com paginação e pesquisa.
        
        Args:
            pagina (int): Número da página (começa em 1)
            por_pagina (int): Quantidade de registros por página (padrão: 200)
            termo_pesquisa (str): Termo para pesquisa global (opcional)
            data_inicio (str): Data de início no formato YYYY-MM-DD (opcional)
            data_fim (str): Data de fim no formato YYYY-MM-DD (opcional)
        
        Returns:
            dict: Dicionário com 'agendamentos', 'total', 'pagina', 'por_pagina', 'total_paginas', 'termo_pesquisa'
        """
        from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
        from sistema.models_views.financeiro.lancamento_avulso.lancamento_avulso_model import LancamentoAvulsoModel
        from sistema.models_views.gerenciar.pessoa_financeiro.pessoa_financeiro_model import PessoaFinanceiroModel
        
        # Query base com filtros comuns e joins necessários para pesquisa
        base_query = db.session.query(AgendamentoPagamentoModel)\
            .join(
                FaturamentoModel,
                AgendamentoPagamentoModel.faturamento_id == FaturamentoModel.id,
                isouter=True
            )\
            .join(
                LancamentoAvulsoModel,
                AgendamentoPagamentoModel.lancamento_avulso_id == LancamentoAvulsoModel.id,
                isouter=True
            )\
            .join(
                PessoaFinanceiroModel,
                AgendamentoPagamentoModel.pessoa_financeiro_id == PessoaFinanceiroModel.id
            )\
            .filter(
                AgendamentoPagamentoModel.ativo == True,
                AgendamentoPagamentoModel.deletado == False,
                db.or_(
                    # Agendamento vem de faturamento com direção de receita
                    db.and_(
                        AgendamentoPagamentoModel.faturamento_id.isnot(None),
                        FaturamentoModel.direcao_financeira == 1  # Receitas
                    ),
                    # Agendamento vem de lançamento avulso de receita
                    db.and_(
                        AgendamentoPagamentoModel.lancamento_avulso_id.isnot(None),
                        LancamentoAvulsoModel.tipo_movimentacao == 1  # Receitas
                    )
                )
            )
        
        # Aplicar filtro de pesquisa se fornecido
        if termo_pesquisa and len(termo_pesquisa.strip()) >= 2:
            termo_pesquisa = termo_pesquisa.strip()
            base_query = base_query.filter(
                db.or_(
                    # Pesquisar na descrição do agendamento
                    AgendamentoPagamentoModel.descricao.ilike(f'%{termo_pesquisa}%'),
                    # Pesquisar na referência do agendamento
                    AgendamentoPagamentoModel.referencia.ilike(f'%{termo_pesquisa}%'),
                    # Pesquisar na identificação da pessoa financeiro
                    PessoaFinanceiroModel.identificacao.ilike(f'%{termo_pesquisa}%'),
                    # Pesquisar no código do faturamento
                    FaturamentoModel.codigo_faturamento.ilike(f'%{termo_pesquisa}%'),
                    # Pesquisar na descrição do lançamento avulso
                    LancamentoAvulsoModel.descricao.ilike(f'%{termo_pesquisa}%')
                )
            )

        # Aplicar filtros de data de vencimento (espera strings no formato YYYY-MM-DD)
        from datetime import datetime
        try:
            if data_inicio:
                dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                base_query = base_query.filter(AgendamentoPagamentoModel.data_vencimento >= dt_inicio)
            if data_fim:
                dt_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
                base_query = base_query.filter(AgendamentoPagamentoModel.data_vencimento <= dt_fim)
        except Exception:
            # Se houver erro no parse, ignorar filtro de data
            pass
        
        # Contar total de registros
        total_registros = base_query.count()
        
        # Calcular total de páginas
        import math
        total_paginas = math.ceil(total_registros / por_pagina) if total_registros > 0 else 1
        
        # Calcular offset
        offset = (pagina - 1) * por_pagina
        
        # Query para buscar os registros paginados
        agendamentos_query = base_query.order_by(AgendamentoPagamentoModel.id.desc())\
            .offset(offset)\
            .limit(por_pagina)
        
        # Executar a query
        agendamentos = agendamentos_query.all()
        
        return {
            'agendamentos': agendamentos,
            'total': total_registros,
            'pagina': pagina,
            'por_pagina': por_pagina,
            'total_paginas': total_paginas,
            'termo_pesquisa': termo_pesquisa
        }

    
    @staticmethod
    def listar_despesas_avulsas_agendamentos(pagina=1, por_pagina=200, termo_pesquisa=None, data_inicio=None, data_fim=None):
        """
        Lista agendamentos de despesas avulsas (faturamentos e lançamentos) com paginação e pesquisa.
        Retorna apenas os agendamentos que não foram conciliados nem liquidados.
        
        Args:
            pagina (int): Número da página (começa em 1)
            por_pagina (int): Quantidade de registros por página (padrão: 200)
            termo_pesquisa (str): Termo para pesquisa global (opcional)
        
        Returns:
            dict: Dicionário com 'agendamentos', 'total', 'pagina', 'por_pagina', 'total_paginas'
        """
        from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
        from sistema.models_views.financeiro.lancamento_avulso.lancamento_avulso_model import LancamentoAvulsoModel
        from sistema.models_views.gerenciar.pessoa_financeiro.pessoa_financeiro_model import PessoaFinanceiroModel
        
        # Query base com filtros comuns e joins necessários para pesquisa
        base_query = db.session.query(AgendamentoPagamentoModel)\
            .join(
                FaturamentoModel,
                AgendamentoPagamentoModel.faturamento_id == FaturamentoModel.id,
                isouter=True
            )\
            .join(
                LancamentoAvulsoModel,
                AgendamentoPagamentoModel.lancamento_avulso_id == LancamentoAvulsoModel.id,
                isouter=True
            )\
            .join(
                PessoaFinanceiroModel,
                AgendamentoPagamentoModel.pessoa_financeiro_id == PessoaFinanceiroModel.id
            )\
            .filter(
                AgendamentoPagamentoModel.ativo == True,
                AgendamentoPagamentoModel.deletado == False,
                db.or_(
                    # Agendamento vem de faturamento com direção de despesa
                    db.and_(
                        AgendamentoPagamentoModel.faturamento_id.isnot(None),
                        FaturamentoModel.direcao_financeira == 2  # Despesas
                    ),
                    # Agendamento vem de lançamento avulso de despesa
                    db.and_(
                        AgendamentoPagamentoModel.lancamento_avulso_id.isnot(None),
                        LancamentoAvulsoModel.tipo_movimentacao == 2  # Despesas
                    )
                )
            )
        
        # Aplicar filtro de pesquisa se fornecido
        if termo_pesquisa and len(termo_pesquisa.strip()) >= 2:
            termo_pesquisa = termo_pesquisa.strip()
            base_query = base_query.filter(
                db.or_(
                    # Pesquisar na descrição do agendamento
                    AgendamentoPagamentoModel.descricao.ilike(f'%{termo_pesquisa}%'),
                    # Pesquisar na referência do agendamento
                    AgendamentoPagamentoModel.referencia.ilike(f'%{termo_pesquisa}%'),
                    # Pesquisar na identificação da pessoa financeiro
                    PessoaFinanceiroModel.identificacao.ilike(f'%{termo_pesquisa}%'),
                    # Pesquisar no código do faturamento
                    FaturamentoModel.codigo_faturamento.ilike(f'%{termo_pesquisa}%'),
                    # Pesquisar na descrição do lançamento avulso
                    LancamentoAvulsoModel.descricao.ilike(f'%{termo_pesquisa}%')
                )
            )

        # Aplicar filtros de data de vencimento (espera strings no formato YYYY-MM-DD)
        from datetime import datetime
        try:
            if data_inicio:
                dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                base_query = base_query.filter(AgendamentoPagamentoModel.data_vencimento >= dt_inicio)
            if data_fim:
                dt_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
                base_query = base_query.filter(AgendamentoPagamentoModel.data_vencimento <= dt_fim)
        except Exception:
            # Se houver erro no parse, ignorar filtro de data
            pass
        
        # Contar total de registros
        total_registros = base_query.count()
        
        # Calcular total de páginas
        import math
        total_paginas = math.ceil(total_registros / por_pagina) if total_registros > 0 else 1
        
        # Calcular offset
        offset = (pagina - 1) * por_pagina
        
        # Query para buscar os registros paginados
        agendamentos_query = base_query.order_by(AgendamentoPagamentoModel.id.desc())\
            .offset(offset)\
            .limit(por_pagina)
        
        # Executar a query
        agendamentos = agendamentos_query.all()
        
        return {
            'agendamentos': agendamentos,
            'total': total_registros,
            'pagina': pagina,
            'por_pagina': por_pagina,
            'total_paginas': total_paginas,
            'termo_pesquisa': termo_pesquisa
        }

    @staticmethod
    def obter_sugestoes_conciliacao_formatadas(valor_transacao, eh_credito):
        """
        Busca e formata sugestões de agendamentos para conciliação bancária.
        Retorna os dados já formatados para uso direto no template.
        
        Args:
            valor_transacao (int): Valor da transação em centavos
            eh_credito (bool): True se for crédito (entrada), False se for débito (saída)
        
        Returns:
            list: Lista de sugestões formatadas para o template
        """
        # Buscar sugestões usando o método existente
        sugestoes = AgendamentoPagamentoModel.buscar_sugestoes_conciliacao(
            valor_transacao=valor_transacao,
            eh_credito=eh_credito
        )
        
        # Formatar as sugestões para o template
        sugestoes_formatadas = []
        for agendamento in sugestoes:
            # Determinar origem (faturamento ou lançamento avulso)
            origem = 'Faturamento'
            origem_id = agendamento.faturamento_id
            if agendamento.lancamento_avulso_id:
                origem = 'Lançamento Avulso'
                origem_id = agendamento.lancamento_avulso_id
            
            # Formattar valor
            from sistema._utilitarios.valores_monetarios import ValoresMonetarios
            valor_formatado = ValoresMonetarios.converter_float_brl_positivo(agendamento.valor_total_100 / 100)            
            # Informações da pessoa/fornecedor
            pessoa_nome = agendamento.pessoa_financeiro.identificacao if agendamento.pessoa_financeiro else 'N/A'
            
            # Categorias (do JSON)
            categorias_nomes = []
            if agendamento.categorias_json:
                try:
                    import json
                    # Se for string, fazer parse do JSON
                    if isinstance(agendamento.categorias_json, str):
                        categorias_data = json.loads(agendamento.categorias_json)
                    else:
                        categorias_data = agendamento.categorias_json
                    
                    # Processar as categorias
                    if isinstance(categorias_data, list):
                        for cat in categorias_data:
                            if isinstance(cat, dict):
                                categorias_nomes.append(cat.get('categoria', 'Categoria não identificada'))
                            else:
                                categorias_nomes.append(str(cat))
                    else:
                        categorias_nomes.append('Categoria não identificada')
                        
                except (json.JSONDecodeError, TypeError, AttributeError) as e:
                    print(f"[WARNING] Erro ao processar categorias_json: {str(e)}")
                    categorias_nomes.append('Categoria não identificada')
            
            sugestao = {
                'id': agendamento.id,
                'valor_formatado': valor_formatado,
                'valor_centavos': agendamento.valor_total_100,
                'data_vencimento': agendamento.data_vencimento.strftime('%d/%m/%Y') if agendamento.data_vencimento else 'N/A',
                'descricao': agendamento.descricao or agendamento.referencia or 'Sem descrição',
                'pessoa_nome': pessoa_nome,
                'origem': origem,
                'faturamento_codigo': agendamento.faturamento.codigo_faturamento if agendamento.faturamento else '',
                'origem_id': origem_id,
                'categorias': categorias_nomes,
                'diferenca_dias': 0  # Calcular diferença de dias se necessário
            }
            sugestoes_formatadas.append(sugestao)
        
        return sugestoes_formatadas

    @staticmethod
    def obter_agendamentos_recentes_formatados(eh_credito):
        """
        Busca agendamentos recentes do mesmo tipo (receitas ou despesas) para exibir na conciliação.
        Retorna os últimos 30 registros por tipo de movimentação.
        
        Args:
            eh_credito (bool): True se for crédito (receitas), False se for débito (despesas)
        
        Returns:
            list: Lista de agendamentos formatados para o template (máximo 30 registros)
        """
        from datetime import datetime
        from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
        from sistema.models_views.financeiro.lancamento_avulso.lancamento_avulso_model import LancamentoAvulsoModel
        from sistema.models_views.gerenciar.pessoa_financeiro.pessoa_financeiro_model import PessoaFinanceiroModel
        
        # Query base otimizada - buscar últimos 30 agendamentos por tipo
        query = db.session.query(AgendamentoPagamentoModel)\
            .filter(
                AgendamentoPagamentoModel.ativo == True,
                AgendamentoPagamentoModel.deletado == False,
                AgendamentoPagamentoModel.situacao_pagamento_id.notin_([8, 9])  # Excluir conciliados e liquidados
            )
        
        # Aplicar JOINs para filtrar por tipo de movimentação
        if eh_credito:
            query = query.outerjoin(FaturamentoModel, AgendamentoPagamentoModel.faturamento_id == FaturamentoModel.id)\
                         .outerjoin(LancamentoAvulsoModel, AgendamentoPagamentoModel.lancamento_avulso_id == LancamentoAvulsoModel.id)\
                         .filter(
                             db.or_(
                                 db.and_(
                                     AgendamentoPagamentoModel.faturamento_id.isnot(None),
                                     FaturamentoModel.direcao_financeira == 1,
                                     FaturamentoModel.ativo == True,
                                     FaturamentoModel.deletado == False
                                 ),
                                 db.and_(
                                     AgendamentoPagamentoModel.lancamento_avulso_id.isnot(None),
                                     LancamentoAvulsoModel.tipo_movimentacao == 1,
                                     LancamentoAvulsoModel.ativo == True,
                                     LancamentoAvulsoModel.deletado == False
                                 )
                             )
                         )
        else:
            query = query.outerjoin(FaturamentoModel, AgendamentoPagamentoModel.faturamento_id == FaturamentoModel.id)\
                         .outerjoin(LancamentoAvulsoModel, AgendamentoPagamentoModel.lancamento_avulso_id == LancamentoAvulsoModel.id)\
                         .filter(
                             db.or_(
                                 db.and_(
                                     AgendamentoPagamentoModel.faturamento_id.isnot(None),
                                     FaturamentoModel.direcao_financeira == 2,
                                     FaturamentoModel.ativo == True,
                                     FaturamentoModel.deletado == False
                                 ),
                                 db.and_(
                                     AgendamentoPagamentoModel.lancamento_avulso_id.isnot(None),
                                     LancamentoAvulsoModel.tipo_movimentacao == 2,
                                     LancamentoAvulsoModel.ativo == True,
                                     LancamentoAvulsoModel.deletado == False
                                 )
                             )
                         )
        
        # Buscar últimos 30 registros ordenados por data de vencimento (mais recentes primeiro)
        agendamentos = query.order_by(AgendamentoPagamentoModel.data_vencimento.desc())\
                           .limit(30)\
                           .all()
        
        # Formatar os agendamentos para o template (usando a mesma estrutura das sugestões)
        agendamentos_formatados = []
        for agendamento in agendamentos:
            # Determinar origem (faturamento ou lançamento avulso)
            origem = 'Faturamento'
            origem_id = agendamento.faturamento_id
            codigo_origem = ''
            
            if agendamento.faturamento_id and agendamento.faturamento:
                origem = 'Faturamento'
                origem_id = agendamento.faturamento_id
                codigo_origem = agendamento.faturamento.codigo_faturamento
            elif agendamento.lancamento_avulso_id:
                origem = 'Lançamento Avulso'
                origem_id = agendamento.lancamento_avulso_id
                codigo_origem = f'LA-{agendamento.lancamento_avulso_id}'
            
            # Formattar valor
            from sistema._utilitarios.valores_monetarios import ValoresMonetarios
            valor_formatado = ValoresMonetarios.converter_float_brl_positivo(agendamento.valor_total_100 / 100)
            
            # Informações da pessoa/fornecedor
            pessoa_nome = agendamento.pessoa_financeiro.identificacao if agendamento.pessoa_financeiro else 'N/A'
            
            # Categorias (do JSON)
            categorias_nomes = []
            if agendamento.categorias_json:
                try:
                    import json
                    # Se for string, fazer parse do JSON
                    if isinstance(agendamento.categorias_json, str):
                        categorias_data = json.loads(agendamento.categorias_json)
                    else:
                        categorias_data = agendamento.categorias_json
                    
                    # Processar as categorias
                    if isinstance(categorias_data, list):
                        for cat in categorias_data:
                            if isinstance(cat, dict):
                                # Tentar diferentes chaves possíveis
                                categoria_nome = cat.get('categoria')
                                if categoria_nome:
                                    categorias_nomes.append(categoria_nome)
                            else:
                                categorias_nomes.append(str(cat))
                    
                    if not categorias_nomes:
                        categorias_nomes.append('Categoria não identificada')
                        
                except (json.JSONDecodeError, TypeError, AttributeError) as e:
                    print(f"[WARNING] Erro ao processar categorias_json no agendamento {agendamento.id}: {str(e)}")
                    categorias_nomes.append('Categoria não identificada')
            
            # Calcular diferença de dias entre hoje e data de vencimento
            diferenca_dias = 0
            if agendamento.data_vencimento:
                try:
                    from datetime import date
                    hoje = date.today()
                    diferenca_dias = (agendamento.data_vencimento - hoje).days
                except Exception as e:
                    print(f"[WARNING] Erro ao calcular diferença de dias: {str(e)}")
            
            agendamento_formatado = {
                'id': agendamento.id,
                'valor_formatado': valor_formatado,
                'valor_centavos': agendamento.valor_total_100,
                'data_vencimento': agendamento.data_vencimento.strftime('%d/%m/%Y') if agendamento.data_vencimento else 'N/A',
                'descricao': agendamento.descricao or agendamento.referencia or 'Sem descrição',
                'pessoa_nome': pessoa_nome,
                'origem': origem,
                'faturamento_codigo': codigo_origem,
                'origem_id': origem_id,
                'categorias': categorias_nomes,
                'diferenca_dias': diferenca_dias
            }
            agendamentos_formatados.append(agendamento_formatado)
        
        return agendamentos_formatados

    @staticmethod
    def _formatar_agendamentos_para_template(agendamentos):
        """
        Método privado para formatar agendamentos para exibição no template usando a mesma estrutura 
        do método obter_agendamentos_recentes_formatados.
        
        Args:
            agendamentos (list): Lista de objetos AgendamentoPagamentoModel
            
        Returns:
            list: Lista de agendamentos formatados para o template
        """
        from datetime import date
        from sistema._utilitarios.valores_monetarios import ValoresMonetarios
        import json
        
        agendamentos_formatados = []
        for agendamento in agendamentos:
            # Determinar origem e código
            origem = 'Faturamento'
            origem_id = agendamento.faturamento_id
            codigo_origem = ''
            
            if agendamento.faturamento_id and agendamento.faturamento:
                origem = 'Faturamento'
                origem_id = agendamento.faturamento_id
                codigo_origem = agendamento.faturamento.codigo_faturamento
            elif agendamento.lancamento_avulso_id:
                origem = 'Lançamento Avulso'
                origem_id = agendamento.lancamento_avulso_id
                codigo_origem = f'LA-{agendamento.lancamento_avulso_id}'
            
            # Formatar valor usando a mesma função do model
            valor_formatado = ValoresMonetarios.converter_float_brl_positivo(agendamento.valor_total_100 / 100)
            
            # Informações da pessoa/fornecedor
            pessoa_nome = agendamento.pessoa_financeiro.identificacao if agendamento.pessoa_financeiro else 'N/A'
            
            # Processar categorias do JSON
            categorias_nomes = []
            if agendamento.categorias_json:
                try:
                    # Parse do JSON das categorias
                    if isinstance(agendamento.categorias_json, str):
                        categorias_data = json.loads(agendamento.categorias_json)
                    else:
                        categorias_data = agendamento.categorias_json
                    
                    # Processar as categorias
                    if isinstance(categorias_data, list):
                        for cat in categorias_data:
                            if isinstance(cat, dict):
                                # Tentar diferentes chaves possíveis
                                categoria_nome = cat.get('categoria')
                                if categoria_nome:
                                    categorias_nomes.append(categoria_nome)
                            else:
                                categorias_nomes.append(str(cat))
                    
                    if not categorias_nomes:
                        categorias_nomes.append('Categoria não identificada')
                        
                except (json.JSONDecodeError, TypeError, AttributeError) as e:
                    print(f"[WARNING] Erro ao processar categorias_json no agendamento {agendamento.id}: {str(e)}")
                    categorias_nomes.append('Categoria não identificada')
            
            # Calcular diferença de dias entre hoje e data de vencimento
            diferenca_dias = 0
            if agendamento.data_vencimento:
                try:
                    hoje = date.today()
                    diferenca_dias = (agendamento.data_vencimento - hoje).days
                except Exception as e:
                    print(f"[WARNING] Erro ao calcular diferença de dias: {str(e)}")
            
            # ================================================================
            # SISTEMA DE CONCILIAÇÃO PARCIAL - FORMATAÇÃO PARA INTERFACE
            # ================================================================
            # Calcula e formata informações de conciliação parcial para exibição
            # na interface do usuário, incluindo valores restantes e percentuais
            # ================================================================
            
            # Formatar valores monetários para exibição
            valor_conciliado_formatado = ValoresMonetarios.converter_float_brl_positivo((agendamento.valor_conciliado_100 or 0) / 100)
            valor_restante_formatado = ValoresMonetarios.converter_float_brl_positivo(agendamento.valor_pendente_conciliacao_100 / 100)
            
            # Criar objeto formatado usando a mesma estrutura do model
            agendamento_formatado = {
                'id': agendamento.id,
                'valor_formatado': valor_formatado,
                'valor_centavos': agendamento.valor_total_100,
                'data_vencimento': agendamento.data_vencimento.strftime('%d/%m/%Y') if agendamento.data_vencimento else 'N/A',
                'descricao': agendamento.descricao or agendamento.referencia or 'Sem descrição',
                'pessoa_nome': pessoa_nome,
                'origem': origem,
                'faturamento_codigo': codigo_origem,
                'origem_id': origem_id,
                'categorias': categorias_nomes,
                'diferenca_dias': diferenca_dias,
                
                # ================================================================
                # CAMPOS DE CONCILIAÇÃO PARCIAL PARA INTERFACE
                # ================================================================
                # Novos campos implementados para suporte a exibição de valores
                # restantes e controle de conciliação parcial na interface
                # ================================================================
                'conciliacao_parcial': agendamento.conciliacao_parcial or False,
                'valor_conciliado_centavos': agendamento.valor_conciliado_100 or 0,
                'valor_conciliado_formatado': valor_conciliado_formatado,
                'valor_restante_centavos': agendamento.valor_pendente_conciliacao_100,
                'valor_restante_formatado': valor_restante_formatado,
                'percentual_conciliado': float(agendamento.percentual_conciliado)
            }
            agendamentos_formatados.append(agendamento_formatado)
        
        return agendamentos_formatados

