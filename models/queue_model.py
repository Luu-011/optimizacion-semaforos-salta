import math
from collections.abc import Mapping, Sequence
from typing import Any


def _positivo(nombre: str, valor: float) -> float:
    """Convierte a float y valida que el parámetro sea finito y positivo."""
    try:
        numero = float(valor)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{nombre} debe ser un número positivo.") from exc
    if not math.isfinite(numero) or numero <= 0:
        raise ValueError(f"{nombre} debe ser un número finito mayor que cero.")
    return numero


def _cantidad_entera_positiva(nombre: str, valor: int) -> int:
    """Valida parámetros que representan cantidades enteras, como servidores o carriles."""
    try:
        numero = float(valor)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{nombre} debe ser un entero positivo.") from exc
    if not math.isfinite(numero) or not numero.is_integer() or numero <= 0:
        raise ValueError(f"{nombre} debe ser un entero positivo.")
    return int(numero)


def calcular_mu_efectiva(
    flujo_saturacion_veh_min_por_carril,
    verde_efectivo_s,
    ciclo_s,
):
    """Calcula μ efectiva = s * (g/C), en veh/min por carril.

    El flujo de saturación s debe ingresarse en veh/min/carril. El verde efectivo
    g y el ciclo C se ingresan en segundos, por lo que su cociente no tiene unidades.
    """
    s = _positivo(
        "flujo_saturacion_veh_min_por_carril",
        flujo_saturacion_veh_min_por_carril,
    )
    verde = _positivo("verde_efectivo_s", verde_efectivo_s)
    ciclo = _positivo("ciclo_s", ciclo_s)
    if verde >= ciclo:
        raise ValueError("El verde efectivo debe ser menor que la duración del ciclo.")
    return s * (verde / ciclo)


def calcular_mmc(lamda, mu, c):
    """Calcula medidas de desempeño para un modelo de colas M/M/c.

    Args:
        lamda: tasa total de llegada, en vehículos por unidad de tiempo.
        mu: tasa de servicio de cada servidor, en vehículos por la misma unidad.
        c: cantidad entera de servidores/canales paralelos.

    Returns:
        Diccionario con rho, P0, P_espera, Lq, Wq, Ws y Ls.

    Raises:
        ValueError: si los parámetros no son válidos o el sistema es inestable.
    """
    lamda = _positivo("lamda", lamda)
    mu = _positivo("mu", mu)
    c = _cantidad_entera_positiva("c", c)

    rho = lamda / (c * mu)
    if rho >= 1:
        raise ValueError(
            "El sistema es inestable: la tasa de utilización (rho) debe ser menor que 1."
        )

    carga_ofrecida = lamda / mu

    # Probabilidad de que el sistema esté vacío (P0).
    suma = sum(
        (carga_ofrecida**n) / math.factorial(n)
        for n in range(c)
    )
    termino_c = (
        (carga_ofrecida**c)
        / math.factorial(c)
        * (1 / (1 - rho))
    )
    p0 = 1 / (suma + termino_c)

    # Probabilidad de que una llegada deba esperar: fórmula Erlang C.
    p_espera = termino_c * p0

    # Medidas de desempeño en régimen estacionario.
    lq = (
        p0
        * (carga_ofrecida**c)
        * rho
        / (math.factorial(c) * (1 - rho) ** 2)
    )
    wq = lq / lamda
    ws = wq + 1 / mu
    ls = lamda * ws

    return {
        "rho": rho,
        "p0": p0,
        "P_espera": p_espera,
        "Lq": lq,
        "Wq": wq,
        "Ws": ws,
        "Ls": ls,
    }


def calcular_relacion_flujo(demanda_veh_h, carriles, flujo_saturacion_veh_h_por_carril):
    """Calcula y_i = q_i / (c_i * s) para una fase semafórica.

    Args:
        demanda_veh_h: flujo total de la fase, en vehículos por hora.
        carriles: número de carriles de descarga de la fase.
        flujo_saturacion_veh_h_por_carril: flujo de saturación por carril,
            en vehículos por hora y por carril.
    """
    q = _positivo("demanda_veh_h", demanda_veh_h)
    c_i = _cantidad_entera_positiva("carriles", carriles)
    s = _positivo(
        "flujo_saturacion_veh_h_por_carril",
        flujo_saturacion_veh_h_por_carril,
    )
    return q / (c_i * s)


def calcular_demora_webster(
    demanda_veh_h,
    carriles,
    flujo_saturacion_veh_h_por_carril,
    ciclo_s,
    verde_efectivo_s,
):
    """Calcula la demora Webster de una fase, sin el término correctivo empírico.

    La demanda se convierte de veh/h a veh/s para que la demora resultante quede
    expresada en segundos. El grado de saturación es x = y/u, donde u = g/C.
    """
    q_h = _positivo("demanda_veh_h", demanda_veh_h)
    ciclo = _positivo("ciclo_s", ciclo_s)
    verde = _positivo("verde_efectivo_s", verde_efectivo_s)
    y_i = calcular_relacion_flujo(
        q_h,
        carriles,
        flujo_saturacion_veh_h_por_carril,
    )

    if verde >= ciclo:
        raise ValueError("El verde efectivo debe ser menor que la duración del ciclo.")

    u_i = verde / ciclo
    x_i = y_i / u_i
    if x_i >= 1:
        raise ValueError(
            f"La fase no es estable con este reparto de verde (x={x_i:.4f} >= 1)."
        )

    q_segundo = q_h / 3600
    denominador_uniforme = 2 * (1 - u_i * x_i)
    if denominador_uniforme <= 0:
        raise ValueError("Los parámetros producen una demora uniforme no definida.")

    demora_uniforme_s = ciclo * (1 - u_i) ** 2 / denominador_uniforme
    demora_aleatoria_s = x_i**2 / (2 * q_segundo * (1 - x_i))
    demora_total_s = demora_uniforme_s + demora_aleatoria_s

    return {
        "y_i": y_i,
        "u_i": u_i,
        "x_i": x_i,
        "demora_uniforme_s": demora_uniforme_s,
        "demora_aleatoria_s": demora_aleatoria_s,
        "demora_total_s": demora_total_s,
    }


def calcular_webster(
    fases: Sequence[Mapping[str, Any]],
    flujo_saturacion_veh_h_por_carril=1440.0,
    tiempo_perdido_total_s=8.0,
):
    """Calcula el ciclo de Webster, los verdes efectivos y las demoras por fase.

    Cada elemento de `fases` debe incluir:
        - nombre: etiqueta de la fase (opcional).
        - demanda_veh_h: flujo total de la fase en vehículos por hora.
        - carriles: cantidad de carriles de descarga de esa fase.

    El flujo de saturación y el tiempo perdido deben ser supuestos o mediciones
    documentados por quien use el modelo. Esta función calcula el Webster clásico
    y no aplica límites operativos de ciclo; esos límites deben tratarse al comparar
    las alternativas de diseño.
    """
    if not isinstance(fases, Sequence) or isinstance(fases, (str, bytes)) or len(fases) < 2:
        raise ValueError("Se requieren al menos dos fases para analizar una intersección.")

    s = _positivo(
        "flujo_saturacion_veh_h_por_carril",
        flujo_saturacion_veh_h_por_carril,
    )
    tiempo_perdido = _positivo("tiempo_perdido_total_s", tiempo_perdido_total_s)

    fases_validadas = []
    nombres = set()
    for indice, fase in enumerate(fases, start=1):
        if not isinstance(fase, Mapping):
            raise ValueError(f"La fase {indice} debe ser un diccionario de parámetros.")
        if "demanda_veh_h" not in fase or "carriles" not in fase:
            raise ValueError(
                f"La fase {indice} debe incluir 'demanda_veh_h' y 'carriles'."
            )

        nombre = str(fase.get("nombre") or f"Fase {indice}").strip()
        if not nombre:
            nombre = f"Fase {indice}"
        if nombre in nombres:
            raise ValueError(f"El nombre de fase '{nombre}' está repetido.")
        nombres.add(nombre)

        q = _positivo(f"demanda_veh_h de {nombre}", fase["demanda_veh_h"])
        carriles = _cantidad_entera_positiva(
            f"carriles de {nombre}", fase["carriles"]
        )
        y_i = q / (carriles * s)
        fases_validadas.append(
            {
                "nombre": nombre,
                "demanda_veh_h": q,
                "carriles": carriles,
                "y_i": y_i,
            }
        )

    suma_y = sum(fase["y_i"] for fase in fases_validadas)
    if suma_y >= 1:
        raise ValueError(
            f"La intersección está sobresaturada (Y={suma_y:.4f} >= 1); "
            "el método de Webster no puede proponer un ciclo finito factible."
        )

    ciclo_webster_s = (1.5 * tiempo_perdido + 5) / (1 - suma_y)
    verde_disponible_s = ciclo_webster_s - tiempo_perdido
    if ciclo_webster_s <= tiempo_perdido or verde_disponible_s <= 0:
        raise ValueError("El ciclo calculado no deja tiempo efectivo para repartir entre fases.")

    resultados_fases = []
    for fase in fases_validadas:
        verde_i_s = verde_disponible_s * fase["y_i"] / suma_y
        demora = calcular_demora_webster(
            demanda_veh_h=fase["demanda_veh_h"],
            carriles=fase["carriles"],
            flujo_saturacion_veh_h_por_carril=s,
            ciclo_s=ciclo_webster_s,
            verde_efectivo_s=verde_i_s,
        )
        resultados_fases.append(
            {
                **fase,
                "verde_efectivo_s": verde_i_s,
                "demora_s": demora["demora_total_s"],
                "grado_saturacion": demora["x_i"],
                "proporcion_verde": demora["u_i"],
                "demora_uniforme_s": demora["demora_uniforme_s"],
                "demora_aleatoria_s": demora["demora_aleatoria_s"],
            }
        )

    demanda_total = sum(fase["demanda_veh_h"] for fase in resultados_fases)
    demora_ponderada_s = sum(
        fase["demanda_veh_h"] * fase["demora_s"]
        for fase in resultados_fases
    ) / demanda_total

    return {
        "Y": suma_y,
        "flujo_saturacion_veh_h_por_carril": s,
        "tiempo_perdido_total_s": tiempo_perdido,
        "ciclo_webster_s": ciclo_webster_s,
        "verde_disponible_s": verde_disponible_s,
        "demora_media_ponderada_s": demora_ponderada_s,
        "fases": resultados_fases,
    }
