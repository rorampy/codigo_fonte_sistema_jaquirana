from ....base_model import BaseModel, db
from sqlalchemy import case, or_, and_, func
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.configuracoes_gerais.situacao_pagamento.situacao_pagamento_model import SituacaoPagamentoModel
from datetime import datetime, timedelta, date
from sistema.models_views.controle_carga.solicitacao_nf.carga_model import CargaModel
from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
from sistema.models_views.gerenciar.veiculo.veiculo_model import VeiculoModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_cadastro_model import FornecedorCadastroModel
from sistema.models_views.gerenciar.extrator.extrator_model import ExtratorModel
from sistema.models_views.gerenciar.motorista.motorista_model import MotoristaModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema.models_views.gerenciar.motorista.transportadora_motorista_associado_model import TransportadoraMotoristaAssocModel
from sistema.models_views.financeiro.movimentacao_financeira.movimentacao_financeira_model import MovimentacaoFinanceiraModel


class ExtratorPagarModel(BaseModel):
    __tablename__ = "fin_extrator_a_pagar"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    solicitacao_id = db.Column(db.Integer, db.ForeignKey("car_carga.id"), nullable=True)
    solicitacao = db.relationship(
        "CargaModel", backref=db.backref("fin_extrator_a_pagar_solicitacao", lazy=True)
    )
    fornecedor_id = db.Column(
        db.Integer, db.ForeignKey("for_fornecedor.id"), nullable=True
    )
    fornecedor = db.relationship(
        "FornecedorModel",
        backref=db.backref("fin_extrator_a_pagar_fornecedor", lazy=True),
    )
    bitola_id = db.Column(db.Integer, db.ForeignKey("z_sys_bitola.id"), nullable=False)
    bitola = db.relationship(
        "BitolaModel", backref=db.backref("fin_extrator_a_pagar_bitola", lazy=True)
    )
    situacao_pagamento_id = db.Column(
        db.Integer, db.ForeignKey("fin_situacao_pagamento.id"), nullable=False
    )
    situacao = db.relationship(
        "SituacaoPagamentoModel",
        backref=db.backref("fin_extrator_a_pagar_situacao", lazy=True),
    )

    utiliza_credito = db.Column(db.Boolean, nullable=True)

    # Caso utiliza credito
    valor_credito_100 = db.Column(db.Integer, nullable=True)

    utiliza_saldo_movimentacao = db.Column(db.Boolean, nullable=True)

    # Guarda valor saldo debitado
    valor_saldo_debitado_100 = db.Column(db.Integer, nullable=True)

    comprovante_pagamento_complementar_id = db.Column(
        db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True
    )
    comprovante_pagamento_complementar = db.relationship(
        "UploadArquivoModel",
        foreign_keys=[comprovante_pagamento_complementar_id],
        backref=db.backref("comprovante_pagamento_complementar_extrator", lazy=True),
    )

    comprovante_pagamento_id = db.Column(
        db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True
    )
    comprovante_pagamento = db.relationship(
        "UploadArquivoModel",
        foreign_keys=[comprovante_pagamento_id],
        backref=db.backref("comprovante_pagamento_extrator", lazy=True),
    )

    conta_bancaria_id = db.Column(db.Integer, db.ForeignKey("con_conta_bancaria.id"), nullable=True)
    conta_bancaria = db.relationship("ContaBancariaModel", foreign_keys=[conta_bancaria_id], backref=db.backref("conta_bancaria_a_pagar_extrator", lazy=True))

    plano_conta_id = db.Column(db.Integer, db.ForeignKey("plan_plano_conta.id"), nullable=True)
    plano_conta = db.relationship("PlanoContaModel", foreign_keys=[plano_conta_id], backref=db.backref("plano_conta_pagar_extrator", lazy=True))

    categorizacao_fiscal_id = db.Column(db.Integer, db.ForeignKey("ca_categorizacao_fiscal.id"), nullable=True)
    categorizacao_fiscal = db.relationship("CategorizacaoFiscalModel", foreign_keys=[categorizacao_fiscal_id], backref=db.backref("categorizacao_fiscal_pagar_extrator", lazy=True))

    preco_custo_bitola_100 = db.Column(db.Integer, nullable=False)
    valor_total_a_pagar_100 = db.Column(db.Integer, nullable=False)

    # Associação com movimentação financeira de pagamento em massa (conciliada)
    movimentacao_financeira_id = db.Column(db.Integer, db.ForeignKey('mov_movimentacao_financeira.id'), nullable=True)
    movimentacao_financeira = db.relationship('MovimentacaoFinanceiraModel', foreign_keys=[movimentacao_financeira_id], backref=db.backref('extratores_pagos_massa', lazy=True))

    data_entrega_ticket = db.Column(db.Date, nullable=True)
    data_liquidacao = db.Column(db.Date, nullable=True)
    incompleto = db.Column(db.Boolean, nullable=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    def __init__(
        self,
        solicitacao_id,
        fornecedor_id,
        bitola_id,
        preco_custo_bitola_100,
        valor_total_a_pagar_100,
        incompleto=None,
        data_entrega_ticket=None,
        situacao_pagamento_id=None,
        comprovante_pagamento_complementar_id=None,
        comprovante_pagamento_id=None,
        utiliza_credito=None,
        utiliza_saldo_movimentacao=None,
        valor_credito_100=None,
        valor_saldo_debitado_100=None,
        conta_bancaria_id=None,
        plano_conta_id=None,
        categorizacao_fiscal_id=None,
        data_liquidacao=None,
        ativo=True,
        movimentacao_financeira_id=None
    ):
        self.solicitacao_id = solicitacao_id
        self.fornecedor_id = fornecedor_id
        self.bitola_id = bitola_id
        self.data_entrega_ticket = data_entrega_ticket
        self.data_liquidacao = data_liquidacao
        self.situacao_pagamento_id = situacao_pagamento_id
        self.preco_custo_bitola_100 = preco_custo_bitola_100
        self.valor_total_a_pagar_100 = valor_total_a_pagar_100
        self.incompleto = incompleto
        self.comprovante_pagamento_complementar_id = (
            comprovante_pagamento_complementar_id
        )
        self.comprovante_pagamento_id = comprovante_pagamento_id
        self.utiliza_credito = utiliza_credito
        self.utiliza_saldo_movimentacao = utiliza_saldo_movimentacao
        self.valor_credito_100 = valor_credito_100
        self.valor_saldo_debitado_100 = valor_saldo_debitado_100
        self.conta_bancaria_id = conta_bancaria_id
        self.plano_conta_id = plano_conta_id
        self.categorizacao_fiscal_id = categorizacao_fiscal_id
        self.ativo = ativo
        self.movimentacao_financeira_id = movimentacao_financeira_id

    def obter_extrator_a_pagar_solicitacao(id):
        """
        Obtém um registro de extrator a pagar específico por ID.
        
        Args:
            id (int): ID do registro de extrator a pagar
        
        Returns:
            ExtratorPagarModel: Objeto do extrator a pagar encontrado ou None se não encontrar
        """
        return ExtratorPagarModel.query.filter(
            ExtratorPagarModel.deletado == False,
            ExtratorPagarModel.ativo == True,
            ExtratorPagarModel.solicitacao_id == id,
        ).first()

    def obter_extrator_a_pagar_id(id):
        """
        Obtém um registro de extrator a pagar específico por ID.
        
        Args:
            id (int): ID do registro de extrator a pagar
        
        Returns:
            ExtratorPagarModel: Objeto do extrator a pagar encontrado ou None se não encontrar
        """
        return ExtratorPagarModel.query.filter(
            ExtratorPagarModel.deletado == False,
            ExtratorPagarModel.ativo == True,
            ExtratorPagarModel.id == id,
        ).first()


    def listar_extratores_a_pagar():
        """
        Lista todos os extratores a pagar ativos e não deletados, ordenados por ID decrescente.
        
        Returns:
            list: Lista de objetos ExtratorPagarModel ativos e não deletados
        """
        return (
            ExtratorPagarModel.query.filter(
                ExtratorPagarModel.deletado == 0,
                ExtratorPagarModel.ativo == 1,
            )
            .order_by(ExtratorPagarModel.id.desc())
            .all()
        )


    def filtrar_extratores_a_pagar(
        nomeFornecedor=None,
        nomeMotorista=None,
        bitola=None,
        produto=None,
        incompleto=None,
        statusPagamento=None,
        placaVeiculo=None,
    ):
        """
        Filtra extratores a pagar por múltiplos critérios.
        
        Args:
            nomeFornecedor (str, optional): Nome/identificação do fornecedor
            nomeMotorista (str, optional): Nome completo do motorista
            bitola (str, optional): Bitola
            produto (str, optional): Nome do produto
            incompleto (bool, optional): Se o registro está incompleto
            statusPagamento (str, optional): Status do pagamento
            placaVeiculo (str, optional): Placa do veículo
        
        Returns:
            list: Lista de objetos ExtratorPagarModel que atendem aos critérios de filtro
        """
        query = (
            ExtratorPagarModel.query
            .join(ExtratorPagarModel.solicitacao)
            .join(CargaModel.produto)
            .join(CargaModel.veiculo)
            .join(CargaModel.motorista)
            .join(ExtratorPagarModel.fornecedor)
            .join(ExtratorPagarModel.bitola)
            .join(ExtratorPagarModel.situacao)
            .filter(
                ExtratorPagarModel.deletado == False,
                ExtratorPagarModel.ativo == True
            )
        )
        
        if nomeFornecedor:
            query = query.filter(
                FornecedorCadastroModel.identificacao.ilike(f"%{nomeFornecedor}%")
            )
            
        if nomeMotorista:
            query = query.filter(
                MotoristaModel.nome_completo.ilike(f"%{nomeMotorista}%")
            )
            
        if bitola:
            query = query.filter(BitolaModel.bitola.ilike(f"%{bitola}%"))
            
        if produto:
            query = query.filter(ProdutoModel.nome.ilike(f"%{produto}%"))
            
        if statusPagamento:
            query = query.filter(
                SituacaoPagamentoModel.situacao.ilike(f"%{statusPagamento}%")
            )
            
        if incompleto is not None:
            query = query.filter(ExtratorPagarModel.incompleto == incompleto)
            
        if placaVeiculo:
            query = query.filter(VeiculoModel.placa_veiculo.ilike(f"%{placaVeiculo}%"))
            
        return query.order_by(ExtratorPagarModel.id.desc()).all()


    def obter_valor_total_a_pagar():
        """
        Calcula o valor total pendente de pagamento para extratores.
        
        Considera apenas registros ativos, não deletados e com situação diferente de "pago" (id != 1).
        
        Returns:
            int: Valor total a pagar em centavos, ou 0 se não houver registros
        """
        a_pagar = ExtratorPagarModel.query.filter(
            ExtratorPagarModel.deletado == 0,
            ExtratorPagarModel.ativo == 1,
            ExtratorPagarModel.situacao_pagamento_id != 1,
        ).all()

        return (
            sum(
                a.valor_total_a_pagar_100 if a.valor_total_a_pagar_100 else 0
                for a in a_pagar
            )
            or 0
        )


    def obter_valor_total_pago():
        """
        Calcula o valor total já pago para extratores.
        
        Considera apenas registros ativos, não deletados e pagos (situacao_pagamento_id == 1).
        
        Returns:
            int: Valor total pago em centavos, ou 0 se não houver registros
        """
        a_pagar = ExtratorPagarModel.query.filter(
            ExtratorPagarModel.deletado == 0,
            ExtratorPagarModel.ativo == 1,
            ExtratorPagarModel.situacao_pagamento_id == 1,
        ).all()

        return (
            sum(
                a.valor_total_a_pagar_100 if a.valor_total_a_pagar_100 else 0
                for a in a_pagar
            )
            or 0
        )


    def obter_valor_total_pago_por_conta(conta_id=1):
        """
        Calcula o valor total pago para extratores através de uma conta bancária específica.
        
        Utiliza o valor do saldo debitado (valor_saldo_debitado_100) e considera apenas 
        registros pagos (situacao_pagamento_id == 1) e movimentações de saída/pagamento 
        (tipo_movimentacao == 2).
        
        Args:
            conta_id (int, optional): ID da conta bancária. Default: 1
        
        Returns:
            int: Valor total pago pela conta em centavos, ou 0 se não houver registros
        """
        if conta_id == None:
            conta_id = 1
            
        q = (
            db.session
            .query(func.coalesce(func.sum(ExtratorPagarModel.valor_saldo_debitado_100), 0))
            .join(
                MovimentacaoFinanceiraModel,
                and_(
                    MovimentacaoFinanceiraModel.extrator_pagamento_id == ExtratorPagarModel.id,
                    MovimentacaoFinanceiraModel.tipo_movimentacao == 2,  # saída/pagamento
                )
            )
            .filter(
                ExtratorPagarModel.deletado == False,
                ExtratorPagarModel.ativo == True,
                ExtratorPagarModel.situacao_pagamento_id == 1,  # somente pagos
            )
        )

        if conta_id and conta_id != 0:
            q = q.filter(MovimentacaoFinanceiraModel.conta_bancaria_id == conta_id)

        total_centavos = q.scalar() or 0
        return total_centavos


    def obter_extratores_agrupados():
        """
        Retorna todos os extratores agrupados com informações relacionadas.
        
        Returns:
            list: Lista de dicionários com extratores agrupados por origem, produto e bitola
        """
        from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel

        data_inicio = date.today() - timedelta(days=30)
        data_fim = date.today()

        query = (
            db.session.query(
                ExtratorPagarModel, RegistroOperacionalModel, ExtratorModel
            )
            .join(CargaModel, ExtratorPagarModel.solicitacao)
            .join(
                RegistroOperacionalModel,
                CargaModel.id == RegistroOperacionalModel.solicitacao_nf_id,
            )
            .join(FornecedorCadastroModel, ExtratorPagarModel.fornecedor)
            .join(ExtratorModel, FornecedorCadastroModel.extrator_id == ExtratorModel.id)
            .join(BitolaModel, ExtratorPagarModel.bitola)
            .join(SituacaoPagamentoModel, ExtratorPagarModel.situacao)
            .join(ClienteModel, CargaModel.cliente)
            .join(VeiculoModel, CargaModel.veiculo)
            .join(MotoristaModel, CargaModel.motorista)
            .filter(
                ExtratorPagarModel.deletado == False, 
                ExtratorPagarModel.ativo == True,
                ExtratorPagarModel.situacao_pagamento_id == 2
            )
            .order_by(
                ExtratorModel.identificacao.asc(), 
                ExtratorPagarModel.id.desc()
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
        for registro, registro_operacional, extrator in query.all():
            produto_nome = getattr(registro.solicitacao.produto, "nome", "Indefinido")
            bitola_nome = getattr(registro.solicitacao.bitola, "bitola", "")
            origem = registro.fornecedor.identificacao
            
            registros.append({
                "registro": registro,
                "produto": produto_nome,
                "origem": origem,
                "extrator": extrator,
                "bitola": bitola_nome,
                "registro_operacional": registro_operacional,
            })

        return registros

    def filtrar_extratores_agrupados(
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
        statusPagamento=None,
        extrator=None,
        incompleto=None,
    ):
        """
        Filtra e retorna extratores agrupados com informações relacionadas.
        """
        from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import (
            RegistroOperacionalModel,
        )
        
        if not data_inicio or not data_fim:
            data_inicio = date.today() - timedelta(days=30)
            data_fim = date.today()

        query = (
            db.session.query(
                ExtratorPagarModel, RegistroOperacionalModel, ExtratorModel
            )
            .join(CargaModel, ExtratorPagarModel.solicitacao)
            .join(
                RegistroOperacionalModel,
                CargaModel.id == RegistroOperacionalModel.solicitacao_nf_id,
            )
            .join(FornecedorCadastroModel, ExtratorPagarModel.fornecedor)
            .join(ExtratorModel, FornecedorCadastroModel.extrator_id == ExtratorModel.id)
            .filter(
                ExtratorPagarModel.deletado == False, 
                ExtratorPagarModel.ativo == True
            )
        )

        # Aplica filtros de data
        if data_inicio and data_fim:
            query = query.filter(
                ExtratorPagarModel.data_entrega_ticket.isnot(None),
                ExtratorPagarModel.data_entrega_ticket.between(data_inicio, data_fim),
            )
        elif data_inicio:
            query = query.filter(
                ExtratorPagarModel.data_entrega_ticket.isnot(None),
                ExtratorPagarModel.data_entrega_ticket >= data_inicio,
            )
        elif data_fim:
            query = query.filter(
                ExtratorPagarModel.data_entrega_ticket.isnot(None),
                ExtratorPagarModel.data_entrega_ticket <= data_fim,
            )

        # JOINs condicionais - só quando necessários
        if cliente:
            query = query.join(ClienteModel, CargaModel.cliente).filter(ClienteModel.identificacao.ilike(f"%{cliente}%"))
            
        if numero_nf:
            query = query.filter(
                or_(
                    RegistroOperacionalModel.numero_nota_fiscal.ilike(f"%{numero_nf}%"),
                    RegistroOperacionalModel.numero_nota_fiscal_excessao.ilike(f"%{numero_nf}%"),
                    RegistroOperacionalModel.numero_nota_fiscal_estorno.ilike(f"%{numero_nf}%"),
                    RegistroOperacionalModel.numero_nota_fiscal_ticket.ilike(f"%{numero_nf}%"),
                )
            )

        if produto:
            query = query.join(ProdutoModel, CargaModel.produto_id == ProdutoModel.id).filter(ProdutoModel.nome.ilike(f"%{produto}%"))

        if bitola:
            query = query.join(BitolaModel, ExtratorPagarModel.bitola).filter(BitolaModel.bitola.ilike(f"%{bitola}%"))

        if motorista:
            query = query.join(MotoristaModel, CargaModel.motorista).filter(MotoristaModel.nome_completo.ilike(f"%{motorista}%"))

        if transportadora:
            query = query.outerjoin(
                TransportadoraModel,
                CargaModel.transportadora_id == TransportadoraModel.id,
            ).filter(TransportadoraModel.identificacao.ilike(f"%{transportadora}%"))

        if fornecedor:
            query = query.filter(FornecedorCadastroModel.identificacao.ilike(f"%{fornecedor}%"))

        if placa:
            query = query.join(VeiculoModel, CargaModel.veiculo).filter(VeiculoModel.placa_veiculo.ilike(f"%{placa}%"))

        if statusPagamento and statusPagamento != "":
            query = query.join(SituacaoPagamentoModel, ExtratorPagarModel.situacao).filter(SituacaoPagamentoModel.id == statusPagamento)
            
        if extrator:
            query = query.filter(ExtratorModel.identificacao.ilike(f"%{extrator}%"))
            
        if incompleto is not None:
            query = query.filter(ExtratorPagarModel.incompleto == incompleto)

        query = query.order_by(
            ExtratorModel.identificacao.asc(), 
            ExtratorPagarModel.id.desc()
        )

        registros = []
        for registro, registro_operacional, extrator in query.all():
            produto_nome = getattr(registro.solicitacao.produto, "nome", "Indefinido")
            bitola_nome = getattr(registro.solicitacao.bitola, "bitola", "")
            origem = registro.fornecedor.identificacao
            
            registros.append({
                "registro": registro,
                "produto": produto_nome,
                "origem": origem,
                "extrator": extrator,
                "bitola": bitola_nome,
                "registro_operacional": registro_operacional,
            })

        return registros
