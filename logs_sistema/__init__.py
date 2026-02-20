import logging
from logging.handlers import TimedRotatingFileHandler


logging.getLogger().setLevel(logging.CRITICAL)

flask_logger = logging.getLogger('flask')

flask_logger.setLevel(logging.INFO)

log_flask = TimedRotatingFileHandler(
    "logs_sistema/registro.log", 
    when="midnight", 
    backupCount=30
)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_flask.setFormatter(formatter)

flask_logger.addHandler(log_flask)