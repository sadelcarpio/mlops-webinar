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
uv run jupyter lab notebooks/01_modelo_demanda.ipynb
```

## Datos

Los datos no se incluyen en el repositorio: el código los descarga directamente del COES.
Revisa los [términos y condiciones del COES](https://www.coes.org.pe/Portal/Organizacion/TerminosyCondiciones)
antes de cualquier uso comercial o redistribución.
