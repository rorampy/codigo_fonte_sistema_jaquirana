from ..base_model import BaseModel, db
from sqlalchemy import and_, Numeric
from sistema.models_views.controle_carga.carga_model import CargaModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema.models_views.gerenciar.veiculo.veiculo_model import VeiculoModel
from sistema.models_views.gerenciar.motorista.motorista_model import MotoristaModel


class LancarEmissaoNotaFiscalModel(BaseModel):
    """
    Model para registro de lançamentos de nf
    """
    __tablename__ = 'car_carga_emissao_nf'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    solicitacao_nf_id = db.Column(db.Integer, db.ForeignKey('car_carga.id'), nullable=True)
    solicitacao = db.relationship('CargaModel', backref=db.backref('car_carga_emissao_nf', lazy=True))

    floresta_id = db.Column(db.Integer, db.ForeignKey('flor_floresta.id'), nullable=True)
    floresta = db.relationship('FlorestaModel', backref=db.backref('floresta_lancamento', lazy=True))

    fornecedor_id = db.Column(db.Integer, db.ForeignKey('for_fornecedor.id'), nullable=True)
    fornecedor = db.relationship('FornecedorModel', backref=db.backref('car_carga_emissao_nf', lazy=True))
    
    razao_social_emissor = db.Column(db.String(200), nullable=True)
    numero_nota_fiscal = db.Column(db.String(20), nullable=True)
    serie_nota = db.Column(db.String(5), nullable=True)
    chave_acesso = db.Column(db.String(255), nullable=True)

    destinatario_nome = db.Column(db.String(200), nullable=True)
    destinatario_cnpj_cpf = db.Column(db.String(20), nullable=True)
    destinatario_insc_estadual = db.Column(db.String(50), nullable=True)
    destinatario_data_emissao = db.Column(db.Date, nullable=True)
    
    valor_total_nota_100 = db.Column(db.Integer, nullable=True)

    # Novos campos para dados do Transportador
    transportador_nome = db.Column(db.String(200), nullable=True)
    transportador_cnpj_cpf = db.Column(db.String(20), nullable=True)
    transportador_insc_estadual = db.Column(db.String(50), nullable=True)

    placa = db.Column(db.String(50), nullable=True)
    motorista = db.Column(db.String(200), nullable=True)
    
    arquivo_nota_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=False)
    arquivo_nota = db.relationship("UploadArquivoModel", backref=db.backref("car_carga_emissao_nf", lazy=True))

    ativo = db.Column(db.Boolean, default=True, nullable=False)
        
    def __init__(
        self,
        solicitacao_nf_id,
        numero_nota_fiscal=None,
        data_hora_emissao=None,
        arquivo_nota_id=None,
        floresta_id=None,
        fornecedor_id=None,
        razao_social_emissor=None,
        serie_nota=None,
        chave_acesso=None,
        destinatario_nome=None,
        destinatario_cnpj_cpf=None,
        destinatario_insc_estadual=None,
        destinatario_data_emissao=None,
        peso_ton_nf=None,
        valor_total_nota_100=None,
        transportador_nome=None,
        transportador_cnpj_cpf=None,
        transportador_insc_estadual=None,
        placa=None,
        motorista=None,
        ativo=True,
    ):
        self.solicitacao_nf_id = solicitacao_nf_id
        self.numero_nota_fiscal = numero_nota_fiscal
        self.data_hora_emissao = data_hora_emissao
        self.arquivo_nota_id = arquivo_nota_id
        self.floresta_id = floresta_id
        self.fornecedor_id = fornecedor_id

        self.razao_social_emissor = razao_social_emissor
        self.serie_nota = serie_nota
        self.chave_acesso = chave_acesso

        self.destinatario_nome = destinatario_nome
        self.destinatario_cnpj_cpf = destinatario_cnpj_cpf
        self.destinatario_insc_estadual = destinatario_insc_estadual
        self.destinatario_data_emissao = destinatario_data_emissao

        self.peso_ton_nf = peso_ton_nf
        self.valor_total_nota_100 = valor_total_nota_100

        self.transportador_nome = transportador_nome
        self.transportador_cnpj_cpf = transportador_cnpj_cpf
        self.transportador_insc_estadual = transportador_insc_estadual

        self.placa = placa
        self.motorista = motorista
        self.ativo = ativo

    def listar_emissoes():
        """
        Lista todas as emissões de nota fiscal ativas e não deletadas.
        
        Returns:
            list: Lista de emissões ordenadas por ID decrescente
        """
        emissoes = (
            LancarEmissaoNotaFiscalModel.query.filter(
                LancarEmissaoNotaFiscalModel.deletado == 0,
                LancarEmissaoNotaFiscalModel.ativo == 1,
            )
            .order_by(LancarEmissaoNotaFiscalModel.id.desc())
            .all()
        )
        
        return emissoes


    def listar_emissoes_inativas():
        """
        Lista todas as emissões de nota fiscal inativas.
        
        Returns:
            list: Lista de emissões inativas ordenadas por ID decrescente
        """
        emissoes = (
            LancarEmissaoNotaFiscalModel.query.filter(
                LancarEmissaoNotaFiscalModel.ativo == 0
            )
            .order_by(LancarEmissaoNotaFiscalModel.id.desc())
            .all()
        )
        
        return emissoes


    def obter_emissao_por_id(id):
        """
        Obtém uma emissão de nota fiscal específica pelo ID.
        
        Args:
            id (int): ID da emissão a ser buscada
            
        Returns:
            LancarEmissaoNotaFiscalModel: Emissão encontrada ou None se não existir
        """
        emissao = LancarEmissaoNotaFiscalModel.query.filter(
            LancarEmissaoNotaFiscalModel.id == id
        ).first()
        
        return emissao


    def filtrar_emissoes(
        motorista_nf=None,
        nome_cliente=None,
        numero_nf=None,
        placa_nf=None,
        placa_solicitacao=None,
    ):
        """
        Filtra emissões de nota fiscal por múltiplos critérios.
        
        Args:
            motorista_nf (str, optional): Nome completo do motorista
            nome_cliente (str, optional): Identificação do cliente
            numero_nf (str, optional): Número da nota fiscal
            placa_nf (str, optional): Placa registrada na nota fiscal
            placa_solicitacao (str, optional): Placa do veículo da solicitação
            
        Returns:
            list: Lista de emissões filtradas ordenadas por ID decrescente
        """
        query = (
            LancarEmissaoNotaFiscalModel.query.join(
                LancarEmissaoNotaFiscalModel.solicitacao
            )
            .join(CargaModel.cliente)
            .join(CargaModel.veiculo)
            .join(CargaModel.motorista)
        )
        
        if nome_cliente:
            query = query.filter(ClienteModel.identificacao.like(f"%{nome_cliente}%"))
        
        if numero_nf:
            query = query.filter(
                LancarEmissaoNotaFiscalModel.numero_nota_fiscal.like(f"%{numero_nf}%")
            )
        
        if motorista_nf:
            query = query.filter(MotoristaModel.nome_completo.like(f"%{motorista_nf}%"))
        
        if placa_nf:
            query = query.filter(
                LancarEmissaoNotaFiscalModel.placa.like(f"%{placa_nf}%")
            )
        
        if placa_solicitacao:
            query = query.filter(
                VeiculoModel.placa_veiculo.like(f"%{placa_solicitacao}%")
            )
        
        return query.order_by(LancarEmissaoNotaFiscalModel.id.desc()).all()
