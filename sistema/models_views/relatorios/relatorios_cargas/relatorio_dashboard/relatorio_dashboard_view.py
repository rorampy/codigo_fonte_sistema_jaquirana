from datetime import datetime, timedelta, date
from sistema import app, requires_roles, db, formatar_data_para_brl
from flask import request, redirect, url_for, flash
from flask_login import login_required, current_user
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema._utilitarios import *
from sistema.models_views.configuracoes_gerais.situacao_pagamento.situacao_pagamento_model import SituacaoPagamentoModel
from sistema.models_views.controle_carga.solicitacao_nf.carga_model import CargaModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema.models_views.gerenciar.veiculo.veiculo_model import VeiculoModel
from sistema.models_views.gerenciar.motorista.motorista_model import MotoristaModel
from sistema.models_views.gerenciar.floresta.floresta_model import FlorestaModel
from sistema.models_views.faturamento.cargas_a_faturar.fornecedor.fornecedor_a_pagar_model import FornecedorPagarModel
from sistema.models_views.faturamento.cargas_a_faturar.extrator.extrator_a_pagar_model import ExtratorPagarModel
from sistema.models_views.faturamento.cargas_a_faturar.comissionado.comissionado_a_pagar_model import ComissionadoPagarModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_cadastro_model import FornecedorCadastroModel
from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.faturamento.cargas_a_faturar.transportadora.frete_a_pagar_model import FretePagarModel
from sistema.models_views.gerenciar.comissionado.comissionado_model import ComissionadoModel
from sistema.models_views.gerenciar.extrator.extrator_model import ExtratorModel
from sistema.models_views.controle_carga.nf_complementar.nf_entrada_model import NfEntradaModel
from sqlalchemy import case, desc, or_


@app.context_processor
def inject_relatorio_excel():
    """Context processor global para variáveis usadas em toda a aplicação"""
   
    dados_corretos = {}
    situacoes_pagamento = []
    semanas_disponiveis = []
    
    try:
        if request and hasattr(request, 'form'):
            dados_corretos = request.form.to_dict()
            
        if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            situacoes_pagamento = SituacaoPagamentoModel.listar_status()
            semanas_disponiveis = UtilitariosSemana.obter_semanas_do_mes_atual()
            
    except Exception as e:
        pass
        
    return {
        "dados_corretos": dados_corretos,
        "situacoes_pagamento": situacoes_pagamento,
        "statusPagamentos": situacoes_pagamento,
        "semanas_disponiveis": semanas_disponiveis
    }


def filtro_excel_dashboard(
    data_inicio=None,
    data_fim=None,
    cliente=None,
    numero_nf=None,
    placa=None,
    motorista=None,
    transportadora=None,
    fornecedor=None,
    produto=None,
    bitola=None,
    statusPagamentoCarga=None
):
    """
    Filtra e retorna registros para compor o relatório Excel do dashboard.
    
    Args:
        data_inicio (date, optional): Data inicial do filtro
        data_fim (date, optional): Data final do filtro
        cliente (str, optional): Nome do cliente
        numero_nf (str, optional): Número da nota fiscal
        placa (str, optional): Placa do veículo
        motorista (str, optional): Nome do motorista
        transportadora (str, optional): Nome da transportadora
        fornecedor (str, optional): Nome do fornecedor ou floresta
        produto (str, optional): Nome do produto
        bitola (str, optional): Bitola
        statusPagamentoCarga (int, optional): Status de pagamento da carga
    
    Returns:
        list: Lista de dicionários com registros filtrados e unificados
    """
    if not data_inicio or not data_fim:
        data_inicio = date.today() - timedelta(days=30)
        data_fim = date.today()

    query = (
        db.session.query(
            RegistroOperacionalModel,
            FornecedorCadastroModel,
            FlorestaModel,
            FornecedorPagarModel,
            FretePagarModel,
            ExtratorPagarModel,
            ComissionadoPagarModel,
            ClienteModel,
            ProdutoModel,
            BitolaModel,
            VeiculoModel,
            MotoristaModel,
            NfEntradaModel,
        )
        .join(CargaModel, RegistroOperacionalModel.solicitacao)
        .join(ClienteModel, CargaModel.cliente)
        .join(VeiculoModel, CargaModel.veiculo)
        .join(MotoristaModel, CargaModel.motorista)
        .join(ProdutoModel, CargaModel.produto)
        .join(BitolaModel, CargaModel.bitola)
        .outerjoin(FornecedorCadastroModel, CargaModel.fornecedor)
        .outerjoin(FlorestaModel, CargaModel.floresta)
        .outerjoin(FornecedorPagarModel, FornecedorPagarModel.solicitacao_id == CargaModel.id)
        .outerjoin(FretePagarModel, FretePagarModel.solicitacao_id == CargaModel.id)
        .outerjoin(ExtratorPagarModel, ExtratorPagarModel.solicitacao_id == CargaModel.id)
        .outerjoin(ComissionadoPagarModel, ComissionadoPagarModel.solicitacao_id == CargaModel.id)
        .outerjoin(NfEntradaModel, NfEntradaModel.registro_id == RegistroOperacionalModel.id)
        .filter(
            RegistroOperacionalModel.deletado.is_(False),
            RegistroOperacionalModel.ativo.is_(True),
        )
        .order_by(
            desc(RegistroOperacionalModel.data_entrega_ticket),
        )
    )

    if data_inicio and data_fim:
        query = query.filter(
            RegistroOperacionalModel.data_entrega_ticket.isnot(None),
            RegistroOperacionalModel.data_entrega_ticket.between(data_inicio, data_fim),
        )
    elif data_inicio:
        query = query.filter(
            RegistroOperacionalModel.data_entrega_ticket.isnot(None),
            RegistroOperacionalModel.data_entrega_ticket >= data_inicio,
        )
    elif data_fim:
        query = query.filter(
            RegistroOperacionalModel.data_entrega_ticket.isnot(None),
            RegistroOperacionalModel.data_entrega_ticket <= data_fim,
        )

    if cliente:
        query = query.filter(ClienteModel.identificacao.ilike(f"%{cliente}%"))
        
    if numero_nf:
        query = query.filter(or_(
            RegistroOperacionalModel.numero_nota_fiscal.ilike(f"%{numero_nf}%"),
            RegistroOperacionalModel.numero_nota_fiscal_excessao.ilike(f"%{numero_nf}%"),
            RegistroOperacionalModel.numero_nota_fiscal_estorno.ilike(f"%{numero_nf}%"),
        ))
        
    if produto:
        query = query.filter(ProdutoModel.nome.ilike(f"%{produto}%"))
        
    if bitola:
        query = query.filter(BitolaModel.bitola.ilike(f"%{bitola}%"))
        
    if motorista:
        query = query.filter(MotoristaModel.nome_completo.ilike(f"%{motorista}%"))
        
    if placa:
        query = query.filter(VeiculoModel.placa_veiculo.ilike(f"%{placa}%"))
        
    if fornecedor:
        query = query.filter(or_(
            CargaModel.fornecedor.has(FornecedorCadastroModel.identificacao.ilike(f"%{fornecedor}%")),
            CargaModel.floresta.has(FlorestaModel.identificacao.ilike(f"%{fornecedor}%")),
        ))
    
    if statusPagamentoCarga and statusPagamentoCarga != "":
        query = query.join(SituacaoPagamentoModel, RegistroOperacionalModel.situacao)\
                    .filter(SituacaoPagamentoModel.id == statusPagamentoCarga)

    registros = []
    registros_vistos = set()

    for (registro, fornecedor_obj, floresta_obj, pag_fornecedor, pag_frete, 
         pag_extrator, pag_comissionado, cliente_obj, produto_obj, bitola_obj, veiculo_obj, 
         motorista_obj, nf_entrada) in query.all():
        
        chave_unica = (registro.id, motorista_obj.id, veiculo_obj.id)
        if chave_unica in registros_vistos:
            continue
        registros_vistos.add(chave_unica)

        carga = registro.solicitacao
        
        if transportadora and transportadora.lower() not in carga.transportadora_exibicao.lower():
            continue

        origem_nome = (fornecedor_obj.identificacao if fornecedor_obj  else floresta_obj.identificacao if floresta_obj else "Indefinido")
        
        peso_liquido = registro.peso_liquido_ticket or 0
        custo_fornecedor = pag_fornecedor.valor_total_a_pagar_100 if pag_fornecedor else 0
        custo_frete = pag_frete.valor_total_a_pagar_100 if pag_frete else 0
        custo_extracao = pag_extrator.valor_total_a_pagar_100 if pag_extrator else 0
        
        total_custos = custo_fornecedor + custo_frete + custo_extracao
        total_receita = registro.valor_total_nota_100 or 0
        margem = total_receita - total_custos

        registro_formatado = {
            "registro_operacional": registro,
            "solicitacao": registro.solicitacao,
            "fat_fornecedor": pag_fornecedor,
            "fat_frete": pag_frete,
            "fat_extrator": pag_extrator,
            "fat_comissionado": pag_comissionado,
            "nf_entrada": nf_entrada,
        }
        
        registros.append(registro_formatado)

    return registros


@app.route("/relatorios/excel-dashboard", methods=["GET", "POST"])
@login_required
@requires_roles
def relatorio_excel_dashboard():
    try:
        if request.method == "POST":
            tipo_filtro = request.form.get("tipo_filtro", "semanal")
            semana_selecionada = request.form.get("semanaSelecionada")
            data_inicio_form = request.form.get("dataInicio")
            data_fim_form = request.form.get("dataFim")
            placa = request.form.get("placaCarga")
            motorista = request.form.get("motoristaCarga")
            transportadora = request.form.get("transportadoraCarga")
            fornecedor = request.form.get("fornecedorCarga")
            cliente = request.form.get("clienteCarga")
            numero_nf = request.form.get("numeroNF")
            produto = request.form.get("produtoCarga")
            bitola = request.form.get("bitolaCarga")
            statusPagamentoCarga = request.form.get("statusPagamentoCarga")
            
            if tipo_filtro == "data" and data_inicio_form and data_fim_form:
                data_inicio = datetime.strptime(data_inicio_form, "%Y-%m-%d").date()
                data_fim = datetime.strptime(data_fim_form, "%Y-%m-%d").date()
            else:
                data_inicio, data_fim = UtilitariosSemana.processar_semana_selecionada(semana_selecionada)
            
            registros = filtro_excel_dashboard(
                data_inicio=data_inicio,
                data_fim=data_fim,
                placa=placa,
                motorista=motorista,
                transportadora=transportadora,
                fornecedor=fornecedor,
                cliente=cliente,
                numero_nf=numero_nf,
                produto=produto,
                bitola=bitola,
                statusPagamentoCarga=statusPagamentoCarga
            )
            
            dados_excel = []

            for item in registros:
                registro = item["registro_operacional"]
                solicitacao = item["solicitacao"]
                fat_fornecedor = item["fat_fornecedor"]
                fat_frete = item["fat_frete"]
                fat_extrator = item["fat_extrator"]
                fat_comissionado = item["fat_comissionado"]
                nf_entrada = item["nf_entrada"]
                
                peso_ticket = registro.peso_liquido_ticket or 0
                peso_nf = registro.peso_ton_nf or 0
                valor_total_nf = (registro.valor_total_nota_100 or 0) / 100
                valor_unitario_nf = (registro.preco_un_nf or 0) / 100
                
                valor_fornecedor = (fat_fornecedor.valor_total_a_pagar_100 or 0) / 100 if fat_fornecedor else 0
                valor_frete = (fat_frete.valor_total_a_pagar_100 or 0) / 100 if fat_frete else 0
                valor_extrator = (fat_extrator.valor_total_a_pagar_100 or 0) / 100 if fat_extrator else 0
                valor_comissionado = (fat_comissionado.valor_total_a_pagar_100 or 0) / 100 if fat_comissionado else 0
                
                valor_ton_fornecedor = valor_fornecedor / peso_ticket if peso_ticket > 0 else 0
                valor_ton_frete = valor_frete / peso_ticket if peso_ticket > 0 else 0
                valor_ton_extracao = valor_extrator / peso_ticket if peso_ticket > 0 else 0
                valor_ton_comissao = valor_comissionado / peso_ticket if peso_ticket > 0 else 0
                
                peso_complementar = peso_ticket - peso_nf
                complementar_perc = (peso_complementar / peso_ticket * 100) if peso_ticket > 0 else 0
                
                tempo_entrega_dias = 0
                if registro.data_entrega_ticket and registro.destinatario_data_emissao:
                    tempo_entrega_dias = (registro.data_entrega_ticket - registro.destinatario_data_emissao).days
                
                classe = "Sem classificação"
                if valor_ton_fornecedor > 0 and valor_ton_frete > 0:
                    classe = "Fornecedor"
                elif valor_ton_fornecedor == 0 and valor_ton_frete > 0:
                    classe = "Floresta"
                elif valor_ton_frete == 0 and valor_ton_fornecedor > 0:
                    classe = "Madeira Posta"
                elif valor_ton_fornecedor == 0 and valor_ton_frete == 0:
                    classe = "Cargas sem preço"
                
                classe_inco = "N/A"
                if classe in ["Fornecedor", "Floresta"]:
                    classe_inco = "CFR"
                elif classe == "Madeira Posta":
                    classe_inco = "FOB"
                
                custo_total_ton = valor_ton_fornecedor + valor_ton_frete + valor_ton_extracao + valor_ton_comissao
                custo_total = valor_fornecedor + valor_frete + valor_extrator + valor_comissionado
                
                receita_venda = valor_unitario_nf * peso_ticket
                
                servico_ton = 0
                cliente_nome = solicitacao.cliente.identificacao if solicitacao.cliente else ""
                produto_nome = solicitacao.produto.nome if solicitacao.produto else ""
                bitola_nome = solicitacao.bitola.bitola if solicitacao.bitola else ""
                
                if (cliente_nome == "Fibraplac Paineis de Madeira LTDA" and 
                    produto_nome == "Pinus" and bitola_nome == "Torete"):
                    servico_ton = 40
                elif produto_nome == "Eucalipto" and bitola_nome == "Torete":
                    servico_ton = 10
                elif produto_nome == "Biomassa" and bitola_nome == "Cavaco":
                    servico_ton = 5
                
                receita_servico = servico_ton * peso_ticket
                receita_total_bruta = receita_venda + receita_servico
                receita_bruta_ton = receita_total_bruta / peso_ticket if peso_ticket > 0 else 0
                
                margem_bruta = receita_total_bruta - custo_total
                margem_bruta_ton = receita_bruta_ton - custo_total_ton
                
                icms = receita_venda * 0.12
                pis = receita_venda * 0.0165
                cofins = receita_venda * 0.076
                iss = receita_servico * 0.03
                
                funrural_senar = ""
                funrural = 0
                
                total_impostos = icms + pis + cofins + iss + funrural
                receita_liquida = receita_total_bruta - total_impostos
                margem_liquida = receita_liquida - custo_total
                margem_liquida_ton = margem_liquida / peso_ticket if peso_ticket > 0 else 0
                participacao_impostos = (total_impostos / receita_total_bruta * 100) if receita_total_bruta > 0 else 0
                impostos_ton = total_impostos / peso_ticket if peso_ticket > 0 else 0
                
                status_entrada = "Pendente"
                data_entrada = ""
                peso_entrada = 0
                valor_nf_entrada = ""
                descricao_produto_entrada = ""
                saldo_estoque = 0
                
                if nf_entrada:
                    if nf_entrada.arquivo_nf_entrada_id and nf_entrada.arquivo_contra_nota_id:
                        status_entrada = "Lançado"
                    elif nf_entrada.arquivo_nf_entrada_id:
                        status_entrada = "NF Anexada"
                    else:
                        status_entrada = "Criado"
                    
                    if hasattr(nf_entrada, 'data_cadastro') and nf_entrada.data_cadastro:
                        data_entrada = formatar_data_para_brl(nf_entrada.data_cadastro)
                    
                    if nf_entrada.peso_contra_nota:
                        peso_entrada = nf_entrada.peso_contra_nota
                        
                    saldo_estoque = peso_entrada - peso_ticket
                    
                    valor_nf_entrada = ""
                    descricao_produto_entrada = ""

                dados_excel.append(
                    {
                        "Empresa Emissora": solicitacao.empresa_emissora.identificacao if solicitacao.empresa_emissora else "",
                        "Numero NF": registro.numero_nota_fiscal or "",
                        "Data emissão": formatar_data_para_brl(registro.destinatario_data_emissao) if registro.destinatario_data_emissao else "",
                        "Cliente": solicitacao.cliente.identificacao if solicitacao.cliente else "",
                        "Placa": solicitacao.veiculo.placa_veiculo if solicitacao.veiculo else "",
                        "Motorista": solicitacao.motorista.nome_completo if solicitacao.motorista else "",
                        "Transportadora": solicitacao.transportadora_exibicao.identificacao if solicitacao.transportadora_exibicao else "",
                        "Descrição Produto NF": "",
                        "Produto": solicitacao.produto.nome if solicitacao.produto else "",
                        "Bitola": solicitacao.bitola.bitola if solicitacao.bitola else "",
                        "Valor Total NF": ValoresMonetarios.converter_float_brl_positivo(valor_total_nf),
                        "Status Faturamento a Receber": registro.situacao.situacao if registro.situacao else "Pendente",
                        "Valor unitário NF": ValoresMonetarios.converter_float_brl_positivo(valor_unitario_nf),
                        "Peso NF": f"{peso_nf:,.2f}".replace(".", ","),
                        "Status Ticket": "Fechado" if registro.peso_liquido_ticket else "Pendente",
                        "Fornecedor": (solicitacao.fornecedor.identificacao if solicitacao.fornecedor 
                                     else solicitacao.floresta.identificacao if solicitacao.floresta else ""),
                        "Classe_Fornecedor": "Floresta" if solicitacao.fornecedor.classe_fornecedor == True else "Terceiro",
                        "Data Entrega": formatar_data_para_brl(registro.data_entrega_ticket) if registro.data_entrega_ticket else "",
                        "Peso Ticket": f"{peso_ticket:,.2f}".replace(".", ","),
                        "Tempo Entrega (dias)": str(tempo_entrega_dias),
                        "Peso Complementar": f"{peso_complementar:,.2f}".replace(".", ","),
                        "Complementar (%)": f"{complementar_perc:,.1f}%".replace(".", ","),
                        "Valor Ton": ValoresMonetarios.converter_float_brl_positivo(valor_ton_fornecedor),
                        "A pagar Fornecedor": ValoresMonetarios.converter_float_brl_positivo(valor_fornecedor),
                        "Status Faturamento Fornecedor": fat_fornecedor.situacao.situacao if fat_fornecedor and fat_fornecedor.situacao else "Pendente",
                        "Valor Ton Frete": ValoresMonetarios.converter_float_brl_positivo(valor_ton_frete),
                        "Validador": "Rota cadastrada" if valor_ton_frete > 0 else "Carga posta",
                        "A pagar Transportadora": ValoresMonetarios.converter_float_brl_positivo(valor_frete),
                        "Status Faturamento Frete": fat_frete.situacao.situacao if fat_frete and fat_frete.situacao else "Pendente",
                        "Valor Ton Extração": ValoresMonetarios.converter_float_brl_positivo(valor_ton_extracao),
                        "A pagar Extrator": ValoresMonetarios.converter_float_brl_positivo(valor_extrator),
                        "Status Faturamento Extrator": fat_extrator.situacao.situacao if fat_extrator and fat_extrator.situacao else "Pendente",
                        "Valor Ton Comissão": ValoresMonetarios.converter_float_brl_positivo(valor_ton_comissao),
                        "A pagar Comissão": ValoresMonetarios.converter_float_brl_positivo(valor_comissionado),
                        "Status Faturamento Comissão": fat_comissionado.situacao.situacao if fat_comissionado and fat_comissionado.situacao else "Pendente",
                        "Classe_Carga": classe,
                        "Classe_Inco": classe_inco,
                        "Custo Total Ton": ValoresMonetarios.converter_float_brl_positivo(custo_total_ton),
                        "Custo Total": ValoresMonetarios.converter_float_brl_positivo(custo_total),
                        "Receita_venda": ValoresMonetarios.converter_float_brl_positivo(receita_venda),
                        "Serviço_Ton": ValoresMonetarios.converter_float_brl_positivo(servico_ton),
                        "Receita_serviço": ValoresMonetarios.converter_float_brl_positivo(receita_servico),
                        "Receita Total Bruta": ValoresMonetarios.converter_float_brl_positivo(receita_total_bruta),
                        "Receita Bruta_Ton": ValoresMonetarios.converter_float_brl_positivo(receita_bruta_ton),
                        "Margem Bruta": ValoresMonetarios.converter_float_brl_positivo(margem_bruta),
                        "Margem Bruta Ton": ValoresMonetarios.converter_float_brl_positivo(margem_bruta_ton),
                        "ICMS": ValoresMonetarios.converter_float_brl_positivo(icms),
                        "PIS": ValoresMonetarios.converter_float_brl_positivo(pis),
                        "COFINS": ValoresMonetarios.converter_float_brl_positivo(cofins),
                        "ISS": ValoresMonetarios.converter_float_brl_positivo(iss),
                        "Funrural/Senar": funrural_senar,
                        "Funrural": ValoresMonetarios.converter_float_brl_positivo(funrural),
                        "Receita Líquida": ValoresMonetarios.converter_float_brl_positivo(receita_liquida),
                        "Margem Líquida": ValoresMonetarios.converter_float_brl_positivo(margem_liquida),
                        "Margem Liquida Ton": ValoresMonetarios.converter_float_brl_positivo(margem_liquida_ton),
                        "Total Impostos": ValoresMonetarios.converter_float_brl_positivo(total_impostos),
                        "Participação Impostos": f"{participacao_impostos:,.1f}%".replace(".", ","),
                        "Controle Entrada": "Sim" if (solicitacao.fornecedor and solicitacao.fornecedor.controle_entrada) else "Não",
                        "Impostos ton": ValoresMonetarios.converter_float_brl_positivo(impostos_ton),
                        "Status Entrada": status_entrada,
                        "Data Entrada": data_entrada,
                        "Peso Entrada": f"{peso_entrada:,.2f}".replace(".", ",") if peso_entrada > 0 else "",
                        "Valor NF Entrada": valor_nf_entrada,
                        "Descrição Produto": descricao_produto_entrada,
                        "Saldo Estoque": f"{saldo_estoque:,.2f}".replace(".", ",") if peso_entrada > 0 else "",
                    }
                )

            data_hoje = datetime.now().strftime("%Y-%m-%d")
            nome_arquivo_saida = f"relatorio-dashboard-{data_hoje}"
            resposta = ManipulacaoArquivos.exportar_excel(dados_excel, nome_arquivo_saida)
            return resposta
        else:
            return redirect(url_for("principal"))
        
    except Exception as e:
        flash(("Erro ao gerar o relatório Excel para o Dashboard.", "error"))
        return redirect(url_for("principal"))
