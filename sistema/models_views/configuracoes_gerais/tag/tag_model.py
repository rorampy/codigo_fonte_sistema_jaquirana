from ...base_model import BaseModel, db
from sqlalchemy import and_, desc


class TagModel(BaseModel):
    """
    Model para registro de tags
    """
    __tablename__ = 'ta_tag'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo_tag = db.Column(db.String(20), nullable=False)
    nome_tag = db.Column(db.String(255), nullable=False)  
    ativo = db.Column(db.Boolean, default=True, nullable=False)             

    def __init__(self, codigo_tag, nome_tag, ativo=True):
        self.codigo_tag = codigo_tag
        self.nome_tag = nome_tag
        self.ativo = ativo

    
    def gerar_codigo_nova_tag():
        ultimo_cor = (
            TagModel.query.filter(TagModel.deletado == 0, TagModel.ativo == True)
            .order_by(desc(TagModel.id))
            .first()
        )

        if not ultimo_cor:
            codigo = "TAG-000001"
        else:
            id = str(ultimo_cor.id + 1)

            while len(id) < 6:
                id = "0" + id

            codigo = "TAG-" + id

        return codigo
    
    def obter_tags_ativas():
        """
        Obtém todas as tags ativas e não deletadas.

        Returns:
            list: Lista de objetos TagModel ativos.
        """
        
        tags = TagModel.query.filter(
            and_(
                TagModel.ativo == True,
                TagModel.deletado == False
            )
        ).order_by(desc(TagModel.id)).all()
        return tags
    
    def obter_tag_por_id(tag_id):
        """
        Obtém uma tag pelo seu ID.

        Args:
            tag_id (int): ID da tag a ser obtida.

        Returns:
            TagModel: Objeto TagModel correspondente ao ID fornecido, ou None se não encontrado.
        """
        
        tag = TagModel.query.filter(
            and_(
                TagModel.id == tag_id,
                TagModel.deletado == False
            )
        ).first()
        return tag