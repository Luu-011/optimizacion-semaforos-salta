from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class TrafficRequest(BaseModel):
    lamda: float = Field(..., gt=0, description="Tasa de llegada de vehículos (veh/min)")
    mu: float = Field(..., gt=0, description="Tasa de servicio por carril (veh/min)")
    c: int = Field(..., gt=0, description="Número de carriles o canales de salida")
    num_vehiculos: int = Field(1000, gt=0, description="Cantidad de vehículos para la simulación")

class ScenarioConfig(BaseModel):
    nombre: str
    ubicacion: str
    descripcion: str
    parametros: TrafficRequest

# Escenarios reales preconfigurados para las arterias críticas de Salta
ESCENARIOS_SALTA = [
    {
        "nombre": "Hora Pico Matutina",
        "ubicacion": "Av. Paraguay e Intersección Circunvalación",
        "descripcion": "Alto flujo vehicular de ingreso a la ciudad por la mañana.",
        "parametros": {"lamda": 15.0, "mu": 6.0, "c": 3, "num_vehiculos": 1000}
    },
    {
        "nombre": "Hora Pico Vespertina",
        "ubicacion": "Av. Bicentenario y Croquis",
        "descripcion": "Congestión por salida de actividad escolar y administrativa.",
        "parametros": {"lamda": 12.0, "mu": 5.5, "c": 2, "num_vehiculos": 1000}
    },
    {
        "nombre": "Hora Valle",
        "ubicacion": "Av. Entre Ríos",
        "descripcion": "Flujo moderado y estable sin restricciones severas de cola.",
        "parametros": {"lamda": 6.0, "mu": 6.0, "c": 2, "num_vehiculos": 1000}
    }
]