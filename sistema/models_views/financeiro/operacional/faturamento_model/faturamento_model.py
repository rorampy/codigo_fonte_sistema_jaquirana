from ....base_model import BaseModel, db
from sqlalchemy import desc
import json
from sistema.models_views.financeiro.operacional.categorizar_fatura.categorizacao_model import AgendamentoPagamentoModel

# === Nova Arquitetura de Créditos ===
# ServicoCreditos abstrai o acesso aos dados de crédito para compatibilidade
# from sistema.models_views.faturamento.controle_credito.servico_creditos import ServicoCreditos

# Imports para modelos de entidades
from sistema.models_views.gerenciar.fornecedor.fornecedor_model import FornecedorModel
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema.models_views.gerenciar.extrator.extrator_model import ExtratorModel
from sistema.models_views.gerenciar.comissionado.comissionado_model import ComissionadoModel

class FaturamentoModel(BaseModel):
    __tablename__ = 'fin_faturamento'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    tipo_operacao = db.Column(db.Integer, nullable=False)  # 1-Carga, 2-Lancamento, 3-Credito
    direcao_financeira = db.Column(db.Integer, nullable=False)  # 1-Receber, 2-Despesa
    
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    usuario = db.relationship('UsuarioModel', backref=db.backref('faturamentos', lazy=True))
    codigo_faturamento = db.Column(db.String(20), nullable=False)
    valor_total = db.Column(db.Integer, nullable=False)
    valor_bruto_total = db.Column(db.Integer, nullable=True)  # Valor antes do crédito
    valor_credito_aplicado = db.Column(db.Integer, nullable=True) 
    valor_fornecedor = db.Column(db.Integer, nullable=True)  # Valor total dos fornecedores
    valor_transportadora = db.Column(db.Integer, nullable=True)  # Valor total das transportadoras
    valor_extrator = db.Column(db.Integer, nullable=True)  # Valor total dos extratores
    valor_comissionado = db.Column(db.Integer, nullable=True)  # Valor total dos comissionados
    valor_receita = db.Column(db.Integer, nullable=True)  # Valor total das receitas
    valor_despesa = db.Column(db.Integer, nullable=True)  # Valor total das despesas
    utilizou_credito = db.Column(db.Boolean, default=False, nullable=True)
    ids_fornecedores= db.Column(db.Text, nullable=True)  # ids dos fornecedores, separados por vírgula
    ids_fretes = db.Column(db.Text, nullable=True)      # ids dos fretes, separados por vírgula
    ids_extratores = db.Column(db.Text, nullable=True)      # ids dos extratores, separados por vírgula
    ids_comissionados = db.Column(db.Text, nullable=True)      # ids dos comissionados, separados por vírgula
    ids_a_receber = db.Column(db.Text, nullable=True)      # ids dos a receber, separados por vírgula
    ids_nf_complementar = db.Column(db.Text, nullable=True)      # ids dos a NF complementar, separados por vírgula
    ids_nf_servico = db.Column(db.Text, nullable=True)      # ids dos a NF serviço, separados por vírgula

    lancamento_avulso_id = db.Column(db.Integer, db.ForeignKey("lan_lancamento_avulso.id"), nullable=True)
    lancamento_avulso = db.relationship("LancamentoAvulsoModel", backref=db.backref("lancamento", lazy=True))

    detalhes_json = db.Column(db.JSON, nullable=True)     # detalhes dos registros (JSON)
    situacao_pagamento_id = db.Column(db.Integer, db.ForeignKey("fin_situacao_pagamento.id"), nullable=True)
    situacao = db.relationship("SituacaoPagamentoModel", backref=db.backref("faturamento_status", lazy=True))
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    

    def __init__(self, usuario_id, valor_total, codigo_faturamento, tipo_operacao=None, direcao_financeira=None, ids_fornecedores=None, valor_bruto_total=None, valor_credito_aplicado=None, valor_fornecedor=None, valor_transportadora=None, 
                 valor_extrator=None, valor_comissionado=None, valor_receita=None, valor_despesa=None, utilizou_credito=False, ids_fretes=None, ids_extratores=None, ids_comissionados=None, 
                 lancamento_avulso_id=None, detalhes_json=None, situacao_pagamento_id=None, ativo=True, ids_a_receber=None, ids_nf_complementar=None, ids_nf_servico=None):
        self.usuario_id = usuario_id
        self.valor_total = valor_total
        self.valor_bruto_total = valor_bruto_total
        self.valor_credito_aplicado = valor_credito_aplicado
        self.valor_fornecedor = valor_fornecedor
        self.valor_transportadora = valor_transportadora
        self.valor_extrator = valor_extrator
        self.valor_comissionado = valor_comissionado
        self.valor_receita = valor_receita
        self.valor_despesa = valor_despesa
        self.utilizou_credito = utilizou_credito
        self.ids_fornecedores = ids_fornecedores
        self.ids_a_receber = ids_a_receber
        self.ids_nf_complementar = ids_nf_complementar
        self.ids_nf_servico = ids_nf_servico
        self.codigo_faturamento = codigo_faturamento
        self.ids_fretes = ids_fretes
        self.ids_extratores = ids_extratores
        self.ids_comissionados = ids_comissionados
        self.tipo_operacao = tipo_operacao
        self.direcao_financeira = direcao_financeira
        self.lancamento_avulso_id = lancamento_avulso_id
        self.detalhes_json = detalhes_json
        self.situacao_pagamento_id = situacao_pagamento_id
        self.ativo = ativo


    def gerar_codigo_novo_faturamento():
        ultimo_cor = (
            FaturamentoModel.query.filter(FaturamentoModel.deletado == 0, FaturamentoModel.ativo == True)
            .order_by(desc(FaturamentoModel.id))
            .first()
        )

        if not ultimo_cor:
            codigo = "FAT-000001"
        else:
            id = str(ultimo_cor.id + 1)

            while len(id) < 6:
                id = "0" + id

            codigo = "FAT-" + id

        return codigo
    
    def obter_lancamento_despesa_id(id):
        """
        Obtém o ID do lançamento avulso associado a uma despesa específica.
        """
        faturamento = FaturamentoModel.query.filter_by(lancamento_avulso_id=id, tipo_operacao=2, direcao_financeira=2, deletado=False, ativo=True).first()
        return faturamento
    
    def obter_lancamento_receita_id(id):
        """
        Obtém o ID do lançamento avulso associado a uma receita específica.
        """
        faturamento = FaturamentoModel.query.filter_by(lancamento_avulso_id=id, tipo_operacao=2, direcao_financeira=1, deletado=False, ativo=True).first()
        return faturamento

    def obter_faturamento_por_id(id):
        """
        Obtém um faturamento pelo seu ID.
        """
        return FaturamentoModel.query.filter_by(id=id, deletado=0, ativo=True).first()

    def salvar_detalhes(self, fornecedores=[], transportadoras=[], extratores=[], comissionados=[], 
                        cargas_a_receber=[], credito_fornecedor=[], credito_transportadora=[], credito_extrator=[],
                        nf_complementar=[], nf_servico=[]):
        """
        Salva os detalhes dos fornecedores, transportadoras e extratores no campo detalhes_json.
        fornecedores: lista de dicts
        transportadoras: lista de dicts
        extratores: lista de dicts
        comissionados: lista de dicts
        cargas_a_receber: lista de dicts
        credito_fornecedor: lista de dicts
        credito_transportadora: lista of dicts
        credito_extrator: lista of dicts
        nf_complementar: lista of dicts
        ids_nf_servico: lista of dicts
         Cada dict deve conter as informações relevantes para cada entidade.
        """
        detalhes = {}
        
        if fornecedores:
            detalhes["fornecedores"] = fornecedores
        
        if transportadoras:
            detalhes["transportadoras"] = transportadoras
        
        if extratores:
            detalhes["extratores"] = extratores
        
        if comissionados:
            detalhes["comissionados"] = comissionados
        
        if cargas_a_receber:
            detalhes["cargas_a_receber"] = cargas_a_receber
            
        if credito_fornecedor:
            detalhes["credito_fornecedor"] = credito_fornecedor
            
        if credito_transportadora:
            detalhes["credito_transportadora"] = credito_transportadora
            
        if credito_extrator:
            detalhes["credito_extrator"] = credito_extrator
        if nf_complementar:
            detalhes["nf_complementar"] = nf_complementar
        if nf_servico:
            detalhes["nf_servico"] = nf_servico
        
        # Como o campo é db.JSON, salvamos diretamente o dict (não fazemos json.dumps)
        self.detalhes_json = detalhes

    def obter_detalhes(self):
        """
        Retorna um dicionário com os detalhes dos fornecedores, transportadoras e extratores.
        """
        default_detalhes = {"fornecedores": [], "transportadoras": [], "extratores": [], "comissionados": [], "cargas_a_receber": [],
                           "credito_fornecedor": [], "credito_transportadora": [], "credito_extrator": [], "nf_complementar": [], "nf_servico": []}
        
        if not self.detalhes_json:
            return default_detalhes
            
        try:
            # Se for string, tentar fazer parse
            if isinstance(self.detalhes_json, str):
                detalhes = json.loads(self.detalhes_json)
            else:
                # Se já for dict/objeto, usar diretamente
                detalhes = self.detalhes_json
                
            # Garantir que todas as chaves necessárias existam
            for chave in default_detalhes.keys():
                if chave not in detalhes:
                    detalhes[chave] = []
                    
            return detalhes
        except Exception as e:
            print(f"Erro ao processar detalhes_json do faturamento {self.id}: {e}")
            return default_detalhes
            
    def obter_lista_fornecedores(self):
        """Retorna lista de fornecedores do faturamento."""
        return self.obter_detalhes().get("fornecedores", [])

    def obter_lista_transportadoras(self):
        """Retorna lista de transportadoras do faturamento."""
        return self.obter_detalhes().get("transportadoras", [])

    def obter_lista_extratores(self):
        """Retorna lista de extratores do faturamento."""
        return self.obter_detalhes().get("extratores", [])
    
    def obter_lista_comissionados(self):
        """Retorna lista de comissionados do faturamento."""
        return self.obter_detalhes().get("comissionados", [])
    
    def obter_lista_cargas_a_receber(self):
        """Retorna lista de cargas a receber do faturamento."""
        return self.obter_detalhes().get("cargas_a_receber", [])

    def obter_lista_credito_fornecedor(self):
        """Retorna lista de crédito de fornecedor do faturamento."""
        return self.obter_detalhes().get("credito_fornecedor", [])

    def obter_lista_credito_transportadora(self):
        """Retorna lista de crédito de transportadora do faturamento."""
        return self.obter_detalhes().get("credito_transportadora", [])
    
    def obter_lista_credito_extrator(self):
        """Retorna lista de crédito de extrator do faturamento."""
        return self.obter_detalhes().get("credito_extrator", [])
    
    def obter_lista_nf_complementar(self):
        """Retorna lista de NF complementar do faturamento."""
        return self.obter_detalhes().get("nf_complementar", [])

    def obter_lista_nf_servico(self):
        """Retorna lista de NF serviço do faturamento."""
        return self.obter_detalhes().get("nf_servico", [])

    def obter_faturamentos_cargas_a_pagar():
        faturamentos = FaturamentoModel.query.filter(
            FaturamentoModel.deletado == False,
            FaturamentoModel.ativo == True,
            FaturamentoModel.tipo_operacao == 1,
            FaturamentoModel.direcao_financeira == 2
        ).order_by(desc(FaturamentoModel.data_cadastro)).all()
        
        return faturamentos

    def obter_faturamentos_cargas_a_receber():
        faturamentos = FaturamentoModel.query.filter(
            FaturamentoModel.deletado == False,
            FaturamentoModel.ativo == True,
           FaturamentoModel.tipo_operacao == 1,
           FaturamentoModel.direcao_financeira == 1
        ).order_by(desc(FaturamentoModel.data_cadastro)).all()
        
        return faturamentos

    def obter_faturamentos_lancamentos_receitas_avulsas():
        faturamentos = FaturamentoModel.query.filter(
            FaturamentoModel.deletado == False,
            FaturamentoModel.ativo == True,
            FaturamentoModel.tipo_operacao == 2,
            FaturamentoModel.direcao_financeira == 1
        ).order_by(desc(FaturamentoModel.data_cadastro)).all()
        
        return faturamentos
    
    def obter_faturamentos_lancamentos_despesas_avulsas():
        faturamentos = FaturamentoModel.query.filter(
            FaturamentoModel.deletado == False,
            FaturamentoModel.ativo == True,
            FaturamentoModel.tipo_operacao == 2,
            FaturamentoModel.direcao_financeira == 2
        ).order_by(desc(FaturamentoModel.data_cadastro)).all()
        
        return faturamentos
    
    def obter_faturamentos_controle_creditos():
        faturamentos = FaturamentoModel.query.filter(
            FaturamentoModel.deletado == False,
            FaturamentoModel.ativo == True,
            FaturamentoModel.tipo_operacao == 3,
            FaturamentoModel.direcao_financeira == 2
        ).order_by(desc(FaturamentoModel.data_cadastro)).all()
        
        return faturamentos

    def obter_faturamentos_nf_complementar():
        faturamentos = FaturamentoModel.query.filter(
            FaturamentoModel.deletado == False,
            FaturamentoModel.ativo == True,
            FaturamentoModel.tipo_operacao == 1,
            FaturamentoModel.direcao_financeira == 1
        ).order_by(desc(FaturamentoModel.data_cadastro)).all()

        return faturamentos

    def obter_faturamentos_nf_servico():
        faturamentos = FaturamentoModel.query.filter(
            FaturamentoModel.deletado == False,
            FaturamentoModel.ativo == True,
            FaturamentoModel.tipo_operacao == 1,
            FaturamentoModel.direcao_financeira == 1
        ).order_by(desc(FaturamentoModel.data_cadastro)).all()

        return faturamentos

    @staticmethod
    def filtrar_a_pagar_faturamentos(beneficiario=None, situacao_id=None):
        """
        Filtra faturamentos com base na identificação do beneficiário e na situação.
        
        Args:
            beneficiario (int, optional): ID do beneficiário.
            situacao_id (int, optional): ID da situação do faturamento. Se None, não filtra por situação.

        Returns:
            list: Lista de objetos FaturamentoModel que atendem aos critérios de filtro.
        """
        # Caso especial: Não Categorizado (situacao_id = 7) com filtro de beneficiário
        # Nesse caso, não há AgendamentoPagamentoModel, então devemos buscar nos detalhes do faturamento
        if beneficiario and situacao_id == 7:
            from sistema.models_views.gerenciar.pessoa_financeiro.pessoa_financeiro_model import PessoaFinanceiroModel
            
            # Buscar a pessoa e seus vínculos
            pessoa = PessoaFinanceiroModel.obter_pessoa_por_id(beneficiario)
            if not pessoa or not pessoa.vinculos_operacionais:
                # Se não tem vínculos, retornar vazio
                return []
            
            # Extrair IDs dos vínculos operacionais
            vinculos = pessoa.vinculos_operacionais
            ids_vinculados = {
                'fornecedor': vinculos.get('fornecedor', []) if vinculos else [],
                'transportadora': vinculos.get('transportadora', []) if vinculos else [],
                'extrator': vinculos.get('extrator', []) if vinculos else [],
                'comissionado': vinculos.get('comissionado', []) if vinculos else []
            }
            
            # Buscar todos os faturamentos não categorizados
            faturamentos = FaturamentoModel.query.filter(
                FaturamentoModel.ativo == True,
                FaturamentoModel.deletado == False,
                FaturamentoModel.tipo_operacao == 1,
                FaturamentoModel.direcao_financeira == 2,
                FaturamentoModel.situacao_pagamento_id == 7
            ).order_by(desc(FaturamentoModel.data_cadastro)).all()
            
            # Filtrar em Python os que contêm os IDs vinculados nos detalhes
            faturamentos_filtrados = []
            for fat in faturamentos:
                detalhes = fat.obter_detalhes()
                
                # Verificar se algum fornecedor está vinculado
                for fornecedor in detalhes.get('fornecedores', []):
                    if fornecedor.get('fornecedor_id') in ids_vinculados['fornecedor']:
                        faturamentos_filtrados.append(fat)
                        break
                else:
                    # Verificar transportadoras
                    for transportadora in detalhes.get('transportadoras', []):
                        if transportadora.get('transportadora_id') in ids_vinculados['transportadora']:
                            faturamentos_filtrados.append(fat)
                            break
                    else:
                        # Verificar extratores
                        for extrator in detalhes.get('extratores', []):
                            if extrator.get('extrator_id') in ids_vinculados['extrator']:
                                faturamentos_filtrados.append(fat)
                                break
                        else:
                            # Verificar comissionados
                            for comissionado in detalhes.get('comissionados', []):
                                if comissionado.get('comissionado_id') in ids_vinculados['comissionado']:
                                    faturamentos_filtrados.append(fat)
                                    break
            
            return faturamentos_filtrados
        
        # Lógica normal para outros casos
        query = FaturamentoModel.query

        if beneficiario:
            # Usar outerjoin para incluir faturamentos sem categorização quando não há filtro específico
            query = query.outerjoin(AgendamentoPagamentoModel).filter(
                AgendamentoPagamentoModel.pessoa_financeiro_id == beneficiario
            )

        if situacao_id is not None:
            query = query.filter(FaturamentoModel.situacao_pagamento_id == situacao_id)

        return query.filter(
            FaturamentoModel.ativo == True,
            FaturamentoModel.deletado == False,
            FaturamentoModel.tipo_operacao == 1,
            FaturamentoModel.direcao_financeira == 2
        ).order_by(desc(FaturamentoModel.data_cadastro)).all()
        
    @staticmethod
    def filtrar_creditos_faturamentos(beneficiario=None, situacao_id=None):
        """
        Filtra faturamentos com base na identificação do beneficiário e na situação.
        
        Args:
            beneficiario (int, optional): ID do beneficiário.
            situacao_id (int, optional): ID da situação do faturamento. Se None, não filtra por situação.

        Returns:
            list: Lista de objetos FaturamentoModel que atendem aos critérios de filtro.
        """
        query = FaturamentoModel.query

        if beneficiario:
            query = query.join(AgendamentoPagamentoModel).filter(
                AgendamentoPagamentoModel.pessoa_financeiro_id == beneficiario
            )

        if situacao_id is not None:
            query = query.filter(FaturamentoModel.situacao_pagamento_id == situacao_id)

        return query.filter(
            FaturamentoModel.ativo == True,
            FaturamentoModel.deletado == False,
            FaturamentoModel.tipo_operacao == 3,
            FaturamentoModel.direcao_financeira == 2
        ).order_by(desc(FaturamentoModel.data_cadastro)).all()
    
    @staticmethod
    def filtrar_a_receber_faturamentos(beneficiario=None, situacao_id=None):
        """
        Filtra faturamentos com base na identificação do beneficiário e na situação.
        
        Args:
            beneficiario (int, optional): ID do beneficiário.
            situacao_id (int, optional): ID da situação do faturamento. Se None, não filtra por situação.

        Returns:
            list: Lista de objetos FaturamentoModel que atendem aos critérios de filtro.
        """
        query = FaturamentoModel.query

        if beneficiario:
            query = query.join(AgendamentoPagamentoModel).filter(
                AgendamentoPagamentoModel.pessoa_financeiro_id == beneficiario
            )

        if situacao_id is not None:
            query = query.filter(FaturamentoModel.situacao_pagamento_id == situacao_id)

        return query.filter(
            FaturamentoModel.ativo == True,
            FaturamentoModel.deletado == False,
            FaturamentoModel.tipo_operacao == 1,
           FaturamentoModel.direcao_financeira == 1
        ).order_by(desc(FaturamentoModel.data_cadastro)).all()
        
    @staticmethod
    def filtrar_a_receber_conciliados(beneficiario=None):
        """
        Filtra faturamentos com base na identificação do beneficiário e na situação.
        
        Args:
            beneficiario (int, optional): ID do beneficiário.
            situacao_id (int, optional): ID da situação do faturamento. Se None, não filtra por situação.

        Returns:
            list: Lista de objetos FaturamentoModel que atendem aos critérios de filtro.
        """
        query = FaturamentoModel.query

        if beneficiario:
            query = query.join(AgendamentoPagamentoModel).filter(
                AgendamentoPagamentoModel.pessoa_financeiro_id == beneficiario
            )

        return query.filter(
            FaturamentoModel.ativo == True,
            FaturamentoModel.deletado == False,
            FaturamentoModel.direcao_financeira == 1,
            FaturamentoModel.situacao_pagamento_id == 6,
        ).order_by(desc(FaturamentoModel.data_cadastro)).all()
        

    def agrupar_fornecedores_pdf(fornecedores):
        """Agrupa fornecedores para PDF"""
        from collections import defaultdict
        grupos = defaultdict(lambda: {'registros': [], 'total': 0.0})
        
        for fornecedor in fornecedores:
            nome = fornecedor.get('fornecedor_identificacao', 'Não informado')
            valor_str = fornecedor.get('valor_faturado', 'R$ 0,00')
            valor = valor_str
            
            grupos[nome]['registros'].append({
                **fornecedor,
                'valor_faturado_num': valor
            })
            grupos[nome]['total'] += valor
        
        return dict(grupos)

    def agrupar_transportadoras_pdf(transportadoras):
        """Agrupa transportadoras para PDF"""
        from collections import defaultdict
        grupos = defaultdict(lambda: {'registros': [], 'total': 0.0})
        
        for transportadora in transportadoras:
            nome = transportadora.get('nome', 'Não informado') if transportadora.get('nome') else transportadora.get('transportadora_identificacao', 'Não informado')
            valor_str = transportadora.get('valor_faturado', 'R$ 0,00')
            valor = valor_str
            
            grupos[nome]['registros'].append({
                **transportadora,
                'valor_faturado_num': valor
            })
            grupos[nome]['total'] += valor
        
        return dict(grupos)

    def agrupar_extratores_pdf(extratores):
        """Agrupa extratores para PDF"""
        from collections import defaultdict
        grupos = defaultdict(lambda: {'registros': [], 'total': 0.0})

        for extrator in extratores:
            # Tenta pegar o nome do extrator pelos diferentes campos possíveis
            nome = extrator.get('extrator_identificacao') or extrator.get('identificacao') or extrator.get('nome', 'Não informado')
            valor_str = extrator.get('valor_faturado', 'R$ 0,00')
            valor = valor_str
            
            grupos[nome]['registros'].append({
                **extrator,
                'valor_faturado_num': valor
            })
            grupos[nome]['total'] += valor
        
        return dict(grupos)

    def agrupar_comissionados_pdf(comissionados):
        """Agrupa comissionados para PDF"""
        from collections import defaultdict
        grupos = defaultdict(lambda: {'registros': [], 'total': 0.0})

        for comissionado in comissionados:
            # Tenta pegar o nome do comissionado pelos diferentes campos possíveis
            nome = comissionado.get('comissionado_identificacao') or comissionado.get('identificacao') or comissionado.get('nome', 'Não informado')
            valor_str = comissionado.get('valor_faturado', 'R$ 0,00')
            valor = valor_str
            
            grupos[nome]['registros'].append({
                **comissionado,
                'valor_faturado_num': valor
            })
            grupos[nome]['total'] += valor
        
        return dict(grupos)
    
    def agrupar_dados_por_cliente_produto(detalhes):
        """
        Agrupa todos os dados (fornecedores, transportadoras, extratores, comissionados, cargas_a_receber) 
        por cliente e produto, retornando uma estrutura completa com agrupamentos originais + hierárquico.
        """
        from collections import defaultdict
        
        resultado = {
            # Agrupamentos originais para compatibilidade
            'fornecedores_agrupados': {},
            'transportadoras_agrupadas': {},
            'extratores_agrupados': {},
            'comissionados_agrupados': {},
            'cargas_a_receber_agrupadas': {},
            
            # Estrutura hierárquica por cliente e produto
            'dados_hierarquicos': []
        }
        
        # === AGRUPAMENTOS ORIGINAIS ===
        
        # Agrupar fornecedores
        grupos_fornecedores = defaultdict(lambda: {'registros': [], 'total': 0.0})
        for fornecedor in detalhes.get('fornecedores', []):
            nome = fornecedor.get('fornecedor_identificacao', 'Não informado')
            valor_str = fornecedor.get('valor_faturado', 'R$ 0,00')
            valor = valor_str
            
            grupos_fornecedores[nome]['registros'].append({
                **fornecedor,
                'valor_faturado_num': valor
            })
            grupos_fornecedores[nome]['total'] += valor
        resultado['fornecedores_agrupados'] = dict(grupos_fornecedores)
        
        # Agrupar transportadoras
        grupos_transportadoras = defaultdict(lambda: {'registros': [], 'total': 0.0})
        for transportadora in detalhes.get('transportadoras', []):
            nome = transportadora.get('nome', 'Não informado') if transportadora.get('nome') else transportadora.get('transportadora_identificacao', 'Não informado')
            valor_str = transportadora.get('valor_faturado', 'R$ 0,00')
            valor = valor_str
            
            grupos_transportadoras[nome]['registros'].append({
                **transportadora,
                'valor_faturado_num': valor
            })
            grupos_transportadoras[nome]['total'] += valor
        resultado['transportadoras_agrupadas'] = dict(grupos_transportadoras)
        
        # Agrupar extratores
        grupos_extratores = defaultdict(lambda: {'registros': [], 'total': 0.0})
        for extrator in detalhes.get('extratores', []):
            nome = extrator.get('extrator_identificacao') or extrator.get('identificacao') or extrator.get('nome', 'Não informado')
            valor_str = extrator.get('valor_faturado', 'R$ 0,00')
            valor = valor_str
            
            grupos_extratores[nome]['registros'].append({
                **extrator,
                'valor_faturado_num': valor
            })
            grupos_extratores[nome]['total'] += valor
        resultado['extratores_agrupados'] = dict(grupos_extratores)
        
        # Agrupar comissionados
        grupos_comissionados = defaultdict(lambda: {'registros': [], 'total': 0.0})
        for comissionado in detalhes.get('comissionados', []):
            nome = comissionado.get('comissionado_identificacao') or comissionado.get('identificacao') or comissionado.get('nome', 'Não informado')
            valor_str = comissionado.get('valor_faturado', 'R$ 0,00')
            valor = valor_str
            
            grupos_comissionados[nome]['registros'].append({
                **comissionado,
                'valor_faturado_num': valor
            })
            grupos_comissionados[nome]['total'] += valor
        resultado['comissionados_agrupados'] = dict(grupos_comissionados)
        
        # Agrupar cargas a receber
        grupos_cargas = defaultdict(lambda: {'registros': [], 'total': 0.0})
        for carga in detalhes.get('cargas_a_receber', []):
            nome = carga.get('cliente_identificacao', 'Não informado')
            valor_str = carga.get('valor_faturado', 'R$ 0,00')
            valor = valor_str
            
            grupos_cargas[nome]['registros'].append({
                **carga,
                'valor_faturado_num': valor
            })
            grupos_cargas[nome]['total'] += valor
        resultado['cargas_a_receber_agrupadas'] = dict(grupos_cargas)
        
        # === ESTRUTURA HIERÁRQUICA POR CLIENTE E PRODUTO ===
        
        # Estrutura: clientes[cliente_nome][produto_nome] = {...}
        clientes = defaultdict(lambda: defaultdict(lambda: {
            'registros': {
                'fornecedores': [],
                'transportadoras': [],
                'extratores': [],
                'comissionados': [],
                'cargas_a_receber': []
            },
            'totais': {
                'fornecedores': 0.0,
                'transportadoras': 0.0,
                'extratores': 0.0,
                'comissionados': 0.0,
                'cargas_a_receber': 0.0,
                'total_geral': 0.0
            }
        }))
        
        # Processar cada categoria de dados
        categorias = ['fornecedores', 'transportadoras', 'extratores', 'comissionados', 'cargas_a_receber']
        
        for categoria in categorias:
            registros = detalhes.get(categoria, [])
            
            for registro in registros:
                # Extrair cliente e produto do registro
                cliente_nome = (
                    registro.get('cliente_identificacao') or 
                    registro.get('cliente_nome') or 
                    registro.get('cliente') or 
                    'Cliente não informado'
                )
                
                produto_nome = (
                    registro.get('produto_nome') or 
                    registro.get('produto') or 
                    'Produto não informado'
                )
                
                # Extrair valor do registro
                valor = 0.0
                if 'valor_faturado' in registro:
                    if isinstance(registro['valor_faturado'], (int, float)):
                        valor = float(registro['valor_faturado'])
                    elif isinstance(registro['valor_faturado'], str):
                        # Remover formatação monetária se houver
                        try:
                            valor_str = registro['valor_faturado'].replace('R$', '').replace('.', '').replace(',', '.').strip()
                            valor = float(valor_str) if valor_str else 0.0
                        except:
                            valor = 0.0
                
                # Adicionar registro à estrutura
                clientes[cliente_nome][produto_nome]['registros'][categoria].append({
                    **registro,
                    'valor_faturado_num': valor
                })
                
                # Somar ao total da categoria
                clientes[cliente_nome][produto_nome]['totais'][categoria] += valor
                
                # Somar ao total geral
                clientes[cliente_nome][produto_nome]['totais']['total_geral'] += valor
        
        # Converter estrutura hierárquica para lista
        dados_hierarquicos = []
        
        for cliente_nome, produtos in clientes.items():
            cliente_data = {
                'cliente': cliente_nome,
                'produtos': [],
                'total_cliente': 0.0
            }
            
            for produto_nome, dados_produto in produtos.items():
                produto_data = {
                    'produto': produto_nome,
                    'registros': dados_produto['registros'],
                    'totais': dados_produto['totais']
                }
                cliente_data['produtos'].append(produto_data)
                cliente_data['total_cliente'] += dados_produto['totais']['total_geral']
            
            dados_hierarquicos.append(cliente_data)
        
        # Ordenar clientes por nome
        dados_hierarquicos.sort(key=lambda x: x['cliente'])
        resultado['dados_hierarquicos'] = dados_hierarquicos
        
        return resultado

    def _buscar_creditos_em_aberto(detalhes):
        """
        Busca créditos em aberto das entidades vinculadas ao faturamento.
        Utiliza ServicoCreditos para compatibilidade com a nova arquitetura.
        
        Args:
            detalhes (dict): Dicionário com os detalhes do faturamento
            
        Returns:
            dict: Créditos em aberto organizados por categoria
        """
        from sistema.models_views.financeiro.controle_adiantamentos.servico_creditos import ServicoCreditos
        
        creditos_em_aberto = {
            'fornecedores': [],
            'transportadoras': [],
            'extratores': [],
            'comissionados': []
        }
        
        try:
            # Coletar IDs únicos de todas as entidades do faturamento
            fornecedores_ids = set()
            transportadoras_ids = set()
            extratores_ids = set()
            comissionados_ids = set()
            
            # Extrair IDs dos fornecedores
            for fornecedor in detalhes.get('fornecedores', []):
                fornecedor_id = fornecedor.get('fornecedor_id')
                if fornecedor_id:
                    fornecedores_ids.add(fornecedor_id)
            
            # Extrair IDs das transportadoras
            for transportadora in detalhes.get('transportadoras', []):
                transportadora_id = transportadora.get('transportadora_id')
                if transportadora_id:
                    transportadoras_ids.add(transportadora_id)
            
            # Extrair IDs dos extratores
            for extrator in detalhes.get('extratores', []):
                extrator_id = extrator.get('extrator_id')
                if extrator_id:
                    extratores_ids.add(extrator_id)
                    
            # Extrair IDs dos comissionados
            for comissionado in detalhes.get('comissionados', []):
                comissionado_id = comissionado.get('comissionado_id')
                if comissionado_id:
                    comissionados_ids.add(comissionado_id)
            
            # Buscar créditos em aberto dos fornecedores via ServicoCreditos
            for fornecedor_id in fornecedores_ids:
                creditos = ServicoCreditos.obter_creditos_disponiveis_fornecedor(fornecedor_id)
                if creditos:
                    fornecedor = FornecedorModel.query.get(fornecedor_id)
                    if fornecedor:
                        for credito in creditos:
                            creditos_em_aberto['fornecedores'].append({
                                'identificacao': fornecedor.identificacao,
                                'valor_credito': credito.get('saldo_disponivel_100') or credito.get('valor_credito_100', 0),
                                'data_ultima_movimentacao': credito.get('data_movimentacao', '-'),
                                'descricao': credito.get('descricao') or "Adiantamento em aberto"
                            })
            
            # Buscar créditos em aberto das transportadoras via ServicoCreditos
            for transportadora_id in transportadoras_ids:
                creditos = ServicoCreditos.obter_creditos_disponiveis_transportadora(transportadora_id)
                if creditos:
                    transportadora = TransportadoraModel.query.get(transportadora_id)
                    if transportadora:
                        for credito in creditos:
                            creditos_em_aberto['transportadoras'].append({
                                'identificacao': transportadora.identificacao,
                                'valor_credito': credito.get('saldo_disponivel_100') or credito.get('valor_credito_100', 0),
                                'data_ultima_movimentacao': credito.get('data_movimentacao', '-'),
                                'descricao': credito.get('descricao') or "Adiantamento em aberto"
                            })
            
            # Buscar créditos em aberto dos extratores via ServicoCreditos
            for extrator_id in extratores_ids:
                creditos = ServicoCreditos.obter_creditos_disponiveis_extrator(extrator_id)
                if creditos:
                    extrator = ExtratorModel.query.get(extrator_id)
                    if extrator:
                        for credito in creditos:
                            creditos_em_aberto['extratores'].append({
                                'identificacao': extrator.identificacao,
                                'valor_credito': credito.get('saldo_disponivel_100') or credito.get('valor_credito_100', 0),
                                'data_ultima_movimentacao': credito.get('data_movimentacao', '-'),
                                'descricao': credito.get('descricao') or "Adiantamento em aberto"
                            })
        
        except Exception as e:
            print(f"[ERROR] Erro ao buscar créditos em aberto: {e}")
            import traceback
            traceback.print_exc()
        
        return creditos_em_aberto
    
    def buscar_faturamento_origem_por_extrato(extrato_credito_id, tipo_credito):
        """
        Busca o código do faturamento origem baseado no ID do extrato de crédito.
        Busca nos detalhes JSON de todos os faturamentos.
        
        Args:
            extrato_credito_id (int): ID do extrato de crédito (pode ser legado ou TransacaoCreditoModel)
            tipo_credito (str): Tipo do crédito ('fornecedor', 'freteiro', 'extrator', 'transportadora')
        
        Returns:
            str: Código do faturamento origem ou 'N/A'
        """
        try:
            if not extrato_credito_id:
                return "N/A"

            # Mapear tipo de crédito para o campo no JSON (formato legado)
            campo_extrato_legado = {
                'fornecedor': 'extrato_credito_fornecedor_id',
                'transportadora': 'extrato_credito_transportadora_id', 
                'freteiro': 'extrato_credito_transportadora_id',
                'extrator': 'extrato_credito_extrator_id'
            }
            
            campo_credito = {
                'fornecedor': 'credito_fornecedor',
                'transportadora': 'credito_transportadora',
                'freteiro': 'credito_transportadora',
                'extrator': 'credito_extrator'
            }
            
            if tipo_credito not in campo_credito:
                return "N/A"
                
            # Buscar em todos os faturamentos ativos
            faturamentos = FaturamentoModel.query.filter_by(ativo=True, deletado=False).all()
            
            for faturamento in faturamentos:
                if not faturamento.detalhes_json:
                    continue
                    
                try:
                    # Processar detalhes JSON
                    if isinstance(faturamento.detalhes_json, dict):
                        detalhes = faturamento.detalhes_json
                    else:
                        detalhes = json.loads(faturamento.detalhes_json)
                    
                    # Buscar no array de créditos do tipo correspondente
                    creditos = detalhes.get(campo_credito[tipo_credito], [])
                    
                    for credito in creditos:
                        # Verificar formato novo (credito_id)
                        if credito.get('credito_id') == extrato_credito_id:
                            return faturamento.codigo_faturamento
                        
                        # Verificar formato legado (extrato_credito_X_id)
                        if tipo_credito in campo_extrato_legado:
                            if credito.get(campo_extrato_legado[tipo_credito]) == extrato_credito_id:
                                return faturamento.codigo_faturamento
                            
                except (json.JSONDecodeError, TypeError):
                    continue
            
            # Se não encontrou nos detalhes JSON, tentar buscar pelo TransacaoCreditoModel
            try:
                from sistema.models_views.financeiro.controle_adiantamentos.transacao_credito_model import TransacaoCreditoModel
                transacao = TransacaoCreditoModel.query.get(extrato_credito_id)
                if transacao and transacao.faturamento_origem_id:
                    fat_origem = FaturamentoModel.query.get(transacao.faturamento_origem_id)
                    if fat_origem:
                        return fat_origem.codigo_faturamento
            except Exception:
                pass
                    
            return "N/A"
        except Exception as e:
            return "N/A"
        
    def buscar_faturamento_origem_por_carga_pagar_id(carga_pagar_id, tipo_entidade):
        """
        Busca o código do faturamento origem baseado no ID da carga a pagar.
        Busca nos detalhes JSON de todos os faturamentos.
        
        Args:
            carga_pagar_id (int): ID da carga a pagar (fornecedor_a_pagar_id, frete_a_pagar_id, etc.)
            tipo_entidade (str): Tipo da entidade ('fornecedor', 'transportadora', 'comissionado', 'extrator')
        
        Returns:
            str: Código do faturamento origem ou 'N/A'
        """
        try:
            if not carga_pagar_id:
                return "N/A"

            # Mapear tipo de entidade para o campo ID no JSON
            campo_id = {
                'fornecedor': 'fornecedor_a_pagar_id',
                'transportadora': 'frete_a_pagar_id', 
                'comissionado': 'comissionado_a_pagar_id',
                'extrator': 'extrator_a_pagar_id'
            }
            
            # Mapear tipo de entidade para o campo da categoria no JSON
            campo_categoria = {
                'fornecedor': 'fornecedores',
                'transportadora': 'transportadoras',
                'comissionado': 'comissionados', 
                'extrator': 'extratores'
            }
            
            if tipo_entidade not in campo_id:
                return "N/A"
                
            # Buscar em todos os faturamentos ativos
            faturamentos = FaturamentoModel.query.filter_by(ativo=True, deletado=False).all()
            
            for faturamento in faturamentos:
                if not faturamento.detalhes_json:
                    continue
                    
                try:
                    # Processar detalhes JSON
                    if isinstance(faturamento.detalhes_json, dict):
                        detalhes = faturamento.detalhes_json
                    else:
                        detalhes = json.loads(faturamento.detalhes_json)
                    
                    # Buscar no array da categoria correspondente
                    registros = detalhes.get(campo_categoria[tipo_entidade], [])
                    
                    for registro in registros:
                        if registro.get(campo_id[tipo_entidade]) == carga_pagar_id:
                            return faturamento.codigo_faturamento
                            
                except (json.JSONDecodeError, TypeError):
                    continue
                    
            return "N/A"
        except Exception as e:
            return "N/A"



