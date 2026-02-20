import os
import random, string
from flask import jsonify
from werkzeug.utils import secure_filename
from sistema import db, app, request
from sistema.models_views.upload_arquivo.upload_arquivo_model import UploadArquivoModel
from sistema._utilitarios import DataHora


def upload_arquivo(arquivo, pasta_destino, nome_referencia=""):
    """
    Função para realizar upload de arquivos no sistema.

    Parâmetros:
    - arquivo: O arquivo recebido do formulário (request.files).
    - pasta_destino: Caminho da pasta onde o arquivo será armazenado. Ex.: 'UPLOADED_USERS'
    - nome_referencia: (Opcional) String adicional para compor o nome do arquivo.

    Retorno:
    - ID do arquivo salvo no banco, ou None se não houver upload.
    """
    if not arquivo or not arquivo.filename:
        return None
    
    if nome_referencia == "":
        nome_referencia = ''.join(random.choices(string.ascii_uppercase, k=6))

    nome_arquivo = f'{DataHora.obter_data_atual_padrao_en()}_{nome_referencia}_{arquivo.filename}'
    filename = secure_filename(nome_arquivo)

    file_path = os.path.join(app.config[f'{pasta_destino}'], filename)

    arquivo.save(file_path)

    extensao = os.path.splitext(arquivo.filename)[1]
    tamanho = os.path.getsize(file_path)

    arquivo_model = UploadArquivoModel(filename, file_path, extensao, tamanho)
    db.session.add(arquivo_model)
    db.session.commit()

    return arquivo_model

@app.route('/upload-banner-portal', methods=['POST'])
def upload_banner_portal():
    informacoes_upload = []
        
    files = request.files.getlist('files[]')

    for file in files:
        if file.filename == '':
            continue
        
        if file and UploadArquivoModel.validar_extensao_imagem(file.filename):
            
            numero_aleatorio = random.randint(1,99)
            
            nome_arquivo = f'{str(DataHora.obter_data_atual_padrao_en())}_{numero_aleatorio}_{file.filename}'
                
            filename = secure_filename(nome_arquivo)
                
            file_path = os.path.join(app.config['UPLOAD_BANNERS'], filename)
                
            file.save(file_path)
                    
            extensao = os.path.splitext(file.filename)[1]
                    
            tamanho = os.path.getsize(file_path) 
                    
            arquivo = UploadArquivoModel(filename, file_path, extensao, tamanho)
            db.session.add(arquivo)
            db.session.commit()
            
            arquivo_id = arquivo.id
            informacoes_upload.append(
                {
                    "filename": filename, 
                    "path": file_path, 
                    "arquivo_id": arquivo_id
                }
            )

        else:
            return jsonify({"error": "Extensão não permitida!"}), 400

    return jsonify(
        {
            "success": "Arquivo(s) carregado(s) com sucesso!", 
            "files": informacoes_upload
        }
    ), 200
