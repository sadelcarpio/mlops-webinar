"""El job que corre todos los días, solo:

    1. Ingesta: trae los datos de ayer del COES
    2. Monitoreo: compara lo que predijimos con lo que realmente pasó
    3. Si el error supera el umbral: reentrenar con los datos más recientes
    4. Predicción: la demanda de hoy

Uso:
    uv run python -m pipeline.job_diario
"""
import pandas as pd

from pipeline import config
from pipeline.ingest import ingestar
from pipeline.monitor import monitorear
from pipeline.predict import predecir
from pipeline.train import entrenar


def correr(hoy: pd.Timestamp, ingestar_datos: bool = True) -> float:
    if ingestar_datos:
        ingestar()

    if not config.ruta("modelo/modelo.json").exists():
        entrenar(hoy)

    if monitorear(hoy)["alerta"]:
        entrenar(hoy)

    return predecir(hoy)


if __name__ == "__main__":
    correr(pd.Timestamp(config.hoy()))
