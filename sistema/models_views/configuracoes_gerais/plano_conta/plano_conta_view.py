from sistema import app, db, requires_roles, current_user
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required
from sistema.models_views.configuracoes_gerais.plano_conta.plano_conta_model import (
    PlanoContaModel,
)
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import (
    PontuacaoUsuarioModel,
)

from sistema.models_views.autenticacao.usuario_model import UsuarioModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema._utilitarios import *


@app.route("/configuracoes/gerais/plano-contas/listar", methods=["GET", "POST"])
@login_required
@requires_roles
def listar_plano_contas():
    try:
        inicializar_categorias_padrao()

        categorias_principais = PlanoContaModel.buscar_principais()

        controle_estrutura_ativo = PlanoContaModel.query.filter_by(
            controle_estrutura=True,
            ativo=True).first() is not None

        estrutura = []
        for categoria in categorias_principais:
            categoria_dict = categoria.to_dict()
            categoria_dict["children"] = obter_subcategorias_recursivo(categoria.id)
            estrutura.append(categoria_dict)

        return render_template(
            "configuracoes_gerais/plano_conta/plano_conta.html", 
            estrutura=estrutura, 
            controle_estrutura_ativo=controle_estrutura_ativo
        )

    except Exception as e:
        flash((f"Erro ao carregar plano de contas: {str(e)}", "error"))
        return render_template(
            "configuracoes_gerais/plano_conta/plano_conta.html", 
            estrutura=[],
            controle_estrutura_ativo=False
        )


@app.route("/configuracoes/gerais/plano-contas/criar", methods=["POST"])
@login_required
@requires_roles
def criar_subcategoria():
    try:
        data = request.get_json()
        parent_code = data.get("parent_code")
        nome = data.get("nome", "").strip()

        if not nome:
            return jsonify({"erro": "Nome é obrigatório"}), 400

        if not parent_code:
            return jsonify({"erro": "Código pai é obrigatório"}), 400

        categoria_pai = PlanoContaModel.buscar_por_codigo(parent_code)
        if not categoria_pai:
            return jsonify({"erro": "Categoria pai não encontrada ou inativa"}), 404

        novo_codigo = PlanoContaModel.gerar_proximo_codigo(parent_code)
        if not novo_codigo:
            return jsonify({"erro": "Não foi possível gerar código único"}), 400

        codigo_existente = PlanoContaModel.query.filter_by(codigo=novo_codigo).first()
        if codigo_existente:
            if codigo_existente.ativo:
                return jsonify({"erro": f"Código {novo_codigo} já existe e está ativo"}), 400

        nivel = novo_codigo.count(".") + 1

        categoria_inativa = PlanoContaModel.query.filter_by(
            codigo=novo_codigo, 
        ).first()
        
        if categoria_inativa:
            categoria_inativa.nome = nome
            categoria_inativa.tipo = categoria_pai.tipo
            categoria_inativa.parent_id = categoria_pai.id
            categoria_inativa.nivel = nivel
            categoria_inativa.ativo = True
            
            nova_categoria = categoria_inativa
            action_message = "reativada"
        else:
            categoria_existente = PlanoContaModel.query.filter_by(codigo=novo_codigo).first()
            if categoria_existente:
                return jsonify({"erro": f"Código {novo_codigo} já existe no sistema"}), 400
            
            nova_categoria = PlanoContaModel(
                codigo=novo_codigo,
                nome=nome,
                tipo=categoria_pai.tipo,
                parent_id=categoria_pai.id,
                nivel=nivel,
            )
            db.session.add(nova_categoria)
            action_message = "criada"

        try:
            db.session.commit()
        except Exception as e:
            
            db.session.rollback()
            return jsonify({"erro": f"Erro ao salvar: {str(e)}"}), 500

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

@app.route("/configuracoes/gerais/plano-contas/inativos", methods=["GET"])
@login_required
@requires_roles
def listar_categorias_inativas():
    """Lista categorias inativas para debug/administração"""
    try:
        categorias_inativas = PlanoContaModel.query.filter_by(ativo=False).order_by(PlanoContaModel.codigo).all()
        
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

@app.route("/configuracoes/gerais/plano-contas/reativar/<int:categoria_id>", methods=["POST"])
@login_required
@requires_roles
def reativar_categoria(categoria_id):
    """Reativa uma categoria que foi excluída"""
    try:
        categoria = PlanoContaModel.query.get_or_404(categoria_id)
        
        if categoria.ativo:
            return jsonify({"erro": "Categoria já está ativa"}), 400
        
        conflito = PlanoContaModel.query.filter_by(
            codigo=categoria.codigo,
            ativo=True
        ).first()
        
        if conflito:
            return jsonify({
                "erro": f"Não é possível reativar: código {categoria.codigo} já está em uso"
            }), 400
        
        categoria.ativo = True
        db.session.commit()
        
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

@app.route("/configuracoes/gerais/plano-contas/editar/<int:categoria_id>", methods=["PUT"])
@login_required
@requires_roles
def editar_categoria(categoria_id):
    try:
        categoria = PlanoContaModel.query.get_or_404(categoria_id)
        data = request.get_json()
        novo_nome = data.get("nome", "").strip()

        if not novo_nome:
            return jsonify({"erro": "Nome é obrigatório"}), 400

        nome_anterior = categoria.nome
        categoria.nome = novo_nome
        db.session.commit()

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
    "/configuracoes/gerais/plano-contas/excluir/<int:categoria_id>", methods=["DELETE"]
)
@login_required
@requires_roles
def excluir_categoria(categoria_id):
    try:
        categoria = PlanoContaModel.query.get_or_404(categoria_id)

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

        nome_categoria = categoria.nome
        categoria.ativo = False
        db.session.commit()

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


@app.route("/configuracoes/gerais/plano-contas/api/estrutura", methods=["GET"])
@login_required
@requires_roles
def api_estrutura_plano_contas():
    try:
        categorias_principais = PlanoContaModel.buscar_principais()
        estrutura = []

        for categoria in categorias_principais:
            categoria_dict = categoria.to_dict()
            categoria_dict["children"] = obter_subcategorias_recursivo(categoria.id)
            estrutura.append(categoria_dict)

        return jsonify({"estrutura": estrutura})

    except Exception as e:
        return jsonify({"erro": f"Erro ao carregar estrutura: {str(e)}"}), 500


def inicializar_categorias_padrao():
    """Inicializa as categorias padrão se não existirem (considera apenas ativas)"""
    categorias_padrao = [
        ("1", "Receitas", 1),
        ("2", "Despesas", 2),
        ("3", "Movimentação", 3),
    ]

    for codigo, nome, tipo in categorias_padrao:
        existe_ativa = PlanoContaModel.buscar_por_codigo(codigo)
        if not existe_ativa:
            categoria_inativa = PlanoContaModel.query.filter_by(
                codigo=codigo,
                ativo=False
            ).first()
            
            if categoria_inativa:
                categoria_inativa.nome = nome
                categoria_inativa.tipo = tipo
                categoria_inativa.ativo = True
            else:
                categoria = PlanoContaModel(
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


def obter_subcategorias_recursivo(parent_id):
    """Obtém subcategorias de forma recursiva, marcando categorias folha"""
    subcategorias = PlanoContaModel.buscar_filhos(parent_id)
    resultado = []

    for sub in subcategorias:
        sub_dict = sub.to_dict()
        sub_dict["children"] = obter_subcategorias_recursivo(sub.id)
        sub_dict["is_leaf"] = len(sub_dict["children"]) == 0
        resultado.append(sub_dict)

    return resultado

def limpar_codigos_orfaos():
    """
    Remove registros órfãos que podem estar causando conflitos
    USE COM CUIDADO - apenas para limpeza de dados
    """
    try:
        orfaos = PlanoContaModel.query.filter(
            PlanoContaModel.ativo == False,
            PlanoContaModel.parent_id.isnot(None)
        ).all()
        
        removidos = []
        for orfao in orfaos:
            pai = PlanoContaModel.query.filter_by(
                id=orfao.parent_id,
                ativo=True
            ).first()
            
            if not pai:
                removidos.append(f"{orfao.codigo} - {orfao.nome}")
                db.session.delete(orfao)
        
        db.session.commit()
        return removidos
        
    except Exception as e:
        db.session.rollback()
        raise




@app.route("/configuracoes/gerais/plano-contas/criar-com-flash", methods=["POST"])
@login_required
@requires_roles
def criar_subcategoria_com_flash():
    """Versão alternativa que usa flash messages em vez de JSON"""
    try:
        parent_code = request.form.get("parent_code")
        nome = request.form.get("nome", "").strip()

        if not nome:
            flash(("Nome é obrigatório", "error"))
            return redirect(url_for("listar_plano_contas"))

        if not parent_code:
            flash(("Código pai é obrigatório", "error"))
            return redirect(url_for("listar_plano_contas"))

        categoria_pai = PlanoContaModel.buscar_por_codigo(parent_code)
        if not categoria_pai:
            flash(("Categoria pai não encontrada", "error"))
            return redirect(url_for("listar_plano_contas"))

        novo_codigo = PlanoContaModel.gerar_proximo_codigo(parent_code)
        if not novo_codigo:
            flash(("Não foi possível gerar código", "error"))
            return redirect(url_for("listar_plano_contas"))

        nivel = novo_codigo.count(".") + 1

        nova_categoria = PlanoContaModel(
            codigo=novo_codigo,
            nome=nome,
            tipo=categoria_pai.tipo,
            parent_id=categoria_pai.id,
            nivel=nivel,
        )

        db.session.add(nova_categoria)
        db.session.commit()

        flash((f'Subcategoria "{nome}" criada com sucesso!', "success"))

        try:
            PontuacaoUsuarioModel.registrar_acao(
                usuario_id=current_user.id,
                tipo_acao=TipoAcaoEnum.CADASTRO,
                detalhes=f"Criou subcategoria: {nome}",
            )
        except:
            pass

        return redirect(url_for("listar_plano_contas"))

    except Exception as e:
        db.session.rollback()
        flash((f"Erro interno: {str(e)}", "error"))
        return redirect(url_for("listar_plano_contas"))


def obter_estrutura_com_folhas(tipo_plano_conta):
    """
    Função simples para obter estrutura do plano de contas 
    marcando quais são categorias folha (selecionáveis) vs categorias pai (apenas visuais)
    
    Baseado nos seus dados:
    - Selecionáveis: 1.01.01.04, 1.01.01.05, 1.01.02.02, etc (folhas sem filhos)
    - Não selecionáveis: 1, 1.01, 1.01.01, etc (têm filhos)
    """
    inicializar_categorias_padrao()
    
    principais = PlanoContaModel.query.filter(
        PlanoContaModel.tipo.in_(tipo_plano_conta),
        PlanoContaModel.nivel == 1,
        PlanoContaModel.ativo == True
    ).order_by(PlanoContaModel.codigo).all()
    
    estrutura = []
    
    for cat in principais:
        d = cat.to_dict()
        d["children"] = obter_subcategorias_recursivo(cat.id)
        d["is_leaf"] = len(d["children"]) == 0
        estrutura.append(d)
    
    return estrutura


def eh_categoria_folha(categoria_id):
    """
    Verifica se uma categoria é folha (não tem filhos) = selecionável
    Função simples que pode ser usada em qualquer lugar
    """
    filhos = PlanoContaModel.buscar_filhos(categoria_id)
    return len(filhos) == 0


@app.route("/configuracoes/gerais/plano-contas/usuario-permitir-alterar", methods=["PUT"])
@login_required
@requires_roles
def permitir_alterar_estrutura():
    try:
        usuarioid = current_user.id
        usuario = UsuarioModel.obter_usuario_por_id(usuarioid)
        
        if not usuario or usuario.role_id != 1:
            return jsonify({"erro": "Permissão negada"}), 403
        
        categorias = PlanoContaModel.listar_todos_planos()
        
        if not categorias:
            return jsonify({"erro": "Nenhuma categoria encontrada"}), 404
        
        for categoria in categorias:
            categoria.controle_estrutura = True
        
        db.session.commit()

        return jsonify(
            {
                "sucesso": True,
                "mensagem": f"Estrutura liberada! {len(categorias)} categorias atualizadas com sucesso!",
            }
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao atualizar: {str(e)}"}), 500

@app.route("/configuracoes/gerais/plano-contas/usuario-negar-alteracao", methods=["PUT"])
@login_required
@requires_roles
def negar_alterar_estrutura():
    try:
        usuarioid = current_user.id
        usuario = UsuarioModel.obter_usuario_por_id(usuarioid)
        
        if not usuario or usuario.role_id != 1:
            return jsonify({"erro": "Permissão negada"}), 403
        
        categorias = PlanoContaModel.listar_todos_planos()
        
        if not categorias:
            return jsonify({"erro": "Nenhuma categoria encontrada"}), 404
        
        for categoria in categorias:
            categoria.controle_estrutura = False
        
        db.session.commit()

        return jsonify(
            {
                "sucesso": True,
                "mensagem": f"Estrutura bloqueada! {len(categorias)} categorias atualizadas com sucesso!",
            }
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao atualizar: {str(e)}"}), 500