from sistema import app, requires_roles, db
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.controle_carga.solicitacao_nf.solicitacao_pedido_venda_model import SolicitacaoPedidoVendaModel
from sistema.models_views.controle_carga.registro_operacional.pedido_venda_model import PedidoVendaModel
from sistema.models_views.controle_carga.registro_operacional.pedido_venda_dados_nf_model import PedidoVendaDadosNfModel
from sistema.models_views.controle_carga.registro_operacional.pedido_venda_dados_ticket_model import PedidoVendaDadosTicketModel
from sistema.models_views.gerenciar.floresta.floresta_model import FlorestaModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_cadastro_model import FornecedorCadastroModel
from sistema.models_views.faturamento.cargas_a_faturar.extrator.extrator_a_pagar_model import ExtratorPagarModel
from sistema.models_views.faturamento.cargas_a_faturar.fornecedor.fornecedor_a_pagar_model import FornecedorPagarModel
from sistema.models_views.faturamento.cargas_a_faturar.transportadora.frete_a_pagar_model import FretePagarModel
from sistema.models_views.gerenciar.motorista.transportadora_motorista_associado_model import TransportadoraMotoristaAssocModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_comissionado_model import FornecedorComissionadoModel
from sistema.models_views.faturamento.cargas_a_faturar.comissionado.comissionado_a_pagar_model import ComissionadoPagarModel
from sistema.models_views.controle_carga.nf_complementar.nf_entrada_model import NfEntradaModel
from sistema._utilitarios import *
import json
import os
import tempfile
import os
import tempfile


@app.route("/controle-cargas/cadastrar/ticket/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def cadastrar_ticket(id):
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    solicitacao = SolicitacaoPedidoVendaModel.obter_solicitacao_por_id(id)
    if not solicitacao:
        flash(("Não encontramos nenhuma solicitação!", "warning"))
        return redirect(url_for("vendas_em_transito"))

    if solicitacao.ticket_emitido:
        flash(("O ticket desta solicitação já foi emitido", "warning"))
        return redirect(url_for("vendas_entregues"))

    # Buscar o pedido de venda e dados NF
    pedido_venda = PedidoVendaModel.obter_pedido_venda_por_solicitacao_id(solicitacao.id)
    if not pedido_venda:
        flash(("Pedido de venda não encontrado para esta solicitação!", "warning"))
        return redirect(url_for("vendas_em_transito"))

    dados_nf = PedidoVendaDadosNfModel.obter_dados_nf_por_pedido_venda_id(pedido_venda.id)
    fornecedores = FornecedorCadastroModel.listar_fornecedores()

    if request.method == "POST":
        arquivoTicket = request.files.get("arquivoTicket")
        numeroNf = request.form.get("numeroNf")
        pesoLiquido = request.form.get("pesoLiquido")
        placaVeiculo = request.form.get("placaVeiculo")
        motoristaTicket = request.form.get("motoristaTicket")
        dataEntregaTicket = request.form.get("dataEntregaTicket")
        fornecedores_data = request.form.get("fornecedoresData")
        print(fornecedores_data)
        if not fornecedores_data:
            gravar_banco = False
            flash(("Você deve adicionar pelo menos um fornecedor!", "warning"))
        else:
            try:
                fornecedores_lista = json.loads(fornecedores_data)
            except json.JSONDecodeError:
                gravar_banco = False
                flash(("Erro ao processar dados dos fornecedores!", "warning"))

        campos = {
            "arquivoTicket": ["Arquivo", arquivoTicket],
            "numeroNf": ["Número NF", numeroNf],
            "pesoLiquido": ["Peso líquido total", pesoLiquido],
            "placaVeiculo": ["Placa", placaVeiculo],
            "motoristaTicket": ["Motorista", motoristaTicket],
            "dataEntregaTicket": ["Data entrega", dataEntregaTicket],
        }

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
        if "validado" not in validacao_campos_obrigatorios:
            gravar_banco = False
            flash(("Verifique os campos destacados em vermelho!", "warning"))

        if gravar_banco and len(numeroNf) > 20:
            gravar_banco = False
            flash(("O número informado para a nota fiscal é mais longo do que o permitido.", "warning"))

        # Validar soma dos pesos dos fornecedores
        if gravar_banco:
            peso_total_ticket = float(pesoLiquido)
            peso_total_fornecedores = sum(float(f.get('peso', 0)) for f in fornecedores_lista)
            
            if abs(peso_total_ticket - peso_total_fornecedores) > 0.01:
                gravar_banco = False
                flash((f"A soma dos pesos dos fornecedores ({peso_total_fornecedores:.2f} ton) não corresponde ao peso total do ticket ({peso_total_ticket:.2f} ton)!", "warning"))

        if gravar_banco:
            try:
                # Upload do arquivo do ticket
                arquivo_ticket_id = None
                if arquivoTicket and arquivoTicket.filename:
                    if arquivoTicket.mimetype not in ["image/jpeg", "image/png"]:
                        flash(("O Ticket deve estar em formato JPG, JPEG ou PNG.", "warning"))
                        return redirect(url_for("cadastrar_ticket", id=solicitacao.id))
                    
                    ticket_upload = upload_arquivo(
                        arquivoTicket, "UPLOAD_ARQUIVO_TICKET", f"ticket_{pedido_venda.id}"
                    )
                    arquivo_ticket_id = ticket_upload.id

                # Atualizar solicitação
                solicitacao.ticket_emitido = True
                produto = solicitacao.produto.nome
                bitolaSolicitacao = solicitacao.bitola_id

                # Processar cada fornecedor
                for fornecedor_data in fornecedores_lista:
                    print(fornecedor_data)
                    fornecedor_id = int(fornecedor_data.get('fornecedor_id'))
                    peso_fornecedor = float(fornecedor_data.get('peso'))
                    
                    if fornecedor_id == 0:
                        flash(("Um ou mais fornecedores não foram selecionados corretamente!", "warning"))
                        return redirect(url_for("cadastrar_ticket", id=solicitacao.id))

                    # Criar registro de dados do ticket para este fornecedor
                    dados_ticket = PedidoVendaDadosTicketModel(
                        pedido_venda_id=pedido_venda.id,
                        placa_ticket=placaVeiculo,
                        motorista_ticket=motoristaTicket,
                        data_entrega_ticket=dataEntregaTicket,
                        numero_nota_fiscal_ticket=numeroNf,
                        peso_liquido_ticket=peso_fornecedor,
                        arquivo_ticket_id=arquivo_ticket_id,
                        fornecedor_id=fornecedor_id,
                        ativo=True
                    )
                    db.session.add(dados_ticket)
                    db.session.flush()

                    # Obter preços do fornecedor
                    resultado_fornecedor = FornecedorCadastroModel.obter_precos_custo_fornecedor(
                        fornecedor_id, produto, bitolaSolicitacao, solicitacao.cliente_id, solicitacao.transportadora_id
                    )
                    
                    preco_custo = resultado_fornecedor['preco_custo'] or 0
                    preco_custo_extrator = resultado_fornecedor['preco_custo_extrator'] or 0
                    origemIncompleta = resultado_fornecedor['origem_incompleta']
                    fornecedor = resultado_fornecedor['fornecedor']

                    valorTotal = peso_fornecedor * preco_custo if preco_custo else 0
                    valorTotalExtrator = peso_fornecedor * preco_custo_extrator if preco_custo_extrator else 0

                    # Criar pagamento para o fornecedor
                    fornecedorPagamento = FornecedorPagarModel(
                        solicitacao_id=solicitacao.id,
                        fornecedor_id=fornecedor_id,
                        bitola_id=bitolaSolicitacao,
                        situacao_pagamento_id=2,
                        preco_custo_bitola_100=preco_custo,
                        valor_total_a_pagar_100=valorTotal,
                        data_entrega_ticket=dataEntregaTicket,
                        incompleto=origemIncompleta,
                    )
                    db.session.add(fornecedorPagamento)

                    # Criar pagamento para o extrator
                    extratorPagamento = ExtratorPagarModel(
                        solicitacao_id=solicitacao.id,
                        fornecedor_id=fornecedor_id,
                        bitola_id=bitolaSolicitacao,
                        situacao_pagamento_id=2,
                        preco_custo_bitola_100=preco_custo_extrator,
                        valor_total_a_pagar_100=valorTotalExtrator,
                        data_entrega_ticket=dataEntregaTicket,
                        incompleto=origemIncompleta,
                    )
                    db.session.add(extratorPagamento)

                    # Verificar se o fornecedor possui comissionados vinculados
                    if fornecedor and fornecedor.possui_comissionado:
                        comissionados_vinculados = FornecedorComissionadoModel.query.filter(
                            FornecedorComissionadoModel.fornecedor_id == fornecedor.id,
                            FornecedorComissionadoModel.deletado == False,
                            FornecedorComissionadoModel.ativo == True
                        ).all()
                        
                        for vinculo in comissionados_vinculados:
                            if vinculo.tipo_comissao == 1:  # Porcentagem
                                percentual = (vinculo.valor_comissao_ton_100 or 0) / 100
                                valor_comissao_por_ton = (preco_custo * percentual) / 100
                                valor_total_comissao = peso_fornecedor * valor_comissao_por_ton
                            else:  # Valor fixo (tipo = 0)
                                valor_comissao_por_ton = (vinculo.valor_comissao_ton_100 or 0) / 100
                                valor_total_comissao = peso_fornecedor * valor_comissao_por_ton
                            
                            comissionadoPagamento = ComissionadoPagarModel(
                                solicitacao_id=solicitacao.id,
                                fornecedor_id=fornecedor_id,
                                comissionado_id=vinculo.comissionado_id,
                                bitola_id=bitolaSolicitacao,
                                situacao_pagamento_id=2,
                                preco_custo_bitola_100=int(valor_comissao_por_ton * 100),
                                valor_total_a_pagar_100=int(valor_total_comissao * 100),
                                data_entrega_ticket=dataEntregaTicket,
                                incompleto=origemIncompleta,
                            )
                            db.session.add(comissionadoPagamento)

                    # Criar pagamento de frete
                    if hasattr(solicitacao, 'transportadora_id') and solicitacao.transportadora_id:
                        resultado_frete = TransportadoraModel.obter_preco_frete(
                            solicitacao.cliente_id, 
                            solicitacao.transportadora_id, 
                            fornecedor_id, 
                            produto, 
                            bitolaSolicitacao
                        )
                        
                        preco_frete = resultado_frete['preco_frete']
                        frete_incompleto = resultado_frete['frete_incompleto']
                        valor_total_frete = peso_fornecedor * preco_frete

                        fretePagamento = FretePagarModel(
                            solicitacao_id=solicitacao.id,
                            transportadora_id=solicitacao.transportadora_id,
                            fornecedor_id=fornecedor_id,
                            bitola_id=bitolaSolicitacao,
                            preco_custo_bitola_100=preco_frete,
                            valor_total_a_pagar_100=int(valor_total_frete),
                            data_entrega_ticket=dataEntregaTicket,
                            incompleto=frete_incompleto,
                            situacao_pagamento_id=2,
                        )
                        db.session.add(fretePagamento)

                # Criar NF de Entrada vinculada ao pedido de venda
                nfEntrada = NfEntradaModel(pedido_venda_id=pedido_venda.id)
                db.session.add(nfEntrada)

                db.session.commit()
                
                acao = TipoAcaoEnum.CADASTRO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id, acao, acao.pontos, modulo="lancamento_ticket"
                )

                flash(("Ticket lançado com sucesso!", "success"))
                return redirect(url_for("vendas_entregues"))

            except Exception as e:
                db.session.rollback()
                print(f"Erro ao cadastrar ticket: {str(e)}")
                flash(("Houve um erro ao tentar lançar ticket, entre em contato com o suporte!", "warning"))

    return render_template(
        "/controle_carga/ticket/ticket_cadastrar.html",
        fornecedores=fornecedores,
        solicitacao=solicitacao,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
        pedido_venda=pedido_venda,
        dados_nf=dados_nf,
    )


@app.route("/api/processar-ticket", methods=["POST"])
def processar_ticket_api():
    """
    API para processar imagem do ticket e extrair dados automaticamente.
    Valida qualidade da imagem antes de processar.
    """
    temp_path = None
    try:
        if 'arquivo' not in request.files:
            return jsonify({
                'sucesso': False,
                'erro': 'ARQUIVO_NAO_ENVIADO',
                'mensagem': 'Nenhum arquivo foi enviado'
            }), 400
        
        arquivo = request.files['arquivo']
        
        if not arquivo or arquivo.filename == '':
            return jsonify({
                'sucesso': False,
                'erro': 'ARQUIVO_INVALIDO',
                'mensagem': 'Arquivo inválido'
            }), 400
        
        # Validar tamanho do arquivo (máximo 10MB)
        arquivo.seek(0, os.SEEK_END)
        tamanho_arquivo = arquivo.tell()
        arquivo.seek(0)
        
        if tamanho_arquivo > 10 * 1024 * 1024:  # 10MB
            return jsonify({
                'sucesso': False,
                'erro': 'ARQUIVO_MUITO_GRANDE',
                'mensagem': 'O arquivo deve ter no máximo 10MB'
            }), 413
        
        if arquivo.mimetype not in ["image/jpeg", "image/png", "image/jpg"]:
            return jsonify({
                'sucesso': False,
                'erro': 'FORMATO_INVALIDO',
                'mensagem': 'O arquivo deve estar em formato JPG, JPEG ou PNG'
            }), 400
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(arquivo.filename)[1]) as temp_file:
            arquivo.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            extrator = ExtracaoTicket(temp_path)
            dados = extrator.processar()
            
            # Liberar memória explicitamente
            del extrator
            
            if not dados.get('sucesso'):
                return jsonify({
                    'sucesso': False,
                    'erro': dados.get('erro'),
                    'mensagem': dados.get('mensagem'),
                    'dados': {
                        'numero_nf': dados.get('numero_nf') or '',
                        'peso_liquido': dados.get('peso_liquido') if dados.get('peso_liquido') else None,
                        'data_entrega': dados.get('data_entrega').strftime('%Y-%m-%d') if dados.get('data_entrega') else '',
                        'placa': dados.get('placa') or ''
                    }
                }), 422
            
            resultado = {
                'sucesso': True,
                'dados': {
                    'numero_nf': dados.get('numero_nf') or '',
                    'peso_liquido': dados.get('peso_liquido') if dados.get('peso_liquido') else None,
                    'data_entrega': dados.get('data_entrega').strftime('%Y-%m-%d') if dados.get('data_entrega') else '',
                    'placa': dados.get('placa') or ''
                },
                'campos_faltantes': dados.get('campos_faltantes')
            }
            
            return jsonify(resultado), 200
            
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
    
    except MemoryError:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception:
                pass
        return jsonify({
            'sucesso': False,
            'erro': 'ERRO_MEMORIA',
            'mensagem': 'Servidor sem memória disponível. Tente com uma imagem menor.'
        }), 507
    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception:
                pass
        return jsonify({
            'sucesso': False,
            'erro': 'ERRO_PROCESSAMENTO',
            'mensagem': f'Erro ao processar ticket: {str(e)}'
        }), 500


@app.route("/tickets/lancamentos/editar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_ticket(id):
    """
    Edita um ticket existente, seguindo o mesmo padrão do cadastro com múltiplos fornecedores.
    :param id: ID do pedido de venda (PedidoVendaModel)
    """
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    try:
        # Buscar o pedido de venda pelo ID
        pedido_venda = PedidoVendaModel.obter_pedido_venda_por_id(id)
        if not pedido_venda:
            flash(("Pedido de venda não encontrado!", "warning"))
            return redirect(url_for("vendas_entregues"))

        # Buscar a solicitação através do pedido de venda
        solicitacao = pedido_venda.solicitacao
        if not solicitacao:
            flash(("Solicitação não encontrada!", "warning"))
            return redirect(url_for("vendas_entregues"))

        # Buscar dados da NF e lista de fornecedores
        dados_nf = PedidoVendaDadosNfModel.obter_dados_nf_por_pedido_venda_id(pedido_venda.id)
        fornecedores = FornecedorCadastroModel.listar_fornecedores()

        # Buscar todos os dados de ticket existentes (múltiplos fornecedores)
        dados_ticket_existentes = PedidoVendaDadosTicketModel.listar_dados_ticket_por_pedido_venda_id(pedido_venda.id)
        
        # Preparar dados para o template
        fornecedores_ticket = []
        for dt in dados_ticket_existentes:
            fornecedores_ticket.append({
                'id': dt.id,
                'fornecedor_id': dt.fornecedor_id,
                'peso': float(dt.peso_liquido_ticket) if dt.peso_liquido_ticket else 0
            })

        # Dados para preencher o formulário
        primeiro_ticket = dados_ticket_existentes[0] if dados_ticket_existentes else None
        
        dados_corretos = {
            "numeroNf": primeiro_ticket.numero_nota_fiscal_ticket if primeiro_ticket else "",
            "pesoLiquido": sum(float(dt.peso_liquido_ticket or 0) for dt in dados_ticket_existentes) if dados_ticket_existentes else "",
            "placaVeiculo": primeiro_ticket.placa_ticket if primeiro_ticket else "",
            "motoristaTicket": primeiro_ticket.motorista_ticket if primeiro_ticket else "",
            "dataEntregaTicket": primeiro_ticket.data_entrega_ticket if primeiro_ticket else "",
        }

        if request.method == "POST":
            arquivoTicket = request.files.get("arquivoTicket")
            numeroNf = request.form.get("numeroNf")
            pesoLiquido = request.form.get("pesoLiquido")
            placaVeiculo = request.form.get("placaVeiculo")
            motoristaTicket = request.form.get("motoristaTicket")
            dataEntregaTicket = request.form.get("dataEntregaTicket")
            fornecedores_data = request.form.get("fornecedoresData")

            # Validar fornecedores
            if not fornecedores_data:
                gravar_banco = False
                flash(("Você deve adicionar pelo menos um fornecedor!", "warning"))
            else:
                try:
                    fornecedores_lista = json.loads(fornecedores_data)
                except json.JSONDecodeError:
                    gravar_banco = False
                    flash(("Erro ao processar dados dos fornecedores!", "warning"))

            # Validar campos obrigatórios
            campos = {
                "numeroNf": ["Número NF", numeroNf],
                "pesoLiquido": ["Peso líquido total", pesoLiquido],
                "placaVeiculo": ["Placa", placaVeiculo],
                "motoristaTicket": ["Motorista", motoristaTicket],
                "dataEntregaTicket": ["Data entrega", dataEntregaTicket],
            }

            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
            if "validado" not in validacao_campos_obrigatorios:
                gravar_banco = False
                flash(("Verifique os campos destacados em vermelho!", "warning"))

            if gravar_banco and len(numeroNf) > 20:
                gravar_banco = False
                flash(("O número informado para a nota fiscal é mais longo do que o permitido.", "warning"))

            # Validar soma dos pesos dos fornecedores
            if gravar_banco:
                peso_total_ticket = float(pesoLiquido)
                peso_total_fornecedores = sum(float(f.get('peso', 0)) for f in fornecedores_lista)
                
                if abs(peso_total_ticket - peso_total_fornecedores) > 0.01:
                    gravar_banco = False
                    flash((f"A soma dos pesos dos fornecedores ({peso_total_fornecedores:.2f} ton) não corresponde ao peso total do ticket ({peso_total_ticket:.2f} ton)!", "warning"))

            # Verificar se algum pagamento já foi realizado
            if gravar_banco:
                fornecedor_pago = FornecedorPagarModel.query.filter_by(
                    solicitacao_id=solicitacao.id,
                    situacao_pagamento_id=1
                ).first()
                if fornecedor_pago:
                    gravar_banco = False
                    flash(("Não é possível editar: já existe pagamento realizado para fornecedor!", "warning"))

                extrator_pago = ExtratorPagarModel.query.filter_by(
                    solicitacao_id=solicitacao.id,
                    situacao_pagamento_id=1
                ).first()
                if extrator_pago:
                    gravar_banco = False
                    flash(("Não é possível editar: já existe pagamento realizado para extrator!", "warning"))

                frete_pago = FretePagarModel.query.filter_by(
                    solicitacao_id=solicitacao.id,
                    situacao_pagamento_id=1
                ).first()
                if frete_pago:
                    gravar_banco = False
                    flash(("Não é possível editar: já existe pagamento realizado para frete!", "warning"))

                comissionado_pago = ComissionadoPagarModel.query.filter_by(
                    solicitacao_id=solicitacao.id,
                    situacao_pagamento_id=1,
                    deletado=False,
                    ativo=True
                ).first()
                if comissionado_pago:
                    gravar_banco = False
                    flash(("Não é possível editar: já existe pagamento realizado para comissionado!", "warning"))

            if gravar_banco:
                try:
                    # Upload do arquivo do ticket (se enviado)
                    arquivo_ticket_id = primeiro_ticket.arquivo_ticket_id if primeiro_ticket else None
                    
                    if arquivoTicket and arquivoTicket.filename:
                        if arquivoTicket.mimetype not in ["image/jpeg", "image/png"]:
                            flash(("O Ticket deve estar em formato JPG, JPEG ou PNG.", "warning"))
                            return redirect(url_for("editar_ticket", id=pedido_venda.id))
                        
                        ticket_upload = upload_arquivo(
                            arquivoTicket, "UPLOAD_ARQUIVO_TICKET", f"ticket_{pedido_venda.id}"
                        )
                        arquivo_ticket_id = ticket_upload.id

                    produto = solicitacao.produto.nome
                    bitolaSolicitacao = solicitacao.bitola_id

                    # Desativar dados de ticket existentes
                    for dt in dados_ticket_existentes:
                        dt.ativo = False
                        dt.deletado = True

                    # Desativar pagamentos existentes (fornecedor, extrator, comissionado, frete)
                    FornecedorPagarModel.query.filter_by(solicitacao_id=solicitacao.id).update({
                        'ativo': False, 'deletado': True
                    })
                    ExtratorPagarModel.query.filter_by(solicitacao_id=solicitacao.id).update({
                        'ativo': False, 'deletado': True
                    })
                    ComissionadoPagarModel.query.filter_by(solicitacao_id=solicitacao.id).update({
                        'ativo': False, 'deletado': True
                    })
                    FretePagarModel.query.filter_by(solicitacao_id=solicitacao.id).update({
                        'ativo': False, 'deletado': True
                    })

                    # Processar cada fornecedor
                    for fornecedor_data in fornecedores_lista:
                        fornecedor_id = int(fornecedor_data.get('fornecedor_id'))
                        peso_fornecedor = float(fornecedor_data.get('peso'))
                        
                        if fornecedor_id == 0:
                            flash(("Um ou mais fornecedores não foram selecionados corretamente!", "warning"))
                            return redirect(url_for("editar_ticket", id=pedido_venda.id))

                        # Criar novo registro de dados do ticket para este fornecedor
                        dados_ticket = PedidoVendaDadosTicketModel(
                            pedido_venda_id=pedido_venda.id,
                            placa_ticket=placaVeiculo,
                            motorista_ticket=motoristaTicket,
                            data_entrega_ticket=dataEntregaTicket,
                            numero_nota_fiscal_ticket=numeroNf,
                            peso_liquido_ticket=peso_fornecedor,
                            arquivo_ticket_id=arquivo_ticket_id,
                            fornecedor_id=fornecedor_id,
                            ativo=True
                        )
                        db.session.add(dados_ticket)
                        db.session.flush()

                        # Obter preços do fornecedor
                        resultado_fornecedor = FornecedorCadastroModel.obter_precos_custo_fornecedor(
                            fornecedor_id, produto, bitolaSolicitacao, solicitacao.cliente_id, solicitacao.transportadora_id
                        )
                        
                        preco_custo = resultado_fornecedor['preco_custo'] or 0
                        preco_custo_extrator = resultado_fornecedor['preco_custo_extrator'] or 0
                        origemIncompleta = resultado_fornecedor['origem_incompleta']
                        fornecedor = resultado_fornecedor['fornecedor']

                        valorTotal = peso_fornecedor * preco_custo if preco_custo else 0
                        valorTotalExtrator = peso_fornecedor * preco_custo_extrator if preco_custo_extrator else 0

                        # Criar pagamento para o fornecedor
                        fornecedorPagamento = FornecedorPagarModel(
                            solicitacao_id=solicitacao.id,
                            fornecedor_id=fornecedor_id,
                            bitola_id=bitolaSolicitacao,
                            situacao_pagamento_id=2,
                            preco_custo_bitola_100=preco_custo,
                            valor_total_a_pagar_100=valorTotal,
                            data_entrega_ticket=dataEntregaTicket,
                            incompleto=origemIncompleta,
                        )
                        db.session.add(fornecedorPagamento)

                        # Criar pagamento para o extrator
                        extratorPagamento = ExtratorPagarModel(
                            solicitacao_id=solicitacao.id,
                            fornecedor_id=fornecedor_id,
                            bitola_id=bitolaSolicitacao,
                            situacao_pagamento_id=2,
                            preco_custo_bitola_100=preco_custo_extrator,
                            valor_total_a_pagar_100=valorTotalExtrator,
                            data_entrega_ticket=dataEntregaTicket,
                            incompleto=origemIncompleta,
                        )
                        db.session.add(extratorPagamento)

                        # Verificar se o fornecedor possui comissionados vinculados
                        if fornecedor and fornecedor.possui_comissionado:
                            comissionados_vinculados = FornecedorComissionadoModel.query.filter(
                                FornecedorComissionadoModel.fornecedor_id == fornecedor.id,
                                FornecedorComissionadoModel.deletado == False,
                                FornecedorComissionadoModel.ativo == True
                            ).all()
                            
                            for vinculo in comissionados_vinculados:
                                if vinculo.tipo_comissao == 1:  # Porcentagem
                                    percentual = (vinculo.valor_comissao_ton_100 or 0) / 100
                                    valor_comissao_por_ton = (preco_custo * percentual) / 100
                                    valor_total_comissao = peso_fornecedor * valor_comissao_por_ton
                                else:  # Valor fixo (tipo = 0)
                                    valor_comissao_por_ton = (vinculo.valor_comissao_ton_100 or 0) / 100
                                    valor_total_comissao = peso_fornecedor * valor_comissao_por_ton
                                
                                comissionadoPagamento = ComissionadoPagarModel(
                                    solicitacao_id=solicitacao.id,
                                    fornecedor_id=fornecedor_id,
                                    comissionado_id=vinculo.comissionado_id,
                                    bitola_id=bitolaSolicitacao,
                                    situacao_pagamento_id=2,
                                    preco_custo_bitola_100=int(valor_comissao_por_ton * 100),
                                    valor_total_a_pagar_100=int(valor_total_comissao * 100),
                                    data_entrega_ticket=dataEntregaTicket,
                                    incompleto=origemIncompleta,
                                )
                                db.session.add(comissionadoPagamento)

                        # Criar pagamento de frete
                        if hasattr(solicitacao, 'transportadora_id') and solicitacao.transportadora_id:
                            resultado_frete = TransportadoraModel.obter_preco_frete(
                                solicitacao.cliente_id, 
                                solicitacao.transportadora_id, 
                                fornecedor_id, 
                                produto, 
                                bitolaSolicitacao
                            )
                            
                            preco_frete = resultado_frete['preco_frete']
                            frete_incompleto = resultado_frete['frete_incompleto']
                            valor_total_frete = peso_fornecedor * preco_frete

                            fretePagamento = FretePagarModel(
                                solicitacao_id=solicitacao.id,
                                transportadora_id=solicitacao.transportadora_id,
                                fornecedor_id=fornecedor_id,
                                bitola_id=bitolaSolicitacao,
                                preco_custo_bitola_100=preco_frete,
                                valor_total_a_pagar_100=int(valor_total_frete),
                                data_entrega_ticket=dataEntregaTicket,
                                incompleto=frete_incompleto,
                                situacao_pagamento_id=2,
                            )
                            db.session.add(fretePagamento)

                    db.session.commit()
                    
                    # Gameficação
                    acao = TipoAcaoEnum.EDICAO
                    PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                        current_user.id, acao, acao.pontos, modulo="lancamento_ticket"
                    )

                    flash(("Ticket editado com sucesso!", "success"))
                    return redirect(url_for("vendas_entregues"))

                except Exception as e:
                    db.session.rollback()
                    print(f"Erro ao editar ticket: {str(e)}")
                    flash(("Houve um erro ao tentar editar o ticket, entre em contato com o suporte!", "warning"))

        return render_template(
            "/controle_carga/ticket/ticket_editar.html",
            fornecedores=fornecedores,
            solicitacao=solicitacao,
            campos_obrigatorios=validacao_campos_obrigatorios,
            campos_erros=validacao_campos_erros,
            dados_corretos=dados_corretos,
            pedido_venda=pedido_venda,
            dados_nf=dados_nf,
            dados_ticket_existentes=dados_ticket_existentes,
            fornecedores_ticket=fornecedores_ticket,
        )

    except Exception as e:
        print(f"Erro ao carregar edição de ticket: {str(e)}")
        flash(("Houve um erro ao tentar carregar este ticket! Entre em contato com o suporte", "warning"))
        return redirect(url_for("vendas_entregues"))
