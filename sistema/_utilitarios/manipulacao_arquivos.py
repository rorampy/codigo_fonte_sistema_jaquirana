from flask import make_response
import pandas as pd
import subprocess
from io import BytesIO
from config import *
import pdfkit
import os
import random

class ManipulacaoArquivos:
    """
    Classe responsável devolver um arquivo PDF como resposta a uma
    requisição.
    """
    
    def gerar_pdf_from_html(html, nome_arquivo, orientacao="Portrait", abrir_em_nova_aba=True):
        """
        Recebe como parâmetro um template HTML renderizado, um nome para o arquivo
        PDF de saída, a orientação do documento e se deve abrir em nova aba.
        """
        options = {
            "enable-local-file-access": "",  # habilita acesso a arquivos locais
            "encoding": "UTF-8",
            "orientation": orientacao,  # Portrait ou Landscape
        }
        
        # Gerar o PDF a partir do HTML
        arquivo_pdf = pdfkit.from_string(
            html, False, configuration=pdfkit_config, options=options
        )
        
        # Retorna o PDF como resposta da requisição
        resposta = make_response(arquivo_pdf)
        resposta.headers["Content-Type"] = "application/pdf"
        
        # Define se vai baixar ou abrir em nova aba
        if abrir_em_nova_aba:
            resposta.headers["Content-Disposition"] = f"inline; filename={nome_arquivo}.pdf"
        else:
            resposta.headers["Content-Disposition"] = f"attachment; filename={nome_arquivo}.pdf"
        
        return resposta
    
    @staticmethod
    def gerar_imagem_from_html(html, nome_arquivo, largura=1400, altura=0):
        import subprocess
        from flask import make_response
        import os
        
        wkhtmltopdf_path = caminho_wkhtmltopdf

        if os.name == 'nt':  # Windows
            wkhtmltoimage_path = wkhtmltopdf_path.replace('wkhtmltopdf.exe', 'wkhtmltoimage.exe')
        else:  # Linux ou outros
            wkhtmltoimage_path = wkhtmltopdf_path.replace('wkhtmltopdf', 'wkhtmltoimage')
                
        # Verificar se o arquivo existe
        if not os.path.exists(wkhtmltoimage_path):
            raise Exception(f"wkhtmltoimage não encontrado em: {wkhtmltoimage_path}")
        
        options = [
            '--width', str(largura),
            '--height', str(altura),
            '--format', 'jpg',
            '--quality', '95',
            '--enable-local-file-access',
            '--encoding', 'UTF-8'
        ]
        
        try:
            processo = subprocess.run([
                wkhtmltoimage_path,
                *options,
                '-',
                '-'
            ], input=html.encode('utf-8'), capture_output=True, timeout=30)
            
            if processo.returncode != 0:
                raise Exception(f"Erro ao gerar imagem: {processo.stderr.decode()}")
            
            resposta = make_response(processo.stdout)
            resposta.headers['Content-Type'] = 'image/jpeg'
            resposta.headers['Content-Disposition'] = f'inline; filename={nome_arquivo}.jpg'
            
            return resposta
            
        except Exception as e:
            raise Exception(f"Erro ao gerar imagem: {str(e)}")

    def mover_e_renomear_arquivo(caminho_atual, novo_caminho, novo_nome=None):
        """
        Recebe como parâmetro o 'caminho atual' do arquivo (diretorio/nome.extensao),
        o 'novo caminho' (diretório/) e o 'novo nome' para arquivo (novo_nome_arquivo.extensao).
        A função verifica se o 'caminho_atual' e o 'novo caminho' existem e se o 'nome do arquivo'
        foi enviado. Caso sim, move e renomeia o arquivo e retorna um dicionário com a chave
        'validado' e a mensagem de sucesso. Caso não, retorna um dicionário com chave 'erro'
        e mensagem de erro. OBS: A função adiciona um número aleatório ao novo nome do arquivo
        para evitar conflitos de nomes iguais.
        """
        resultado = {}
        if (
            os.path.exists(caminho_atual)
            and os.path.exists(novo_caminho)
            and novo_nome != None
        ):
            novo = novo_caminho + str(random.randint(1, 99)) + "_" + novo_nome
            os.rename(caminho_atual, novo)
            resultado["validado"] = f"Arquivo movido e renomeado!"
            
            return resultado
        
        else:
            resultado["erro"] = f"Operação de mover e renomear falhou"
            return resultado

    def exportar_excel(dados, nome_arquivo, colunas=None):
        """
        Gera e retorna um arquivo Excel para download.
        
        :param dados: Pode ser uma lista de dicionários, uma lista de listas (com colunas), ou um DataFrame.
        :param nome_arquivo: Nome do arquivo (sem extensão).
        :param colunas: Lista de nomes das colunas (se dados for lista de listas). Opcional.
        """
        # Converte os dados para DataFrame, se já não for
        if isinstance(dados, pd.DataFrame):
            df = dados
        else:
            df = pd.DataFrame(dados, columns=colunas)
        
        # Cria um buffer para manter o arquivo na memória
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Sheet1")
        
        output.seek(0)
        
        resposta = make_response(output.read())
        resposta.headers["Content-Disposition"] = (
            f"attachment; filename={nome_arquivo}.xlsx"
        )
        resposta.headers["Content-Type"] = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        return resposta
    
    
        