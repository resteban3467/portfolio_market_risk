# portfolio_market_risk

Es un proyecto integral donde simulo un portafolio de inversión y evalúo su exposición al riesgo de mercado a través de diversas metodologías financieras, extrayendo datos directamente del mercado mediante la API de Alpaca.

## Características Principales

* **Gestión de Cartera Automática**: Creación y compra automatizada de un portafolio (`VT`, `ECH`, `VNQ`, `GLD`, `AGG`) utilizando la API de simulación (Paper Trading) de Alpaca.
* **Pipeline de Datos (ETL)**: Extracción automatizada de datos históricos de precios ajustados y cálculo de los pesos reales del portafolio en base al valor de mercado, almacenándolos eficientemente de manera local en formato `.parquet`.
* **Análisis de Riesgo Avanzado**:
  * Cálculo de retornos logarítmicos del portafolio.
  * **VaR Normal**: Cálculo paramétrico clásico del Valor en Riesgo.
  * **VaR Lognormal**: Valor en Riesgo bajo el supuesto de distribución lognormal, aplicando volatilidad dinámica ponderada exponencialmente (**EWMA**).
  * **Expected Shortfall (ES)**: Cálculo de la pérdida esperada condicional en la cola de la distribución, ajustada también por decaimiento exponencial (**EWMA**).
  * **Pruebas de Estrés (Stress Testing)**: Simulación de escenarios de crisis aplicando shocks multiplicativos a la volatilidad del portafolio.

## Estructura del Proyecto

* `src/cartera/creador_cartera.py`: Script para ejecutar órdenes de mercado en Alpaca y constituir el portafolio base.
* `src/etl/extracción_data.py`: Módulo que maneja la conexión con Alpaca, lista posiciones, calcula pesos reales y descarga datos históricos.
* `src/riesgo/riesgo.py`: Motor matemático para el cálculo de métricas de exposición de riesgo (VaR, ES, EWMA y shocks de volatilidad).
* `test.py`: Script principal de ejecución y orquestación que instancia las clases, ejecuta los cálculos e imprime los resultados en consola.

## Configuración y Requisitos

1. Asegúrate de tener instalado Python 3.x.
2. Instala las dependencias necesarias. Necesitarás librerías como `pandas`, `numpy`, `scipy`, `alpaca_trade_api`, y `python-dotenv`.
3. Crea un archivo `.env` en la raíz de tu proyecto con tus credenciales de Alpaca Paper Trading:
   ```env
   key=TU_API_KEY
   secret=TU_API_SECRET
   ```
4. Asegúrate de tener tu configuración de rutas correcta en `src/config.py`.

## Uso

Para comprar los activos iniciales y armar el portafolio en tu cuenta virtual, ejecuta:
```bash
python src/cartera/creador_cartera.py
```
Para ejecutar el análisis de riesgo completo de tu cartera actual, ejecuta:
```bash
python test.py
```
