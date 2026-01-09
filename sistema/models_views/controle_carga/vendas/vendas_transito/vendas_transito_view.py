from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem, formatar_data_para_brl
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sistema.models_views.controle_carga.nf_complementar.nf_entrada_model import NfEntradaModel
from sistema.models_views.controle_carga.registro_operacional.pedido_venda_model import PedidoVendaModel
from sistema.models_views.controle_carga.registro_operacional.pedido_venda_dados_nf_model import PedidoVendaDadosNfModel
from sistema.models_views.controle_carga.registro_operacional.pedido_venda_dados_ticket_model import PedidoVendaDadosTicketModel
from sistema.models_views.controle_carga.solicitacao_nf.solicitacao_pedido_venda_model import SolicitacaoPedidoVendaModel
from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema._utilitarios import *


@app.route('/controle-carga/vendas/vendas-transito', methods=['GET', 'POST'])
@login_required
@requires_roles
def vendas_em_transito():
    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = 200
    
    resultado = PedidoVendaModel.listar_vendas(pagina=pagina, por_pagina=por_pagina, categoria_venda='transito')
    produtos = ProdutoModel.listar_produtos()
    bitolas = BitolaModel.listar_bitolas_ativas()
    
    return render_template(
        '/controle_carga/vendas/vendas_transito/listagem_vendas_transito.html',
        vendas_em_transito=resultado['registros'],
        paginacao=resultado,
        produtos=produtos, 
        bitolas=bitolas
    )

@app.route('/controle-carga/vendas/vendas-transito/filtrar', methods=['GET', 'POST'])
@login_required
@requires_roles
def vendas_em_transito_filtrar():
    cliente_venda = request.args.get('cliente_venda', '').strip()
    nf_venda = request.args.get('nf_venda', '').strip()
    produto_venda = request.args.get('produto_venda')
    bitola_venda = request.args.get('bitola_venda')
    transportadora_venda = request.args.get('transportadora_venda', '').strip()
    motorista_venda = request.args.get('motorista_venda', '').strip()
    placa_venda = request.args.get('placa_venda', '').strip()
    origem_venda = request.args.get('origem_venda', '').strip()
    data_inicio = request.args.get('data_inicio', '').strip()
    data_fim = request.args.get('data_fim', '').strip()

    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = 200

    resultado = PedidoVendaModel.listar_vendas_filtrar(
        cliente_venda=cliente_venda,
        nf_venda=nf_venda,
        produto_venda=produto_venda,
        bitola_venda=bitola_venda,
        transportadora_venda=transportadora_venda,
        motorista_venda=motorista_venda,
        placa_venda=placa_venda,
        origem_venda=origem_venda,
        data_inicio=data_inicio,
        data_fim=data_fim,
        pagina=pagina,
        por_pagina=por_pagina,
        categoria_venda='transito'
    )
    
    produtos = ProdutoModel.listar_produtos()
    bitolas = BitolaModel.listar_bitolas_ativas()
    
    dados_corretos = {
        'cliente_venda': cliente_venda,
        'nf_venda': nf_venda,
        'produto_venda': produto_venda,
        'bitola_venda': bitola_venda,
        'transportadora_venda': transportadora_venda,
        'motorista_venda': motorista_venda,
        'placa_venda': placa_venda,
        'origem_venda': origem_venda,
        'data_inicio': data_inicio,
        'data_fim': data_fim
    }
    
    return render_template(
        '/controle_carga/vendas/vendas_transito/listagem_vendas_transito.html',
        vendas_em_transito=resultado['registros'],
        paginacao=resultado,
        produtos=produtos,
        bitolas=bitolas,
        dados_corretos=dados_corretos
    )

@app.route('/controle-carga/vendas/vendas-transito/busca-rapida-ajax', methods=['GET', 'POST'])
@login_required
@requires_roles
def vendas_em_transito_filtrar_ajax():
    cliente_venda = request.args.get('cliente_venda', '').strip()
    nf_venda = request.args.get('nf_venda', '').strip()
    transportadora_venda = request.args.get('transportadora_venda', '').strip()
    data_inicio = request.args.get('data_inicio', '').strip()
    data_fim = request.args.get('data_fim', '').strip()

    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = 200

    resultado = PedidoVendaModel.listar_vendas_filtrar(
        cliente_venda=cliente_venda,
        nf_venda=nf_venda,
        produto_venda='',
        bitola_venda='',
        transportadora_venda=transportadora_venda,
        motorista_venda='',
        placa_venda='',
        origem_venda='',
        data_inicio=data_inicio,
        data_fim=data_fim,
        pagina=pagina,
        por_pagina=por_pagina,
        categoria_venda='transito'
    )
    
    produtos = ProdutoModel.listar_produtos()
    bitolas = BitolaModel.listar_bitolas_ativas()
    
    dados_corretos = {
        'cliente_venda': cliente_venda,
        'nf_venda': nf_venda,
        'transportadora_venda': transportadora_venda,
        'data_inicio': data_inicio,
        'data_fim': data_fim
    }
    
    return render_template(
        '/controle_carga/vendas/vendas_transito/listagem_vendas_transito.html',
        vendas_em_transito=resultado['registros'],
        paginacao=resultado,
        produtos=produtos,
        bitolas=bitolas,
        dados_corretos=dados_corretos
    )
    
@app.route('/controle-carga/vendas/vendas-transito/exportar-pdf', methods=['GET', 'POST'])
@login_required
@requires_roles
def vendas_em_transito_exportar_pdf():
    dataHoje = DataHora.obter_data_atual_padrao_br()
    
    cliente_venda = request.args.get('cliente_venda', '').strip()
    nf_venda = request.args.get('nf_venda', '').strip()
    produto_venda = request.args.get('produto_venda')
    bitola_venda = request.args.get('bitola_venda')
    transportadora_venda = request.args.get('transportadora_venda', '').strip()
    motorista_venda = request.args.get('motorista_venda', '').strip()
    placa_venda = request.args.get('placa_venda', '').strip()
    origem_venda = request.args.get('origem_venda', '').strip()
    data_inicio = request.args.get('data_inicio', '').strip()
    data_fim = request.args.get('data_fim', '').strip()

    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = 200

    resultado = PedidoVendaModel.listar_vendas_filtrar(
        cliente_venda=cliente_venda,
        nf_venda=nf_venda,
        produto_venda=produto_venda,
        bitola_venda=bitola_venda,
        transportadora_venda=transportadora_venda,
        motorista_venda=motorista_venda,
        placa_venda=placa_venda,
        origem_venda=origem_venda,
        data_inicio=data_inicio,
        data_fim=data_fim,
        pagina=pagina,
        por_pagina=por_pagina,
        categoria_venda='transito'
    )
    
    produtos = ProdutoModel.listar_produtos()
    bitolas = BitolaModel.listar_bitolas_ativas()
    
    dados_corretos = {
        'cliente_venda': cliente_venda,
        'nf_venda': nf_venda,
        'produto_venda': produto_venda,
        'bitola_venda': bitola_venda,
        'transportadora_venda': transportadora_venda,
        'motorista_venda': motorista_venda,
        'placa_venda': placa_venda,
        'origem_venda': origem_venda,
        'data_inicio': data_inicio,
        'data_fim': data_fim
    }
    
    logo_path = obter_url_absoluta_de_imagem("logo.png")
    html = render_template(
        '/controle_carga/vendas/vendas_transito/relatorio_pdf/relatorio_venda_transito.html',
        vendas_em_transito=resultado['registros'],
        paginacao=resultado,
        produtos=produtos,
        bitolas=bitolas,
        dados_corretos=dados_corretos,
        logo_path=logo_path,
        data_geracao=dataHoje
    )
    
    nome_arquivo_saida = f"relatorio-venda-transito-{dataHoje}"
    resposta = ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida)
    return resposta

@app.route('/controle-carga/vendas/vendas-transito/exportar-excel', methods=['GET', 'POST'])
@login_required
@requires_roles
def vendas_em_transito_exportar_excel():
    dataHoje = DataHora.obter_data_atual_padrao_br()
    
    cliente_venda = request.args.get('cliente_venda', '').strip()
    nf_venda = request.args.get('nf_venda', '').strip()
    produto_venda = request.args.get('produto_venda')
    bitola_venda = request.args.get('bitola_venda')
    transportadora_venda = request.args.get('transportadora_venda', '').strip()
    motorista_venda = request.args.get('motorista_venda', '').strip()
    placa_venda = request.args.get('placa_venda', '').strip()
    origem_venda = request.args.get('origem_venda', '').strip()
    data_inicio = request.args.get('data_inicio', '').strip()
    data_fim = request.args.get('data_fim', '').strip()

    resultado = PedidoVendaModel.listar_vendas_filtrar(
        cliente_venda=cliente_venda,
        nf_venda=nf_venda,
        produto_venda=produto_venda,
        bitola_venda=bitola_venda,
        transportadora_venda=transportadora_venda,
        motorista_venda=motorista_venda,
        placa_venda=placa_venda,
        origem_venda=origem_venda,
        data_inicio=data_inicio,
        data_fim=data_fim,
        pagina=1,
        por_pagina=10000,
        categoria_venda='transito'
    )
    
    dados_excel = []
    for pedido in resultado['registros']:
        dados_nf = PedidoVendaDadosNfModel.obter_dados_nf_por_pedido_venda_id(pedido.id)
        if dados_nf:
            dados_excel.append(
                {
                    "Cliente": pedido.solicitacao.cliente.identificacao or "",
                    "Produto": pedido.solicitacao.produto.nome or "",
                    "Bitola": pedido.solicitacao.bitola.bitola or "",
                    "Número NF": f"{dados_nf.numero_nota_fiscal_estorno} *" if dados_nf.estorno_nf else dados_nf.numero_nota_fiscal or "",
                    "Placa": pedido.solicitacao.veiculo.placa_veiculo or "",
                    "Motorista": pedido.solicitacao.motorista.nome_completo or "",
                    "Transportadora": pedido.solicitacao.transportadora.identificacao or "",
                    "Peso NF (Ton.)": dados_nf.peso_ton_nf or "",
                    "Data Emissão": formatar_data_para_brl(dados_nf.destinatario_data_emissao) if dados_nf.destinatario_data_emissao else ""
                }
            )

    nome_arquivo_saida = f"vendas-em-transito-{dataHoje}"
    resposta = ManipulacaoArquivos.exportar_excel(dados_excel, nome_arquivo_saida)
    return resposta

@app.route('/controle-cargas/vendas/venda/excluir/<int:id>', methods=['GET', 'POST'])
@app.route('/controle-cargas/vendas/venda/excluir/<int:id>/<string:retorno>', methods=['GET', 'POST'])
@login_required
def excluir_venda(id, retorno=None):
    from sistema.models_views.faturamento.cargas_a_faturar.comissionado.comissionado_a_pagar_model import ComissionadoPagarModel
    from sistema.models_views.faturamento.cargas_a_faturar.extrator.extrator_a_pagar_model import ExtratorPagarModel
    from sistema.models_views.faturamento.cargas_a_faturar.fornecedor.fornecedor_a_pagar_model import FornecedorPagarModel
    from sistema.models_views.faturamento.cargas_a_faturar.transportadora.frete_a_pagar_model import FretePagarModel
    
    pedido_venda = PedidoVendaModel.obter_pedido_venda_por_id(id)
    contraNota = NfEntradaModel.obter_contra_nota_por_registro(id)
    
    if not pedido_venda:
        flash(('Venda não encontrada!', 'warning'))
        if retorno == 'entregue':
            return redirect(url_for('vendas_entregues'))
        else:
            return redirect(url_for('vendas_em_transito'))
    
    dados_nf = PedidoVendaDadosNfModel.obter_dados_nf_por_pedido_venda_id(pedido_venda.id)
    dados_tickets = PedidoVendaDadosTicketModel.listar_dados_ticket_por_pedido_venda_id(pedido_venda.id)
    
    # Buscar todos os pagamentos vinculados
    comissionados_pagar = ComissionadoPagarModel.query.filter_by(solicitacao_id=pedido_venda.solicitacao.id, ativo=True, deletado=False).all()
    extratores_pagar = ExtratorPagarModel.query.filter_by(solicitacao_id=pedido_venda.solicitacao.id, ativo=True, deletado=False).all()
    fornecedores_pagar = FornecedorPagarModel.query.filter_by(solicitacao_id=pedido_venda.solicitacao.id, ativo=True, deletado=False).all()
    fretes_pagar = FretePagarModel.query.filter_by(solicitacao_id=pedido_venda.solicitacao.id, ativo=True, deletado=False).all()
    
    # Verificar se algum pagamento já foi processado
    situacoes_bloqueadas = [5, 8, 9, 10]
    
    for c in comissionados_pagar:
        if c.situacao_pagamento_id in situacoes_bloqueadas:
            flash(('Não é possível excluir a venda pois existem pagamentos de comissionado já processados.', 'warning'))
            return redirect(url_for('vendas_entregues' if retorno == 'entregue' else 'vendas_em_transito'))
    
    for e in extratores_pagar:
        if e.situacao_pagamento_id in situacoes_bloqueadas:
            flash(('Não é possível excluir a venda pois existem pagamentos de extrator já processados.', 'warning'))
            return redirect(url_for('vendas_entregues' if retorno == 'entregue' else 'vendas_em_transito'))
    
    for f in fornecedores_pagar:
        if f.situacao_pagamento_id in situacoes_bloqueadas:
            flash(('Não é possível excluir a venda pois existem pagamentos de fornecedor já processados.', 'warning'))
            return redirect(url_for('vendas_entregues' if retorno == 'entregue' else 'vendas_em_transito'))
    
    for fr in fretes_pagar:
        if fr.situacao_pagamento_id in situacoes_bloqueadas:
            flash(('Não é possível excluir a venda pois existem pagamentos de frete já processados.', 'warning'))
            return redirect(url_for('vendas_entregues' if retorno == 'entregue' else 'vendas_em_transito'))
    
    if pedido_venda.situacao_financeira_id in situacoes_bloqueadas:
        flash(('Não é possível excluir a venda pois a situação financeira já foi processada.', 'warning'))
        return redirect(url_for('vendas_entregues' if retorno == 'entregue' else 'vendas_em_transito'))

    # Excluir logicamente todos os pagamentos
    for c in comissionados_pagar:
        c.deletado = True
        c.ativo = False
    
    for e in extratores_pagar:
        e.deletado = True
        e.ativo = False
    
    for f in fornecedores_pagar:
        f.deletado = True
        f.ativo = False
    
    for fr in fretes_pagar:
        fr.deletado = True
        fr.ativo = False
        
    # Excluir logicamente a solicitação
    pedido_venda.solicitacao.deletado = 1
    pedido_venda.solicitacao.ativo = 0

    # Excluir logicamente o pedido de venda
    pedido_venda.deletado = 1
    pedido_venda.ativo = 0

    # Excluir logicamente os dados da NF
    if dados_nf:
        dados_nf.deletado = 1
        dados_nf.ativo = 0
        if dados_nf.arquivo_nota:
            dados_nf.arquivo_nota.deletado = 1
            dados_nf.arquivo_nota.ativo = 0
    
    # Excluir logicamente todos os dados de ticket
    for ticket in dados_tickets:
        ticket.deletado = True
        ticket.ativo = False
        
    pedido_venda.status_emissao_nf_complementar_id = 3

    if contraNota:
        contraNota.deletado = True
        contraNota.ativo = False
        
    db.session.commit()
    flash(('Venda excluida com sucesso!', 'success'))
    
    if retorno == 'entregue':
        return redirect(url_for('vendas_entregues'))
    else:
        return redirect(url_for('vendas_em_transito'))
    
@app.route("/controle-cargas/vendas/vendas-transito/split/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def split_carga(id):
    pedido_venda = PedidoVendaModel.obter_pedido_venda_por_id(id)
         
    if not pedido_venda:
        flash(("Pedido de venda não encontrado!", "warning"))
        return redirect(url_for("vendas_em_transito"))
    
    dados_nf = PedidoVendaDadosNfModel.obter_dados_nf_por_pedido_venda_id(pedido_venda.id)
    dados_ticket = PedidoVendaDadosTicketModel.obter_dados_ticket_por_pedido_venda_id(pedido_venda.id)
    
    if not dados_nf:
        flash(("Dados da nota fiscal não encontrados!", "warning"))
        return redirect(url_for("vendas_em_transito"))
    
    if dados_nf.realizado_split:
        flash(("Não é possível realizar split para este registro!", "warning"))
        if pedido_venda.solicitacao.ticket_emitido:
            return redirect(url_for("vendas_entregues"))
        else:
            return redirect(url_for("vendas_em_transito"))
    
    produtos = ProdutoModel.listar_produtos()
    bitolas = BitolaModel.listar_bitolas_ativas()
         
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    if request.method == "POST":
        produto_novo = request.form.get("produto_novo")
        bitola_nova = request.form.get("bitola_nova")
        peso_normal_novo = request.form.get("peso_normal_novo")
        peso_excesso_novo = request.form.get("peso_excesso_novo", "0") if dados_nf.possui_excesso_carga else "0"
                 
        if dados_nf.possui_excesso_carga:
            peso_normal_atual = request.form.get("peso_normal_atual")
            peso_excesso_atual = request.form.get("peso_excesso_atual")
                         
            campos = {
                "produto_novo": ["Produto", produto_novo],
                "bitola_nova": ["Bitola", bitola_nova],
                "peso_normal_atual": ["Peso Normal Atual", peso_normal_atual],
                "peso_excesso_atual": ["Peso Excesso Atual", peso_excesso_atual],
                "peso_normal_novo": ["Peso Normal Novo", peso_normal_novo],
                "peso_excesso_novo": ["Peso Excesso Novo", peso_excesso_novo]
            }
        else:
            peso_atual = request.form.get("peso_atual")
                         
            campos = {
                "produto_novo": ["Produto", produto_novo],
                "bitola_nova": ["Bitola", bitola_nova],
                "peso_atual": ["Peso Atual", peso_atual],
                "peso_normal_novo": ["Peso Normal Novo", peso_normal_novo]
            }

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash(("Verifique os campos destacados em vermelho!", "warning"))

        if gravar_banco:
            try:
                peso_original = (dados_nf.peso_ton_nf or 0) + (dados_nf.peso_ton_nf_excesso or 0)
                                 
                if dados_nf.peso_ton_nf_excesso:
                    peso_normal_atual_float = float(peso_normal_atual or 0)
                    peso_excesso_atual_float = float(peso_excesso_atual or 0)
                    peso_total_atual = peso_normal_atual_float + peso_excesso_atual_float
                else:
                    peso_total_atual = float(peso_atual or 0)
                                 
                peso_normal_novo_float = float(peso_normal_novo or 0)
                peso_excesso_novo_float = float(peso_excesso_novo or 0) if dados_nf.peso_ton_nf_excesso else 0
                peso_total_novo = peso_normal_novo_float + peso_excesso_novo_float
                peso_total_split = peso_total_atual + peso_total_novo
                                 
                if abs(peso_total_split - peso_original) > 0.01:
                    gravar_banco = False
                    flash((f"Erro: A soma dos pesos ({peso_total_split:.2f}) não confere com o peso original ({peso_original:.2f})!", "warning"))
                                 
                if peso_total_atual <= 0 or peso_normal_novo_float <= 0:
                    gravar_banco = False
                    flash(("Erro: Os pesos normais devem ser maiores que zero!", "warning"))
                                 
            except (ValueError, TypeError):
                gravar_banco = False
                flash(("Erro: Valores de peso inválidos!", "warning"))

        if gravar_banco:
            try:
                nova_solicitacao = SolicitacaoPedidoVendaModel(
                    empresa_emissora_id=pedido_venda.solicitacao.empresa_emissora_id,
                    cliente_id=pedido_venda.solicitacao.cliente_id,
                    bitola_id=bitola_nova,
                    produto_id=produto_novo,
                    motorista_id=pedido_venda.solicitacao.motorista_id,
                    transportadora_id=pedido_venda.solicitacao.transportadora_id,
                    veiculo_id=pedido_venda.solicitacao.veiculo_id,
                    usuario_id=current_user.id,
                    grupo_whats_id=pedido_venda.solicitacao.grupo_whats_id,
                    certificacao_id=pedido_venda.solicitacao.certificacao_id,
                    nf_emitida=True,
                    ticket_emitido=pedido_venda.solicitacao.ticket_emitido,
                    cancelada=False,
                    realizado_split=True,
                    ativo=True
                )
                db.session.add(nova_solicitacao)
                db.session.flush()

                novo_pedido = PedidoVendaModel.criar_pedido_venda(
                    solicitacao_pedido_venda_id=nova_solicitacao.id,
                    situacao_financeira_id=pedido_venda.situacao_financeira_id
                )

                PedidoVendaDadosNfModel.criar_dados_nf(
                    pedido_venda_id=novo_pedido.id,
                    razao_social_emissor=dados_nf.razao_social_emissor,
                    numero_nota_fiscal=dados_nf.numero_nota_fiscal,
                    serie_nota=dados_nf.serie_nota,
                    chave_acesso=dados_nf.chave_acesso,
                    destinatario_nome=dados_nf.destinatario_nome,
                    destinatario_cnpj_cpf=dados_nf.destinatario_cnpj_cpf,
                    destinatario_insc_estadual=dados_nf.destinatario_insc_estadual,
                    destinatario_data_emissao=dados_nf.destinatario_data_emissao,
                    valor_total_nota_100=dados_nf.valor_total_nota_100,
                    preco_un_nf=dados_nf.preco_un_nf,
                    transportador_nome=dados_nf.transportador_nome,
                    transportador_cnpj_cpf=dados_nf.transportador_cnpj_cpf,
                    transportador_insc_estadual=dados_nf.transportador_insc_estadual,
                    placa_nf=dados_nf.placa_nf,
                    motorista_nf=dados_nf.motorista_nf,
                    peso_ton_nf=peso_normal_novo_float,
                    peso_ton_nf_excesso=peso_excesso_novo_float if peso_excesso_novo_float > 0 else None,
                    peso_nf_ton_com_excecao=peso_total_novo if peso_excesso_novo_float > 0 else peso_normal_novo_float,
                    possui_excesso_carga=(peso_excesso_novo_float > 0),
                    arquivo_nota_id=dados_nf.arquivo_nota_id,
                    arquivo_nota_xml_id=dados_nf.arquivo_nota_xml_id,
                    arquivo_nota_excesso_id=dados_nf.arquivo_nota_excesso_id if peso_excesso_novo_float > 0 else None,
                    arquivo_nota_excesso_xml_id=dados_nf.arquivo_nota_excesso_xml_id if peso_excesso_novo_float > 0 else None,
                    numero_nota_fiscal_excessao=dados_nf.numero_nota_fiscal_excessao if peso_excesso_novo_float > 0 else None,
                    estorno_nf=dados_nf.estorno_nf,
                    arquivo_nota_estorno_id=dados_nf.arquivo_nota_estorno_id,
                    numero_nota_fiscal_estorno=dados_nf.numero_nota_fiscal_estorno,
                    status_emissao_nf_complementar_id=dados_nf.status_emissao_nf_complementar_id if dados_nf.status_emissao_nf_complementar_id else None,
                    realizado_split=True,
                    carga_frf=dados_nf.carga_frf,
                    ativo=True
                )

                if dados_ticket:
                    novos_dados_ticket = PedidoVendaDadosTicketModel(
                        pedido_venda_id=novo_pedido.id,
                        placa_ticket=dados_ticket.placa_ticket,
                        motorista_ticket=dados_ticket.motorista_ticket,
                        data_entrega_ticket=dados_ticket.data_entrega_ticket,
                        numero_nota_fiscal_ticket=dados_ticket.numero_nota_fiscal_ticket,
                        peso_liquido_ticket=dados_ticket.peso_liquido_ticket,
                        arquivo_ticket_id=dados_ticket.arquivo_ticket_id,
                        ativo=True
                    )
                    db.session.add(novos_dados_ticket)

                dados_nf.realizado_split = True
                pedido_venda.solicitacao.realizado_split = True
                
                if dados_nf.peso_ton_nf_excesso:
                    dados_nf.peso_ton_nf = peso_normal_atual_float
                    dados_nf.peso_ton_nf_excesso = peso_excesso_atual_float if peso_excesso_atual_float > 0 else None
                    dados_nf.peso_nf_ton_com_excecao = peso_total_atual
                    dados_nf.possui_excesso_carga = (peso_excesso_atual_float > 0)
                    if peso_excesso_atual_float <= 0:
                        dados_nf.arquivo_nota_excesso_id = None
                        dados_nf.arquivo_nota_excesso_xml_id = None
                        dados_nf.numero_nota_fiscal_excessao = None
                else:
                    dados_nf.peso_ton_nf = peso_total_atual
                    dados_nf.peso_nf_ton_com_excecao = peso_total_atual

                db.session.commit()

                acao = TipoAcaoEnum.EDICAO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    acao,
                    acao.pontos,
                    modulo='split_carga'
                )

                flash((f"Split de carga realizado com sucesso! Criado novo pedido de venda #{novo_pedido.id}", "success"))
                if pedido_venda.solicitacao.ticket_emitido:
                    return redirect(url_for("vendas_entregues"))
                else:
                    return redirect(url_for("vendas_em_transito"))

            except Exception as e:
                db.session.rollback()
                flash((f"Erro ao realizar split: {str(e)}", "danger"))

    registro_view = type('obj', (object,), {
        'id': pedido_venda.id,
        'solicitacao': pedido_venda.solicitacao,
        'peso_ton_nf': dados_nf.peso_ton_nf,
        'peso_ton_nf_excesso': dados_nf.peso_ton_nf_excesso,
        'possui_excesso_carga': dados_nf.possui_excesso_carga,
        'peso_nf_ton_com_excecao': dados_nf.peso_nf_ton_com_excecao,
        'realizado_split': dados_nf.realizado_split,
    })()
    
    return render_template(
        "controle_carga/registro_operacional/split_carga/split_carga.html",
        registro=registro_view,
        pedido_venda=pedido_venda,
        dados_nf=dados_nf,
        dados_ticket=dados_ticket,
        produtos=produtos,
        bitolas=bitolas,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
    )