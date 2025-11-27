"""
Dashboard Model - Concentra toda a lógica de negócio para o dashboard principal.

Este módulo é responsável por:
- Coleta e processamento de dados do dashboard
- Cálculos de vendas, acumulados e rankings
- Mapeamento de produtos e categorização
- Preparação de dados para gráficos e visualizações
"""

from datetime import datetime
from calendar import monthrange
from sqlalchemy import extract, func
from sistema import db
from sistema.models_views.controle_carga.solicitacao_nf.carga_model import CargaModel
from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.controle_carga.nf_complementar.nf_entrada_model import NfEntradaModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.autenticacao.usuario_model import UsuarioModel


class DashboardModel:
    """
    Model responsável por toda a lógica de negócio do dashboard principal.
    
    Esta classe centraliza as consultas e cálculos necessários para:
    - Vendas por dia/período
    - Totais acumulados
    - Rankings de produtividade
    - Contra-notas
    - Mapeamento de produtos
    """
    
    # Configurações de grupos de produtos
    GRUPOS_PRODUTOS = [
        "eucalipto_torete",
        "pinus_torete", 
        "pinus_18_25",
        "pinus_25_32",
        "pinus_33_mais",
        "cavaco"
    ]
    
    PRODUTOS_LABELS = [
        "Eucalipto Torete",
        "Pinus Torete",
        "Pinus 18-25", 
        "Pinus 25-32",
        "Pinus 33+",
        "Biomassa"
    ]
    
    # Data de início para cálculos cumulativos
    DATA_INICIO_CUMULATIVO = datetime(2025, 5, 1)
    
    @staticmethod
    def mapear_produto_chave(nome, bitola):
        """
        Mapeia produto e bitola para a chave correta dos grupos.
        
        Args:
            nome (str): Nome do produto
            bitola (str): Bitola do produto
            
        Returns:
            str: Chave do grupo correspondente
        """
        chave_prod = (nome or "").lower()
        chave_bit = (
            (bitola or "").lower().strip().replace("-", "_").replace("+", "_mais")
        )
        
        # Lógica específica para cada tipo de produto
        if "biomassa" in chave_prod or chave_bit == "cavaco":
            return "cavaco"
        elif "eucalipto" in chave_prod:
            return f"eucalipto_{chave_bit}"
        else:  # pinus por padrão
            return f"pinus_{chave_bit}"
    
    @classmethod
    def obter_vendas_por_dia(cls, ano, mes, empresa_id):
        """
        Obtém vendas diárias por produto no período especificado.
        
        Args:
            ano (int): Ano de consulta
            mes (int): Mês de consulta  
            empresa_id (int): ID da empresa emissora
            
        Returns:
            tuple: (dados_por_grupo, labels, dados_front, mostrar_graficos)
        """
        dias_do_mes = list(range(1, monthrange(ano, mes)[1] + 1))
        data_por_grupo = {g: {d: 0 for d in dias_do_mes} for g in cls.GRUPOS_PRODUTOS}

        # Query para vendas diárias
        query_dia = (
            db.session.query(
                extract("day", RegistroOperacionalModel.data_entrega_ticket).label("dia"),
                ProdutoModel.nome,
                BitolaModel.bitola,
                func.coalesce(
                    func.sum(RegistroOperacionalModel.peso_liquido_ticket), 0
                ).label("total"),
            )
            .join(CargaModel, RegistroOperacionalModel.solicitacao_nf_id == CargaModel.id)
            .join(ProdutoModel, CargaModel.produto_id == ProdutoModel.id)
            .join(BitolaModel, CargaModel.bitola_id == BitolaModel.id)
            .filter(
                extract("year", RegistroOperacionalModel.data_entrega_ticket) == ano,
                extract("month", RegistroOperacionalModel.data_entrega_ticket) == mes,
                RegistroOperacionalModel.ativo == True,
                CargaModel.empresa_emissora_id == empresa_id,
            )
            .group_by("dia", ProdutoModel.nome, BitolaModel.bitola)
            .all()
        )

        # Processa dados da query
        for dia, nome, bitola, total in query_dia:
            chave = cls.mapear_produto_chave(nome, bitola)
            if chave in data_por_grupo:
                data_por_grupo[chave][int(dia)] += float(total)

        # Prepara dados para frontend
        labels = [str(d) for d in dias_do_mes]
        dados_front = {
            g: [round(data_por_grupo[g][d], 2) for d in dias_do_mes] 
            for g in cls.GRUPOS_PRODUTOS
        }
        mostrar_graficos = any(v > 0 for g in cls.GRUPOS_PRODUTOS for v in dados_front[g])
        
        return data_por_grupo, labels, dados_front, mostrar_graficos
    
    @classmethod 
    def obter_vendas_acumuladas_mes(cls, ano, mes, empresa_id):
        """
        Obtém vendas acumuladas do mês especificado.
        
        Args:
            ano (int): Ano de consulta
            mes (int): Mês de consulta
            empresa_id (int): ID da empresa emissora
            
        Returns:
            list: Valores acumulados por grupo de produto
        """
        acumulado_venda = {g: 0.0 for g in cls.GRUPOS_PRODUTOS}

        query_venda_acumulada = (
            db.session.query(
                ProdutoModel.nome,
                BitolaModel.bitola,
                func.coalesce(
                    func.sum(RegistroOperacionalModel.peso_liquido_ticket), 0
                ).label("total_venda"),
            )
            .join(CargaModel, RegistroOperacionalModel.solicitacao_nf_id == CargaModel.id)
            .join(ProdutoModel, CargaModel.produto_id == ProdutoModel.id)
            .join(BitolaModel, CargaModel.bitola_id == BitolaModel.id)
            .filter(
                extract("year", RegistroOperacionalModel.data_entrega_ticket) == ano,
                extract("month", RegistroOperacionalModel.data_entrega_ticket) == mes,
                RegistroOperacionalModel.ativo == True,
                CargaModel.empresa_emissora_id == empresa_id,
            )
            .group_by(ProdutoModel.nome, BitolaModel.bitola)
            .all()
        )

        # Agrupa totais por produto
        for nome, bitola, total in query_venda_acumulada:
            chave = cls.mapear_produto_chave(nome, bitola)
            if chave in acumulado_venda:
                acumulado_venda[chave] = float(total)

        return [round(acumulado_venda[g], 2) for g in cls.GRUPOS_PRODUTOS]
    
    @classmethod
    def obter_vendas_acumuladas_cumulativas(cls, empresa_id):
        """
        Obtém vendas cumulativas desde DATA_INICIO_CUMULATIVO.
        
        Args:
            empresa_id (int): ID da empresa emissora
            
        Returns:
            list: Valores acumulados cumulativos por grupo de produto
        """
        acumulado_venda_mes = {g: 0.0 for g in cls.GRUPOS_PRODUTOS}

        query_venda_acumulada_mes = (
            db.session.query(
                ProdutoModel.nome,
                BitolaModel.bitola,
                func.coalesce(
                    func.sum(RegistroOperacionalModel.peso_liquido_ticket), 0
                ).label("total_venda"),
            )
            .join(CargaModel, RegistroOperacionalModel.solicitacao_nf_id == CargaModel.id)
            .join(ProdutoModel, CargaModel.produto_id == ProdutoModel.id)
            .join(BitolaModel, CargaModel.bitola_id == BitolaModel.id)
            .filter(
                RegistroOperacionalModel.data_entrega_ticket >= cls.DATA_INICIO_CUMULATIVO,
                RegistroOperacionalModel.ativo == True,
                CargaModel.empresa_emissora_id == empresa_id,
            )
            .group_by(ProdutoModel.nome, BitolaModel.bitola)
            .all()
        )

        # Agrupa totais cumulativos por produto
        for nome, bitola, total in query_venda_acumulada_mes:
            chave = cls.mapear_produto_chave(nome, bitola)
            if chave in acumulado_venda_mes:
                acumulado_venda_mes[chave] = float(total)

        return [round(acumulado_venda_mes[g], 2) for g in cls.GRUPOS_PRODUTOS]
    
    @classmethod
    def obter_ranking_produtividade(cls, ano, mes):
        """
        Obtém ranking de produtividade dos usuários no período.
        
        Args:
            ano (int): Ano de consulta
            mes (int): Mês de consulta
            
        Returns:
            tuple: (dados_usuarios_front, tem_pontuacao)
        """
        hoje = datetime.today()
        dias_do_mes = list(range(1, monthrange(ano, mes)[1] + 1))
        
        # Define até que dia exibir
        if ano == hoje.year and mes == hoje.month:
            hoje_dia = hoje.day
        else:
            hoje_dia = monthrange(ano, mes)[1]

        # Obtém pontuações diárias
        pontuacoes = (
            db.session.query(
                func.day(PontuacaoUsuarioModel.data_cadastro).label("dia"),
                UsuarioModel.nome,
                func.sum(PontuacaoUsuarioModel.pontos).label("pontos"),
            )
            .join(UsuarioModel, PontuacaoUsuarioModel.usuario_id == UsuarioModel.id)
            .filter(
                extract("year", PontuacaoUsuarioModel.data_cadastro) == ano,
                extract("month", PontuacaoUsuarioModel.data_cadastro) == mes,
                PontuacaoUsuarioModel.ativo == True,
            )
            .group_by("dia", UsuarioModel.nome)
            .all()
        )

        # Organiza pontuações por usuário
        pontos_por_usuario = {}
        for dia, usuario, pts in pontuacoes:
            pontos_por_usuario.setdefault(usuario, {d: 0.0 for d in dias_do_mes})
            pontos_por_usuario[usuario][int(dia)] += float(pts)

        # Prepara dados para gráfico acumulativo
        dados_usuarios_front = []
        for usuario, mapa in pontos_por_usuario.items():
            acumul = 0.0
            serie = []
            for d in dias_do_mes:
                if d <= hoje_dia:
                    acumul += mapa[d]
                    label = usuario if d == hoje_dia and acumul > 0 else ""
                    serie.append({"x": str(d), "y": round(acumul, 2), "label": label})
                else:
                    serie.append({"x": str(d), "y": None, "label": ""})
            dados_usuarios_front.append({"name": usuario, "data": serie})

        # Verifica se há pontuação para exibir
        tem_pontuacao = any(
            any(p["y"] not in (None, 0) for p in usr["data"])
            for usr in dados_usuarios_front
        )
        
        return dados_usuarios_front, tem_pontuacao
    
    @classmethod
    def obter_contra_notas_acumuladas(cls, empresa_id):
        """
        Obtém contra-notas acumuladas cumulativas do ano atual.
        
        Args:
            empresa_id (int): ID da empresa emissora
            
        Returns:
            list: Valores de contra-notas acumuladas por grupo de produto
        """
        hoje = datetime.today()
        contra_por_grupo_mes = {g: 0.0 for g in cls.GRUPOS_PRODUTOS}

        query_contra_acumulada = (
            db.session.query(
                ProdutoModel.nome,
                BitolaModel.bitola,
                func.coalesce(func.sum(NfEntradaModel.peso_contra_nota), 0).label(
                    "total_contra"
                ),
            )
            .join(
                RegistroOperacionalModel,
                NfEntradaModel.registro_id == RegistroOperacionalModel.id,
            )
            .join(CargaModel, RegistroOperacionalModel.solicitacao_nf_id == CargaModel.id)
            .join(ProdutoModel, CargaModel.produto_id == ProdutoModel.id)
            .join(BitolaModel, CargaModel.bitola_id == BitolaModel.id)
            .filter(
                extract("year", NfEntradaModel.data_cadastro) == hoje.year,
                extract("month", NfEntradaModel.data_cadastro) <= hoje.month,
                NfEntradaModel.ativo == True,
                NfEntradaModel.deletado == False,
                NfEntradaModel.registro.has(deletado=False, ativo=True),
                CargaModel.empresa_emissora_id == empresa_id,
            )
            .group_by(ProdutoModel.nome, BitolaModel.bitola)
            .all()
        )

        # Agrupa totais de contra-notas por produto
        for nome, bitola, total in query_contra_acumulada:
            chave = cls.mapear_produto_chave(nome, bitola)
            if chave in contra_por_grupo_mes:
                contra_por_grupo_mes[chave] = float(total)

        return [round(contra_por_grupo_mes[g], 2) for g in cls.GRUPOS_PRODUTOS]
    
    @classmethod
    def obter_dados_completos_dashboard(cls, empresa_id, ano=None, mes=None):
        """
        Método principal que retorna todos os dados necessários para o dashboard.
        
        Args:
            empresa_id (int): ID da empresa emissora
            ano (int, optional): Ano de consulta (padrão: atual)
            mes (int, optional): Mês de consulta (padrão: atual)
            
        Returns:
            dict: Dicionário com todos os dados processados do dashboard
        """
        hoje = datetime.today()
        ano = ano or hoje.year
        mes = mes or hoje.month
        
        # Coleta todos os dados
        data_por_grupo, labels, dados_front, mostrar_graficos = cls.obter_vendas_por_dia(ano, mes, empresa_id)
        valores_acumulados = cls.obter_vendas_acumuladas_mes(ano, mes, empresa_id)
        valores_acumulados_mes = cls.obter_vendas_acumuladas_cumulativas(empresa_id)
        dados_usuarios_front, tem_pontuacao = cls.obter_ranking_produtividade(ano, mes)
        valores_contra_acumulados = cls.obter_contra_notas_acumuladas(empresa_id)
        
        return {
            # Dados de vendas
            'labels': labels,
            'dados_front': dados_front,
            'valores_acumulados': valores_acumulados,
            'valores_acumulados_mes': valores_acumulados_mes,
            'mostrar_linhas_graficas': mostrar_graficos,
            
            # Dados de produtividade
            'dados_usuarios_front': dados_usuarios_front,
            'tem_pontuacao': tem_pontuacao,
            
            # Dados de contra-notas
            'valores_contra_acumulados': valores_contra_acumulados,
            
            # Configurações
            'produtos_labels': cls.PRODUTOS_LABELS,
            'grupos': cls.GRUPOS_PRODUTOS,
            
            # Parâmetros
            'ano': ano,
            'mes': mes,
            'empresa_selecionada_id': empresa_id
        }