import pandas as pd
import os

# Ruta de la carpeta principal del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Ruta a la carpeta data
DATA_DIR = os.path.join(BASE_DIR, "data")


def cargar_fact_suministros():
    ruta = os.path.join(DATA_DIR, "fact_suministros.xlsx")
    fact = pd.read_excel(ruta)
    return fact


def cargar_calendario():
    ruta = os.path.join(DATA_DIR, "dim_calendario_facturacion.xlsx")
    calendario = pd.read_excel(ruta)
    return calendario