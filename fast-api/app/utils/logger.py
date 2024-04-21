import logging
from app.core.config import settings

# Создание логгера
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler("/project/peer/logs/" + "fast-debug.log")
# Создание обработчика и форматирования
shandler = logging.StreamHandler()
formatter = logging.Formatter("%(levelname)s: %(asctime)s - %(name)s:: %(message)s")
handler.setFormatter(formatter)
shandler.setFormatter(formatter)

# Добавление обработчика к логгеру
logger.addHandler(handler)
logger.addHandler(shandler)

