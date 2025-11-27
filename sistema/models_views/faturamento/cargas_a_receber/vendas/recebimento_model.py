from pickle import NONE
from ....base_model import BaseModel, db

class RecebimentoModel(BaseModel):
    """
    Model para aguardar valores de recebimento de clientes
    """
    __tablename__ = 're_recebimento'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    cliente_id = db.Column(db.Integer, db.ForeignKey("cli_cliente.id"), nullable=False)
    cliente = db.relationship("ClienteModel", backref=db.backref("cliente_recebimento", lazy=True))

    registro_operacional_id = db.Column(db.Integer, db.ForeignKey("re_registro_operacional.id"), nullable=False)
    registro = db.relationship("RegistroOperacionalModel", backref=db.backref("registro_recebimento", lazy=True))

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    usuario = db.relationship('UsuarioModel', backref=db.backref('usuario_cadastro_recebimento', lazy=True))

    data_recebimento = db.Column(db.Date, nullable=True)

    numero_nota_fiscal = db.Column(db.String(20), nullable=True)

    valor_total_recebimento_100 = db.Column(db.Integer, nullable=True)

    conta_bancaria_id = db.Column(db.Integer, db.ForeignKey("con_conta_bancaria.id"), nullable=True)
    conta_bancaria = db.relationship("ContaBancariaModel", foreign_keys=[conta_bancaria_id], backref=db.backref("conta_bancaria_recebimento", lazy=True))

    plano_conta_id = db.Column(db.Integer, db.ForeignKey("plan_plano_conta.id"), nullable=True)
    plano_conta = db.relationship("PlanoContaModel", foreign_keys=[plano_conta_id], backref=db.backref("plano_conta_recebimento", lazy=True))

    categorizacao_fiscal_id = db.Column(db.Integer, db.ForeignKey("ca_categorizacao_fiscal.id"), nullable=True)
    categorizacao_fiscal = db.relationship("CategorizacaoFiscalModel", foreign_keys=[categorizacao_fiscal_id], backref=db.backref("categorizacao_fiscal_recebimento", lazy=True))

    comprovante_recebimento_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    comprovante_recebimento = db.relationship("UploadArquivoModel", foreign_keys=[comprovante_recebimento_id], backref=db.backref("comprovante_recebimento", lazy=True))

    movimentacao_financeira_id = db.Column(db.Integer, db.ForeignKey('mov_movimentacao_financeira.id'), nullable=True)
    movimentacao_financeira = db.relationship(
        'MovimentacaoFinanceiraModel',
        foreign_keys=[movimentacao_financeira_id],
        backref=db.backref('recebimentos_massa', lazy='select')
    )

    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(
        self,
        cliente_id,
        registro_operacional_id,
        usuario_id,
        numero_nota_fiscal,
        valor_total_recebimento_100,
        data_recebimento=None,
        conta_bancaria_id=None,
        plano_conta_id=None,
        categorizacao_fiscal_id=None,
        comprovante_recebimento_id=None,
        movimentacao_financeira_id=None,
        ativo=True,
    ):
        self.cliente_id = cliente_id
        self.registro_operacional_id = registro_operacional_id
        self.usuario_id = usuario_id
        self.data_recebimento = data_recebimento
        self.numero_nota_fiscal = numero_nota_fiscal
        self.valor_total_recebimento_100 = valor_total_recebimento_100
        self.conta_bancaria_id = conta_bancaria_id
        self.plano_conta_id = plano_conta_id
        self.categorizacao_fiscal_id = categorizacao_fiscal_id
        self.comprovante_recebimento_id = comprovante_recebimento_id
        self.movimentacao_financeira_id = movimentacao_financeira_id
        self.ativo = ativo

    def obter_recebimento_pore_registro_id(id):
        registro = RecebimentoModel.query.filter(
            RecebimentoModel.deletado == 0,
            RecebimentoModel.ativo == 1,
            RecebimentoModel.registro_operacional_id == id
        ).first()


        return registro
    
    @staticmethod
    def filtrar_recebimentos_agrupado(cliente_identificacao=None, data_inicio=None, data_fim=None, situacao_financeira_id=None):
        """
        Filtra e retorna recebimentos agrupados por cliente e produto, similar ao obter_recebimentos_agrupados.
        Args:
            cliente_identificacao (str, optional): Parte do nome do cliente para filtro (busca em ClienteModel.identificacao)
            data_inicio (date, optional): Data inicial da entrega do ticket
            data_fim (date, optional): Data final da entrega do ticket
            situacao_financeira_id (int, optional): Situação financeira do registro operacional
        Returns:
            list: Lista de dicionários com recebimentos filtrados e agrupados

        Exemplo de resposta:
        [
            {
                "cliente": "Cliente A",
                "produto": "Produto X",
                "recebimento": <RecebimentoModel ...>
            },
            {
                "cliente": "Cliente B",
                "produto": "Produto Y",
                "recebimento": <RecebimentoModel ...>
            },
            # ...
        ]
        """
        from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
        from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
        from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
        from sistema.models_views.controle_carga.solicitacao_nf.carga_model import CargaModel
        from datetime import date, timedelta
        from sqlalchemy import and_

        if not data_inicio or not data_fim:
            data_inicio = date.today() - timedelta(days=30)
            data_fim = date.today()

        query = (
            db.session.query(RecebimentoModel, ClienteModel, ProdutoModel)
            .join(RecebimentoModel.cliente)
            .join(RecebimentoModel.registro)
            .join(CargaModel, RegistroOperacionalModel.solicitacao_nf_id == CargaModel.id)
            .join(ProdutoModel, CargaModel.produto_id == ProdutoModel.id)
            .filter(
                RecebimentoModel.ativo.is_(True),
                RegistroOperacionalModel.deletado.is_(False),
                RegistroOperacionalModel.ativo.is_(True)
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

        if cliente_identificacao:
            query = query.filter(ClienteModel.identificacao.ilike(f"%{cliente_identificacao}%"))
        if situacao_financeira_id:
            query = query.filter(RegistroOperacionalModel.situacao_financeira_id == situacao_financeira_id)

        resultados = []
        for recebimento, cliente, produto in query.all():
            resultados.append({
                "cliente": cliente.identificacao,
                "produto": produto.nome,
                "recebimento": recebimento,
            })

        resultados.sort(key=lambda x: (x["cliente"], x["produto"]))
        return resultados