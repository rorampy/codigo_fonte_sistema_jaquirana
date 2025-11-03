from datetime import datetime
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sistema.models_views.financeiro.lancamento_avulso.lancamento_avulso_model import LancamentoAvulsoModel
from sistema.models_views.configuracoes_gerais.conta_bancaria.conta_bancaria_model import ContaBancariaModel
from sistema.models_views.financeiro.situacao_pagamento_model import SituacaoPagamentoModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema._utilitarios import *


@app.route("/financeiro/relatorio-receitas-avulsas", methods=["GET"])
@login_required
@requires_roles
def relatorio_receitas_avulsas():
    """Página de relatório de receitas avulsas"""
    contas_bancarias = ContaBancariaModel.obter_contas_bancarias_ativas()
    status_pagamentos = SituacaoPagamentoModel.listar_status()
    
    return render_template(
        "relatorios/relatorios_financeiros/relatorio_receitas_avulsas/relatorio_receitas_avulsas.html",
        contas_bancarias=contas_bancarias,
        status_pagamentos=status_pagamentos,
        dados_corretos=request.args
    )


@app.route("/financeiro/relatorio-receitas-avulsas-dados", methods=["GET", "POST"])
@login_required
@requires_roles
def relatorio_dados_receitas_avulsas():
    """Gera os dados do relatório de receitas avulsas"""
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    dataHoje = datetime.now().strftime("%d-%m-%Y")
    contas_bancarias = ContaBancariaModel.obter_contas_bancarias_ativas()
    status_pagamentos = SituacaoPagamentoModel.listar_status()
    
    def obter_registros_com_filtros():
        # Para POST, primeiro verifica se há filtros no form, senão usa args
        filtros_source = request.form if request.method == "POST" and any(request.form.values()) else request.args
        
        if any(filtros_source.values()):
            data_inicio = filtros_source.get("dataInicio")
            data_fim = filtros_source.get("dataFim")
            conta_bancaria_id = filtros_source.get("contaBancaria")
            status_pagamento = filtros_source.get("statusPagamento")
            descricao = filtros_source.get("descricao")
            
            # Filtros base
            query = LancamentoAvulsoModel.query.filter(
                LancamentoAvulsoModel.tipo_movimentacao == 1,  # Receitas
                LancamentoAvulsoModel.ativo == True
            )
            
            # Aplicar filtros opcionais
            if data_inicio:
                try:
                    data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d')
                    query = query.filter(LancamentoAvulsoModel.data_cadastro >= data_inicio_obj)
                except:
                    pass
            
            if data_fim:
                try:
                    data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d')
                    # Adicionar 23:59:59 para incluir todo o dia
                    data_fim_obj = data_fim_obj.replace(hour=23, minute=59, second=59)
                    query = query.filter(LancamentoAvulsoModel.data_cadastro <= data_fim_obj)
                except:
                    pass
            
            if conta_bancaria_id:
                query = query.filter(LancamentoAvulsoModel.conta_bancaria_id == int(conta_bancaria_id))
            
            if status_pagamento:
                query = query.filter(LancamentoAvulsoModel.situacao_pagamento_id == int(status_pagamento))
            
            if descricao:
                query = query.filter(LancamentoAvulsoModel.descricao.ilike(f'%{descricao}%'))
            
            return query.order_by(LancamentoAvulsoModel.data_cadastro.desc()).all()
        else:
            return LancamentoAvulsoModel.query.filter(
                LancamentoAvulsoModel.tipo_movimentacao == 1,
                LancamentoAvulsoModel.ativo == True
            ).order_by(LancamentoAvulsoModel.data_cadastro.desc()).all()
    
    # Obtém os parâmetros de filtro corretos
    if request.method == "POST":
        dados_corretos = request.form if any(request.form.get(k) for k in ['dataInicio', 'dataFim', 'contaBancaria', 'statusPagamento', 'descricao']) else request.args
    else:
        dados_corretos = request.args
    
    registros = obter_registros_com_filtros()
    
    if request.method == "POST":
        if request.form.get("exportar_pdf"):
            logo_path = obter_url_absoluta_de_imagem("logo.png")
            html = render_template(
                "relatorios/relatorios_financeiros/relatorio_receitas_avulsas/exportar_relatorio_receitas_avulsas_pdf.html",
                logo_path=logo_path,
                changelog=changelog,
                dataHoje=dataHoje,
                dados_corretos=dados_corretos,
                registros=registros
            )
            
            nome_arquivo_saida = f"relatorio_receitas_avulsas_{dataHoje}"
            return ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida, "Portrait")
        
        if request.form.get("exportar_excel"):
            dados_excel = []
            
            for receita in registros:
                dados_excel.append({
                    "Data Cadastro": receita.data_cadastro.strftime("%d/%m/%Y %H:%M") if receita.data_cadastro else "",
                    "Descrição": receita.descricao or "",
                    "Valor": f"R$ {receita.valor_movimentacao_100 / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                    "Conta Bancária": receita.conta_bancaria.identificacao if receita.conta_bancaria else "N/A",
                    "Status": receita.situacao.situacao if receita.situacao else "Pendente",
                    "Usuário": f"{receita.usuario.nome} {receita.usuario.sobrenome}" if receita.usuario else "N/A"
                })
            
            nome_arquivo_saida = f"receitas_avulsas_{dataHoje}"
            return ManipulacaoArquivos.gerar_excel_from_dados(dados_excel, nome_arquivo_saida)
    
    return render_template(
        "relatorios/relatorios_financeiros/relatorio_receitas_avulsas/relatorio_receitas_avulsas.html",
        contas_bancarias=contas_bancarias,
        status_pagamentos=status_pagamentos,
        registros=registros,
        dados_corretos=dados_corretos
    )
