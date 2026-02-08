from typing import List, Dict
from bs4 import BeautifulSoup


def _obtener_lineas(html: str) -> List[str]:
    """
    Convierte el HTML en texto plano y devuelve una lista de líneas.
    Conservamos líneas vacías porque ayudan a separar bloques.
    """
    sopa = BeautifulSoup(html, "html.parser")
    texto = sopa.get_text("\n")
    lineas = [linea.strip() for linea in texto.splitlines()]
    return lineas


def _siguiente_linea_no_vacia(lineas: List[str], indice: int) -> int:
    """
    Devuelve el índice de la siguiente línea no vacía a partir de 'indice'.
    Si no encuentra, devuelve len(lineas).
    """
    total = len(lineas)
    i = indice
    while i < total and lineas[i].strip() == "":
        i += 1
    return i


def _es_texto_control_maquinas(texto: str) -> bool:
    """
    Detecta textos de interfaz que no forman parte de las máquinas,
    por ejemplo: 'Resumen de unidades', '×', 'Cerrar'.
    """
    t = texto.strip().upper()
    if t in {"×", "X", "CERRAR"}:
        return True
    if "RESUMEN DE UNIDADES" in t:
        return True
    return False


# -----------------------------------------------------------
# PARSER 1: FORMATO LISTA COMPACTA
# -----------------------------------------------------------

def _extraer_registros_lista(lineas: List[str]) -> List[Dict[str, str]]:
    registros: List[Dict[str, str]] = []
    i = 0
    total = len(lineas)

    while i < total:
        linea = lineas[i].strip()
        partes = linea.split()

        # Detectar inicio de registro formato lista:
        # primera palabra: número de fila
        # segunda palabra: número de parte (cualquier cantidad de dígitos)
        if len(partes) >= 3 and partes[0].isdigit() and partes[1].isdigit():
            nro_parte = partes[1]
            fecha_hora = " ".join(partes[2:])

            # Dirección / Distrito
            i = _siguiente_linea_no_vacia(lineas, i + 1)
            if i >= total:
                break
            direccion_distrito = lineas[i].strip()

            # Tipo + Estado
            i = _siguiente_linea_no_vacia(lineas, i + 1)
            if i >= total:
                break
            linea_tipo_estado = lineas[i].strip()
            partes_tipo = linea_tipo_estado.split()
            if partes_tipo:
                estado = partes_tipo[-1]           # ATENDIENDO / CERRADO
                tipo = " ".join(partes_tipo[:-1])  # descripción del tipo
            else:
                estado = ""
                tipo = ""

            # Máquinas (líneas con "*")
            maquinas_lista: List[str] = []
            i += 1
            while i < total:
                texto_linea = lineas[i].strip()

                if texto_linea == "":
                    i += 1
                    continue

                # Si es texto de interfaz (Resumen de unidades, ×, Cerrar) -> fin de bloque
                if _es_texto_control_maquinas(texto_linea):
                    i += 1
                    break

                if texto_linea.startswith("*"):
                    texto_maquina = texto_linea.lstrip("*").strip()
                    if texto_maquina:
                        maquinas_lista.append(texto_maquina)
                    i += 1
                    continue

                # termina bloque de máquinas
                break

            maquinas = " / ".join(maquinas_lista)

            registros.append(
                {
                    "nro_parte": nro_parte,
                    "fecha_hora": fecha_hora,
                    "direccion_distrito": direccion_distrito,
                    "tipo": tipo,
                    "estado": estado,
                    "maquinas": maquinas,
                }
            )

            # NO hacemos i += 1 aquí; ya quedó en la siguiente posición
            continue

        # si no es inicio de registro, seguimos recorriendo
        i += 1

    return registros


# -----------------------------------------------------------
# PARSER 2: FORMATO BLOQUES "#1 ... / N° Parte:"
# -----------------------------------------------------------

def _extraer_registros_bloques(lineas: List[str]) -> List[Dict[str, str]]:
    registros: List[Dict[str, str]] = []
    i = 0
    total = len(lineas)

    while i < total:
        linea = lineas[i].strip()

        # Buscamos encabezados tipo "#1 EMERGENCIA MEDICA / ..."
        if linea.startswith("#") and any(ch.isdigit() for ch in linea):
            # quitamos "#" y separamos número de fila del tipo
            texto = linea.lstrip("#").strip()
            partes = texto.split(maxsplit=1)
            if len(partes) == 2:
                # numero_fila = partes[0]  # no lo usamos
                tipo_desde_header = partes[1]
            else:
                tipo_desde_header = ""

            # Buscar "N° Parte:" en las siguientes líneas
            j = i + 1
            nro_parte = ""
            while j < min(total, i + 15):
                t = lineas[j].strip()
                if "PARTE" in t.upper():
                    # extraer el número que venga después
                    for token in t.replace("°", "").replace("º", "").split():
                        if token.isdigit():
                            nro_parte = token
                            break
                    break
                j += 1

            # Buscar estado (ATENDIENDO / CERRADO)
            k = j + 1
            estado = ""
            while k < min(total, i + 25):
                t = lineas[k].strip().upper()
                if t in ("ATENDIENDO", "CERRADO"):
                    estado = t
                    break
                k += 1

            # Dirección / Distrito = primera línea no vacía después del estado
            d = _siguiente_linea_no_vacia(lineas, k + 1)
            if d >= total:
                break
            direccion_distrito = lineas[d].strip()

            # Fecha y hora = siguiente línea no vacía
            fh = _siguiente_linea_no_vacia(lineas, d + 1)
            if fh >= total:
                break
            fecha_hora = lineas[fh].strip()

            # Máquinas = líneas siguientes hasta línea vacía o nuevo "#"
            m = fh + 1
            maquinas_lista: List[str] = []
            while m < total:
                t = lineas[m].strip()

                if t == "":
                    m += 1
                    continue

                # Si es texto de interfaz (Resumen de unidades, ×, Cerrar) -> fin de bloque
                if _es_texto_control_maquinas(t):
                    m += 1
                    break

                if t.startswith("#"):
                    break

                maquinas_lista.append(t)
                m += 1

            maquinas = " / ".join(maquinas_lista)

            # Si el header traía mejor descripción de tipo, lo usamos
            tipo = tipo_desde_header if tipo_desde_header else ""

            registros.append(
                {
                    "nro_parte": nro_parte,
                    "fecha_hora": fecha_hora,
                    "direccion_distrito": direccion_distrito,
                    "tipo": tipo,
                    "estado": estado,
                    "maquinas": maquinas,
                }
            )

            i = m
            continue

        i += 1

    return registros


# -----------------------------------------------------------
# FUNCIÓN PRINCIPAL: intenta ambos formatos
# -----------------------------------------------------------

def extraer_registros(html: str) -> List[Dict[str, str]]:
    lineas = _obtener_lineas(html)

    # 1) Intentar formato lista
    registros_lista = _extraer_registros_lista(lineas)
    if registros_lista:
        print(f"Registros extraídos (formato lista): {len(registros_lista)}")
        return registros_lista

    # 2) Si no encontró nada, intentar formato bloques "#1 / N° Parte"
    registros_bloques = _extraer_registros_bloques(lineas)
    print(f"Registros extraídos (formato bloques): {len(registros_bloques)}")
    return registros_bloques
