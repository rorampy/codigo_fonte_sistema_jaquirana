from sistema import app, db, requires_roles, current_user
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal.categorizacao_fiscal_model import CategorizacaoFiscalModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import (
    PontuacaoUsuarioModel,
)
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema._utilitarios import *


@app.route("/configuracoes/gerais/categorizacao-fiscal/listar", methods=["GET", "POST"])
@login_required
@requires_roles
def listar_categorizacao_fiscal():
    try:
        # Inicializar categorias padrão se não existirem
        inicializar_categorias_padrao_categorizacao_fiscal()

        # Buscar categorias principais
        categorias_principais = CategorizacaoFiscalModel.buscar_principais()

        # Montar estrutura hierárquica
        estrutura = []
        for categoria in categorias_principais:
            categoria_dict = categoria.to_dict()
            categoria_dict["children"] = obter_subcategorias_recursivo_categorizacao_fiscal(categoria.id)
            estrutura.append(categoria_dict)

        return render_template(
            "configuracoes_gerais/categorizacao_fiscal/categorizacao_fiscal.html", estrutura=estrutura
        )

    except Exception as e:
        flash((f"Erro ao carregar plano de contas: {str(e)}", "error"))
        return render_template(
            "configuracoes_gerais/categorizacao_fiscal/categorizacao_fiscal.html", estrutura=[]
        )


@app.route("/configuracoes/gerais/categorizacao-fiscal/criar", methods=["POST"])
@login_required
@requires_roles
def criar_subcategoria_categorizacao_fiscal():
    try:
        data = request.get_json()
        parent_code = data.get("parent_code")
        nome = data.get("nome", "").strip()

        if not nome:
            return jsonify({"erro": "Nome é obrigatório"}), 400

        if not parent_code:
            return jsonify({"erro": "Código pai é obrigatório"}), 400

        # Buscar categoria pai (apenas ativas)
        categoria_pai = CategorizacaoFiscalModel.buscar_por_codigo(parent_code)
        if not categoria_pai:
            return jsonify({"erro": "Categoria pai não encontrada ou inativa"}), 404

        # Gerar próximo código (agora considera apenas registros ativos)
        novo_codigo = CategorizacaoFiscalModel.gerar_proximo_codigo(parent_code)
        if not novo_codigo:
            return jsonify({"erro": "Não foi possível gerar código"}), 400

        # Calcular nível
        nivel = novo_codigo.count(".") + 1

        # ✅ VERIFICAÇÃO ADICIONAL: Se código já existe ativo
        if not CategorizacaoFiscalModel.verificar_codigo_disponivel(novo_codigo):
            # Tentar gerar um código alternativo
            for tentativa in range(1, 100):  # Máximo 99 tentativas
                codigo_alternativo = CategorizacaoFiscalModel.gerar_proximo_codigo(parent_code)
                if CategorizacaoFiscalModel.verificar_codigo_disponivel(codigo_alternativo):
                    novo_codigo = codigo_alternativo
                    break
            else:
                return jsonify({"erro": "Não foi possível gerar código único"}), 400

        # ✅ TRATAMENTO INTELIGENTE: Reativar se existir inativo ou criar novo
        categoria_inativa = CategorizacaoFiscalModel.query.filter_by(
            codigo=novo_codigo, 
            ativo=False
        ).first()
        
        if categoria_inativa:
            # Reativar categoria existente
            categoria_inativa.nome = nome
            categoria_inativa.tipo = categoria_pai.tipo
            categoria_inativa.parent_id = categoria_pai.id
            categoria_inativa.nivel = nivel
            categoria_inativa.ativo = True
            
            nova_categoria = categoria_inativa
            action_message = "reativada"
        else:
            # Criar nova categoria
            nova_categoria = CategorizacaoFiscalModel(
                codigo=novo_codigo,
                nome=nome,
                tipo=categoria_pai.tipo,
                parent_id=categoria_pai.id,
                nivel=nivel,
            )
            db.session.add(nova_categoria)
            action_message = "criada"

        db.session.commit()

        # Registrar pontuação do usuário
        try:
            PontuacaoUsuarioModel.registrar_acao(
                usuario_id=current_user.id,
                tipo_acao=TipoAcaoEnum.CADASTRO,
                detalhes=f"Subcategoria {action_message}: {nome} ({novo_codigo})",
            )
        except:
            pass  # Não falhar se pontuação der erro

        return jsonify(
            {
                "sucesso": True,
                "categoria": nova_categoria.to_dict(),
                "mensagem": f'Subcategoria "{nome}" {action_message} com sucesso! (Código: {novo_codigo})',
            }
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500

@app.route("/configuracoes/gerais/categorizacao-fiscal/inativos", methods=["GET"])
@login_required
@requires_roles
def listar_categorias_categorizacao_fiscal_inativas():
    """Lista categorias inativas para debug/administração"""
    try:
        categorias_inativas = CategorizacaoFiscalModel.query.filter_by(ativo=False).order_by(CategorizacaoFiscalModel.codigo).all()
        
        lista_inativas = []
        for cat in categorias_inativas:
            lista_inativas.append({
                'id': cat.id,
                'codigo': cat.codigo,
                'nome': cat.nome,
                'tipo': cat.tipo,
                'nivel': cat.nivel,
                'parent_id': cat.parent_id
            })
        
        return jsonify({
            'categorias_inativas': lista_inativas,
            'total': len(lista_inativas)
        })
        
    except Exception as e:
        return jsonify({"erro": f"Erro ao listar inativos: {str(e)}"}), 500

# ✅ ROTA ADICIONAL: Para reativar categoria específica
@app.route("/configuracoes/gerais/categorizacao-fiscal/reativar/<int:categoria_id>", methods=["POST"])
@login_required
@requires_roles
def reativar_categoria_categorizacao_fiscal(categoria_id):
    """Reativa uma categoria que foi excluída"""
    try:
        categoria = CategorizacaoFiscalModel.query.get_or_404(categoria_id)
        
        if categoria.ativo:
            return jsonify({"erro": "Categoria já está ativa"}), 400
        
        # Verificar se código não conflita com categoria ativa
        conflito = CategorizacaoFiscalModel.query.filter_by(
            codigo=categoria.codigo,
            ativo=True
        ).first()
        
        if conflito:
            return jsonify({
                "erro": f"Não é possível reativar: código {categoria.codigo} já está em uso"
            }), 400
        
        # Reativar
        categoria.ativo = True
        db.session.commit()
        
        # Registrar pontuação
        try:
            PontuacaoUsuarioModel.registrar_acao(
                usuario_id=current_user.id,
                tipo_acao=TipoAcaoEnum.EDICAO,
                detalhes=f"Reativou categoria: {categoria.nome} ({categoria.codigo})",
            )
        except:
            pass
        
        return jsonify({
            "sucesso": True,
            "categoria": categoria.to_dict(),
            "mensagem": f"Categoria '{categoria.nome}' reativada com sucesso!"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao reativar: {str(e)}"}), 500

@app.route(
    "/configuracoes/gerais/categorizacao-fiscal/editar/<int:categoria_id>", methods=["PUT"]
)
@login_required
@requires_roles
def editar_categoria_categorizacao_fiscal(categoria_id):
    try:
        categoria = CategorizacaoFiscalModel.query.get_or_404(categoria_id)
        data = request.get_json()
        novo_nome = data.get("nome", "").strip()

        if not novo_nome:
            return jsonify({"erro": "Nome é obrigatório"}), 400

        nome_anterior = categoria.nome
        categoria.nome = novo_nome
        db.session.commit()

        # Registrar pontuação
        try:
            PontuacaoUsuarioModel.registrar_acao(
                usuario_id=current_user.id,
                tipo_acao=TipoAcaoEnum.EDICAO,
                detalhes=f"Editou categoria: {nome_anterior} -> {novo_nome}",
            )
        except:
            pass

        return jsonify(
            {
                "sucesso": True,
                "categoria": categoria.to_dict(),
                "mensagem": "Categoria atualizada com sucesso!",
            }
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao atualizar: {str(e)}"}), 500


@app.route(
    "/configuracoes/gerais/categorizacao-fiscal/excluir/<int:categoria_id>", methods=["DELETE"]
)
@login_required
@requires_roles
def excluir_categoria_categorizacao_fiscal(categoria_id):
    try:
        categoria = CategorizacaoFiscalModel.query.get_or_404(categoria_id)

        # Verificar se tem subcategorias ativas
        filhos = categoria.get_children_ordenados()
        if filhos:
            return (
                jsonify(
                    {
                        "erro": "Não é possível excluir categoria que possui subcategorias ativas"
                    }
                ),
                400,
            )

        # Soft delete
        nome_categoria = categoria.nome
        categoria.ativo = False
        db.session.commit()

        # Registrar pontuação
        try:
            PontuacaoUsuarioModel.registrar_acao(
                usuario_id=current_user.id,
                tipo_acao=TipoAcaoEnum.EXCLUSAO,
                detalhes=f"Excluiu categoria: {nome_categoria}",
            )
        except:
            pass

        return jsonify(
            {
                "sucesso": True,
                "mensagem": f'Categoria "{nome_categoria}" excluída com sucesso!',
            }
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao excluir: {str(e)}"}), 500


@app.route("/configuracoes/gerais/categorizacao-fiscal/api/estrutura", methods=["GET"])
@login_required
@requires_roles
def api_estrutura_plano_contas_categorizacao_fiscal():
    try:
        categorias_principais = CategorizacaoFiscalModel.buscar_principais()
        estrutura = []

        for categoria in categorias_principais:
            categoria_dict = categoria.to_dict()
            categoria_dict["children"] = obter_subcategorias_recursivo_categorizacao_fiscal(categoria.id)
            estrutura.append(categoria_dict)

        return jsonify({"estrutura": estrutura})

    except Exception as e:
        return jsonify({"erro": f"Erro ao carregar estrutura: {str(e)}"}), 500


def inicializar_categorias_padrao_categorizacao_fiscal():
    """Inicializa as categorias padrão se não existirem (considera apenas ativas)"""
    categorias_padrao = [
        ("1", "Geral", 1)
    ]

    for codigo, nome, tipo in categorias_padrao:
        # Verificar se existe categoria ativa
        existe_ativa = CategorizacaoFiscalModel.buscar_por_codigo(codigo)
        if not existe_ativa:
            # Verificar se existe inativa para reativar
            categoria_inativa = CategorizacaoFiscalModel.query.filter_by(
                codigo=codigo,
                ativo=False
            ).first()
            
            if categoria_inativa:
                # Reativar
                categoria_inativa.nome = nome
                categoria_inativa.tipo = tipo
                categoria_inativa.ativo = True
            else:
                # Criar nova
                categoria = CategorizacaoFiscalModel(
                    codigo=codigo, 
                    nome=nome, 
                    tipo=tipo, 
                    nivel=1
                )
                db.session.add(categoria)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao inicializar categorias padrão: {str(e)}")


def obter_subcategorias_recursivo_categorizacao_fiscal(parent_id):
    """Obtém subcategorias de forma recursiva"""
    subcategorias = CategorizacaoFiscalModel.buscar_filhos(parent_id)
    resultado = []

    for sub in subcategorias:
        sub_dict = sub.to_dict()
        sub_dict["children"] = obter_subcategorias_recursivo_categorizacao_fiscal(sub.id)
        resultado.append(sub_dict)

    return resultado

def limpar_codigos_orfaos():
    """
    Remove registros órfãos que podem estar causando conflitos
    USE COM CUIDADO - apenas para limpeza de dados
    """
    try:
        # Buscar registros inativo que não têm pai válido
        orfaos = CategorizacaoFiscalModel.query.filter(
            CategorizacaoFiscalModel.ativo == False,
            CategorizacaoFiscalModel.parent_id.isnot(None)
        ).all()
        
        removidos = []
        for orfao in orfaos:
            # Verificar se pai ainda existe e está ativo
            pai = CategorizacaoFiscalModel.query.filter_by(
                id=orfao.parent_id,
                ativo=True
            ).first()
            
            if not pai:
                removidos.append(f"{orfao.codigo} - {orfao.nome}")
                db.session.delete(orfao)  # Delete definitivo para órfãos
        
        db.session.commit()
        return removidos
        
    except Exception as e:
        db.session.rollback()
        raise


# ========================================
# VERSÃO ALTERNATIVA COM MAIS TRATAMENTO DE FLASH
# ========================================

# Se você quiser adicionar mais mensagens flash no processo:

@app.route("/configuracoes/gerais/categorizacao-fiscal/criar-com-flash", methods=["POST"])
@login_required
@requires_roles
def criar_subcategoria_com_flash_categorizacao_fiscal():
    """Versão alternativa que usa flash messages em vez de JSON"""
    try:
        parent_code = request.form.get("parent_code")
        nome = request.form.get("nome", "").strip()

        if not nome:
            flash(("Nome é obrigatório", "error"))
            return redirect(url_for("listar_categorizacao_fiscal"))

        if not parent_code:
            flash(("Código pai é obrigatório", "error"))
            return redirect(url_for("listar_categorizacao_fiscal"))

        # Buscar categoria pai
        categoria_pai = CategorizacaoFiscalModel.buscar_por_codigo(parent_code)
        if not categoria_pai:
            flash(("Categoria pai não encontrada", "error"))
            return redirect(url_for("listar_categorizacao_fiscal"))

        # Gerar próximo código
        novo_codigo = CategorizacaoFiscalModel.gerar_proximo_codigo(parent_code)
        if not novo_codigo:
            flash(("Não foi possível gerar código", "error"))
            return redirect(url_for("listar_categorizacao_fiscal"))

        # Calcular nível
        nivel = novo_codigo.count(".") + 1

        # Criar nova subcategoria
        nova_categoria = CategorizacaoFiscalModel(
            codigo=novo_codigo,
            nome=nome,
            tipo=categoria_pai.tipo,
            parent_id=categoria_pai.id,
            nivel=nivel,
        )

        db.session.add(nova_categoria)
        db.session.commit()

        # ✅ Mensagem de sucesso com tupla
        flash((f'Subcategoria "{nome}" criada com sucesso!', "success"))

        # Registrar pontuação do usuário
        try:
            PontuacaoUsuarioModel.registrar_acao(
                usuario_id=current_user.id,
                tipo_acao=TipoAcaoEnum.CADASTRO,
                detalhes=f"Criou subcategoria: {nome}",
            )
        except:
            pass

        return redirect(url_for("listar_categorizacao_fiscal"))

    except Exception as e:
        db.session.rollback()
        flash((f"Erro interno: {str(e)}", "error"))
        return redirect(url_for("listar_categorizacao_fiscal"))