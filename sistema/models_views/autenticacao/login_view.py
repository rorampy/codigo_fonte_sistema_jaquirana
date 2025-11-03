from sistema import app, requires_roles, db
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required, login_user, logout_user
from sqlalchemy import extract, func
import re
from datetime import datetime
from calendar import monthrange
from sistema.models_views.autenticacao.usuario_model import UsuarioModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_model import FornecedorModel
from sistema.models_views.gerenciar.floresta.floresta_model import FlorestaModel
from sistema.models_views.gerenciar.motorista.motorista_model import MotoristaModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema.models_views.controle_carga.carga_model import CargaModel
from sistema.models_views.controle_carga.produto_model import ProdutoModel
from sistema.models_views.controle_carga.registro_operacional_model import (
    RegistroOperacionalModel,
)
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import (
    PontuacaoUsuarioModel,
)
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.controle_carga.nf_entrada_model import NfEntradaModel
from sistema.models_views.configuracoes_gerais.empresa_emissora.empresa_emissora_model import (
    EmpresaEmissoraModel,
)
from sistema._utilitarios import Tels


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        telefone = request.form["telefone"]
        senha = request.form["senha"]

        if telefone:
            telefone = Tels.remove_pontuacao_telefone_celular_br(telefone)

        usuario = UsuarioModel.obter_usuario_por_telefone(telefone)

        if not usuario or not usuario.verificar_senha(senha):
            flash((f"Telefone e/ou Senha incorreto(s)!", "warning"))

        else:
            login_user(usuario)
            return redirect(url_for("principal"))

    return render_template("autenticacao/login.html")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    logout_user()

    return redirect(url_for("login"))


@app.route("/", methods=["GET"])
@login_required
@requires_roles
def principal():
    # Dados iniciais
    empresas_emissoras = EmpresaEmissoraModel.obter_empresas_emissoras_ativas()
    fornecedores = FornecedorModel.listar_fornecedores_ativos()
    florestas = FlorestaModel.listar_florestas_ativas()
    nfContraNota = NfEntradaModel.listar_nfs_entrada_sem_contra_nota()
    motoristas = MotoristaModel.listar_motoristas_ativos()
    clientes = ClienteModel.listar_clientes_ativos()
    nfs_nao_emitidas = CargaModel.listar_nfs_nao_emitidas()
    tickets_nao_lancados = CargaModel.listar_tickets_nao_lancados()
    cargasOrigemNaoIdentificada = CargaModel.listar_cargas_com_origem_nao_identificada()

    empresa_selecionada_id = request.args.get("empresa_emissora_id", type=int) or 1
    # Seletor de mês via query string (YYYY-MM)
    mesano = request.args.get("mesano")
    hoje = datetime.today()
    if mesano:
        try:
            ano, mes = map(int, mesano.split("-"))
        except ValueError:
            ano, mes = hoje.year, hoje.month
    else:
        ano, mes = hoje.year, hoje.month

    # Define até que dia exibir nos gráficos
    if ano == hoje.year and mes == hoje.month:
        hoje_dia = hoje.day
    else:
        hoje_dia = monthrange(ano, mes)[1]

    grupos = [
        "eucalipto_torete",
        "pinus_torete",
        "pinus_18_25",
        "pinus_25_32",
        "pinus_33_mais",
        "cavaco"
    ]

    produtos_labels = [
        "Eucalipto Torete",
        "Pinus Torete",
        "Pinus 18-25",
        "Pinus 25-32",
        "Pinus 33+",
        "Biomassa"
    ]

    # ---------- Toneladas por dia (vendas do mês) ----------
    dias_do_mes = list(range(1, monthrange(ano, mes)[1] + 1))
    data_por_grupo = {g: {d: 0 for d in dias_do_mes} for g in grupos}

    query_dia = (
        db.session.query(
            extract("day", RegistroOperacionalModel.data_entrega_ticket).label("dia"),
            ProdutoModel.nome,
            BitolaModel.bitola,
            func.coalesce(
                func.sum(RegistroOperacionalModel.peso_liquido_ticket), 0
            ).label("total"),
        )
        .join(CargaModel, RegistroOperacionalModel.solicitacao_nf_id == CargaModel.id)
        .join(ProdutoModel, CargaModel.produto_id == ProdutoModel.id)
        .join(BitolaModel, CargaModel.bitola_id == BitolaModel.id)
        .filter(
            extract("year", RegistroOperacionalModel.data_entrega_ticket) == ano,
            extract("month", RegistroOperacionalModel.data_entrega_ticket) == mes,
            RegistroOperacionalModel.ativo == True,
            CargaModel.empresa_emissora_id == empresa_selecionada_id,
        )
        .group_by("dia", ProdutoModel.nome, BitolaModel.bitola)
        .all()
    )

    def mapear_produto_chave(nome, bitola):
        """Função para mapear produto e bitola para a chave correta"""
        chave_prod = (nome or "").lower()
        chave_bit = (
            (bitola or "").lower().strip().replace("-", "_").replace("+", "_mais")
        )
        
        # Lógica específica para cada tipo de produto
        if "biomassa" in chave_prod or chave_bit == "cavaco":
            return "cavaco"
        elif "eucalipto" in chave_prod:
            return f"eucalipto_{chave_bit}"
        else:  # pinus por padrão
            return f"pinus_{chave_bit}"

    for dia, nome, bitola, total in query_dia:
        chave = mapear_produto_chave(nome, bitola)
        if chave in data_por_grupo:
            data_por_grupo[chave][int(dia)] += float(total)

    labels = [str(d) for d in dias_do_mes]
    dados_front = {
        g: [round(data_por_grupo[g][d], 2) for d in dias_do_mes] for g in grupos
    }
    mostrar_linhas_graficas = any(v > 0 for g in grupos for v in dados_front[g])

    # ---------- Acumulado total no mês (vendas) ----------
    acumulado_venda = {g: 0.0 for g in grupos}

    query_venda_acumulada = (
        db.session.query(
            ProdutoModel.nome,
            BitolaModel.bitola,
            func.coalesce(
                func.sum(RegistroOperacionalModel.peso_liquido_ticket), 0
            ).label("total_venda"),
        )
        .join(CargaModel, RegistroOperacionalModel.solicitacao_nf_id == CargaModel.id)
        .join(ProdutoModel, CargaModel.produto_id == ProdutoModel.id)
        .join(BitolaModel, CargaModel.bitola_id == BitolaModel.id)
        .filter(
            extract("year", RegistroOperacionalModel.data_entrega_ticket) == ano,
            extract("month", RegistroOperacionalModel.data_entrega_ticket) == mes,
            RegistroOperacionalModel.ativo == True,
            CargaModel.empresa_emissora_id == empresa_selecionada_id,
        )
        .group_by(ProdutoModel.nome, BitolaModel.bitola)
        .all()
    )

    for nome, bitola, total in query_venda_acumulada:
        chave = mapear_produto_chave(nome, bitola)
        if chave in acumulado_venda:
            acumulado_venda[chave] = float(total)

    valores_acumulados = [round(acumulado_venda[g], 2) for g in grupos]

    # ---------- Acumulado total no mês (vendas) CUMULATIVO inclusive meses anteriores a partir de 01/05/25 ----------
    acumulado_venda_mes = {g: 0.0 for g in grupos}
    data_inicio = datetime(2025, 5, 1)

    query_venda_acumulada_mes = (
        db.session.query(
            ProdutoModel.nome,
            BitolaModel.bitola,
            func.coalesce(
                func.sum(RegistroOperacionalModel.peso_liquido_ticket), 0
            ).label("total_venda"),
        )
        .join(CargaModel, RegistroOperacionalModel.solicitacao_nf_id == CargaModel.id)
        .join(ProdutoModel, CargaModel.produto_id == ProdutoModel.id)
        .join(BitolaModel, CargaModel.bitola_id == BitolaModel.id)
        .filter(
            RegistroOperacionalModel.data_entrega_ticket >= data_inicio,
            RegistroOperacionalModel.ativo == True,
            CargaModel.empresa_emissora_id == empresa_selecionada_id,
        )
        .group_by(ProdutoModel.nome, BitolaModel.bitola)
        .all()
    )

    for nome, bitola, total in query_venda_acumulada_mes:
        chave = mapear_produto_chave(nome, bitola)
        if chave in acumulado_venda_mes:
            acumulado_venda_mes[chave] = float(total)

    valores_acumulados_mes = [round(acumulado_venda_mes[g], 2) for g in grupos]

    # ---------- Ranking de produtividade por usuário ----------
    pontuacoes = (
        db.session.query(
            func.day(PontuacaoUsuarioModel.data_cadastro).label("dia"),
            UsuarioModel.nome,
            func.sum(PontuacaoUsuarioModel.pontos).label("pontos"),
        )
        .join(UsuarioModel, PontuacaoUsuarioModel.usuario_id == UsuarioModel.id)
        .filter(
            extract("year", PontuacaoUsuarioModel.data_cadastro) == ano,
            extract("month", PontuacaoUsuarioModel.data_cadastro) == mes,
            PontuacaoUsuarioModel.ativo == True,
        )
        .group_by("dia", UsuarioModel.nome)
        .all()
    )

    pontos_por_usuario = {}
    for dia, usuario, pts in pontuacoes:
        pontos_por_usuario.setdefault(usuario, {d: 0.0 for d in dias_do_mes})
        pontos_por_usuario[usuario][int(dia)] += float(pts)

    dados_usuarios_front = []
    for usuario, mapa in pontos_por_usuario.items():
        acumul = 0.0
        serie = []
        for d in dias_do_mes:
            if d <= hoje_dia:
                acumul += mapa[d]
                label = usuario if d == hoje_dia and acumul > 0 else ""
                serie.append({"x": str(d), "y": round(acumul, 2), "label": label})
            else:
                serie.append({"x": str(d), "y": None, "label": ""})
        dados_usuarios_front.append({"name": usuario, "data": serie})

    tem_pontuacao = any(
        any(p["y"] not in (None, 0) for p in usr["data"])
        for usr in dados_usuarios_front
    )

    # ---------- Acumulado total no mês (contra-nota) CUMULATIVO inclusive meses anteriores ----------
    contra_por_grupo_mes = {g: 0.0 for g in grupos}

    query_contra_acumulada = (
        db.session.query(
            ProdutoModel.nome,
            BitolaModel.bitola,
            func.coalesce(func.sum(NfEntradaModel.peso_contra_nota), 0).label(
                "total_contra"
            ),
        )
        .join(
            RegistroOperacionalModel,
            NfEntradaModel.registro_id == RegistroOperacionalModel.id,
        )
        .join(CargaModel, RegistroOperacionalModel.solicitacao_nf_id == CargaModel.id)
        .join(ProdutoModel, CargaModel.produto_id == ProdutoModel.id)
        .join(BitolaModel, CargaModel.bitola_id == BitolaModel.id)
        .filter(
            extract("year", NfEntradaModel.data_cadastro) == hoje.year,
            extract("month", NfEntradaModel.data_cadastro) <= hoje.month,
            NfEntradaModel.ativo == True,
            NfEntradaModel.deletado == False,
            NfEntradaModel.registro.has(deletado=False, ativo=True),
            CargaModel.empresa_emissora_id == empresa_selecionada_id,
        )
        .group_by(ProdutoModel.nome, BitolaModel.bitola)
        .all()
    )

    for nome, bitola, total in query_contra_acumulada:
        chave = mapear_produto_chave(nome, bitola)
        if chave in contra_por_grupo_mes:
            contra_por_grupo_mes[chave] = float(total)

    valores_contra_acumulados = [round(contra_por_grupo_mes[g], 2) for g in grupos]

    return render_template(
        "estrutura/dashboard.html",
        fornecedores=fornecedores,
        empresas_emissoras=empresas_emissoras,
        florestas=florestas,
        motoristas=motoristas,
        nfContraNota=nfContraNota,
        clientes=clientes,
        cargasOrigemNaoIdentificada=cargasOrigemNaoIdentificada,
        nfs_nao_emitidas=nfs_nao_emitidas,
        tickets_nao_lancados=tickets_nao_lancados,
        labels=labels,
        dados_front=dados_front,
        produtos_labels=produtos_labels,
        valores_acumulados=valores_acumulados,
        valores_acumulados_mes=valores_acumulados_mes,
        valores_contra_acumulados=valores_contra_acumulados,
        ano=ano,
        mes=mes,
        empresa_selecionada_id=empresa_selecionada_id,
        mostrar_linhas_graficas=mostrar_linhas_graficas,
        dados_usuarios_front=dados_usuarios_front,
        tem_pontuacao=tem_pontuacao,
    )
