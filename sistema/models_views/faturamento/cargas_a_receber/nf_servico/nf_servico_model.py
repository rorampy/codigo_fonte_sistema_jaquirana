from ....base_model import BaseModel, db
from datetime import date, timedelta
from sqlalchemy import and_, or_, case, desc, asc, nullslast, func
from datetime import datetime, timedelta

class NfServicoModel(BaseModel):
    """
    Model para registro de nota fiscal de serviço com todas as informações da NFSe
    """

    __tablename__ = "fin_nf_servico"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    
    cliente_id = db.Column(db.Integer, db.ForeignKey("cli_cliente.id"), nullable=False)
    cliente = db.relationship("ClienteModel", backref=db.backref("cliente_nf_servico", lazy=True))

    # Dados do Serviço
    servico_exigivel = db.Column(db.String(150), nullable=True)
    municipio_prestacao_servico = db.Column(db.String(150), nullable=True)
    municipio_incidencia = db.Column(db.String(150), nullable=True)
    
    # Prestador do Serviço (empresa que emite)
    prestador_identificacao_social = db.Column(db.String(255), nullable=True)
    prestador_nome_fantasia = db.Column(db.String(255), nullable=True)
    prestador_endereco = db.Column(db.String(500), nullable=True)
    prestador_municipio = db.Column(db.String(150), nullable=True)
    prestador_cep = db.Column(db.String(15), nullable=True)
    prestador_cnpj_cpf = db.Column(db.String(25), nullable=True)
    prestador_inscricao_municipal = db.Column(db.String(100), nullable=True)
    prestador_inscricao_estadual = db.Column(db.String(100), nullable=True)
    prestador_telefone = db.Column(db.String(100), nullable=True)
    prestador_email = db.Column(db.String(150), nullable=True)
    
    # Tomador do Serviço (cliente)
    tomador_razao_social = db.Column(db.String(255), nullable=True)
    tomador_endereco = db.Column(db.String(500), nullable=True)
    tomador_municipio = db.Column(db.String(150), nullable=True)
    tomador_cep = db.Column(db.String(15), nullable=True)
    tomador_cnpj_cpf = db.Column(db.String(25), nullable=True)
    tomador_inscricao_municipal = db.Column(db.String(100), nullable=True)
    tomador_telefone = db.Column(db.String(100), nullable=True)
    tomador_email = db.Column(db.String(150), nullable=True)
    
    # Discriminação do Serviço
    discriminacao_servico = db.Column(db.Text, nullable=True)  # Descrição do serviço prestado
    carregamento_discriminacao = db.Column(db.String(255), nullable=True)  # Ex: "SERVIÇOS PRESTADOS NO PERÍODO 11/09/25 A 25/09/25"
    base_calculo_rs = db.Column(db.Integer, nullable=True)  # Base de Cálculo(R$) * 100
    valor_servico_100 = db.Column(db.Integer, nullable=True)  # Valor do Serviço * 100
    valor_desconto_100 = db.Column(db.Integer, nullable=True)  # Desconto(R$) * 100
    desconto_condicional_100 = db.Column(db.Integer, nullable=True)  # Desconto Condicional(R$) * 100
    valor_liquido_100 = db.Column(db.Integer, nullable=True)  # Valor Líquido * 100
    
    # Alíquotas e Valores
    aliquota_servico = db.Column(db.Float, nullable=True)  # % da alíquota
    valor_iss_100 = db.Column(db.Integer, nullable=True)  # Valor do ISS(R$) * 100
    valor_iss_retido_100 = db.Column(db.Integer, nullable=True)  # Valor do ISS Retido(R$) * 100
    desconto_condicional_rs = db.Column(db.Integer, nullable=True)  # Desconto Condicional(R$) * 100
    
    # Retenções Federais
    pis_percentual = db.Column(db.Float, nullable=True)  # PIS (%)
    pis_valor_100 = db.Column(db.Integer, nullable=True)  # PIS valor * 100
    cofins_percentual = db.Column(db.Float, nullable=True)  # COFINS (%)
    cofins_valor_100 = db.Column(db.Integer, nullable=True)  # COFINS valor * 100
    inss_percentual = db.Column(db.Float, nullable=True)  # INSS (%)
    inss_valor_100 = db.Column(db.Integer, nullable=True)  # INSS valor * 100
    csll_percentual = db.Column(db.Float, nullable=True)  # CSLL (%)
    csll_valor_100 = db.Column(db.Integer, nullable=True)  # CSLL valor * 100
    outras_retencoes_100 = db.Column(db.Integer, nullable=True)  # Outras Retenções * 100
    
    # Totais
    total_servicos_100 = db.Column(db.Integer, nullable=True)  # Total dos Serviços * 100
    total_liquido_100 = db.Column(db.Integer, nullable=True)  # Total Líquido * 100
    
    # Dados da Nota Fiscal
    numero_nota_fiscal = db.Column(db.String(50), nullable=True)
    serie_nota = db.Column(db.String(10), nullable=True)
    data_emissao = db.Column(db.Date, nullable=True)
    data_competencia = db.Column(db.Date, nullable=True)
    chave_acesso = db.Column(db.String(500), nullable=True)
    
    # Período de prestação do serviço
    periodo_inicio = db.Column(db.Date, nullable=True)
    periodo_fim = db.Column(db.Date, nullable=True)
    
    # Arquivos
    arquivo_nota_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    arquivo_nota = db.relationship("UploadArquivoModel", foreign_keys=[arquivo_nota_id], backref=db.backref("arquivo_nf_servico", lazy=True))
    
    situacao_financeira_id = db.Column(db.Integer, db.ForeignKey("fin_situacao_pagamento.id"), nullable=True)
    situacao = db.relationship("SituacaoPagamentoModel", backref=db.backref("fin_servico_situacao", lazy=True))

    ativo = db.Column(db.Boolean, default=True, nullable=False)

    def __init__(
        self,
        cliente_id=None,
        # Dados do Serviço
        servico_exigivel=None,
        municipio_prestacao_servico=None,
        municipio_incidencia=None,
        # Prestador do Serviço
        prestador_identificacao_social=None,
        prestador_nome_fantasia=None,
        prestador_endereco=None,
        prestador_municipio=None,
        prestador_cep=None,
        prestador_cnpj_cpf=None,
        prestador_inscricao_municipal=None,
        prestador_inscricao_estadual=None,
        prestador_telefone=None,
        prestador_email=None,
        # Tomador do Serviço
        tomador_razao_social=None,
        tomador_endereco=None,
        tomador_municipio=None,
        tomador_cep=None,
        tomador_cnpj_cpf=None,
        tomador_inscricao_municipal=None,
        tomador_telefone=None,
        tomador_email=None,
        # Discriminação do Serviço
        discriminacao_servico=None,
        carregamento_cavaco_biomassa=None,
        base_calculo_rs=None,
        valor_servico_100=None,
        valor_desconto_100=None,
        desconto_condicional_100=None,
        valor_liquido_100=None,
        # Alíquotas e Valores
        aliquota_servico=None,
        valor_iss_100=None,
        valor_iss_retido_100=None,
        desconto_condicional_rs=None,
        # Retenções Federais
        pis_percentual=None,
        pis_valor_100=None,
        cofins_percentual=None,
        cofins_valor_100=None,
        inss_percentual=None,
        inss_valor_100=None,
        csll_percentual=None,
        csll_valor_100=None,
        outras_retencoes_100=None,
        # Totais
        total_servicos_100=None,
        total_liquido_100=None,
        # Dados da Nota
        numero_nota_fiscal=None,
        serie_nota=None,
        data_emissao=None,
        data_competencia=None,
        chave_acesso=None,
        periodo_inicio=None,
        periodo_fim=None,
        arquivo_nota_id=None,
        situacao_financeira_id=None,
        ativo=True
    ):
        self.cliente_id = cliente_id
        # Dados do Serviço
        self.servico_exigivel = servico_exigivel
        self.municipio_prestacao_servico = municipio_prestacao_servico
        self.municipio_incidencia = municipio_incidencia
        # Prestador do Serviço
        self.prestador_identificacao_social = prestador_identificacao_social
        self.prestador_nome_fantasia = prestador_nome_fantasia
        self.prestador_endereco = prestador_endereco
        self.prestador_municipio = prestador_municipio
        self.prestador_cep = prestador_cep
        self.prestador_cnpj_cpf = prestador_cnpj_cpf
        self.prestador_inscricao_municipal = prestador_inscricao_municipal
        self.prestador_inscricao_estadual = prestador_inscricao_estadual
        self.prestador_telefone = prestador_telefone
        self.prestador_email = prestador_email
        # Tomador do Serviço
        self.tomador_razao_social = tomador_razao_social
        self.tomador_endereco = tomador_endereco
        self.tomador_municipio = tomador_municipio
        self.tomador_cep = tomador_cep
        self.tomador_cnpj_cpf = tomador_cnpj_cpf
        self.tomador_inscricao_municipal = tomador_inscricao_municipal
        self.tomador_telefone = tomador_telefone
        self.tomador_email = tomador_email
        # Discriminação do Serviço
        self.discriminacao_servico = discriminacao_servico
        self.carregamento_cavaco_biomassa = carregamento_cavaco_biomassa
        self.base_calculo_rs = base_calculo_rs
        self.valor_servico_100 = valor_servico_100
        self.valor_desconto_100 = valor_desconto_100
        self.desconto_condicional_100 = desconto_condicional_100
        self.valor_liquido_100 = valor_liquido_100
        # Alíquotas e Valores
        self.aliquota_servico = aliquota_servico
        self.valor_iss_100 = valor_iss_100
        self.valor_iss_retido_100 = valor_iss_retido_100
        self.desconto_condicional_rs = desconto_condicional_rs
        # Retenções Federais
        self.pis_percentual = pis_percentual
        self.pis_valor_100 = pis_valor_100
        self.cofins_percentual = cofins_percentual
        self.cofins_valor_100 = cofins_valor_100
        self.inss_percentual = inss_percentual
        self.inss_valor_100 = inss_valor_100
        self.csll_percentual = csll_percentual
        self.csll_valor_100 = csll_valor_100
        self.outras_retencoes_100 = outras_retencoes_100
        # Totais
        self.total_servicos_100 = total_servicos_100
        self.total_liquido_100 = total_liquido_100
        # Dados da Nota
        self.numero_nota_fiscal = numero_nota_fiscal
        self.serie_nota = serie_nota
        self.data_emissao = data_emissao
        self.data_competencia = data_competencia
        self.chave_acesso = chave_acesso
        self.periodo_inicio = periodo_inicio
        self.periodo_fim = periodo_fim
        self.arquivo_nota_id = arquivo_nota_id
        self.situacao_financeira_id = situacao_financeira_id
        self.ativo = ativo

    @staticmethod
    def criar_nf_servico(
        cliente_id,
        # Dados do Serviço
        servico_exigivel=None,
        municipio_prestacao_servico=None,
        municipio_incidencia=None,
        # Prestador do Serviço
        prestador_identificacao_social=None,
        prestador_nome_fantasia=None,
        prestador_endereco=None,
        prestador_municipio=None,
        prestador_cep=None,
        prestador_cnpj_cpf=None,
        prestador_inscricao_municipal=None,
        prestador_inscricao_estadual=None,
        prestador_telefone=None,
        prestador_email=None,
        # Tomador do Serviço
        tomador_razao_social=None,
        tomador_endereco=None,
        tomador_municipio=None,
        tomador_cep=None,
        tomador_cnpj_cpf=None,
        tomador_inscricao_municipal=None,
        tomador_telefone=None,
        tomador_email=None,
        # Discriminação do Serviço
        discriminacao_servico=None,
        carregamento_discriminacao=None,
        base_calculo_rs=None,
        valor_servico_100=None,
        valor_desconto_100=None,
        desconto_condicional_100=None,
        valor_liquido_100=None,
        # Alíquotas e Valores
        aliquota_servico=None,
        valor_iss_100=None,
        valor_iss_retido_100=None,
        desconto_condicional_rs=None,
        # Retenções Federais
        pis_percentual=None,
        pis_valor_100=None,
        cofins_percentual=None,
        cofins_valor_100=None,
        inss_percentual=None,
        inss_valor_100=None,
        csll_percentual=None,
        csll_valor_100=None,
        outras_retencoes_100=None,
        # Totais
        total_servicos_100=None,
        total_liquido_100=None,
        # Dados da Nota
        numero_nota_fiscal=None,
        serie_nota=None,
        data_emissao=None,
        data_competencia=None,
        chave_acesso=None,
        periodo_inicio=None,
        periodo_fim=None,
        arquivo_nota_id=None,
        situacao_financeira_id=None,
        ativo=True
    ):
        """
        Cria uma nova nota fiscal de serviço.
        
        Args:
            cliente_id (int): ID do cliente
            ... (todos os outros parâmetros)
            
        Returns:
            NfServicoModel: Nova instância da nota fiscal de serviço criada
            
        Raises:
            Exception: Se houver erro na criação
        """
        try:
            nova_nf_servico = NfServicoModel(
                cliente_id=cliente_id,
                # Dados do Serviço
                servico_exigivel=servico_exigivel,
                municipio_prestacao_servico=municipio_prestacao_servico,
                municipio_incidencia=municipio_incidencia,
                # Prestador do Serviço
                prestador_identificacao_social=prestador_identificacao_social,
                prestador_nome_fantasia=prestador_nome_fantasia,
                prestador_endereco=prestador_endereco,
                prestador_municipio=prestador_municipio,
                prestador_cep=prestador_cep,
                prestador_cnpj_cpf=prestador_cnpj_cpf,
                prestador_inscricao_municipal=prestador_inscricao_municipal,
                prestador_inscricao_estadual=prestador_inscricao_estadual,
                prestador_telefone=prestador_telefone,
                prestador_email=prestador_email,
                # Tomador do Serviço
                tomador_razao_social=tomador_razao_social,
                tomador_endereco=tomador_endereco,
                tomador_municipio=tomador_municipio,
                tomador_cep=tomador_cep,
                tomador_cnpj_cpf=tomador_cnpj_cpf,
                tomador_inscricao_municipal=tomador_inscricao_municipal,
                tomador_telefone=tomador_telefone,
                tomador_email=tomador_email,
                # Discriminação do Serviço
                discriminacao_servico=discriminacao_servico,
                carregamento_discriminacao=carregamento_discriminacao,
                base_calculo_rs=base_calculo_rs,
                valor_servico_100=valor_servico_100,
                valor_desconto_100=valor_desconto_100,
                desconto_condicional_100=desconto_condicional_100,
                valor_liquido_100=valor_liquido_100,
                # Alíquotas e Valores
                aliquota_servico=aliquota_servico,
                valor_iss_100=valor_iss_100,
                valor_iss_retido_100=valor_iss_retido_100,
                desconto_condicional_rs=desconto_condicional_rs,
                # Retenções Federais
                pis_percentual=pis_percentual,
                pis_valor_100=pis_valor_100,
                cofins_percentual=cofins_percentual,
                cofins_valor_100=cofins_valor_100,
                inss_percentual=inss_percentual,
                inss_valor_100=inss_valor_100,
                csll_percentual=csll_percentual,
                csll_valor_100=csll_valor_100,
                outras_retencoes_100=outras_retencoes_100,
                # Totais
                total_servicos_100=total_servicos_100,
                total_liquido_100=total_liquido_100,
                # Dados da Nota
                numero_nota_fiscal=numero_nota_fiscal,
                serie_nota=serie_nota,
                data_emissao=data_emissao,
                data_competencia=data_competencia,
                chave_acesso=chave_acesso,
                periodo_inicio=periodo_inicio,
                periodo_fim=periodo_fim,
                arquivo_nota_id=arquivo_nota_id,
                situacao_financeira_id=situacao_financeira_id,
                ativo=ativo
            )
            
            db.session.add(nova_nf_servico)
            db.session.commit()
            
            return nova_nf_servico
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erro ao criar nota fiscal de serviço: {str(e)}")

    @staticmethod
    def obter_por_id(nf_servico_id):
        """
        Obtém uma nota fiscal de serviço pelo ID.
        
        Args:
            nf_servico_id (int): ID da nota fiscal de serviço
            
        Returns:
            NfServicoModel: Instância da nota fiscal de serviço ou None
        """
        return db.session.query(NfServicoModel).filter(
            NfServicoModel.id == nf_servico_id,
            NfServicoModel.ativo.is_(True),
            NfServicoModel.deletado.is_(False)
        ).first()

    @staticmethod
    def listar_ativas():
        """
        Lista todas as notas fiscais de serviço ativas.
        
        Returns:
            list: Lista de instâncias NfServicoModel ativas
        """
        return db.session.query(NfServicoModel).filter(
            NfServicoModel.ativo.is_(True),
            NfServicoModel.deletado.is_(False),
            NfServicoModel.situacao_financeira_id == 2
        ).order_by(NfServicoModel.id.desc()).all()

    @staticmethod
    def obter_por_numero_nf(numero_nota_fiscal):
        """
        Obtém uma nota fiscal de serviço pelo número da nota.
        
        Args:
            numero_nota_fiscal (str): Número da nota fiscal
            
        Returns:
            NfServicoModel: Instância da nota fiscal de serviço ou None
        """
        return db.session.query(NfServicoModel).filter(
            NfServicoModel.numero_nota_fiscal == numero_nota_fiscal,
            NfServicoModel.ativo.is_(True),
            NfServicoModel.deletado.is_(False)
        ).first()

    @staticmethod
    def obter_por_cliente(cliente_id, ativo=True):
        """
        Obtém todas as notas fiscais de serviço de um cliente.
        
        Args:
            cliente_id (int): ID do cliente
            ativo (bool): Se deve filtrar apenas registros ativos
            
        Returns:
            list: Lista de instâncias NfServicoModel
        """
        query = db.session.query(NfServicoModel).filter(
            NfServicoModel.cliente_id == cliente_id,
            NfServicoModel.deletado.is_(False)
        )
        
        if ativo:
            query = query.filter(NfServicoModel.ativo.is_(True))
            
        return query.order_by(NfServicoModel.created_at.desc()).all()

    @staticmethod
    def obter_por_periodo(data_inicio, data_fim, cliente_id=None):
        """
        Obtém notas fiscais de serviço por período.
        
        Args:
            data_inicio (date): Data de início do período
            data_fim (date): Data de fim do período
            cliente_id (int, optional): ID do cliente para filtrar
            
        Returns:
            list: Lista de instâncias NfServicoModel
        """
        query = db.session.query(NfServicoModel).filter(
            NfServicoModel.data_emissao.between(data_inicio, data_fim),
            NfServicoModel.ativo.is_(True),
            NfServicoModel.deletado.is_(False)
        )
        
        if cliente_id:
            query = query.filter(NfServicoModel.cliente_id == cliente_id)
            
        return query.order_by(NfServicoModel.data_emissao.desc()).all()

    def atualizar_valores(self, **kwargs):
        """
        Atualiza valores da nota fiscal de serviço.
        
        Args:
            **kwargs: Campos para atualizar
            
        Returns:
            bool: True se atualizou com sucesso
        """
        try:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erro ao atualizar NF de serviço: {str(e)}")

    def desativar(self):
        """
        Desativa a nota fiscal de serviço (soft delete).
        
        Returns:
            bool: True se desativou com sucesso
        """
        try:
            self.ativo = False
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erro ao desativar NF de serviço: {str(e)}")

    def get_valor_total_liquido(self):
        """
        Obtém o valor total líquido da NF de serviço em reais.
        
        Returns:
            float: Valor total líquido em reais
        """
        if self.total_liquido_100:
            return self.total_liquido_100
        return 0.0

    def get_valor_servicos(self):
        """
        Obtém o valor dos serviços em reais.
        
        Returns:
            float: Valor dos serviços em reais
        """
        if self.valor_servico_100:
            return self.valor_servico_100 / 100.0
        return 0.0

    def get_total_retencoes(self):
        """
        Calcula o total das retenções federais.
        
        Returns:
            float: Total das retenções em reais
        """
        total = 0
        
        if self.pis_valor_100:
            total += self.pis_valor_100
        if self.cofins_valor_100:
            total += self.cofins_valor_100
        if self.inss_valor_100:
            total += self.inss_valor_100
        if self.csll_valor_100:
            total += self.csll_valor_100
        if self.outras_retencoes_100:
            total += self.outras_retencoes_100
            
        return total / 100.0

    def get_periodo_prestacao(self):
        """
        Obtém o período de prestação do serviço formatado.
        
        Returns:
            str: Período formatado (DD/MM/AAAA - DD/MM/AAAA) ou None
        """
        if self.periodo_inicio and self.periodo_fim:
            return f"{self.periodo_inicio.strftime('%d/%m/%Y')} - {self.periodo_fim.strftime('%d/%m/%Y')}"
        elif self.periodo_inicio:
            return f"A partir de {self.periodo_inicio.strftime('%d/%m/%Y')}"
        elif self.periodo_fim:
            return f"Até {self.periodo_fim.strftime('%d/%m/%Y')}"
        return None
