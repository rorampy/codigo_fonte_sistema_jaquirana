from datetime import datetime, date, timedelta


class DataHora:
    def adicionar_dias_em_data(data: datetime, dias: int) -> datetime:
        '''
        Adiciona um número específico de dias a uma data.

        Args:
            data (datetime): A data original à qual os dias serão adicionados.
            dias (int): O número de dias a adicionar à data.

        Returns:
            datetime: A nova data resultante da adição dos dias.

        Exemplo:
            data_original = datetime(2023, 6, 1)
            dias_para_adicionar = 10
            nova_data = adicionar_dias(data_original, dias_para_adicionar)
            print(nova_data)  # Saída: 2023-06-11 00:00:00
        '''
        # Cria um objeto timedelta que representa o número de dias a serem adicionados
        delta = timedelta(days=dias)
        
        # Adiciona o timedelta à data original
        nova_data = data + delta
        
        # Retorna a nova data
        return nova_data
    
    
    def remover_dias_em_data(data: datetime, dias: int) -> datetime:
        '''
        Remove um número específico de dias de uma data.

        Args:
            data (datetime): A data original à qual os dias serão removidos.
            dias (int): O número de dias a remover da data.

        Returns:
            datetime: A nova data resultante da remoção dos dias.

        Exemplo:
            data_original = datetime(2023, 6, 1)
            dias_para_remover = 10
            nova_data = remover_dias_em_data(data_original, dias_para_remover)
            print(nova_data)  # Saída: 2023-05-20 00:00:00
        '''
        # Cria um objeto timedelta que representa o número de dias a serem removidos
        delta = timedelta(days=dias)
        
        # Adiciona o timedelta à data original
        nova_data = data - delta
        
        # Retorna a nova data
        return nova_data
    
    
    def obter_data_e_hora_atual_padrao_en():
        '''
        Obtem a data e hora atual no padrão AAAA-MM-DD HH:MM:SS.
        '''
        informacao = datetime.now()

        return informacao


    def obter_data_atual_padrao_br():
        '''
        Obtem a data atual no padrão DD/MM/AAAA.
        '''
        data_formatada = DataHora.obter_data_e_hora_atual_padrao_en().strftime("%d/%m/%Y")

        return data_formatada


    def obter_data_atual_padrao_en():
        '''
        Obtem a data atual no padrão AAAA-MM-DD.
        '''
        data_atual = datetime.now().strftime("%Y-%m-%d")

        return data_atual
    
    
    def obter_data_em_objeto_datetime(objeto_date_time):
        '''
        Obtem somente a data de um objeto DateTime
        '''
        somente_data = objeto_date_time.strftime('%Y-%m-%d')

        return somente_data


    def obter_hora_atual_padrao_br():
        '''
        Obtem a hora atual no padrão HH:MM:SS.
        '''
        hora_formatada = DataHora.obter_data_e_hora_atual_padrao_en().strftime("%H:%M:%S")

        return hora_formatada


    def obter_mes_em_data_en(data):
        '''
        Recebe por parâmetro uma data no formato yyyy-mm-dd e retorma
        um número inteiro ref. ao mês atual. Ex.: Agosto -> Int 8.
        '''
        data_formatada = datetime.strptime(data, '%Y-%m-%d')
        mes = data_formatada.month
        
        return mes
    

    def obter_mes_anterior_em_data_en(data_str):
        '''
        Recebe como parâmetro uma data string 'YYYY-MM-DD' e obtem o 
        mês anterior a data informada. Retorna uma lista com duas 
        strings contendo ano e mês anterior. ['aaaa', 'mm']
        '''

        # Converte a string para um objeto datetime
        data_formatada = datetime.strptime(data_str, "%Y-%m-%d")

        # Subtrai um mês da data
        primeiro_dia_mes_atual = data_formatada.replace(day=1)
        mes_anterior = primeiro_dia_mes_atual - timedelta(days=1)

        # Obter o mês e ano do resultado
        mes_anterior_str = mes_anterior.strftime("%m")
        ano_anterior_str = mes_anterior.strftime("%Y")

        ano_mes = []
        ano_mes.append(ano_anterior_str)
        ano_mes.append(mes_anterior_str)

        return ano_mes


    def obter_dia_em_data_en(data):
        '''
        Recebe por parâmetro uma data no formato yyyy-mm-dd e retorma
        um número inteiro ref. ao ano atual. Ex.: 2023 -> Int 2023.
        '''
        data_formatada = datetime.strptime(data, '%Y-%m-%d')
        dia = data_formatada.day
        
        return dia
    

    def obter_mes_em_data_en(data):
        '''
        Recebe por parâmetro uma data no formato yyyy-mm-dd e retorma
        um número inteiro ref. ao ano atual. Ex.: 2023 -> Int 2023.
        '''
        data_formatada = datetime.strptime(data, '%Y-%m-%d')
        mes = data_formatada.month
        
        return mes


    def obter_ano_em_data_en(data):
        '''
        Recebe por parâmetro uma data no formato yyyy-mm-dd e retorma
        um número inteiro ref. ao ano atual. Ex.: 2023 -> Int 2023.
        '''
        data_formatada = datetime.strptime(data, '%Y-%m-%d')
        ano = data_formatada.year
        
        return ano
    

    def obter_mes_por_extenso_pt_br(numero_mes):
        '''
        Recebe como parâmetro um número inteiro entre 1 e 12 e retorna
        o nome do mês correspondente ao número informado. Se informar
        um número fora do range solicitado retorna False.
        '''
        meses_pt_br = [
            '', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ]

        if numero_mes >= 1 and numero_mes <= 12:
            return meses_pt_br[numero_mes]
        
        else:
            return False

    
    def verificar_fim_de_semana(data):
        """
        Verifica se uma data é sábado ou domingo.

        Parâmetros:
        data (datetime): Objeto datetime representando a data a ser verificada.

        Retorna:
        int: 5 se a data for sábado, 6 se a data for domingo.
        bool: False se a data não for sábado nem domingo.
        """
        dia_da_semana = data.weekday()
        
        if dia_da_semana == 5:
            return 5
        elif dia_da_semana == 6:
            return 6
        else:
            return False
        

    def converter_data_str_en_em_objeto_datetime(data_str):
        '''
        Recebe como parâmetro uma data string 'YYYY-MM-DD' e retorna 
        um objeto datetime convetido. Apartir desse retorno é possível,
        é possível interagir com o objeto. Ex.: objeto.year, objeto.mouth.
        '''
        # Converter a data em um objeto datetime
        data_convertida = datetime.strptime(data_str, '%Y-%m-%d')

        return data_convertida


    def converter_data_str_br_em_objeto_date(data_str):
        """
        Recebe como parâmetro uma data no formato 'dd/mm/aaaa' e retorna 
        um objeto do tipo date.
        
        Exemplo:
        data_str = '25/12/2025'
        retorno = converter_data_str_em_objeto_date(data_str)
        # retorno será um objeto date representando 25 de dezembro de 2025.
        """
        # Converter a data em um objeto datetime e retornar apenas a parte da data
        data_convertida = datetime.strptime(data_str, '%d/%m/%Y').date()
        return data_convertida


    def converter_data_de_en_para_br(data):
        '''
        Recebe como parêmetro uma data no formato YYYY-MM-DD, podendo ser
        do tipo str ou date. Converte e retorna uma data no formato 
        DD/MM/AAAA, do tipo date.
        '''
        if isinstance(data, str):
            data_obj = datetime.strptime(data, '%Y-%m-%d').date()
            return data_obj.strftime('%d/%m/%Y')
        elif isinstance(data, date):
            return data.strftime('%d/%m/%Y')
        else:
            raise ValueError("Formato enviado. Enviar uma str ou date!")
        
        
    def converter_objeto_datetime_em_html_iso_8601(data):
        '''
        Recebe como parêmetro um objeto datetime e retorna a mesma data
        no formato ISO-8601 que é o formato padrão do HTML5. 
        Esta função geralmente é usada para converter datas em telas
        de edição.
        '''
        if data:
            data_convertida = data.strftime('%Y-%m-%d')
            return data_convertida
        
        else:
            raise ValueError("Formato enviado. Enviar uma str ou date!")


    @staticmethod
    def obter_exercicios_disponiveis_ano_atual():
        '''
        Retorna lista de exercícios (MM/YYYY) do ano atual, do mês atual para baixo.
        Formato de retorno: [{'valor': 'MM/YYYY', 'texto': 'MM/YYYY'}, ...]
        
        Exemplo de retorno:
        [
            {'valor': '09/2025', 'texto': '09/2025'},
            {'valor': '08/2025', 'texto': '08/2025'},
            {'valor': '07/2025', 'texto': '07/2025'}
        ]
        '''
        hoje = date.today()
        exercicios = []
        
        # Gerar lista do mês atual até janeiro do ano atual
        for mes in range(hoje.month, 0, -1):
            mes_formatado = f"{mes:02d}"
            ano = hoje.year
            exercicio = f"{mes_formatado}/{ano}"
            
            exercicios.append({
                'valor': exercicio,
                'texto': exercicio,
                'mes': mes,
                'ano': ano
            })
        
        return exercicios


    @staticmethod
    def obter_periodo_completo_mes(exercicio_str):
        '''
        Recebe um exercício no formato MM/YYYY e retorna as datas de início e fim do mês.
        
        Args:
            exercicio_str (str): Exercício no formato "MM/YYYY" (ex: "09/2025")
        
        Returns:
            tuple: (data_inicio, data_fim) como objetos date
        
        Exemplo:
            inicio, fim = obter_periodo_completo_mes("09/2025")
            # inicio = date(2025, 9, 1)
            # fim = date(2025, 9, 30)
        '''
        try:
            mes, ano = exercicio_str.split('/')
            mes = int(mes)
            ano = int(ano)
            
            # Primeiro dia do mês
            data_inicio = date(ano, mes, 1)
            
            # Último dia do mês usando calendar
            import calendar
            ultimo_dia = calendar.monthrange(ano, mes)[1]
            data_fim = date(ano, mes, ultimo_dia)
            
            return data_inicio, data_fim
            
        except (ValueError, IndexError):
            raise ValueError("Formato de exercício inválido! Use MM/YYYY (ex: 09/2025)")

    @staticmethod
    def obter_exercicio_mes_atual():
        '''
        Retorna o exercício do mês atual no formato MM/YYYY.
        
        Returns:
            str: Exercício atual no formato "MM/YYYY" (ex: "09/2025")
        
        Exemplo:
            exercicio = obter_exercicio_mes_atual()
            # retorna "09/2025" se estivermos em setembro de 2025
        '''
        hoje = date.today()
        return f"{hoje.month:02d}/{hoje.year}"
