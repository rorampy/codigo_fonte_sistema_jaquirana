from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
from sistema.models_views.financeiro.operacional.categorizar_fatura.categorizacao_model import AgendamentoPagamentoModel
from sistema.models_views.faturamento.cargas_a_faturar.fornecedor.fornecedor_a_pagar_model import FornecedorPagarModel
from sistema.models_views.faturamento.cargas_a_faturar.transportadora.frete_a_pagar_model import FretePagarModel
from sistema.models_views.faturamento.cargas_a_faturar.extrator.extrator_a_pagar_model import ExtratorPagarModel
from sistema.models_views.faturamento.cargas_a_faturar.comissionado.comissionado_a_pagar_model import ComissionadoPagarModel
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
import json


class DREModel:
    """
    Modelo para processamento de dados do DRE (Demonstrativo de Resultado do Exercício)
    """
    
    @staticmethod
    def _varrer_tabelas_a_pagar(data_inicio, data_fim):
        """
        Varre as tabelas de 'a pagar' e retorna valores agrupados por código de categoria.
        
        Este método realiza queries diretas nas tabelas de fornecedor, frete, extrator e comissionado
        filtrando por data_entrega_ticket e somando os valores para categorização automática no DRE.
        
        Args:
            data_inicio (date): Data de início do período
            data_fim (date): Data de fim do período
            
        Returns:
            dict: Dicionário com códigos de categoria como chave e valores totais (em centavos)
        """
        valores_por_codigo = {}
        
        try:
            # 2.01.01 - Compra de Madeira (Fornecedores)
            fornecedores_query = FornecedorPagarModel.query.filter(
                FornecedorPagarModel.ativo == True,
                FornecedorPagarModel.deletado == False,
                FornecedorPagarModel.data_entrega_ticket.isnot(None)
            )
            
            if data_inicio:
                fornecedores_query = fornecedores_query.filter(
                    FornecedorPagarModel.data_entrega_ticket >= data_inicio
                )
            if data_fim:
                fornecedores_query = fornecedores_query.filter(
                    FornecedorPagarModel.data_entrega_ticket <= data_fim
                )
            
            fornecedores = fornecedores_query.all()
            total_fornecedores = sum(f.valor_total_a_pagar_100 or 0 for f in fornecedores)
            
            if total_fornecedores > 0:
                valores_por_codigo['2.01.01'] = total_fornecedores
            
            # 2.01.02 - Fretes (Transportadoras)
            fretes_query = FretePagarModel.query.filter(
                FretePagarModel.ativo == True,
                FretePagarModel.deletado == False,
                FretePagarModel.data_entrega_ticket.isnot(None)
            )
            
            if data_inicio:
                fretes_query = fretes_query.filter(
                    FretePagarModel.data_entrega_ticket >= data_inicio
                )
            if data_fim:
                fretes_query = fretes_query.filter(
                    FretePagarModel.data_entrega_ticket <= data_fim
                )
            
            fretes = fretes_query.all()
            total_fretes = sum(f.valor_total_a_pagar_100 or 0 for f in fretes)
            
            if total_fretes > 0:
                valores_por_codigo['2.01.02'] = total_fretes
            
            # 2.01.03 - Extração de madeira (Extratores)
            extratores_query = ExtratorPagarModel.query.filter(
                ExtratorPagarModel.ativo == True,
                ExtratorPagarModel.deletado == False,
                ExtratorPagarModel.data_entrega_ticket.isnot(None)
            )
            
            if data_inicio:
                extratores_query = extratores_query.filter(
                    ExtratorPagarModel.data_entrega_ticket >= data_inicio
                )
            if data_fim:
                extratores_query = extratores_query.filter(
                    ExtratorPagarModel.data_entrega_ticket <= data_fim
                )
            
            extratores = extratores_query.all()
            total_extratores = sum(e.valor_total_a_pagar_100 or 0 for e in extratores)
            
            if total_extratores > 0:
                valores_por_codigo['2.01.03'] = total_extratores
            
            # 2.01.04 - Comissões Compra Madeira (Comissionados)
            comissionados_query = ComissionadoPagarModel.query.filter(
                ComissionadoPagarModel.ativo == True,
                ComissionadoPagarModel.deletado == False,
                ComissionadoPagarModel.data_entrega_ticket.isnot(None)
            )
            
            if data_inicio:
                comissionados_query = comissionados_query.filter(
                    ComissionadoPagarModel.data_entrega_ticket >= data_inicio
                )
            if data_fim:
                comissionados_query = comissionados_query.filter(
                    ComissionadoPagarModel.data_entrega_ticket <= data_fim
                )
            
            comissionados = comissionados_query.all()
            total_comissionados = sum(c.valor_total_a_pagar_100 or 0 for c in comissionados)
            
            if total_comissionados > 0:
                valores_por_codigo['2.01.04'] = total_comissionados
            
            # 1.01.01 - Vendas Madeira (Registro Operacional)
            vendas_query = RegistroOperacionalModel.query.filter(
                RegistroOperacionalModel.ativo == True,
                RegistroOperacionalModel.deletado == False,
                RegistroOperacionalModel.data_entrega_ticket.isnot(None)
            )
            
            if data_inicio:
                vendas_query = vendas_query.filter(
                    RegistroOperacionalModel.data_entrega_ticket >= data_inicio
                )
            if data_fim:
                vendas_query = vendas_query.filter(
                    RegistroOperacionalModel.data_entrega_ticket <= data_fim
                )
            
            vendas = vendas_query.all()
            total_vendas = sum(v.valor_total_nota_100 or 0 for v in vendas)
            
            if total_vendas > 0:
                valores_por_codigo['1.01.01'] = total_vendas
            
        except Exception as e:
            print(f"[DRE] Erro ao varrer tabelas a pagar: {e}")
        
        return valores_por_codigo
    
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
            # Query base para agendamentos ativos e com situação financeira 6
            query = AgendamentoPagamentoModel.query.filter(
                AgendamentoPagamentoModel.ativo == True,
                AgendamentoPagamentoModel.deletado == False,
                AgendamentoPagamentoModel.situacao_pagamento_id.in_([6, 8, 9]) # Somente os categorizados, conciliados, ; conforme a solicitação
            )
            
            # Aplicar filtros de data
            if data_inicio:
                query = query.filter(AgendamentoPagamentoModel.data_competencia >= data_inicio)
            if data_fim:
                query = query.filter(AgendamentoPagamentoModel.data_competencia <= data_fim)
            
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
            
            # Varrer tabelas 'a pagar' para categorização automática
            valores_a_pagar = DREModel._varrer_tabelas_a_pagar(data_inicio, data_fim)
            
            # Converter códigos para IDs de categoria e adicionar aos valores
            for codigo, valor in valores_a_pagar.items():
                try:
                    categoria = PlanoContaModel.query.filter_by(
                        codigo=codigo,
                        ativo=True,
                        deletado=False
                    ).first()
                    
                    if categoria:
                        # Filtrar por categoria_ids se fornecido
                        if categoria_ids is None or categoria.id in categoria_ids:
                            if categoria.id not in valores_categoria:
                                valores_categoria[categoria.id] = 0
                            valores_categoria[categoria.id] += valor
                except Exception as e:
                    pass
            
            return valores_categoria
            
        except Exception as e:
            print(f"Erro ao calcular valores por categoria: {e}")
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
        
        # Percorrer a hierarquia do filho para o pai
        while categoria_atual:
            hierarquia.append(categoria_atual.nome)
            if categoria_atual.parent_id and categoria_atual.parent_id in categorias_dict:
                categoria_atual = categorias_dict[categoria_atual.parent_id]
            else:
                categoria_atual = None
        
        # Inverter para mostrar do pai para o filho
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
            
        # Receitas (código 1.xx.xx)
        if codigo.startswith('1.01'):
            return 'receitas_operacionais'
        elif codigo.startswith('1.02'):
            return 'receitas_nao_operacionais'
        elif codigo.startswith('1.'):
            return 'receitas_outras'
            
        # Custos e Despesas (código 2.xx.xx)
        # 2.01.xx = Custos Operacionais
        # Qualquer outro 2.xx = Despesas Operacionais (dinâmico para novos códigos criados pelo usuário)
        elif codigo.startswith('2.01'):
            return 'custos_operacionais'
        elif codigo.startswith('2.'):
            return 'despesas_operacionais'
            
        # Outros códigos
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
        # Obter estrutura hierárquica completa do plano de contas
        estrutura_completa = PlanoContaModel.obter_estrutura_hierarquica_completa()
        
        # Organizar por tipos DRE mantendo a ordem hierárquica
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
            tipo_dre = DREModel.identificar_tipo_dre_por_codigo(codigo)
            
            # Identificar se é categoria folha (sem filhos)
            tem_filhos = bool(categoria.get('children'))
            
            if not tem_filhos and tipo_dre in estrutura_dre:
                # É categoria folha, adicionar à estrutura DRE
                categoria_info = {
                    'categoria_obj': categoria,
                    'codigo': codigo,
                    'nome': categoria.get('nome', ''),
                    'id': categoria.get('id'),
                    'parent_id': categoria.get('parent_id'),
                    'nivel': nivel,
                    'caminho_hierarquico': DREModel._obter_caminho_categoria(categoria, estrutura_completa)
                }
                estrutura_dre[tipo_dre].append(categoria_info)
            
            # Processar subcategorias recursivamente
            for subcategoria in categoria.get('children', []):
                processar_categoria_recursiva(subcategoria, nivel + 1)
        
        # Processar toda a estrutura
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
                
                # Buscar nas subcategorias
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
        estrutura_hierarquica = DREModel.obter_estrutura_hierarquica_dre()
        
        # Converter para o formato esperado pelo template
        classificacao = {}
        
        for tipo_dre, categorias in estrutura_hierarquica.items():
            if categorias:  # Só incluir tipos que tenham categorias
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
    def gerar_dre_analitico(data_inicio, data_fim):
        """
        Gera o DRE analítico completo para um período específico baseado nas categorias folha
        
        Args:
            data_inicio (date): Data de início do período
            data_fim (date): Data de fim do período
            
        Returns:
            dict: DRE analítico estruturado
        """
        # Obter categorias folha organizadas
        categorias_folha = DREModel.obter_categorias_folha_por_tipo()
        
        # Calcular valores por categoria
        valores_categoria = DREModel.calcular_valores_por_categoria(data_inicio, data_fim)
        
        # Estrutura base do DRE (será expandida dinamicamente)
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
        
        # Processar dinamicamente todas as categorias encontradas
        dre_secoes = {
            'receitas_operacionais': {'chave_dre': 'receitas.operacionais', 'nome': 'Receitas Operacionais'},
            'receitas_nao_operacionais': {'chave_dre': 'receitas.nao_operacionais', 'nome': 'Receitas Não-Operacionais'},
            'receitas_outras': {'chave_dre': 'receitas.outras', 'nome': 'Outras Receitas'},
            'custos_operacionais': {'chave_dre': 'custos.operacionais', 'nome': 'Custos Operacionais'},
            'despesas_operacionais': {'chave_dre': 'despesas.operacionais', 'nome': 'Despesas Operacionais'},
            'despesas_outras': {'chave_dre': 'despesas.outras', 'nome': 'Outras Despesas'}
        }
        
        # Inicializar seções dinâmicas no DRE
        for tipo in categorias_folha.keys():
            if tipo not in dre_secoes:
                continue
                
            secao_info = dre_secoes[tipo]
            chaves = secao_info['chave_dre'].split('.')
            
            # Criar estrutura se não existir
            if chaves[0] not in dre:
                dre[chaves[0]] = {'total': 0}
            if len(chaves) > 1 and chaves[1] not in dre[chaves[0]]:
                dre[chaves[0]][chaves[1]] = {'total': 0, 'detalhes': []}
        
        # Processar cada tipo dinamicamente
        for tipo, categorias_lista in categorias_folha.items():
            if tipo not in dre_secoes:
                continue
                
            secao_info = dre_secoes[tipo]
            chaves = secao_info['chave_dre'].split('.')
            total_secao = 0
            detalhes_secao = []
            
            for categoria_info in categorias_lista:
                valor = valores_categoria.get(categoria_info['id'], 0)
                
                 #Ignorar categorias específicas (Colheita mecanizada 2.01.05)
                if categoria_info['codigo'].startswith('2.01.05'):
                    continue
                
                if valor != 0:  # Só incluir se tiver valor
                    detalhes_secao.append({
                        'codigo': categoria_info['codigo'],
                        'nome': categoria_info['nome'],
                        'hierarquia_completa': categoria_info['hierarquia_completa'],
                        'valor': valor,
                        'categoria_id': categoria_info['id'],
                        'nivel_hierarquia': categoria_info['nivel_hierarquia']
                    })
                    total_secao += valor
            
            # Atualizar estrutura DRE
            if len(chaves) == 1:
                dre[chaves[0]]['total'] += total_secao
                if 'detalhes' not in dre[chaves[0]]:
                    dre[chaves[0]]['detalhes'] = []
                dre[chaves[0]]['detalhes'].extend(detalhes_secao)
            else:
                dre[chaves[0]][chaves[1]]['total'] = total_secao
                dre[chaves[0]][chaves[1]]['detalhes'] = detalhes_secao
                dre[chaves[0]]['total'] += total_secao
        
        # Calcular resultados
        dre['resultado']['bruto'] = dre['receitas']['total'] - dre['custos']['total']
        
        # Calcular Margem de Contribuição (A+B) onde:
        # A = Receitas Operacionais
        # B = Custos Operacionais (como valor negativo na fórmula, então é subtração)
        # Margem de Contribuição = Receitas Operacionais - Custos Operacionais
        dre['resultado']['margem_contribuicao'] = dre['receitas']['operacionais']['total'] - dre['custos']['operacionais']['total']
        
        # Calcular percentual da Margem de Contribuição em relação às receitas operacionais
        if dre['receitas']['operacionais']['total'] != 0:
            dre['resultado']['margem_contribuicao_percentual'] = (dre['resultado']['margem_contribuicao'] / dre['receitas']['operacionais']['total']) * 100
        else:
            dre['resultado']['margem_contribuicao_percentual'] = 0
        
        # Resultado Operacional = Margem de Contribuição - Despesas Operacionais (apenas)
        dre['resultado']['operacional'] = dre['resultado']['margem_contribuicao'] - dre['despesas']['operacionais']['total']
        
        # Calcular Atividades de Investimento e Financiamento
        # Atividades de Investimento (categorias 1.02.xx - aplicações financeiras)
        atividades_investimento = 0
        if 'receitas' in dre and 'nao_operacionais' in dre['receitas']:
            for item in dre['receitas']['nao_operacionais']['detalhes']:
                if item['codigo'].startswith('1.02.01'):  # Aplicações financeiras
                    atividades_investimento += item['valor']
        
        # Atividades de Financiamento (categorias 1.02.xx exceto 1.02.01)
        atividades_financiamento = 0
        if 'receitas' in dre and 'nao_operacionais' in dre['receitas']:
            for item in dre['receitas']['nao_operacionais']['detalhes']:
                if item['codigo'].startswith('1.02') and not item['codigo'].startswith('1.02.01'):
                    atividades_financiamento += item['valor']
        
        # Adicionar despesas de financiamento (categorias 2.02.05 - retirada de capital)
        if 'despesas' in dre and 'operacionais' in dre['despesas']:
            for item in dre['despesas']['operacionais']['detalhes']:
                if item['codigo'].startswith('2.02.05'):  # Retirada de capital
                    atividades_financiamento -= item['valor']
        
        # Armazenar os valores das atividades
        dre['resultado']['atividades_investimento'] = atividades_investimento
        dre['resultado']['atividades_financiamento'] = atividades_financiamento
        
        # Calcular Variação de Caixa = Resultado Operacional + Atividades de Investimento + Atividades de Financiamento
        dre['resultado']['variacao_caixa'] = (dre['resultado']['operacional'] + 
                                             dre['resultado']['atividades_investimento'] + 
                                             dre['resultado']['atividades_financiamento'])
        
        dre['resultado']['liquido'] = dre['resultado']['operacional']
        
        return dre
    

    
    @staticmethod
    def gerar_dre_sintetico(data_inicio, data_fim):
        """
        Gera o DRE sintético para um período específico
        Aplica filtros específicos:
        - Receitas: Exclui 1.02.01 (Aplicações Financeiras) dos totais operacionais
        - Custos Operacionais: Exclui 2.01.11 (Compra de Floresta) e 2.02.05 (Retirada de Capital)
        
        Args:
            data_inicio (date): Data de início do período
            data_fim (date): Data de fim do período
            
        Returns:
            dict: DRE sintético estruturado
        """
        dre_analitico = DREModel.gerar_dre_analitico(data_inicio, data_fim)
        
        # Separar itens filtrados para atividades de investimento e financiamento
        aplicacoes_financeiras = []  # 1.02.01
        compra_floresta = []         # 2.01.11
        retirada_capital = []        # 2.02.05
        
        # Calcular receitas não-operacionais sem aplicações financeiras (1.02.01)
        receitas_nao_op_filtradas = 0
        for item in dre_analitico['receitas']['nao_operacionais']['detalhes']:
            if item['codigo'].startswith('1.02.01'):
                aplicacoes_financeiras.append(item)
            else:
                receitas_nao_op_filtradas += item['valor']
        
        # Calcular custos operacionais sem compra de floresta (2.01.11) e sem retirada de capital (2.02.05)
        custos_op_filtrados = 0
        for item in dre_analitico['custos']['operacionais']['detalhes']:
            if item['codigo'].startswith('2.01.11'):
                compra_floresta.append(item)
            elif item['codigo'].startswith('2.02.05'):
                retirada_capital.append(item)
            else:
                custos_op_filtrados += item['valor']
        
        # Calcular despesas operacionais (sem exclusões específicas)
        despesas_op_filtradas = dre_analitico['despesas']['operacionais']['total']
        
        # Total de receitas sem aplicações financeiras
        total_receitas_filtrado = dre_analitico['receitas']['operacionais']['total'] + receitas_nao_op_filtradas
        
        # Total de custos sem compra de floresta
        total_custos_filtrado = custos_op_filtrados
        
        # Resultado bruto = Receitas - Custos (ambos filtrados)
        resultado_bruto_filtrado = total_receitas_filtrado - total_custos_filtrado
        
        # Resultado operacional = Resultado bruto - Despesas operacionais (filtradas)
        resultado_operacional_filtrado = resultado_bruto_filtrado - despesas_op_filtradas
        
        # Calcular totais das atividades
        total_atividades_investimento = sum(item['valor'] for item in compra_floresta) * -1  # Negativo pois é custo
        total_atividades_financiamento = (sum(item['valor'] for item in aplicacoes_financeiras) - 
                                        sum(item['valor'] for item in retirada_capital))
        
        # Calcular variação de caixa
        variacao_caixa = resultado_operacional_filtrado + total_atividades_investimento + total_atividades_financiamento
        
        # Estrutura sintética com valores filtrados e atividades separadas
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
            'resultado_liquido': resultado_operacional_filtrado,  # No sintético, resultado líquido = operacional
            
            # Campos específicos para o template sintético
            'receitas_aplicacoes_financeiras': sum(item['valor'] for item in aplicacoes_financeiras),
            'despesas_compra_floresta': sum(item['valor'] for item in compra_floresta),
            'despesas_retirada_capital': sum(item['valor'] for item in retirada_capital),
            'total_investimento_retirada': total_atividades_investimento + (sum(item['valor'] for item in retirada_capital) * -1),
            
            # Atividades de Investimento (itens filtrados)
            'atividades_investimento': {
                'compra_floresta': compra_floresta,
                'total': total_atividades_investimento
            },
            
            # Atividades de Financiamento (itens filtrados)  
            'atividades_financiamento': {
                'aplicacoes_financeiras': aplicacoes_financeiras,
                'retirada_capital': retirada_capital,
                'total': total_atividades_financiamento
            },
            
            # Variação de Caixa
            'variacao_caixa': variacao_caixa
        }
        
        return dre_sintetico