from datetime import datetime
import json
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem, formatar_data_para_brl
from sistema._utilitarios.manipulacao_arquivos import ManipulacaoArquivos
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
from sistema.models_views.configuracoes_gerais.situacao_pagamento.situacao_pagamento_model import SituacaoPagamentoModel
from sistema.models_views.autenticacao.usuario_model import UsuarioModel
from sistema.models_views.gerenciar.pessoa_financeiro.pessoa_financeiro_model import PessoaFinanceiroModel
from sistema.models_views.financeiro.operacional.categorizar_fatura.categorizacao_model import AgendamentoPagamentoModel
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema._utilitarios import *


@app.route("/financeiro/operacional/cargas-a-receber", methods=["GET"])
@login_required
@requires_roles
def listagem_faturamentos_cargas_a_receber():
    """
    Lista todos os faturamentos realizados no sistema.
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

        
         # Obter faturamentos com base nos filtros utilizando o método do modelo
        faturamentos = FaturamentoModel.filtrar_a_receber_faturamentos(beneficiario, situacao_faturamento)
        
        # Obter situações de faturamento
        situacoes_faturamento = SituacaoPagamentoModel.listar_situacoes_faturamento()
        beneficiarios = PessoaFinanceiroModel.listar_pessoas_ativas()
        
        # Adicionar informação do usuário a cada faturamento
        for faturamento in faturamentos:
            if faturamento.usuario_id:
                usuario = UsuarioModel.query.get(faturamento.usuario_id)
                faturamento.usuario = usuario
        
        return render_template(
            "financeiro/operacional/cargas_a_receber/listagem_faturamentos.html",
            faturamentos=faturamentos,
            dados_corretos=request.args,
            situacoes_faturamento=situacoes_faturamento,
            beneficiarios=beneficiarios
        )
        
    except Exception as e:
        print(f"[ERROR listagem_faturamentos_cargas_a_pagar] {e}")
        flash(("Erro ao carregar listagem de faturamentos! Contate o suporte.", "error"))
        return redirect(url_for("listagem_faturamentos_cargas_a_pagar"))

@app.route("/financeiro/operacional/cargas-a-receber/detalhes/<int:id>", methods=["GET"])
@login_required
@requires_roles
def detalhes_faturamento_cargas_a_receber_ajax(id):
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
        
        # Preparar dados do faturamento
        dados_faturamento = {
            "codigo_faturamento": faturamento.codigo_faturamento,
            "data_cadastro": faturamento.data_cadastro.strftime("%d/%m/%Y %H:%M") if faturamento.data_cadastro else "",
            "usuario": f"{usuario.nome} {usuario.sobrenome}" if usuario else "N/A",
            "valor_total": formatar_valor(faturamento.valor_total),
            "valor_bruto_total": formatar_valor(faturamento.valor_bruto_total),
            "valor_credito_aplicado": formatar_valor(faturamento.valor_credito_aplicado),
            "valor_fornecedor": formatar_valor(faturamento.valor_fornecedor),
            "valor_transportadora": formatar_valor(faturamento.valor_transportadora),
            "valor_extrator": formatar_valor(faturamento.valor_extrator),
            "valor_comissionado": formatar_valor(getattr(faturamento, 'valor_comissionado', 0)),
            "utilizou_credito": "Sim" if faturamento.utilizou_credito else "Não",
            "situacao": faturamento.situacao.situacao if faturamento.situacao else "Pendente",
            "total_cargas_a_receber": len(detalhes.get("cargas_a_receber", [])),
            "total_nfs_complementares": len(detalhes.get("nf_complementar", [])),
            "total_nfs_servico": len(detalhes.get("nf_servico", [])),
        }
    
        
        # Formatar detalhes dos fornecedores
        cargas_a_receber_formatadas = []
        for carga in detalhes.get("cargas_a_receber", []):
            carga_formatada = {
                "carga_a_receber_id": carga.get("carga_a_receber_id", "N/A"),
                "solicitacao_id": carga.get("solicitacao_id", "N/A"),
                "fornecedor_identificacao": carga.get("fornecedor_identificacao", "N/A"),
                "cliente_id": carga.get("cliente_id", "N/A"),
                "cliente": carga.get("cliente", "N/A"),
                "valor_bruto": formatar_valor(carga.get("valor_bruto", "N/A")),
                "valor_credito": formatar_valor(carga.get("valor_credito", "N/A")),
                "valor_faturado": formatar_valor(carga.get("valor_faturado", "N/A")),
                "nota_fiscal": carga.get("nota_fiscal", "N/A"),
                "peso_ticket": carga.get("peso_ticket", 0),
                "preco_custo": formatar_valor(carga.get("preco_custo", 0)),
                "produto": carga.get("produto", "N/A"),
                "bitola": carga.get("bitola", "N/A"),
                "data_entrega": carga.get("data_entrega", "N/A"),
                "utiliza_credito": carga.get("utiliza_credito", "N/A"),
                "registro_operacional_id": carga.get("registro_operacional_id", "N/A"),
                "motorista" : carga.get("motorista", "N/A"),
            }
            cargas_a_receber_formatadas.append(carga_formatada)

        # Formatar detalhes das NFs complementares
        nfs_complementares_formatadas = []
        for nf in detalhes.get("nf_complementar", []):
            nf_formatada = {
                "nf_complementar_id": nf.get("nf_complementar_id", "N/A"),
                "numero_nf": nf.get("numero_nf", "N/A"),
                "cliente_id": nf.get("cliente_id", "N/A"),
                "cliente": nf.get("cliente", "N/A"),
                "valor_total_nota_100": nf.get("valor_total_nota_100", 0),
                "peso_ton_nf": nf.get("peso_ton_nf", "N/A"),
                "preco_un_nf": nf.get("preco_un_nf", 0),
                "destinatario_data_emissao": nf.get("destinatario_data_emissao", "N/A"),
            }
            nfs_complementares_formatadas.append(nf_formatada)

        # Formatar detalhes das NFs de Serviço
        nfs_servico_formatadas = []
        for nf in detalhes.get("nf_servico", []):
            nf_formatada = {
                "nf_servico_id": nf.get("nf_servico_id", "N/A"),
                "numero_nf": nf.get("numero_nf", "N/A"),
                "cliente_id": nf.get("cliente_id", "N/A"),
                "cliente": nf.get("cliente", "N/A"),
                "valor_total": nf.get("valor_total", 0),
                "discriminacao": nf.get("discriminacao", "N/A"),
                "data_emissao": nf.get("data_emissao", "N/A"),
            }
            nfs_servico_formatadas.append(nf_formatada)
            
        return jsonify({
            "faturamento": dados_faturamento,
            "cargas_a_receber": cargas_a_receber_formatadas,
            "nf_complementar": nfs_complementares_formatadas,
            "nf_servico": nfs_servico_formatadas,
        })
        
    except Exception as e:
        print(f"[ERROR detalhes_faturamento_ajax] {e}")
        return jsonify({"erro": "Erro interno do servidor"}), 500


@app.route("/financeiro/operacional/cargas-a-receber/nf-complementar/<int:nf_id>/registros-operacionais", methods=["GET"])
@login_required
@requires_roles
def obter_registros_operacionais_nf_complementar(nf_id):
    """
    Retorna os registros operacionais de uma NF complementar específica.
    """
    try:
        from sistema.models_views.faturamento.cargas_a_receber.nf_complementar.nf_complementar_model import NfComplementarModel
        
        # Buscar a NF complementar
        nf_complementar = NfComplementarModel.obter_por_id(nf_id)
        
        if not nf_complementar:
            return jsonify({"erro": "NF complementar não encontrada"}), 404
        
        registros_operacionais = []
        
        # Buscar registros operacionais dos detalhes da NF complementar
        if nf_complementar.nf_complementar_detalhes and 'registros_operacionais' in nf_complementar.nf_complementar_detalhes:
            registro_ids = [item['registro_id'] for item in nf_complementar.nf_complementar_detalhes['registros_operacionais']]
            if registro_ids:
                registros = RegistroOperacionalModel.query.filter(
                    RegistroOperacionalModel.id.in_(registro_ids)
                ).all()
                
                for reg in registros:
                    registro_formatado = {
                        "data_entrega_ticket": formatar_data_para_brl(reg.data_entrega_ticket) if reg.data_entrega_ticket else '-',
                        "fornecedor": reg.solicitacao.fornecedor.identificacao if reg.solicitacao and reg.solicitacao.fornecedor else '-',
                        "transportadora": reg.solicitacao.transportadora_exibicao.identificacao if reg.solicitacao and reg.solicitacao.transportadora_exibicao else '-',
                        "cliente": reg.solicitacao.cliente.identificacao if reg.solicitacao and reg.solicitacao.cliente else '-',
                        "placa_veiculo": reg.solicitacao.veiculo.placa_veiculo if reg.solicitacao and reg.solicitacao.veiculo else '-',
                        "motorista": reg.solicitacao.motorista.nome_completo if reg.solicitacao and reg.solicitacao.motorista else '-',
                        "produto": reg.solicitacao.produto.nome if reg.solicitacao and reg.solicitacao.produto else '-',
                        "bitola": reg.solicitacao.bitola.bitola if reg.solicitacao and reg.solicitacao.bitola else '-',
                        "peso_liquido_ticket": reg.peso_liquido_ticket or 0,
                        "numero_nota_fiscal": reg.numero_nota_fiscal or '-'
                    }
                    registros_operacionais.append(registro_formatado)
        
        return jsonify({
            "registros_operacionais": registros_operacionais
        })
        
    except Exception as e:
        print(f"[ERROR obter_registros_operacionais_nf_complementar] {e}")
        return jsonify({"erro": "Erro interno do servidor"}), 500


@app.route('/financeiro/operacional/cargas-a-receber/exportar-pdf/<int:faturamento_id>', methods=['GET','POST'])
@login_required
@requires_roles
def exportar_faturamento_cargas_a_receber_pdf(faturamento_id):
    """Gera PDF do faturamento com opções de ocultação"""
    try:
        # Buscar faturamento
        faturamento = FaturamentoModel.query.get_or_404(faturamento_id)
        
        # Processar dados do faturamento (reutilizar função existente)
        dados_processados = processar_dados_faturamento(faturamento)
        
        # Dados adicionais para o template
        dados_extras = {
            'logo_path': obter_url_absoluta_de_imagem("logo.png"),
            'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'usuario_geracao': current_user.nome if hasattr(current_user, 'nome') else 'Sistema'
        }
        
        # Combinar todos os dados
        dados_template = {**dados_processados, **dados_extras}

        # Renderizar template HTML
        html = render_template('financeiro/operacional/cargas_a_receber/relatorio_faturamento/relatorio_faturamento.html', **dados_template)

        # Gerar nome do arquivo
        codigo_fat = faturamento.codigo_faturamento
        nome_arquivo = f"Faturamento_{codigo_fat}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Gerar PDF
        return ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo, orientacao="Portrait", abrir_em_nova_aba=True)
        
    except Exception as e:
        print(f"[ERROR exportar_faturamento_pdf] {e}")
        flash((f"Erro ao gerar PDF do faturamento! Contate o suporte. {e}", "error"))
        return redirect(url_for("listagem_faturamentos_cargas_a_receber"))
    
@app.route('/financeiro/operacional/cargas-a-receber/exportar-imagem/<int:faturamento_id>', methods=['GET', 'POST'])
@login_required
@requires_roles
def exportar_faturamento_cargas_a_receber_imagem(faturamento_id):
    """Gera imagem JPG do faturamento com opções de ocultação"""
    try:
        # Buscar faturamento
        faturamento = FaturamentoModel.query.get_or_404(faturamento_id)
        
        dados_processados = processar_dados_faturamento(faturamento)
        
        # Dados adicionais para o template
        dados_extras = {
            'logo_path': obter_url_absoluta_de_imagem("logo.png"),
            'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'usuario_geracao': current_user.nome if hasattr(current_user, 'nome') else 'Sistema'
        }
        
        # Combinar todos os dados
        dados_template = {**dados_processados, **dados_extras}

        # USAR O MESMO TEMPLATE DO PDF
        html = render_template('financeiro/operacional/cargas_a_receber/relatorio_faturamento/relatorio_faturamento_imagem.html', **dados_template)

        # Gerar nome do arquivo
        codigo_fat = faturamento.codigo_faturamento
        nome_arquivo = f"Faturamento_{codigo_fat}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Gerar IMAGEM ao invés de PDF
        return ManipulacaoArquivos.gerar_imagem_from_html(html, nome_arquivo, largura=1400)
        
    except Exception as e:
        print(f"[ERROR exportar_faturamento_imagem] {e}")
        flash((f"Erro ao gerar imagem do faturamento! Contate o suporte. {e}", "error"))
        return redirect(url_for("listagem_faturamentos_cargas_a_receber"))
 

@app.route('/financeiro/cargas-a-receber/excluir/<int:faturamento_id>', methods=['GET', 'POST'])
@login_required
@requires_roles
def excluir_faturamento_a_receber(faturamento_id):
    """
    Exclui um faturamento de cargas a receber e coloca situação 2 nos registros operacionais.
    """
    faturamento = FaturamentoModel.query.get_or_404(faturamento_id)
    
    try:
        # Verificar se o faturamento possui situação 6 (não pode ser excluído)
        if faturamento.situacao_pagamento_id == 6:
            flash(('Não é possível excluir este faturamento pois ele possui situação que não permite exclusão.', 'error'))
            return redirect(url_for('listagem_faturamentos_cargas_a_receber'))
        
        # Buscar todos os agendamentos relacionados ao faturamento
        agendamentos = AgendamentoPagamentoModel.query.filter_by(
            faturamento_id=faturamento_id
        ).all()
        
        # Verificar se algum agendamento possui situação 1 (não pode ser excluído)
        agendamentos_situacao_1 = [ag for ag in agendamentos if ag.situacao_pagamento_id == 1]
        if agendamentos_situacao_1:
            flash(('Não é possível excluir este faturamento pois possui agendamentos com situação que não permite exclusão.', 'error'))
            return redirect(url_for('listagem_faturamentos_cargas_a_receber'))
        
        # Atualizar situação de todos os agendamentos para deletado/inativo
        for agendamento in agendamentos:
            agendamento.ativo = False
            agendamento.deletado = True

        # Processar cargas a receber para alterar situação dos registros operacionais
        if faturamento.detalhes_json:
            try:
                # Verificar se detalhes_json já é um dicionário ou string JSON
                if isinstance(faturamento.detalhes_json, dict):
                    detalhes = faturamento.detalhes_json
                else:
                    detalhes = json.loads(faturamento.detalhes_json)
                
                # Processar cargas a receber
                cargas_a_receber = detalhes.get('cargas_a_receber', [])
                for carga_data in cargas_a_receber:
                    registro_operacional_id = carga_data.get('registro_operacional_id')
                    if registro_operacional_id:
                        # Buscar registro operacional
                        registro = RegistroOperacionalModel.query.get(registro_operacional_id)
                        if registro:
                            # Alterar situação para 2 (pendente)
                            registro.situacao_financeira_id = 2
                
                # Processar NFs complementares
                nfs_complementares = detalhes.get('nf_complementar', [])
                for nf_data in nfs_complementares:
                    nf_complementar_id = nf_data.get('nf_complementar_id')
                    if nf_complementar_id:
                        try:
                            from sistema.models_views.faturamento.cargas_a_receber.nf_complementar.nf_complementar_model import NfComplementarModel
                            nf_complementar = NfComplementarModel.obter_por_id(nf_complementar_id)
                            if nf_complementar:
                                # Alterar situação para 2 (pendente)
                                nf_complementar.situacao_financeira_id = 2
                        except Exception as e:
                            print(f"[ERROR] Erro ao atualizar NF complementar {nf_complementar_id}: {e}")
                
                # Processar NFs de serviço
                nfs_servico = detalhes.get('nf_servico', [])
                for nf_data in nfs_servico:
                    nf_servico_id = nf_data.get('nf_servico_id')
                    if nf_servico_id:
                        try:
                            from sistema.models_views.faturamento.cargas_a_receber.nf_servico.nf_servico_model import NfServicoModel
                            nf_servico = NfServicoModel.obter_por_id(nf_servico_id)
                            if nf_servico:
                                # Alterar situação para 2 (pendente)
                                nf_servico.situacao_financeira_id = 2
                        except Exception as e:
                            print(f"[ERROR] Erro ao atualizar NF serviço {nf_servico_id}: {e}")
                
            except (json.JSONDecodeError, TypeError) as e:
                print(f"[ERROR] Erro ao processar detalhes do faturamento: {e}")
                pass
        
        # Marcar faturamento como excluído (ativo=False, deletado=True)
        faturamento.ativo = False
        faturamento.deletado = True
        
        db.session.commit()
        flash(('Faturamento de cargas a receber excluído com sucesso!', 'success'))
        
    except Exception as e:
        db.session.rollback()
        flash((f'Erro ao excluir faturamento: {str(e)}', 'error'))
    
    return redirect(url_for('listagem_faturamentos_cargas_a_receber'))

    

def processar_dados_faturamento(faturamento):
    """Processa dados do faturamento para uso nos templates"""
    
    # Obter detalhes do faturamento
    try:
        detalhes = faturamento.obter_detalhes()
    except:
        detalhes = {}
    
    # Processar detalhes JSON se existir (fallback)
    if not detalhes and faturamento.detalhes_json:
        try:
            detalhes = json.loads(faturamento.detalhes_json)
        except:
            detalhes = {}
    
    # Obter informações do usuário
    usuario = UsuarioModel.query.get(faturamento.usuario_id) if faturamento.usuario_id else None
    
    # Calcular período quinzenal baseado nas datas de entrega dos registros
    todas_datas = []
    
    # Coletar todas as datas de entrega das cargas a receber
    cargas_a_receber = detalhes.get('cargas_a_receber', [])
    for carga in cargas_a_receber:
        data_entrega = carga.get('data_entrega')
        if data_entrega and data_entrega != '-':
            todas_datas.append(data_entrega)
    
    # Determinar o período quinzenal
    periodo_quinzenal = DataHora.obter_periodo_quinzenal(todas_datas) if todas_datas else None
    
    # Dados básicos do faturamento
    dados = {
        'faturamento': {
            "codigo_faturamento": faturamento.codigo_faturamento,
            "data_cadastro": faturamento.data_cadastro.strftime("%d/%m/%Y %H:%M") if faturamento.data_cadastro else "",
            "usuario": f"{usuario.nome} {usuario.sobrenome}" if usuario else "N/A",
            "valor_total": faturamento.valor_total,
            "valor_bruto_total": faturamento.valor_bruto_total,
            "valor_credito_aplicado": faturamento.valor_credito_aplicado,
            "valor_cargas_a_receber": faturamento.valor_total,  # Para cargas a receber, o valor total é o valor das cargas
            "utilizou_credito": faturamento.utilizou_credito,
            "situacao": faturamento.situacao.situacao if faturamento.situacao else "Pendente",
            "periodo_quinzenal": periodo_quinzenal
        }
    }
    
    # Processar cargas a receber (clientes)
    cargas_a_receber = detalhes.get('cargas_a_receber', [])
    cargas_agrupadas = agrupar_clientes_pdf(cargas_a_receber)
    dados['cargas_a_receber'] = cargas_agrupadas
    dados['total_cargas_a_receber'] = len(cargas_a_receber)
    
    # Processar NFs complementares
    nfs_complementares = detalhes.get('nf_complementar', [])
    nfs_agrupadas = agrupar_nfs_complementares_pdf(nfs_complementares)
    dados['nfs_complementares'] = nfs_agrupadas
    dados['total_nfs_complementares'] = len(nfs_complementares)
    
    # Processar NFs de Serviço
    nfs_servico = detalhes.get('nf_servico', [])
    nfs_servico_agrupadas = agrupar_nfs_servico_pdf(nfs_servico)
    dados['nfs_servico'] = nfs_servico_agrupadas
    dados['total_nfs_servico'] = len(nfs_servico)
    
    # Opções padrão (podem ser customizadas posteriormente)
    dados['opcoes'] = {
        'ocultar_cliente': False,
        'ocultar_fornecedores': True,  # Para cargas a receber, não mostramos fornecedores
        'ocultar_transportadoras': True,  # Para cargas a receber, não mostramos transportadoras
        'ocultar_receitas_avulsas': True,
        'ocultar_despesas_avulsas': True,
    }
    
    # Calcular total de toneladas somando todos os peso_ticket das cargas a receber
    total_toneladas = 0.0
    for carga in cargas_a_receber:
        peso = carga.get('peso_ticket', 0)
        if peso:
            try:
                # Converter para float se for string
                if isinstance(peso, str):
                    peso = float(peso.replace(',', '.'))
                total_toneladas += float(peso)
            except (ValueError, TypeError):
                pass  # Ignorar valores inválidos
    
    # Somar também toneladas das NFs complementares (registros operacionais)
    for nf_grupo in nfs_agrupadas.values():
        for registro in nf_grupo.get('registros_operacionais', []):
            peso = registro.get('peso_liquido_ticket', 0)
            if peso:
                try:
                    if isinstance(peso, str):
                        peso = float(peso.replace(',', '.'))
                    total_toneladas += float(peso)
                except (ValueError, TypeError):
                    pass
    
    dados['totais'] = {
        'total_toneladas': round(total_toneladas, 2)
    }

    return dados


def agrupar_clientes_pdf(cargas_a_receber):
    """Agrupa cargas a receber por cliente para PDF"""
    from collections import defaultdict
    grupos = defaultdict(lambda: {'registros': [], 'total': 0})

    for carga in cargas_a_receber:
        nome_cliente = carga.get('cliente', 'Não informado')
        valor_faturado = carga.get('valor_faturado', 0)
        
        # Garantir que o valor seja numérico (em centavos)
        if isinstance(valor_faturado, str):
            valor_faturado = 0
        
        grupos[nome_cliente]['registros'].append(carga)
        grupos[nome_cliente]['total'] += valor_faturado
    
    return dict(grupos)

def agrupar_nfs_servico_pdf(nfs_servico):
    """Agrupa NFs de Serviço por cliente para PDF"""
    from collections import defaultdict
    
    grupos = defaultdict(lambda: {'nfs': [], 'total': 0})

    for nf_data in nfs_servico:
        nome_cliente = nf_data.get('cliente', 'Não informado')
        valor_nf = nf_data.get('valor_total', 0)
        
        # Garantir que o valor seja numérico (já em centavos)
        if isinstance(valor_nf, str):
            valor_nf = 0
        
        grupos[nome_cliente]['nfs'].append(nf_data)
        grupos[nome_cliente]['total'] += valor_nf
    
    return dict(grupos)

def agrupar_nfs_complementares_pdf(nfs_complementares):
    """Agrupa NFs complementares por cliente para PDF"""
    from collections import defaultdict
    from sistema.models_views.faturamento.cargas_a_receber.nf_complementar.nf_complementar_model import NfComplementarModel
    
    grupos = defaultdict(lambda: {'nfs': [], 'total': 0, 'registros_operacionais': []})

    for nf_data in nfs_complementares:
        nome_cliente = nf_data.get('cliente', 'Não informado')
        valor_nf = nf_data.get('valor_total_nota_100', 0)
        
        # Garantir que o valor seja numérico (já em centavos)
        if isinstance(valor_nf, str):
            valor_nf = 0
        
        # Buscar registros operacionais da NF complementar
        nf_id = nf_data.get('nf_complementar_id')
        registros_operacionais = []
        
        if nf_id:
            try:
                nf_complementar = NfComplementarModel.obter_por_id(nf_id)
                if nf_complementar and nf_complementar.nf_complementar_detalhes and 'registros_operacionais' in nf_complementar.nf_complementar_detalhes:
                    registro_ids = [item['registro_id'] for item in nf_complementar.nf_complementar_detalhes['registros_operacionais']]
                    if registro_ids:
                        registros = RegistroOperacionalModel.query.filter(
                            RegistroOperacionalModel.id.in_(registro_ids)
                        ).all()
                        
                        for reg in registros:
                            registro_formatado = {
                                "data_entrega_ticket": reg.data_entrega_ticket.strftime('%d/%m/%Y') if reg.data_entrega_ticket else '-',
                                "fornecedor": reg.solicitacao.fornecedor.identificacao if reg.solicitacao and reg.solicitacao.fornecedor else '-',
                                "transportadora": reg.solicitacao.transportadora_exibicao.identificacao if reg.solicitacao and reg.solicitacao.transportadora_exibicao else '-',
                                "cliente_reg": reg.solicitacao.cliente.identificacao if reg.solicitacao and reg.solicitacao.cliente else '-',
                                "placa_veiculo": reg.solicitacao.veiculo.placa_veiculo if reg.solicitacao and reg.solicitacao.veiculo else '-',
                                "motorista": reg.solicitacao.motorista.nome_completo if reg.solicitacao and reg.solicitacao.motorista else '-',
                                "produto": reg.solicitacao.produto.nome if reg.solicitacao and reg.solicitacao.produto else '-',
                                "bitola": reg.solicitacao.bitola.bitola if reg.solicitacao and reg.solicitacao.bitola else '-',
                                "peso_liquido_ticket": reg.peso_liquido_ticket or 0,
                                "numero_nota_fiscal": reg.numero_nota_fiscal or '-'
                            }
                            registros_operacionais.append(registro_formatado)
            except Exception as e:
                print(f"[ERROR] Erro ao buscar registros operacionais da NF {nf_id}: {e}")
        
        # Adicionar dados da NF com registros operacionais
        nf_completa = {**nf_data, 'registros_operacionais': registros_operacionais}
        
        grupos[nome_cliente]['nfs'].append(nf_completa)
        grupos[nome_cliente]['total'] += valor_nf
        grupos[nome_cliente]['registros_operacionais'].extend(registros_operacionais)
    
    return dict(grupos)

def agrupar_nfs_servico_pdf(nfs_servico):
    """Agrupa NFs de serviço por cliente para PDF"""
    from collections import defaultdict
    
    grupos = defaultdict(lambda: {'nfs': [], 'total': 0})

    for nf_data in nfs_servico:
        nome_cliente = nf_data.get('cliente', 'Não informado')
        valor_nf = nf_data.get('valor_total', 0)
        
        # Garantir que o valor seja numérico (já em centavos)
        if isinstance(valor_nf, str):
            valor_nf = 0
        
        # Usar os campos que realmente temos nas NFs de serviço
        nf_formatada = {
            'numero_nf': nf_data.get('numero_nf', '-'),
            'data_emissao': nf_data.get('data_emissao', '-'),
            'discriminacao': nf_data.get('discriminacao', '-'),
            'valor_total': valor_nf
        }
        
        grupos[nome_cliente]['nfs'].append(nf_formatada)
        grupos[nome_cliente]['total'] += valor_nf
    
    return dict(grupos)
