import streamlit as st
import os
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

client = None

if api_key:
    client = OpenAI(api_key=api_key)

def mostrar_chat_ia(df):

    st.markdown("<h2>🤖 Copiloto Operativo</h2>", unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # mostrar historial
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("Pregunta sobre suministros...")

    if user_input:

        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        with st.chat_message("user"):
            st.write(user_input)

        response = generar_respuesta(user_input, df)

        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })

        with st.chat_message("assistant"):
            st.write(response)


def generar_respuesta(prompt, df):

    resumen = crear_contexto(df)

    system = f"""
Eres un analista operativo de Luz del Sur.

Tu trabajo:
- Analizar suministros eléctricos
- Detectar retrasos
- Priorizar urgencias
- Explicar causas operativas

Datos actuales:
{resumen}

Reglas:
- Sé claro y directo
- Usa lenguaje ejecutivo
- Da recomendaciones cuando sea posible
"""

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ]
    )

    return completion.choices[0].message.content


def crear_contexto(df):

    total_fuera = len(df[df["estado"] == "Fuera de fecha"])
    total_pendientes = len(df[df["estado"].str.contains("Pendiente", na=False)])
    total_activos = len(df[df["estado_obra_proceso"] == "En obra"])

    return f"""
- Fuera de plazo: {total_fuera}
- Pendientes: {total_pendientes}
- En obra: {total_activos}
"""
