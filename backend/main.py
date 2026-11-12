from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os

# Agregamos la ruta raíz para importar los modelos correctamente
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.queue_model import calcular_mmc
from models.simulation import ejecutar_simulacion

app = FastAPI(
    title="API Optimización de Semáforos - Salta",
    description="Motor de cálculo de Teoría de Colas y Simulación para corredores viales",
    version="1.0.0"
)

class TrafficRequest(BaseModel):
    lamda: float  # Tasa de llegada (vehículos/minuto)
    mu: float     # Tasa de servicio por carril (vehículos/minuto)
    c: int        # Cantidad de carriles (canales)
    num_vehiculos: int = 1000

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de Optimización de Tráfico en Salta (IO2)"}

@app.post("/optimize")
def optimize_traffic(data: TrafficRequest):
    try:
        # 1. Cálculo Analítico (M/M/c)
        analitico = calcular_mmc(data.lamda, data.mu, data.c)
        
        # 2. Simulación de Eventos Discretos (SimPy)
        simulado = ejecutar_simulacion(data.lamda, data.mu, data.c, data.num_vehiculos)
        
        return {
            "status": "success",
            "parametros_entrada": {
                "lamda": data.lamda,
                "mu": data.mu,
                "c": data.c
            },
            "resultados_analiticos": analitico,
            "resultados_simulacion": simulado
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno en el servidor: {str(e)}")