from datetime import datetime
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem, formatar_float_para_brl, formatar_data_para_brl
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema.models_views.parametros.status_emissao_nf_complementar.status_emissao_nf_complementar_model import StatusEmissaoNfComplementarModel
from sistema._utilitarios import *

@app.route("/relatorios/relatorio-cargas/controle-nf-complementar", methods=["GET", "POST"])
@login_required
@requires_roles
def relatorio_controle_nf_complementar():
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    dataHoje = datetime.now().strftime('%d-%m-%Y')
    statusNfComplementar = StatusEmissaoNfComplementarModel.listar_status_ativos()

    if request.method == 'POST':
        registros = RegistroOperacionalModel.registros_carga_cliente(
            data_inicio=request.form.get('dataInicio'),
            data_fim=request.form.get('dataFim'),
            numero_nf=request.form.get('numeroNfComplementar'),
            cliente=request.form.get('clienteNfComplementar'),
            status_nf_complementar=request.form.get('statusNfComplementarEmitida')
        )
        dados_corretos = request.form
    else:
        registros = RegistroOperacionalModel.registros_carga_cliente()
        dados_corretos = {}

    if request.form.get('exportar_pdf'):
        logo_path = obter_url_absoluta_de_imagem('logo.png')
        html = render_template(
            "relatorios/relatorio_de_cargas/relatorio_controle_nf_complementar/exportar_relatorio_controle_complementar.html",
            logo_path=logo_path,
            dataHoje=dataHoje,
            registros=registros,
            dados_corretos=dados_corretos,
            changelog=changelog
        )
        nome_arquivo_saida = f'relatorio-nota-complementar_{dataHoje}'
        return ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida)

    if request.form.get('exportar_excel'):
        linhas = []

        for item in registros:
            registro = item['registro']

            if registro.peso_ton_nf is not None and registro.peso_liquido_ticket is not None:
                diferenca = round(registro.peso_ton_nf - registro.peso_liquido_ticket, 2)
                linha = {
                    'Data Emissão NF': formatar_data_para_brl(registro.destinatario_data_emissao) if registro.destinatario_data_emissao else '-',
                    'Cliente': item['cliente'] or '-',
                    'Número NF': f"{registro.numero_nota_fiscal_estorno} *" or "" if registro.estorno_nf else registro.numero_nota_fiscal or "",
                    'Peso NF': f"{registro.peso_ton_nf} Ton.",
                    'Peso Ticket': f"{registro.peso_liquido_ticket} Ton.",
                    'Diferença': f"{diferenca} Ton.",
                    'NF Complementar Emitida': (
                        registro.status_emissao_nf_complementar.status if registro.status_emissao_nf_complementar else '-'
                    )
                }
                linhas.append(linha)

        nome_arquivo_saida = f'relatorio-nota-complementar_{dataHoje}'
        return ManipulacaoArquivos.exportar_excel(linhas, nome_arquivo_saida)

    return render_template(
        "relatorios/relatorio_de_cargas/relatorio_controle_nf_complementar/relatorio_controle_nf_complementar.html",
        registros=registros,
        dados_corretos=dados_corretos,
        statusNfComplementar=statusNfComplementar,
        changelog=changelog,
        dataHoje=dataHoje
    )
