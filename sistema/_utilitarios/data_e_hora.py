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
        delta = timedelta(days=dias)
        
        nova_data = data + delta
        
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
        delta = timedelta(days=dias)
        
        nova_data = data - delta
        
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

        data_formatada = datetime.strptime(data_str, "%Y-%m-%d")

        primeiro_dia_mes_atual = data_formatada.replace(day=1)
        mes_anterior = primeiro_dia_mes_atual - timedelta(days=1)

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
            
            data_inicio = date(ano, mes, 1)
            
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

    @staticmethod
    def obter_periodo_quinzenal(data_entrega_ou_lista):
        '''
        Calcula o período quinzenal baseado na data de entrega ou lista de datas.
        
        1ª Quinzena: dia 1 ao 15
        2ª Quinzena: dia 16 ao último dia do mês
        
        Args:
            data_entrega_ou_lista: Uma data única OU uma lista de datas nos formatos string (DD/MM/YYYY, YYYY-MM-DD) ou objeto date/datetime
        
        Returns:
            str: Período formatado. Ex: "2ª Quinzena - 16/10/2025 a 31/10/2025 e 1ª Quinzena - 01/11/2025 a 15/11/2025"
        
        Exemplos:
            # Para uma data única
            obter_periodo_quinzenal("25/10/2025") 
            # Retorna: "2ª Quinzena - 16/10/2025 a 31/10/2025"
            
            # Para uma lista de datas
            obter_periodo_quinzenal(["25/10/2025", "10/11/2025"])
            # Retorna: "2ª Quinzena - 16/10/2025 a 31/10/2025 e 1ª Quinzena - 01/11/2025 a 15/11/2025"
        '''
        if not data_entrega_ou_lista:
            return None
        
        try:
            if isinstance(data_entrega_ou_lista, list):
                todas_datas = data_entrega_ou_lista
            else:
                todas_datas = [data_entrega_ou_lista]
            
            datas_convertidas = []
            for data_item in todas_datas:
                if not data_item or data_item == '-':
                    continue
                    
                if isinstance(data_item, str):
                    formatos = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']
                    data_obj = None
                    for formato in formatos:
                        try:
                            data_obj = datetime.strptime(data_item, formato).date()
                            break
                        except ValueError:
                            continue
                    if data_obj:
                        datas_convertidas.append(data_obj)
                elif isinstance(data_item, datetime):
                    datas_convertidas.append(data_item.date())
                elif isinstance(data_item, date):
                    datas_convertidas.append(data_item)
            
            if not datas_convertidas:
                return None
            
            if len(datas_convertidas) == 1:
                data_obj = datas_convertidas[0]
                dia = data_obj.day
                if dia <= 15:
                    inicio = data_obj.replace(day=1)
                    fim = data_obj.replace(day=15)
                    return f"1ª Quinzena - {inicio.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}"
                else:
                    inicio = data_obj.replace(day=16)
                    import calendar
                    ultimo_dia = calendar.monthrange(data_obj.year, data_obj.month)[1]
                    fim = data_obj.replace(day=ultimo_dia)
                    return f"2ª Quinzena - {inicio.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}"
            
            datas_ordenadas = sorted(datas_convertidas)
            primeira_data = datas_ordenadas[0]
            ultima_data = datas_ordenadas[-1]
            
            primeira_quinzena = 1 if primeira_data.day <= 15 else 2
            ultima_quinzena = 1 if ultima_data.day <= 15 else 2
            
            if (primeira_data.month == ultima_data.month and 
                primeira_data.year == ultima_data.year and 
                primeira_quinzena == ultima_quinzena):
                return DataHora.obter_periodo_quinzenal(primeira_data)
            
            quinzenas_encontradas = []
            data_atual = primeira_data
            
            while data_atual <= ultima_data:
                if data_atual.day <= 15:
                    inicio_quinzena = data_atual.replace(day=1)
                    fim_quinzena = data_atual.replace(day=15)
                    nome_quinzena = "1ª Quinzena"
                else:
                    inicio_quinzena = data_atual.replace(day=16)
                    import calendar
                    ultimo_dia = calendar.monthrange(data_atual.year, data_atual.month)[1]
                    fim_quinzena = data_atual.replace(day=ultimo_dia)
                    nome_quinzena = "2ª Quinzena"
                
                if inicio_quinzena <= ultima_data and fim_quinzena >= primeira_data:
                    quinzena_formatada = f"{nome_quinzena} - {inicio_quinzena.strftime('%d/%m/%Y')} a {fim_quinzena.strftime('%d/%m/%Y')}"
                    if quinzena_formatada not in quinzenas_encontradas:
                        quinzenas_encontradas.append(quinzena_formatada)
                
                if data_atual.day <= 15:
                    data_atual = data_atual.replace(day=16)
                else:
                    if data_atual.month == 12:
                        data_atual = data_atual.replace(year=data_atual.year + 1, month=1, day=1)
                    else:
                        data_atual = data_atual.replace(month=data_atual.month + 1, day=1)
            
            if len(quinzenas_encontradas) == 1:
                return quinzenas_encontradas[0]
            elif len(quinzenas_encontradas) > 1:
                return " e ".join(quinzenas_encontradas)
            else:
                return DataHora.obter_periodo_quinzenal(primeira_data)
                
        except Exception:
            return None