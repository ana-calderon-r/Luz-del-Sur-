import streamlit as st


def mostrar_evolucion(metricas):

    st.title("📈 Evolución")

    st.caption("Comparación con el snapshot anterior")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "✅ Solucionados",
        metricas["solucionados"]
    )

    c2.metric(
        "🔴 Nuevos Fuera de Plazo",
        metricas["nuevos"]
    )

    c3.metric(
        "🟠 En Seguimiento",
        metricas["seguimiento"]
    )

    c4.metric(
        "🔥 Críticos",
        metricas["criticos"]
    )

    st.divider()

    # ------------------------

    with st.expander("✅ Ver suministros solucionados"):

        st.dataframe(
            metricas["df_solucionados"],
            use_container_width=True
        )

    # ------------------------

    with st.expander("🔴 Ver nuevos fuera de plazo"):

        st.dataframe(
            metricas["df_nuevos"],
            use_container_width=True
        )

    # ------------------------

    with st.expander("🟠 Ver seguimiento"):

        st.dataframe(
            metricas["df_seguimiento"],
            use_container_width=True
        )

    # ------------------------

    with st.expander("🔥 Ver críticos"):

        st.dataframe(
            metricas["df_criticos"],
            use_container_width=True
        )