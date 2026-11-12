import simpy
import random

def ejecutar_simulacion(lamda, mu, c, num_vehiculos=1000, seed=42):
    """
    Simulación de eventos discretos para una intersección con c carriles (canales).
    :param lamda: Tasa de llegada de vehículos (vehículos por unidad de tiempo)
    :param mu: Tasa de servicio (vehículos atendidos por unidad de tiempo por canal)
    :param c: Número de canales (carriles de salida)
    :param num_vehiculos: Total de vehículos a simular
    :param seed: Semilla para reproducibilidad
    """
    random.seed(seed)
    env = simpy.Environment()
    servidor = simpy.Resource(env, capacity=c)
    
    tiempos_espera = []

    def vehiculo(env, name, servidor):
        llegada = env.now
        
        with servidor.request() as req:
            yield req
            espera = env.now - llegada
            tiempos_espera.append(espera)
            
            # Tiempo de servicio exponencial basado en mu
            tiempo_servicio = random.expovariate(mu)
            yield env.timeout(tiempo_servicio)

    def generador_vehiculos(env, servidor):
        i = 0
        while i < num_vehiculos:
            yield env.timeout(random.expovariate(lamda))
            i += 1
            env.process(vehiculo(env, f'Vehiculo_{i}', servidor))

    env.process(generador_vehiculos(env, servidor))
    env.run()

    wq_simulado = sum(tiempos_espera) / len(tiempos_espera) if tiempos_espera else 0
    
    return {
        "Wq_simulado": wq_simulado,
        "total_vehiculos_simulados": len(tiempos_espera)
    }