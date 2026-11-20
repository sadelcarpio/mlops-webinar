# MLOps en la práctica: pronóstico de la demanda eléctrica del Perú

Proyecto del webinar: cómo pasar de un notebook a un modelo que vive en producción.
Usamos datos reales del [COES](https://www.coes.org.pe/Portal/portalinformacion/demanda):
la demanda eléctrica del SEIN, medida cada 30 minutos.

## El proyecto, paso a paso

Cada etapa es un tag de git. Para ver una etapa: `git checkout <tag>`.
Para ver qué cambió entre dos etapas: `git diff v0-notebook v1-modular`.

| Tag | Qué agrega |
|---|---|
| `v0-notebook` | El modelo en un notebook: exploración, features, entrenamiento, evaluación |
| `v1-modular` | Código separado en scripts + registro de experimentos con MLflow |
| `v2-tests-ci` | Tests automáticos que corren en un contenedor en cada push (GitHub Actions) |
| `v3-nuevos-datos` | Job diario en AWS: trae los datos nuevos y predice solo |
| `v4-monitoreo` | Monitoreo del error y reentrenamiento automático cuando el modelo falla |

## Cómo correrlo

Requisitos: Python 3.12 y [uv](https://docs.astral.sh/uv/).

```bash
uv sync

# El notebook original
uv run jupyter lab notebooks/01_modelo_demanda.ipynb

# El pipeline, paso a paso
uv run python -m pipeline.ingest --desde-anio 2016   # 1. descargar datos del COES
uv run python -m pipeline.train                      # 2. entrenar (y registrar en MLflow)
uv run python -m pipeline.predict                    # 3. predecir la demanda de hoy

# Ver los experimentos y el registro de modelos en http://localhost:5000
uv run mlflow ui --backend-store-uri sqlite:///mlflow.db
```

## El código

| Archivo | Qué hace |
|---|---|
| `pipeline/config.py` | Toda la configuración en un solo lugar |
| `pipeline/ingest.py` | Descarga la demanda cada 30 min del COES y la convierte en un valor por día |
| `pipeline/features.py` | Construye las features. **La misma función** se usa al entrenar y al predecir |
| `pipeline/train.py` | Entrena XGBoost con validación temporal y guarda el modelo |
| `pipeline/registro.py` | Registra parámetros y métricas de cada entrenamiento en MLflow, para comparar experimentos |
| `pipeline/predict.py` | Predice la demanda de un día y guarda la predicción |

## Tests y CI

```bash
uv run pytest                 # tests en tu máquina
uv run ruff check pipeline tests

# Lo mismo que corre GitHub Actions en cada push: tests DENTRO del contenedor
docker build --target tests -t demanda-tests .
docker run --rm demanda-tests
```

El `Dockerfile` tiene dos etapas: `produccion` (solo lo necesario para correr el pipeline) y
`tests` (la misma imagen + pytest + los tests). Así probamos exactamente lo que se despliega.

Los tests (`tests/`) usan datos sintéticos, no necesitan internet y verifican lo que más duele
si se rompe: que el dato de las 00:00 vaya al día correcto, que las features nunca usen el día que
se quiere predecir, y que entrenar y predecir funcionen de punta a punta.

**El modelo:** la demanda promedio de un día se predice con la de los 14 días anteriores
(`lag_1` ... `lag_14`) y el día de la semana. XGBoost no sabe nada de tiempo: convertimos la
serie en una tabla con `shift()`. Benchmark: el pronóstico oficial del COES.

## Datos

Los datos no se incluyen en el repositorio: el código los descarga directamente del COES.
Revisa los [términos y condiciones del COES](https://www.coes.org.pe/Portal/Organizacion/TerminosyCondiciones)
antes de cualquier uso comercial o redistribución.
