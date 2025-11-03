from ....base_model import BaseModel, db
from datetime import timedelta, date

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
    
    situacao_pagamento_id = db.Column(db.Integer, db.ForeignKey("fin_situacao_pagamento.id"), nullable=True)
    situacao = db.relationship("SituacaoPagamentoModel", backref=db.backref("agendamentos", lazy=True))
    
    # Controle
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(self, pessoa_financeiro_id, data_vencimento, valor_total_100,faturamento_id = None,  conta_bancaria_id=None, lancamento_avulso_id=None, descricao=None, referencia=None, data_competencia=None, categorias_json=None, centros_custo_json=None, parcelamento_ativo=False, numero_parcelas=None, dias_entre_parcelas=30, situacao_pagamento_id=None, ativo=True):
        self.faturamento_id = faturamento_id
        self.conta_bancaria_id = conta_bancaria_id
        self.pessoa_financeiro_id = pessoa_financeiro_id
        self.data_vencimento = data_vencimento
        self.valor_total_100 = valor_total_100
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
    def buscar_sugestoes_conciliacao(valor_transacao, eh_credito):
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
            AgendamentoPagamentoModel.situacao_pagamento_id != 8,  # Excluir conciliados
            AgendamentoPagamentoModel.situacao_pagamento_id != 9   # Excluir liquidados
        )
        
        # Usar JOINs simples para filtrar por direção/tipo
        from sistema.models_views.faturamento.faturamento_model import FaturamentoModel
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
    def buscar_agendamentos_com_filtros(eh_credito, valor_min=None, valor_max=None, data_inicio=None, data_fim=None, categoria_id=None, beneficiario_id=None):
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
        from sistema.models_views.faturamento.faturamento_model import FaturamentoModel
        from sistema.models_views.financeiro.lancamento_avulso.lancamento_avulso_model import LancamentoAvulsoModel
        from sistema.models_views.gerenciar.pessoa_financeiro.pessoa_financeiro_model import PessoaFinanceiroModel
        
        # Query base otimizada - fazer JOINs apenas quando necessário
        query = db.session.query(AgendamentoPagamentoModel)\
            .filter(
                AgendamentoPagamentoModel.ativo == True,
                AgendamentoPagamentoModel.deletado == False,
                AgendamentoPagamentoModel.situacao_pagamento_id.notin_([8, 9])  # Excluir conciliados e liquidados
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
            beneficiario_id is not None and beneficiario_id != '' and str(beneficiario_id).isdigit() and int(beneficiario_id) > 0
        ])
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
            
            if beneficiario_id is not None and beneficiario_id != '' and str(beneficiario_id).isdigit():
                beneficiario_id_int = int(beneficiario_id)
                query = query.filter(AgendamentoPagamentoModel.pessoa_financeiro_id == beneficiario_id_int)
                            
            

        # Ordenar e limitar resultados para performance
        if tem_filtros:
            # Com filtros, buscar até 50 registros
            agendamentos = query.order_by(AgendamentoPagamentoModel.data_vencimento.desc()).limit(50).all()
        else:
            # Sem filtros, buscar apenas 15 registros mais recentes
            agendamentos = query.order_by(AgendamentoPagamentoModel.data_vencimento.desc()).limit(15).all()
        
        return agendamentos

    @staticmethod
    def listar_receitas_avulsas_agendamentos():
        """
        Lista agendamentos de receitas avulsas (direção financeira = 1 e situação != 8).
        
        Returns:
            list: Lista de objetos AgendamentoPagamentoModel de receitas avulsas não conciliadas
        """
        from sistema.models_views.financeiro.lancamento_avulso.lancamento_avulso_model import LancamentoAvulsoModel
        from sistema.models_views.gerenciar.pessoa_financeiro.pessoa_financeiro_model import PessoaFinanceiroModel
        from sistema.models_views.faturamento.faturamento_model import FaturamentoModel
        
        # Construir a query
        query = db.session.query(AgendamentoPagamentoModel)\
            .outerjoin(FaturamentoModel, AgendamentoPagamentoModel.faturamento_id == FaturamentoModel.id)\
            .outerjoin(LancamentoAvulsoModel, AgendamentoPagamentoModel.lancamento_avulso_id == LancamentoAvulsoModel.id)\
            .join(PessoaFinanceiroModel, AgendamentoPagamentoModel.pessoa_financeiro_id == PessoaFinanceiroModel.id)\
            .filter(
                AgendamentoPagamentoModel.ativo == True,
                AgendamentoPagamentoModel.deletado == False,
                AgendamentoPagamentoModel.situacao_pagamento_id != 8,  # Não conciliadas
                AgendamentoPagamentoModel.situacao_pagamento_id != 9, # Liquidados
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
            )\
            .order_by(AgendamentoPagamentoModel.data_cadastro.desc())

        # Executar a query
        agendamentos = query.all()
        
        return agendamentos

    
    @staticmethod
    def listar_despesas_avulsas_agendamentos():
        """
        Lista agendamentos de despesas avulsas (faturamentos e lançamentos).
        Retorna apenas os agendamentos que não foram conciliados nem liquidados.
        """
        from sistema.models_views.faturamento.faturamento_model import FaturamentoModel
        from sistema.models_views.financeiro.lancamento_avulso.lancamento_avulso_model import LancamentoAvulsoModel
        
        # Query com joins necessários
        query = db.session.query(AgendamentoPagamentoModel)\
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
            .filter(
                AgendamentoPagamentoModel.ativo == True,
                AgendamentoPagamentoModel.deletado == False,
                AgendamentoPagamentoModel.situacao_pagamento_id != 8,  # Não conciliadas
                AgendamentoPagamentoModel.situacao_pagamento_id != 9, # Liquidados
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
            )\
            .order_by(AgendamentoPagamentoModel.data_cadastro.desc())

        # Executar a query
        agendamentos = query.all()
        
        return agendamentos

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
        
        Args:
            eh_credito (bool): True se for crédito (receitas), False se for débito (despesas)
        
        Returns:
            list: Lista de agendamentos formatados para o template
        """
        # Buscar agendamentos usando o método existente (sem filtros, apenas por tipo)
        agendamentos = AgendamentoPagamentoModel.buscar_agendamentos_com_filtros(
            eh_credito=eh_credito,
            valor_min=None,
            valor_max=None,
            data_inicio=None,
            data_fim=None,
            categoria_id=None,
            beneficiario_id=None
        )
        
        # Formatar os agendamentos para o template (usando a mesma estrutura das sugestões)
        agendamentos_formatados = []
        for agendamento in agendamentos:
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
            
            agendamento_formatado = {
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
            agendamentos_formatados.append(agendamento_formatado)
        
        return agendamentos_formatados

