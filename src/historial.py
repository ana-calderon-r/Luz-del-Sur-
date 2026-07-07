import os
import pandas as pd

def obtener_snapshots():

    carpeta = "historial"

    archivos = sorted([
        f for f in os.listdir(carpeta)
        if f.endswith(".parquet")
    ])

    return archivos

def cargar_ultimo_snapshot():

    archivos = obtener_snapshots()

    if len(archivos) == 0:
        return None

    return pd.read_parquet(
        os.path.join("historial", archivos[-1])
    )

def cargar_snapshot_anterior():

    archivos = obtener_snapshots()

    if len(archivos) < 2:
        return None

    return pd.read_parquet(
        os.path.join("historial", archivos[-2])
    )

def comparar_snapshots(actual, anterior):

    if anterior is None:
        return None

    hoy = set(actual["numero_cliente"])

    ayer = set(anterior["numero_cliente"])

    nuevos = hoy - ayer

    solucionados = ayer - hoy

    return nuevos, solucionados