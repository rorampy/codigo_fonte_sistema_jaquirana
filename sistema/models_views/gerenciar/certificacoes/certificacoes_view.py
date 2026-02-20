from sistema import app, db, requires_roles, current_user
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from .certificacoes_model import CertificacoesModel, CertificacaoAnexoModel
from sistema._utilitarios import *

@app.route("/gerenciar/certificacoes", methods=["GET"])
@login_required
@requires_roles
def listar_certificacoes():
    if any(request.args.values()):
        certificacoes = CertificacoesModel.filtrar_certificacoes(
            nome=request.args.get('nome'),
            descricao=request.args.get('descricao')
        )
    else:
        certificacoes = CertificacoesModel.listar_certificacoes()
    
    return render_template(
        "gerenciar/certificacoes/certificacao_listar.html",
        certificacoes=certificacoes,
        dados_corretos=request.args
    )

@app.route("/gerenciar/certificacao/cadastrar", methods=["GET", "POST"])
@login_required
@requires_roles
def cadastrar_certificacao():
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    if request.method == "POST":
        nome = request.form["nome"]
        descricao = request.form["descricao"]
        descricao_nota = request.form["descricao_nota"]
        valor_estoque = request.form.get("valor_estoque", "").strip()
        
        campos = {
            "nome": ["Nome", nome],
            "valor_estoque": ["Estoque (Toneladas)", valor_estoque]
        }

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash(("Verifique os campos destacados em vermelho!", "warning"))

        valor_estoque_float = None
        try:
            if valor_estoque:
                valor_limpo = valor_estoque.replace(',', '.').strip()
                
                if not valor_limpo:
                    raise ValueError("Valor vazio")
                
                valor_estoque_float = float(valor_limpo)
                
                import math
                if math.isnan(valor_estoque_float):
                    raise ValueError("Valor inválido (NaN)")
                
                if math.isinf(valor_estoque_float):
                    raise ValueError("Valor inválido (infinito)")
                
                if valor_estoque_float < 0:
                    raise ValueError("Valor não pode ser negativo")
                
                if valor_estoque_float > 999999.99:
                    raise ValueError("Valor muito alto (máximo: 999.999,99 toneladas)")
                    
                valor_estoque_float = round(valor_estoque_float, 2)
                
            else:
                valor_estoque_float = 0.0
                
        except (ValueError, TypeError, AttributeError) as e:
            gravar_banco = False
            validacao_campos_erros["valor_estoque"] = "Estoque inválido. Use apenas números (ex: 25.5 ou 25,5)"
            valor_estoque_float = None

        if gravar_banco and valor_estoque_float is not None:
            try:
                certificacao = CertificacoesModel(
                    nome=nome,
                    descricao=descricao if descricao else None,
                    descricao_nota=descricao_nota if descricao_nota else None,
                    valor_estoque_inicial=valor_estoque_float,
                    valor_estoque_atual=valor_estoque_float,
                    ativo=True
                )
                db.session.add(certificacao)
                db.session.flush()

                anexos = request.files.getlist('anexos')
                anexos_validos = [anexo for anexo in anexos if anexo and anexo.filename != '']

                if anexos_validos:
                    for i, anexo in enumerate(anexos_validos):
                        try:
                            nome_arquivo = f"anexo_cert_{certificacao.id}_{i+1}"
                            objeto_upload = upload_arquivo(
                                anexo, 
                                "UPLOAD_ESTOQUE_CERTIFICACOES",
                                nome_arquivo
                            )
                            
                            certificacao_anexo = CertificacaoAnexoModel(
                                certificacao_id=certificacao.id,
                                arquivo_upload_id=objeto_upload.id,
                                descricao_anexo=request.form.get(f'descricao_anexo_{i}', f'Anexo {i+1}'),
                                ordem_exibicao=i+1
                            )
                            db.session.add(certificacao_anexo)
                            
                        except Exception as e:
                            flash((f"Erro ao fazer upload do arquivo {anexo.filename}: {str(e)}", "warning"))
                            continue
                
                db.session.commit()

                acao = TipoAcaoEnum.CADASTRO
                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    current_user.id,
                    acao,
                    acao.pontos,
                    modulo='certificacao'
                )
                
                flash(("Certificação cadastrada com sucesso!", "success"))
                return redirect(url_for("listar_certificacoes"))
                
            except Exception as e:
                db.session.rollback()
                flash((f"Erro ao salvar certificação: {str(e)}", "error"))
                gravar_banco = False

    return render_template(
        "gerenciar/certificacoes/certificacao_cadastrar.html",
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form
    )

@app.route("/gerenciar/certificacao/editar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_certificacao(id):
    certificacao = CertificacoesModel.query.filter_by(id=id).first()

    if certificacao is None:
        flash(("Certificação não encontrada", "warning"))
        return redirect(url_for("listar_certificacoes"))
    
    if certificacao.ativo == False:
        flash(("Esta certificação está desativada e, por isso, não pode ser editada.", "warning"))
        return redirect(url_for("listar_certificacoes"))

    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    dados_corretos = {
        "nome": certificacao.nome or "",
        "descricao": certificacao.descricao or "",
        "descricao_nota": certificacao.descricao_nota or "",
        "valor_estoque": certificacao.valor_estoque_atual or "",
    }

    if request.method == "POST":
        nome = request.form["nome"]
        descricao = request.form["descricao"]
        descricao_nota = request.form["descricao_nota"]
        valor_estoque = request.form["valor_estoque"]
        
        campos = {
            "nome": ["Nome", nome],
            "valor_estoque": ["Valor do Estoque", valor_estoque]
        }

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash(("Verifique os campos destacados em vermelho!", "warning"))

        try:
            valor_estoque_float = float(valor_estoque.replace(',', '.'))
        except (ValueError, AttributeError):
            gravar_banco = False
            validacao_campos_erros["valor_estoque"] = "Valor de estoque inválido."

        if gravar_banco:
            certificacao.nome = nome
            certificacao.descricao = descricao if descricao else None
            certificacao.descricao_nota = descricao_nota if descricao_nota else None
            certificacao.valor_estoque_inicial = valor_estoque_float
            certificacao.valor_estoque_atual = valor_estoque_float

            db.session.commit()

            anexos = request.files.getlist('anexos')
            if anexos:
                anexos_existentes = len(certificacao.obter_anexos_ativos())
                
                for i, anexo in enumerate(anexos):
                    if anexo and anexo.filename != '':
                        try:
                            objeto_upload = upload_arquivo(
                                anexo, 
                                "UPLOAD_ESTOQUE_CERTIFICACOES", 
                                f"cert_{certificacao.id}_anexo_{anexos_existentes + i + 1}_{anexo.filename}"
                            )
                            
                            certificacao_anexo = CertificacaoAnexoModel(
                                certificacao_id=certificacao.id,
                                arquivo_upload_id=objeto_upload.id,
                                descricao_anexo=request.form.get(f'descricao_anexo_{i}', f'Anexo {anexos_existentes + i + 1}'),
                                ordem_exibicao=anexos_existentes + i + 1
                            )
                            db.session.add(certificacao_anexo)
                            
                        except Exception as e:
                            flash((f"Erro ao fazer upload do arquivo {anexo.filename}: {str(e)}", "warning"))
                            continue
                
                db.session.commit()

            flash(("Certificação editada com sucesso!", "success"))
            return redirect(url_for("listar_certificacoes"))
        else:
            dados_corretos = request.form

    return render_template(
        "gerenciar/certificacoes/certificacao_editar.html",
        certificacao=certificacao,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=dados_corretos
    )

@app.route("/gerenciar/certificacao/detalhes/<int:id>")
@login_required
@requires_roles
def detalhes_certificacao(id):
    """Visualizar detalhes da certificação com todos os anexos"""
    certificacao = CertificacoesModel.query.filter_by(id=id).first()

    if not certificacao:
        flash(("Certificação não encontrada!", "warning"))
        return redirect(url_for("listar_certificacoes"))
    
    anexos = sorted(certificacao.obter_anexos_ativos(), key=lambda x: x.ordem_exibicao)
    
    return render_template(
        "gerenciar/certificacoes/certificacao_detalhes.html", 
        certificacao=certificacao, 
        anexos=anexos
    )

@app.route("/gerenciar/certificacao/excluir/<int:id>")
@login_required
@requires_roles
def excluir_certificacao(id):
    """Exclusão lógica de certificação"""
    certificacao = CertificacoesModel.obter_certificacao_por_id(id)

    if certificacao is None:
        flash(("Certificação não encontrada", "warning"))
    else:
        certificacao.deletado = True
        certificacao.ativo = False
        db.session.commit()
        flash(("Certificação excluída com sucesso!", "success"))
    
    return redirect(url_for("listar_certificacoes"))

@app.route("/gerenciar/certificacao/desativar/<int:id>")
@login_required
@requires_roles
def desativar_certificacao(id):
    certificacao = CertificacoesModel.obter_certificacao_por_id(id)

    if certificacao is None:
        flash(("Certificação não encontrada", "warning"))
    else:
        certificacao.ativo = False
        db.session.commit()
        flash(("Certificação desativada com sucesso!", "success"))
    
    return redirect(url_for("listar_certificacoes"))

@app.route("/gerenciar/certificacao/ativar/<int:id>")
@login_required
@requires_roles
def ativar_certificacao(id):
    certificacao = CertificacoesModel.obter_certificacao_inativa_por_id(id)
    if certificacao is None:
        flash(("Certificação não encontrada", "warning"))
    else:
        certificacao.ativo = True
        db.session.commit()
        flash(("Certificação ativada com sucesso!", "success"))
    
    return redirect(url_for("listar_certificacoes"))

@app.route("/gerenciar/certificacao/excluir_anexo/<int:anexo_id>")
@login_required
@requires_roles
def excluir_anexo_certificacao(anexo_id):
    """Exclusão lógica de anexo específico - CADA ANEXO É INDEPENDENTE"""
    try:
        anexo = CertificacaoAnexoModel.obter_anexo_por_id(anexo_id)
        if anexo:
            anexo.excluir_anexo()  
            flash(("Anexo excluído com sucesso!", "success"))
        else:
            flash(("Anexo não encontrado!", "warning"))
    except Exception as e:
        flash((f"Erro ao excluir anexo: {str(e)}", "error"))
    
    return redirect(request.referrer)
