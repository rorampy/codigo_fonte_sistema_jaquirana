from sistema import app, requires_roles, db, obter_url_absoluta_de_imagem, formatar_data_para_brl
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.controle_carga.registro_operacional_model import RegistroOperacionalModel
from sistema.models_views.parametrizacao.changelog_model import ChangelogModel
from sistema.models_views.controle_carga.produto_model import ProdutoModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.pontuacao_usuario.pontuacao_usuario_model import PontuacaoUsuarioModel
from sistema.enum.pontuacao_enum.pontuacao_enum import TipoAcaoEnum
from sistema.models_views.controle_carga.nf_entrada_model import NfEntradaModel
from sistema._utilitarios import *

@app.route('/controle-cargas/registros-operacionais', methods=['GET'])
@login_required
@requires_roles
def listagem_registros_operacionais():
    produtos = ProdutoModel.listar_produtos()
    bitolas = BitolaModel.listar_bitolas_ativas()
    
    if any(request.args.values()):
        registros = RegistroOperacionalModel.filtrar_listagem_registros_operacionais(
            data_inicio=request.args.get('dataInicio'),
            data_fim=request.args.get('dataFim'),
            numero_nf=request.args.get('numeroNfOperacao'),
            transportadora=request.args.get('transportadoraOperacao'),
            motorista=request.args.get('motoristaOperacao'),
            origem=request.args.get('origemOperacao'),
            cliente=request.args.get('clienteOperacao'),
            produto=request.args.get('produtoEmissao'),
            bitola=request.args.get('bitolaEmissao'),
            placa=request.args.get('placaOperacao')
        )
    else:
        registros = RegistroOperacionalModel.obter_registros_operacionais()

    return render_template(
        '/controle_carga/registro_operacional/listagem_registros_operacionais.html',
        dados_corretos=request.args,
        registros=registros,
        produtos=produtos,
        bitolas=bitolas
    )

@app.route('/controle-cargas/registro-operacional/detalhes/<int:id>', methods=['GET', 'POST'])
@login_required
@requires_roles
def detalhe_registro_operacional(id):
    registro = RegistroOperacionalModel.obter_por_id(id)
    return render_template('/controle_carga/registro_operacional/detalhes_registro_operacional.html', dados_corretos=request.form,
                           registro=registro)

@app.route('/controle-cargas/registro-operacional/excluir/<int:id>', methods=['GET', 'POST'])
@login_required
@requires_roles
def excluir_registro_operacional(id):
    registro = RegistroOperacionalModel.obter_por_id(id)
    contraNota = NfEntradaModel.obter_contra_nota_por_registro(id)
    if not registro:
        flash(('Registro Operacional não encontrado!', 'warning'))

    registro.solicitacao.deletado = 1
    registro.solicitacao.ativo = 0

    registro.deletado = 1
    registro.ativo = 0

    # Deletar arquivo PDF se existir
    if registro.arquivo_nota:
        registro.arquivo_nota.deletado = 1
        registro.arquivo_nota.ativo = 0
    
    # Deletar arquivo XML se existir
    if registro.arquivo_nota_xml:
        registro.arquivo_nota_xml.deletado = 1
        registro.arquivo_nota_xml.ativo = 0
        
    # Deletar arquivo PDF de excesso se existir
    if registro.arquivo_nota_excesso:
        registro.arquivo_nota_excesso.deletado = 1
        registro.arquivo_nota_excesso.ativo = 0
        
    # Deletar arquivo XML de excesso se existir
    if registro.arquivo_nota_excesso_xml:
        registro.arquivo_nota_excesso_xml.deletado = 1
        registro.arquivo_nota_excesso_xml.ativo = 0
        
    registro.status_emissao_nf_complementar_id = 3

    if contraNota:
        contraNota.deletado = True
        contraNota.ativo = False
  

    db.session.commit()
    flash(('Registro Operacional excluido com sucesso!', 'success'))
    return redirect(url_for('listagem_registros_operacionais'))


@app.route("/controle-cargas/relatorios/controle-emissao", methods=["GET", "POST"])
@login_required
@requires_roles
def relatorio_controle_emissao():
    dataHoje = DataHora.obter_data_atual_padrao_br()
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    produtos = ProdutoModel.listar_produtos()
    bitolas = BitolaModel.listar_bitolas_ativas()

    if request.method == 'POST':
        registrosOperacionais = RegistroOperacionalModel.relatorio_controle_complementar(
            data_inicio=request.form.get("dataInicio"), data_fim=request.form.get("dataFim"),
            produto=request.form.get("produtoEmissao"), bitola=request.form.get("bitolaEmissao"),
            transportadora=request.form.get("transportadoraEmissao"), motorista=request.form.get("motoristaEmissao"),
            placa=request.form.get("placaEmissao"), cliente=request.form.get("clienteEmissao"), numero_nf=request.form.get("numeroNfEmissao")
        )
        dados_corretos = request.form
    else:
        registrosOperacionais = RegistroOperacionalModel.relatorio_controle_complementar(
            data_inicio=request.form.get('dataInicio'), data_fim=request.form.get('dataFim'),
            produto=request.form.get("produtoEmissao"), bitola=request.form.get("bitolaEmissao"),
            transportadora=request.form.get('transportadoraEmissao'), motorista=request.form.get('motoristaEmissao'),
            placa=request.form.get('placaEmissao'), cliente=request.form.get('clienteEmissao'), numero_nf=request.form.get('numeroNfEmissao')
        )
        dados_corretos = {}

    if request.form.get("exportar_pdf"):

        logo_path = obter_url_absoluta_de_imagem("logo.png")
        html = render_template(
            "relatorios/relatorio_de_cargas/relatorio_controle_emissao/exportar_relatorio_controle_emissao.html",
            logo_path=logo_path,
            dataHoje=dataHoje,
            registrosOperacionais=registrosOperacionais,
            dados_corretos=dados_corretos,
            changelog=changelog,
        )

        nome_arquivo_saida = f"relatorio-controle-emissao_{dataHoje}"
        resposta = ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida)
        return resposta
    
    if request.form.get("exportar_excel"):
        dados_excel = []
        for r in registrosOperacionais:
            dados_excel.append(
                {
                    "Data Emissão NF": (
                        formatar_data_para_brl(r.destinatario_data_emissao)
                        if r.destinatario_data_emissao
                        else ""
                    ),
                    "Produto": r.solicitacao.produto.nome or "",
                    "Bitola": r.solicitacao.bitola.bitola or "",
                    "Transportadora":r.solicitacao.transportadora_exibicao.identificacao or "",
                    "Placa": r.solicitacao.veiculo.placa_veiculo or "",
                    "Motorista": r.solicitacao.motorista.nome_completo,
                    "Cliente": r.solicitacao.cliente.identificacao,
                    "Peso NF (Ton.)": r.peso_ton_nf,
                    "Número NF": f"{r.numero_nota_fiscal_estorno} *" or "" if r.estorno_nf else r.numero_nota_fiscal or ""
                }
            )

        nome_arquivo_saida = f"relatorio-controle-emissao_{dataHoje}"
        resposta = ManipulacaoArquivos.exportar_excel(dados_excel, nome_arquivo_saida)
        return resposta

    return render_template(
        "relatorios/relatorio_de_cargas/relatorio_controle_emissao/relatorio_controle_emissao.html", dataHoje=dataHoje,
                                                                    produtos=produtos,bitolas=bitolas,
                                                                    registrosOperacionais=registrosOperacionais,
                                                                    changelog=changelog, dados_corretos=request.form)

@app.route("/relatorios/relatorio-controle-carga", methods=["GET", "POST"])
@login_required
@requires_roles
def relatorio_de_cargas():
    dataHoje = DataHora.obter_data_atual_padrao_br()

    data_inicio=request.form['dataInicioCarga']
    data_fim=request.form['dataFimCarga']
    placa_carga=request.form['placaCarga']
    freteiro_carga=request.form['freteiroCarga']
    transportadora_carga=request.form['transportadoraCarga']
    floresta_fornecedor=request.form['florestaFornecedorCarga']
    cliente_carga=request.form['clienteCarga']

    registrosOperacionais = RegistroOperacionalModel.filtro_relatorio_registros(
        data_inicio=data_inicio,
        data_fim=data_fim,
        placa_carga=placa_carga,
        freteiro_carga=freteiro_carga,
        transportadora_carga=transportadora_carga,
        floresta_fornecedor=floresta_fornecedor,
        cliente_carga=cliente_carga
    )
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()

    logo_path = obter_url_absoluta_de_imagem('logo.png')

    html =  render_template(
        "relatorios/relatorio_de_cargas/relatorio_de_cargas.html",logo_path=logo_path, dataHoje=dataHoje,
                                                                    changelog=changelog, registrosOperacionais=registrosOperacionais,
                                                                    data_inicio=data_inicio,
                                                                    data_fim=data_fim, placa_carga=placa_carga, freteiro_carga=freteiro_carga, transportadora_carga=transportadora_carga,
                                                                    floresta_fornecedor=floresta_fornecedor, cliente_carga=cliente_carga)

    nome_arquivo_saida = f'relatorio-cargas-{dataHoje}'
    resposta = ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida)

    return resposta

@app.route('/controle-cargas/atualizar-preco-un', methods=['GET', 'POST'])
@login_required
@requires_roles
def atualiza_preco_un_nf():
    if request.method == 'POST':
        RegistroOperacionalModel.corrigir_peso_preco_un_nf_todos()
        flash(('Atualização executada com sucesso!', 'success'))
        return redirect(url_for('listagem_registros_operacionais'))
    
    if request.method == 'GET':
        RegistroOperacionalModel.corrigir_peso_preco_un_nf_todos()
        flash(('Atualização executada com sucesso!', 'success'))
        return redirect(url_for('listagem_registros_operacionais'))