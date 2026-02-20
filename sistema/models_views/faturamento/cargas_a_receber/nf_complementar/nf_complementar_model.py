from ....base_model import BaseModel, db
from datetime import date, timedelta
from sqlalchemy import and_, or_, case, desc, asc, nullslast, func
from datetime import datetime, timedelta

class NfComplementarModel(BaseModel):
    """
    Model unificada para registro de emissão de nota fiscal e ticket
    """

    __tablename__ = "fin_nf_complementar"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    
    cliente_id = db.Column(db.Integer, db.ForeignKey("cli_cliente.id"), nullable=False)
    cliente = db.relationship("ClienteModel", backref=db.backref("cliente_nf_complementar", lazy=True))
    
    nf_complementar_detalhes = db.Column(db.JSON, nullable=True)

    numero_nota_fiscal = db.Column(db.String(20), nullable=True)
    peso_ton_nf = db.Column(db.Float, nullable=True)
    serie_nota = db.Column(db.String(5), nullable=True)
    chave_acesso = db.Column(db.String(255), nullable=True)
    
    destinatario_nome = db.Column(db.String(200), nullable=True)
    destinatario_cnpj_cpf = db.Column(db.String(20), nullable=True)
    destinatario_insc_estadual = db.Column(db.String(50), nullable=True)
    destinatario_data_emissao = db.Column(db.Date, nullable=True)
    
    valor_total_nota_100 = db.Column(db.Integer, nullable=True)
    
    preco_un_nf = db.Column(db.Integer, nullable=True)

    transportador_nome = db.Column(db.String(200), nullable=True)
    transportador_cnpj_cpf = db.Column(db.String(20), nullable=True)
    transportador_insc_estadual = db.Column(db.String(50), nullable=True)

    placa_nf = db.Column(db.String(50), nullable=True)
    motorista_nf = db.Column(db.String(200), nullable=True)

    arquivo_nota_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    arquivo_nota = db.relationship("UploadArquivoModel",foreign_keys=[arquivo_nota_id], backref=db.backref("arquivo_nf_complementar", lazy=True))
    
    situacao_financeira_id = db.Column(db.Integer, db.ForeignKey("fin_situacao_pagamento.id"), nullable=True)
    situacao = db.relationship("SituacaoPagamentoModel", backref=db.backref("fin_complementar_situacao", lazy=True))
    
    conta_bancaria_id = db.Column(db.Integer, db.ForeignKey("con_conta_bancaria.id"), nullable=True)
    conta_bancaria = db.relationship("ContaBancariaModel", foreign_keys=[conta_bancaria_id], backref=db.backref("conta_bancaria_nf_complementar", lazy=True))
    
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    def __init__(
        self,
        cliente_id=None,
        nf_complementar_detalhes=None,
        numero_nota_fiscal=None,
        peso_ton_nf=None,
        serie_nota=None,
        chave_acesso=None,
        destinatario_nome=None,
        destinatario_cnpj_cpf=None,
        destinatario_insc_estadual=None,
        destinatario_data_emissao=None,
        valor_total_nota_100=None,
        preco_un_nf=None,
        transportador_nome=None,
        transportador_cnpj_cpf=None,
        transportador_insc_estadual=None,
        placa_nf=None,
        motorista_nf=None,
        arquivo_nota_id=None,
        situacao_financeira_id=None,
        conta_bancaria_id=None,
        ativo=True
    ):
        self.cliente_id = cliente_id
        self.nf_complementar_detalhes = nf_complementar_detalhes
        self.numero_nota_fiscal = numero_nota_fiscal
        self.peso_ton_nf = peso_ton_nf
        self.serie_nota = serie_nota
        self.chave_acesso = chave_acesso
        self.destinatario_nome = destinatario_nome
        self.destinatario_cnpj_cpf = destinatario_cnpj_cpf
        self.destinatario_insc_estadual = destinatario_insc_estadual
        self.destinatario_data_emissao = destinatario_data_emissao
        self.valor_total_nota_100 = valor_total_nota_100
        self.preco_un_nf = preco_un_nf
        self.transportador_nome = transportador_nome
        self.transportador_cnpj_cpf = transportador_cnpj_cpf
        self.transportador_insc_estadual = transportador_insc_estadual
        self.placa_nf = placa_nf
        self.motorista_nf = motorista_nf
        self.arquivo_nota_id = arquivo_nota_id
        self.situacao_financeira_id = situacao_financeira_id
        self.conta_bancaria_id = conta_bancaria_id
        self.ativo = ativo

    @staticmethod
    def criar_nf_complementar(
        cliente_id,
        nf_complementar_detalhes=None,
        numero_nota_fiscal=None,
        peso_ton_nf=None,
        serie_nota=None,
        chave_acesso=None,
        destinatario_nome=None,
        destinatario_cnpj_cpf=None,
        destinatario_insc_estadual=None,
        destinatario_data_emissao=None,
        valor_total_nota_100=None,
        preco_un_nf=None,
        transportador_nome=None,
        transportador_cnpj_cpf=None,
        transportador_insc_estadual=None,
        placa_nf=None,
        motorista_nf=None,
        arquivo_nota_id=None,
        ativo=True
    ):
        """
        Cria uma nova nota fiscal complementar.
        
        Args:
            cliente_id (int): ID do cliente
            nf_complementar_detalhes (dict): Dados JSON com IDs dos registros operacionais e detalhes
            numero_nota_fiscal (str): Número da nota fiscal
            peso_ton_nf (float): Peso em toneladas da nota fiscal
            serie_nota (str): Série da nota fiscal
            chave_acesso (str): Chave de acesso da nota fiscal
            destinatario_nome (str): Nome do destinatário
            destinatario_cnpj_cpf (str): CNPJ/CPF do destinatário
            destinatario_insc_estadual (str): Inscrição estadual do destinatário
            destinatario_data_emissao (date): Data de emissão da nota
            valor_total_nota_100 (int): Valor total da nota multiplicado por 100
            preco_un_nf (int): Preço unitário multiplicado por 100
            transportador_nome (str): Nome do transportador
            transportador_cnpj_cpf (str): CNPJ/CPF do transportador
            transportador_insc_estadual (str): Inscrição estadual do transportador
            placa_nf (str): Placa do veículo na nota fiscal
            motorista_nf (str): Nome do motorista na nota fiscal
            arquivo_nota_id (int): ID do arquivo da nota fiscal
            ativo (bool): Se o registro está ativo
            
        Returns:
            NfComplementarModel: Nova instância da nota fiscal complementar criada
            
        Raises:
            Exception: Se houver erro na criação
        """
        try:
            nova_nf_complementar = NfComplementarModel(
                cliente_id=cliente_id,
                nf_complementar_detalhes=nf_complementar_detalhes,
                numero_nota_fiscal=numero_nota_fiscal,
                peso_ton_nf=peso_ton_nf,
                serie_nota=serie_nota,
                chave_acesso=chave_acesso,
                destinatario_nome=destinatario_nome,
                destinatario_cnpj_cpf=destinatario_cnpj_cpf,
                destinatario_insc_estadual=destinatario_insc_estadual,
                destinatario_data_emissao=destinatario_data_emissao,
                valor_total_nota_100=valor_total_nota_100,
                preco_un_nf=preco_un_nf,
                transportador_nome=transportador_nome,
                transportador_cnpj_cpf=transportador_cnpj_cpf,
                transportador_insc_estadual=transportador_insc_estadual,
                placa_nf=placa_nf,
                motorista_nf=motorista_nf,
                arquivo_nota_id=arquivo_nota_id,
                ativo=ativo
            )
            
            db.session.add(nova_nf_complementar)
            db.session.commit()
            
            return nova_nf_complementar
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erro ao criar nota fiscal complementar: {str(e)}")

    @staticmethod
    def obter_por_id(nf_complementar_id):
        """
        Obtém uma nota fiscal complementar pelo ID.
        
        Args:
            nf_complementar_id (int): ID da nota fiscal complementar
            
        Returns:
            NfComplementarModel: Instância da nota fiscal complementar ou None
        """
        return db.session.query(NfComplementarModel).filter(
            NfComplementarModel.id == nf_complementar_id,
            NfComplementarModel.ativo.is_(True),
            NfComplementarModel.deletado.is_(False)
        ).first()

    @staticmethod
    def listar_ativas():
        """
        Lista todas as notas fiscais complementares ativas.
        
        Returns:
            list: Lista de instâncias NfComplementarModel ativas
        """
        return db.session.query(NfComplementarModel).filter(
            NfComplementarModel.ativo.is_(True),
            NfComplementarModel.deletado.is_(False),
            NfComplementarModel.situacao_financeira_id == 2
        ).order_by(NfComplementarModel.id.desc()).all()

    @staticmethod
    def obter_por_numero_nf(numero_nota_fiscal):
        """
        Obtém uma nota fiscal complementar pelo número da nota.
        
        Args:
            numero_nota_fiscal (str): Número da nota fiscal
            
        Returns:
            NfComplementarModel: Instância da nota fiscal complementar ou None
        """
        return db.session.query(NfComplementarModel).filter(
            NfComplementarModel.numero_nota_fiscal == numero_nota_fiscal,
            NfComplementarModel.ativo.is_(True),
            NfComplementarModel.deletado.is_(False)
        ).first()

    def atualizar_detalhes(self, novos_detalhes):
        """
        Atualiza os detalhes JSON da nota fiscal complementar.
        
        Args:
            novos_detalhes (dict): Novos dados para o campo JSON
            
        Returns:
            bool: True se atualizou com sucesso
        """
        try:
            self.nf_complementar_detalhes = novos_detalhes
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erro ao atualizar detalhes da NF complementar: {str(e)}")

    def desativar(self):
        """
        Desativa a nota fiscal complementar (soft delete).
        
        Returns:
            bool: True se desativou com sucesso
        """
        try:
            self.ativo = False
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erro ao desativar NF complementar: {str(e)}")

    @staticmethod
    def criar_nf_complementar_de_registros_operacionais(registros_operacionais, arquivo_nota_id=None):
        """
        Cria uma nota fiscal complementar a partir de uma lista de registros operacionais.
        
        Args:
            registros_operacionais (list): Lista de instâncias RegistroOperacionalModel
            arquivo_nota_id (int, optional): ID do arquivo PDF anexado
            
        Returns:
            NfComplementarModel: Nova instância da nota fiscal complementar criada
            
        Raises:
            Exception: Se houver erro na criação ou se os registros não forem do mesmo cliente
        """
        from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
        
        if not registros_operacionais:
            raise Exception("Nenhum registro operacional fornecido")
        
        primeiro_cliente_id = registros_operacionais[0].solicitacao.cliente_id if registros_operacionais[0].solicitacao else None
        cliente_nome = registros_operacionais[0].solicitacao.cliente.identificacao if registros_operacionais[0].solicitacao.cliente else None
        
        for registro in registros_operacionais:
            if not registro.solicitacao or not registro.solicitacao.cliente:
                raise Exception(f"Registro {registro.id} não possui cliente válido")
                
            if registro.solicitacao.cliente_id != primeiro_cliente_id:
                raise Exception("Todos os registros devem ser do mesmo cliente")
        
        peso_total_diferenca = 0
        detalhes_registros = []
        
        for registro in registros_operacionais:
            peso_nf_final = registro.peso_nf_ton_com_excecao if registro.peso_ton_nf_excesso else registro.peso_ton_nf
            
            if peso_nf_final and registro.peso_liquido_ticket:
                diferenca = peso_nf_final - registro.peso_liquido_ticket
                
                if diferenca > 0:
                    peso_total_diferenca += diferenca
                
                detalhes_registros.append({
                    "registro_operacional_id": registro.id,
                    "numero_nf_original": registro.numero_nota_fiscal,
                    "peso_nf_original": peso_nf_final,
                    "peso_ticket": registro.peso_liquido_ticket,
                    "diferenca": round(diferenca, 3),
                    "data_entrega": registro.data_entrega_ticket.isoformat() if registro.data_entrega_ticket else None,
                    "placa": registro.placa_nf or registro.placa_ticket,
                    "motorista": registro.motorista_nf or registro.motorista_ticket
                })
        
        if peso_total_diferenca <= 0:
            raise Exception("Não há diferenças positivas para emitir nota complementar")
        
        primeiro_registro = registros_operacionais[0]
        
        nf_complementar_detalhes = {
            "registros_operacionais": detalhes_registros,
            "peso_total_diferenca": round(peso_total_diferenca, 3),
            "quantidade_registros": len(registros_operacionais),
            "data_criacao": date.today().isoformat(),
            "cliente_origem": cliente_nome,
            "observacoes": f"NF Complementar gerada automaticamente a partir de {len(registros_operacionais)} registro(s) operacional(is)"
        }
        
        ultimo_numero = db.session.query(func.max(NfComplementarModel.id)).scalar() or 0
        numero_nf_complementar = f"COMP{ultimo_numero + 1:06d}"
        
        valor_estimado = None
        if primeiro_registro.preco_un_nf and peso_total_diferenca:
            valor_estimado = int(primeiro_registro.preco_un_nf * peso_total_diferenca)
        
        try:
            nova_nf_complementar = NfComplementarModel(
                cliente_id=primeiro_cliente_id,
                nf_complementar_detalhes=nf_complementar_detalhes,
                numero_nota_fiscal=numero_nf_complementar,
                peso_ton_nf=peso_total_diferenca,
                destinatario_nome=primeiro_registro.destinatario_nome,
                destinatario_cnpj_cpf=primeiro_registro.destinatario_cnpj_cpf,
                destinatario_insc_estadual=primeiro_registro.destinatario_insc_estadual,
                destinatario_data_emissao=date.today(),
                valor_total_nota_100=valor_estimado,
                preco_un_nf=primeiro_registro.preco_un_nf,
                transportador_nome=primeiro_registro.transportador_nome,
                transportador_cnpj_cpf=primeiro_registro.transportador_cnpj_cpf,
                transportador_insc_estadual=primeiro_registro.transportador_insc_estadual,
                placa_nf=primeiro_registro.placa_nf,
                motorista_nf=primeiro_registro.motorista_nf,
                arquivo_nota_id=arquivo_nota_id,
                ativo=True
            )
            
            db.session.add(nova_nf_complementar)
            db.session.commit()
            
            return nova_nf_complementar
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erro ao criar nota fiscal complementar: {str(e)}")

    @staticmethod
    def obter_por_cliente(cliente_id, ativo=True):
        """
        Obtém todas as notas fiscais complementares de um cliente.
        
        Args:
            cliente_id (int): ID do cliente
            ativo (bool): Se deve filtrar apenas registros ativos
            
        Returns:
            list: Lista de instâncias NfComplementarModel
        """
        query = db.session.query(NfComplementarModel).filter(
            NfComplementarModel.cliente_id == cliente_id,
            NfComplementarModel.deletado.is_(False)
        )
        
        if ativo:
            query = query.filter(NfComplementarModel.ativo.is_(True))
            
        return query.order_by(NfComplementarModel.created_at.desc()).all()

    def get_peso_diferenca_total(self):
        """
        Obtém o peso total de diferença desta NF complementar a partir dos detalhes JSON.
        
        Returns:
            float: Peso total da diferença
        """
        if self.nf_complementar_detalhes and 'peso_total_diferenca' in self.nf_complementar_detalhes:
            return self.nf_complementar_detalhes['peso_total_diferenca']
        return self.peso_ton_nf or 0

    def get_registros_operacionais_origem(self):
        """
        Obtém a lista de IDs dos registros operacionais que originaram esta NF complementar.
        
        Returns:
            list: Lista de IDs dos registros operacionais
        """
        if self.nf_complementar_detalhes and 'registros_operacionais' in self.nf_complementar_detalhes:
            return [reg['registro_operacional_id'] for reg in self.nf_complementar_detalhes['registros_operacionais']]
        return []
