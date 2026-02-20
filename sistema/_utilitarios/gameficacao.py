class Gameficacao:

    def compara_objetos(obj1, obj2):
        """
        Compara dois dicionários (obj1 e obj2) e retorna True se houver diferenças entre eles,
        caso contrário, retorna False. Também imprime as diferenças encontradas no console.

        Parâmetros:
        - obj1 (dict): Dicionário com os dados antigos (ex: do banco de dados).
        - obj2 (dict): Dicionário com os dados novos (ex: enviados via formulário).

        Retorno:
        - bool: True se houver diferenças, False se os objetos forem iguais.
        """
        
        diferencas = {}

        todas_chaves = set(obj1.keys()) | set(obj2.keys()) 

        for chave in todas_chaves:
            if obj1.get(chave) != obj2.get(chave):
                diferencas[chave] = {
                    'objeto1': obj1.get(chave),
                    'objeto2': obj2.get(chave)
                }

        if diferencas:
            for chave, valores in diferencas.items():
                pass
            return True 
        else:
            return False

