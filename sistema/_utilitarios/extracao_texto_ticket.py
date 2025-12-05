"""
Módulo para extração de informações de tickets usando pytesseract.
Extrai apenas: Número NF, Peso Líquido, Data Entrega e Placa.
Inclui validação de qualidade de imagem antes do processamento.
"""

import cv2
import numpy as np
import re
from paddleocr import PaddleOCR
from datetime import datetime


class ExtracaoTicket:
    """Classe para extrair informações de tickets: NF, Peso, Data Entrega e Placa."""

    def __init__(self, caminho_imagem):
        """
        Inicializa o extrator de dados de tickets.
        
        Args:
            caminho_imagem (str): Caminho completo para o arquivo de imagem do ticket
            
        Note:
            Cria uma nova instância do PaddleOCR para cada ticket processado,
            evitando problemas de estado corrompido entre processamentos
        """
        self.caminho_imagem = caminho_imagem
        self.ocr_engine = PaddleOCR(lang='pt', use_angle_cls=True)

    def preprocessar_imagem(path):
        """
        Realiza pré-processamento da imagem para melhorar a qualidade do OCR.
        
        Args:
            path (str): Caminho da imagem a ser processada
            
        Returns:
            numpy.ndarray: Imagem processada em tons de cinza com melhorias aplicadas
            
        Note:
            Aplica as seguintes técnicas:
            - Conversão para escala de cinza
            - Remoção de ruído com filtro Gaussiano
            - Melhoria de contraste com CLAHE (Contrast Limited Adaptive Histogram Equalization)
            - Aumento de nitidez com unsharp mask
        """
        img = cv2.imread(path)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(blur)

        sharpen = cv2.addWeighted(enhanced, 1.5, blur, -0.5, 0)

        return sharpen


    def ler_ocr(self, imagem_path=None):
        """
        Executa OCR na imagem do ticket usando PaddleOCR.
        
        Args:
            imagem_path (str, optional): Caminho da imagem. Se None, usa self.caminho_imagem
            
        Returns:
            list: Lista de textos extraídos da imagem. Retorna lista vazia em caso de erro
            
        Note:
            PaddleOCR retorna um OCRResult (objeto dict-like) contendo:
            - 'rec_texts': lista de textos reconhecidos
            - 'rec_scores': lista de scores de confiança para cada texto
        """
        if imagem_path is None:
            imagem_path = self.caminho_imagem
            
        try:
            resultado = self.ocr_engine.ocr(imagem_path)
        except Exception as e:
            return []
        
        if not resultado or not resultado[0]:
            return []
        
        ocr_result = resultado[0]
        
        if 'rec_texts' not in ocr_result:
            return []
        
        linhas = ocr_result['rec_texts']
        return linhas


    def extrair_numero(texto):
        """
        Extrai o primeiro número encontrado no texto.
        
        Args:
            texto (str): Texto contendo um ou mais números
            
        Returns:
            float or None: Primeiro número encontrado (pode ser decimal), ou None se não encontrar
            
        Note:
            Remove vírgulas e espaços antes da extração.
            Aceita tanto números decimais (com ponto) quanto inteiros.
        """
        texto = texto.replace(",", ".").replace(" ", "")
        match = re.search(r"\d+\.\d+|\d+", texto)
        if not match:
            return None
        try:
            return float(match.group(0))
        except:
            return None

    def extrair_placa(texto):
        """
        Extrai placa de veículo brasileiro do texto.
        
        Args:
            texto (str): Texto contendo possível placa de veículo
            
        Returns:
            str or None: Placa no formato AAA0A00 ou AAA0000, ou None se não encontrar
            
        Note:
            Suporta os formatos:
            - Padrão antigo: AAA0000 (3 letras + 4 números)
            - Padrão Mercosul: AAA0A00 (3 letras + 1 número + 1 letra + 2 números)
        """
        placa = re.search(r"[A-Z]{3}[0-9][A-Z0-9][0-9]{2}", texto.upper())
        if placa:
            return placa.group(0)
        return None

    def extrair_data(texto):
        """
        Extrai data no formato brasileiro do texto.
        
        Args:
            texto (str): Texto contendo possível data
            
        Returns:
            str or None: Data no formato DD/MM/YYYY, ou None se não encontrar
            
        Note:
            Reconhece diferentes separadores: / . -
            Normaliza sempre para o formato DD/MM/YYYY
        """
        match = re.search(r"(\d{1,2})[/\.\-](\d{1,2})[/\.\-](\d{4})", texto)
        if match:
            return f"{match.group(1)}/{match.group(2)}/{match.group(3)}"
        return None


    def extrair_dados_ticket(self):
        """
        Executa a extração completa dos dados do ticket.
        
        Returns:
            dict: Dicionário contendo os campos extraídos:
                - placa (str or None): Placa do veículo
                - peso_liquido (float or None): Peso líquido em toneladas
                - data_entrada (str or None): Data de entrada no formato DD/MM/YYYY
                - numero_nota (str or None): Número da nota fiscal
                
        Note:
            Campos extraídos do ticket:
            1. Placa: padrão AAA0A00 ou AAA0000
            2. Peso líquido: buscado próximo à palavra "líquido"
            3. Data de entrada: buscado próximo a "entrada" ou "peso ent"
            4. Número da nota: número de 5-9 dígitos próximo a "nota" ou "n.f"
            
            Se o OCR falhar, retorna dicionário com todos os campos None.
        """
        try:
            linhas = self.ler_ocr()
        except Exception as e:
            return {
                "placa": None,
                "peso_liquido": None,
                "data_entrada": None,
                "numero_nota": None
            }
        
        if not linhas:
            return {
                "placa": None,
                "peso_liquido": None,
                "data_entrada": None,
                "numero_nota": None
            }

        dados = {
            "placa": None,
            "peso_liquido": None,
            "data_entrada": None,
            "numero_nota": None
        }
        
        for i, linha in enumerate(linhas):
            linha_lower = linha.lower()

            if not dados["placa"]:
                placa = ExtracaoTicket.extrair_placa(linha)
                if placa:
                    dados["placa"] = placa

            if re.search(r'l[ií]quido', linha_lower):
                num = ExtracaoTicket.extrair_numero(linha)
                if num and num > 0:
                    dados["peso_liquido"] = num
                elif i + 1 < len(linhas):
                    num = ExtracaoTicket.extrair_numero(linhas[i + 1])
                    if num and num > 0:
                        dados["peso_liquido"] = num

            if not dados["data_entrada"]:
                if re.search(r'entrada|peso\s+ent', linha_lower):
                    data = ExtracaoTicket.extrair_data(linha)
                    if data:
                        dados["data_entrada"] = data
                    elif i + 1 < len(linhas):
                        data = ExtracaoTicket.extrair_data(linhas[i + 1])
                        if data:
                            dados["data_entrada"] = data
                    elif i + 2 < len(linhas):
                        data = ExtracaoTicket.extrair_data(linhas[i + 2])
                        if data:
                            dados["data_entrada"] = data
                elif re.search(r'data[:.]?|\d{2}[/\.\-]\d{2}[/\.\-]\d{4}', linha_lower):
                    data = ExtracaoTicket.extrair_data(linha)
                    if data:
                        dados["data_entrada"] = data

            if not dados["numero_nota"]:
                if re.search(r'nota|n\.?f|num\.?\s*nota|numer[oa]', linha_lower):
                    match = re.search(r'\d{5,9}', linha)
                    if match:
                        dados["numero_nota"] = match.group(0)
                    elif i + 1 < len(linhas):
                        match = re.search(r'\d{5,9}', linhas[i + 1])
                        if match:
                            dados["numero_nota"] = match.group(0)

        return dados

        return dados

    def processar(self):
        """
        Processa o ticket e retorna os dados extraídos formatados para a view.
        
        Returns:
            dict: Dicionário contendo:
                - sucesso (bool): True se processamento foi bem sucedido
                - numero_nf (str or None): Número da nota fiscal
                - peso_liquido (float or None): Peso líquido em toneladas
                - data_entrega (datetime or None): Data de entrega como objeto datetime
                - placa (str or None): Placa do veículo
                - erro (str, opcional): Tipo do erro, se houver
                - mensagem (str, opcional): Mensagem de erro detalhada, se houver
                - campos_faltantes (list, opcional): Lista de campos não extraídos, se houver erro
                
        Note:
            Sempre retorna sucesso=True mesmo se alguns campos não forem extraídos,
            permitindo que o usuário preencha manualmente. Somente retorna sucesso=False
            em caso de exceção durante o processamento.
        """
        try:
            dados_extraidos = self.extrair_dados_ticket()
            
            if dados_extraidos is None:
                dados_extraidos = {
                    "placa": None,
                    "peso_liquido": None,
                    "data_entrada": None,
                    "numero_nota": None
                }
            
            data_entrega = None
            if dados_extraidos.get('data_entrada'):
                try:
                    data_entrega = datetime.strptime(dados_extraidos['data_entrada'], '%d/%m/%Y')
                except:
                    pass
            
            resultado = {
                'sucesso': True,
                'numero_nf': dados_extraidos.get('numero_nota'),
                'peso_liquido': dados_extraidos.get('peso_liquido'),
                'data_entrega': data_entrega,
                'placa': dados_extraidos.get('placa')
            }
            
            return resultado
            
        except Exception as e:
            return {
                'sucesso': False,
                'erro': 'ERRO_EXTRACAO',
                'mensagem': f'Erro ao extrair dados: {str(e)}',
                'numero_nf': None,
                'peso_liquido': None,
                'data_entrega': None,
                'placa': None,
                'campos_faltantes': ['numero_nf', 'peso_liquido', 'data_entrega', 'placa']
            }
