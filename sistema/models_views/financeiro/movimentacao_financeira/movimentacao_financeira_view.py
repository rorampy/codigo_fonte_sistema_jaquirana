from datetime import datetime
import io
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem
from werkzeug.utils import secure_filename
from flask import render_template, request, redirect, url_for, flash, session, jsonify, Response
from flask_login import login_required, current_user
from sistema.models_views.financeiro.movimentacao_financeira.movimentacao_financeira_model import MovimentacaoFinanceiraModel
from sistema.models_views.financeiro.movimentacao_financeira.saldo_movimentacao_financeira_model import SaldoMovimentacaoFinanceiraModel
from sistema.models_views.faturamento.cargas_a_faturar.transportadora.frete_a_pagar_model import FretePagarModel
from sistema.models_views.faturamento.cargas_a_faturar.extrator.extrator_a_pagar_model import ExtratorPagarModel
from sistema.models_views.faturamento.cargas_a_faturar.fornecedor.fornecedor_a_pagar_model import FornecedorPagarModel
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.configuracoes_gerais.conta_bancaria.conta_bancaria_model import ContaBancariaModel
from sistema.models_views.configuracoes_gerais.centro_custo.centro_custo_model import CentroCustoModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_model import CategorizacaoFiscalModel
from sistema.models_views.financeiro.movimentacao_financeira.lancamento_movimentacao_extra_model import LancamentoMovimentacaoExtraModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_view import inicializar_categorias_padrao, obter_subcategorias_recursivo
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_view import inicializar_categorias_padrao_categorizacao_fiscal, obter_subcategorias_recursivo_categorizacao_fiscal
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx
from sistema.models_views.importacao_ofx.importacao_ofx_service import ImportacaoOfxService
from sistema.models_views.importacao_ofx.importacao_ofx_view import limpar_dados_conciliacao
from sistema.models_views.importacao_ofx.importacao_ofx_view import verificar_e_limpar_conciliacao_incorreta
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema._utilitarios import *


@app.context_processor
def inject_contas_bancarias():
    contas = ContaBancariaModel.obter_contas_bancarias_ativas()
    return {"contas_bancarias": contas}

    

@app.route("/financeiro/movimentacoes-financeiras/listagem", methods=["GET", "POST"])
@login_required
@requires_roles
def movimentacoes_financeiras():
    conta_selecionada_id = request.args.get("conta_bancaria_id", type=int)
    stats_transacoes = ImportacaoOfxService.obter_estatisticas_transacoes()

    transacoes_nao_conciliadas = stats_transacoes.get('nao_conciliadas', 0)

    movimentacoes = MovimentacaoFinanceiraModel.listagem_movimentacoes_financeiras_por_conta(conta_selecionada_id)
    contas_bancarias = ContaBancariaModel.obter_contas_bancarias_ativas()
    saldo = SaldoMovimentacaoFinanceiraModel.obter_registro_saldo_por_conta_bancaria(conta_selecionada_id)
    saldo_disponivel = saldo

    a_pagar_frete = FretePagarModel.obter_valor_total_a_pagar()
    a_pagar_fornecedor = FornecedorPagarModel.obter_valor_total_a_pagar()
    a_pagar_extrator = ExtratorPagarModel.obter_valor_total_a_pagar()

    valor_total_pagar = int(a_pagar_frete + a_pagar_fornecedor + a_pagar_extrator)

    total_a_receber = RegistroOperacionalModel.obter_valor_total_a_receber_por_conta(conta_selecionada_id)
    total_recebido = MovimentacaoFinanceiraModel.obter_valor_total_recebidos(conta_selecionada_id)

    valor_total_pago = MovimentacaoFinanceiraModel.obter_valor_total_saidas(conta_selecionada_id)

    return render_template(
        "financeiro/movimentacoes_financeiras/listagem_movimentacoes_financeiras.html",
        movimentacoes=movimentacoes,
        conta_selecionada_id=conta_selecionada_id,
        dados_corretos=request.form,
        saldo_disponivel=saldo_disponivel,
        valor_total_pagar=valor_total_pagar,
        contas_bancarias=contas_bancarias,
        valor_total_pago=valor_total_pago,
        total_a_receber=total_a_receber,
        total_recebido=total_recebido,
        transacoes_nao_conciliadas=transacoes_nao_conciliadas
    )


@app.route("/financeiro/movimentacoes-financeiras/nova-movimentacao", methods=["GET", "POST"])
@login_required
@requires_roles
def nova_movimentacao_financeira():
    try:
        validacao_campos_obrigatorios = {}
        validacao_campos_erros = {}
        gravar_banco = True

        dados_conciliacao = session.get('dados_conciliacao', {})
        tipo_conciliacao = dados_conciliacao.get('tipo_conciliacao', '')

        if tipo_conciliacao in ['outros_pagamentos', 'outros_recebimentos']:
            verificar_e_limpar_conciliacao_incorreta(tipo_conciliacao)
        else:
            verificar_e_limpar_conciliacao_incorreta('outros_pagamentos') 

        dados_conciliacao = session.get('dados_conciliacao', {})
        conciliar_transacao_id = dados_conciliacao.get('transacao_id')
        
        tem_diferenca = dados_conciliacao.get('tem_diferenca', False)
        transacao_ofx_id = dados_conciliacao.get('transacao_ofx_id')
        registro_recebimento_id = dados_conciliacao.get('registro_recebimento_id')

        contas_bancarias = ContaBancariaModel.obter_contas_bancarias_ativas()
        centros_custo = CentroCustoModel.obter_centro_custos_ativos()

        inicializar_categorias_padrao()
        principais = PlanoContaModel.buscar_principais()
        estrutura = []
        for cat in principais:
            d = cat.to_dict()
            d["children"] = obter_subcategorias_recursivo(cat.id)
            estrutura.append(d)

        inicializar_categorias_padrao_categorizacao_fiscal()
        principais_fiscal = CategorizacaoFiscalModel.buscar_principais()
        estrutura_fiscal = []
        for cat in principais_fiscal:
            d = cat.to_dict()
            d["children"] = obter_subcategorias_recursivo_categorizacao_fiscal(cat.id)
            estrutura_fiscal.append(d)

        transacao_ofx = None
        if conciliar_transacao_id:
            transacao_ofx = ImportacaoOfx.query.get(conciliar_transacao_id)

        dados_preenchidos = {}
        if tem_diferenca:
            dados_preenchidos = {
                'tipoMovimentacao': dados_conciliacao.get('tipo_movimentacao_predefinido', 'receita'),
                'valor': dados_conciliacao.get('valor_sem_formatacao', ''),
                'descricao': dados_conciliacao.get('descricao_sugerida', ''),
                'vencimento': dados_conciliacao.get('vencimento', ''),
                'mesAno': dados_conciliacao.get('mesAno', ''),
                'contaBancaria': '1'  
            }

        if request.method == "POST":
            tipoMovimentacao = request.form.get("tipoMovimentacao", "")
            vencimento = request.form.get("vencimento", "")
            descricao = request.form.get("descricao", "")
            mesAno = request.form.get("mesAno", "")
            valor = request.form.get("valor", "")
            planoContas = request.form.get("planoContas", "")
            categoriaFiscal = request.form.get("categoriaFiscal", "")
            contaBancaria = request.form.get("contaBancaria", "")
            centroCusto = request.form.get("centroCusto", "")

            campos = {
                "tipoMovimentacao": ["Tipo movimentação", tipoMovimentacao],
                "vencimento": ["Vencimento", vencimento],
                "descricao": ["Descrição", descricao],
                "mesAno": ["Mês/Ano", mesAno],
                "valor": ["Valor", valor],
                "planoContas": ["Plano contas", planoContas],
                "categoriaFiscal": ["Categoria fiscal", categoriaFiscal],
                "contaBancaria": ["Conta bancária", contaBancaria],
            }

            tipo_movimentacao = 1 if tipoMovimentacao == "receita" else 2

            if tipo_movimentacao == 2:
                campos["centroCusto"] = ["Centro custo", centroCusto]
            
            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

            if not "validado" in validacao_campos_obrigatorios:
                gravar_banco = False
                flash((f"Verifique os campos destacados em vermelho!", "warning"))

            if gravar_banco == True:
                valor_formatado = (
                    ValoresMonetarios.converter_string_brl_para_float(valor) * 100
                )

                lancamento_extra = LancamentoMovimentacaoExtraModel(
                    tipo_movimentacao=tipo_movimentacao,
                    vencimento=vencimento,
                    descricao=descricao,
                    mes_ano=mesAno,
                    valor_movimentacao_100=valor_formatado,
                    plano_conta_id=planoContas,
                    categorizacao_fiscal_id=categoriaFiscal,
                    conta_bancaria_id=contaBancaria,
                    centro_custo_id=centroCusto if tipo_movimentacao == 2 else None,
                    usuario_id=current_user.id,
                )

                db.session.add(lancamento_extra)
                db.session.flush()

                movimentacao = MovimentacaoFinanceiraModel(
                    tipo_movimentacao=tipo_movimentacao,
                    usuario_id=current_user.id,
                    data_movimentacao=datetime.now(),
                    lancamento_movimentacao_id=lancamento_extra.id,
                    conta_bancaria_id=contaBancaria,
                    valor_movimentacao_100=valor_formatado if tipo_movimentacao == 1 else valor_formatado,
                    conciliacao_bancaria=True if transacao_ofx else False,
                    importacao_ofx_id=transacao_ofx.id if transacao_ofx else None,
                    movimentacao_extra=1 if transacao_ofx else 0
                )
                db.session.add(movimentacao)

                saldo_total = SaldoMovimentacaoFinanceiraModel.obter_registro_conta_bancaria(contaBancaria)
                if saldo_total == None:
                    saldo = SaldoMovimentacaoFinanceiraModel(
                        data_movimentacao=datetime.now(),
                        valor_total_saldo_100= valor_formatado if tipo_movimentacao == 1 else -valor_formatado,
                        conta_bancaria_id=contaBancaria
                    )
                    db.session.add(saldo)
                else:
                    valor_saldo_novo = valor_formatado if tipo_movimentacao == 1 else -valor_formatado
                    saldo_total.data_movimentacao = datetime.now()
                    saldo_total.valor_total_saldo_100 += valor_saldo_novo
                    saldo_total.conta_bancaria_id = contaBancaria
                
                if tem_diferenca and transacao_ofx_id:
                    transacao_diferenca = ImportacaoOfx.query.get(transacao_ofx_id)
                    if transacao_diferenca:
                        observacao_diferenca = f"Diferença de conciliação - Transação OFX {transacao_diferenca.fitid}"
                        lancamento_extra.descricao = observacao_diferenca

                if transacao_ofx and not transacao_ofx.conciliado:
                    transacao_ofx.conciliado = True
                    tipo_conciliacao_atual = dados_conciliacao.get('tipo_conciliacao', 'outros_pagamentos')
                    transacao_ofx.tipo_conciliacao = tipo_conciliacao_atual
                    
                    transacao_ofx.pagamento_id = lancamento_extra.id
                    if tipo_movimentacao == 1:
                        observacao = f"Conciliado com receita extra ID {lancamento_extra.id}"
                    else:
                        observacao = f"Conciliado com despesa extra ID {lancamento_extra.id}"
                    
                    transacao_ofx.data_conciliacao = datetime.now()
                    transacao_ofx.usuario_conciliacao_id = current_user.id
                    transacao_ofx.observacoes_conciliacao = observacao
                    
                else:
                    pass

                acao = TipoAcaoEnum.CADASTRO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    acao,
                    acao.pontos,
                    modulo="movimentacao_financeira_extra",
                )

                db.session.commit()

                if tem_diferenca:
                    limpar_dados_conciliacao()
                    flash(("Diferença de conciliação lançada com sucesso!", "success"))
                    return redirect(url_for("listagem_ofx"))
                elif conciliar_transacao_id:
                    limpar_dados_conciliacao()
                    flash(("Movimentação cadastrada e transação OFX conciliada com sucesso!", "success"))
                    return redirect(url_for("listagem_ofx"))
                else:
                    flash(("Movimentação cadastrada com sucesso!", "success"))
                    return redirect(url_for("movimentacoes_financeiras"))
                
    except Exception as e:
        db.session.rollback()
        
        dados_conciliacao = session.get('dados_conciliacao', {})
        if dados_conciliacao.get('transacao_id') or dados_conciliacao.get('tem_diferenca'):
            limpar_dados_conciliacao()
        flash(("Erro ao tentar cadastrar nova movimentação! Entre em contato com o suporte.", "warning"))
        return redirect(url_for("nova_movimentacao_financeira"))

    return render_template(
        "financeiro/movimentacoes_financeiras/nova_movimentacao/nova_movimentacao_cadastrar.html",
        contas_bancarias=contas_bancarias,
        centros_custo=centros_custo,
        estrutura_plano=estrutura,
        estrutura_fiscal=estrutura_fiscal,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=dados_preenchidos if tem_diferenca else request.form,
        conciliar_transacao_id=conciliar_transacao_id,
        valor_conciliar=dados_conciliacao.get('valor'),
        data_conciliar=dados_conciliacao.get('data'),
        descricao_conciliar=dados_conciliacao.get('descricao'),
        fitid_conciliar=dados_conciliacao.get('fitid'),
        dados_conciliacao=dados_conciliacao,
        tem_diferenca=tem_diferenca,
        valor_diferenca=int(dados_conciliacao.get('valor_sem_formatacao') * 100) if tem_diferenca else None,
        tipo_diferenca=dados_conciliacao.get('tipo_movimentacao_predefinido') if tem_diferenca else None
    )


