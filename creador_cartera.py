import alpaca_trade_api as tradeapi
from src.config import config
import time

# 1. Conexión
api = tradeapi.REST(
    config.ALPACA_KEY,
    config.ALPACA_SECRET,
    base_url='https://paper-api.alpaca.markets'
)

# 2. Definir el Portafolio Objetivo
# Formato: Simbolo: Cantidad
target_portfolio = {
    "VT": 10,    # Mundo
    "ECH": 20,   # Chile (ETF)
    "SQM": 5,    # Soquimich (ADR)
    "GLD": 2,    # Oro
    "AGG": 10    # Bonos
}

def comprar_todo():
    print("Iniciando compra de portafolio...")
    
    for symbol, qty in target_portfolio.items():
        try:
            # Obtenemos precio actual para referencia
            quote = api.get_latest_trade(symbol)
            price = quote.price
            print(f"Comprando {qty} de {symbol} a aprox ${price}...")

            # ENVIAR ORDEN DE MERCADO (La más simple para empezar)
            api.submit_order(
                symbol=symbol,
                qty=qty,
                side='buy',
                type='market',      # <--- Aquí defines el tipo
                time_in_force='day' # <--- Expira hoy si no se compra
            )
            print(f"Orden enviada para {symbol}")
            time.sleep(1) # Esperar un poco para no saturar la API
            
        except Exception as e:
            print(f"Error comprando {symbol}: {e}")

# 3. Función avanzada: Orden Límite (Comprar barato)
def comprar_con_limite(symbol, qty, precio_maximo):
    print(f"Poniendo orden límite por {symbol} a ${precio_maximo}")
    api.submit_order(
        symbol=symbol,
        qty=qty,
        side='buy',
        type='limit',        # <--- Tipo Límite
        limit_price=precio_maximo, # <--- Tu precio tope
        time_in_force='gtc'  # <--- GTC: Déjala abierta hasta que caiga el precio
    )

if __name__ == "__main__":
    # Verifica si el mercado está abierto (solo funciona lun-vie 9:30-16:00 ET)
    clock = api.get_clock()
    if clock.is_open:
        comprar_todo()
    else:
        print("El mercado está cerrado. Las órdenes quedarán en cola para mañana.")
        # Igual puedes ejecutarlo, Alpaca las guardará.
        comprar_todo()