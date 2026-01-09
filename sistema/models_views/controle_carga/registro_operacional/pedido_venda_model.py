from ...base_model import BaseModel, db
from datetime import date, timedelta
from sqlalchemy import and_, or_, case, desc, asc, nullslast, func
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
from sistema import request
from sistema.models_views.configuracoes_gerais.situacao_pagamento.situacao_pagamento_model import SituacaoPagamentoModel
from sistema.models_views.controle_carga.solicitacao_nf.carga_model import CargaModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema.models_views.gerenciar.veiculo.veiculo_model import VeiculoModel
from sistema.models_views.gerenciar.motorista.motorista_model import MotoristaModel
from sistema.models_views.gerenciar.motorista.transportadora_motorista_associado_model import TransportadoraMotoristaAssocModel
from sistema.models_views.gerenciar.floresta.floresta_model import FlorestaModel
from sistema.models_views.faturamento.cargas_a_faturar.fornecedor.fornecedor_a_pagar_model import FornecedorPagarModel
from sistema.models_views.faturamento.cargas_a_faturar.extrator.extrator_a_pagar_model import ExtratorPagarModel
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema.models_views.gerenciar.veiculo.veiculo_transportadora_veiculo_associado_model import TransportadoraVeiculoAssocModel
from sistema.models_views.parametros.rotas_frete.rota_model import RotaFreteModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_cadastro_model import FornecedorCadastroModel
from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.faturamento.cargas_a_faturar.transportadora.frete_a_pagar_model import FretePagarModel
from sistema.models_views.faturamento.cargas_a_receber.vendas.recebimento_model import RecebimentoModel
from sistema.models_views.financeiro.movimentacao_financeira.movimentacao_financeira_model import MovimentacaoFinanceiraModel
from sistema._utilitarios import *
from sistema._utilitarios.extracao_texto_nota_fiscal import ExtrairTextoNotaFiscal
from sistema.models_views.upload_arquivo.upload_arquivo_model import UploadArquivoModel

class PedidoVendaModel(BaseModel):
    """
    Model unificada para registro de emissão de nota fiscal e ticket
    """

    __tablename__ = "ped_pedido_venda"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    solicitacao_pedido_venda_id = db.Column(db.Integer, db.ForeignKey("spv_solicitacao_pedido_venda.id"), nullable=True)
    solicitacao = db.relationship("SolicitacaoPedidoVendaModel", backref=db.backref("pedido_venda_solicitacao", lazy=True))

    situacao_financeira_id = db.Column(db.Integer, db.ForeignKey("fin_situacao_pagamento.id"), nullable=True)
    situacao = db.relationship("SituacaoPagamentoModel",backref=db.backref("pedido_venda_situacao_financeira", lazy=True))
    
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    def __init__(self, solicitacao_pedido_venda_id, situacao_financeira_id=None, ativo=True):
        self.solicitacao_pedido_venda_id = solicitacao_pedido_venda_id
        self.situacao_financeira_id = situacao_financeira_id
        self.ativo = ativo
        
    @staticmethod
    def obter_pedido_venda_por_id(pedido_venda_id):
        """
        Obtém um pedido de venda pelo ID.
        
        Args:
            pedido_venda_id (int): ID do pedido de venda
            
        Returns:
            PedidoVendaModel: Pedido de venda encontrado ou None
        """
        return PedidoVendaModel.query.filter_by(
            id=pedido_venda_id,
            ativo=True,
            deletado=False
        ).first()
    
    @staticmethod
    def obter_pedido_venda_por_solicitacao_id(solicitacao_id):
        """
        Obtém um pedido de venda pela solicitação.
        
        Args:
            solicitacao_id (int): ID da solicitação
            
        Returns:
            PedidoVendaModel: Pedido de venda encontrado ou None
        """
        return PedidoVendaModel.query.filter_by(
            solicitacao_pedido_venda_id=solicitacao_id,
            ativo=True,
            deletado=False
        ).first()
    
    @staticmethod
    def criar_pedido_venda(solicitacao_pedido_venda_id, situacao_financeira_id=None):
        """
        Cria um novo pedido de venda.
        
        Args:
            solicitacao_pedido_venda_id (int): ID da solicitação
            situacao_financeira_id (int, optional): ID da situação financeira
            
        Returns:
            PedidoVendaModel: Instância criada e salva
        """
        pedido = PedidoVendaModel(
            solicitacao_pedido_venda_id=solicitacao_pedido_venda_id,
            situacao_financeira_id=situacao_financeira_id,
            ativo=True
        )
        db.session.add(pedido)
        db.session.flush()
        return pedido
    
    @staticmethod
    def listar_vendas(pagina=1, por_pagina=200, categoria_venda='transito'):
        """
        Lista pedidos de venda com filtros básicos.
        
        Args:
            pagina (int): Página atual
            por_pagina (int): Registros por página
            categoria_venda (str): 'transito' ou 'entregue'
            
        Returns:
            dict: Dicionário com registros e informações de paginação
        """
        from sistema.models_views.controle_carga.solicitacao_nf.solicitacao_pedido_venda_model import SolicitacaoPedidoVendaModel
        
        query = db.session.query(PedidoVendaModel).join(
            SolicitacaoPedidoVendaModel,
            PedidoVendaModel.solicitacao_pedido_venda_id == SolicitacaoPedidoVendaModel.id
        ).filter(
            PedidoVendaModel.ativo == True,
            PedidoVendaModel.deletado == False,
            SolicitacaoPedidoVendaModel.nf_emitida == True,
            SolicitacaoPedidoVendaModel.cancelada == False
        )
        
        if categoria_venda == 'transito':
            query = query.filter(SolicitacaoPedidoVendaModel.ticket_emitido == False)
        elif categoria_venda == 'entregue':
            query = query.filter(SolicitacaoPedidoVendaModel.ticket_emitido == True)
        
        query = query.order_by(PedidoVendaModel.id.desc())
        
        paginacao = query.paginate(page=pagina, per_page=por_pagina, error_out=False)
        
        return {
            'registros': paginacao.items,
            'total': paginacao.total,
            'total_paginas': paginacao.pages,
            'pagina': paginacao.page,
            'por_pagina': por_pagina,
            'tem_proximo': paginacao.has_next,
            'tem_anterior': paginacao.has_prev,
            'proxima_pagina': paginacao.next_num if paginacao.has_next else None,
            'pagina_anterior': paginacao.prev_num if paginacao.has_prev else None
        }
    
    @staticmethod
    def listar_vendas_filtrar(cliente_venda='', nf_venda='', produto_venda='', bitola_venda='',
                              transportadora_venda='', motorista_venda='', placa_venda='',
                              origem_venda='', data_inicio='', data_fim='', pagina=1,
                              por_pagina=200, categoria_venda='transito'):
        """
        Lista pedidos de venda com filtros avançados.
        """
        from sistema.models_views.controle_carga.solicitacao_nf.solicitacao_pedido_venda_model import SolicitacaoPedidoVendaModel
        from sistema.models_views.controle_carga.registro_operacional.pedido_venda_dados_nf_model import PedidoVendaDadosNfModel
        
        query = db.session.query(PedidoVendaModel).join(
            SolicitacaoPedidoVendaModel,
            PedidoVendaModel.solicitacao_pedido_venda_id == SolicitacaoPedidoVendaModel.id
        ).join(
            PedidoVendaDadosNfModel,
            PedidoVendaModel.id == PedidoVendaDadosNfModel.pedido_venda_id
        ).filter(
            PedidoVendaModel.ativo == True,
            PedidoVendaModel.deletado == False,
            PedidoVendaDadosNfModel.ativo == True,
            PedidoVendaDadosNfModel.deletado == False,
            SolicitacaoPedidoVendaModel.nf_emitida == True,
            SolicitacaoPedidoVendaModel.cancelada == False
        )
        
        if categoria_venda == 'transito':
            query = query.filter(SolicitacaoPedidoVendaModel.ticket_emitido == False)
        elif categoria_venda == 'entregue':
            query = query.filter(SolicitacaoPedidoVendaModel.ticket_emitido == True)
        
        if cliente_venda:
            query = query.join(ClienteModel, SolicitacaoPedidoVendaModel.cliente_id == ClienteModel.id).filter(
                ClienteModel.identificacao.ilike(f'%{cliente_venda}%')
            )
        
        if nf_venda:
            query = query.filter(
                or_(
                    PedidoVendaDadosNfModel.numero_nota_fiscal.ilike(f'%{nf_venda}%'),
                    PedidoVendaDadosNfModel.numero_nota_fiscal_estorno.ilike(f'%{nf_venda}%')
                )
            )
        
        if produto_venda:
            query = query.filter(SolicitacaoPedidoVendaModel.produto_id == produto_venda)
        
        if bitola_venda:
            query = query.filter(SolicitacaoPedidoVendaModel.bitola_id == bitola_venda)
        
        if transportadora_venda:
            query = query.join(TransportadoraModel, SolicitacaoPedidoVendaModel.transportadora_id == TransportadoraModel.id).filter(
                TransportadoraModel.identificacao.ilike(f'%{transportadora_venda}%')
            )
        
        if motorista_venda:
            query = query.join(MotoristaModel, SolicitacaoPedidoVendaModel.motorista_id == MotoristaModel.id).filter(
                MotoristaModel.nome_completo.ilike(f'%{motorista_venda}%')
            )
        
        if placa_venda:
            query = query.join(VeiculoModel, SolicitacaoPedidoVendaModel.veiculo_id == VeiculoModel.id).filter(
                VeiculoModel.placa_veiculo.ilike(f'%{placa_venda}%')
            )
        
        if data_inicio:
            try:
                data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                query = query.filter(PedidoVendaDadosNfModel.destinatario_data_emissao >= data_inicio_obj)
            except:
                pass
        
        if data_fim:
            try:
                data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
                query = query.filter(PedidoVendaDadosNfModel.destinatario_data_emissao <= data_fim_obj)
            except:
                pass
        
        query = query.order_by(PedidoVendaModel.id.desc())
        
        paginacao = query.paginate(page=pagina, per_page=por_pagina, error_out=False)
        
        return {
            'registros': paginacao.items,
            'total': paginacao.total,
            'total_paginas': paginacao.pages,
            'pagina': paginacao.page,
            'por_pagina': por_pagina,
            'tem_proximo': paginacao.has_next,
            'tem_anterior': paginacao.has_prev,
            'proxima_pagina': paginacao.next_num if paginacao.has_next else None,
            'pagina_anterior': paginacao.prev_num if paginacao.has_prev else None
        }
    
    @staticmethod
    def extrair_dados_frf_form(request):
        """
        Extrai e valida os dados do formulário para FRF (campos manuais).
        """
        destinatarioFrf = request.form.get("destinatarioFrf", "")
        destinatarioNumeroDocumento = request.form.get("destinatarioNumeroDocumento", "")
        dataLancamentoFrf = request.form.get("dataLancamentoFrf", "")
        transportadorFrf = request.form.get("transportadorFrf", "")
        transportadoraNumeroDocumento = request.form.get("transportadoraNumeroDocumento", "")
        placaFrf = request.form.get("placaFrf", "")
        motoristaFrf = request.form.get("motoristaFrf", "")
        pesoFrf = request.form.get("pesoFrf", "")
        valorTotalFrf = request.form.get("valorTotalFrf", "")
        return {
            "destinatario_nome": destinatarioFrf,
            "destinatario_cnpj_cpf": destinatarioNumeroDocumento,
            "destinatario_data_emissao": dataLancamentoFrf,
            "transportador_nome": transportadorFrf,
            "transportador_cnpj_cpf": transportadoraNumeroDocumento,
            "placa_nf": placaFrf,
            "motorista_nf": motoristaFrf,
            "peso_ton_nf": pesoFrf,
            "valor_total_nota_100": valorTotalFrf,
        }
    
    @staticmethod
    def extrair_dados_nf_xml(dados_xml):
        """
        Processa os dados extraídos do XML da nota fiscal.
        """
        # Dados do emissor
        razao_social_emissor = dados_xml["emissor"].get("razao_social_emissor", "")
        numero_nota_fiscal = dados_xml["emissor"].get("numero_nota", "")
        serie_nota = dados_xml["emissor"].get("serie", "")
        chave_acesso = dados_xml["emissor"].get("chave_acesso", "")
        
        # Dados do destinatário
        destinatario_nome = dados_xml["destinatario"].get("nome_razao_social", "")
        destinatario_cnpj_cpf = dados_xml["destinatario"].get("cnpj_cpf", "")
        destinatario_insc_estadual = dados_xml["destinatario"].get("insc_estadual", "")
        destinatario_data_emissao = dados_xml["destinatario"].get("data_emissao", "")
        
        # Dados do transportador
        transportador_nome = dados_xml["transportador"].get("nome", "")
        transportador_cnpj_cpf = dados_xml["transportador"].get("cnpj_cpf", "")
        transportador_insc_estadual = dados_xml["transportador"].get("insc_estadual", "")
        
        # Dados adicionais
        placa_nf = dados_xml["dados_adicionais"].get("placa", "")
        motorista_nf = dados_xml["dados_adicionais"].get("motorista", "")
        
        # Valor total da nota (já está em reais no XML)
        valor_total_nota = dados_xml["calculo_imposto"].get("valor_total_nota", "0")
        valor_total_nota_centavos = int(float(valor_total_nota) * 100) if valor_total_nota else 0
        
        # Calcular peso e valores dos itens
        peso_nf = 0
        preco_un = 0
        for item in dados_xml["itens"]:
            quantidade = item.get("quantidade", "0").replace(',', '.')
            peso_nf += round(float(quantidade), 2) if quantidade else 0
            
            preco_unitario = item.get("preco_unitario", "0").replace(',', '.')
            if preco_unitario:
                preco_un += int(round(float(preco_unitario) * 100))
        
        return {
            "razao_social_emissor": razao_social_emissor,
            "numero_nota_fiscal": numero_nota_fiscal,
            "serie_nota": serie_nota,
            "chave_acesso": chave_acesso,
            "destinatario_nome": destinatario_nome,
            "destinatario_cnpj_cpf": destinatario_cnpj_cpf,
            "destinatario_insc_estadual": destinatario_insc_estadual,
            "destinatario_data_emissao": destinatario_data_emissao,
            "valor_total_nota_100": valor_total_nota_centavos,
            "preco_un_nf": preco_un,
            "transportador_nome": transportador_nome,
            "transportador_cnpj_cpf": transportador_cnpj_cpf,
            "transportador_insc_estadual": transportador_insc_estadual,
            "placa_nf": placa_nf,
            "motorista_nf": motorista_nf,
            "peso_ton_nf": peso_nf,
        }

    @staticmethod
    def extrair_dados_nf_excesso_xml(dados_xml):
        """
        Processa os dados de excesso extraídos do XML.
        """
        numero_nota_excessao = dados_xml["emissor"].get("numero_nota", "")
        peso_nf_excesso = 0
        
        for item in dados_xml["itens"]:
            quantidade = item.get("quantidade", "0").replace(',', '.')
            peso_nf_excesso += round(float(quantidade), 2) if quantidade else 0
        
        return {
            "numero_nota_fiscal_excessao": numero_nota_excessao,
            "peso_ton_nf_excesso": peso_nf_excesso,
        }
    
    @staticmethod
    def extrair_dados_nota_fiscal(objeto_nf_xml):
        """
        Extrai dados da nota fiscal SEMPRE e APENAS do XML (obrigatório).
        """
        if not objeto_nf_xml or not objeto_nf_xml.caminho:
            raise ValueError("XML é obrigatório e deve ser fornecido")
        
        try:
            dados_xml = ExtrairTextoNotaFiscal.nf_extrair_dados_nota_xml(objeto_nf_xml.caminho)
            
            if not (dados_xml.get("emissor", {}).get("numero_nota") and 
                    dados_xml.get("destinatario", {}).get("nome_razao_social") and 
                    dados_xml.get("calculo_imposto", {}).get("valor_total_nota")):
                raise ValueError("XML não contém dados essenciais para processamento")
            
            dados_nf = PedidoVendaModel.extrair_dados_nf_xml(dados_xml)
            print(f"[INFO] Dados extraídos do XML com sucesso")
            return dados_nf
            
        except Exception as e:
            print(f"[ERRO] Falha ao processar XML obrigatório: {e}")
            raise e

    @staticmethod
    def extrair_dados_nota_excesso(objeto_nf_excesso_xml):
        """
        Extrai dados da nota fiscal de excesso SEMPRE e APENAS do XML (obrigatório).
        """
        if not objeto_nf_excesso_xml or not objeto_nf_excesso_xml.caminho:
            raise ValueError("XML de excesso é obrigatório e deve ser fornecido")
        
        try:
            dados_xml = ExtrairTextoNotaFiscal.nf_extrair_dados_nota_xml(objeto_nf_excesso_xml.caminho)
            
            if not (dados_xml.get("emissor", {}).get("numero_nota") and 
                    dados_xml.get("itens")):
                raise ValueError("XML de excesso não contém dados essenciais")
            
            dados_excesso = PedidoVendaModel.extrair_dados_nf_excesso_xml(dados_xml)
            print(f"[INFO] Dados de excesso extraídos do XML com sucesso")
            return dados_excesso
            
        except Exception as e:
            print(f"[ERRO] Falha ao processar XML de excesso: {e}")
            raise e

    @staticmethod
    def obter_registros_carga_agrupados():
        """
        Retorna todos os registros de pedido de venda (cargas entregues) agrupados por cliente e produto.
        Filtra apenas os que têm ticket emitido e situação financeira pendente (id=2).
        
        Returns:
            list: Lista de dicionários com registros agrupados
        """
        from sistema.models_views.controle_carga.solicitacao_nf.solicitacao_pedido_venda_model import SolicitacaoPedidoVendaModel
        from sistema.models_views.controle_carga.registro_operacional.pedido_venda_dados_nf_model import PedidoVendaDadosNfModel
        from sistema.models_views.controle_carga.registro_operacional.pedido_venda_dados_ticket_model import PedidoVendaDadosTicketModel
        
        data_inicio = date.today() - timedelta(days=30)
        data_fim = date.today()
        
        query = (
            db.session.query(PedidoVendaModel, ClienteModel)
            .join(SolicitacaoPedidoVendaModel, PedidoVendaModel.solicitacao_pedido_venda_id == SolicitacaoPedidoVendaModel.id)
            .join(ClienteModel, SolicitacaoPedidoVendaModel.cliente_id == ClienteModel.id)
            .join(PedidoVendaDadosNfModel, PedidoVendaModel.id == PedidoVendaDadosNfModel.pedido_venda_id)
            .outerjoin(PedidoVendaDadosTicketModel, PedidoVendaModel.id == PedidoVendaDadosTicketModel.pedido_venda_id)
            .filter(
                PedidoVendaModel.deletado.is_(False),
                PedidoVendaModel.ativo.is_(True),
                PedidoVendaDadosNfModel.deletado.is_(False),
                PedidoVendaDadosNfModel.ativo.is_(True),
                SolicitacaoPedidoVendaModel.ticket_emitido == True,
                SolicitacaoPedidoVendaModel.cancelada == False,
                PedidoVendaModel.situacao_financeira_id == 2  # Pendente
            )
        )

        # Filtrar por data do ticket
        query = query.filter(
            PedidoVendaDadosTicketModel.data_entrega_ticket.isnot(None),
            PedidoVendaDadosTicketModel.data_entrega_ticket.between(data_inicio, data_fim),
        )

        resultados = []
        for pedido_venda, cliente in query.all():
            produto_nome = "Indefinido"
            if pedido_venda.solicitacao and pedido_venda.solicitacao.produto:
                produto_nome = pedido_venda.solicitacao.produto.nome
            
            resultados.append({
                "cliente": cliente.identificacao,
                "produto": produto_nome,
                "registro": pedido_venda,  # Mantém compatibilidade com templates existentes
                "pedido_venda": pedido_venda,
            })

        resultados.sort(key=lambda x: (x["cliente"], x["produto"]))
        return resultados

    @staticmethod
    def filtrar_registros_carga_cliente(
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
        status_nf_complementar=None,
        status_pagamento=None,
    ):
        """
        Filtra e retorna registros de pedido de venda (cargas) agrupados por cliente e produto.
        
        Args:
            data_inicio (date, optional): Data inicial do filtro
            data_fim (date, optional): Data final do filtro
            cliente (str, optional): Nome/identificação do cliente
            numero_nf (str, optional): Número da nota fiscal
            placa (str, optional): Placa do veículo
            motorista (str, optional): Nome do motorista
            transportadora (str, optional): Nome da transportadora
            fornecedor (str, optional): Nome do fornecedor
            produto (str, optional): Nome do produto
            bitola (str, optional): Bitola
            status_nf_complementar (int, optional): Status da NF complementar
            status_pagamento (int, optional): ID da situação financeira
        
        Returns:
            list: Lista de dicionários com registros filtrados e agrupados
        """
        from sistema.models_views.controle_carga.solicitacao_nf.solicitacao_pedido_venda_model import SolicitacaoPedidoVendaModel
        from sistema.models_views.controle_carga.registro_operacional.pedido_venda_dados_nf_model import PedidoVendaDadosNfModel
        from sistema.models_views.controle_carga.registro_operacional.pedido_venda_dados_ticket_model import PedidoVendaDadosTicketModel
        
        if not data_inicio or not data_fim:
            data_inicio = date.today() - timedelta(days=30)
            data_fim = date.today()

        query = (
            db.session.query(PedidoVendaModel, ClienteModel)
            .join(SolicitacaoPedidoVendaModel, PedidoVendaModel.solicitacao_pedido_venda_id == SolicitacaoPedidoVendaModel.id)
            .join(ClienteModel, SolicitacaoPedidoVendaModel.cliente_id == ClienteModel.id)
            .join(PedidoVendaDadosNfModel, PedidoVendaModel.id == PedidoVendaDadosNfModel.pedido_venda_id)
            .outerjoin(PedidoVendaDadosTicketModel, PedidoVendaModel.id == PedidoVendaDadosTicketModel.pedido_venda_id)
            .join(MotoristaModel, SolicitacaoPedidoVendaModel.motorista_id == MotoristaModel.id)
            .join(VeiculoModel, SolicitacaoPedidoVendaModel.veiculo_id == VeiculoModel.id)
            .join(ProdutoModel, SolicitacaoPedidoVendaModel.produto_id == ProdutoModel.id)
            .join(BitolaModel, SolicitacaoPedidoVendaModel.bitola_id == BitolaModel.id)
            .filter(
                PedidoVendaModel.deletado.is_(False),
                PedidoVendaModel.ativo.is_(True),
                PedidoVendaDadosNfModel.deletado.is_(False),
                PedidoVendaDadosNfModel.ativo.is_(True),
                SolicitacaoPedidoVendaModel.ticket_emitido == True,
                SolicitacaoPedidoVendaModel.cancelada == False,
            )
        )

        # Filtro por data
        if data_inicio and data_fim:
            query = query.filter(
                PedidoVendaDadosTicketModel.data_entrega_ticket.isnot(None),
                PedidoVendaDadosTicketModel.data_entrega_ticket.between(data_inicio, data_fim),
            )
        elif data_inicio:
            query = query.filter(
                PedidoVendaDadosTicketModel.data_entrega_ticket.isnot(None),
                PedidoVendaDadosTicketModel.data_entrega_ticket >= data_inicio,
            )
        elif data_fim:
            query = query.filter(
                PedidoVendaDadosTicketModel.data_entrega_ticket.isnot(None),
                PedidoVendaDadosTicketModel.data_entrega_ticket <= data_fim,
            )

        # Filtro por cliente
        if cliente:
            query = query.filter(ClienteModel.identificacao.ilike(f"%{cliente}%"))

        # Filtro por número NF
        if numero_nf:
            query = query.filter(
                or_(
                    PedidoVendaDadosNfModel.numero_nota_fiscal.ilike(f"%{numero_nf}%"),
                    PedidoVendaDadosNfModel.numero_nota_fiscal_excessao.ilike(f"%{numero_nf}%"),
                    PedidoVendaDadosNfModel.numero_nota_fiscal_estorno.ilike(f"%{numero_nf}%"),
                )
            )

        # Filtro por status NF complementar
        if status_nf_complementar:
            query = query.filter(
                PedidoVendaDadosNfModel.status_emissao_nf_complementar_id == status_nf_complementar
            )

        # Filtro por produto
        if produto:
            query = query.filter(ProdutoModel.nome.ilike(f"%{produto}%"))

        # Filtro por bitola
        if bitola:
            query = query.filter(BitolaModel.bitola.ilike(f"%{bitola}%"))

        # Filtro por motorista
        if motorista:
            query = query.filter(MotoristaModel.nome_completo.ilike(f"%{motorista}%"))

        # Filtro por transportadora
        if transportadora:
            query = query.outerjoin(
                TransportadoraModel,
                SolicitacaoPedidoVendaModel.transportadora_id == TransportadoraModel.id,
            ).filter(
                TransportadoraModel.identificacao.ilike(f"%{transportadora}%")
            )

        # Filtro por placa
        if placa:
            query = query.filter(VeiculoModel.placa_veiculo.ilike(f"%{placa}%"))

        # Filtro por status de pagamento
        if status_pagamento:
            query = query.filter(PedidoVendaModel.situacao_financeira_id == status_pagamento)

        resultados = []
        for pedido_venda, cliente in query.all():
            produto_nome = "Indefinido"
            if pedido_venda.solicitacao and pedido_venda.solicitacao.produto:
                produto_nome = pedido_venda.solicitacao.produto.nome
            
            resultados.append({
                "cliente": cliente.identificacao,
                "produto": produto_nome,
                "registro": pedido_venda,  # Mantém compatibilidade com templates existentes
                "pedido_venda": pedido_venda,
            })

        resultados.sort(key=lambda x: (x["cliente"], x["produto"]))
        return resultados

    @staticmethod
    def obter_por_id(id):
        """
        Obtém um pedido de venda pelo ID.
        Método de compatibilidade com o antigo RegistroOperacionalModel.
        
        Args:
            id (int): ID do pedido de venda
            
        Returns:
            PedidoVendaModel: Pedido de venda encontrado ou None
        """
        return PedidoVendaModel.query.filter_by(
            id=id,
            ativo=True,
            deletado=False
        ).first()
    
    @property
    def dados_nf(self):
        """
        Obtém os dados da NF associada ao pedido de venda.
        
        Returns:
            PedidoVendaDadosNfModel: Dados da NF ou None
        """
        from sistema.models_views.controle_carga.registro_operacional.pedido_venda_dados_nf_model import PedidoVendaDadosNfModel
        return PedidoVendaDadosNfModel.obter_dados_nf_por_pedido_venda_id(self.id)
    
    @property
    def dados_ticket(self):
        """
        Obtém os dados do ticket associado ao pedido de venda.
        
        Returns:
            PedidoVendaDadosTicketModel: Dados do ticket ou None
        """
        from sistema.models_views.controle_carga.registro_operacional.pedido_venda_dados_ticket_model import PedidoVendaDadosTicketModel
        return PedidoVendaDadosTicketModel.obter_dados_ticket_por_pedido_venda_id(self.id)
    
    # Propriedades de compatibilidade com RegistroOperacionalModel
    @property
    def numero_nota_fiscal(self):
        """Retorna o número da nota fiscal do pedido de venda"""
        dados = self.dados_nf
        return dados.numero_nota_fiscal if dados else None
    
    @property
    def valor_total_nota_100(self):
        """Retorna o valor total da nota em centavos"""
        dados = self.dados_nf
        return dados.valor_total_nota_100 if dados else 0
    
    @valor_total_nota_100.setter
    def valor_total_nota_100(self, value):
        """Define o valor total da nota em centavos"""
        dados = self.dados_nf
        if dados:
            dados.valor_total_nota_100 = value
    
    @property
    def preco_un_nf(self):
        """Retorna o preço unitário da NF"""
        dados = self.dados_nf
        return dados.preco_un_nf if dados else 0
    
    @property
    def peso_liquido_ticket(self):
        """Retorna o peso líquido do ticket"""
        dados = self.dados_ticket
        return dados.peso_liquido_ticket if dados else 0
    
    @property
    def data_entrega_ticket(self):
        """Retorna a data de entrega do ticket"""
        dados = self.dados_ticket
        return dados.data_entrega_ticket if dados else None
    
    @property
    def estorno_nf(self):
        """Retorna se houve estorno da NF"""
        dados = self.dados_nf
        return dados.estorno_nf if dados else False
    
    @property
    def numero_nota_fiscal_estorno(self):
        """Retorna o número da NF de estorno"""
        dados = self.dados_nf
        return dados.numero_nota_fiscal_estorno if dados else None
    
    @property
    def fornecedor_id(self):
        """Retorna o ID do fornecedor do ticket"""
        dados = self.dados_ticket
        return dados.fornecedor_id if dados else None
