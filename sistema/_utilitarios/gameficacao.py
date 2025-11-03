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
        
        diferencas = {} # Dicionário que armazenará as chaves que possuem valores diferentes

        # Junta todas as chaves dos dois objetos para garantir que todas sejam verificadas
        todas_chaves = set(obj1.keys()) | set(obj2.keys()) 

        # Itera sobre cada chave e compara os valores dos dois objetos
        for chave in todas_chaves:
            if obj1.get(chave) != obj2.get(chave):
                # Se os valores forem diferentes, adiciona ao dicionário de diferenças
                diferencas[chave] = {
                    'objeto1': obj1.get(chave),
                    'objeto2': obj2.get(chave)
                }

        # Se houver diferenças, imprime e retorna True
        if diferencas:
            print("Diferenças encontradas:")
            for chave, valores in diferencas.items():
                print(f" - {chave}: '{valores['objeto1']}' != '{valores['objeto2']}'")
            return True 
        else:
            # Se não houver diferenças, informa e retorna False
            print("Os objetos são iguais.")
            return False

