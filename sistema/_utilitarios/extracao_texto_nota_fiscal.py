import fitz
import re
import xml.etree.ElementTree as ET

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
        
        Suporta múltiplos formatos de NF:
        - Com seção "IDENTIFICAÇÃO DO EMITENTE"
        - Com texto "RECEBEMOS DE ... OS PRODUTOS"
        - Entre "NF-e" e "DANFE"
        """
        # Captura Número (formato: Nº. 000.006.044 ou Nº 7866)
        m_numero = re.search(r"Nº\.?\s*(\d{3}\.\d{3}\.\d{3}|\d+)", texto)
        numero_nota = m_numero.group(1).replace(".", "") if m_numero else None

        # Captura Série - aceita "Série 1" ou "SÉRIE 1"
        m_serie = re.search(r"S[ÉE]RIE\s+(\d+)", texto, re.IGNORECASE)
        serie = m_serie.group(1) if m_serie else None

        # Captura Chave de Acesso (removendo espaços)
        m_chave = re.search(r"CHAVE DE ACESSO\s*\n\s*((?:\d+\s*)+)", texto, re.IGNORECASE)
        chave = "".join(m_chave.group(1).split()) if m_chave else None

        # Extração da razão social do emissor - tenta múltiplos métodos
        emissor = None
        
        # MÉTODO 1: Procura por "RECEBEMOS DE ... OS PRODUTOS"
        # Este é o método mais confiável para o novo formato de NF
        m_recebemos = re.search(
            r"RECEBEMOS DE\s+([A-ZÀÁÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ\s&.-]+)\s+OS PRODUTOS",
            texto,
            re.IGNORECASE
        )
        if m_recebemos:
            emissor = m_recebemos.group(1).strip()
        
        # MÉTODO 2: Procura por "IDENTIFICAÇÃO DO EMITENTE" (formato tradicional)
        if not emissor:
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
        
        # MÉTODO 3: Fallback - usa regex simples para "IDENTIFICAÇÃO DO EMITENTE"
        if not emissor:
            m_emissor = re.search(
                r"IDENTIFICAÇÃO DO EMITENTE\s*\n\s*([A-ZÀÁÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ\s&.-]+)",
                texto
            )
            if m_emissor:
                emissor = m_emissor.group(1).strip()
        
        # MÉTODO 4: Procura entre "NF-e" e "DANFE" (formato alternativo)
        if not emissor:
            linhas = texto.splitlines()
            encontrou_nfe = False
            for linha in linhas:
                if "NF-e" in linha:
                    encontrou_nfe = True
                    continue
                if encontrou_nfe and "DANFE" in linha:
                    break
                if encontrou_nfe and linha.strip():
                    # Pula linhas de número e série
                    if not re.match(r'^(Nº|SÉRIE|S[ÉE]RIE|\d)', linha.strip(), re.IGNORECASE):
                        # Verifica se parece um nome de empresa (letras maiúsculas)
                        if linha.strip() == linha.strip().upper() and len(linha.strip()) > 5:
                            # Verifica se não é endereço
                            if not re.search(r'CEP:|AV |RUA |AL |Fone:', linha, re.IGNORECASE):
                                emissor = linha.strip()
                                break

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
        
        # Primeiro, tenta extrair o bloco específico do destinatário para evitar pegar dados do emissor
        # Isso é importante pois o PDF pode ter CNPJ/IE do emissor antes da seção do destinatário
        bloco_destinatario = None
        
        # Tenta encontrar o bloco do destinatário usando diferentes variações de formato
        pos_dest = -1
        for marcador in ["DESTINATÁRIO/REMETENTE", "DESTINATÁRIO / REMETENTE", "DESTINATÁRIO"]:
            pos_dest = texto.find(marcador)
            if pos_dest > 0:
                break
        
        pos_calc = texto.find("CÁLCULO DO IMPOSTO")
        
        if pos_dest > 0 and pos_calc > pos_dest:
            bloco_destinatario = texto[pos_dest:pos_calc]
        else:
            # Fallback para o texto completo se não encontrar o bloco
            bloco_destinatario = texto
        
        # Nome/Razão Social (após "DESTINATÁRIO / REMETENTE" ou variações)
        m_nome = re.search(
            r"NOME\s*/?\s*RAZÃO SOCIAL\s*\n\s*([^\n]+)",
            bloco_destinatario,
            re.IGNORECASE
        )
        if m_nome:
            resultado["nome_razao_social"] = m_nome.group(1).strip()

        # CNPJ/CPF - Procura no bloco do destinatário para não pegar do emissor
        m_cnpj = re.search(
            r"CNPJ\s*/?\s*CPF\s*\n\s*([\d./-]+)",
            bloco_destinatario,
            re.IGNORECASE
        )
        if m_cnpj:
            resultado["cnpj_cpf"] = m_cnpj.group(1).strip()

        # Inscrição Estadual - Procura no bloco do destinatário
        m_ie = re.search(
            r"INSCRIÇÃO ESTADUAL\s*\n\s*(\d+)",
            bloco_destinatario,
            re.IGNORECASE
        )
        if m_ie:
            resultado["insc_estadual"] = m_ie.group(1).strip()

        # Endereço
        m_endereco = re.search(
            r"ENDEREÇO\s*\n\s*([^\n]+)",
            bloco_destinatario,
            re.IGNORECASE
        )
        if m_endereco:
            resultado["endereco"] = m_endereco.group(1).strip()

        # Bairro - aceita ambos os formatos "BAIRRO" e "BAIRRO / DISTRITO"
        m_bairro = re.search(
            r"BAIRRO\s*(?:/\s*DISTRITO)?\s*\n\s*([^\n]+)",
            bloco_destinatario,
            re.IGNORECASE
        )
        if m_bairro:
            resultado["bairro"] = m_bairro.group(1).strip()

        # CEP - aceita formatos com e sem pontuação (89.380-000 ou 89380000)
        m_cep = re.search(
            r"CEP\s*\n\s*([\d.-]+)",
            bloco_destinatario,
            re.IGNORECASE
        )
        if m_cep:
            resultado["cep"] = m_cep.group(1).strip()

        # Município
        m_municipio = re.search(
            r"MUNICÍPIO\s*\n\s*([^\n]+)",
            bloco_destinatario,
            re.IGNORECASE
        )
        if m_municipio:
            resultado["municipio"] = m_municipio.group(1).strip()

        # UF
        m_uf = re.search(
            r"\bUF\s*\n\s*([A-Z]{2})\b",
            bloco_destinatario,
            re.IGNORECASE
        )
        if m_uf:
            resultado["uf"] = m_uf.group(1).strip().upper()

        # Data de emissão - aceita "DATA DA EMISSÃO" e "DATA EMISSÃO"
        m_data_emissao = re.search(
            r"DATA\s*(?:DA)?\s*EMISSÃO\s*\n\s*(\d{2}/\d{2}/\d{4})",
            bloco_destinatario,
            re.IGNORECASE
        )
        if m_data_emissao:
            resultado["data_emissao"] = m_data_emissao.group(1).strip()

        # Data de saída/entrada - aceita "DATA DA SAÍDA/ENTRADA", "DATA SAÍDA" e variações
        m_data_saida = re.search(
            r"DATA\s*(?:DA)?\s*SAÍDA(?:\s*/\s*ENTRADA)?\s*\n\s*(\d{2}/\d{2}/\d{4})",
            bloco_destinatario,
            re.IGNORECASE
        )
        if m_data_saida:
            resultado["data_saida_entrada"] = m_data_saida.group(1).strip()

        return resultado

    def nf_extrair_calculo_imposto(texto):
        """
        Extrai os dados da tabela "Cálculo do imposto".
        Suporta diferentes formatos de NF (padrões variados de labels).
        """
        resultado = {}
        
        # Mapeamento dos campos com múltiplos padrões para cada campo
        # Cada campo pode ter várias variações de label
        campos_multiplos = {
            "base_calculo_icms": [
                r"BASE DE CÁLC(?:ULO)?(?:\.)?\s*(?:DO)?\s*ICMS\s*\n\s*([\d.,]+)",
                r"BASE DE CÁLCULO DO ICMS\s*\n\s*([\d.,]+)",
            ],
            "valor_icms": [
                r"VALOR DO ICMS\s*\n\s*([\d.,]+)",
            ],
            "base_calculo_icms_subst": [
                r"BASE DE CÁLC(?:ULO)?(?:\.)?\s*(?:DO)?\s*ICMS\s*S(?:UBST)?(?:\.)?\s*T(?:\.)?\s*\n\s*([\d.,]+)",
                r"BASE DE CÁLC\.\s+ICMS\s+S\.T\.\s*\n\s*([\d.,]+)",
            ],
            "valor_icms_subst": [
                r"VALOR DO ICMS SUBST(?:\.)?\s*\n\s*([\d.,]+)",
            ],
            "valor_fcp_st": [
                r"V\.?\s*FCP\s*UF\s*DEST\.?\s*\n\s*([\d.,]+)",
            ],
            "valor_total_produtos": [
                r"V(?:ALOR)?(?:\.)?\s*TOTAL\s*(?:DOS)?\s*PRODUTOS\s*\n\s*([\d.,]+)",
                r"VALOR TOTAL DOS PRODUTOS\s*\n\s*([\d.,]+)",
            ],
            "valor_frete": [
                r"VALOR DO FRETE\s*\n\s*([\d.,]+)",
            ],
            "valor_seguro": [
                r"VALOR DO SEGURO\s*\n\s*([\d.,]+)",
            ],
            "desconto": [
                r"DESCONTO\s*\n\s*([\d.,]+)",
            ],
            "outras_despesas": [
                r"OUTRAS\s*DESPESAS(?:\s*ACESSÓRIAS)?\s*\n\s*([\d.,]+)",
            ],
            "valor_ipi": [
                r"VALOR\s*(?:TOTAL)?\s*(?:DO)?\s*IPI\s*\n\s*([\d.,]+)",
            ],
            "valor_total_nota": [
                r"V(?:ALOR)?(?:\.)?\s*TOTAL\s*DA\s*NOTA\s*\n\s*([\d.,]+)",
                r"VALOR TOTAL DA NOTA\s*\n\s*([\d.,]+)",
            ],
        }
        
        for chave, patterns in campos_multiplos.items():
            for pattern in patterns:
                m = re.search(pattern, texto, re.IGNORECASE)
                if m:
                    resultado[chave] = m.group(1).strip()
                    break  # Se encontrou, não precisa tentar os outros padrões
        
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
        Suporta múltiplos formatos de NF:
        - Formato em linha única (tradicional)
        - Formato multilinha (cada campo em linha separada)
        """
        # Localiza o bloco de produtos - tenta diferentes variações do marcador
        bloco = ExtrairTextoNotaFiscal.nf_analisar_secao(
            texto, "DADOS DOS PRODUTOS / SERVIÇOS", "DADOS ADICIONAIS"
        )
        
        if not bloco:
            # Tenta variação sem espaços nas barras
            bloco = ExtrairTextoNotaFiscal.nf_analisar_secao(
                texto, "DADOS DOS PRODUTOS/SERVIÇOS", "CÁLCULO DO ISSQN"
            )
        
        if not bloco:
            # Tenta outra variação
            bloco = ExtrairTextoNotaFiscal.nf_analisar_secao(
                texto, "DADOS DOS PRODUTOS/SERVIÇOS", "DADOS ADICIONAIS"
            )
        
        if not bloco:
            bloco = texto
        
        itens = []
        
        # PADRÃO 1: Formato multilinha (cada campo em linha separada)
        # Estrutura:
        # 01
        # TORA - DIAMETRO 18-25 COMRIMENTO 2,15 METROS
        # 44032100
        # 000
        # 6102
        # Ton 56,2600
        # 312,00000
        # 17.553,12
        pattern_multiline = re.compile(
            r"^(\d{1,3})\s*$\s*"  # Código do item em linha separada (01, 02, etc)
            r"([A-ZÀÁÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ][^\n]+?)\s*"  # Descrição do produto
            r"(\d{8})\s*"  # NCM (8 dígitos)
            r"(\d{3})\s*"  # CST (3 dígitos)
            r"(\d{4})\s*"  # CFOP (4 dígitos)
            r"([A-Za-z]+)\s+([\d.,]+)\s*"  # Unidade + Quantidade
            r"([\d.,]+)\s*"  # Valor unitário
            r"([\d.,]+)",  # Valor total
            re.MULTILINE | re.IGNORECASE
        )
        
        matches = pattern_multiline.findall(bloco)
        
        # PADRÃO 2: Formato em linha única (tradicional)
        # Estrutura: 01 TORETE DE PINUS 44032200 0/00 6102 Ton 38,0000 228,7400 8.692,12
        if not matches:
            pattern_inline = re.compile(
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
            matches = pattern_inline.findall(bloco)
        
        for match in matches:
            # Normaliza o CST - se vier só números (000), formata como 0/00
            cst_valor = match[3]
            if len(cst_valor) == 3 and cst_valor.isdigit():
                cst_valor = f"{cst_valor[0]}/{cst_valor[1:]}"
            
            item = {
                "codigo": match[0],
                "descricao": match[1].strip(),
                "ncm": match[2],
                "cst_csosn": cst_valor,
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
        Inclui: placa, motorista e informações complementares.
        """
        dados = {}
        
        # Baseado na estrutura real da nota, extrai informações adicionais
        bloco = ExtrairTextoNotaFiscal.nf_analisar_secao(texto, "DADOS ADICIONAIS")
        
        if bloco:
            # Procura por informações complementares - múltiplos formatos
            if "Inf. Contribuinte:" in bloco:
                m_info = re.search(r"Inf\.\s*Contribuinte:\s*([^\n]+)", bloco)
                if m_info:
                    dados["informacoes_complementares"] = m_info.group(1).strip()
            elif "OBSERVAÇÕES" in bloco:
                # Extrai texto após OBSERVAÇÕES até RESERVADO AO FISCO ou fim do bloco
                m_obs = re.search(r"OBSERVAÇÕES\s*\n\s*(.*?)(?:RESERVADO AO FISCO|$)", bloco, re.DOTALL | re.IGNORECASE)
                if m_obs:
                    obs_texto = m_obs.group(1).strip()
                    # Limpa e normaliza o texto
                    obs_texto = re.sub(r'\s+', ' ', obs_texto)
                    dados["informacoes_complementares"] = obs_texto
        
        # Tenta extrair placa do bloco de transportador
        bloco_transp = ExtrairTextoNotaFiscal.nf_analisar_secao(
            texto, "TRANSPORTADOR", "DADOS DOS PRODUTOS"
        )
        if bloco_transp:
            # Placa do veículo
            m_placa = re.search(r"PLACA\s*(?:DO)?\s*(?:VEÍCULO)?\s*\n\s*([A-Z]{3}[\-]?\d[A-Z0-9]\d{2})", bloco_transp, re.IGNORECASE)
            if m_placa:
                dados["placa"] = m_placa.group(1).strip().upper()
        
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
    

    def nf_extrair_dados_nota_xml(caminho_xml):
        """
        Extrai dados da nota fiscal a partir do arquivo XML.
        """
        
        try:
            tree = ET.parse(caminho_xml)
            root = tree.getroot()
            
            
            ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
            
            
            inf_nfe = root.find('.//nfe:infNFe', ns)
            if inf_nfe is None:
            
                inf_nfe = root.find('.//infNFe')
                ns = None
            
            dados = {
                "emissor": {},
                "destinatario": {},
                "calculo_imposto": {},
                "transportador": {},
                "itens": [],
                "dados_adicionais": {}
            }
            
            if inf_nfe is not None:
                #  DADOS DO EMISSOR 
                emit = inf_nfe.find('nfe:emit', ns) if ns else inf_nfe.find('emit')
                if emit is not None:
                    numero_nota_elem = inf_nfe.find('nfe:ide/nfe:nNF', ns) if ns else inf_nfe.find('ide/nNF')
                    serie_elem = inf_nfe.find('nfe:ide/nfe:serie', ns) if ns else inf_nfe.find('ide/serie')
                    nome_elem = emit.find('nfe:xNome', ns) if ns else emit.find('xNome')
                    
                    numero_nota_formatado = ""
                    if numero_nota_elem is not None:
                        numero_original = numero_nota_elem.text
                        numero_nota_formatado = numero_original.zfill(6)

                    dados["emissor"] = {
                        "razao_social_emissor": nome_elem.text if nome_elem is not None else "",
                        "numero_nota": numero_nota_formatado,
                        "serie": serie_elem.text if serie_elem is not None else "",
                        "chave_acesso": inf_nfe.get('Id', '').replace('NFe', '') if inf_nfe.get('Id') else ""
                    }
                
                #  DADOS DESTINATÁRIO 
                dest = inf_nfe.find('nfe:dest', ns) if ns else inf_nfe.find('dest')
                if dest is not None:
                    # Data de Emissão
                    data_emissao_elem = inf_nfe.find('nfe:ide/nfe:dhEmi', ns) if ns else inf_nfe.find('ide/dhEmi')
                    data_emissao = ""
                    if data_emissao_elem is not None:
                        data_emissao = data_emissao_elem.text[:10]  
                        data_emissao = '/'.join(reversed(data_emissao.split('-')))
                    
                    # Data de saída
                    data_saida_elem = inf_nfe.find('nfe:ide/nfe:dhSaiEnt', ns) if ns else inf_nfe.find('ide/dhSaiEnt')
                    data_saida = ""
                    if data_saida_elem is not None:
                        data_saida = data_saida_elem.text[:10]
                        data_saida = '/'.join(reversed(data_saida.split('-')))
                    
                    # Nome do destinatário
                    nome_dest_elem = dest.find('nfe:xNome', ns) if ns else dest.find('xNome')
                    
                    # CNPJ/CPF do destinatário
                    cnpj_elem = dest.find('nfe:CNPJ', ns) if ns else dest.find('CNPJ')
                    cpf_elem = dest.find('nfe:CPF', ns) if ns else dest.find('CPF')
                    cnpj_cpf = ""
                    if cnpj_elem is not None:
                        cnpj_cpf = cnpj_elem.text
                    elif cpf_elem is not None:
                        cnpj_cpf = cpf_elem.text
                    
                    # Inscrição Estadual
                    ie_elem = dest.find('nfe:IE', ns) if ns else dest.find('IE')
                    
                    
                    endereco_elem = dest.find('nfe:enderDest/nfe:xLgr', ns) if ns else dest.find('enderDest/xLgr')
                    numero_elem = dest.find('nfe:enderDest/nfe:nro', ns) if ns else dest.find('enderDest/nro')
                    bairro_elem = dest.find('nfe:enderDest/nfe:xBairro', ns) if ns else dest.find('enderDest/xBairro')
                    cep_elem = dest.find('nfe:enderDest/nfe:CEP', ns) if ns else dest.find('enderDest/CEP')
                    municipio_elem = dest.find('nfe:enderDest/nfe:xMun', ns) if ns else dest.find('enderDest/xMun')
                    uf_elem = dest.find('nfe:enderDest/nfe:UF', ns) if ns else dest.find('enderDest/UF')
                    
                    
                    endereco = ""
                    if endereco_elem is not None:
                        endereco = endereco_elem.text
                        if numero_elem is not None:
                            endereco += f", {numero_elem.text}"
                    
                    dados["destinatario"] = {
                        "nome_razao_social": nome_dest_elem.text if nome_dest_elem is not None else "",
                        "cnpj_cpf": cnpj_cpf,
                        "insc_estadual": ie_elem.text if ie_elem is not None else "",
                        "endereco": endereco,
                        "bairro": bairro_elem.text if bairro_elem is not None else "",
                        "cep": cep_elem.text if cep_elem is not None else "",
                        "municipio": municipio_elem.text if municipio_elem is not None else "",
                        "uf": uf_elem.text if uf_elem is not None else "",
                        "data_emissao": data_emissao,
                        "data_saida_entrada": data_saida
                    }
                
                
                total = inf_nfe.find('nfe:total/nfe:ICMSTot', ns) if ns else inf_nfe.find('total/ICMSTot')
                if total is not None:
                    valor_nf_elem = total.find('nfe:vNF', ns) if ns else total.find('vNF')
                    base_icms_elem = total.find('nfe:vBC', ns) if ns else total.find('vBC')
                    valor_icms_elem = total.find('nfe:vICMS', ns) if ns else total.find('vICMS')
                    base_icms_st_elem = total.find('nfe:vBCST', ns) if ns else total.find('vBCST')
                    valor_icms_st_elem = total.find('nfe:vST', ns) if ns else total.find('vST')
                    valor_fcp_elem = total.find('nfe:vFCPUFDest', ns) if ns else total.find('vFCPUFDest')
                    valor_produtos_elem = total.find('nfe:vProd', ns) if ns else total.find('vProd')
                    valor_frete_elem = total.find('nfe:vFrete', ns) if ns else total.find('vFrete')
                    valor_seguro_elem = total.find('nfe:vSeg', ns) if ns else total.find('vSeg')
                    desconto_elem = total.find('nfe:vDesc', ns) if ns else total.find('vDesc')
                    outras_desp_elem = total.find('nfe:vOutro', ns) if ns else total.find('vOutro')
                    valor_ipi_elem = total.find('nfe:vIPI', ns) if ns else total.find('vIPI')
                    
                    dados["calculo_imposto"] = {
                        "valor_total_nota": valor_nf_elem.text if valor_nf_elem is not None else "",
                        "base_calculo_icms": base_icms_elem.text if base_icms_elem is not None else "",
                        "valor_icms": valor_icms_elem.text if valor_icms_elem is not None else "",
                        "base_calculo_icms_subst": base_icms_st_elem.text if base_icms_st_elem is not None else "",
                        "valor_icms_subst": valor_icms_st_elem.text if valor_icms_st_elem is not None else "",
                        "valor_fcp_st": valor_fcp_elem.text if valor_fcp_elem is not None else "",
                        "valor_total_produtos": valor_produtos_elem.text if valor_produtos_elem is not None else "",
                        "valor_frete": valor_frete_elem.text if valor_frete_elem is not None else "",
                        "valor_seguro": valor_seguro_elem.text if valor_seguro_elem is not None else "",
                        "desconto": desconto_elem.text if desconto_elem is not None else "",
                        "outras_despesas": outras_desp_elem.text if outras_desp_elem is not None else "",
                        "valor_ipi": valor_ipi_elem.text if valor_ipi_elem is not None else ""
                    }
                
                #  DADOS DO TRANSPORTADOR 
                transp = inf_nfe.find('nfe:transp', ns) if ns else inf_nfe.find('transp')
                if transp is not None:
                    # Modalidade de frete
                    mod_frete_elem = transp.find('nfe:modFrete', ns) if ns else transp.find('modFrete')
                    mod_frete = mod_frete_elem.text if mod_frete_elem is not None else ""
                    
                    # Dados do transportador (se houver)
                    transporta = transp.find('nfe:transporta', ns) if ns else transp.find('transporta')
                    
                    transportador_nome = ""
                    transportador_cnpj_cpf = ""
                    transportador_ie = ""
                    
                    if transporta is not None:
                        nome_transp_elem = transporta.find('nfe:xNome', ns) if ns else transporta.find('xNome')
                        cnpj_transp_elem = transporta.find('nfe:CNPJ', ns) if ns else transporta.find('CNPJ')
                        cpf_transp_elem = transporta.find('nfe:CPF', ns) if ns else transporta.find('CPF')
                        ie_transp_elem = transporta.find('nfe:IE', ns) if ns else transporta.find('IE')
                        
                        transportador_nome = nome_transp_elem.text if nome_transp_elem is not None else ""
                        
                        if cnpj_transp_elem is not None:
                            transportador_cnpj_cpf = cnpj_transp_elem.text
                        elif cpf_transp_elem is not None:
                            transportador_cnpj_cpf = cpf_transp_elem.text
                        
                        transportador_ie = ie_transp_elem.text if ie_transp_elem is not None else ""
                    else:
                        # Se não há transportador específico, usar modalidade de frete
                        if mod_frete == "0":
                            transportador_nome = "Por conta do Emitente"
                        elif mod_frete == "1":
                            transportador_nome = "Por conta do Destinatário"
                        elif mod_frete == "2":
                            transportador_nome = "Por conta de Terceiros"
                        elif mod_frete == "9":
                            transportador_nome = "Sem cobrança de frete"
                    
                    dados["transportador"] = {
                        "nome": transportador_nome,
                        "cnpj_cpf": transportador_cnpj_cpf,
                        "insc_estadual": transportador_ie
                    }
                    
                    #  DADOS DO VEÍCULO/PLACA 
                    veiculo = transp.find('nfe:veicTransp', ns) if ns else transp.find('veicTransp')
                    placa = ""
                    if veiculo is not None:
                        placa_elem = veiculo.find('nfe:placa', ns) if ns else veiculo.find('placa')
                        placa = placa_elem.text if placa_elem is not None else ""
                    
                    dados["dados_adicionais"] = {
                        "placa": placa,
                        "motorista": "",  # XML não possui dados do motorista normalmente
                        "informacoes_complementares": ""
                    }
                
                #  ITENS DA NOTA 
                itens = inf_nfe.findall('nfe:det', ns) if ns else inf_nfe.findall('det')
                for item in itens:
                    prod = item.find('nfe:prod', ns) if ns else item.find('prod')
                    if prod is not None:
                        codigo_elem = prod.find('nfe:cProd', ns) if ns else prod.find('cProd')
                        desc_elem = prod.find('nfe:xProd', ns) if ns else prod.find('xProd')
                        ncm_elem = prod.find('nfe:NCM', ns) if ns else prod.find('NCM')
                        cfop_elem = prod.find('nfe:CFOP', ns) if ns else prod.find('CFOP')
                        unidade_elem = prod.find('nfe:uCom', ns) if ns else prod.find('uCom')
                        qtd_elem = prod.find('nfe:qCom', ns) if ns else prod.find('qCom')
                        valor_un_elem = prod.find('nfe:vUnCom', ns) if ns else prod.find('vUnCom')
                        valor_total_elem = prod.find('nfe:vProd', ns) if ns else prod.find('vProd')
                        
                        # CST/CSOSN do ICMS
                        imposto = item.find('nfe:imposto', ns) if ns else item.find('imposto')
                        cst_csosn = ""
                        if imposto is not None:
                            icms = imposto.find('nfe:ICMS', ns) if ns else imposto.find('ICMS')
                            if icms is not None:
                                # Procura por qualquer tag que contenha CST ou CSOSN
                                for child in icms:
                                    cst_elem = child.find('nfe:CST', ns) if ns else child.find('CST')
                                    csosn_elem = child.find('nfe:CSOSN', ns) if ns else child.find('CSOSN')
                                    if cst_elem is not None:
                                        cst_csosn = f"0/{cst_elem.text}"
                                        break
                                    elif csosn_elem is not None:
                                        cst_csosn = csosn_elem.text
                                        break
                        
                        item_dados = {
                            "codigo": item.get('nItem', ''),
                            "descricao": desc_elem.text if desc_elem is not None else "",
                            "ncm": ncm_elem.text if ncm_elem is not None else "",
                            "cst_csosn": cst_csosn,
                            "cfop": cfop_elem.text if cfop_elem is not None else "",
                            "unidade": unidade_elem.text if unidade_elem is not None else "",
                            "quantidade": qtd_elem.text if qtd_elem is not None else "0",
                            "preco_unitario": valor_un_elem.text if valor_un_elem is not None else "0",
                            "preco_total": valor_total_elem.text if valor_total_elem is not None else "0"
                        }
                        dados["itens"].append(item_dados)
                
                #  INFORMAÇÕES COMPLEMENTARES 
                inf_adic = inf_nfe.find('nfe:infAdic', ns) if ns else inf_nfe.find('infAdic')
                if inf_adic is not None:
                    info_compl_elem = inf_adic.find('nfe:infCpl', ns) if ns else inf_adic.find('infCpl')
                    if info_compl_elem is not None:
                        dados["dados_adicionais"]["informacoes_complementares"] = info_compl_elem.text
            
            return dados
            
        except Exception as e:
            print(f"Erro ao processar XML: {e}")
            return {
                "emissor": {},
                "destinatario": {},
                "calculo_imposto": {},
                "transportador": {},
                "itens": [],
                "dados_adicionais": {}
            }