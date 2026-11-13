from pathlib import Path
import sys

from fastapi import FastAPI, HTTPException

# Agrega la raíz del repositorio a la ruta de importación.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.schemas import (
    ESCENARIOS_SALTA,
    TrafficRequest,
    WebsterRequest,
)
from models.queue_model import calcular_mmc, calcular_webster
from models.simulation import ejecutar_simulacion


app = FastAPI(
    title="API Optimización de Semáforos - Salta",
    description=(
        "API ilustrativa para medidas M/M/c, simulación y cálculo "
        "analítico del ciclo de Webster."
    ),
    version="1.1.0",
)


@app.get("/")
def read_root():
    return {
        "message": "API de análisis de tráfico de Salta",
        "nota": "Los escenarios disponibles son ilustrativos.",
    }


@app.get("/scenarios")
def obtener_escenarios():
    """Devuelve escenarios ilustrativos preconfigurados."""
    return {
        "status": "success",
        "ciudad": "Salta, Argentina",
        "tipo_datos": "ilustrativos",
        "escenarios": ESCENARIOS_SALTA,
    }


@app.post("/optimize")
def optimize_traffic(data: TrafficRequest):
    """Calcula medidas M/M/c y ejecuta la simulación existente."""
    try:
        analitico = calcular_mmc(
            lamda=data.lamda,
            mu=data.mu,
            c=data.c,
        )

        simulado = ejecutar_simulacion(
            lamda=data.lamda,
            mu=data.mu,
            c=data.c,
            num_vehiculos=data.num_vehiculos,
        )

        return {
            "status": "success",
            "parametros_entrada": {
                "lamda": data.lamda,
                "mu": data.mu,
                "c": data.c,
                "num_vehiculos": data.num_vehiculos,
            },
            "resultados_analiticos": analitico,
            "resultados_simulacion": simulado,
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/webster")
def optimizar_webster(data: WebsterRequest):
    """Calcula el ciclo clásico de Webster y los verdes efectivos por fase."""
    try:
        # Compatibilidad con Pydantic 1 y Pydantic 2.
        fases = [
            fase.model_dump() if hasattr(fase, "model_dump") else fase.dict()
            for fase in data.fases
        ]

        resultado = calcular_webster(
            fases=fases,
            flujo_saturacion_veh_h_por_carril=(
                data.flujo_saturacion_veh_h_por_carril
            ),
            tiempo_perdido_total_s=data.tiempo_perdido_total_s,
        )

        return {
            "status": "success",
            "resultado": resultado,
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
