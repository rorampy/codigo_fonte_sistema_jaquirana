import fitz
import re


class ExtrairTextoNotaFiscal:
    def extrair_texto_do_pdf(caminho_pdf):
        """
        Extrai todo o texto do PDF. O PDF nao pode ser uma imagem.
        """
        documento = fitz.open(caminho_pdf)
        texto_completo = ""
        for pagina in documento:
            texto_completo += pagina.get_text() + "\n"
        return texto_completo

    def nf_analisar_secao(texto, marcador_inicio, marcador_fim=None):
        """
        Retorna o bloco de texto que está entre o marcador de início e, se informado, o marcador de fim.
        Se não houver marcador final, retorna desde o início até o fim do texto.
        """
        if marcador_fim:
            partes = texto.split(marcador_inicio)
            if len(partes) < 2:
                return ""
            bloco = partes[1].split(marcador_fim)[0]
        else:
            partes = texto.split(marcador_inicio)
            bloco = partes[1] if len(partes) > 1 else ""
        return bloco

    def nf_extrair_info_emissor(texto):
        """
        Extrai os dados da nota fiscal referentes ao emissor:
        - Razão Social do emissor
        - Número da Nota
        - Série
        - Chave de Acesso
        """
        # Captura Número (formato: Nº. 000.006.044)
        m_numero = re.search(r"Nº\.?\s*(\d{3}\.\d{3}\.\d{3}|\d+)", texto)
        numero_nota = m_numero.group(1).replace(".", "") if m_numero else None

        # Captura Série
        m_serie = re.search(r"Série\s+(\d+)", texto)
        serie = m_serie.group(1) if m_serie else None

        # Captura Chave de Acesso (removendo espaços)
        m_chave = re.search(r"CHAVE DE ACESSO\s*\n\s*((?:\d+\s*)+)", texto, re.IGNORECASE)
        chave = "".join(m_chave.group(1).split()) if m_chave else None

        # Extração da razão social do emissor
        # Procura por "IDENTIFICAÇÃO DO EMITENTE" e pega as próximas linhas em maiúscula
        emissor = None
        
        # Primeiro tenta o método mais robusto
        linhas = texto.splitlines()
        indice_emitente = None
        for i, linha in enumerate(linhas):
            if "IDENTIFICAÇÃO DO EMITENTE" in linha:
                indice_emitente = i
                break
        
        if indice_emitente is not None:
            linhas_candidatas = []
            for j in range(indice_emitente + 1, len(linhas)):
                linha_candidata = linhas[j].strip()
                # Se a linha não estiver vazia e estiver em caixa alta, considera parte do nome
                if linha_candidata and linha_candidata == linha_candidata.upper():
                    # Para evitar capturar seções seguintes, verifica se não é um cabeçalho conhecido
                    if not any(cabecalho in linha_candidata for cabecalho in 
                              ["DESTINATÁRIO", "REMETENTE", "CÁLCULO", "TRANSPORTADOR"]):
                        # Verifica se não é endereço (contém números de endereço ou CEP)
                        if not re.search(r'\d{4,}', linha_candidata) and not re.search(r'AV\s|RUA\s|AL\s', linha_candidata):
                            linhas_candidatas.append(linha_candidata)
                        elif linhas_candidatas:  # Se já tem nome e chegou no endereço, para
                            break
                    else:
                        break
                # Se já capturou alguma linha e encontrou uma linha que não seja todo em caixa alta,
                # considera que o nome terminou.
                elif linhas_candidatas:
                    break
            
            if linhas_candidatas:
                emissor = " ".join(linhas_candidatas)
        
        # Se não conseguiu pelo método robusto, usa o método original como fallback
        if not emissor:
            m_emissor = re.search(
                r"IDENTIFICAÇÃO DO EMITENTE\s*\n\s*([A-ZÀÁÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ\s&.-]+)",
                texto
            )
            if m_emissor:
                emissor = m_emissor.group(1).strip()

        return {
            "razao_social_emissor": emissor,
            "numero_nota": numero_nota,
            "serie": serie,
            "chave_acesso": chave,
        }

    def nf_extrair_info_destinatario(texto):
        """
        Extrai os dados do destinatário.
        Campos extraídos:
        - Nome / Razão Social
        - CNPJ/CPF
        - Inscrição Estadual
        - Endereço
        - Bairro
        - CEP
        - Município
        - UF
        - Data emissão
        - Data saída/entrada
        """
        resultado = {}
        
        # Nome/Razão Social (após "DESTINATÁRIO / REMETENTE")
        m_nome = re.search(
            r"DESTINATÁRIO\s*/\s*REMETENTE\s*\n\s*NOME\s*/\s*RAZÃO SOCIAL\s*\n\s*([^\n]+)",
            texto,
            re.IGNORECASE
        )
        if m_nome:
            resultado["nome_razao_social"] = m_nome.group(1).strip()

        # CNPJ/CPF
        m_cnpj = re.search(
            r"CNPJ\s*/\s*CPF\s*\n\s*([\d./-]+)",
            texto,
            re.IGNORECASE
        )
        if m_cnpj:
            resultado["cnpj_cpf"] = m_cnpj.group(1).strip()

        # Inscrição Estadual
        m_ie = re.search(
            r"INSCRIÇÃO ESTADUAL\s*\n\s*(\d+)",
            texto,
            re.IGNORECASE
        )
        if m_ie:
            resultado["insc_estadual"] = m_ie.group(1).strip()

        # Endereço
        m_endereco = re.search(
            r"ENDEREÇO\s*\n\s*([^\n]+)",
            texto,
            re.IGNORECASE
        )
        if m_endereco:
            resultado["endereco"] = m_endereco.group(1).strip()

        # Bairro
        m_bairro = re.search(
            r"BAIRRO\s*/\s*DISTRITO\s*\n\s*([^\n]+)",
            texto,
            re.IGNORECASE
        )
        if m_bairro:
            resultado["bairro"] = m_bairro.group(1).strip()

        # CEP
        m_cep = re.search(
            r"CEP\s*\n\s*([\d-]+)",
            texto,
            re.IGNORECASE
        )
        if m_cep:
            resultado["cep"] = m_cep.group(1).strip()

        # Município
        m_municipio = re.search(
            r"MUNICÍPIO\s*\n\s*([^\n]+)",
            texto,
            re.IGNORECASE
        )
        if m_municipio:
            resultado["municipio"] = m_municipio.group(1).strip()

        # UF
        m_uf = re.search(
            r"UF\s*\n\s*([A-Z]{2})",
            texto,
            re.IGNORECASE
        )
        if m_uf:
            resultado["uf"] = m_uf.group(1).strip()

        # Data de emissão
        m_data_emissao = re.search(
            r"DATA DA EMISSÃO\s*\n\s*(\d{2}/\d{2}/\d{4})",
            texto,
            re.IGNORECASE
        )
        if m_data_emissao:
            resultado["data_emissao"] = m_data_emissao.group(1).strip()

        # Data de saída/entrada
        m_data_saida = re.search(
            r"DATA DA SAÍDA/ENTRADA\s*\n\s*(\d{2}/\d{2}/\d{4})",
            texto,
            re.IGNORECASE
        )
        if m_data_saida:
            resultado["data_saida_entrada"] = m_data_saida.group(1).strip()

        return resultado

    def nf_extrair_calculo_imposto(texto):
        """
        Extrai os dados da tabela "Cálculo do imposto".
        """
        resultado = {}
        
        # Mapeamento dos campos
        campos = {
            r"BASE DE CÁLC\.\s+DO ICMS\s*\n\s*([\d.,]+)": "base_calculo_icms",
            r"VALOR DO ICMS\s*\n\s*([\d.,]+)": "valor_icms",
            r"BASE DE CÁLC\.\s+ICMS S\.T\.\s*\n\s*([\d.,]+)": "base_calculo_icms_subst",
            r"VALOR DO ICMS SUBST\.\s*\n\s*([\d.,]+)": "valor_icms_subst",
            r"V\.\s+FCP UF DEST\.\s*\n\s*([\d.,]+)": "valor_fcp_st",
            r"V\.\s+TOTAL PRODUTOS\s*\n\s*([\d.,]+)": "valor_total_produtos",
            r"VALOR DO FRETE\s*\n\s*([\d.,]+)": "valor_frete",
            r"VALOR DO SEGURO\s*\n\s*([\d.,]+)": "valor_seguro",
            r"DESCONTO\s*\n\s*([\d.,]+)": "desconto",
            r"OUTRAS DESPESAS\s*\n\s*([\d.,]+)": "outras_despesas",
            r"VALOR TOTAL IPI\s*\n\s*([\d.,]+)": "valor_ipi",
            r"V\.\s+TOTAL DA NOTA\s*\n\s*([\d.,]+)": "valor_total_nota",
        }
        
        for pattern, chave in campos.items():
            m = re.search(pattern, texto, re.IGNORECASE)
            if m:
                resultado[chave] = m.group(1).strip()
        
        return resultado

    def nf_extrair_info_transportador(texto):
        """
        Extrai os dados do transportador.
        """
        resultado = {}
        
        # Extrai a seção de transportador
        bloco_transportador = ExtrairTextoNotaFiscal.nf_analisar_secao(
            texto, "TRANSPORTADOR / VOLUMES TRANSPORTADOS", "DADOS DOS PRODUTOS"
        )
        
        if not bloco_transportador:
            bloco_transportador = texto
        
        # Nome/Razão Social do transportador
        # Procura por informação de frete na seção transportador
        m_frete = re.search(
            r"FRETE\s*\n\s*([^\n]+)",
            bloco_transportador,
            re.IGNORECASE
        )
        if m_frete:
            frete_info = m_frete.group(1).strip()
            
            # Interpreta códigos de frete padrão
            if "0-Por conta do Emit" in frete_info or "Por conta do Emit" in frete_info:
                resultado["nome"] = "Por conta do Emitente"
            elif "1-Por conta do Dest" in frete_info or "Por conta do Dest" in frete_info:
                resultado["nome"] = "Por conta do Destinatário"  
            elif "2-Por conta de terceiros" in frete_info:
                resultado["nome"] = "Por conta de Terceiros"
            elif "9-Sem cobrança de frete" in frete_info:
                resultado["nome"] = "Sem cobrança de frete"
            elif frete_info and not any(rotulo in frete_info.upper() for rotulo in 
                ["CÓDIGO", "PLACA", "CNPJ", "CPF", "ENDEREÇO", "MUNICÍPIO", "INSCRIÇÃO"]):
                resultado["nome"] = frete_info
            
        # Se não encontrou pelo frete, tenta pelo padrão antigo
        if "nome" not in resultado:
            m_nome = re.search(
                r"NOME\s*/\s*RAZÃO SOCIAL\s*\n\s*([^\n]+)",
                bloco_transportador,
                re.IGNORECASE
            )
            if m_nome:
                nome_valor = m_nome.group(1).strip()
                if nome_valor and nome_valor != "FRETE":
                    resultado["nome"] = nome_valor

        # CNPJ/CPF do transportador
        # Procura por padrão de CNPJ/CPF após o rótulo "CNPJ / CPF" na seção transportador
        m_cnpj = re.search(
            r"CNPJ\s*/\s*CPF\s*\n\s*ENDEREÇO\s*\n\s*([\d./-]+)",
            bloco_transportador,
            re.IGNORECASE
        )
        if m_cnpj:
            resultado["cnpj_cpf"] = m_cnpj.group(1).strip()

        # Inscrição Estadual do transportador
        # Procura após "INSCRIÇÃO ESTADUAL" na seção transportador
        m_insc = re.search(
            r"INSCRIÇÃO ESTADUAL\s*\n\s*QUANTIDADE\s*\n\s*([\w.-]+)",
            bloco_transportador,
            re.IGNORECASE
        )
        if m_insc:
            insc_valor = m_insc.group(1).strip()
            # Verifica se não é um rótulo
            if not any(rotulo in insc_valor.upper() for rotulo in 
                ["ESPÉCIE", "MARCA", "NUMERAÇÃO", "PESO"]):
                resultado["insc_estadual"] = insc_valor

        # Garante que as chaves essenciais sempre existam
        chaves_essenciais = ["nome", "cnpj_cpf", "insc_estadual"]
        for chave in chaves_essenciais:
            if chave not in resultado:
                resultado[chave] = ""
                
        return resultado

    def nf_extrair_itens(texto):
        """
        Extrai os itens da nota fiscal baseado na estrutura real observada.
        """
        # Localiza o bloco de produtos
        bloco = ExtrairTextoNotaFiscal.nf_analisar_secao(
            texto, "DADOS DOS PRODUTOS / SERVIÇOS", "DADOS ADICIONAIS"
        )
        
        if not bloco:
            bloco = texto
        
        itens = []
        
        # Padrão baseado na estrutura real da nota: 
        # 01 TORETE DE PINUS 44032200 0/00 6102 Ton 38,0000 228,7400 8.692,12 0,00 8.692,12 1.043,05 12,00
        pattern = re.compile(
            r"(\d{2})\s+"  # código do item (01, 02, etc)
            r"([A-ZÀÁÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ][^\d]+?)\s+"  # descrição (TORETE DE PINUS)
            r"(\d{8})\s+"  # NCM (44032200)
            r"([\d/]+)\s+"  # O/CST (0/00)
            r"(\d{4})\s+"  # CFOP (6102)
            r"([A-Za-z]+)\s+"  # Unidade (Ton)
            r"([\d.,]+)\s+"  # Quantidade (38,0000)
            r"([\d.,]+)\s+"  # Valor unitário (228,7400)
            r"([\d.,]+)",  # Valor total (8.692,12)
            re.IGNORECASE
        )
        
        matches = pattern.findall(bloco)
        
        for match in matches:
            item = {
                "codigo": match[0],
                "descricao": match[1].strip(),
                "ncm": match[2],
                "cst_csosn": match[3],
                "cfop": match[4],
                "unidade": match[5],
                "quantidade": match[6],
                "preco_unitario": match[7],
                "preco_total": match[8]
            }
            itens.append(item)
        
        return itens

    def nf_extrair_dados_adicionais(texto):
        """
        Extrai os dados adicionais da nota fiscal.
        """
        dados = {}
        
        # Baseado na estrutura real da nota, extrai informações adicionais simples
        bloco = ExtrairTextoNotaFiscal.nf_analisar_secao(texto, "DADOS ADICIONAIS")
        
        if bloco:
            # Procura por informações complementares
            if "Inf. Contribuinte:" in bloco:
                m_info = re.search(r"Inf\.\s*Contribuinte:\s*([^\n]+)", bloco)
                if m_info:
                    dados["informacoes_complementares"] = m_info.group(1).strip()
        
        # Garante que campos essenciais existam
        for campo in ["placa", "motorista", "informacoes_complementares"]:
            if campo not in dados:
                dados[campo] = ""
                
        return dados

    def nf_extrair_dados_nota(caminho_pdf):
        """
        Função principal que extrai todos os dados da nota fiscal.
        """
        texto_completo = ExtrairTextoNotaFiscal.extrair_texto_do_pdf(caminho_pdf)
        dados = {}
        dados["emissor"] = ExtrairTextoNotaFiscal.nf_extrair_info_emissor(texto_completo)
        dados["destinatario"] = ExtrairTextoNotaFiscal.nf_extrair_info_destinatario(texto_completo)
        dados["calculo_imposto"] = ExtrairTextoNotaFiscal.nf_extrair_calculo_imposto(texto_completo)
        dados["transportador"] = ExtrairTextoNotaFiscal.nf_extrair_info_transportador(texto_completo)
        dados["itens"] = ExtrairTextoNotaFiscal.nf_extrair_itens(texto_completo)
        dados["dados_adicionais"] = ExtrairTextoNotaFiscal.nf_extrair_dados_adicionais(texto_completo)
        return dados