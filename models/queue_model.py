import math

def calcular_mmc(lamda, mu, c):
    """
    Calcula las medidas de desempeño para un modelo de colas M/M/c.
    :param lamda: Tasa de llegada de vehículos (vehículos/unidad de tiempo)
    :param mu: Tasa de servicio de los semáforos/carril (vehículos/unidad de tiempo)
    :param c: Cantidad de canales (carriles o fases de salida)
    """
    rho = lamda / (c * mu)
    if rho >= 1:
        raise ValueError("El sistema es inestable: la tasa de utilización (rho) debe ser menor a 1.")
    
    # Cálculo de la probabilidad P0 (sistema vacío)
    suma = sum(((lamda / mu) ** n) / math.factorial(n) for n in range(c))
    termino_c = (((lamda / mu) ** c) / math.factorial(c)) * (1 / (1 - rho))
    p0 = 1 / (suma + termino_c)
    
    # Longitud de la cola (Lq)
    lq = (p0 * ((lamda / mu) ** c) * rho) / (math.factorial(c) * ((1 - rho) ** 2))
    
    # Tiempo de espera en la cola (Wq)
    wq = lq / lamda
    
    # Tiempo total en el sistema (Ws)
    ws = wq + (1 / mu)
    
    # Longitud total en el sistema (Ls)
    ls = lamda * ws
    
    return {
        "rho": rho,
        "p0": p0,
        "Lq": lq,
        "Wq": wq,
        "Ws": ws,
        "Ls": ls
    }