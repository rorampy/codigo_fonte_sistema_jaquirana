from ....base_model import BaseModel, db
from sqlalchemy import case, or_, and_, func
from datetime import datetime, timedelta, date
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.configuracoes_gerais.situacao_pagamento.situacao_pagamento_model import SituacaoPagamentoModel
from sistema.models_views.controle_carga.solicitacao_nf.carga_model import CargaModel
from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
from sistema.models_views.gerenciar.veiculo.veiculo_model import VeiculoModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_model import FornecedorModel
from sistema.models_views.gerenciar.motorista.motorista_model import MotoristaModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema.models_views.gerenciar.motorista.transportadora_motorista_associado_model import TransportadoraMotoristaAssocModel
from sistema.models_views.financeiro.movimentacao_financeira.movimentacao_financeira_model import MovimentacaoFinanceiraModel



class FretePagarModel(BaseModel):
    """
    Model para registro do controle de cargas.
    """

    __tablename__ = "fin_frete_a_pagar"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    solicitacao_id = db.Column(db.Integer, db.ForeignKey("car_carga.id"), nullable=True)
    solicitacao = db.relationship("CargaModel", backref=db.backref("fin_frete_a_pagar_solicitacao", lazy=True))

    transportadora_id = db.Column(db.Integer, db.ForeignKey("transp_transportadora.id"), nullable=True)
    transportadora = db.relationship("TransportadoraModel", backref=db.backref("fin_frete_a_pagar_transportadora", lazy=True),)

    fornecedor_id = db.Column(db.Integer, db.ForeignKey("for_fornecedor.id"), nullable=True)
    fornecedor = db.relationship("FornecedorModel", backref=db.backref("fin_frete_a_pagar_fornecedor", lazy=True))

    bitola_id = db.Column(db.Integer, db.ForeignKey("z_sys_bitola.id"), nullable=False)
    bitola = db.relationship("BitolaModel", backref=db.backref("fin_frete_a_pagar_bitola", lazy=True))

    situacao_pagamento_id = db.Column(db.Integer, db.ForeignKey("fin_situacao_pagamento.id"), nullable=False)
    situacao = db.relationship("SituacaoPagamentoModel", backref=db.backref("fin_frete_a_pagar", lazy=True))

    utiliza_credito = db.Column(db.Boolean, nullable=True)

    # Caso utiliza credito
    valor_credito_100 = db.Column(db.Integer, nullable=True)

    utiliza_saldo_movimentacao = db.Column(db.Boolean, nullable=True)

    # Guarda valor saldo debitado
    valor_saldo_debitado_100 = db.Column(db.Integer, nullable=True)

    comprovante_pagamento_complementar_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    comprovante_pagamento_complementar = db.relationship("UploadArquivoModel", foreign_keys=[comprovante_pagamento_complementar_id], backref=db.backref("comprovante_pagamento_complementar_frete", lazy=True))

    comprovante_pagamento_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    comprovante_pagamento = db.relationship("UploadArquivoModel", foreign_keys=[comprovante_pagamento_id], backref=db.backref("comprovante_pagamento_frete", lazy=True))

    conta_bancaria_id = db.Column(db.Integer, db.ForeignKey("con_conta_bancaria.id"), nullable=True)
    conta_bancaria = db.relationship("ContaBancariaModel", foreign_keys=[conta_bancaria_id], backref=db.backref("conta_bancaria_a_pagar_frete", lazy=True))

    plano_conta_id = db.Column(db.Integer, db.ForeignKey("plan_plano_conta.id"), nullable=True)
    plano_conta = db.relationship("PlanoContaModel", foreign_keys=[plano_conta_id], backref=db.backref("plano_conta_pagar_frete", lazy=True))

    categorizacao_fiscal_id = db.Column(db.Integer, db.ForeignKey("ca_categorizacao_fiscal.id"), nullable=True)
    categorizacao_fiscal = db.relationship("CategorizacaoFiscalModel", foreign_keys=[categorizacao_fiscal_id], backref=db.backref("categorizacao_fiscal_pagar_frete", lazy=True))


    preco_custo_bitola_100 = db.Column(db.Integer, nullable=False)
    valor_total_a_pagar_100 = db.Column(db.Integer, nullable=False)

    # Associação com movimentação financeira de pagamento em massa (conciliada)
    movimentacao_financeira_id = db.Column(db.Integer, db.ForeignKey('mov_movimentacao_financeira.id'), nullable=True)
    movimentacao_financeira = db.relationship('MovimentacaoFinanceiraModel', foreign_keys=[movimentacao_financeira_id], backref=db.backref('transportadoras_pagas_massa', lazy=True))

    data_entrega_ticket = db.Column(db.Date, nullable=True)
    data_liquidacao = db.Column(db.Date, nullable=True)

    incompleto = db.Column(db.Boolean, nullable=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    def __init__(
        self,
        solicitacao_id,
        transportadora_id,
        fornecedor_id,
        bitola_id,
        preco_custo_bitola_100,
        valor_total_a_pagar_100,
        data_entrega_ticket=None,
        incompleto=None,
        situacao_pagamento_id=None,
        comprovante_pagamento_complementar_id=None,
        comprovante_pagamento_id=None,
        utiliza_credito=None,
        utiliza_saldo_movimentacao=None,
        valor_credito_100 = None,
        valor_saldo_debitado_100 = None,
        conta_bancaria_id=None,
        plano_conta_id=None,
        categorizacao_fiscal_id=None,
        data_liquidacao=None,
        ativo=True,
        movimentacao_financeira_id=None
    ):
        self.solicitacao_id = solicitacao_id
        self.transportadora_id = transportadora_id
        self.fornecedor_id = fornecedor_id
        self.bitola_id = bitola_id
        self.situacao_pagamento_id = situacao_pagamento_id
        self.preco_custo_bitola_100 = preco_custo_bitola_100
        self.valor_total_a_pagar_100 = valor_total_a_pagar_100
        self.data_entrega_ticket = data_entrega_ticket
        self.incompleto = incompleto
        self.comprovante_pagamento_complementar_id=comprovante_pagamento_complementar_id
        self.comprovante_pagamento_id=comprovante_pagamento_id
        self.utiliza_credito = utiliza_credito
        self.utiliza_saldo_movimentacao = utiliza_saldo_movimentacao
        self.valor_credito_100 = valor_credito_100
        self.valor_saldo_debitado_100 = valor_saldo_debitado_100
        self.conta_bancaria_id = conta_bancaria_id
        self.plano_conta_id = plano_conta_id
        self.categorizacao_fiscal_id = categorizacao_fiscal_id
        self.data_liquidacao = data_liquidacao
        self.ativo = ativo
        self.movimentacao_financeira_id = movimentacao_financeira_id
    
    def obter_frete_a_pagar_solicitacao(id):
        """
        Obtém um registro de frete a pagar específico por ID da solicitação.
        
        Args:
            id (int): ID da solicitação.
        
        Returns:
            FretePagarModel: Instância do modelo FretePagarModel correspondente à solicitação.
        """
        frete = FretePagarModel.query.filter(
            FretePagarModel.deletado == False,
            FretePagarModel.ativo == True,
            FretePagarModel.solicitacao_id == id,
        ).first()

        return frete
    
    def obter_frete_transportadora_agrupados():
        """
        Retorna todos os fretes por transportadora agrupados com informações relacionadas.
        
        Returns:
            list: Lista de dicionários com fretes agrupados por transportadora, produto e bitola
        """
        from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel


        data_inicio = date.today() - timedelta(days=30)
        data_fim = date.today()

        query = (
            db.session.query(FretePagarModel, RegistroOperacionalModel)
            .join(CargaModel, FretePagarModel.solicitacao)
            .join(
                RegistroOperacionalModel,
                CargaModel.id == RegistroOperacionalModel.solicitacao_nf_id,
            )
            .join(FornecedorModel, FretePagarModel.fornecedor)
            .join(BitolaModel, FretePagarModel.bitola)
            .join(SituacaoPagamentoModel, FretePagarModel.situacao)
            .join(ClienteModel, CargaModel.cliente)
            .join(VeiculoModel, CargaModel.veiculo)
            .join(MotoristaModel, CargaModel.motorista)
            .outerjoin(
                TransportadoraMotoristaAssocModel,
                and_(
                    TransportadoraMotoristaAssocModel.motorista_id == MotoristaModel.id,
                    TransportadoraMotoristaAssocModel.ativo.is_(True),
                    TransportadoraMotoristaAssocModel.deletado.is_(False),
                )
            )
            .outerjoin(
                TransportadoraModel,
                or_(
                    TransportadoraModel.id == MotoristaModel.transportadora_id,
                    TransportadoraModel.id == TransportadoraMotoristaAssocModel.transportadora_id,
                )
            )
            .filter(FretePagarModel.deletado == False, FretePagarModel.ativo == True, FretePagarModel.situacao_pagamento_id == 2) 
            .order_by(
                case((TransportadoraModel.identificacao == None, 1), else_=0),
                TransportadoraModel.identificacao.asc(),
                TransportadoraModel.id.desc(),
            )
        )

        if data_inicio and data_fim:
            query = query.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket.between(data_inicio, data_fim),
            )
        elif data_inicio:
            query = query.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket >= data_inicio,
            )
        elif data_fim:
            query = query.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket <= data_fim,
            )

        registros = []
        for registro, registro_operacional in query.all():
            if registro:
                produto = getattr(registro.solicitacao.produto, "nome", "Indefinido")
                bitola = getattr(registro.solicitacao.bitola, "bitola", "")
                origem = registro.transportadora.identificacao if registro.transportadora else "Sem transportadora"

                registros.append({
                    "registro": registro,
                    "produto": produto,
                    "origem": origem,
                    "bitola": bitola,
                    "registro_operacional": registro_operacional,
                })

        return registros

    def _criar_query_base():
        """Cria a query base com todos os joins necessários"""
        from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
        
        return (
            db.session.query(FretePagarModel, RegistroOperacionalModel)
            .join(CargaModel, FretePagarModel.solicitacao)
            .join(RegistroOperacionalModel, CargaModel.id == RegistroOperacionalModel.solicitacao_nf_id)
            .join(FornecedorModel, FretePagarModel.fornecedor)
            .join(BitolaModel, FretePagarModel.bitola)
            .join(SituacaoPagamentoModel, FretePagarModel.situacao)
            .join(ClienteModel, CargaModel.cliente)
            .join(VeiculoModel, CargaModel.veiculo)
            .join(MotoristaModel, CargaModel.motorista)
            .outerjoin(
                TransportadoraMotoristaAssocModel,
                and_(
                    TransportadoraMotoristaAssocModel.motorista_id == MotoristaModel.id,
                    TransportadoraMotoristaAssocModel.ativo == True,
                    TransportadoraMotoristaAssocModel.deletado == False,
                )
            )
            .outerjoin(
                TransportadoraModel,
                or_(
                    TransportadoraModel.id == MotoristaModel.transportadora_id,
                    TransportadoraModel.id == TransportadoraMotoristaAssocModel.transportadora_id,
                )
            )
            .filter(FretePagarModel.deletado == False, FretePagarModel.ativo == True)
        )

    def filtrar_frete_transportadora_agrupados(
        data_inicio=None,
        data_fim=None,
        numero_nf=None,
        placa=None,
        motorista=None,
        produto=None,
        bitola=None,
        transportadora=None,
        fornecedor=None,
        cliente=None,
        statusPagamento=None
    ):
        """Filtra fretes por transportadora com informações relacionadas."""
        from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
        
        # Define período padrão se não informado
        if not data_inicio or not data_fim:
            data_inicio = date.today() - timedelta(days=30)
            data_fim = date.today()

        # Cria query base
        query = FretePagarModel._criar_query_base()

        # Aplica filtros de data
        query = query.filter(
            RegistroOperacionalModel.data_entrega_ticket.between(data_inicio, data_fim)
        )

        # Filtros por texto usando LIKE
        if cliente:
            query = query.filter(ClienteModel.identificacao.ilike(f"%{cliente}%"))
        if motorista:
            query = query.filter(MotoristaModel.nome_completo.ilike(f"%{motorista}%"))
        if transportadora:
            query = query.filter(TransportadoraModel.identificacao.ilike(f"%{transportadora}%"))
        if fornecedor:
            query = query.filter(FornecedorModel.identificacao.ilike(f"%{fornecedor}%"))
        if bitola:
            query = query.filter(BitolaModel.bitola.ilike(f"%{bitola}%"))
        if placa:
            query = query.filter(VeiculoModel.placa_veiculo.ilike(f"%{placa}%"))

        # Filtro de produto usando LIKE
        if produto:
            query = query.join(ProdutoModel, CargaModel.produto).filter(
                ProdutoModel.nome.ilike(f"%{produto}%")
            )

        # Filtro específico para status pagamento (mantém por ID)
        if statusPagamento:
            query = query.filter(SituacaoPagamentoModel.id == statusPagamento)

        # Filtro especial para número de NF (múltiplos campos)
        if numero_nf:
            query = query.filter(
                or_(
                    RegistroOperacionalModel.numero_nota_fiscal.ilike(f"%{numero_nf}%"),
                    RegistroOperacionalModel.numero_nota_fiscal_ticket.ilike(f"%{numero_nf}%"),
                    RegistroOperacionalModel.numero_nota_fiscal_estorno.ilike(f"%{numero_nf}%"),
                    RegistroOperacionalModel.numero_nota_fiscal_excessao.ilike(f"%{numero_nf}%"),
                )
            )

        # Ordena resultados
        query = query.order_by(
            case((TransportadoraModel.identificacao.is_(None), 1), else_=0),
            TransportadoraModel.identificacao.asc(),
            TransportadoraModel.id.desc(),
        )

        # Processa resultados
        return [
            {
                "registro": registro,
                "produto": getattr(registro.solicitacao.produto, "nome", "Indefinido"),
                "origem": registro.transportadora.identificacao if registro.transportadora else "Sem transportadora",
                "bitola": getattr(registro.solicitacao.bitola, "bitola", ""),
                "registro_operacional": registro_operacional,
            }
            for registro, registro_operacional in query.all()
            if registro
        ]

    def obter_frete_a_pagar_id(id):
        """
        Obtém um registro de frete a pagar específico por ID.
        
        Args:
            id (int): ID do registro de frete a pagar
        
        Returns:
            FretePagarModel: Objeto do frete a pagar encontrado ou None se não encontrar
        """
        frete = FretePagarModel.query.filter(
            FretePagarModel.deletado == False,
            FretePagarModel.ativo == True,
            FretePagarModel.id == id,
        ).first()

        return frete

    def listar_fretes_a_pagar():
        """
        Lista todos os fretes a pagar ativos e não deletados, ordenados por ID decrescente.
        
        Returns:
            list: Lista de objetos FretePagarModel ativos e não deletados
        """
        fretes = (
            FretePagarModel.query.filter(
                FretePagarModel.deletado == 0,
                FretePagarModel.ativo == 1,
            )
            .order_by(FretePagarModel.id.desc())
            .all()
        )

        return fretes

    def obter_valor_total_a_pagar():
        """
        Calcula o valor total pendente de pagamento para fretes.
        
        Considera apenas registros ativos, não deletados e com situação diferente de "pago" (id != 1).
        
        Returns:
            int: Valor total a pagar em centavos, ou 0 se não houver registros
        """
        a_pagar = FretePagarModel.query.filter(
            FretePagarModel.deletado == 0,
            FretePagarModel.ativo == 1,
            FretePagarModel.situacao_pagamento_id != 1
        ).all()

        return sum(
            a.valor_total_a_pagar_100 if a.valor_total_a_pagar_100 else 0
            for a in a_pagar
        ) or 0

    def obter_valor_total_pago():
        """
        Calcula o valor total já pago para fretes.
        
        Considera apenas registros ativos, não deletados e pagos (situacao_pagamento_id == 1).
        
        Returns:
            int: Valor total pago em centavos, ou 0 se não houver registros
        """
        a_pagar = FretePagarModel.query.filter(
            FretePagarModel.deletado == 0,
            FretePagarModel.ativo == 1,
            FretePagarModel.situacao_pagamento_id == 1
        ).all()

        return sum(
            a.valor_total_a_pagar_100 if a.valor_total_a_pagar_100 else 0
            for a in a_pagar
        ) or 0

    def obter_valor_total_pago_por_conta(conta_id=1):
        """
        Calcula o valor total pago para fretes através de uma conta bancária específica.
        
        Considera apenas registros pagos (situacao_pagamento_id == 1) e movimentações 
        de saída/pagamento (tipo_movimentacao == 2).
        
        Args:
            conta_id (int, optional): ID da conta bancária. Default: 1
        
        Returns:
            int: Valor total pago pela conta em centavos, ou 0 se não houver registros
        """
        if conta_id == None:
            conta_id = 1
            
        q = (
            db.session
            .query(func.coalesce(func.sum(FretePagarModel.valor_total_a_pagar_100), 0))
            .join(
                MovimentacaoFinanceiraModel,
                MovimentacaoFinanceiraModel.freteiro_pagamento_id == FretePagarModel.id
            )
            .filter(
                FretePagarModel.deletado == False,
                FretePagarModel.ativo == True,
                FretePagarModel.situacao_pagamento_id == 1,  # somente pagos
                MovimentacaoFinanceiraModel.tipo_movimentacao == 2,  # saída/pagamento
            )
        )

        if conta_id and conta_id != 0:
            q = q.filter(MovimentacaoFinanceiraModel.conta_bancaria_id == conta_id)

        total_centavos = q.scalar() or 0
        return total_centavos

    def obter_frete_por_solicitacao_id(id_solicitacao):
        """
        Obtém um frete a pagar através do ID da solicitação.
        
        Args:
            id_solicitacao (int): ID da solicitação de carga
        
        Returns:
            FretePagarModel: Objeto do frete a pagar encontrado ou None se não encontrar
        """
        frete = FretePagarModel.query.filter(
            FretePagarModel.ativo == 1,
            FretePagarModel.deletado == 0,
            FretePagarModel.solicitacao_id == id_solicitacao
        ).first()

        return frete

    def listar_fretes_a_pagar_por_periodo_entrega(data_inicio=None, data_fim=None):
        """
        Lista fretes a pagar filtrados por período de data de entrega do ticket
        
        Args:
            data_inicio (date): Data de início do filtro
            data_fim (date): Data de fim do filtro
        
        Returns:
            List: Lista de fretes a pagar no período
        """
        query = FretePagarModel.query
        
        # Aplicar filtros de data se fornecidos
        if data_inicio or data_fim:        
            if data_inicio:
                query = query.filter(FretePagarModel.data_entrega_ticket >= data_inicio)
            
            if data_fim:
                from datetime import timedelta
                data_fim_inclusiva = data_fim + timedelta(days=1)
                query = query.filter(FretePagarModel.data_entrega_ticket < data_fim_inclusiva)
        
        # Filtrar apenas registros com data de entrega
        query = query.filter(FretePagarModel.data_entrega_ticket.isnot(None))
        
        # Ordenar por data de entrega mais recente primeiro
        query = query.order_by(FretePagarModel.data_entrega_ticket.desc())
        
        return query.all()