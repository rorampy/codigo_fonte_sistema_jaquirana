from datetime import datetime, date
from sistema.models_views.base_model import BaseModel, db
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
from sistema.models_views.financeiro.operacional.categorizar_fatura.categorizacao_model import AgendamentoPagamentoModel
from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
from sistema.models_views.financeiro.lancamento_avulso.lancamento_avulso_model import LancamentoAvulsoModel
from sqlalchemy import and_, or_, extract
import json


class DFCModel:
    """
    Modelo para processamento de dados do DFC (Demonstrativo de Fluxo de Caixa)
    """
    
    @staticmethod
    def calcular_valores_por_categoria(data_inicio=None, data_fim=None, categoria_ids=None):
        """
        Calcula valores por categoria baseado nos agendamentos de pagamento
        
        Args:
            data_inicio (date, optional): Data de início do período
            data_fim (date, optional): Data de fim do período
            categoria_ids (list, optional): Lista de IDs de categorias específicas
            
        Returns:
            dict: Dicionário com valores por categoria
        """
        try:
            query = AgendamentoPagamentoModel.query.filter(
                AgendamentoPagamentoModel.ativo == True,
                AgendamentoPagamentoModel.deletado == False,
                AgendamentoPagamentoModel.situacao_pagamento_id.in_([8, 9])
            )
            
            if data_inicio:
                query = query.filter(AgendamentoPagamentoModel.data_vencimento >= data_inicio)
            if data_fim:
                query = query.filter(AgendamentoPagamentoModel.data_vencimento <= data_fim)
            
            agendamentos = query.all()
            
            valores_categoria = {}
            
            for agendamento in agendamentos:
                if agendamento.categorias_json:
                    try:
                        categorias = json.loads(agendamento.categorias_json) if isinstance(agendamento.categorias_json, str) else agendamento.categorias_json
                        
                        if isinstance(categorias, list):
                            for categoria_info in categorias:
                                if isinstance(categoria_info, dict) and 'categoria_id' in categoria_info:
                                    categoria_id = categoria_info['categoria_id']
                                    valor = categoria_info.get('valor', 0)
                                    
                                    if categoria_ids is None or categoria_id in categoria_ids:
                                        if categoria_id not in valores_categoria:
                                            valores_categoria[categoria_id] = 0
                                        valores_categoria[categoria_id] += valor
                    except (json.JSONDecodeError, TypeError):
                        continue
            
            return valores_categoria
            
        except Exception as e:
            return {}
    
    @staticmethod
    def obter_hierarquia_categoria(categoria, categorias_dict):
        """
        Obtém a hierarquia completa de uma categoria (caminho do pai até a categoria)
        
        Args:
            categoria: Categoria atual
            categorias_dict: Dicionário com todas as categorias por ID
            
        Returns:
            str: Hierarquia completa (ex: "Compra de Madeira > Pinus")
        """
        hierarquia = []
        categoria_atual = categoria
        
        while categoria_atual:
            hierarquia.append(categoria_atual.nome)
            if categoria_atual.parent_id and categoria_atual.parent_id in categorias_dict:
                categoria_atual = categorias_dict[categoria_atual.parent_id]
            else:
                categoria_atual = None
        
        hierarquia.reverse()
        return " > ".join(hierarquia)

    @staticmethod
    def identificar_tipo_dre_por_codigo(codigo):
        """
        Identifica dinamicamente o tipo DRE baseado no código da categoria
        
        Args:
            codigo (str): Código da categoria
            
        Returns:
            str: Tipo DRE identificado
        """
        if not codigo:
            return 'outros'
            
        if codigo.startswith('1.01'):
            return 'receitas_operacionais'
        elif codigo.startswith('1.02'):
            return 'receitas_nao_operacionais'
        elif codigo.startswith('1.'):
            return 'receitas_outras'
            
        elif codigo.startswith('2.01'):
            return 'custos_operacionais'
        elif codigo.startswith('2.02'):
            return 'despesas_operacionais'
        elif codigo.startswith('2.'):
            return 'despesas_outras'
            
        else:
            return 'outros'

    @staticmethod
    def obter_estrutura_hierarquica_dre():
        """
        Obtém a estrutura hierárquica completa do plano de contas organizada para DRE
        seguindo a ordem exata da árvore hierárquica
        
        Returns:
            dict: Estrutura hierárquica organizada por tipo DRE
        """
        estrutura_completa = PlanoContaModel.obter_estrutura_hierarquica_completa()
        
        estrutura_dre = {
            'receitas_operacionais': [],
            'receitas_nao_operacionais': [],
            'receitas_outras': [],
            'custos_operacionais': [],
            'despesas_operacionais': [],
            'despesas_outras': []
        }
        
        def processar_categoria_recursiva(categoria, nivel=0):
            """Processa uma categoria e suas subcategorias recursivamente"""
            codigo = categoria.get('codigo', '')
            tipo_dre = DFCModel.identificar_tipo_dre_por_codigo(codigo)
            
            tem_filhos = bool(categoria.get('children'))
            
            if not tem_filhos and tipo_dre in estrutura_dre:
                categoria_info = {
                    'categoria_obj': categoria,
                    'codigo': codigo,
                    'nome': categoria.get('nome', ''),
                    'id': categoria.get('id'),
                    'parent_id': categoria.get('parent_id'),
                    'nivel': nivel,
                    'caminho_hierarquico': DFCModel._obter_caminho_categoria(categoria, estrutura_completa)
                }
                estrutura_dre[tipo_dre].append(categoria_info)
            
            for subcategoria in categoria.get('children', []):
                processar_categoria_recursiva(subcategoria, nivel + 1)
        
        for categoria_principal in estrutura_completa:
            processar_categoria_recursiva(categoria_principal)
        
        return estrutura_dre

    @staticmethod
    def _obter_caminho_categoria(categoria_alvo, estrutura_completa, caminho_atual=None):
        """
        Obtém o caminho hierárquico completo de uma categoria na estrutura
        
        Args:
            categoria_alvo: Categoria para a qual queremos o caminho
            estrutura_completa: Estrutura hierárquica completa
            caminho_atual: Caminho atual sendo construído
            
        Returns:
            str: Caminho hierárquico completo (ex: "Receitas > Receitas Operacionais > Venda de Madeira")
        """
        if caminho_atual is None:
            caminho_atual = []
        
        def buscar_na_estrutura(categorias, caminho):
            for categoria in categorias:
                novo_caminho = caminho + [categoria.get('nome', '')]
                
                if categoria.get('id') == categoria_alvo.get('id'):
                    return ' > '.join(novo_caminho)
                
                if categoria.get('children'):
                    resultado = buscar_na_estrutura(categoria['children'], novo_caminho)
                    if resultado:
                        return resultado
            
            return None
        
        return buscar_na_estrutura(estrutura_completa, [])

    @staticmethod
    def obter_categorias_folha_por_tipo():
        """
        Obtém todas as categorias "folha" organizadas por tipo DRE
        mantendo a ordem hierárquica do plano de contas
        
        Returns:
            dict: Categorias folha organizadas por classificação DRE com hierarquia completa
        """
        estrutura_hierarquica = DFCModel.obter_estrutura_hierarquica_dre()
        
        classificacao = {}
        
        for tipo_dre, categorias in estrutura_hierarquica.items():
            if categorias:
                classificacao[tipo_dre] = []
                
                for categoria_info in categorias:
                    categoria_formatada = {
                        'categoria': categoria_info['categoria_obj'],
                        'hierarquia_completa': categoria_info['caminho_hierarquico'],
                        'codigo': categoria_info['codigo'],
                        'nome': categoria_info['nome'],
                        'id': categoria_info['id'],
                        'nivel_hierarquia': categoria_info['nivel']
                    }
                    classificacao[tipo_dre].append(categoria_formatada)
        
        return classificacao

    @staticmethod
    def gerar_dfc_analitico(data_inicio, data_fim):
        """
        Gera o DFC analítico completo para um período específico baseado nas categorias folha
        
        Args:
            data_inicio (date): Data de início do período
            data_fim (date): Data de fim do período
            
        Returns:
            dict: DFC analítico estruturado
        """
        categorias_folha = DFCModel.obter_categorias_folha_por_tipo()
        
        valores_categoria = DFCModel.calcular_valores_por_categoria(data_inicio, data_fim)
        
        dre = {
            'periodo': {
                'data_inicio': data_inicio,
                'data_fim': data_fim
            },
            'receitas': {
                'total': 0,
                'operacionais': {'total': 0, 'detalhes': []},
                'nao_operacionais': {'total': 0, 'detalhes': []}
            },
            'custos': {
                'total': 0,
                'operacionais': {'total': 0, 'detalhes': []}
            },
            'despesas': {
                'total': 0,
                'operacionais': {'total': 0, 'detalhes': []}
            },
            'resultado': {
                'bruto': 0,
                'operacional': 0,
                'liquido': 0
            }
        }
        
        dre_secoes = {
            'receitas_operacionais': {'chave_dre': 'receitas.operacionais', 'nome': 'Receitas Operacionais'},
            'receitas_nao_operacionais': {'chave_dre': 'receitas.nao_operacionais', 'nome': 'Receitas Não-Operacionais'},
            'receitas_outras': {'chave_dre': 'receitas.outras', 'nome': 'Outras Receitas'},
            'custos_operacionais': {'chave_dre': 'custos.operacionais', 'nome': 'Custos Operacionais'},
            'despesas_operacionais': {'chave_dre': 'despesas.operacionais', 'nome': 'Despesas Operacionais'},
            'despesas_outras': {'chave_dre': 'despesas.outras', 'nome': 'Outras Despesas'}
        }
        
        for tipo in categorias_folha.keys():
            if tipo not in dre_secoes:
                continue
                
            secao_info = dre_secoes[tipo]
            chaves = secao_info['chave_dre'].split('.')
            
            if chaves[0] not in dre:
                dre[chaves[0]] = {'total': 0}
            if len(chaves) > 1 and chaves[1] not in dre[chaves[0]]:
                dre[chaves[0]][chaves[1]] = {'total': 0, 'detalhes': []}
        
        for tipo, categorias_lista in categorias_folha.items():
            if tipo not in dre_secoes:
                continue
                
            secao_info = dre_secoes[tipo]
            chaves = secao_info['chave_dre'].split('.')
            total_secao = 0
            detalhes_secao = []
            
            for categoria_info in categorias_lista:
                valor = valores_categoria.get(categoria_info['id'], 0)
                if valor != 0:
                    detalhes_secao.append({
                        'codigo': categoria_info['codigo'],
                        'nome': categoria_info['nome'],
                        'hierarquia_completa': categoria_info['hierarquia_completa'],
                        'valor': valor,
                        'categoria_id': categoria_info['id'],
                        'nivel_hierarquia': categoria_info['nivel_hierarquia']
                    })
                    total_secao += valor
            
            if len(chaves) == 1:
                dre[chaves[0]]['total'] += total_secao
                if 'detalhes' not in dre[chaves[0]]:
                    dre[chaves[0]]['detalhes'] = []
                dre[chaves[0]]['detalhes'].extend(detalhes_secao)
            else:
                dre[chaves[0]][chaves[1]]['total'] = total_secao
                dre[chaves[0]][chaves[1]]['detalhes'] = detalhes_secao
                dre[chaves[0]]['total'] += total_secao
        
        dre['resultado']['bruto'] = dre['receitas']['total'] - dre['custos']['total']
        
        dre['resultado']['margem_contribuicao'] = dre['receitas']['operacionais']['total'] - dre['custos']['operacionais']['total']
        
        if dre['receitas']['operacionais']['total'] != 0:
            dre['resultado']['margem_contribuicao_percentual'] = (dre['resultado']['margem_contribuicao'] / dre['receitas']['operacionais']['total']) * 100
        else:
            dre['resultado']['margem_contribuicao_percentual'] = 0
        
        dre['resultado']['operacional'] = dre['resultado']['bruto'] - dre['despesas']['total']
        
        atividades_investimento = 0
        if 'receitas' in dre and 'nao_operacionais' in dre['receitas']:
            for item in dre['receitas']['nao_operacionais']['detalhes']:
                if item['codigo'].startswith('1.02.01'):
                    atividades_investimento += item['valor']
        
        atividades_financiamento = 0
        if 'receitas' in dre and 'nao_operacionais' in dre['receitas']:
            for item in dre['receitas']['nao_operacionais']['detalhes']:
                if item['codigo'].startswith('1.02') and not item['codigo'].startswith('1.02.01'):
                    atividades_financiamento += item['valor']
        
        if 'despesas' in dre and 'operacionais' in dre['despesas']:
            for item in dre['despesas']['operacionais']['detalhes']:
                if item['codigo'].startswith('2.02.05'):
                    atividades_financiamento -= item['valor']
        
        dre['resultado']['atividades_investimento'] = atividades_investimento
        dre['resultado']['atividades_financiamento'] = atividades_financiamento
        
        dre['resultado']['variacao_caixa'] = (dre['resultado']['operacional'] + 
                                             dre['resultado']['atividades_investimento'] + 
                                             dre['resultado']['atividades_financiamento'])
        
        dre['resultado']['liquido'] = dre['resultado']['operacional']
        
        return dre
    

    
    @staticmethod
    def gerar_dfc_sintetico(data_inicio, data_fim):
        """
        Gera o DFC sintético para um período específico
        Aplica filtros específicos:
        - Receitas: Exclui 1.02.01 (Aplicações Financeiras) dos totais operacionais
        - Custos Operacionais: Exclui 2.01.11 (Compra de Floresta) e 2.02.05 (Retirada de Capital)
        
        Args:
            data_inicio (date): Data de início do período
            data_fim (date): Data de fim do período
            
        Returns:
            dict: DFC sintético estruturado
        """
        dre_analitico = DFCModel.gerar_dfc_analitico(data_inicio, data_fim)
        
        aplicacoes_financeiras = []
        compra_floresta = []
        retirada_capital = []
        
        receitas_nao_op_filtradas = 0
        for item in dre_analitico['receitas']['nao_operacionais']['detalhes']:
            if item['codigo'].startswith('1.02.01'):
                aplicacoes_financeiras.append(item)
            else:
                receitas_nao_op_filtradas += item['valor']
        
        custos_op_filtrados = 0
        for item in dre_analitico['custos']['operacionais']['detalhes']:
            if item['codigo'].startswith('2.01.11'):
                compra_floresta.append(item)
            elif item['codigo'].startswith('2.02.05'):
                retirada_capital.append(item)
            else:
                custos_op_filtrados += item['valor']
        
        despesas_op_filtradas = dre_analitico['despesas']['operacionais']['total']
        
        total_receitas_filtrado = dre_analitico['receitas']['operacionais']['total'] + receitas_nao_op_filtradas
        
        total_custos_filtrado = custos_op_filtrados
        
        resultado_bruto_filtrado = total_receitas_filtrado - total_custos_filtrado
        
        resultado_operacional_filtrado = resultado_bruto_filtrado - despesas_op_filtradas
        
        total_atividades_investimento = sum(item['valor'] for item in compra_floresta) * -1
        total_atividades_financiamento = (sum(item['valor'] for item in aplicacoes_financeiras) - 
                                        sum(item['valor'] for item in retirada_capital))
        
        variacao_caixa = resultado_operacional_filtrado + total_atividades_investimento + total_atividades_financiamento
        
        dre_sintetico = {
            'periodo': dre_analitico['periodo'],
            'receitas_operacionais': dre_analitico['receitas']['operacionais']['total'],
            'receitas_nao_operacionais': receitas_nao_op_filtradas,
            'total_receitas': total_receitas_filtrado,
            'total_receitas_nao_operacionais': sum(item['valor'] for item in aplicacoes_financeiras),
            'custos_operacionais': custos_op_filtrados,
            'resultado_bruto': resultado_bruto_filtrado,
            'despesas_operacionais': despesas_op_filtradas,
            'resultado_operacional': resultado_operacional_filtrado,
            'resultado_liquido': resultado_operacional_filtrado,
            
            'receitas_aplicacoes_financeiras': sum(item['valor'] for item in aplicacoes_financeiras),
            'despesas_compra_floresta': sum(item['valor'] for item in compra_floresta),
            'despesas_retirada_capital': sum(item['valor'] for item in retirada_capital),
            'total_investimento_retirada': total_atividades_investimento + (sum(item['valor'] for item in retirada_capital) * -1),
            
            'atividades_investimento': {
                'compra_floresta': compra_floresta,
                'total': total_atividades_investimento
            },
            
            'atividades_financiamento': {
                'aplicacoes_financeiras': aplicacoes_financeiras,
                'retirada_capital': retirada_capital,
                'total': total_atividades_financiamento
            },
            
            'variacao_caixa': variacao_caixa
        }
        
        return dre_sintetico