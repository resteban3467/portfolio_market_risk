import json
import numpy as np
import pandas as pd
from scipy.stats import norm
from typing import Optional, Dict
import src.config as cfg


class AnalisisRiesgo:
    """
    Motor de cálculo de métricas de riesgo de mercado para un portafolio.

    Implementa VaR paramétrico (normal y lognormal con volatilidad EWMA),
    Expected Shortfall y pruebas de estrés por shock de volatilidad.
    """

    def __init__(self, pesos_dict: Optional[Dict[str, float]] = None, filename: str = 'market_data.parquet'):
        """
        Inicia el análisis cargando precios históricos y asignando pesos.

        Parameters
        ----------
        pesos_dict : Dict[str, float], optional
            Diccionario {ticker: peso}. Si es None, se usa cartera equiponderada.
        filename : str
            Nombre del archivo parquet con los datos de precios históricos.
        """
        self.path = cfg.RAW_DIR / filename
        self.df_precios = pd.read_parquet(self.path)

        self.log_returns: Optional[pd.DataFrame] = None
        self.retornos_portafolio: Optional[pd.Series] = None

        # Validación y asignación de pesos
        if pesos_dict:
            tickers_df = set(self.df_precios.columns)
            tickers_pesos = set(pesos_dict.keys())
            faltantes = tickers_df - tickers_pesos
            sobrantes = tickers_pesos - tickers_df

            if faltantes:
                raise KeyError(
                    f"Los siguientes tickers del DataFrame no tienen peso asignado: {faltantes}"
                )
            if sobrantes:
                raise KeyError(
                    f"Los siguientes tickers del diccionario de pesos no están en los datos: {sobrantes}"
                )

            self.pesos = np.array([pesos_dict[col] for col in self.df_precios.columns])
            print("Pesos reales cargados y alineados correctamente.")
        else:
            num_activos = len(self.df_precios.columns)
            self.pesos = np.array([1.0 / num_activos] * num_activos)
            print(f"No se detectaron pesos. Usando cartera equiponderada (1/{num_activos}).")

    def _calcular_pesos_ewma(self, lambda_ewma: float, n: int) -> np.ndarray:
        """
        Calcula el vector de pesos exponencialmente decrecientes (EWMA).

        Parameters
        ----------
        lambda_ewma : float
            Factor de decaimiento (típicamente 0.94 para datos diarios).
        n : int
            Número de observaciones.

        Returns
        -------
        np.ndarray
            Vector de pesos EWMA normalizados (suma = 1).
        """
        if not 0 < lambda_ewma < 1:
            raise ValueError(f"lambda_ewma debe estar en (0, 1). Recibido: {lambda_ewma}")

        pesos = (1 - lambda_ewma) * (lambda_ewma ** np.arange(n - 1, -1, -1))
        return pesos / pesos.sum()

    def calcular_log_returns(self) -> pd.Series:
        """
        Calcula retornos logarítmicos por activo y el retorno ponderado del portafolio.

        Returns
        -------
        pd.Series
            Serie de retornos logarítmicos diarios del portafolio.
        """
        self.log_returns = np.log(self.df_precios / self.df_precios.shift(1)).dropna()
        self.retornos_portafolio = self.log_returns.dot(self.pesos)
        self.retornos_portafolio.name = 'retorno_portafolio'
        return self.retornos_portafolio

    def calcular_matriz_correlacion(self) -> pd.DataFrame:
        """
        Calcula la matriz de correlación lineal entre los activos del portafolio.

        Returns
        -------
        pd.DataFrame
            Matriz de correlación (N x N) con tickers como índices y columnas.
        """
        if self.log_returns is None:
            self.calcular_log_returns()

        return self.log_returns.corr()

    def calcular_var_normal(self, confianza: float = 0.95, desv_estres: Optional[float] = None) -> float:
        """
        Calcula el VaR bajo el supuesto de distribución normal de los retornos.

        Parameters
        ----------
        confianza : float
            Nivel de confianza (default 0.95).
        desv_estres : float, optional
            Desviación estándar en escenario de estrés. Si es None, usa la histórica.

        Returns
        -------
        float
            VaR como cuantil de retorno (negativo indica pérdida).
        """
        if self.retornos_portafolio is None:
            self.calcular_log_returns()

        media = self.retornos_portafolio.mean()
        desv = desv_estres if desv_estres is not None else self.retornos_portafolio.std()
        z = norm.ppf(1 - confianza)

        return media + z * desv

    def calcular_var_lognormal(
        self, confianza: float = 0.95, desv_estres: Optional[float] = None, lambda_ewma: float = 0.94
    ) -> float:
        """
        Calcula el VaR bajo el supuesto de distribución lognormal (retornos simples)
        utilizando volatilidad condicional EWMA.

        Parameters
        ----------
        confianza : float
            Nivel de confianza (default 0.95).
        desv_estres : float, optional
            Desviación estándar en escenario de estrés.
        lambda_ewma : float
            Factor de decaimiento EWMA (default 0.94, estándar RiskMetrics).

        Returns
        -------
        float
            VaR como retorno simple (ej. -0.02 = pérdida del 2 %).
        """
        if self.retornos_portafolio is None:
            self.calcular_log_returns()

        media = self.retornos_portafolio.mean()
        retornos = self.retornos_portafolio

        if desv_estres is not None:
            desv = desv_estres
        else:
            t = len(retornos)
            pesos = self._calcular_pesos_ewma(lambda_ewma, t)
            varianza_ewma = np.sum(pesos * (retornos.values - media) ** 2)
            desv = np.sqrt(varianza_ewma)

        z = norm.ppf(1 - confianza)
        return np.exp(media + z * desv) - 1

    def calcular_expected_shortfall(self, confianza: float = 0.95, lambda_ewma: float = 0.94) -> float:
        """
        Calcula el Expected Shortfall (CVaR) como la pérdida promedio en la cola
        de la distribución, ponderada por EWMA para dar más peso a observaciones recientes.

        Parameters
        ----------
        confianza : float
            Nivel de confianza (default 0.95).
        lambda_ewma : float
            Factor de decaimiento EWMA (default 0.94).

        Returns
        -------
        float
            Expected Shortfall como retorno (negativo indica pérdida).
        """
        if self.retornos_portafolio is None:
            self.calcular_log_returns()

        retornos = self.retornos_portafolio
        t = len(retornos)

        var_umbral = retornos.quantile(1 - confianza)

        pesos = self._calcular_pesos_ewma(lambda_ewma, t)

        mascara_peores = (retornos.values <= var_umbral)
        peores_casos = retornos.values[mascara_peores]
        pesos_cola = pesos[mascara_peores]

        if len(peores_casos) == 0:
            return var_umbral

        pesos_cola_norm = pesos_cola / pesos_cola.sum()
        return float(np.sum(peores_casos * pesos_cola_norm))

    def test_estres_volatilidad(
        self, factor_shock: float = 2.0, confianza: float = 0.95
    ) -> tuple[float, float]:
        """
        Simula el impacto de un shock multiplicativo en la volatilidad del mercado.

        Parameters
        ----------
        factor_shock : float
            Factor por el cual se multiplica la volatilidad histórica (default 2.0).
        confianza : float
            Nivel de confianza para el cálculo del VaR (default 0.95).

        Returns
        -------
        tuple[float, float]
            (VaR Normal estresado, VaR Lognormal estresado).
        """
        if self.retornos_portafolio is None:
            self.calcular_log_returns()

        desv_historica = self.retornos_portafolio.std()
        desv_estresada = desv_historica * factor_shock

        var_estresado = self.calcular_var_normal(desv_estres=desv_estresada)
        var_lognormal_estresado = self.calcular_var_lognormal(desv_estres=desv_estresada)

        print(f"\n--- PRUEBA DE ESTRÉS: SHOCK DE VOLATILIDAD (Factor x{factor_shock}) ---")
        print(f"VaR Normal (histórico):    {self.calcular_var_normal():.2%}")
        print(f"VaR Normal (estresado):    {var_estresado:.2%}")
        print(f"VaR Lognormal (estresado): {var_lognormal_estresado:.2%}")

        return var_estresado, var_lognormal_estresado

    def calcular_volatilidad_ewma_serie(self, lambda_ewma: float = 0.94) -> pd.Series:
        """
        Calcula la serie temporal completa de volatilidad condicional EWMA.

        Utiliza la fórmula recursiva:
            sigma²_t = lambda * sigma²_{t-1} + (1 - lambda) * (r_t - mu)²

        Parameters
        ----------
        lambda_ewma : float
            Factor de decaimiento (default 0.94).

        Returns
        -------
        pd.Series
            Volatilidad EWMA anualizada para cada día, indexada por fecha.
        """
        if self.retornos_portafolio is None:
            self.calcular_log_returns()

        retornos = self.retornos_portafolio.values
        fechas = self.retornos_portafolio.index
        media = self.retornos_portafolio.mean()
        t = len(retornos)

        var_ewma = np.zeros(t)
        var_ewma[0] = np.var(retornos)

        for i in range(1, t):
            var_ewma[i] = lambda_ewma * var_ewma[i - 1] + (1 - lambda_ewma) * (retornos[i] - media) ** 2

        volatilidad = np.sqrt(var_ewma) * np.sqrt(252)
        return pd.Series(volatilidad, index=fechas, name='volatilidad_ewma')

    def calcular_var_rodante(self, confianza: float = 0.95, ventana: int = 252) -> pd.Series:
        """
        Calcula el VaR paramétrico normal en ventanas móviles para backtesting.

        Parameters
        ----------
        confianza : float
            Nivel de confianza (default 0.95).
        ventana : int
            Número de días en la ventana móvil (default 252, un año de trading).

        Returns
        -------
        pd.Series
            VaR rodante alineado a la fecha de cada ventana.
        """
        if self.retornos_portafolio is None:
            self.calcular_log_returns()

        z = norm.ppf(1 - confianza)

        var_rodante = self.retornos_portafolio.rolling(window=ventana).apply(
            lambda x: x.mean() + z * x.std(),
            raw=True,
        )

        var_rodante.name = f'var_{confianza:.0%}'.replace('%', 'pct')
        return var_rodante.dropna()

    def exportar_resultados(self, confianza: float = 0.95, lambda_ewma: float = 0.94) -> None:
        """
        Calcula todas las métricas pendientes y persiste los resultados en data/processed/.

        Genera seis archivos listos para visualización y auditoría:
        - retornos_portafolio.parquet
        - matriz_correlacion.parquet
        - var_rodante.parquet
        - volatilidad_ewma.parquet
        - resumen_riesgo.json
        - dataset_graficos.parquet

        Parameters
        ----------
        confianza : float
            Nivel de confianza para VaR y CVaR (default 0.95).
        lambda_ewma : float
            Factor de decaimiento EWMA (default 0.94).
        """
        if self.retornos_portafolio is None:
            self.calcular_log_returns()

        processed = cfg.PROCESSED_DIR

        # 1. Retornos del portafolio
        self.retornos_portafolio.to_frame().to_parquet(processed / 'retornos_portafolio.parquet')

        # 2. Matriz de correlación
        self.calcular_matriz_correlacion().to_parquet(processed / 'matriz_correlacion.parquet')

        # 3. VaR rodante (95 % y 99 %)
        var_95 = self.calcular_var_rodante(confianza=0.95)
        var_99 = self.calcular_var_rodante(confianza=0.99)
        var_df = pd.DataFrame({'var_95': var_95, 'var_99': var_99})
        var_df.to_parquet(processed / 'var_rodante.parquet')

        volatilidad_ewma = self.calcular_volatilidad_ewma_serie(lambda_ewma=lambda_ewma)
        volatilidad_ewma.to_frame().to_parquet(processed / 'volatilidad_ewma.parquet')

        var_norm = self.calcular_var_normal(confianza=confianza)
        var_log = self.calcular_var_lognormal(confianza=confianza, lambda_ewma=lambda_ewma)
        es_val = self.calcular_expected_shortfall(confianza=confianza, lambda_ewma=lambda_ewma)
        var_estresado, var_log_estresado = self.test_estres_volatilidad(factor_shock=2.0, confianza=confianza)
        sharpe = (self.retornos_portafolio.mean() / self.retornos_portafolio.std()) * np.sqrt(252)

        resumen = {
            'var_normal': round(float(var_norm), 6),
            'var_lognormal': round(float(var_log), 6),
            'expected_shortfall': round(float(es_val), 6),
            'var_normal_estresado': round(float(var_estresado), 6),
            'var_lognormal_estresado': round(float(var_log_estresado), 6),
            'sharpe_ratio': round(float(sharpe), 4),
            'confianza': confianza,
            'lambda_ewma': lambda_ewma,
            'tickers': list(self.df_precios.columns),
            'pesos': {k: round(float(v), 6) for k, v in zip(self.df_precios.columns, self.pesos)},
        }

        with open(processed / 'resumen_riesgo.json', 'w', encoding='utf-8') as f:
            json.dump(resumen, f, indent=2, ensure_ascii=False, default=str)

        dataset = pd.DataFrame({'retorno': self.retornos_portafolio})
        dataset = dataset.join(var_95.rename('var_95'), how='left')
        dataset = dataset.join(var_99.rename('var_99'), how='left')
        dataset = dataset.join(volatilidad_ewma, how='left')
        dataset['violacion_var'] = dataset['retorno'] < dataset['var_95']
        dataset.to_parquet(processed / 'dataset_graficos.parquet')

        print(f'\nResultados exportados a: {processed}/')
        print(f'  - retornos_portafolio.parquet')
        print(f'  - matriz_correlacion.parquet')
        print(f'  - var_rodante.parquet')
        print(f'  - volatilidad_ewma.parquet')
        print(f'  - resumen_riesgo.json')
        print(f'  - dataset_graficos.parquet')
