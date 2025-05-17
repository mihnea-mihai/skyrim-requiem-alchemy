import logging

with open("alchemy.log", "w", encoding="utf-8"):
    pass
logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="alchemy.log",
    format="%(levelname)s\t%(asctime)s\t%(message)s",
    level=logging.INFO,
)
