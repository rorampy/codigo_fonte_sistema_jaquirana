from flask import make_response
import pandas as pd
import subprocess
from io import BytesIO
from config import *
import pdfkit
import os
import random
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

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

    @staticmethod
    def exportar_excel_formatado(dados, nome_arquivo, titulo_planilha='Relatório',
                                  colunas_monetarias=None, coluna_destaque=None,
                                  linha_totais=None):
        """
        Gera um Excel formatado com:
        - Linha de título mesclada
        - Cabeçalho estilizado (verde escuro)
        - Largura de colunas automática
        - Colunas monetárias formatadas em BRL (R$ 1.234,56)
        - Linha de totais opcional ao final
        - Coluna de destaque (cor vermelha) para saldos pendentes

        :param dados: Lista de dicts (cada dict = 1 linha).
        :param nome_arquivo: Nome do arquivo sem extensão.
        :param titulo_planilha: Título exibido na primeira linha.
        :param colunas_monetarias: Lista de nomes de colunas que contêm valores monetários (float).
        :param coluna_destaque: Nome de coluna monetária a destacar em vermelho.
        :param linha_totais: Dict com labels de totalização (ex: {'Valor Original': 123456.78}).
        """
        colunas_monetarias = colunas_monetarias or []

        df = pd.DataFrame(dados)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Dados', startrow=2)
            wb = writer.book
            ws = writer.sheets['Dados']

            num_colunas = len(df.columns)
            num_linhas = len(df)

            # --- Estilos ---
            verde_escuro = '1E5631'
            verde_claro = 'E7F0E7'
            cinza_zebra = 'F9F9F9'
            vermelho = 'C92A2A'

            font_titulo = Font(name='Segoe UI', size=14, bold=True, color='FFFFFF')
            fill_titulo = PatternFill(start_color=verde_escuro, end_color=verde_escuro, fill_type='solid')

            font_header = Font(name='Segoe UI', size=11, bold=True, color='FFFFFF')
            fill_header = PatternFill(start_color=verde_escuro, end_color=verde_escuro, fill_type='solid')

            font_normal = Font(name='Segoe UI', size=10, color='333333')
            font_monetario = Font(name='Segoe UI', size=10, color='333333')
            font_destaque = Font(name='Segoe UI', size=10, bold=True, color=vermelho)

            font_total = Font(name='Segoe UI', size=11, bold=True, color=verde_escuro)
            fill_total = PatternFill(start_color=verde_claro, end_color=verde_claro, fill_type='solid')

            fill_zebra = PatternFill(start_color=cinza_zebra, end_color=cinza_zebra, fill_type='solid')

            align_center = Alignment(horizontal='center', vertical='center', wrap_text=True)
            align_right = Alignment(horizontal='right', vertical='center')
            align_left = Alignment(horizontal='left', vertical='center', wrap_text=True)

            borda_fina = Border(
                bottom=Side(style='thin', color='DDDDDD')
            )

            # --- Título (linha 1, mesclada) ---
            ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=num_colunas)
            celula_titulo = ws.cell(row=1, column=1, value=titulo_planilha)
            celula_titulo.font = font_titulo
            celula_titulo.fill = fill_titulo
            celula_titulo.alignment = Alignment(horizontal='center', vertical='center')
            ws.row_dimensions[1].height = 35

            # --- Linha vazia (row 2) ---
            ws.row_dimensions[2].height = 8

            # --- Cabeçalho (row 3) ---
            for col_idx in range(1, num_colunas + 1):
                cell = ws.cell(row=3, column=col_idx)
                cell.font = font_header
                cell.fill = fill_header
                cell.alignment = align_center
                cell.border = Border(bottom=Side(style='medium', color=verde_escuro))
            ws.row_dimensions[3].height = 28

            # --- Identificar colunas monetárias e destaque por índice ---
            colunas = list(df.columns)
            idx_monetarias = set()
            idx_destaque = None
            for i, col_name in enumerate(colunas):
                if col_name in colunas_monetarias:
                    idx_monetarias.add(i)
                if col_name == coluna_destaque:
                    idx_destaque = i

            # --- Dados (a partir da row 4) ---
            for row_idx in range(num_linhas):
                excel_row = row_idx + 4

                for col_idx in range(num_colunas):
                    cell = ws.cell(row=excel_row, column=col_idx + 1)
                    cell.border = borda_fina

                    if col_idx in idx_monetarias:
                        valor = cell.value
                        if isinstance(valor, (int, float)):
                            cell.number_format = '#,##0.00'
                            cell.value = round(valor, 2)
                        cell.alignment = align_center

                        if col_idx == idx_destaque:
                            cell.font = font_destaque
                        else:
                            cell.font = font_monetario
                    else:
                        cell.font = font_normal
                        cell.alignment = align_center

                # Zebra striping
                if row_idx % 2 == 1:
                    for col_idx in range(num_colunas):
                        ws.cell(row=excel_row, column=col_idx + 1).fill = fill_zebra

            # --- Linha de totais ---
            if linha_totais:
                total_row = num_linhas + 4
                ws.row_dimensions[total_row].height = 28

                for col_idx in range(num_colunas):
                    cell = ws.cell(row=total_row, column=col_idx + 1)
                    cell.fill = fill_total
                    cell.border = Border(top=Side(style='medium', color=verde_escuro))
                    col_name = colunas[col_idx]

                    if col_name in linha_totais:
                        cell.value = round(linha_totais[col_name], 2)
                        cell.number_format = '#,##0.00'
                        cell.alignment = align_center
                        if col_name == coluna_destaque:
                            cell.font = Font(name='Segoe UI', size=11, bold=True, color=vermelho)
                        else:
                            cell.font = font_total
                    elif col_idx == 0:
                        cell.value = 'TOTAIS'
                        cell.font = font_total
                        cell.alignment = align_center
                    else:
                        cell.font = font_total

            # --- Auto-width das colunas ---
            for col_idx in range(num_colunas):
                col_letter = get_column_letter(col_idx + 1)
                max_len = len(str(colunas[col_idx])) + 4

                for row_idx in range(num_linhas):
                    cell_value = ws.cell(row=row_idx + 4, column=col_idx + 1).value
                    if cell_value is not None:
                        cell_len = len(str(cell_value))
                        if cell_len > max_len:
                            max_len = cell_len

                ws.column_dimensions[col_letter].width = max(12, min(max_len + 2, 45))

            # Congelar cabeçalho
            ws.freeze_panes = 'A4'

        output.seek(0)

        resposta = make_response(output.read())
        resposta.headers['Content-Disposition'] = f'attachment; filename={nome_arquivo}.xlsx'
        resposta.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

        return resposta