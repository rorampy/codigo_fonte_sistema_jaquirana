from datetime import datetime
from sistema import app, requires_roles, db, current_user
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.controle_carga.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.faturamento.cargas_a_receber.nf_complementar.nf_complementar_model import NfComplementarModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema.models_views.parametros.status_emissao_nf_complementar.status_emissao_nf_complementar_model import StatusEmissaoNfComplementarModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema.models_views.upload_arquivo.upload_arquivo_model import UploadArquivoModel
from sistema.models_views.faturamento.faturamento_model import FaturamentoModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema._utilitarios import *

@app.route("/faturamento/nf-complementar", methods=["GET"])
@login_required
@requires_roles
def faturamento_nf_complementar():
    """Listagem de NFs complementares para faturamento, agrupadas por cliente"""
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    dataHoje = datetime.now().strftime('%d-%m-%Y')
    clientes = ClienteModel.listar_clientes_ativos()

    # Verificar se está vindo do agrupamento de cargas a receber
    agrupar_cargas_receber = request.args.get('agrupar_cargas_receber')
    if agrupar_cargas_receber:
        # Filtrar apenas NFs pendentes (situação 2)
        nfs_complementares = NfComplementarModel.query.filter(
            NfComplementarModel.ativo == True,
            NfComplementarModel.situacao_financeira_id == 2
        ).all()
    else:
        nfs_complementares = NfComplementarModel.listar_ativas()

    # Adaptar dados para o formato esperado pelo template (agrupado por cliente)
    registros_agrupados = []
    for nf in nfs_complementares:
        registro_obj = type('obj', (object,), {
            'id': nf.id,
            'cliente': nf.cliente.identificacao if nf.cliente else "Cliente não identificado",
            'numero_nf': nf.numero_nota_fiscal,
            'data_emissao': nf.destinatario_data_emissao,
            'peso_ton': nf.peso_ton_nf,
            'valor_total': nf.valor_total_nota_100 if nf.valor_total_nota_100 else 0,
            'destinatario_nome': nf.destinatario_nome,
            'transportador_nome': nf.transportador_nome,
            'placa_nf': nf.placa_nf,
            'motorista_nf': nf.motorista_nf,
            'arquivo_nota': nf.arquivo_nota,
            'nf_complementar_detalhes': nf.nf_complementar_detalhes,
            'situacao_financeira': nf.situacao,
            'nf_complementar': nf
        })()
        
        # Criar objeto no formato pelo template (cliente + registro)
        item_agrupado = type('obj', (object,), {
            'cliente': nf.cliente.identificacao if nf.cliente else "Cliente não identificado",
            'registro': registro_obj
        })()
        
        registros_agrupados.append(item_agrupado)

    return render_template(
        "faturamento/cargas_a_receber/nf_complementar/faturamento_nf_complementar.html",
        registros=registros_agrupados,
        clientes=clientes,
        dados_corretos=request.args,
        changelog=changelog,
        dataHoje=dataHoje,
        agrupar_cargas_receber=agrupar_cargas_receber
    )

@app.route("/faturamento/nf-complementar/informar-faturamento/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def informar_faturamento_nf_complementar(id):
    try:
        campos_obrigatorios = {}
        campos_erros = {}
        gravar_banco = True

        registro = NfComplementarModel.obter_por_id(id)

        if not registro:
            flash(("Registro não encontrado!", "warning"))
            return redirect(url_for('faturamento_nf_complementar'))

        if registro.situacao_financeira_id == 5:
            flash(("Registro já consta como faturado!", "warning"))
            return redirect(url_for('faturamento_nf_complementar'))
            
        # Buscar registros operacionais dos detalhes
        registros_operacionais = []
        if registro.nf_complementar_detalhes and 'registros_operacionais' in registro.nf_complementar_detalhes:
            registro_ids = [item['registro_id'] for item in registro.nf_complementar_detalhes['registros_operacionais']]
            if registro_ids:
                registros_operacionais = RegistroOperacionalModel.query.filter(
                    RegistroOperacionalModel.id.in_(registro_ids)
                ).all()
        
        registro_dict = {
            'id': registro.id,
            'cliente': registro.cliente if registro.cliente else None,
            'data_emissao': registro.destinatario_data_emissao or None,
            'destinatario': registro.destinatario_nome or 'Não informado',
            'numero_nota_fiscal': registro.numero_nota_fiscal or None,
            'peso_ton': registro.peso_ton_nf or 0,
            'transportador': registro.transportador_nome or None,
            'valor_total_100': registro.valor_total_nota_100 or 0,
            'registros_operacionais': registros_operacionais,
        }
        
        if request.method == "POST":
            if gravar_banco:
                registro.situacao_financeira_id = 5  
                
                # Criação do faturamento para o registro individual (adaptado para extrator)
                novo_faturamento = FaturamentoModel(
                    usuario_id=current_user.id,
                    codigo_faturamento=FaturamentoModel.gerar_codigo_novo_faturamento(),
                    valor_total=registro.valor_total_nota_100 or 0, 
                    ids_nf_complementar=str(registro.id),
                    situacao_pagamento_id=7,
                    tipo_operacao=1,
                    direcao_financeira=1
                )
               
                # Detalhes para NF complementar (vai no array de NF complementar)
                detalhes_nf_complementar = [{
                    "nf_complementar_id": registro.id,
                    "numero_nf": registro.numero_nota_fiscal or "",
                    "cliente_id": registro.cliente.id if registro.cliente else "",
                    "cliente": registro.cliente.identificacao if registro.cliente else "",
                    "valor_total_nota_100": registro.valor_total_nota_100 or 0,
                    "peso_ton_nf": f"{registro.peso_ton_nf}" if registro and registro.peso_ton_nf else "",
                    "preco_un_nf": registro.preco_un_nf or 0,
                    "destinatario_data_emissao": registro.destinatario_data_emissao.strftime('%Y-%m-%d') if registro.destinatario_data_emissao else "",
                }]

                # Salvar detalhes
                novo_faturamento.salvar_detalhes(nf_complementar=detalhes_nf_complementar)

                db.session.add(novo_faturamento)
                db.session.commit()
                
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    TipoAcaoEnum.CADASTRO,
                    TipoAcaoEnum.CADASTRO.pontos,
                    modulo="informar_faturamento_nf_complementar",
                )
                
                flash(("Faturamento informado com sucesso!", "success"))
                return redirect(url_for('faturamento_nf_complementar'))

        return render_template(
            "faturamento/cargas_a_receber/nf_complementar/informar_faturamento_nf_complementar.html",
            campos_obrigatorios=campos_obrigatorios,
            campos_erros=campos_erros,
            dados_corretos=request.form,
            registro=registro_dict
        )
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Erro ao informar faturamento de carga: {e}")
        flash((f"Erro ao informar faturamento de carga: {str(e)}", "danger"))
        return redirect(url_for("faturamento_nf_complementar"))

@app.route("/faturamento/nf-complementar/informar-faturamento-massa", methods=["GET", "POST"])
@login_required
@requires_roles
def informar_faturamento_nf_complementar_massa():
    try:
        campos_obrigatorios = {}
        campos_erros = {}
        gravar_banco = True

        if request.method == "GET":
            ids_selecionados = request.args.get('ids_registros', '')
            if not ids_selecionados:
                flash(("Nenhum registro foi selecionado para recebimento!", "warning"))
                return redirect(url_for("faturamento_nf_complementar"))
            
            try:
                ids_list = [int(id.strip()) for id in ids_selecionados.split(',') if id.strip()]
            except ValueError:
                flash(("IDs inválidos selecionados!", "warning"))
                return redirect(url_for("faturamento_nf_complementar"))

        else:  # POST
            ids_selecionados = request.form.get('ids_registros', '')
            if not ids_selecionados:
                flash(("Nenhum registro foi selecionado para recebimento!", "warning"))
                return redirect(url_for("faturamento_nf_complementar"))
            
            try:
                ids_list = [int(id.strip()) for id in ids_selecionados.split(',') if id.strip()]
            except ValueError:
                flash(("IDs inválidos selecionados!", "warning"))
                return redirect(url_for("faturamento_nf_complementar"))

        registros = [NfComplementarModel.obter_por_id(registro_id) for registro_id in ids_list]
        registros = [r for r in registros if r and r.situacao_financeira_id != 5]  # Filtrar já recebidos

        if not registros:
            flash(("Nenhum registro válido encontrado para recebimento!", "warning"))
            return redirect(url_for("faturamento_nf_complementar"))
        
        if len(registros) != len(ids_list):
            flash(("Alguns registros selecionados não estão disponíveis para recebimento!", "warning"))

        clientes_dict = {}
        valor_total_geral = 0
        valores_recebidos_dict = {}  # id do registro -> valor editado (centavos)

        for registro in registros:
            valor_total_recebimento = registro.valor_total_nota_100 or 0
            valores_recebidos_dict[registro.id] = valor_total_recebimento

            cliente_id = registro.cliente_id if registro.cliente else 0
            valor_total_geral += valor_total_recebimento

            if cliente_id not in clientes_dict:
                clientes_dict[cliente_id] = {
                    'cliente': registro.cliente if registro.cliente else None,
                    'registros': [],
                    'valor_total': 0
                }

            # Buscar registros operacionais dos detalhes
            registros_operacionais = []
            if registro.nf_complementar_detalhes and 'registros_operacionais' in registro.nf_complementar_detalhes:
                registro_ids = [item['registro_id'] for item in registro.nf_complementar_detalhes['registros_operacionais']]
                if registro_ids:
                    registros_operacionais = RegistroOperacionalModel.query.filter(
                        RegistroOperacionalModel.id.in_(registro_ids)
                    ).all()

            registro_dict = {
                'id': registro.id,
                'cliente': registro.cliente if registro.cliente else None,
                'data_emissao': registro.destinatario_data_emissao or None,
                'destinatario': registro.destinatario_nome or None,
                'numero_nota_fiscal': registro.numero_nota_fiscal or None,
                'peso_ton': registro.peso_ton_nf or 0,
                'transportador': registro.transportador_nome or None,
                'valor_total_100': registro.valor_total_nota_100 or 0,
                'registros_operacionais': registros_operacionais,
            }

            clientes_dict[cliente_id]['registros'].append(registro_dict)
            clientes_dict[cliente_id]['valor_total'] += valor_total_recebimento

        if request.method == "POST":
            if gravar_banco:
                try:
                    registros_processados = 0
                    valor_total_processado = 0
                    detalhes_nf_complementar = []

                    for registro in registros:
                        valor_recebido = valores_recebidos_dict.get(registro.id, registro.valor_total_nota_100 or 0)

                        registro.situacao_financeira_id = 5

                        registros_processados += 1
                        valor_total_processado += valor_recebido

                        detalhes_nf_complementar.append({
                            "nf_complementar_id": registro.id,
                            "numero_nf": registro.numero_nota_fiscal or "",
                            "cliente_id": registro.cliente.id if registro.cliente else "",
                            "cliente": registro.cliente.identificacao if registro.cliente else "",
                            "valor_total_nota_100": registro.valor_total_nota_100 or 0,
                            "peso_ton_nf": f"{registro.peso_ton_nf}" if registro and registro.peso_ton_nf else "",
                            "preco_un_nf": registro.preco_un_nf or 0,
                            "destinatario_data_emissao": registro.destinatario_data_emissao.strftime('%Y-%m-%d') if registro.destinatario_data_emissao else "",
                        })

                    # Criação do faturamento em massa (um único faturamento para todos os registros)
                    novo_faturamento = FaturamentoModel(
                        usuario_id=current_user.id,
                        codigo_faturamento=FaturamentoModel.gerar_codigo_novo_faturamento(),
                        valor_total=valor_total_processado or 0, 
                        ids_nf_complementar=','.join([str(r.id) for r in registros]),
                        situacao_pagamento_id=7,
                        tipo_operacao=1,
                        direcao_financeira=1
                    )
                   
                    # Salvar detalhes 
                    novo_faturamento.salvar_detalhes(nf_complementar=detalhes_nf_complementar)
                    db.session.add(novo_faturamento)

                    PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                        current_user.id,
                        TipoAcaoEnum.CADASTRO,
                        TipoAcaoEnum.CADASTRO.pontos * registros_processados,
                        modulo="informar_faturamento_nf_complementar_massa",
                    )

                    db.session.commit()
                    
                    flash((f"Faturamento em massa processado com sucesso!", "success"))
                    return redirect(url_for('faturamento_nf_complementar'))

                except Exception as e:
                    print(f"[ERROR] Erro ao processar faturamento em massa: {e}")
                    db.session.rollback()
                    flash((f"Erro ao processar faturamento em massa: {str(e)}", "error"))
                    return redirect(request.url)

        return render_template(
            "/faturamento/cargas_a_receber/nf_complementar/informar_faturamento_nf_complementar_massa.html",
            campos_obrigatorios=campos_obrigatorios,
            campos_erros=campos_erros,
            dados_corretos=request.form,
            registros=registros,
            clientes_dict=clientes_dict,
            valor_total=valor_total_geral,
            ids_selecionados=ids_selecionados
        )

    except Exception as e:
        print(f"[ERROR] Erro interno: {e}")
        db.session.rollback()
        flash((f"Erro interno: {str(e)}", "error"))
        return redirect(url_for("faturamento_nf_complementar"))
