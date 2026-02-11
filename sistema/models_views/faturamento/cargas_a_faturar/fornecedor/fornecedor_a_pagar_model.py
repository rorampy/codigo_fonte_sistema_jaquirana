from ....base_model import BaseModel, db
from sqlalchemy import case, or_, and_, func
from datetime import datetime, timedelta, date
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.configuracoes_gerais.situacao_pagamento.situacao_pagamento_model import SituacaoPagamentoModel
from sistema.models_views.controle_carga.solicitacao_nf.carga_model import CargaModel
from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
from sistema.models_views.gerenciar.veiculo.veiculo_model import VeiculoModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_cadastro_model import FornecedorCadastroModel
from sistema.models_views.gerenciar.motorista.motorista_model import MotoristaModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema.models_views.gerenciar.motorista.transportadora_motorista_associado_model import TransportadoraMotoristaAssocModel
from sistema.models_views.financeiro.movimentacao_financeira.movimentacao_financeira_model import MovimentacaoFinanceiraModel


class FornecedorPagarModel(BaseModel):
    """
    Model para registro de fornecedores a pagar.
    """

    __tablename__ = "fin_fornecedor_a_pagar"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    solicitacao_id = db.Column(db.Integer, db.ForeignKey("car_carga.id"), nullable=True)
    solicitacao = db.relationship("CargaModel", backref=db.backref("fin_fornecedor_a_pagar_solicitacao", lazy=True))

    fornecedor_id = db.Column(db.Integer, db.ForeignKey("for_fornecedor_cadastro.id"), nullable=True)
    fornecedor = db.relationship("FornecedorCadastroModel", backref=db.backref("fin_fornecedor_a_pagar_fornecedor", lazy=True))

    bitola_id = db.Column(db.Integer, db.ForeignKey("z_sys_bitola.id"), nullable=False)
    bitola = db.relationship("BitolaModel", backref=db.backref("fin_fornecedor_a_pagar_bitola", lazy=True))

    situacao_pagamento_id = db.Column(db.Integer, db.ForeignKey("fin_situacao_pagamento.id"), nullable=False)
    situacao = db.relationship("SituacaoPagamentoModel", backref=db.backref("fin_fornecedor_a_pagar", lazy=True))

    utiliza_credito = db.Column(db.Boolean, nullable=True)

    # Caso utiliza credito
    valor_credito_100 = db.Column(db.Integer, nullable=True)

    utiliza_saldo_movimentacao = db.Column(db.Boolean, nullable=True)

    # Guarda valor saldo debitado
    valor_saldo_debitado_100 = db.Column(db.Integer, nullable=True)

    comprovante_pagamento_complementar_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    comprovante_pagamento_complementar = db.relationship("UploadArquivoModel", foreign_keys=[comprovante_pagamento_complementar_id], backref=db.backref("comprovante_pagamento_complementar", lazy=True))

    comprovante_pagamento_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    comprovante_pagamento = db.relationship("UploadArquivoModel", foreign_keys=[comprovante_pagamento_id], backref=db.backref("comprovante_pagamento", lazy=True))

    conta_bancaria_id = db.Column(db.Integer, db.ForeignKey("con_conta_bancaria.id"), nullable=True)
    conta_bancaria = db.relationship("ContaBancariaModel", foreign_keys=[conta_bancaria_id], backref=db.backref("conta_bancaria_a_pagar_fornecedor", lazy=True))

    plano_conta_id = db.Column(db.Integer, db.ForeignKey("plan_plano_conta.id"), nullable=True)
    plano_conta = db.relationship("PlanoContaModel", foreign_keys=[plano_conta_id], backref=db.backref("plano_conta_pagar_fornecedor", lazy=True))

    categorizacao_fiscal_id = db.Column(db.Integer, db.ForeignKey("ca_categorizacao_fiscal.id"), nullable=True)
    categorizacao_fiscal = db.relationship("CategorizacaoFiscalModel", foreign_keys=[categorizacao_fiscal_id], backref=db.backref("categorizacao_fiscal_pagar_fornecedor", lazy=True))

    preco_custo_bitola_100 = db.Column(db.Integer, nullable=False)
    valor_total_a_pagar_100 = db.Column(db.Integer, nullable=False)

    movimentacao_financeira_id = db.Column(db.Integer, db.ForeignKey('mov_movimentacao_financeira.id'), nullable=True)
    movimentacao_financeira = db.relationship('MovimentacaoFinanceiraModel', foreign_keys=[movimentacao_financeira_id], backref=db.backref('fornecedores_pagos_massa', lazy=True))

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
        self.conta_bancaria_id = conta_bancaria_id
        self.comprovante_pagamento_complementar_id = (
            comprovante_pagamento_complementar_id
        )
        self.comprovante_pagamento_id = comprovante_pagamento_id
        self.utiliza_credito = utiliza_credito
        self.utiliza_saldo_movimentacao = utiliza_saldo_movimentacao
        self.valor_credito_100 = valor_credito_100
        self.valor_saldo_debitado_100 = valor_saldo_debitado_100
        self.plano_conta_id = plano_conta_id
        self.categorizacao_fiscal_id = categorizacao_fiscal_id
        self.ativo = ativo

    def obter_fornecedor_a_pagar_solicitacao(id):
        """
        Obtém um registro de fornecedor a pagar específico por ID.
        
        Args:
            id (int): ID do registro de fornecedor a pagar
        
        Returns:
            FornecedorPagarModel: Objeto do fornecedor a pagar encontrado ou None se não encontrar
        """
        fornecedor = FornecedorPagarModel.query.filter(
            FornecedorPagarModel.deletado == False,
            FornecedorPagarModel.ativo == True,
            FornecedorPagarModel.solicitacao_id == id,
        ).first()

        return fornecedor
    
    def obter_fornecedor_a_pagar_id(id):
        """
        Obtém um registro de fornecedor a pagar específico por ID.
        
        Args:
            id (int): ID do registro de fornecedor a pagar
        
        Returns:
            FornecedorPagarModel: Objeto do fornecedor a pagar encontrado ou None se não encontrar
        """
        fornecedor = FornecedorPagarModel.query.filter(
            FornecedorPagarModel.deletado == False,
            FornecedorPagarModel.ativo == True,
            FornecedorPagarModel.id == id,
        ).first()

        return fornecedor


    def listar_fornecedores_a_pagar():
        """
        Lista todos os fornecedores a pagar ativos e não deletados, ordenados por ID decrescente.
        
        Returns:
            list: Lista de objetos FornecedorPagarModel ativos e não deletados
        """
        fornecedores = (
            FornecedorPagarModel.query.filter(
                FornecedorPagarModel.deletado == 0,
                FornecedorPagarModel.ativo == 1,
            )
            .order_by(FornecedorPagarModel.id.desc())
            .all()
        )

        return fornecedores


    def obter_valor_total_a_pagar():
        """
        Calcula o valor total pendente de pagamento para fornecedores.
        
        Considera apenas registros ativos, não deletados e com situação diferente de "pago" (id != 1).
        
        Returns:
            int: Valor total a pagar em centavos, ou 0 se não houver registros
        """
        a_pagar = FornecedorPagarModel.query.filter(
            FornecedorPagarModel.deletado == 0,
            FornecedorPagarModel.ativo == 1,
            FornecedorPagarModel.situacao_pagamento_id != 1,
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
        Calcula o valor total já pago para fornecedores utilizando saldo de movimentação.
        
        Considera apenas registros ativos, não deletados, pagos (situacao_pagamento_id == 1) 
        e que utilizaram saldo de movimentação.
        
        Returns:
            int: Valor total pago em centavos, ou 0 se não houver registros
        """
        a_pagar = FornecedorPagarModel.query.filter(
            FornecedorPagarModel.deletado == 0,
            FornecedorPagarModel.ativo == 1,
            FornecedorPagarModel.situacao_pagamento_id == 1,
        ).all()

        return (
            sum(
                a.valor_saldo_debitado_100 if a.utiliza_saldo_movimentacao else 0
                for a in a_pagar
            )
            or 0
        )


    def obter_valor_total_pago_por_conta(conta_id=1):
        """
        Calcula o valor total pago para fornecedores através de uma conta bancária específica.
        
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
            .query(
                func.coalesce(
                    func.sum(FornecedorPagarModel.valor_saldo_debitado_100),
                    0
                )
            )
            .join(
                MovimentacaoFinanceiraModel,
                MovimentacaoFinanceiraModel.fornecedor_pagamento_id == FornecedorPagarModel.id
            )
            .filter(
                FornecedorPagarModel.deletado == False,
                FornecedorPagarModel.ativo == True,
                FornecedorPagarModel.situacao_pagamento_id == 1,  # somente pagos
                MovimentacaoFinanceiraModel.tipo_movimentacao == 2,  # saída/pagamento
            )
        )

        if conta_id and conta_id != 0:
            q = q.filter(MovimentacaoFinanceiraModel.conta_bancaria_id == conta_id)

        total_centavos = q.scalar() or 0
        return total_centavos
    

    def obter_fornecedores_agrupados():
        """
        Retorna todos os fornecedores agrupados com informações relacionadas.
        
        Returns:
            list: Lista de dicionários com fornecedores agrupados por origem, produto e bitola
        """
        from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel

        query = (
            db.session.query(FornecedorPagarModel, RegistroOperacionalModel)
            .join(CargaModel, FornecedorPagarModel.solicitacao)
            .join(
                RegistroOperacionalModel,
                CargaModel.id == RegistroOperacionalModel.solicitacao_nf_id,
            )
            .join(FornecedorCadastroModel, FornecedorPagarModel.fornecedor)
            .join(BitolaModel, FornecedorPagarModel.bitola)
            .join(SituacaoPagamentoModel, FornecedorPagarModel.situacao)
            .join(ClienteModel, CargaModel.cliente)
            .join(VeiculoModel, CargaModel.veiculo)
            .join(MotoristaModel, CargaModel.motorista)
            .filter(
                FornecedorPagarModel.deletado == False,
                FornecedorPagarModel.ativo == True,
                FornecedorPagarModel.situacao_pagamento_id == 2,  # somente pendentes
            )
            .order_by(
                case((FornecedorCadastroModel.identificacao == None, 1), else_=0),
                FornecedorCadastroModel.identificacao.asc(),
                FornecedorPagarModel.id.desc(),
            )
        )

        registros = []
        for registro, registro_operacional in query.all():
            if registro:
                produto = getattr(registro.solicitacao.produto, "nome", "Indefinido")
                bitola = getattr(registro.solicitacao.bitola, "bitola", "")
                origem = registro.fornecedor.identificacao

                registros.append({
                    "registro": registro,
                    "produto": produto,
                    "origem": origem,
                    "tags": [ft.tag for ft in registro.fornecedor.fornecedor_tags if ft.ativo],
                    "bitola": bitola,
                    "registro_operacional": registro_operacional,
                })

        return registros


    def filtrar_fornecedores_agrupados(
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
        tipo_data_filtro=None
    ):
        """
        Filtra e retorna fornecedores agrupados com informações relacionadas.
        
        Args:
            data_inicio (date, optional): Data inicial do filtro
            data_fim (date, optional): Data final do filtro
            cliente (int, optional): ID do cliente
            numero_nf (str, optional): Número da nota fiscal
            placa (str, optional): Placa do veículo
            motorista (int, optional): ID do motorista
            transportadora (int, optional): ID da transportadora
            fornecedor (int, optional): ID do fornecedor
            produto (int, optional): ID do produto
            bitola (int, optional): ID da bitola
            statusPagamento (int, optional): ID do status do pagamento
            tipo_data_filtro (str, optional): 'data_emissao' para filtrar por destinatario_data_emissao,
                                              'data_entrega' (padrão) para filtrar por data_entrega_ticket
        
        Returns:
            list: Lista de dicionários com fornecedores filtrados e agrupados
        """
        from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import (RegistroOperacionalModel)
        
        if not data_inicio or not data_fim:
            data_inicio = date.today() - timedelta(days=30)
            data_fim = date.today()

        query = (
            db.session.query(FornecedorPagarModel, RegistroOperacionalModel)
            .join(CargaModel, FornecedorPagarModel.solicitacao)
            .join(RegistroOperacionalModel, CargaModel.id == RegistroOperacionalModel.solicitacao_nf_id)
            .join(FornecedorCadastroModel, FornecedorPagarModel.fornecedor)
            .outerjoin(BitolaModel, FornecedorPagarModel.bitola)
            .outerjoin(SituacaoPagamentoModel, FornecedorPagarModel.situacao)
            .outerjoin(ClienteModel, CargaModel.cliente)
            .outerjoin(VeiculoModel, CargaModel.veiculo)
            .outerjoin(MotoristaModel, CargaModel.motorista)
            .outerjoin(ProdutoModel, CargaModel.produto_id == ProdutoModel.id)
            .outerjoin(TransportadoraModel, CargaModel.transportadora_id == TransportadoraModel.id)
            .filter(
                FornecedorPagarModel.deletado == False,
                FornecedorPagarModel.ativo == True,
            )
        )

        # Seleciona o campo de data conforme o tipo de filtro
        if tipo_data_filtro == 'data_emissao':
            campo_data = RegistroOperacionalModel.destinatario_data_emissao
        else:
            # Padrão: data de entrega do ticket
            campo_data = RegistroOperacionalModel.data_entrega_ticket

        if data_inicio and data_fim:
            query = query.filter(
                campo_data.isnot(None),
                campo_data.between(data_inicio, data_fim),
            )
        elif data_inicio:
            query = query.filter(
                campo_data.isnot(None),
                campo_data >= data_inicio,
            )
        elif data_fim:
            query = query.filter(
                campo_data.isnot(None),
                campo_data <= data_fim,
            )

        # Aplicar filtros
        if cliente:
            query = query.filter(ClienteModel.identificacao.ilike(f"%{cliente}%"))

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
            query = query.filter(ProdutoModel.nome.ilike(f"%{produto}%"))

        if bitola:
            query = query.filter(BitolaModel.bitola.ilike(f"%{bitola}%"))

        if motorista:
            query = query.filter(MotoristaModel.nome_completo.ilike(f"%{motorista}%"))

        if transportadora:
            query = query.filter(TransportadoraModel.identificacao.ilike(f"%{transportadora}%"))

        if fornecedor:
            query = query.filter(FornecedorCadastroModel.identificacao.ilike(f"%{fornecedor}%"))

        if placa:
            query = query.filter(VeiculoModel.placa_veiculo.ilike(f"%{placa}%"))

        if statusPagamento and statusPagamento != "":
            query = query.filter(SituacaoPagamentoModel.id == statusPagamento)

        query = query.order_by(
            case((FornecedorCadastroModel.identificacao == None, 1), else_=0),
            FornecedorCadastroModel.identificacao.asc(),
            FornecedorPagarModel.id.desc(),
        )

        registros = []
        for registro, registro_operacional in query.all():
            if registro:
                produto = getattr(registro.solicitacao.produto, "nome", "Indefinido")
                bitola = getattr(registro.solicitacao.bitola, "bitola", "")
                origem = registro.fornecedor.identificacao

                registros.append({
                    "registro": registro,
                    "produto": produto,
                    "origem": origem,
                    "tags": [ft.tag for ft in registro.fornecedor.fornecedor_tags if ft.ativo],
                    "bitola": bitola,
                    "registro_operacional": registro_operacional,
                })

        return registros
        

    def fornecedores_agrupados(
        data_inicio=None,
        data_fim=None,
        cliente=None,
        numero_nf=None,
        placa=None,
        motorista=None,
        transportadora=None,
        fornecedor=None,
        produto=None,
        bitola=None,
        statusPagamento=None,
        incompleto=None,
    ):
        from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import (RegistroOperacionalModel)

        query = (
            db.session.query(FornecedorPagarModel, RegistroOperacionalModel)
            .join(CargaModel, FornecedorPagarModel.solicitacao)
            .join(
                RegistroOperacionalModel,
                CargaModel.id == RegistroOperacionalModel.solicitacao_nf_id,
            )
            .join(FornecedorCadastroModel, FornecedorPagarModel.fornecedor)
            .join(BitolaModel, FornecedorPagarModel.bitola)
            .join(SituacaoPagamentoModel, FornecedorPagarModel.situacao)
            .join(ClienteModel, CargaModel.cliente)
            .join(VeiculoModel, CargaModel.veiculo)
            .join(MotoristaModel, CargaModel.motorista)
            .join(SituacaoPagamentoModel, FornecedorPagarModel.situacao)
            .filter(
                FornecedorPagarModel.deletado == False,
                FornecedorPagarModel.ativo == True,
            )
        )

        # Se datas forem fornecidas, aplica o filtro
        if data_inicio and data_fim:
            query = query.filter(
                FornecedorPagarModel.data_entrega_ticket.isnot(None),
                FornecedorPagarModel.data_entrega_ticket.between(data_inicio, data_fim),
            )
        elif data_inicio:
            query = query.filter(
                FornecedorPagarModel.data_entrega_ticket.isnot(None),
                FornecedorPagarModel.data_entrega_ticket >= data_inicio,
            )
        elif data_fim:
            query = query.filter(
                FornecedorPagarModel.data_entrega_ticket.isnot(None),
                FornecedorPagarModel.data_entrega_ticket <= data_fim,
            )

        if cliente:
            query = query.filter(ClienteModel.identificacao.ilike(f"%{cliente}%"))

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
            query = query.filter(ProdutoModel.nome.ilike(f"%{produto}%"))

        if bitola:
            query = query.filter(BitolaModel.bitola.ilike(f"%{bitola}%"))

        if motorista:
            query = query.filter(MotoristaModel.nome_completo.ilike(f"%{motorista}%"))

        if transportadora:
            query = query.outerjoin(
                TransportadoraModel,
                CargaModel.transportadora_id == TransportadoraModel.id,
            ).filter(
                TransportadoraModel.identificacao.ilike(f"%{transportadora}%")
            )

        if fornecedor:
            query = query.filter(FornecedorCadastroModel.identificacao.ilike(f"%{fornecedor}%"))

        if placa:
            query = query.filter(VeiculoModel.placa_veiculo.ilike(f"%{placa}%"))

        if statusPagamento:
            query = query.filter(
                SituacaoPagamentoModel.situacao.like(f"%{statusPagamento}%")
            )

        if incompleto:
            query = query.filter(FornecedorPagarModel.incompleto == incompleto)

        # Ordenação
        query = query.order_by(
            case((FornecedorCadastroModel.identificacao == None, 1), else_=0),
            FornecedorCadastroModel.identificacao.asc(),
            FornecedorPagarModel.id.desc(),
        )

        registros = []
        for registro, registro_operacional in query.all():
            if registro:

                produto = getattr(registro.solicitacao.produto, "nome", "Indefinido")
                bitola = getattr(registro.solicitacao.bitola, "bitola", "")
                origem = registro.fornecedor.identificacao

                registros.append(
                    {
                        "registro": registro,
                        "produto": produto,
                        "origem": origem,
                        "bitola": bitola,
                        "registro_operacional": registro_operacional,
                    }
                )

        return registros
    
    
    def listar_fornecedores_a_pagar_por_periodo_entrega(data_inicio=None, data_fim=None):
        """
        Lista fornecedores a pagar filtrados por período de data de entrega do ticket
        
        Args:
            data_inicio (date): Data de início do filtro
            data_fim (date): Data de fim do filtro
        
        Returns:
            List: Lista de fornecedores a pagar no período
        """
        query = FornecedorPagarModel.query
        # Aplicar filtros de data se fornecidos
        if data_inicio or data_fim:        
            if data_inicio:
                query = query.filter(FornecedorPagarModel.data_entrega_ticket >= data_inicio)
            
            if data_fim:
                data_fim_inclusiva = data_fim + timedelta(days=1)
                query = query.filter(FornecedorPagarModel.data_entrega_ticket < data_fim_inclusiva)
        
        # Filtrar apenas registros com data de entrega
        query = query.filter(FornecedorPagarModel.data_entrega_ticket.isnot(None))
        
        # Ordenar por data de entrega mais recente primeiro
        query = query.order_by(FornecedorPagarModel.data_entrega_ticket.desc())
        return query.all()