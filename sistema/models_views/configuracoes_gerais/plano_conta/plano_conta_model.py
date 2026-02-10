from ...base_model import BaseModel, db
from sqlalchemy import and_, desc
from sqlalchemy.orm import relationship


class PlanoContaModel(BaseModel):
    """
    Model para registro de plano de conta
    """
    
    __tablename__ = "plan_plano_conta"
    
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    codigo = db.Column(db.String(255), unique=True, nullable=False, index=True)
    nome = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.Integer, nullable=False)  # 1=Receita, 2=Despesa, 3=Movimentação
    nivel = db.Column(db.Integer, nullable=False, default=1)  # 1=Principal, 2=Sub, 3=SubSub
    parent_id = db.Column(db.Integer, db.ForeignKey('plan_plano_conta.id'), nullable=True)
    controle_estrutura = db.Column(db.Boolean, default=False, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relacionamentos
    parent = relationship("PlanoContaModel", remote_side=[id], backref="children")
    
    def __init__(self, controle_estrutura=None, codigo=None, nome=None, tipo=None, parent_id=None, nivel=1, ativo=True):
        self.controle_estrutura = controle_estrutura
        self.codigo = codigo
        self.nome = nome
        self.tipo = tipo
        self.parent_id = parent_id
        self.nivel = nivel
        self.ativo = ativo

    # Metodo complementar para permitir a liberação da estrutura para role_id != 1
    @staticmethod
    def listar_todos_planos():
        """
        Lista todos os planos de conta ativos.
        """
        
        return PlanoContaModel.query.filter_by(ativo=True, deletado=False).order_by(PlanoContaModel.id).all()
    
        
    @classmethod
    def buscar_por_codigo(cls, codigo):
        """
        Busca plano de conta por código (apenas ativas).
        
        Args:
            codigo (str): Código do plano de conta a ser buscado
            
        Returns:
            PlanoContaModel: Plano de conta encontrado ou None se não existir
        """
        return cls.query.filter_by(codigo=codigo, ativo=True).first()

    @classmethod
    def buscar_por_id(cls, id):
        """
        Busca plano de conta por ID (apenas ativas).
        
        Args:
            id (int): ID do plano de conta a ser buscado
            
        Returns:
            PlanoContaModel: Plano de conta encontrado ou None se não existir
        """
        return cls.query.filter_by(id=id, ativo=True).first()

    @classmethod
    def buscar_principais(cls):
        """
        Busca contas principais (nível 1, apenas ativas).
        
        Returns:
            list: Lista de contas principais ordenadas por código
        """
        return cls.query.filter_by(nivel=1, ativo=True).order_by(cls.codigo).all()

    @classmethod
    def buscar_filhos(cls, parent_id):
        """
        Busca subcontas de uma conta pai (apenas ativas).
        
        Args:
            parent_id (int): ID da conta pai
            
        Returns:
            list: Lista de subcontas ordenadas por código
        """
        return cls.query.filter_by(parent_id=parent_id, ativo=True).order_by(cls.codigo).all()

    @classmethod
    def gerar_proximo_codigo(cls, parent_code=None):
        """
        Gera o próximo código disponível para uma subconta.
        
        Args:
            parent_code (str, optional): Código da conta pai
            
        Returns:
            str: Próximo código disponível ou None se parent_code for None
        """
        if parent_code is None:
            return None
        
        if '.' not in parent_code:
            # Para subcategorias (1.01, 1.02, etc.)
            subcategorias = cls.query.filter(
                cls.codigo.like(f"{parent_code}.%"),
                ~cls.codigo.like(f"{parent_code}.%.%"),
                cls.ativo == True
            ).all()
            
            if not subcategorias:
                return f"{parent_code}.01"
            
            # Extrair números das subcategorias (ativas e inativas)
            numeros = []
            for sub in subcategorias:
                try:
                    num = int(sub.codigo.split('.')[1])
                    numeros.append(num)
                except (IndexError, ValueError):
                    continue
            
            # Encontrar próximo número disponível
            proximo = 1
            while proximo in numeros:
                proximo += 1
            
            return f"{parent_code}.{proximo:02d}"
        
        else:
            # Para sub-subcategorias e níveis mais profundos
            sub_subcategorias = cls.query.filter(
                cls.codigo.like(f"{parent_code}.%"),
                cls.ativo == True
            ).all()
            
            if not sub_subcategorias:
                return f"{parent_code}.01"
            
            # Extrair números das sub-subcategorias (ativas e inativas)
            numeros = []
            nivel_esperado = parent_code.count('.') + 2  # Próximo nível
            
            for subsub in sub_subcategorias:
                try:
                    parts = subsub.codigo.split('.')
                    if len(parts) == nivel_esperado:
                        num = int(parts[-1])  # Último número do código
                        numeros.append(num)
                except (IndexError, ValueError):
                    continue
            
            # Encontrar próximo número disponível
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
        Reativa uma conta que foi excluída (soft delete).
        
        Args:
            codigo (str): Código da conta a ser reativada
            
        Returns:
            PlanoContaModel: Conta reativada ou None se não encontrada
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
            int: Nível da conta (1, 2 ou 3)
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
            list: Lista de contas filhas ordenadas por código
        """
        return self.__class__.query.filter_by(
            parent_id=self.id,
            ativo=True  
        ).order_by(self.__class__.codigo).all()

    def soft_delete(self):
        """
        Exclui conta (soft delete) e todos os filhos recursivamente.
        
        Returns:
            None
        """
        # Excluir filhos recursivamente
        filhos = self.get_children_ordenados()
        for filho in filhos:
            filho.soft_delete()
        
        # Excluir esta categoria
        self.ativo = False
        db.session.commit()

    def to_dict(self):
        """
        Converte conta para dicionário.
        
        Returns:
            dict: Dicionário com dados da conta
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

    @classmethod
    def obter_estrutura_hierarquica_completa(cls):
        """
        Retorna a estrutura hierárquica completa do plano de contas
        com todos os níveis organizados em árvore.
        
        Returns:
            list: Lista estruturada com categorias principais e seus filhos aninhados
        """
        # Buscar todas as categorias ativas e não deletadas ordenadas por código
        todas_categorias = cls.query.filter_by(ativo=True, deletado=False).order_by(cls.codigo).all()
        
        # Criar um dicionário para facilitar a busca por ID
        categorias_dict = {cat.id: cat.to_dict() for cat in todas_categorias}
        
        # Adicionar lista de filhos para cada categoria
        for cat in categorias_dict.values():
            cat['children'] = []
        
        # Organizar a hierarquia
        estrutura_raiz = []
        
        for categoria in todas_categorias:
            cat_dict = categorias_dict[categoria.id]
            
            if categoria.parent_id is None:
                # Categoria principal (raiz)
                estrutura_raiz.append(cat_dict)
            else:
                # Categoria filha - adicionar ao parent
                if categoria.parent_id in categorias_dict:
                    categorias_dict[categoria.parent_id]['children'].append(cat_dict)
        
        return estrutura_raiz
    
    @classmethod
    def obter_estrutura_plana_hierarquica(cls):
        """
        Retorna uma lista plana do plano de contas mantendo a ordem hierárquica
        com indicação visual de níveis (como no exemplo da imagem).
        
        Returns:
            list: Lista plana com categorias ordenadas hierarquicamente
        """
        estrutura_hierarquica = cls.obter_estrutura_hierarquica_completa()
        lista_plana = []
        
        def processar_nivel(categorias, nivel_indentacao=0):
            for categoria in categorias:
                # Adicionar a categoria atual com indicação de nível
                item = {
                    'id': categoria['id'],
                    'codigo': categoria['codigo'],
                    'nome': categoria['nome'],
                    'tipo': categoria['tipo'],
                    'nivel': categoria['nivel'],
                    'parent_id': categoria['parent_id'],
                    'nivel_indentacao': nivel_indentacao,
                    'indentacao_visual': '&nbsp;&nbsp;' * nivel_indentacao,
                    'tem_filhos': len(categoria['children']) > 0,
                    'ativo': categoria['ativo']
                }
                lista_plana.append(item)
                
                # Processar recursivamente os filhos
                if categoria['children']:
                    processar_nivel(categoria['children'], nivel_indentacao + 1)
        
        processar_nivel(estrutura_hierarquica)
        return lista_plana


def criar_categoria_com_tratamento_duplicacao(codigo, nome, tipo, parent_id=None, nivel=1):
    """
    Cria plano de conta com tratamento inteligente de duplicação.
    
    Args:
        codigo (str): Código da conta
        nome (str): Nome da conta
        tipo (str): Tipo da conta
        parent_id (int, optional): ID da conta pai
        nivel (int, optional): Nível da conta (padrão: 1)
        
    Returns:
        PlanoContaModel: Conta criada ou reativada
        
    Raises:
        ValueError: Se código já existe e está ativo
        Exception: Se ocorrer erro durante criação/reativação
    """
    try:
        # Verificar se código já existe como registro ativo
        categoria_existente = PlanoContaModel.buscar_por_codigo(codigo)
        if categoria_existente:
            raise ValueError(f"Código {codigo} já existe e está ativo")
        
        # Verificar se existe registro inativo com mesmo código
        categoria_inativa = PlanoContaModel.query.filter_by(codigo=codigo, ativo=False).first()
        
        if categoria_inativa:
            # Reativar categoria existente
            categoria_inativa.nome = nome  # Atualizar nome
            categoria_inativa.ativo = True
            db.session.commit()
            return categoria_inativa
        else:
            # Criar nova categoria
            nova_categoria = PlanoContaModel(
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

    