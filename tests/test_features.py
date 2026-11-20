import numpy as np
import pandas as pd

from pipeline.features import crear_features, features_para


def test_los_lags_son_los_dias_anteriores(datos):
    df = crear_features(datos)
    dia = pd.Timestamp("2018-06-15")
    assert df.loc[dia, "lag_1"] == datos.loc[dia - pd.Timedelta(days=1), "demanda"]
    assert df.loc[dia, "lag_7"] == datos.loc[dia - pd.Timedelta(days=7), "demanda"]


def test_las_features_no_usan_el_dia_a_predecir(datos):
    """Si cambiamos la demanda del día que queremos predecir, sus features no deben cambiar."""
    dia = pd.Timestamp("2018-06-15")
    antes = features_para(datos, dia)
    modificado = datos.copy()
    modificado.loc[dia, "demanda"] = 999_999
    assert antes.equals(features_para(modificado, dia))


def test_si_falta_un_dia_no_se_inventa(datos):
    sin_un_dia = datos.drop(pd.Timestamp("2018-06-14"))
    X = features_para(sin_un_dia, pd.Timestamp("2018-06-15"))
    assert np.isnan(X["lag_1"].iloc[0])
