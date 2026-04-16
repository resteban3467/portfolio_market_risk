import numpy as np
import pandas as pd
from scipy.stats import norm
import src.config as cfg

class AnalisisRiesgo:
    def __init__(self, pesos_dict: dict = None, filename: str = 'market_data.parquet'):
        """
        Inicia el análisis cargando precios y asignando los pesos reales.
        """
        self.path = cfg.RAW_DIR / filename
        self.df_precios = pd.read_parquet(self.path)
        
        # Atributos para almacenar resultados
        self.log_returns = None
        self.retornos_portafolio = None
        
        # Asignación de pesos a cada instrumento en cartera.
        if pesos_dict:
            self.pesos = np.array([pesos_dict[col] for col in self.df_precios.columns])
            print("Pesos reales cargados y alineados correctamente.")
        else:
            num_activos = len(self.df_precios.columns)
            self.pesos = np.array([1/num_activos] * num_activos)
            print("No se detectaron pesos. Usando cartera equiponderada.")

    def calcular_log_returns(self):
        """Calcula retornos logarítmicos por activo y para el portafolio total."""
        self.log_returns = np.log(self.df_precios / self.df_precios.shift(1)).dropna()
        # Producto punto para el promedio ponderado diario
        self.retornos_portafolio = self.log_returns.dot(self.pesos)
        return self.retornos_portafolio

    def calcular_matriz_correlacion(self):
        """Calcula la matriz de correlación entre los instrumentos de la cartera."""
        if self.log_returns is None:
            self.calcular_log_returns()
            
        correlaciones = self.log_returns.corr()
        return correlaciones

    def calcular_var_normal(self, confianza: float = 0.95, desv_estres = None):
        """VaR bajo el supuesto de distribución normal."""
        if self.retornos_portafolio is None: 
            self.calcular_log_returns()

        media = self.retornos_portafolio.mean()
        if not desv_estres:
            desv = self.retornos_portafolio.std()
        else:
            desv = desv_estres
        z = norm.ppf(1 - confianza)

        return media + z * desv

    def calcular_var_lognormal(self, confianza: float = 0.95, desv_estres = None, lambda_ewma: float = 0.94):
        """VaR bajo el supuesto de distribución lognormal (retornos simples) con volatilidad EWMA."""
        if self.retornos_portafolio is None: 
            self.calcular_log_returns()

        media = self.retornos_portafolio.mean()
        retornos = self.retornos_portafolio

        if not desv_estres:
            # Calcular volatilidad ponderada por EWMA
            t = len(retornos)
            pesos = (1 - lambda_ewma) * (lambda_ewma ** np.arange(t - 1, -1, -1))
            pesos /= pesos.sum()
            
            varianza_ewma = np.sum(pesos * (retornos - media)**2)
            desv = np.sqrt(varianza_ewma)
        else:
            desv = desv_estres

        z = norm.ppf(1 - confianza)
    
        return np.exp(media + z * desv) - 1


    def calcular_expected_shortfall(self, confianza: float = 0.95, lambda_ewma: float = 0.94):
            """
            Calcula el Expected Shortfall (Pérdida promedio en el peor escenario)
            ponderado por EWMA (Exponentially Weighted Moving Average).
            """
            if self.retornos_portafolio is None: 
                self.calcular_log_returns()
                
            retornos = self.retornos_portafolio
            
            # 1. Calculamos el VaR Histórico como umbral
            var_umbral = retornos.quantile(1 - confianza)
            
            # 2. Creamos los pesos EWMA (mayor peso a observaciones más recientes)
            t = len(retornos)
            pesos = (1 - lambda_ewma) * (lambda_ewma ** np.arange(t - 1, -1, -1))
            pesos /= pesos.sum() # Normalizamos para que la suma total sea 1
            
            # 3. Filtramos los retornos y sus pesos en los peores casos
            mascara_peores = (retornos <= var_umbral).values
            peores_casos = retornos.values[mascara_peores]
            pesos_cola = pesos[mascara_peores]
            
            # 4. Normalizamos los pesos en la cola para que su suma sea 1 y calculamos el promedio ponderado
            pesos_cola_norm = pesos_cola / pesos_cola.sum()
            return np.sum(peores_casos * pesos_cola_norm)

    def test_estres_volatilidad(self, factor_shock: float = 2.0, confianza: float = 0.95):
            """
            Simula el impacto de un aumento súbito en la volatilidad del mercado.
            factor_shock=2.0 significa que la volatilidad se duplica.
            """
            if self.retornos_portafolio is None: self.calcular_log_returns()
            
            media = self.retornos_portafolio.mean()
            desv_historica = self.retornos_portafolio.std()
            
            # Aplicamos el shock a la varianza (volatilidad)
            desv_estresada = desv_historica * factor_shock
            
            var_estresado = self.calcular_var_normal(desv_estres= desv_estresada)   

            var_lognormal_estresado = self.calcular_var_lognormal(desv_estres= desv_estresada)         
            print(f"\n--- SHOCK DE VOLATILIDAD (Factor x{factor_shock}) ---")
            print(f"VaR Normal (Histórico): {self.calcular_var_normal():.2%}")
            print(f"VaR Estresado:          {var_estresado:.2%}")
            print(f"VaR Lognormal Estresado:          {var_lognormal_estresado :.2%}")
            
            return var_estresado, var_lognormal_estresado