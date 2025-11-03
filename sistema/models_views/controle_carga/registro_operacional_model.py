from ..base_model import BaseModel, db
from datetime import date, timedelta
from sqlalchemy import and_, or_, case, desc, asc, nullslast, func
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
from sistema import request
from sistema.models_views.financeiro.situacao_pagamento_model import SituacaoPagamentoModel
from sistema.models_views.controle_carga.carga_model import CargaModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema.models_views.gerenciar.veiculo.veiculo_model import VeiculoModel
from sistema.models_views.gerenciar.motorista.motorista_model import MotoristaModel
from sistema.models_views.gerenciar.motorista.transportadora_motorista_associado_model import TransportadoraMotoristaAssocModel
from sistema.models_views.gerenciar.floresta.floresta_model import FlorestaModel
from sistema.models_views.faturamento.cargas_a_pagar.fornecedor.fornecedor_a_pagar_model import FornecedorPagarModel
from sistema.models_views.faturamento.cargas_a_pagar.extrator.extrator_a_pagar_model import ExtratorPagarModel
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema.models_views.gerenciar.veiculo.veiculo_transportadora_veiculo_associado_model import TransportadoraVeiculoAssocModel
from sistema.models_views.parametros.rotas_frete.rota_model import RotaFreteModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_model import FornecedorModel
from sistema.models_views.controle_carga.produto_model import ProdutoModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.faturamento.cargas_a_pagar.transportadora.frete_a_pagar_model import FretePagarModel
from sistema.models_views.faturamento.cargas_a_receber.recebimento_model import RecebimentoModel
from sistema.models_views.financeiro.movimentacao_financeira.movimentacao_financeira_model import MovimentacaoFinanceiraModel


class RegistroOperacionalModel(BaseModel):
    """
    Model unificada para registro de emissão de nota fiscal e ticket
    """

    __tablename__ = "re_registro_operacional"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    solicitacao_nf_id = db.Column(db.Integer, db.ForeignKey("car_carga.id"), nullable=True)
    solicitacao = db.relationship("CargaModel", backref=db.backref("car_carga_registro_operacional", lazy=True))

    # Dados do emissor da nota fiscal

    # =========================> ATENÇÃO <=========================
    # Coluna descontinuada no projeto, agora é usada somente a tabela de fornecedor_id
    floresta_id = db.Column(db.Integer, db.ForeignKey("flor_floresta.id"), nullable=True)
    # =============================================================
    fornecedor_id = db.Column(db.Integer, db.ForeignKey("for_fornecedor.id"), nullable=True)

    razao_social_emissor = db.Column(db.String(200), nullable=True)
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

    # Dados do transportador (nota fiscal)
    transportador_nome = db.Column(db.String(200), nullable=True)
    transportador_cnpj_cpf = db.Column(db.String(20), nullable=True)
    transportador_insc_estadual = db.Column(db.String(50), nullable=True)

    # Dados transporte NF
    placa_nf = db.Column(db.String(50), nullable=True)
    motorista_nf = db.Column(db.String(200), nullable=True)

    # Dados transporte Ticket
    placa_ticket = db.Column(db.String(50), nullable=True)
    motorista_ticket = db.Column(db.String(200), nullable=True)
    data_entrega_ticket = db.Column(db.Date, nullable=True)

    # Ticket de pesagem
    numero_nota_fiscal_ticket = db.Column(db.String(20), nullable=True)
    peso_liquido_ticket = db.Column(db.Float, nullable=True)

    # Arquivos
    arquivo_nota_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    arquivo_nota = db.relationship("UploadArquivoModel",foreign_keys=[arquivo_nota_id], backref=db.backref("car_registro_nf", lazy=True))

    arquivo_ticket_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    arquivo_ticket = db.relationship("UploadArquivoModel", foreign_keys=[arquivo_ticket_id], backref=db.backref("car_registro_ticket", lazy=True))

    status_emissao_nf_complementar_id = db.Column(db.Integer, db.ForeignKey("z_sys_status_emissao_nf_complementar.id"), nullable=True)
    status_emissao_nf_complementar = db.relationship("StatusEmissaoNfComplementarModel",foreign_keys=[status_emissao_nf_complementar_id],backref=db.backref("status_emissao_nf_complementar", lazy=True))

    situacao_financeira_id = db.Column(db.Integer, db.ForeignKey("fin_situacao_pagamento.id"), nullable=True)
    situacao = db.relationship("SituacaoPagamentoModel",backref=db.backref("situacao_financeira_registro", lazy=True),)

    possui_excesso_carga = db.Column(db.Boolean, default=False, nullable=False) 
    arquivo_nota_excesso_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    arquivo_nota_excesso = db.relationship("UploadArquivoModel",foreign_keys=[arquivo_nota_excesso_id], backref=db.backref("arquivo_nota_excesso", lazy=True))
    peso_ton_nf_excesso = db.Column(db.Float, nullable=True)
    peso_nf_ton_com_excecao = db.Column(db.Float, nullable=True)
    numero_nota_fiscal_excessao = db.Column(db.String(20), nullable=True)

    estorno_nf = db.Column(db.Boolean, default=False, nullable=False) 
    arquivo_nota_estorno_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    arquivo_nota_estorno = db.relationship("UploadArquivoModel",foreign_keys=[arquivo_nota_estorno_id], backref=db.backref("arquivo_nota_estorno", lazy=True))
    numero_nota_fiscal_estorno = db.Column(db.String(20), nullable=True)

    realizado_split = db.Column(db.Boolean, default=False, nullable=True) 

    carga_frf = db.Column(db.Boolean, default=False, nullable=False) 
    
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    def __init__(
        self,
        solicitacao_nf_id,
        data_entrega_ticket=None,
        ativo=True,
        numero_nota_fiscal=None,
        peso_ton_nf=None,
        numero_nota_fiscal_ticket=None,
        peso_liquido_ticket=None,
        serie_nota=None,
        chave_acesso=None,
        floresta_id=None,
        fornecedor_id=None,
        razao_social_emissor=None,
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
        placa_ticket=None,
        motorista_ticket=None,
        peso_liquido=None,
        arquivo_nota_id=None,
        arquivo_ticket_id=None,
        status_emissao_nf_complementar_id=None,
        situacao_financeira_id=None,
        possui_excesso_carga=False,
        arquivo_nota_excesso_id=None,
        peso_ton_nf_excesso=None,
        peso_nf_ton_com_excecao=None,
        estorno_nf=False,
        arquivo_nota_estorno_id=None,
        numero_nota_fiscal_estorno=None,
        numero_nota_fiscal_excessao = None,
        carga_frf = False,
        realizado_split=False
    ):
        self.solicitacao_nf_id = solicitacao_nf_id
        self.numero_nota_fiscal = numero_nota_fiscal
        self.peso_ton_nf = peso_ton_nf
        self.numero_nota_fiscal_ticket = numero_nota_fiscal_ticket
        self.peso_liquido_ticket = peso_liquido_ticket
        self.serie_nota = serie_nota
        self.chave_acesso = chave_acesso
        self.floresta_id = floresta_id
        self.fornecedor_id = fornecedor_id
        self.razao_social_emissor = razao_social_emissor
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
        self.placa_ticket = placa_ticket
        self.data_entrega_ticket = data_entrega_ticket
        self.motorista_ticket = motorista_ticket
        self.peso_liquido = peso_liquido
        self.arquivo_nota_id = arquivo_nota_id
        self.arquivo_ticket_id = arquivo_ticket_id
        self.status_emissao_nf_complementar_id = status_emissao_nf_complementar_id
        self.situacao_financeira_id = situacao_financeira_id
        self.possui_excesso_carga = possui_excesso_carga
        self.arquivo_nota_excesso_id = arquivo_nota_excesso_id
        self.peso_ton_nf_excesso = peso_ton_nf_excesso
        self.peso_nf_ton_com_excecao = peso_nf_ton_com_excecao
        self.estorno_nf = estorno_nf
        self.arquivo_nota_estorno_id = arquivo_nota_estorno_id
        self.numero_nota_fiscal_estorno = numero_nota_fiscal_estorno
        self.realizado_split = realizado_split
        self.numero_nota_fiscal_excessao = numero_nota_fiscal_excessao
        self.carga_frf = carga_frf
        self.ativo = ativo


    def corrigir_peso_preco_un_nf_todos():
        """
        Corrige o peso e o preço unitário de todas as notas fiscais, lendo novamente o(s) PDF(s).
        Atualiza separadamente os campos da nota normal e da nota de excesso, conforme o arquivo processado.
        Não sobrescreve valores de excesso com valores da nota normal.
        """
        from sistema._utilitarios.extracao_texto_nota_fiscal import ExtrairTextoNotaFiscal
        from sistema.models_views.upload_arquivo.upload_arquivo_model import UploadArquivoModel
        registros = RegistroOperacionalModel.query.filter_by(deletado=False).all()
        for registro in registros:
            if registro.carga_frf:
                continue
            atualizou = False
            # Corrige nota normal
            if registro.arquivo_nota_id and (registro.peso_ton_nf is None or registro.preco_un_nf is None):
                arquivo = UploadArquivoModel.query.get(registro.arquivo_nota_id)
                if arquivo and hasattr(arquivo, 'caminho') and arquivo.caminho:
                    try:
                        texto_pdf = ExtrairTextoNotaFiscal.extrair_texto_do_pdf(arquivo.caminho)
                        itens = ExtrairTextoNotaFiscal.nf_extrair_itens(texto_pdf)
                        peso_nf = 0
                        preco_un = 0
                        for item in itens:
                            quantidade = item.get('quantidade', '0').replace(',', '.')
                            preco_unitario = item.get('preco_unitario', '0').replace(',', '.')
                            try:
                                peso_nf += round(float(quantidade), 2)
                                preco_un += int(round(float(preco_unitario) * 100))
                            except Exception:
                                continue
                        registro.peso_ton_nf = peso_nf
                        registro.preco_un_nf = preco_un
                        atualizou = True
                    except Exception as e:
                        db.session.rollback()
            # Corrige nota de excesso
            if registro.possui_excesso_carga and registro.arquivo_nota_excesso_id and registro.peso_ton_nf_excesso is None:
                arquivo_excesso = UploadArquivoModel.query.get(registro.arquivo_nota_excesso_id)
                if arquivo_excesso and hasattr(arquivo_excesso, 'caminho') and arquivo_excesso.caminho:
                    try:
                        texto_pdf_excesso = ExtrairTextoNotaFiscal.extrair_texto_do_pdf(arquivo_excesso.caminho)
                        itens_excesso = ExtrairTextoNotaFiscal.nf_extrair_itens(texto_pdf_excesso)
                        peso_nf_excesso = 0
                        for item in itens_excesso:
                            quantidade = item.get('quantidade', '0').replace(',', '.')
                            try:
                                peso_nf_excesso += round(float(quantidade), 2)
                            except Exception:
                                continue
                        registro.peso_ton_nf_excesso = peso_nf_excesso
                        # Atualiza campo total se necessário
                        registro.peso_nf_ton_com_excecao = (registro.peso_ton_nf or 0) + (registro.peso_ton_nf_excesso or 0)
                        atualizou = True
                    except Exception as e:
                        db.session.rollback()

            # Corrige nota de estorno
            if registro.estorno_nf and registro.arquivo_nota_estorno_id and (getattr(registro, 'peso_ton_nf_estorno', None) is None or getattr(registro, 'preco_un_nf_estorno', None) is None):
                arquivo_estorno = UploadArquivoModel.query.get(registro.arquivo_nota_estorno_id)
                if arquivo_estorno and hasattr(arquivo_estorno, 'caminho') and arquivo_estorno.caminho:
                    try:
                        texto_pdf_estorno = ExtrairTextoNotaFiscal.extrair_texto_do_pdf(arquivo_estorno.caminho)
                        itens_estorno = ExtrairTextoNotaFiscal.nf_extrair_itens(texto_pdf_estorno)
                        peso_nf_estorno = 0
                        preco_un_estorno = 0
                        for item in itens_estorno:
                            quantidade = item.get('quantidade', '0')
                            preco_unitario = item.get('preco_unitario', '0')
                            try:
                                peso_nf_estorno += round(float(quantidade), 2)
                                preco_un_estorno += int(round(float(preco_unitario) * 100))
                            except Exception:
                                continue
                        registro.peso_ton_nf_estorno = peso_nf_estorno
                        registro.preco_un_nf_estorno = preco_un_estorno
                        atualizou = True
                    except Exception as e:
                        db.session.rollback()
            if atualizou:
                try:
                    db.session.add(registro)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                
    def extrair_dados_frf_form(request):
        """
        Extrai e valida os dados do formulário para FRF (campos manuais).
        """
        destinatarioFrf = request.form.get("destinatarioFrf", "")
        destinatarioNumeroDocumento = request.form.get("destinatarioNumeroDocumento", "")
        dataLancamentoFrf = request.form.get("dataLancamentoFrf", "")
        transportadorFrf = request.form.get("transportadorFrf", "")
        transportadoraNumeroDocumento = request.form.get("transportadoraNumeroDocumento", "")
        placaFrf = request.form.get("placaFrf", "")
        motoristaFrf = request.form.get("motoristaFrf", "")
        pesoFrf = request.form.get("pesoFrf", "")
        valorTotalFrf = request.form.get("valorTotalFrf", "")
        return {
            "destinatario_nome": destinatarioFrf,
            "destinatario_cnpj_cpf": destinatarioNumeroDocumento,
            "destinatario_data_emissao": dataLancamentoFrf,
            "transportador_nome": transportadorFrf,
            "transportador_cnpj_cpf": transportadoraNumeroDocumento,
            "placa_nf": placaFrf,
            "motorista_nf": motoristaFrf,
            "peso_ton_nf": pesoFrf,
            "valor_total_nota_100": valorTotalFrf,
        }

    def extrair_dados_nf_pdf(dados_nota):
        """
        Extrai e valida os dados de uma nota fiscal extraída do PDF.
        """
        razao_social_emissor = dados_nota["emissor"]["razao_social_emissor"]
        numero_nota = dados_nota["emissor"]["numero_nota"]
        serie = dados_nota["emissor"]["serie"]
        chave_acesso = dados_nota["emissor"]["chave_acesso"]
        destinatario = dados_nota["destinatario"]["nome_razao_social"]
        destinatario_cpf_cnpj = dados_nota["destinatario"]["cnpj_cpf"]
        destinatario_insc_estadual = dados_nota["destinatario"]["insc_estadual"]
        destinatario_data_emissao = dados_nota["destinatario"]["data_emissao"]
        valor_total_nota = dados_nota["calculo_imposto"]["valor_total_nota"]
        transportador = dados_nota["transportador"]["nome"]
        transportador_cpf_cnpj = dados_nota["transportador"]["cnpj_cpf"]
        transportador_insc_estadual = dados_nota["transportador"]["insc_estadual"]
        placa = dados_nota["dados_adicionais"]["placa"]
        motorista = dados_nota["dados_adicionais"]["motorista"]
        itens_nf = dados_nota['itens']
        peso_nf = 0
        preco_un = 0
        for i in itens_nf:
            quantidade = i['quantidade'].replace(',', '.')
            peso_nf += round(float(quantidade), 2)
            preco_un += int(round(float(i['preco_unitario'].replace(',', '.')) * 100))
        return {
            "razao_social_emissor": razao_social_emissor,
            "numero_nota_fiscal": numero_nota,
            "serie_nota": serie,
            "chave_acesso": chave_acesso,
            "destinatario_nome": destinatario,
            "destinatario_cnpj_cpf": destinatario_cpf_cnpj,
            "destinatario_insc_estadual": destinatario_insc_estadual,
            "destinatario_data_emissao": destinatario_data_emissao,
            "valor_total_nota_100": valor_total_nota,
            "preco_un_nf": preco_un,
            "transportador_nome": transportador,
            "transportador_cnpj_cpf": transportador_cpf_cnpj,
            "transportador_insc_estadual": transportador_insc_estadual,
            "placa_nf": placa,
            "motorista_nf": motorista,
            "peso_ton_nf": peso_nf,
        }

    def extrair_dados_nf_excesso_pdf(dados_nota_excesso):
        """
        Extrai e valida os dados de uma nota fiscal de excesso extraída do PDF.
        """
        numero_nota_excessao = dados_nota_excesso["emissor"]["numero_nota"]
        itens_nf_excesso = dados_nota_excesso['itens']
        peso_nf_excesso = 0
        for i in itens_nf_excesso:
            quantidade_excesso = i['quantidade'].replace(',', '.')
            peso_nf_excesso += round(float(quantidade_excesso), 2)
        return {
            "numero_nota_fiscal_excessao": numero_nota_excessao,
            "peso_ton_nf_excesso": peso_nf_excesso,
        }

    def criar_registro_operacional(**kwargs):
        """
        Cria um registro operacional de acordo com os campos fornecidos.
        """
        registro = RegistroOperacionalModel(**kwargs)
        db.session.add(registro)
        db.session.commit()
        return registro


    def listar_inativos():
        """
        Retorna todos os registros operacionais inativos e não deletados, ordenados por ID decrescente.
        
        Returns:
            list: Lista de registros inativos
        """
        return (
            RegistroOperacionalModel.query.filter_by(ativo=False, deletado=False)
            .order_by(RegistroOperacionalModel.id.desc())
            .all()
        )

    def obter_por_id(id):
        """
        Obtém um registro operacional pelo seu ID, se não estiver deletado.
        
        Args:
            id (int): ID do registro operacional
        Returns:
            RegistroOperacionalModel | None: Registro encontrado ou None
        """
        return RegistroOperacionalModel.query.filter_by(id=id, deletado=False).first()

    def obter_registro_solicitacao_por_id(id):
        """
        Obtém o registro operacional ativo vinculado a uma solicitação de nota fiscal específica.
        
        Args:
            id (int): ID da solicitação de nota fiscal
        Returns:
            RegistroOperacionalModel | None: Registro encontrado ou None
        """
        return RegistroOperacionalModel.query.filter_by(
            solicitacao_nf_id=id, deletado=False, ativo=True
        ).first()

    def filtro_relatorio_registros(
        data_inicio=None,
        data_fim=None,
        placa_carga=None,
        freteiro_carga=None,
        transportadora_carga=None,
        floresta_fornecedor=None,
        cliente_carga=None,
    ):
        """
        Filtra registros operacionais para relatório, com base em datas e parâmetros de carga.
        
        Args:
            data_inicio (date, optional): Data inicial do filtro
            data_fim (date, optional): Data final do filtro
            placa_carga (str, optional): Placa do veículo
            freteiro_carga (str, optional): Nome do motorista/freteiro
            transportadora_carga (str, optional): Nome da transportadora
            floresta_fornecedor (str, optional): Nome do fornecedor ou floresta
            cliente_carga (str, optional): Nome do cliente
        Returns:
            list: Lista de registros filtrados
        """
        query = RegistroOperacionalModel.query.join(
            RegistroOperacionalModel.solicitacao
        ).filter(
            RegistroOperacionalModel.deletado == False,
            RegistroOperacionalModel.ativo == True,
        )

        if not data_inicio and not data_fim:
            data_inicio = date.today() - timedelta(days=30)
            data_fim = date.today()
            query = query.filter(
                or_(
                    RegistroOperacionalModel.data_entrega_ticket.is_(None),
                    and_(
                        RegistroOperacionalModel.data_entrega_ticket >= data_inicio,
                        RegistroOperacionalModel.data_entrega_ticket <= data_fim,
                    ),
                )
            )
        else:
            if data_inicio:
                query = query.filter(
                    RegistroOperacionalModel.data_entrega_ticket >= data_inicio
                )
            if data_fim:
                query = query.filter(
                    RegistroOperacionalModel.data_entrega_ticket <= data_fim
                )

        if placa_carga:
            query = query.filter(
                or_(
                    RegistroOperacionalModel.placa_nf.ilike(f"%{placa_carga}%"),
                    RegistroOperacionalModel.placa_ticket.ilike(f"%{placa_carga}%"),
                )
            )

        if freteiro_carga:
            query = query.filter(
                or_(
                    RegistroOperacionalModel.motorista_nf.ilike(f"%{freteiro_carga}%"),
                    RegistroOperacionalModel.motorista_ticket.ilike(
                        f"%{freteiro_carga}%"
                    ),
                )
            )

        if transportadora_carga:
            query = (
                query.join(CargaModel.veiculo)
                .join(VeiculoModel.transportadora)
                .filter(
                    TransportadoraModel.identificacao.ilike(f"%{transportadora_carga}%")
                )
            )

        if floresta_fornecedor:
            query = (
                query.join(CargaModel.floresta)
                .join(CargaModel.fornecedor)
                .filter(
                    or_(
                        FlorestaModel.identificacao.ilike(f"%{floresta_fornecedor}%"),
                        FornecedorModel.identificacao.ilike(f"%{floresta_fornecedor}%"),
                    )
                )
            )

        if cliente_carga:
            query = query.join(CargaModel.cliente).filter(
                ClienteModel.identificacao.ilike(f"%{cliente_carga}%")
            )

        return query.order_by(RegistroOperacionalModel.id.desc()).all()
    
    def obter_registros_carga_agrupados():
        """
        Retorna todos os registros de carga agrupados por cliente e produto.
        
        Returns:
            list: Lista de dicionários com registros agrupados
        """
       
        data_inicio = date.today() - timedelta(days=30)
        data_fim = date.today()
        
        query = (
            db.session.query(RegistroOperacionalModel, ClienteModel)
            .join(CargaModel, RegistroOperacionalModel.solicitacao_nf_id == CargaModel.id)
            .join(ClienteModel, CargaModel.cliente_id == ClienteModel.id)
            .join(MotoristaModel, CargaModel.motorista_id == MotoristaModel.id)
            .join(VeiculoModel, CargaModel.veiculo_id == VeiculoModel.id)
            .outerjoin(
                TransportadoraVeiculoAssocModel,
                CargaModel.transportadora_id == TransportadoraVeiculoAssocModel.transportadora_id,
            )
            .join(ProdutoModel, CargaModel.produto_id == ProdutoModel.id)
            .join(BitolaModel, CargaModel.bitola_id == BitolaModel.id)
            .filter(
                RegistroOperacionalModel.deletado.is_(False),
                RegistroOperacionalModel.ativo.is_(True),
                RegistroOperacionalModel.situacao_financeira_id == 2
            )
        )

        if data_inicio and data_fim:
            query = query.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket.between(data_inicio, data_fim),
            )
        elif data_inicio:
            query = query.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket >= data_inicio,
            )
        elif data_fim:
            query = query.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket <= data_fim,
            )

        resultados = []
        for registro, cliente in query.all():
            produto = getattr(registro.solicitacao.produto, "nome", "Indefinido")
            
            resultados.append({
                "cliente": cliente.identificacao,
                "produto": produto,
                "registro": registro,
            })

        resultados.sort(key=lambda x: (x["cliente"], x["produto"]))
        return resultados
    
    def filtrar_registros_carga_cliente(
        data_inicio=None,
        data_fim=None,
        cliente=None,
        numero_nf=None,
        placa=None,
        motorista=None,
        transportadora=None,
        fornecedor=None,
        produto=None,
        bitola=None,
        status_nf_complementar=None,
        status_pagamento=None,
    ):
        """
        Filtra e retorna registros de carga agrupados por cliente e produto.
        
        Args:
            data_inicio (date, optional): Data inicial do filtro
            data_fim (date, optional): Data final do filtro
            cliente (str, optional): Nome/identificação do cliente
            numero_nf (str, optional): Número da nota fiscal
            placa (str, optional): Placa do veículo
            motorista (str, optional): Nome do motorista
            transportadora (str, optional): Nome da transportadora
            fornecedor (str, optional): Nome do fornecedor
            produto (str, optional): Nome do produto
            bitola (str, optional): Bitola
            status_nf_complementar (int, optional): Status da NF complementar
            status_pagamento (int, optional): ID da situação financeira
        
        Returns:
            list: Lista de dicionários com registros filtrados e agrupados
        """
        if not data_inicio or not data_fim:
            data_inicio = date.today() - timedelta(days=30)
            data_fim = date.today()

        query = (
            db.session.query(RegistroOperacionalModel, ClienteModel)
            .join(CargaModel, RegistroOperacionalModel.solicitacao_nf_id == CargaModel.id)
            .join(ClienteModel, CargaModel.cliente_id == ClienteModel.id)
            .join(MotoristaModel, CargaModel.motorista_id == MotoristaModel.id)
            .join(VeiculoModel, CargaModel.veiculo_id == VeiculoModel.id)
            .join(ProdutoModel, CargaModel.produto_id == ProdutoModel.id)
            .join(BitolaModel, CargaModel.bitola_id == BitolaModel.id)
            .filter(
                RegistroOperacionalModel.deletado.is_(False),
                RegistroOperacionalModel.ativo.is_(True),
            )
        )

        if data_inicio and data_fim:
            query = query.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket.between(data_inicio, data_fim),
            )
        elif data_inicio:
            query = query.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket >= data_inicio,
            )
        elif data_fim:
            query = query.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket <= data_fim,
            )

        if cliente:
            query = query.filter(ClienteModel.identificacao.ilike(f"%{cliente}%"))

        if numero_nf:
            query = query.filter(
                or_(
                    RegistroOperacionalModel.numero_nota_fiscal.ilike(f"%{numero_nf}%"),
                    RegistroOperacionalModel.numero_nota_fiscal_excessao.ilike(f"%{numero_nf}%"),
                    RegistroOperacionalModel.numero_nota_fiscal_estorno.ilike(f"%{numero_nf}%"),
                )
            )

        if status_nf_complementar:
            query = query.filter(
                RegistroOperacionalModel.status_emissao_nf_complementar_id == status_nf_complementar
            )

        if produto:
            query = query.filter(ProdutoModel.nome.ilike(f"%{produto}%"))

        if bitola:
            query = query.filter(BitolaModel.bitola.ilike(f"%{bitola}%"))

        if motorista:
            query = query.filter(MotoristaModel.nome_completo.ilike(f"%{motorista}%"))

        if transportadora:
            query = query.outerjoin(
                TransportadoraModel,
                CargaModel.transportadora_id == TransportadoraModel.id,
            ).filter(
                TransportadoraModel.identificacao.ilike(f"%{transportadora}%")
            )

        if fornecedor:
            query = query.filter(
                or_(
                    CargaModel.fornecedor.has(
                        FornecedorModel.identificacao.ilike(f"%{fornecedor}%")
                    ),
                    CargaModel.floresta.has(
                        FlorestaModel.identificacao.ilike(f"%{fornecedor}%")
                    ),
                )
            )

        if placa:
            query = query.filter(VeiculoModel.placa_veiculo.ilike(f"%{placa}%"))

        if status_pagamento:
            query = query.filter(RegistroOperacionalModel.situacao_financeira_id == status_pagamento)

        resultados = []
        for registro, cliente in query.all():
            produto = getattr(registro.solicitacao.produto, "nome", "Indefinido")
            
            resultados.append({
                "cliente": cliente.identificacao,
                "produto": produto,
                "registro": registro,
            })

        resultados.sort(key=lambda x: (x["cliente"], x["produto"]))
        return resultados

    def registros_carga_cliente(
        data_inicio=None,
        data_fim=None,
        cliente=None,
        numero_nf=None,
        placa=None,
        motorista=None,
        transportadora=None,
        fornecedor=None,
        produto=None,
        bitola=None,
        status_nf_complementar=None,
    ):
        """
        Filtra e retorna registros de carga por cliente, produto e outros parâmetros.
        
        Args:
            data_inicio (date, optional): Data inicial do filtro
            data_fim (date, optional): Data final do filtro
            cliente (str, optional): Nome/identificação do cliente
            numero_nf (str, optional): Número da nota fiscal
            placa (str, optional): Placa do veículo
            motorista (str, optional): Nome do motorista
            transportadora (str, optional): Nome da transportadora
            fornecedor (str, optional): Nome do fornecedor
            produto (str, optional): Nome do produto
            bitola (str, optional): Bitola
            status_nf_complementar (int, optional): Status da NF complementar
        Returns:
            list: Lista de dicionários com registros filtrados e agrupados
        """
        if not data_inicio or not data_fim:
            data_inicio = date.today() - timedelta(days=30)
            data_fim = date.today()

        query = (
            db.session.query(RegistroOperacionalModel, ClienteModel)
            .join(
                CargaModel, RegistroOperacionalModel.solicitacao_nf_id == CargaModel.id
            )
            .join(ClienteModel, CargaModel.cliente_id == ClienteModel.id)
            .join(MotoristaModel, CargaModel.motorista_id == MotoristaModel.id)
            .join(VeiculoModel, CargaModel.veiculo_id == VeiculoModel.id)
            .outerjoin(
                TransportadoraVeiculoAssocModel,
                CargaModel.transportadora_id
                == TransportadoraVeiculoAssocModel.transportadora_id,
            )
            .join(ProdutoModel, CargaModel.produto_id == ProdutoModel.id)
            .join(BitolaModel, CargaModel.bitola_id == BitolaModel.id)
            .filter(
                RegistroOperacionalModel.deletado.is_(False),
                RegistroOperacionalModel.ativo.is_(True),
            )
        )

        if data_inicio and data_fim:
            query = query.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket.between(
                    data_inicio, data_fim
                ),
            )

        elif data_inicio:
            query = query.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket >= data_inicio,
            )
        elif data_fim:
            query = query.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket <= data_fim,
            )

        if cliente:
            query = query.filter(ClienteModel.identificacao.ilike(f"%{cliente}%"))

        if numero_nf:
            query = query.filter(
                or_(                     
                    RegistroOperacionalModel.numero_nota_fiscal.ilike(f"%{numero_nf}%"),
                    RegistroOperacionalModel.numero_nota_fiscal_excessao.ilike(f"%{numero_nf}%"),                     
                    RegistroOperacionalModel.numero_nota_fiscal_estorno.ilike(f"%{numero_nf}%"),                 
                )     
            )

        if status_nf_complementar:
            query = query.filter(
                RegistroOperacionalModel.status_emissao_nf_complementar_id
                == status_nf_complementar
            )

        if produto:
            query = query.filter(ProdutoModel.nome.ilike(f"%{produto}%"))

        if bitola:
            query = query.filter(BitolaModel.bitola.ilike(f"%{bitola}%"))

        if motorista:
            query = query.filter(MotoristaModel.nome_completo.ilike(f"%{motorista}%"))

        if transportadora:
            query = query.outerjoin(
                TransportadoraModel,
                or_(
                    CargaModel.transportadora_id == TransportadoraModel.id,
                )
            ).filter(
                TransportadoraModel.identificacao.ilike(f"%{transportadora}%")
            )

        if fornecedor:
            query = query.filter(
                or_(
                    CargaModel.fornecedor.has(
                        FornecedorModel.identificacao.ilike(f"%{fornecedor}%")
                    ),
                    CargaModel.floresta.has(
                        FlorestaModel.identificacao.ilike(f"%{fornecedor}%")
                    ),
                )
            )

        if placa:
            query = query.filter(VeiculoModel.placa_veiculo.ilike(f"%{placa}%"))

        resultados = []
        for registro, cliente in query.all():
            # Aqui garantimos que o relacionamento está sendo acessado corretamente
            produto = getattr(registro.solicitacao.produto, "nome", "Indefinido")

            resultados.append(
                {
                    "cliente": cliente.identificacao,
                    "produto": produto,
                    "registro": registro,
                }
            )

        resultados.sort(key=lambda x: (x["cliente"], x["produto"]))

        return resultados

    def obter_registros_unificado_cargas():
        """
        Retorna todos os registros unificados de cargas com informações de custos e receitas.
        
        Returns:
            list: Lista de dicionários com registros unificados incluindo custos de fornecedor, frete e extração
        """
        q = (
            db.session.query(
                RegistroOperacionalModel,
                FornecedorModel,
                FlorestaModel,
                FornecedorPagarModel,
                FretePagarModel,
                ExtratorPagarModel,
                ClienteModel,
                ProdutoModel,
                BitolaModel,
                VeiculoModel,
                MotoristaModel,
            )
            .join(CargaModel, RegistroOperacionalModel.solicitacao)
            .join(ClienteModel, CargaModel.cliente)
            .join(VeiculoModel, CargaModel.veiculo)
            .join(MotoristaModel, CargaModel.motorista)
            .join(ProdutoModel, CargaModel.produto)
            .join(BitolaModel, CargaModel.bitola)
            .outerjoin(FornecedorModel, CargaModel.fornecedor)
            .outerjoin(FlorestaModel, CargaModel.floresta)
            .outerjoin(FornecedorPagarModel, FornecedorPagarModel.solicitacao_id == CargaModel.id)
            .outerjoin(FretePagarModel, FretePagarModel.solicitacao_id == CargaModel.id)
            .outerjoin(ExtratorPagarModel, ExtratorPagarModel.solicitacao_id == CargaModel.id)
            .filter(
                RegistroOperacionalModel.deletado.is_(False),
                RegistroOperacionalModel.ativo.is_(True),
            )
            .order_by(
                case(
                    (FornecedorModel.identificacao != None, FornecedorModel.identificacao),
                    else_=FlorestaModel.identificacao,
                ),
                RegistroOperacionalModel.data_entrega_ticket.desc(),
            )
        )

        registros = []
        vistos = set()

        for (
            registro,
            forn,
            flor,
            pag_forn,
            pag_frete,
            pag_ext,
            cli,
            prod,
            bit,
            vei,
            mot,
        ) in q.all():
            chave = (registro.id, mot.id, vei.id)
            if chave in vistos:
                continue
            vistos.add(chave)

            carga = registro.solicitacao
            transp = carga.transportadora_exibicao
            nome_transp = transp.identificacao if transp else "Indefinido"
            origem_nome = forn.identificacao if forn else (flor.identificacao if flor else "Indefinido")
            peso = registro.peso_liquido_ticket or 0
            custo_fornecedor = pag_forn.valor_total_a_pagar_100 if pag_forn else 0
            custo_frete = pag_frete.valor_total_a_pagar_100 if pag_frete else 0
            custo_extracao = pag_ext.valor_total_a_pagar_100 if pag_ext else 0
            total_pagar = custo_fornecedor + custo_frete + custo_extracao
            total_receber = registro.valor_total_nota_100 or 0
            diferenca = total_receber - total_pagar

            registros.append({
                "registro": registro,
                "origem": origem_nome,
                "cliente": cli.identificacao if cli else "Indefinido",
                "transportadora": nome_transp,
                "produto": prod.nome if prod else "Indefinido",
                "bitola": bit.bitola if bit else "",
                "placa": vei.placa_veiculo if vei else "",
                "motorista": mot.nome_completo if mot else "",
                "valor_por_ton": (custo_fornecedor / peso) if peso else 0,
                "custo_fornecedor": custo_fornecedor,
                "custo_frete": custo_frete,
                "valor_frete_ton": (custo_frete / peso) if peso else 0,
                "custo_extracao": custo_extracao,
                "total_pagar": total_pagar,
                "total_receber": total_receber,
                "diferenca": diferenca,
            })

        return registros

    def filtrar_registros_unificado_cargas(
        data_inicio=None,
        data_fim=None,
        cliente=None,
        numero_nf=None,
        placa=None,
        motorista=None,
        transportadora=None,
        fornecedor=None,
        produto=None,
        bitola=None,
        statusPagamentoCarga=None
    ):
        """
        Filtra e retorna registros unificados de cargas com informações de custos e receitas.
        
        Args:
            data_inicio (date, optional): Data inicial do filtro
            data_fim (date, optional): Data final do filtro
            cliente (str, optional): Nome do cliente
            numero_nf (str, optional): Número da nota fiscal
            placa (str, optional): Placa do veículo
            motorista (str, optional): Nome do motorista
            transportadora (str, optional): Nome da transportadora
            fornecedor (str, optional): Nome do fornecedor ou floresta
            produto (str, optional): Nome do produto
            bitola (str, optional): Bitola
            statusPagamentoCarga (int, optional): Status de pagamento da carga
        
        Returns:
            list: Lista de dicionários com registros filtrados e unificados
        """
        if not data_inicio or not data_fim:
            data_inicio = date.today() - timedelta(days=30)
            data_fim = date.today()

        q = (
            db.session.query(
                RegistroOperacionalModel,
                FornecedorModel,
                FlorestaModel,
                FornecedorPagarModel,
                FretePagarModel,
                ExtratorPagarModel,
                ClienteModel,
                ProdutoModel,
                BitolaModel,
                VeiculoModel,
                MotoristaModel,
            )
            .join(CargaModel, RegistroOperacionalModel.solicitacao)
            .join(ClienteModel, CargaModel.cliente)
            .join(VeiculoModel, CargaModel.veiculo)
            .join(MotoristaModel, CargaModel.motorista)
            .join(ProdutoModel, CargaModel.produto)
            .join(BitolaModel, CargaModel.bitola)
            .outerjoin(FornecedorModel, CargaModel.fornecedor)
            .outerjoin(FlorestaModel, CargaModel.floresta)
            .outerjoin(FornecedorPagarModel, FornecedorPagarModel.solicitacao_id == CargaModel.id)
            .outerjoin(FretePagarModel, FretePagarModel.solicitacao_id == CargaModel.id)
            .outerjoin(ExtratorPagarModel, ExtratorPagarModel.solicitacao_id == CargaModel.id)
            .filter(
                RegistroOperacionalModel.deletado.is_(False),
                RegistroOperacionalModel.ativo.is_(True),
            )
            .order_by(
                case(
                    (FornecedorModel.identificacao != None, FornecedorModel.identificacao),
                    else_=FlorestaModel.identificacao,
                ),
                desc(RegistroOperacionalModel.data_entrega_ticket),
            )
        )

        if data_inicio and data_fim:
            q = q.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket.between(data_inicio, data_fim),
            )
        elif data_inicio:
            q = q.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket >= data_inicio,
            )
        elif data_fim:
            q = q.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket <= data_fim,
            )

        if cliente:
            q = q.filter(ClienteModel.identificacao.ilike(f"%{cliente}%"))
            
        if numero_nf:
            q = q.filter(or_(
                RegistroOperacionalModel.numero_nota_fiscal.ilike(f"%{numero_nf}%"),
                RegistroOperacionalModel.numero_nota_fiscal_excessao.ilike(f"%{numero_nf}%"),
                RegistroOperacionalModel.numero_nota_fiscal_estorno.ilike(f"%{numero_nf}%"),
            ))
            
        if produto:
            q = q.filter(ProdutoModel.nome.ilike(f"%{produto}%"))
            
        if bitola:
            q = q.filter(BitolaModel.bitola.ilike(f"%{bitola}%"))
            
        if motorista:
            q = q.filter(MotoristaModel.nome_completo.ilike(f"%{motorista}%"))
            
        if placa:
            q = q.filter(VeiculoModel.placa_veiculo.ilike(f"%{placa}%"))
            
        if fornecedor:
            q = q.filter(or_(
                CargaModel.fornecedor.has(FornecedorModel.identificacao.ilike(f"%{fornecedor}%")),
                CargaModel.floresta.has(FlorestaModel.identificacao.ilike(f"%{fornecedor}%")),
            ))
        
        if statusPagamentoCarga and statusPagamentoCarga != "":
            q = q.join(SituacaoPagamentoModel, RegistroOperacionalModel.situacao).filter(SituacaoPagamentoModel.id == statusPagamentoCarga)

        registros = []
        vistos = set()

        for (
            registro,
            forn,
            flor,
            pag_forn,
            pag_frete,
            pag_ext,
            cli,
            prod,
            bit,
            vei,
            mot,
        ) in q.all():
            chave = (registro.id, mot.id, vei.id)
            if chave in vistos:
                continue
            vistos.add(chave)

            carga = registro.solicitacao
            transp = carga.transportadora_exibicao or mot.transportadora
            nome_transp = transp.identificacao if transp else "Indefinido"
            
            # Filtro especial de transportadora aplicado após a query
            if transportadora and transportadora.lower() not in nome_transp.lower():
                continue

            origem_nome = forn.identificacao if forn else (flor.identificacao if flor else "Indefinido")
            peso = registro.peso_liquido_ticket or 0
            custo_fornecedor = pag_forn.valor_total_a_pagar_100 if pag_forn else 0
            custo_frete = pag_frete.valor_total_a_pagar_100 if pag_frete else 0
            custo_extracao = pag_ext.valor_total_a_pagar_100 if pag_ext else 0
            total_pagar = custo_fornecedor + custo_frete + custo_extracao
            total_receber = registro.valor_total_nota_100 or 0
            diferenca = total_receber - total_pagar

            registros.append({
                "registro": registro,
                "origem": origem_nome,
                "cliente": cli.identificacao if cli else "Indefinido",
                "transportadora": nome_transp,
                "produto": prod.nome if prod else "Indefinido",
                "bitola": bit.bitola if bit else "",
                "placa": vei.placa_veiculo if vei else "",
                "motorista": mot.nome_completo if mot else "",
                "valor_por_ton": (custo_fornecedor / peso) if peso else 0,
                "custo_fornecedor": custo_fornecedor,
                "custo_frete": custo_frete,
                "valor_frete_ton": (custo_frete / peso) if peso else 0,
                "custo_extracao": custo_extracao,
                "total_pagar": total_pagar,
                "total_receber": total_receber,
                "diferenca": diferenca,
            })

        return registros
    
    def obter_registros_carga_fornecedor_floresta_produto():
        """
        Retorna todos os registros de carga agrupados por fornecedor/floresta e produto.
        
        Returns:
            list: Lista de dicionários com registros agrupados por origem, cliente, produto e bitola
        """

        data_inicio = date.today() - timedelta(days=30)
        data_fim = date.today()

        query = (
            db.session.query(
                RegistroOperacionalModel,
                ClienteModel,
                FornecedorModel,
                FlorestaModel,
                FornecedorPagarModel,
            )
            .join(CargaModel, RegistroOperacionalModel.solicitacao)
            .join(ClienteModel, CargaModel.cliente)
            .join(VeiculoModel, CargaModel.veiculo)
            .join(MotoristaModel, CargaModel.motorista)
            .join(ProdutoModel, CargaModel.produto)
            .join(BitolaModel, CargaModel.bitola)
            .outerjoin(FornecedorModel, CargaModel.fornecedor)
            .outerjoin(FlorestaModel, CargaModel.floresta)
            .outerjoin(
                FornecedorPagarModel,
                FornecedorPagarModel.solicitacao_id == CargaModel.id,
            )
            .filter(
                RegistroOperacionalModel.deletado.is_(False),
                RegistroOperacionalModel.ativo.is_(True),
            )
            .order_by(
                case(
                    (FornecedorModel.identificacao != None, FornecedorModel.identificacao),
                    else_=FlorestaModel.identificacao,
                ),
                RegistroOperacionalModel.id.desc(),
            )
        )

        if data_inicio and data_fim:
            query = query.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket.between(
                    data_inicio, data_fim
                ),
            )

        elif data_inicio:
            query = query.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket >= data_inicio,
            )
        elif data_fim:
            query = query.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket <= data_fim,
            )

        registros = []
        for registro, cliente, fornecedor, floresta, fornecedor_pagar in query.all():
            origem = "Indefinido"
            if fornecedor and fornecedor.identificacao:
                origem = fornecedor.identificacao
            elif floresta and floresta.identificacao:
                origem = floresta.identificacao

            produto = getattr(registro.solicitacao.produto, "nome", "Indefinido")
            bitola = getattr(registro.solicitacao.bitola, "bitola", "")
            valor_pagar = (
                fornecedor_pagar.valor_total_a_pagar_100
                if fornecedor_pagar and fornecedor_pagar.valor_total_a_pagar_100
                else 0
            )

            registros.append({
                "origem": origem,
                "cliente": cliente,
                "produto": produto,
                "bitola": bitola,
                "valor_pagar": valor_pagar,
                "registro": registro,
                "valor_ton": (
                    (int(valor_pagar) / registro.peso_liquido_ticket)
                    if registro.peso_liquido_ticket > 0
                    else 0
                ),
            })
            
        return registros

    def filtrar_registros_carga_fornecedor_floresta_produto(
        data_inicio=None,
        data_fim=None,
        cliente=None,
        numero_nf=None,
        placa=None,
        motorista=None,
        transportadora=None,
        fornecedor=None,
        produto=None,
        bitola=None,
    ):
        """
        Filtra e retorna registros de carga agrupados por fornecedor/floresta e produto.
        
        Args:
            data_inicio (date, optional): Data inicial do filtro
            data_fim (date, optional): Data final do filtro
            cliente (str, optional): Nome do cliente
            numero_nf (str, optional): Número da nota fiscal
            placa (str, optional): Placa do veículo
            motorista (str, optional): Nome do motorista
            transportadora (str, optional): Nome da transportadora
            fornecedor (str, optional): Nome do fornecedor ou floresta
            produto (str, optional): Nome do produto
            bitola (str, optional): Bitola
        
        Returns:
            list: Lista de dicionários com registros filtrados e agrupados
        """
        if not data_inicio or not data_fim:
            data_inicio = date.today() - timedelta(days=30)
            data_fim = date.today()

        query = (
            db.session.query(
                RegistroOperacionalModel,
                ClienteModel,
                FornecedorModel,
                FlorestaModel,
                FornecedorPagarModel,
            )
            .join(CargaModel, RegistroOperacionalModel.solicitacao)
            .join(ClienteModel, CargaModel.cliente)
            .join(VeiculoModel, CargaModel.veiculo)
            .join(MotoristaModel, CargaModel.motorista)
            .join(ProdutoModel, CargaModel.produto)
            .join(BitolaModel, CargaModel.bitola)
            .outerjoin(FornecedorModel, CargaModel.fornecedor)
            .outerjoin(FlorestaModel, CargaModel.floresta)
            .outerjoin(
                FornecedorPagarModel,
                FornecedorPagarModel.solicitacao_id == CargaModel.id,
            )
            .filter(
                RegistroOperacionalModel.deletado.is_(False),
                RegistroOperacionalModel.ativo.is_(True),
            )
        )

        if data_inicio and data_fim:
            query = query.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket.between(data_inicio, data_fim),
            )
        elif data_inicio:
            query = query.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket >= data_inicio,
            )
        elif data_fim:
            query = query.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket <= data_fim,
            )

        if cliente:
            query = query.filter(ClienteModel.identificacao.ilike(f"%{cliente}%"))

        if numero_nf:
            query = query.filter(
                or_(
                    RegistroOperacionalModel.numero_nota_fiscal.ilike(f"%{numero_nf}%"),
                    RegistroOperacionalModel.numero_nota_fiscal_excessao.ilike(f"%{numero_nf}%"),
                    RegistroOperacionalModel.numero_nota_fiscal_estorno.ilike(f"%{numero_nf}%"),
                )
            )

        if produto:
            query = query.filter(ProdutoModel.nome.ilike(f"%{produto}%"))

        if bitola:
            query = query.filter(BitolaModel.bitola.ilike(f"%{bitola}%"))

        if motorista:
            query = query.filter(MotoristaModel.nome_completo.ilike(f"%{motorista}%"))

        if transportadora:
            query = query.outerjoin(
                TransportadoraModel,
                or_(
                    CargaModel.transportadora_id == TransportadoraModel.id,
                )
            ).filter(
                TransportadoraModel.identificacao.ilike(f"%{transportadora}%")
            )

        if fornecedor:
            query = query.filter(
                or_(
                    CargaModel.fornecedor.has(
                        FornecedorModel.identificacao.ilike(f"%{fornecedor}%")
                    ),
                    CargaModel.floresta.has(
                        FlorestaModel.identificacao.ilike(f"%{fornecedor}%")
                    ),
                )
            )

        if placa:
            query = query.filter(VeiculoModel.placa_veiculo.ilike(f"%{placa}%"))

        query = query.order_by(
            case(
                (FornecedorModel.identificacao != None, FornecedorModel.identificacao),
                else_=FlorestaModel.identificacao,
            ),
            desc(RegistroOperacionalModel.data_entrega_ticket),
        )

        registros = []
        for registro, cliente, fornecedor, floresta, fornecedor_pagar in query.all():
            origem = "Indefinido"
            if fornecedor and fornecedor.identificacao:
                origem = fornecedor.identificacao
            elif floresta and floresta.identificacao:
                origem = floresta.identificacao

            produto = getattr(registro.solicitacao.produto, "nome", "Indefinido")
            bitola = getattr(registro.solicitacao.bitola, "bitola", "")
            valor_pagar = (
                fornecedor_pagar.valor_total_a_pagar_100
                if fornecedor_pagar and fornecedor_pagar.valor_total_a_pagar_100
                else 0
            )

            registros.append({
                "origem": origem,
                "fornecedor_obj": fornecedor or floresta,  # Objeto do fornecedor/floresta para acessar dados bancários
                "cliente": cliente,
                "transportadora": registro.solicitacao.transportadora_exibicao.identificacao if registro.solicitacao.transportadora_exibicao else "Indefinido",
                "produto": produto,
                "bitola": bitola,
                "valor_pagar": valor_pagar,
                "registro": registro,
                "valor_ton": (
                    (int(valor_pagar) / registro.peso_liquido_ticket)
                    if registro.peso_liquido_ticket > 0
                    else 0
                ),
            })
            
        return registros

    def obter_registros_carga_transportadora():
        """
        Retorna todos os registros de carga agrupados por transportadora.
        
        Returns:
            list: Lista de dicionários com registros agrupados por transportadora, produto e origem
        """
        data_inicio = date.today() - timedelta(days=30)
        data_fim = date.today()

        query = (
            db.session.query(
                RegistroOperacionalModel,
                ClienteModel,
                FornecedorModel,
                FlorestaModel,
                FretePagarModel,
            )
            .join(CargaModel, RegistroOperacionalModel.solicitacao)
            .join(ClienteModel, CargaModel.cliente)
            .join(VeiculoModel, CargaModel.veiculo)
            .join(MotoristaModel, CargaModel.motorista)
            .join(ProdutoModel, CargaModel.produto)
            .join(BitolaModel, CargaModel.bitola)
            .outerjoin(FornecedorModel, CargaModel.fornecedor)
            .outerjoin(FlorestaModel, CargaModel.floresta)
            .outerjoin(
                FretePagarModel,
                FretePagarModel.solicitacao_id == CargaModel.id,
            )
            .filter(
                RegistroOperacionalModel.deletado.is_(False),
                RegistroOperacionalModel.ativo.is_(True),
            )
            .order_by(
                RegistroOperacionalModel.id.desc()
            )
        )

        if data_inicio and data_fim:
            query = query.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket.between(data_inicio, data_fim),
            )
        elif data_inicio:
            query = query.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket >= data_inicio,
            )
        elif data_fim:
            query = query.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket <= data_fim,
            )

        registros = []
        for registro, cliente, fornecedor, floresta, frete_pagar in query.all():
            origem = "Indefinido"
            if fornecedor and fornecedor.identificacao:
                origem = fornecedor.identificacao
            elif floresta and floresta.identificacao:
                origem = floresta.identificacao

            carga = registro.solicitacao
            mot = carga.motorista
            transp = carga.transportadora_exibicao or mot.transportadora
            transportadora_nome = transp.identificacao if transp else "Indefinido"

            produto = carga.produto
            bitola_id = carga.bitola_id
            bitola = carga.bitola

            valor_frete = 0
            if transp:
                rota = (
                    db.session.query(RotaFreteModel)
                    .filter(
                        RotaFreteModel.cliente_id == carga.cliente_id,
                        RotaFreteModel.transportadora_id == transp.id,
                        or_(
                            RotaFreteModel.fornecedor_id == carga.fornecedor_id,
                            RotaFreteModel.floresta_id == carga.floresta_id,
                        ),
                    )
                    .first()
                )
            else:
                rota = None

            if rota and produto:
                nome = produto.nome.lower()
                if nome.startswith("eucalipto"):
                    if rota.euca_bitola_1_id == bitola_id:
                        valor_frete = rota.euca_preco_custo_frete_bitola_1_100
                    elif rota.euca_bitola_2_id == bitola_id:
                        valor_frete = rota.euca_preco_custo_frete_bitola_2_100
                    elif rota.euca_bitola_3_id == bitola_id:
                        valor_frete = rota.euca_preco_custo_frete_bitola_3_100
                    elif rota.euca_bitola_4_id == bitola_id:
                        valor_frete = rota.euca_preco_custo_frete_bitola_4_100
                elif nome.startswith("pinus"):
                    if rota.pinus_bitola_1_id == bitola_id:
                        valor_frete = rota.pinus_preco_custo_frete_bitola_1_100
                    elif rota.pinus_bitola_2_id == bitola_id:
                        valor_frete = rota.pinus_preco_custo_frete_bitola_2_100
                    elif rota.pinus_bitola_3_id == bitola_id:
                        valor_frete = rota.pinus_preco_custo_frete_bitola_3_100
                    elif rota.pinus_bitola_4_id == bitola_id:
                        valor_frete = rota.pinus_preco_custo_frete_bitola_4_100
                    elif rota.pinus_bitola_5_id == bitola_id:
                        valor_frete = rota.pinus_preco_custo_frete_bitola_5_100
                elif nome.startswith("Biomassa"):
                    if rota.bio_bitola_5_id == bitola_id:
                        valor_frete = rota.bio_preco_custo_frete_bitola_5_100

            valor_total = 0
            if registro.peso_liquido_ticket is not None:
                valor_total = float(valor_frete) * registro.peso_liquido_ticket

            valor_total_frete = (
                int(frete_pagar.valor_total_a_pagar_100)
                if frete_pagar and frete_pagar.valor_total_a_pagar_100 is not None
                else 0
            )

            registros.append({
                "origem": origem,
                "cliente": cliente,
                "transportadora": transportadora_nome,
                "produto": produto.nome if produto else "Indefinido",
                "bitola": bitola.bitola if bitola else "",
                "valor_frete": (
                    frete_pagar.valor_total_a_pagar_100
                    if frete_pagar and frete_pagar.valor_total_a_pagar_100
                    else 0
                ),
                "valor_frete_por_produto": (
                    float(f"{int(valor_total_frete) / registro.peso_liquido_ticket:.2f}")
                    if valor_total_frete > 0 and registro.peso_liquido_ticket > 0
                    else 0
                ),
                "registro": registro,
            })

        registros.sort(
            key=lambda x: (x["transportadora"], x["produto"], x["valor_frete"])
        )
        return registros

    def filtrar_registros_carga_transportadora(
        data_inicio=None,
        data_fim=None,
        cliente=None,
        numero_nf=None,
        placa=None,
        motorista=None,
        transportadora=None,
        fornecedor=None,
        produto=None,
        bitola=None,
        origem=None
    ):
        """
        Filtra e retorna registros de carga agrupados por transportadora.
        
        Args:
            data_inicio (date, optional): Data inicial do filtro
            data_fim (date, optional): Data final do filtro
            cliente (str, optional): Nome do cliente
            numero_nf (str, optional): Número da nota fiscal
            placa (str, optional): Placa do veículo
            motorista (str, optional): Nome do motorista
            transportadora (str, optional): Nome da transportadora
            fornecedor (str, optional): Nome do fornecedor
            produto (str, optional): Nome do produto
            bitola (str, optional): Bitola
            origem (str, optional): Nome da origem (fornecedor ou floresta)
        
        Returns:
            list: Lista de dicionários com registros filtrados e agrupados
        """
        if not data_inicio and not data_fim:
            data_inicio = date.today() - timedelta(days=30)
            data_fim = date.today()

        query = (
            db.session.query(
                RegistroOperacionalModel,
                ClienteModel,
                FornecedorModel,
                FlorestaModel,
                FretePagarModel,
            )
            .join(CargaModel, RegistroOperacionalModel.solicitacao)
            .join(ClienteModel, CargaModel.cliente)
            .join(VeiculoModel, CargaModel.veiculo)
            .join(MotoristaModel, CargaModel.motorista)
            .join(ProdutoModel, CargaModel.produto)
            .join(BitolaModel, CargaModel.bitola)
            .outerjoin(FornecedorModel, CargaModel.fornecedor)
            .outerjoin(FlorestaModel, CargaModel.floresta)
            .outerjoin(
                FretePagarModel,
                FretePagarModel.solicitacao_id == CargaModel.id,
            )
            .filter(
                RegistroOperacionalModel.deletado.is_(False),
                RegistroOperacionalModel.ativo.is_(True),
            )
        )

        if data_inicio and data_fim:
            query = query.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket.between(data_inicio, data_fim),
            )
        elif data_inicio:
            query = query.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket >= data_inicio,
            )
        elif data_fim:
            query = query.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket <= data_fim,
            )

        if cliente:
            query = query.filter(ClienteModel.identificacao.ilike(f"%{cliente}%"))

        if numero_nf:
            query = query.filter(
                or_(
                    RegistroOperacionalModel.numero_nota_fiscal.ilike(f"%{numero_nf}%"),
                    RegistroOperacionalModel.numero_nota_fiscal_excessao.ilike(f"%{numero_nf}%"),
                    RegistroOperacionalModel.numero_nota_fiscal_estorno.ilike(f"%{numero_nf}%"),
                )
            )

        if produto:
            query = query.filter(ProdutoModel.nome.ilike(f"%{produto}%"))

        if bitola:
            query = query.filter(BitolaModel.bitola.ilike(f"%{bitola}%"))

        if motorista:
            query = query.filter(MotoristaModel.nome_completo.ilike(f"%{motorista}%"))

        if transportadora:
            print(transportadora)
            query = query.outerjoin(
                TransportadoraModel,
                CargaModel.transportadora_id == TransportadoraModel.id,
            ).filter(
                TransportadoraModel.identificacao.ilike(f"%{transportadora}%")
            )

        if fornecedor:
            query = query.filter(
                or_(
                    CargaModel.fornecedor.has(
                        FornecedorModel.identificacao.ilike(f"%{fornecedor}%")
                    ),
                    CargaModel.floresta.has(
                        FlorestaModel.identificacao.ilike(f"%{fornecedor}%")
                    ),
                )
            )

        if origem:
            query = query.filter(or_(
                FornecedorModel.identificacao.ilike(f"%{origem}%"),
                FlorestaModel.identificacao.ilike(f"%{origem}%"),
            ))

        if placa:
            query = query.filter(VeiculoModel.placa_veiculo.ilike(f"%{placa}%"))

        query = query.order_by(
            RegistroOperacionalModel.id.desc()
        )

        registros = []
        for registro, cliente, fornecedor, floresta, frete_pagar in query.all():
            origem = "Indefinido"
            if fornecedor and fornecedor.identificacao:
                origem = fornecedor.identificacao
            elif floresta and floresta.identificacao:
                origem = floresta.identificacao

            carga = registro.solicitacao
            mot = carga.motorista
            transp = carga.transportadora_exibicao or mot.transportadora
            transportadora_nome = transp.identificacao if transp else "Indefinido"

            produto = carga.produto
            bitola_id = carga.bitola_id
            bitola = carga.bitola

            valor_frete = 0
            if transp:
                rota = (
                    db.session.query(RotaFreteModel)
                    .filter(
                        RotaFreteModel.cliente_id == carga.cliente_id,
                        RotaFreteModel.transportadora_id == transp.id,
                        or_(
                            RotaFreteModel.fornecedor_id == carga.fornecedor_id,
                            RotaFreteModel.floresta_id == carga.floresta_id,
                        ),
                    )
                    .first()
                )
            else:
                rota = None

            if rota and produto:
                nome = produto.nome.lower()
                if nome.startswith("eucalipto"):
                    if rota.euca_bitola_1_id == bitola_id:
                        valor_frete = rota.euca_preco_custo_frete_bitola_1_100
                    elif rota.euca_bitola_2_id == bitola_id:
                        valor_frete = rota.euca_preco_custo_frete_bitola_2_100
                    elif rota.euca_bitola_3_id == bitola_id:
                        valor_frete = rota.euca_preco_custo_frete_bitola_3_100
                    elif rota.euca_bitola_4_id == bitola_id:
                        valor_frete = rota.euca_preco_custo_frete_bitola_4_100
                elif nome.startswith("pinus"):
                    if rota.pinus_bitola_1_id == bitola_id:
                        valor_frete = rota.pinus_preco_custo_frete_bitola_1_100
                    elif rota.pinus_bitola_2_id == bitola_id:
                        valor_frete = rota.pinus_preco_custo_frete_bitola_2_100
                    elif rota.pinus_bitola_3_id == bitola_id:
                        valor_frete = rota.pinus_preco_custo_frete_bitola_3_100
                    elif rota.pinus_bitola_4_id == bitola_id:
                        valor_frete = rota.pinus_preco_custo_frete_bitola_4_100
                    elif rota.pinus_bitola_5_id == bitola_id:
                        valor_frete = rota.pinus_preco_custo_frete_bitola_5_100
                elif nome.startswith("Biomassa"):
                    if rota.bio_bitola_5_id == bitola_id:
                        valor_frete = rota.bio_preco_custo_frete_bitola_5_100

            valor_total = 0
            if registro.peso_liquido_ticket is not None:
                valor_total = float(valor_frete) * registro.peso_liquido_ticket

            valor_total_frete = (
                int(frete_pagar.valor_total_a_pagar_100)
                if frete_pagar and frete_pagar.valor_total_a_pagar_100 is not None
                else 0
            )

            registros.append({
                "origem": origem,
                "cliente": cliente,
                "transportadora": transportadora_nome,
                "transportadora_obj": transp,  # Objeto da transportadora para acessar dados bancários
                "fornecedor": fornecedor.identificacao if fornecedor else (floresta.identificacao if floresta else "Indefinido"),
                "produto": produto.nome if produto else "Indefinido",
                "bitola": bitola.bitola if bitola else "",
                "valor_frete": (
                    frete_pagar.valor_total_a_pagar_100
                    if frete_pagar and frete_pagar.valor_total_a_pagar_100
                    else 0
                ),
                "valor_frete_por_produto": (
                    float(f"{int(valor_total_frete) / registro.peso_liquido_ticket:.2f}")
                    if valor_total_frete > 0 and registro.peso_liquido_ticket > 0
                    else 0
                ),
                "registro": registro,
            })

        registros.sort(
            key=lambda x: (x["transportadora"], x["produto"], x["valor_frete"])
        )
        return registros

    def relatorio_controle_complementar(
        data_inicio=None,
        data_fim=None,
        produto=None,
        bitola=None,
        transportadora=None,
        motorista=None,
        placa=None,
        cliente=None,
        numero_nf=None,
    ):
        """
        Gera relatório de controle complementar filtrando por datas, produto, bitola, transportadora, motorista, placa, cliente e número da nota fiscal.
        
        Args:
            data_inicio (date, optional): Data inicial do filtro
            data_fim (date, optional): Data final do filtro
            produto (str, optional): Nome do produto
            bitola (str, optional): Bitola
            transportadora (str, optional): Nome da transportadora
            motorista (str, optional): Nome do motorista
            placa (str, optional): Placa do veículo
            cliente (str, optional): Nome do cliente
            numero_nf (str, optional): Número da nota fiscal
        Returns:
            list: Lista de registros filtrados para o relatório
        """

        if not data_inicio and not data_fim:
            data_inicio = date.today() - timedelta(days=30)
            data_fim = date.today()

        query = (
            RegistroOperacionalModel.query.join(RegistroOperacionalModel.solicitacao)
            .join(CargaModel.cliente)
            .join(CargaModel.veiculo)
            .join(CargaModel.produto)
            .join(CargaModel.bitola)
            .join(VeiculoModel.transportadora)
            .join(CargaModel.motorista)
            .filter(
                RegistroOperacionalModel.deletado == False,
                RegistroOperacionalModel.ativo == True,
            )
        )

        if not data_inicio and not data_fim:
            data_inicio = date.today() - timedelta(days=30)
            data_fim = date.today()

            query = query.filter(
                or_(
                    RegistroOperacionalModel.destinatario_data_emissao.is_(None),
                    and_(
                        RegistroOperacionalModel.destinatario_data_emissao
                        >= data_inicio,
                        RegistroOperacionalModel.destinatario_data_emissao <= data_fim,
                    ),
                )
            )
        else:
            if data_inicio:
                query = query.filter(
                    RegistroOperacionalModel.destinatario_data_emissao >= data_inicio
                )
            if data_fim:
                query = query.filter(
                    RegistroOperacionalModel.destinatario_data_emissao <= data_fim
                )

        if produto:
            query = query.filter(ProdutoModel.nome.ilike(f"%{produto}%"))

        if bitola:
            query = query.filter(BitolaModel.bitola.ilike(f"%{bitola}%"))

        if cliente:
            query = query.filter(ClienteModel.identificacao.ilike(f"%{cliente}%"))

        if numero_nf:
            query = query.filter(
                or_(                     
                    RegistroOperacionalModel.numero_nota_fiscal.ilike(f"%{numero_nf}%"),
                    RegistroOperacionalModel.numero_nota_fiscal_excessao.ilike(f"%{numero_nf}%"),                     
                    RegistroOperacionalModel.numero_nota_fiscal_estorno.ilike(f"%{numero_nf}%"),                 
                )     
            )

        if motorista:
            query = query.filter(MotoristaModel.nome_completo.ilike(f"%{motorista}%"))

        if transportadora:
            query = query.filter(
                TransportadoraModel.identificacao.ilike(f"%{transportadora}%")
            )

        if placa:
            query = query.filter(VeiculoModel.placa_veiculo.ilike(f"%{placa}%"))

        return query.order_by(
            desc(RegistroOperacionalModel.destinatario_data_emissao)
        ).all()
    
    def obter_registros_operacionais(qtd_itens_por_pagina=500):
        """
        Retorna todos os registros operacionais ativos com paginação.
        
        Args:
            qtd_itens_por_pagina (int, optional): Quantidade de itens por página. Default: 500
        
        Returns:
            Pagination: Objeto de paginação com registros operacionais
        """
        
        q = (
            db.session.query(RegistroOperacionalModel)
            .join(CargaModel, RegistroOperacionalModel.solicitacao)
            .join(MotoristaModel, CargaModel.motorista)
            .join(ClienteModel, CargaModel.cliente)
            .outerjoin(FornecedorModel, CargaModel.fornecedor)
            .outerjoin(FlorestaModel, CargaModel.floresta)
            .join(VeiculoModel, CargaModel.veiculo)
            .join(ProdutoModel, CargaModel.produto)
            .join(BitolaModel, CargaModel.bitola)
            .filter(
                RegistroOperacionalModel.deletado.is_(False),
                RegistroOperacionalModel.ativo.is_(True),
            )
            .order_by(
                case(
                    ((CargaModel.ticket_emitido.is_(False)) | (CargaModel.ticket_emitido.is_(None)), 0),
                    else_=1,
                ),
                desc(RegistroOperacionalModel.data_cadastro),
            )
        )

        page = request.args.get("page", default=1, type=int)
        per_page = qtd_itens_por_pagina

        return q.paginate(page=page, per_page=per_page, error_out=False)
    
    def filtrar_listagem_registros_operacionais(
        data_inicio=None,
        data_fim=None,
        produto=None,
        bitola=None,
        transportadora=None,
        motorista=None,
        origem=None,
        placa=None,
        cliente=None,
        numero_nf=None,
        qtd_itens_por_pagina=500,
        debug_query=False
    ):
        """
        Filtra e retorna registros operacionais com paginação.
        
        Args:
            data_inicio (date, optional): Data inicial do filtro
            data_fim (date, optional): Data final do filtro
            produto (str, optional): Nome do produto
            bitola (str, optional): Bitola
            transportadora (str, optional): Nome da transportadora
            motorista (str, optional): Nome do motorista
            origem (str, optional): Nome da origem (fornecedor ou floresta)
            placa (str, optional): Placa do veículo
            cliente (str, optional): Nome do cliente
            numero_nf (str, optional): Número da nota fiscal
            qtd_itens_por_pagina (int, optional): Quantidade de itens por página. Default: 500
        
        Returns:
            Pagination: Objeto de paginação com registros filtrados
        """
        if not data_inicio and not data_fim:
            data_inicio = date.today() - timedelta(days=30)
            data_fim = date.today()

        q = (
            db.session.query(RegistroOperacionalModel)
            .join(CargaModel, RegistroOperacionalModel.solicitacao)
            .join(MotoristaModel, CargaModel.motorista)
            .join(ClienteModel, CargaModel.cliente)
            .outerjoin(FornecedorModel, CargaModel.fornecedor)
            .outerjoin(FlorestaModel, CargaModel.floresta)
            .join(VeiculoModel, CargaModel.veiculo)
            .join(ProdutoModel, CargaModel.produto)
            .join(BitolaModel, CargaModel.bitola)
            .filter(
                RegistroOperacionalModel.deletado.is_(False),
                RegistroOperacionalModel.ativo.is_(True),
            )
        )

        if data_inicio:
            q = q.filter(
                or_(
                    RegistroOperacionalModel.data_entrega_ticket.is_(None),
                    func.date(RegistroOperacionalModel.data_entrega_ticket) >= data_inicio
                )
            )
        if data_fim:
            q = q.filter(
                or_(
                    RegistroOperacionalModel.data_entrega_ticket.is_(None),
                    func.date(RegistroOperacionalModel.data_entrega_ticket) <= data_fim
                )
            )
        if cliente:
            q = q.filter(ClienteModel.identificacao.ilike(f"%{cliente}%"))
        if produto:
            q = q.filter(ProdutoModel.nome.ilike(f"%{produto}%"))
        if bitola:
            q = q.filter(BitolaModel.bitola.ilike(f"%{bitola}%"))
        if numero_nf:
            q = q.filter(or_(
                RegistroOperacionalModel.numero_nota_fiscal == numero_nf,  
                RegistroOperacionalModel.numero_nota_fiscal.ilike(f"%{numero_nf}%"),  
                RegistroOperacionalModel.numero_nota_fiscal_excessao == numero_nf,
                RegistroOperacionalModel.numero_nota_fiscal_excessao.ilike(f"%{numero_nf}%"),
                RegistroOperacionalModel.numero_nota_fiscal_ticket == numero_nf,
                RegistroOperacionalModel.numero_nota_fiscal_ticket.ilike(f"%{numero_nf}%"),
                RegistroOperacionalModel.numero_nota_fiscal_estorno == numero_nf,
                RegistroOperacionalModel.numero_nota_fiscal_estorno.ilike(f"%{numero_nf}%"),
            ))
        if motorista:
            q = q.filter(MotoristaModel.nome_completo.ilike(f"%{motorista}%"))
        if origem:
            q = q.filter(or_(
                FornecedorModel.identificacao.ilike(f"%{origem}%"),
                FlorestaModel.identificacao.ilike(f"%{origem}%"),
            ))
        if placa:
            q = q.filter(VeiculoModel.placa_veiculo.ilike(f"%{placa}%"))

        if transportadora:
            q = q.outerjoin(
                TransportadoraModel,
                CargaModel.transportadora_id == TransportadoraModel.id,
            ).filter(
                TransportadoraModel.identificacao.ilike(f"%{transportadora}%")
            )
        
        if debug_query:
            # Imprime a query SQL
            compiled = q.statement.compile(compile_kwargs={"literal_binds": True})
            print("Query SQL:")
            print(str(compiled))

        page = request.args.get("page", default=1, type=int)
        per_page = qtd_itens_por_pagina

        return q.paginate(page=page, per_page=per_page, error_out=False)

    def registros_carga_fornecedor_produto(
        data_inicio=None,
        data_fim=None,
        cliente=None,
        numero_nf=None,
        placa=None,
        motorista=None,
        transportadora=None,
        fornecedor=None,
        produto=None,
        bitola=None,
    ):
        if not data_inicio or not data_fim:
            data_inicio = date.today() - timedelta(days=30)
            data_fim = date.today()

        query = (
            db.session.query(
                RegistroOperacionalModel,
                FornecedorModel,
                FornecedorPagarModel,
            )
            .join(CargaModel, RegistroOperacionalModel.solicitacao)
            .join(ClienteModel, CargaModel.cliente)
            .join(VeiculoModel, CargaModel.veiculo)
            .join(MotoristaModel, CargaModel.motorista)
            .join(ProdutoModel, CargaModel.produto)
            .join(BitolaModel, CargaModel.bitola)
            .outerjoin(
                TransportadoraMotoristaAssocModel,
                and_(
                    TransportadoraMotoristaAssocModel.motorista_id == MotoristaModel.id,
                    TransportadoraMotoristaAssocModel.ativo.is_(True),
                    TransportadoraMotoristaAssocModel.deletado.is_(False),
                ),
            )
            .outerjoin(
                TransportadoraModel,
                or_(
                    TransportadoraModel.id == MotoristaModel.transportadora_id,
                    TransportadoraModel.id
                    == TransportadoraMotoristaAssocModel.transportadora_id,
                ),
            )
            .outerjoin(FornecedorModel, CargaModel.fornecedor)
            .outerjoin(
                FornecedorPagarModel,
                FornecedorPagarModel.solicitacao_id == CargaModel.id,
            )
            .filter(
                RegistroOperacionalModel.deletado.is_(False),
                RegistroOperacionalModel.ativo.is_(True),
            )
        )

        # Se datas forem fornecidas, aplica o filtro
        if data_inicio and data_fim:
            query = query.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket.between(
                    data_inicio, data_fim
                ),
            )
        elif data_inicio:
            query = query.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket >= data_inicio,
            )
        elif data_fim:
            query = query.filter(
                RegistroOperacionalModel.data_entrega_ticket.isnot(None),
                RegistroOperacionalModel.data_entrega_ticket <= data_fim,
            )

        if cliente:
            query = query.filter(ClienteModel.identificacao.ilike(f"%{cliente}%"))

        if numero_nf:
            query = query.filter(
                RegistroOperacionalModel.numero_nota_fiscal.ilike(f"%{numero_nf}%")
            )

        if produto:
            query = query.filter(ProdutoModel.nome.ilike(f"%{produto}%"))

        if bitola:
            query = query.filter(BitolaModel.bitola.ilike(f"%{bitola}%"))

        if motorista:
            query = query.filter(MotoristaModel.nome_completo.ilike(f"%{motorista}%"))

        if transportadora:
            query = query.filter(
                TransportadoraModel.identificacao.ilike(f"%{transportadora}%")
            )

        if fornecedor:
            query = query.filter(FornecedorModel.identificacao.ilike(f"%{fornecedor}%"))

        if placa:
            query = query.filter(VeiculoModel.placa_veiculo.ilike(f"%{placa}%"))

        # Ordenação
        query = query.order_by(
            case((FornecedorModel.identificacao == None, 1), else_=0),
            FornecedorModel.identificacao.asc(),
            RegistroOperacionalModel.id.desc(),
        )

        # Monta os registros
        registros = []
        for registro, fornecedor, fornecedor_pagar in query.all():
            origem = "Indefinido"
            if fornecedor and fornecedor.identificacao:
                origem = fornecedor.identificacao

            produto = getattr(registro.solicitacao.produto, "nome", "Indefinido")
            bitola = getattr(registro.solicitacao.bitola, "bitola", "")
            valor_pagar = (
                fornecedor_pagar.valor_total_a_pagar_100
                if fornecedor_pagar and fornecedor_pagar.valor_total_a_pagar_100
                else 0
            )

            registros.append(
                {
                    "origem": origem,
                    "produto": produto,
                    "bitola": bitola,
                    "valor_pagar": valor_pagar,
                    "registro": registro,
                }
            )
        return registros

    def obter_valor_total_a_receber():
        a_receber = RegistroOperacionalModel.query.filter(
            RegistroOperacionalModel.deletado == 0,
            RegistroOperacionalModel.ativo == 1,
            RegistroOperacionalModel.situacao_financeira_id != 3,
        ).all()

        return (
            sum(
                a.valor_total_nota_100 if a.valor_total_nota_100 else 0
                for a in a_receber
            )
            or 0
        )

    def obter_valor_total_a_receber_por_conta(id_conta=1):
        """
        Obter valor total a receber por conta (implementação simplificada temporariamente)
        TODO: Reimplementar usando novo sistema de conciliação
        """
        # Por enquanto, retornar os valores a receber não conciliados
        q = (
            db.session.query(
                func.coalesce(
                    func.sum(RegistroOperacionalModel.valor_total_nota_100), 0
                )
            )
            .filter(
                RegistroOperacionalModel.deletado == False,
                RegistroOperacionalModel.ativo == True,
                RegistroOperacionalModel.situacao_financeira_id != 3,  # não recebidos
            )
        )

        total_centavos = q.scalar() or 0
        return total_centavos

    def obter_valor_total_recebido():
        a_receber = RegistroOperacionalModel.query.filter(
            RegistroOperacionalModel.deletado == 0,
            RegistroOperacionalModel.ativo == 1,
            RegistroOperacionalModel.situacao_financeira_id == 3,
        ).all()

        return (
            sum(
                a.valor_total_nota_100 if a.valor_total_nota_100 else 0
                for a in a_receber
            )
            or 0
        )

    def obter_valor_total_recebido_por_conta(id_conta=1):
        """
        Obter valor total recebido por conta (implementação simplificada temporariamente)
        TODO: Reimplementar usando novo sistema de conciliação
        """
        # Por enquanto, retornar os valores já recebidos
        q = (
            db.session.query(
                func.coalesce(
                    func.sum(RegistroOperacionalModel.valor_total_nota_100), 0
                )
            )
            .filter(
                RegistroOperacionalModel.deletado == False,
                RegistroOperacionalModel.ativo == True,
                RegistroOperacionalModel.situacao_financeira_id == 3,  # recebidos
            )
        )

        total_centavos = q.scalar() or 0
        return total_centavos

    def criar_registro_carga_frf(
        solicitacao_nf_id,
        peso_ton_nf,
        destinatario_nome,
        destinatario_cnpj_cpf,
        valor_total_nota_100,
        transportador_nome,
        transportador_cnpj_cpf,
        placa_nf,
        motorista_nf,
        destinatario_data_emissao,
        carga_frf=True,
        situacao_financeira_id=2,
        ativo=True,
        numero_nota_fiscal='000000',
    ):
        """
        Cria um registro operacional de carga FRF com todos os campos relevantes da model.
        """
        carga_frf = RegistroOperacionalModel(
            solicitacao_nf_id=solicitacao_nf_id,
            peso_ton_nf=peso_ton_nf,
            destinatario_nome=destinatario_nome,
            destinatario_cnpj_cpf=destinatario_cnpj_cpf,
            valor_total_nota_100=valor_total_nota_100,
            transportador_nome=transportador_nome,
            transportador_cnpj_cpf=transportador_cnpj_cpf,
            placa_nf=placa_nf,
            motorista_nf=motorista_nf,
            destinatario_data_emissao=destinatario_data_emissao,
            carga_frf=carga_frf,
            situacao_financeira_id=situacao_financeira_id,
            ativo=ativo,
            numero_nota_fiscal=numero_nota_fiscal,
        )
        db.session.add(carga_frf)
        db.session.commit()
        return carga_frf
