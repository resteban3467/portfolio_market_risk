from datetime import date, timedelta
from dotenv import load_dotenv, dotenv_values
from pathlib import Path
import os

fecha_inicio = date.today() - timedelta(days= 365 * 5)
# Conexión a la api
load_dotenv() 
key = os.getenv("key")
secret = os.getenv("secret")
base_url= 'https://paper-api.alpaca.markets'

# Configuración
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = BASE_DIR / "reports"

# Creación de directorios

for folder in [DATA_DIR, RAW_DIR, PROCESSED_DIR, REPORTS_DIR]:
    folder.mkdir(exist_ok=True, parents=True)