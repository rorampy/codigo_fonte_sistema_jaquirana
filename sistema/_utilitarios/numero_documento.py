import re


class ValidaDocs:
    def remove_pontuacao_cpf(cpf):
        '''
        Recebe um número de CPF por parâmetro e remove os dois 
        pontos e o traço do final.
        Ex.: Entrada -> 000.000.000-00 | Saída -> 00000000000
        '''
        # Remove todos os caracteres não numéricos do CPF
        cpf = ''.join(filter(str.isdigit, cpf))

        return cpf
    
    
    def insere_pontuacao_cpf(cpf):
        '''
        Recebe um número de CPF por parâmetro e remove os dois 
        pontos e o traço do final.
        Ex.: Entrada -> 00000000000 | Saída -> 000.000.000-00
        '''
        
        cpf = str(cpf)

        if len(cpf) == 11:
            cpf = f'{cpf[0:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'
            return cpf
        
        else:
            return 'Inválido!'
    

    def remove_pontuacao_cnpj(cnpj):
        '''
        Recebe um número de CNPJ por parâmetro e remove pontos, 
        barra e traço.
        Ex.: Entrada -> 00.000.000/0000-00 | Saída -> 00000000000000
        '''
        # Remove todos os caracteres não numéricos do CNPJ
        cnpj = ''.join(filter(str.isdigit, cnpj))

        return cnpj


    def insere_pontuacao_cnpj(cnpj):
        '''
        Recebe um número de CNPJ por parâmetro e insere os pontos, 
        barra e traço nos locais adequados.
        Ex.: Entrada -> 00000000000000 | Saída -> 00.000.000/0000-00
        '''
        cnpj = str(cnpj)

        if len(cnpj) == 14:
            cnpj = f'{cnpj[0:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}'
            return cnpj

        else:
            return 'Inválido!'
        
        
    def remove_pontuacao_cep(cep):
        '''
        Recebe um número de CEP por parâmetro e remove tudo que não 
        for número do mesmo.
        Ex.: Entrada -> 00000-000 | Saída -> 00000000
        '''
        cep_sem_pontos = re.sub(r'[^0-9]', '', cep)
        
        return cep_sem_pontos
    
    
    def remove_pontuacao_cip_py(cedula):
        '''
        Recebe um número de Cédula de Identidad Personal (CIP) do Paraguai 
        por parâmetro e remove espaços e outros caracteres não numéricos.
        Ex.: Entrada -> 1234567 | Saída -> 1234567
        '''
        # Remove todos os caracteres não numéricos da Cédula
        cedula = ''.join(filter(str.isdigit, cedula))

        return cedula
    
    
    def insere_pontuacao_cip_py(cedula):
        '''
        Recebe um número de Cédula de Identidad Personal (CIP) do Paraguai
        por parâmetro e formata com pontos para facilitar a leitura.
        Ex.: Entrada -> 1234567 | Saída -> 1.234.567
        '''
        
        cedula = str(cedula)

        if len(cedula) <= 7:
            # Adiciona pontos a cada três dígitos
            cedula = '.'.join(cedula[i:i+3] for i in range(0, len(cedula), 3))
            return cedula
        else:
            return 'Inválido!'


    def remove_pontuacao_ruc_py(ruc):
        '''
        Recebe um número de RUC (Registro Único de Contribuyentes) do Paraguai 
        por parâmetro e remove traços e outros caracteres não numéricos.
        Ex.: Entrada -> 1234567-8 | Saída -> 12345678
        '''
        # Remove todos os caracteres não numéricos do RUC
        ruc = ''.join(filter(str.isdigit, ruc))

        return ruc


    def insere_pontuacao_ruc_py(ruc):
        '''
        Recebe um número de RUC (Registro Único de Contribuyentes) do Paraguai 
        por parâmetro e insere o traço antes do dígito verificador.
        Ex.: Entrada -> 12345678 | Saída -> 1234567-8
        '''
        ruc = str(ruc)

        if 6 <= len(ruc) <= 8:
            # Insere um traço antes do último dígito
            ruc = f'{ruc[:-1]}-{ruc[-1]}'
            return ruc
        else:
            return 'Inválido!'
        
    #Retira todos os caracteres de um numero
    def somente_numeros(valor):
        if isinstance(valor, tuple):
            valor = valor[0]
        if valor is None:
            return None
        return re.sub(r'\D', '', str(valor))


