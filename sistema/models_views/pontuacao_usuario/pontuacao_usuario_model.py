from sistema import db
from sistema.models_views.base_model import BaseModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum

class PontuacaoUsuarioModel(BaseModel):
    __tablename__ = 'pon_pontuacao_usuario'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    usuario = db.relationship('UsuarioModel', backref=db.backref('usuario', lazy=True))
    tipo_acao = db.Column(db.String(100), nullable=False)  # ex: 'cadastro', 'edicao'
    pontos = db.Column(db.Float, nullable=False) # cadastro => 1 | edição => 0.5
    modulo = db.Column(db.String(150), nullable=False)  # opcional: 'clientes', 'transportadoras' etc.
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    def __init__(self, usuario_id, tipo_acao, pontos, modulo, ativo=True):
        self.usuario_id = usuario_id
        self.tipo_acao = tipo_acao
        self.pontos = pontos 
        self.modulo = modulo
        self.ativo = ativo


    @staticmethod
    def cadastrar_pontuacao_usuario(usuario_id, tipo_acao: TipoAcaoEnum, pontuacao: float, modulo: str):
        if not usuario_id or not tipo_acao or pontuacao is None or usuario_id == 1 or usuario_id == 2 or usuario_id == 18:
            return False

        registro = PontuacaoUsuarioModel(
            usuario_id=usuario_id,
            tipo_acao=tipo_acao.value,  # converte Enum para string
            pontos=pontuacao,
            modulo=modulo,
            ativo=True
        )
        db.session.add(registro)
        db.session.commit()
        return True