import logging
from logging.handlers import TimedRotatingFileHandler


# Configurar o logger raiz para registrar apenas mensagens CRITICAL.
logging.getLogger().setLevel(logging.CRITICAL)

# instanciando o log - poderia passar 'huey' e integrar com o huey
flask_logger = logging.getLogger('flask')

 # ou logging.DEBUG para mais detalhes
flask_logger.setLevel(logging.INFO)

# Cria um log que grava logs para um arquivo e rotaciona diariamente.
# 'midnight' significa que o log será rotacionado à meia-noite.
# backupCount=7 significa que manterá os logs dos últimos 7 dias.
log_flask = TimedRotatingFileHandler(
    "logs_sistema/registro.log", 
    when="midnight", 
    backupCount=30
)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_flask.setFormatter(formatter)

# Adiciona o handler ao logger
flask_logger.addHandler(log_flask)