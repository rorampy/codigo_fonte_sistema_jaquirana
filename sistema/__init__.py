import os
from flask import Flask, request, render_template, send_from_directory, redirect, url_for, flash, abort, session, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from mapeamento_roles import mapeamento_roles
from datetime import datetime
from functools import wraps
from config import *


app = Flask(__name__)
app.config['SECRET_KEY'] = CHAVE_SECRETA_FLASK
app.config['SESSION_TYPE'] = 'filesystem' # para utilizar sessão
app.config.from_object('config')


# instância banco
db = SQLAlchemy()
db.init_app(app)

# instância migration
mi = Migrate(app, db)

# login
login_manager = LoginManager(app)

@login_manager.unauthorized_handler
def unauthorized():
    # Verifica se a rota de origem e uma rota protegida diferente de login
    if request.endpoint != 'login':
        flash((f'Você precisa estar logado para acessar esta página!', 'warning'))
    return redirect(url_for('login'))


def requires_roles(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        # Obtendo nome da rota automaticamente
        endpoint = request.endpoint
        required_roles = mapeamento_roles.get(endpoint, [])
        
        # se for em um relacionamento N-N entre usuario e roles
        #user_roles = [role.nome for role in current_user.roles]
        user_role = current_user.role.nome
        
        #if not any(role in user_roles for role in required_roles):
        if not user_role in required_roles:
            return render_template('paginas_erro/erro_401.html')
            
        return f(*args, **kwargs)
    return wrapped


# uploads
app.config['UPLOAD_USERS'] = UPLOAD_USERS
app.config['UPLOAD_CONTRATO_FLORESTA'] = UPLOAD_CONTRATO_FLORESTA
app.config['UPLOAD_CONTRATO_FORNECEDOR'] = UPLOAD_CONTRATO_FORNECEDOR
app.config['UPLOAD_ARQUIVO_NF'] = UPLOAD_ARQUIVO_NF
app.config['UPLOAD_ARQUIVO_ESTORNO'] = UPLOAD_ARQUIVO_ESTORNO
app.config['UPLOAD_ARQUIVO_TICKET'] = UPLOAD_ARQUIVO_TICKET
app.config['UPLOAD_ARQUIVO_NF_ENTRADA'] = UPLOAD_ARQUIVO_NF_ENTRADA
app.config['UPLOAD_ARQUIVO_NF_EXCESSO'] = UPLOAD_ARQUIVO_NF_EXCESSO
app.config['UPLOAD_ARQUIVO_CONTRA_NOTA'] = UPLOAD_ARQUIVO_CONTRA_NOTA
app.config['UPLOAD_ARQUIVO_CTE'] = UPLOAD_ARQUIVO_CTE
app.config['UPLOAD_ARQUIVO_MDF'] = UPLOAD_ARQUIVO_MDF
app.config['UPLOAD_DECLARACAO_SENAR'] = UPLOAD_DECLARACAO_SENAR
app.config['UPLOAD_DOCUMENTACAO_COMPROVANTE'] = UPLOAD_DOCUMENTACAO_COMPROVANTE
app.config['UPLOAD_DOCUMENTACAO_COMPROVANTE_BANCARIO'] = UPLOAD_DOCUMENTACAO_COMPROVANTE_BANCARIO
app.config['UPLOAD_COMPROVANTE_PAGAMENTO_FORNECEDOR'] = UPLOAD_COMPROVANTE_PAGAMENTO_FORNECEDOR
app.config['UPLOAD_COMPROVANTE_PAGAMENTO_COMPLEMENTAR_FORNECEDOR'] = UPLOAD_COMPROVANTE_PAGAMENTO_COMPLEMENTAR_FORNECEDOR
app.config['UPLOAD_COMPROVANTE_PAGAMENTO_FRETEIRO'] = UPLOAD_COMPROVANTE_PAGAMENTO_FRETEIRO
app.config['UPLOAD_COMPROVANTE_PAGAMENTO_COMPLEMENTAR_FRETEIRO'] = UPLOAD_COMPROVANTE_PAGAMENTO_COMPLEMENTAR_FRETEIRO
app.config['UPLOAD_COMPROVANTE_PAGAMENTO_EXTRATOR'] = UPLOAD_COMPROVANTE_PAGAMENTO_EXTRATOR
app.config['UPLOAD_COMPROVANTE_PAGAMENTO_COMPLEMENTAR_EXTRATOR'] = UPLOAD_COMPROVANTE_PAGAMENTO_COMPLEMENTAR_EXTRATOR
app.config['UPLOAD_COMPROVANTE_PAGAMENTO_COMISSIONADO'] = UPLOAD_COMPROVANTE_PAGAMENTO_COMISSIONADO
app.config['UPLOAD_COMPROVANTE_PAGAMENTO_COMPLEMENTAR_COMISSIONADO'] = UPLOAD_COMPROVANTE_PAGAMENTO_COMPLEMENTAR_COMISSIONADO
app.config['UPLOAD_COMPROVANTE_RECEBIMENTO_CLIENTE'] = UPLOAD_COMPROVANTE_RECEBIMENTO_CLIENTE
app.config['UPLOAD_NOTA_COMPLEMENTAR'] = UPLOAD_NOTA_COMPLEMENTAR
app.config['UPLOAD_NOTA_SERVICO'] = UPLOAD_NOTA_SERVICO
app.config['UPLOAD_ESTOQUE_CERTIFICACOES'] = UPLOAD_ESTOQUE_CERTIFICACOES
app.config['UPLOAD_COMPROVANTE_RECEITA_DESPESA'] = UPLOAD_COMPROVANTE_RECEITA_DESPESA

# tornando a pasta 'uploads' acessível no front
# determinar o caminho para a pasta raiz do projeto
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))


@app.route('/uploads/_info_users/<filename>')
def diretorio_uploads_usuarios(filename):
    # Valida se o arquivo existe
    caminho_arquivo = os.path.join(PROJECT_ROOT, '..', 'uploads/_info_users', filename)
    if not os.path.isfile(caminho_arquivo):
        abort(404)  # Retorna erro 404 se o arquivo não existir
    
    return send_from_directory(
        os.path.join(PROJECT_ROOT, '..', 'uploads/_info_users'), 
        filename
    )

@app.route('/uploads/_arquivo_nf/<filename>')
def diretorio_uploads_nota_fiscal(filename):
    # Valida se o arquivo existe
    caminho_arquivo = os.path.join(PROJECT_ROOT, '..', 'uploads/_arquivo_nf', filename)
    if not os.path.isfile(caminho_arquivo):
        abort(404)  # Retorna erro 404 se o arquivo não existir
    
    return send_from_directory(
        os.path.join(PROJECT_ROOT, '..', 'uploads/_arquivo_nf'), 
        filename
    )

@app.route('/uploads/_contratos_florestas/<filename>')
def diretorio_uploads_contrato_floresta(filename):
    # Valida se o arquivo existe
    caminho_arquivo = os.path.join(PROJECT_ROOT, '..', 'uploads/_contratos_florestas', filename)
    if not os.path.isfile(caminho_arquivo):
        abort(404)  # Retorna erro 404 se o arquivo não existir
    
    return send_from_directory(
        os.path.join(PROJECT_ROOT, '..', 'uploads/_contratos_florestas'), 
        filename
    )


@app.route('/uploads/_contratos_fornecedores/<filename>')
def diretorio_uploads_contrato_fornecedor(filename):
    # Valida se o arquivo existe
    caminho_arquivo = os.path.join(PROJECT_ROOT, '..', 'uploads/_contratos_fornecedores', filename)
    if not os.path.isfile(caminho_arquivo):
        abort(404)  # Retorna erro 404 se o arquivo não existir
    
    return send_from_directory(
        os.path.join(PROJECT_ROOT, '..', 'uploads/_contratos_fornecedores'), 
        filename
    )

@app.route('/uploads/_declaracao_senar/<filename>')
def diretorio_uploads_declaracao_senar(filename):
    # Valida se o arquivo existe
    caminho_arquivo = os.path.join(PROJECT_ROOT, '..', 'uploads/_declaracao_senar', filename)
    if not os.path.isfile(caminho_arquivo):
        abort(404)  # Retorna erro 404 se o arquivo não existir
    
    return send_from_directory(
        os.path.join(PROJECT_ROOT, '..', 'uploads/_declaracao_senar'), 
        filename
    )

@app.route('/uploads/_arquivo_ticket/<filename>')
def diretorio_uploads_tickets(filename):
    # Valida se o arquivo existe
    caminho_arquivo = os.path.join(PROJECT_ROOT, '..', 'uploads/_arquivo_ticket', filename)
    if not os.path.isfile(caminho_arquivo):
        abort(404)  # Retorna erro 404 se o arquivo não existir
    
    return send_from_directory(
        os.path.join(PROJECT_ROOT, '..', 'uploads/_arquivo_ticket'), 
        filename
    )

@app.route('/uploads/_nf_entrada/<filename>')
def diretorio_uploads_nf_entrada(filename):
    # Valida se o arquivo existe
    caminho_arquivo = os.path.join(PROJECT_ROOT, '..', 'uploads/_nf_entrada', filename)
    if not os.path.isfile(caminho_arquivo):
        abort(404)  # Retorna erro 404 se o arquivo não existir
    
    return send_from_directory(
        os.path.join(PROJECT_ROOT, '..', 'uploads/_nf_entrada'), 
        filename
    )

@app.route('/uploads/_arquivo_estorno/<filename>')
def diretorio_uploads_arquivo_estorno(filename):
    # Valida se o arquivo existe
    caminho_arquivo = os.path.join(PROJECT_ROOT, '..', 'uploads/_arquivo_estorno', filename)
    if not os.path.isfile(caminho_arquivo):
        abort(404)  # Retorna erro 404 se o arquivo não existir
    
    return send_from_directory(
        os.path.join(PROJECT_ROOT, '..', 'uploads/_arquivo_estorno'), 
        filename
    )

@app.route('/uploads/_nf_excessao/<filename>')
def diretorio_uploads_nf_excessao(filename):
    # Valida se o arquivo existe
    caminho_arquivo = os.path.join(PROJECT_ROOT, '..', 'uploads/_nf_excessao', filename)
    if not os.path.isfile(caminho_arquivo):
        abort(404)  # Retorna erro 404 se o arquivo não existir
    
    return send_from_directory(
        os.path.join(PROJECT_ROOT, '..', 'uploads/_nf_excessao'), 
        filename
    )

@app.route('/uploads/_contra_nota/<filename>')
def diretorio_uploads_contra_nota(filename):
    # Valida se o arquivo existe
    caminho_arquivo = os.path.join(PROJECT_ROOT, '..', 'uploads/_contra_nota', filename)
    if not os.path.isfile(caminho_arquivo):
        abort(404)  # Retorna erro 404 se o arquivo não existir
    
    return send_from_directory(
        os.path.join(PROJECT_ROOT, '..', 'uploads/_contra_nota'), 
        filename
    )

@app.route('/uploads/_arquivo_cte/<filename>')
def diretorio_uploads_arquivo_cte(filename):
    # Valida se o arquivo existe
    caminho_arquivo = os.path.join(PROJECT_ROOT, '..', 'uploads/_arquivo_cte', filename)
    if not os.path.isfile(caminho_arquivo):
        abort(404)  # Retorna erro 404 se o arquivo não existir
    
    return send_from_directory(
        os.path.join(PROJECT_ROOT, '..', 'uploads/_arquivo_cte'), 
        filename
    )

@app.route('/uploads/_arquivo_mdf/<filename>')
def diretorio_uploads_arquivo_mdf(filename):
    # Valida se o arquivo existe
    caminho_arquivo = os.path.join(PROJECT_ROOT, '..', 'uploads/_arquivo_mdf', filename)
    if not os.path.isfile(caminho_arquivo):
        abort(404)  # Retorna erro 404 se o arquivo não existir
    
    return send_from_directory(
        os.path.join(PROJECT_ROOT, '..', 'uploads/_arquivo_mdf'), 
        filename
    )

@app.route('/uploads/_comprovante_pagamento_comissionado/<filename>')
def diretorio_uploads_comprovante_pagamento_comissionado(filename):
    # Valida se o arquivo existe
    caminho_arquivo = os.path.join(PROJECT_ROOT, '..', 'uploads/_comprovante_pagamento_comissionado', filename)
    if not os.path.isfile(caminho_arquivo):
        abort(404)  # Retorna erro 404 se o arquivo não existir
    
    return send_from_directory(
        os.path.join(PROJECT_ROOT, '..', 'uploads/_comprovante_pagamento_comissionado'), 
        filename
    )

@app.route('/uploads/_nf_complementar/<filename>')
def diretorio_uploads_nf_complementar(filename):
    # Valida se o arquivo existe
    caminho_arquivo = os.path.join(PROJECT_ROOT, '..', 'uploads/_nf_complementar', filename)
    if not os.path.isfile(caminho_arquivo):
        abort(404)  # Retorna erro 404 se o arquivo não existir
    
    return send_from_directory(
        os.path.join(PROJECT_ROOT, '..', 'uploads/_nf_complementar'),
        filename
    )


@app.route('/uploads/_nf_servico/<filename>')
def diretorio_uploads_nf_servico(filename):
    # Valida se o arquivo existe
    caminho_arquivo = os.path.join(PROJECT_ROOT, '..', 'uploads/_nf_servico', filename)
    if not os.path.isfile(caminho_arquivo):
        abort(404)  # Retorna erro 404 se o arquivo não existir
    
    return send_from_directory(
        os.path.join(PROJECT_ROOT, '..', 'uploads/_nf_servico'),
        filename
    )

# NOVA ROTA PARA CERTIFICAÇÕES
@app.route('/uploads/_estoque_certificacoes/<filename>')
def diretorio_uploads_estoque_certificacoes(filename):
    # Valida se o arquivo existe
    caminho_arquivo = os.path.join(PROJECT_ROOT, '..', 'uploads/_estoque_certificacoes', filename)
    if not os.path.isfile(caminho_arquivo):
        abort(404)  # Retorna erro 404 se o arquivo não existir
    
    return send_from_directory(
        os.path.join(PROJECT_ROOT, '..', 'uploads/_estoque_certificacoes'),
        filename
    )
    
@app.route('/uploads/_anexo_comprovante_receita_despesa/<filename>')
def diretorio_uploads_anexo_comprovante_receita_despesa(filename):
    # Valida se o arquivo existe
    caminho_arquivo = os.path.join(PROJECT_ROOT, '..', 'uploads/_anexo_comprovante_receita_despesa', filename)
    if not os.path.isfile(caminho_arquivo):
        abort(404)  # Retorna erro 404 se o arquivo não existir
    
    return send_from_directory(
        os.path.join(PROJECT_ROOT, '..', 'uploads/_anexo_comprovante_receita_despesa'),
        filename
    )


def obter_url_absoluta_de_imagem(nome_imagem):
    # Obtem o caminho absoluto para a pasta 'static'
    static_folder = current_app.static_folder
    # Cria o caminho absoluto para a imagem
    image_path = os.path.join(static_folder, 'images', nome_imagem)
    
    return image_path


# funções para front
# Função para formatar valores em Real Brasileiro (BRL)
def formatar_float_para_brl(valor):
    # Arredonda o valor para duas casas decimais
    valor_formatado = valor / 100

    # Converte o valor formatado para uma string
    valor_str = "{:,.2f}".format(valor_formatado)

    # Substitui ',' por '.' e vice-versa, para atender ao formato BRL
    valor_str = valor_str.replace(',', 'temp').replace('.', ',').replace('temp', '.')

    # Adiciona o símbolo R$
    valor_str = "R$ " + valor_str

    return valor_str


# Função para formatar valores em Real Brasileiro (BRL)
def formatar_float_para_brl_sem_cifrao(valor):
    # Arredonda o valor para duas casas decimais
    valor_formatado = valor / 100

    # Converte o valor formatado para uma string
    valor_str = "{:,.2f}".format(valor_formatado)

    # Substitui ',' por '.' e vice-versa, para atender ao formato BRL
    valor_str = valor_str.replace(',', 'temp').replace('.', ',').replace('temp', '.')

    # Adiciona o símbolo R$
    valor_str = valor_str

    return valor_str

# Função para formatar valores em Dólar Americano (USD)
def formatar_float_para_usd(valor):
    # Arredonda o valor para duas casas decimais
    valor_formatado = valor / 100

    # Converte o valor formatado para uma string
    valor_str = "{:,.2f}".format(valor_formatado)

    # Substitui ',' por '.' para separar os milhares
    valor_str = valor_str.replace(',', 'temp').replace('.', ',').replace('temp', '.')

    # Adiciona o símbolo $
    valor_str = "$ " + valor_str

    return valor_str

# Exibe um objeto datetime no formato de data do Brasil
def formatar_data_para_brl(data):
    # Formata a data para o padrão brasileiro dd/mm/aaaa
    return data.strftime('%d/%m/%Y')

# Função específica para filtros que aceita tanto datetime quanto string
def formatar_data_filtro_para_brl(data):
    """
    Aceita datetime ou string no formato 'YYYY-MM-DD' e retorna 'DD/MM/YYYY'
    Função específica para os filtros dos relatórios
    """
    try:
        if isinstance(data, str):
            data_obj = datetime.strptime(data, "%Y-%m-%d")
        elif isinstance(data, datetime):
            data_obj = data
        else:
            return ""  # Retorna string vazia para tipos inválidos
        
        # Formata a data para o padrão brasileiro dd/mm/aaaa
        return data_obj.strftime('%d/%m/%Y')
    except (ValueError, TypeError):
        return ""  # Retorna string vazia em caso de erro

def formatar_data_hora(data_entrada) -> str:
    """
    Aceita datetime ou string no formato 'YYYY-MM-DD HH:MM:SS' e retorna 'DD/MM/YYYY HH:MM:SS'
    """
    try:
        if isinstance(data_entrada, str):
            data_obj = datetime.strptime(data_entrada, "%Y-%m-%d %H:%M:%S")
        elif isinstance(data_entrada, datetime):
            data_obj = data_entrada
        else:
            return ""  # Retorna string vazia para tipos inválidos

        return data_obj.strftime("%d/%m/%Y %H:%M:%S")
    except (ValueError, TypeError):
        return ""  # Retorna string vazia em caso de erro

def converte_data_para_datetime_converte_data_brl(data):
    # Converte a string para um objeto datetime
    data_obj = datetime.strptime(data, '%Y-%m-%d')
    
    # Formata a data para o padrão brasileiro dd/mm/aaaa
    return data_obj.strftime('%d/%m/%Y')

# Exibe um objeto datetime no formato de data e hora do Brasil
def formatar_data_hora_para_brl(data):
    # Formata a data para o padrão brasileiro dd/mm/aaaa hh:mm
    return data.strftime('%d/%m/%Y %H:%M')

app.jinja_env.filters['formatar_float_para_brl'] = formatar_float_para_brl
app.jinja_env.filters['formatar_float_para_brl_sem_cifrao'] = formatar_float_para_brl_sem_cifrao
app.jinja_env.filters['formatar_float_para_usd'] = formatar_float_para_usd
app.jinja_env.filters['formatar_data_para_brl'] = formatar_data_para_brl
app.jinja_env.filters['formatar_data_filtro_para_brl'] = formatar_data_filtro_para_brl
app.jinja_env.filters['formatar_data_hora_para_brl'] = formatar_data_hora_para_brl
app.jinja_env.filters['formatar_data_hora'] = formatar_data_hora
app.jinja_env.filters['converte_data_para_datetime_converte_data_brl'] = converte_data_para_datetime_converte_data_brl
app.jinja_env.filters['obter_url_absoluta_de_imagem'] = obter_url_absoluta_de_imagem


# models e rotas
from sistema.models_views import base_model
from sistema.models_views.upload_arquivo import upload_arquivo_model
from sistema.models_views.upload_arquivo import upload_arquivo_view
from sistema.models_views.autenticacao import role_model
from sistema.models_views.parametrizacao import changelog_model
from sistema.models_views.parametrizacao import changelog_view
from sistema.models_views.parametrizacao import variavel_sistema_model
from sistema.models_views.parametrizacao import variavel_sistema_view
from sistema.models_views.autenticacao import usuario_model
from sistema.models_views.autenticacao import login_view
from sistema.models_views.autenticacao import role_view
from sistema.models_views.autenticacao import usuario_view
from sistema.models_views.autenticacao import dashboard_model

# Notas fiscais
from sistema.models_views.controle_carga.solicitacao_nf import carga_model
from sistema.models_views.controle_carga.solicitacao_nf import carga_view
from sistema.models_views.controle_carga.vendas.vendas_entregues import vendas_entregues_view
from sistema.models_views.controle_carga.vendas.vendas_transito import vendas_transito_view
from sistema.models_views.controle_carga.registro_operacional import registro_operacional_model
from sistema.models_views.controle_carga.registro_operacional import registro_operacional_view
from sistema.models_views.controle_carga import emissao_nota_fiscal_model
from sistema.models_views.controle_carga import lancamento_nota_fiscal_view
from sistema.models_views.controle_carga.lancamento_ticket import ticket_model
from sistema.models_views.controle_carga.lancamento_ticket import ticket_view
from sistema.models_views.controle_carga.produto import produto_model
from sistema.models_views.controle_carga.nf_complementar import nf_complementar_view
from sistema.models_views.controle_carga.nf_complementar import nf_entrada_model
from sistema.models_views.controle_carga.nf_entrada import nf_entrada_view

# Gerenciamento
from sistema.models_views.gerenciar.cliente import cliente_model
from sistema.models_views.gerenciar.cliente import cliente_view

from sistema.models_views.gerenciar.floresta import floresta_model
from sistema.models_views.gerenciar.floresta import floresta_view

from sistema.models_views.gerenciar.fornecedor import fornecedor_model
from sistema.models_views.gerenciar.fornecedor import fornecedor_madeira_posta_model
from sistema.models_views.gerenciar.fornecedor import fornecedor_view
from sistema.models_views.gerenciar.fornecedor.fornecedor_tag_model import FornecedorTag
from sistema.models_views.faturamento.cargas_a_faturar.extrator import extrator_a_pagar_model
from sistema.models_views.faturamento.cargas_a_faturar.extrator import extrator_a_pagar_view

from sistema.models_views.gerenciar.motorista import motorista_model
from sistema.models_views.gerenciar.motorista import transportadora_motorista_associado_model
from sistema.models_views.gerenciar.motorista import motorista_view

from sistema.models_views.gerenciar.veiculo import veiculo_model
from sistema.models_views.gerenciar.veiculo import veiculo_transportadora_veiculo_associado_model
from sistema.models_views.gerenciar.veiculo import veiculo_view

from sistema.models_views.gerenciar.transportadora import transportadora_model
from sistema.models_views.gerenciar.transportadora import transportadora_view

from sistema.models_views.gerenciar.extrator import extrator_model
from sistema.models_views.gerenciar.extrator import extrator_view

from sistema.models_views.gerenciar.comissionado import comissionado_model
from sistema.models_views.gerenciar.comissionado import comissionado_view
from sistema.models_views.gerenciar.pessoa_financeiro import pessoa_financeiro_model
from sistema.models_views.gerenciar.pessoa_financeiro import pessoa_financeiro_view

# Parametros
from sistema.models_views.parametros.bitola import bitola_model
from sistema.models_views.parametros.bitola import bitola_view

from sistema.models_views.parametros.rotas_frete import rota_model
from sistema.models_views.parametros.rotas_frete import rota_view

from sistema.models_views.parametros.status_emissao_nf_complementar import status_emissao_nf_complementar_model

from sistema.models_views.parametros.nome_grupo_whats import nome_grupo_whats_model
from sistema.models_views.parametros.nome_grupo_whats import nome_grupo_whats_view

# Relatorios
from sistema.models_views.relatorios.relatorios_cargas.relatorio_nf_entrada import relatorio_nf_entrada_view
from sistema.models_views.relatorios.relatorios_cargas.relatorio_carga_cliente import relatorio_carga_cliente_view
from sistema.models_views.relatorios.relatorios_cargas.relatorio_carga_fornecedor import relatorio_carga_fornecedor_floresta_view
from sistema.models_views.relatorios.relatorio_semanal.relatorio_prestacao_fornecedor import relatorio_prestacao_fornecedor_view
from sistema.models_views.relatorios.relatorio_semanal.relatorio_prestacao_transportadora import relatorio_prestacao_transportadora_view
from sistema.models_views.relatorios.relatorios_cargas.relatorio_carga_transportadora import relatorio_carga_transportadora_view
from sistema.models_views.relatorios.relatorio_semanal.relatorio_unificado_cargas import relatorio_unificado_cargas_view
from sistema.models_views.relatorios.relatorio_controle_nf_complementar import relatorio_nf_complementar_view
from sistema.models_views.relatorios.relatorios_cargas.relatorio_carga_sintetico_cliente import relatorio_sintetico_carga_cliente_view
from sistema.models_views.relatorios.relatorio_semanal.relatorio_carga_sintetico_fornecedor import relatorio_sintetico_fornecedor_floresta_view
from sistema.models_views.relatorios.relatorio_semanal.relatorio_sintetico_transportadora import relatorio_sintetico_transportadora_view
from sistema.models_views.relatorios.relatorio_controle_funrural_senar import controle_funrural_senar_view
from sistema.models_views.relatorios.relatorios_cargas.relatorio_dashboard import relatorio_dashboard_view
from sistema.models_views.relatorios.relatorios_financeiros.relatorio_a_pagar_fornecedores import relatorio_a_pagar_fornecedores_view
from sistema.models_views.relatorios.relatorios_financeiros.relatorio_a_pagar_transportadora import relatorio_a_pagar_transportadora_view
from sistema.models_views.relatorios.relatorios_financeiros.relatorio_a_pagar_extratores import relatorio_a_pagar_extratores_view
from sistema.models_views.relatorios.relatorios_financeiros.relatorio_a_pagar_comissionado import relatorio_a_pagar_comissionado_view
from sistema.models_views.relatorios.relatorios_financeiros.relatorio_cargas_a_receber import relatorio_cargas_a_receber_view
from sistema.models_views.relatorios.relatorio_movimentacao_financeira import relatorio_movimentacao_financeira_view
from sistema.models_views.relatorios.relatorio_controle_emissao import relatorio_controle_emissao_view

# Configurações
from sistema.models_views.configuracoes_gerais.empresa_emissora import empresa_emissora_model
from sistema.models_views.configuracoes_gerais.empresa_emissora import empresa_emissora_view
from sistema.models_views.configuracoes_gerais.centro_custo import centro_custo_model
from sistema.models_views.configuracoes_gerais.centro_custo import centro_custo_view
from sistema.models_views.configuracoes_gerais.conta_bancaria import conta_bancaria_model
from sistema.models_views.configuracoes_gerais.conta_bancaria import conta_bancaria_view
from sistema.models_views.configuracoes_gerais.plano_conta import plano_conta_view
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal import categorizacao_fiscal_model
from sistema.models_views.configuracoes_gerais.categorizacao_fiscal import categorizacao_fiscal_view
from sistema.models_views.parametros.instituicoes_financeiras import instituicao_financeira_model
from sistema.models_views.configuracoes_gerais.tag import tag_model
from sistema.models_views.configuracoes_gerais.tag import tag_view

# Imposto
from sistema.models_views.parametros.imposto import imposto_model

# Financeiro
from sistema.models_views.configuracoes_gerais.situacao_pagamento import situacao_pagamento_model
from sistema.models_views.faturamento.cargas_a_receber.vendas.recebimento_model import RecebimentoModel
from sistema.models_views.faturamento.cargas_a_receber.vendas import cargas_a_receber_view
from sistema.models_views.financeiro.movimentacao_financeira import movimentacao_financeira_model
from sistema.models_views.financeiro.movimentacao_financeira.saldo_movimentacao_financeira_model import SaldoMovimentacaoFinanceiraModel
from sistema.models_views.financeiro.movimentacao_financeira import movimentacao_financeira_view
from sistema.models_views.financeiro.movimentacao_financeira import lancamento_movimentacao_extra_model
from sistema.models_views.importacao_ofx import importacao_ofx_model
from sistema.models_views.importacao_ofx import importacao_ofx_view
from sistema.models_views.precificacao_mbr import precificacao_view
from sistema.models_views.financeiro.lancamento_avulso.despesas_avulsas import despesas_avulsas_view
from sistema.models_views.financeiro.lancamento_avulso.lancamento_avulso_model import LancamentoAvulsoModel
from sistema.models_views.financeiro.lancamento_avulso.receitas_avulsas import receitas_avulsas_view
from sistema.models_views.financeiro.operacional.controle_credito import controle_credito_view
from sistema.models_views.financeiro.operacional.receita_avulsa import receita_avulsa_view
from sistema.models_views.financeiro.operacional.despesa_avulsa import despesa_avulsa_view
from sistema.models_views.financeiro.contas_bancarias import contas_bancarias_view
from sistema.models_views.faturamento.cargas_a_receber.nf_complementar import nf_complementar_model
from sistema.models_views.faturamento.cargas_a_receber.nf_complementar import nf_complementar_view
from sistema.models_views.faturamento.cargas_a_receber.nf_servico import nf_servico_model
from sistema.models_views.faturamento.cargas_a_receber.nf_servico import nf_servico_view

# Faturamento
from sistema.models_views.faturamento.cargas_a_faturar.fornecedor import fornecedor_a_pagar_model
from sistema.models_views.faturamento.cargas_a_faturar.transportadora import frete_a_pagar_model
from sistema.models_views.faturamento.cargas_a_faturar.fornecedor import fornecedor_a_pagar_view
from sistema.models_views.faturamento.cargas_a_faturar.transportadora import frete_a_pagar_view
from sistema.models_views.faturamento.controle_credito.extrato_terceiros import saldo_fornecedores_view
from sistema.models_views.faturamento.controle_credito.extrato_terceiros import saldo_extratores_view
from sistema.models_views.faturamento.controle_credito.extrato_terceiros import saldo_freteiros_view
from sistema.models_views.faturamento.cargas_a_faturar.comissionado import comissionado_a_pagar_model
from sistema.models_views.faturamento.cargas_a_faturar.comissionado import comissionado_a_pagar_view
from sistema.models_views.financeiro.operacional.faturamento_model import faturamento_model
from sistema.models_views.faturamento.controle_credito.extrato_credito import extrato_credito_extrator_model
from sistema.models_views.faturamento.controle_credito.extrato_credito import extrato_credito_fornecedor_model
from sistema.models_views.faturamento.controle_credito.extrato_credito import extrato_credito_freteiro_model
from sistema.models_views.faturamento.controle_credito.credito_agrupado import credito_extrator_model
from sistema.models_views.faturamento.controle_credito.credito_agrupado import credito_fornecedor_model
from sistema.models_views.faturamento.controle_credito.credito_agrupado import credito_freteiro_model
from sistema.models_views.financeiro.operacional.categorizar_fatura import categorizacao_fatura_view
from sistema.models_views.financeiro.operacional.categorizar_fatura import categorizacao_model
from sistema.models_views.financeiro.operacional.categorizar_fatura import categorizacao_anexo_model
from sistema.models_views.financeiro.operacional.categorizar_fatura.parcela_categorizacao import parcela_categorizacao_model
from sistema.models_views.financeiro.operacional.carga_a_receber import cargas_a_receber_view
from sistema.models_views.relatorios.relatorios_financeiros.relatorio_dfc_dre.relatorio_dfc import relatorio_financeiro_dfc_view
from sistema.models_views.relatorios.relatorios_financeiros.relatorio_dfc_dre.relatorio_dre import relatorio_financeiro_dre_view

# Operacional
from sistema.models_views.financeiro.operacional.carga_a_pagar import carga_a_pagar_view

# Pontuacao Usuario
from sistema.models_views.pontuacao_usuario import pontuacao_usuario_model

# Certificações
from sistema.models_views.gerenciar.certificacoes import certificacoes_model
from sistema.models_views.gerenciar.certificacoes import certificacoes_view