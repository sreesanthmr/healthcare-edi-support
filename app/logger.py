import logging
from pathlib import Path


LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)


logger = logging.getLogger("edi_processor")

logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(
    LOG_DIR / "edi_processor.log"
)

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s"
)

file_handler.setFormatter(formatter)

logger.addHandler(file_handler)