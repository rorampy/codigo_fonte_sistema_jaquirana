from datetime import datetime
from sistema import app, requires_roles, db, current_user, obter_url_absoluta_de_imagem
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.controle_carga.nf_complementar.nf_entrada_model import NfEntradaModel
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema._utilitarios import *


@app.route("/controle-cargas/nf-entrada/listagem", methods=["GET"])
@requires_roles
@login_required
def listagem_nf_entrada():
    try:
        if any(request.args.values()):
            registros = NfEntradaModel.filtrar_nf_entrada_ativas(
                data_inicio=request.args.get('dataInicio'),
                data_fim=request.args.get('dataFim'),
                numero_nf=request.args.get('numeroNf'),
                origem=request.args.get('origemEntrada'),
            )
        else:
            registros = NfEntradaModel.obter_nf_entrada_agrupadas()

    except Exception as e:
        flash(("Não foi possível listar as NFs de entrada! Entre em contato com o suporte!", "warning"))
        print(f"Erro nas listagens de NF de entrada: {e}")
        return redirect(url_for("principal"))

    return render_template(
        "/controle_carga/nf_entrada/listagem_nf_entrada.html",
        registros=registros,
        dados_corretos=request.args,
    )

@app.route(
    "/controle-cargas/nf-entrada/lancar-nf-entrada/<int:id>", methods=["GET", "POST"]
)
@requires_roles
@login_required
def lancar_nf_entrada(id):
    try:
        dados_corretos = request.form
        validacao_campos_obrigatorios = {}
        validacao_campos_erros = {}
        gravar_banco = True

        nfEntrada = NfEntradaModel.obter_nf_entrada(id)
        dataHoje = DataHora.obter_data_atual_padrao_en()

        if not nfEntrada:
            flash(("NF de entrada não encontrada!", "warning"))
            return redirect(url_for("listagem_nf_entrada"))

        if request.method == "POST":
            arquivoNfEntrada = request.files.get("arquivoNfEntrada")
            arquivoContraNota = request.files.get("arquivoContraNota")

            campos = {
                "arquivoNfEntrada": ["Arquivo NF Entrada", arquivoNfEntrada],
                "arquivoContraNota": ["Arquivo Contra Nota", arquivoContraNota],
            }

            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
            if not "validado" in validacao_campos_obrigatorios:
                gravar_banco = False
                flash((f"Verifique os campos destacados em vermelho!", "warning"))

            if gravar_banco == True:
                if arquivoContraNota and arquivoContraNota.filename:
                    if arquivoContraNota.mimetype == "application/pdf":
                        contra = upload_arquivo(
                            arquivoContraNota,
                            "UPLOAD_ARQUIVO_CONTRA_NOTA",
                            f"contra_nota-{nfEntrada.registro_id}_{dataHoje}",
                        )
                        dados_nota = ExtrairTextoNotaFiscal.nf_extrair_dados_nota(
                            contra.caminho
                        )
                        if (
                            not dados_nota["destinatario"]
                            or not dados_nota["emissor"]
                            or not dados_nota["calculo_imposto"]
                        ):
                            flash(
                                (
                                    "Arquivo enviado não é uma NF válida. Entre em contato com o suporte!",
                                    "warning",
                                )
                            )
                            gravar_banco = False
                        else:
                            peso_contra_nota = 0
                            itens_nf = dados_nota['itens']
                            for i in itens_nf:
                                if ',' in i['quantidade']:
                                    partes = i['quantidade'].split(',')
                                    quantidade_str = partes[0].replace('.', '') + '.' + partes[1]
                                else:
                                    quantidade_str = i['quantidade'].replace('.', '')
                                peso_contra_nota += round(float(quantidade_str), 2)

                            if itens_nf == []:
                                flash(("Houve um erro ao lançar peso da contra nota! Entre em contato com o suporte.","warning",))
                                gravar_banco = False
                    else:
                        flash(
                            (
                                "O arquivo da contra nota deve estar em formato PDF.",
                                "warning",
                            )
                        )
                        gravar_banco = False
                else:
                    flash(("Envie a contra-nota antes de lançar.", "warning"))
                    gravar_banco = False

            if gravar_banco:
                if arquivoNfEntrada and arquivoNfEntrada.filename:
                    if arquivoNfEntrada.mimetype in [
                        "image/jpeg",
                        "image/png",
                        "application/pdf",
                    ]:
                        entrada = upload_arquivo(
                            arquivoNfEntrada,
                            "UPLOAD_ARQUIVO_NF_ENTRADA",
                            f"nf_entrada-{nfEntrada.registro_id}_{dataHoje}",
                        )
                    else:
                        flash(
                            (
                                "O arquivo da NF de Entrada deve estar em formato PDF, PNG ou JPG.",
                                "warning",
                            )
                        )
                        gravar_banco = False
                else:
                    flash(("Envie a NF de entrada.", "warning"))
                    gravar_banco = False

            if gravar_banco:
                nfEntrada.arquivo_contra_nota_id = contra.id
                nfEntrada.peso_contra_nota = peso_contra_nota
                nfEntrada.arquivo_nf_entrada_id = entrada.id

                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    TipoAcaoEnum.CADASTRO,
                    TipoAcaoEnum.CADASTRO.pontos,
                    modulo="lancamento_contra_nota",
                )
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    TipoAcaoEnum.CADASTRO,
                    TipoAcaoEnum.CADASTRO.pontos,
                    modulo="lancamento_nf_entrada",
                )

                db.session.commit()
                flash(
                    ("Lançamento de NFs de entrada executado com sucesso!", "success")
                )
                return redirect(url_for("listagem_nf_entrada"))
            else:
                db.session.rollback()

    except Exception as e:
        print(e)
        db.session.rollback()
        flash(
            (
                "Erro ao efetuar upload de arquivo! Entre em contato com o suporte.",
                "warning",
            )
        )
        return redirect(url_for("listagem_nf_entrada"))

    return render_template(
        "/controle_carga/nf_entrada/cadastrar_nf_entrada.html",
        nfEntrada=nfEntrada,
        dados_corretos=dados_corretos,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
    )


@app.route("/controle-cargas/nf-entrada/lancar-cte/<int:id>", methods=["GET", "POST"])
@requires_roles
@login_required
def lancar_cte(id):
    try:
        dados_corretos = request.form
        validacao_campos_obrigatorios = {}
        validacao_campos_erros = {}
        gravar_banco = True

        nfEntrada = NfEntradaModel.obter_nf_entrada(id)
        dataHoje = DataHora.obter_data_atual_padrao_en()

        if not nfEntrada:
            flash(("NF de entrada não encontrada!", "warning"))
            return redirect(url_for("listagem_nf_entrada"))

        if request.method == "POST":
            arquivoCTE = request.files.get("arquivoCTE")

            campos = {
                "arquivoCTE": ["Arquivo CTE", arquivoCTE],
            }

            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

            if not "validado" in validacao_campos_obrigatorios:
                gravar_banco = False
                flash((f"Verifique os campos destacados em vermelho!", "warning"))

            if gravar_banco == True:

                if arquivoCTE and arquivoCTE.filename:
                    if arquivoCTE.mimetype in ["application/pdf"]:
                        arquivo = upload_arquivo(
                            arquivoCTE,
                            "UPLOAD_ARQUIVO_CTE",
                            f"arquivo_CTE-{nfEntrada.registro_id}_{dataHoje}",
                        )
                        nfEntrada.arquivo_cte_id = arquivo.id
                        acao = TipoAcaoEnum.CADASTRO
                        PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                            current_user.id, acao, acao.pontos, modulo="lancamento_cte"
                        )
                    else:
                        flash(("O arquivo CTE deve estar em formato PDF", "warning"))
                        return redirect(url_for("lancar_cte", id=nfEntrada.id))

                db.session.commit()
                flash(("Lançamento de CTE executado com sucesso!", "success"))
                return redirect(url_for("listagem_nf_entrada"))

    except Exception as e:
        flash(
            (
                "Erro ao efetuar upload de arquivo! Entre em contato com o suporte",
                "warning",
            )
        )
        print(e)
        return redirect(url_for("listagem_nf_entrada"))

    return render_template(
        "/controle_carga/nf_entrada/cadastrar_cte.html",
        nfEntrada=nfEntrada,
        dados_corretos=dados_corretos,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
    )


@app.route("/controle-cargas/nf-entrada/lancar-mdf/<int:id>", methods=["GET", "POST"])
@requires_roles
@login_required
def lancar_mdf(id):
    try:
        dados_corretos = request.form
        validacao_campos_obrigatorios = {}
        validacao_campos_erros = {}
        gravar_banco = True

        nfEntrada = NfEntradaModel.obter_nf_entrada(id)
        dataHoje = DataHora.obter_data_atual_padrao_en()

        if not nfEntrada:
            flash(("NF de entrada não encontrada!", "warning"))
            return redirect(url_for("listagem_nf_entrada"))

        if request.method == "POST":
            arquivoMDF = request.files.get("arquivoMDF")

            campos = {
                "arquivoMDF": ["Arquivo MDF", arquivoMDF],
            }

            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

            if not "validado" in validacao_campos_obrigatorios:
                gravar_banco = False
                flash((f"Verifique os campos destacados em vermelho!", "warning"))

            if gravar_banco == True:

                if arquivoMDF and arquivoMDF.filename:
                    if arquivoMDF.mimetype in ["application/pdf"]:
                        arquivo = upload_arquivo(
                            arquivoMDF,
                            "UPLOAD_ARQUIVO_MDF",
                            f"arquivo_MDF-{nfEntrada.registro_id}_{dataHoje}",
                        )
                        nfEntrada.arquivo_mdf_id = arquivo.id
                        acao = TipoAcaoEnum.CADASTRO
                        PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                            current_user.id, acao, acao.pontos, modulo="lancamento_mdf"
                        )
                    else:
                        flash(("O arquivo MDF deve estar em formato PDF", "warning"))
                        return redirect(url_for("lancar_mdf", id=nfEntrada.id))

                db.session.commit()
                flash(("Lançamento de MDF executado com sucesso!", "success"))
                return redirect(url_for("listagem_nf_entrada"))

    except Exception as e:
        flash(
            (
                "Erro ao efetuar upload de arquivo! Entre em contato com o suporte",
                "warning",
            )
        )
        print(e)
        return redirect(url_for("listagem_nf_entrada"))

    return render_template(
        "/controle_carga/nf_entrada/cadastrar_mdf.html",
        nfEntrada=nfEntrada,
        dados_corretos=dados_corretos,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
    )
