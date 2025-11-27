from datetime import datetime, date
import json
from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem, formatar_data_para_brl
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
from sistema.models_views.autenticacao.usuario_model import UsuarioModel
from sistema.models_views.financeiro.lancamento_avulso.lancamento_avulso_model import LancamentoAvulsoModel
from sistema.models_views.configuracoes_gerais.situacao_pagamento.situacao_pagamento_model import SituacaoPagamentoModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_model import FornecedorModel
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema.models_views.gerenciar.extrator.extrator_model import ExtratorModel
from sistema.models_views.gerenciar.comissionado.comissionado_model import ComissionadoModel
from sistema.models_views.gerenciar.pessoa_financeiro.pessoa_financeiro_model import PessoaFinanceiroModel
from sistema.models_views.financeiro.operacional.categorizar_fatura.categorizacao_model import AgendamentoPagamentoModel

# Imports para modelos de A Pagar
from sistema.models_views.faturamento.cargas_a_faturar.fornecedor.fornecedor_a_pagar_model import FornecedorPagarModel
from sistema.models_views.faturamento.cargas_a_faturar.transportadora.frete_a_pagar_model import FretePagarModel
from sistema.models_views.faturamento.cargas_a_faturar.extrator.extrator_a_pagar_model import ExtratorPagarModel
from sistema.models_views.faturamento.cargas_a_faturar.comissionado.comissionado_a_pagar_model import ComissionadoPagarModel

# Imports para modelos de Crédito
from sistema.models_views.faturamento.controle_credito.credito_agrupado.credito_fornecedor_model import CreditoFornecedorModel
from sistema.models_views.faturamento.controle_credito.credito_agrupado.credito_freteiro_model import CreditoFreteiroModel
from sistema.models_views.faturamento.controle_credito.credito_agrupado.credito_extrator_model import CreditoExtratorModel
from sistema.models_views.faturamento.controle_credito.extrato_credito.extrato_credito_fornecedor_model import ExtratoCreditoFornecedorModel
from sistema.models_views.faturamento.controle_credito.extrato_credito.extrato_credito_freteiro_model import ExtratoCreditoFreteiroModel
from sistema.models_views.faturamento.controle_credito.extrato_credito.extrato_credito_extrator_model import ExtratoCreditoExtratorModel
from sistema._utilitarios import *


@app.route("/financeiro/operacional/cargas-a-pagar", methods=["GET"])
@login_required
@requires_roles
def listagem_faturamentos_cargas_a_pagar():
    """
    Lista todos os faturamentos realizados no sistema com filtros opcionais.
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
        faturamentos = FaturamentoModel.filtrar_a_pagar_faturamentos(beneficiario, situacao_faturamento)

        # Obter situações de faturamento
        situacoes_faturamento = SituacaoPagamentoModel.listar_situacoes_faturamento()
        beneficiarios = PessoaFinanceiroModel.listar_pessoas_ativas()

        # Adicionar informação do usuário a cada faturamento
        for faturamento in faturamentos:
            if faturamento.usuario_id:
                usuario = UsuarioModel.query.get(faturamento.usuario_id)
                faturamento.usuario = usuario

        return render_template(
            "financeiro/faturamentos/listagem_faturamentos.html",
            faturamentos=faturamentos,
            dados_corretos=request.args,
            situacoes_faturamento=situacoes_faturamento,
            beneficiarios=beneficiarios
        )

    except Exception as e:
        flash(("Erro ao carregar listagem de faturamentos! Contate o suporte.", "error"))
        return redirect(url_for("listagem_faturamentos_cargas_a_pagar"))

@app.route("/financeiro/faturamentos/detalhes/<int:id>", methods=["GET"])
@login_required  
@requires_roles
def detalhes_faturamento_ajax(id):
    """
    Retorna os detalhes do faturamento em JSON para exibição no modal.
    """
    try:
        faturamento = FaturamentoModel.query.get_or_404(id)
        
        if not faturamento.ativo:
            return jsonify({"erro": "Faturamento não encontrado"}), 404
            
        # Tratamento seguro para obter detalhes
        try:
            detalhes = faturamento.obter_detalhes()
        except Exception as e:
            detalhes = {"fornecedores": [], "transportadoras": [], "extratores": [], "comissionados": [], "cargas_a_receber": [],
                       "credito_fornecedor": [], "credito_transportadora": [], "credito_extrator": []}
        
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
            "total_fornecedores": len(detalhes.get("fornecedores", [])),
            "total_transportadoras": len(detalhes.get("transportadoras", [])),
            "total_extratores": len(detalhes.get("extratores", [])),
            "total_comissionados": len(detalhes.get("comissionados", []))
        }
        
        # Formatar detalhes dos fornecedores
        fornecedores_formatados = []
        for fornecedor in detalhes.get("fornecedores", []):
            fornecedor_formatado = {
                "fornecedor_identificacao": fornecedor.get("fornecedor_identificacao", "N/A"),
                "cliente": fornecedor.get("cliente", "N/A"),
                "nota_fiscal": fornecedor.get("nota_fiscal", "N/A"),
                "produto": fornecedor.get("produto", "N/A"),
                "bitola": fornecedor.get("bitola", "N/A"),
                "peso_ticket": fornecedor.get("peso_ticket", "N/A"),
                "data_entrega": fornecedor.get("data_entrega", "N/A"),
                "placa_veiculo": fornecedor.get("placa_veiculo", "N/A"),
                "motorista": fornecedor.get("motorista", "N/A"),
                "valor_bruto": formatar_valor(fornecedor.get("valor_bruto", 0)),
                "valor_credito": formatar_valor(fornecedor.get("valor_credito", 0)),
                "valor_faturado": formatar_valor(fornecedor.get("valor_faturado", 0)),
                "preco_custo": formatar_valor(fornecedor.get("preco_custo", 0)),
                "utiliza_credito": "Sim" if fornecedor.get("utiliza_credito") == 1 else "Não"
            }
            fornecedores_formatados.append(fornecedor_formatado)
        
        # Formatar detalhes das transportadoras
        transportadoras_formatadas = []
        for transportadora in detalhes.get("transportadoras", []):
            transportadora_formatada = {
                "transportadora_identificacao": transportadora.get("nome", "N/A") if transportadora.get("nome") else transportadora.get("transportadora_identificacao", "N/A"),
                "fornecedor": transportadora.get("fornecedor", "N/A"),
                "cliente": transportadora.get("cliente", "N/A"),
                "nota_fiscal": transportadora.get("nota_fiscal", "N/A"),
                "produto": transportadora.get("produto", "N/A"),
                "bitola": transportadora.get("bitola", "N/A"),
                "peso_ticket": transportadora.get("peso_ticket", "N/A"),
                "data_entrega": transportadora.get("data_entrega", "N/A"),
                "placa": transportadora.get("placa", "N/A"),
                "motorista_registro": transportadora.get("motorista_registro", "N/A"),
                "valor_bruto": formatar_valor(transportadora.get("valor_bruto", 0)),
                "valor_credito": formatar_valor(transportadora.get("valor_credito", 0)),
                "valor_faturado": formatar_valor(transportadora.get("valor_faturado", 0)),
                "preco_custo": formatar_valor(transportadora.get("preco_custo", 0)),
                "utiliza_credito": "Sim" if transportadora.get("utiliza_credito") == 1 else "Não"
            }
            transportadoras_formatadas.append(transportadora_formatada)
        
        # Formatar detalhes dos extratores
        extratores_formatados = []
        for extrator in detalhes.get("extratores", []):
            extrator_formatado = {
                "nome": extrator.get("extrator_identificacao", "N/A"),
                "fornecedor": extrator.get("fornecedor", "N/A"),
                "cliente": extrator.get("cliente", "N/A"),
                "nota_fiscal": extrator.get("nota_fiscal", "N/A"),
                "produto": extrator.get("produto", "N/A"),
                "bitola": extrator.get("bitola", "N/A"),
                "peso_ticket": extrator.get("peso_ticket", "N/A"),
                "data_entrega": extrator.get("data_entrega", "N/A"),
                "placa": extrator.get("placa", "N/A"),
                "motorista_registro": extrator.get("motorista_registro", "N/A"),
                "valor_bruto": formatar_valor(extrator.get("valor_bruto", 0)),
                "valor_credito": formatar_valor(extrator.get("valor_credito", 0)),
                "valor_faturado": formatar_valor(extrator.get("valor_faturado", 0)),
                "preco_custo": formatar_valor(extrator.get("preco_custo", 0)),
                "utiliza_credito": "Sim" if extrator.get("utiliza_credito") == 1 else "Não"
            }
            extratores_formatados.append(extrator_formatado)

        # Formatar detalhes dos comissionados
        comissionados_formatados = []
        for comissionado in detalhes.get("comissionados", []):
            comissionado_formatado = {
                "nome": comissionado.get("comissionado_identificacao", "N/A"),
                "fornecedor": comissionado.get("fornecedor", "N/A"),
                "cliente": comissionado.get("cliente", "N/A"),
                "nota_fiscal": comissionado.get("nota_fiscal", "N/A"),
                "produto": comissionado.get("produto", "N/A"),
                "bitola": comissionado.get("bitola", "N/A"),
                "peso_ticket": comissionado.get("peso_ticket", "N/A"),
                "data_entrega": comissionado.get("data_entrega", "N/A"),
                "placa": comissionado.get("placa", "N/A"),
                "motorista_registro": comissionado.get("motorista_registro", "N/A"),
                "valor_bruto": formatar_valor(comissionado.get("valor_bruto", 0)),
                "valor_credito": formatar_valor(comissionado.get("valor_credito", 0)),
                "valor_faturado": formatar_valor(comissionado.get("valor_faturado", 0)),
                "preco_custo": formatar_valor(comissionado.get("preco_custo", 0)),
                "utiliza_credito": "Sim" if comissionado.get("utiliza_credito") == 1 else "Não"
            }
            comissionados_formatados.append(comissionado_formatado)

        # Buscar receitas e despesas avulsas apenas se este faturamento for de lançamento avulso
        receitas_avulsas_formatadas = []
        despesas_avulsas_formatadas = []
        
        if faturamento.lancamento_avulso_id and faturamento.lancamento_avulso:
            lancamento = faturamento.lancamento_avulso
            
            # Se for receita avulsa (tipo_movimentacao = 1)
            if lancamento.tipo_movimentacao == 1:
                receita_formatada = {
                    "descricao": lancamento.descricao or "N/A",
                    "valor": formatar_valor(lancamento.valor_movimentacao_100),
                    "conta_bancaria": lancamento.conta_bancaria.identificacao if lancamento.conta_bancaria else "N/A",
                    "data_cadastro": lancamento.data_cadastro.strftime("%d/%m/%Y %H:%M") if lancamento.data_cadastro else "N/A",
                    "situacao": lancamento.situacao.situacao if lancamento.situacao else "Pendente"
                }
                receitas_avulsas_formatadas.append(receita_formatada)
                
            # Se for despesa avulsa (tipo_movimentacao = 2)
            elif lancamento.tipo_movimentacao == 2:
                despesa_formatada = {
                    "descricao": lancamento.descricao or "N/A",
                    "valor": formatar_valor(lancamento.valor_movimentacao_100),
                    "conta_bancaria": lancamento.conta_bancaria.identificacao if lancamento.conta_bancaria else "N/A",
                    "data_cadastro": lancamento.data_cadastro.strftime("%d/%m/%Y %H:%M") if lancamento.data_cadastro else "N/A",
                    "situacao": lancamento.situacao.situacao if lancamento.situacao else "Pendente"
                }
                despesas_avulsas_formatadas.append(despesa_formatada)

        # Atualizar dados do faturamento com totais de receitas e despesas
        dados_faturamento["total_receitas_avulsas"] = len(receitas_avulsas_formatadas)
        dados_faturamento["total_despesas_avulsas"] = len(despesas_avulsas_formatadas)

        # Formatar detalhes dos créditos utilizados
        creditos_utilizados_formatados = []
        
        # Processar créditos de fornecedor
        credito_fornecedor = detalhes.get("credito_fornecedor", [])
        if credito_fornecedor:
            for credito in credito_fornecedor:
                # Buscar código do faturamento origem
                extrato_credito_id = credito.get("extrato_credito_fornecedor_id")
                codigo_faturamento_origem = FaturamentoModel.buscar_faturamento_origem_por_extrato(extrato_credito_id, 'fornecedor')
                
                credito_formatado = {
                    "categoria": "Fornecedor",
                    "identificacao": credito.get("fornecedor_identificacao", credito.get("descricao", "N/A")),
                    "descricao": credito.get("credito_descricao", credito.get("descricao", "Crédito de Fornecedor")),
                    "valor_utilizado": formatar_valor(credito.get("valor", 0)),
                    "codigo_faturamento": codigo_faturamento_origem
                }
                creditos_utilizados_formatados.append(credito_formatado)
        
        # Processar créditos de transportadora
        credito_transportadora = detalhes.get("credito_transportadora", [])
        if credito_transportadora:
            for credito in credito_transportadora:
                # Buscar código do faturamento origem
                extrato_credito_id = credito.get("extrato_credito_transportadora_id")
                codigo_faturamento_origem = FaturamentoModel.buscar_faturamento_origem_por_extrato(extrato_credito_id, 'transportadora')
                
                credito_formatado = {
                    "categoria": "Frete",
                    "identificacao": credito.get("transportadora_identificacao", credito.get("descricao", "N/A")),
                    "descricao": credito.get("credito_descricao", credito.get("descricao", "Crédito de Transportadora")),
                    "valor_utilizado": formatar_valor(credito.get("valor", 0)),
                    "codigo_faturamento": codigo_faturamento_origem
                }
                creditos_utilizados_formatados.append(credito_formatado)
        
        # Processar créditos de extrator
        credito_extrator = detalhes.get("credito_extrator", [])
        if credito_extrator:
            for credito in credito_extrator:
                # Buscar código do faturamento origem
                extrato_credito_id = credito.get("extrato_credito_extrator_id")
                codigo_faturamento_origem = FaturamentoModel.buscar_faturamento_origem_por_extrato(extrato_credito_id, 'extrator')
                
                credito_formatado = {
                    "categoria": "Extrator",
                    "identificacao": credito.get("extrator_identificacao", credito.get("descricao", "N/A")),
                    "descricao": credito.get("credito_descricao", credito.get("descricao", "Crédito de Extrator")),
                    "valor_utilizado": formatar_valor(credito.get("valor", 0)),
                    "codigo_faturamento": codigo_faturamento_origem
                }
                creditos_utilizados_formatados.append(credito_formatado)

        return jsonify({
            "faturamento": dados_faturamento,
            "fornecedores": fornecedores_formatados,
            "transportadoras": transportadoras_formatadas,
            "extratores": extratores_formatados,
            "comissionados": comissionados_formatados,
            "receitas_avulsas": receitas_avulsas_formatadas,
            "despesas_avulsas": despesas_avulsas_formatadas,
            "creditos_utilizados": creditos_utilizados_formatados
        })
        
    except Exception as e:
        return jsonify({"erro": "Erro interno do servidor"}), 500


@app.route('/financeiro/faturamentos/dados-bancarios/<int:faturamento_id>')
@login_required  
@requires_roles
def dados_bancarios_faturamento(faturamento_id):
    """Retorna todos os dados bancários de um faturamento"""
    try:
        faturamento = FaturamentoModel.query.get_or_404(faturamento_id)
        
        # Processar detalhes JSON para obter IDs únicos
        detalhes = {}
        if faturamento.detalhes_json:
            try:
                # Verificar se detalhes_json já é um dicionário ou string JSON
                if isinstance(faturamento.detalhes_json, dict):
                    detalhes = faturamento.detalhes_json
                else:
                    detalhes = json.loads(faturamento.detalhes_json)
            except (json.JSONDecodeError, TypeError):
                detalhes = {}
        
        # Obter fornecedores únicos
        fornecedores_ids = set()
        if detalhes.get('fornecedores'):
            for fornecedor in detalhes['fornecedores']:
                if fornecedor.get('fornecedor_id'):
                    fornecedores_ids.add(fornecedor['fornecedor_id'])
        
        # Obter transportadoras únicas
        transportadoras_ids = set()
        if detalhes.get('transportadoras'):
            for transportadora in detalhes['transportadoras']:
                if transportadora.get('transportadora_id'):
                    transportadoras_ids.add(transportadora['transportadora_id'])

        # Obter extratores únicos
        extratores_ids = set()
        if detalhes.get('extratores'):
            for extrator in detalhes['extratores']:
                if extrator.get('extrator_id'):
                    extratores_ids.add(extrator['extrator_id'])

        # Obter comissionados únicos
        comissionados_ids = set()
        if detalhes.get('comissionados'):
            for comissionado in detalhes['comissionados']:
                if comissionado.get('comissionado_id'):
                    comissionados_ids.add(comissionado['comissionado_id'])
        
        # Buscar dados bancários dos fornecedores
        fornecedores_dados = []
        for fornecedor_id in fornecedores_ids:
            fornecedor = FornecedorModel.query.get(fornecedor_id)
            if fornecedor:
                fornecedores_dados.append({
                    'identificacao': fornecedor.identificacao,
                    'instituicao_financeira': fornecedor.instituicao_financeira.nome if fornecedor.instituicao_financeira else 'Banco não informado',
                    'agencia_bancaria': fornecedor.agencia_bancaria,
                    'conta_bancaria': fornecedor.conta_bancaria,
                    'chave_pix': fornecedor.chave_pix
                })
        
        # Buscar dados bancários das transportadoras
        transportadoras_dados = []
        for transportadora_id in transportadoras_ids:
            transportadora = TransportadoraModel.query.get(transportadora_id)
            if transportadora:
                transportadoras_dados.append({
                    'identificacao': transportadora.identificacao,
                    'instituicao_financeira': transportadora.instituicao_financeira.nome if transportadora.instituicao_financeira else 'Banco não informado',
                    'agencia_bancaria': transportadora.agencia_bancaria,
                    'conta_bancaria': transportadora.conta_bancaria,
                    'chave_pix': transportadora.chave_pix
                })
        
        # Buscar dados bancários dos extratores
        extratores_dados = []
        for extrator_id in extratores_ids:
            extrator = ExtratorModel.query.get(extrator_id)
            if extrator:
                extratores_dados.append({
                    'identificacao': extrator.identificacao,
                    'instituicao_financeira': extrator.instituicao_financeira.nome if extrator.instituicao_financeira else 'Banco não informado',
                    'agencia_bancaria': extrator.agencia_bancaria,
                    'conta_bancaria': extrator.conta_bancaria,
                    'chave_pix': extrator.chave_pix
                })

        # Buscar dados bancários dos comissionados
        comissionados_dados = []
        for comissionado_id in comissionados_ids:
            comissionado = ComissionadoModel.query.get(comissionado_id)
            if comissionado:
                comissionados_dados.append({
                    'identificacao': comissionado.identificacao,
                    'instituicao_financeira': comissionado.instituicao_financeira.nome if comissionado.instituicao_financeira else 'Banco não informado',
                    'agencia_bancaria': comissionado.agencia_bancaria,
                    'conta_bancaria': comissionado.conta_bancaria,
                    'chave_pix': comissionado.chave_pix
                })

        # Buscar dados bancários de receitas e despesas avulsas
        receitas_avulsas_dados = []
        despesas_avulsas_dados = []
        
        if faturamento.lancamento_avulso_id and faturamento.lancamento_avulso:
            lancamento = faturamento.lancamento_avulso
            
            if lancamento.conta_bancaria:
                dados_conta = {
                    'descricao': lancamento.descricao or 'Lançamento Avulso',
                    'identificacao': lancamento.conta_bancaria.identificacao,
                    'instituicao_financeira': lancamento.conta_bancaria.nome_banco,
                    'agencia_bancaria': lancamento.conta_bancaria.agencia,
                    'conta_bancaria': lancamento.conta_bancaria.conta,
                    'chave_pix': 'N/A'  # ContaBancariaModel não tem campo PIX
                }
                
                # Adicionar ao array correto baseado no tipo
                if lancamento.tipo_movimentacao == 1:  # Receita
                    receitas_avulsas_dados.append(dados_conta)
                elif lancamento.tipo_movimentacao == 2:  # Despesa
                    despesas_avulsas_dados.append(dados_conta)
        
        return jsonify({
            'fornecedores': fornecedores_dados,
            'transportadoras': transportadoras_dados,
            'extratores': extratores_dados,
            'comissionados': comissionados_dados,
            'receitas_avulsas': receitas_avulsas_dados,
            'despesas_avulsas': despesas_avulsas_dados
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/financeiro/fornecedors/dados-bancarios/<int:fornecedor_id>')
@login_required  
@requires_roles
def dados_bancarios_fornecedor(fornecedor_id):
    """Retorna dados bancários de um fornecedor específico"""
    try:
        fornecedor = FornecedorModel.query.get_or_404(fornecedor_id)
        
        return jsonify({
            'identificacao': fornecedor.identificacao,
            'instituicao_financeira': fornecedor.instituicao_financeira.nome if fornecedor.instituicao_financeira else 'Banco não informado',
            'agencia_bancaria': fornecedor.agencia_bancaria,
            'conta_bancaria': fornecedor.conta_bancaria,
            'chave_pix': fornecedor.chave_pix
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/financeiro/transportadoras/dados-bancarios/<int:transportadora_id>')
@login_required  
@requires_roles
def dados_bancarios_transportadora(transportadora_id):
    """Retorna dados bancários de uma transportadora específica"""
    try:
        transportadora = TransportadoraModel.query.get_or_404(transportadora_id)
        
        return jsonify({
            'identificacao': transportadora.identificacao,
            'instituicao_financeira': transportadora.instituicao_financeira.nome if transportadora.instituicao_financeira else 'Banco não informado',
            'agencia_bancaria': transportadora.agencia_bancaria,
            'conta_bancaria': transportadora.conta_bancaria,
            'chave_pix': transportadora.chave_pix
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/financeiro/extratores/dados-bancarios/<int:extrator_id>')
@login_required  
@requires_roles
def dados_bancarios_extrator(extrator_id):
    """Retorna dados bancários de um extrator específico"""
    try:
        extrator = ExtratorModel.query.get_or_404(extrator_id)

        return jsonify({
            'identificacao': extrator.identificacao,
            'instituicao_financeira': extrator.instituicao_financeira.nome if extrator.instituicao_financeira else 'Banco não informado',
            'agencia_bancaria': extrator.agencia_bancaria,
            'conta_bancaria': extrator.conta_bancaria,
            'chave_pix': extrator.chave_pix
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/financeiro/comissionados/dados-bancarios/<int:comissionado_id>')
@login_required  
@requires_roles
def dados_bancarios_comissionado(comissionado_id):
    """Retorna dados bancários de um comissionado específico"""
    try:
        comissionado = ComissionadoModel.query.get_or_404(comissionado_id)

        return jsonify({
            'identificacao': comissionado.identificacao,
            'instituicao_financeira': comissionado.instituicao_financeira.nome if comissionado.instituicao_financeira else 'Banco não informado',
            'agencia_bancaria': comissionado.agencia_bancaria,
            'conta_bancaria': comissionado.conta_bancaria,
            'chave_pix': comissionado.chave_pix
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/financeiro/cargas-a-pagar/excluir/<int:faturamento_id>', methods=['GET', 'POST'])
@login_required
@requires_roles
def excluir_faturamento_a_pagar(faturamento_id):
    """
    Exclui um faturamento e todos os registros relacionados.
    Define situacao = 2 para todos os registros de pagamento.
    Devolve créditos utilizados para os fornecedores, transportadoras e extratores.
    """
    faturamento = FaturamentoModel.query.get_or_404(faturamento_id)
    
    try:
        # Verificar se o faturamento possui situação 6 (não pode ser excluído)
        if faturamento.situacao_pagamento_id == 6 and current_user.role_id != 1:
            flash(('Não é possível excluir este faturamento pois ele possui situação que não permite exclusão.', 'error'))
            return redirect(url_for('listagem_faturamentos_cargas_a_pagar'))
        
        # Buscar todos os agendamentos relacionados ao faturamento
        agendamentos = AgendamentoPagamentoModel.query.filter_by(
            faturamento_id=faturamento_id
        ).all()
        
        # Verificar se algum agendamento possui situação 1 (não pode ser excluído)
        agendamentos_situacao_1 = [ag for ag in agendamentos if ag.situacao_pagamento_id == 1]
        if agendamentos_situacao_1:
            flash(('Não é possível excluir este faturamento pois possui agendamentos com situação que não permite exclusão.', 'error'))
            return redirect(url_for('listagem_faturamentos_cargas_a_pagar'))
        
        # Atualizar situação de todos os agendamentos para 2 (pendente)
        for agendamento in agendamentos:
            agendamento.ativo = False
            agendamento.deletado = True

        # Processar detalhes do faturamento para devolver créditos e alterar situações
        if faturamento.detalhes_json:
            try:
                # Verificar se detalhes_json já é um dicionário ou string JSON
                if isinstance(faturamento.detalhes_json, dict):
                    detalhes = faturamento.detalhes_json
                else:
                    detalhes = json.loads(faturamento.detalhes_json)
                
                # Processar fornecedores
                fornecedores = detalhes.get('fornecedores', [])
                for fornecedor_data in fornecedores:
                    fornecedor_a_pagar_id = fornecedor_data.get('fornecedor_a_pagar_id')
                    if fornecedor_a_pagar_id:
                        # Buscar registro de fornecedor a pagar
                        fornecedor_pagar = FornecedorPagarModel.query.get(fornecedor_a_pagar_id)
                        if fornecedor_pagar:
                            # Alterar situação para 2 (pendente)
                            fornecedor_pagar.situacao_pagamento_id = 2

                # Processar transportadoras
                transportadoras = detalhes.get('transportadoras', [])
                for transportadora_data in transportadoras:
                    frete_a_pagar_id = transportadora_data.get('frete_a_pagar_id')
                    if frete_a_pagar_id:
                        # Buscar registro de frete a pagar
                        frete_pagar = FretePagarModel.query.get(frete_a_pagar_id)
                        if frete_pagar:
                            # Alterar situação para 2 (pendente)
                            frete_pagar.situacao_pagamento_id = 2

                # Processar extratores
                extratores = detalhes.get('extratores', [])
                for extrator_data in extratores:
                    extrator_a_pagar_id = extrator_data.get('extrator_a_pagar_id')
                    if extrator_a_pagar_id:
                        # Buscar registro de extrator a pagar
                        extrator_pagar = ExtratorPagarModel.query.get(extrator_a_pagar_id)
                        if extrator_pagar:
                            # Alterar situação para 2 (pendente)
                            extrator_pagar.situacao_pagamento_id = 2

                # Processar comissionados
                comissionados = detalhes.get('comissionados', [])
                for comissionado_data in comissionados:
                    comissionado_a_pagar_id = comissionado_data.get('comissionado_a_pagar_id')
                    if comissionado_a_pagar_id:
                        # Buscar registro de comissionado a pagar
                        comissionado_pagar = ComissionadoPagarModel.query.get(comissionado_a_pagar_id)
                        if comissionado_pagar:
                            # Alterar situação para 2 (pendente)
                            comissionado_pagar.situacao_pagamento_id = 2

                # Devolver créditos utilizados
                _devolver_creditos_faturamento(detalhes)
                
            except (json.JSONDecodeError, TypeError) as e:
                print(f"[ERROR] Erro ao processar detalhes do faturamento: {e}")
                pass
        
        # Marcar faturamento como excluído (ativo=False, deletado=True)
        faturamento.ativo = False
        faturamento.deletado = True
        
        db.session.commit()
        flash(('Faturamento excluído com sucesso!', 'success'))
        
    except Exception as e:
        print(e)
        db.session.rollback()
        flash((f'Erro ao excluir faturamento!', 'error'))
    
    return redirect(url_for('listagem_faturamentos_cargas_a_pagar'))


def _devolver_creditos_faturamento(detalhes):
    """
    Devolve os créditos utilizados no faturamento.
    
    Args:
        detalhes (dict): Dicionário com os detalhes do faturamento
    """
    try:
        # Processar créditos de fornecedor
        credito_fornecedor = detalhes.get('credito_fornecedor', [])
        for credito_data in credito_fornecedor:
            credito_id = credito_data.get('credito_id')
            valor_utilizado = credito_data.get('valor', 0)
            fornecedor_id = credito_data.get('fornecedor_id')
            
            if credito_id and valor_utilizado and fornecedor_id:
                # Buscar o registro de crédito original
                credito_original = ExtratoCreditoFornecedorModel.query.get(credito_id)
                if credito_original:
                    # Criar novo registro de estorno
                    estorno = ExtratoCreditoFornecedorModel(
                        data_movimentacao=date.today(),
                        descricao=f"{credito_data.get('descricao', 'Crédito')}",
                        fornecedor_id=fornecedor_id,
                        valor_credito_100=valor_utilizado,
                        usuario_id=current_user.id,
                        tipo_movimentacao=4,  # Tipo 4 = Estorno
                        ativo=True
                    )
                    db.session.add(estorno)
                    
                    # Atualizar o crédito agrupado
                    credito_agrupado = CreditoFornecedorModel.obtem_registro_id(fornecedor_id)
                    if credito_agrupado:
                        credito_agrupado.valor_total_credito_100 += valor_utilizado
                    else:
                        # Criar novo registro de crédito agrupado se não existir
                        novo_credito = CreditoFornecedorModel(
                            data_movimentacao=date.today(),
                            fornecedor_id=fornecedor_id,
                            valor_total_credito_100=valor_utilizado
                        )
                        db.session.add(novo_credito)
                    
        # Processar créditos de transportadora
        credito_transportadora = detalhes.get('credito_transportadora', [])
        for credito_data in credito_transportadora:
            credito_id = credito_data.get('credito_id')
            valor_utilizado = credito_data.get('valor', 0)
            transportadora_id = credito_data.get('transportadora_id')
            
            if credito_id and valor_utilizado and transportadora_id:
                # Buscar o registro de crédito original
                credito_original = ExtratoCreditoFreteiroModel.query.get(credito_id)
                if credito_original: 
                                       
                    # Criar novo registro de estorno
                    estorno = ExtratoCreditoFreteiroModel(
                        data_movimentacao=date.today(),
                        descricao=f"{credito_data.get('descricao', 'Crédito')}",
                        transportadora_id=transportadora_id,
                        valor_credito_100=valor_utilizado,
                        usuario_id=current_user.id,
                        tipo_movimentacao=4,  # Tipo 4 = Estorno
                        ativo=True
                    )
                    db.session.add(estorno)
                    
                    # Atualizar o crédito agrupado
                    credito_agrupado = CreditoFreteiroModel.query.filter_by(
                        transportadora_id=transportadora_id,
                        ativo=True,
                        deletado=False
                    ).first()
                    if credito_agrupado:
                        credito_agrupado.valor_total_credito_100 += valor_utilizado
                    else:
                        # Criar novo registro de crédito agrupado se não existir
                        novo_credito = CreditoFreteiroModel(
                            data_movimentacao=date.today(),
                            transportadora_id=transportadora_id,
                            valor_total_credito_100=valor_utilizado
                        )
                        db.session.add(novo_credito)
                    
        # Processar créditos de extrator
        credito_extrator = detalhes.get('credito_extrator', [])
        for credito_data in credito_extrator:
            credito_id = credito_data.get('credito_id')
            valor_utilizado = credito_data.get('valor', 0)
            extrator_id = credito_data.get('extrator_id')
            
            if credito_id and valor_utilizado and extrator_id:
                # Buscar o registro de crédito original
                credito_original = ExtratoCreditoExtratorModel.query.get(credito_id)
                if credito_original:
                
                    # Criar novo registro de estorno
                    estorno = ExtratoCreditoExtratorModel(
                        data_movimentacao=date.today(),
                        descricao=f"{credito_data.get('descricao', 'Crédito')}",
                        extrator_id=extrator_id,
                        valor_credito_100=valor_utilizado,
                        usuario_id=current_user.id,
                        tipo_movimentacao=4,  # Tipo 4 = Estorno
                        ativo=True
                    )
                    db.session.add(estorno)
                    
                    # Atualizar o crédito agrupado
                    credito_agrupado = CreditoExtratorModel.query.filter_by(
                        extrator_id=extrator_id,
                        ativo=True,
                        deletado=False
                    ).first()
                    if credito_agrupado:
                        credito_agrupado.valor_total_credito_100 += valor_utilizado
                    else:
                        # Criar novo registro de crédito agrupado se não existir
                        novo_credito = CreditoExtratorModel(
                            data_movimentacao=date.today(),
                            extrator_id=extrator_id,
                            valor_total_credito_100=valor_utilizado
                        )
                        db.session.add(novo_credito)
                    
    except Exception as e:
        raise e

@app.route('/financeiro/cargas-a-pagar/exportar-pdf/<int:faturamento_id>', methods=['POST'])
@login_required
@requires_roles
def exportar_faturamento_pdf(faturamento_id):
    """Gera PDF do faturamento com opções de ocultação"""
    try:
        # Buscar faturamento
        faturamento = FaturamentoModel.query.get_or_404(faturamento_id)
        
        # Obter opções de ocultação do formulário
        opcoes = {
            'ocultar_fornecedores': request.form.get('ocultar_fornecedores') == 'true',
            'ocultar_transportadoras': request.form.get('ocultar_transportadoras') == 'true',
            'ocultar_cliente': request.form.get('ocultar_cliente') == 'true',
            'ocultar_receitas_avulsas': request.form.get('ocultar_receitas_avulsas') == 'true',
            'ocultar_despesas_avulsas': request.form.get('ocultar_despesas_avulsas') == 'true'
        }
        
        # Processar dados do faturamento (reutilizar função existente)
        dados_processados = processar_dados_faturamento(faturamento)
                
        # Dados adicionais para o template
        dados_extras = {
            'opcoes': opcoes,
            'logo_path': obter_url_absoluta_de_imagem("logo.png"),
            'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'usuario_geracao': current_user.nome if hasattr(current_user, 'nome') else 'Sistema'
        }
        
        # Combinar todos os dados
        dados_template = {**dados_processados, **dados_extras}

        # Renderizar template HTML
        html = render_template('financeiro/faturamentos/relatorio_faturamento/relatorio_faturamento.html', **dados_template)
        
        # Gerar nome do arquivo
        codigo_fat = faturamento.codigo_faturamento
        nome_arquivo = f"Faturamento_{codigo_fat}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Gerar PDF
        return ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo, orientacao="Portrait", abrir_em_nova_aba=True)
        
    except Exception as e:
        flash((f"Erro ao gerar PDF do faturamento! Contate o suporte. {e}", "error"))
        return redirect(url_for("listagem_faturamentos_cargas_a_pagar"))
    
@app.route('/financeiro/cargas-a-pagar/exportar-imagem/<int:faturamento_id>', methods=['POST'])
@login_required
@requires_roles
def exportar_faturamento_imagem(faturamento_id):
    """Gera imagem JPG do faturamento com opções de ocultação"""
    try:
        # Buscar faturamento
        faturamento = FaturamentoModel.query.get_or_404(faturamento_id)
        
        # Obter opções de ocultação do formulário
        opcoes = {
            'ocultar_fornecedores': request.form.get('ocultar_fornecedores') == 'true',
            'ocultar_transportadoras': request.form.get('ocultar_transportadoras') == 'true',
            'ocultar_cliente': request.form.get('ocultar_cliente') == 'true',
            'ocultar_receitas_avulsas': request.form.get('ocultar_receitas_avulsas') == 'true',
            'ocultar_despesas_avulsas': request.form.get('ocultar_despesas_avulsas') == 'true'
        }
        
        dados_processados = processar_dados_faturamento(faturamento)
                
        # Dados adicionais para o template
        dados_extras = {
            'opcoes': opcoes,
            'logo_path': obter_url_absoluta_de_imagem("logo.png"),
            'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'usuario_geracao': current_user.nome if hasattr(current_user, 'nome') else 'Sistema'
        }
        
        # Combinar todos os dados
        dados_template = {**dados_processados, **dados_extras}
        
        # USAR O MESMO TEMPLATE DO PDF
        html = render_template('financeiro/faturamentos/relatorio_faturamento/relatorio_faturamento_imagem.html', **dados_template)
        
        # Gerar nome do arquivo
        codigo_fat = faturamento.codigo_faturamento
        nome_arquivo = f"Faturamento_{codigo_fat}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Gerar IMAGEM ao invés de PDF
        return ManipulacaoArquivos.gerar_imagem_from_html(html, nome_arquivo, largura=1200)
        
    except Exception as e:
        flash((f"Erro ao gerar imagem do faturamento! Contate o suporte. {e}", "error"))
        return redirect(url_for("listagem_faturamentos_cargas_a_pagar"))
    

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
            'valor_fornecedor': faturamento.valor_fornecedor or 0,
            'valor_transportadora': faturamento.valor_transportadora or 0,
            'valor_extrator': faturamento.valor_extrator or 0,
            'valor_comissionado': getattr(faturamento, 'valor_comissionado', 0) or 0,
            'situacao': faturamento.situacao.situacao if faturamento.situacao else 'Pendente'
        }
    }
    
    # Processar detalhes JSON se existir
    detalhes = {}
    if faturamento.detalhes_json:
        try:
            # Verificar se detalhes_json já é um dicionário ou string JSON
            if isinstance(faturamento.detalhes_json, dict):
                detalhes = faturamento.detalhes_json
            else:
                detalhes = json.loads(faturamento.detalhes_json)
        except (json.JSONDecodeError, TypeError):
            detalhes = {}
    
    # Calcular período quinzenal baseado nas datas de entrega dos registros
    todas_datas = []
    
    # Coletar todas as datas de entrega dos registros
    for categoria in ['fornecedores', 'transportadoras', 'extratores', 'comissionados']:
        registros = detalhes.get(categoria, [])
        for registro in registros:
            data_entrega = registro.get('data_entrega')
            if data_entrega and data_entrega != '-':
                todas_datas.append(data_entrega)
    
    # Determinar o período quinzenal - a função faz toda a mágica!
    periodo_quinzenal = DataHora.obter_periodo_quinzenal(todas_datas) if todas_datas else None
    
    # Adicionar período quinzenal aos dados do faturamento
    dados['faturamento']['periodo_quinzenal'] = periodo_quinzenal
    
    # Usar método integrado que retorna AMBAS as estruturas
    todos_dados_agrupados = FaturamentoModel.agrupar_dados_por_cliente_produto(detalhes)
    
    # Estrutura ORIGINAL: extrair agrupamentos por categoria
    dados['fornecedores'] = todos_dados_agrupados['fornecedores_agrupados']
    dados['transportadoras'] = todos_dados_agrupados['transportadoras_agrupadas']
    dados['extratores'] = todos_dados_agrupados['extratores_agrupados']
    dados['comissionados'] = todos_dados_agrupados['comissionados_agrupados']
    dados['cargas_a_receber'] = todos_dados_agrupados['cargas_a_receber_agrupadas']
    
    # NOVA estrutura hierárquica: agrupar TODOS os dados por cliente e produto
    dados['clientes'] = todos_dados_agrupados['dados_hierarquicos']
    dados['total_clientes'] = len(todos_dados_agrupados['dados_hierarquicos'])
    
    # Usar os totais calculados pela função agrupar_dados_por_cliente_produto
    # Os totais estão dentro de dados_hierarquicos -> produtos -> totais
    totais_globais = {
        'fornecedores': 0.0,
        'transportadoras': 0.0,
        'extratores': 0.0,
        'comissionados': 0.0,
        'cargas_a_receber': 0.0,
        'total_geral': 0.0
    }
    
    # Somar todos os totais de todos os produtos de todos os clientes
    for cliente in todos_dados_agrupados.get('dados_hierarquicos', []):
        for produto in cliente.get('produtos', []):
            totais_produto = produto.get('totais', {})
            totais_globais['fornecedores'] += totais_produto.get('fornecedores', 0.0)
            totais_globais['transportadoras'] += totais_produto.get('transportadoras', 0.0)
            totais_globais['extratores'] += totais_produto.get('extratores', 0.0)
            totais_globais['comissionados'] += totais_produto.get('comissionados', 0.0)
            totais_globais['cargas_a_receber'] += totais_produto.get('cargas_a_receber', 0.0)
            totais_globais['total_geral'] += totais_produto.get('total_geral', 0.0)
    
    dados['totais'] = totais_globais
    # Calcular totais gerais para compatibilidade
    dados['total_fornecedores'] = len(detalhes.get('fornecedores', []))
    dados['total_transportadoras'] = len(detalhes.get('transportadoras', []))
    dados['total_extratores'] = len(detalhes.get('extratores', []))
    dados['total_comissionados'] = len(detalhes.get('comissionados', []))
    dados['total_cargas_a_receber'] = len(detalhes.get('cargas_a_receber', []))
    # Processar receitas avulsas (via relacionamento direto)
    receitas_avulsas = []
    if faturamento.lancamento_avulso_id:
        receitas_query = LancamentoAvulsoModel.query.filter_by(
            faturamento_id=faturamento.id,
            tipo_movimentacao=1,  # Receitas
            ativo=True
        ).all()
        
        for receita in receitas_query:
            receitas_avulsas.append({
                'descricao': receita.descricao,
                'valor': receita.valor_movimentacao_100 / 100 if receita.valor_movimentacao_100 else 0,
                'conta_bancaria': receita.conta_bancaria.conta_descritiva if receita.conta_bancaria else 'Não informado',
                'data_lancamento': receita.data_lancamento.strftime('%d/%m/%Y') if receita.data_lancamento else 'Não informado'
            })
    
    dados['receitas_avulsas'] = receitas_avulsas
    dados['total_receitas_avulsas'] = len(receitas_avulsas)

    # Processar despesas avulsas (via relacionamento direto)
    despesas_avulsas = []
    if faturamento.lancamento_avulso_id:
        despesas_query = LancamentoAvulsoModel.query.filter_by(
            faturamento_id=faturamento.id,
            tipo_movimentacao=2,  # Despesas
            ativo=True
        ).all()
        
        for despesa in despesas_query:
            despesas_avulsas.append({
                'descricao': despesa.descricao,
                'valor': despesa.valor_movimentacao_100 / 100 if despesa.valor_movimentacao_100 else 0,
                'conta_bancaria': despesa.conta_bancaria.conta_descritiva if despesa.conta_bancaria else 'Não informado',
                'data_lancamento': despesa.data_lancamento.strftime('%d/%m/%Y') if despesa.data_lancamento else 'Não informado'
            })
    
    dados['despesas_avulsas'] = despesas_avulsas
    dados['total_despesas_avulsas'] = len(despesas_avulsas)

    creditos_utilizados = []
    
    # Processar créditos de fornecedor
    credito_fornecedor = detalhes.get("credito_fornecedor", [])
    if credito_fornecedor:
        for credito in credito_fornecedor:
            fornecedor_id = credito.get("entidade_id") or credito.get("fornecedor_id")
            valor_utilizado = credito.get("valor", 0)
            valor_original = credito.get("valor_original", valor_utilizado)
            
            # Calcular saldo restante deste crédito específico
            valor_restante = valor_original - valor_utilizado
            
            # Buscar código do faturamento origem
            extrato_credito_id = credito.get("credito_id")
            codigo_faturamento_origem = FaturamentoModel.buscar_faturamento_origem_por_extrato(extrato_credito_id, 'fornecedor')
            
            creditos_utilizados.append({
                "categoria": "Fornecedor",
                "identificacao": credito.get("entidade_nome") or credito.get("fornecedor_identificacao", credito.get("descricao", "N/A")),
                "descricao": credito.get("descricao", "Crédito de Fornecedor"),
                "credito_id": credito.get("credito_id"),
                "valor_original": valor_original,
                "valor_utilizado": valor_utilizado,
                "valor_restante": valor_restante,
                "uso_parcial": credito.get("uso_parcial", False),
                "codigo_faturamento": codigo_faturamento_origem
            })
    
    # Processar créditos de transportadora
    credito_transportadora = detalhes.get("credito_transportadora", [])
    if credito_transportadora:
        for credito in credito_transportadora:
            
            transportadora_id = credito.get("entidade_id") or credito.get("transportadora_id")
            valor_utilizado = credito.get("valor", 0)
            valor_original = credito.get("valor_original", valor_utilizado)
            
            # Calcular saldo restante deste crédito específico
            valor_restante = valor_original - valor_utilizado
            # Buscar código do faturamento origem
            extrato_credito_id = credito.get("credito_id")
            codigo_faturamento_origem = FaturamentoModel.buscar_faturamento_origem_por_extrato(extrato_credito_id, 'transportadora')
            
            creditos_utilizados.append({
                "categoria": "Frete",
                "identificacao": credito.get("entidade_nome") or credito.get("transportadora_identificacao", credito.get("descricao", "N/A")),
                "descricao": credito.get("descricao", "Crédito de Transportadora"),
                "credito_id": credito.get("credito_id"),
                "valor_original": valor_original,
                "valor_utilizado": valor_utilizado,
                "valor_restante": valor_restante,
                "uso_parcial": credito.get("uso_parcial", False),
                "codigo_faturamento": codigo_faturamento_origem
            })
    
    # Processar créditos de extrator
    credito_extrator = detalhes.get("credito_extrator", [])
    if credito_extrator:
        for credito in credito_extrator:
            extrator_id = credito.get("entidade_id") or credito.get("extrator_id")
            valor_utilizado = credito.get("valor", 0)
            valor_original = credito.get("valor_original", valor_utilizado)
            
            # Calcular saldo restante deste crédito específico
            valor_restante = valor_original - valor_utilizado
            
            # Buscar código do faturamento origem
            extrato_credito_id = credito.get("credito_id")
            codigo_faturamento_origem = FaturamentoModel.buscar_faturamento_origem_por_extrato(extrato_credito_id, 'extrator')
            
            creditos_utilizados.append({
                "categoria": "Extrator",
                "identificacao": credito.get("entidade_nome") or credito.get("extrator_identificacao", credito.get("descricao", "N/A")),
                "descricao": credito.get("descricao", "Crédito de Extrator"),
                "credito_id": credito.get("credito_id"),
                "valor_original": valor_original,
                "valor_utilizado": valor_utilizado,
                "valor_restante": valor_restante,
                "uso_parcial": credito.get("uso_parcial", False),
                "codigo_faturamento": codigo_faturamento_origem
            })

    dados['creditos_utilizados'] = creditos_utilizados
    dados['faturamento']['utilizou_credito'] = faturamento.utilizou_credito

    # Buscar créditos em aberto das entidades vinculadas ao faturamento
    creditos_em_aberto = FaturamentoModel._buscar_creditos_em_aberto(detalhes)
    dados['creditos_em_aberto'] = creditos_em_aberto

    return dados