import alpaca_trade_api as tradeapi
from src.config import config
import time
import os
from dotenv import load_dotenv, dotenv_values

# Conexión
# Cargar información sensible
load_dotenv() 

api = tradeapi.REST(
    os.getenv("key"),
    os.getenv("secret"),
    base_url= 'https://paper-api.alpaca.markets'
)

# Establecer cartera
cartera  = {
    "VT": 10,
    "ECH": 20,
    "SQM": 5,
    "GLD": 2,
    "AGG": 10
}

def comprar_todo():
    print("Iniciando compra de cartera...")
    
    for symbol, qty in cartera.items():
        try:
            quote = api.get_latest_trade(symbol)
            price = quote.price
            print(f"Comprando {qty} de {symbol} a aprox ${price}...")

            api.submit_order(
                symbol=symbol,
                qty=qty,
                side='buy',
                type='market',
                time_in_force='day' 
            )
            print(f"Orden enviada para {symbol}")
            time.sleep(5) 
            
        except Exception as e:
            print(f"Error comprando {symbol}: porque {e}")

if __name__ == "__main__":

    clock = api.get_clock()
    if clock.is_open:
        comprar_todo()
    else:
        print("El mercado está cerrado. Las órdenes quedarán agendadas para mañana.")
        comprar_todo()