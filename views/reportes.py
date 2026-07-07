import streamlit as st
import pandas as pd
from io import BytesIO


def convertir_excel(df):
    output = BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Reporte")

    return output.getvalue()


def mostrar_reportes(df):

    st.markdown("<h2>📄 Reportes Operativos</h2>", unsafe_allow_html=True)

    # No modificar el dataframe original
    df = df.copy()

    # Por ahora todas las filas pertenecen a SPC
    df["área"] = "SPC"

    # ---------------------------------------------------
    # Filtros
    # ---------------------------------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        area = st.selectbox(
            "Área",
            ["SPC"]
        )

    with col2:
        estado_obra = st.multiselect(
            "Estado de Obra",
            ["En obra", "Obra finalizada"],
            default=["En obra", "Obra finalizada"]
        )

    with col3:
        estado = st.multiselect(
            "Estado",
            ["Dentro de fecha", "Fuera de fecha"],
            default=["Dentro de fecha", "Fuera de fecha"]
        )

    # ---------------------------------------------------
    # Aplicar filtros
    # ---------------------------------------------------
    df_filtrado = df[
        (df["área"] == area) &
        (df["estado_obra_proceso"].isin(estado_obra)) &
        (df["estado"].isin(estado))
    ]

    # ---------------------------------------------------
    # Columnas del reporte
    # ---------------------------------------------------
    columnas = [
        "nro_solicitud",
        "área",
        "fec_finalizac_real",
        "sector_final",
        "fecha_facturacion_correspondiente",
        "dias_transcurridos",
        "dias_hasta_facturacion",
        "estado",
        "causa_raiz",
        "estado_obra_proceso",
        "cod_sscc"
    ]

    df_final = df_filtrado[columnas].copy()

    # ---------------------------------------------------
    # Formato de fechas
    # ---------------------------------------------------
    df_final["fec_finalizac_real"] = pd.to_datetime(
        df_final["fec_finalizac_real"]
    ).dt.strftime("%d/%m/%Y")

    df_final["fecha_facturacion_correspondiente"] = pd.to_datetime(
        df_final["fecha_facturacion_correspondiente"]
    ).dt.strftime("%d/%m/%Y")

    # ---------------------------------------------------
    # Renombrar columnas
    # ---------------------------------------------------
    df_final = df_final.rename(columns={
        "nro_solicitud": "N° Suministro",
        "área": "Área",
        "fec_finalizac_real": "Fecha Fin de Obra",
        "sector_final": "Sector",
        "fecha_facturacion_correspondiente": "Fecha de Facturación",
        "dias_transcurridos": "Días Facturados",
        "dias_hasta_facturacion": "Días Disponibles",
        "estado": "Estado",
        "causa_raiz": "Motivo",
        "estado_obra_proceso": "Estado de Obra",
        "cod_sscc": "Código SSCC"
    })

    # ---------------------------------------------------
    # Vista preliminar + búsqueda
    # ---------------------------------------------------
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("<h3>📊 Vista Preliminar</h3>", unsafe_allow_html=True)

    with col2:
        st.markdown("**🔍 Buscar suministro**")
        suministro_busqueda = st.text_input(
            label="Buscar",
            placeholder="Ej. 12345678",
            label_visibility="collapsed"
        )

    # Aplicar búsqueda
    if suministro_busqueda:
        df_mostrar = df_final[
            df_final["N° Suministro"]
            .astype(str)
            .str.contains(suministro_busqueda.strip(), case=False, na=False)
        ]
    else:
        df_mostrar = df_final

    # Cantidad de registros
    st.caption(f"Mostrando **{len(df_mostrar):,}** registros")

    # Tabla
    st.dataframe(
        df_mostrar,
        use_container_width=True,
        height=500
    )

    # ---------------------------------------------------
    # Descargar Excel
    # ---------------------------------------------------
    excel_data = convertir_excel(df_mostrar)

    st.download_button(
        label="📥 Descargar Reporte en Excel",
        data=excel_data,
        file_name="Reporte_Operativo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )