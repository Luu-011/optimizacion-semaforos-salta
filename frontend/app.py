from pathlib import Path
import sys

import numpy as np
import pandas as pd
import streamlit as st

# Permite importar los modelos del proyecto al ejecutar Streamlit.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.queue_model import calcular_mmc, calcular_webster


st.set_page_config(
    page_title="Smart Traffic Salta",
    page_icon="🚦",
    layout="wide",
)

st.title("🚦 Smart Traffic Salta")
st.subheader("Análisis de colas para corredores viales")

# Los aforos del proyecto son sintéticos, no mediciones oficiales.
st.warning(
    "Los aforos de este prototipo son sintéticos. "
    "Los resultados son ilustrativos y no representan mediciones oficiales de tránsito."
)

# Cargar el CSV procesado.
ruta_csv = ROOT / "data" / "processed" / "aforos_limpios.csv"

if not ruta_csv.exists():
    st.error(
        "No se encontró data/processed/aforos_limpios.csv. "
        "Ejecutá primero el notebook de exploración para generarlo."
    )
    st.stop()

df = pd.read_csv(ruta_csv, parse_dates=["timestamp"])

columnas_requeridas = {
    "timestamp",
    "interseccion",
    "periodo",
    "demanda_veh_h",
    "tiempo_servicio_s",
}

if not columnas_requeridas.issubset(df.columns):
    st.error("El CSV no contiene todas las columnas requeridas.")
    st.stop()

# Controles del escenario.
with st.sidebar:
    st.header("Parámetros del escenario")

    intersecciones = sorted(df["interseccion"].dropna().unique())
    interseccion = st.selectbox("Corredor", intersecciones)

    periodos_disponibles = sorted(df["periodo"].dropna().unique())
    periodo = st.selectbox(
        "Franja horaria",
        ["Todo el día"] + periodos_disponibles,
    )

    carriles = st.number_input(
        "Carriles / servidores (c)",
        min_value=1,
        max_value=10,
        value=3,
        step=1,
    )

    # Parámetros del informe: s = 24 veh/min/carril y u = g/C = 0,5.
    flujo_saturacion = st.number_input(
        "Flujo de saturación por carril s (veh/min)",
        min_value=0.1,
        value=24.0,
        step=1.0,
        help="Supuesto del informe; no está medido en el CSV.",
    )

    proporcion_verde = st.number_input(
        "Proporción de verde u = g/C",
        min_value=0.01,
        max_value=0.99,
        value=0.50,
        step=0.05,
        help="Fracción del ciclo durante la cual la fase tiene verde efectivo.",
    )

# Filtrar los datos por corredor y período.
df_seleccion = df[df["interseccion"] == interseccion].copy()

if periodo != "Todo el día":
    df_seleccion = df_seleccion[df_seleccion["periodo"] == periodo]

if df_seleccion.empty:
    st.error("No hay registros para el corredor y período seleccionados.")
    st.stop()

# Convertir la demanda promedio del CSV de veh/h a veh/min.
lambda_veh_min = df_seleccion["demanda_veh_h"].mean() / 60

# Convertir flujo de saturación a tasa efectiva por carril:
# μ efectiva = s × proporción de verde.
mu_efectiva = flujo_saturacion * proporcion_verde

st.caption(
    f"Escenario: **{interseccion}** · **{periodo}** · "
    f"{len(df_seleccion)} registros del dataset"
)

st.write(
    f"Demanda media calculada desde el CSV: **{lambda_veh_min:.2f} veh/min**. "
    f"Tasa efectiva de servicio usada: **{mu_efectiva:.2f} veh/min por carril**."
)

tab_resultados, tab_sensibilidad, tab_datos, tab_supuestos, tab_webster = st.tabs(
    ["Resultados", "Sensibilidad", "Datos del aforo", "Supuestos", "Webster"]
)

with tab_resultados:
    st.header("Medidas de desempeño M/M/c")

    try:
        resultados = calcular_mmc(
            lamda=lambda_veh_min,
            mu=mu_efectiva,
            c=int(carriles),
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Cola media (Lq)",
            f"{resultados['Lq']:.2f} vehículos",
        )

        col2.metric(
            "Espera en cola (Wq)",
            f"{resultados['Wq'] * 60:.2f} segundos",
        )

        col3.metric(
            "Utilización (ρ)",
            f"{resultados['rho']:.1%}",
        )

        col4.metric(
            "Vehículos en el sistema (L)",
            f"{resultados['Ls']:.2f}",
        )

        if "P_espera" in resultados:
            st.metric(
                "Probabilidad de tener que esperar",
                f"{resultados['P_espera']:.1%}",
            )

        st.info(
            "Estos son resultados del modelo M/M/c para los parámetros seleccionados. "
            "La aplicación todavía no calcula automáticamente un ciclo semafórico óptimo."
        )

    except ValueError as error:
        st.error(f"No se puede calcular un sistema estable: {error}")
        st.info(
            "El modelo requiere λ < c × μ. "
            "Revisá la demanda, la tasa efectiva de servicio o el número de carriles."
        )

with tab_sensibilidad:
    st.header("Sensibilidad ante cambios en la demanda")
    st.caption(
        "La curva vuelve a calcular el modelo M/M/c para cada variación de demanda."
    )

    variaciones = np.arange(-30, 41, 10)
    filas = []

    for variacion_pct in variaciones:
        lamda_escenario = lambda_veh_min * (1 + variacion_pct / 100)

        try:
            metrica = calcular_mmc(
                lamda=lamda_escenario,
                mu=mu_efectiva,
                c=int(carriles),
            )

            filas.append(
                {
                    "Variación de demanda (%)": variacion_pct,
                    "Lq (vehículos)": metrica["Lq"],
                    "Wq (segundos)": metrica["Wq"] * 60,
                    "Utilización (ρ)": metrica["rho"],
                    "Estado": "Estable",
                }
            )

        except ValueError:
            filas.append(
                {
                    "Variación de demanda (%)": variacion_pct,
                    "Lq (vehículos)": np.nan,
                    "Wq (segundos)": np.nan,
                    "Utilización (ρ)": lamda_escenario
                    / (int(carriles) * mu_efectiva),
                    "Estado": "Inestable",
                }
            )

    df_sensibilidad = pd.DataFrame(filas)

    st.line_chart(
        df_sensibilidad.set_index("Variación de demanda (%)")[
            ["Lq (vehículos)"]
        ]
    )

    st.dataframe(
        df_sensibilidad.round(3),
        use_container_width=True,
        hide_index=True,
    )

with tab_datos:
    st.header("Registros del CSV")
    st.caption(
        "Datos de data/processed/aforos_limpios.csv. "
        "En este proyecto fueron generados sintéticamente."
    )

    serie_demanda = (
        df_seleccion
        .sort_values("timestamp")
        .set_index("timestamp")["demanda_veh_h"]
        .rename("Demanda (veh/h)")
    )

    st.line_chart(serie_demanda)

    st.dataframe(
        df_seleccion,
        use_container_width=True,
        hide_index=True,
    )

with tab_supuestos:
    st.header("Supuestos del modelo")
    st.markdown(
        """
        - Las llegadas se representan mediante un proceso de Poisson.
        - Los tiempos de servicio se consideran exponenciales.
        - Los carriles se modelan como servidores paralelos equivalentes.
        - La tasa efectiva por carril se calcula como `μ = s × (g/C)`.
        - El flujo de saturación y la proporción de verde son parámetros editables.
        - Los datos del repositorio son sintéticos y no representan aforos oficiales.
        - Este cálculo no simula explícitamente las fases roja y verde del semáforo.
        """
    )

    
with tab_webster:
    st.header("Optimización semafórica — Webster")

    st.warning(
        "Los valores iniciales son un ejemplo ilustrativo del informe, "
        "no mediciones verificadas de una intersección real. "
        "Reemplazalos por los aforos de cada fase cuando los tengan."
    )

    st.caption(
        "El ciclo calculado es el Webster clásico. El verde informado es verde "
        "efectivo; no incluye la carga de tiempos amarillos o todo-rojo."
    )

    with st.form("formulario_webster"):
        col_fase_1, col_fase_2 = st.columns(2)

        with col_fase_1:
            st.subheader("Fase 1")
            nombre_1 = st.text_input(
                "Nombre de la fase 1",
                value="Av. Bicentenario",
            )
            demanda_1 = st.number_input(
                "Demanda de la fase 1 (veh/h)",
                min_value=1.0,
                value=1424.0,
                step=10.0,
            )
            carriles_1 = st.number_input(
                "Carriles de la fase 1",
                min_value=1,
                value=3,
                step=1,
            )

        with col_fase_2:
            st.subheader("Fase 2")
            nombre_2 = st.text_input(
                "Nombre de la fase 2",
                value="Av. Entre Ríos",
            )
            demanda_2 = st.number_input(
                "Demanda de la fase 2 (veh/h)",
                min_value=1.0,
                value=1187.0,
                step=10.0,
            )
            carriles_2 = st.number_input(
                "Carriles de la fase 2",
                min_value=1,
                value=2,
                step=1,
            )

        flujo_saturacion_webster = st.number_input(
            "Flujo de saturación (veh/h por carril)",
            min_value=1.0,
            value=1440.0,
            step=60.0,
            help="El ejemplo del informe usa 24 veh/min por carril, equivalentes a 1440 veh/h.",
        )

        tiempo_perdido = st.number_input(
            "Tiempo perdido total por ciclo (s)",
            min_value=0.1,
            value=8.0,
            step=1.0,
        )

        calcular = st.form_submit_button("Calcular ciclo de Webster")

    if calcular:
        try:
            resultado_webster = calcular_webster(
                fases=[
                    {
                        "nombre": nombre_1,
                        "demanda_veh_h": demanda_1,
                        "carriles": int(carriles_1),
                    },
                    {
                        "nombre": nombre_2,
                        "demanda_veh_h": demanda_2,
                        "carriles": int(carriles_2),
                    },
                ],
                flujo_saturacion_veh_h_por_carril=flujo_saturacion_webster,
                tiempo_perdido_total_s=tiempo_perdido,
            )

            metrica_1, metrica_2, metrica_3 = st.columns(3)

            metrica_1.metric(
                "Ciclo Webster",
                f"{resultado_webster['ciclo_webster_s']:.2f} s",
            )

            metrica_2.metric(
                "Demora media ponderada",
                f"{resultado_webster['demora_media_ponderada_s']:.2f} s",
            )

            metrica_3.metric(
                "Relación crítica total (Y)",
                f"{resultado_webster['Y']:.3f}",
            )

            tabla_fases = pd.DataFrame(
                [
                    {
                        "Fase": fase["nombre"],
                        "Demanda (veh/h)": fase["demanda_veh_h"],
                        "Carriles": fase["carriles"],
                        "Verde efectivo (s)": fase["verde_efectivo_s"],
                        "Grado de saturación (x)": fase["grado_saturacion"],
                        "Demora (s)": fase["demora_s"],
                    }
                    for fase in resultado_webster["fases"]
                ]
            )

            st.subheader("Resultados por fase")
            st.dataframe(
                tabla_fases.round(3),
                use_container_width=True,
                hide_index=True,
            )

            st.info(
                "Este cálculo no sustituye una validación de campo ni aplica "
                "límites mínimos y máximos de ciclo del controlador semafórico."
            )

        except ValueError as error:
            st.error(f"No se pudo calcular Webster: {error}")
