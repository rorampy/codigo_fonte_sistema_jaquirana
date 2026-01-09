from sistema import app, requires_roles, db
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.controle_carga.solicitacao_nf.carga_model import CargaModel
from sistema.models_views.gerenciar.floresta.floresta_model import FlorestaModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_cadastro_model import FornecedorCadastroModel
from sistema.models_views.faturamento.cargas_a_faturar.extrator.extrator_a_pagar_model import ExtratorPagarModel
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.faturamento.cargas_a_faturar.fornecedor.fornecedor_a_pagar_model import FornecedorPagarModel
from sistema.models_views.faturamento.cargas_a_faturar.transportadora.frete_a_pagar_model import FretePagarModel
from sistema.models_views.parametros.rotas_frete.rota_model import RotaFreteModel
from sistema.models_views.gerenciar.motorista.transportadora_motorista_associado_model import TransportadoraMotoristaAssocModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.controle_carga.nf_complementar.nf_entrada_model import NfEntradaModel
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_comissionado_model import FornecedorComissionadoModel
from sistema.models_views.faturamento.cargas_a_faturar.comissionado.comissionado_a_pagar_model import ComissionadoPagarModel
from sistema._utilitarios import *
import os
import tempfile


@app.route("/controle-cargas/cadastrar/ticket/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def cadastrar_ticket(id):
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}

    try:
        solicitacao = CargaModel.obter_solicitacao_por_id(id)
        if not solicitacao:
            flash(("Não encontramos nenhuma solicitação!", "warning"))
            return redirect(url_for("vendas_em_transito"))

        if solicitacao.ticket_emitido:
            flash(("O ticket desta solicitação já foi emitido", "warning"))
            return redirect(url_for("vendas_entregues"))

        if request.method == "POST":
            arquivoTicket = request.files.get("arquivoTicket")
            fornecedorIdentificacao = request.form["fornecedorIdentificacao"]
            numeroNf = request.form["numeroNf"]
            pesoLiquido = request.form["pesoLiquido"]
            placaVeiculo = request.form["placaVeiculo"]
            motoristaTicket = request.form["motoristaTicket"]
            dataEntregaTicket = request.form["dataEntregaTicket"]

            campos = {
                "arquivoTicket": ["Arquivo", arquivoTicket],
                "numeroNf": ["Número NF", numeroNf],
                "pesoLiquido": ["Peso líquido", pesoLiquido],
                "placaVeiculo": ["Placa", placaVeiculo],
                "motoristaTicket": ["Motorista", motoristaTicket],
                "dataEntregaTicket": ["Data entrega", dataEntregaTicket],
                "fornecedorIdentificacao": ["Fornecedor", fornecedorIdentificacao],
            }

            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
            if "validado" not in validacao_campos_obrigatorios:
                flash(("Verifique os campos destacados em vermelho!", "warning"))
                return render_template(
                    "/controle_carga/ticket/ticket_cadastrar.html",
                    fornecedores=FornecedorCadastroModel.listar_fornecedores(),
                    florestas=FlorestaModel.listar_florestas_ativas(),
                    solicitacao=solicitacao,
                    campos_obrigatorios=validacao_campos_obrigatorios,
                    campos_erros=validacao_campos_erros,
                    dados_corretos=request.form,
                    registroOperacional=RegistroOperacionalModel.obter_registro_solicitacao_por_id(id),
                )

            if len(numeroNf) > 20:
                flash(("O número informado para a nota fiscal é mais longo do que o permitido.", "warning"))
                return render_template(
                    "/controle_carga/ticket/ticket_cadastrar.html",
                    fornecedores=FornecedorCadastroModel.listar_fornecedores(),
                    florestas=FlorestaModel.listar_florestas_ativas(),
                    solicitacao=solicitacao,
                    campos_obrigatorios=validacao_campos_obrigatorios,
                    campos_erros=validacao_campos_erros,
                    dados_corretos=request.form,
                    registroOperacional=RegistroOperacionalModel.obter_registro_solicitacao_por_id(id),
                )

            obterRegistro = RegistroOperacionalModel.obter_registro_solicitacao_por_id(solicitacao.id)
            
            solicitacao.ticket_emitido = 1
            solicitacao.floresta_id = None
            solicitacao.fornecedor_id = None

            if obterRegistro:
                obterRegistro.floresta_id = None
                obterRegistro.fornecedor_id = None

            produto = solicitacao.produto.nome
            bitolaSolicitacao = solicitacao.bitola_id

            resultado_fornecedor = FornecedorCadastroModel.obter_precos_custo_fornecedor(
                fornecedorIdentificacao, produto, bitolaSolicitacao, solicitacao.cliente_id, solicitacao.transportadora_id
            )
            
            preco_custo = resultado_fornecedor['preco_custo'] or 0
            preco_custo_extrator = resultado_fornecedor['preco_custo_extrator'] or 0
            origemIncompleta = resultado_fornecedor['origem_incompleta']
            fornecedor = resultado_fornecedor['fornecedor']
            fornecedor_id = fornecedor.id if fornecedor else None

            peso_liquido_float = float(pesoLiquido)
            valorTotal = peso_liquido_float * preco_custo if preco_custo else 0
            valorTotalExtrator = peso_liquido_float * preco_custo_extrator if preco_custo_extrator else 0

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
                    if vinculo.tipo_comissao == 1:
                        # Comissão percentual: converte de (percentual * 100) para decimal
                        # Divide por 10000 pois: /100 desfaz o *100 do armazenamento, /100 converte % para decimal
                        percentual = (vinculo.valor_comissao_ton_100 or 0) / 10000
                        valor_comissao_por_ton_100 = preco_custo * percentual
                        valor_total_comissao_100 = peso_liquido_float * valor_comissao_por_ton_100
                    else:
                        # Comissão valor fixo: já está em centavos, usa diretamente
                        valor_comissao_por_ton_100 = vinculo.valor_comissao_ton_100 or 0
                        valor_total_comissao_100 = peso_liquido_float * valor_comissao_por_ton_100
                    
                    comissionadoPagamento = ComissionadoPagarModel(
                        solicitacao_id=solicitacao.id,
                        fornecedor_id=fornecedor_id,
                        comissionado_id=vinculo.comissionado_id,
                        bitola_id=bitolaSolicitacao,
                        situacao_pagamento_id=2,
                        preco_custo_bitola_100=int(valor_comissao_por_ton_100),
                        valor_total_a_pagar_100=int(valor_total_comissao_100),
                        data_entrega_ticket=dataEntregaTicket,
                        incompleto=origemIncompleta,
                    )
                    db.session.add(comissionadoPagamento)

            if not hasattr(solicitacao, 'transportadora_id') or not solicitacao.transportadora_id:
                flash(('Erro ao obter transportadora da solicitação. Entre em contato com o suporte!', "warning"))
                return redirect(url_for('cadastrar_ticket', id=solicitacao.id))

            if fornecedorIdentificacao != "0":
                resultado_frete = TransportadoraModel.obter_preco_frete(
                    solicitacao.cliente_id, 
                    solicitacao.transportadora_id, 
                    fornecedorIdentificacao, 
                    produto, 
                    bitolaSolicitacao
                )
                
                preco_frete = resultado_frete['preco_frete']
                frete_incompleto = resultado_frete['frete_incompleto']
                valor_total_frete = peso_liquido_float * preco_frete

                fretePagamento = FretePagarModel(
                    solicitacao_id=solicitacao.id,
                    transportadora_id=solicitacao.transportadora_id,
                    fornecedor_id=fornecedorIdentificacao,
                    bitola_id=bitolaSolicitacao,
                    preco_custo_bitola_100=preco_frete,
                    valor_total_a_pagar_100=int(valor_total_frete),
                    data_entrega_ticket=dataEntregaTicket,
                    incompleto=frete_incompleto,
                    situacao_pagamento_id=2,
                )
                db.session.add(fretePagamento)

                solicitacao.fornecedor_id = fornecedorIdentificacao
                if obterRegistro:
                    obterRegistro.fornecedor_id = fornecedorIdentificacao

            if obterRegistro:
                obterRegistro.numero_nota_fiscal_ticket = numeroNf
                obterRegistro.peso_liquido_ticket = pesoLiquido
                obterRegistro.placa_ticket = placaVeiculo
                obterRegistro.arquivo_ticket_id = None
                obterRegistro.motorista_ticket = motoristaTicket
                obterRegistro.ativo = 1
                obterRegistro.data_entrega_ticket = dataEntregaTicket
                registro = obterRegistro
            else:
                registro = RegistroOperacionalModel(
                    solicitacao_nf_id=solicitacao.id,
                    floresta_id=None,
                    fornecedor_id=fornecedorIdentificacao,
                    numero_nota_fiscal_ticket=numeroNf,
                    peso_liquido_ticket=pesoLiquido,
                    placa_ticket=placaVeiculo,
                    data_entrega_ticket=dataEntregaTicket,
                    arquivo_ticket_id=None,
                    motorista_ticket=motoristaTicket,
                    situacao_financeira_id=2,
                    ativo=True,
                )
                db.session.add(registro)

            db.session.flush()

            if arquivoTicket and arquivoTicket.filename:
                if arquivoTicket.mimetype not in ["image/jpeg", "image/png"]:
                    flash(("O Ticket deve estar em formato JPG, JPEG ou PNG.", "warning"))
                    return redirect(url_for("cadastrar_ticket", id=solicitacao.id))
                
                ticket_upload = upload_arquivo(
                    arquivoTicket, "UPLOAD_ARQUIVO_TICKET", f"{registro.id}"
                )
                registro.arquivo_ticket_id = ticket_upload.id

            nfEntrada = NfEntradaModel(registro_id=registro.id)
            db.session.add(nfEntrada)

            db.session.commit()
            
            acao = TipoAcaoEnum.CADASTRO
            PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                current_user.id, acao, acao.pontos, modulo="lancamento_ticket"
            )

            flash(("Ticket lançado com sucesso!", "success"))
            return redirect(url_for("vendas_entregues"))

    except Exception as e:
        print(e)
        flash(("Houve um erro ao tentar lançar ticket, entre em contato com o suporte!", "warning"))
        return redirect(url_for("vendas_entregues"))

    registroOperacional = RegistroOperacionalModel.obter_registro_solicitacao_por_id(id)
    fornecedores = FornecedorCadastroModel.listar_fornecedores()
    florestas = FlorestaModel.listar_florestas_ativas()

    return render_template(
        "/controle_carga/ticket/ticket_cadastrar.html",
        fornecedores=fornecedores,
        florestas=florestas,
        solicitacao=solicitacao,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
        registroOperacional=registroOperacional,
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
    try:
        validacao_campos_obrigatorios = {}
        validacao_campos_erros = {}
        registro = RegistroOperacionalModel.obter_por_id(id)
        fornecedores = FornecedorCadastroModel.listar_fornecedores()
        florestas = FlorestaModel.listar_florestas_ativas()

        if not registro:
            flash(("Ticket não encontrado", "warning"))
            return redirect(url_for("listar_solicitacoes"))

        dados_corretos = {
            "tipoOrigem": "fornecedor" if registro.solicitacao.fornecedor_id else "floresta",
            "florestaIdentificacao": (
                registro.solicitacao.floresta.identificacao
                if registro.solicitacao.floresta_id
                else "Sem registro de floresta"
            ),
            "fornecedorIdentificacao": registro.solicitacao.fornecedor_id or 0,
            "numeroNf": registro.numero_nota_fiscal_ticket,
            "pesoLiquido": registro.peso_liquido_ticket,
            "placaVeiculo": registro.placa_ticket,
            "motoristaTicket": registro.motorista_ticket,
            "dataEntregaTicket": registro.data_entrega_ticket,
        }

        if request.method == "POST":
            arquivoTicket = request.files.get("arquivoTicket")
            fornecedorIdentificacao = request.form.get("fornecedorIdentificacao")
            numeroNf = request.form["numeroNf"]
            pesoLiquido = request.form["pesoLiquido"]
            placaVeiculo = request.form["placaVeiculo"]
            motoristaTicket = request.form["motoristaTicket"]
            dataEntregaTicket = request.form["dataEntregaTicket"]

            campos = {
                "numeroNf": ["Número NF", numeroNf],
                "pesoLiquido": ["Peso líquido", pesoLiquido],
                "placaVeiculo": ["Placa", placaVeiculo],
                "motoristaTicket": ["Motorista", motoristaTicket],
                "dataEntregaTicket": ["Data entrega", dataEntregaTicket],
                "fornecedorIdentificacao": ["Fornecedor", fornecedorIdentificacao],
            }

            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
            if "validado" not in validacao_campos_obrigatorios:
                flash(("Verifique os campos destacados em vermelho!", "warning"))
                return render_template(
                    "/controle_carga/ticket/ticket_editar.html",
                    florestas=florestas,
                    fornecedores=fornecedores,
                    registro=registro,
                    campos_obrigatorios=validacao_campos_obrigatorios,
                    campos_erros=validacao_campos_erros,
                    dados_corretos=dados_corretos,
                )

            if len(numeroNf) > 20:
                flash(("O número informado para a nota fiscal é mais longo do que o permitido.", "warning"))
                return render_template(
                    "/controle_carga/ticket/ticket_editar.html",
                    florestas=florestas,
                    fornecedores=fornecedores,
                    registro=registro,
                    campos_obrigatorios=validacao_campos_obrigatorios,
                    campos_erros=validacao_campos_erros,
                    dados_corretos=dados_corretos,
                )

            obj1 = {
                "fornecedorIdentificacao": str(registro.solicitacao.fornecedor_id or 0),
                "numeroNf": registro.numero_nota_fiscal_ticket or "",
                "pesoLiquido": str(registro.peso_liquido_ticket or ""),
                "placaVeiculo": registro.placa_ticket or "",
                "motoristaTicket": registro.motorista_ticket or "",
                "dataEntregaTicket": str(registro.data_entrega_ticket or ""),
            }

            obj2 = {
                "fornecedorIdentificacao": fornecedorIdentificacao,
                "numeroNf": numeroNf,
                "pesoLiquido": pesoLiquido,
                "placaVeiculo": placaVeiculo,
                "motoristaTicket": motoristaTicket,
                "dataEntregaTicket": dataEntregaTicket,
            }

            diferencas = Gameficacao.compara_objetos(obj1, obj2)
            if diferencas:
                acao = TipoAcaoEnum.EDICAO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id, acao, acao.pontos, modulo="lancamento_ticket"
                )

            registro.solicitacao.floresta_id = None
            registro.solicitacao.fornecedor_id = None
            registro.floresta_id = None
            registro.fornecedor_id = None

            produto = registro.solicitacao.produto.nome
            bitolaSolicitacao = registro.solicitacao.bitola_id

            resultado_fornecedor = FornecedorCadastroModel.obter_precos_custo_fornecedor(
                fornecedorIdentificacao, produto, bitolaSolicitacao, registro.solicitacao.cliente_id, registro.solicitacao.transportadora_id
            )
            
            preco_custo = resultado_fornecedor['preco_custo'] or 0
            preco_custo_extrator = resultado_fornecedor['preco_custo_extrator'] or 0
            origemIncompleta = resultado_fornecedor['origem_incompleta']
            fornecedor = resultado_fornecedor['fornecedor']
            fornecedor_id = fornecedor.id if fornecedor else None

            peso_liquido_float = float(pesoLiquido)
            valorTotal = peso_liquido_float * preco_custo if preco_custo else 0
            valorTotalExtrator = peso_liquido_float * preco_custo_extrator if preco_custo_extrator else 0

            if fornecedorIdentificacao != "0":
                fornecedor_existente = FornecedorPagarModel.query.filter_by(
                    solicitacao_id=registro.solicitacao.id
                ).first()
                
                if fornecedor_existente:
                    if fornecedor_existente.situacao_pagamento_id == 1:
                        flash(("Fornecedor não pode ser editado, pois já foi realizado o pagamento!", "warning"))
                        return redirect(url_for("editar_ticket", id=id))
                    
                    fornecedor_existente.fornecedor_id = fornecedor_id
                    fornecedor_existente.bitola_id = bitolaSolicitacao
                    fornecedor_existente.preco_custo_bitola_100 = preco_custo
                    fornecedor_existente.valor_total_a_pagar_100 = valorTotal
                    fornecedor_existente.incompleto = origemIncompleta
                    fornecedor_existente.data_entrega_ticket = dataEntregaTicket
                    fornecedor_existente.situacao_pagamento_id = 2
                else:
                    fornecedorPagamento = FornecedorPagarModel(
                        solicitacao_id=registro.solicitacao.id,
                        fornecedor_id=fornecedor_id,
                        bitola_id=bitolaSolicitacao,
                        situacao_pagamento_id=2,
                        preco_custo_bitola_100=preco_custo,
                        valor_total_a_pagar_100=int(valorTotal),
                        data_entrega_ticket=dataEntregaTicket,
                        incompleto=False,
                    )
                    db.session.add(fornecedorPagamento)

                extrator_existente = ExtratorPagarModel.query.filter_by(
                    solicitacao_id=registro.solicitacao.id
                ).first()
                
                if extrator_existente:
                    if extrator_existente.situacao_pagamento_id == 1:
                        flash(("Extrator não pode ser editado, pois já foi realizado o pagamento!", "warning"))
                        return redirect(url_for("editar_ticket", id=id))
                    
                    extrator_existente.fornecedor_id = fornecedor_id
                    extrator_existente.bitola_id = bitolaSolicitacao
                    extrator_existente.preco_custo_bitola_100 = preco_custo_extrator
                    extrator_existente.valor_total_a_pagar_100 = valorTotalExtrator
                    extrator_existente.incompleto = origemIncompleta
                    extrator_existente.data_entrega_ticket = dataEntregaTicket
                    extrator_existente.situacao_pagamento_id = 2
                else:
                    extratorPagamento = ExtratorPagarModel(
                        solicitacao_id=registro.solicitacao.id,
                        fornecedor_id=fornecedor_id,
                        bitola_id=bitolaSolicitacao,
                        situacao_pagamento_id=2,
                        preco_custo_bitola_100=preco_custo_extrator,
                        valor_total_a_pagar_100=int(valorTotalExtrator),
                        data_entrega_ticket=dataEntregaTicket,
                        incompleto=False,
                    )
                    db.session.add(extratorPagamento)

                comissionados_existentes = ComissionadoPagarModel.query.filter_by(
                    solicitacao_id=registro.solicitacao.id,
                    deletado=False,
                    ativo=True
                ).all()

                # Verificar se algum comissionado já foi pago
                comissionados_pagos = [c for c in comissionados_existentes if c.situacao_pagamento_id == 1]
                if comissionados_pagos:
                    flash(("Comissionados não podem ser editados, pois já foi realizado o pagamento!", "warning"))
                    return redirect(url_for("editar_ticket", id=id))

                # Remover comissionados existentes que não foram pagos (serão recriados)
                for comissionado_existente in comissionados_existentes:
                    if comissionado_existente.situacao_pagamento_id != 1:
                        comissionado_existente.ativo = False
                        comissionado_existente.deletado = True

                # Criar novos registros de comissionados se o fornecedor tiver
                if fornecedorIdentificacao != "0" and fornecedor and fornecedor.possui_comissionado:
                    comissionados_vinculados = FornecedorComissionadoModel.query.filter(
                        FornecedorComissionadoModel.fornecedor_id == fornecedor.id,
                        FornecedorComissionadoModel.deletado == False,
                        FornecedorComissionadoModel.ativo == True
                    ).all()
                    
                    for vinculo in comissionados_vinculados:
                        if vinculo.tipo_comissao == 1:
                            # Comissão percentual: converte de (percentual * 100) para decimal
                            # Divide por 10000 pois: /100 desfaz o *100 do armazenamento, /100 converte % para decimal
                            percentual = (vinculo.valor_comissao_ton_100 or 0) / 10000
                            valor_comissao_por_ton_100 = preco_custo * percentual
                            valor_total_comissao_100 = peso_liquido_float * valor_comissao_por_ton_100
                        else:
                            # Comissão valor fixo: já está em centavos, usa diretamente
                            valor_comissao_por_ton_100 = vinculo.valor_comissao_ton_100 or 0
                            valor_total_comissao_100 = peso_liquido_float * valor_comissao_por_ton_100
                            
                        comissionadoPagamento = ComissionadoPagarModel(
                            solicitacao_id=registro.solicitacao.id,
                            fornecedor_id=fornecedor_id,
                            comissionado_id=vinculo.comissionado_id,
                            bitola_id=bitolaSolicitacao,
                            situacao_pagamento_id=2,
                            preco_custo_bitola_100=int(valor_comissao_por_ton_100),
                            valor_total_a_pagar_100=int(valor_total_comissao_100),
                            data_entrega_ticket=dataEntregaTicket,
                            incompleto=False,
                        )
                        db.session.add(comissionadoPagamento)

            motorista = registro.solicitacao.motorista
            assoc_atual = TransportadoraMotoristaAssocModel.query.filter_by(
                motorista_id=motorista.id, ativo=True, deletado=False
            ).first()

            transportadoraFrete = registro.solicitacao.transportadora_id
            fornecedor_id_frete = fornecedorIdentificacao if fornecedorIdentificacao != "0" else None

            resultado_frete = TransportadoraModel.obter_preco_frete(
                registro.solicitacao.cliente_id,
                transportadoraFrete,
                fornecedorIdentificacao,
                produto,
                bitolaSolicitacao
            )
            
            preco_frete = resultado_frete['preco_frete']
            frete_incompleto = resultado_frete['frete_incompleto']
            valor_total_frete = peso_liquido_float * preco_frete

            frete_existente = FretePagarModel.query.filter_by(
                solicitacao_id=registro.solicitacao.id
            ).first()
            
            if frete_existente and frete_existente.situacao_pagamento_id == 1:
                flash(("Transportadora não pode ser editada, pois já foi realizado o pagamento!", "warning"))
                return redirect(url_for("editar_ticket", id=id))
            
            if frete_existente:
                frete_existente.transportadora_id = transportadoraFrete
                frete_existente.fornecedor_id = fornecedor_id_frete
                frete_existente.bitola_id = bitolaSolicitacao
                frete_existente.preco_custo_bitola_100 = preco_frete
                frete_existente.valor_total_a_pagar_100 = valor_total_frete
                frete_existente.incompleto = frete_incompleto
                frete_existente.data_entrega_ticket = dataEntregaTicket
                frete_existente.situacao_pagamento_id = 2
            else:
                fretePagamento = FretePagarModel(
                    solicitacao_id=registro.solicitacao.id,
                    transportadora_id=transportadoraFrete,
                    fornecedor_id=fornecedor_id_frete,
                    bitola_id=bitolaSolicitacao,
                    preco_custo_bitola_100=preco_frete,
                    valor_total_a_pagar_100=int(valor_total_frete),
                    incompleto=frete_incompleto,
                    data_entrega_ticket=dataEntregaTicket,
                    situacao_pagamento_id=2,
                )
                db.session.add(fretePagamento)

            if fornecedorIdentificacao != "0":
                registro.solicitacao.fornecedor_id = fornecedorIdentificacao
                registro.fornecedor_id = fornecedorIdentificacao

            registro.numero_nota_fiscal_ticket = numeroNf
            registro.peso_liquido_ticket = pesoLiquido
            registro.placa_ticket = placaVeiculo
            registro.motorista_ticket = motoristaTicket
            registro.data_entrega_ticket = dataEntregaTicket

            if arquivoTicket and arquivoTicket.filename:
                if arquivoTicket.mimetype not in ["image/jpeg", "image/png"]:
                    flash(("O Ticket deve estar em formato JPG, JPEG ou PNG.", "warning"))
                    return redirect(url_for("editar_ticket", id=registro.id))
                
                ticket_upload = upload_arquivo(
                    arquivoTicket, "UPLOAD_ARQUIVO_TICKET", f"{registro.id}"
                )
                registro.arquivo_ticket_id = ticket_upload.id

            db.session.commit()
            flash(("Ticket editado com sucesso!", "success"))
            return redirect(url_for("vendas_entregues"))

    except Exception as e:
        flash(("Houve um erro ao tentar editar este ticket! Entre em contato com o suporte", "warning"))
        return redirect(url_for("vendas_entregues"))
    return render_template(
        "/controle_carga/ticket/ticket_editar.html",
        florestas=florestas,
        fornecedores=fornecedores,
        registro=registro,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=dados_corretos,
    )
