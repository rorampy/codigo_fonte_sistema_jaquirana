from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sistema import app, db, requires_roles
from sistema._utilitarios.validador_formularios import ValidaForms
from sistema._utilitarios.valores_monetarios import ValoresMonetarios
from sistema.models_views.financeiro.lancamento_avulso.lancamento_avulso_model import LancamentoAvulsoModel
from sistema.models_views.configuracoes_gerais.conta_bancaria.conta_bancaria_model import ContaBancariaModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.financeiro.operacional.categorizar_fatura.categorizacao_model import AgendamentoPagamentoModel
from sistema.models_views.financeiro.movimentacao_financeira.movimentacao_financeira_model import MovimentacaoFinanceiraModel
from sistema.models_views.financeiro.movimentacao_financeira.saldo_movimentacao_financeira_model import SaldoMovimentacaoFinanceiraModel
from sistema.models_views.faturamento.cargas_a_faturar.fornecedor.fornecedor_a_pagar_model import FornecedorPagarModel
from sistema.models_views.faturamento.cargas_a_faturar.transportadora.frete_a_pagar_model import FretePagarModel
from sistema.models_views.faturamento.cargas_a_faturar.extrator.extrator_a_pagar_model import ExtratorPagarModel
from sistema.models_views.faturamento.cargas_a_faturar.comissionado.comissionado_a_pagar_model import ComissionadoPagarModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_view import (inicializar_categorias_padrao, obter_estrutura_com_folhas)
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_view import (inicializar_categorias_padrao_categorizacao_fiscal, obter_subcategorias_recursivo_categorizacao_fiscal)
from sistema.models_views.configuracoes_gerais.centro_custo.centro_custo_model import CentroCustoModel
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_model import CategorizacaoFiscalModel
from sistema.models_views.gerenciar.pessoa_financeiro.pessoa_financeiro_model import PessoaFinanceiroModel
from sistema.models_views.configuracoes_gerais.situacao_pagamento.situacao_pagamento_model import SituacaoPagamentoModel
from sistema._utilitarios import *
from datetime import date, datetime
from sistema.models_views.financeiro.operacional.categorizar_fatura.parcela_categorizacao.parcela_categorizacao_model import ParcelaCategorizacaoModel
import json


@app.route("/financeiro/despesas-avulsas", methods=["GET"])
@login_required
@requires_roles
def listagem_despesas_avulsas():
    """Lista todas as despesas avulsas ativas baseadas nos agendamentos com paginação"""
    try:
        pagina = request.args.get('pagina', 1, type=int)
        por_pagina = request.args.get('por_pagina', 200, type=int)
        
        termo_pesquisa = request.args.get('pesquisa', '').strip()
        data_inicio = request.args.get('data_inicio', '').strip()
        data_fim = request.args.get('data_fim', '').strip()

        if pagina < 1:
            pagina = 1
        if por_pagina < 1 or por_pagina > 200:
            por_pagina = 200
            
        resultado_paginacao = AgendamentoPagamentoModel.listar_despesas_avulsas_agendamentos(
            pagina=pagina,
            por_pagina=por_pagina,
            termo_pesquisa=termo_pesquisa,
            data_inicio=data_inicio or None,
            data_fim=data_fim or None
        )
        
        contas_bancarias = ContaBancariaModel.obter_contas_bancarias_ativas()
        
        return render_template(
            "financeiro/lancamento_avulso/despesas_avulsas/despesa_avulsa_listagem.html",
            agendamentos=resultado_paginacao['agendamentos'],
            contas_bancarias=contas_bancarias,
            paginacao=resultado_paginacao
        )
        
    except Exception as e:
        flash(("Erro ao carregar listagem de despesas! Contate o suporte.", "warning"))
        return redirect(url_for("listagem_despesas_avulsas"))


@app.route("/financeiro/despesa-avulsa/cadastrar", methods=["GET", "POST"])
@login_required
def cadastrar_despesa_avulsa():
    """Cadastra uma nova despesa avulsa com categorização completa"""
    
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    dados_corretos = {}
    gravar_banco = True
    
    pessoas_financeiro = PessoaFinanceiroModel.listar_pessoas_ativas()
    for p in pessoas_financeiro:
        if p.numero_documento and len(p.numero_documento.strip()) > 0:
            p.documento_formatado = ValidaDocs.insere_pontuacao_cnpj(p.numero_documento) if len(p.numero_documento) == 14 else ValidaDocs.insere_pontuacao_cpf(p.numero_documento)
        else:
            p.documento_formatado = "N/A"
    
    situacoes_pagamento = SituacaoPagamentoModel.listar_status()
    centros_custo = CentroCustoModel.obter_centro_custos_ativos()
    contas_bancarias = ContaBancariaModel.obter_contas_bancarias_ativas()
    
    inicializar_categorias_padrao()
    estrutura_plano_contas = obter_estrutura_com_folhas([2])

    inicializar_categorias_padrao_categorizacao_fiscal()
    principais_fiscal = CategorizacaoFiscalModel.buscar_filhos(2)
    estrutura_fiscal = []
    for cat in principais_fiscal:
        categoria_data = {'id': cat.id, 'codigo': cat.codigo, 'nome': cat.nome, 'children': []}
        categoria_data['children'] = obter_subcategorias_recursivo_categorizacao_fiscal(cat.id)
        estrutura_fiscal.append(categoria_data)
    
    try:
        
        if request.method == "POST":
            data_vencimento = request.form.get("data_vencimento", "")
            data_competencia = request.form.get("data_competencia", "")
            conta_bancaria_id = request.form.get("conta_bancaria_id", "")
            pessoa_financeiro_id = request.form.get("pessoa_financeiro_id", "")
            descricao = request.form.get("descricao", "")
            referencia = request.form.get("referencia", "")
            valor = request.form.get("valor", "").strip()

            categorias_json = request.form.get("categorias_json", "")
            centros_custo_json = request.form.get("centros_custo_json", "")
            valores_detalhados_ativo = request.form.get("valores_detalhados_ativo") == "true"
            parcelamento_ativo = request.form.get("parcelamento_ativo") == "true"
            numero_parcelas = request.form.get("numero_parcelas", "")
            dias_entre_parcelas = request.form.get("dias_entre_parcelas", "30")
            parcelas_json = request.form.get("parcelas_json", "")

            dados_corretos = {
                'data_vencimento': data_vencimento,
                'data_competencia': data_competencia,
                'conta_bancaria_id': conta_bancaria_id,
                'pessoa_financeiro_id': pessoa_financeiro_id,
                'descricao': descricao,
                'referencia': referencia,
                'valor': valor,
                'categorias_json': categorias_json,
                'centros_custo_json': centros_custo_json,
                'valores_detalhados_ativo': valores_detalhados_ativo,
                'parcelamento_ativo': parcelamento_ativo,
                'numero_parcelas': numero_parcelas,
                'dias_entre_parcelas': dias_entre_parcelas,
                'parcelas_json': parcelas_json
            }

            if not data_vencimento.strip():
                validacao_campos_obrigatorios['data_vencimento'] = 'Campo obrigatório'
            
            if not pessoa_financeiro_id.strip():
                validacao_campos_obrigatorios['pessoa_financeiro_id'] = 'Campo obrigatório'
                
            if not conta_bancaria_id.strip():
                validacao_campos_obrigatorios['conta_bancaria_id'] = 'Campo obrigatório'
            


            if not descricao.strip():
                validacao_campos_obrigatorios['descricao'] = 'Campo obrigatório'

            if not valor.strip():
                validacao_campos_obrigatorios['valor'] = 'Campo obrigatório'

            data_vencimento_obj = None
            if data_vencimento:
                try:
                    data_vencimento_obj = datetime.strptime(data_vencimento, '%Y-%m-%d').date()
                except ValueError:
                    validacao_campos_erros['data_vencimento'] = 'Data inválida'

            data_competencia_obj = None
            if data_competencia:
                try:
                    data_competencia_obj = datetime.strptime(f"01/{data_competencia}", '%d/%m/%Y').date()
                except ValueError:
                    validacao_campos_erros['data_competencia'] = 'Competência inválida'

            valor_float = 0
            if valor:
                try:
                    valor_float = ValoresMonetarios.converter_string_brl_para_float(valor)
                    if valor_float <= 0:
                        validacao_campos_erros['valor'] = 'Valor deve ser maior que zero'
                except:
                    validacao_campos_erros['valor'] = 'Valor inválido'

            categorias_obj = None
            if not categorias_json or not categorias_json.strip():
                validacao_campos_obrigatorios['categorias_json'] = 'Deve haver pelo menos uma categoria informada'
            else:
                try:
                    categorias_obj = json.loads(categorias_json) if isinstance(categorias_json, str) else categorias_json
                    if not isinstance(categorias_obj, list) or len(categorias_obj) == 0:
                        validacao_campos_erros['categorias_json'] = 'Deve haver pelo menos uma categoria'
                    else:
                        soma_categorias = 0
                        for i, categoria in enumerate(categorias_obj, 1):
                            if not categoria.get('categoria_id'):
                                validacao_campos_erros['categorias_json'] = f'Categoria {i}: ID da categoria é obrigatório'
                                break
                            if not categoria.get('valor') or int(categoria.get('valor', 0)) <= 0:
                                validacao_campos_erros['categorias_json'] = f'Categoria {i}: Valor deve ser maior que zero'
                                break
                                
                            try:
                                valor_categoria_centavos = float(categoria['valor'])
                                valor_categoria = valor_categoria_centavos / 100
                                soma_categorias += valor_categoria
                            except:
                                validacao_campos_erros['categorias_json'] = f'Categoria {i}: Valor inválido'
                                break
                        
                        if 'categorias_json' not in validacao_campos_erros and valor_float > 0:
                            if soma_categorias > valor_float:
                                validacao_campos_erros['categorias_json'] = f'A soma dos valores das categorias não pode ser maior que o valor total'
                            elif soma_categorias < valor_float:
                                validacao_campos_erros['categorias_json'] = f'A soma dos valores das categorias deve ser igual ao valor total'
                except:
                    validacao_campos_erros['categorias_json'] = 'JSON de categorias inválido'

            centros_custo_obj = []
            if valores_detalhados_ativo:
                if centros_custo_json:
                    try:
                        centros_custo_obj = json.loads(centros_custo_json) if isinstance(centros_custo_json, str) else centros_custo_json
                        if not isinstance(centros_custo_obj, list):
                            validacao_campos_erros['centros_custo_json'] = 'Formato de centros de custo inválido'
                    except:
                        validacao_campos_erros['centros_custo_json'] = 'JSON de centros de custo inválido'
                else:
                    validacao_campos_obrigatorios['centros_custo_json'] = 'Centros de custo são obrigatórios quando valores detalhados estão ativos'

            parcelas_obj = []
            if parcelamento_ativo:
                if not numero_parcelas or int(numero_parcelas) < 2:
                    validacao_campos_erros['numero_parcelas'] = 'Número de parcelas deve ser maior que 1'
                
                if parcelas_json:
                    try:
                        parcelas_obj = json.loads(parcelas_json) if isinstance(parcelas_json, str) else parcelas_json
                        if not isinstance(parcelas_obj, list) or len(parcelas_obj) == 0:
                            validacao_campos_erros['parcelas_json'] = 'Deve haver pelo menos uma parcela'
                    except:
                        validacao_campos_erros['parcelas_json'] = 'JSON de parcelas inválido'
                else:
                    validacao_campos_obrigatorios['parcelas_json'] = 'Parcelas são obrigatórias quando parcelamento está ativo'

            if validacao_campos_obrigatorios or validacao_campos_erros:
                gravar_banco = False
                flash(("Verifique os campos destacados em vermelho!", "warning"))

            if gravar_banco:
                valor_formatado = int(valor_float * 100)

                nova_despesa = LancamentoAvulsoModel(
                    tipo_movimentacao=2,
                    descricao=descricao,
                    valor_movimentacao_100=valor_formatado,
                    usuario_id=current_user.id,
                    situacao_pagamento_id=6
                )

                db.session.add(nova_despesa)
                db.session.flush()

                novo_agendamento = AgendamentoPagamentoModel(
                    faturamento_id=None,
                    lancamento_avulso_id=nova_despesa.id,
                    pessoa_financeiro_id=int(pessoa_financeiro_id),
                    data_vencimento=data_vencimento_obj,
                    valor_total_100=valor_formatado,
                    descricao=descricao if descricao else None,
                    referencia=referencia if referencia else None,
                    data_competencia=data_competencia_obj,
                    categorias_json=categorias_obj,
                    centros_custo_json=centros_custo_obj,
                    parcelamento_ativo=parcelamento_ativo,
                    numero_parcelas=int(numero_parcelas) if numero_parcelas else None,
                    dias_entre_parcelas=int(dias_entre_parcelas),
                    conta_bancaria_id=conta_bancaria_id,
                    situacao_pagamento_id=6
                )

                db.session.add(novo_agendamento)
                db.session.flush()

                nova_despesa.situacao_pagamento_id = 6

                if parcelamento_ativo and parcelas_json:
                    try:
                        parcelas_dados = json.loads(parcelas_json) if isinstance(parcelas_json, str) else parcelas_json
                        if isinstance(parcelas_dados, list):
                            for i, parcela_data in enumerate(parcelas_dados, 1):
                                nova_parcela = ParcelaCategorizacaoModel(
                                    agendamento_id=novo_agendamento.id,
                                    numero_parcela=i,
                                    data_vencimento=datetime.strptime(parcela_data['vencimento'], '%Y-%m-%d').date(),
                                    valor_parcela=int(parcela_data['valor']),
                                    descricao=parcela_data.get('descricao', ''),
                                    referencia=parcela_data.get('referencia', ''),
                                    situacao_pagamento_id=2
                                )
                                db.session.add(nova_parcela)
                    except Exception as e:
                        import traceback
                        traceback.print_exc()

                acao = TipoAcaoEnum.CADASTRO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    acao,
                    acao.pontos,
                    modulo="despesa_avulsa"
                )

                db.session.commit()

                flash(("Despesa cadastrada e categorizada com sucesso!", "success"))
                return redirect(url_for("listagem_despesas_avulsas"))

        return render_template(
            "financeiro/lancamento_avulso/despesas_avulsas/despesa_avulsa_cadastrar_novo.html",
            campos_obrigatorios=validacao_campos_obrigatorios,
            campos_erros=validacao_campos_erros,
            dados_corretos=dados_corretos,
            pessoas_financeiro=pessoas_financeiro,
            situacoes_pagamento=situacoes_pagamento,
            estrutura_plano_contas=estrutura_plano_contas,
            estrutura_fiscal=estrutura_fiscal,
            centros_custo=centros_custo,
            contas_bancarias=contas_bancarias,
            objeto_principal={'valor_movimentacao_100': dados_corretos.get('valor', 0)}
        )
        
    except Exception as e:
        flash(("Erro ao processar despesa! Entre em contato com o suporte.", "warning"))
        return redirect(url_for("listagem_despesas_avulsas"))


@app.route("/financeiro/despesa-avulsa/editar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_despesa_avulsa(id):
    """Edita uma despesa avulsa existente"""
    
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    dados_corretos = {}
    gravar_banco = True

    try:
        despesa_existente = LancamentoAvulsoModel.obter_lancamento_por_id(id)
        if not despesa_existente or despesa_existente.tipo_movimentacao != 2:
            flash(("Despesa não encontrada!", "warning"))
            return redirect(url_for("listagem_despesas_avulsas"))
        
        if despesa_existente.situacao_pagamento_id == 6:
            flash(("Não é possível editar uma despesa que já foi categorizada!", "warning"))
            return redirect(url_for("listagem_despesas_avulsas"))

        
        if request.method == "POST":
            descricao = request.form.get("descricao", "").strip()
            valor = request.form.get("valor", "").strip()

            dados_corretos = {
                "descricao": descricao,
                "valor": valor,
            }

            campos = {
                "descricao": ["Descrição", descricao],
                "valor": ["Valor", descricao],
            }
            
            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

            if "validado" not in validacao_campos_obrigatorios:
                gravar_banco = False
                flash("Verifique os campos destacados em vermelho!", "warning")

            valor_float = ValoresMonetarios.converter_string_brl_para_float(valor)

            if gravar_banco:
                valor_formatado = int(valor_float * 100)

                despesa_existente.descricao = descricao
                despesa_existente.valor_movimentacao_100 = valor_formatado

                acao = TipoAcaoEnum.EDICAO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    acao,
                    acao.pontos,
                    modulo="despesa_avulsa"
                )

                db.session.commit()

                flash(("Despesa editada com sucesso!", "success"))
                return redirect(url_for("listagem_despesas_avulsas"))
        
        else:
            dados_corretos = {
                "descricao": despesa_existente.descricao,
                "valor": despesa_existente.valor_movimentacao_100,
            }

        return render_template(
            "financeiro/lancamento_avulso/despesas_avulsas/despesa_avulsa_editar.html",
            campos_obrigatorios=validacao_campos_obrigatorios,
            campos_erros=validacao_campos_erros,
            dados_corretos=dados_corretos,
            lancamento_id=id
        )
        
    except Exception as e:
        flash(("Erro ao tentar editar despesa! Entre em contato com o suporte.", "warning"))
        return redirect(url_for("listagem_despesas_avulsas"))


@app.route("/financeiro/despesa-avulsa/excluir/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def excluir_despesa_avulsa(id):
    """Exclui uma despesa avulsa (soft delete) e reverte conciliação se houver"""
    try:
        
        agendamento = AgendamentoPagamentoModel.obter_agendamento_por_id(id)
        
        if not agendamento:
            flash(("Agendamento não encontrado!", "warning"))
            return redirect(url_for("listagem_despesas_avulsas"))
        
        despesa_existente = None
        if agendamento.lancamento_avulso_id:
            despesa_existente = LancamentoAvulsoModel.obter_lancamento_por_id(agendamento.lancamento_avulso_id)
            if despesa_existente and despesa_existente.tipo_movimentacao != 2:
                flash(("Esta não é uma despesa válida!", "warning"))
                return redirect(url_for("listagem_despesas_avulsas"))

        from sistema.models_views.importacao_ofx.importacao_ofx_model import ImportacaoOfx
        
        conciliacao_existe = False
        transacao_conciliada = None
        
        if agendamento:
            transacao_conciliada = ImportacaoOfx.query.filter(
                ImportacaoOfx.conciliado == True,
                ImportacaoOfx.dados_conciliacao_json.contains(f'"agendamentos_ids": [{agendamento.id}]') |
                ImportacaoOfx.dados_conciliacao_json.contains(f'"agendamentos_ids":[{agendamento.id}]')
            ).first()

            if transacao_conciliada:
                conciliacao_existe = True

        try:
            movimentacoes_ja_revertidas = set()

            if conciliacao_existe and transacao_conciliada:
                
                import json
                
                if isinstance(transacao_conciliada.dados_conciliacao_json, dict):
                    dados_conciliacao = transacao_conciliada.dados_conciliacao_json
                elif isinstance(transacao_conciliada.dados_conciliacao_json, str):
                    dados_conciliacao = json.loads(transacao_conciliada.dados_conciliacao_json)
                else:
                    dados_conciliacao = {}
                
                transacao_conciliada.conciliado = False
                transacao_conciliada.dados_conciliacao_json = None
                transacao_conciliada.data_conciliacao = None
                
                agendamentos_ids = dados_conciliacao.get('agendamentos_ids', [])
                for agend_id in agendamentos_ids:
                    agend = AgendamentoPagamentoModel.obter_agendamento_por_id(agend_id)
                    if agend and agend.situacao_pagamento_id in [8, 9 , 10]:
                        agend.ativo = False
                        agend.deletado = True
                        agend.situacao_pagamento_id = 11
                
                movimentacoes_ids = dados_conciliacao.get('movimentacoes_ids', [])
                for mov_id in movimentacoes_ids:
                    movimentacoes_ja_revertidas.add(mov_id)
                    movimentacao = MovimentacaoFinanceiraModel.query.get(mov_id)
                    if movimentacao:
                        if movimentacao.conta_bancaria_id:
                            saldo_conta = SaldoMovimentacaoFinanceiraModel.query.filter(
                                SaldoMovimentacaoFinanceiraModel.conta_bancaria_id == movimentacao.conta_bancaria_id,
                                SaldoMovimentacaoFinanceiraModel.ativo == True,
                                SaldoMovimentacaoFinanceiraModel.deletado == False
                            ).first()
                            
                            if saldo_conta:
                                
                                valor_reversao = movimentacao.valor_movimentacao_100
                                tipo_reversao = None
                                
                                if movimentacao.tipo_movimentacao == 2:
                                    saldo_conta.valor_total_saldo_100 += valor_reversao
                                    tipo_reversao = 1
                                elif movimentacao.tipo_movimentacao == 1:
                                    saldo_conta.valor_total_saldo_100 -= valor_reversao
                                    tipo_reversao = 2
                                
                                if tipo_reversao:
                                    movimentacao_reversao = MovimentacaoFinanceiraModel(
                                        tipo_movimentacao=tipo_reversao,
                                        usuario_id=current_user.id,
                                        data_movimentacao=DataHora.obter_data_atual_padrao_en(),
                                        valor_movimentacao_100=valor_reversao,
                                        conta_bancaria_id=movimentacao.conta_bancaria_id,
                                        agendamento_id=None,
                                        observacao_movimentacao=f"Reversão de conciliação - Exclusão do agendamento {agendamento.descricao}"
                                    )
                                    db.session.add(movimentacao_reversao)
                                
                                saldo_conta.data_movimentacao = DataHora.obter_data_atual_padrao_en()
                        
                        movimentacao.ativo = False
                        movimentacao.deletado = True
                

            movimentacoes_liquidacao = MovimentacaoFinanceiraModel.query.filter(
                MovimentacaoFinanceiraModel.agendamento_id == agendamento.id,
                MovimentacaoFinanceiraModel.ativo == True,
                MovimentacaoFinanceiraModel.deletado == False
            ).all()

            for movimentacao in movimentacoes_liquidacao:
                if movimentacao.id in movimentacoes_ja_revertidas:
                    continue

                
                if movimentacao.conta_bancaria_id:
                    saldo_conta = SaldoMovimentacaoFinanceiraModel.query.filter(
                        SaldoMovimentacaoFinanceiraModel.conta_bancaria_id == movimentacao.conta_bancaria_id,
                        SaldoMovimentacaoFinanceiraModel.ativo == True,
                        SaldoMovimentacaoFinanceiraModel.deletado == False
                    ).first()
                    
                    if saldo_conta:
                        valor_reversao = movimentacao.valor_movimentacao_100
                        tipo_reversao = None
                        
                        if movimentacao.tipo_movimentacao == 2:
                            saldo_conta.valor_total_saldo_100 += valor_reversao
                            tipo_reversao = 1
                        elif movimentacao.tipo_movimentacao == 1:
                            saldo_conta.valor_total_saldo_100 -= valor_reversao
                            tipo_reversao = 2
                        
                        if tipo_reversao:
                            movimentacao_reversao = MovimentacaoFinanceiraModel(
                                tipo_movimentacao=tipo_reversao,
                                usuario_id=current_user.id,
                                data_movimentacao=DataHora.obter_data_atual_padrao_en(),
                                valor_movimentacao_100=valor_reversao,
                                conta_bancaria_id=movimentacao.conta_bancaria_id,
                                agendamento_id=None,
                                observacao_movimentacao=f"Reversão de liquidação - Exclusão da despesa {agendamento.descricao}"
                            )
                            db.session.add(movimentacao_reversao)
                        
                        saldo_conta.data_movimentacao = DataHora.obter_data_atual_padrao_en()
                
                movimentacao.ativo = False
                movimentacao.deletado = True

            liquidacao_revertida = len(movimentacoes_liquidacao) > 0

            agendamento.deletado = True
            agendamento.ativo = False
            
            if despesa_existente:
                despesa_existente.ativo = False
                despesa_existente.deletado = True

            db.session.commit()

            if conciliacao_existe and liquidacao_revertida:
                flash(("Despesa excluída com sucesso! A conciliação bancária e a liquidação foram revertidas automaticamente.", "success"))
            elif conciliacao_existe:
                flash(("Despesa excluída com sucesso! A conciliação bancária foi revertida automaticamente.", "success"))
            elif liquidacao_revertida:
                flash(("Despesa excluída com sucesso! A liquidação foi revertida e o saldo da conta foi ajustado.", "success"))
            else:
                flash(("Despesa excluída com sucesso!", "success"))
                
            return redirect(url_for("listagem_despesas_avulsas"))
            
        except Exception as e:
            db.session.rollback()
            import traceback
            traceback.print_exc()
            flash(("Erro ao excluir despesa e reverter conciliação! Entre em contato com o suporte.", "warning"))
            return redirect(url_for("listagem_despesas_avulsas"))
                
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(("Erro ao tentar excluir despesa! Entre em contato com o suporte.", "warning"))
        return redirect(url_for("listagem_despesas_avulsas"))


@app.route("/financeiro/despesa-avulsa/liquidar", methods=["POST"])
@login_required
@requires_roles
def liquidar_despesa():
    """Liquida uma despesa avulsa criando movimentação financeira"""
    try:
        agendamento_id = request.form.get("agendamento_id")
        conta_bancaria_id = request.form.get("conta_bancaria_id")

        if not agendamento_id:
            flash(("ID do agendamento não informado!", "warning"))
            return redirect(url_for("listagem_despesas_avulsas"))

        if not conta_bancaria_id:
            flash(("Selecione uma conta bancária!", "warning"))
            return redirect(url_for("listagem_despesas_avulsas"))

        agendamento = AgendamentoPagamentoModel.obter_agendamento_por_id(agendamento_id)

        if not agendamento:
            flash(("Agendamento não encontrado!", "warning"))
            return redirect(url_for("listagem_despesas_avulsas"))

        if agendamento.situacao_pagamento_id == 9:
            flash(("Esta despesa já foi liquidada!", "warning"))
            return redirect(url_for("listagem_despesas_avulsas"))

        conta_bancaria = ContaBancariaModel.obter_conta_por_id(conta_bancaria_id)
        if not conta_bancaria:
            flash(("Conta bancária não encontrada!", "warning"))
            return redirect(url_for("listagem_despesas_avulsas"))

        if agendamento.faturamento_id and agendamento.faturamento:
            valor_despesa = int(agendamento.faturamento.valor_total) if agendamento.faturamento.valor_total else 0
        elif agendamento.lancamento_avulso_id and agendamento.lancamento_avulso:
            valor_despesa = agendamento.lancamento_avulso.valor_movimentacao_100
        else:
            valor_despesa = agendamento.valor_total_100

        nova_movimentacao = MovimentacaoFinanceiraModel(
            tipo_movimentacao=2,
            usuario_id=current_user.id,
            data_movimentacao=date.today(),
            valor_movimentacao_100=valor_despesa,
            conta_bancaria_id=conta_bancaria_id,
            agendamento_id=agendamento_id
        )

        agendamento.situacao_pagamento_id = 9
        agendamento.conta_bancaria_id = conta_bancaria_id

        
        if agendamento.faturamento_id:
            agendamento.faturamento.situacao_pagamento_id = 9
            
            detalhes = agendamento.faturamento.obter_detalhes()
            
            fornecedores = detalhes.get("fornecedores", [])
            for fornecedor in fornecedores:
                if "fornecedor_a_pagar_id" in fornecedor:
                    fornecedor_pagar = FornecedorPagarModel.obter_fornecedor_a_pagar_id(fornecedor["fornecedor_a_pagar_id"])
                    if fornecedor_pagar:
                        fornecedor_pagar.situacao_pagamento_id = 9
            
            transportadoras = detalhes.get("transportadoras", [])
            for transportadora in transportadoras:
                if "frete_a_pagar_id" in transportadora:
                    frete_pagar = FretePagarModel.obter_frete_a_pagar_id(transportadora["frete_a_pagar_id"])
                    if frete_pagar:
                        frete_pagar.situacao_pagamento_id = 9
            
            extratores = detalhes.get("extratores", [])
            for extrator in extratores:
                if "extrator_a_pagar_id" in extrator:
                    extrator_pagar = ExtratorPagarModel.obter_extrator_a_pagar_id(extrator["extrator_a_pagar_id"])
                    if extrator_pagar:
                        extrator_pagar.situacao_pagamento_id = 9
            
            comissionados = detalhes.get("comissionados", [])
            for comissionado in comissionados:
                if "comissionado_a_pagar_id" in comissionado:
                    comissionado_pagar = ComissionadoPagarModel.obter_comissionado_a_pagar_id(comissionado["comissionado_a_pagar_id"])
                    if comissionado_pagar:
                        comissionado_pagar.situacao_pagamento_id = 9
        else:
            agendamento.lancamento_avulso.situacao_pagamento_id = 9

        saldo_conta = SaldoMovimentacaoFinanceiraModel.query.filter(
            SaldoMovimentacaoFinanceiraModel.conta_bancaria_id == conta_bancaria_id,
            SaldoMovimentacaoFinanceiraModel.ativo == True,
            SaldoMovimentacaoFinanceiraModel.deletado == False
        ).first()
        
        if not saldo_conta:
            saldo_conta = SaldoMovimentacaoFinanceiraModel(
                data_movimentacao=date.today(),
                valor_total_saldo_100=0,
                conta_bancaria_id=conta_bancaria_id,
                ativo=True
            )
            db.session.add(saldo_conta)
        
        saldo_conta.valor_total_saldo_100 -= valor_despesa
        saldo_conta.data_movimentacao = DataHora.obter_data_atual_padrao_en()
        db.session.add(saldo_conta)

        db.session.add(nova_movimentacao)
        db.session.commit()

        acao = TipoAcaoEnum.CADASTRO if hasattr(TipoAcaoEnum, 'LIQUIDACAO') else TipoAcaoEnum.CADASTRO
        PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
            current_user.id,
            acao,
            acao.pontos,
            modulo="despesa_avulsa_liquidacao"
        )

        flash(("Despesa liquidada com sucesso!", "success"))
        return redirect(url_for("listagem_despesas_avulsas"))

    except Exception as e:
        db.session.rollback()
        flash(("Erro ao liquidar despesa! Entre em contato com o suporte.", "warning"))
        return redirect(url_for("listagem_despesas_avulsas"))
