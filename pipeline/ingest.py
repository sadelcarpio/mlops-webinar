"""Paso 1 - Ingesta: descarga la demanda del COES y la guarda como un valor por día.

Uso:
    uv run python -m pipeline.ingest --desde-anio 2016
"""
import argparse
from datetime import date

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


def ingestar(desde_anio: int) -> pd.DataFrame:
    anios = range(desde_anio, date.today().year + 1)
    diario = a_diario(pd.concat(descargar_anio(anio) for anio in anios))
    config.DATA_DIR.mkdir(exist_ok=True)
    diario.to_parquet(config.ruta("demanda_diaria.parquet"))
    print(f"[ingest] {len(diario):,} días, de {diario.index.min():%Y-%m-%d} a {diario.index.max():%Y-%m-%d}")
    return diario


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--desde-anio", type=int, default=2016)
    ingestar(parser.parse_args().desde_anio)
