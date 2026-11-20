"""Simulación para el webinar: "viajamos en el tiempo" y corremos el job diario día por día.

Arrancamos con un modelo entrenado hasta noviembre de 2019 y vemos qué pasa cuando llega la
cuarentena (16 de marzo de 2020): el error se dispara, el monitoreo lo detecta y el sistema
se reentrena solo.

Uso (necesita los datos descargados: uv run python -m pipeline.ingest):
    uv run python -m pipeline.simular
"""
import argparse
import shutil
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from pipeline import config, job_diario
from pipeline.train import entrenar, mape

CUARENTENA = pd.Timestamp("2020-03-16")


def simular(desde: pd.Timestamp, hasta: pd.Timestamp) -> None:
    # La simulación trabaja en su propia carpeta y su propio registro de MLflow
    carpeta = Path("data/simulacion")
    shutil.rmtree(carpeta, ignore_errors=True)
    carpeta.mkdir(parents=True)
    shutil.copy(config.ruta("demanda_diaria.parquet"), carpeta)
    config.DATA_DIR = carpeta
    config.MLFLOW_TRACKING_URI = "sqlite:///mlflow_simulacion.db"

    entrenar(desde)
    for hoy in pd.date_range(desde, hasta):
        job_diario.correr(hoy, ingestar_datos=False)  # cada paso solo mira datos anteriores a "hoy"

    graficar(hasta)


def graficar(hasta: pd.Timestamp) -> None:
    diario = pd.read_parquet(config.ruta("demanda_diaria.parquet"))
    pred = pd.read_parquet(config.ruta(config.ARCHIVO_PREDICCIONES)).join(diario)
    monitoreo = pd.read_parquet(config.ruta("monitoreo.parquet")).dropna(subset=["mape"])
    reentrenos = monitoreo.index[monitoreo["alerta"]]

    fig, (arriba, abajo) = plt.subplots(2, 1, figsize=(13, 8), sharex=True, height_ratios=[3, 2])
    arriba.plot(pred.index, pred["demanda"], color="black", lw=2, label="Demanda real")
    arriba.plot(pred.index, pred["prediccion"], color="tab:blue", label="Nuestro modelo")
    arriba.plot(pred.index, pred["pronostico_coes"], color="gray", ls="--", lw=1, label="Pronóstico COES")
    arriba.set_ylabel("Demanda promedio diaria (MW)")
    arriba.set_title("Demanda eléctrica del SEIN: el modelo vs. la cuarentena de 2020", loc="left")
    arriba.legend(loc="lower left")

    abajo.plot(monitoreo.index, monitoreo["mape"], color="tab:red", label="Error del modelo (últimos 7 días)")
    abajo.axhline(config.UMBRAL_MAPE, color="tab:red", ls=":", label=f"Umbral ({config.UMBRAL_MAPE}%)")
    abajo.set_ylabel("MAPE (%)")

    for eje in (arriba, abajo):
        eje.axvline(CUARENTENA, color="tab:orange", lw=2)
        for fecha in reentrenos:
            eje.axvline(fecha, color="tab:green", ls="--", lw=1)
        eje.grid(alpha=0.3)
    abajo.plot([], [], color="tab:orange", lw=2, label="Inicio de la cuarentena")
    abajo.plot([], [], color="tab:green", ls="--", label="Reentrenamiento automático")
    abajo.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig("simulacion_2020.png", dpi=130)

    print("\nGráfico: simulacion_2020.png")
    print(f"Reentrenamientos automáticos: {[f'{f:%Y-%m-%d}' for f in reentrenos]}")
    periodos = {"Antes de la cuarentena": ("2020-01-01", "2020-03-15"),
                "Primeras 2 semanas": ("2020-03-16", "2020-03-31"),
                "Después": ("2020-04-01", f"{hasta:%Y-%m-%d}")}
    for nombre, (a, b) in periodos.items():
        p = pred.loc[a:b]
        print(f"  {nombre:<24} MAPE modelo {mape(p['demanda'], p['prediccion']):5.2f}%"
              f" | COES {mape(p['demanda'], p['pronostico_coes']):5.2f}%")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--desde", type=date.fromisoformat, default=date(2019, 11, 1))
    parser.add_argument("--hasta", type=date.fromisoformat, default=date(2020, 7, 31))
    args = parser.parse_args()
    simular(pd.Timestamp(args.desde), pd.Timestamp(args.hasta))
