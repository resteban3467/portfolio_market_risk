import os
import alpaca_trade_api as tradeapi
import yfinance as yf
import pandas as pd
from typing import List, Optional


import src.config as cfg

class CargaDatos:
    """
    Clase encargada de extraer datos de posición (Alpaca) y mercado (Yahoo Finance).
    """

    def __init__(self, api_key: str, secret_key: str, base_url: str):
        """
        Inicializa la conexión con Alpaca.
        """
        self.api = tradeapi.REST(api_key, secret_key, base_url, api_version='v2')
        self.tickers: List[str] = []

 
        
    def get_tickers_cartera(self) -> List[str]:
        """
        Consulta Alpaca para obtener los símbolos activos en la cartera.
        """

        try:
            positions = self.api.list_positions()
            self.tickers = [pos.symbol for pos in positions]
            print(f"Tickers encontrados en cartera: {self.tickers}")
            return self.tickers

        except Exception as e:
            print(f"No se pudo concretar la conexión por: {e}")
            return []

    def fetch_market_data(self, fecha_inicio: str, include_benchmark: bool) -> pd.DataFrame:
        """
        Descarga data histórica de yfinance basada en los tickers obtenidos.
        """
        if not self.tickers:
            print("No hay tickers cargados. Ejecuta get_tickers_cartera primero.")
            return pd.DataFrame()

        download_list = self.tickers.copy()
        
        if include_benchmark:
            download_list.append("SPY") # Agregamos S&P 500 como referencia
        
        print(f"Descargando datos para: {download_list}")
        
        # Descarga optimizada
        data = yf.download(
            download_list, 
            start=fecha_inicio, 
            group_by='ticker', 
            auto_adjust=True,
            progress=False
        )
        
        return data

    def save_to_parquet(self, data: pd.DataFrame, filename: str = "market_data.parquet"):
        """
        Guarda el DataFrame en la carpeta processed.
        """
        # Se define la ruta relativa
        output_path = os.path.join("data", "processed", filename)
        
        # Se comprueba si la carpeta existe
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Se guarda en un parquet para mayor eficiencia de espacio y velocidad de lectura.
        data.to_parquet(output_path)
        print(f"Datos guardados exitosamente en: {output_path}")

datos = CargaDatos(api_key= cfg.key, secret_key= cfg.secret, base_url= cfg.base_url)
datos_cartera = datos.get_tickers_cartera()
datos_mercado = datos.fetch_market_data(cfg.fecha_inicio, True)
datos_mercado.head()