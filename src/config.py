from datetime import date, timedelta
from dotenv import load_dotenv, dotenv_values
import os

fecha_inicio = date.today() - timedelta(days= 365 * 5)
# Conexión a la api
load_dotenv() 
key = os.getenv("key")
secret = os.getenv("secret")
base_url= 'https://paper-api.alpaca.markets'
