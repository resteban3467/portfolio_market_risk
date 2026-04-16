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

correlaciones = riesgo.calcular_matriz_correlacion()
print("\n--- MATRIZ DE CORRELACIONES ---")
print(correlaciones)
print("-------------------------------\n")

var_norm = riesgo.calcular_var_normal()

var_log = riesgo.calcular_var_lognormal()

es = riesgo.calcular_expected_shortfall()

print(f"El VaR normal es:{var_norm:.2%}, siendo que el Lognormal es de: {var_log:.2%}, por su parte, el ES es de: {es:.2%}")


riesgo.test_estres_volatilidad()