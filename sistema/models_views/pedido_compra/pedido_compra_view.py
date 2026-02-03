from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import login_required, current_user

# Imports do sistema
from sistema import app, db, requires_roles, obter_url_absoluta_de_imagem

# Models utilizados
from sistema.models_views.pedido_compra.pedido_compra_model import PedidoCompraModel
from sistema.models_views.pedido_compra.pedido_compra_item_model import PedidoCompraItemModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_cadastro_model import FornecedorCadastroModel
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema.models_views.gerenciar.motorista.motorista_model import MotoristaModel
from sistema.models_views.gerenciar.motorista.transportadora_motorista_associado_model import TransportadoraMotoristaAssocModel
from sistema.models_views.gerenciar.veiculo.veiculo_model import VeiculoModel
from sistema.models_views.gerenciar.veiculo.veiculo_transportadora_veiculo_associado_model import TransportadoraVeiculoAssocModel
from sistema.models_views.gerenciar.extrator.extrator_model import ExtratorModel
from sistema._utilitarios.manipulacao_arquivos import ManipulacaoArquivos


# =============================================================================
# LISTAGEM DE PEDIDOS DE COMPRA
# =============================================================================

@app.route("/pedido-compra", methods=["GET"])
@login_required
@requires_roles
def listar_pedidos_compra():
    """
    Lista todos os itens de pedidos de compra agrupados por fornecedor.
    
    Exibe um accordion onde cada seção é um fornecedor e mostra todos os 
    itens (cargas) daquele fornecedor, mostrando:
    - Data da carga
    - Data de entrega
    - Transportadora
    - Motorista
    - Placa do veículo
    - Extrator
    - Código do pedido ao qual pertence
    - Ações (editar pedido, excluir item)
    
    Returns:
        render_template: Página HTML com a listagem agrupada por fornecedor
    """
    # Usa a função do model para buscar e agrupar os itens por fornecedor
    itens_por_fornecedor = PedidoCompraItemModel.listar_itens_ativos_agrupados_por_fornecedor()
    
    # Calcula total de itens
    total_itens = sum(len(grupo['itens']) for grupo in itens_por_fornecedor.values())
    
    # Lista de pedidos para o botão de cadastrar
    pedidos = PedidoCompraModel.listar_pedidos_compra()
    
    return render_template(
        "pedido_compra/pedido_compra_listar.html",
        itens_por_fornecedor=itens_por_fornecedor,
        pedidos=pedidos,
        total_itens=total_itens
    )


# =============================================================================
# CADASTRO DE NOVO PEDIDO DE COMPRA
# =============================================================================

@app.route("/pedido-compra/cadastrar", methods=["GET", "POST"])
@login_required
@requires_roles
def cadastrar_pedido_compra():
    """
    Cadastra um novo pedido de compra.
    
    GET: Exibe o formulário de cadastro com os selects populados
    POST: Processa o formulário e cria o pedido com seus itens
    
    O pedido é criado vazio e os itens são adicionados via AJAX posteriormente,
    ou podem ser adicionados diretamente no formulário de cadastro.
    
    Returns:
        GET: render_template com formulário de cadastro
        POST: redirect para edição do pedido criado ou re-exibe formulário com erros
    """
    # Busca dados para popular os selects do formulário
    fornecedores = FornecedorCadastroModel.listar_fornecedores_ativos()
    transportadoras = TransportadoraModel.listar_transportadoras_ativas()
    motoristas = MotoristaModel.listar_motoristas_ativos()
    veiculos = VeiculoModel.listar_veiculos_ativos()
    extratores = ExtratorModel.listar_extratores_ativos()
    
    if request.method == "POST":
        try:
            # Cria o pedido de compra principal
            pedido = PedidoCompraModel(
                usuario_id=current_user.id,
                ativo=True
            )
            
            # Adiciona o pedido ao banco para obter o ID
            db.session.add(pedido)
            db.session.flush()  # Flush para obter o ID antes do commit
            
            # Processa os itens enviados no formulário (se houver)
            # Os itens são enviados como arrays: data_carga[], data_entrega[], etc.
            datas_carga = request.form.getlist('data_carga[]')
            datas_entrega = request.form.getlist('data_entrega[]')
            fornecedores_ids = request.form.getlist('fornecedor_id[]')
            transportadoras_ids = request.form.getlist('transportadora_id[]')
            motoristas_ids = request.form.getlist('motorista_id[]')
            veiculos_ids = request.form.getlist('veiculo_id[]')
            extratores_ids = request.form.getlist('extrator_id[]')
            
            # Cria cada item do pedido
            for i in range(len(datas_carga)):
                if datas_carga[i] and datas_entrega[i]:  # Só cria se tiver as datas
                    item = PedidoCompraItemModel(
                        pedido_compra_id=pedido.id,
                        data_carga=datetime.strptime(datas_carga[i], '%Y-%m-%d').date(),
                        data_entrega=datetime.strptime(datas_entrega[i], '%Y-%m-%d').date(),
                        fornecedor_id=int(fornecedores_ids[i]) if fornecedores_ids[i] else None,
                        transportadora_id=int(transportadoras_ids[i]) if transportadoras_ids[i] else None,
                        motorista_id=int(motoristas_ids[i]) if motoristas_ids[i] else None,
                        veiculo_id=int(veiculos_ids[i]) if veiculos_ids[i] else None,
                        extrator_id=int(extratores_ids[i]) if extratores_ids[i] else None,
                        usuario_id=current_user.id,
                        ativo=True
                    )
                    db.session.add(item)
            
            # Salva tudo no banco
            db.session.commit()
            
            flash(('Pedido de compra cadastrado com sucesso!', 'success'))
            return redirect(url_for('editar_pedido_compra', id=pedido.id))
            
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Erro ao cadastrar pedido de compra: {e}")
            flash(('Erro ao cadastrar pedido de compra. Tente novamente.', 'error'))
    
    return render_template(
        "pedido_compra/pedido_compra_cadastrar.html",
        fornecedores=fornecedores,
        transportadoras=transportadoras,
        motoristas=motoristas,
        veiculos=veiculos,
        extratores=extratores
    )


# =============================================================================
# EDIÇÃO DE PEDIDO DE COMPRA
# =============================================================================

@app.route("/pedido-compra/editar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_pedido_compra(id):
    """
    Edita um pedido de compra existente.
    
    GET: Exibe o formulário de edição com os dados do pedido e seus itens
    POST: Atualiza os dados do pedido e seus itens
    
    Args:
        id: ID do pedido de compra a ser editado
    
    Returns:
        GET: render_template com formulário de edição preenchido
        POST: redirect para listagem ou re-exibe formulário com erros
    """
    # Busca o pedido pelo ID
    pedido = PedidoCompraModel.obter_por_id(id)
    
    if not pedido:
        flash(('Pedido de compra não encontrado!', 'error'))
        return redirect(url_for('listar_pedidos_compra'))
    
    # Busca dados para popular os selects
    fornecedores = FornecedorCadastroModel.listar_fornecedores_ativos()
    transportadoras = TransportadoraModel.listar_transportadoras_ativas()
    motoristas = MotoristaModel.listar_motoristas_ativos()
    veiculos = VeiculoModel.listar_veiculos_ativos()
    extratores = ExtratorModel.listar_extratores_ativos()
    
    # Busca os itens do pedido
    itens = PedidoCompraItemModel.listar_por_pedido(pedido.id)
    
    # Agrupa itens por fornecedor para exibição organizada
    itens_agrupados = pedido.obter_itens_agrupados_por_fornecedor()
    
    if request.method == "POST":
        try:
            # Processa os itens enviados no formulário
            # IDs dos itens existentes (para saber quais atualizar vs criar)
            itens_ids = request.form.getlist('item_id[]')
            datas_carga = request.form.getlist('data_carga[]')
            datas_entrega = request.form.getlist('data_entrega[]')
            fornecedores_ids = request.form.getlist('fornecedor_id[]')
            transportadoras_ids = request.form.getlist('transportadora_id[]')
            motoristas_ids = request.form.getlist('motorista_id[]')
            veiculos_ids = request.form.getlist('veiculo_id[]')
            extratores_ids = request.form.getlist('extrator_id[]')
            
            # Processa cada item
            for i in range(len(datas_carga)):
                if datas_carga[i] and datas_entrega[i]:  # Só processa se tiver as datas
                    
                    # Se tem ID, atualiza o item existente
                    if i < len(itens_ids) and itens_ids[i]:
                        item = PedidoCompraItemModel.obter_por_id(int(itens_ids[i]))
                        if item:
                            item.data_carga = datetime.strptime(datas_carga[i], '%Y-%m-%d').date()
                            item.data_entrega = datetime.strptime(datas_entrega[i], '%Y-%m-%d').date()
                            item.fornecedor_id = int(fornecedores_ids[i]) if fornecedores_ids[i] else None
                            item.transportadora_id = int(transportadoras_ids[i]) if transportadoras_ids[i] else None
                            item.motorista_id = int(motoristas_ids[i]) if motoristas_ids[i] else None
                            item.veiculo_id = int(veiculos_ids[i]) if veiculos_ids[i] else None
                            item.extrator_id = int(extratores_ids[i]) if extratores_ids[i] else None
                    else:
                        # Se não tem ID, cria novo item
                        item = PedidoCompraItemModel(
                            pedido_compra_id=pedido.id,
                            data_carga=datetime.strptime(datas_carga[i], '%Y-%m-%d').date(),
                            data_entrega=datetime.strptime(datas_entrega[i], '%Y-%m-%d').date(),
                            fornecedor_id=int(fornecedores_ids[i]) if fornecedores_ids[i] else None,
                            transportadora_id=int(transportadoras_ids[i]) if transportadoras_ids[i] else None,
                            motorista_id=int(motoristas_ids[i]) if motoristas_ids[i] else None,
                            veiculo_id=int(veiculos_ids[i]) if veiculos_ids[i] else None,
                            extrator_id=int(extratores_ids[i]) if extratores_ids[i] else None,
                            usuario_id=current_user.id,
                            ativo=True
                        )
                        db.session.add(item)
            
            db.session.commit()
            
            flash(('Pedido de compra atualizado com sucesso!', 'success'))
            return redirect(url_for('listar_pedidos_compra'))
            
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Erro ao atualizar pedido de compra: {e}")
            flash(('Erro ao atualizar pedido de compra. Tente novamente.', 'error'))
    
    return render_template(
        "pedido_compra/pedido_compra_editar.html",
        pedido=pedido,
        itens=itens,
        itens_agrupados=itens_agrupados,
        fornecedores=fornecedores,
        transportadoras=transportadoras,
        motoristas=motoristas,
        veiculos=veiculos,
        extratores=extratores
    )


# =============================================================================
# EXCLUSÃO/DESATIVAÇÃO DE PEDIDO DE COMPRA
# =============================================================================

@app.route("/pedido-compra/excluir/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def excluir_pedido_compra(id):
    """
    Exclui (desativa) um pedido de compra.
    
    A exclusão é lógica (soft delete), marcando o pedido como inativo
    em vez de removê-lo fisicamente do banco de dados.
    
    Args:
        id: ID do pedido de compra a ser excluído
    
    Returns:
        redirect: Redireciona para a listagem de pedidos
    """
    pedido = PedidoCompraModel.obter_por_id(id)
    
    if not pedido:
        flash(('Pedido de compra não encontrado!', 'error'))
        return redirect(url_for('listar_pedidos_compra'))
    
    try:
        # Desativa o pedido (soft delete)
        pedido.ativo = False
        pedido.deletado = True
        
        # Desativa também todos os itens do pedido
        for item in pedido.itens.all():
            item.ativo = False
            item.deletado = True
        
        db.session.commit()
        
        flash(('Pedido de compra excluído com sucesso!', 'success'))
        
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Erro ao excluir pedido de compra: {e}")
        flash(('Erro ao excluir pedido de compra. Tente novamente.', 'error'))
    
    return redirect(url_for('listar_pedidos_compra'))


# =============================================================================
# EXCLUSÃO DE ESCALA COMPLETA (AJAX)
# =============================================================================

@app.route("/pedido-compra/escala/excluir/<int:pedido_id>", methods=["POST"])
@login_required
@requires_roles
def excluir_escala_completa(pedido_id):
    """
    Exclui todas as cargas de uma escala específica via AJAX.
    
    Remove o pedido de compra e todos os seus itens (soft delete).
    Usado quando o usuário clica no botão "Excluir Escala" na listagem.
    
    Args:
        pedido_id: ID do pedido de compra (escala) a ser excluído
    
    Returns:
        JSON: Resposta indicando sucesso ou erro
    """
    try:
        pedido = PedidoCompraModel.obter_por_id(pedido_id)
        
        if not pedido:
            return jsonify({'sucesso': False, 'mensagem': 'Escala não encontrada'}), 404
        
        # Conta itens antes da exclusão
        total_itens = pedido.contar_itens()
        codigo = pedido.codigo_transacao
        
        # Soft delete do pedido
        pedido.ativo = False
        pedido.deletado = True
        
        # Soft delete de todos os itens
        for item in pedido.itens.all():
            item.ativo = False
            item.deletado = True
        
        db.session.commit()
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'Escala {codigo} excluída com sucesso! {total_itens} cargas removidas.'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Erro ao excluir escala completa: {e}")
        return jsonify({'sucesso': False, 'mensagem': str(e)}), 500


# =============================================================================
# EXCLUSÃO DE ITEM DO PEDIDO (AJAX)
# =============================================================================

@app.route("/pedido-compra/item/excluir/<int:item_id>", methods=["POST"])
@login_required
@requires_roles
def excluir_item_pedido_compra(item_id):
    """
    Exclui um item específico do pedido de compra via AJAX.
    
    Usado quando o usuário clica no botão de remover item na tela de edição.
    
    Args:
        item_id: ID do item a ser excluído
    
    Returns:
        JSON: Resposta indicando sucesso ou erro
    """
    try:
        item = PedidoCompraItemModel.obter_por_id(item_id)
        
        if not item:
            return jsonify({'sucesso': False, 'mensagem': 'Item não encontrado'}), 404
        
        # Soft delete do item
        item.ativo = False
        item.deletado = True
        
        db.session.commit()
        
        return jsonify({'sucesso': True, 'mensagem': 'Item excluído com sucesso'})
        
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Erro ao excluir item: {e}")
        return jsonify({'sucesso': False, 'mensagem': str(e)}), 500


# =============================================================================
# ADICIONAR ITEM AO PEDIDO (AJAX)
# =============================================================================

@app.route("/pedido-compra/<int:pedido_id>/item/adicionar", methods=["POST"])
@login_required
@requires_roles
def adicionar_item_pedido_compra(pedido_id):
    """
    Adiciona um novo item ao pedido de compra via AJAX.
    
    Recebe os dados do item via JSON e cria um novo registro no banco.
    
    Args:
        pedido_id: ID do pedido de compra
    
    Returns:
        JSON: Dados do item criado ou mensagem de erro
    """
    try:
        pedido = PedidoCompraModel.obter_por_id(pedido_id)
        
        if not pedido:
            return jsonify({'sucesso': False, 'mensagem': 'Pedido não encontrado'}), 404
        
        # Obtém dados do JSON enviado
        dados = request.get_json()
        
        # Cria o novo item
        item = PedidoCompraItemModel(
            pedido_compra_id=pedido.id,
            data_carga=datetime.strptime(dados.get('data_carga'), '%Y-%m-%d').date(),
            data_entrega=datetime.strptime(dados.get('data_entrega'), '%Y-%m-%d').date(),
            fornecedor_id=dados.get('fornecedor_id') if dados.get('fornecedor_id') else None,
            transportadora_id=dados.get('transportadora_id') if dados.get('transportadora_id') else None,
            motorista_id=dados.get('motorista_id') if dados.get('motorista_id') else None,
            veiculo_id=dados.get('veiculo_id') if dados.get('veiculo_id') else None,
            extrator_id=dados.get('extrator_id') if dados.get('extrator_id') else None,
            usuario_id=current_user.id,
            ativo=True
        )
        
        db.session.add(item)
        db.session.commit()
        
        # Retorna os dados do item criado
        return jsonify({
            'sucesso': True,
            'mensagem': 'Item adicionado com sucesso',
            'item': {
                'id': item.id,
                'data_carga': item.data_carga.strftime('%d/%m/%Y'),
                'data_entrega': item.data_entrega.strftime('%d/%m/%Y'),
                'fornecedor': item.obter_nome_fornecedor(),
                'transportadora': item.obter_nome_transportadora(),
                'motorista': item.obter_nome_motorista(),
                'placa': item.obter_placa_veiculo(),
                'extrator': item.obter_nome_extrator()
            }
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Erro ao adicionar item: {e}")
        return jsonify({'sucesso': False, 'mensagem': str(e)}), 500


# =============================================================================
# EXPORTAÇÃO PARA PDF
# =============================================================================

@app.route("/pedido-compra/<int:id>/exportar-pdf", methods=["GET"])
@login_required
@requires_roles
def exportar_pedido_compra_pdf(id):
    """
    Exporta o pedido de compra para PDF.
    
    Gera um relatório em PDF com todos os itens do pedido,
    agrupados por fornecedor conforme solicitado.
    Utiliza o padrão de relatórios do sistema com ManipulacaoArquivos.
    
    Args:
        id: ID do pedido de compra
    
    Returns:
        Response: Arquivo PDF para download
    """
    pedido = PedidoCompraModel.obter_por_id(id)
    
    if not pedido:
        flash(('Pedido de compra não encontrado!', 'error'))
        return redirect(url_for('listar_pedidos_compra'))
    
    # Agrupa itens por fornecedor
    itens_agrupados = pedido.obter_itens_agrupados_por_fornecedor()
    
    # Obtém o caminho absoluto da logo
    logo_path = obter_url_absoluta_de_imagem("logo.png")
    
    # Renderiza o template HTML para PDF
    html = render_template(
        "pedido_compra/pedido_compra_pdf.html",
        pedido=pedido,
        itens_agrupados=itens_agrupados,
        logo_path=logo_path,
        data_geracao=datetime.now()
    )
    
    # Gera o PDF usando a função utilitária do sistema
    nome_arquivo = f"pedido-compra-{pedido.codigo_transacao}-{datetime.now().strftime('%Y%m%d')}"
    resposta = ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo)
    
    return resposta


# =============================================================================
# EXPORTAÇÃO PARA EXCEL
# =============================================================================

@app.route("/pedido-compra/<int:id>/exportar-excel", methods=["GET"])
@login_required
@requires_roles
def exportar_pedido_compra_excel(id):
    """
    Exporta o pedido de compra para Excel.
    
    Gera uma planilha Excel com todos os itens do pedido,
    agrupados por fornecedor.
    Utiliza o padrão de relatórios do sistema com ManipulacaoArquivos.
    
    Args:
        id: ID do pedido de compra
    
    Returns:
        Response: Arquivo Excel para download
    """
    pedido = PedidoCompraModel.obter_por_id(id)
    
    if not pedido:
        flash(('Pedido de compra não encontrado!', 'error'))
        return redirect(url_for('listar_pedidos_compra'))
    
    try:
        # Agrupa itens por fornecedor
        itens_agrupados = pedido.obter_itens_agrupados_por_fornecedor()
        
        # Prepara dados para o Excel
        dados_excel = []
        
        # Adiciona cabeçalho do pedido
        dados_excel.append({
            "Fornecedor/Floresta": f"PEDIDO DE COMPRA - {pedido.codigo_transacao}",
            "Data Carga": "",
            "Data Lançamento": "",
            "Data Entrega": "",
            "Transportadora": "",
            "Motorista": "",
            "Placa": "",
            "Corte/Extrator": ""
        })
        
        dados_excel.append({
            "Fornecedor/Floresta": "",
            "Data Carga": "",
            "Data Lançamento": "",
            "Data Entrega": "",
            "Transportadora": "",
            "Motorista": "",
            "Placa": "",
            "Corte/Extrator": ""
        })
        
        # Itera pelos fornecedores
        for fornecedor_id, itens_do_fornecedor in itens_agrupados.items():
            fornecedor = itens_do_fornecedor[0].fornecedor if itens_do_fornecedor[0].fornecedor else None
            
            # Adiciona cabeçalho do fornecedor
            dados_excel.append({
                "Fornecedor/Floresta": fornecedor.identificacao.upper() if fornecedor else "SEM FORNECEDOR DEFINIDO",
                "Data Carga": "",
                "Data Lançamento": "",
                "Data Entrega": "",
                "Transportadora": "",
                "Motorista": "",
                "Placa": "",
                "Corte/Extrator": ""
            })
            
            # Adiciona itens do fornecedor
            for item in itens_do_fornecedor:
                dados_excel.append({
                    "Fornecedor/Floresta": "",
                    "Data Carga": item.data_carga.strftime('%d/%m/%Y') if item.data_carga else "-",
                    "Data Lançamento": item.data_cadastro.strftime('%d/%m/%Y %H:%M') if item.data_cadastro else "-",
                    "Data Entrega": item.data_entrega.strftime('%d/%m/%Y') if item.data_entrega else "-",
                    "Transportadora": item.obter_nome_transportadora(),
                    "Motorista": item.obter_nome_motorista(),
                    "Placa": item.obter_placa_veiculo(),
                    "Corte/Extrator": item.obter_nome_extrator()
                })
            
            # Adiciona total de cargas do fornecedor
            dados_excel.append({
                "Fornecedor/Floresta": "",
                "Data Carga": "",
                "Data Lançamento": "",
                "Data Entrega": "",
                "Transportadora": "",
                "Motorista": "",
                "Placa": "Cargas deste fornecedor:",
                "Corte/Extrator": len(itens_do_fornecedor)
            })
            
            # Linha em branco entre fornecedores
            dados_excel.append({
                "Fornecedor/Floresta": "",
                "Data Carga": "",
                "Data Lançamento": "",
                "Data Entrega": "",
                "Transportadora": "",
                "Motorista": "",
                "Placa": "",
                "Corte/Extrator": ""
            })
        
        # Adiciona total geral
        dados_excel.append({
            "Fornecedor/Floresta": "",
            "Data Carga": "",
            "Data Entrega": "",
            "Transportadora": "",
            "Motorista": "",
            "Placa": "TOTAL GERAL DE CARGAS:",
            "Corte/Extrator": pedido.contar_itens()
        })
        
        # Gera o Excel usando a função utilitária do sistema
        nome_arquivo = f"pedido-compra-{pedido.codigo_transacao}-{datetime.now().strftime('%Y%m%d')}"
        resposta = ManipulacaoArquivos.exportar_excel(dados_excel, nome_arquivo)
        
        return resposta
        
    except Exception as e:
        print(f"[ERROR] Erro ao exportar Excel: {e}")
        flash(('Erro ao exportar para Excel.', 'error'))
        return redirect(url_for('editar_pedido_compra', id=id))


# =============================================================================
# API: BUSCAR MOTORISTAS POR TRANSPORTADORA (AJAX)
# =============================================================================

@app.route("/pedido-compra/api/motoristas/<int:transportadora_id>", methods=["GET"])
@login_required
def api_motoristas_por_transportadora(transportadora_id):
    """
    Retorna lista de motoristas de uma transportadora específica.
    
    Usa a tabela de associação TransportadoraMotoristaAssoc para buscar
    motoristas vinculados à transportadora, além do campo legado.
    
    Args:
        transportadora_id: ID da transportadora
    
    Returns:
        JSON: Lista de motoristas {id, nome}
    """
    print(f"[DEBUG] Buscando motoristas para transportadora ID: {transportadora_id}")
    try:
        # Usa a função que busca tanto pela associação quanto pelo campo legado
        motoristas = TransportadoraMotoristaAssocModel.obter_motoristas_assoc_transportadora_id(transportadora_id)
        
        return jsonify({
            'sucesso': True,
            'motoristas': [{'id': m.id, 'nome': m.nome_completo} for m in motoristas]
        })
        
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': str(e)}), 500


# =============================================================================
# API: BUSCAR VEÍCULOS POR TRANSPORTADORA (AJAX)
# =============================================================================

@app.route("/pedido-compra/api/veiculos/<int:transportadora_id>", methods=["GET"])
@login_required
def api_veiculos_por_transportadora(transportadora_id):
    """
    Retorna lista de veículos de uma transportadora específica.
    
    Busca pela tabela de associação TransportadoraVeiculoAssoc.
    
    Args:
        transportadora_id: ID da transportadora
    
    Returns:
        JSON: Lista de veículos {id, placa}
    """
    try:
        # Busca veículos pela tabela de associação
        veiculos = (
            db.session.query(VeiculoModel)
            .join(
                TransportadoraVeiculoAssocModel,
                VeiculoModel.id == TransportadoraVeiculoAssocModel.veiculo_id
            )
            .filter(
                TransportadoraVeiculoAssocModel.transportadora_id == transportadora_id,
                TransportadoraVeiculoAssocModel.ativo == True,
                TransportadoraVeiculoAssocModel.deletado == False
            )
            .all()
        )
        
        return jsonify({
            'sucesso': True,
            'veiculos': [{'id': v.id, 'placa': v.placa_veiculo} for v in veiculos]
        })
        
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': str(e)}), 500
