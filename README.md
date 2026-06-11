# Portfolio Market Risk

Sistema de monitoreo de riesgo de mercado para portafolios de inversión. Construye un portafolio multi-activo, extrae datos históricos desde Alpaca Markets y calcula métricas de riesgo avanzadas: VaR paramétrico, VaR lognormal con volatilidad condicional EWMA, Expected Shortfall (CVaR) y pruebas de estrés.

## Características

- **Gestión de cartera automatizada** — creación y órdenes de mercado en Alpaca Paper Trading para un portafolio diversificado (`VT`, `ECH`, `VNQ`, `GLD`, `AGG`).
- **Pipeline ETL** — extracción de precios ajustados, cálculo de pesos por valor de mercado y almacenamiento en formato Parquet.
- **Value at Risk (VaR)** — paramétrico normal y lognormal con volatilidad condicional EWMA (RiskMetrics, $\lambda = 0.94$).
- **Expected Shortfall (CVaR)** — pérdida esperada en la cola, ponderada exponencialmente para reflejar condiciones recientes de mercado.
- **Stress testing** — simulación de crisis mediante shocks multiplicativos a la volatilidad del portafolio.

## Estructura del proyecto

```
.
├── src/
│   ├── config.py                    # Configuración global, rutas y credenciales
│   ├── cartera/
│   │   └── creador_cartera.py       # Creación automatizada del portafolio en Alpaca
│   ├── etl/
│   │   └── extracción_data.py       # Extracción de precios y pesos reales
│   └── riesgo/
│       └── riesgo.py                # Motor de cálculo de métricas de riesgo
├── data/
│   ├── raw/                         # Datos históricos en formato Parquet
│   └── processed/                   # Resultados del análisis listos para visualización
├── main.py                          # Script principal de orquestación (CLI)
└── pyproject.toml                   # Dependencias y configuración del paquete
```

## Requisitos

- Python 3.10 o superior
- Cuenta de [Alpaca Markets](https://alpaca.markets/) (Paper Trading recomendado para desarrollo)

## Instalación

```bash
git clone <repo-url>
cd portfolio_market_risk

python -m venv .venv
source .venv/bin/activate  # Linux / macOS
# .venv\Scripts\activate   # Windows

pip install -e .
```

## Configuración

1. Copia el archivo de ejemplo y edítalo con tus credenciales de Alpaca:

```bash
cp .env.example .env
```

2. Edita `.env`:

```env
key=TU_API_KEY
secret=TU_API_SECRET
```

## Uso

### 1. Crear el portafolio

Compra los activos iniciales en tu cuenta Paper de Alpaca:

```bash
python src/cartera/creador_cartera.py
```

### 2. Ejecutar el análisis de riesgo

```bash
python main.py
```

Opciones disponibles:

| Flag | Descripción |
|------|-------------|
| `-c`, `--confianza` | Nivel de confianza para VaR/CVaR (default: `0.95`) |
| `-l`, `--lambda-ewma` | Factor de decaimiento EWMA (default: `0.94`) |
| `-s`, `--factor-estres` | Factor de shock de volatilidad (default: `2.0`) |
| `--no-exportar` | Solo imprime métricas, no exporta a `data/processed/` |
| `-q`, `--quiet` | Suprime la impresión de la matriz de correlación |

Ejemplos:

```bash
python main.py -c 0.99                    # VaR al 99% de confianza
python main.py -s 3.0 --lambda-ewma 0.90  # Stress x3, lambda más reactiva
python main.py --no-exportar -q           # Solo imprimir VaR/CVaR
```

Salida esperada:

```
--- MATRIZ DE CORRELACIONES ---
           VT       ECH       VNQ       GLD       AGG
VT   1.000000  0.723456  0.812345 -0.123456  0.345678
ECH  0.723456  1.000000  0.654321 -0.098765  0.234567
...

VaR Normal (95%):    -1.85%
VaR Lognormal (95%): -1.83%
Expected Shortfall:  -2.41%

--- PRUEBA DE ESTRÉS: SHOCK DE VOLATILIDAD (Factor x2.0) ---
VaR Normal (histórico):    -1.85%
VaR Normal (estresado):    -3.70%
VaR Lognormal (estresado): -3.64%
```

### 3. Resultados exportados

Al ejecutar sin `--no-exportar`, se generan los siguientes archivos en `data/processed/`:

| Archivo | Contenido |
|---------|-----------|
| `dataset_graficos.parquet` | DataFrame unificado (fecha, retorno, VaR 95/99, volatilidad EWMA, violaciones) listo para graficar |
| `retornos_portafolio.parquet` | Serie diaria de retornos del portafolio |
| `volatilidad_ewma.parquet` | Serie temporal de volatilidad condicional EWMA anualizada |
| `var_rodante.parquet` | VaR en ventana móvil de 252 días |
| `matriz_correlacion.parquet` | Matriz de correlación entre activos |
| `resumen_riesgo.json` | Métricas puntuales: VaR, CVaR, Sharpe ratio, stress test, pesos |

## Metodología

### Value at Risk (VaR)

| Variante | Descripción |
|----------|-------------|
| **VaR Normal** | Paramétrico bajo distribución normal de retornos logarítmicos. $\text{VaR}_\alpha = \mu + z_\alpha \cdot \sigma$ |
| **VaR Lognormal** | Asume distribución lognormal para retornos simples, acotando pérdidas a un máximo de -100 %. Utiliza volatilidad condicional EWMA con $\lambda = 0.94$. |

### Expected Shortfall (CVaR)

Pérdida promedio en el peor $(1-\alpha)\%$ de los escenarios. El umbral de cola se determina con el cuantil empírico (VaR histórico) y los retornos en la cola se ponderan con EWMA para priorizar observaciones recientes.

### EWMA (Exponentially Weighted Moving Average)

Los pesos decaen exponencialmente hacia el pasado según:

$$w_t = \frac{(1 - \lambda) \cdot \lambda^{t-1}}{\sum_{i=1}^T (1 - \lambda) \cdot \lambda^{i-1}}$$

con $\lambda = 0.94$ (estándar RiskMetrics para datos diarios, vida media de $\approx 11$ días).

## Dependencias principales

| Librería | Uso |
|----------|-----|
| `pandas` | Manipulación de series temporales |
| `numpy` | Operaciones vectorizadas |
| `scipy` | Cuantiles de la distribución normal |
| `alpaca-trade-api` | Conexión con Alpaca Markets |
| `python-dotenv` | Carga de variables de entorno |
| `matplotlib`, `seaborn` | Visualizaciones (extensible) |

## Limitaciones y próximos pasos

- EWMA se aplica a la volatilidad del portafolio agregado (univariado). Una extensión natural es implementar la matriz de covarianza EWMA multivariada para descomposición del riesgo por activo.
- No se modelan colas pesadas. La incorporación de una distribución t de Student o Teoría de Valores Extremos (EVT) mejoraría la precisión en escenarios de crisis.
- Backtesting automático (tests de Kupiec y Christoffersen) para validación estadística.
- Visualizaciones: evolución temporal del VaR/CVaR, heatmap de correlaciones y frontera eficiente.

## Licencia

MIT
