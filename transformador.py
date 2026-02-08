from typing import List, Dict

import pandas as pd


COLUMNAS = [
    "nro_parte",
    "fecha_hora",
    "direccion_distrito",
    "tipo",
    "estado",
    "maquinas",
]


def construir_dataframe(registros: List[Dict[str, str]]) -> pd.DataFrame:
    """
    Recibe la lista de registros (diccionarios) y devuelve un DataFrame de pandas
    con las columnas en el orden definido.

    En esta etapa respetamos los valores tal cual vienen de la interfaz (As Is).
    La normalización (separar fecha/hora, distrito, latitud/longitud, etc.)
    se hará en un proceso posterior.
    """
    if not registros:
        # DataFrame vacío pero con las columnas esperadas
        return pd.DataFrame(columns=COLUMNAS)

    df = pd.DataFrame(registros)

    # Aseguramos que existan todas las columnas esperadas
    for columna in COLUMNAS:
        if columna not in df.columns:
            df[columna] = ""

    # Reordenamos columnas
    df = df[COLUMNAS]

    # Ajuste ligero: limpiamos espacios y dejamos estado en mayúsculas (ATENDIENDO / CERRADO)
    df["estado"] = df["estado"].astype(str).str.strip().str.upper()

    # Aseguramos que el resto sean texto por ahora (As Is)
    for columna in ["nro_parte", "fecha_hora", "direccion_distrito", "tipo", "maquinas"]:
        df[columna] = df[columna].astype(str)

    return df
