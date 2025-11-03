import re
import pdfplumber
from datetime import datetime

class ExtrairDadosNFSe:
    def __init__(self):
        pass

    @staticmethod
    def extrair_texto_do_pdf(caminho_arquivo):
        """Extrai texto do PDF usando pdfplumber"""
        texto = ""
        try:
            with pdfplumber.open(caminho_arquivo) as pdf:
                for pagina in pdf.pages:
                    texto += pagina.extract_text() + "\n"
        except Exception as e:
            print(f"Erro ao extrair texto do PDF: {e}")
            return ""
        return texto

    @staticmethod
    def extrair_dados_nfse_simples(caminho_pdf):
        """Extração dinâmica de dados NFSe"""
        texto = ExtrairDadosNFSe.extrair_texto_do_pdf(caminho_pdf)
        linhas = [linha.strip() for linha in texto.split('\n') if linha.strip()]
        
        dados = {
            "cabecalho": {},
            "prestador": {},
            "tomador": {},
            "discriminacao": {},
            "retencoes": {},
            "totais": {}
        }
        
        # === CABEÇALHO ===
        # Número da nota
        for i, linha in enumerate(linhas):
            if "Número da Nota" in linha:
                # Buscar número na mesma linha ou próximas linhas
                numero = re.search(r'\d+', linha)
                if numero:
                    dados["cabecalho"]["numero_nota"] = numero.group()
                    break
                # Verificar próximas 3 linhas
                for j in range(1, 4):
                    if i + j < len(linhas):
                        numero = re.search(r'^\d+$', linhas[i + j].strip())
                        if numero:
                            dados["cabecalho"]["numero_nota"] = numero.group()
                            break
                if dados["cabecalho"].get("numero_nota"):
                    break
        
        # Data/hora, código e competência
        for linha in linhas:
            if not dados["cabecalho"].get("data_hora_emissao"):
                data_hora = re.search(r'(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})', linha)
                if data_hora:
                    dados["cabecalho"]["data_hora_emissao"] = data_hora.group(1)
            
            if not dados["cabecalho"].get("codigo_verificacao"):
                codigo = re.search(r'(\d{4}\.\w+)', linha)
                if codigo:
                    dados["cabecalho"]["codigo_verificacao"] = codigo.group(1)
        
        # Competência
        for i, linha in enumerate(linhas):
            if "Competência" in linha and i + 1 < len(linhas):
                data_competencia = re.search(r'(\d{2}/\d{2}/\d{4})', linhas[i + 1])
                if data_competencia:
                    dados["cabecalho"]["data_competencia"] = data_competencia.group(1)
                    break
        
        # === DADOS DO SERVIÇO ===
        for linha in linhas:
            if "Exigível" in linha:
                dados["dados_servico"] = {"exigibilidade": "Exigível"}
                municipios = re.findall(r'(\w+/\w+)', linha)
                if len(municipios) >= 2:
                    dados["dados_servico"]["municipio_prestacao"] = municipios[0]
                    dados["dados_servico"]["municipio_incidencia"] = municipios[1]
                break
        
        # === PRESTADOR ===
        prestador_inicio = -1
        for i, linha in enumerate(linhas):
            if "PRESTADOR DO(S) SERVIÇO" in linha:
                prestador_inicio = i
                break
        
        if prestador_inicio > -1:
            tomador_inicio = -1
            for i, linha in enumerate(linhas[prestador_inicio:], prestador_inicio):
                if "TOMADOR DO(S) SERVIÇO" in linha:
                    tomador_inicio = i
                    break
            
            secao_prestador = linhas[prestador_inicio:tomador_inicio] if tomador_inicio > -1 else linhas[prestador_inicio:prestador_inicio+30]
            
            # Extrair dados do prestador dinamicamente
            for i, linha in enumerate(secao_prestador):
                # Nome/Razão Social (primeira linha em maiúscula após título)
                if linha.isupper() and len(linha) > 10 and not re.match(r'^[0-9\s\.,/-]+$', linha) and "PRESTADOR" not in linha and "Nome/Razão Social" not in linha:
                    if not dados["prestador"].get("identificacao_social"):
                        dados["prestador"]["identificacao_social"] = linha
                
                # Nome Fantasia
                if "Nome Fantasia" in linha and i + 1 < len(secao_prestador):
                    dados["prestador"]["nome_fantasia"] = secao_prestador[i + 1]
                
                # Endereço
                if "Endereço" in linha and i + 1 < len(secao_prestador):
                    dados["prestador"]["endereco"] = secao_prestador[i + 1]
                
                # Município e CEP
                municipio_cep = re.search(r'(\w+/\w+)\s+CEP\s+([0-9-]+)', linha)
                if municipio_cep:
                    dados["prestador"]["municipio"] = municipio_cep.group(1)
                    dados["prestador"]["cep"] = municipio_cep.group(2)
                
                # CNPJ
                cnpj = re.search(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', linha)
                if cnpj:
                    dados["prestador"]["cnpj_cpf"] = cnpj.group(1)
                
                # Inscrições (buscar separadamente)
                # Inscrição Municipal (número após CNPJ na mesma linha)
                if dados["prestador"].get("cnpj_cpf") and dados["prestador"]["cnpj_cpf"] in linha:
                    # Na linha: 34.113.986/0001-28 46802 022/0089175
                    partes = linha.split()
                    for j, parte in enumerate(partes):
                        if dados["prestador"]["cnpj_cpf"] in parte and j + 1 < len(partes):
                            # Próxima parte é inscrição municipal
                            dados["prestador"]["inscricao_municipal"] = partes[j + 1]
                            # E a seguinte é inscrição estadual
                            if j + 2 < len(partes):
                                dados["prestador"]["inscricao_estadual"] = partes[j + 2]
                            break
                
                # Telefone
                telefone = re.search(r'\((\d{2})\)(\d{4,5}-\d{4})', linha)
                if telefone:
                    dados["prestador"]["telefone"] = f"({telefone.group(1)}){telefone.group(2)}"
                
                # Email
                email = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', linha)
                if email:
                    dados["prestador"]["email"] = email.group(1)
        
        # === TOMADOR ===
        if tomador_inicio > -1:
            discriminacao_inicio = -1
            for i, linha in enumerate(linhas[tomador_inicio:], tomador_inicio):
                if "DISCRIMINAÇÃO DO(S) SERVIÇO" in linha:
                    discriminacao_inicio = i
                    break
            
            secao_tomador = linhas[tomador_inicio:discriminacao_inicio] if discriminacao_inicio > -1 else linhas[tomador_inicio:tomador_inicio+20]
            
            # Extrair dados do tomador dinamicamente
            for i, linha in enumerate(secao_tomador):
                # Nome/Razão Social
                if linha.isupper() and len(linha) > 10 and not re.match(r'^[0-9\s\.,/-]+$', linha) and "TOMADOR" not in linha and "Nome/Razão Social" not in linha:
                    if not dados["tomador"].get("razao_social"):
                        dados["tomador"]["razao_social"] = linha
                
                # Endereço
                if "Endereço" in linha and i + 1 < len(secao_tomador):
                    dados["tomador"]["endereco"] = secao_tomador[i + 1]
                
                # Município e CEP
                municipio_cep = re.search(r'(\w+/\w+)\s+CEP\s+([0-9-]+)', linha)
                if municipio_cep:
                    dados["tomador"]["municipio"] = municipio_cep.group(1)
                    dados["tomador"]["cep"] = municipio_cep.group(2)
                
                # CNPJ (diferente do prestador)
                cnpj = re.search(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', linha)
                if cnpj and cnpj.group(1) != dados["prestador"].get("cnpj_cpf"):
                    dados["tomador"]["cnpj_cpf"] = cnpj.group(1)
                
                # Inscrição Municipal (buscar na linha específica ou após CNPJ)
                if "Inscrição Municipal" in linha:
                    # Se tem o label, pegar próxima linha
                    if i + 1 < len(secao_tomador):
                        inscricao = secao_tomador[i + 1].strip()
                        # Só aceitar se não for um CNPJ
                        if not re.match(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', inscricao):
                            dados["tomador"]["inscricao_municipal"] = inscricao
                
                # Telefone
                telefone = re.search(r'\((\d{2})\)(\d{4,5}-\d{4})', linha)
                if telefone and telefone.group(0) != dados["prestador"].get("telefone"):
                    dados["tomador"]["telefone"] = f"({telefone.group(1)}){telefone.group(2)}"
                
                # Email
                email = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', linha)
                if email and email.group(1) != dados["prestador"].get("email"):
                    dados["tomador"]["email"] = email.group(1)
        
        # === DISCRIMINAÇÃO ===
        if discriminacao_inicio > -1:
            retencoes_inicio = -1
            for i, linha in enumerate(linhas[discriminacao_inicio:], discriminacao_inicio):
                if "RETENÇÕES FEDERAIS" in linha:
                    retencoes_inicio = i
                    break
            
            secao_discriminacao = linhas[discriminacao_inicio:retencoes_inicio] if retencoes_inicio > -1 else linhas[discriminacao_inicio:discriminacao_inicio+20]
            
            # Discriminação do serviço
            for linha in secao_discriminacao:
                if "SERVIÇOS PRESTADOS" in linha:
                    dados["discriminacao"]["discriminacao_servico"] = linha
                elif "CARREGAMENTO" in linha:
                    dados["discriminacao"]["carregamento_cavaco_biomassa"] = linha
            
            # Valores específicos da discriminação
            valores_monetarios = []
            for linha in secao_discriminacao:
                valores = re.findall(r'(\d{1,3}(?:\.\d{3})*,\d{2})', linha)
                valores_monetarios.extend(valores)
            
            # Mapear valores de forma mais precisa
            if valores_monetarios:
                # Buscar valor principal (15.478,30)
                for linha in secao_discriminacao:
                    if "SERVIÇOS PRESTADOS" in linha:
                        valores_linha = re.findall(r'(\d{1,3}(?:\.\d{3})*,\d{2})', linha)
                        if valores_linha:
                            dados["discriminacao"]["valor_servico"] = valores_linha[0]  # Primeiro valor da linha
                            if len(valores_linha) >= 3:  # Valor, alíquota, ISS
                                dados["discriminacao"]["aliquota_iss"] = valores_linha[1]
                                dados["discriminacao"]["valor_iss"] = valores_linha[2]
                        break
                
                # Se não encontrou na linha de serviços, buscar separadamente
                if not dados["discriminacao"].get("valor_servico"):
                    # Pegar o maior valor encontrado
                    valores_numericos = [float(v.replace('.', '').replace(',', '.')) for v in valores_monetarios]
                    if valores_numericos:
                        maior_valor = max(valores_numericos)
                        for valor in valores_monetarios:
                            if float(valor.replace('.', '').replace(',', '.')) == maior_valor:
                                dados["discriminacao"]["valor_servico"] = valor
                                break
                
                # Buscar alíquota (número baixo tipo 3,00)
                if not dados["discriminacao"].get("aliquota_iss"):
                    for valor in valores_monetarios:
                        num_valor = float(valor.replace(',', '.'))
                        if 1 <= num_valor <= 10:  # Alíquota entre 1% e 10%
                            dados["discriminacao"]["aliquota_iss"] = valor
                            break
                
                # Buscar valor ISS (valor médio, nem o maior nem o menor)
                if not dados["discriminacao"].get("valor_iss"):
                    valores_ordenados = sorted(valores_monetarios, key=lambda x: float(x.replace('.', '').replace(',', '.')))
                    if len(valores_ordenados) >= 2:
                        # Pegar o segundo maior ou um valor médio
                        dados["discriminacao"]["valor_iss"] = valores_ordenados[-2] if len(valores_ordenados) >= 2 else valores_ordenados[-1]
        
        # === TOTAIS ===
        totais_inicio = -1
        for i, linha in enumerate(linhas):
            if "TOTAIS" in linha:
                totais_inicio = i
                break
        
        if totais_inicio > -1:
            secao_totais = linhas[totais_inicio:totais_inicio+5]
            valores_totais = []
            for linha in secao_totais:
                valores = re.findall(r'(\d{1,3}(?:\.\d{3})*,\d{2})', linha)
                valores_totais.extend(valores)
            
            if valores_totais:
                # Total dos serviços e total líquido (geralmente iguais)
                dados["totais"]["total_servicos"] = valores_totais[0] if len(valores_totais) > 0 else None
                dados["totais"]["total_liquido"] = valores_totais[-1] if len(valores_totais) > 0 else None
        
        return dados

    @staticmethod
    def extrair_periodo_servico(texto_discriminacao):
        """Extrai período de prestação do serviço"""
        if not texto_discriminacao:
            return None, None
        
        periodo_match = re.search(r'(\d{2}/\d{2}/\d{2,4})\s+A\s+(\d{2}/\d{2}/\d{2,4})', texto_discriminacao)
        if periodo_match:
            data_inicio_str, data_fim_str = periodo_match.groups()
            
            try:
                # Se ano tem 2 dígitos, assumir 20xx
                if len(data_inicio_str.split('/')[-1]) == 2:
                    data_inicio_str = data_inicio_str[:-2] + '20' + data_inicio_str[-2:]
                    data_fim_str = data_fim_str[:-2] + '20' + data_fim_str[-2:]
                
                data_inicio = datetime.strptime(data_inicio_str, '%d/%m/%Y').date()
                data_fim = datetime.strptime(data_fim_str, '%d/%m/%Y').date()
                return data_inicio, data_fim
            except ValueError:
                pass
        
        return None, None

    # Alias para compatibilidade
    @staticmethod
    def extrair_dados_nfse_melhorado(caminho_pdf):
        return ExtrairDadosNFSe.extrair_dados_nfse_simples(caminho_pdf)