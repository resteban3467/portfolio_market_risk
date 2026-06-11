import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import TimeFrame, APIError
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Literal
from datetime import date
import src.config as cfg


class CargaDatos:
    """
    Clase encargada de extraer datos de posición y de mercado desde Alpaca.
    """

    def __init__(self, api_key: str, secret_key: str, base_url: str):
        """
        Inicia conexión con Alpaca.

        Parameters
        ----------
        api_key : str
            API Key de Alpaca.
        secret_key : str
            API Secret de Alpaca.
        base_url : str
            URL base del endpoint (paper o live).
        """
        self.api = tradeapi.REST(api_key, secret_key, base_url, api_version='v2')
        self.tickers: List[str] = []
        self._posiciones_cache: Optional[List] = None

    def _obtener_posiciones(self) -> List:
        """
        Llama a la API de Alpaca una sola vez y cachea el resultado.
        """
        if self._posiciones_cache is None:
            self._posiciones_cache = self.api.list_positions()
        return self._posiciones_cache

    def get_tickers_cartera(self) -> List[str]:
        """
        Consulta Alpaca para obtener los tickers en la cartera.

        Returns
        -------
        List[str]
            Lista de símbolos presentes en el portafolio.
        """
        try:
            positions = self._obtener_posiciones()
            self.tickers = [pos.symbol for pos in positions]
            print(f"Tickers encontrados en cartera: {self.tickers}")
            return self.tickers

        except APIError as e:
            print(f"Error de API al obtener tickers: {e}")
            return []
        except Exception as e:
            print(f"Error inesperado al obtener tickers: {e}")
            return []

    def fetch_market_data(self, fecha_inicio: date) -> pd.DataFrame:
        """
        Extrae datos históricos de precios ajustados desde Alpaca.

        Parameters
        ----------
        fecha_inicio : date
            Fecha desde la cual extraer datos históricos.

        Returns
        -------
        pd.DataFrame
            DataFrame con precios de cierre ajustados (filas=fecha, columnas=ticker).
        """
        if not self.tickers:
            self.get_tickers_cartera()

        if not self.tickers:
            print("No se pudieron obtener los tickers; no es posible descargar datos.")
            return pd.DataFrame()

        # Alpaca espera string en formato ISO
        fecha_str = fecha_inicio.isoformat()
        print(f"Extrayendo datos de Alpaca para: {self.tickers} desde {fecha_str}")

        try:
            bars = self.api.get_bars(
                self.tickers,
                TimeFrame.Day,
                start=fecha_str,
                adjustment='all',
            ).df

            if bars.empty:
                print("No se encontraron datos para el rango solicitado.")
                return pd.DataFrame()

            df_precios = bars.pivot_table(index='timestamp', columns='symbol', values='close')
            df_precios.index = pd.to_datetime(df_precios.index).date
            df_precios.index.name = 'fecha'

            print("Descarga completada exitosamente.")
            return df_precios

        except APIError as e:
            print(f"Error de API al descargar datos: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Error inesperado al descargar datos: {e}")
            return pd.DataFrame()

    def get_pesos_reales(self) -> Dict[str, float]:
        """
        Calcula los pesos reales del portafolio según el valor de mercado
        de cada posición.

        Returns
        -------
        Dict[str, float]
            Diccionario {ticker: peso} con pesos normalizados a 1.
        """
        try:
            positions = self._obtener_posiciones()
            valores = {pos.symbol: float(pos.market_value) for pos in positions}
            total_cartera = sum(valores.values())

            if total_cartera == 0:
                print("El valor total de la cartera es cero; no se pueden calcular pesos.")
                return {}

            pesos = {ticker: valor / total_cartera for ticker, valor in valores.items()}

            print("Pesos reales calculados por valor de mercado:")
            for t, w in pesos.items():
                print(f"  {t}: {w:.2%}")

            return pesos

        except APIError as e:
            print(f"Error de API al obtener posiciones: {e}")
            return {}
        except Exception as e:
            print(f"Error inesperado al calcular pesos: {e}")
            return {}

    def save_to_parquet(
        self, data: pd.DataFrame, filename: str = "market_data.parquet",
        target: Literal["raw", "processed"] = "raw",
    ) -> None:
        """
        Guarda el DataFrame en la carpeta de datos raw o processed.

        Parameters
        ----------
        data : pd.DataFrame
            DataFrame a guardar.
        filename : str
            Nombre del archivo de salida.
        target : {'raw', 'processed'}
            Carpeta de destino dentro de data/.
        """
        if data.empty:
            print("No hay datos para guardar (DataFrame vacío).")
            return

        destino = cfg.RAW_DIR if target == "raw" else cfg.PROCESSED_DIR

        try:
            output_path = destino / filename
            data.to_parquet(output_path)
            print(f"Datos guardados exitosamente en: {output_path}")
        except OSError as e:
            print(f"Error de sistema de archivos al guardar: {e}")
        except Exception as e:
            print(f"Error inesperado al guardar datos: {e}")
