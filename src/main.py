import os
import pandas as pd

from extract import cargar_fact_suministros, cargar_calendario

from transform import (
    filtrar_obras_validas,
    preparar_ruta_facturacion,
    agregar_plazo_legal,
    calcular_fecha_limite,
    calcular_cumplimiento_sla,
    crear_estado_puser,
    crear_estado_ruta,
    crear_estado_activacion,
    preparar_calendario,
    evaluar_puser,
    calcular_dias_sin_puser,
    calcular_dias_hasta_facturacion,
    calcular_fec_apto_facturar,
    calcular_fecha_facturacion_correspondiente,
    calcular_dias_transcurridos,
    crear_estado_facturacion,
    asignar_responsable
)

# ==========================
# Extraer datos
# ==========================

fact = cargar_fact_suministros()
calendario = cargar_calendario()
calendario = preparar_calendario(calendario)

# ==========================
# Transformar datos
# ==========================

fact = filtrar_obras_validas(fact)

# Crear sector_final, zona_final y ruta_final
fact = preparar_ruta_facturacion(fact)

fact = agregar_plazo_legal(fact)
fact = calcular_fecha_limite(fact)
fact = calcular_cumplimiento_sla(fact)

fact = crear_estado_puser(fact)
fact = crear_estado_ruta(fact)
fact = crear_estado_activacion(fact)

fact = calcular_fec_apto_facturar(fact)
fact = calcular_fecha_facturacion_correspondiente(fact, calendario)
fact = calcular_dias_transcurridos(fact)
fact = crear_estado_facturacion(fact)

fact = asignar_responsable(fact)

fact = calcular_dias_sin_puser(fact)
fact = evaluar_puser(fact)

fact = calcular_dias_hasta_facturacion(fact)

# ==========================
# Mostrar resultados
# ==========================

print(
    fact[
        [
            "numero_cliente",

            "sector",
            "sector_cliente",
            "sector_final",

            "zona",
            "zona_cliente",
            "zona_final",

            "correlativo_ruta",
            "ruta_cliente",
            "ruta_final",

            "fec_puser_nextel",
            "estado_puser",
            "estado_ruta",
            "estado_activacion",

            "fec_apto_facturar",
            "fecha_facturacion_correspondiente",
            "dias_transcurridos",
            "estado",

            "responsable",
            "dias_hasta_puser",
            "estado_puser_plazo",
            "dias_hasta_facturacion"
        ]
    ].head(20)
)

# ==========================
# Guardar archivo
# ==========================

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "output"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

ruta_salida = os.path.join(
    OUTPUT_DIR,
    "fact_suministros_procesado.xlsx"
)

fact.to_excel(ruta_salida, index=False)

print(f"Archivo guardado en: {ruta_salida}")