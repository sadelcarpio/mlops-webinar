"""El job que corre todos los días, solo:

    1. Ingesta: trae los datos de ayer del COES
    2. Reentrenamiento: si el modelo tiene más de DIAS_ENTRE_REENTRENOS días
    3. Predicción: la demanda de hoy

Uso:
    uv run python -m pipeline.job_diario
"""
import pandas as pd

from pipeline import config
from pipeline.ingest import ingestar
from pipeline.predict import predecir
from pipeline.train import cargar_modelo, entrenar


def correr(hoy: pd.Timestamp) -> float:
    ingestar()

    if not config.ruta("modelo/modelo.json").exists():
        entrenar(hoy)
    else:
        _, metadata = cargar_modelo()
        edad = (hoy - pd.Timestamp(metadata["entrenado_hasta"])).days
        if edad >= config.DIAS_ENTRE_REENTRENOS:
            entrenar(hoy)

    return predecir(hoy)


if __name__ == "__main__":
    correr(pd.Timestamp(config.hoy()))
