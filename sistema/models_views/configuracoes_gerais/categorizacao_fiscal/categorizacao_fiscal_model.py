from ...base_model import BaseModel, db
from sqlalchemy import and_, desc
from sqlalchemy.orm import relationship


class CategorizacaoFiscalModel(BaseModel):
    """
    Model para registro de categorizacaoFiscal
    """
    
    __tablename__ = "ca_categorizacao_fiscal"
    
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False, index=True)
    nome = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.Integer, nullable=False)
    nivel = db.Column(db.Integer, nullable=False, default=1)
    parent_id = db.Column(db.Integer, db.ForeignKey('ca_categorizacao_fiscal.id'), nullable=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    parent = relationship("CategorizacaoFiscalModel", remote_side=[id], backref="children")
    
    def __init__(self, codigo=None, nome=None, tipo=None, parent_id=None, nivel=1, ativo=True):
        self.codigo = codigo
        self.nome = nome
        self.tipo = tipo
        self.parent_id = parent_id
        self.nivel = nivel
        self.ativo = ativo
    
    @classmethod
    def buscar_por_codigo(cls, codigo):
        """
        Busca categoria por código (apenas ativas).
        
        Args:
            codigo (str): Código da categoria a ser buscada
            
        Returns:
            CategorizacaoFiscalModel: Categoria encontrada ou None se não existir
        """
        return cls.query.filter_by(codigo=codigo, ativo=True).first()

    @classmethod
    def buscar_principais(cls):
        """
        Busca categorias principais (nível 1, apenas ativas).
        
        Returns:
            list: Lista de categorias principais ordenadas por código
        """
        return cls.query.filter_by(nivel=1, ativo=True).order_by(cls.codigo).all()

    @classmethod
    def buscar_filhos(cls, parent_id):
        """
        Busca subcategorias de uma categoria pai (apenas ativas).
        
        Args:
            parent_id (int): ID da categoria pai
            
        Returns:
            list: Lista de subcategorias ordenadas por código
        """
        return cls.query.filter_by(parent_id=parent_id, ativo=True).order_by(cls.codigo).all()

    @classmethod
    def gerar_proximo_codigo(cls, parent_code=None):
        """
        Gera o próximo código disponível para uma subcategoria.
        
        Args:
            parent_code (str, optional): Código da categoria pai
            
        Returns:
            str: Próximo código disponível ou None se parent_code for None
        """
        if parent_code is None:
            return None
        
        if '.' not in parent_code:
            subcategorias = cls.query.filter(
                cls.codigo.like(f"{parent_code}.%"),
                ~cls.codigo.like(f"{parent_code}.%.%"),
                cls.ativo == True 
            ).all()
            
            if not subcategorias:
                return f"{parent_code}.01"
            
            numeros = []
            for sub in subcategorias:
                try:
                    num = int(sub.codigo.split('.')[1])
                    numeros.append(num)
                except (IndexError, ValueError):
                    continue
            
            proximo = 1
            while proximo in numeros:
                proximo += 1
            
            return f"{parent_code}.{proximo:02d}"
        
        else:
            sub_subcategorias = cls.query.filter(
                cls.codigo.like(f"{parent_code}.%"),
                cls.ativo == True  
            ).all()
            
            if not sub_subcategorias:
                return f"{parent_code}.01"
            
            numeros = []
            for subsub in sub_subcategorias:
                try:
                    parts = subsub.codigo.split('.')
                    if len(parts) == 3:
                        num = int(parts[2])
                        numeros.append(num)
                except (IndexError, ValueError):
                    continue
            
            proximo = 1
            while proximo in numeros:
                proximo += 1
            
            return f"{parent_code}.{proximo:02d}"

    @classmethod
    def verificar_codigo_disponivel(cls, codigo):
        """
        Verifica se um código está disponível.
        
        Args:
            codigo (str): Código a ser verificado
            
        Returns:
            bool: True se disponível, False se já existe e está ativo
        """
        existe_ativo = cls.query.filter_by(codigo=codigo, ativo=True).first()
        return existe_ativo is None

    @classmethod
    def reativar_categoria(cls, codigo):
        """
        Reativa uma categoria que foi excluída (soft delete).
        
        Args:
            codigo (str): Código da categoria a ser reativada
            
        Returns:
            CategorizacaoFiscalModel: Categoria reativada ou None se não encontrada
        """
        categoria_inativa = cls.query.filter_by(codigo=codigo, ativo=False).first()
        if categoria_inativa:
            categoria_inativa.ativo = True
            db.session.commit()
            return categoria_inativa
        return None

    def calcular_nivel(self):
        """
        Calcula o nível baseado no código.
        
        Returns:
            int: Nível da categoria (1, 2 ou 3)
        """
        if '.' not in self.codigo:
            return 1
        elif self.codigo.count('.') == 1:
            return 2
        else:
            return 3

    def get_children_ordenados(self):
        """
        Retorna filhos ordenados por código (apenas ativos).
        
        Returns:
            list: Lista de categorias filhas ordenadas por código
        """
        return self.__class__.query.filter_by(
            parent_id=self.id,
            ativo=True  
        ).order_by(self.__class__.codigo).all()

    def soft_delete(self):
        """
        Exclui categoria (soft delete) e todos os filhos recursivamente.
        
        Returns:
            None
        """
        filhos = self.get_children_ordenados()
        for filho in filhos:
            filho.soft_delete()
        
        self.ativo = False
        db.session.commit()

    def to_dict(self):
        """
        Converte categoria para dicionário.
        
        Returns:
            dict: Dicionário com dados da categoria
        """
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nome': self.nome,
            'tipo': self.tipo,
            'nivel': self.nivel,
            'parent_id': self.parent_id,
            'ativo': self.ativo
        }


def criar_categoria_com_tratamento_duplicacao(codigo, nome, tipo, parent_id=None, nivel=1):
    """
    Cria categoria com tratamento inteligente de duplicação.
    
    Args:
        codigo (str): Código da categoria
        nome (str): Nome da categoria
        tipo (str): Tipo da categoria
        parent_id (int, optional): ID da categoria pai
        nivel (int, optional): Nível da categoria (padrão: 1)
        
    Returns:
        CategorizacaoFiscalModel: Categoria criada ou reativada
        
    Raises:
        ValueError: Se código já existe e está ativo
        Exception: Se ocorrer erro durante criação/reativação
    """
    try:
        categoria_existente = CategorizacaoFiscalModel.buscar_por_codigo(codigo)
        if categoria_existente:
            raise ValueError(f"Código {codigo} já existe e está ativo")
        
        categoria_inativa = CategorizacaoFiscalModel.query.filter_by(codigo=codigo, ativo=False).first()
        
        if categoria_inativa:
            categoria_inativa.nome = nome
            categoria_inativa.ativo = True
            db.session.commit()
            return categoria_inativa
        else:
            nova_categoria = CategorizacaoFiscalModel(
                codigo=codigo,
                nome=nome,
                tipo=tipo,
                parent_id=parent_id,
                nivel=nivel
            )
            db.session.add(nova_categoria)
            db.session.commit()
            return nova_categoria
            
    except Exception as e:
        db.session.rollback()
        raise