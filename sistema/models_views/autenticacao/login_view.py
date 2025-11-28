from sistema import app, requires_roles, db
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required, login_user, logout_user
from sqlalchemy import extract, func
import re
from datetime import datetime
from calendar import monthrange
from sistema.models_views.autenticacao.usuario_model import UsuarioModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_cadastro_model import FornecedorCadastroModel
from sistema.models_views.gerenciar.floresta.floresta_model import FlorestaModel
from sistema.models_views.gerenciar.floresta.floresta_model import FlorestaModel
from sistema.models_views.gerenciar.motorista.motorista_model import MotoristaModel
from sistema.models_views.gerenciar.cliente.cliente_model import ClienteModel
from sistema.models_views.controle_carga.solicitacao_nf.carga_model import CargaModel
from sistema.models_views.controle_carga.nf_complementar.nf_entrada_model import NfEntradaModel
from sistema.models_views.configuracoes_gerais.empresa_emissora.empresa_emissora_model import EmpresaEmissoraModel
from sistema.models_views.autenticacao.dashboard_model import DashboardModel
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
    """
    Rota principal do dashboard que exibe dados consolidados do sistema.
    
    Apresenta informações sobre:
    - Dados básicos (empresas, fornecedores, clientes, etc.)
    - Gráficos de vendas por produto/período
    - Ranking de produtividade dos usuários
    - Totais acumulados de vendas e contra-notas
    
    Query Parameters:
        empresa_emissora_id (int): ID da empresa emissora (padrão: 1)
        mesano (str): Período no formato YYYY-MM (padrão: mês atual)
    
    Returns:
        Template renderizado com todos os dados do dashboard
    """
    
    # ========== COLETA DE DADOS BÁSICOS ==========
    # Obtém dados padrão para o dashboard
    empresas_emissoras = EmpresaEmissoraModel.obter_empresas_emissoras_ativas()
    fornecedores = FornecedorCadastroModel.listar_fornecedores_ativos()
    florestas = FlorestaModel.listar_florestas_ativas()
    nfContraNota = NfEntradaModel.listar_nfs_entrada_sem_contra_nota()
    motoristas = MotoristaModel.listar_motoristas_ativos()
    clientes = ClienteModel.listar_clientes_ativos()
    nfs_nao_emitidas = CargaModel.listar_nfs_nao_emitidas()
    tickets_nao_lancados = CargaModel.listar_tickets_nao_lancados()
    cargasOrigemNaoIdentificada = CargaModel.listar_cargas_com_origem_nao_identificada()

    # ========== PARÂMETROS DE FILTRO ==========
    # Empresa padrão 1 caso não informada
    empresa_selecionada_id = request.args.get("empresa_emissora_id", type=int) or 1
    
    # Seletor de mês via query string (formato YYYY-MM)
    mesano = request.args.get("mesano")
    hoje = datetime.today()
    
    if mesano:
        try:
            ano, mes = map(int, mesano.split("-"))
        except ValueError:
            # Em caso de formato inválido, usa mês atual
            ano, mes = hoje.year, hoje.month
    else:
        ano, mes = hoje.year, hoje.month

    # ========== COLETA DE DADOS DO DASHBOARD ==========
    # Utiliza a DashboardModel para obter todos os dados processados
    dados_dashboard = DashboardModel.obter_dados_completos_dashboard(
        empresa_selecionada_id, ano, mes
    )

    # ========== RENDERIZAÇÃO DO TEMPLATE ==========
    return render_template(
        "estrutura/dashboard.html",
        # Dados básicos
        fornecedores=fornecedores,
        empresas_emissoras=empresas_emissoras,
        florestas=florestas,
        motoristas=motoristas,
        nfContraNota=nfContraNota,
        clientes=clientes,
        cargasOrigemNaoIdentificada=cargasOrigemNaoIdentificada,
        nfs_nao_emitidas=nfs_nao_emitidas,
        tickets_nao_lancados=tickets_nao_lancados,
        # Dados dos gráficos e dashboard (vindos da DashboardModel)
        **dados_dashboard
    )
