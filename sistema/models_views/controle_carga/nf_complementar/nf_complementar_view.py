from datetime import datetime
from sistema import app, requires_roles, db, current_user
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.faturamento.cargas_a_receber.nf_complementar.nf_complementar_model import NfComplementarModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema.models_views.parametros.status_emissao_nf_complementar.status_emissao_nf_complementar_model import StatusEmissaoNfComplementarModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema.models_views.upload_arquivo.upload_arquivo_model import UploadArquivoModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema._utilitarios import *

@app.route("/controle-cargas/nfs-complementares", methods=["GET"])
@login_required
@requires_roles
def listagem_nf_complementar():
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    dataHoje = datetime.now().strftime('%d-%m-%Y')
    statusNfComplementar = StatusEmissaoNfComplementarModel.listar_status_ativos()
    clientes = ClienteModel.listar_clientes_ativos()

    if any(request.args.values()):
        registros = RegistroOperacionalModel.filtrar_registros_carga_cliente(
            data_inicio=request.args.get('dataInicio'),
            data_fim=request.args.get('dataFim'),
            numero_nf=request.args.get('numeroNfComplementar'),
            cliente=request.args.get('clienteNfComplementar'),
            status_nf_complementar=request.args.get('statusNfComplementarEmitida')
        )
    else:
        registros = RegistroOperacionalModel.obter_registros_carga_agrupados()

    return render_template(
        "controle_carga/nf_complementar/nf_complementar_listagem.html",
        registros=registros,
        clientes=clientes,
        dados_corretos=request.args,
        statusNfComplementar=statusNfComplementar,
        changelog=changelog,
        dataHoje=dataHoje
    )
    

@app.route("/controle-cargas/nfs-complementares/emitir-nfs-complementares", methods=["POST"])
@login_required
@requires_roles
def emitir_nfs_complementares_em_massa():
    """Processa formulário de criação de NF Complementar com upload de arquivo"""
    validacao_campos_obrigatorios = {}
    gravar_banco = True
    # Verificar se é requisição de formulário (POST normal) ou AJAX (JSON)
    if request.method == "POST":
        try:
            # Obter dados do formulário
            cliente_id = request.form.get('cliente_id')
            ids_registros = request.form.getlist('ids_registros')
            arquivo_nf = request.files.get('arquivo_nf_complementar')
            
            campos = {
                "cliente_id": ["Cliente", cliente_id],
            }
            
            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

            if not "validado" in validacao_campos_obrigatorios:
                gravar_banco = False
                flash((f"Verifique os campos destacados em vermelho!", "warning"))
                
            if not ids_registros:
                gravar_banco = False
                flash(('Nenhum registro operacional foi selecionado.', 'error'))
                
                
            if not arquivo_nf:
                gravar_banco = False
                flash(('Arquivo da NF Complementar é obrigatório.', 'error'))
                return redirect(url_for('listagem_nf_complementar'))

            if gravar_banco:
                
                # Obter registros operacionais
                registros = RegistroOperacionalModel.query.filter(
                    RegistroOperacionalModel.id.in_(ids_registros)
                ).all()
                
                if not registros:
                    flash('Nenhum registro operacional encontrado com os IDs fornecidos.', 'error')
                    return redirect(url_for('listagem_nf_complementar'))
                
                # Verificar se todos os registros são do mesmo cliente
                clientes_registros = set(reg.solicitacao.cliente.id for reg in registros 
                    if reg.solicitacao and reg.solicitacao.cliente)

                if len(clientes_registros) > 1 or (clientes_registros and int(cliente_id) not in clientes_registros):
                    flash(('Todos os registros devem ser do mesmo cliente selecionado.', 'error'))
                    return redirect(url_for('listagem_nf_complementar'))
                
                # Validar se é PDF
                if arquivo_nf.mimetype != "application/pdf":
                    flash(('Arquivo deve ser um PDF válido.', 'error'))
                    return redirect(url_for('listagem_nf_complementar'))
                
                # Se chegou até aqui, todas as validações básicas passaram. Criar o registro.
                detalhes_registros = []
                for registro in registros:
                    detalhes_registros.append({
                        'registro_id': registro.id,
                        'solicitacao_id': registro.solicitacao_nf_id
                    })
                
                # Salva as informações da NF Complementar
                nf_complementar = NfComplementarModel(
                    cliente_id=int(cliente_id),
                    nf_complementar_detalhes={'registros_operacionais': detalhes_registros},
                    situacao_financeira_id = 2, # Pendente de faturamento
                )
                
                db.session.add(nf_complementar)
                db.session.flush()  # Garante que o ID seja gerado
                
                # Fazer upload do arquivo
                objeto_nf = upload_arquivo(arquivo_nf, "UPLOAD_NOTA_COMPLEMENTAR", f"{nf_complementar.id}")
                
                dados_nota = ExtrairTextoNotaFiscal.nf_extrair_dados_nota(objeto_nf.caminho)
                if (not dados_nota["destinatario"] or not dados_nota["emissor"] or not dados_nota["calculo_imposto"]):
                    flash(("Arquivo enviado não é uma NF válida. Entre em contato com o suporte!", "warning"))
                    db.session.rollback()
                    return redirect(url_for("listagem_nf_complementar"))
                
                dados_nf = RegistroOperacionalModel.extrair_dados_nf_pdf(dados_nota)
                peso_nf = dados_nf["peso_ton_nf"]
                preco_un = dados_nf["preco_un_nf"]
                
                if peso_nf is None or peso_nf < 0 or peso_nf == "":
                    flash(("O peso extraído da nota fiscal é inválido! Entre em contato com o suporte!", "warning"))
                    db.session.rollback()
                    return redirect(url_for("listagem_nf_complementar"))
                
                # Processar dados da NF
                destinatario_data_emissao = dados_nf["destinatario_data_emissao"]
                if destinatario_data_emissao:
                    destinatario_data_emissao = DataHora.converter_data_str_br_em_objeto_date(destinatario_data_emissao)
                valor_total_nota = dados_nf["valor_total_nota_100"]
                if valor_total_nota:
                    valor_total_nota_float = ValoresMonetarios.converter_string_brl_para_float(valor_total_nota)
                    valor_total_nota_100 = valor_total_nota_float * 100
                else:
                    valor_total_nota_100 = None
                    
                nf_complementar.numero_nota_fiscal=dados_nf["numero_nota_fiscal"]
                nf_complementar.serie_nota=dados_nf["serie_nota"]
                nf_complementar.peso_ton_nf = peso_nf
                nf_complementar.chave_acesso=dados_nf["chave_acesso"]
                nf_complementar.destinatario_nome=dados_nf["destinatario_nome"]
                nf_complementar.destinatario_cnpj_cpf=dados_nf["destinatario_cnpj_cpf"]
                nf_complementar.destinatario_insc_estadual=dados_nf["destinatario_insc_estadual"]
                nf_complementar.destinatario_data_emissao=destinatario_data_emissao
                nf_complementar.valor_total_nota_100=valor_total_nota_100
                nf_complementar.preco_un_nf = preco_un
                nf_complementar.transportador_nome=dados_nf["transportador_nome"]
                nf_complementar.transportador_cnpj_cpf=dados_nf["transportador_cnpj_cpf"]
                nf_complementar.transportador_insc_estadual=dados_nf["transportador_insc_estadual"]
                nf_complementar.placa_nf=dados_nf["placa_nf"]
                nf_complementar.motorista_nf=dados_nf["motorista_nf"]
                nf_complementar.arquivo_nota_id=objeto_nf.id

                if nf_complementar and nf_complementar.arquivo_nota_id is not None:
                    # Atualizar status dos registros operacionais
                    for registro in registros:
                        registro.status_emissao_nf_complementar_id = 1
                        # Registrar pontuação
                        PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                            current_user.id,
                            TipoAcaoEnum.CADASTRO,
                            TipoAcaoEnum.CADASTRO.pontos,
                            modulo='marcar_nf_complementar'
                        )
                    db.session.commit()
                    flash((f'NF Complementar {nf_complementar.numero_nota_fiscal} criada com sucesso! ', 'success'))
                else:
                    db.session.rollback()
                    flash(('Erro ao criar NF Complementar. Tente novamente.', 'error'))
        except Exception as e:
            
            db.session.rollback()
            print(f"Erro na emissão de NF Complementar: {str(e)}")
            flash(('Erro inesperado ao processar NF Complementar. Tente novamente.', 'error'))
        return redirect(url_for('listagem_nf_complementar'))