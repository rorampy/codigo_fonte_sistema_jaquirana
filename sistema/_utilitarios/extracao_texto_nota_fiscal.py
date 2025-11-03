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
        # Captura Número e Série
        m_numero = re.search(r"Nº\s+(\d+)", texto)
        numero_nota = m_numero.group(1) if m_numero else None

        m_serie = re.search(r"Série\s*[:]*\s*(\d+)", texto)
        serie = m_serie.group(1) if m_serie else None

        # Captura Chave de Acesso (removendo espaços)
        m_chave = re.search(r"Chave de acesso\s*(?:\n|:)?\s*((?:\d+\s*)+)", texto)
        chave = "".join(m_chave.group(1).split()) if m_chave else None

        # Extração da razão social do emissor: após a linha com "Série",
        # captura as linhas seguintes que estejam em caixa alta.
        emissor = None
        linhas = texto.splitlines()
        indice_serie = None
        for i, linha in enumerate(linhas):
            if "Série" in linha:
                indice_serie = i
                break
        if indice_serie is not None:
            linhas_candidatas = []
            for j in range(indice_serie + 1, len(linhas)):
                linha_candidata = linhas[j].strip()
                # Se a linha não estiver vazia e estiver em caixa alta, considera parte do nome
                if linha_candidata and linha_candidata == linha_candidata.upper():
                    linhas_candidatas.append(linha_candidata)
                # Se já capturou alguma linha e encontrou uma linha que não seja todo em caixa alta,
                # considera que o nome terminou.
                elif linhas_candidatas:
                    break
            if linhas_candidatas:
                emissor = " ".join(linhas_candidatas)

        return {
            "razao_social_emissor": emissor,
            "numero_nota": numero_nota,
            "serie": serie,
            "chave_acesso": chave,
        }

    def nf_extrair_info_destinatario(texto):
        """
        Extrai os dados do destinatário a partir do bloco delimitado por "Destinatário/Remetente" e "Faturas".
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
        """
        bloco = ExtrairTextoNotaFiscal.nf_analisar_secao(
            texto, "Destinatário/Remetente", "Faturas"
        )
        linhas = bloco.splitlines()
        mapeamento = {
            "Nome / Razão Social": "nome_razao_social",
            "CNPJ/CPF": "cnpj_cpf",
            "Inscrição Estadual": "insc_estadual",
            "Endereço": "endereco",
            "Bairro": "bairro",
            "CEP": "cep",
            "Município": "municipio",
            "UF": "uf",
            "Data emissão": "data_emissao",
        }
        resultado = {}
        for i in range(len(linhas)):
            linha = linhas[i].strip()
            for cabecalho, chave in mapeamento.items():
                if linha.lower() == cabecalho.lower():
                    # Procura a próxima linha não vazia para pegar o valor
                    j = i + 1
                    while j < len(linhas) and not linhas[j].strip():
                        j += 1
                    if j < len(linhas):
                        resultado[chave] = linhas[j].strip()
        return resultado

    def nf_extrair_calculo_imposto(texto):
        """
        Extrai os dados da tabela "Cálculo do imposto" a partir do bloco delimitado por
        "Cálculo do imposto" e "Transportador/Volumes transportados".
        Retorna um dicionário com os campos:
        - base_calculo_icms
        - valor_icms
        - base_calculo_icms_subst
        - valor_icms_subst
        - valor_fcp_st
        - valor_total_produtos
        - valor_frete
        - valor_seguro
        - desconto
        - outras_despesas
        - valor_ipi
        - valor_total_nota
        """
        bloco = ExtrairTextoNotaFiscal.nf_analisar_secao(
            texto, "Cálculo do imposto", "Transportador/Volumes transportados"
        )
        linhas = bloco.splitlines()
        mapeamento = {
            "Base de cálculo do ICMS": "base_calculo_icms",
            "Valor do ICMS": "valor_icms",
            "Base de cálculo do ICMS Subst.": "base_calculo_icms_subst",
            "Valor do ICMS Subst.": "valor_icms_subst",
            "Valor do FCP ST": "valor_fcp_st",
            "Valor total dos produtos": "valor_total_produtos",
            "Valor do frete": "valor_frete",
            "Valor do seguro": "valor_seguro",
            "Desconto": "desconto",
            "Outras despesas acessórias": "outras_despesas",
            "Valor do IPI": "valor_ipi",
            "Valor total da nota": "valor_total_nota",
        }
        resultado = {}
        for i, linha in enumerate(linhas):
            linha = linha.strip()
            for cabecalho, chave in mapeamento.items():
                if linha.lower() == cabecalho.lower():
                    j = i + 1
                    while j < len(linhas) and not linhas[j].strip():
                        j += 1
                    if j < len(linhas):
                        resultado[chave] = linhas[j].strip()
        return resultado

    def nf_extrair_info_transportador(texto):
        """
        Extrai os dados do transportador a partir do bloco delimitado por
        "Transportador/Volumes transportados" e "Itens da nota fiscal".
        Campos extraídos:
        - Nome
        - CNPJ/CPF
        - Inscrição Estadual
        - Endereço
        - Município
        - UF
        """
        bloco = ExtrairTextoNotaFiscal.nf_analisar_secao(
            texto, "Transportador/Volumes transportados", "Itens da nota fiscal"
        )
        linhas = bloco.splitlines()
        mapeamento = {
            "Nome": "nome",
            "CNPJ/CPF": "cnpj_cpf",
            "Inscrição Estadual": "insc_estadual",
            "Endereço": "endereco",
            "Município": "municipio",
            "UF": "uf",
        }
        resultado = {}
        for i in range(len(linhas)):
            linha = linhas[i].strip()
            for cabecalho, chave in mapeamento.items():
                if linha.lower() == cabecalho.lower():
                    j = i + 1
                    while j < len(linhas) and not linhas[j].strip():
                        j += 1
                    if j < len(linhas):
                        resultado[chave] = linhas[j].strip()
        return resultado

    def nf_extrair_itens(texto):
        """
        Extrai descrição e peso (quantidade) de cada item da NF-e,
        suportando variações de unidade (TN, TON, tn, ton etc.).
        """
        print("=== DEBUG: Iniciando extração de itens ===")
        
        # obtém só o bloco de itens
        bloco = ExtrairTextoNotaFiscal.nf_analisar_secao(
            texto, "Itens da nota fiscal", "Cálculo do ISSQN"
        )
        
        print(f"=== DEBUG: Bloco inicial extraído ===")
        print(f"Tamanho: {len(bloco)} chars")
        print(f"Primeiros 200 chars: {bloco[:200]}")
        print(f"Últimos 100 chars: {bloco[-100:]}")

        # Se o bloco estiver vazio, usa o texto completo
        if not bloco or len(bloco.strip()) < 50:
            print("=== DEBUG: Bloco vazio/pequeno, usando texto completo ===")
            bloco = texto

        # junta tudo numa única string, removendo quebras e espaços extras
        linhas = [l.strip() for l in bloco.splitlines() if l.strip()]
        bloco_norm = " ".join(linhas)
        bloco_norm = re.sub(r"\s{2,}", " ", bloco_norm)
        
        print(f"=== DEBUG: Texto normalizado ===")
        print(f"Tamanho: {len(bloco_norm)} chars")
        print(f"Texto completo: {bloco_norm}")

        # Padrões ajustados para a estrutura real encontrada
        patterns = [
            # Padrão original (mantido para compatibilidade)
            re.compile(
                r"(?P<codigo>[A-Za-z0-9]+)\s+"
                r"(?P<descricao>.+?)\s+"
                r"(?P<ncm>\d{8})\s+"
                r"(?P<cst_csosn>\d+)\s+"
                r"(?P<cfop>\d\.\d{3})\s+"
                r"(?P<unidade>[A-Za-z³²¹]+)\s+"
                r"(?P<quantidade>[\d.,]+)\s+"
                r"(?P<preco_unitario>[\d.,]+)(?:\s+(?P<preco_total>[\d.,]+))?",
                re.IGNORECASE
            ),
            
            # Padrão específico para a contra-nota analisada
            re.compile(
                r"(?P<codigo>[A-Z0-9]+)\s+"  # LGFRS3235 etc
                r"(?P<descricao>[A-ZÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ][^0-9]+?)\s+"  # TORA - DIAMETRO...
                r"(?P<ncm>\d{8})\s+"  # 44012100
                r"(?P<cst>\d{3})\s+"  # 051
                r"(?P<cfop>\d\.\d{3})\s+"  # 1.102
                r"(?P<unidade>[A-Z]{1,4})"  # TO
                r"(?P<quantidade>[\d.,]+)"  # 48,000000
                r"(?P<preco_unitario>[\d.,]+)\s+"  # 38,000000
                r"(?P<preco_total>[\d.,]+)",  # 1.824,00
                re.IGNORECASE
            ),
            
            # Padrão mais flexível para casos onde quantidade e preço estão grudados
            re.compile(
                r"(?P<codigo>[A-Z0-9]+)\s+"
                r"(?P<descricao>[A-ZÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ][^0-9]+?)\s+"
                r"(?P<ncm>\d{8})\s+"
                r"(?P<cst>\d{2,3})\s+"
                r"(?P<cfop>\d\.\d{3})\s+"
                r"(?P<unidade>[A-Z]{1,4})"
                r"(?P<dados_numericos>[\d.,]+)\s+"  # Captura tudo junto
                r"(?P<preco_total>[\d.,]+)",
                re.IGNORECASE
            ),
            
            # Padrão mais simples
            re.compile(
                r"([A-Z0-9]+)\s+"  # código
                r"([A-ZÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ][^0-9]+?)\s+"  # descrição
                r"(\d{8})\s+"  # NCM
                r"(\d{2,3})\s+"  # CST
                r"(\d\.\d{3})\s+"  # CFOP
                r"([A-Z]{1,4})([\d.,]+)\s+"  # unidade + números
                r"([\d.,]+)",  # preço total
                re.IGNORECASE
            )
        ]
        
        itens = []
        
        for i, pattern in enumerate(patterns):
            print(f"\n=== DEBUG: Testando padrão {i+1} ===")
            print(f"Regex: {pattern.pattern}")
            
            matches = list(pattern.finditer(bloco_norm))
            print(f"Encontrados {len(matches)} matches")
            
            if matches:
                print(f"=== DEBUG: Processando {len(matches)} matches do padrão {i+1} ===")
                
                for j, m in enumerate(matches):
                    print(f"\n--- Match {j+1} ---")
                    print(f"Grupos completos: {m.groups()}")
                    
                    if hasattr(m, 'groupdict'):  # Grupos nomeados
                        grupos = m.groupdict()
                        print(f"Grupos nomeados: {grupos}")
                        
                        # Trata o caso especial onde quantidade e preço podem estar grudados
                        if 'dados_numericos' in grupos and grupos['dados_numericos']:
                            dados = grupos['dados_numericos']
                            print(f"Dados numéricos grudados: '{dados}'")
                            
                            # Exemplo: "48,0000000038,000000" -> quantidade: "48,000000", preço: "38,000000"
                            if len(dados.replace(',', '.').replace('.', '')) > 10:  # Se tem muitos dígitos
                                print("Tentando separar dados grudados...")
                                # Tenta dividir no meio ou procurar padrão
                                numeros = re.findall(r'[\d.,]+', dados)
                                print(f"Números encontrados: {numeros}")
                                
                                if len(numeros) >= 2:
                                    quantidade = numeros[0]
                                    preco_unitario = numeros[1]
                                    print(f"Separados - Qtd: '{quantidade}', Preço: '{preco_unitario}'")
                                else:
                                    # Tenta dividir string no meio aproximadamente
                                    meio = len(dados) // 2
                                    quantidade = dados[:meio]
                                    preco_unitario = dados[meio:]
                                    print(f"Divisão no meio - Qtd: '{quantidade}', Preço: '{preco_unitario}'")
                            else:
                                quantidade = dados
                                preco_unitario = dados
                                print(f"Usando dados como estão - Qtd: '{quantidade}', Preço: '{preco_unitario}'")
                        else:
                            quantidade = grupos.get("quantidade", "")
                            preco_unitario = grupos.get("preco_unitario", "")
                            print(f"Dados diretos - Qtd: '{quantidade}', Preço: '{preco_unitario}'")
                        
                        item = {
                            "descricao": grupos.get("descricao", "").strip(),
                            "quantidade": quantidade,
                            "preco_unitario": preco_unitario,
                        }
                        
                        # Adiciona campos extras se existirem
                        for campo in ["codigo", "ncm", "unidade", "preco_total", "cfop", "cst"]:
                            if grupos.get(campo):
                                item[campo] = grupos[campo]
                        
                        print(f"Item criado: {item}")
                                
                    else:  # Grupos numerados
                        grupos = m.groups()
                        print(f"Processando grupos numerados: {grupos}")
                        
                        # Para o padrão simples (último)
                        if len(grupos) >= 8:
                            print("Padrão com 8+ grupos")
                            # grupos: codigo, descricao, ncm, cst, cfop, unidade, numeros, preco_total
                            dados_numericos = grupos[6]  # Os números que vêm depois da unidade
                            print(f"Dados numéricos (grupo 6): '{dados_numericos}'")
                            
                            # Tenta extrair quantidade e preço unitário
                            numeros = re.findall(r'[\d.,]+', dados_numericos)
                            print(f"Números extraídos: {numeros}")
                            
                            if len(numeros) >= 2:
                                quantidade = numeros[0]
                                preco_unitario = numeros[1]
                                print(f"Qtd: '{quantidade}', Preço: '{preco_unitario}'")
                            else:
                                quantidade = dados_numericos
                                preco_unitario = grupos[7]  # preço total como fallback
                                print(f"Fallback - Qtd: '{quantidade}', Preço: '{preco_unitario}'")
                            
                            item = {
                                "codigo": grupos[0],
                                "descricao": grupos[1].strip(),
                                "ncm": grupos[2],
                                "quantidade": quantidade,
                                "preco_unitario": preco_unitario,
                                "unidade": grupos[5],
                                "preco_total": grupos[7]
                            }
                            
                            print(f"Item criado: {item}")
                        else:
                            print(f"Grupos insuficientes ({len(grupos)}), pulando...")
                            continue
                    
                    if item.get("descricao"):  # Só adiciona se tem descrição
                        itens.append(item)
                        print(f"Item adicionado à lista (total: {len(itens)})")
                    else:
                        print("Item sem descrição, não adicionado")
                
                if itens:  # Se encontrou itens, para de tentar outros padrões
                    print(f"=== DEBUG: Encontrou {len(itens)} itens com padrão {i+1}, parando ===")
                    break
            else:
                print("Nenhum match encontrado para este padrão")
        
        print(f"\n=== DEBUG: Resultado final ===")
        print(f"Total de itens extraídos: {len(itens)}")
        for i, item in enumerate(itens):
            print(f"Item {i+1}: {item}")
        
        return itens

    def nf_extrair_dados_adicionais(texto):
        """
        Extrai os dados adicionais a partir do bloco "Dados adicionais".
        """
        bloco = ExtrairTextoNotaFiscal.nf_analisar_secao(texto, "Dados adicionais")
        dados = {}
        m_placa = re.search(r"PLACA\s*[:\-]?\s*(\S+)", bloco, flags=re.IGNORECASE)
        m_motorista = re.search(
            r"MOTORISTA\s*[:\-]?\s*([^\n]+)", bloco, flags=re.IGNORECASE
        )
        dados["placa"] = m_placa.group(1).strip() if m_placa else None
        dados["motorista"] = m_motorista.group(1).strip() if m_motorista else None
        return dados

    def nf_extrair_dados_nota(caminho_pdf):
        texto_completo = ExtrairTextoNotaFiscal.extrair_texto_do_pdf(caminho_pdf)
        dados = {}
        dados["emissor"] = ExtrairTextoNotaFiscal.nf_extrair_info_emissor(texto_completo)
        dados["destinatario"] = ExtrairTextoNotaFiscal.nf_extrair_info_destinatario(texto_completo)
        dados["calculo_imposto"] = ExtrairTextoNotaFiscal.nf_extrair_calculo_imposto(texto_completo)
        dados["transportador"] = ExtrairTextoNotaFiscal.nf_extrair_info_transportador(texto_completo)
        dados["itens"] = ExtrairTextoNotaFiscal.nf_extrair_itens(texto_completo)
        dados["dados_adicionais"] = ExtrairTextoNotaFiscal.nf_extrair_dados_adicionais(texto_completo)
        return dados
