from src.etl.extracción_data import CargaDatos
from src.riesgo.riesgo import AnalisisRiesgo
import src.config as cfg
import pandas as pd

# Instancias

datos = CargaDatos(cfg.key, cfg.secret, cfg.base_url)

pesos_cartera = datos.get_pesos_reales()

riesgo = AnalisisRiesgo(pesos_dict = pesos_cartera)

# Cálculos

log_returns = riesgo.calcular_log_returns()

var_norm = riesgo.calcular_var_normal()

var_exp = riesgo.calcular_var_cornish()

es = riesgo.calcular_expected_shortfall()

print(f"El VaR normal es:{var_norm:.2%}, siendo que el Cornish-Fisher es de: {var_exp:.2%}, por su parte, el ES es de: {es:.2%}")


riesgo.test_estres_volatilidad()