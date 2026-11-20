"""Paso 4 - Monitoreo: ¿qué tan bien predijimos los últimos días?

Aquí el valor real llega al día siguiente, así que podemos medir directamente el ERROR del modelo
(en otros problemas, como riesgo crediticio, la respuesta tarda meses y se vigila el drift de los datos).
"""
import pandas as pd

from pipeline import config
from pipeline.train import cargar_modelo, mape


def monitorear(hoy: pd.Timestamp) -> dict:
    diario = pd.read_parquet(config.ruta("demanda_diaria.parquet"))
    _, metadata = cargar_modelo()
    archivo_predicciones = config.ruta("predicciones.parquet")
    predicciones = pd.read_parquet(archivo_predicciones) if archivo_predicciones.exists() else None

    resultado = {"modelo": metadata["entrenado_hasta"], "dias_evaluados": 0,
                 "mape": None, "mape_coes": None, "alerta": False}
    if predicciones is not None:
        # Días que ya pasaron, predichos por el modelo actual: comparamos con la realidad
        df = predicciones.join(diario, how="inner")
        df = df[(df.index < hoy) & (df["modelo"] == metadata["entrenado_hasta"])]
        df = df.tail(config.VENTANA_MONITOREO)
        if len(df) > 0:
            resultado["dias_evaluados"] = len(df)
            resultado["mape"] = mape(df["demanda"], df["prediccion"])
            resultado["mape_coes"] = mape(df["demanda"], df["pronostico_coes"])
        # Solo damos alerta con una semana completa de evidencia (un feriado aislado no cuenta)
        resultado["alerta"] = (len(df) == config.VENTANA_MONITOREO
                               and resultado["mape"] > config.UMBRAL_MAPE)

    guardar_monitoreo(hoy, resultado)
    if resultado["mape"] is not None:
        estado = "ALERTA: reentrenar" if resultado["alerta"] else "ok"
        print(f"[monitor] {hoy:%Y-%m-%d} MAPE últimos {resultado['dias_evaluados']} días: "
              f"{resultado['mape']:.2f}% (umbral {config.UMBRAL_MAPE}%) -> {estado}")
    return resultado


def guardar_monitoreo(hoy: pd.Timestamp, resultado: dict) -> None:
    archivo = config.ruta("monitoreo.parquet")
    nuevo = pd.DataFrame([resultado], index=pd.DatetimeIndex([hoy], name="fecha"))
    if archivo.exists():
        anterior = pd.read_parquet(archivo)
        nuevo = pd.concat([anterior.drop(hoy, errors="ignore"), nuevo]).sort_index()
    nuevo.to_parquet(archivo)
