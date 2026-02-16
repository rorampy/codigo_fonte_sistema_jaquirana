from sistema import app, requires_roles, db
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from sistema.models_views.gerenciar.fornecedor.fornecedor_cadastro_model import FornecedorCadastroModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_extrator_model import FornecedorExtratorModel
from sistema.models_views.gerenciar.extrator.extrator_model import ExtratorModel
from sistema._utilitarios import *


# ============================================================
# LISTAGEM - Fornecedores com extratores vinculados
# ============================================================
@app.route("/gerenciar/fornecedor-extratores", methods=["GET"])
@login_required
@requires_roles
def listar_fornecedor_extratores():
    """Lista todos os fornecedores que possuem custo de extração, 
    mostrando seus extratores vinculados."""
    try:
        if any(request.args.values()):
            identificacao = request.args.get("identificacao", "").strip()
            
            fornecedores = FornecedorCadastroModel.query.filter(
                FornecedorCadastroModel.deletado == False,
                FornecedorCadastroModel.custo_extracao == True,
                FornecedorCadastroModel.identificacao.ilike(f"%{identificacao}%") if identificacao else True
            ).order_by(FornecedorCadastroModel.identificacao).all()
        else:
            fornecedores = FornecedorCadastroModel.query.filter(
                FornecedorCadastroModel.deletado == False,
                FornecedorCadastroModel.custo_extracao == True
            ).order_by(FornecedorCadastroModel.identificacao).all()

        # Para cada fornecedor, carregar extratores vinculados
        dados_fornecedores = []
        for f in fornecedores:
            extratores_vinculados = FornecedorExtratorModel.listar_por_fornecedor(f.id)
            nomes_extratores = [ev.extrator.identificacao for ev in extratores_vinculados if ev.extrator]
            dados_fornecedores.append({
                'fornecedor': f,
                'extratores': nomes_extratores,
                'qtd_extratores': len(nomes_extratores)
            })

        return render_template(
            "gerenciar/fornecedores/fornecedor_extratores_listar.html",
            dados_fornecedores=dados_fornecedores,
            dados_corretos=request.args,
        )
    except Exception as e:
        print(e)
        flash(("Erro ao listar fornecedores com extratores!", "warning"))
        return redirect(url_for("listar_fornecedores"))


# ============================================================
# GERENCIAR - Adicionar/remover extratores de um fornecedor
# ============================================================
@app.route("/gerenciar/fornecedor-extratores/<int:fornecedor_id>", methods=["GET", "POST"])
@login_required
@requires_roles
def gerenciar_fornecedor_extratores(fornecedor_id):
    """Tela para gerenciar (adicionar/remover) extratores de um fornecedor específico."""
    try:
        fornecedor = FornecedorCadastroModel.obter_fornecedor_por_id(fornecedor_id)
        if fornecedor is None:
            flash(("Fornecedor não encontrado!", "warning"))
            return redirect(url_for("listar_fornecedor_extratores"))

        extratores_disponiveis = ExtratorModel.listar_extratores_ativos()

        if request.method == "POST":
            extratores_selecionados = request.form.getlist("extratores[]")
            
            try:
                # Desativar vínculos existentes (soft delete)
                vinculos_existentes = FornecedorExtratorModel.listar_por_fornecedor(fornecedor.id)
                for vinculo in vinculos_existentes:
                    vinculo.ativo = False
                    vinculo.deletado = True

                # Criar novos vínculos
                for extrator_id_str in extratores_selecionados:
                    if extrator_id_str and extrator_id_str.strip():
                        extrator_id = int(extrator_id_str)
                        
                        # Verificar se já existe um registro (reativar) ou criar novo
                        vinculo_existente = FornecedorExtratorModel.query.filter(
                            FornecedorExtratorModel.fornecedor_id == fornecedor.id,
                            FornecedorExtratorModel.extrator_id == extrator_id
                        ).first()
                        
                        if vinculo_existente:
                            vinculo_existente.ativo = True
                            vinculo_existente.deletado = False
                        else:
                            novo_vinculo = FornecedorExtratorModel(
                                fornecedor_id=fornecedor.id,
                                extrator_id=extrator_id
                            )
                            db.session.add(novo_vinculo)

                db.session.commit()
                flash(("Extratores do fornecedor atualizados com sucesso!", "success"))
                return redirect(url_for("listar_fornecedor_extratores"))

            except Exception as e:
                db.session.rollback()
                print(e)
                flash(("Erro ao salvar extratores do fornecedor!", "warning"))

        # Carregar extratores já vinculados
        extratores_vinculados = FornecedorExtratorModel.listar_por_fornecedor(fornecedor.id)
        ids_vinculados = [ev.extrator_id for ev in extratores_vinculados]

        return render_template(
            "gerenciar/fornecedores/fornecedor_extratores_gerenciar.html",
            fornecedor=fornecedor,
            extratores=extratores_disponiveis,
            ids_vinculados=ids_vinculados,
        )
    except Exception as e:
        print(e)
        flash(("Erro ao gerenciar extratores do fornecedor!", "warning"))
        return redirect(url_for("listar_fornecedor_extratores"))


# ============================================================
# REMOVER VÍNCULO INDIVIDUAL
# ============================================================
@app.route("/gerenciar/fornecedor-extratores/remover/<int:vinculo_id>", methods=["GET"])
@login_required
@requires_roles
def remover_fornecedor_extrator(vinculo_id):
    """Remove (soft delete) um vínculo específico fornecedor-extrator."""
    try:
        vinculo = FornecedorExtratorModel.obter_por_id(vinculo_id)
        if vinculo is None:
            flash(("Vínculo não encontrado!", "warning"))
            return redirect(url_for("listar_fornecedor_extratores"))

        vinculo.ativo = False
        vinculo.deletado = True
        db.session.commit()
        flash(("Extrator removido do fornecedor com sucesso!", "success"))
        return redirect(url_for("gerenciar_fornecedor_extratores", fornecedor_id=vinculo.fornecedor_id))
    except Exception as e:
        db.session.rollback()
        print(e)
        flash(("Erro ao remover extrator do fornecedor!", "warning"))
        return redirect(url_for("listar_fornecedor_extratores"))


# ============================================================
# API JSON - Extratores por fornecedor (para uso no ticket)
# ============================================================
@app.route("/api/extratores-fornecedor/<int:fornecedor_id>", methods=["GET"])
@login_required
def api_extratores_por_fornecedor(fornecedor_id):
    """Retorna lista de extratores vinculados a um fornecedor em formato JSON.
    Usado pelo formulário de ticket para carregar extratores dinamicamente."""
    try:
        vinculos = FornecedorExtratorModel.listar_por_fornecedor(fornecedor_id)
        extratores = []
        for v in vinculos:
            if v.extrator:
                extratores.append({
                    "id": v.extrator.id,
                    "identificacao": v.extrator.identificacao
                })
        
        return jsonify({"success": True, "extratores": extratores})
    except Exception as e:
        return jsonify({"success": False, "message": "Erro ao buscar extratores", "extratores": []})
