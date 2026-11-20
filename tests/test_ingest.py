import pandas as pd

from pipeline.ingest import a_diario


def datos_cada_30_min(desde: str, intervalos: int) -> pd.DataFrame:
    ts = pd.date_range(desde, periods=intervalos, freq="30min")
    return pd.DataFrame({"ts": ts, "demanda": 100.0, "pronostico_coes": 100.0})


def test_el_dato_de_medianoche_pertenece_al_dia_anterior():
    # 48 intervalos: del 01/01 00:30 al 02/01 00:00 -> un solo día completo, el 1 de enero
    diario = a_diario(datos_cada_30_min("2024-01-01 00:30", 48))
    assert list(diario.index) == [pd.Timestamp("2024-01-01")]


def test_los_dias_incompletos_se_descartan():
    # Un día completo + 10 intervalos del día siguiente (por ejemplo, "hoy" a media mañana)
    diario = a_diario(datos_cada_30_min("2024-01-01 00:30", 48 + 10))
    assert list(diario.index) == [pd.Timestamp("2024-01-01")]
