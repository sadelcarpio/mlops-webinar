from datetime import UTC, date, datetime

import pandas as pd

from pipeline import config, job_diario
from pipeline.train import cargar_modelo


def test_hoy_usa_la_hora_de_lima():
    # 20 de noviembre a las 2 am en UTC = 19 de noviembre a las 9 pm en Lima
    assert config.hoy(datetime(2026, 11, 20, 2, 0, tzinfo=UTC)) == date(2026, 11, 19)


def correr_dias(desde: str, hasta: str) -> None:
    for hoy in pd.date_range(desde, hasta):
        job_diario.correr(hoy, ingestar_datos=False)


def test_sin_cambios_en_los_datos_no_reentrena(datos):
    correr_dias("2019-06-01", "2019-07-15")
    assert cargar_modelo()[1]["entrenado_hasta"] == "2019-06-01"


def test_si_la_demanda_cae_de_golpe_reentrena(datos):
    # Simulamos una "cuarentena": desde el 1 de julio la demanda cae 40%
    datos.loc["2019-07-01":, ["demanda", "pronostico_coes"]] *= 0.6
    datos.to_parquet(config.ruta("demanda_diaria.parquet"))

    correr_dias("2019-06-01", "2019-07-15")
    assert cargar_modelo()[1]["entrenado_hasta"] > "2019-07-01"

    monitoreo = pd.read_parquet(config.ruta("monitoreo.parquet"))
    assert monitoreo["alerta"].any()
    assert not monitoreo.loc[:"2019-06-30", "alerta"].any()  # antes de la caída: sin alertas
