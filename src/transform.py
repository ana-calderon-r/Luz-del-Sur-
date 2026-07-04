import pandas as pd

def filtrar_obras_validas(fact):
    """
    Conserva únicamente las obras validas:
    - Estado A (Admisible) o T (Terminado)
    - Costo de servicio mayor que 0
    - Motivo diferente de 16 y 37
    - EXCLUYE: registros con año de finalización 2025 y estado_hisfact 'ACTIVO'
    """

    # Reemplazar \N por valores nulos
    fact = fact.replace("\\N", pd.NA)

    # Convertimos la columna a tipo datetime por si viene como texto, 
    # errors='coerce' transformará lo que no sea fecha en NaT (nulo)
    fact["fec_finalizac_real"] = pd.to_datetime(fact["fec_finalizac_real"], errors="coerce")

    # Creamos una máscara para identificar los que SÍ queremos borrar (Año 2025 Y ACTIVO)
    a_borrar = (fact["fec_finalizac_real"].dt.year == 2025) & (fact["estado_hisfac"] == "ACTIVO")

    # Aplicamos los filtros originales y sumamos la exclusión usando la negación (~)
    fact = fact[
        (fact["estado_obra"].isin(["A", "T"])) &
        (fact["total_costo_servicio"] > 0) &
        (~fact["motivo"].isin([16, 37])) &
        (~a_borrar)  # Conserva todo lo que NO cumpla la condición de borrado
    ].copy()

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

    fact["estado"] = fact["dias_transcurridos"].apply(
        lambda x:
            "Dentro de fecha"
            if pd.notna(x) and x <= 45
            else "Fuera de fecha"
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