"""Diagrama de arquitectura con estilo AWS (layout a mano, íconos oficiales).

Genera docs/arquitectura.svg y docs/arquitectura.png. Los íconos salen del paquete `diagrams`.
Uso, desde la raíz del repo:
    uv run --with diagrams --with cairosvg python docs/arquitectura.py
"""
import base64
from pathlib import Path

import cairosvg
import diagrams

ICONOS = Path(diagrams.__file__).parent.parent / "resources"
SALIDA = Path("docs")
TAM = 64  # tamaño de los íconos (px)
FUENTE = "Helvetica, Arial, sans-serif"

elementos: list[str] = []


def icono(archivo: str, x: int, y: int, nombre: str, detalle: str = "") -> None:
    """Ícono centrado en (x, y) con su nombre debajo."""
    datos = base64.b64encode((ICONOS / archivo).read_bytes()).decode()
    elementos.append(f'<image x="{x - TAM / 2}" y="{y - TAM / 2}" width="{TAM}" height="{TAM}" '
                     f'href="data:image/png;base64,{datos}"/>')
    texto(x, y + TAM / 2 + 18, nombre, tam=13, color="#232F3E")
    if detalle:
        texto(x, y + TAM / 2 + 34, detalle, tam=11, color="#5F6B7A")


def texto(x, y, contenido, tam=13, color="#232F3E", peso="normal", ancla="middle") -> None:
    elementos.append(f'<text x="{x}" y="{y}" font-family="{FUENTE}" font-size="{tam}" fill="{color}" '
                     f'font-weight="{peso}" text-anchor="{ancla}">{contenido}</text>')


def flecha(*puntos, doble=False, punteada=False) -> None:
    """Flecha ortogonal que pasa por los puntos dados."""
    camino = " ".join(f"{x},{y}" for x, y in puntos)
    extra = ' marker-start="url(#punta-inicio)"' if doble else ""
    trazo = ' stroke-dasharray="6,4"' if punteada else ""
    elementos.append(f'<polyline points="{camino}" fill="none" stroke="#232F3E" stroke-width="1.6"'
                     f' marker-end="url(#punta)"{extra}{trazo}/>')


def paso(x, y, etiqueta, tipo="produccion") -> None:
    """Círculo numerado: negro para el flujo diario, blanco con borde para el despliegue."""
    relleno, letra = ("#232F3E", "white") if tipo == "produccion" else ("white", "#232F3E")
    elementos.append(f'<circle cx="{x}" cy="{y}" r="13" fill="{relleno}" stroke="#232F3E" stroke-width="1.6"/>')
    texto(x, y + 4.5, etiqueta, tam=13, color=letra, peso="bold")


def grupo(x, y, ancho, alto, titulo, color, punteado=False) -> None:
    trazo = ' stroke-dasharray="6,4"' if punteado else ""
    elementos.append(f'<rect x="{x}" y="{y}" width="{ancho}" height="{alto}" fill="none" '
                     f'stroke="{color}" stroke-width="1.6"{trazo}/>')
    elementos.append(f'<rect x="{x}" y="{y}" width="{len(titulo) * 7.6 + 24}" height="26" fill="{color}"/>')
    texto(x + 12, y + 18, titulo, tam=13, color="white", peso="bold", ancla="start")


def laptop(x, y, nombre, detalle) -> None:
    """Laptop dibujada en líneas, como el ícono de cliente de AWS."""
    elementos.append(f'<rect x="{x - 24}" y="{y - 22}" width="48" height="32" rx="2" fill="none" '
                     f'stroke="#232F3E" stroke-width="3"/>')
    elementos.append(f'<path d="M{x - 32},{y + 18} h64 l-6,-8 h-52 z" fill="none" stroke="#232F3E" '
                     f'stroke-width="3" stroke-linejoin="round"/>')
    texto(x, y + TAM / 2 + 18, nombre, tam=13)
    texto(x, y + TAM / 2 + 34, detalle, tam=11, color="#5F6B7A")


# ---------- Layout ----------
MEDIO = TAM / 2

# Desarrollo
grupo(30, 150, 370, 470, "Desarrollo", "#7D8998", punteado=True)
laptop(130, 340, "Científico de datos", "uv · notebook · pipeline/")
icono("onprem/mlops/mlflow.png", 130, 210, "MLflow", "experimentos (local)")
icono("onprem/ci/github-actions.png", 310, 340, "GitHub Actions", "CI: ruff + pytest")
icono("onprem/container/docker.png", 310, 530, "deploy.sh", "docker build + push")

flecha((130, 340 - 26), (130, 210 + MEDIO + 40), punteada=True)
flecha((130 + 34, 340), (310 - MEDIO - 4, 340))
paso(220, 340, "A", tipo="despliegue")
flecha((130, 340 + MEDIO + 42), (130, 530), (310 - MEDIO - 4, 530))
paso(130, 482, "B", tipo="despliegue")

# Fuente externa
icono("onprem/network/internet.png", 860, 62, "Portal del COES", "demanda cada 30 min")

# AWS
grupo(450, 150, 880, 470, "AWS Cloud · us-east-1", "#232F3E")
icono("aws/integration/eventbridge-scheduler.png", 570, 340, "Amazon EventBridge Scheduler",
      "6:00 am hora de Lima")
icono("aws/compute/lambda.png", 860, 340, "AWS Lambda", "job diario (imagen Docker)")
icono("aws/storage/simple-storage-service-s3.png", 1160, 340, "Amazon S3", "data/: demanda · modelo · predicciones")
icono("aws/compute/ec2-container-registry.png", 570, 530, "Amazon ECR", "imagen del pipeline")
icono("aws/management/cloudwatch-logs.png", 1160, 530, "Amazon CloudWatch Logs")

flecha((310 + MEDIO + 4, 530), (570 - MEDIO - 6, 530))  # deploy.sh -> ECR
flecha((570 + MEDIO + 6, 340), (860 - MEDIO - 6, 340))  # scheduler -> Lambda
paso(715, 340, "1")
flecha((1160 - MEDIO - 6, 326), (860 + MEDIO + 6, 326))  # S3 -> Lambda
paso(1010, 326, "2")
flecha((860, 62 + MEDIO + 44), (860, 340 - MEDIO - 6))  # COES -> Lambda
paso(860, 210, "3")
paso(904, 296, "4")
flecha((860 + MEDIO + 6, 354), (1160 - MEDIO - 6, 354))  # Lambda -> S3
paso(1010, 354, "5")
flecha((880, 340 + MEDIO + 42), (880, 530), (1160 - MEDIO - 6, 530))  # Lambda -> CloudWatch
paso(1010, 530, "6")
flecha((570 + MEDIO + 6, 530), (840, 530), (840, 340 + MEDIO + 42))  # ECR -> Lambda
paso(715, 530, "C", tipo="despliegue")

# Leyenda
diario = ["EventBridge Scheduler invoca la Lambda todos los días.",
          "La Lambda trae data/ desde S3: histórico, modelo y predicciones.",
          "Descarga del COES la demanda de ayer.",
          "Monitorea el error; si supera el umbral, reentrena. Predice hoy.",
          "Devuelve a S3 la data actualizada.",
          "Registra los logs de la ejecución en CloudWatch."]
despliegue = ["git push: GitHub Actions corre lint y tests en el contenedor.",
              "deploy.sh construye la imagen y la sube a ECR.",
              "La Lambda usa esa imagen (la misma probada en CI)."]
texto(30, 668, "Cada día (automático)", tam=14, peso="bold", ancla="start")
for i, linea in enumerate(diario):
    paso(44, 696 + i * 30, str(i + 1))
    texto(68, 701 + i * 30, linea, tam=13, ancla="start")
texto(720, 668, "Desarrollo y despliegue", tam=14, peso="bold", ancla="start")
for i, linea in enumerate(despliegue):
    paso(734, 696 + i * 30, "ABC"[i], tipo="despliegue")
    texto(758, 701 + i * 30, linea, tam=13, ancla="start")

ANCHO, ALTO = 1360, 880
svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{ANCHO}" height="{ALTO}" viewBox="0 0 {ANCHO} {ALTO}">
<defs>
  <marker id="punta" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
    <path d="M0,0 L10,5 L0,10 z" fill="#232F3E"/></marker>
  <marker id="punta-inicio" viewBox="0 0 10 10" refX="1" refY="5" markerWidth="7" markerHeight="7" orient="auto">
    <path d="M10,0 L0,5 L10,10 z" fill="#232F3E"/></marker>
</defs>
<rect width="100%" height="100%" fill="white"/>
{chr(10).join(elementos)}
</svg>"""

SALIDA.mkdir(exist_ok=True)
(SALIDA / "arquitectura.svg").write_text(svg)
cairosvg.svg2png(bytestring=svg.encode(), write_to=str(SALIDA / "arquitectura.png"), output_width=ANCHO * 2)
print(f"Listo: {SALIDA}/arquitectura.svg y {SALIDA}/arquitectura.png")
