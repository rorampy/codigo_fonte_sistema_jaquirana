import os
import smtplib
from logs_sistema import flask_logger
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from huey import SqliteHuey, crontab
from config import *

# obtendo o caminho relativo para o banco ficar ao lado de tarefas.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'bd_tarefas.db')

# instância
huey = SqliteHuey(filename=DB_PATH)


@huey.task(retries=3, retry_delay=30)
def enviar_email_html(titulo, corpo, destinatario):
    server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORTA, timeout=10)
    
    # se quiser ativar o debug do smtplib
    # server.set_debuglevel(1)
    server.starttls()
    server.login(EMAIL_LOGIN, EMAIL_SENHA)
    email_msg = MIMEMultipart()
    email_msg['From'] = EMAIL_LOGIN
    email_msg['To'] = destinatario
    email_msg['Subject'] = titulo
    email_msg.attach(MIMEText(corpo, 'html'))    # 'plain' = tipo texto | 'html' = tipo HTML
    
    server.sendmail(email_msg['From'], email_msg['To'], email_msg.as_string())
    server.quit()
    
    return True


@huey.task(retries=2, retry_delay=60)
def sincronizar_precos_fornecedores(data_inicio=None, data_fim=None, fornecedor_id=None):
    """
    Tarefa assíncrona para sincronizar preços de fornecedores com otimizações de performance.
    
    Este processo foi otimizado para reduzir queries ao banco de dados:
    - Carrega registros operacionais em lote (1 query ao invés de N)
    - Utiliza eager loading para carregar solicitações junto com fornecedores
    - Cria mapeamentos em memória para acesso rápido aos dados
    
    Args:
        data_inicio (str): Data de início no formato 'YYYY-MM-DD'
        data_fim (str): Data de fim no formato 'YYYY-MM-DD'
        fornecedor_id (str): ID do fornecedor específico ou None para todos
    
    Returns:
        dict: Resultado da sincronização com estatísticas
    """
    from sistema import db, app
    from sistema.models_views.gerenciar.fornecedor.fornecedor_model import FornecedorModel
    from sistema.models_views.faturamento.cargas_a_faturar.fornecedor.fornecedor_a_pagar_model import FornecedorPagarModel
    from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
    from datetime import datetime
    from sqlalchemy.orm import joinedload

    with app.app_context():
        try:
            filtro_data_inicio = None
            filtro_data_fim = None
            
            if data_inicio:
                try:
                    filtro_data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                except ValueError:
                    raise ValueError(f"Formato de data_inicio inválido: {data_inicio}")
            
            if data_fim:
                try:
                    filtro_data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
                except ValueError:
                    raise ValueError(f"Formato de data_fim inválido: {data_fim}")
            
            fornecedoresPagar = FornecedorPagarModel.listar_fornecedores_a_pagar_por_periodo_entrega(
                data_inicio=filtro_data_inicio,
                data_fim=filtro_data_fim
            )
            
            # Filtrar por fornecedor específico se informado
            if fornecedor_id:
                try:
                    fornecedor_id_int = int(fornecedor_id)
                    fornecedoresPagar = [f for f in fornecedoresPagar if f.fornecedor_id == fornecedor_id_int]
                except (ValueError, TypeError):
                    raise ValueError(f"ID do fornecedor inválido: {fornecedor_id}")
            
            solicitacao_ids = [f.solicitacao_id for f in fornecedoresPagar if f.solicitacao_id]
            registros_map = {}
            
            if solicitacao_ids:
                registros_operacionais = (
                    db.session.query(RegistroOperacionalModel)
                    .filter(RegistroOperacionalModel.solicitacao_nf_id.in_(solicitacao_ids))
                    .all()
                )
                
                registros_map = {reg.solicitacao_nf_id: reg for reg in registros_operacionais}
            
            fornecedores_query = (
                db.session.query(FornecedorPagarModel)
                .options(joinedload(FornecedorPagarModel.solicitacao))  
                .filter(FornecedorPagarModel.id.in_([f.id for f in fornecedoresPagar]),
                        FornecedorPagarModel.situacao_pagamento_id != 5, # Faturado
                        FornecedorPagarModel.situacao_pagamento_id != 8) # Conciliado
                .all()
            )
            
            sincronizados = 0
            erros = []
            total_processados = len(fornecedores_query)
                        
            for i, forne in enumerate(fornecedores_query, 1):
                try:
                    registroOperacional = registros_map.get(forne.solicitacao_id)
                    
                    if forne.situacao_pagamento_id != 1 and forne.fornecedor:
                        solicitacao = forne.solicitacao
                        
                        if not solicitacao:
                            continue
                        
                        resultado_precos = FornecedorModel.obter_precos_custo_fornecedor(
                            fornecedor_identificacao=forne.fornecedor_id,
                            produto=solicitacao.produto.nome.strip(),
                            bitola_solicitacao=solicitacao.bitola_id,
                            cliente_id=solicitacao.cliente_id,
                            transportadora_id=solicitacao.transportadora_id
                        )
                        
                        if not resultado_precos['origem_incompleta'] and resultado_precos['preco_custo'] is not None:
                            preco = resultado_precos['preco_custo']
                            
                            if registroOperacional and registroOperacional.peso_liquido_ticket != 0.0:
                                valorTotal = float(preco) * registroOperacional.peso_liquido_ticket
                                
                                if valorTotal != 0.0:
                                    forne.preco_custo_bitola_100 = preco
                                    forne.valor_total_a_pagar_100 = valorTotal
                                    forne.incompleto = False
                                    sincronizados += 1
                                    
                        else:
                            produto_nome = solicitacao.produto.nome.strip()
                            bitola_id = solicitacao.bitola_id
                            erro_msg = f'Preço não encontrado para fornecedor {forne.id}, produto: {produto_nome}, bitola: {bitola_id}'
                            erros.append(erro_msg)
                
                except Exception as e:
                    erro_msg = f'Erro ao processar fornecedor {forne.id}: {str(e)}'
                    erros.append(erro_msg)
                    continue
                        
            if sincronizados > 0:
                db.session.commit()  
            else:
                db.session.rollback()  
                
            resultado = {
                'sincronizados': sincronizados,
                'total_processados': total_processados,
                'total_erros': len(erros),
                'erros': erros[:10],  
                'sucesso': True,
                'periodo': f"{data_inicio} a {data_fim}" if data_inicio and data_fim else "Sem filtro",
                'fornecedor_filtrado': fornecedor_id is not None
            }
            
            return resultado
            
        except Exception as e:
            db.session.rollback()
            erro_msg = f"Erro geral na sincronização: {str(e)}"
            return {
                'sincronizados': 0,
                'total_processados': 0,
                'total_erros': 1,
                'erros': [erro_msg],
                'sucesso': False,
                'periodo': f"{data_inicio} a {data_fim}" if data_inicio and data_fim else "Sem filtro",
                'fornecedor_filtrado': fornecedor_id is not None
            }

@huey.task(retries=2, retry_delay=60)
def sincronizar_precos_transportadoras(data_inicio=None, data_fim=None, transportadora_id=None):
    """
    Tarefa assíncrona para sincronizar preços de fretes com otimizações de performance.
    
    Este processo foi otimizado para reduzir queries ao banco de dados:
    - Carrega registros operacionais em lote (1 query ao invés de N)
    - Utiliza eager loading para carregar solicitações junto com fretes
    - Cria mapeamentos em memória para acesso rápido aos dados
    
    Args:
        data_inicio (str): Data de início no formato 'YYYY-MM-DD'
        data_fim (str): Data de fim no formato 'YYYY-MM-DD'
        transportadora_id (str): ID da transportadora específica ou None para todas
    
    Returns:
        dict: Resultado da sincronização com estatísticas
    """
    from sistema import db, app
    from sistema.models_views.faturamento.cargas_a_faturar.transportadora.frete_a_pagar_model import FretePagarModel
    from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
    from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
    from datetime import datetime
    from sqlalchemy.orm import joinedload

    with app.app_context():
        try:
            
            # Processamento e validação das datas de filtro
            filtro_data_inicio = None
            filtro_data_fim = None
            
            if data_inicio:
                try:
                    filtro_data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                except ValueError:
                    raise ValueError(f"Formato de data_inicio inválido: {data_inicio}")
            
            if data_fim:
                try:
                    filtro_data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
                except ValueError:
                    raise ValueError(f"Formato de data_fim inválido: {data_fim}")
            

            fretesPagar = FretePagarModel.listar_fretes_a_pagar_por_periodo_entrega(
                data_inicio=filtro_data_inicio,
                data_fim=filtro_data_fim
            )

            if transportadora_id:
                try:
                    transportadora_id_int = int(transportadora_id)
                    fretesPagar = [f for f in fretesPagar if f.solicitacao and f.solicitacao.transportadora_id == transportadora_id_int]
                except (ValueError, TypeError):
                    raise ValueError(f"ID da transportadora inválido: {transportadora_id}")
            
            solicitacao_ids = [f.solicitacao_id for f in fretesPagar if f.solicitacao_id]
            registros_map = {}
            
            if solicitacao_ids:
                registros_operacionais = (
                    db.session.query(RegistroOperacionalModel)
                    .filter(RegistroOperacionalModel.solicitacao_nf_id.in_(solicitacao_ids))
                    .all()
                )
                
                registros_map = {reg.solicitacao_nf_id: reg for reg in registros_operacionais}
            
            fretes_query = (
                db.session.query(FretePagarModel)
                .options(joinedload(FretePagarModel.solicitacao))  
                .filter(FretePagarModel.id.in_([f.id for f in fretesPagar]),
                        FretePagarModel.situacao_pagamento_id != 5, # Faturado
                        FretePagarModel.situacao_pagamento_id != 8) # Conciliado
                .all()
            )
            
            sincronizados = 0
            erros = []
            total_processados = len(fretes_query)
            

            for i, frete in enumerate(fretes_query, 1):
                try:
                    registroOperacional = registros_map.get(frete.solicitacao_id)

                    if frete.situacao_pagamento_id != 1:
                        solicitacao = frete.solicitacao
                        
                        if not solicitacao:
                            continue
                        
                        resultado_frete = TransportadoraModel.obter_preco_frete(
                            cliente_id=solicitacao.cliente_id,
                            transportadora_id=solicitacao.transportadora_id,
                            fornecedor_identificacao=solicitacao.fornecedor_id,
                            produto=solicitacao.produto.nome.strip(),
                            bitola_solicitacao=solicitacao.bitola_id
                        )
                        
                        if not resultado_frete['frete_incompleto'] and resultado_frete['preco_frete'] is not None:
                            preco_frete = resultado_frete['preco_frete']
                            
                            if registroOperacional and registroOperacional.peso_liquido_ticket != 0.0:
                                valorTotal = float(preco_frete) * registroOperacional.peso_liquido_ticket
                                
                                if valorTotal != 0.0:
                                    frete.preco_custo_frete_100 = preco_frete
                                    frete.valor_total_a_pagar_100 = valorTotal
                                    frete.incompleto = False
                                    sincronizados += 1
                                    
                        else:
                            produto_nome = solicitacao.produto.nome.strip()
                            bitola_id = solicitacao.bitola_id
                            erro_msg = f'Preço de frete não encontrado para registro {frete.id}, produto: {produto_nome}, bitola: {bitola_id}, cliente: {solicitacao.cliente_id}, transportadora: {solicitacao.transportadora_id}, fornecedor: {solicitacao.fornecedor_id}'
                            erros.append(erro_msg)
                            
                except Exception as e:
                    erro_msg = f'Erro ao processar frete {frete.id}: {str(e)}'
                    erros.append(erro_msg)
                    continue
                        
            if sincronizados > 0:
                db.session.commit()  
            else:
                db.session.rollback() 
            
            resultado = {
                'sincronizados': sincronizados,
                'total_processados': total_processados,
                'total_erros': len(erros),
                'erros': erros[:10],  
                'sucesso': True,
                'periodo': f"{data_inicio} a {data_fim}" if data_inicio and data_fim else "Sem filtro",
                'transportadora_filtrada': transportadora_id is not None
            }
            
            return resultado
            
        except Exception as e:
            db.session.rollback()
            erro_msg = f"Erro geral na sincronização de fretes: {str(e)}"
            return {
                'sincronizados': 0,
                'total_processados': 0,
                'total_erros': 1,
                'erros': [erro_msg],
                'sucesso': False,
                'periodo': f"{data_inicio} a {data_fim}" if data_inicio and data_fim else "Sem filtro"
            }