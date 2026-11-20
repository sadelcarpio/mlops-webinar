"""Features del modelo.

Esta MISMA función se usa al entrenar y al predecir. Si las features se calcularan de forma
distinta en cada lado, el modelo fallaría en silencio (training/serving skew)."""
import pandas as pd

from pipeline import config

FEATURES = [f"lag_{i}" for i in range(1, config.N_LAGS + 1)] + ["dia_semana"]


def crear_features(diario: pd.DataFrame) -> pd.DataFrame:
    """Una fila por día con la demanda de ese día y la de los N días anteriores."""
    df = diario.asfreq("D")  # si falta un día, queda vacío (no se inventa nada)
    for i in range(1, config.N_LAGS + 1):
        df[f"lag_{i}"] = df["demanda"].shift(i)
    df["dia_semana"] = df.index.day_of_week
    return df


def features_para(diario: pd.DataFrame, fecha: pd.Timestamp) -> pd.DataFrame:
    """Las features para predecir `fecha`, usando solo los días anteriores."""
    historia = diario[diario.index < fecha]
    con_fecha = historia.reindex(historia.index.union([fecha]))
    return crear_features(con_fecha).loc[[fecha], FEATURES]
