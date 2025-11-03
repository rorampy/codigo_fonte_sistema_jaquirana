from ..base_model import BaseModel, db
from sqlalchemy import desc
from datetime import datetime
import json
from sistema.models_views.financeiro.operacional.categorizar_fatura.categorizacao_model import AgendamentoPagamentoModel
from sistema.models_views.gerenciar.pessoa_financeiro.pessoa_financeiro_model import PessoaFinanceiroModel

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
