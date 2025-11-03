from datetime import datetime
import json
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem, formatar_data_para_brl
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sistema.models_views.controle_carga.carga_model import CargaModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema.models_views.gerenciar.motorista.motorista_model import MotoristaModel
from sistema.models_views.gerenciar.motorista.transportadora_motorista_associado_model import TransportadoraMotoristaAssocModel
from sistema.models_views.gerenciar.veiculo.veiculo_model import VeiculoModel
from sistema.models_views.gerenciar.veiculo.veiculo_transportadora_veiculo_associado_model import TransportadoraVeiculoAssocModel
from sistema.models_views.controle_carga.produto_model import ProdutoModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.parametros.nome_grupo_whats.nome_grupo_whats_model import NomeGrupoWhatsModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.configuracoes_gerais.empresa_emissora.empresa_emissora_model import EmpresaEmissoraModel
from sistema.models_views.faturamento.cargas_a_pagar.transportadora.frete_a_pagar_model import FretePagarModel
from sistema.models_views.faturamento.faturamento_model import FaturamentoModel
from sistema.models_views.autenticacao.usuario_model import UsuarioModel
from sistema._utilitarios import *
from sistema.models_views.financeiro.lancamento_avulso.lancamento_avulso_model import LancamentoAvulsoModel
from sistema.models_views.financeiro.situacao_pagamento_model import SituacaoPagamentoModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_model import FornecedorModel
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema.models_views.gerenciar.extrator.extrator_model import ExtratorModel
from sistema.models_views.gerenciar.comissionado.comissionado_model import ComissionadoModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.financeiro.operacional.categorizar_fatura.categorizacao_model import AgendamentoPagamentoModel
from sistema.models_views.financeiro.operacional.categorizar_fatura.parcela_categorizacao.parcela_categorizacao_model import ParcelaCategorizacaoModel
from sistema.models_views.gerenciar.pessoa_financeiro.pessoa_financeiro_model import PessoaFinanceiroModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_view import (inicializar_categorias_padrao, obter_subcategorias_recursivo)
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_view import (inicializar_categorias_padrao_categorizacao_fiscal, obter_subcategorias_recursivo_categorizacao_fiscal)
from sistema.models_views.configuracoes_gerais.centro_custo.centro_custo_model import CentroCustoModel
from sistema.models_views.faturamento.controle_credito.extrato_credito.extrato_credito_fornecedor_model import ExtratoCreditoFornecedorModel
from sistema.models_views.faturamento.controle_credito.extrato_credito.extrato_credito_freteiro_model import ExtratoCreditoFreteiroModel
from sistema.models_views.faturamento.controle_credito.extrato_credito.extrato_credito_extrator_model import ExtratoCreditoExtratorModel
from sistema.models_views.faturamento.controle_credito.credito_agrupado.credito_fornecedor_model import CreditoFornecedorModel
from sistema.models_views.faturamento.controle_credito.credito_agrupado.credito_freteiro_model import CreditoFreteiroModel
from sistema.models_views.faturamento.controle_credito.credito_agrupado.credito_extrator_model import CreditoExtratorModel
from sistema._utilitarios import *

@app.route("/financeiro/operacional/controle-creditos", methods=["GET"])
@login_required
@requires_roles
def listagem_faturamentos_controle_credito():
    """
    Lista todos os faturamentos de créditos (fornecedores e transportadoras).
    """
    try:
        # Obter parâmetros de filtro
        beneficiario = request.args.get('beneficiario', type=int)
        situacao_faturamento = request.args.get('situacaoFaturamento', type=int)
        
        # Se não há nenhum parâmetro na URL (acesso inicial), definir padrão como "não categorizado" (situação 7)
        if not request.args:
            situacao_faturamento = 7
        # Se há parâmetros mas situacaoFaturamento está vazio/None, significa "Todos"
        elif 'situacaoFaturamento' in request.args and not situacao_faturamento:
            situacao_faturamento = None
        
        faturamentos = FaturamentoModel.filtrar_creditos_faturamentos(beneficiario, situacao_faturamento)
        
        # Obter situações de faturamento
        situacoes_faturamento = SituacaoPagamentoModel.listar_situacoes_faturamento()
        beneficiarios = PessoaFinanceiroModel.listar_pessoas_ativas()
        
        # Adicionar informação do usuário a cada faturamento
        for faturamento in faturamentos:
            if faturamento.usuario_id:
                usuario = UsuarioModel.query.get(faturamento.usuario_id)
                faturamento.usuario = usuario
        
        return render_template(
            "financeiro/operacional/controle_creditos/listagem_faturamentos_controle_creditos.html",
            faturamentos=faturamentos,
            dados_corretos=request.args,
            situacoes_faturamento=situacoes_faturamento,
            beneficiarios=beneficiarios
        )
        
    except Exception as e:
        print(f"[ERROR listagem_faturamentos_controle_creditos] {e}")
        flash(("Erro ao carregar listagem de faturamentos! Contate o suporte.", "error"))
        return redirect(url_for("listagem_faturamentos_controle_credito"))


@app.route("/financeiro/operacional/controle-creditos/detalhes/<int:id>", methods=["GET"])
@login_required  
@requires_roles
def detalhes_faturamento_controle_credito_ajax(id):
    """
    Retorna os detalhes do faturamento em JSON para exibição no modal.
    """
    try:
        faturamento = FaturamentoModel.query.get_or_404(id)
        
        if not faturamento.ativo:
            return jsonify({"erro": "Faturamento não encontrado"}), 404
            
        detalhes = faturamento.obter_detalhes()
        
        # Buscar informações do usuário
        usuario = UsuarioModel.query.get(faturamento.usuario_id) if faturamento.usuario_id else None
        
        # Formatar valores monetários
        def formatar_valor(valor_centavos):
            if valor_centavos is None:
                return "R$ 0,00"
            return f"R$ {valor_centavos / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        # Preparar dados do faturamento de créditos
        dados_faturamento = {
            "codigo_faturamento": faturamento.codigo_faturamento,
            "data_cadastro": faturamento.data_cadastro.strftime("%d/%m/%Y %H:%M") if faturamento.data_cadastro else "",
            "usuario": f"{usuario.nome} {usuario.sobrenome}" if usuario else "N/A",
            "valor_total": formatar_valor(faturamento.valor_total),
            "valor_bruto_total": formatar_valor(faturamento.valor_bruto_total),
            "situacao": faturamento.situacao.situacao if faturamento.situacao else "Pendente",
            "total_creditos_fornecedores": len(detalhes.get("credito_fornecedor", [])),
            "total_creditos_transportadoras": len(detalhes.get("credito_transportadora", [])),
            "total_creditos_extratores": len(detalhes.get("credito_extrator", [])),
        }

        # Créditos de fornecedores (seguindo padrão do cadastro de crédito)
        creditos_fornecedores = []
        for credito in detalhes.get("credito_fornecedor", []):
            creditos_fornecedores.append({
                "fornecedor_id": credito.get("fornecedor_id", "N/A"),
                "fornecedor_identificacao": credito.get("fornecedor_identificacao", "N/A"),
                "data_movimentacao": DataHora.converter_data_de_en_para_br(credito.get("data_movimentacao")) or "N/A",
                "credito_descricao": credito.get("credito_descricao", "N/A"),
                "valor_credito_100": formatar_valor(credito.get("valor_credito_100", 0)),
                "conta_bancaria_id": credito.get("conta_bancaria_id", "N/A"),
                "extrato_credito_fornecedor_id": credito.get("extrato_credito_fornecedor_id", "N/A"),
            })

        creditos_transportadoras = []
        for credito in detalhes.get("credito_transportadora", []):
            creditos_transportadoras.append({
                "transportadora_id": credito.get("transportadora_id", "N/A"),
                "transportadora_identificacao": credito.get("transportadora_identificacao", "N/A"),
                "data_movimentacao": DataHora.converter_data_de_en_para_br(credito.get("data_movimentacao")) or "N/A",
                "credito_descricao": credito.get("credito_descricao", "N/A"),
                "valor_credito_100": formatar_valor(credito.get("valor_credito_100", 0)),
                "conta_bancaria_id": credito.get("conta_bancaria_id", "N/A"),
                "extrato_credito_transportadora_id": credito.get("extrato_credito_transportadora_id", "N/A"),
            })
            
        creditos_extratores = []
        for credito in detalhes.get("credito_extrator", []):
            creditos_extratores.append({
                "extrator_id": credito.get("extrator_id", "N/A"),
                "extrator_identificacao": credito.get("extrator_identificacao", "N/A"),
                "data_movimentacao": DataHora.converter_data_de_en_para_br(credito.get("data_movimentacao")) or "N/A",
                "credito_descricao": credito.get("credito_descricao", "N/A"),
                "valor_credito_100": formatar_valor(credito.get("valor_credito_100", 0)),
                "conta_bancaria_id": credito.get("conta_bancaria_id", "N/A"),
                "extrato_credito_extrator_id": credito.get("extrato_credito_extrator_id", "N/A"),
            })

        return jsonify({
            "faturamento": dados_faturamento,
            "creditos_fornecedores": creditos_fornecedores,
            "creditos_transportadoras": creditos_transportadoras,
            "creditos_extratores": creditos_extratores
        })
        
    except Exception as e:
        print(f"[ERROR detalhes_faturamento_ajax] {e}")
        return jsonify({"erro": "Erro interno do servidor"}), 500
    
    
@app.route("/financeiro/operacional/categorizacao/controle-creditos/detalhes-json/<int:id>", methods=["GET"])
@login_required
@requires_roles
def detalhes_categorizacao_faturamento_controle_creditos_json(id):
    """Retorna JSON com os detalhes da categorização de um faturamento de controle de créditos"""
    try:
        # Buscar o faturamento
        faturamento = FaturamentoModel.obter_faturamento_por_id(id)
        if not faturamento:
            return jsonify({'error': 'Faturamento não encontrado!'}), 404
            
        # Verificar se é um faturamento de controle de créditos
        if faturamento.tipo_operacao != 3 or faturamento.direcao_financeira != 2:
            return jsonify({'error': 'Este não é um faturamento de controle de créditos.'}), 400
            
        # Buscar o agendamento de pagamento
        agendamento = db.session.query(AgendamentoPagamentoModel).filter_by(faturamento_id=id).first()
        if not agendamento:
            return jsonify({'error': 'Este faturamento ainda não foi categorizado.'}), 404
            
        # Buscar dados relacionados
        pessoa = PessoaFinanceiroModel.obter_pessoa_por_id(agendamento.pessoa_financeiro_id)
        situacao = SituacaoPagamentoModel.obter_situacao_por_id(agendamento.situacao_pagamento_id)
        
        # Obter detalhes específicos de créditos do faturamento
        detalhes = faturamento.obter_detalhes()
        creditos_fornecedores = detalhes.get("credito_fornecedor", [])
        creditos_transportadoras = detalhes.get("credito_transportadora", [])
        creditos_extratores = detalhes.get("credito_extrator", [])

        # Formatar valores monetários
        def formatar_valor(valor_centavos):
            if valor_centavos is None:
                return 0.0
            return float(valor_centavos / 100) if isinstance(valor_centavos, (int, float)) else 0.0
        
        # Processar créditos de fornecedores para garantir campos corretos
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
        
        # Processar créditos de transportadoras para garantir campos corretos  
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

        # Processar créditos de extratores para garantir campos corretos  
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
        
        # Processar categorias
        categorias_processadas = []
        if agendamento.categorias_json:
            try:
                # Verificar se é objeto JSON ou string e converter adequadamente
                if isinstance(agendamento.categorias_json, (list, dict)):
                    categorias = agendamento.categorias_json
                elif isinstance(agendamento.categorias_json, str) and agendamento.categorias_json.strip():
                    categorias = json.loads(agendamento.categorias_json)
                else:
                    categorias = []
                
                for cat in categorias:
                    categoria_nome = cat.get('categoria', 'Não informado')
                    categoria_codigo = ''
                    categoria_detalhamento = cat.get('detalhamento', 'Não informado')
                    categoria_referencia = cat.get('referencia', 'Não informado')
                    
                    # Se for ID numérico, buscar dados completos da categoria
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
                
        # Processar centros de custo  
        centros_custo_processados = []
        if agendamento.centros_custo_json:
            try:
                # Verificar se é objeto JSON ou string e converter adequadamente
                if isinstance(agendamento.centros_custo_json, (list, dict)):
                    centros_custo = agendamento.centros_custo_json
                elif isinstance(agendamento.centros_custo_json, str) and agendamento.centros_custo_json.strip():
                    centros_custo = json.loads(agendamento.centros_custo_json)
                else:
                    centros_custo = []
                
                for cc in centros_custo:
                    centro_nome = cc.get('centro', 'Não informado')
                    
                    # Se for ID numérico, buscar dados completos do centro de custo
                    if str(centro_nome).isdigit():
                        centro_custo_obj = CentroCustoModel.obter_centro_custo_por_id(int(centro_nome))
                        if centro_custo_obj:
                            centro_nome = centro_custo_obj.nome
                    
                    # Converter valor de centavos para reais (baseado no exemplo: 32323 -> R$ 323,23)
                    valor_raw = cc.get('valor', 0)
                    valor_convertido = float(valor_raw) / 100 if isinstance(valor_raw, (int, float)) else 0.0
                    
                    # Converter percentual
                    percentual_raw = cc.get('percentual', 0)
                    percentual_convertido = float(percentual_raw) if percentual_raw and str(percentual_raw).strip() else 0.0
                    
                    centros_custo_processados.append({
                        'nome': centro_nome,
                        'valor': valor_convertido,
                        'percentual': percentual_convertido
                    })
                    
                print(f"[DEBUG] Centros de custo processados: {centros_custo_processados}")
            except (json.JSONDecodeError, ValueError) as e:
                print(f"[ERROR] Erro ao processar centros de custo: {e}")
                centros_custo_processados = []
                
        # Buscar parcelas se houver parcelamento
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
        
        # Calcular totais dos créditos
        valor_total_final = float(faturamento.valor_total / 100) if faturamento.valor_total else 0.0
        valor_bruto_total = float(faturamento.valor_bruto_total / 100) if faturamento.valor_bruto_total else valor_total_final
        
        # Calcular totais por tipo de crédito
        total_creditos_fornecedores = sum(c['valor_credito'] for c in creditos_fornecedores_processados)
        total_creditos_transportadoras = sum(c['valor_credito'] for c in creditos_transportadoras_processados)
        total_creditos_extratores = sum(c['valor_credito'] for c in creditos_extratores_processados)
        
        valor_credito_total = total_creditos_fornecedores + total_creditos_transportadoras + total_creditos_extratores

        # Montar resposta JSON específica para controle de créditos
        dados = {
            'categorizacao_id': agendamento.id,
            'faturamento': {
                'codigo': faturamento.codigo_faturamento,
                'tipo': 'Controle de Créditos',
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
        print(f"[ERRO] Erro ao buscar detalhes da categorização: {e}")
        return jsonify({'error': 'Erro interno do servidor. Tente novamente.'}), 500

@app.route('/financeiro/faturamentos/exportar-pdf/<int:faturamento_id>', methods=['GET','POST'])
@login_required
@requires_roles
def exportar_controle_creditos_pdf(faturamento_id):
    """Gera PDF do faturamento de controle de créditos"""
    try:
        # Buscar faturamento
        faturamento = FaturamentoModel.query.get_or_404(faturamento_id)
        
        # Verificar se é um faturamento de controle de créditos
        if faturamento.tipo_operacao != 3 or faturamento.direcao_financeira != 2:
            flash(("Este não é um faturamento de controle de créditos.", "error"))
            return redirect(url_for("listagem_faturamentos_controle_credito"))
        
        # Processar dados do faturamento
        dados_processados = processar_dados_faturamento(faturamento)
        
        # Dados adicionais para o template
        dados_extras = {
            'logo_path': obter_url_absoluta_de_imagem("logo.png"),
            'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'usuario_geracao': current_user.nome if hasattr(current_user, 'nome') else 'Sistema'
        }
        
        # Combinar todos os dados
        dados_template = {**dados_processados, **dados_extras}
        
        # Renderizar template HTML específico para controle de créditos
        html = render_template('financeiro/operacional/controle_creditos/relatorio_faturamento/relatorio_faturamento.html', **dados_template)

        # Gerar nome do arquivo
        codigo_fat = faturamento.codigo_faturamento
        nome_arquivo = f"Controle_Creditos_{codigo_fat}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Gerar PDF
        return ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo, orientacao="Portrait", abrir_em_nova_aba=True)
        
    except Exception as e:
        print(f"[ERROR exportar_controle_creditos_pdf] {e}")
        flash((f"Erro ao gerar PDF do controle de créditos! Contate o suporte. {e}", "error"))
        return redirect(url_for("listagem_faturamentos_controle_credito"))
    

@app.route('/financeiro/faturamentos/exportar-imagem/<int:faturamento_id>', methods=['GET','POST'])
@login_required
@requires_roles
def exportar_controle_creditos_imagem(faturamento_id):
    """Gera imagem JPG do faturamento de controle de créditos"""
    try:
        # Buscar faturamento
        faturamento = FaturamentoModel.query.get_or_404(faturamento_id)
        
        # Verificar se é um faturamento de controle de créditos
        if faturamento.tipo_operacao != 3 or faturamento.direcao_financeira != 2:
            flash(("Este não é um faturamento de controle de créditos.", "error"))
            return redirect(url_for("listagem_faturamentos_controle_credito"))
        
        # Processar dados do faturamento
        dados_processados = processar_dados_faturamento(faturamento)
        
        # Dados adicionais para o template
        dados_extras = {
            'logo_path': obter_url_absoluta_de_imagem("logo.png"),
            'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'usuario_geracao': current_user.nome if hasattr(current_user, 'nome') else 'Sistema'
        }
        
        # Combinar todos os dados
        dados_template = {**dados_processados, **dados_extras}

        # Renderizar template HTML específico para controle de créditos (versão imagem)
        html = render_template('financeiro/operacional/controle_creditos/relatorio_faturamento/relatorio_faturamento_imagem.html', **dados_template)

        # Gerar nome do arquivo
        codigo_fat = faturamento.codigo_faturamento
        nome_arquivo = f"Controle_Creditos_{codigo_fat}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Gerar IMAGEM
        return ManipulacaoArquivos.gerar_imagem_from_html(html, nome_arquivo, largura=1400, altura=1400)
        
    except Exception as e:
        print(f"[ERROR exportar_controle_creditos_imagem] {e}")
        flash((f"Erro ao gerar imagem do controle de créditos! Contate o suporte. {e}", "error"))
        return redirect(url_for("listagem_faturamentos_controle_credito"))

@app.route('/financeiro/controle-creditos/excluir/<int:faturamento_id>', methods=['GET', 'POST'])
@login_required
@requires_roles
def excluir_faturamento_creditos(faturamento_id):
    """
    Exclui um faturamento e todos os registros relacionados.
    Define situacao = 2 para todos os registros de pagamento.
    Devolve créditos utilizados para os fornecedores, transportadoras e extratores.
    """
    faturamento = FaturamentoModel.query.get_or_404(faturamento_id)
    
    try:
        # Verificar se o faturamento possui situação 6 (não pode ser excluído)
        if faturamento.situacao_pagamento_id == 6:
            flash(('Não é possível excluir este faturamento pois ele possui situação que não permite exclusão.', 'error'))
            return redirect(url_for('listagem_faturamentos_controle_credito'))
        
        # Buscar todos os agendamentos relacionados ao faturamento
        agendamentos = AgendamentoPagamentoModel.query.filter_by(
            faturamento_id=faturamento_id
        ).all()
        
        # Verificar se algum agendamento possui situação 1 (não pode ser excluído)
        agendamentos_situacao_1 = [ag for ag in agendamentos if ag.situacao_pagamento_id == 1]
        if agendamentos_situacao_1:
            flash(('Não é possível excluir este faturamento pois possui agendamentos com situação que não permite exclusão.', 'error'))
            return redirect(url_for('listagem_faturamentos_controle_credito'))
        
        # Atualizar situação de todos os agendamentos para 2 (pendente)
        for agendamento in agendamentos:
            agendamento.ativo = False
            agendamento.deletado = True

        # Processar detalhes do faturamento para marcar créditos como deletados e debitar saldos
        if faturamento.detalhes_json:
            try:
                detalhes = json.loads(faturamento.detalhes_json)
                
                # Processar créditos de fornecedores
                creditos_fornecedores = detalhes.get('credito_fornecedor', [])
                for credito_data in creditos_fornecedores:
                    extrato_credito_fornecedor_id = credito_data.get('extrato_credito_fornecedor_id')
                    fornecedor_id = credito_data.get('fornecedor_id')
                    valor_credito_100 = credito_data.get('valor_credito_100', 0)
                    
                    if extrato_credito_fornecedor_id:
                        # Buscar registro de crédito de fornecedor no extrato
                        extrato_credito = ExtratoCreditoFornecedorModel.query.get(extrato_credito_fornecedor_id)
                        if extrato_credito:
                            # Marcar como deletado e inativo
                            extrato_credito.deletado = True
                            extrato_credito.ativo = False
                    
                    if fornecedor_id and valor_credito_100 > 0:
                        # Debitar o valor do saldo agrupado do fornecedor
                        credito_agrupado = CreditoFornecedorModel.obtem_registro_id(fornecedor_id)
                        if credito_agrupado:
                            # Reduzir o valor do crédito agrupado
                            credito_agrupado.valor_total_credito_100 -= valor_credito_100

                # Processar créditos de transportadoras
                creditos_transportadoras = detalhes.get('credito_transportadora', [])
                for credito_data in creditos_transportadoras:
                    extrato_credito_transportadora_id = credito_data.get('extrato_credito_transportadora_id')
                    transportadora_id = credito_data.get('transportadora_id')
                    valor_credito_100 = credito_data.get('valor_credito_100', 0)
                    
                    if extrato_credito_transportadora_id:
                        # Buscar registro de crédito de transportadora no extrato
                        extrato_credito = ExtratoCreditoFreteiroModel.query.get(extrato_credito_transportadora_id)
                        if extrato_credito:
                            # Marcar como deletado e inativo
                            extrato_credito.deletado = True
                            extrato_credito.ativo = False
                    
                    if transportadora_id and valor_credito_100 > 0:
                        # Debitar o valor do saldo agrupado da transportadora
                        credito_agrupado = CreditoFreteiroModel.obtem_registro_id(transportadora_id)
                        if credito_agrupado:
                            # Reduzir o valor do crédito agrupado
                            credito_agrupado.valor_total_credito_100 -= valor_credito_100
                # Processar créditos de extratores
                creditos_extratores = detalhes.get('credito_extrator', [])
                for credito_data in creditos_extratores:
                    extrato_credito_extrator_id = credito_data.get('extrato_credito_extrator_id')
                    extrator_id = credito_data.get('extrator_id')
                    valor_credito_100 = credito_data.get('valor_credito_100', 0)
                    
                    if extrato_credito_extrator_id:
                        # Buscar registro de crédito de extrator no extrato
                        extrato_credito = ExtratoCreditoExtratorModel.query.get(extrato_credito_extrator_id)
                        if extrato_credito:
                            # Marcar como deletado e inativo
                            extrato_credito.deletado = True
                            extrato_credito.ativo = False
                    
                    if extrator_id and valor_credito_100 > 0:
                        # Debitar o valor do saldo agrupado do extrator
                        credito_agrupado = CreditoExtratorModel.obtem_registro_extrator_id(extrator_id)
                        if credito_agrupado:
                            # Reduzir o valor do crédito agrupado
                            credito_agrupado.valor_total_credito_100 -= valor_credito_100
                
            except json.JSONDecodeError as e:
                print(f"[ERROR] Erro ao processar JSON do faturamento: {e}")
                pass
        
        faturamento.ativo = False
        faturamento.deletado = True
        
        db.session.commit()
        flash(('Faturamento de controle de créditos excluído com sucesso! Registros de créditos foram deletados e os saldos foram debitados.', 'success'))
        
    except Exception as e:
        db.session.rollback()
        flash((f'Erro ao excluir faturamento: {str(e)}', 'error'))
    
    return redirect(url_for('listagem_faturamentos_controle_credito'))


def processar_dados_faturamento(faturamento):
    """Processa dados do faturamento para uso nos templates"""
    
    # Dados básicos do faturamento
    dados = {
        'faturamento': {
            'id': faturamento.id,
            'codigo_faturamento': faturamento.codigo_faturamento,
            'data_cadastro': faturamento.data_cadastro.strftime('%d/%m/%Y %H:%M') if faturamento.data_cadastro else '-',
            'usuario': faturamento.usuario.nome if faturamento.usuario else '-',
            'valor_bruto_total': faturamento.valor_bruto_total or 0,
            'valor_credito_aplicado': faturamento.valor_credito_aplicado or 0,
            'valor_total': faturamento.valor_total or 0,
            'tipo_operacao': 'Controle de Créditos' if faturamento.tipo_operacao == 3 else 'Outro',
            'direcao_financeira': 'Despesa' if faturamento.direcao_financeira == 2 else 'Outro',
            'situacao': faturamento.situacao.situacao if faturamento.situacao else 'Pendente'
        }
    }
    
    # Obter detalhes do faturamento
    detalhes = faturamento.obter_detalhes()
    
    # Processar créditos de fornecedores
    creditos_fornecedores = detalhes.get('credito_fornecedor', [])
    fornecedores_agrupados = agrupar_creditos_fornecedores_pdf(creditos_fornecedores)
    dados['fornecedores'] = fornecedores_agrupados
    dados['total_fornecedores'] = len(creditos_fornecedores)
    
    # Processar créditos de transportadoras
    creditos_transportadoras = detalhes.get('credito_transportadora', [])
    transportadoras_agrupadas = agrupar_creditos_transportadoras_pdf(creditos_transportadoras)
    dados['transportadoras'] = transportadoras_agrupadas
    dados['total_transportadoras'] = len(creditos_transportadoras)

    # Processar créditos de extratores
    creditos_extratores = detalhes.get('credito_extrator', [])
    extratores_agrupados = agrupar_creditos_extratores_pdf(creditos_extratores)
    dados['extratores'] = extratores_agrupados
    dados['total_extratores'] = len(creditos_extratores)

    # Não há receitas nem despesas avulsas no controle de créditos
    dados['receitas_avulsas'] = []
    dados['total_receitas_avulsas'] = 0
    dados['despesas_avulsas'] = []
    dados['total_despesas_avulsas'] = 0

    return dados


def agrupar_creditos_fornecedores_pdf(creditos_fornecedores):
    """Agrupa créditos de fornecedores para PDF"""
    from collections import defaultdict
    grupos = defaultdict(lambda: {'registros': [], 'total': 0.0})
    
    for credito in creditos_fornecedores:
        nome = credito.get('fornecedor_identificacao', 'Não informado')
        valor_centavos = credito.get('valor_credito_100', 0)
        valor_reais = valor_centavos / 100 if valor_centavos else 0.0
        
        # Preparar dados do crédito
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
    
    # Formatar total de cada grupo
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
        
        # Preparar dados do crédito
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
    
    # Formatar total de cada grupo
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
        
        # Preparar dados do crédito
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
    
    # Formatar total de cada grupo
    for grupo in grupos.values():
        grupo['total_formatado'] = f"R$ {grupo['total']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    return dict(grupos)
