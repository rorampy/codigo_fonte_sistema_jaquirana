from datetime import datetime, timedelta, date
import calendar

class UtilitariosSemana:
    
    @staticmethod
    def _obter_primeira_segunda(data_inicial):
        """Encontra a primeira segunda-feira da semana que contém a data inicial."""
        while data_inicial.weekday() != 0:  # 0 = segunda-feira
            data_inicial -= timedelta(days=1)
        return data_inicial
    
    @staticmethod
    def _criar_semana_info(inicio, fim, hoje, is_mes_completo=False):
        """Cria dicionário com informações da semana."""
        is_atual = inicio <= hoje <= fim if not is_mes_completo else False
        
        return {
            "valor": f"{inicio.strftime('%Y-%m-%d')}|{fim.strftime('%Y-%m-%d')}",
            "texto": f"Semana: {inicio.strftime('%d/%m')} a {fim.strftime('%d/%m')}" if not is_mes_completo else "Período Completo",
            "inicio": inicio,
            "fim": fim,
            "is_atual": is_atual,
            "is_mes_completo": is_mes_completo,
        }
    
    @staticmethod
    def obter_semanas_do_mes_atual():
        hoje = datetime.now().date()
        ano, mes = hoje.year, hoje.month
        
        # Define período: início do ano até final do mês atual
        inicio_periodo = date(ano, 1, 1)
        fim_periodo = date(ano, mes, calendar.monthrange(ano, mes)[1])
        
        semanas = []
        
        # Adiciona opção de período completo
        semanas.append(UtilitariosSemana._criar_semana_info(
            inicio_periodo, fim_periodo, hoje, is_mes_completo=True
        ))
        
        # Encontra primeira segunda-feira e gera semanas
        semana_inicio = UtilitariosSemana._obter_primeira_segunda(inicio_periodo)
        
        while semana_inicio <= fim_periodo:
            fim_semana = semana_inicio + timedelta(days=6)
            
            # Só processa semanas que interceptam o período e não são futuras
            if (fim_semana >= inicio_periodo and semana_inicio <= hoje):
                semana_info = UtilitariosSemana._criar_semana_info(
                    semana_inicio, fim_semana, hoje
                )
                semanas.append(semana_info)
            
            semana_inicio += timedelta(days=7)
        
        # Ordena: semana atual primeiro, depois por data decrescente
        return sorted(semanas[1:], key=lambda x: (not x["is_atual"], -x["inicio"].toordinal())) + [semanas[0]]
    
    @staticmethod
    def obter_datas_mes_atual():
        """Retorna primeiro e último dia do mês atual."""
        hoje = datetime.now()
        primeiro_dia = date(hoje.year, hoje.month, 1)
        ultimo_dia = date(hoje.year, hoje.month, calendar.monthrange(hoje.year, hoje.month)[1])
        return primeiro_dia, ultimo_dia
    
    @staticmethod
    def processar_semana_selecionada(semana_valor):
        """Processa valor da semana selecionada e retorna datas de início e fim."""
        if not semana_valor:
            return None, None
        
        try:
            inicio_str, fim_str = semana_valor.split("|")
            inicio = datetime.strptime(inicio_str, "%Y-%m-%d").date()
            fim = datetime.strptime(fim_str, "%Y-%m-%d").date()
            return inicio, fim
        except (ValueError, AttributeError):
            return None, None