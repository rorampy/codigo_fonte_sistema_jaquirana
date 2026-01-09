from datetime import date, timedelta
from ...base_model import BaseModel, db
from sistema import request
from sistema.models_views.controle_carga.registro_operacional.pedido_venda_model import PedidoVendaModel
from sistema.models_views.controle_carga.registro_operacional.pedido_venda_dados_ticket_model import PedidoVendaDadosTicketModel
from sistema.models_views.controle_carga.solicitacao_nf.solicitacao_pedido_venda_model import SolicitacaoPedidoVendaModel
from sqlalchemy import desc


class NfEntradaModel(BaseModel):
    """
    Model para registro d NFs de entrada
    """

    __tablename__ = "re_nf_entrada"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    registro_id = db.Column(db.Integer, db.ForeignKey("re_registro_operacional.id"), nullable=True)
    registro = db.relationship("RegistroOperacionalModel", backref=db.backref("rp_registro", lazy=True))

    # Nova referência para as novas models
    pedido_venda_id = db.Column(db.Integer, db.ForeignKey("ped_pedido_venda.id"), nullable=True)
    pedido_venda = db.relationship("PedidoVendaModel", backref=db.backref("nf_entrada", lazy=True))

    peso_contra_nota = db.Column(db.Float, nullable=True)

    arquivo_nf_entrada_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    arquivo_nf_entrada = db.relationship("UploadArquivoModel",foreign_keys=[arquivo_nf_entrada_id],backref=db.backref("up_nf_entrada", lazy=True),)

    arquivo_contra_nota_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    arquivo_contra_nota = db.relationship("UploadArquivoModel", foreign_keys=[arquivo_contra_nota_id], backref=db.backref("up_nf_contra_nota", lazy=True))

    arquivo_cte_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    arquivo_cte = db.relationship("UploadArquivoModel", foreign_keys=[arquivo_cte_id], backref=db.backref("up_nf_cte", lazy=True))

    arquivo_mdf_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    arquivo_mdf = db.relationship("UploadArquivoModel", foreign_keys=[arquivo_mdf_id], backref=db.backref("up_nf_mdf", lazy=True))

    ativo = db.Column(db.Boolean, default=True, nullable=False)

    def __init__(
        self,
        registro_id=None,
        pedido_venda_id=None,
        peso_contra_nota=None,
        arquivo_nf_entrada_id=None,
        arquivo_contra_nota_id=None,
        arquivo_cte_id=None,
        arquivo_mdf_id=None,
    ):
        self.registro_id = registro_id
        self.pedido_venda_id = pedido_venda_id
        self.peso_contra_nota = peso_contra_nota
        self.arquivo_nf_entrada_id = arquivo_nf_entrada_id
        self.arquivo_contra_nota_id = arquivo_contra_nota_id
        self.arquivo_cte_id = arquivo_cte_id
        self.arquivo_mdf_id = arquivo_mdf_id


    def obter_nf_entrada_agrupadas():
        """
        Retorna todas as NFs de entrada ativas agrupadas por origem, produto e bitola. (últimos 30 dias)
        Utiliza as novas models: PedidoVendaModel e PedidoVendaDadosTicketModel
        
        Returns:
            list: Lista de dicionários com NFs de entrada agrupadas
        """

        data_inicio = date.today() - timedelta(days=30)
        data_fim = date.today()

        # Query principal para buscar NF de entrada com pedido de venda
        query = (
            db.session.query(
                NfEntradaModel, 
                PedidoVendaModel, 
                SolicitacaoPedidoVendaModel
            )
            .join(
                PedidoVendaModel,
                NfEntradaModel.pedido_venda_id == PedidoVendaModel.id,
            )
            .join(
                SolicitacaoPedidoVendaModel,
                PedidoVendaModel.solicitacao_pedido_venda_id == SolicitacaoPedidoVendaModel.id,
            )
            .filter(
                NfEntradaModel.deletado == False, 
                NfEntradaModel.ativo == True,
                NfEntradaModel.pedido_venda_id.isnot(None)
            )
            .order_by(desc(NfEntradaModel.id))
        )

        registros = []
        
        for nfentrada, pedido_venda, solicitacao in query.all():
            # Buscar todos os dados de ticket para este pedido de venda
            dados_tickets = PedidoVendaDadosTicketModel.query.filter(
                PedidoVendaDadosTicketModel.pedido_venda_id == pedido_venda.id,
                PedidoVendaDadosTicketModel.ativo == True,
                PedidoVendaDadosTicketModel.deletado == False
            ).all()
            
            if not dados_tickets:
                continue
                
            # Filtrar por data se especificado
            primeiro_ticket = dados_tickets[0]
            if primeiro_ticket.data_entrega_ticket:
                if data_inicio and primeiro_ticket.data_entrega_ticket < data_inicio:
                    continue
                if data_fim and primeiro_ticket.data_entrega_ticket > data_fim:
                    continue
            else:
                continue
            
            # Calcular peso total de todos os fornecedores
            peso_total_ticket = sum(t.peso_liquido_ticket or 0 for t in dados_tickets)
            
            # Determinar origem (primeiro fornecedor)
            origem = "Indefinido"
            primeiro_fornecedor = None
            if dados_tickets and dados_tickets[0].fornecedor_id:
                primeiro_fornecedor = dados_tickets[0].fornecedor
                if primeiro_fornecedor and primeiro_fornecedor.identificacao:
                    if primeiro_fornecedor.controle_entrada == False:
                        origem = "Outros fornecedores"
                    else:
                        origem = primeiro_fornecedor.identificacao
                
            produto = getattr(solicitacao.produto, "nome", "Indefinido") if solicitacao else "Indefinido"
            bitola = getattr(solicitacao.bitola, "bitola", "") if solicitacao else ""

            registros.append({
                "origem": origem,
                "produto": produto,
                "bitola": bitola,
                "pedido_venda": pedido_venda,
                "dados_ticket": primeiro_ticket,  # Para data/numero NF
                "dados_tickets": dados_tickets,   # Todos os tickets
                "peso_total_ticket": peso_total_ticket,  # Peso somado
                "solicitacao": solicitacao,
                "nfentrada": nfentrada
            })
            
        return registros
    

    def filtrar_nf_entrada_ativas(
        data_inicio=None,
        data_fim=None,
        numero_nf=None,
        origem=None,
    ):
        """
        Filtra e retorna NFs de entrada ativas agrupadas por origem, produto e bitola.
        Utiliza as novas models: PedidoVendaModel e PedidoVendaDadosTicketModel
        
        Args:
            data_inicio (date, optional): Data inicial do filtro
            data_fim (date, optional): Data final do filtro
            numero_nf (str, optional): Número da nota fiscal
            origem (str, optional): Nome da origem (fornecedor)
        
        Returns:
            list: Lista de dicionários com NFs de entrada filtradas e agrupadas
        """
        from sistema.models_views.controle_carga.registro_operacional.pedido_venda_dados_nf_model import PedidoVendaDadosNfModel
        
        if not data_inicio and not data_fim:
            data_inicio = date.today() - timedelta(days=30)
            data_fim = date.today()

        # Query principal para buscar NF de entrada com pedido de venda
        query = (
            db.session.query(
                NfEntradaModel, 
                PedidoVendaModel, 
                SolicitacaoPedidoVendaModel
            )
            .join(
                PedidoVendaModel,
                NfEntradaModel.pedido_venda_id == PedidoVendaModel.id,
            )
            .join(
                SolicitacaoPedidoVendaModel,
                PedidoVendaModel.solicitacao_pedido_venda_id == SolicitacaoPedidoVendaModel.id,
            )
            .filter(
                NfEntradaModel.deletado == False, 
                NfEntradaModel.ativo == True,
                NfEntradaModel.pedido_venda_id.isnot(None)
            )
            .order_by(desc(NfEntradaModel.id))
        )

        registros = []
        
        for nfentrada, pedido_venda, solicitacao in query.all():
            # Buscar todos os dados de ticket para este pedido de venda
            dados_tickets = PedidoVendaDadosTicketModel.query.filter(
                PedidoVendaDadosTicketModel.pedido_venda_id == pedido_venda.id,
                PedidoVendaDadosTicketModel.ativo == True,
                PedidoVendaDadosTicketModel.deletado == False
            ).all()
            
            if not dados_tickets:
                continue
                
            primeiro_ticket = dados_tickets[0]
            
            # Filtrar por data se especificado
            if primeiro_ticket.data_entrega_ticket:
                if data_inicio and primeiro_ticket.data_entrega_ticket < data_inicio:
                    continue
                if data_fim and primeiro_ticket.data_entrega_ticket > data_fim:
                    continue
            else:
                continue
            
            # Filtrar por número de NF se especificado
            if numero_nf:
                nf_encontrada = False
                for ticket in dados_tickets:
                    if ticket.numero_nota_fiscal_ticket and numero_nf.lower() in ticket.numero_nota_fiscal_ticket.lower():
                        nf_encontrada = True
                        break
                if not nf_encontrada:
                    # Verificar também nos dados da NF
                    dados_nf = PedidoVendaDadosNfModel.query.filter_by(
                        pedido_venda_id=pedido_venda.id
                    ).first()
                    if not dados_nf or not dados_nf.numero_nota_fiscal or numero_nf.lower() not in dados_nf.numero_nota_fiscal.lower():
                        continue
            
            # Calcular peso total de todos os fornecedores
            peso_total_ticket = sum(t.peso_liquido_ticket or 0 for t in dados_tickets)
            
            # Determinar origem (primeiro fornecedor)
            origem_nome = "Indefinido"
            primeiro_fornecedor = None
            if dados_tickets and dados_tickets[0].fornecedor_id:
                primeiro_fornecedor = dados_tickets[0].fornecedor
                if primeiro_fornecedor and primeiro_fornecedor.identificacao:
                    if primeiro_fornecedor.controle_entrada == False:
                        origem_nome = "Outros fornecedores"
                    else:
                        origem_nome = primeiro_fornecedor.identificacao
            
            # Filtrar por origem se especificado
            if origem:
                origem_encontrada = False
                # Verificar fornecedores
                for ticket in dados_tickets:
                    if ticket.fornecedor and ticket.fornecedor.identificacao:
                        if origem.lower() in ticket.fornecedor.identificacao.lower():
                            origem_encontrada = True
                            break
                if not origem_encontrada:
                    continue
                
            produto = getattr(solicitacao.produto, "nome", "Indefinido") if solicitacao else "Indefinido"
            bitola = getattr(solicitacao.bitola, "bitola", "") if solicitacao else ""

            registros.append({
                "origem": origem_nome,
                "produto": produto,
                "bitola": bitola,
                "pedido_venda": pedido_venda,
                "dados_ticket": primeiro_ticket,  # Para data/numero NF
                "dados_tickets": dados_tickets,   # Todos os tickets
                "peso_total_ticket": peso_total_ticket,  # Peso somado
                "solicitacao": solicitacao,
                "nfentrada": nfentrada
            })
            
        return registros
    
    
    @staticmethod
    def obter_nf_entrada(id):
        """
        Obtém uma NF de entrada específica por ID.
        
        Args:
            id (int): ID da NF de entrada
        
        Returns:
            NfEntradaModel: Objeto da NF de entrada encontrada ou None se não encontrar
        """
        nf = NfEntradaModel.query.filter(
            NfEntradaModel.deletado == False,
            NfEntradaModel.ativo == True,
            NfEntradaModel.id == id,
        ).first()

        return nf


    def listar_nfs_entrada_sem_contra_nota():
        """
        Lista todas as NFs de entrada ativas que não possuem contra nota.
        
        Returns:
            list: Lista de objetos NfEntradaModel sem contra nota
        """
        nf = NfEntradaModel.query.filter(
            NfEntradaModel.deletado == False,
            NfEntradaModel.ativo == True,
            NfEntradaModel.arquivo_contra_nota_id == None,
        ).all()

        return nf


    def obter_contra_nota_por_registro(id):
        """
        Obtém a contra nota através do ID do registro operacional (legado).
        
        Args:
            id (int): ID do registro operacional
        
        Returns:
            NfEntradaModel: Objeto da NF de entrada associada ao registro ou None se não encontrar
        """
        contraNota = NfEntradaModel.query.filter(
            NfEntradaModel.registro_id == id
        ).first()

        return contraNota
    
    
    @staticmethod
    def obter_nf_entrada_por_pedido_venda(pedido_venda_id):
        """
        Obtém a NF de entrada através do ID do pedido de venda.
        
        Args:
            pedido_venda_id (int): ID do pedido de venda
        
        Returns:
            NfEntradaModel: Objeto da NF de entrada associada ao pedido de venda ou None se não encontrar
        """
        return NfEntradaModel.query.filter(
            NfEntradaModel.pedido_venda_id == pedido_venda_id,
            NfEntradaModel.deletado == False,
            NfEntradaModel.ativo == True
        ).first()