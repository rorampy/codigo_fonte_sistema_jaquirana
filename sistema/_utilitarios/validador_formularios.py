import re
import requests
from datetime import datetime
from werkzeug.datastructures import FileStorage
from sistema.models_views.parametrizacao.variavel_sistema_model import VariavelSistemaModel

class ValidaForms:
    def campo_obrigatorio(campos):
        '''
        Recebe como parâmetro um dicionario ("chave": ["Label", valor_input]).
        Um laço for varre item a item, caso encontre algum valor_input com valor
        None (vazio) ou sem ao menos uma letra ou número em sua composição,
        ou o valor "R$ 0,00", esse registro é armazenado no dicionario resultado 
        ("chave": "mensagem"). O retorno pode ser o dicionário contendo os erros
        encontrados ou com a informação de sucesso caso não encontre nenhum erro.
        '''
        resultado = {}
        contador = 0
        for chave, valores in campos.items():
            valor_input = valores[1]
        
            if valor_input is None or valor_input == "R$ 0,00":
                resultado[f'{chave}'] = f'O Campo {valores[0]} é obrigatório!'
                contador += 1
            # Verifica se é um float e se o valor é igual a 0.0
            elif isinstance(valor_input, float) and valor_input == 0.0:
                resultado[f'{chave}'] = f'O Campo {valores[0]} é obrigatório!'
                contador += 1
            # Verifica se o valor_input é uma string vazia ou contém apenas espaços
            elif isinstance(valor_input, str) and (not valor_input.strip() or not any(c.isalnum() for c in valor_input)):
                resultado[f'{chave}'] = f'O Campo {valores[0]} é obrigatório!'
                contador += 1
            
            # Validação de arquivo vazio
            elif isinstance(valor_input, FileStorage) and not valor_input.filename.strip():
                resultado[chave] = f'O Campo {valores[0]} é obrigatório!'
                contador += 1

        if contador == 0:
            resultado['validado'] = 'Nenhum erro encontrado relacionado a campos obrigatórios'

        return resultado


    def verificar_recaptcha_google(recaptcha_response):
        """
        Verifica o reCAPTCHA.

        Args:
            recaptcha_response: O valor do campo `g-recaptcha-response` do formulário.

        Returns:
            True se o reCAPTCHA for válido, False caso contrário.
        """
        
        variaveis = VariavelSistemaModel.obter_variaveis_de_sistema_por_id(1)

        url = "https://www.google.com/recaptcha/api/siteverify"
        data = {
            "secret": variaveis.chave_priv_google_recaptcha,
            "response": recaptcha_response,
        }
        response = requests.post(url, data=data)
        
        print(f'Resultado ReCAPTCHA ===> {response.json()}')
        
        return response.json()

    def validar_cpf(cpf):
        '''
        Recebe um número de CPF por parâmetro e verifica se é valido ou não.
        Retorna um dicionário com a chave 'cpf' seguido do erro de validação quando 
        quando encontrado ou retorna um dicionário com uma chave 'validado' seguido
        da informação de sucesso.
        '''

        resultado = {}
        contador = 0

        # Remove todos os caracteres não numéricos do CPF
        cpf = ''.join(filter(str.isdigit, cpf))

        # Verifica se o CPF possui 11 dígitos
        if len(cpf) != 11:
            resultado['cpf'] = f'O CPF deve possuir 11 dígitos'
            contador += 1

            return resultado

        # Verifica se todos os dígitos são iguais
        if cpf == cpf[0] * 11:
            resultado['cpf'] = f'O CPF não pode possuir todos os números iguais'
            contador += 1

            return resultado

        # Verifica o primeiro dígito verificador
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        resto = soma % 11
        if resto < 2:
            digito_verif1 = 0
        else:
            digito_verif1 = 11 - resto
        if int(cpf[9]) != digito_verif1:
            resultado['cpf'] = f'CPF com 1º digito verificador inválido!'
            contador += 1

            return resultado

        # Verifica o segundo dígito verificador
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        resto = soma % 11
        if resto < 2:
            digito_verif2 = 0
        else:
            digito_verif2 = 11 - resto
        if int(cpf[10]) != digito_verif2:
            resultado['cpf'] = f'CPF com 2º digito verificador inválido!'
            contador += 1

            return resultado
        
        # CPF válido
        if contador == 0:
            resultado['validado'] = 'Nenhum erro encontrado relacionado a validação do CPF!'
            return resultado
    
    def validar_cnpj(cnpj):
        """
        Recebe um número de CNPJ por parâmetro e verifica se é válido ou não.
        Retorna um dicionário com a chave 'cnpj' seguido do erro de validação quando
        encontrado ou retorna um dicionário com uma chave 'validado' seguido
        da informação de sucesso.
        """
        resultado = {}

        # Remove caracteres não numéricos
        cnpj = ''.join(filter(str.isdigit, cnpj))

        # Verifica se o CNPJ possui 14 dígitos
        if len(cnpj) != 14:
            resultado['cnpj'] = 'O CNPJ deve possuir 14 dígitos'
            return resultado

        # Verifica se todos os dígitos são iguais
        if cnpj == cnpj[0] * 14:
            resultado['cnpj'] = 'O CNPJ não pode possuir todos os números iguais'
            return resultado

        # Cálculo dos dígitos verificadores
        def calcular_digito(cnpj, multiplicadores):
            soma = sum(int(digito) * multiplicador for digito, multiplicador in zip(cnpj, multiplicadores))
            resto = soma % 11
            return '0' if resto < 2 else str(11 - resto)

        # Multiplicadores para os dígitos verificadores
        multiplicadores1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        multiplicadores2 = [6] + multiplicadores1

        primeiro_digito = calcular_digito(cnpj[:-2], multiplicadores1)
        segundo_digito = calcular_digito(cnpj[:-1], multiplicadores2)

        if cnpj[-2:] != primeiro_digito + segundo_digito:
            resultado['cnpj'] = 'CNPJ com dígito verificador inválido!'
            return resultado

        resultado['validado'] = 'Nenhum erro encontrado relacionado à validação do CNPJ!'
        return resultado


    def validar_e_converter_valor_input_brl(valor):
        '''
        Recebe como parâmetro um valor vindo de um input BRL e converte para 
        o formato int em centavos (vezes 100) para armazenar no banco. 
        '''
        try:
            padrao = r'^R\$\s*\d{0,3}(?:\.\d{3})*(?:,\d{2})?$'
            if re.match(padrao, valor):
                valor_sem_simbolos = re.sub(r'[^\d,]', '', valor)
                valor_float = float(valor_sem_simbolos.replace(',', '.'))
                valor_100 = valor_float * 100
                return valor_100
        except ValueError as erro:
            return f'Houve um erro ao tentar realizaar a conversão: {erro}'
        
    
    def validar_email(email):
        '''
        Recebe como parâmetro um email e válida se o mesmo está no formato
        usuario@provedor.extensao. Caso esteja correto retorna um dicionário 
        com a chave 'validado' e o valor contendo uma mensagem de sucesso. 
        Caso esteja incorreto retorna um dicionário com a chave 'email', e
        a mensagem de erro.
        '''

        resultado = {}
        # Expressão regular para validar email (usuario@provedor.extensao)
        padrao = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    
        if re.match(padrao, email):
            resultado['validado'] = 'Nenhum erro encontrado relacionado a validação do e-mail!'
            return resultado
        else:
            resultado['email'] = 'Digite um e-mail válido!'
            return resultado
        
    
    def validar_e_converter_data_de_br_para_en(data):
        '''
        Recebe por parâmetro uma data no formato dd/mm/yyyy e retorma
        em formato internacional yyyy-mm-dd.
        Antes da conversão são realizadas verificações e caso reprove
        em alguma verificação o método retornará um dicionário onde a
        chave será o identificador (no caso uma "data") e a o valor 
        será o erro encontrado.
        '''
        resultado = {}
        data = str(data)

        # Verifica se a data está no formato correto
        if len(data) != 10 or data[2] != '/' or data[5] != '/':
            resultado['data'] = f'A data informada contém erros!'
            return resultado

        # Extrai os componentes da data
        dia, mes, ano = data.split('/')

        # Verifica se os componentes são numéricos
        if not dia.isdigit() or not mes.isdigit() or not ano.isdigit():
            resultado['data'] = f'A data informada deve ser um número!'
            return resultado

        # Verifica se os componentes são válidos
        dia = int(dia)
        mes = int(mes)
        ano = int(ano)
        if dia < 1 or dia > 31 or mes < 1 or mes > 12 or ano < datetime.now().year - 120 or ano > datetime.now().year:
            resultado['data'] = f'Dia deve estar entre 1 e 31, mês entre 1 e 12 e ano entre {datetime.now().year - 120} e ano atual!'
            return resultado
            
        # Formata a data no novo formato
        resultado['validado'] = f'{ano:04d}-{mes:02d}-{dia:02d}'
        return resultado
    

    def validar_e_converter_data_de_en_para_br(data):
        '''
        Recebe por parâmetro uma data no formato internacional yyyy-mm-dd
        e retorna no formato brasileiro dd/mm/yyyy.
        Antes da conversão são realizadas verificações e caso reprove
        em alguma verificação o método retornará um dicionário onde a
        chave será o identificador (no caso uma "data") e a o valor 
        será o erro encontrado.
        '''
        resultado = {}
        data = str(data)

        # Verifica se a data está no formato correto
        if len(data) != 10 or data[4] != '-' or data[7] != '-':
            resultado['data'] = f'A data informada contém erros!'
            return resultado
    
        # Extrai os componentes da data
        ano, mes, dia = data.split('-')

        # Verifica se os componentes são numéricos
        if not dia.isdigit() or not mes.isdigit() or not ano.isdigit():
            resultado['data'] = f'A data informada deve ser um número!'
            return resultado
    
        # Verifica se os componentes são válidos
        dia = int(dia)
        mes = int(mes)
        ano = int(ano)
        if dia < 1 or dia > 31 or mes < 1 or mes > 12 or ano < datetime.now().year - 120 or ano > datetime.now().year:
            resultado['data'] = f'Dia deve estar entre 1 e 31, mês entre 1 e 12 e ano entre {datetime.now().year - 120} e ano atual!'
            return resultado
    
        # Formata a data no novo formato
        resultado['validado'] = f'{dia:02d}/{mes:02d}/{ano:04d}'
        return resultado
    
    
    def converter_numero_brasileiro_para_float(valor):
        '''
        Converte um número no formato brasileiro (ex: "1.234,56" ou "56,2600") 
        para float (ex: 1234.56 ou 56.26).
        
        Parâmetros:
            valor: String ou número no formato brasileiro (pontos como separador 
                   de milhar e vírgula como separador decimal)
        
        Retorna:
            float: Valor convertido ou 0.0 em caso de erro
        '''
        if valor is None:
            return 0.0
        
        valor_str = str(valor).strip()
        
        if not valor_str:
            return 0.0
        
        try:
            # Remove pontos de milhar e substitui vírgula por ponto decimal
            valor_str = valor_str.replace('.', '').replace(',', '.')
            return float(valor_str)
        except (ValueError, AttributeError):
            return 0.0
            