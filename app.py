import streamlit as st
from streamlit_option_menu import option_menu
from views.dashboard import mostrar_dashboard
import os
import pandas as pd
from views.chat_ia import mostrar_chat_ia
from views.reportes import mostrar_reportes
from views.evolucion import mostrar_evolucion
from src.transform import calcular_metricas_evolucion


BASE_DIR = os.path.dirname(__file__)

ruta_parquet = os.path.join(
    BASE_DIR,
    "output",
    "fact_suministros_procesado.parquet"
)

df = pd.read_parquet(ruta_parquet)

metricas = {
    "solucionados": 0,
    "nuevos": 0,
    "seguimiento": 0,
    "criticos": 0,
    "df_solucionados": pd.DataFrame(),
    "df_nuevos": pd.DataFrame(),
    "df_seguimiento": pd.DataFrame(),
    "df_criticos": pd.DataFrame()
}

st.set_page_config(
    page_title="Luz del Sur",
    page_icon="⚡",
    layout="wide"
)

df = pd.read_parquet(ruta_parquet)

metricas = calcular_metricas_evolucion()

# -----------------------
# HEADER
# -----------------------
import base64

def get_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

logo = get_base64("assets/logo_luzdelsur.png")

st.markdown(f"""
<style>

.banner{{
    width:100%;
    background:#FFD200;
    border-radius:16px;
    padding:22px 0;
    text-align:center;
    margin-bottom:18px;
}}

.banner img{{
    height:90px;
}}

.titulo{{
    text-align:center;
    margin-top:15px;
}}

.titulo h1{{
    margin-bottom:5px;
    font-size:40px;
    font-weight:1000;
    color:#2b2b2b;
}}

.titulo p{{
    margin:0;
    font-size:18px;
    color:#666;
}}

</style>

<div class="banner">
    <img src="data:image/png;base64,{logo}">
</div>

<div class="titulo">
    <h1>Centro de Control de Primera Facturación</h1>
    <p>Seguimiento del ciclo de activación de Suministros Nuevos</p>
</div>

""", unsafe_allow_html=True)

# -----------------------
# MENÚ HORIZONTAL
# -----------------------
seleccion = option_menu(
    menu_title=None,
    options=[
        "Inicio",
        "Evolución",
        "Chat IA",
        "Reportes"
    ],
    icons=[
        "house-fill",
        "graph-up",
        "robot",
        "file-earmark-text-fill"
    ],
    orientation="horizontal",
    default_index=0,
    styles={
        "container": {
            "padding": "0!important",
            "background-color": "#ffffff",
        },
        "icon": {
            "color": "#EF5B52",
            "font-size": "20px"
        },
        "nav-link": {
            "font-size": "18px",
            "font-weight": "500",
            "text-align": "center",
            "margin": "0px",
            "--hover-color": "#f5f5f5",
        },
        "nav-link-selected": {
            "background-color": "#EF5B52",
            "color": "white",
        },
    },
)

st.divider()

if seleccion == "Inicio":
    mostrar_dashboard(df)

elif seleccion == "Evolución":
    mostrar_evolucion(metricas)

elif seleccion == "Chat IA":
    mostrar_chat_ia(df)

elif seleccion == "Reportes":
    mostrar_reportes(df)