from sistema import app, requires_roles, db
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.controle_carga.solicitacao_nf.carga_model import CargaModel
from sistema.models_views.controle_carga.emissao_nota_fiscal_model import LancarEmissaoNotaFiscalModel
from sistema.models_views.controle_carga.registro_operacional.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.gerenciar.floresta.floresta_model import FlorestaModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_cadastro_model import FornecedorCadastroModel
from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.gerenciar.certificacoes.certificacoes_model import CertificacoesModel
from sistema._utilitarios import *
import os

@app.route("/controle-cargas/notas-fiscais/detalhe/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def visualizar_emissao(id):
    emissao = LancarEmissaoNotaFiscalModel.obter_emissao_por_id(id)
    return render_template(
        "/controle_carga/lancamento_nf/lancamento_visualizar.html", emissao=emissao
    )

@app.route("/controle-cargas/notas-fiscais/lancadas", methods=["GET", "POST"])
@login_required
@requires_roles
def listar_emissoes():
    emissoes = LancarEmissaoNotaFiscalModel.listar_emissoes()
    if request.method == "POST":
        emissoes = LancarEmissaoNotaFiscalModel.filtrar_emissoes(
            motorista_nf=request.form.get("motoristaNf"),
            nome_cliente=request.form.get("nomeCliente"),
            numero_nf=request.form.get("numeroNf"),
            placa_nf=request.form.get("placaNf"),
            placa_solicitacao=request.form.get("placaSolicitacao"),
        )
    else:
        emissoes = LancarEmissaoNotaFiscalModel.listar_emissoes()
    return render_template(
        "/controle_carga/lancamento_nf/lancamentos_listar.html",
        emissoes=emissoes,
        dados_corretos=request.form,
    )