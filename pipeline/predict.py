"""Paso 3 - Predicción: la demanda promedio de un día, con el modelo entrenado.

Uso:
    uv run python -m pipeline.predict                     # hoy
    uv run python -m pipeline.predict --fecha 2020-03-20
"""
import argparse
from datetime import date

import pandas as pd

from pipeline import config
from pipeline.features import features_para
from pipeline.train import cargar_modelo


def predecir(fecha: pd.Timestamp) -> float:
    diario = pd.read_parquet(config.ruta("demanda_diaria.parquet"))
    X = features_para(diario, fecha)
    if X.isna().any(axis=None):
        raise ValueError(f"Faltan datos de los {config.N_LAGS} días anteriores a {fecha:%Y-%m-%d}")

    modelo, metadata = cargar_modelo()
    prediccion = float(modelo.predict(X)[0])
    guardar_prediccion(fecha, prediccion, metadata["entrenado_hasta"])
    print(f"[predict] {fecha:%Y-%m-%d}: {prediccion:,.0f} MW")
    return prediccion


def guardar_prediccion(fecha: pd.Timestamp, prediccion: float, modelo: str) -> None:
    """Agrega la predicción al historial (si ya había una para esa fecha, la reemplaza)."""
    archivo = config.ruta("predicciones.parquet")
    nueva = pd.DataFrame({"prediccion": [prediccion], "modelo": [modelo]},
                         index=pd.DatetimeIndex([fecha], name="fecha"))
    if archivo.exists():
        anteriores = pd.read_parquet(archivo)
        nueva = pd.concat([anteriores.drop(fecha, errors="ignore"), nueva]).sort_index()
    nueva.to_parquet(archivo)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fecha", type=date.fromisoformat, default=date.today())
    predecir(pd.Timestamp(parser.parse_args().fecha))
