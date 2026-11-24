import re
from typing import Tuple, Dict, Any

PRICE_PATTERN = re.compile(r"\$?([\d,]+)\s*-\s*\$?([\d,]+)")


def parse_precio_renta(precio_str: str) -> Tuple[float, float]:
    if not precio_str:
        return 0.0, 0.0

    match = PRICE_PATTERN.search(precio_str)
    if match:
        precio_min = float(match.group(1).replace(",", ""))
        precio_max = float(match.group(2).replace(",", ""))
        return precio_min, precio_max

    single = re.search(r"\$?([\d,]+)", precio_str)
    if single:
        val = float(single.group(1).replace(",", ""))
        return val, val

    return 0.0, 0.0


def precio_promedio(precio_str: str) -> float:
    min_v, max_v = parse_precio_renta(precio_str)
    if min_v == 0 and max_v == 0:
        return 0.0
    return (min_v + max_v) / 2


def calcular_descuento(dias: int) -> float:
    if dias >= 30:
        return 0.20
    elif dias >= 14:
        return 0.15
    elif dias >= 7:
        return 0.10
    elif dias >= 3:
        return 0.05
    return 0.0


def calcular_costo(
    precio_str: str,
    dias: int,
    cantidad: int = 1,
) -> Dict[str, Any]:
    precio_dia = precio_promedio(precio_str)
    if precio_dia == 0:
        return {"error": "No se pudo determinar el precio de la máquina"}

    subtotal = precio_dia * dias * cantidad
    tasa_descuento = calcular_descuento(dias)
    descuento = round(subtotal * tasa_descuento, 2)
    total = round(subtotal - descuento, 2)

    return {
        "precio_dia": round(precio_dia, 2),
        "dias": dias,
        "cantidad": cantidad,
        "subtotal": round(subtotal, 2),
        "tasa_descuento": tasa_descuento,
        "descuento": descuento,
        "total": total,
        "moneda": "MXN",
    }
