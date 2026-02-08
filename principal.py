from pathlib import Path

import pandas as pd

from obtener_pagina import obtener_pagina
from analizador import extraer_registros
from transformador import construir_dataframe, COLUMNAS


def _parsear_fecha_hora_orden(serie_fechas: pd.Series) -> pd.Series:
    """
    Convierte la columna 'fecha_hora' (texto en formato dd/mm/YYYY hh:mm:ss a.m./p.m.)
    en un datetime para poder ordenar de más reciente a más antiguo.

    No modifica el valor original, solo devuelve una Serie auxiliar.
    """
    texto_normalizado = (
        serie_fechas.astype(str)
        .str.replace(" a.m.", " AM", regex=False)
        .str.replace(" p.m.", " PM", regex=False)
        .str.replace(" a. m.", " AM", regex=False)
        .str.replace(" p. m.", " PM", regex=False)
    )

    fechas = pd.to_datetime(
        texto_normalizado,
        dayfirst=True,
        errors="coerce",
    )
    return fechas


def ejecutar():
    """
    Flujo actual (pensado para ejecución periódica):

    1) Descarga la página de emergencias 24 horas.
    2) Extrae los registros en forma de diccionarios.
    3) Construye un DataFrame de pandas con las columnas definidas (As Is).
    4) Lee (o crea) el archivo maestro 'emergencias_historico.csv'.
    5) Concatena la extracción actual al histórico.
    6) Elimina filas duplicadas (mismas columnas completas).
    7) Ordena el histórico desde la fecha/hora más reciente a la más antigua.
    8) Guarda nuevamente el histórico en disco.
    """

    # 1) Descarga de la página
    html = obtener_pagina()
    print("Página descargada correctamente.")

    # 2) Extracción de registros
    registros = extraer_registros(html)
    print(f"Total de registros extraídos en esta corrida: {len(registros)}")

    # 3) Construir DataFrame As Is
    df_actual = construir_dataframe(registros)
    print(f"DataFrame actual: {len(df_actual)} filas x {len(df_actual.columns)} columnas")
    print("Columnas:", list(df_actual.columns))

    if df_actual.empty:
        print("Advertencia: DataFrame vacío, no se actualizará el histórico.")
        return

    # 4) Rutas de proyecto y archivo maestro (relativas al código)
    carpeta_proyecto = Path(__file__).resolve().parent
    carpeta_salida = carpeta_proyecto / "salida"
    carpeta_salida.mkdir(exist_ok=True)

    ruta_historico = carpeta_salida / "emergencias_historico.csv"

    # 5) Cargar histórico si existe
    if ruta_historico.exists():
        historico_df = pd.read_csv(ruta_historico, dtype=str, encoding="utf-8-sig")
        # Aseguramos columnas esperadas
        for col in COLUMNAS:
            if col not in historico_df.columns:
                historico_df[col] = ""
        historico_df = historico_df[COLUMNAS]
    else:
        historico_df = pd.DataFrame(columns=COLUMNAS)

    print(f"Registros ya almacenados en histórico: {len(historico_df)}")

    # 6) Concatenar extracción actual al histórico
    combinado = pd.concat([historico_df, df_actual], ignore_index=True)

    # 7) Eliminar duplicados:
    #    - Dos filas se consideran la misma "versión" si TODOS los campos coinciden.
    combinado.drop_duplicates(subset=COLUMNAS, inplace=True)

    # 8) Ordenar: primero por fecha/hora (más reciente primero),
    #    y luego por nro_parte para tener algo consistente.
    combinado["__orden_fecha"] = _parsear_fecha_hora_orden(combinado["fecha_hora"])

    combinado.sort_values(
        by=["__orden_fecha", "nro_parte"],
        ascending=[False, True],  # más reciente arriba
        kind="mergesort",         # estable
        inplace=True,
    )

    combinado.drop(columns=["__orden_fecha"], inplace=True)
    combinado.reset_index(drop=True, inplace=True)

    nuevos_registros = len(combinado) - len(historico_df)
    print(f"Nuevas versiones de partes agregadas al histórico: {nuevos_registros}")
    print(f"Total de registros en histórico después de actualizar: {len(combinado)}")

    # 9) Guardar histórico actualizado
    combinado.to_csv(ruta_historico, index=False, encoding="utf-8-sig")
    print(f"\nHistórico actualizado guardado en:\n  {ruta_historico}")

    # 10) Mostrar una vista previa de las primeras filas (las más recientes)
    print("\nPrimeras 5 filas del histórico (más recientes):")
    print(combinado.head(5).to_string(index=False))


if __name__ == "__main__":
    ejecutar()
