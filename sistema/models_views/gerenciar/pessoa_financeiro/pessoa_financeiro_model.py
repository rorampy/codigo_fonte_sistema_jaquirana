from ...base_model import BaseModel, db
from sqlalchemy import and_

class PessoaFinanceiroModel(BaseModel):
    __tablename__ = 'pe_pessoa_financeiro'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    tipo_cadastro = db.Column(db.Boolean, nullable=False)
    identificacao = db.Column(db.String(255), nullable=False)
    numero_documento = db.Column(db.String(20), nullable=False)
    telefone = db.Column(db.String(20), nullable=True)
    instituicao_financeira_id = db.Column(db.Integer, db.ForeignKey('z_sys_instituicoes_financeiras.id'), nullable=True)
    instituicao_financeira = db.relationship('InstituicoesFinanceirasModel', backref='instituicao_financeira_pessoa_financeiro', lazy=True)
    agencia_bancaria = db.Column(db.String(50), nullable=True)
    conta_bancaria = db.Column(db.String(50), nullable=True)
    chave_pix = db.Column(db.String(155), nullable=True)
    tem_vinculo_fornecedor = db.Column(db.Boolean, default=False, nullable=False)
    tem_vinculo_transportadora = db.Column(db.Boolean, default=False, nullable=False)
    tem_vinculo_extrator = db.Column(db.Boolean, default=False, nullable=False)
    tem_vinculo_comissionado = db.Column(db.Boolean, default=False, nullable=False)
    vinculos_operacionais = db.Column(db.JSON, nullable=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    def __init__(
            self, tipo_cadastro, identificacao, numero_documento, telefone=None, 
            instituicao_financeira_id=None, agencia_bancaria=None, conta_bancaria=None, 
            chave_pix=None, tem_vinculo_fornecedor=False, tem_vinculo_transportadora=False,
            tem_vinculo_extrator=False, tem_vinculo_comissionado=False, 
            vinculos_operacionais=None, ativo=True
    ):
        self.tipo_cadastro = tipo_cadastro
        self.identificacao = identificacao
        self.numero_documento = numero_documento
        self.telefone = telefone
        self.instituicao_financeira_id = instituicao_financeira_id
        self.agencia_bancaria = agencia_bancaria
        self.conta_bancaria = conta_bancaria
        self.chave_pix = chave_pix
        self.tem_vinculo_fornecedor = tem_vinculo_fornecedor
        self.tem_vinculo_transportadora = tem_vinculo_transportadora
        self.tem_vinculo_extrator = tem_vinculo_extrator
        self.tem_vinculo_comissionado = tem_vinculo_comissionado
        self.vinculos_operacionais = vinculos_operacionais
        self.ativo = ativo

    @staticmethod
    def processar_vinculos(vinculos_json_str):
        """
        Processa o JSON de vínculos e retorna os valores booleanos e dados
        """
        if not vinculos_json_str or vinculos_json_str.strip() == '' or vinculos_json_str.strip() == '{}':
            return False, False, False, False, []
            
        import json
        try:
            vinculos_data = json.loads(vinculos_json_str)
            if not vinculos_data:
                return False, False, False, False, []
        except (json.JSONDecodeError, TypeError):
            return False, False, False, False, []
        
        tem_fornecedor = 'fornecedor' in vinculos_data and len(vinculos_data['fornecedor']) > 0
        tem_transportadora = 'transportadora' in vinculos_data and len(vinculos_data['transportadora']) > 0
        tem_extrator = 'extrator' in vinculos_data and len(vinculos_data['extrator']) > 0
        tem_comissionado = 'comissionado' in vinculos_data and len(vinculos_data['comissionado']) > 0
        
        return tem_fornecedor, tem_transportadora, tem_extrator, tem_comissionado, vinculos_data
    
        
    def listar_pessoas():
        """
        Lista todas as pessoas financeiro não deletadas, ordenadas por ID decrescente.
        
        Returns:
            list: Lista de objetos PessoaFinanceiroModel não deletados
        """
        pessoas = PessoaFinanceiroModel.query.filter(
            PessoaFinanceiroModel.deletado == 0,
        ).order_by(PessoaFinanceiroModel.id.desc()).all()
        return pessoas

    def listar_pessoas_ativas():
        """
        Lista todas as pessoas financeiro ativas e não deletadas, ordenadas por ID decrescente.
        
        Returns:
            list: Lista de objetos PessoaFinanceiroModel ativos e não deletados
        """
        pessoas = PessoaFinanceiroModel.query.filter(
            PessoaFinanceiroModel.deletado == 0,
            PessoaFinanceiroModel.ativo == 1
        ).order_by(PessoaFinanceiroModel.id.desc()).all()
        return pessoas

    def listar_pessoas_inativas():
        """
        Lista todas as pessoas financeiro inativas (independente se deletadas ou não).
        
        Returns:
            list: Lista de objetos PessoaFinanceiroModel inativos
        """
        pessoas = PessoaFinanceiroModel.query.filter(
            PessoaFinanceiroModel.ativo == False
        ).all()
        return pessoas

    @staticmethod
    def obter_pessoa_por_id(id):
        """
        Obtém uma pessoa financeiro específica por ID, apenas se não estiver deletada.
        
        Args:
            id (int): ID da pessoa financeiro
        
        Returns:
            PessoaFinanceiroModel: Objeto da pessoa encontrada ou None se não encontrar
        """
        pessoa = PessoaFinanceiroModel.query.filter(
            PessoaFinanceiroModel.id == id,
            PessoaFinanceiroModel.deletado == 0
        ).first()
        return pessoa

    def filtrar_pessoas(
        identificacao=None,
        numero_documento=None,
        telefone=None
    ):
        """
        Filtra pessoas financeiro ativas por identificação, número de documento ou telefone.
        
        Args:
            identificacao (str, optional): Nome/identificação da pessoa
            numero_documento (str, optional): Número do documento da pessoa
            telefone (str, optional): Telefone da pessoa
        
        Returns:
            list: Lista de objetos PessoaFinanceiroModel que atendem aos critérios de filtro
        """
        query = PessoaFinanceiroModel.query.filter(
            PessoaFinanceiroModel.deletado == False,
            PessoaFinanceiroModel.ativo == True
        )
        if identificacao:
            query = query.filter(
                PessoaFinanceiroModel.identificacao.ilike(f"%{identificacao}%")
            )
        if numero_documento:
            query = query.filter(
                PessoaFinanceiroModel.numero_documento.ilike(f"%{numero_documento}%")
            )
        if telefone:
            query = query.filter(
                PessoaFinanceiroModel.telefone.ilike(f"%{telefone}%")
            )
        return query.order_by(PessoaFinanceiroModel.id.desc()).all()
