import numpy as np
import pandas as pd
import src.config as cfg

class analisisRiesgo:
    def __init__(self, filename : str = "market_data.parquet"):
        self.path = cfg.RAW_DIR / filename
        self.df_precios = pd.read_parquet(self.path)
        self.log_returns = None
    
    def log_returns(self):
        self.log_returns = np.log(self.df_precios / self.df_precios.shift(1)).dropna()
        return self.log_returns