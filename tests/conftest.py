"""Datos de prueba: 3 años de demanda sintética con patrón semanal. Sin internet ni MLflow."""
import numpy as np
import pandas as pd
import pytest

from pipeline import config


@pytest.fixture
def datos(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)  # cada test usa su propia carpeta
    monkeypatch.setattr(config, "MLFLOW_TRACKING_URI", "")  # sin MLflow en los tests

    fechas = pd.date_range("2017-01-01", "2019-12-31", freq="D", name="fecha")
    rng = np.random.default_rng(42)
    demanda = 6000 - 400 * (fechas.day_of_week == 6) + rng.normal(0, 30, len(fechas))
    diario = pd.DataFrame({"demanda": demanda, "pronostico_coes": demanda * 1.01}, index=fechas)
    diario.to_parquet(config.ruta("demanda_diaria.parquet"))
    return diario
