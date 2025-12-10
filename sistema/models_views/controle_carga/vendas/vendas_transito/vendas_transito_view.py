from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem, formatar_data_para_brl
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sistema.models_views.controle_carga.nf_complementar.nf_entrada_model import NfEntradaModel
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema._utilitarios import *


@app.route('/controle-carga/vendas/vendas-transito', methods=['GET', 'POST'])
@login_required
@requires_roles
def vendas_em_transito():
    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = 200
    
    resultado = RegistroOperacionalModel.listar_vendas(pagina=pagina, por_pagina=por_pagina, categoria_venda='transito')
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

    resultado = RegistroOperacionalModel.listar_vendas_filtrar(
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

    resultado = RegistroOperacionalModel.listar_vendas_filtrar(
        cliente_venda=cliente_venda,
        nf_venda=nf_venda,
        produto_venda='',
        bitola_venda='',
        transportadora_venda=transportadora_venda,
        motorista_venda='',
        placa_venda='',
        origem_venda='',  # Vendas em trânsito não têm origem
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

    resultado = RegistroOperacionalModel.listar_vendas_filtrar(
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

    # Buscar todos os registros para exportar (sem limite de paginação)
    resultado = RegistroOperacionalModel.listar_vendas_filtrar(
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
        por_pagina=10000,  # Limite alto para pegar todos os registros
        categoria_venda='transito'
    )
    
    dados_excel = []
    for r in resultado['registros']:
        dados_excel.append(
            {
                "Cliente": r.solicitacao.cliente.identificacao or "",
                "Produto": r.solicitacao.produto.nome or "",
                "Bitola": r.solicitacao.bitola.bitola or "",
                "Número NF": f"{r.numero_nota_fiscal_estorno} *" if r.estorno_nf else r.numero_nota_fiscal or "",
                "Placa": r.solicitacao.veiculo.placa_veiculo or "",
                "Motorista": r.solicitacao.motorista.nome_completo or "",
                "Transportadora": r.solicitacao.transportadora_exibicao.identificacao or "",
                "Peso NF (Ton.)": r.peso_ton_nf or "",
                "Data Emissão": formatar_data_para_brl(r.destinatario_data_emissao) if r.destinatario_data_emissao else ""
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
    from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
    
    registro = RegistroOperacionalModel.obter_por_id(id)
    contraNota = NfEntradaModel.obter_contra_nota_por_registro(id)
    
    if not registro or not contraNota:
        flash(('Venda não encontrada!', 'warning'))
        
    # Verifica em todo o faturamento se há registros vinculados a essa venda e os deleta
    
    comissionado_pagar = ComissionadoPagarModel.obter_comissionado_a_pagar_solicitacao(registro.solicitacao.id)
    extrator_pagar = ExtratorPagarModel.obter_extrator_a_pagar_solicitacao(registro.solicitacao.id)
    fornecedor_pagar = FornecedorPagarModel.obter_fornecedor_a_pagar_solicitacao(registro.solicitacao.id)
    frete_pagar = FretePagarModel.obter_frete_a_pagar_solicitacao(registro.solicitacao.id)
    
    if comissionado_pagar or extrator_pagar or fornecedor_pagar or frete_pagar or registro:
        if (comissionado_pagar and comissionado_pagar.situacao_pagamento_id in [5, 8, 9, 10]) or \
        (extrator_pagar and extrator_pagar.situacao_pagamento_id in [5, 8, 9, 10]) or \
        (fornecedor_pagar and fornecedor_pagar.situacao_pagamento_id in [5, 8, 9, 10]) or \
        (frete_pagar and frete_pagar.situacao_pagamento_id in [5, 8, 9, 10]) or \
        (registro and registro.situacao_financeira_id in [5, 8, 9, 10]):
            
            flash(('Não é possível excluir a venda pois existem pagamentos vinculados a ela que já foram processados.', 'warning'))
            if retorno == 'entregue':
                return redirect(url_for('vendas_entregues'))
            else:
                return redirect(url_for('vendas_em_transito'))

        if comissionado_pagar:
            comissionado_pagar.deletado = True
            comissionado_pagar.ativo = False
        
        if extrator_pagar:
            extrator_pagar.deletado = True
            extrator_pagar.ativo = False
        
        if fornecedor_pagar:
            fornecedor_pagar.deletado = True
            fornecedor_pagar.ativo = False
        
        if frete_pagar:
            frete_pagar.deletado = True
            frete_pagar.ativo = False
            
        registro.solicitacao.deletado = 1
        registro.solicitacao.ativo = 0

        registro.deletado = 1
        registro.ativo = 0

        if registro.arquivo_nota:
            registro.arquivo_nota.deletado = 1
            registro.arquivo_nota.ativo = 0
            
        registro.status_emissao_nf_complementar_id = 3

        contraNota.deletado = True
        contraNota.ativo = False
    db.session.commit()
    flash(('Venda excluida com sucesso!', 'success'))
    
    if retorno == 'entregue':
        return redirect(url_for('vendas_entregues'))
    else:
        return redirect(url_for('vendas_em_transito'))