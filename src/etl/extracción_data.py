import os
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import TimeFrame
import pandas as pd
from typing import List, Optional


import src.config as cfg

class CargaDatos:
    """
    Clase encargada de extraer datos de posición y mercado de alpaca.
    """

    def __init__(self, api_key: str, secret_key: str, base_url: str):
        """
        Inicia conexión con Alpaca.
        """
        self.api = tradeapi.REST(api_key, secret_key, base_url, api_version='v2')
        self.tickers: List[str] = []

 
        
    def get_tickers_cartera(self) -> List[str]:
        """
        Consulta Alpaca para obtener los tickers en la cartera.
        """

        try:
            positions = self.api.list_positions()
            self.tickers = [pos.symbol for pos in positions]
            print(f"Tickers encontrados en cartera: {self.tickers}")
            return self.tickers

        except Exception as e:
            print(f"No se pudo concretar la conexión por: {e}")
            return []

    def fetch_market_data(self, fecha_inicio: str) -> pd.DataFrame:
        """
        Extrae datos históricos ajustados directamente de Alpaca.
        """
        print(f"Extrayendo datos de Alpaca para: {self.tickers}")
        
        try:
            # Se obtiene info de alpaca. Se deja adjustment='all' para evitar irregularidades en precios
            bars = self.api.get_bars(
                self.tickers, 
                TimeFrame.Day, 
                start=fecha_inicio,
                adjustment='all'
            ).df

            if bars.empty:
                print("No se encontraron datos.")
                return pd.DataFrame()

            # Se le da forma vertical al df
            df_precios = bars.pivot_table(index='timestamp', columns='symbol', values='close')
            
            # Se deja fecha en formato YYYY-MM-DD
            df_precios.index = pd.to_datetime(df_precios.index).date
            
            print(f"Se realizó la descarga exitosamente.")
            return df_precios

        except Exception as e:
            print(f"No se pudo descargar la data porque: {e}")
            return pd.DataFrame()

    def save_to_parquet(self, data: pd.DataFrame, filename: str = "market_data.parquet"):
        """
        Guarda el DataFrame en la carpeta processed.
        """        

        try:
            # Se define la ruta relativa
            output_path = cfg.RAW_DIR / filename
            
            # Se guarda en la dirección indicada
            data.to_parquet(output_path)
            print(f"Datos guardados exitosamente en: {output_path}")
        except Exception as e:
            print(f"Los datos no se pudieron guardar porque: {e}")