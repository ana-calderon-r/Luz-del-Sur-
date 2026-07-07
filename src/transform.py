import pandas as pd

def filtrar_obras_validas(fact):

    fact = fact.replace("\\N", pd.NA)

    fact["fec_finalizac_real"] = pd.to_datetime(
        fact["fec_finalizac_real"],
        errors="coerce"
    )

    fact = fact[

        (fact["estado_obra"].isin(["A", "T"])) &
        (fact["total_costo_servicio"] > 0) &
        (~fact["motivo"].isin([16, 37])) &

        # Solo universo NUEVO
        (fact["estado_hisfac"] == "NUEVO") &

        # Excluir finalizados en 2025
        (
            fact["fec_finalizac_real"].isna()
            |
            (fact["fec_finalizac_real"].dt.year != 2025)
        )

    ].copy()

    return fact

def crear_estado_obra_proceso(fact):
    """
    Determina si la obra ya finalizó o continúa en ejecución.
    """

    fact["fec_finalizac_real"] = pd.to_datetime(
        fact["fec_finalizac_real"],
        errors="coerce"
    )

    fact["estado_obra_proceso"] = fact["fec_finalizac_real"].apply(
        lambda x: "Obra finalizada" if pd.notna(x) else "En obra"
    )

    return fact

def preparar_ruta_facturacion(fact):
    """
    Obtiene la información definitiva de sector, zona y ruta.
    Si el dato principal está vacío utiliza el dato del cliente.
    """

    columnas = [
        "sector", "sector_cliente",
        "zona", "zona_cliente",
        "correlativo_ruta", "ruta_cliente"
    ]

    for col in columnas:
        fact[col] = (
            fact[col]
            .replace("\\N", pd.NA)
            .replace("", pd.NA)
            .astype("string")
            .str.strip()
        )

    fact["sector_final"] = (
        fact["sector"]
        .combine_first(fact["sector_cliente"])
    )

    fact["zona_final"] = (
        fact["zona"]
        .combine_first(fact["zona_cliente"])
    )

    fact["ruta_final"] = (
        fact["correlativo_ruta"]
        .combine_first(fact["ruta_cliente"])
    )

    return fact

def agregar_plazo_legal(fact):
    """
    Asigna el plazo legal según el tipo de rutina.
    """

    plazos = {
        "A": 7,
        "B": 21,
        "C": 21,
        "D": 56,
        "E": 360
    }

    fact["plazo_legal_dias"] = fact["cnd_rutina"].map(plazos)

    return fact

def calcular_fecha_limite(fact):

    fact["fecha_inicio_ley"] = pd.to_datetime(
        fact["fecha_inicio_ley"],
        errors="coerce"
    )

    fact["fecha_limite"] = (
        fact["fecha_inicio_ley"] +
        pd.to_timedelta(fact["plazo_legal_dias"], unit="D")
    )

    return fact

def calcular_cumplimiento_sla(fact):

    fact["fec_finalizac_real"] = pd.to_datetime(
        fact["fec_finalizac_real"],
        errors="coerce"
    )

    fact["cumple_sla"] = (
        fact["fec_finalizac_real"] <= fact["fecha_limite"]
    )

    return fact

def crear_estado_puser(fact):

    # Corregido: Se cambió a 'fec_puser_nextel'
    fact["estado_puser"] = fact["fec_puser_nextel"].apply(
        lambda x: "Tiene PUSER" if pd.notna(x) else "Falta PUSER"
    )

    return fact

def crear_estado_ruta(fact):

    fact["estado_ruta"] = (
        (
            fact["sector_final"].notna() &
            fact["zona_final"].notna() &
            fact["ruta_final"].notna()
        )
        .map({
            True: "Tiene Ruta",
            False: "Falta Ruta"
        })
    )

    return fact

def crear_estado_activacion(fact):

    condiciones = [
        (fact["estado_puser"] == "Tiene PUSER") &
        (fact["estado_ruta"] == "Tiene Ruta"),

        (fact["estado_puser"] == "Falta PUSER") &
        (fact["estado_ruta"] == "Tiene Ruta"),

        (fact["estado_puser"] == "Tiene PUSER") &
        (fact["estado_ruta"] == "Falta Ruta"),

        (fact["estado_puser"] == "Falta PUSER") &
        (fact["estado_ruta"] == "Falta Ruta")
    ]

    resultados = [
        "Activo",
        "Pendiente PUSER",
        "Pendiente RUTA",
        "Pendiente PUSER y RUTA"
    ]

    fact["estado_activacion"] = ""

    for condicion, resultado in zip(condiciones, resultados):
        fact.loc[condicion, "estado_activacion"] = resultado

    return fact

def preparar_calendario(calendario):

    calendario["Fecha_Lectura"] = pd.to_datetime(
        calendario["Fecha_Lectura"],
        errors="coerce"
    )

    calendario["Sector"] = (
        calendario["Sector"]
        .astype(str)
        .str.strip()
    )

    return calendario

def buscar_fecha_facturacion(fec_apto_facturar, sector, calendario):

    if pd.isna(fec_apto_facturar) or pd.isna(sector):
        return pd.NaT

    fechas = calendario[
        (calendario["Sector"] == sector) &
        (calendario["Fecha_Lectura"] >= fec_apto_facturar)
    ]

    if fechas.empty:
        return pd.NaT

    return fechas["Fecha_Lectura"].min()

def calcular_fec_apto_facturar(fact):

    fact["fec_finalizac_real"] = pd.to_datetime(
        fact["fec_finalizac_real"],
        errors="coerce"
    )

    fact["fec_apto_facturar"] = (
        fact["fec_finalizac_real"] +
        pd.Timedelta(days=15)
    )

    return fact

def calcular_fecha_facturacion_correspondiente(fact, calendario):

    fact["fecha_facturacion_correspondiente"] = fact.apply(
        lambda fila: buscar_fecha_facturacion(
            fila["fec_apto_facturar"],
            fila["sector_final"],
            calendario
        ),
        axis=1
    )

    return fact

def buscar_fecha_facturacion_mes_finalizacion(fec_apto_facturar, sector, calendario):

    if pd.isna(fec_apto_facturar) or pd.isna(sector):
        return pd.NaT

    fechas = calendario[
        (calendario["Sector"] == sector) &
        (calendario["Fecha_Lectura"].dt.year == fec_apto_facturar.year) &
        (calendario["Fecha_Lectura"].dt.month == fec_apto_facturar.month)
    ]

    if fechas.empty:
        return pd.NaT

    return fechas["Fecha_Lectura"].min()

def calcular_fecha_facturacion_mes_finalizacion(fact, calendario):

    fact["fecha_facturacion_mes_finalizacion"] = fact.apply(
        lambda fila: buscar_fecha_facturacion_mes_finalizacion(
            fila["fec_apto_facturar"],
            fila["sector_final"],
            calendario
        ),
        axis=1
    )

    return fact

def calcular_dias_transcurridos(fact):

    fact["fec_finalizac_real"] = pd.to_datetime(
        fact["fec_finalizac_real"],
        errors="coerce"
    )

    fact["dias_transcurridos"] = (
        fact["fecha_facturacion_correspondiente"]
        - fact["fec_finalizac_real"]
    ).dt.days

    return fact

def crear_estado_facturacion(fact):

    fact["estado_facturacion"] = fact.apply(
        lambda fila:
            "En obra"
            if fila["estado_obra_proceso"] == "En obra"
            else (
                "Dentro de fecha"
                if pd.notna(fila["dias_transcurridos"]) and fila["dias_transcurridos"] <= 45
                else "Fuera de fecha"
            ),
        axis=1
    )

    return fact

def asignar_responsable(fact):

    responsables = {
        "Pendiente PUSER": "Área SPC",
        "Pendiente RUTA": "Sucursal",
        "Pendiente PUSER y RUTA": "Área SPC y Sucursal"
    }

    fact["responsable"] = (
        fact["estado_activacion"]
        .map(responsables)
    )

    return fact     

def calcular_dias_sin_puser(fact):
 
    fact["fec_finalizac_real"] = pd.to_datetime(
        fact["fec_finalizac_real"],
        errors="coerce"
    )
 
    # Corregido: Se cambió 'fecha_puser_nextel' a 'fec_puser_nextel'
    fact["fec_puser_nextel"] = pd.to_datetime(
        fact["fec_puser_nextel"],
        errors="coerce"
    )
 
    # Fecha de hoy (sin hora)
    hoy = pd.Timestamp.today().normalize()
 
    # Corregido: Se cambió .fillna(hoy) sobre 'fec_puser_nextel'
    fact["dias_hasta_puser"] = (
        fact["fec_puser_nextel"]
        .fillna(hoy)
        .sub(fact["fec_finalizac_real"])
        .dt.days
    )
 
    return fact
 
def evaluar_puser(fact):
 
    fact["estado_puser_plazo"] = fact["dias_hasta_puser"].apply(
        lambda x:
            "Cumple"
            if pd.notna(x) and x <= 1
            else "Fuera de plazo"
    )
 
    return fact

#EXTRA

def calcular_dias_hasta_facturacion(fact):

    hoy = pd.Timestamp.today().normalize()

    fact["dias_hasta_facturacion"] = (
        fact["fecha_facturacion_correspondiente"] - hoy
    ).dt.days

    return fact

#ANÁLISIS

def crear_estado(fact):

    estados = []

    for _, fila in fact.iterrows():

        # Sigue en obra
        if fila["estado_obra_proceso"] == "En obra":
            estados.append("En obra")

        # Ya terminó la obra
        else:

            if fila["estado_activacion"] == "Pendiente PUSER":
                estados.append("Pendiente PUSER")

            elif fila["estado_activacion"] == "Pendiente RUTA":
                estados.append("Pendiente Ruta")

            elif fila["estado_activacion"] == "Pendiente PUSER y RUTA":
                estados.append("Pendiente PUSER y Ruta")

            elif fila["estado_activacion"] == "Activo":

                if fila["estado_facturacion"] == "Dentro de fecha":
                    estados.append("Dentro de fecha")
                else:
                    estados.append("Fuera de fecha")

            else:
                estados.append("Sin clasificar")

    fact["estado"] = estados

    return fact

def crear_causa_raiz(fact):

    causas = []

    for _, fila in fact.iterrows():

        # EN OBRA
        if fila["estado"] == "En obra":
            causas.append("Obra en ejecución")

        # PENDIENTES
        elif fila["estado"] == "Pendiente PUSER":
            causas.append("Pendiente de registro PUSER")

        elif fila["estado"] == "Pendiente Ruta":
            causas.append("Pendiente de asignación de Ruta")

        elif fila["estado"] == "Pendiente PUSER y Ruta":
            causas.append("Pendiente de registro PUSER y asignación de Ruta")

        # DENTRO DE FECHA
        elif fila["estado"] == "Dentro de fecha":
            causas.append("Sin observaciones")

        # FUERA DE FECHA
        elif fila["estado"] == "Fuera de fecha":

            if fila["fec_apto_facturar"] > fila["fecha_facturacion_mes_finalizacion"]:

                causas.append(
                    "No alcanzó el ciclo de facturación del mes"
                )

            elif (
                pd.notna(fila["fec_puser_nextel"])
                and
                fila["fec_puser_nextel"] > fila["fecha_facturacion_mes_finalizacion"]
            ):

                causas.append(
                    "PUSER registrado después del cierre del ciclo"
                )

            else:

                causas.append("Otro motivo")

        else:

            causas.append("Sin clasificar")

    fact["causa_raiz"] = causas

    return fact

import os
import pandas as pd

def calcular_metricas_evolucion():

    # ==============================
    # Carpeta historial
    # ==============================

    historial_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "historial"
    )

    archivos = sorted([
        f for f in os.listdir(historial_dir)
        if f.endswith(".parquet")
    ])

    # Si aún no existen dos snapshots
    if len(archivos) < 2:

        return {
            "solucionados": 0,
            "nuevos": 0,
            "seguimiento": 0,
            "criticos": 0,
            "df_solucionados": pd.DataFrame(),
            "df_nuevos": pd.DataFrame(),
            "df_seguimiento": pd.DataFrame(),
            "df_criticos": pd.DataFrame()
        }

    # ==============================
    # Leer los dos últimos snapshots
    # ==============================

    ruta_ayer = os.path.join(historial_dir, archivos[-2])
    ruta_hoy = os.path.join(historial_dir, archivos[-1])

    df_ayer = pd.read_parquet(ruta_ayer)
    df_hoy = pd.read_parquet(ruta_hoy)

    # ==============================
    # Solo fuera de fecha
    # ==============================

    ayer_fp = df_ayer[
        df_ayer["estado"] == "Fuera de fecha"
    ].copy()

    hoy_fp = df_hoy[
        df_hoy["estado"] == "Fuera de fecha"
    ].copy()

    llave = "numero_cliente"

    set_ayer = set(ayer_fp[llave])
    set_hoy = set(hoy_fp[llave])

    # ==============================
    # KPI 1
    # Solucionados
    # ==============================

    solucionados = set_ayer - set_hoy

    df_solucionados = ayer_fp[
        ayer_fp[llave].isin(solucionados)
    ]

    # ==============================
    # KPI 2
    # Nuevos fuera de fecha
    # ==============================

    nuevos = set_hoy - set_ayer

    df_nuevos = hoy_fp[
        hoy_fp[llave].isin(nuevos)
    ]

    # ==============================
    # KPI 3
    # Seguimiento
    # ==============================

    seguimiento = set_hoy.intersection(set_ayer)

    df_seguimiento = hoy_fp[
        hoy_fp[llave].isin(seguimiento)
    ]

    # ==============================
    # KPI 4
    # Críticos
    # ==============================

    df_criticos = hoy_fp[
        (hoy_fp["dias_hasta_facturacion"] >= 0) &
        (hoy_fp["dias_hasta_facturacion"] <= 10)
    ]

    # ==============================

    return {

        "solucionados": len(df_solucionados),

        "nuevos": len(df_nuevos),

        "seguimiento": len(df_seguimiento),

        "criticos": len(df_criticos),

        "df_solucionados": df_solucionados,

        "df_nuevos": df_nuevos,

        "df_seguimiento": df_seguimiento,

        "df_criticos": df_criticos

    }