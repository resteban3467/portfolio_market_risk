import numpy as np
import pandas as pd
from scipy.stats import norm
import src.config as cfg

class analisisRiesgo:
    def __init__(self, filename : str = "market_data.parquet"):
        self.path = cfg.RAW_DIR / filename
        self.df_precios = pd.read_parquet(self.path)
        self.log_returns = None
        self.retornos_portafolio = None

        # Se asume distribución pareja de pesos en cartera.
        num_activos = len(self.df_precios.columns)
        self.pesos = np.array([1/num_activos] * num_activos) 
    
    def calcular_log_returns(self):
        self.log_returns = np.log(self.df_precios / self.df_precios.shift(1)).dropna()
        self.retornos_portafolio = self.log_returns.dot(self.pesos)
        return self.retornos_portafolio

    def calcular_var_normal(self, confianza: float = 0.95):
        if self.calcular_log_returns is None: self.calcular_log_returns()

        media = self.retornos_portafolio.mean()
        desv = self.retornos_portafolio.std()

        z = norm.ppf(1-confianza)

        return media + z *desv

    def calcular_var_cornish(self, confianza: float = 0.95):
        if self.calcular_log_returns is None: self.calcular_log_returns()

        media = self.retornos_portafolio.mean()
        desv = self.retornos_portafolio.std()
        s = self.retornos_portafolio.skew()
        k = self.retornos_portafolio.kurt()

        z = norm.ppf(1-confianza)
    
        z_cf = (z + 
                (1/6) * (z**2 - 1) * s + 
                (1/24) * (z**3 - 3*z) * k - 
                (1/36) * (2*z**3 - 5*z) * (s**2))
        
        return media + z_cf * desv


