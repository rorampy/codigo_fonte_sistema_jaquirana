from sistema import db, login_manager
from sistema.models_views.base_model import BaseModel
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import and_, desc
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return UsuarioModel.query.get(int(user_id))


class UsuarioModel(BaseModel, UserMixin):
    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    sobrenome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    foto_perfil_id = db.Column(db.Integer, db.ForeignKey('upload_arquivo.id'))
    foto_perfil = db.relationship('UploadArquivoModel', backref=db.backref('usuario', lazy=True))
    telefone = db.Column(db.String(18), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('RoleModel', backref=db.backref('usuarios', lazy=True))
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    def __init__(
        self, nome, sobrenome, cpf, foto_perfil_id, telefone, email, senha, role_id, ativo=True
    ):
        self.nome = nome
        self.sobrenome = sobrenome
        self.cpf = cpf
        self.foto_perfil_id = foto_perfil_id
        self.telefone = telefone
        self.email = email
        self.senha = generate_password_hash(senha)
        self.role_id = role_id
        self.ativo = ativo

    
    @classmethod
    def obter_usuarios_desc_id(cls):
        """
        Obtém todos os usuários não deletados ordenados por ID em ordem decrescente.

        Retorna:
        list: Lista de objetos UsuarioModel ordenados por ID em ordem decrescente.
        """
        return cls.query.filter_by(deletado=False).order_by(desc(cls.id)).all()

    @classmethod
    def obter_usuario_por_id(cls, id):
        """
        Obtém um usuário pelo seu ID.

        Parâmetros:
        id (int): O ID do usuário.

        Retorna:
        UsuarioModel: O objeto do usuário correspondente ao ID fornecido, ou None se não encontrado.
        """
        return cls.query.get(id)

    @classmethod
    def obter_usuario_por_cpf(cls, cpf):
        """
        Obtém um usuário pelo seu CPF.

        Parâmetros:
        cpf (str): O CPF do usuário.

        Retorna:
        UsuarioModel: O objeto do usuário correspondente ao CPF fornecido, ou None se não encontrado.
        """
        return cls.query.filter_by(cpf=cpf).first()

    @classmethod
    def obter_usuario_por_email(cls, email):
        """
        Obtém um usuário pelo seu email.

        Parâmetros:
        email (str): O email do usuário.

        Retorna:
        UsuarioModel: O objeto do usuário correspondente ao email fornecido, ou None se não encontrado.
        """
        return cls.query.filter_by(email=email).first()

    @classmethod
    def obter_usuario_por_telefone(cls, telefone):
        """
        Obtém um usuário pelo seu telefone.

        Parâmetros:
        telefone (str): O telefone do usuário.

        Retorna:
        UsuarioModel: O objeto do usuário correspondente ao telefone fornecido, ou None se não encontrado.
        """
        return cls.query.filter_by(telefone=telefone).first()
    
    
    def verificar_senha(self, senha_validar):
        """
        Verifica se a senha fornecida corresponde ao hash armazenado.

        Parâmetros:
        senha_validar (str): A senha que será validada.

        Retorna:
        bool: True se a senha corresponder ao hash armazenado, False caso contrário.
        """
        return check_password_hash(self.senha, senha_validar)

    @classmethod
    def verificar_email_existente(cls, email):
        """
        Verifica se um email já está registrado e não foi deletado.

        Parâmetros:
        cls (UsuarioModel): A própria classe UsuarioModel.
        email (str): O email a ser verificado.

        Retorna:
        UsuarioModel: A instância do usuário se o email estiver registrado e não deletado, caso contrário, None.
        """
        return cls.query.filter(and_(cls.email == email, cls.deletado == False)).first()

    @classmethod
    def verificar_email_existente_excluido(cls, email):
        """"
        Verifica se um email já está registrado e foi deletado.

        Parâmetros:
        email (str): O email que será verificado.

        Retorna:
        objeto ou None: O objeto do registro encontrado se o email estiver registrado e deletado, 
        ou None se não houver correspondência.
        """
        return cls.query.filter(and_(cls.email == email, cls.deletado == True)).first()

    @staticmethod
    def gerar_hash_senha(senha):
        """
        Gera um hash seguro para a senha fornecida.

        Este método utiliza a função `generate_password_hash` para criar um hash da senha,
        garantindo que a senha seja armazenada de forma segura no banco de dados.
        
        Parâmetros:
        senha (str): A senha em texto plano que será convertida em hash.

        Retorna:
        str: O hash seguro da senha.
        """
        return generate_password_hash(senha)

    @staticmethod
    def gerar_senha_aleatoria_sem_cripto(tamanho):
        """
        Gera uma senha aleatória de tamanho especificado.

        Esta função cria uma senha aleatória contendo caracteres alfanuméricos.
        A senha gerada não é criptografada e deve ser usada com cuidado.

        Parâmetros:
        tamanho (int): O comprimento desejado para a senha gerada.

        Retorna:
        str: A senha aleatória gerada.
        """
        import random
        import string
        caracteres = string.ascii_letters + string.digits
        return ''.join(random.choice(caracteres) for _ in range(tamanho))
    
    def obter_usuario_por_id(id):
        usuario = UsuarioModel.query.filter(
            UsuarioModel.id == id
        ).first()
        
        return usuario