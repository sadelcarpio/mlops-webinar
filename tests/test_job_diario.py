from datetime import UTC, date, datetime

import pandas as pd

from pipeline import config, job_diario
from pipeline.train import cargar_modelo


def test_hoy_usa_la_hora_de_lima():
    # 20 de noviembre a las 2 am en UTC = 19 de noviembre a las 9 pm en Lima
    assert config.hoy(datetime(2026, 11, 20, 2, 0, tzinfo=UTC)) == date(2026, 11, 19)


def test_el_job_reentrena_solo_cuando_el_modelo_es_viejo(datos, monkeypatch):
    monkeypatch.setattr(job_diario, "ingestar", lambda: None)  # sin internet en los tests

    job_diario.correr(pd.Timestamp("2019-06-01"))  # no hay modelo -> entrena
    assert cargar_modelo()[1]["entrenado_hasta"] == "2019-06-01"

    job_diario.correr(pd.Timestamp("2019-06-03"))  # modelo de 2 días -> no reentrena
    assert cargar_modelo()[1]["entrenado_hasta"] == "2019-06-01"

    job_diario.correr(pd.Timestamp("2019-06-08"))  # modelo de 7 días -> reentrena
    assert cargar_modelo()[1]["entrenado_hasta"] == "2019-06-08"
