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

    def calcular_var_cornish(self, confianza: float = 0.95, desv_estres = None):
        """VaR ajustado por asimetría y curtosis (Cornish-Fisher)."""
        if self.retornos_portafolio is None: 
            self.calcular_log_returns()

        media = self.retornos_portafolio.mean()

        if not desv_estres:
            desv = self.retornos_portafolio.std()
        else:
            desv = desv_estres

        s = self.retornos_portafolio.skew()
        k = self.retornos_portafolio.kurt() # Pandas calcula exceso de curtosis por defecto

        z = norm.ppf(1 - confianza)
    
        # Fórmula de expansión de Cornish-Fisher
        z_cf = (z + 
                (1/6) * (z**2 - 1) * s + 
                (1/24) * (z**3 - 3*z) * k - 
                (1/36) * (2*z**3 - 5*z) * (s**2))
        
        return media + z_cf * desv


    def calcular_expected_shortfall(self, confianza: float = 0.95):
            """
            Calcula el Expected Shortfall (Pérdida promedio en el peor escenario).
            """
            if self.retornos_portafolio is None: 
                self.calcular_log_returns()
                
            # 1. Calculamos el VaR Histórico como umbral
            var_umbral = self.retornos_portafolio.quantile(1 - confianza)
            
            # 2. Filtramos solo los días donde la pérdida fue peor que el VaR
            peores_casos = self.retornos_portafolio[self.retornos_portafolio <= var_umbral]
            
            # 3. El promedio de esos peores casos es el ES
            return peores_casos.mean()

    def test_estres_volatilidad(self, factor_shock: float = 10.0, confianza: float = 0.95):
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

            var_cornis_fisher_estresado = self.calcular_var_cornish(desv_estres= desv_estresada)         
            print(f"\n--- SHOCK DE VOLATILIDAD (Factor x{factor_shock}) ---")
            print(f"VaR Normal (Histórico): {self.calcular_var_normal():.2%}")
            print(f"VaR Estresado:          {var_estresado:.2%}")
            print(f"VaR Cornish-Fisher Estresado:          {var_cornis_fisher_estresado :.2%}")
            
            return var_estresado, var_cornis_fisher_estresado