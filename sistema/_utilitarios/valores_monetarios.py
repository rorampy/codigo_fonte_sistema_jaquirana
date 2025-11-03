import locale
import re

class ValoresMonetarios:
    
    def converter_float_brl_positivo(valor):
        '''
        Recebe como parâmetro um valor Float (0.00) podendo ser positivo ou
        negativo. Retorna uma string "R$...", sempre positivo (sem o sinal 
        de negativo).
        '''
        # Configurar a localização para o formato de números brasileiro
        try:
            locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')
        except locale.Error:
            try:
                # Tentar com o nome da localização em minúsculas
                locale.setlocale(locale.LC_ALL, 'pt_br.utf8')
            except locale.Error:
                # Caso a localização 'pt_BR.utf8' não esteja disponível, usar a localização 'en_US.UTF-8'
                locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

        # Formatar o valor como moeda brasileira
        valor_editado = locale.currency(abs(valor), grouping=True, symbol='R$')

        return valor_editado


    def converter_string_brl_para_float(valor):
        '''
        Recebe como parâmetro uma string no formato (R$0,00) e retorna 
        um float no padrão 0.00.
        '''
        try:
            # Remove o símbolo de Real
            valor_numerico = valor.replace("R$", "")

            # Substitui vírgula por ponto e remove pontos de milhar
            valor_numerico = valor_numerico.replace(".", "").replace(",", ".")

            # Converte para float
            return float(valor_numerico)
        
        except ValueError as erro:
            return 'Erro ao tentar converter o valor BRL!'
        

    def converter_string_pyg_para_int(valor):
        '''
        Recebe como parâmetro uma string no formato (₲ 0.000.000) e retorna 
        um inteiro no padrão 0000000.
        '''
        try:
            # Remove o símbolo de Guarani e quaisquer espaços extras
            valor_numerico = valor.replace("₲", "").replace(" ", "")

            # Remove pontos de milhar
            valor_numerico = valor_numerico.replace(".", "")

            # Converte para inteiro
            return int(valor_numerico)
        
        except ValueError as erro:
            return 'Erro ao tentar converter o valor PYG!'


    def converter_string_usd_para_float(valor):
        '''
        Recebe como parâmetro uma string no formato ($0.00) e retorna 
        um float no padrão 0.00.
        '''
        try:
            # Remove o símbolo de Dólar
            valor_numerico = valor.replace("$", "").replace(" ", "")
            
            # Remove as vírgulas de milhar e deixa o ponto como separador decimal
            valor_numerico = valor_numerico.replace(",", "")

            # Converte para float
            return float(valor_numerico)
        
        except ValueError as erro:
            return 'Erro ao tentar converter o valor USD!'

