from datetime import datetime
from sistema import app, requires_roles, db
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.financeiro.movimentacao_financeira.movimentacao_financeira_model import MovimentacaoFinanceiraModel
from sistema.models_views.financeiro.movimentacao_financeira.saldo_movimentacao_financeira_model import SaldoMovimentacaoFinanceiraModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_model import CategorizacaoFiscalModel
from sistema.models_views.configuracoes_gerais.conta_bancaria.conta_bancaria_model import ContaBancariaModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_view import inicializar_categorias_padrao, obter_subcategorias_recursivo
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_view import inicializar_categorias_padrao_categorizacao_fiscal, obter_subcategorias_recursivo_categorizacao_fiscal
from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
from sistema._utilitarios import *

# === Nova Arquitetura de Créditos ===
from sistema.models_views.financeiro.controle_adiantamentos.servico_creditos import ServicoCreditos
from sistema.models_views.financeiro.controle_adiantamentos.transacao_credito_model import (
    TransacaoCreditoModel, TipoTransacaoCredito, TipoPessoa
)
from sistema.models_views.financeiro.controle_adiantamentos.faturamento_credito_vinculo_model import FaturamentoCreditoVinculoModel
from sistema.models_views.financeiro.controle_adiantamentos.historico_transacao_model import HistoricoTransacaoCreditoModel, AcaoHistoricoCredito


@app.route("/financeiro/extrato-terceiros/freteiros", methods=["GET"])
@login_required
@requires_roles
def saldo_freteiros():
    if any(request.args.values()):
        numero_documento = request.args.get('numeroDocumento')
        telefone = request.args.get('telefone')

        numeroDocumento = ValidaDocs.somente_numeros(numero_documento) if numero_documento else None
        numeroTelefone = ValidaDocs.somente_numeros(telefone) if telefone else None

        transportadoras = TransportadoraModel.filtrar_transportadoras(
            identificacao=request.args.get('identificacao'),
            numero_documento=numeroDocumento,
            telefone=numeroTelefone
        )
    else:
        transportadoras = TransportadoraModel.listar_transportadoras()

    # === Usando nova arquitetura via ServicoCreditos ===
    for t in transportadoras:
        t.valor_credito_100 = ServicoCreditos.obter_saldo_transportadora(t.id)

    return render_template(
        "financeiro/extrato_terceiros/listagem_terceiros/listagem_freteiros.html",
        transportadoras=transportadoras,
        dados_corretos=request.args
    )

@app.route("/financeiro/extrato-terceiros/freteiros/extrato-freteiro/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def extrato_freteiro(id):
    # === Usando nova arquitetura via ServicoCreditos ===
    extrato = ServicoCreditos.obter_historico_transportadora(id)
    transportadora = TransportadoraModel.obter_transportadora_por_id(id)

    if transportadora is None:
        flash(('Esta transportadora nâo possui dados a serem mostrados!', 'warning'))
        return redirect(url_for('saldo_freteiros'))

    saldo_credito_valor = ServicoCreditos.obter_saldo_transportadora(transportadora.id)

    return render_template(
        "/financeiro/extrato_terceiros/extrato_credito_terceiros/extrato_credito_freteiro.html",
        dados_corretos=request.form,
        extrato=extrato, saldo=saldo_credito_valor,
        transportadora=transportadora
    )


@app.route("/financeiro/extrato-terceiros/freteiros/lancar-credito/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def lancar_credito_freteiro(id):
    try:
        validacao_campos_obrigatorios = {}
        validacao_campos_erros = {}
        gravar_banco = True

        transportadora = TransportadoraModel.obter_transportadora_por_id(id)

        if not transportadora:
            flash(("Transportadora informado não existe!", "success"))
            return redirect(url_for("saldo_freteiros"))
        
        contas_bancarias = ContaBancariaModel.obter_contas_bancarias_ativas()
        # === Usando nova arquitetura via ServicoCreditos ===
        saldo_credito_valor = ServicoCreditos.obter_saldo_transportadora(transportadora.id)

        if request.method == 'POST':
            data_movimentacao = request.form.get("data_movimentacao")
            valor_credito = request.form.get("valor_credito")
            descricao = request.form.get("descricao")
            contaBancaria = request.form.get("contaBancaria", "")
            tipo_valor = request.form.get("tipo_valor", "positivo")
            
            campos = {
                "data_movimentacao": ["Data movimentação", data_movimentacao],
                "valor_credito": ["Valor", valor_credito],
                "descricao": ["Descrição", descricao],
                "contaBancaria": ["Conta bancária", contaBancaria],
            }

            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

            if not "validado" in validacao_campos_obrigatorios:
                gravar_banco = False
                flash((f"Verifique os campos destacados em vermelho!", "warning"))

            if gravar_banco:

                valor_credito_formatado = int(ValoresMonetarios.converter_string_brl_para_float(valor_credito) * 100)
                
                # Se o tipo for negativo, aplicar o sinal negativo ao valor
                if tipo_valor == "negativo":
                    valor_credito_formatado = -1 * valor_credito_formatado

                # === Usar ServicoCreditos para lançamento (compatível com legado e novo) ===
                resultado_lancamento = ServicoCreditos.lancar_credito_transportadora(
                    transportadora_id=transportadora.id,
                    valor_100=valor_credito_formatado,  # Mantém o sinal (positivo ou negativo)
                    descricao=descricao,
                    usuario_id=current_user.id,
                    data_movimentacao=datetime.strptime(data_movimentacao, '%Y-%m-%d').date() if isinstance(data_movimentacao, str) else data_movimentacao,
                    tipo_valor=tipo_valor,
                    conta_bancaria_id=int(contaBancaria) if contaBancaria else None,
                )

                # Registrar pontuação de cadastro
                acao = TipoAcaoEnum.CADASTRO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id, acao, acao.pontos, modulo="lancamento_credito_freteiro"
                )

                valor_faturamento = abs(valor_credito_formatado)
                # Determinar tipo de operação e direção baseado no tipo de valor
                if tipo_valor == "positivo":
                    tipo_operacao = 3  # Crédito
                    direcao_financeira = 2  # Despesa (empresa paga crédito ao freteiro)
                    valor_despesa = valor_faturamento
                    valor_receita = 0
                else:  # tipo_valor == "negativo" - Débito (freteiro deve para MBR)
                    tipo_operacao = 4  # Débito
                    direcao_financeira = 1  # Receita (freteiro deve à empresa)
                    valor_despesa = 0
                    valor_receita = valor_faturamento
                
                faturamento = FaturamentoModel(
                    usuario_id=current_user.id,
                    valor_total=valor_faturamento,
                    valor_bruto_total=valor_faturamento,
                    valor_despesa=valor_despesa,
                    valor_receita=valor_receita,
                    codigo_faturamento=FaturamentoModel.gerar_codigo_novo_faturamento(),
                    tipo_operacao=tipo_operacao,
                    direcao_financeira=direcao_financeira,
                    situacao_pagamento_id=7, # A categorizar
                )

                db.session.add(faturamento)
                db.session.flush()
                
                # === Atualizar faturamento_origem_id na transação de crédito ===
                transacao_nova_id = resultado_lancamento.get('novo_id')
                if transacao_nova_id:
                    transacao = TransacaoCreditoModel.query.get(transacao_nova_id)
                    if transacao:
                        transacao.faturamento_origem_id = faturamento.id

                conta_identificacao = ContaBancariaModel.obter_conta_por_id(contaBancaria)
                
                # === Registrar vínculo na nova arquitetura ===
                extrato_legado_id = resultado_lancamento.get('legado_id')
                
                detalhes_credito_transportadora = [{
                    "transportadora_id": transportadora.id,
                    "transportadora_identificacao": transportadora.identificacao,
                    "data_movimentacao": data_movimentacao,
                    "credito_descricao": descricao,
                    "valor_credito_100": int(valor_faturamento),
                    "extrato_credito_transportadora_id": extrato_legado_id,
                    "transacao_credito_id": transacao_nova_id,
                    "conta_bancaria_id": conta_identificacao.identificacao if conta_identificacao else "Sem informação",
                }]

                faturamento.salvar_detalhes(credito_transportadora=detalhes_credito_transportadora)
                
                if transacao_nova_id:
                    vinculo = FaturamentoCreditoVinculoModel(
                        faturamento_id=faturamento.id,
                        transacao_credito_id=transacao_nova_id,
                        tipo_pessoa=TipoPessoa.FRETEIRO,
                        valor_aplicado_100=valor_faturamento,
                        usuario_id=current_user.id,
                        extrato_credito_freteiro_id=extrato_legado_id,
                        transportadora_id=transportadora.id
                    )
                    db.session.add(vinculo)

                db.session.commit()
                tipo_msg = "Crédito" if tipo_valor == "positivo" else "Débito"
                flash((f"{tipo_msg} lançado com sucesso e faturamento registrado!", "success"))
                return redirect(url_for("saldo_freteiros"))

    except Exception as e:
        print(e)
        flash(('Houve um erro ao tentar cadastrar crédito para o freteiro! Entre em contato com o suporte.', 'warning'))
        return redirect(url_for('saldo_freteiros'))
    return render_template(
        "financeiro/extrato_terceiros/lancamento_credito_terceiros/lancar_credito_freteiro.html", campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
        transportadora=transportadora,
        contas_bancarias=contas_bancarias,
        saldo=saldo_credito_valor
    )


@app.route("/financeiro/extrato-terceiros/freteiros/excluir-credito/<int:credito_id>", methods=["POST"])
@login_required
@requires_roles
def excluir_credito_freteiro(credito_id):
    """
    Exclui um lançamento de crédito de freteiro/transportadora.
    Utiliza ServicoCreditos para operação unificada.
    """
    try:
        motivo = request.form.get("motivo", "")
        transportadora_id = request.form.get("transportadora_id")
        
        resultado = ServicoCreditos.excluir_credito(
            tipo='freteiro',
            credito_id=credito_id,
            usuario_id=current_user.id,
            motivo=motivo
        )
        
        if resultado['sucesso']:
            flash((resultado['mensagem'], "success"))
        else:
            flash((resultado['mensagem'], "warning"))
        
        if transportadora_id:
            return redirect(url_for("extrato_freteiro", id=transportadora_id))
        return redirect(url_for("saldo_freteiros"))
        
    except Exception as e:
        print(f"[ERRO excluir_credito_freteiro]: {e}")
        flash(("Erro ao excluir crédito. Entre em contato com o suporte.", "danger"))
        return redirect(url_for("saldo_freteiros"))


@app.route("/financeiro/extrato-terceiros/freteiros/editar-credito/<int:credito_id>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_credito_freteiro(credito_id):
    """
    Edita um lançamento de crédito de freteiro/transportadora.
    GET: Exibe formulário de edição
    POST: Processa a edição
    """
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    
    try:
        # Buscar crédito
        credito = TransacaoCreditoModel.query.get(credito_id)
        if not credito:
            flash(("Crédito não encontrado!", "warning"))
            return redirect(url_for("saldo_freteiros"))
        
        # Buscar transportadora
        transportadora = TransportadoraModel.obter_transportadora_por_id(credito.transportadora_id)
        if not transportadora:
            flash(("Freteiro não encontrado!", "warning"))
            return redirect(url_for("saldo_freteiros"))
        
        # Verificar se pode editar
        if credito.valor_utilizado_100 and credito.valor_utilizado_100 > 0:
            flash(("Este crédito já foi utilizado e não pode ser editado!", "warning"))
            return redirect(url_for("extrato_freteiro", id=transportadora.id))
        
        saldo_credito_valor = ServicoCreditos.obter_saldo_transportadora(transportadora.id)
        
        if request.method == "GET":
            return render_template(
                "financeiro/extrato_terceiros/lancamento_credito_terceiros/editar_credito_freteiro.html",
                credito=credito,
                transportadora=transportadora,
                saldo=saldo_credito_valor,
                campos_obrigatorios=validacao_campos_obrigatorios,
                campos_erros=validacao_campos_erros,
                dados_corretos={},
            )
        
        # POST: Processar edição
        valor_credito = request.form.get("valor_credito")
        descricao = request.form.get("descricao")
        data_movimentacao = request.form.get("data_movimentacao")
        transportadora_id = request.form.get("transportadora_id")
        tipo_valor = request.form.get("tipo_valor", "positivo")
        
        # Validação de campos obrigatórios
        campos = {
            "data_movimentacao": ["Data movimentação", data_movimentacao],
            "valor_credito": ["Valor", valor_credito],
            "descricao": ["Descrição", descricao],
            "tipo_valor": ["Tipo de valor", tipo_valor],
        }
        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
        
        if not "validado" in validacao_campos_obrigatorios:
            flash(("Verifique os campos destacados em vermelho!", "warning"))
            return render_template(
                "financeiro/extrato_terceiros/lancamento_credito_terceiros/editar_credito_freteiro.html",
                credito=credito,
                transportadora=transportadora,
                saldo=saldo_credito_valor,
                campos_obrigatorios=validacao_campos_obrigatorios,
                campos_erros=validacao_campos_erros,
                dados_corretos=request.form,
            )
        
        # Converter valor de BRL para centavos
        valor_100 = None
        if valor_credito:
            valor_100 = int(ValoresMonetarios.converter_string_brl_para_float(valor_credito) * 100)
            # Aplicar sinal negativo se tipo for negativo
            if tipo_valor == "negativo":
                valor_100 = -abs(valor_100)
            else:
                valor_100 = abs(valor_100)
        
        # Converter data
        data_mov = None
        if data_movimentacao:
            data_mov = datetime.strptime(data_movimentacao, '%Y-%m-%d').date()
        
        resultado = ServicoCreditos.editar_credito_transportadora(
            credito_id=credito_id,
            valor_100=valor_100,
            descricao=descricao if descricao else None,
            data_movimentacao=data_mov,
            tipo_valor=tipo_valor,
            usuario_id=current_user.id
        )
        
        if resultado['sucesso']:
            flash((resultado['mensagem'], "success"))
            
            # Registrar pontuação de edição
            try:
                PontuacaoUsuarioModel.registrar_acao(
                    usuario_id=current_user.id,
                    tipo_acao=TipoAcaoEnum.ATUALIZAR,
                    pontos=5,
                    descricao=f"Edição de lançamento de crédito ID {credito_id}"
                )
            except:
                pass  # Não falhar se pontuação der erro
        else:
            flash((resultado['mensagem'], "warning"))
        
        if transportadora_id:
            return redirect(url_for("extrato_freteiro", id=transportadora_id))
        return redirect(url_for("saldo_freteiros"))
        
    except Exception as e:
        print(f"[ERRO editar_credito_freteiro]: {e}")
        import traceback
        traceback.print_exc()
        flash(("Erro ao editar crédito. Entre em contato com o suporte.", "danger"))
        return redirect(url_for("saldo_freteiros"))
