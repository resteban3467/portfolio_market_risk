from datetime import date, timedelta
from dotenv import load_dotenv
from pathlib import Path
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

key = os.getenv("key")
secret = os.getenv("secret")

if not key or not secret:
    logger.warning(
        "Credenciales de Alpaca no encontradas. "
        "Copia .env.example a .env y completa tus API keys."
    )

fecha_inicio: date = date.today() - timedelta(days=365 * 5)

base_url: str = 'https://paper-api.alpaca.markets'

BASE_DIR: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = BASE_DIR / "data"
RAW_DIR: Path = DATA_DIR / "raw"
PROCESSED_DIR: Path = DATA_DIR / "processed"
REPORTS_DIR: Path = BASE_DIR / "reports"

for folder in [DATA_DIR, RAW_DIR, PROCESSED_DIR, REPORTS_DIR]:
    folder.mkdir(exist_ok=True, parents=True)
