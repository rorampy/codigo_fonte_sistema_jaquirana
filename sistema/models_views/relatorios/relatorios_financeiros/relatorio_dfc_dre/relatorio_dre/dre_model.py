from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
from sistema.models_views.financeiro.operacional.categorizar_fatura.categorizacao_model import AgendamentoPagamentoModel
from sistema.models_views.faturamento.cargas_a_faturar.fornecedor.fornecedor_a_pagar_model import FornecedorPagarModel
from sistema.models_views.faturamento.cargas_a_faturar.transportadora.frete_a_pagar_model import FretePagarModel
from sistema.models_views.faturamento.cargas_a_faturar.extrator.extrator_a_pagar_model import ExtratorPagarModel
from sistema.models_views.faturamento.cargas_a_faturar.comissionado.comissionado_a_pagar_model import ComissionadoPagarModel
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.faturamento.cargas_a_receber.nf_complementar.nf_complementar_model import NfComplementarModel
import json


class DREModel:
    """
    Modelo para processamento de dados do DRE (Demonstrativo de Resultado do Exercício)
    
    Estrutura do Plano de Contas:
    - 1.01.xx = Receitas Operacionais (Vendas)
    - 1.02.xx = Receitas Não-Operacionais
    - 2.01.xx = Custos Operacionais (CMV)
    - 2.02.xx+ = Despesas Operacionais
    
    Categorias Automáticas (valores vêm das tabelas operacionais):
    - 1.01.01 = Vendas Madeira (RegistroOperacionalModel)
    - 2.01.01 = Compra de Madeira (FornecedorPagarModel)
    - 2.01.02 = Fretes (FretePagarModel)
    - 2.01.03 = Extração (ExtratorPagarModel)
    - 2.01.04 = Comissões (ComissionadoPagarModel)
    """
    
    # Configuração das categorias automáticas (valores vindos das tabelas operacionais)
    CATEGORIAS_AUTOMATICAS = {
        '1.01.01': {
            'model': RegistroOperacionalModel,
            'campo_valor': 'valor_total_nota_100',
            'campo_data': 'data_entrega_ticket',
            'filtro_operacional': 'solicitacao_nf_id',  # Exclui receitas avulsas
            'descricao': 'Vendas NFe Peso Padrão'
        },
        '1.01.03': {
            'model': NfComplementarModel,
            'campo_valor': 'valor_total_nota_100',
            'campo_data': 'destinatario_data_emissao',
            'filtro_operacional': 'cliente_id',  # Todas NF complementares são operacionais
            'descricao': 'Vendas de NFe Complementares'
        },
        '2.01.01': {
            'model': FornecedorPagarModel,
            'campo_valor': 'valor_total_a_pagar_100',
            'campo_data': 'data_entrega_ticket',
            'filtro_operacional': 'solicitacao_id',  # Exclui despesas avulsas
            'descricao': 'Compra de Madeira'
        },
        '2.01.02': {
            'model': FretePagarModel,
            'campo_valor': 'valor_total_a_pagar_100',
            'campo_data': 'data_entrega_ticket',
            'filtro_operacional': 'solicitacao_id',
            'descricao': 'Fretes'
        },
        '2.01.03': {
            'model': ExtratorPagarModel,
            'campo_valor': 'valor_total_a_pagar_100',
            'campo_data': 'data_entrega_ticket',
            'filtro_operacional': 'solicitacao_id',
            'descricao': 'Extração de Madeira'
        },
        '2.01.04': {
            'model': ComissionadoPagarModel,
            'campo_valor': 'valor_total_a_pagar_100',
            'campo_data': 'data_entrega_ticket',
            'filtro_operacional': 'solicitacao_id',
            'descricao': 'Comissões'
        }
    }
    
    # Mapeamento de código para tipo DRE
    TIPO_DRE_MAP = {
        '1.01': 'receitas_operacionais',
        '1.02': 'receitas_nao_operacionais',
        '2.01': 'custos_operacionais',
        # Qualquer 2.xx (exceto 2.01) = despesas_operacionais
    }
    
    # Códigos a ignorar no DRE (não impactam resultado)
    CODIGOS_IGNORADOS = [
        '2.01.05',  # Colheita mecanizada
        '3.',       # Transferências entre contas (não é receita nem despesa)
    ]
    
    # ==================== MÉTODOS PRINCIPAIS ====================
    
    @classmethod
    def gerar_dre(cls, data_inicio, data_fim):
        """
        Gera o DRE completo para um período.
        
        Returns:
            dict: Estrutura completa do DRE com receitas, custos, despesas e resultados
        """
        # 1. Obter valores por categoria
        valores = cls._calcular_valores_por_categoria(data_inicio, data_fim)
        
        # 2. Organizar por seções do DRE
        dre = cls._organizar_estrutura_dre(valores)
        
        # 3. Calcular totais e resultados
        cls._calcular_resultados(dre)
        
        # 4. Adicionar período
        dre['periodo'] = {'data_inicio': data_inicio, 'data_fim': data_fim}
        
        return dre
    
    @classmethod
    def gerar_dre_sintetico(cls, data_inicio, data_fim):
        """
        Gera versão sintética do DRE (resumida).
        """
        dre = cls.gerar_dre(data_inicio, data_fim)
        
        # Filtrar itens para atividades de investimento/financiamento
        aplicacoes_financeiras = [i for i in dre['receitas']['nao_operacionais']['itens'] 
                                   if i['codigo'].startswith('1.02.01')]
        compra_floresta = [i for i in dre['custos']['operacionais']['itens'] 
                          if i['codigo'].startswith('2.01.11')]
        retirada_capital = [i for i in dre['despesas']['operacionais']['itens'] 
                           if i['codigo'].startswith('2.02.05')]
        
        # Calcular totais filtrados
        total_aplicacoes = sum(i['valor'] for i in aplicacoes_financeiras)
        total_compra_floresta = sum(i['valor'] for i in compra_floresta)
        total_retirada_capital = sum(i['valor'] for i in retirada_capital)
        
        # Receitas sem aplicações financeiras
        receitas_nao_op_filtradas = dre['receitas']['nao_operacionais']['total'] - total_aplicacoes
        total_receitas_filtrado = dre['receitas']['operacionais']['total'] + receitas_nao_op_filtradas
        
        # Custos sem compra de floresta
        custos_filtrados = dre['custos']['operacionais']['total'] - total_compra_floresta
        
        # Resultados filtrados
        resultado_bruto = total_receitas_filtrado - custos_filtrados
        resultado_operacional = resultado_bruto - dre['despesas']['operacionais']['total']
        
        # Atividades
        atividades_investimento = total_compra_floresta * -1
        atividades_financiamento = total_aplicacoes - total_retirada_capital
        variacao_caixa = resultado_operacional + atividades_investimento + atividades_financiamento
        
        return {
            'periodo': dre['periodo'],
            'receitas_operacionais': dre['receitas']['operacionais']['total'],
            'receitas_nao_operacionais': receitas_nao_op_filtradas,
            'total_receitas': total_receitas_filtrado,
            'custos_operacionais': custos_filtrados,
            'resultado_bruto': resultado_bruto,
            'despesas_operacionais': dre['despesas']['operacionais']['total'],
            'resultado_operacional': resultado_operacional,
            'resultado_liquido': resultado_operacional,
            'atividades_investimento': {'total': atividades_investimento, 'itens': compra_floresta},
            'atividades_financiamento': {'total': atividades_financiamento, 'aplicacoes': aplicacoes_financeiras, 'retiradas': retirada_capital},
            'variacao_caixa': variacao_caixa,
            # Chaves esperadas pelo template PDF
            'receitas_aplicacoes_financeiras': total_aplicacoes,
            'despesas_compra_floresta': total_compra_floresta,
            'despesas_retirada_capital': total_retirada_capital
        }
    
    # ==================== MÉTODOS AUXILIARES ====================
    
    @classmethod
    def _calcular_valores_por_categoria(cls, data_inicio, data_fim):
        """
        Calcula valores de todas as categorias (automáticas + manuais).
        
        Returns:
            dict: {categoria_id: {'codigo': str, 'nome': str, 'valor': int, 'hierarquia': str}}
        """
        valores = {}
        
        # 1. Buscar valores das categorias automáticas (tabelas operacionais)
        valores_automaticos = cls._buscar_valores_automaticos(data_inicio, data_fim)
        
        # 2. Buscar IDs das categorias automáticas para excluir dos agendamentos
        ids_automaticas = set()
        for codigo in valores_automaticos.keys():
            cat = PlanoContaModel.query.filter_by(codigo=codigo, ativo=True, deletado=False).first()
            if cat:
                ids_automaticas.add(cat.id)
                valores[cat.id] = {
                    'codigo': codigo,
                    'nome': cat.nome,
                    'valor': valores_automaticos[codigo],
                    'hierarquia': cls._obter_hierarquia(cat)
                }
        
        # 3. Buscar valores dos agendamentos categorizados (exceto categorias automáticas)
        # Status: 6=Categorizado, 8=Conciliado, 9=Liquidado, 10=Parcialmente Conciliado
        # DRE é regime de competência: o valor categorizado entra independente do status de pagamento
        agendamentos = AgendamentoPagamentoModel.query.filter(
            AgendamentoPagamentoModel.ativo == True,
            AgendamentoPagamentoModel.deletado == False,
            AgendamentoPagamentoModel.situacao_pagamento_id.in_([6, 8, 9, 10]),
            AgendamentoPagamentoModel.data_competencia >= data_inicio,
            AgendamentoPagamentoModel.data_competencia <= data_fim
        ).all()
        
        for agendamento in agendamentos:
            if not agendamento.categorias_json:
                continue
            
            try:
                categorias = json.loads(agendamento.categorias_json) if isinstance(agendamento.categorias_json, str) else agendamento.categorias_json
                
                for cat_info in categorias or []:
                    cat_id = cat_info.get('categoria_id')
                    valor = cat_info.get('valor', 0)
                    
                    # Pular categorias sem ID válido
                    if not cat_id:
                        continue
                    
                    # Pular categorias automáticas
                    if cat_id in ids_automaticas:
                        continue
                    
                    if cat_id not in valores:
                        cat = PlanoContaModel.query.get(cat_id)
                        if cat:
                            valores[cat_id] = {
                                'codigo': cat.codigo,
                                'nome': cat.nome,
                                'valor': 0,
                                'hierarquia': cls._obter_hierarquia(cat)
                            }
                    
                    if cat_id in valores:
                        valores[cat_id]['valor'] += valor
                        
            except (json.JSONDecodeError, TypeError):
                continue
        
        return valores
    
    @classmethod
    def _buscar_valores_automaticos(cls, data_inicio, data_fim):
        """
        Busca valores das categorias automáticas (tabelas operacionais).
        
        Returns:
            dict: {codigo_categoria: valor_total_centavos}
        """
        valores = {}
        
        for codigo, config in cls.CATEGORIAS_AUTOMATICAS.items():
            Model = config['model']
            campo_valor = config['campo_valor']
            campo_data = config['campo_data']
            filtro_op = config['filtro_operacional']
            
            try:
                # Tratamento especial para NFs Complementares (1.01.03)
                # Inclui emitidas + não emitidas (positivas E negativas)
                if codigo == '1.01.03':
                    total = cls._calcular_nf_complementares_total(data_inicio, data_fim)
                    if total != 0:
                        valores[codigo] = total
                    continue
                
                query = Model.query.filter(
                    Model.ativo == True,
                    Model.deletado == False,
                    getattr(Model, campo_data).isnot(None),
                    getattr(Model, filtro_op).isnot(None),  # Exclui lançamentos avulsos
                    getattr(Model, campo_valor) > 0          # Exclui registros sem preço configurado
                )
                
                if data_inicio:
                    query = query.filter(getattr(Model, campo_data) >= data_inicio)
                if data_fim:
                    query = query.filter(getattr(Model, campo_data) <= data_fim)
                
                registros = query.all()
                total = sum(getattr(r, campo_valor) or 0 for r in registros)
                
                if total > 0:
                    valores[codigo] = total
                    
            except Exception as e:
                print(f"[DRE] Erro ao buscar {codigo}: {e}")
        
        return valores
    
    @classmethod
    def _calcular_nf_complementares_total(cls, data_inicio, data_fim):
        """
        Calcula o valor total de NFs Complementares título a título.
        
        Usa SEMPRE os registros operacionais individuais (re_registro_operacional),
        independente do status de emissão da NF Complementar.
        
        Fórmula por registro: (peso_liquido_ticket - peso_ton_nf) * preco_un_nf
        
        Isso garante que o valor entre na DRE pela data_entrega_ticket (competência),
        e não pela data de emissão da NF Complementar (que pode ser em outro mês).
        
        Returns:
            int: valor total em centavos (pode ser positivo ou negativo)
        """
        from sistema import db
        
        total = 0
        
        try:
            # Buscar TODOS os registros operacionais com diferença de peso,
            # independente do status de emissão da NF Complementar.
            # Usa data_entrega_ticket como data de competência.
            query = RegistroOperacionalModel.query.filter(
                RegistroOperacionalModel.ativo == True,
                RegistroOperacionalModel.deletado == False,
                RegistroOperacionalModel.solicitacao_nf_id.isnot(None),
                RegistroOperacionalModel.peso_ton_nf.isnot(None),
                RegistroOperacionalModel.peso_liquido_ticket.isnot(None),
                RegistroOperacionalModel.preco_un_nf > 0,
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                # Todas as diferenças de peso (positivas e negativas)
                RegistroOperacionalModel.peso_liquido_ticket != RegistroOperacionalModel.peso_ton_nf
            )
            
            if data_inicio:
                query = query.filter(
                    RegistroOperacionalModel.data_entrega_ticket >= data_inicio
                )
            if data_fim:
                query = query.filter(
                    RegistroOperacionalModel.data_entrega_ticket <= data_fim
                )
            
            registros = query.all()
            for r in registros:
                diferenca = (r.peso_liquido_ticket or 0) - (r.peso_ton_nf or 0)
                valor = round(diferenca * (r.preco_un_nf or 0))
                total += valor
            
        except Exception as e:
            print(f"[DRE] Erro ao calcular NF Complementares: {e}")
        
        return total
    
    @classmethod
    def _organizar_estrutura_dre(cls, valores):
        """
        Organiza valores na estrutura hierárquica do DRE.
        """
        dre = {
            'receitas': {
                'total': 0,
                'operacionais': {'total': 0, 'itens': []},
                'nao_operacionais': {'total': 0, 'itens': []}
            },
            'custos': {
                'total': 0,
                'operacionais': {'total': 0, 'itens': []}
            },
            'despesas': {
                'total': 0,
                'operacionais': {'total': 0, 'itens': []}
            }
        }
        
        for cat_id, info in valores.items():
            codigo = info['codigo']
            valor = info['valor']
            
            # Ignorar categorias específicas
            if any(codigo.startswith(ign) for ign in cls.CODIGOS_IGNORADOS):
                continue
            
            # Ignorar valores zerados
            if valor == 0:
                continue
            
            item = {
                'categoria_id': cat_id,
                'codigo': codigo,
                'nome': info['nome'],
                'valor': valor,
                'hierarquia_completa': info['hierarquia']
            }
            
            # Classificar por tipo
            tipo = cls._identificar_tipo_dre(codigo)
            
            if tipo == 'receitas_operacionais':
                dre['receitas']['operacionais']['itens'].append(item)
                dre['receitas']['operacionais']['total'] += valor
            elif tipo == 'receitas_nao_operacionais':
                dre['receitas']['nao_operacionais']['itens'].append(item)
                dre['receitas']['nao_operacionais']['total'] += valor
            elif tipo == 'custos_operacionais':
                dre['custos']['operacionais']['itens'].append(item)
                dre['custos']['operacionais']['total'] += valor
            else:  # despesas_operacionais
                dre['despesas']['operacionais']['itens'].append(item)
                dre['despesas']['operacionais']['total'] += valor
        
        return dre
    
    @classmethod
    def _calcular_resultados(cls, dre):
        """
        Calcula totais e resultados do DRE.
        """
        # Totais por seção
        dre['receitas']['total'] = (
            dre['receitas']['operacionais']['total'] + 
            dre['receitas']['nao_operacionais']['total']
        )
        dre['custos']['total'] = dre['custos']['operacionais']['total']
        dre['despesas']['total'] = dre['despesas']['operacionais']['total']
        
        # Resultados
        dre['resultado'] = {
            # Margem de Contribuição = Receitas Operacionais - Custos Operacionais
            'margem_contribuicao': dre['receitas']['operacionais']['total'] - dre['custos']['operacionais']['total'],
            
            # Resultado Bruto = Total Receitas - Total Custos
            'bruto': dre['receitas']['total'] - dre['custos']['total'],
            
            # Resultado Operacional = Margem de Contribuição - Despesas Operacionais
            'operacional': 0,
            
            # Resultado Líquido (por ora igual ao operacional)
            'liquido': 0
        }
        
        dre['resultado']['operacional'] = dre['resultado']['margem_contribuicao'] - dre['despesas']['operacionais']['total']
        dre['resultado']['liquido'] = dre['resultado']['operacional']
        
        # Percentual da margem
        if dre['receitas']['operacionais']['total'] != 0:
            dre['resultado']['margem_contribuicao_percentual'] = (
                dre['resultado']['margem_contribuicao'] / dre['receitas']['operacionais']['total']
            ) * 100
        else:
            dre['resultado']['margem_contribuicao_percentual'] = 0
    
    @classmethod
    def _identificar_tipo_dre(cls, codigo):
        """
        Identifica o tipo DRE baseado no código da categoria.
        """
        if not codigo:
            return 'outros'
        
        # Códigos 3.xx = Transferências (ignorar)
        if codigo.startswith('3.'):
            return 'outros'
        
        # Verificar mapeamento direto
        for prefixo, tipo in cls.TIPO_DRE_MAP.items():
            if codigo.startswith(prefixo):
                return tipo
        
        # Padrão: 2.xx que não é 2.01 = despesas
        if codigo.startswith('2.'):
            return 'despesas_operacionais'
        
        # 1.xx que não está mapeado = receitas não-operacionais
        if codigo.startswith('1.'):
            return 'receitas_nao_operacionais'
        
        return 'outros'
    
    @classmethod
    def _obter_hierarquia(cls, categoria):
        """
        Obtém caminho hierárquico da categoria.
        """
        partes = []
        cat = categoria
        
        while cat:
            partes.insert(0, cat.nome)
            if cat.parent_id:
                cat = PlanoContaModel.query.get(cat.parent_id)
            else:
                cat = None
        
        return ' > '.join(partes)
    
    # ==================== COMPATIBILIDADE ====================
    # Métodos para manter compatibilidade com código existente
    
    @classmethod
    def gerar_dre_analitico(cls, data_inicio, data_fim):
        """Alias para gerar_dre() - mantém compatibilidade."""
        dre = cls.gerar_dre(data_inicio, data_fim)
        
        # Converter estrutura para formato esperado pelo template atual
        return {
            'periodo': dre['periodo'],
            'receitas': {
                'total': dre['receitas']['total'],
                'operacionais': {
                    'total': dre['receitas']['operacionais']['total'],
                    'detalhes': dre['receitas']['operacionais']['itens']
                },
                'nao_operacionais': {
                    'total': dre['receitas']['nao_operacionais']['total'],
                    'detalhes': dre['receitas']['nao_operacionais']['itens']
                }
            },
            'custos': {
                'total': dre['custos']['total'],
                'operacionais': {
                    'total': dre['custos']['operacionais']['total'],
                    'detalhes': dre['custos']['operacionais']['itens']
                }
            },
            'despesas': {
                'total': dre['despesas']['total'],
                'operacionais': {
                    'total': dre['despesas']['operacionais']['total'],
                    'detalhes': dre['despesas']['operacionais']['itens']
                }
            },
            'resultado': dre['resultado']
        }
    
    @classmethod
    def calcular_valores_por_categoria(cls, data_inicio=None, data_fim=None, categoria_ids=None):
        """Método de compatibilidade - retorna valores no formato antigo."""
        valores = cls._calcular_valores_por_categoria(data_inicio, data_fim)
        
        # Converter para formato {categoria_id: valor}
        resultado = {}
        for cat_id, info in valores.items():
            if categoria_ids is None or cat_id in categoria_ids:
                resultado[cat_id] = info['valor']
        
        return resultado
