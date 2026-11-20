"""Diagrama de arquitectura del proyecto (diagram as code).

Usa la librería `diagrams` (íconos oficiales de AWS) y necesita Graphviz instalado.
Uso, desde la raíz del repo:
    uv run --with diagrams python docs/arquitectura.py   # -> docs/arquitectura.png
"""
from diagrams import Cluster, Diagram, Edge
from diagrams.aws.compute import ECR, Lambda
from diagrams.aws.integration import EventbridgeScheduler
from diagrams.aws.management import CloudwatchLogs
from diagrams.aws.storage import S3
from diagrams.onprem.ci import GithubActions
from diagrams.onprem.client import User
from diagrams.onprem.container import Docker
from diagrams.onprem.mlops import Mlflow
from diagrams.onprem.network import Internet
from diagrams.onprem.vcs import Github
from diagrams.programming.language import Python

grafo = {"fontsize": "22", "fontname": "Helvetica", "pad": "0.6", "nodesep": "0.9", "ranksep": "1.1", "splines": "spline"}
nodo = {"fontsize": "13", "fontname": "Helvetica"}
cluster = {"fontsize": "15", "fontname": "Helvetica Bold", "margin": "22"}

with Diagram("Pronóstico de demanda eléctrica del SEIN — arquitectura", filename="docs/arquitectura",
             outformat="png", show=False, direction="LR", graph_attr=grafo, node_attr=nodo):

    with Cluster("Desarrollo (tu laptop)", graph_attr={**cluster, "bgcolor": "#F4F6F8"}):
        cientifico = User("Científico\nde datos")
        codigo = Python("pipeline/\nnotebook")
        mlflow = Mlflow("MLflow\n(experimentos)")
        docker = Docker("docker build\n(deploy.sh)")

    with Cluster("GitHub", graph_attr={**cluster, "bgcolor": "#F4F6F8"}):
        repo = Github("Repositorio\n(tags v0…v4)")
        ci = GithubActions("CI: ruff + pytest\ndentro del contenedor")

    with Cluster("Fuente de datos", graph_attr={**cluster, "bgcolor": "#F1F8E9"}):
        coes = Internet("Portal del COES\n(demanda cada 30 min)")

    with Cluster("AWS (us-east-1)", graph_attr={**cluster, "bgcolor": "#FFF8EE", "pencolor": "#FF9900"}):
        ecr = ECR("ECR\nimagen Docker")
        scheduler = EventbridgeScheduler("EventBridge Scheduler\n6:00 am hora de Lima")
        lam = Lambda("Lambda\n(job diario)")
        s3 = S3("S3: data/\ndemanda · modelo\npredicciones · monitoreo")
        logs = CloudwatchLogs("CloudWatch Logs")

    # Desarrollo
    cientifico >> codigo
    codigo >> Edge(style="dashed", label="métricas") >> mlflow
    codigo >> Edge(label="git push") >> repo >> Edge(label="cada push") >> ci
    codigo >> docker >> Edge(label="push") >> ecr

    # Producción
    ecr >> Edge(label="imagen") >> lam
    scheduler >> Edge(label="invoca: ingesta → monitoreo\n→ reentreno si hay alerta → predicción",
                     color="#FF9900", penwidth="2") >> lam
    coes >> Edge(label="datos de ayer", color="#2E7D32") >> lam
    lam - Edge(label="trae / devuelve data/", color="#1565C0", penwidth="2", forward=True, reverse=True) - s3
    lam >> Edge(style="dashed") >> logs
