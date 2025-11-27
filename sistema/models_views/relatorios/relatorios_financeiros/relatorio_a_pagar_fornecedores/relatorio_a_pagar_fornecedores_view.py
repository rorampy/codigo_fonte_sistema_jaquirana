from datetime import datetime
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem, formatar_data_para_brl
from flask import render_template, request, redirect, url_for, flash, session, jsonify, json
from flask_login import login_required, current_user
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.upload_arquivo.upload_arquivo_model import UploadArquivoModel
from sistema.models_views.faturamento.cargas_a_faturar.fornecedor.fornecedor_a_pagar_model import FornecedorPagarModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
from sistema.models_views.configuracoes_gerais.situacao_pagamento.situacao_pagamento_model import SituacaoPagamentoModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.faturamento.controle_credito.credito_agrupado.credito_fornecedor_model import CreditoFornecedorModel
from sistema.models_views.faturamento.controle_credito.credito_agrupado.credito_freteiro_model import CreditoFreteiroModel
from sistema.models_views.faturamento.controle_credito.credito_agrupado.credito_extrator_model import CreditoExtratorModel
from sistema.models_views.faturamento.controle_credito.extrato_credito.extrato_credito_fornecedor_model import ExtratoCreditoFornecedorModel
from sistema.models_views.faturamento.controle_credito.extrato_credito.extrato_credito_freteiro_model import ExtratoCreditoFreteiroModel
from sistema.models_views.faturamento.controle_credito.extrato_credito.extrato_credito_extrator_model import ExtratoCreditoExtratorModel
from sistema.models_views.financeiro.movimentacao_financeira.movimentacao_financeira_model import MovimentacaoFinanceiraModel
from sistema.models_views.financeiro.movimentacao_financeira.saldo_movimentacao_financeira_model import SaldoMovimentacaoFinanceiraModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.configuracoes_gerais.conta_bancaria.conta_bancaria_model import ContaBancariaModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_view import (inicializar_categorias_padrao, obter_subcategorias_recursivo)
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_view import (inicializar_categorias_padrao_categorizacao_fiscal, obter_subcategorias_recursivo_categorizacao_fiscal)
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_model import CategorizacaoFiscalModel
from sistema.models_views.faturamento.cargas_a_faturar.transportadora.frete_a_pagar_model import FretePagarModel
from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx
from sistema.models_views.importacao_ofx.importacao_ofx_view import limpar_dados_conciliacao
from sistema.models_views.importacao_ofx.importacao_ofx_view import verificar_e_limpar_conciliacao_incorreta
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
from sistema.models_views.gerenciar.motorista.motorista_model import MotoristaModel
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema._utilitarios import *
from sistema._utilitarios.utilitario_semanal import UtilitariosSemana

@app.route("/relatorios/relatorios-financeiros/a-pagar-fornecedores", methods=["GET", "POST"])
@login_required
@requires_roles
def relatorio_a_pagar_fornecedores():
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    dataHoje = datetime.now().strftime("%d-%m-%Y")
    bitola = BitolaModel.listar_bitolas_ativas()
    produtos = ProdutoModel.listar_produtos()
    statusPagamentos = SituacaoPagamentoModel.listar_status()
    
    def obter_registros_com_filtros():
        # Para POST, primeiro verifica se há filtros no form, senão usa args
        filtros_source = request.form if request.method == "POST" and any(request.form.values()) else request.args
        
        if any(filtros_source.values()):
            data_inicio = filtros_source.get("dataInicio")
            data_fim = filtros_source.get("dataFim")
            placa = filtros_source.get("placaCargaCliente")
            motorista = filtros_source.get("motoristaCargaCliente")
            transportadora = filtros_source.get("tranpostadoraCargaCliente")
            fornecedor = filtros_source.get("fornecedorCargaCliente")
            cliente = filtros_source.get("clienteCarga")
            numero_nf = filtros_source.get("numeroNfCliente")
            incompleto = filtros_source.get("registroIncompleto")
            statusPagamento = filtros_source.get("statusPagamento") or "Pendente"
            
            incompleto_bool = None
            if incompleto == "1":
                incompleto_bool = True
            elif incompleto == "0":
                incompleto_bool = False
            
            return FornecedorPagarModel.filtrar_fornecedores_agrupados(
                data_inicio=data_inicio,
                data_fim=data_fim,
                placa=placa,
                motorista=motorista,
                transportadora=transportadora,
                fornecedor=fornecedor,
                cliente=cliente,
                numero_nf=numero_nf,
                statusPagamento=statusPagamento
            )
        else:
            return FornecedorPagarModel.obter_fornecedores_agrupados()
    
    # Obtém os parâmetros de filtro corretos
    if request.method == "POST":
        # Para POST, preserva os filtros do args ou form
        dados_corretos = request.form if any(request.form.get(k) for k in ['dataInicio', 'dataFim', 'placaCargaCliente', 'motoristaCargaCliente', 'tranpostadoraCargaCliente', 'fornecedorCargaCliente', 'clienteCarga', 'numeroNfCliente', 'registroIncompleto', 'statusPagamento']) else request.args
    else:
        dados_corretos = request.args
    
    registros = obter_registros_com_filtros()
    
    if request.method == "POST":
        # Garantir que a exportação use os mesmos filtros
        registros_exportacao = registros  # Reutiliza os registros já filtrados

        if request.form.get("exportar_pdf"):
            logo_path = obter_url_absoluta_de_imagem("logo.png")
            html = render_template(
                "relatorios/relatorios_financeiros/relatorio_a_pagar_fornecedor/exportar_relatorio_a_pagar_fornecedor_pdf.html",
                logo_path=logo_path,
                changelog=changelog,
                dataHoje=dataHoje,
                dados_corretos=dados_corretos,
                registros=registros_exportacao
            )

            nome_arquivo_saida = f"relacao_fornecedores_a_pagar_{dataHoje}"
            return ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida, "Landscape")
        
        if request.form.get("exportar_excel"):
            dados_excel = []
            registros_por_origem = {}
            
            for item in registros_exportacao:
                origem = item.get("origem", "Sem origem")
                if origem not in registros_por_origem:
                    registros_por_origem[origem] = {}
                    
                produto = item.get("produto", "Sem produto")
                if produto not in registros_por_origem[origem]:
                    registros_por_origem[origem][produto] = []
                    
                registros_por_origem[origem][produto].append(item)

            for origem in sorted(registros_por_origem.keys()):
                produtos_origem = registros_por_origem[origem]
                
                dados_excel.append({
                    "Origem": origem.upper(),
                    "Data Entrega": "",
                    "Placa/Motorista": "",
                    "Transportadora": "",
                    "Bitola": "",
                    "Peso Ticket": "",
                    "Número NF": "",
                    "A pagar fornecedor": "",
                    "Status pagamento": "",
                    "Incompleto": "",
                })
                
                for produto in sorted(produtos_origem.keys()):
                    registros_produto = produtos_origem[produto]
                    
                    dados_excel.append({
                        "Origem": f"  PRODUTO: {produto}",
                        "Data Entrega": "",
                        "Placa/Motorista": "",
                        "Transportadora": "",
                        "Bitola": "",
                        "Peso Ticket": "",
                        "Número NF": "",
                        "A pagar fornecedor": "",
                        "Status pagamento": "",
                        "Incompleto": "",
                    })
                    
                    total_produto = 0
                    
                    for item in registros_produto:
                        registro = item["registro"]
                        
                        motorista_nome = ""
                        if (registro.solicitacao and 
                            registro.solicitacao.motorista and 
                            registro.solicitacao.motorista.nome_completo):
                            nome_split = registro.solicitacao.motorista.nome_completo.split()
                            if len(nome_split) > 1:
                                motorista_nome = f"{nome_split[0]} {nome_split[1][0]}."
                            else:
                                motorista_nome = nome_split[0]
                        
                        placa = (registro.solicitacao.veiculo.placa_veiculo 
                                if registro.solicitacao and registro.solicitacao.veiculo 
                                and registro.solicitacao.veiculo.placa_veiculo else "")
                        placa_motorista = f"{placa} | {motorista_nome}" if motorista_nome else placa
                        
                        transportadora = ""
                        if (registro.solicitacao and 
                            registro.solicitacao.transportadora_exibicao and 
                            registro.solicitacao.transportadora_exibicao.identificacao):
                            transportadora = registro.solicitacao.transportadora_exibicao.identificacao
                        else:
                            transportadora = ""
                        
                        bitola = ""
                        if (registro.solicitacao and 
                            registro.solicitacao.bitola and 
                            registro.solicitacao.bitola.bitola):
                            bitola = registro.solicitacao.bitola.bitola
                        else:
                            bitola = ""
                        
                        peso_ticket = ""
                        if hasattr(item, 'registro_operacional') and item.registro_operacional.peso_liquido_ticket:
                            peso_ticket = f"{item.registro_operacional.peso_liquido_ticket} Ton."
                        else:
                            peso_ticket = "Sem peso"
                        
                        numero_nf = ""
                        if hasattr(item, 'registro_operacional'):
                            if item.registro_operacional.estorno_nf:
                                numero_nf = f"{item.registro_operacional.numero_nota_fiscal_estorno} *"
                            elif item.registro_operacional.numero_nota_fiscal:
                                numero_nf = item.registro_operacional.numero_nota_fiscal
                            else:
                                numero_nf = ""
                        else:
                            numero_nf = ""
                        
                        valor_pagar = 0
                        if registro.valor_total_a_pagar_100:
                            valor_pagar = registro.valor_total_a_pagar_100 / 100
                            total_produto += valor_pagar
                        
                        status = registro.situacao.situacao if registro.situacao else "Pendente"
                        incompleto = "Sim" if registro.incompleto else "Não"
                        
                        dados_excel.append({
                            "Origem": "",
                            "Data Entrega": (registro.data_entrega_ticket.strftime("%d/%m/%Y") 
                                        if registro.data_entrega_ticket else ""),
                            "Placa/Motorista": placa_motorista,
                            "Transportadora": transportadora,
                            "Bitola": bitola,
                            "Peso Ticket": peso_ticket,
                            "Número NF": numero_nf,
                            "A pagar fornecedor": f"{valor_pagar:,.2f}" if valor_pagar > 0 else "",
                            "Status pagamento": status,
                            "Incompleto": incompleto,
                        })
                    
                    if registros_produto and total_produto > 0:
                        dados_excel.append({
                            "Origem": "",
                            "Data Entrega": "",
                            "Placa/Motorista": "",
                            "Transportadora": "",
                            "Bitola": "",
                            "Peso Ticket": "",
                            "Número NF": "",
                            "A pagar fornecedor": f"TOTAL A PAGAR: R$ {total_produto:,.2f}",
                            "Status pagamento": "",
                            "Incompleto": "",
                        })
                    
                    dados_excel.append({
                        "Origem": "",
                        "Data Entrega": "",
                        "Placa/Motorista": "",
                        "Transportadora": "",
                        "Bitola": "",
                        "Peso Ticket": "",
                        "Número NF": "",
                        "A pagar fornecedor": "",
                        "Status pagamento": "",
                        "Incompleto": "",
                    })
                
                dados_excel.append({
                    "Origem": "",
                    "Data Entrega": "",
                    "Placa/Motorista": "",
                    "Transportadora": "",
                    "Bitola": "",
                    "Peso Ticket": "",
                    "Número NF": "",
                    "A pagar fornecedor": "",
                    "Status pagamento": "",
                    "Incompleto": "",
                })

            nome_arquivo_saida = f"relatorio-fornecedores-a-pagar-{dataHoje}"
            return ManipulacaoArquivos.exportar_excel(dados_excel, nome_arquivo_saida)

    return render_template(
        "relatorios/relatorios_financeiros/relatorio_a_pagar_fornecedor/relatorio_a_pagar_fornecedor.html",
        registros=registros,
        bitola=bitola,
        produtos=produtos,
        statusPagamentos=statusPagamentos,
        dados_corretos=dados_corretos,
    )

