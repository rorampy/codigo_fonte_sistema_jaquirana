from sistema import app, db, requires_roles, current_user
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from sistema.models_views.gerenciar.pessoa_financeiro.pessoa_financeiro_model import PessoaFinanceiroModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.models_views.parametros.instituicoes_financeiras.instituicao_financeira_model import InstituicoesFinanceirasModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.gerenciar.extrator.extrator_model import ExtratorModel
from sistema.models_views.gerenciar.transportadora.transportadora_model import TransportadoraModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_cadastro_model import FornecedorCadastroModel
from sistema.models_views.gerenciar.comissionado.comissionado_model import ComissionadoModel
from sistema._utilitarios import *

@app.route("/gerenciar/pessoas-financeiro", methods=["GET"])
@login_required
@requires_roles
def listar_pessoas_financeiro():
    if any(request.args.values()):
        numero_documento = request.args.get('numeroDocumento')
        telefone = request.args.get('telefone')
        numeroDocumento = ValidaDocs.somente_numeros(numero_documento) if numero_documento else None
        numeroTelefone = ValidaDocs.somente_numeros(telefone) if telefone else None
        pessoas = PessoaFinanceiroModel.filtrar_pessoas(
            identificacao=request.args.get('identificacao'),
            numero_documento=numeroDocumento,
            telefone=numeroTelefone
        )
    else:
        pessoas = PessoaFinanceiroModel.listar_pessoas()
    return render_template(
        "gerenciar/pessoas_financeiro/pessoas_financeiro_listar.html",
        pessoas=pessoas,
        dados_corretos=request.args
    )

@app.route("/gerenciar/pessoa-financeiro/cadastrar", methods=["GET", "POST"])
@login_required
@requires_roles
def cadastrar_pessoa_financeiro():
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True
    bancos = InstituicoesFinanceirasModel.obter_todos_bancos()
    extratores = ExtratorModel.listar_extratores_ativos()
    transportadoras = TransportadoraModel.listar_transportadoras_ativas()
    fornecedores = FornecedorCadastroModel.listar_fornecedores_ativos()
    comissionados = ComissionadoModel.listar_comissionados_ativos()
    
    if request.method == "POST":
        tipoCadastro = request.form["tipoCadastro"]
        nomePessoa = request.form["nomePessoa"]
        cpfPessoa = request.form["cpfPessoa"]
        razao_social = request.form["razaoSocial"]
        cnpj = request.form["cnpj"]
        telefone = request.form["telefone"]
        instituicao_financeira = request.form["instituicao_financeira"]
        agencia_bancaria = request.form["agencia_bancaria"]
        conta_bancaria = request.form["conta_bancaria"]
        chave_pix = request.form["chave_pix"]
        vinculos_json = request.form.get('vinculos_json')
        
        tem_fornecedor, tem_transportadora, tem_extrator, tem_comissionado, vinculos_data = PessoaFinanceiroModel.processar_vinculos(vinculos_json)

        campos = {}
        if tipoCadastro == 'cpf':
            campos['nomePessoa'] = ["Nome Completo", nomePessoa]
            campos["cpfPessoa"] = ["CPF", cpfPessoa]
        if tipoCadastro == 'cnpj':
            campos['razaoSocial'] = ["Razão Social", razao_social]
            campos["cnpj"] = ["CNPJ", cnpj]
            
        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))
            
        if tipoCadastro == 'cpf':
            verificacao_cpf = ValidaForms.validar_cpf(cpfPessoa)
            if not "validado" in verificacao_cpf:
                gravar_banco = False
                validacao_campos_erros.update(verificacao_cpf)
            numeroDocumento = ValidaDocs.remove_pontuacao_cpf(cpfPessoa)
            pesquisa_nr_documento_banco = PessoaFinanceiroModel.query.filter_by(
                numero_documento=numeroDocumento
            ).first()
            if pesquisa_nr_documento_banco:
                gravar_banco = False
                validacao_campos_erros["cpfPessoa"] = (
                    f"O CPF informado já existe no banco de dados!"
                )
            identificacaoPessoa = nomePessoa
            tipoCadastroPessoa = 1
            
        if tipoCadastro == 'cnpj':
            verificacao_cnpj = ValidaForms.validar_cnpj(cnpj)
            if not "validado" in verificacao_cnpj:
                gravar_banco = False
                validacao_campos_erros.update(verificacao_cnpj)
            numeroDocumento = ValidaDocs.remove_pontuacao_cnpj(cnpj)
            pesquisa_nr_documento_banco = PessoaFinanceiroModel.query.filter_by(
                numero_documento=numeroDocumento
            ).first()
            if pesquisa_nr_documento_banco:
                gravar_banco = False
                validacao_campos_erros["cnpj"] = (
                    f"O CNPJ informado já existe no banco de dados!"
                )
            identificacaoPessoa = razao_social
            tipoCadastroPessoa = 0
            
        if gravar_banco == True:
            telefone_tratado = Tels.remove_pontuacao_telefone_celular_br(telefone) if telefone else None
            Pessoa = PessoaFinanceiroModel(
                tipo_cadastro=tipoCadastroPessoa,
                identificacao=identificacaoPessoa,
                numero_documento=numeroDocumento,
                telefone=telefone_tratado,
                instituicao_financeira_id=instituicao_financeira if instituicao_financeira else None,
                agencia_bancaria=agencia_bancaria if agencia_bancaria else None,
                conta_bancaria=conta_bancaria if conta_bancaria else None,
                chave_pix=chave_pix if chave_pix else None,
                tem_vinculo_fornecedor=tem_fornecedor,
                tem_vinculo_transportadora=tem_transportadora,
                tem_vinculo_extrator=tem_extrator,
                tem_vinculo_comissionado=tem_comissionado,
                vinculos_operacionais=vinculos_data,
                ativo=True
            )
            db.session.add(Pessoa)
            db.session.commit()
            acao = TipoAcaoEnum.CADASTRO
            PontuacaoUsuarioModel.cadastrar_pontuacao_usuario(
                current_user.id,
                acao,
                acao.pontos,
                modulo='pessoa_financeiro'
            )
            flash(("Pessoa cadastrada com sucesso!", "success"))
            return redirect(url_for("listar_pessoas_financeiro"))
            
    return render_template(
        "gerenciar/pessoas_financeiro/pessoa_financeiro_cadastrar.html",
        campos_obrigatorios=validacao_campos_obrigatorios,
        bancos=bancos,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
        extratores=extratores,
        transportadoras=transportadoras,
        fornecedores=fornecedores,
        comissionados=comissionados
    )

@app.route("/gerenciar/pessoa-financeiro/editar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_pessoa_financeiro(id):
    pessoa = PessoaFinanceiroModel.obter_pessoa_por_id(id)
    if pessoa is None:
        flash(("Pessoa não encontrada", "warning"))
        return redirect(url_for("listar_pessoas_financeiro"))
    if pessoa.ativo == 0:
        flash((f"Esta pessoa não pode ser editada, pois está desativada!", "warning"))
        return redirect(url_for("listar_pessoas_financeiro"))
    
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True
    bancos = InstituicoesFinanceirasModel.obter_todos_bancos()
    extratores = ExtratorModel.listar_extratores_ativos()
    transportadoras = TransportadoraModel.listar_transportadoras_ativas()
    fornecedores = FornecedorCadastroModel.listar_fornecedores_ativos()
    comissionados = ComissionadoModel.listar_comissionados_ativos()
    
    dados_corretos = {
        "tipoCadastro": "cpf" if pessoa.tipo_cadastro == 1 else "cnpj",
        "razaoSocial": pessoa.identificacao or "",
        "nomePessoa": pessoa.identificacao or "",
        "cnpj": pessoa.numero_documento,
        "cpfPessoa": pessoa.numero_documento,
        "telefone": pessoa.telefone,
        "instituicao_financeira": pessoa.instituicao_financeira_id if pessoa.instituicao_financeira_id else "",
        "agencia_bancaria": pessoa.agencia_bancaria or "",
        "conta_bancaria": pessoa.conta_bancaria or "",
        "chave_pix": pessoa.chave_pix or "",
    }
    
    # Preparar vínculos existentes para o JavaScript
    vinculos_existentes = {}
    if pessoa.vinculos_operacionais:
        # Se vínculos_operacionais já é um dict, usar diretamente
        if isinstance(pessoa.vinculos_operacionais, dict):
            vinculos_existentes = pessoa.vinculos_operacionais
        # Se é uma string JSON, fazer parse
        elif isinstance(pessoa.vinculos_operacionais, str):
            import json
            try:
                vinculos_existentes = json.loads(pessoa.vinculos_operacionais)
            except:
                vinculos_existentes = {}
    
    # Converter para JSON string para usar no template
    import json
    vinculos_json = json.dumps(vinculos_existentes) if vinculos_existentes else 'null'
    
    if request.method == "POST":
        tipoCadastro = request.form["tipoCadastro"]
        nomePessoa = request.form["nomePessoa"]
        cpfPessoa = request.form["cpfPessoa"]
        razao_social = request.form["razaoSocial"]
        cnpj = request.form["cnpj"]
        telefone = request.form["telefone"]
        instituicao_financeira = request.form["instituicao_financeira"]
        agencia_bancaria = request.form["agencia_bancaria"]
        conta_bancaria = request.form["conta_bancaria"]
        chave_pix = request.form["chave_pix"]
        vinculos_json = request.form.get('vinculos_json')
        
        tem_fornecedor, tem_transportadora, tem_extrator, tem_comissionado, vinculos_data = PessoaFinanceiroModel.processar_vinculos(vinculos_json)
        
        campos = {}
        if tipoCadastro == 'cpf':
            campos['nomePessoa'] = ["Nome Completo", nomePessoa]
            campos["cpfPessoa"] = ["CPF", cpfPessoa]
        if tipoCadastro == 'cnpj':
            campos['razaoSocial'] = ["Razão Social", razao_social]
            campos["cnpj"] = ["CNPJ", cnpj]
            
        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))
            
        if tipoCadastro == 'cpf':
            verificacao_cpf = ValidaForms.validar_cpf(cpfPessoa)
            if not "validado" in verificacao_cpf:
                gravar_banco = False
                validacao_campos_erros.update(verificacao_cpf)
            numeroDocumento = ValidaDocs.remove_pontuacao_cpf(cpfPessoa)
            if pessoa.numero_documento != numeroDocumento:
                pesquisa_nr_documento_banco = PessoaFinanceiroModel.query.filter_by(
                    numero_documento=numeroDocumento
                ).first()
                if pesquisa_nr_documento_banco:
                    gravar_banco = False
                    validacao_campos_erros["cpfPessoa"] = (
                        f"O CPF informado já existe no banco de dados!"
                    )
            identificacaoPessoa = nomePessoa
            tipoCadastroPessoa = 1
            
        if tipoCadastro == 'cnpj':
            verificacao_cnpj = ValidaForms.validar_cnpj(cnpj)
            if not "validado" in verificacao_cnpj:
                gravar_banco = False
                validacao_campos_erros.update(verificacao_cnpj)
            numeroDocumento = ValidaDocs.remove_pontuacao_cnpj(cnpj)
            if pessoa.numero_documento != numeroDocumento:
                pesquisa_nr_documento_banco = PessoaFinanceiroModel.query.filter_by(
                    numero_documento=numeroDocumento
                ).first()
                if pesquisa_nr_documento_banco:
                    gravar_banco = False
                    validacao_campos_erros["cnpj"] = (
                        f"O CNPJ informado já existe no banco de dados!"
                    )
            identificacaoPessoa = razao_social
            tipoCadastroPessoa = 0
            
        if gravar_banco == True:
            telefone_tratado = Tels.remove_pontuacao_telefone_celular_br(telefone) if telefone else None
            pessoa.tipo_cadastro = tipoCadastroPessoa
            pessoa.identificacao = identificacaoPessoa
            pessoa.numero_documento = numeroDocumento
            pessoa.telefone = telefone_tratado
            pessoa.instituicao_financeira_id = instituicao_financeira if instituicao_financeira else None
            pessoa.agencia_bancaria = agencia_bancaria if agencia_bancaria else None
            pessoa.conta_bancaria = conta_bancaria if conta_bancaria else None
            pessoa.chave_pix = chave_pix if chave_pix else None
            pessoa.tem_vinculo_fornecedor = tem_fornecedor
            pessoa.tem_vinculo_transportadora = tem_transportadora
            pessoa.tem_vinculo_extrator = tem_extrator
            pessoa.tem_vinculo_comissionado = tem_comissionado
            pessoa.vinculos_operacionais = vinculos_data
            db.session.commit()
            flash(("Pessoa editada com sucesso!", "success"))
            return redirect(url_for("listar_pessoas_financeiro"))
            
    return render_template(
        "gerenciar/pessoas_financeiro/pessoa_financeiro_editar.html",
        pessoa=pessoa,
        bancos=bancos,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=dados_corretos,
        extratores=extratores,
        transportadoras=transportadoras,
        fornecedores=fornecedores,
        comissionados=comissionados,
        vinculos_json=vinculos_json 
    )

@app.route("/gerenciar/pessoa-financeiro/desativar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def desativar_pessoa_financeiro(id):
    pessoa = PessoaFinanceiroModel.obter_pessoa_por_id(id)
    if pessoa is None:
        flash(("Pessoa não encontrada", "warning"))
    pessoa.ativo = False
    db.session.commit()
    flash(("Pessoa desativada com sucesso!", "success"))
    return redirect(url_for("listar_pessoas_financeiro"))

@app.route("/gerenciar/pessoa-financeiro/ativar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def ativar_pessoa_financeiro(id):
    pessoa = PessoaFinanceiroModel.obter_pessoa_por_id(id)
    if pessoa is None:
        flash(("Pessoa não encontrada", "warning"))
    pessoa.ativo = True
    db.session.commit()
    flash(("Pessoa ativada com sucesso!", "success"))
    return redirect(url_for("listar_pessoas_financeiro"))