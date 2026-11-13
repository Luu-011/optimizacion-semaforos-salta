import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# Fijamos semilla para que los datos siempre sean los mismos (Reproducibilidad)
np.random.seed(42)

intersecciones = ["Av. Bicentenario", "Av. Paraguay", "Entre Ríos"]
registros = []

# Simulamos 1 día (desde las 06:00 hasta las 22:00) en intervalos de 15 minutos
fecha_base = datetime(2026, 5, 10, 6, 0)
intervalos = 16 * 4 # 16 horas * 4 registros por hora

for i in range(intervalos):
    hora_actual = fecha_base + timedelta(minutes=15 * i)
    hora = hora_actual.hour
    
    # Lógica de tránsito en Salta: Picos a las 8 AM y 18 PM
    if (7 <= hora <= 9) or (17 <= hora <= 19):
        periodo = "Pico"
        flujo_base = np.random.normal(1200, 150) # Mucha demanda
    else:
        periodo = "Valle"
        flujo_base = np.random.normal(400, 80)   # Poca demanda

    for interseccion in intersecciones:
        # Variación según la avenida (Bicentenario suele ser más caótica)
        factor_avenida = 1.2 if interseccion == "Av. Bicentenario" else 1.0
        
        demanda = max(50, int(flujo_base * factor_avenida))
        # Tiempo de servicio (ej: 2.5 segundos promedio por auto en verde)
        tiempo_servicio = round(abs(np.random.normal(2.5, 0.3)), 2)

        registros.append({
            "timestamp": hora_actual,
            "interseccion": interseccion,
            "periodo": periodo,
            "demanda_veh_h": demanda,
            "tiempo_servicio_s": tiempo_servicio
        })

# Crear DataFrame y guardar en data/raw
df = pd.DataFrame(registros)

# Asegurarnos de que la carpeta existe
os.makedirs("data/raw", exist_ok=True)
ruta_salida = "data/raw/aforos_salta_raw.csv"
df.to_csv(ruta_salida, index=False)

print(f"¡Dataset generado con éxito en: {ruta_salida}!")
print(f"Total de registros: {len(df)}")
print(df.head())