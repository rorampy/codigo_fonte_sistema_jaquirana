from ....base_model import BaseModel, db
from sqlalchemy import case, or_, and_, func
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.configuracoes_gerais.situacao_pagamento.situacao_pagamento_model import SituacaoPagamentoModel
from datetime import datetime, timedelta, date
from sistema.models_views.controle_carga.solicitacao_nf.carga_model import CargaModel
from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
from sistema.models_views.gerenciar.veiculo.veiculo_model import VeiculoModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_cadastro_model import FornecedorCadastroModel
from sistema.models_views.gerenciar.comissionado.comissionado_model import ComissionadoModel
from sistema.models_views.gerenciar.motorista.motorista_model import MotoristaModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema.models_views.gerenciar.motorista.transportadora_motorista_associado_model import TransportadoraMotoristaAssocModel
from sistema.models_views.financeiro.movimentacao_financeira.movimentacao_financeira_model import MovimentacaoFinanceiraModel


class ComissionadoPagarModel(BaseModel):
    __tablename__ = "fin_comissionado_a_pagar"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    solicitacao_id = db.Column(db.Integer, db.ForeignKey("car_carga.id"), nullable=True)
    solicitacao = db.relationship("CargaModel", backref=db.backref("fin_comissionado_a_pagar_solicitacao", lazy=True))
    fornecedor_id = db.Column(db.Integer, db.ForeignKey("for_fornecedor_cadastro.id"), nullable=True)
    fornecedor = db.relationship("FornecedorCadastroModel", backref=db.backref("fin_comissionado_a_pagar_fornecedor", lazy=True))
    comissionado_id = db.Column(db.Integer, db.ForeignKey("com_comissionado.id"), nullable=True)
    comissionado = db.relationship("ComissionadoModel", backref=db.backref("fin_comissionado_a_pagar", lazy=True))
    bitola_id = db.Column(db.Integer, db.ForeignKey("z_sys_bitola.id"), nullable=False)
    bitola = db.relationship("BitolaModel", backref=db.backref("fin_comissionado_a_pagar_bitola", lazy=True))
    situacao_pagamento_id = db.Column(db.Integer, db.ForeignKey("fin_situacao_pagamento.id"), nullable=False)
    situacao = db.relationship("SituacaoPagamentoModel", backref=db.backref("fin_comissionado_a_pagar_situacao", lazy=True))

    utiliza_credito = db.Column(db.Boolean, nullable=True)

    valor_credito_100 = db.Column(db.Integer, nullable=True)

    utiliza_saldo_movimentacao = db.Column(db.Boolean, nullable=True)

    valor_saldo_debitado_100 = db.Column(db.Integer, nullable=True)

    comprovante_pagamento_complementar_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    comprovante_pagamento_complementar = db.relationship("UploadArquivoModel", foreign_keys=[comprovante_pagamento_complementar_id], backref=db.backref("comprovante_pagamento_complementar_comissionado", lazy=True))

    comprovante_pagamento_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    comprovante_pagamento = db.relationship("UploadArquivoModel", foreign_keys=[comprovante_pagamento_id], backref=db.backref("comprovante_pagamento_comissionado", lazy=True))

    conta_bancaria_id = db.Column(db.Integer, db.ForeignKey("con_conta_bancaria.id"), nullable=True)
    conta_bancaria = db.relationship("ContaBancariaModel", foreign_keys=[conta_bancaria_id], backref=db.backref("conta_bancaria_a_pagar_comissionado", lazy=True))

    plano_conta_id = db.Column(db.Integer, db.ForeignKey("plan_plano_conta.id"), nullable=True)
    plano_conta = db.relationship("PlanoContaModel", foreign_keys=[plano_conta_id], backref=db.backref("plano_conta_pagar_comissionado", lazy=True))

    categorizacao_fiscal_id = db.Column(db.Integer, db.ForeignKey("ca_categorizacao_fiscal.id"), nullable=True)
    categorizacao_fiscal = db.relationship("CategorizacaoFiscalModel", foreign_keys=[categorizacao_fiscal_id], backref=db.backref("categorizacao_fiscal_pagar_comissionado", lazy=True))

    preco_custo_bitola_100 = db.Column(db.Integer, nullable=False)
    valor_total_a_pagar_100 = db.Column(db.Integer, nullable=False)

    movimentacao_financeira_id = db.Column(db.Integer, db.ForeignKey('mov_movimentacao_financeira.id'), nullable=True)
    movimentacao_financeira = db.relationship('MovimentacaoFinanceiraModel', foreign_keys=[movimentacao_financeira_id], backref=db.backref('comissionados_pagos_massa', lazy=True))

    data_entrega_ticket = db.Column(db.Date, nullable=True)
    data_liquidacao = db.Column(db.Date, nullable=True)
    incompleto = db.Column(db.Boolean, nullable=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    def __init__(
        self,
        solicitacao_id,
        fornecedor_id,
        comissionado_id,
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
        self.comissionado_id = comissionado_id
        self.bitola_id = bitola_id
        self.data_entrega_ticket = data_entrega_ticket
        self.data_liquidacao = data_liquidacao
        self.situacao_pagamento_id = situacao_pagamento_id
        self.preco_custo_bitola_100 = preco_custo_bitola_100
        self.valor_total_a_pagar_100 = valor_total_a_pagar_100
        self.incompleto = incompleto
        self.comprovante_pagamento_complementar_id = comprovante_pagamento_complementar_id
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

    @staticmethod
    def obter_comissionado_a_pagar_solicitacao(id):
        """
        Obtém um registro de comissionado a pagar específico por ID.
        
        Args:
            id (int): ID do registro de comissionado a pagar
        
        Returns:
            ComissionadoPagarModel: Objeto do comissionado a pagar encontrado ou None se não encontrar
        """
        return ComissionadoPagarModel.query.filter(
            ComissionadoPagarModel.deletado == False,
            ComissionadoPagarModel.ativo == True,
            ComissionadoPagarModel.solicitacao_id == id,
        ).first()
    
    @staticmethod
    def obter_comissionado_a_pagar_id(id):
        """
        Obtém um registro de comissionado a pagar específico por ID.
        
        Args:
            id (int): ID do registro de comissionado a pagar
        
        Returns:
            ComissionadoPagarModel: Objeto do comissionado a pagar encontrado ou None se não encontrar
        """
        return ComissionadoPagarModel.query.filter(
            ComissionadoPagarModel.deletado == False,
            ComissionadoPagarModel.ativo == True,
            ComissionadoPagarModel.id == id,
        ).first()

    @staticmethod
    def listar_comissionados_a_pagar():
        """
        Lista todos os comissionados a pagar ativos e não deletados, ordenados por ID decrescente.
        
        Returns:
            list: Lista de objetos ComissionadoPagarModel ativos e não deletados
        """
        return (
            ComissionadoPagarModel.query.filter(
                ComissionadoPagarModel.deletado == 0,
                ComissionadoPagarModel.ativo == 1,
            )
            .order_by(ComissionadoPagarModel.id.desc())
            .all()
        )

    @staticmethod
    def filtrar_comissionados_a_pagar(
        nomeFornecedor=None,
        nomeMotorista=None,
        nomeComissionado=None,
        bitola=None,
        produto=None,
        incompleto=None,
        statusPagamento=None,
        placaVeiculo=None,
    ):
        """
        Filtra comissionados a pagar por múltiplos critérios.
        
        Args:
            nomeFornecedor (str, optional): Nome/identificação do fornecedor
            nomeMotorista (str, optional): Nome completo do motorista
            nomeComissionado (str, optional): Nome/identificação do comissionado
            bitola (str, optional): Bitola
            produto (str, optional): Nome do produto
            incompleto (bool, optional): Se o registro está incompleto
            statusPagamento (str, optional): Status do pagamento
            placaVeiculo (str, optional): Placa do veículo
        
        Returns:
            list: Lista de objetos ComissionadoPagarModel que atendem aos critérios de filtro
        """
        query = (
            ComissionadoPagarModel.query
            .join(ComissionadoPagarModel.solicitacao)
            .join(CargaModel.produto)
            .join(CargaModel.veiculo)
            .join(CargaModel.motorista)
            .join(ComissionadoPagarModel.fornecedor)
            .join(ComissionadoPagarModel.comissionado)
            .join(ComissionadoPagarModel.bitola)
            .join(ComissionadoPagarModel.situacao)
            .filter(
                ComissionadoPagarModel.deletado == False,
                ComissionadoPagarModel.ativo == True
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

        if nomeComissionado:
            query = query.filter(
                ComissionadoModel.identificacao.ilike(f"%{nomeComissionado}%")
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
            query = query.filter(ComissionadoPagarModel.incompleto == incompleto)
            
        if placaVeiculo:
            query = query.filter(VeiculoModel.placa_veiculo.ilike(f"%{placaVeiculo}%"))
            
        return query.order_by(ComissionadoPagarModel.id.desc()).all()

    @staticmethod
    def obter_valor_total_a_pagar():
        """
        Calcula o valor total pendente de pagamento para comissionados.
        
        Considera apenas registros ativos, não deletados e com situação diferente de "pago" (id != 1).
        
        Returns:
            int: Valor total a pagar em centavos, ou 0 se não houver registros
        """
        a_pagar = ComissionadoPagarModel.query.filter(
            ComissionadoPagarModel.deletado == 0,
            ComissionadoPagarModel.ativo == 1,
            ComissionadoPagarModel.situacao_pagamento_id != 1,
        ).all()

        return (
            sum(
                a.valor_total_a_pagar_100 if a.valor_total_a_pagar_100 else 0
                for a in a_pagar
            )
            or 0
        )

    @staticmethod
    def obter_valor_total_pago():
        """
        Calcula o valor total já pago para comissionados.
        
        Considera apenas registros ativos, não deletados e pagos (situacao_pagamento_id == 1).
        
        Returns:
            int: Valor total pago em centavos, ou 0 se não houver registros
        """
        a_pagar = ComissionadoPagarModel.query.filter(
            ComissionadoPagarModel.deletado == 0,
            ComissionadoPagarModel.ativo == 1,
            ComissionadoPagarModel.situacao_pagamento_id == 1,
        ).all()

        return (
            sum(
                a.valor_total_a_pagar_100 if a.valor_total_a_pagar_100 else 0
                for a in a_pagar
            )
            or 0
        )

    @staticmethod
    def obter_valor_total_pago_por_conta(conta_id=1):
        """
        Calcula o valor total pago para comissionados através de uma conta bancária específica.
        
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
            .query(func.coalesce(func.sum(ComissionadoPagarModel.valor_saldo_debitado_100), 0))
            .join(
                MovimentacaoFinanceiraModel,
                and_(
                    MovimentacaoFinanceiraModel.comissionado_pagamento_id == ComissionadoPagarModel.id,
                    MovimentacaoFinanceiraModel.tipo_movimentacao == 2,
                )
            )
            .filter(
                ComissionadoPagarModel.deletado == False,
                ComissionadoPagarModel.ativo == True,
                ComissionadoPagarModel.situacao_pagamento_id == 1,
            )
        )

        if conta_id and conta_id != 0:
            q = q.filter(MovimentacaoFinanceiraModel.conta_bancaria_id == conta_id)

        total_centavos = q.scalar() or 0
        return total_centavos

    @staticmethod
    def obter_comissionados_agrupados():
        """
        Retorna todos os comissionados agrupados com informações relacionadas.
        
        Returns:
            list: Lista de dicionários com comissionados agrupados por origem, produto e bitola
        """
        from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
        from sistema.models_views.gerenciar.fornecedor.fornecedor_comissionado_model import FornecedorComissionadoModel

        query = (
            db.session.query(
                ComissionadoPagarModel, RegistroOperacionalModel, ComissionadoModel, FornecedorComissionadoModel
            )
            .join(CargaModel, ComissionadoPagarModel.solicitacao)
            .join(
                RegistroOperacionalModel,
                CargaModel.id == RegistroOperacionalModel.solicitacao_nf_id,
            )
            .join(FornecedorCadastroModel, ComissionadoPagarModel.fornecedor)
            .join(ComissionadoModel, ComissionadoPagarModel.comissionado)
            .outerjoin(
                FornecedorComissionadoModel,
                and_(
                    FornecedorComissionadoModel.fornecedor_id == ComissionadoPagarModel.fornecedor_id,
                    FornecedorComissionadoModel.comissionado_id == ComissionadoPagarModel.comissionado_id,
                    FornecedorComissionadoModel.deletado == False,
                    FornecedorComissionadoModel.ativo == True
                )
            )
            .join(BitolaModel, ComissionadoPagarModel.bitola)
            .join(SituacaoPagamentoModel, ComissionadoPagarModel.situacao)
            .join(ClienteModel, CargaModel.cliente)
            .join(VeiculoModel, CargaModel.veiculo)
            .join(MotoristaModel, CargaModel.motorista)
            .filter(
                ComissionadoPagarModel.deletado == False, 
                ComissionadoPagarModel.ativo == True,
                ComissionadoPagarModel.situacao_pagamento_id == 2
            )
            .order_by(
                ComissionadoModel.identificacao.asc(), 
                ComissionadoPagarModel.id.desc()
            )
        )

        registros = []
        for registro, registro_operacional, comissionado, vinculo_comissao in query.all():
            produto_nome = getattr(registro.solicitacao.produto, "nome", "Indefinido")
            bitola_nome = getattr(registro.solicitacao.bitola, "bitola", "")
            origem = registro.fornecedor.identificacao
            
            registros.append({
                "registro": registro,
                "produto": produto_nome,
                "origem": origem,
                "comissionado": comissionado,
                "bitola": bitola_nome,
                "registro_operacional": registro_operacional,
                "vinculo_comissao": vinculo_comissao,
            })

        return registros

    @staticmethod
    def filtrar_comissionados_agrupados(
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
        comissionado=None,
        incompleto=None,
        tipo_data_filtro=None,
    ):
        """
        Filtra e retorna comissionados agrupados com informações relacionadas.
        """
        from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import (
            RegistroOperacionalModel,
        )
        from sistema.models_views.gerenciar.fornecedor.fornecedor_comissionado_model import FornecedorComissionadoModel

        if tipo_data_filtro == 'data_emissao':
            campo_data = RegistroOperacionalModel.destinatario_data_emissao
        else:
            campo_data = RegistroOperacionalModel.data_entrega_ticket

        query = (
            db.session.query(
                ComissionadoPagarModel, RegistroOperacionalModel, ComissionadoModel, FornecedorComissionadoModel
            )
            .join(CargaModel, ComissionadoPagarModel.solicitacao)
            .join(
                RegistroOperacionalModel,
                CargaModel.id == RegistroOperacionalModel.solicitacao_nf_id,
            )
            .join(FornecedorCadastroModel, ComissionadoPagarModel.fornecedor)
            .join(ComissionadoModel, ComissionadoPagarModel.comissionado)
            .outerjoin(
                FornecedorComissionadoModel,
                and_(
                    FornecedorComissionadoModel.fornecedor_id == ComissionadoPagarModel.fornecedor_id,
                    FornecedorComissionadoModel.comissionado_id == ComissionadoPagarModel.comissionado_id,
                    FornecedorComissionadoModel.deletado == False,
                    FornecedorComissionadoModel.ativo == True
                )
            )
            .filter(
                ComissionadoPagarModel.deletado == False, 
                ComissionadoPagarModel.ativo == True
            )
        )

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
            query = query.join(BitolaModel, ComissionadoPagarModel.bitola).filter(BitolaModel.bitola.ilike(f"%{bitola}%"))

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
            query = query.join(SituacaoPagamentoModel, ComissionadoPagarModel.situacao).filter(SituacaoPagamentoModel.id == statusPagamento)

        if comissionado:
            query = query.filter(ComissionadoModel.identificacao.ilike(f"%{comissionado}%"))
            
        if incompleto is not None:
            query = query.filter(ComissionadoPagarModel.incompleto == incompleto)

        query = query.order_by(
            ComissionadoModel.identificacao.asc(), 
            ComissionadoPagarModel.id.desc()
        )

        query = query.order_by(
            ComissionadoModel.identificacao.asc(), 
            ComissionadoPagarModel.id.desc()
        )

        registros = []
        for registro, registro_operacional, comissionado, vinculo_comissao in query.all():
            produto_nome = getattr(registro.solicitacao.produto, "nome", "Indefinido")
            bitola_nome = getattr(registro.solicitacao.bitola, "bitola", "")
            origem = registro.fornecedor.identificacao
            
            registros.append({
                "registro": registro,
                "produto": produto_nome,
                "origem": origem,
                "comissionado": comissionado,
                "bitola": bitola_nome,
                "registro_operacional": registro_operacional,
                "vinculo_comissao": vinculo_comissao,
            })

        return registros

    @staticmethod
    def listar_comissionados_a_pagar_por_periodo_entrega(data_inicio=None, data_fim=None):
        """
        Lista comissionados a pagar filtrados por período de data de entrega do ticket
        
        Args:
            data_inicio (date): Data de início do filtro
            data_fim (date): Data de fim do filtro
        
        Returns:
            List: Lista de comissionados a pagar no período
        """
        query = ComissionadoPagarModel.query
        if data_inicio or data_fim:        
            if data_inicio:
                query = query.filter(ComissionadoPagarModel.data_entrega_ticket >= data_inicio)
            
            if data_fim:
                data_fim_inclusiva = data_fim + timedelta(days=1)
                query = query.filter(ComissionadoPagarModel.data_entrega_ticket < data_fim_inclusiva)
        
        query = query.filter(ComissionadoPagarModel.data_entrega_ticket.isnot(None))
        
        query = query.order_by(ComissionadoPagarModel.data_entrega_ticket.desc())
        return query.all()
