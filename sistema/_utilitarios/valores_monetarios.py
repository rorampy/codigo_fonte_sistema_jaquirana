import locale
import re

class ValoresMonetarios:
    
    def converter_float_brl_positivo(valor):
        '''
        Recebe como parâmetro um valor Float (0.00) podendo ser positivo ou
        negativo. Retorna uma string "R$...", sempre positivo (sem o sinal 
        de negativo).
        '''
        valor_absoluto = abs(valor)
        
        parte_inteira = int(valor_absoluto)
        parte_decimal = round((valor_absoluto - parte_inteira) * 100)
        
        parte_inteira_formatada = f"{parte_inteira:,}".replace(",", ".")
        
        parte_decimal_formatada = f"{parte_decimal:02d}"
        
        return f"R$ {parte_inteira_formatada},{parte_decimal_formatada}"


    def converter_string_brl_para_float(valor):
        '''
        Recebe como parâmetro uma string no formato (R$0,00) e retorna 
        um float no padrão 0.00.
        '''
        try:
            valor_numerico = valor.replace("R$", "")

            valor_numerico = valor_numerico.replace(".", "").replace(",", ".")

            return float(valor_numerico)
        
        except ValueError as erro:
            return 'Erro ao tentar converter o valor BRL!'
        

    def converter_string_pyg_para_int(valor):
        '''
        Recebe como parâmetro uma string no formato (₲ 0.000.000) e retorna 
        um inteiro no padrão 0000000.
        '''
        try:
            valor_numerico = valor.replace("₲", "").replace(" ", "")

            valor_numerico = valor_numerico.replace(".", "")

            return int(valor_numerico)
        
        except ValueError as erro:
            return 'Erro ao tentar converter o valor PYG!'


    def converter_string_usd_para_float(valor):
        '''
        Recebe como parâmetro uma string no formato ($0.00) e retorna 
        um float no padrão 0.00.
        '''
        try:
            valor_numerico = valor.replace("$", "").replace(" ", "")
            
            valor_numerico = valor_numerico.replace(",", "")

            return float(valor_numerico)
        
        except ValueError as erro:
            return 'Erro ao tentar converter o valor USD!'

