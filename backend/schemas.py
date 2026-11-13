from typing import List
from pydantic import BaseModel, Field

class TrafficRequest(BaseModel):
    lamda: float = Field(
        ...,
        gt=0,
        description="Tasa de llegada de vehículos (veh/min)",
    )
    mu: float = Field(
        ...,
        gt=0,
        description="Tasa de servicio por carril (veh/min)",
    )
    c: int = Field(
        ...,
        gt=0,
        description="Cantidad de carriles o servidores",
    )
    num_vehiculos: int = Field(
        1000,
        gt=0,
        description="Cantidad de vehículos para la simulación",
    )

    warmup: int = Field(0,
        ge=0,
        description="Cantidad inicial de vehículos descartados en cada réplica",
    )
    replicas: int = Field(
        1,
        ge=1,
        description="Cantidad de réplicas independientes",
    )
    seed_base: int = Field(
        42,
        ge=0,
        description="Semilla base para reproducir las réplicas",
    )



class FaseWebster(BaseModel):
    nombre: str = Field(
        ...,
        min_length=1,
        description="Nombre o movimiento que representa la fase",
    )
    demanda_veh_h: float = Field(
        ...,
        gt=0,
        description="Demanda de la fase (veh/h)",
    )
    carriles: int = Field(
        ...,
        gt=0,
        description="Carriles de descarga de la fase",
    )


class WebsterRequest(BaseModel):
    fases: List[FaseWebster] = Field(
        ...,
        description="Fases de la intersección; se requieren al menos dos",
    )
    flujo_saturacion_veh_h_por_carril: float = Field(
        1440.0,
        gt=0,
        description="Flujo de saturación (veh/h por carril)",
    )
    tiempo_perdido_total_s: float = Field(
        8.0,
        gt=0,
        description="Tiempo perdido total por ciclo (s)",
    )


class ScenarioConfig(BaseModel):
    nombre: str
    ubicacion: str
    descripcion: str
    parametros: TrafficRequest


# Son escenarios ilustrativos construidos para probar el modelo.
# No son mediciones ni ubicaciones relevadas en campo.
ESCENARIOS_SALTA = [
    {
        "nombre": "Hora Pico Matutina",
        "ubicacion": "Corredor Av. Paraguay (escenario ilustrativo)",
        "descripcion": "Ejemplo de flujo de ingreso en hora pico.",
        "parametros": {
            "lamda": 15.0,
            "mu": 6.0,
            "c": 3,
            "num_vehiculos": 1000,
        },
    },
    {
        "nombre": "Hora Pico Vespertina",
        "ubicacion": "Corredor Av. Bicentenario (escenario ilustrativo)",
        "descripcion": (
            "Ejemplo sobresaturado para probar el mensaje de inestabilidad; "
            "no usar como recomendación operativa."
        ),
        "parametros": {
            "lamda": 12.0,
            "mu": 5.5,
            "c": 2,
            "num_vehiculos": 1000,
        },
    },
    {
        "nombre": "Hora Valle",
        "ubicacion": "Corredor Av. Entre Ríos (escenario ilustrativo)",
        "descripcion": "Ejemplo de flujo moderado.",
        "parametros": {
            "lamda": 6.0,
            "mu": 6.0,
            "c": 2,
            "num_vehiculos": 1000,
        },
    },
]
