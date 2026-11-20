"""Paso 1 - Ingesta: descarga la demanda del COES y la guarda como un valor por día.

La primera vez descarga todo desde PRIMER_ANIO. Las siguientes, solo lo que falta.

Uso:
    uv run python -m pipeline.ingest
"""
import pandas as pd
import requests

from pipeline import config

URL_COES = "https://www.coes.org.pe/Portal/portalinformacion/demanda"


def descargar_anio(anio: int) -> pd.DataFrame:
    """Demanda cada 30 minutos de un año: la real y el pronóstico oficial del COES."""
    respuesta = requests.post(URL_COES, timeout=120, data={
        "fechaInicial": f"01/01/{anio}",
        "fechaFinal": f"31/12/{anio}",
    })
    respuesta.raise_for_status()
    series = {s["Name"]: s["Data"] for s in respuesta.json()["Chart"]["Series"]}
    demanda = pd.Series({r["Nombre"]: r["Valor"] for r in series["Ejecutado"]})
    pronostico = pd.Series({r["Nombre"]: r["Valor"] for r in series["Programación Diaria"]})
    df = pd.DataFrame({"demanda": demanda, "pronostico_coes": pronostico})
    df.index = pd.to_datetime(df.index)
    return df.rename_axis("ts").reset_index()


def a_diario(df30: pd.DataFrame) -> pd.DataFrame:
    """Promedio por día. El dato de las 00:00 es el último intervalo del día anterior,
    por eso restamos 30 minutos. Solo se quedan los días completos (48 intervalos)."""
    fecha = (df30["ts"] - pd.Timedelta(minutes=30)).dt.normalize().rename("fecha")
    agrupado = df30.groupby(fecha)
    diario = agrupado[["demanda", "pronostico_coes"]].mean()
    return diario[agrupado["demanda"].count() == 48]


def ingestar() -> pd.DataFrame:
    archivo = config.ruta("demanda_diaria.parquet")
    if archivo.exists():
        actual = pd.read_parquet(archivo)
        desde_anio = actual.index.max().year  # volvemos a bajar el último año (son segundos)
    else:
        actual, desde_anio = None, config.PRIMER_ANIO

    anios = range(desde_anio, config.hoy().year + 1)
    nuevo = a_diario(pd.concat(descargar_anio(anio) for anio in anios))
    if actual is not None:
        nuevo = pd.concat([actual[actual.index < nuevo.index.min()], nuevo])

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    nuevo.to_parquet(archivo)
    print(f"[ingest] {len(nuevo):,} días, de {nuevo.index.min():%Y-%m-%d} a {nuevo.index.max():%Y-%m-%d}")
    return nuevo


if __name__ == "__main__":
    ingestar()
