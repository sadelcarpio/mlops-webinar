"""Registro de experimentos con MLflow.

Cada entrenamiento queda guardado con sus parámetros y métricas, para comparar corridas en la
interfaz de MLflow. El modelo que usa el sistema NO se lee de aquí: vive en data/modelo/."""
import os

os.environ.setdefault("MLFLOW_LOGGING_LEVEL", "ERROR")  # MLflow es muy conversador
import mlflow

from pipeline import config


def registrar_en_mlflow(metadata: dict) -> str:
    mlflow.set_tracking_uri(config.MLFLOW_TRACKING_URI)
    mlflow.set_experiment("demanda-sein")
    with mlflow.start_run(run_name=f"hasta-{metadata['entrenado_hasta']}") as run:
        mlflow.log_params({**config.PARAMS_XGB, "n_lags": config.N_LAGS,
                           "anios_entrenamiento": config.ANIOS_ENTRENAMIENTO,
                           "entrenado_hasta": metadata["entrenado_hasta"]})
        mlflow.log_metrics({k: v for k, v in metadata.items() if k.startswith("mape")})
    return run.info.run_id
