from typing import Dict, List, Any, Optional


def get_all_tools() -> List[Dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "listar_categorias",
                "description": "Obtén todas las categorías de maquinaria disponibles con un resumen de las máquinas en cada una.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "obtener_categoria",
                "description": "Obtén todos los detalles de una categoría específica con especificaciones, precios, FAQ, etc.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nombre": {
                            "type": "string",
                            "description": "Nombre exacto de la categoría. Ej: 'Excavadoras', 'Compactación'.",
                        }
                    },
                    "required": ["nombre"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "buscar_maquinaria",
                "description": "Busca maquinaria por palabra clave en nombre, nombre común, sinónimos, o descripción. Ej: 'excavadora', 'compactar', 'grúa', 'orugas'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "termino": {
                            "type": "string",
                            "description": "Término de búsqueda (palabra clave).",
                        }
                    },
                    "required": ["termino"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "detalle_maquinaria",
                "description": "Obtén la ficha completa de una máquina: especificaciones técnicas, precios de renta, casos de uso, preguntas frecuentes y reglas de negocio.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nombre": {
                            "type": "string",
                            "description": "Nombre exacto de la máquina. Ej: 'Excavadora Hidráulica de Orugas', 'Bulldozer', 'Rodillo Vibratorio'.",
                        }
                    },
                    "required": ["nombre"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "listar_proyectos",
                "description": "Obtén combinaciones típicas de maquinaria para proyectos comunes de construcción, minería, etc.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "obtener_proyecto",
                "description": "Obtén maquinaria recomendada para un proyecto específico (construcción, excavación, movimiento de tierra, etc.).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nombre": {
                            "type": "string",
                            "description": "Nombre del proyecto. Ej: 'Excavación de cimentación', 'Movimiento de tierra masivo'.",
                        }
                    },
                    "required": ["nombre"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "query_maquinaria",
                "description": "Haz una pregunta en lenguaje natural sobre maquinaria pesada. El sistema buscará en la base de conocimiento documental para responder. Úsala cuando la pregunta sea compleja, comparativa o requiera análisis entre varias máquinas.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Pregunta en lenguaje natural del usuario.",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Número de fragmentos a recuperar (default: 5, max: 20).",
                            "default": 5,
                        },
                    },
                    "required": ["question"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "calcular_costo_renta",
                "description": "Calcula el costo de renta de una máquina específica por una cantidad de días, aplicando descuentos progresivos (3+ días 5%, 7+ días 10%, 14+ días 15%, 30+ días 20%).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "maquina": {
                            "type": "string",
                            "description": "Nombre o sinónimo de la máquina. Ej: 'Excavadora Hidráulica de Orugas', 'Bulldozer', 'retro'.",
                        },
                        "dias": {
                            "type": "integer",
                            "description": "Cantidad de días de renta.",
                            "minimum": 1,
                        },
                        "cantidad": {
                            "type": "integer",
                            "description": "Cantidad de unidades (default: 1).",
                            "default": 1,
                        },
                    },
                    "required": ["maquina", "dias"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "verificar_disponibilidad",
                "description": "Verifica si una máquina está disponible para renta en un rango de fechas específico. Consulta el calendario de disponibilidad en la base de datos.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "maquina": {
                            "type": "string",
                            "description": "Nombre o sinónimo de la máquina.",
                        },
                        "fecha_inicio": {
                            "type": "string",
                            "description": "Fecha de inicio en formato YYYY-MM-DD. Ej: '2026-06-15'.",
                        },
                        "fecha_fin": {
                            "type": "string",
                            "description": "Fecha de fin en formato YYYY-MM-DD. Ej: '2026-06-20'.",
                        },
                    },
                    "required": ["maquina", "fecha_inicio", "fecha_fin"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "recomendar_por_trabajo",
                "description": "Recomienda maquinaria para un tipo de trabajo específico (cimentación, excavación, movimiento de tierra, pavimentación, etc.). Opcionalmente considera un presupuesto para estimar días de renta posibles.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tipo_trabajo": {
                            "type": "string",
                            "description": "Tipo de trabajo o proyecto. Ej: 'excavación de cimentación', 'movimiento de tierra', 'pavimentación'.",
                        },
                        "presupuesto": {
                            "type": "number",
                            "description": "Presupuesto disponible en MXN (opcional).",
                            "default": None,
                        },
                    },
                    "required": ["tipo_trabajo"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "comparar_maquinas",
                "description": "Compara dos o más máquinas lado a lado mostrando sus especificaciones técnicas, precios, casos de uso, recomendaciones y no recomendaciones.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nombres": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Lista de nombres de máquinas a comparar (mínimo 2). Ej: ['Excavadora Hidráulica de Orugas', 'Miniexcavadora'].",
                        }
                    },
                    "required": ["nombres"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "calcular_costo_proyecto",
                "description": "Calcula el costo total de un proyecto que involucra múltiples máquinas por una cantidad de días. Aplica descuentos progresivos y devuelve desglose detallado.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "maquinas": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "nombre": {"type": "string", "description": "Nombre de la máquina"},
                                    "cantidad": {"type": "integer", "description": "Cantidad de unidades", "default": 1},
                                },
                                "required": ["nombre"],
                            },
                            "description": "Lista de máquinas con nombre y cantidad. Ej: [{'nombre': 'Excavadora...', 'cantidad': 2}, {'nombre': 'Bulldozer', 'cantidad': 1}].",
                        },
                        "dias": {
                            "type": "integer",
                            "description": "Cantidad de días de renta para todas las máquinas.",
                        },
                    },
                    "required": ["maquinas", "dias"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "registrar_solicitud",
                "description": "Registra una solicitud de renta formal. IMPORTANTE: Solo úsala cuando el usuario YA haya proporcionado su nombre real y contacto. Si no los ha dado, primero pregúntalos.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cliente": {
                            "type": "string",
                            "description": "Nombre del cliente o empresa.",
                        },
                        "contacto": {
                            "type": "string",
                            "description": "Teléfono, email u otro medio de contacto del cliente.",
                        },
                        "maquinas": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "nombre": {"type": "string", "description": "Nombre de la máquina"},
                                    "cantidad": {"type": "integer", "description": "Cantidad de unidades", "default": 1},
                                },
                                "required": ["nombre"],
                            },
                            "description": "Lista de máquinas a rentar.",
                        },
                        "fecha_inicio": {
                            "type": "string",
                            "description": "Fecha de inicio en formato YYYY-MM-DD.",
                        },
                        "fecha_fin": {
                            "type": "string",
                            "description": "Fecha de fin en formato YYYY-MM-DD.",
                        },
                    },
                    "required": ["cliente", "contacto", "maquinas", "fecha_inicio", "fecha_fin"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "generar_cotizacion",
                "description": "Genera una cotización formal con folio único. IMPORTANTE: Solo úsala cuando el usuario YA haya proporcionado su nombre real y contacto. Si no los ha dado, primero pregúntalos.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cliente": {
                            "type": "string",
                            "description": "Nombre del cliente o empresa.",
                        },
                        "contacto": {
                            "type": "string",
                            "description": "Teléfono, email u otro medio de contacto.",
                        },
                        "maquinas": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "nombre": {"type": "string", "description": "Nombre de la máquina"},
                                    "cantidad": {"type": "integer", "description": "Cantidad de unidades", "default": 1},
                                },
                                "required": ["nombre"],
                            },
                            "description": "Lista de máquinas a cotizar.",
                        },
                        "dias": {
                            "type": "integer",
                            "description": "Cantidad de días de renta.",
                        },
                    },
                    "required": ["cliente", "contacto", "maquinas", "dias"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "consultar_mis_cotizaciones",
                "description": "Consulta el HISTORIAL de cotizaciones del usuario autenticado. Devuelve folio, máquinas, días, total y vigencia. NO recibe parámetros porque identifica al usuario automáticamente.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "consultar_mis_solicitudes",
                "description": "Consulta el HISTORIAL de solicitudes de renta del usuario autenticado. Devuelve folio, máquinas, fechas, estado. NO recibe parámetros porque identifica al usuario automáticamente.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "validar_fecha",
                "description": "VALIDA si una fecha es válida para renta (debe ser al menos 1 día después de hoy). Usa esta herramienta SIEMPRE que tengas dudas sobre una fecha o antes de llamar a registrar_solicitud. Esta herramienta te dirá la fecha de hoy y si la fecha que consultas es válida.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fecha": {
                            "type": "string",
                            "description": "Fecha a validar en formato YYYY-MM-DD. Ej: '2026-07-22'.",
                        }
                    },
                    "required": ["fecha"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "agregar_al_carrito",
                "description": "Agrega una máquina al carrito del usuario con duración y fechas. DESPUÉS de recomendar máquinas y que el usuario acepte, usa esta herramienta para ponerlas en su carrito. El usuario podrá revisar y confirmar la compra después.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "maquina": {
                            "type": "string",
                            "description": "Nombre de la máquina a agregar. Ej: 'Excavadora Hidráulica de Orugas'.",
                        },
                        "duration": {
                            "type": "integer",
                            "description": "Cantidad de tiempo de renta.",
                            "minimum": 1,
                        },
                        "duration_unit": {
                            "type": "string",
                            "enum": ["dias", "semanas", "meses"],
                            "description": "Unidad de duración (default: dias).",
                            "default": "dias",
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Fecha de inicio en formato YYYY-MM-DD (opcional).",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "Fecha de fin en formato YYYY-MM-DD (opcional).",
                        },
                        "cantidad": {
                            "type": "integer",
                            "description": "Cantidad de unidades (default: 1).",
                            "default": 1,
                        },
                    },
                    "required": ["maquina", "duration"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "ver_carrito",
                "description": "Muestra el contenido actual del carrito del usuario: máquinas, duración, fechas, precios y subtotal. No recibe parámetros.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "quitar_del_carrito",
                "description": "Elimina una máquina del carrito del usuario. Úsala cuando el usuario diga 'esa no la quiero' o 'quita esa máquina'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "maquina": {
                            "type": "string",
                            "description": "Nombre de la máquina a quitar. Ej: 'Bulldozer / Topadora'. Opcional si se provee item_id.",
                        },
                    },
                    "required": [],
                },
            },
        },
    ]


def get_tool_names() -> List[str]:
    return [t["function"]["name"] for t in get_all_tools()]


def get_tool_schema(name: str) -> Optional[Dict[str, Any]]:
    for t in get_all_tools():
        if t["function"]["name"] == name:
            return t
    return None


TOOL_FUNCTIONS_MAP = {
    "listar_categorias": "listar_categorias_fallback",
    "obtener_categoria": "obtener_categoria_fallback",
    "buscar_maquinaria": "buscar_maquinaria_fallback",
    "detalle_maquinaria": "detalle_maquinaria_fallback",
    "listar_proyectos": "listar_proyectos_fallback",
    "obtener_proyecto": "obtener_proyecto_fallback",
    "query_maquinaria": "query_maquinaria_backend",
    "calcular_costo_renta": "exec_calcular_costo_renta",
    "verificar_disponibilidad": "exec_verificar_disponibilidad",
    "recomendar_por_trabajo": "exec_recomendar_por_trabajo",
    "comparar_maquinas": "exec_comparar_maquinas",
    "calcular_costo_proyecto": "exec_calcular_costo_proyecto",
    "registrar_solicitud": "exec_registrar_solicitud",
    "generar_cotizacion": "exec_generar_cotizacion",
    "consultar_mis_cotizaciones": "exec_consultar_mis_cotizaciones",
    "consultar_mis_solicitudes": "exec_consultar_mis_solicitudes",
}
