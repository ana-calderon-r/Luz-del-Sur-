import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from src.components import card


def mostrar_dashboard(df):

    # --------------------
    # Header
    # --------------------
    col1, col2 = st.columns([5, 1])

    with col1:
        st.markdown("<h2>Indicadores Operativos</h2>", unsafe_allow_html=True)

    with col2:
        st.info(
            f"**Última actualización**\n\n{datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )

    # --------------------
    # KPIs
    # --------------------
    total = len(df)

    en_obra = df["estado_obra_proceso"].eq("En obra").sum()
    finalizados = df["estado_obra_proceso"].eq("Obra finalizada").sum()

    pendientes = df["estado"].isin([
        "Pendiente PUSER",
        "Pendiente Ruta",
        "Pendiente PUSER y Ruta"
    ]).sum()

    fuera = df["estado"].eq("Fuera de fecha").sum()

    # --------------------
    # Tarjetas
    # --------------------
    k1, k2, k3, k4, k5 = st.columns(5)

    with k1:
        card("Suministros Nuevos", total, "100 % del universo", "👥", "#F8F9FA")

    with k2:
        card("En Obra", en_obra, f"{en_obra/total:.1%}", "🚧", "#EAF2FF")

    with k3:
        card("Finalizados", finalizados, f"{finalizados/total:.1%}", "🏁", "#EDF9ED")

    with k4:
        card("Pendientes", pendientes, f"{pendientes/total:.1%}", "⚠", "#FFF9E6")

    with k5:
        card("Fuera de Plazo", fuera, f"{fuera/total:.1%}", "🚨", "#FDECEC")

    st.divider()
    st.markdown(
    "<small>*Los Pendientes corresponden a suministros que no cuentan con fecha PUSER y/o Ruta.</small>",
    unsafe_allow_html=True
)

    # --------------------
    # DIAGRAMA
    # --------------------
    mostrar_diagrama()

    st.divider()

    # --------------------
    # TABLA FUERA DE FECHA
    # --------------------
    st.markdown(
    "<h2>Detalle de Fuera de Plazo</h2>",
    unsafe_allow_html=True
)
    st.caption("Suministros que requieren acción inmediata.")

    df_fuera = df[df["estado"] == "Fuera de fecha"].copy()

    if df_fuera.empty:
        st.info("No hay registros fuera de fecha 🎉")
    else:

        tabla = df_fuera[[
            "nro_solicitud",
            "fec_finalizac_real",
            "sector_final",
            "fecha_facturacion_correspondiente",
            "dias_transcurridos",
            "dias_hasta_facturacion",
            "estado",
            "causa_raiz"
        ]].copy()

        # --------------------
        # RENOMBRAR COLUMNAS
        # --------------------
        tabla = tabla.rename(columns={
            "nro_solicitud": "N° suministro",
            "fec_finalizac_real": "Fecha fin obra",
            "sector_final": "Sector",
            "fecha_facturacion_correspondiente": "Fecha Facturación",
            "dias_transcurridos": "Días Facturados",
            "dias_hasta_facturacion": "Días Disponibles",
            "estado": "Estado",
            "causa_raiz": "Motivo"
        })

        # --------------------
# FORMATO DE COLUMNAS
# --------------------

# Fechas sin hora
        tabla["Fecha fin obra"] = pd.to_datetime(
            tabla["Fecha fin obra"],
            errors="coerce"
        ).dt.strftime("%d/%m/%Y")

        tabla["Fecha Facturación"] = pd.to_datetime(
            tabla["Fecha Facturación"],
            errors="coerce"
        ).dt.strftime("%d/%m/%Y")

# Días sin decimales
        tabla["Días Facturados"] = (
            pd.to_numeric(tabla["Días Facturados"], errors="coerce")
            .fillna(0)
            .astype(int)
        )

        tabla["Días Disponibles"] = (
            pd.to_numeric(tabla["Días Disponibles"], errors="coerce")
            .fillna(0)
            .astype(int)
        )

        # ordenar por criticidad
        tabla = tabla.sort_values("Días Disponibles")

        # --------------------
        # SEMÁFORO POR FILA
        # --------------------
        def semaforo_fila(row):
            val = row["Días Disponibles"]

            # rojo más oscuro
            rojo = "background-color: #b30000; color: white; font-weight: bold;"
            amarillo = "background-color: #FFD700; color: black; font-weight: bold;"
            verde = "background-color: #2E8B57; color: white; font-weight: bold;"
            normal = ""
            
            if pd.isna(val):
                return [normal] * len(row)

            try:
                val = float(val)
            except:
                return [normal] * len(row)

            if val <= 10:
                color = rojo
            elif 11 <= val <= 20:
                color = amarillo
            elif 21 <= val <= 30:
                color = verde
            else:
                color = normal

            return [color] * len(row)
        # aplicar estilo
        tabla_estilada = tabla.style.apply(semaforo_fila, axis=1)

        # MOSTRAR TABLA (ESTO TE FALTABA)
        st.dataframe(tabla_estilada, use_container_width=True)

def mostrar_diagrama():

    st.markdown(
    "<h2>Proceso de Activación para la Primera Facturación</h2>",
    unsafe_allow_html=True
)

    dot = """
    digraph G {
        rankdir=TB;
        bgcolor="white";

        node [shape=box, style="rounded,filled", fontname="Arial"];

        SN [label="Suministros Nuevos\\n= En Obra + Finalizados", fillcolor="#1f3b64", fontcolor="white"];

        EO [label="En Obra", fillcolor="#cfd8e3"];
        FZ [label="Finalizados", fillcolor="#a8d5a2"];

        SN -> EO;
        SN -> FZ;

        A [label="Activos\\n(tiene Puser y Ruta)", fillcolor="#d9f2d9"];
        FP [label="Falta Puser\\n(tiene Ruta, no Puser)", fillcolor="#d9f2d9"];
        FR [label="Falta Ruta\\n(tiene Puser, no Ruta)", fillcolor="#d9f2d9"];
        FPR [label="Falta Puser y Ruta\\n(no tiene ninguno)", fillcolor="#d9f2d9"];

        FZ -> A;
        FZ -> FP;
        FZ -> FR;
        FZ -> FPR;

        CALC [label="Para calcular el ciclo de facturación\\nSÍ o SÍ necesito RUTA", 
              fillcolor="#ffe0b2"];

        A -> CALC;
        FP -> CALC;

        DP [label="Dentro de Plazo\\nFacturación dentro del ciclo esperado", fillcolor="#c8e6c9"];
        FPZ [label="Fuera de Plazo\\nFacturación fuera del ciclo esperado", fillcolor="#ffcdd2"];

        CALC -> DP;
        CALC -> FPZ;
    }
    """

    st.graphviz_chart(dot, use_container_width=True)