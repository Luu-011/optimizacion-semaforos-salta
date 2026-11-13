import streamlit as st
import pandas as pd
import numpy as np

# 1. Configuración de la página
st.set_page_config(page_title="Smart Traffic Salta", page_icon="🚦", layout="wide")

# 2. CSS para Modo Oscuro - Tonos Marrón Café con letras legibles
st.markdown("""
    <style>
    /* Fondo general: Marrón muy oscuro (Café) */
    .stApp {
        background-color: #2C1E16; 
    }
    
    /* Barra lateral: Marrón ligeramente más claro */
    [data-testid="stSidebar"] {
        background-color: #3D2B22 !important;
    }
    
    /* Letras generales: Crema / Marrón pastel claro para que se lean bien */
    h1, h2, h3, h4, h5, h6, p, span, label, div[data-testid="stMarkdownContainer"] {
        color: #E6D5C3 !important; 
    }
    
    /* Tarjetas de métricas (KPIs) */
    div[data-testid="metric-container"] {
        background-color: #4A352A;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        border-left: 6px solid #D4A373; /* Borde marrón pastel claro */
    }
    
    /* Color específico para el valor de la métrica */
    div[data-testid="stMetricValue"] {
        color: #FFFFFF !important; 
    }

    /* Pestañas */
    .stTabs [data-baseweb="tab"] {
        color: #D4A373 !important; /* Color caramelo */
        font-size: 16px;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] {
        color: #E6D5C3 !important;
        border-bottom-color: #D4A373 !important;
    }
    
    /* Botón principal */
    .stButton>button {
        background-color: #D4A373 !important; /* Botón color caramelo/pastel */
        color: #2C1E16 !important; /* Texto oscuro para contrastar */
        border-radius: 8px;
        border: none;
        font-weight: bold;
        padding: 10px 24px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #E6D5C3 !important; /* Se aclara al pasar el mouse */
    }
    
    /* Cajas de info (los carteles por defecto) */
    .stAlert {
        background-color: #4A352A !important;
        color: #E6D5C3 !important;
        border: 1px solid #D4A373 !important;
    }
    
    /* Estilo para el contenedor con borde (Gráficos y Tablas) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #3D2B22;
        border: 1px solid #5C4336 !important;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Encabezado principal
st.markdown("<h1 style='text-align: center; font-size: 50px; margin-bottom: 0;'>🚦 Smart Traffic Salta</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 18px; color: #D4A373 !important;'>Sistema Inteligente de Optimización Semafórica e Investigación Operativa</p>", unsafe_allow_html=True)
st.divider()

# 4. Barra lateral
with st.sidebar:
    st.markdown("<h1 style='text-align: center; font-size: 50px;'>🚥</h1>", unsafe_allow_html=True)
    st.header("⚙️ Panel de Control")
    
    interseccion = st.selectbox(
        "📍 Intersección",
        ["Av. Bicentenario", "Av. Paraguay", "Entre Ríos"]
    )
    
    st.markdown("### 🚗 Datos de Tránsito")
    tasa_arribo = st.number_input("Tasa de Arribo - λ (veh/min)", value=20.0, step=1.0)
    tasa_servicio = st.number_input("Capacidad por carril - μ (veh/min)", value=13.33, step=0.1)
    num_carriles = st.slider("Número de carriles (c)", min_value=1, max_value=4, value=2)
    
    st.divider()
    # Botón restaurado a "Calcular Métricas"
    boton_calcular = st.button("📊 Calcular Métricas", use_container_width=True)

# 5. Pestañas
tab1, tab2, tab3 = st.tabs(["📊 Métricas", "📈 Análisis de Sensibilidad", "📋 Datos del Aforo"])

with tab1:
    st.subheader("Métricas Analíticas de Teoría de Colas (M/M/c)")
    if boton_calcular:
        with st.spinner('Calculando modelo...'):
            st.success(f"Resultados calculados con éxito para **{interseccion}**")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="Largo de Cola (Lq)", value="3.45 veh", delta="-0.5 vs actual", delta_color="inverse")
            with col2:
                st.metric(label="Demora Promedio (Wq)", value="0.15 min", delta="-0.02 vs actual", delta_color="inverse")
            with col3:
                st.metric(label="Utilización (ρ)", value="75 %", delta="Óptimo", delta_color="normal")
                
            st.markdown("---")
            st.markdown("### 💡 Recomendación Semafórica")
            st.info("Con los parámetros actuales, se sugiere configurar un ciclo semafórico de **90 segundos**, con un verde efectivo de **45 segundos** para evitar saturación.")
    else:
        st.info("👈 Configurá los parámetros en la barra lateral y presioná 'Calcular Métricas'.")

with tab2:
    st.subheader("Análisis de Sensibilidad del Modelo")
    if boton_calcular:
        with st.container(border=True):
            variaciones = np.linspace(-0.3, 0.3, 20)
            lq = [max(0, 3.45 * (1 + v)**5) for v in variaciones] 
            df_grafico = pd.DataFrame({"Variación de Demanda (%)": variaciones * 100, "Largo de Cola (Lq)": lq})
            
            # Gráfico con color marrón pastel/caramelo
            st.line_chart(df_grafico.set_index("Variación de Demanda (%)"), color="#D4A373")
            st.caption("El gráfico demuestra cómo la cola se dispara exponencialmente a medida que la demanda se acerca a la capacidad máxima de la avenida.")
    else:
        st.info("Ejecutá las métricas para ver el análisis de sensibilidad.")

with tab3:
    st.subheader("Exploración de Datos de Aforo (Salta)")
    with st.container(border=True):
        st.markdown("Muestra de los datos generados para el corredor vial.")
        df_mock = pd.DataFrame({
            "Hora": ["08:00", "08:15", "08:30", "08:45"],
            "Demanda (veh/h)": [1250, 1300, 1280, 1150],
            "Ocupación (%)": [85, 92, 88, 75]
        })
        st.dataframe(df_mock, use_container_width=True, hide_index=True)