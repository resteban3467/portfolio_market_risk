import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import APIError
from src.config import key, secret, base_url
import time

api = tradeapi.REST(key, secret, base_url, api_version='v2')

CARTERA_OBJETIVO = {
    "VT": 10,
    "ECH": 20,
    "VNQ": 5,
    "GLD": 2,
    "AGG": 10,
}


def comprar_todo() -> None:
    print("Iniciando compra de cartera...")

    for symbol, qty in CARTERA_OBJETIVO.items():
        try:
            quote = api.get_latest_trade(symbol)
            price = quote.price
            print(f"Comprando {qty} de {symbol} a aprox ${price}...")

            api.submit_order(
                symbol=symbol,
                qty=qty,
                side='buy',
                type='market',
                time_in_force='day',
            )
            print(f"Orden enviada para {symbol}")
            time.sleep(5)

        except APIError as e:
            print(f"Error de API comprando {symbol}: {e}")
        except Exception as e:
            print(f"Error inesperado comprando {symbol}: {e}")


if __name__ == "__main__":
    clock = api.get_clock()
    if clock.is_open:
        comprar_todo()
    else:
        print("El mercado está cerrado. Las órdenes quedarán agendadas para el día siguiente.")
        comprar_todo()
