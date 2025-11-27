from datetime import datetime
from sistema import app, requires_roles, obter_url_absoluta_de_imagem, formatar_data_para_brl
from flask import render_template, request
from flask_login import login_required
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema.models_views.faturamento.cargas_a_receber.vendas.recebimento_model import RecebimentoModel
from sistema._utilitarios import *

@app.route("/relatorios/relatorios-financeiros/cargas-receber/filtrar", methods=["GET", "POST"])
@login_required
@requires_roles
def relatorio_cargas_receber():
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    dataHoje = datetime.now().strftime("%d-%m-%Y")

    if request.method == "POST":
        cliente_nome = request.form.get("clienteCarga")
        data_inicio = request.form.get("dataInicio")
        data_fim = request.form.get("dataFim")
        situacao_financeira_id = request.form.get("situacaoFinanceira")
        exportar_pdf = request.form.get("exportar_pdf")
        exportar_excel = request.form.get("exportar_excel")
        recebimentos_agrupados = RecebimentoModel.filtrar_recebimentos_agrupado(
            cliente_identificacao=cliente_nome,
            data_inicio=data_inicio,
            data_fim=data_fim,
            situacao_financeira_id=situacao_financeira_id
        )
        dados_corretos = request.form
        if exportar_pdf or exportar_excel:
            registros = []
            for agrupado in recebimentos_agrupados:
                cliente_nome = agrupado.get('cliente', '-')
                recebimento = agrupado.get('recebimento')
                registro = recebimento.registro if recebimento else None
                item = {
                    'cliente': cliente_nome,
                    'data_entrega': registro.data_entrega_ticket if registro else None,
                    'placa_motorista': ((registro.solicitacao.veiculo.placa_veiculo if registro and registro.solicitacao and hasattr(registro.solicitacao, 'veiculo') and registro.solicitacao.veiculo else '-') + ' | ' + (registro.solicitacao.motorista.nome_completo if registro and registro.solicitacao and hasattr(registro.solicitacao, 'motorista') and registro.solicitacao.motorista else '-')),
                    'fornecedor': registro.solicitacao.floresta.identificacao if registro and registro.solicitacao and hasattr(registro.solicitacao, 'floresta') and registro.solicitacao.floresta else (registro.solicitacao.fornecedor.identificacao if registro and registro.solicitacao and hasattr(registro.solicitacao, 'fornecedor') and registro.solicitacao.fornecedor else '-'),
                    'produto_bitola': (registro.solicitacao.produto.nome if registro and registro.solicitacao and hasattr(registro.solicitacao, 'produto') and registro.solicitacao.produto else '-') + ' / ' + (registro.solicitacao.bitola.bitola if registro and registro.solicitacao and hasattr(registro.solicitacao, 'bitola') and registro.solicitacao.bitola else '-'),
                    'peso_ticket': registro.peso_liquido_ticket if registro and hasattr(registro, 'peso_liquido_ticket') else '-',
                    'numero_nf': registro.numero_nota_fiscal_estorno if registro and hasattr(registro, 'estorno_nf') and registro.estorno_nf else (registro.numero_nota_fiscal if registro and hasattr(registro, 'numero_nota_fiscal') else '-'),
                    'situacao': registro.situacao.situacao if registro and hasattr(registro, 'situacao') and registro.situacao else '-',
                    'a_receber': registro.valor_total_nota_100 if registro and hasattr(registro, 'valor_total_nota_100') and registro.valor_total_nota_100 else '-',
                }
                registros.append(item)
            if exportar_pdf:
                logo_path = obter_url_absoluta_de_imagem("logo.png")
                html = render_template(
                    "relatorios/relatorios_financeiros/relatorio_a_receber_cliente/exportar_relatorio_cargas_cliente_pdf.html",
                    logo_path=logo_path,
                    dataHoje=dataHoje,
                    registros=registros,
                    dados_corretos=dados_corretos,
                    changelog=changelog,
                )
                nome_arquivo_saida = f"relatorio-cargas-receber-{dataHoje}"
                resposta = ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida)
                return resposta
            if exportar_excel:
                linhas = []
                for item in registros:
                    linha = {
                        "Data Entrega": formatar_data_para_brl(item.get('data_entrega')) if item.get('data_entrega') else "-",
                        "Placa/Motorista": item.get('placa_motorista', '-') or '-',
                        "Fornecedor": item.get('fornecedor', '-') or '-',
                        "Produto/Bitola": item.get('produto_bitola', '-') or '-',
                        "Peso Ticket": item.get('peso_ticket', '-') or '-',
                        "Número NF": item.get('numero_nf', '-') or '-',
                        "Situação": item.get('situacao', '-') or '-',
                        "A receber": item.get('a_receber', '-') or '-',
                    }
                    linhas.append(linha)
                nome_arquivo_saida = f"relatorio-cargas-receber-{dataHoje}"
                resposta = ManipulacaoArquivos.exportar_excel(linhas, nome_arquivo_saida)
                return resposta
    else:
        cliente_nome = request.args.get("clienteCarga")
        data_inicio = request.args.get("dataInicio")
        data_fim = request.args.get("dataFim")
        situacao_financeira_id = request.args.get("situacaoFinanceira")
        recebimentos_agrupados = RecebimentoModel.filtrar_recebimentos_agrupado(
            cliente_id=cliente_nome,
            data_inicio=data_inicio,
            data_fim=data_fim,
            situacao_financeira_id=situacao_financeira_id
        )
        dados_corretos = request.args

    return render_template(
        "/financeiro/cargas_a_receber/cargas_a_receber.html",
        recebimentos_agrupados=recebimentos_agrupados,
        dados_corretos=dados_corretos,
        changelog=changelog,
    )