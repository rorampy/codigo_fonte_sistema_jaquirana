from sistema import app, render_template, url_for, requires_roles, flash, redirect, request, db
from flask import jsonify
from sistema.models_views.financeiro.operacional.faturamento_model.faturamento_model import FaturamentoModel
from sistema.models_views.financeiro.operacional.categorizar_fatura.categorizacao_model import AgendamentoPagamentoModel
from sistema.models_views.financeiro.operacional.categorizar_fatura.categorizacao_anexo_model import AgendamentoAnexoPagamentoModel
from sistema.models_views.financeiro.operacional.categorizar_fatura.parcela_categorizacao.parcela_categorizacao_model import ParcelaCategorizacaoModel
from sistema.models_views.gerenciar.pessoa_financeiro.pessoa_financeiro_model import PessoaFinanceiroModel
from sistema.models_views.configuracoes_gerais.situacao_pagamento.situacao_pagamento_model import SituacaoPagamentoModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import PlanoContaModel
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_view import (inicializar_categorias_padrao, obter_subcategorias_recursivo, obter_estrutura_com_folhas)
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_view import (inicializar_categorias_padrao_categorizacao_fiscal, obter_subcategorias_recursivo_categorizacao_fiscal)
from sistema.models_views.configuracoes_gerais.centro_custo.centro_custo_model import CentroCustoModel
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_model import CategorizacaoFiscalModel
from sistema.models_views.financeiro.lancamento_avulso.lancamento_avulso_model import LancamentoAvulsoModel
from sistema.models_views.configuracoes_gerais.conta_bancaria.conta_bancaria_model import ContaBancariaModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema._utilitarios import *
from flask_login import login_required, current_user
from datetime import datetime, date
import json

@app.route("/faturamento/categorizar_fatura/<int:id>", methods=["GET", "POST"])
@app.route("/faturamento/categorizar_fatura/<int:id>/<tipo>", methods=["GET", "POST"])
@login_required
@requires_roles
def categorizar_fatura(id, tipo='despesa'):
    try:
        if tipo == 'receita_avulsa' or tipo == 'despesa_avulsa':
            # Buscar lançamento avulso diretamente
            lancamento_avulso = LancamentoAvulsoModel.obter_lancamento_por_id(id)
            if not lancamento_avulso:
                flash((f'Lançamento avulso não encontrado!', 'error'))
                return redirect(url_for('listagem_despesas_avulsas' if tipo == 'despesa_avulsa' else 'listagem_receitas_avulsas'))
            
            valor_total = lancamento_avulso.valor_movimentacao_100
            objeto_principal = lancamento_avulso
            faturamento = None  # Lançamentos avulsos NÃO TÊM faturamento
        else:
            # Buscar faturamento normal
            faturamento = FaturamentoModel.obter_faturamento_por_id(id)
            if not faturamento:
                flash((f'Faturamento não encontrado!', 'error'))
                return redirect(url_for('listagem_faturamentos_cargas_a_pagar'))
            valor_total = faturamento.valor_total
            objeto_principal = faturamento
        # Determinar o tipo de plano de contas baseado no parâmetro
        tipo_plano_conta = [1] if tipo == 'receita' or tipo == 'receita_avulsa' else [2]  # 1 = Receitas, 2 = Despesas
        
        campos_obrigatorios = {}
        campos_erros = {}
        dados_corretos = {}

        # Carregar dados para os selects
        pessoas_financeiro = PessoaFinanceiroModel.listar_pessoas_ativas()
        # Processar documentos formatados para cada pessoa
        for p in pessoas_financeiro:
            if p.numero_documento and len(p.numero_documento.strip()) > 0:
                p.documento_formatado = ValidaDocs.insere_pontuacao_cnpj(p.numero_documento) if len(p.numero_documento) == 14 else ValidaDocs.insere_pontuacao_cpf(p.numero_documento)
            else:
                p.documento_formatado = "N/A"
        situacoes_pagamento = SituacaoPagamentoModel.listar_status()
        centros_custo = CentroCustoModel.obter_centro_custos_ativos()
        contas_bancarias = ContaBancariaModel.obter_contas_bancarias_ativas()
        
        # Inicializar e carregar plano de contas com o tipo correto (com marcação de folhas)
        estrutura_plano_contas = obter_estrutura_com_folhas(tipo_plano_conta)

        # Inicializar e carregar categorização fiscal
        inicializar_categorias_padrao_categorizacao_fiscal()
        principais_fiscal = CategorizacaoFiscalModel.buscar_filhos(tipo_plano_conta)
        estrutura_fiscal = []
        for cat in principais_fiscal:
            d = cat.to_dict()
            d["children"] = obter_subcategorias_recursivo_categorizacao_fiscal(cat.id)
            estrutura_fiscal.append(d)

        if request.method == "GET":
            return render_template(
                "faturamento/categorizar_fatura/categorizar_fatura.html", 
                faturamento=faturamento,
                objeto_principal=objeto_principal,  # Passar o objeto principal (faturamento ou lançamento)
                pessoas_financeiro=pessoas_financeiro,
                situacoes_pagamento=situacoes_pagamento,
                estrutura_plano_contas=estrutura_plano_contas,
                estrutura_fiscal=estrutura_fiscal,
                centros_custo=centros_custo,
                campos_obrigatorios=campos_obrigatorios,
                campos_erros=campos_erros,
                dados_corretos=dados_corretos,
                contas_bancarias=contas_bancarias,
                tipo_categorização=tipo  # Passar o tipo para o template
            )

        # POST - Processar formulário
        data_vencimento = request.form.get("data_vencimento", "")
        data_competencia = request.form.get("data_competencia", "")
        conta_bancaria_id = request.form.get("conta_bancaria_id", "")
        pessoa_financeiro_id = request.form.get("pessoa_financeiro_id", "")
        descricao = request.form.get("descricao", "")
        referencia = request.form.get("referencia", "")
        categorias_json = request.form.get("categorias_json", "")
        centros_custo_json = request.form.get("centros_custo_json", "")
        valores_detalhados_ativo = request.form.get("valores_detalhados_ativo") == "true"
        parcelamento_ativo = request.form.get("parcelamento_ativo") == "true"
        numero_parcelas = request.form.get("numero_parcelas", "")
        dias_entre_parcelas = request.form.get("dias_entre_parcelas", "30")
        parcelas_json = request.form.get("parcelas_json", "")
        anexos_json = request.form.get("anexos_json", "[]")

        # Preservar dados do formulário
        dados_corretos = {
            'data_vencimento': data_vencimento,
            'data_competencia': data_competencia,
            'conta_bancaria_id': conta_bancaria_id,
            'pessoa_financeiro_id': pessoa_financeiro_id,
            'descricao': descricao,
            'referencia': referencia,
            'categorias_json': categorias_json,
            'centros_custo_json': centros_custo_json,
            'valores_detalhados_ativo': valores_detalhados_ativo,
            'parcelamento_ativo': parcelamento_ativo,
            'numero_parcelas': numero_parcelas,
            'dias_entre_parcelas': dias_entre_parcelas,
            'parcelas_json': parcelas_json,
            'anexos_json': anexos_json
        }

        # Validações obrigatórias
        if not data_vencimento.strip():
            campos_obrigatorios['data_vencimento'] = 'Data de vencimento é obrigatória!'
        
        if not pessoa_financeiro_id.strip():
            campos_obrigatorios['pessoa_financeiro_id'] = 'Beneficiário é obrigatório!'
            
        if not conta_bancaria_id.strip():
            campos_obrigatorios['conta_bancaria_id'] = 'Conta bancária é obrigatória!'
        
        if not categorias_json.strip():
            campos_obrigatorios['categorias_json'] = 'Pelo menos uma categoria é obrigatória!'

        # Validações de formato
        if data_vencimento:
            try:
                data_vencimento_obj = datetime.strptime(data_vencimento, '%Y-%m-%d').date()
            except ValueError:
                campos_erros['data_vencimento'] = 'Data de vencimento inválida!'

        if data_competencia:
            try:
                # Formato MM/AAAA
                datetime.strptime(data_competencia, '%m/%Y')
            except ValueError:
                campos_erros['data_competencia'] = 'Data de competência deve estar no formato MM/AAAA!'

        if pessoa_financeiro_id:
            try:
                pessoa_id = int(pessoa_financeiro_id)
                pessoa = PessoaFinanceiroModel.obter_pessoa_por_id(pessoa_id)
                if not pessoa:
                    campos_erros['pessoa_financeiro_id'] = 'Beneficiário não encontrado!'
            except ValueError:
                campos_erros['pessoa_financeiro_id'] = 'Beneficiário inválido!'

        # Validar categorias JSON
        if categorias_json:
            try:
                categorias = json.loads(categorias_json)
                if not isinstance(categorias, list) or len(categorias) == 0:
                    campos_erros['categorias_json'] = 'Pelo menos uma categoria deve ser informada!'
                else:
                    # Verificar categorias duplicadas
                    categorias_usadas = []
                    for cat in categorias:
                        nome_categoria = cat.get('nome', '')
                        if nome_categoria in categorias_usadas:
                            campos_erros['categorias_json'] = f'A categoria "{nome_categoria}" foi selecionada mais de uma vez!'
                            break
                        if nome_categoria:  # Só adiciona se não estiver vazia
                            categorias_usadas.append(nome_categoria)
                    
                    # Validar total apenas se não há categorias duplicadas
                    if 'categorias_json' not in campos_erros:
                        total_categorias = sum(cat.get('valor', 0) for cat in categorias)
                        if total_categorias != valor_total:
                            campos_erros['categorias_json'] = 'O valor total das categorias deve ser igual ao valor do lançamento!'
            except json.JSONDecodeError:
                campos_erros['categorias_json'] = 'Formato de categorias inválido!'

        # Validar parcelamento
        if parcelamento_ativo:
            if not numero_parcelas.strip():
                campos_obrigatorios['numero_parcelas'] = 'Número de parcelas é obrigatório quando parcelamento está ativo!'
            else:
                try:
                    num_parcelas = int(numero_parcelas)
                    if num_parcelas < 2:
                        campos_erros['numero_parcelas'] = 'Número de parcelas deve ser maior que 1!'
                except ValueError:
                    campos_erros['numero_parcelas'] = 'Número de parcelas inválido!'
            
            # Validar dados das parcelas se parcelamento ativo
            if parcelas_json:
                try:
                    parcelas = json.loads(parcelas_json)
                    if not isinstance(parcelas, list) or len(parcelas) == 0:
                        campos_erros['parcelas_json'] = 'Dados de parcelas são obrigatórios quando parcelamento está ativo!'
                    else:
                        for i, parcela in enumerate(parcelas, 1):
                            if not parcela.get('vencimento'):
                                campos_erros['parcelas_json'] = f'Data de vencimento da parcela {i} é obrigatória!'
                                break
                            if not parcela.get('valor') or parcela.get('valor') <= 0:
                                campos_erros['parcelas_json'] = f'Valor da parcela {i} deve ser maior que zero!'
                                break
                except json.JSONDecodeError:
                    campos_erros['parcelas_json'] = 'Formato de parcelas inválido!'
            else:
                campos_erros['parcelas_json'] = 'Dados de parcelas são obrigatórios quando parcelamento está ativo!'

        # Validar valores detalhados (centro de custo)
        if valores_detalhados_ativo:
            if centros_custo_json:
                try:
                    centros_custo = json.loads(centros_custo_json)
                    if not isinstance(centros_custo, list) or len(centros_custo) == 0:
                        campos_erros['centros_custo_json'] = 'Pelo menos um centro de custo deve ser informado quando valores detalhados está ativo!'
                    else:
                        for i, centro in enumerate(centros_custo, 1):
                            if not centro.get('centro'):
                                campos_erros['centros_custo_json'] = f'Centro de custo {i} deve ser selecionado!'
                                break
                            # Validar se tem valor ou percentual dependendo do tipo
                            if not centro.get('valor') and not centro.get('percentual'):
                                campos_erros['centros_custo_json'] = f'Centro de custo {i} deve ter valor ou percentual informado!'
                                break
                except json.JSONDecodeError:
                    campos_erros['centros_custo_json'] = 'Formato de centros de custo inválido!'
            else:
                campos_erros['centros_custo_json'] = 'Dados de centros de custo são obrigatórios quando valores detalhados está ativo!'

        # Validar categorias - sempre obrigatórias
        if categorias_json:
            try:
                categorias = json.loads(categorias_json)
                if not isinstance(categorias, list) or len(categorias) == 0:
                    campos_erros['categorias_json'] = 'Pelo menos uma categoria deve ser informada!'
                else:
                    categorias_usadas = set()
                    for i, categoria in enumerate(categorias, 1):
                        if not categoria.get('categoria'):
                            campos_erros['categorias_json'] = f'Categoria {i} deve ser selecionada!'
                            break
                        if not categoria.get('valor') or categoria.get('valor') <= 0:
                            campos_erros['categorias_json'] = f'Valor da categoria {i} deve ser maior que zero!'
                            break
                        # Verificar duplicatas
                        categoria_id = categoria.get('categoria')
                        if categoria_id in categorias_usadas:
                            campos_erros['categorias_json'] = f'A categoria não pode ser repetida!'
                            break
                        categorias_usadas.add(categoria_id)
            except json.JSONDecodeError:
                campos_erros['categorias_json'] = 'Formato de categorias inválido!'
        else:
            campos_erros['categorias_json'] = 'Pelo menos uma categoria deve ser informada!'

        # Se há erros, retornar formulário com erros
        if campos_obrigatorios or campos_erros:
            return render_template(
                "faturamento/categorizar_fatura/categorizar_fatura.html", 
                faturamento=faturamento,
                objeto_principal=objeto_principal,
                pessoas_financeiro=pessoas_financeiro,
                situacoes_pagamento=situacoes_pagamento,
                estrutura_plano_contas=estrutura_plano_contas,
                estrutura_fiscal=estrutura_fiscal,
                centros_custo=centros_custo,
                campos_obrigatorios=campos_obrigatorios,
                campos_erros=campos_erros,
                dados_corretos=dados_corretos,
                contas_bancarias=contas_bancarias,
                tipo_categorização=tipo
            )

        # Processar e enriquecer centros de custo com nomes
        centros_custo_processados = centros_custo_json
        if centros_custo_json:
            try:
                centros_custo = json.loads(centros_custo_json)
                centros_custo_enriquecidos = []
                
                for cc in centros_custo:
                    centro_id = cc.get('centro')
                    centro_nome = centro_id
                    
                    # Se for ID numérico, buscar o nome do centro de custo
                    if str(centro_id).isdigit():
                        centro_custo_obj = CentroCustoModel.obter_centro_custo_por_id(int(centro_id))
                        if centro_custo_obj:
                            centro_nome = centro_custo_obj.nome
                    
                    # Manter estrutura original mas com nome enriquecido
                    centro_enriquecido = {
                        'centro': centro_id,  # Manter ID original
                        'centro_nome': centro_nome,  # Adicionar nome
                        'percentual': cc.get('percentual', ''),
                        'valor': cc.get('valor', 0)
                    }
                    centros_custo_enriquecidos.append(centro_enriquecido)
                
                # Manter como objeto Python (não converter para JSON string)
                centros_custo_processados = centros_custo_enriquecidos
                
            except (json.JSONDecodeError, ValueError):
                # Em caso de erro, tentar converter o original para objeto
                try:
                    centros_custo_processados = json.loads(centros_custo_json) if centros_custo_json else []
                except:
                    centros_custo_processados = []

        # Salvar agendamento
        data_competencia_obj = None
        if data_competencia:
            mes, ano = data_competencia.split('/')
            data_competencia_obj = date(int(ano), int(mes), 1)

        # Converter JSON string para objeto Python
        categorias_obj = None
        if categorias_json:
            try:
                categorias_obj = json.loads(categorias_json)
            except json.JSONDecodeError:
                categorias_obj = None

        # Converter centros de custo se ainda for string
        centros_custo_obj = []
        if centros_custo_processados:
            if isinstance(centros_custo_processados, str):
                try:
                    centros_custo_obj = json.loads(centros_custo_processados)
                except json.JSONDecodeError:
                    centros_custo_obj = []
            else:
                centros_custo_obj = centros_custo_processados

        novo_agendamento = AgendamentoPagamentoModel(
            faturamento_id=faturamento.id if faturamento else None,
            lancamento_avulso_id=id if (tipo == 'receita_avulsa' or tipo == 'despesa_avulsa') else None,
            pessoa_financeiro_id=int(pessoa_financeiro_id),
            data_vencimento=data_vencimento_obj,
            valor_total_100=valor_total,
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
        db.session.flush()  # Para obter o ID
        
        objeto_principal.situacao_pagamento_id = 6  # Categorizado

        # Salvar parcelas se parcelamento ativo
        if parcelamento_ativo and parcelas_json:
            try:
                parcelas = json.loads(parcelas_json)
                for i, parcela_data in enumerate(parcelas, 1):
                    data_venc_parcela = datetime.strptime(parcela_data['vencimento'], '%Y-%m-%d').date()
                    nova_parcela = ParcelaCategorizacaoModel(
                        agendamento_id=novo_agendamento.id,
                        numero_parcela=i,
                        data_vencimento=data_venc_parcela,
                        valor_parcela=parcela_data['valor'],
                        descricao=parcela_data.get('descricao', ''),
                        referencia=parcela_data.get('referencia', ''),
                        situacao_pagamento_id=2  # A Pagar
                    )
                    db.session.add(nova_parcela)
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                db.session.rollback()
                campos_erros['parcelas_json'] = 'Erro ao processar parcelas!'
                return render_template(
                    "faturamento/categorizar_fatura/categorizar_fatura.html", 
                    faturamento=faturamento,
                    objeto_principal=objeto_principal,
                    pessoas_financeiro=pessoas_financeiro,
                    situacoes_pagamento=situacoes_pagamento,
                    estrutura_plano_contas=estrutura_plano_contas,
                    estrutura_fiscal=estrutura_fiscal,
                    campos_obrigatorios=campos_obrigatorios,
                    campos_erros=campos_erros,
                    dados_corretos=dados_corretos,
                    tipo_categorização=tipo  # Passar o tipo para o template
                )

        # Processar anexos se houver
        anexos = request.files.getlist('anexos')
        anexos_validos = [anexo for anexo in anexos if anexo and anexo.filename != '']
        
        if anexos_validos:
            for i, anexo in enumerate(anexos_validos):
                try:
                    # Nome do arquivo para upload
                    nome_arquivo = f"anexo_agend_{novo_agendamento.id}_{i+1}"
                    objeto_upload = upload_arquivo(
                        anexo,
                        "UPLOAD_COMPROVANTE_RECEITA_DESPESA",
                        nome_arquivo
                    )
                    
                    # Criar registro de anexo
                    novo_anexo = AgendamentoAnexoPagamentoModel(
                        agendamento_id=novo_agendamento.id,
                        upload_arquivo_id=objeto_upload.id
                    )
                    db.session.add(novo_anexo)
                    
                except Exception as e:
                    print(f'Erro ao fazer upload do arquivo {anexo.filename}: {e}')
                    flash((f"Erro ao fazer upload do arquivo {anexo.filename}", "warning"))
                    continue

        # Atualizar situação do lançamento/faturamento
        if tipo == 'receita_avulsa' or tipo == 'despesa_avulsa':
            objeto_principal.situacao_pagamento_id = 6  # Categorizado
            db.session.add(objeto_principal)
        
        # Atualizar situação do faturamento apenas se existir
        if faturamento:
            faturamento.situacao_id = 6  # Categorizado
            db.session.add(faturamento)
            
        PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
            current_user.id,
            TipoAcaoEnum.CADASTRO,
            TipoAcaoEnum.CADASTRO.pontos,
            modulo="informar_categorizacao_fatura",
        )

        db.session.commit()
        flash(('Categorização de faturamento realizado com sucesso!', 'success'))
        if tipo == 'receita':
            return redirect(url_for('listagem_faturamentos_cargas_a_receber'))
        if tipo == 'receita_avulsa':
            return redirect(url_for('listagem_receitas_avulsas'))
        if tipo == 'despesa_avulsa':
            return redirect(url_for('listagem_despesas_avulsas'))
        else:
            return redirect(url_for('listagem_faturamentos_cargas_a_pagar'))

    except Exception as e:
        print(f'Erro ao categorizar fatura: {e}')
        db.session.rollback()
        flash((f'Erro ao categorizar fatura! Entre em contato com o suporte.', 'error'))
        return redirect(url_for('listagem_faturamentos_cargas_a_pagar'))

@app.route("/faturamento/categorizacao/detalhes-json/<int:id>", methods=["GET"])
@login_required
@requires_roles
def detalhes_categorizacao_faturamento_json(id):
    """Retorna JSON com os detalhes da categorização de um faturamento"""
    try:
        # Buscar o faturamento
        faturamento = FaturamentoModel.obter_faturamento_por_id(id)
        if not faturamento:
            return jsonify({'error': 'Faturamento não encontrado!'}), 404
            
        # Buscar o agendamento de pagamento
        agendamento = db.session.query(AgendamentoPagamentoModel).filter_by(faturamento_id=id).first()
        if not agendamento:
            return jsonify({'error': 'Este faturamento ainda não foi categorizado.'}), 404
            
        # Buscar dados relacionados
        pessoa = PessoaFinanceiroModel.obter_pessoa_por_id(agendamento.pessoa_financeiro_id)
        situacao = SituacaoPagamentoModel.obter_situacao_por_id(agendamento.situacao_pagamento_id)
        
        # Obter detalhes dos fornecedores e transportadoras do faturamento
        detalhes = faturamento.obter_detalhes()
        fornecedores_lista = detalhes.get("fornecedores", [])
        transportadoras_lista = detalhes.get("transportadoras", [])
        extratores_lista = detalhes.get("extratores", [])

        # Processar fornecedores para garantir campos corretos
        for fornecedor in fornecedores_lista:
            if not fornecedor.get('identificacao') and fornecedor.get('fornecedor_identificacao'):
                fornecedor['identificacao'] = fornecedor['fornecedor_identificacao']
            if not fornecedor.get('numero_documento') and fornecedor.get('nota_fiscal'):
                fornecedor['numero_documento'] = fornecedor['nota_fiscal']
            # Garantir que os valores de crédito e valor bruto estejam corretos
            fornecedor['valor'] = fornecedor.get('valor_faturado', fornecedor.get('valor_bruto', 0))
            fornecedor['valor_bruto_total'] = fornecedor.get('valor_bruto', 0)
            fornecedor['valor_credito_aplicado'] = fornecedor.get('valor_credito', 0)
        
        # Processar transportadoras para garantir campos corretos  
        for transportadora in transportadoras_lista:
            if not transportadora.get('identificacao') and transportadora.get('transportadora_identificacao'):
                transportadora['identificacao'] = transportadora['transportadora_identificacao']
            # Garantir que os valores de crédito e valor bruto estejam corretos
            transportadora['valor'] = transportadora.get('valor_faturado', transportadora.get('valor_bruto', 0))
            transportadora['valor_bruto_total'] = transportadora.get('valor_bruto', 0)
            transportadora['valor_credito_aplicado'] = transportadora.get('valor_credito', 0)

        # Processar extratores para garantir campos corretos  
        for extrator in extratores_lista:
            if not extrator.get('identificacao') and extrator.get('extrator_identificacao'):
                extrator['identificacao'] = extrator['extrator_identificacao']
            # Garantir que os valores de crédito e valor bruto estejam corretos
            extrator['valor'] = extrator.get('valor_faturado', extrator.get('valor_bruto', 0))
            extrator['valor_bruto_total'] = extrator.get('valor_bruto', 0)
            extrator['valor_credito_aplicado'] = extrator.get('valor_credito', 0)
        
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
                    
                    # Conversões seguras para float
                    try:
                        valor_cat = float(cat.get('valor', 0))
                    except (ValueError, TypeError):
                        valor_cat = 0.0
                    
                    try:
                        percentual_cat = float(cat.get('percentual', 0))
                    except (ValueError, TypeError):
                        percentual_cat = 0.0
                    
                    categorias_processadas.append({
                        'nome': categoria_nome,
                        'detalhamento': categoria_detalhamento,
                        'referencia': categoria_referencia,
                        'codigo': categoria_codigo,
                        'valor': valor_cat,
                        'percentual': percentual_cat,
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
                    centro_id = cc.get('centro', 'Não informado')
                    centro_nome = cc.get('centro_nome')  # Tentar usar nome já salvo
                    
                    # Se não tiver nome salvo, buscar pelo ID
                    if not centro_nome:
                        centro_nome = 'Não informado'
                    
                    # Conversões seguras para float
                    try:
                        valor_cc = float(cc.get('valor', 0))
                    except (ValueError, TypeError):
                        valor_cc = 0.0
                    
                    try:
                        percentual_cc = float(cc.get('percentual', 0))
                    except (ValueError, TypeError):
                        percentual_cc = 0.0
                    
                    centros_custo_processados.append({
                        'id': centro_id,  # ID original do centro de custo
                        'nome': centro_nome,
                        'valor': valor_cc,
                        'percentual': percentual_cc
                    })
            except (json.JSONDecodeError, ValueError):
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
        
        # Calcular totais corretos com tratamento seguro de conversão
        try:
            valor_bruto_total = float(faturamento.valor_bruto_total or faturamento.valor_total or 0)
        except (ValueError, TypeError):
            valor_bruto_total = 0.0
            
        try:
            valor_credito_total = float(faturamento.valor_credito_aplicado or 0)
        except (ValueError, TypeError):
            valor_credito_total = 0.0
            
        try:
            valor_final_total = float(faturamento.valor_total or 0)
        except (ValueError, TypeError):
            valor_final_total = 0.0
        
        # Se não tiver valor_bruto_total, calcular dos fornecedores e transportadoras
        if not valor_bruto_total or valor_bruto_total == valor_final_total:
            valor_bruto_calculado = 0
            valor_credito_calculado = 0
            
            for fornecedor in fornecedores_lista:
                valor_bruto_calculado += (fornecedor.get('valor_bruto_total') or fornecedor.get('valor_bruto') or 0)
                valor_credito_calculado += (fornecedor.get('valor_credito_aplicado') or fornecedor.get('valor_credito') or 0)
            
            for transportadora in transportadoras_lista:
                valor_bruto_calculado += (transportadora.get('valor_bruto_total') or transportadora.get('valor_bruto') or 0)
                valor_credito_calculado += (transportadora.get('valor_credito_aplicado') or transportadora.get('valor_credito') or 0)
            
            if valor_bruto_calculado > 0:
                valor_bruto_total = valor_bruto_calculado
            if valor_credito_calculado > 0:
                valor_credito_total = valor_credito_calculado

        # Montar resposta JSON
        dados = {
            'categorizacao_id': agendamento.id,
            'faturamento': {
                'codigo': faturamento.codigo_faturamento,
                'valor_total': valor_final_total,
                'valor_bruto_total': valor_bruto_total,
                'valor_credito_total': valor_credito_total,
                'fornecedores': fornecedores_lista,
                'transportadoras': transportadoras_lista,
                'extratores': extratores_lista
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


@app.route("/faturamento/editar-categorizacao/<int:agendamento_id>", methods=["GET", "POST"])
@app.route("/faturamento/editar-categorizacao/<int:agendamento_id>/<tipo>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_categorizacao(agendamento_id, tipo=None):
    try:
        # Buscar o agendamento existente
        agendamento = AgendamentoPagamentoModel.query.get(agendamento_id)
        if not agendamento:
            flash((f'Agendamento não encontrado!', 'error'))
            return redirect(url_for('listagem_faturamentos_cargas_a_pagar'))

        # Determinar o tipo se não foi passado na URL
        if not tipo:
            if agendamento.lancamento_avulso_id:
                lancamento_avulso = LancamentoAvulsoModel.obter_lancamento_por_id(agendamento.lancamento_avulso_id)
                tipo = 'receita_avulsa' if lancamento_avulso.tipo_movimentacao == 1 else 'despesa_avulsa'
            else:
                faturamento = FaturamentoModel.obter_faturamento_por_id(agendamento.faturamento_id)
                tipo = 'receita' if faturamento.direcao_financeira == 1 else 'despesa'

        # Buscar objeto principal baseado no tipo
        if tipo == 'receita_avulsa' or tipo == 'despesa_avulsa':
            # Buscar lançamento avulso diretamente
            if not agendamento.lancamento_avulso_id:
                flash((f'Lançamento avulso não encontrado!', 'error'))
                return redirect(url_for('listagem_despesas_avulsas' if tipo == 'despesa_avulsa' else 'listagem_receitas_avulsas'))
            
            lancamento_avulso = LancamentoAvulsoModel.obter_lancamento_por_id(agendamento.lancamento_avulso_id)
            if not lancamento_avulso:
                flash((f'Lançamento avulso não encontrado!', 'error'))
                return redirect(url_for('listagem_despesas_avulsas' if tipo == 'despesa_avulsa' else 'listagem_receitas_avulsas'))
            
            valor_total = lancamento_avulso.valor_movimentacao_100
            objeto_principal = lancamento_avulso
            faturamento = None  # Lançamentos avulsos NÃO TÊM faturamento
        else:
            # Buscar faturamento normal
            if not agendamento.faturamento_id:
                flash((f'Faturamento não encontrado!', 'error'))
                return redirect(url_for('listagem_faturamentos_cargas_a_pagar'))
            
            faturamento = FaturamentoModel.obter_faturamento_por_id(agendamento.faturamento_id)
            if not faturamento:
                flash((f'Faturamento não encontrado!', 'error'))
                return redirect(url_for('listagem_faturamentos_cargas_a_pagar'))
            valor_total = faturamento.valor_total
            objeto_principal = faturamento

        # Determinar o tipo de plano de contas baseado no parâmetro
        tipo_plano_conta = [1] if tipo == 'receita' or tipo == 'receita_avulsa' else [2]  # 1 = Receitas, 2 = Despesas
        
        campos_obrigatorios = {}
        campos_erros = {}
        dados_corretos = {}

        # Carregar dados para os selects
        pessoas_financeiro = PessoaFinanceiroModel.listar_pessoas_ativas()
        # Processar documentos formatados para cada pessoa
        for p in pessoas_financeiro:
            if p.numero_documento and len(p.numero_documento.strip()) > 0:
                p.documento_formatado = ValidaDocs.insere_pontuacao_cnpj(p.numero_documento) if len(p.numero_documento) == 14 else ValidaDocs.insere_pontuacao_cpf(p.numero_documento)
            else:
                p.documento_formatado = "N/A"
        
        situacoes_pagamento = SituacaoPagamentoModel.listar_status()
        centros_custo = CentroCustoModel.obter_centro_custos_ativos()
        contas_bancarias = ContaBancariaModel.obter_contas_bancarias_ativas()
        
        # Inicializar e carregar plano de contas com o tipo correto (com marcação de folhas)
        estrutura_plano_contas = obter_estrutura_com_folhas(tipo_plano_conta)

        # Buscar parcelas existentes se houver
        parcelas_existentes = []
        if agendamento.parcelamento_ativo:
            parcelas_existentes = ParcelaCategorizacaoModel.query.filter_by(agendamento_id=agendamento_id).order_by(ParcelaCategorizacaoModel.numero_parcela).all()

        # Buscar anexos existentes
        anexos_existentes = AgendamentoAnexoPagamentoModel.obter_todos_anexos_por_agendamento(agendamento_id)

        if request.method == "GET":
            # Pré-popular dados do agendamento existente
            dados_corretos = {
                'data_vencimento': agendamento.data_vencimento.strftime('%Y-%m-%d') if agendamento.data_vencimento else '',
                'data_competencia': agendamento.data_competencia.strftime('%m/%Y') if agendamento.data_competencia else '',
                'conta_bancaria_id': str(agendamento.conta_bancaria_id) if agendamento.conta_bancaria_id else '',
                'pessoa_financeiro_id': str(agendamento.pessoa_financeiro_id) if agendamento.pessoa_financeiro_id else '',
                'descricao': agendamento.descricao or '',
                'referencia': agendamento.referencia or '',
                'categorias_json': json.dumps(agendamento.categorias_json) if agendamento.categorias_json and not isinstance(agendamento.categorias_json, str) else (agendamento.categorias_json or ''),
                'centros_custo_json': json.dumps(agendamento.centros_custo_json) if agendamento.centros_custo_json and not isinstance(agendamento.centros_custo_json, str) else (agendamento.centros_custo_json or '[]'),
                'valores_detalhados_ativo': bool(agendamento.centros_custo_json and agendamento.centros_custo_json != '[]'),
                'parcelamento_ativo': agendamento.parcelamento_ativo,
                'numero_parcelas': str(agendamento.numero_parcelas) if agendamento.numero_parcelas else '',
                'dias_entre_parcelas': str(agendamento.dias_entre_parcelas) if agendamento.dias_entre_parcelas else '30',
                'parcelas_json': json.dumps([{
                    'vencimento': p.data_vencimento.strftime('%Y-%m-%d'),
                    'valor': p.valor_parcela,
                    'descricao': p.descricao or '',
                    'referencia': p.referencia or ''
                } for p in parcelas_existentes]) if parcelas_existentes else ''
            }


            return render_template(
                "faturamento/categorizar_fatura/editar_categorizacao_fatura.html", 
                agendamento=agendamento,
                faturamento=faturamento,
                objeto_principal=objeto_principal,
                pessoas_financeiro=pessoas_financeiro,
                situacoes_pagamento=situacoes_pagamento,
                estrutura_plano_contas=estrutura_plano_contas,
                centros_custo=centros_custo,
                campos_obrigatorios=campos_obrigatorios,
                campos_erros=campos_erros,
                dados_corretos=dados_corretos,
                contas_bancarias=contas_bancarias,
                tipo_categorização=tipo,  # Passar o tipo para o template
                parcelas_existentes=parcelas_existentes,
                anexos_existentes=anexos_existentes
            )

        # POST - Processar formulário de edição
        data_vencimento = request.form.get("data_vencimento", "")
        data_competencia = request.form.get("data_competencia", "")
        conta_bancaria_id = request.form.get("conta_bancaria_id", "")
        pessoa_financeiro_id = request.form.get("pessoa_financeiro_id", "")
        descricao = request.form.get("descricao", "")
        referencia = request.form.get("referencia", "")
        categorias_json = request.form.get("categorias_json", "")
        centros_custo_json = request.form.get("centros_custo_json", "")
        valores_detalhados_ativo = request.form.get("valores_detalhados_ativo") == "true"
        parcelamento_ativo = request.form.get("parcelamento_ativo") == "true"
        numero_parcelas = request.form.get("numero_parcelas", "")
        dias_entre_parcelas = request.form.get("dias_entre_parcelas", "30")
        parcelas_json = request.form.get("parcelas_json", "")

        # Preservar dados do formulário
        dados_corretos = {
            'data_vencimento': data_vencimento,
            'data_competencia': data_competencia,
            'conta_bancaria_id': conta_bancaria_id,
            'pessoa_financeiro_id': pessoa_financeiro_id,
            'descricao': descricao,
            'referencia': referencia,
            'categorias_json': categorias_json,
            'centros_custo_json': centros_custo_json,
            'valores_detalhados_ativo': valores_detalhados_ativo,
            'parcelamento_ativo': parcelamento_ativo,
            'numero_parcelas': numero_parcelas,
            'dias_entre_parcelas': dias_entre_parcelas,
            'parcelas_json': parcelas_json
        }
    
        # Validações obrigatórias (mesmas do cadastro)
        if not data_vencimento.strip():
            campos_obrigatorios['data_vencimento'] = 'Data de vencimento é obrigatória!'
        
        if not pessoa_financeiro_id.strip():
            campos_obrigatorios['pessoa_financeiro_id'] = 'Beneficiário é obrigatório!'

        if not conta_bancaria_id.strip():
            campos_obrigatorios['conta_bancaria_id'] = 'Conta bancária é obrigatória!'

        if not categorias_json.strip():
            campos_obrigatorios['categorias_json'] = 'Pelo menos uma categoria é obrigatória!'

        # Validações de formato (mesmas do cadastro)
        if data_vencimento:
            try:
                data_vencimento_obj = datetime.strptime(data_vencimento, '%Y-%m-%d').date()
            except ValueError:
                campos_erros['data_vencimento'] = 'Data de vencimento inválida!'

        if data_competencia:
            try:
                # Formato MM/AAAA
                datetime.strptime(data_competencia, '%m/%Y')
            except ValueError:
                campos_erros['data_competencia'] = 'Data de competência deve estar no formato MM/AAAA!'

        if pessoa_financeiro_id:
            try:
                pessoa_id = int(pessoa_financeiro_id)
                pessoa = PessoaFinanceiroModel.obter_pessoa_por_id(pessoa_id)
                if not pessoa:
                    campos_erros['pessoa_financeiro_id'] = 'Beneficiário não encontrado!'
            except ValueError:
                campos_erros['pessoa_financeiro_id'] = 'Beneficiário inválido!'

        # Validar categorias JSON (mesma lógica do cadastro)
        if categorias_json:
            try:
                categorias = json.loads(categorias_json)
                if not isinstance(categorias, list) or len(categorias) == 0:
                    campos_erros['categorias_json'] = 'Pelo menos uma categoria deve ser informada!'
                else:
                    # Verificar categorias duplicadas
                    categorias_usadas = []
                    for cat in categorias:
                        nome_categoria = cat.get('nome', '')
                        if nome_categoria in categorias_usadas:
                            campos_erros['categorias_json'] = f'A categoria "{nome_categoria}" foi selecionada mais de uma vez!'
                            break
                        if nome_categoria:  # Só adiciona se não estiver vazia
                            categorias_usadas.append(nome_categoria)
                    
                    # Validar total apenas se não há categorias duplicadas
                    if 'categorias_json' not in campos_erros:
                        total_categorias = sum(cat.get('valor', 0) for cat in categorias)
                        if total_categorias != valor_total:
                            campos_erros['categorias_json'] = 'O valor total das categorias deve ser igual ao valor do lançamento!'
            except json.JSONDecodeError:
                campos_erros['categorias_json'] = 'Formato de categorias inválido!'

        # Validar parcelamento (mesma lógica do cadastro)
        if parcelamento_ativo:
            if not numero_parcelas.strip():
                campos_obrigatorios['numero_parcelas'] = 'Número de parcelas é obrigatório quando parcelamento está ativo!'
            else:
                try:
                    num_parcelas = int(numero_parcelas)
                    if num_parcelas < 2:
                        campos_erros['numero_parcelas'] = 'Número de parcelas deve ser maior que 1!'
                except ValueError:
                    campos_erros['numero_parcelas'] = 'Número de parcelas inválido!'
            
            # Validar dados das parcelas se parcelamento ativo
            if parcelas_json:
                try:
                    parcelas = json.loads(parcelas_json)
                    if not isinstance(parcelas, list) or len(parcelas) == 0:
                        campos_erros['parcelas_json'] = 'Dados de parcelas são obrigatórios quando parcelamento está ativo!'
                    else:
                        for i, parcela in enumerate(parcelas, 1):
                            if not parcela.get('vencimento'):
                                campos_erros['parcelas_json'] = f'Data de vencimento da parcela {i} é obrigatória!'
                                break
                            if not parcela.get('valor') or parcela.get('valor') <= 0:
                                campos_erros['parcelas_json'] = f'Valor da parcela {i} deve ser maior que zero!'
                                break
                except json.JSONDecodeError:
                    campos_erros['parcelas_json'] = 'Formato de parcelas inválido!'
            else:
                campos_erros['parcelas_json'] = 'Dados de parcelas são obrigatórios quando parcelamento está ativo!'

        # Validar valores detalhados (centro de custo) - mesma lógica do cadastro
        if valores_detalhados_ativo:
            if centros_custo_json:
                try:
                    centros_custo = json.loads(centros_custo_json)
                    if not isinstance(centros_custo, list) or len(centros_custo) == 0:
                        campos_erros['centros_custo_json'] = 'Pelo menos um centro de custo deve ser informado quando valores detalhados está ativo!'
                    else:
                        for i, centro in enumerate(centros_custo, 1):
                            if not centro.get('centro'):
                                campos_erros['centros_custo_json'] = f'Centro de custo {i} deve ser selecionado!'
                                break
                            # Validar se tem valor ou percentual dependendo do tipo
                            if not centro.get('valor') and not centro.get('percentual'):
                                campos_erros['centros_custo_json'] = f'Centro de custo {i} deve ter valor ou percentual informado!'
                                break
                except json.JSONDecodeError:
                    campos_erros['centros_custo_json'] = 'Formato de centros de custo inválido!'
            else:
                campos_erros['centros_custo_json'] = 'Dados de centros de custo são obrigatórios quando valores detalhados está ativo!'

        # Validar categorias - sempre obrigatórias (mesma lógica do cadastro)
        if categorias_json:
            try:
                categorias = json.loads(categorias_json)
                if not isinstance(categorias, list) or len(categorias) == 0:
                    campos_erros['categorias_json'] = 'Pelo menos uma categoria deve ser informada!'
                else:
                    categorias_usadas = set()
                    for i, categoria in enumerate(categorias, 1):
                        if not categoria.get('categoria'):
                            campos_erros['categorias_json'] = f'Categoria {i} deve ser selecionada!'
                            break
                        if not categoria.get('valor') or categoria.get('valor') <= 0:
                            campos_erros['categorias_json'] = f'Valor da categoria {i} deve ser maior que zero!'
                            break
                        # Verificar duplicatas
                        categoria_id = categoria.get('categoria')
                        if categoria_id in categorias_usadas:
                            campos_erros['categorias_json'] = f'A categoria não pode ser repetida!'
                            break
                        categorias_usadas.add(categoria_id)
            except json.JSONDecodeError:
                campos_erros['categorias_json'] = 'Formato de categorias inválido!'
        else:
            campos_erros['categorias_json'] = 'Pelo menos uma categoria deve ser informada!'

        # Se há erros, retornar formulário com erros
        if campos_obrigatorios or campos_erros:
            return render_template(
                "faturamento/categorizar_fatura/editar_categorizacao_fatura.html", 
                agendamento=agendamento,
                faturamento=faturamento,
                objeto_principal=objeto_principal,
                pessoas_financeiro=pessoas_financeiro,
                situacoes_pagamento=situacoes_pagamento,
                estrutura_plano_contas=estrutura_plano_contas,
                centros_custo=centros_custo,
                campos_obrigatorios=campos_obrigatorios,
                campos_erros=campos_erros,
                dados_corretos=dados_corretos,
                tipo_categorização=tipo,
                parcelas_existentes=parcelas_existentes,
                contas_bancarias=contas_bancarias,
                anexos_existentes=anexos_existentes
            )

        # Processar e enriquecer centros de custo com nomes (mesma lógica do cadastro)
        centros_custo_processados = centros_custo_json
        if centros_custo_json:
            try:
                centros_custo = json.loads(centros_custo_json)
                centros_custo_enriquecidos = []
                
                for cc in centros_custo:
                    centro_id = cc.get('centro')
                    centro_nome = centro_id
                    
                    # Se for ID numérico, buscar o nome do centro de custo
                    if str(centro_id).isdigit():
                        centro_custo_obj = CentroCustoModel.obter_centro_custo_por_id(int(centro_id))
                        if centro_custo_obj:
                            centro_nome = centro_custo_obj.nome
                    
                    # Manter estrutura original mas com nome enriquecido
                    centro_enriquecido = {
                        'centro': centro_id,  # Manter ID original
                        'centro_nome': centro_nome,  # Adicionar nome
                        'percentual': cc.get('percentual', ''),
                        'valor': cc.get('valor', 0)
                    }
                    centros_custo_enriquecidos.append(centro_enriquecido)
                
                # Manter como objeto Python (não converter para JSON string)
                centros_custo_processados = centros_custo_enriquecidos
                
            except (json.JSONDecodeError, ValueError):
                # Em caso de erro, tentar converter o original para objeto
                try:
                    centros_custo_processados = json.loads(centros_custo_json) if centros_custo_json else []
                except:
                    centros_custo_processados = []

        # Atualizar agendamento existente
        data_competencia_obj = None
        if data_competencia:
            mes, ano = data_competencia.split('/')
            data_competencia_obj = date(int(ano), int(mes), 1)

        # Converter JSON string para objeto Python
        categorias_obj = None
        if categorias_json:
            try:
                categorias_obj = json.loads(categorias_json)
            except json.JSONDecodeError:
                categorias_obj = None

        # Converter centros de custo se ainda for string
        centros_custo_obj = []
        if centros_custo_processados:
            if isinstance(centros_custo_processados, str):
                try:
                    centros_custo_obj = json.loads(centros_custo_processados)
                except json.JSONDecodeError:
                    centros_custo_obj = []
            else:
                centros_custo_obj = centros_custo_processados

        # Atualizar campos do agendamento
        agendamento.pessoa_financeiro_id = int(pessoa_financeiro_id)
        agendamento.data_vencimento = data_vencimento_obj
        agendamento.conta_bancaria_id = int(conta_bancaria_id)
        agendamento.descricao = descricao if descricao else None
        agendamento.referencia = referencia if referencia else None
        agendamento.data_competencia = data_competencia_obj
        agendamento.categorias_json = categorias_obj
        agendamento.centros_custo_json = centros_custo_obj
        agendamento.parcelamento_ativo = parcelamento_ativo
        agendamento.numero_parcelas = int(numero_parcelas) if numero_parcelas else None
        agendamento.dias_entre_parcelas = int(dias_entre_parcelas)

        # Remover parcelas antigas se existirem
        ParcelaCategorizacaoModel.query.filter_by(agendamento_id=agendamento_id).delete()

        # Salvar novas parcelas se parcelamento ativo
        if parcelamento_ativo and parcelas_json:
            try:
                parcelas = json.loads(parcelas_json)
                for i, parcela_data in enumerate(parcelas, 1):
                    data_venc_parcela = datetime.strptime(parcela_data['vencimento'], '%Y-%m-%d').date()
                    nova_parcela = ParcelaCategorizacaoModel(
                        agendamento_id=agendamento.id,
                        numero_parcela=i,
                        data_vencimento=data_venc_parcela,
                        valor_parcela=parcela_data['valor'],
                        descricao=parcela_data.get('descricao', ''),
                        referencia=parcela_data.get('referencia', ''),
                        situacao_pagamento_id=2  # A Pagar
                    )
                    db.session.add(nova_parcela)
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                db.session.rollback()
                campos_erros['parcelas_json'] = 'Erro ao processar parcelas!'
                return render_template(
                    "faturamento/categorizar_fatura/editar_categorizacao_fatura.html", 
                    agendamento=agendamento,
                    faturamento=faturamento,
                    objeto_principal=objeto_principal,
                    pessoas_financeiro=pessoas_financeiro,
                    situacoes_pagamento=situacoes_pagamento,
                    estrutura_plano_contas=estrutura_plano_contas,
                    campos_obrigatorios=campos_obrigatorios,
                    campos_erros=campos_erros,
                    dados_corretos=dados_corretos,
                    tipo_categorização=tipo
                )
        
        # Processar anexos se houver novos arquivos
        anexos = request.files.getlist('anexos')
        anexos_validos = [anexo for anexo in anexos if anexo and anexo.filename != '']
        
        if anexos_validos:
            for i, anexo in enumerate(anexos_validos):
                try:
                    # Nome do arquivo para upload
                    nome_arquivo = f"anexo_agend_{agendamento.id}_{i+1}"
                    objeto_upload = upload_arquivo(
                        anexo,
                        "UPLOAD_COMPROVANTE_RECEITA_DESPESA",
                        nome_arquivo
                    )
                    
                    # Criar registro de anexo
                    novo_anexo = AgendamentoAnexoPagamentoModel(
                        agendamento_id=agendamento.id,
                        upload_arquivo_id=objeto_upload.id
                    )
                    db.session.add(novo_anexo)
                    
                except Exception as e:
                    print(f'Erro ao fazer upload do arquivo {anexo.filename}: {e}')
                    flash((f"Erro ao fazer upload do arquivo {anexo.filename}", "warning"))
                    continue
        
        # Processar exclusão de anexos existentes
        anexos_excluir = request.form.get('anexos_excluir', '[]')
        try:
            anexos_ids_excluir = json.loads(anexos_excluir)
            if anexos_ids_excluir and isinstance(anexos_ids_excluir, list):
                for anexo_id in anexos_ids_excluir:
                    anexo = AgendamentoAnexoPagamentoModel.query.get(int(anexo_id))
                    if anexo and anexo.agendamento_id == agendamento.id:
                        anexo.deletado = True
                        anexo.ativo = False
        except (json.JSONDecodeError, ValueError) as e:
            print(f'Erro ao processar exclusão de anexos: {e}')
        
        PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
            current_user.id,
            TipoAcaoEnum.EDICAO,
            TipoAcaoEnum.EDICAO.pontos,
            modulo="editar_categorizacao_fatura",
        )

        db.session.commit()
        flash(('Categorização editada com sucesso!', 'success'))
        
        # Redirecionar baseado no tipo (mesma lógica do cadastro)
        if tipo == 'receita':
            return redirect(url_for('listagem_faturamentos_cargas_a_receber'))
        elif tipo == 'receita_avulsa':
            return redirect(url_for('listagem_receitas_avulsas'))
        elif tipo == 'despesa_avulsa':
            return redirect(url_for('listagem_despesas_avulsas'))
        else:
            return redirect(url_for('listagem_faturamentos_cargas_a_pagar'))

    except Exception as e:
        print(e)
        db.session.rollback()
        flash((f'Erro ao editar categorização! Entre em contato com o suporte.', 'error'))
        return redirect(url_for('listagem_faturamentos_cargas_a_pagar'))

@app.route("/faturamento/categorizacao/detalhes-lancamento-avulso/<int:id>", methods=["GET"])
@login_required
@requires_roles
def detalhes_categorizacao_lancamento_avulso(id):
    """Retorna JSON com os detalhes da categorização de um lançamento avulso"""
    try:
        # Buscar o lançamento avulso
        lancamento_avulso = LancamentoAvulsoModel.obter_lancamento_por_id(id)
        if not lancamento_avulso:
            return jsonify({'error': 'Lançamento avulso não encontrado!'}), 404
            
        # Buscar o agendamento de pagamento relacionado ao lançamento avulso
        agendamento = db.session.query(AgendamentoPagamentoModel).filter_by(lancamento_avulso_id=id).first()
        if not agendamento:
            return jsonify({'error': 'Este lançamento avulso ainda não foi categorizado.'}), 404
            
        # Buscar dados relacionados
        pessoa = PessoaFinanceiroModel.obter_pessoa_por_id(agendamento.pessoa_financeiro_id)
        situacao = SituacaoPagamentoModel.obter_situacao_por_id(agendamento.situacao_pagamento_id)
        
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
                    
                    # Se for ID numérico, buscar dados completos da categoria
                    if str(categoria_nome).isdigit():
                        plano_conta = PlanoContaModel.buscar_por_id(int(categoria_nome))
                        if plano_conta:
                            categoria_nome = plano_conta.nome
                            categoria_codigo = plano_conta.codigo
                    
                    categorias_processadas.append({
                        'nome': f"{categoria_codigo} - {categoria_nome}" if categoria_codigo else categoria_nome,
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
                    centro_id = cc.get('centro', 'Não informado')
                    centro_nome = cc.get('centro_nome')  # Tentar usar nome já salvo
                    
                    # Se não tiver nome salvo, buscar pelo ID
                    if not centro_nome and str(centro_id).isdigit():
                        centro_custo_obj = CentroCustoModel.obter_centro_custo_por_id(int(centro_id))
                        if centro_custo_obj:
                            centro_nome = centro_custo_obj.nome
                    
                    if not centro_nome:
                        centro_nome = 'Não informado'
                    
                    # Tratar valores que podem estar vazios como string
                    percentual = cc.get('percentual', 0)
                    if percentual == "" or percentual is None:
                        percentual = 0
                    else:
                        percentual = float(percentual)
                    
                    valor = cc.get('valor', 0)
                    if valor == "" or valor is None:
                        valor = 0
                    else:
                        valor = float(valor)
                    
                    centro_processado = {
                        'id': centro_id,  # ID original do centro de custo
                        'nome': centro_nome,
                        'valor': valor,
                        'percentual': percentual
                    }
                    centros_custo_processados.append(centro_processado)
                
            except (json.JSONDecodeError, ValueError) as e:
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
        
        # Montar resposta JSON
        dados = {
            'categorizacao_id': agendamento.id,
            'lancamento': {
                'id': lancamento_avulso.id,
                'descricao': lancamento_avulso.descricao,
                'valor': float(lancamento_avulso.valor_movimentacao_100),
                'tipo_movimentacao': lancamento_avulso.tipo_movimentacao,
                'data_cadastro': lancamento_avulso.data_cadastro.strftime('%d/%m/%Y') if hasattr(lancamento_avulso, 'data_cadastro') and lancamento_avulso.data_cadastro else None
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