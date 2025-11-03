from sistema import app, db, requires_roles, current_user
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required
from sistema.models_views.configuracoes_gerais.empresa_emissora.empresa_emissora_model import EmpresaEmissoraModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema._utilitarios import *


@app.route("/configuracoes/gerais/empresa-emissora/listar", methods=["GET", "POST"])
@login_required
@requires_roles
def listar_empresa_emissora():
    empresa_emissora = EmpresaEmissoraModel.obter_empresas_emissoras_ativas()

    return render_template(
        "configuracoes_gerais/empresa_emissora/empresa_emissora_listar.html",
        empresa_emissora=empresa_emissora, dados_corretos=request.form
    )


@app.route("/configuracoes/gerais/empresa-emissora/cadastrar", methods=["GET", "POST"])
@login_required
@requires_roles
def cadastrar_empresa_emissora():
    try:
        usuarioId= current_user.id
        validacao_campos_obrigatorios = {}
        validacao_campos_erros = {}
        gravar_banco = True

        if request.method == "POST":
            razaoSocial = request.form["razaoSocial"]
            cnpj = request.form["cnpj"]
            
            campos = {
                "razaoSocial": ["Razão Social", razaoSocial],
                "cnpj": ["CNPJ", cnpj]
            }

            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

            if not "validado" in validacao_campos_obrigatorios:
                gravar_banco = False
                flash((f"Verifique os campos destacados em vermelho!", "warning"))

            verificacao_cnpj = ValidaForms.validar_cnpj(cnpj)
            if not "validado" in verificacao_cnpj:
                gravar_banco = False
                validacao_campos_erros.update(verificacao_cnpj)

            cnpj_tratado = ValidaDocs.remove_pontuacao_cnpj(cnpj)
            pesquisa_cnpj_banco = EmpresaEmissoraModel.query.filter(
                EmpresaEmissoraModel.numero_documento == cnpj_tratado, 
                EmpresaEmissoraModel.ativo == True,
                EmpresaEmissoraModel.deletado == False
            ).first()
            if pesquisa_cnpj_banco:
                gravar_banco = False
                validacao_campos_erros["cnpj"] = (
                    f"O CNPJ informado já existe no banco de dados!"
                )

            if gravar_banco == True:

                empresa_emissora = EmpresaEmissoraModel(
                    identificacao=razaoSocial,
                    numero_documento=cnpj_tratado,
                    ativo=True
                )
                db.session.add(empresa_emissora)
                db.session.commit()

                acao = TipoAcaoEnum.CADASTRO

                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    usuarioId,
                    acao,
                    acao.pontos,
                    modulo='empresa_emissora'
                )

                flash(("Empresa cadastrada com sucesso!", "success"))
                return redirect(url_for("listar_empresa_emissora"))
    except Exception as e:
        flash(("Erro ao cadastrar empresa! Entre em contato com o suporte!", "warning"))
        return redirect(url_for("listar_empresa_emissora"))

    return render_template(
        "configuracoes_gerais/empresa_emissora/empresa_emissora_cadastrar.html",
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
    )

@app.route("/configuracoes/gerais/empresa-emissora/editar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_empresa_emissora(id):
    try:
        usuarioId= current_user.id
        validacao_campos_obrigatorios = {}
        validacao_campos_erros = {}
        gravar_banco = True

        empresa = EmpresaEmissoraModel.obter_empresa_emissora_por_id(id)

        if not empresa:
            flash(('Empresa não encontrada!', 'warning'))
            return redirect(url_for('listar_empresa_emissora'))
        
        dados_corretos = {
            "razaoSocial": empresa.identificacao,
            "cnpj": empresa.numero_documento
        }

        if request.method == "POST":
            razaoSocial = request.form["razaoSocial"]
            cnpj = request.form["cnpj"]
            
            campos = {
                "razaoSocial": ["Razão Social", razaoSocial],
                "cnpj": ["CNPJ", cnpj]
            }

            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

            if not "validado" in validacao_campos_obrigatorios:
                gravar_banco = False
                flash((f"Verifique os campos destacados em vermelho!", "warning"))

            verificacao_cnpj = ValidaForms.validar_cnpj(cnpj)
            if not "validado" in verificacao_cnpj:
                gravar_banco = False
                validacao_campos_erros.update(verificacao_cnpj)

            cnpj_tratado = ValidaDocs.remove_pontuacao_cnpj(cnpj)

            if empresa.numero_documento != cnpj_tratado:
                pesquisa_cnpj_banco = EmpresaEmissoraModel.query.filter(
                    EmpresaEmissoraModel.numero_documento == cnpj_tratado, 
                    EmpresaEmissoraModel.ativo == True,
                    EmpresaEmissoraModel.deletado == False
                ).first()
                if pesquisa_cnpj_banco:
                    gravar_banco = False
                    validacao_campos_erros["cnpj"] = (
                        f"O CNPJ informado já existe no banco de dados!"
                    )

            if gravar_banco == True:

                empresa.identificacao=razaoSocial,
                empresa.numero_documento=cnpj_tratado,
                
                db.session.commit()

                acao = TipoAcaoEnum.EDICAO

                PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                    usuarioId,
                    acao,
                    acao.pontos,
                    modulo='empresa_emissora'
                )

                flash(("Empresa editada com sucesso!", "success"))
                return redirect(url_for("listar_empresa_emissora"))
            
    except Exception as e:
        flash(("Erro ao editar empresa! Entre em contato com o suporte!", "warning"))
        return redirect(url_for("editar_empresa_emissora", id=id))

    return render_template(
        "configuracoes_gerais/empresa_emissora/empresa_emissora_editar.html",
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        empresa=empresa,
        dados_corretos=dados_corretos,
    )

@app.route("/configuracoes/gerais/empresa-emissora/excluir/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def excluir_empresa_emissora(id):
    try:
        empresa = EmpresaEmissoraModel.obter_empresa_emissora_por_id(id)

        if not empresa:
            flash(('Empresa não encontrada!', 'warning'))
            return redirect(url_for('listar_empresa_emissora'))
        
        empresa.ativo = False
        empresa.deletado = True

        db.session.commit()

        flash(('Empresa excluída com sucesso!', 'success'))
        return redirect(url_for('listar_empresa_emissora'))    
    except Exception as e:
        flash(('Erro ao tentar excluir empresa! Entre em contato com o suporte!', 'warning'))
        return redirect(url_for('listar_empresa_emissora'))    
