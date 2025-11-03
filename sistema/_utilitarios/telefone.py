
class Tels:
    def remove_pontuacao_telefone_celular_br(telefone):
        '''
        Recebe um número de telefone por parâmetro no formato celular do Brasil
        e remove os parênteses, espaços e traços.
        Ex.: Entrada -> (99) 9 9999-9999 | Saída -> 99999999999
        '''

        telefone = ''.join(filter(str.isdigit, telefone))
    
        return telefone
    

    def insere_pontuacao_telefone_celular_br(telefone):
        '''
        Recebe um número de telefone por parâmetro no formato celular do Brasil
        e insere os parênteses, espaços e traços.
        Ex.: Entrada -> 99999999999 | Saída -> (99) 9 9999-9999
        '''
       
        telefone = str(telefone)
    
        if len(telefone) == 11:
            return f"({telefone[0:2]}) {telefone[2]} {telefone[3:7]}-{telefone[7:]}"
        else:
            return 'Inválido!'


    def remove_pontuacao_telefone_fixo_br(telefone):
        '''
        Recebe um número de telefone por parâmetro no formato telefone fixo do Brasil
        e remove os parênteses, espaços e traços.
        Ex.: Entrada -> (99) 9999-9999 | Saída -> 9999999999
        '''

        telefone = ''.join(filter(str.isdigit, telefone))
    
        return telefone
    

    def insere_pontuacao_telefone_fixo_br(telefone):
        '''
        Recebe um número de telefone por parâmetro no formato de telefone fixo do Brasil
        e insere os parênteses, espaços e traços.
        Ex.: Entrada -> 999999999 | Saída -> (99) 9999-9999
        '''
    
        telefone = str(telefone)

        if len(telefone) == 10:
            return f"({telefone[0:2]}) {telefone[2:6]}-{telefone[6:]}"
        else:
            return 'Inválido!'
        
        
    def remove_pontuacao_telefone_celular_py(telefone):
        '''
        Recebe um número de telefone por parâmetro no formato celular do Paraguai
        e remove os espaços e outros caracteres não numéricos.
        Ex.: Entrada -> 981 234 567 | Saída -> 981234567
        '''

        telefone = ''.join(filter(str.isdigit, telefone))

        return telefone

        
    def insere_pontuacao_telefone_celular_py(telefone):
        '''
        Recebe um número de telefone por parâmetro no formato celular do Paraguai
        e insere os espaços.
        Ex.: Entrada -> 981234567 | Saída -> 981 234 567
        '''
    
        telefone = str(telefone)

        if len(telefone) == 9:
            return f"{telefone[0:3]} {telefone[3:6]} {telefone[6:]}"
        else:
            return 'Inválido!'


    def remove_pontuacao_telefone_fixo_py(telefone):
        '''
        Recebe um número de telefone por parâmetro no formato telefone fixo do Paraguai
        e remove os espaços e outros caracteres não numéricos.
        Ex.: Entrada -> 21 234 567 | Saída -> 21234567
        '''

        telefone = ''.join(filter(str.isdigit, telefone))

        return telefone


    def insere_pontuacao_telefone_fixo_py(telefone):
        '''
        Recebe um número de telefone por parâmetro no formato de telefone fixo do Paraguai
        e insere os espaços.
        Ex.: Entrada -> 21234567 | Saída -> 21 234 567
        '''
        
        telefone = str(telefone)

        if len(telefone) == 8:
            return f"{telefone[0:2]} {telefone[2:5]} {telefone[5:]}"
        else:
            return 'Inválido!'
        