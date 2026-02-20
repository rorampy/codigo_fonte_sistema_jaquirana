from datetime import datetime
import json
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem, formatar_data_para_brl
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
from sistema.models_views.autenticacao.usuario_model import UsuarioModel
from sistema._utilitarios import *
from sistema.models_views.configuracoes_gerais.situacao_pagamento.situacao_pagamento_model import SituacaoPagamentoModel
from sistema.models_views.financeiro.operacional.categorizar_fatura.categorizacao_model import AgendamentoPagamentoModel
from sistema.models_views.financeiro.operacional.categorizar_fatura.parcela_categorizacao.parcela_categorizacao_model import ParcelaCategorizacaoModel
from sistema.models_views.gerenciar.pessoa_financeiro.pessoa_financeiro_model import PessoaFinanceiroModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_view import (inicializar_categorias_padrao, obter_subcategorias_recursivo)
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_view import (inicializar_categorias_padrao_categorizacao_fiscal, obter_subcategorias_recursivo_categorizacao_fiscal)
from sistema.models_views.configuracoes_gerais.centro_custo.centro_custo_model import CentroCustoModel
from sistema._utilitarios import *

@app.route("/financeiro/operacional/despesas-avulsas", methods=["GET"])
@login_required
@requires_roles
def listagem_faturamentos_despesas_avulsas():
    """
    Lista todos os faturamentos de despesas avulsas.
    """
    try:
        faturamentos = FaturamentoModel.obter_faturamentos_lancamentos_despesas_avulsas()

        for faturamento in faturamentos:
            if faturamento.usuario_id:
                usuario = UsuarioModel.query.get(faturamento.usuario_id)
                faturamento.usuario = usuario
        
        return render_template(
            "financeiro/operacional/despesas/listagem_faturamentos_despesas_avulsas.html",
            faturamentos=faturamentos,
            dados_corretos=request.args
        )
        
    except Exception as e:
        flash(("Erro ao carregar listagem de faturamentos! Contate o suporte.", "error"))
        return redirect(url_for("listagem_faturamentos_despesas_avulsas"))


@app.route("/financeiro/operacional/despesa-avulsa/detalhes/<int:id>", methods=["GET"])
@login_required
@requires_roles
def detalhes_faturamento_despesa_avulsa_ajax(id):
    """
    Retorna os detalhes do faturamento em JSON para exibição no modal.
    """
    try:
        faturamento = FaturamentoModel.query.get_or_404(id)
        
        if not faturamento.ativo:
            return jsonify({"erro": "Faturamento não encontrado"}), 404
        
        usuario = UsuarioModel.query.get(faturamento.usuario_id) if faturamento.usuario_id else None
        
        def formatar_valor(valor_centavos):
            if valor_centavos is None:
                return "R$ 0,00"
            return f"R$ {valor_centavos / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        dados_faturamento = {
            "codigo_faturamento": faturamento.codigo_faturamento,
            "data_cadastro": faturamento.data_cadastro.strftime("%d/%m/%Y %H:%M") if faturamento.data_cadastro else "",
            "usuario": f"{usuario.nome} {usuario.sobrenome}" if usuario else "N/A",
            "valor_total": formatar_valor(faturamento.valor_despesa),
            "situacao": faturamento.situacao.situacao if faturamento.situacao else "Pendente",
            "total_despesas_avulsas": 1,
        }

        receita_despesa = []
        if faturamento.lancamento_avulso:
            receita_despesa.append({
                "lancamento_id": faturamento.lancamento_avulso.id or 'N/A',
                "data_cadastro": DataHora.converter_data_de_en_para_br(faturamento.lancamento_avulso.data_cadastro) or "N/A",
                "descricao": faturamento.lancamento_avulso.descricao or "N/A",
                "valor": formatar_valor(faturamento.lancamento_avulso.valor_movimentacao_100) or "N/A",
                "conta_bancaria": faturamento.lancamento_avulso.conta_bancaria.identificacao or "N/A",
            })
    
            
        return jsonify({
            "faturamento": dados_faturamento,
            "despesas_avulsas": receita_despesa,
        })
        
    except Exception as e:
        return jsonify({"erro": "Erro interno do servidor"}), 500
    
    
@app.route("/financeiro/operacional/categorizacao/despesas-avulsas/detalhes-json/<int:id>", methods=["GET"])
@login_required
@requires_roles
def detalhes_categorizacao_faturamento_despesa_avulsa_json(id):
    """Retorna JSON com os detalhes da categorização de um faturamento de controle de despesas"""
    try:
        faturamento = FaturamentoModel.obter_faturamento_por_id(id)
        if not faturamento:
            return jsonify({'error': 'Faturamento não encontrado!'}), 404
        if faturamento.tipo_operacao != 2 or faturamento.direcao_financeira != 2:
            return jsonify({'error': 'Este não é um faturamento de despesas avulsas.'}), 400

        agendamento = db.session.query(AgendamentoPagamentoModel).filter_by(faturamento_id=id).first()
        if not agendamento:
            return jsonify({'error': 'Este faturamento ainda não foi categorizado.'}), 404
            
        pessoa = PessoaFinanceiroModel.obter_pessoa_por_id(agendamento.pessoa_financeiro_id)
        situacao = SituacaoPagamentoModel.obter_situacao_por_id(agendamento.situacao_pagamento_id)
        
        detalhes = faturamento.obter_detalhes()
        creditos_fornecedores = detalhes.get("credito_fornecedor", [])
        creditos_transportadoras = detalhes.get("credito_transportadora", [])
        creditos_extratores = detalhes.get("credito_extrator", [])

        def formatar_valor(valor_centavos):
            if valor_centavos is None:
                return 0.0
            return float(valor_centavos / 100) if isinstance(valor_centavos, (int, float)) else 0.0
        
        creditos_fornecedores_processados = []
        for credito in creditos_fornecedores:
            credito_processado = {
                'fornecedor_id': credito.get('fornecedor_id', 'N/A'),
                'identificacao': credito.get('fornecedor_identificacao', 'N/A'),
                'data_movimentacao': DataHora.converter_data_de_en_para_br(credito.get("data_movimentacao")) or "N/A",
                'credito_descricao': credito.get('credito_descricao', 'N/A'),
                'valor_credito': formatar_valor(credito.get('valor_credito_100', 0)),
                'conta_bancaria_id': credito.get('conta_bancaria_id', 'N/A'),
                'extrato_credito_fornecedor_id': credito.get('extrato_credito_fornecedor_id', 'N/A'),
            }
            creditos_fornecedores_processados.append(credito_processado)
        
        creditos_transportadoras_processados = []
        for credito in creditos_transportadoras:
            credito_processado = {
                'transportadora_id': credito.get('transportadora_id', 'N/A'),
                'identificacao': credito.get('transportadora_identificacao', 'N/A'),
                'data_movimentacao': DataHora.converter_data_de_en_para_br(credito.get("data_movimentacao")) or "N/A",
                'credito_descricao': credito.get('credito_descricao', 'N/A'),
                'valor_credito': formatar_valor(credito.get('valor_credito_100', 0)),
                'conta_bancaria_id': credito.get('conta_bancaria_id', 'N/A'),
                'extrato_credito_transportadora_id': credito.get('extrato_credito_transportadora_id', 'N/A'),
            }
            creditos_transportadoras_processados.append(credito_processado)

        creditos_extratores_processados = []
        for credito in creditos_extratores:
            credito_processado = {
                'extrator_id': credito.get('extrator_id', 'N/A'),
                'identificacao': credito.get('extrator_identificacao', 'N/A'),
                'data_movimentacao': DataHora.converter_data_de_en_para_br(credito.get("data_movimentacao")) or "N/A",
                'credito_descricao': credito.get('credito_descricao', 'N/A'),
                'valor_credito': formatar_valor(credito.get('valor_credito_100', 0)),
                'conta_bancaria_id': credito.get('conta_bancaria_id', 'N/A'),
                'extrato_credito_extrator_id': credito.get('extrato_credito_extrator_id', 'N/A'),
            }
            creditos_extratores_processados.append(credito_processado)
        
        categorias_processadas = []
        if agendamento.categorias_json:
            try:
                categorias = json.loads(agendamento.categorias_json)
                for cat in categorias:
                    categoria_nome = cat.get('categoria', 'Não informado')
                    categoria_codigo = ''
                    categoria_detalhamento = cat.get('detalhamento', 'Não informado')
                    categoria_referencia = cat.get('referencia', 'Não informado')
                    
                    if str(categoria_nome).isdigit():
                        plano_conta = PlanoContaModel.buscar_por_id(int(categoria_nome))
                        if plano_conta:
                            categoria_nome = plano_conta.nome
                            categoria_codigo = plano_conta.codigo
                    
                    categorias_processadas.append({
                        'nome': categoria_nome,
                        'detalhamento': categoria_detalhamento,
                        'referencia': categoria_referencia,
                        'codigo': categoria_codigo,
                        'valor': float(cat.get('valor', 0)),
                        'percentual': float(cat.get('percentual', 0)),
                        'descricao': cat.get('descricao', ''),
                        'referencia': cat.get('referencia', '')
                    })
            except (json.JSONDecodeError, ValueError):
                categorias_processadas = []
                
        centros_custo_processados = []
        if agendamento.centros_custo_json:
            try:
                centros_custo = json.loads(agendamento.centros_custo_json)
                
                for cc in centros_custo:
                    centro_nome = cc.get('centro', 'Não informado')
                    
                    if str(centro_nome).isdigit():
                        centro_custo_obj = CentroCustoModel.obter_centro_custo_por_id(int(centro_nome))
                        if centro_custo_obj:
                            centro_nome = centro_custo_obj.nome
                    
                    valor_raw = cc.get('valor', 0)
                    valor_convertido = float(valor_raw) / 100 if isinstance(valor_raw, (int, float)) else 0.0
                    
                    percentual_raw = cc.get('percentual', 0)
                    percentual_convertido = float(percentual_raw) if percentual_raw and str(percentual_raw).strip() else 0.0
                    
                    centros_custo_processados.append({
                        'nome': centro_nome,
                        'valor': valor_convertido,
                        'percentual': percentual_convertido
                    })
                    
            except (json.JSONDecodeError, ValueError) as e:
                centros_custo_processados = []
                
        parcelas = []
        if agendamento.parcelamento_ativo:
            parcelas_obj = ParcelaCategorizacaoModel.obter_parcelas_por_agendamento(agendamento.id)
            for parcela in parcelas_obj:
                situacao_parcela = SituacaoPagamentoModel.obter_situacao_por_id(parcela.situacao_pagamento_id)
                parcelas.append({
                    'numero_parcela': parcela.numero_parcela,
                    'data_vencimento': parcela.data_vencimento.strftime('%d/%m/%Y'),
                    'valor_parcela': float(parcela.valor_parcela),
                    'descricao': parcela.descricao or '',
                    'referencia': parcela.referencia or '',
                    'situacao_id': parcela.situacao_pagamento_id,
                    'situacao_nome': situacao_parcela.situacao if situacao_parcela else 'N/A'
                })
        
        valor_total_final = float(faturamento.valor_total / 100) if faturamento.valor_total else 0.0
        valor_bruto_total = float(faturamento.valor_bruto_total / 100) if faturamento.valor_bruto_total else valor_total_final
        
        total_creditos_fornecedores = sum(c['valor_credito'] for c in creditos_fornecedores_processados)
        total_creditos_transportadoras = sum(c['valor_credito'] for c in creditos_transportadoras_processados)
        total_creditos_extratores = sum(c['valor_credito'] for c in creditos_extratores_processados)
        
        valor_credito_total = total_creditos_fornecedores + total_creditos_transportadoras + total_creditos_extratores

        dados = {
            'categorizacao_id': agendamento.id,
            'faturamento': {
                'codigo': faturamento.codigo_faturamento,
                'tipo': 'Adiantamentos de Créditos',
                'valor_total': valor_total_final,
                'valor_bruto_total': valor_bruto_total,
                'valor_credito_total': valor_credito_total,
                'total_creditos_fornecedores': len(creditos_fornecedores),
                'total_creditos_transportadoras': len(creditos_transportadoras),
                'total_creditos_extratores': len(creditos_extratores),
                'creditos_fornecedores': creditos_fornecedores_processados,
                'creditos_transportadoras': creditos_transportadoras_processados,
                'creditos_extratores': creditos_extratores_processados
            },
            'pagamento': {
                'beneficiario': pessoa.identificacao if pessoa else 'N/A',
                'data_vencimento': agendamento.data_vencimento.strftime('%d/%m/%Y'),
                'situacao_id': situacao.id if situacao else 0,
                'situacao_nome': situacao.situacao if situacao else 'N/A'
            },
            'categorias': categorias_processadas,
            'centros_custo': centros_custo_processados,
            'parcelas': parcelas,
            'parcelamento_ativo': agendamento.parcelamento_ativo
        }
        
        return jsonify(dados)
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor. Tente novamente.'}), 500

@app.route('/financeiro/operacional/despesas-avulsas/exportar-pdf/<int:faturamento_id>', methods=['GET','POST'])
@login_required
@requires_roles
def exportar_despesa_avulsa_pdf(faturamento_id):
    """Gera PDF do faturamento de despesas avulsas"""
    try:
        faturamento = FaturamentoModel.query.get_or_404(faturamento_id)
        
        if faturamento.tipo_operacao != 2 or faturamento.direcao_financeira != 2:
            flash(("Este não é um faturamento de despesas avulsas.", "error"))
            return redirect(url_for("listagem_faturamentos_despesas_avulsas"))
        
        dados_processados = processar_dados_faturamento(faturamento)
        
        dados_extras = {
            'logo_path': obter_url_absoluta_de_imagem("logo.png"),
            'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'usuario_geracao': current_user.nome if hasattr(current_user, 'nome') else 'Sistema'
        }
        
        dados_template = {**dados_processados, **dados_extras}
        
        html = render_template('financeiro/operacional/despesas/relatorio_faturamento/relatorio_faturamento.html', **dados_template)

        codigo_fat = faturamento.codigo_faturamento
        nome_arquivo = f"despesa_avulsa_{codigo_fat}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo, orientacao="Portrait", abrir_em_nova_aba=True)
        
    except Exception as e:
        flash((f"Erro ao gerar PDF das despesas avulsas! Contate o suporte. {e}", "error"))
        return redirect(url_for("listagem_faturamentos_despesas_avulsas"))


@app.route('/financeiro/operacional/despesas-avulsas/exportar-imagem/<int:faturamento_id>', methods=['GET','POST'])
@login_required
@requires_roles
def exportar_despesa_avulsa_imagem(faturamento_id):
    """Gera imagem JPG do faturamento de despesas avulsas"""
    try:
        faturamento = FaturamentoModel.query.get_or_404(faturamento_id)
        
        if faturamento.tipo_operacao != 2 or faturamento.direcao_financeira != 2:
            flash(("Este não é um faturamento de despesas avulsas.", "error"))
            return redirect(url_for("listagem_faturamentos_despesas_avulsas"))
        
        dados_processados = processar_dados_faturamento(faturamento)
        
        dados_extras = {
            'logo_path': obter_url_absoluta_de_imagem("logo.png"),
            'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'usuario_geracao': current_user.nome if hasattr(current_user, 'nome') else 'Sistema'
        }
        
        dados_template = {**dados_processados, **dados_extras}

        html = render_template('financeiro/operacional/despesas/relatorio_faturamento/relatorio_faturamento_imagem.html', **dados_template)

        codigo_fat = faturamento.codigo_faturamento
        nome_arquivo = f"despesa_avulsa_{codigo_fat}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return ManipulacaoArquivos.gerar_imagem_from_html(html, nome_arquivo, largura=1400, altura=1400)
        
    except Exception as e:
        flash((f"Erro ao gerar imagem das despesas avulsas! Contate o suporte. {e}", "error"))
        return redirect(url_for("listagem_faturamentos_despesas_avulsas"))


def processar_dados_faturamento(faturamento):
    """Processa dados do faturamento de despesas avulsas para uso nos templates"""
    
    dados = {
        'faturamento': {
            'id': faturamento.id,
            'codigo_faturamento': faturamento.codigo_faturamento,
            'data_cadastro': faturamento.data_cadastro.strftime('%d/%m/%Y %H:%M') if faturamento.data_cadastro else '-',
            'usuario': faturamento.usuario.nome if faturamento.usuario else '-',
            'valor_bruto_total': faturamento.valor_bruto_total or 0,
            'valor_total': faturamento.valor_total or 0,
            'tipo_operacao': 'Despesas Avulsas',
            'direcao_financeira': 'Despesa',
            'situacao': faturamento.situacao.situacao if faturamento.situacao else 'Pendente'
        }
    }
    
    despesas_processadas = []
    
    if faturamento.lancamento_avulso:
        valor_centavos = faturamento.lancamento_avulso.valor_movimentacao_100 or 0
        valor_reais = valor_centavos / 100 if valor_centavos else 0.0
        valor_formatado = f"R$ {valor_reais:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        despesa_data = {
            'id': faturamento.lancamento_avulso.id,
            'data_cadastro': DataHora.converter_data_de_en_para_br(faturamento.lancamento_avulso.data_cadastro) or '-',
            'descricao': faturamento.lancamento_avulso.descricao or '-',
            'conta_bancaria': faturamento.lancamento_avulso.conta_bancaria.identificacao if faturamento.lancamento_avulso.conta_bancaria else '-',
            'valor': valor_formatado,
            'valor_numerico': valor_reais,
            'valor_centavos': valor_centavos
        }
        
        despesas_processadas.append(despesa_data)
    
    dados['despesas_avulsas'] = despesas_processadas
    dados['total_despesas_avulsas'] = len(despesas_processadas)
    
    dados['fornecedores'] = {}
    dados['total_fornecedores'] = 0
    dados['transportadoras'] = {}
    dados['total_transportadoras'] = 0
    dados['extratores'] = {}
    dados['total_extratores'] = 0

    return dados


def agrupar_creditos_fornecedores_pdf(creditos_fornecedores):
    """Agrupa créditos de fornecedores para PDF"""
    from collections import defaultdict
    grupos = defaultdict(lambda: {'registros': [], 'total': 0.0})
    
    for credito in creditos_fornecedores:
        nome = credito.get('fornecedor_identificacao', 'Não informado')
        valor_centavos = credito.get('valor_credito_100', 0)
        valor_reais = valor_centavos / 100 if valor_centavos else 0.0
        
        credito_formatado = {
            'fornecedor_id': credito.get('fornecedor_id', 'N/A'),
            'fornecedor_identificacao': nome,
            'data_movimentacao': DataHora.converter_data_de_en_para_br(credito.get('data_movimentacao')) or 'N/A',
            'credito_descricao': credito.get('credito_descricao', 'N/A'),
            'valor_credito_100': valor_centavos,
            'valor_credito_reais': valor_reais,
            'valor_credito_formatado': f"R$ {valor_reais:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            'conta_bancaria_id': credito.get('conta_bancaria_id', 'N/A'),
            'extrato_credito_fornecedor_id': credito.get('extrato_credito_fornecedor_id', 'N/A')
        }
        
        grupos[nome]['registros'].append(credito_formatado)
        grupos[nome]['total'] += valor_reais
    
    for grupo in grupos.values():
        grupo['total_formatado'] = f"R$ {grupo['total']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    return dict(grupos)


def agrupar_creditos_transportadoras_pdf(creditos_transportadoras):
    """Agrupa créditos de transportadoras para PDF"""
    from collections import defaultdict
    grupos = defaultdict(lambda: {'registros': [], 'total': 0.0})
    
    for credito in creditos_transportadoras:
        nome = credito.get('transportadora_identificacao', 'Não informado')
        valor_centavos = credito.get('valor_credito_100', 0)
        valor_reais = valor_centavos / 100 if valor_centavos else 0.0
        
        credito_formatado = {
            'transportadora_id': credito.get('transportadora_id', 'N/A'),
            'transportadora_identificacao': nome,
            'data_movimentacao': DataHora.converter_data_de_en_para_br(credito.get('data_movimentacao')) or 'N/A',
            'credito_descricao': credito.get('credito_descricao', 'N/A'),
            'valor_credito_100': valor_centavos,
            'valor_credito_reais': valor_reais,
            'valor_credito_formatado': f"R$ {valor_reais:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            'conta_bancaria_id': credito.get('conta_bancaria_id', 'N/A'),
            'extrato_credito_transportadora_id': credito.get('extrato_credito_transportadora_id', 'N/A')
        }
        
        grupos[nome]['registros'].append(credito_formatado)
        grupos[nome]['total'] += valor_reais
    
    for grupo in grupos.values():
        grupo['total_formatado'] = f"R$ {grupo['total']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    return dict(grupos)


def agrupar_creditos_extratores_pdf(creditos_extratores):
    """Agrupa créditos de extratores para PDF"""
    from collections import defaultdict
    grupos = defaultdict(lambda: {'registros': [], 'total': 0.0})
    
    for credito in creditos_extratores:
        nome = credito.get('extrator_identificacao', 'Não informado')
        valor_centavos = credito.get('valor_credito_100', 0)
        valor_reais = valor_centavos / 100 if valor_centavos else 0.0
        
        credito_formatado = {
            'extrator_id': credito.get('extrator_id', 'N/A'),
            'extrator_identificacao': nome,
            'data_movimentacao': DataHora.converter_data_de_en_para_br(credito.get('data_movimentacao')) or 'N/A',
            'credito_descricao': credito.get('credito_descricao', 'N/A'),
            'valor_credito_100': valor_centavos,
            'valor_credito_reais': valor_reais,
            'valor_credito_formatado': f"R$ {valor_reais:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            'conta_bancaria_id': credito.get('conta_bancaria_id', 'N/A'),
            'extrato_credito_extrator_id': credito.get('extrato_credito_extrator_id', 'N/A')
        }
        
        grupos[nome]['registros'].append(credito_formatado)
        grupos[nome]['total'] += valor_reais
    
    for grupo in grupos.values():
        grupo['total_formatado'] = f"R$ {grupo['total']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    return dict(grupos)
