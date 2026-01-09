from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sistema.models_views.controle_carga.nf_complementar.nf_entrada_model import NfEntradaModel
from sistema.models_views.controle_carga.registro_operacional.pedido_venda_model import PedidoVendaModel
from sistema.models_views.controle_carga.registro_operacional.pedido_venda_dados_nf_model import PedidoVendaDadosNfModel
from sistema.models_views.controle_carga.registro_operacional.pedido_venda_dados_ticket_model import PedidoVendaDadosTicketModel
from sistema.models_views.controle_carga.solicitacao_nf.solicitacao_pedido_venda_model import SolicitacaoPedidoVendaModel
from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema._utilitarios import *


@app.route('/controle-carga/vendas/vendas-entregues', methods=['GET', 'POST'])
@login_required
@requires_roles
def vendas_entregues():
    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = 200
    
    resultado = PedidoVendaModel.listar_vendas(pagina=pagina, por_pagina=por_pagina, categoria_venda='entregue')
    produtos = ProdutoModel.listar_produtos()
    bitolas = BitolaModel.listar_bitolas_ativas()
    
    return render_template(
        '/controle_carga/vendas/vendas_entregues/listagem_vendas_entregues.html',
        vendas_entregues=resultado['registros'],
        paginacao=resultado,
        produtos=produtos, 
        bitolas=bitolas
    )

@app.route('/controle-carga/vendas/vendas-entregues/filtrar', methods=['GET', 'POST'])
@login_required
@requires_roles
def vendas_entregues_filtrar():
    cliente_venda = request.args.get('cliente_venda').strip()
    nf_venda = request.args.get('nf_venda').strip()
    produto_venda = request.args.get('produto_venda')
    bitola_venda = request.args.get('bitola_venda')
    transportadora_venda = request.args.get('transportadora_venda').strip()
    motorista_venda = request.args.get('motorista_venda').strip()
    placa_venda = request.args.get('placa_venda').strip()
    origem_venda = request.args.get('origem_venda').strip()

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
        pagina=pagina,
        por_pagina=por_pagina,
        categoria_venda='entregue'
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
        'origem_venda': origem_venda
    }
    
    return render_template(
        '/controle_carga/vendas/vendas_entregues/listagem_vendas_entregues.html',
        vendas_entregues=resultado['registros'],
        paginacao=resultado,
        produtos=produtos,
        bitolas=bitolas,
        dados_corretos=dados_corretos
    )
    
@app.route('/controle-carga/vendas/vendas-entregues/busca-rapida-ajax', methods=['GET', 'POST'])
@login_required
@requires_roles
def vendas_entregues_busca_rapida_ajax():
    cliente_venda = request.args.get('cliente_venda', '').strip()
    nf_venda = request.args.get('nf_venda', '').strip()
    origem_venda = request.args.get('origem_venda', '').strip()
    data_inicio = request.args.get('data_inicio', '').strip()
    data_fim = request.args.get('data_fim', '').strip()

    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = 200

    resultado = PedidoVendaModel.listar_vendas_filtrar(
        cliente_venda=cliente_venda,
        nf_venda=nf_venda,
        produto_venda='',
        bitola_venda='',
        transportadora_venda='',
        motorista_venda='',
        placa_venda='',
        origem_venda=origem_venda,
        data_inicio=data_inicio,
        data_fim=data_fim,
        pagina=pagina,
        por_pagina=por_pagina,
        categoria_venda='entregue'
    )
    
    produtos = ProdutoModel.listar_produtos()
    bitolas = BitolaModel.listar_bitolas_ativas()
    
    dados_corretos = {
        'cliente_venda': cliente_venda,
        'nf_venda': nf_venda,
        'origem_venda': origem_venda,
        'data_inicio': data_inicio,
        'data_fim': data_fim
    }
    
    return render_template(
        '/controle_carga/vendas/vendas_entregues/listagem_vendas_entregues.html',
        vendas_entregues=resultado['registros'],
        paginacao=resultado,
        produtos=produtos,
        bitolas=bitolas,
        dados_corretos=dados_corretos
    )
    
@app.route('/controle-cargas/detalhes/vendas/<int:id>', methods=['GET', 'POST'])
@login_required
@requires_roles
def detalhe_pedido_venda(id):
    pedido_venda = PedidoVendaModel.obter_pedido_venda_por_id(id)
    if not pedido_venda:
        flash(("Pedido de venda não encontrado!", "warning"))
        return redirect(url_for("vendas_entregues"))
    
    return render_template('/controle_carga/registro_operacional/detalhes_registro_operacional.html', 
                           dados_corretos=request.form,
                           pedido_venda=pedido_venda,
                           registro=pedido_venda)