"""Configuración del proyecto, en un solo lugar."""
import os
from datetime import UTC, date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# Carpeta donde viven los datos, el modelo y las predicciones
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))

# Registro de experimentos (MLflow). Vacío = no registrar (por ejemplo, en la Lambda)
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")

# Datos: desde qué año descargar la primera vez
PRIMER_ANIO = 2016

# Modelo: la demanda de los últimos N días predice la de mañana
N_LAGS = 14
ANIOS_ENTRENAMIENTO = 3
DIAS_VALIDACION = 28
PARAMS_XGB = {"n_estimators": 400, "max_depth": 4, "learning_rate": 0.05}

# Monitoreo: si el error de los últimos días supera el umbral, se reentrena
VENTANA_MONITOREO = 7  # días
UMBRAL_MAPE = 5.0  # %


def ruta(nombre: str) -> Path:
    return DATA_DIR / nombre


def hoy(ahora: datetime | None = None) -> date:
    """La fecha de hoy en Perú. Ojo: los servidores en la nube corren en UTC, donde después
    de las 7 pm de Lima ya es "mañana"."""
    ahora = ahora or datetime.now(UTC)
    return ahora.astimezone(ZoneInfo("America/Lima")).date()
