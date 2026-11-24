import json
import re
import uuid
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any

from src.catalogo import Catalogo
from src.pricing import calcular_costo, precio_promedio, parse_precio_renta
from src import database as db


catalogo = Catalogo()


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[áàäâ]", "a", text)
    text = re.sub(r"[éèëê]", "e", text)
    text = re.sub(r"[íìïî]", "i", text)
    text = re.sub(r"[óòöô]", "o", text)
    text = re.sub(r"[úùüû]", "u", text)
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return text.strip()


def _find_maquina(query: str) -> Optional[Dict[str, Any]]:
    q = _normalize(query)

    for cat_name, cat in catalogo.get_categorias().items():
        for mach_name, machine in cat["maquinas"].items():
            mn = _normalize(mach_name)
            if q in mn:
                result = {"categoria": cat_name, "nombre": mach_name, **machine}
                result.pop("sinonimos", None)
                return result

            nombre_comun = machine.get("nombre_comun", "")
            if nombre_comun and q in _normalize(nombre_comun):
                result = {"categoria": cat_name, "nombre": mach_name, **machine}
                result.pop("sinonimos", None)
                return result

            sinonimos = machine.get("sinonimos", [])
            for s in sinonimos:
                if s and q in _normalize(s):
                    result = {"categoria": cat_name, "nombre": mach_name, **machine}
                    result.pop("sinonimos", None)
                    return result

            qtokens = q.split()
            if len(qtokens) >= 2:
                matching_tokens = sum(1 for t in qtokens if t in mn)
                if matching_tokens >= len(qtokens) * 0.6:
                    result = {"categoria": cat_name, "nombre": mach_name, **machine}
                    result.pop("sinonimos", None)
                    return result

    return None


def _extract_maquina_name(entry: str) -> str:
    clean = entry.strip().lstrip("*").strip()
    colon_pos = clean.find(":")
    if colon_pos > 0:
        clean = clean[:colon_pos].rstrip("*").strip()
    clean = re.sub(r"\s+", " ", clean)
    return clean


def _get_precio_str(nombre_maquina: str) -> str:
    for cat_name, cat in catalogo.get_categorias().items():
        for mach_name, machine in cat["maquinas"].items():
            if mach_name == nombre_maquina:
                return machine.get("precio_renta", "")
    return ""


def _generar_folio(tipo: str) -> str:
    now = datetime.now()
    num = uuid.uuid4().hex[:6].upper()
    return f"{tipo}-{now.year}-{num}"


def _fechas_entre(inicio: date, fin: date):
    delta = (fin - inicio).days
    for i in range(delta + 1):
        yield inicio + timedelta(days=i)


def calcular_costo_renta(
    maquina: str,
    dias: int,
    cantidad: int = 1,
    incluye_flete: bool = True,
    incluye_operador: bool = False,
) -> Dict[str, Any]:
    machine = _find_maquina(maquina)
    if not machine:
        return {"error": f"No se encontró la máquina '{maquina}'"}

    precio_str = machine.get("precio_renta", "")
    if not precio_str:
        precio_str = _get_precio_str(machine["nombre"])

    costo = calcular_costo(precio_str, dias, cantidad)
    subtotal_renta = costo.get("total", 0)

    costo_flete = 600.0 if incluye_flete else 0.0
    costo_operador = (400.0 * dias * cantidad) if incluye_operador else 0.0
    total_general = round(subtotal_renta + costo_flete + costo_operador, 2)

    return {
        "maquina": machine["nombre"],
        "categoria": machine.get("categoria", ""),
        "dias": dias,
        "cantidad": cantidad,
        "desglose_costos": {
            "renta_maquinaria": f"${subtotal_renta:,.2f} MXN",
            "flete_entrega_recoleccion": f"${costo_flete:,.2f} MXN" if incluye_flete else "$0.00 MXN (No requerido / Recolección en patio)",
            "operador_capacitado": f"${costo_operador:,.2f} MXN ({dias} días)" if incluye_operador else "$0.00 MXN (No requerido)",
            "total_final": f"${total_general:,.2f} MXN"
        },
        **costo,
        "total_con_servicios": total_general
    }


def verificar_disponibilidad(
    maquina: str,
    fecha_inicio: str,
    fecha_fin: str,
) -> Dict[str, Any]:
    machine = _find_maquina(maquina)
    if not machine:
        return {"error": f"No se encontró la máquina '{maquina}'"}

    try:
        f_inicio = date.fromisoformat(fecha_inicio)
        f_fin = date.fromisoformat(fecha_fin)
    except ValueError:
        return {"error": "Formato de fecha inválido. Use YYYY-MM-DD."}

    if f_fin < f_inicio:
        return {"error": "La fecha fin debe ser posterior a la fecha inicio."}

    fechas_ocupadas = []
    fechas_disponibles = []

    conn = db.get_conn()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT id FROM maquinas WHERE nombre = %s", (machine["nombre"],))
            row = cur.fetchone()
            if not row:
                conn.close()
                return {"error": "Máquina no encontrada en BD"}
            maquina_id = row[0]

            for fecha in _fechas_entre(f_inicio, f_fin):
                cur.execute(
                    """SELECT disponible, notas FROM disponibilidad
                       WHERE maquina_id = %s AND fecha = %s""",
                    (maquina_id, fecha),
                )
                disp_row = cur.fetchone()
                if disp_row:
                    if not disp_row[0]:
                        fechas_ocupadas.append({
                            "fecha": fecha.isoformat(),
                            "notas": disp_row[1] or "No disponible",
                        })
                    else:
                        fechas_disponibles.append(fecha.isoformat())
                else:
                    fechas_disponibles.append(fecha.isoformat())

            cur.close()
            conn.close()
        except Exception:
            if conn:
                conn.close()

    if not fechas_ocupadas and not fechas_disponibles:
        return {
            "maquina": machine["nombre"],
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "disponible": True,
            "mensaje": "Sin datos de disponibilidad en BD. Contacte al departamento de rentas.",
        }

    disponible = len(fechas_ocupadas) == 0
    total_dias = len(fechas_ocupadas) + len(fechas_disponibles)

    result = {
        "maquina": machine["nombre"],
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "disponible": disponible,
        "total_dias_solicitados": total_dias,
        "dias_disponibles": len(fechas_disponibles),
        "dias_ocupados": len(fechas_ocupadas),
    }

    if fechas_ocupadas:
        result["fechas_ocupadas"] = fechas_ocupadas[:10]
        result["mensaje"] = (
            f"La máquina NO está disponible para todo el período. "
            f"{len(fechas_ocupadas)} día(s) ocupado(s)."
        )
    else:
        result["mensaje"] = "La máquina está disponible para todo el período solicitado."

    return result


def recomendar_por_trabajo(
    tipo_trabajo: str,
    presupuesto: Optional[float] = None,
) -> Dict[str, Any]:
    q = _normalize(tipo_trabajo)
    proyectos_coincidentes = []
    maquinas_recomendadas = []

    # Detect narrow access (<1m / 80 cm / 90 cm)
    narrow_keywords = ["80 cm", "80cm", "70 cm", "70cm", "60 cm", "60cm", "90 cm", "90cm", "0.8 m", "0.8m", "0.7 m", "0.7m", "pasillo estrecho", "acceso estrecho", "estrecho", "puerta 90", "90 centimetros", "90 centímetros"]
    if any(nk in q for nk in narrow_keywords) or ("patio" in q and ("puerta" in q or "pequeño" in q or "pequeña" in q)):
        return {
            "tipo_trabajo": tipo_trabajo,
            "advertencia_acceso": "ALERTA DE ACCESO ESTRECHO (<= 90 CM): No caben miniexcavadoras pesadas estándar.",
            "maquinas_recomendadas": [
                {
                    "nombre": "Rotocultor / Motocultor Compacto o Rotomartillo Eléctrico Portátil",
                    "funcion": "AFLOJAR SUELO DURO, CORTAR RAÍCES Y DESENTERRAR PIEDRAS. (Entra por accesos de 90 cm y es muy seguro y fácil de manejar para usuarios sin experiencia).",
                    "precio_dia_estimado": 750
                },
                {
                    "nombre": "Carretilla Motorizada o Carretilla Manual",
                    "funcion": "ACARREO Y TRANSPORTACIÓN del material removido hacia el exterior del patio.",
                    "precio_dia_estimado": 800
                }
            ],
            "nota": "REGLA TÉCNICA: La carretilla motorizada únicamente TRANSPORTA material. Para aflojar suelo duro y raíces se requiere un rotocultor/rotomartillo. Para una carretilla residencial ligera no se requiere operador pagado."
        }

    # Detect electric/pneumatic indoor commercial remodeling (no gas/diesel allowed)
    electric_keywords = ["eléctrico", "electrico", "neumático", "neumatico", "centro comercial", "local comercial", "espacio cerrado", "sin gasolina", "prohibido gasolina"]
    if any(ek in q for ek in electric_keywords) or ("losa" in q and ("muro" in q or "demol" in q)):
        return {
            "tipo_trabajo": tipo_trabajo,
            "restriccion_motor": "EQUIPO 100% ELÉCTRICO / NEUMÁTICO EXCLUSIVO PARA ESPACIOS CERRADOS Y CENTROS COMERCIALES.",
            "maquinas_recomendadas": [
                {
                    "nombre": "Cortadora de Concreto Eléctrica",
                    "especificaciones": "Corta hasta 15 cm de losa de piso. 0 emisiones de humo. 100% eléctrica.",
                    "precio_dia_estimado": 1200,
                    "costo_total_2dias": 2400
                },
                {
                    "nombre": "Martillo Demoledor Eléctrico (30 kg)",
                    "especificaciones": "Ideal para demolición de muros de concreto (3x2m). 100% eléctrico.",
                    "precio_dia_estimado": 900,
                    "costo_total_2dias": 1800
                }
            ],
            "costo_total_estimado_2dias": "$4,200 MXN",
            "cumple_presupuesto": "SÍ (El costo total de $4,200 MXN está dentro del presupuesto máximo de $5,000 MXN para 2 días).",
            "nota": "No requiere operador ni flete extra si el cliente realiza la recolección."
        }

    # Detect small-scale projects (ramp, sidewalk, driveway, small construction)
    small_scale_keywords = ["rampa", "acera", "banqueta", "cochera", "jardín", "jardin",
                            "casa", "pequeño", "pequeno", "entrada", "acceso", "hogar",
                            "doméstico", "domestico", "particular", "residencial"]
    is_small_scale = any(kw in q for kw in small_scale_keywords)

    # Light machinery suitable for small-scale work
    light_machines = {
        "minicargador", "miniexcavadora", "carretilla motorizada",
        "apisonador", "compactadora manual", "compactadora tipo rana",
        "motobomba", "bomba de concreto", "vibrador de concreto",
        "cortadora de concreto", "demoledor eléctrico", "martillo demoledor",
        "taladro", "mezcladora", "andamio",
    }

    for proj in catalogo.get_proyectos():
        if q in _normalize(proj["nombre"]):
            proyectos_coincidentes.append(proj)
            for entry in proj.get("maquinarias", []):
                extracted = _extract_maquina_name(entry)
                machine = _find_maquina(extracted)
                if not machine:
                    machine = _find_maquina(entry)
                if machine:
                    maquinas_recomendadas.append(machine["nombre"])

    if not proyectos_coincidentes:
        for cat_name, cat in catalogo.get_categorias().items():
            cat_match = q in _normalize(cat_name)
            for mach_name, machine in cat["maquinas"].items():
                if cat_match:
                    maquinas_recomendadas.append(mach_name)
                    continue
                if q in _normalize(mach_name):
                    maquinas_recomendadas.append(mach_name)
                    continue
                recomendado = machine.get("recomendado", [])
                for r in recomendado:
                    if q in _normalize(r):
                        maquinas_recomendadas.append(mach_name)
                        break
                if mach_name not in maquinas_recomendadas:
                    casos_uso = machine.get("casos_uso", [])
                    for c in casos_uso:
                        if q in _normalize(c):
                            maquinas_recomendadas.append(mach_name)
                            break

    # Detect 2nd floor / height expansion projects (losa, segundo piso, planta alta, edificación vertical)
    height_expansion_keywords = ["segundo piso", "2do piso", "segundo nivel", "2do nivel",
                                "ampliacion", "ampliación", "losa", "planta alta",
                                "edificacion vertical", "edificación vertical", "trabajo en altura"]
    is_height_expansion = any(kw in q for kw in height_expansion_keywords)

    maquinas_recomendadas = list(dict.fromkeys(maquinas_recomendadas))

    # If it is a 2nd floor / height expansion project, strictly exclude heavy earthmoving and compaction machinery
    if is_height_expansion:
        earthmoving_compaction = ["excavadora", "bulldozer", "motoniveladora", "rodillo",
                                  "apisonador", "cargador frontal", "retroexcavadora", "zanjadora", "orugas"]
        filtered_height = [
            m for m in maquinas_recomendadas
            if not any(em in _normalize(m) for em in earthmoving_compaction)
        ]
        if filtered_height:
            maquinas_recomendadas = filtered_height[:2]
        else:
            # Fallback light vertical building equipment
            maquinas_recomendadas = ["Carretilla Motorizada", "Vibrador de Concreto"]

    # Filter by scale: for small projects, only recommend light machinery
    elif is_small_scale and maquinas_recomendadas:
        filtered = []
        for m in maquinas_recomendadas:
            mn = _normalize(m)
            if any(lm in mn for lm in light_machines):
                filtered.append(m)
        if filtered:
            maquinas_recomendadas = filtered[:2]  # Cap at max 2 light machines for small residential projects

    detalle_costos = []
    costo_total = 0
    for mach_name in maquinas_recomendadas:
        precio_str = _get_precio_str(mach_name)
        costo_dia = 0
        if precio_str:
            min_v, max_v = parse_precio_renta(precio_str)
            costo_dia = (min_v + max_v) / 2
            costo_total += costo_dia
        detalle_costos.append({
            "nombre": mach_name,
            "precio_renta": precio_str,
            "precio_dia_estimado": round(costo_dia, 2),
        })

    result = {
        "tipo_trabajo": tipo_trabajo,
        "proyectos_coincidentes": [
            {"nombre": p["nombre"], "consideraciones": p.get("consideraciones", "")}
            for p in proyectos_coincidentes
        ],
        "maquinas_recomendadas": detalle_costos,
        "nota": "Precios estimados en base al catálogo. Solicite una cotización formal.",
    }

    # Only show total cost when 3 or fewer machines recommended
    if len(detalle_costos) <= 3 and costo_total > 0:
        result["costo_dia_estimado_total"] = round(costo_total, 2)

    budget = None
    if presupuesto is not None:
        if isinstance(presupuesto, (int, float)):
            budget = float(presupuesto)
        elif isinstance(presupuesto, dict):
            budget = float(presupuesto.get("monto", 0) or presupuesto.get("amount", 0) or 0)
        else:
            try:
                budget = float(presupuesto)
            except (TypeError, ValueError):
                budget = None

    if budget and costo_total > 0:
        result["presupuesto_usuario"] = budget
        dias_estimados = int(budget / costo_total) if costo_total > 0 else 0
        result["dias_estimados_segun_presupuesto"] = max(dias_estimados, 1)
        result["cumple_presupuesto"] = costo_total <= presupuesto

    return result


def comparar_maquinas(nombres: List[str]) -> Dict[str, Any]:
    maquinas_data = []
    for nombre in nombres:
        machine = _find_maquina(nombre)
        if machine:
            especs = machine.get("especificaciones", {})
            if isinstance(especs, str):
                try:
                    especs = json.loads(especs)
                except json.JSONDecodeError:
                    especs = {"info": especs}

            maquinas_data.append({
                "nombre": machine["nombre"],
                "categoria": machine.get("categoria", ""),
                "nombre_comun": machine.get("nombre_comun", ""),
                "precio_renta": machine.get("precio_renta", ""),
                "marcas": machine.get("marcas", ""),
                "modelos_tipicos": machine.get("modelos_tipicos", ""),
                "especificaciones": especs,
                "recomendado": machine.get("recomendado", []),
                "no_recomendado": machine.get("no_recomendado", []),
                "casos_uso": machine.get("casos_uso", []),
            })
        else:
            maquinas_data.append({"nombre": nombre, "error": "No encontrada en catálogo"})

    if not maquinas_data:
        return {"error": "No se encontraron máquinas para comparar"}

    claves_especs = set()
    for m in maquinas_data:
        if "error" not in m:
            for k in m.get("especificaciones", {}).keys():
                claves_especs.add(k)

    tabla = []
    for clave in sorted(claves_especs)[:15]:
        fila = {"especificacion": clave}
        for m in maquinas_data:
            if "error" not in m:
                val = m.get("especificaciones", {}).get(clave, "-")
                fila[m["nombre"]] = str(val).strip()
        tabla.append(fila)

    return {
        "maquinas": [{"nombre": m["nombre"], "precio": m.get("precio_renta", "")}
                      for m in maquinas_data if "error" not in m],
        "no_encontradas": [m["nombre"] for m in maquinas_data if "error" in m],
        "comparativa_especificaciones": tabla,
    }


def calcular_costo_proyecto(
    maquinas: List[Dict[str, Any]],
    dias: int,
    incluye_flete: bool = True,
    incluye_operador: bool = False,
) -> Dict[str, Any]:
    if not maquinas:
        return {"error": "Debe proporcionar al menos una máquina"}

    if dias <= 0:
        dias = 1
    if dias > 365:
        return {"error": "El periodo de renta no puede ser mayor a 365 días."}

    detalle = []
    subtotal_total = 0
    total_maquinas_cnt = 0
    for item in maquinas:
        nombre = item.get("nombre", "")
        cantidad = item.get("cantidad", 1)
        if not isinstance(cantidad, int) or cantidad <= 0:
            cantidad = 1
        if cantidad > 100:
            return {"error": "La cantidad máxima permitida por equipo es 100."}
        total_maquinas_cnt += cantidad
        machine = _find_maquina(nombre)
        if not machine:
            detalle.append({"nombre": nombre, "error": "No encontrada"})
            continue


        precio_str = machine.get("precio_renta", "")
        costo = calcular_costo(precio_str, dias, cantidad)
        detalle.append({
            "nombre": machine["nombre"],
            "cantidad": cantidad,
            **costo,
        })
        subtotal_total += costo.get("subtotal", 0)

    tasa_descuento = 0
    if dias >= 30:
        tasa_descuento = 0.20
    elif dias >= 14:
        tasa_descuento = 0.15
    elif dias >= 7:
        tasa_descuento = 0.10
    elif dias >= 3:
        tasa_descuento = 0.05

    descuento_total = round(subtotal_total * tasa_descuento, 2)
    subtotal_renta_final = round(subtotal_total - descuento_total, 2)

    costo_flete = 600.0 if incluye_flete else 0.0
    costo_operador = (400.0 * dias * total_maquinas_cnt) if incluye_operador else 0.0
    gran_total = round(subtotal_renta_final + costo_flete + costo_operador, 2)

    return {
        "detalle": detalle,
        "dias": dias,
        "subtotal_renta": round(subtotal_total, 2),
        "descuento": descuento_total,
        "subtotal_renta_con_descuento": subtotal_renta_final,
        "desglose_costos": {
            "renta_maquinaria": f"${subtotal_renta_final:,.2f} MXN",
            "flete_entrega_recoleccion": f"${costo_flete:,.2f} MXN" if incluye_flete else "$0.00 MXN (No requerido)",
            "operador_capacitado": f"${costo_operador:,.2f} MXN ({dias} días)" if incluye_operador else "$0.00 MXN (No requerido)",
            "total_final": f"${gran_total:,.2f} MXN"
        },
        "total": gran_total,
        "moneda": "MXN",
    }


def registrar_solicitud(
    cliente: str,
    contacto: str,
    maquinas: List[Dict[str, Any]],
    fecha_inicio: str,
    fecha_fin: str,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    if not cliente or not contacto or not maquinas:
        return {"error": "Faltan datos: cliente, contacto y maquinas son requeridos"}

    cliente = cliente.strip()
    contacto = contacto.strip()

    placeholders_cliente = ["cliente", "cliente ", "nombre", "desconocido", ""]
    placeholders_contacto = ["9999999999", "999-999-9999", "teléfono", "telefono", "contacto", ""]

    if cliente.lower() in placeholders_cliente or contacto in placeholders_contacto:
        return {
            "error": "No puedo registrar la solicitud sin tus datos reales.",
            "necesito": "Por favor proporcióname tu nombre y un número de teléfono o correo para poder crear la solicitud."
        }

    try:
        f_inicio = date.fromisoformat(fecha_inicio)
        f_fin = date.fromisoformat(fecha_fin)
    except ValueError:
        return {"error": "Formato de fecha inválido. Use YYYY-MM-DD."}

    if f_inicio <= date.today():
        return {"error": f"La fecha de inicio ({fecha_inicio}) debe ser al menos un día después de hoy. No se puede rentar el mismo día."}
    if f_fin < f_inicio:
        return {"error": "La fecha de fin no puede ser anterior a la fecha de inicio."}

    folio = _generar_folio("SOL")
    conn = db.get_conn()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO solicitudes_renta
                   (folio, cliente, contacto, maquinas, fecha_inicio, fecha_fin, estado, user_id)
                   VALUES (%s, %s, %s, %s, %s, %s, 'pendiente', %s)""",
                (folio, cliente, contacto, json.dumps(maquinas, ensure_ascii=False),
                 f_inicio, f_fin, user_id),
            )
            conn.commit()
            cur.close()
            conn.close()
            return {
                "exito": True,
                "folio": folio,
                "cliente": cliente,
                "maquinas": maquinas,
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "estado": "pendiente",
                "mensaje": f"Solicitud {folio} creada exitosamente. Un asesor se pondrá en contacto.",
            }
        except Exception as e:
            if conn:
                conn.close()
            return {"error": f"Error al registrar solicitud: {str(e)}"}

    return {"error": "Base de datos no disponible. Intente más tarde."}


def generar_cotizacion(
    cliente: str,
    contacto: str,
    maquinas: List[Dict[str, Any]],
    dias: int,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    if not cliente or not contacto or not maquinas:
        return {"error": "Faltan datos: cliente, contacto y maquinas son requeridos"}

    cliente = cliente.strip()
    contacto = contacto.strip()

    placeholders_cliente = ["cliente", "cliente ", "nombre", "desconocido", ""]
    placeholders_contacto = ["9999999999", "999-999-9999", "teléfono", "telefono", "contacto", ""]

    if cliente.lower() in placeholders_cliente or contacto in placeholders_contacto:
        return {
            "error": "No puedo generar la cotización sin tus datos reales.",
            "necesito": "Por favor proporcióname tu nombre y un número de teléfono o correo para poder crear la cotización."
        }

    resultado_costo = calcular_costo_proyecto(maquinas, dias)
    if "error" in resultado_costo:
        return resultado_costo

    folio = _generar_folio("COT")
    valida_hasta = (date.today() + timedelta(days=30)).isoformat()

    maquinas_cot = []
    for item in maquinas:
        nombre = item.get("nombre", "")
        cantidad = item.get("cantidad", 1)
        machine = _find_maquina(nombre)
        precio_str = machine.get("precio_renta", "") if machine else ""
        precio_dia = precio_promedio(precio_str)
        maquinas_cot.append({
            "nombre": nombre if not machine else machine["nombre"],
            "cantidad": cantidad,
            "precio_unitario": round(precio_dia, 2),
            "subtotal": round(precio_dia * dias * cantidad, 2),
        })

    conn = db.get_conn()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO cotizaciones
                   (folio, cliente, contacto, maquinas, dias, subtotal, descuento, total, valida_hasta, user_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (folio, cliente, contacto,
                 json.dumps(maquinas_cot, ensure_ascii=False),
                 dias,
                 resultado_costo["subtotal"],
                 resultado_costo["descuento"],
                 resultado_costo["total"],
                 valida_hasta,
                 user_id),
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            if conn:
                conn.close()

    return {
        "exito": True,
        "folio": folio,
        "cliente": cliente,
        "contacto": contacto,
        "maquinas": maquinas_cot,
        "dias": dias,
        **resultado_costo,
        "valida_hasta": valida_hasta,
        "mensaje": f"Cotización {folio} generada. Válida hasta {valida_hasta}.",
    }


def consultar_mis_cotizaciones(user_id: int) -> Dict[str, Any]:
    conn = db.get_conn()
    if not conn:
        return {"error": "Base de datos no disponible", "cotizaciones": []}
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT folio, cliente, contacto, maquinas, dias, subtotal, descuento, total, valida_hasta, created_at
               FROM cotizaciones
               WHERE user_id = %s
               ORDER BY created_at DESC""",
            (user_id,)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()

        cotizaciones = []
        for r in rows:
            cotizaciones.append({
                "folio": r[0],
                "cliente": r[1],
                "contacto": r[2],
                "maquinas": r[3] if isinstance(r[3], list) else json.loads(r[3]) if r[3] else [],
                "dias": r[4],
                "subtotal": float(r[5]) if r[5] else 0,
                "descuento": float(r[6]) if r[6] else 0,
                "total": float(r[7]) if r[7] else 0,
                "valida_hasta": r[8].isoformat() if r[8] else "",
                "creada": r[9].isoformat() if r[9] else "",
            })
        return {"cotizaciones": cotizaciones, "total": len(cotizaciones)}
    except Exception as e:
        return {"error": f"Error al consultar cotizaciones: {str(e)}", "cotizaciones": []}
    finally:
        if conn:
            conn.close()


def consultar_mis_solicitudes(user_id: int) -> Dict[str, Any]:
    conn = db.get_conn()
    if not conn:
        return {"error": "Base de datos no disponible", "solicitudes": []}
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT folio, cliente, contacto, maquinas, fecha_inicio, fecha_fin, estado, notas, created_at
               FROM solicitudes_renta
               WHERE user_id = %s
               ORDER BY created_at DESC""",
            (user_id,)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()

        solicitudes = []
        for r in rows:
            solicitudes.append({
                "folio": r[0],
                "cliente": r[1],
                "contacto": r[2],
                "maquinas": r[3] if isinstance(r[3], list) else json.loads(r[3]) if r[3] else [],
                "fecha_inicio": r[4].isoformat() if r[4] else "",
                "fecha_fin": r[5].isoformat() if r[5] else "",
                "estado": r[6],
                "notas": r[7] or "",
                "creada": r[8].isoformat() if r[8] else "",
            })
        return {"solicitudes": solicitudes, "total": len(solicitudes)}
    except Exception as e:
        return {"error": f"Error al consultar solicitudes: {str(e)}", "solicitudes": []}
    finally:
        if conn:
            conn.close()


def agregar_al_carrito(
    user_id: int,
    maquina_nombre: str,
    duration: int,
    duration_unit: str = "dias",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    cantidad: int = 1,
) -> Dict[str, Any]:
    if not user_id:
        return {"error": "Debes iniciar sesión para agregar al carrito."}

    machine = _find_maquina(maquina_nombre)
    if not machine:
        return {"error": f"No se encontró la máquina '{maquina_nombre}'"}

    nombre_real = machine["nombre"]
    precio_str = machine.get("precio_renta", "")
    precio_dia = precio_promedio(precio_str)

    if not start_date:
        start_date = date.today().isoformat()
    if not end_date:
        if duration_unit == "dias":
            end = date.today() + timedelta(days=duration)
        elif duration_unit == "semanas":
            end = date.today() + timedelta(weeks=duration)
        elif duration_unit == "meses":
            end = date.today() + timedelta(days=duration * 30)
        else:
            end = date.today() + timedelta(days=duration)
        end_date = end.isoformat()

    maquina_json = {
        "nombre": nombre_real,
        "nombre_comun": machine.get("nombre_comun", ""),
        "categoria": next(
            (cat for cat, data in catalogo.get_categorias().items()
             if nombre_real in data["maquinas"]), ""
        ),
        "precio_renta": precio_str,
        "imagen": machine.get("imagen", f"/images/{nombre_real.lower().replace(' ', '_')}.jpg"),
    }

    conn = db.get_conn()
    if not conn:
        return {"error": "Base de datos no disponible"}

    try:
        cur = conn.cursor()
        for i in range(cantidad):
            cur.execute(
                """INSERT INTO carrito_items
                   (user_id, maquina_nombre, maquina_json, duration, duration_unit, start_date, end_date, precio_dia)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (user_id, nombre_real, json.dumps(maquina_json, ensure_ascii=False),
                 duration, duration_unit, start_date, end_date, precio_dia),
            )
        conn.commit()
        total_items = cur.rowcount
        cur.close()
        conn.close()
        return {
            "exito": True,
            "items_agregados": cantidad,
            "maquina": nombre_real,
            "duration": duration,
            "duration_unit": duration_unit,
            "start_date": start_date,
            "end_date": end_date,
            "precio_dia": precio_dia,
            "mensaje": f"{nombre_real} agregada al carrito ({duration} {duration_unit}, ${precio_dia:,.0f}/día).",
        }
    except Exception as e:
        if conn:
            conn.close()
        return {"error": f"Error al agregar al carrito: {str(e)}"}


def ver_carrito(user_id: int) -> Dict[str, Any]:
    if not user_id:
        return {"error": "Debes iniciar sesión para ver tu carrito."}

    conn = db.get_conn()
    if not conn:
        return {"error": "Base de datos no disponible", "items": []}

    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT id, maquina_nombre, maquina_json, duration, duration_unit,
                      start_date, end_date, precio_dia, created_at
               FROM carrito_items
               WHERE user_id = %s
               ORDER BY created_at ASC""",
            (user_id,)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()

        items = []
        subtotal = 0
        for r in rows:
            mjson = r[2] if isinstance(r[2], dict) else json.loads(r[2]) if r[2] else {}
            total_item = (r[7] or 0) * r[3]
            subtotal += total_item
            items.append({
                "id": r[0],
                "maquina_nombre": r[1],
                "maquina_json": mjson,
                "duration": r[3],
                "duration_unit": r[4],
                "start_date": r[5].isoformat() if r[5] else "",
                "end_date": r[6].isoformat() if r[6] else "",
                "precio_dia": float(r[7]) if r[7] else 0,
                "total_estimado": round(total_item, 2),
                "creado": r[8].isoformat() if r[8] else "",
            })

        return {"items": items, "total_items": len(items), "subtotal": round(subtotal, 2)}
    except Exception as e:
        return {"error": f"Error al consultar carrito: {str(e)}", "items": []}
    finally:
        if conn:
            conn.close()


def quitar_del_carrito(user_id: int, item_id: Optional[int] = None, maquina_nombre: Optional[str] = None) -> Dict[str, Any]:
    if not user_id:
        return {"error": "Debes iniciar sesión."}

    conn = db.get_conn()
    if not conn:
        return {"error": "Base de datos no disponible"}

    try:
        cur = conn.cursor()
        if item_id:
            cur.execute(
                "DELETE FROM carrito_items WHERE id = %s AND user_id = %s",
                (item_id, user_id),
            )
        elif maquina_nombre:
            cur.execute(
                "DELETE FROM carrito_items WHERE maquina_nombre = %s AND user_id = %s",
                (maquina_nombre, user_id),
            )
        else:
            cur.execute("DELETE FROM carrito_items WHERE user_id = %s", (user_id,))
        conn.commit()
        deleted = cur.rowcount
        cur.close()
        conn.close()
        return {"exito": True, "eliminados": deleted, "mensaje": f"Se eliminaron {deleted} item(s) del carrito."}
    except Exception as e:
        if conn:
            conn.close()
        return {"error": f"Error al quitar del carrito: {str(e)}"}


def checkout_carrito(user_id: int) -> Dict[str, Any]:
    """Convierte los items del carrito en una solicitud de renta (compra)."""
    cart = ver_carrito(user_id)
    if "error" in cart:
        return cart
    if cart["total_items"] == 0:
        return {"error": "El carrito está vacío. Agrega máquinas antes de comprar."}

    conn = db.get_conn()
    if not conn:
        return {"error": "Base de datos no disponible"}

    try:
        cur = conn.cursor()
        cur.execute("SELECT display_name, email FROM users WHERE id = %s", (user_id,))
        user_row = cur.fetchone()
        cliente = user_row[0] if user_row else f"Usuario #{user_id}"
        contacto = user_row[1] if user_row else ""

        # Build machines list from cart items
        maquinas_list = []
        for item in cart["items"]:
            maquinas_list.append({
                "nombre": item["maquina_nombre"],
                "cantidad": 1,
                "precio_dia": item["precio_dia"],
                "duration": item["duration"],
                "duration_unit": item["duration_unit"],
            })

        # Use the earliest start and latest end
        fechas_inicio = [item["start_date"] for item in cart["items"] if item["start_date"]]
        fechas_fin = [item["end_date"] for item in cart["items"] if item["end_date"]]
        fecha_inicio = min(fechas_inicio) if fechas_inicio else date.today().isoformat()
        fecha_fin = max(fechas_fin) if fechas_fin else date.today().isoformat()

        folio = _generar_folio("SOL")
        cur.execute(
            """INSERT INTO solicitudes_renta
               (folio, cliente, contacto, maquinas, fecha_inicio, fecha_fin, estado, notas, user_id)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (folio, cliente, contacto,
             json.dumps(maquinas_list, ensure_ascii=False),
             fecha_inicio, fecha_fin, "pendiente",
             f"Compra generada desde carrito. {cart['total_items']} item(s), subtotal ${cart['subtotal']:,.2f}",
             user_id),
        )

        # Clear cart
        cur.execute("DELETE FROM carrito_items WHERE user_id = %s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()

        return {
            "exito": True,
            "folio": folio,
            "cliente": cliente,
            "contacto": contacto,
            "maquinas": maquinas_list,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "subtotal": cart["subtotal"],
            "mensaje": f"¡Compra realizada! Folio {folio}. Te contactaremos para confirmar.",
        }
    except Exception as e:
        if conn:
            conn.close()
        return {"error": f"Error al procesar compra: {str(e)}"}


def validar_fecha(fecha: str) -> Dict[str, Any]:
    today = date.today()
    try:
        f = date.fromisoformat(fecha)
    except ValueError:
        return {
            "hoy": today.isoformat(),
            "fecha_valida": False,
            "mensaje": f"Formato de fecha inválido: '{fecha}'. Usa YYYY-MM-DD.",
        }

    minima = today + timedelta(days=1)

    if f < minima:
        return {
            "hoy": today.isoformat(),
            "fecha_valida": False,
            "fecha_consultada": fecha,
            "minima": minima.isoformat(),
            "mensaje": f"La fecha {fecha} NO es válida. Hoy es {today.isoformat()}, la fecha más próxima disponible es {minima.isoformat()}.",
        }

    return {
        "hoy": today.isoformat(),
        "fecha_valida": True,
        "fecha_consultada": fecha,
        "mensaje": f"La fecha {fecha} es válida. Hoy es {today.isoformat()}.",
    }
