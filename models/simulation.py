import math
import random

import simpy
from scipy import stats


def _validar_numero_positivo(nombre, valor):
    try:
        numero = float(valor)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{nombre} debe ser un número positivo.") from exc
    if not math.isfinite(numero) or numero <= 0:
        raise ValueError(f"{nombre} debe ser un número finito mayor que cero.")
    return numero


def _validar_entero(nombre, valor, minimo=0):
    try:
        numero = float(valor)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{nombre} debe ser un número entero.") from exc
    if not math.isfinite(numero) or not numero.is_integer() or numero < minimo:
        raise ValueError(f"{nombre} debe ser un entero mayor o igual a {minimo}.")
    return int(numero)


def _simular_replica(lamda, mu, c, num_vehiculos, warmup, seed):
    """Ejecuta una réplica y devuelve las esperas posteriores al calentamiento."""
    rng = random.Random(seed)
    env = simpy.Environment()
    servidores = simpy.Resource(env, capacity=c)
    tiempos_espera = []

    def vehiculo(indice):
        llegada = env.now
        with servidores.request() as solicitud:
            yield solicitud
            espera = env.now - llegada

            # Se simulan todos los vehículos, pero se miden solo los posteriores
            # a los primeros `warmup` vehículos.
            if indice > warmup:
                tiempos_espera.append(espera)

            tiempo_servicio = rng.expovariate(mu)
            yield env.timeout(tiempo_servicio)

    def generador_vehiculos():
        for indice in range(1, num_vehiculos + 1):
            tiempo_entre_llegadas = rng.expovariate(lamda)
            yield env.timeout(tiempo_entre_llegadas)
            env.process(vehiculo(indice))

    env.process(generador_vehiculos())
    env.run()

    if not tiempos_espera:
        raise ValueError(
            "La réplica no produjo vehículos medidos; revisá num_vehiculos y warmup."
        )

    return {
        "seed": seed,
        "Wq_min": sum(tiempos_espera) / len(tiempos_espera),
        "vehiculos_medidos": len(tiempos_espera),
    }


def ejecutar_simulacion(
    lamda,
    mu,
    c,
    num_vehiculos=1000,
    seed=42,
    warmup=0,
    replicas=1,
    seed_base=None,
):
    """Simula un sistema M/M/c, con calentamiento opcional y varias réplicas.

    Todas las tasas deben usar la misma unidad de tiempo. Por ejemplo, si lamda
    y mu están en vehículos/minuto, los tiempos de espera devueltos están en
    minutos; también se incluye su conversión a segundos.

    Args:
        lamda: tasa total de llegada (vehículos por unidad de tiempo).
        mu: tasa de servicio por servidor (vehículos por la misma unidad).
        c: cantidad de servidores/canales paralelos.
        num_vehiculos: total de llegadas simuladas en cada réplica, incluidos
            los vehículos de calentamiento.
        seed: semilla antigua, mantenida para compatibilidad con llamadas previas.
        warmup: cantidad inicial de vehículos descartados de las métricas.
        replicas: número de corridas independientes.
        seed_base: semilla base; la réplica i utiliza seed_base + i.

    Returns:
        Diccionario compatible con la versión anterior (incluye Wq_simulado y
        total_vehiculos_simulados) y con medias, IC del 95 % t de Student,
        utilización teórica y resultados por réplica.

    Nota:
        Esta es una cola M/M/c abstracta. No simula explícitamente la secuencia
        de luces rojas y verdes del semáforo.
    """
    lamda = _validar_numero_positivo("lamda", lamda)
    mu = _validar_numero_positivo("mu", mu)
    c = _validar_entero("c", c, minimo=1)
    num_vehiculos = _validar_entero("num_vehiculos", num_vehiculos, minimo=1)
    warmup = _validar_entero("warmup", warmup, minimo=0)
    replicas = _validar_entero("replicas", replicas, minimo=1)

    if warmup >= num_vehiculos:
        raise ValueError(
            "warmup debe ser menor que num_vehiculos para que queden vehículos medidos."
        )

    rho = lamda / (c * mu)
    if rho >= 1:
        raise ValueError(
            f"El sistema es inestable (rho={rho:.4f} >= 1); "
            "la simulación de régimen estacionario requiere rho < 1."
        )

    if seed_base is None:
        seed_base = seed
    seed_base = _validar_entero("seed_base", seed_base, minimo=0)

    resultados_replicas = [
        _simular_replica(
            lamda=lamda,
            mu=mu,
            c=c,
            num_vehiculos=num_vehiculos,
            warmup=warmup,
            seed=seed_base + indice,
        )
        for indice in range(replicas)
    ]

    medias = [resultado["Wq_min"] for resultado in resultados_replicas]
    media_wq_min = sum(medias) / len(medias)

    if replicas >= 2:
        desviacion_estandar = float(stats.tstd(medias))
        error_estandar = desviacion_estandar / math.sqrt(replicas)
        t_critico = float(stats.t.ppf(0.975, df=replicas - 1))
        margen = t_critico * error_estandar
        ic95_inferior_min = float(media_wq_min - margen)
        ic95_superior_min = float(media_wq_min + margen)
    else:
        ic95_inferior_min = None
        ic95_superior_min = None

    factor_segundos = 60.0

    return {
        # Claves conservadas para no romper el backend ni notebooks existentes.
        "Wq_simulado": media_wq_min,
        "total_vehiculos_simulados": num_vehiculos * replicas,
        # Resultados explícitos de las réplicas y del intervalo de confianza.
        "rho": rho,
        "media_Wq_min": media_wq_min,
        "media_Wq_segundos": media_wq_min * factor_segundos,
        "IC95_Wq_min": {
            "inferior": ic95_inferior_min,
            "superior": ic95_superior_min,
        },
        "IC95_Wq_segundos": {
            "inferior": (
                None if ic95_inferior_min is None
                else ic95_inferior_min * factor_segundos
            ),
            "superior": (
                None if ic95_superior_min is None
                else ic95_superior_min * factor_segundos
            ),
        },
        "num_vehiculos_por_replica": num_vehiculos,
        "vehiculos_descartados_por_replica": warmup,
        "vehiculos_medidos_por_replica": num_vehiculos - warmup,
        "total_vehiculos_medidos": (num_vehiculos - warmup) * replicas,
        "replicas": replicas,
        "seed_base": seed_base,
        "resultados_replicas": resultados_replicas,
    }
