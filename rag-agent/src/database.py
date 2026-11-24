"""
Módulo de conexión a PostgreSQL para el catálogo de maquinaria.

Proporciona funciones para consultar la base de datos directamente
desde los endpoints de la API, como alternativa al parser de markdown.
"""

import json
import re
from typing import Optional, Dict, List, Any

try:
    import psycopg2
    import psycopg2.extras
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

from .config import config


def get_conn():
    if not HAS_PSYCOPG2:
        return None
    try:
        conn = psycopg2.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            dbname=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            connect_timeout=3,
        )
        return conn
    except Exception:
        return None


def db_disponible() -> bool:
    conn = get_conn()
    if conn:
        conn.close()
        return True
    return False


def listar_categorias() -> List[Dict[str, Any]]:
    conn = get_conn()
    if not conn:
        return []
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT c.id, c.nombre,
                   COUNT(m.id)::int AS total_maquinas,
                   JSON_AGG(
                       JSON_BUILD_OBJECT(
                           'nombre', m.nombre,
                           'nombre_comun', m.nombre_comun,
                           'precio_renta', m.precio_renta,
                           'marcas', m.marcas,
                           'modelos_tipicos', m.modelos_tipicos
                       ) ORDER BY m.nombre
                   ) FILTER (WHERE m.id IS NOT NULL) AS maquinas
            FROM categorias c
            LEFT JOIN maquinas m ON m.categoria_id = c.id
            GROUP BY c.id, c.nombre
            ORDER BY c.nombre
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        result = []
        for row in rows:
            d = dict(row)
            if d["maquinas"] is None:
                d["maquinas"] = []
            result.append(d)
        return result
    except Exception:
        return []


def obtener_categoria(nombre: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    if not conn:
        return None
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM categorias WHERE LOWER(nombre) = LOWER(%s)", (nombre,))
        cat = cur.fetchone()
        if not cat:
            cur.close()
            conn.close()
            return None

        cur.execute("""
            SELECT * FROM maquinas
            WHERE categoria_id = %s
            ORDER BY nombre
        """, (cat["id"],))
        machines = cur.fetchall()

        cur.close()
        conn.close()

        result = dict(cat)
        result["maquinas"] = {}
        for m in machines:
            md = dict(m)
            md.pop("id", None)
            md.pop("categoria_id", None)
            md.pop("created_at", None)
            if isinstance(md.get("especificaciones"), dict):
                md["especificaciones"] = md["especificaciones"]
            if isinstance(md.get("preguntas_frecuentes"), list):
                md["preguntas_frecuentes"] = md["preguntas_frecuentes"]
            result["maquinas"][md["nombre"]] = md

        return result
    except Exception:
        return None


def buscar_maquinaria(termino: str) -> List[Dict[str, Any]]:
    conn = get_conn()
    if not conn:
        return []
    try:
        from src.hybrid_search import hybrid_search, rerank
        results = hybrid_search(conn, termino, limit=20)
        results = rerank(conn, results, termino)

        if not results:
            conn.close()
            return []

        ids = tuple(r["nombre"] for r in results)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        placeholders = ",".join(f"${i+1}::text" for i in range(len(ids)))
        cur.execute(f"""
            SELECT DISTINCT ON (m.nombre) m.id, m.nombre, m.nombre_comun, m.precio_renta,
                   m.marcas, m.modelos_tipicos,
                   c.nombre AS categoria,
                   m.especificaciones
            FROM maquinas m
            JOIN categorias c ON c.id = m.categoria_id
            WHERE m.nombre = ANY(%s)
            ORDER BY m.nombre
        """, (list(ids),))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        order = {name: i for i, name in enumerate(ids)}
        rows.sort(key=lambda r: order.get(r["nombre"], 999))
        return [dict(r) for r in rows]
    except Exception:
        return []


def detalle_maquinaria(nombre: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    if not conn:
        return None
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT m.*, c.nombre AS categoria_nombre
            FROM maquinas m
            JOIN categorias c ON c.id = m.categoria_id
            WHERE LOWER(m.nombre) = LOWER(%s)
            LIMIT 1
        """, (nombre,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return dict(row)
        return None
    except Exception:
        return None


def listar_proyectos() -> List[Dict[str, Any]]:
    conn = get_conn()
    if not conn:
        return []
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM proyectos ORDER BY nombre")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def obtener_catalogo() -> List[Dict[str, Any]]:
    conn = get_conn()
    if not conn:
        return []
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT m.id, m.nombre, m.nombre_comun, m.precio_renta,
                   c.nombre AS categoria,
                   m.marcas, m.modelos_tipicos,
                   m.especificaciones AS specs,
                   m.recomendado, m.no_recomendado,
                   m.perfil_cliente AS descripcion
            FROM maquinas m
            JOIN categorias c ON c.id = m.categoria_id
            ORDER BY c.nombre, m.nombre
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        result = []
        for r in rows:
            d = dict(r)
            if isinstance(d.get("marcas"), str):
                d["marcas"] = [x.strip() for x in d["marcas"].split(",") if x.strip()]
            
            cat_lower = (d.get("categoria") or "").lower()
            if "excavadora" in cat_lower and "retro" not in cat_lower:
                d["imagen"] = "/images/excavadora.jpg"
            elif "bulldozer" in cat_lower or "topador" in cat_lower:
                d["imagen"] = "/images/bulldozer.jpg"
            elif "retro" in cat_lower:
                d["imagen"] = "/images/retroexcavadora.jpg"
            elif "grua" in cat_lower:
                d["imagen"] = "/images/grua.jpg"
            else:
                d["imagen"] = "/images/excavadora.jpg"

            d["precios"] = {
                "diario": 3500,
                "semanal": 21000,
                "mensual": 75000
            }
            if d.get("precio_renta"):
                try:
                    digits = re.sub(r"[^\d]", "", d["precio_renta"])
                    if digits:
                        d["precios"]["diario"] = int(digits)
                        d["precios"]["semanal"] = int(digits) * 6
                        d["precios"]["mensual"] = int(digits) * 22
                except Exception:
                    pass

            result.append(d)
        return result
    except Exception:
        return []

