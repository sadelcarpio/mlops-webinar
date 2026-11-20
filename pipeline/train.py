"""Paso 2 - Entrenamiento: XGBoost con la demanda de los últimos 14 días.

Uso:
    uv run python -m pipeline.train                     # con todos los datos hasta hoy
    uv run python -m pipeline.train --hasta 2020-01-01  # como si hoy fuera esa fecha
"""
import argparse
import json
from datetime import date

import pandas as pd
import xgboost as xgb

from pipeline import config
from pipeline.features import FEATURES, crear_features


def mape(real, prediccion) -> float:
    """Error porcentual absoluto medio."""
    return float(((real - prediccion).abs() / real).mean() * 100)


def entrenar(hasta: pd.Timestamp) -> dict:
    diario = pd.read_parquet(config.ruta("demanda_diaria.parquet"))
    df = crear_features(diario[diario.index < hasta]).dropna(subset=FEATURES + ["demanda"])
    df = df[df.index >= hasta - pd.DateOffset(years=config.ANIOS_ENTRENAMIENTO)]

    # Validación temporal: entrenamos con el pasado y evaluamos con las últimas semanas
    corte = hasta - pd.Timedelta(days=config.DIAS_VALIDACION)
    train, valid = df[df.index < corte], df[df.index >= corte]
    modelo = xgb.XGBRegressor(**config.PARAMS_XGB).fit(train[FEATURES], train["demanda"])
    metricas = {
        "mape_validacion": mape(valid["demanda"], modelo.predict(valid[FEATURES])),
        "mape_coes_validacion": mape(valid["demanda"], valid["pronostico_coes"]),
    }

    # Modelo final: entrenado con todos los datos de la ventana
    modelo = xgb.XGBRegressor(**config.PARAMS_XGB).fit(df[FEATURES], df["demanda"])
    metadata = {"entrenado_hasta": f"{hasta:%Y-%m-%d}", **metricas}

    if config.MLFLOW_TRACKING_URI:
        from pipeline.registro import registrar_en_mlflow
        metadata["mlflow_run_id"] = registrar_en_mlflow(metadata)

    config.ruta("modelo").mkdir(parents=True, exist_ok=True)
    modelo.save_model(config.ruta("modelo/modelo.json"))
    config.ruta("modelo/metadata.json").write_text(json.dumps(metadata, indent=2))
    print(f"[train] modelo entrenado hasta {hasta:%Y-%m-%d} | MAPE validación "
          f"{metricas['mape_validacion']:.2f}% (COES {metricas['mape_coes_validacion']:.2f}%)")
    return metadata


def cargar_modelo() -> tuple[xgb.XGBRegressor, dict]:
    modelo = xgb.XGBRegressor()
    modelo.load_model(config.ruta("modelo/modelo.json"))
    metadata = json.loads(config.ruta("modelo/metadata.json").read_text())
    return modelo, metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--hasta", type=date.fromisoformat, default=config.hoy())
    entrenar(pd.Timestamp(parser.parse_args().hasta))
