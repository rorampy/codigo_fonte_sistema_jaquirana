from sistema import app, requires_roles, obter_url_absoluta_de_imagem, formatar_data_para_brl
from flask import render_template, request
from flask_login import login_required
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema._utilitarios import *


@app.route("/controle-cargas/relatorios/controle-emissao", methods=["GET", "POST"])
@login_required
@requires_roles
def relatorio_controle_emissao():
    dataHoje = DataHora.obter_data_atual_padrao_br()
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    produtos = ProdutoModel.listar_produtos()
    bitolas = BitolaModel.listar_bitolas_ativas()

    if request.method == 'POST':
        registrosOperacionais = RegistroOperacionalModel.relatorio_controle_complementar(
            data_inicio=request.form.get("dataInicio"), data_fim=request.form.get("dataFim"),
            produto=request.form.get("produtoEmissao"), bitola=request.form.get("bitolaEmissao"),
            transportadora=request.form.get("transportadoraEmissao"), motorista=request.form.get("motoristaEmissao"),
            placa=request.form.get("placaEmissao"), cliente=request.form.get("clienteEmissao"), numero_nf=request.form.get("numeroNfEmissao")
        )
        dados_corretos = request.form
    else:
        registrosOperacionais = RegistroOperacionalModel.relatorio_controle_complementar(
            data_inicio=request.form.get('dataInicio'), data_fim=request.form.get('dataFim'),
            produto=request.form.get("produtoEmissao"), bitola=request.form.get("bitolaEmissao"),
            transportadora=request.form.get('transportadoraEmissao'), motorista=request.form.get('motoristaEmissao'),
            placa=request.form.get('placaEmissao'), cliente=request.form.get('clienteEmissao'), numero_nf=request.form.get('numeroNfEmissao')
        )
        dados_corretos = {}

    if request.form.get("exportar_pdf"):

        logo_path = obter_url_absoluta_de_imagem("logo.png")
        html = render_template(
            "relatorios/relatorio_de_cargas/relatorio_controle_emissao/exportar_relatorio_controle_emissao.html",
            logo_path=logo_path,
            dataHoje=dataHoje,
            registrosOperacionais=registrosOperacionais,
            dados_corretos=dados_corretos,
            changelog=changelog,
        )

        nome_arquivo_saida = f"relatorio-controle-emissao_{dataHoje}"
        resposta = ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida)
        return resposta
    
    if request.form.get("exportar_excel"):
        dados_excel = []
        for r in registrosOperacionais:
            dados_excel.append(
                {
                    "Data Emissão NF": (
                        formatar_data_para_brl(r.destinatario_data_emissao)
                        if r.destinatario_data_emissao
                        else ""
                    ),
                    "Produto": r.solicitacao.produto.nome or "",
                    "Bitola": r.solicitacao.bitola.bitola or "",
                    "Transportadora":r.solicitacao.transportadora_exibicao.identificacao or "",
                    "Placa": r.solicitacao.veiculo.placa_veiculo or "",
                    "Motorista": r.solicitacao.motorista.nome_completo,
                    "Cliente": r.solicitacao.cliente.identificacao,
                    "Peso NF (Ton.)": r.peso_ton_nf,
                    "Número NF": f"{r.numero_nota_fiscal_estorno} *" or "" if r.estorno_nf else r.numero_nota_fiscal or ""
                }
            )

        nome_arquivo_saida = f"relatorio-controle-emissao_{dataHoje}"
        resposta = ManipulacaoArquivos.exportar_excel(dados_excel, nome_arquivo_saida)
        return resposta

    return render_template(
        "relatorios/relatorio_de_cargas/relatorio_controle_emissao/relatorio_controle_emissao.html", dataHoje=dataHoje,
                                                                    produtos=produtos,bitolas=bitolas,
                                                                    registrosOperacionais=registrosOperacionais,
                                                                    changelog=changelog, dados_corretos=request.form)

