import requests


URL_EMERGENCIAS = "https://sgonorte.bomberosperu.gob.pe/24horas"


def obtener_pagina() -> str:
    """
    Descarga la página de 'Emergencias 24 horas' y devuelve el HTML como texto.
    Si la respuesta no es 200, lanza un error.
    """
    cabeceras = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }

    respuesta = requests.get(URL_EMERGENCIAS, headers=cabeceras, timeout=30)

    if respuesta.status_code != 200:
        raise RuntimeError(
            f"Error al obtener la página: código {respuesta.status_code}"
        )

    return respuesta.text
