import pandas as pd
import os

def cargar_datos_procesados():
    ruta = os.path.join(
        "output",
        "fact_suministros_procesado.parquet"
    )
    return pd.read_parquet(ruta)