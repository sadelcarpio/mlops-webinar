"""Punto de entrada para AWS Lambda.

La Lambda no tiene disco permanente, así que en cada ejecución:
    1. descarga la carpeta data/ desde S3 a /tmp/data
    2. corre el MISMO job diario que corres en tu laptop
    3. sube la carpeta actualizada de vuelta a S3
"""
import os
import shutil
from pathlib import Path

import boto3
import pandas as pd

from pipeline import config, job_diario

BUCKET = os.getenv("S3_BUCKET", "")
PREFIJO = "data/"
CARPETA_LOCAL = Path("/tmp/data")


def descargar_de_s3(s3) -> None:
    shutil.rmtree(CARPETA_LOCAL, ignore_errors=True)
    for pagina in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=PREFIJO):
        for objeto in pagina.get("Contents", []):
            destino = CARPETA_LOCAL / objeto["Key"].removeprefix(PREFIJO)
            destino.parent.mkdir(parents=True, exist_ok=True)
            s3.download_file(BUCKET, objeto["Key"], str(destino))


def subir_a_s3(s3) -> None:
    for archivo in CARPETA_LOCAL.rglob("*"):
        if archivo.is_file():
            s3.upload_file(str(archivo), BUCKET, PREFIJO + archivo.relative_to(CARPETA_LOCAL).as_posix())


def handler(event, context):
    s3 = boto3.client("s3")
    config.DATA_DIR = CARPETA_LOCAL
    descargar_de_s3(s3)
    prediccion = job_diario.correr(pd.Timestamp(config.hoy()))
    subir_a_s3(s3)
    return {"fecha": f"{config.hoy()}", "prediccion_mw": round(prediccion, 1)}
