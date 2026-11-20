import pandas as pd

from pipeline import config
from pipeline.predict import predecir
from pipeline.train import entrenar


def test_entrenar_y_predecir(datos):
    metadata = entrenar(pd.Timestamp("2019-06-01"))
    assert metadata["mape_validacion"] < 5  # los datos sintéticos son fáciles de predecir

    prediccion = predecir(pd.Timestamp("2019-06-01"))
    real = datos.loc["2019-06-01", "demanda"]
    assert abs(prediccion - real) / real < 0.05

    guardadas = pd.read_parquet(config.ruta(config.ARCHIVO_PREDICCIONES))
    assert list(guardadas.index) == [pd.Timestamp("2019-06-01")]


def test_predecir_dos_veces_el_mismo_dia_no_duplica(datos):
    entrenar(pd.Timestamp("2019-06-01"))
    predecir(pd.Timestamp("2019-06-01"))
    predecir(pd.Timestamp("2019-06-01"))
    assert len(pd.read_parquet(config.ruta(config.ARCHIVO_PREDICCIONES))) == 1
