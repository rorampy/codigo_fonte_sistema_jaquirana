from datetime import datetime
from sistema import app, requires_roles, db, current_user, obter_url_absoluta_de_imagem
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.controle_carga.nf_complementar.nf_entrada_model import NfEntradaModel
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema._utilitarios import *


@app.route("/relatórios/relatorio-carga/nf-entrada/controle-estoque-fornecedor", methods=["GET", "POST"])
@requires_roles
@login_required
def relatorio_controle_estoque_fornecedor():
    try:
        changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
        dataHoje = datetime.now().strftime("%d-%m-%Y")
        
        # Converter strings de data para objetos date se fornecidas
        data_inicio = None
        data_fim = None
        
        if request.args.get('dataInicio'):
            data_inicio = datetime.strptime(request.args.get('dataInicio'), '%Y-%m-%d').date()
                
        if request.args.get('dataFim'):
            data_fim = datetime.strptime(request.args.get('dataFim'), '%Y-%m-%d').date()
        
        if any(request.args.values()):
            registros = NfEntradaModel.filtrar_nf_entrada_ativas(
                data_inicio=data_inicio,
                data_fim=data_fim,
                numero_nf=request.args.get('numeroNf'),
                origem=request.args.get('origemEntrada'),
            )
        else:
            registros = NfEntradaModel.obter_nf_entrada_agrupadas()
            
        logo_path = obter_url_absoluta_de_imagem("logo.png")
        html = render_template(
            "/relatorios/relatorio_semanal/relatorio_prestacao_fornecedor/exportar_relatorio_controle_estoque_fornecedor_pdf.html",
            logo_path=logo_path,
            dataHoje=dataHoje,
            registros=registros,
            dados_corretos=request.args,
            changelog=changelog,
        )

        nome_arquivo_saida = f"relatorio-controle-estoque-fornecedor-pdf-{dataHoje}"
        resposta = ManipulacaoArquivos.gerar_pdf_from_html(
            html, nome_arquivo_saida, abrir_em_nova_aba=True)
        return resposta

    except Exception as e:
        flash(("Não foi possível gerar o relatório de controle de estoque! Entre em contato com o suporte!", "warning"))
        print(f"Erro no relatório de controle de estoque: {e}")
        return redirect(url_for("principal"))