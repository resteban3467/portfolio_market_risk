#!/usr/bin/env python3
"""
Portfolio Market Risk — Script principal de análisis de riesgo de mercado.

Orquesta la extracción de datos desde Alpaca, el cálculo de métricas de riesgo
(VaR, CVaR, volatilidad EWMA) y la exportación de resultados listos para
visualización en data/processed/.

Uso:
    python main.py
    python main.py --confianza 0.99 --no-exportar
"""

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from src.etl.extracción_data import CargaDatos
from src.riesgo.riesgo import AnalisisRiesgo
import src.config as cfg

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("portfolio_risk")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Análisis de riesgo de mercado para el portafolio de Alpaca.",
    )
    parser.add_argument(
        "--confianza", "-c",
        type=float,
        default=0.95,
        help="Nivel de confianza para VaR y CVaR (default: 0.95).",
    )
    parser.add_argument(
        "--lambda-ewma", "-l",
        type=float,
        default=0.94,
        dest="lambda_ewma",
        help="Factor de decaimiento EWMA (default: 0.94, RiskMetrics).",
    )
    parser.add_argument(
        "--factor-estres", "-s",
        type=float,
        default=2.0,
        dest="factor_estres",
        help="Factor multiplicativo de volatilidad para stress test (default: 2.0).",
    )
    parser.add_argument(
        "--no-exportar",
        action="store_true",
        help="No exportar resultados a data/processed/.",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suprimir la impresión de la matriz de correlación.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    logger.info("Iniciando análisis de riesgo del portafolio")

    # ------------------------------------------------------------------
    # 1. Validar credenciales
    # ------------------------------------------------------------------
    if not cfg.key or not cfg.secret:
        logger.error(
            "Credenciales de Alpaca no configuradas. "
            "Configura .env con key= y secret= antes de ejecutar."
        )
        return 1

    # ------------------------------------------------------------------
    # 2. Extraer datos y pesos desde Alpaca
    # ------------------------------------------------------------------
    datos = CargaDatos(cfg.key, cfg.secret, cfg.base_url)
    pesos_cartera = datos.get_pesos_reales()

    if not pesos_cartera:
        logger.error("No se pudieron obtener los pesos del portafolio.")
        return 1

    # ------------------------------------------------------------------
    # 3. Instanciar motor de riesgo
    # ------------------------------------------------------------------
    try:
        riesgo = AnalisisRiesgo(pesos_dict=pesos_cartera)
    except KeyError as e:
        logger.error(f"Inconsistencia entre pesos y datos de mercado: {e}")
        return 1
    except FileNotFoundError:
        logger.error(
            "No se encontró market_data.parquet en data/raw/. "
            "Ejecuta primero CargaDatos.fetch_market_data() para descargar los datos."
        )
        return 1

    # ------------------------------------------------------------------
    # 4. Cálculos
    # ------------------------------------------------------------------
    riesgo.calcular_log_returns()

    if not args.quiet:
        correlaciones = riesgo.calcular_matriz_correlacion()
        print("\n--- MATRIZ DE CORRELACIONES ---")
        print(correlaciones.round(4).to_string())
        print("-------------------------------\n")

    # ------------------------------------------------------------------
    # 5. Exportar resultados
    # ------------------------------------------------------------------
    if args.no_exportar:
        var_norm = riesgo.calcular_var_normal(confianza=args.confianza)
        var_log = riesgo.calcular_var_lognormal(confianza=args.confianza, lambda_ewma=args.lambda_ewma)
        es_val = riesgo.calcular_expected_shortfall(confianza=args.confianza, lambda_ewma=args.lambda_ewma)
        print(
            f"VaR Normal ({args.confianza:.0%}):    {var_norm:.4%}\n"
            f"VaR Lognormal ({args.confianza:.0%}): {var_log:.4%}\n"
            f"Expected Shortfall ({args.confianza:.0%}): {es_val:.4%}"
        )
        riesgo.test_estres_volatilidad(factor_shock=args.factor_estres, confianza=args.confianza)
    else:
        riesgo.exportar_resultados(confianza=args.confianza, lambda_ewma=args.lambda_ewma)

    logger.info("Análisis completado exitosamente")
    return 0


if __name__ == "__main__":
    sys.exit(main())
