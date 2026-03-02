import pandas as pd
from src.config import BASE_DIR

from src.etl.extracción_data import get_pesos_cartera

df = pd.read_parquet(f"{BASE_DIR}/data/raw/market_data.parquet")
print(df)

df1 = get_pesos_cartera()
print(df1)