"""Configuración del proyecto, en un solo lugar."""
from pathlib import Path

# Carpeta donde viven los datos, el modelo y las predicciones
DATA_DIR = Path("data")

# Registro de experimentos (MLflow)
MLFLOW_TRACKING_URI = "sqlite:///mlflow.db"

# Modelo: la demanda de los últimos N días predice la de mañana
N_LAGS = 14
ANIOS_ENTRENAMIENTO = 3
DIAS_VALIDACION = 28
PARAMS_XGB = {"n_estimators": 400, "max_depth": 4, "learning_rate": 0.05}


def ruta(nombre: str) -> Path:
    return DATA_DIR / nombre
