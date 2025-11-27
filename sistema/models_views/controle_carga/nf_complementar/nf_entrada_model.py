from datetime import date, timedelta
from ...base_model import BaseModel, db
from sistema import request
from sistema.models_views.controle_carga.solicitacao_nf.carga_model import CargaModel
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_model import FornecedorModel
from sistema.models_views.gerenciar.floresta.floresta_model import FlorestaModel
from sqlalchemy import and_, desc, or_


class NfEntradaModel(BaseModel):
    """
    Model para registro d NFs de entrada
    """

    __tablename__ = "re_nf_entrada"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    registro_id = db.Column(db.Integer, db.ForeignKey("re_registro_operacional.id"), nullable=True)
    registro = db.relationship("RegistroOperacionalModel", backref=db.backref("rp_registro", lazy=True))

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
        registro_id,
        peso_contra_nota=None,
        arquivo_nf_entrada_id=None,
        arquivo_contra_nota_id=None,
        arquivo_cte_id=None,
        arquivo_mdf_id=None,
    ):
        self.registro_id = registro_id
        self.peso_contra_nota = peso_contra_nota
        self.arquivo_nf_entrada_id = arquivo_nf_entrada_id
        self.arquivo_contra_nota_id = arquivo_contra_nota_id
        self.arquivo_cte_id = arquivo_cte_id
        self.arquivo_mdf_id = arquivo_mdf_id


    def obter_nf_entrada_agrupadas():
        """
        Retorna todas as NFs de entrada ativas agrupadas por origem, produto e bitola. (últimos 30 dias)
        
        Returns:
            list: Lista de dicionários com NFs de entrada agrupadas
        """

        data_inicio = date.today() - timedelta(days=30)
        data_fim = date.today()

        query = (
            db.session.query(NfEntradaModel, RegistroOperacionalModel, FornecedorModel, FlorestaModel)
            .join(
                RegistroOperacionalModel,
                NfEntradaModel.registro_id == RegistroOperacionalModel.id,
            )
            .join(
                CargaModel, RegistroOperacionalModel.solicitacao_nf_id == CargaModel.id
            )
            .outerjoin(FornecedorModel, CargaModel.fornecedor_id == FornecedorModel.id)
            .outerjoin(FlorestaModel, CargaModel.floresta_id == FlorestaModel.id)
            .filter(NfEntradaModel.deletado == False, NfEntradaModel.ativo == True)
            .order_by(desc(NfEntradaModel.id))
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
        for nfentrada, registro, fornecedor, floresta in query.all():
            origem = "Indefinido"
            if fornecedor and fornecedor.identificacao:
                # Se o fornecedor tem controle_entrada = True, agrupa como "Outros fornecedores"
                if fornecedor.controle_entrada == False:
                    origem = "Outros fornecedores"
                else:
                    origem = fornecedor.identificacao
            elif floresta and floresta.identificacao:
                origem = floresta.identificacao
                
            produto = getattr(registro.solicitacao.produto, "nome", "Indefinido")
            bitola = getattr(registro.solicitacao.bitola, "bitola", "")

            registros.append({
                "origem": origem,
                "produto": produto,
                "bitola": bitola,
                "registro": registro,
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
        
        Args:
            data_inicio (date, optional): Data inicial do filtro
            data_fim (date, optional): Data final do filtro
            numero_nf (str, optional): Número da nota fiscal
            origem (str, optional): Nome da origem (fornecedor ou floresta)
        
        Returns:
            list: Lista de dicionários com NFs de entrada filtradas e agrupadas
        """
        if not data_inicio and not data_fim:
            data_inicio = date.today() - timedelta(days=30)
            data_fim = date.today()

        query = (
            db.session.query(NfEntradaModel, RegistroOperacionalModel, FornecedorModel, FlorestaModel)
            .join(
                RegistroOperacionalModel,
                NfEntradaModel.registro_id == RegistroOperacionalModel.id,
            )
            .join(
                CargaModel, RegistroOperacionalModel.solicitacao_nf_id == CargaModel.id
            )
            .outerjoin(FornecedorModel, CargaModel.fornecedor_id == FornecedorModel.id)
            .outerjoin(FlorestaModel, CargaModel.floresta_id == FlorestaModel.id)
            .filter(NfEntradaModel.deletado == False, NfEntradaModel.ativo == True)
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

        if numero_nf:
            query = query.filter(
                or_(
                    RegistroOperacionalModel.numero_nota_fiscal.ilike(f"%{numero_nf}%"),
                    RegistroOperacionalModel.numero_nota_fiscal_excessao.ilike(f"%{numero_nf}%"),
                    RegistroOperacionalModel.numero_nota_fiscal_estorno.ilike(f"%{numero_nf}%"),
                )
            )

        if origem:
            query = query.filter(
                or_(
                    FornecedorModel.identificacao.ilike(f"%{origem}%"),
                    FlorestaModel.identificacao.ilike(f"%{origem}%"),
                )
            )

        query = query.order_by(desc(NfEntradaModel.id))

        registros = []
        for nfentrada, registro, fornecedor, floresta in query.all():
            origem = "Indefinido"
            if fornecedor and fornecedor.identificacao:
                # Se o fornecedor tem controle_entrada = True, agrupa como "Outros fornecedores"
                if fornecedor.controle_entrada:
                    origem = "Outros fornecedores"
                else:
                    origem = fornecedor.identificacao
            elif floresta and floresta.identificacao:
                origem = floresta.identificacao
                
            produto = getattr(registro.solicitacao.produto, "nome", "Indefinido")
            bitola = getattr(registro.solicitacao.bitola, "bitola", "")

            registros.append({
                "origem": origem,
                "produto": produto,
                "bitola": bitola,
                "registro": registro,
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
        Obtém a contra nota através do ID do registro operacional.
        
        Args:
            id (int): ID do registro operacional
        
        Returns:
            NfEntradaModel: Objeto da NF de entrada associada ao registro ou None se não encontrar
        """
        contraNota = NfEntradaModel.query.filter(
            NfEntradaModel.registro_id == id
        ).first()

        return contraNota