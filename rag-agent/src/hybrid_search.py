import json
import math
import re
import requests
from typing import List, Dict, Optional, Tuple

OLLAMA_EMBED_URL = "http://ollama:11434/api/embed"
EMBED_MODEL = "nomic-embed-text"

# RRF (Reciprocal Rank Fusion) constant
RRF_K = 60


def _get_embedding(text: str) -> Optional[List[float]]:
    try:
        r = requests.post(
            OLLAMA_EMBED_URL,
            json={"model": EMBED_MODEL, "input": text},
            timeout=30,
        )
        data = r.json()
        return data["embeddings"][0]
    except Exception:
        return None


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _build_text_for_embedding(machine: Dict) -> str:
    parts = [
        machine.get("nombre", ""),
        machine.get("nombre_comun", ""),
        machine.get("descripcion", ""),
        machine.get("categoria", ""),
    ]
    sinonimos = machine.get("sinonimos", [])
    if isinstance(sinonimos, str):
        try:
            sinonimos = json.loads(sinonimos)
        except Exception:
            sinonimos = [sinonimos]
    if isinstance(sinonimos, list):
        parts.extend(s for s in sinonimos if isinstance(s, str))

    especs = machine.get("especificaciones", {})
    if isinstance(especs, dict):
        parts.extend(str(v) for v in especs.values() if isinstance(v, str))

    return " | ".join(p for p in parts if p)


MACHINE_COLUMNS = ["id", "nombre", "nombre_comun", "sinonimos",
                    "especificaciones", "embedding", "categoria"]

def _get_all_machines_embeddings(conn) -> List[Dict]:
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT m.id, m.nombre, m.nombre_comun, m.sinonimos,
                   m.especificaciones, m.embedding,
                   c.nombre AS categoria
            FROM maquinas m
            JOIN categorias c ON c.id = m.categoria_id
            ORDER BY m.id
        """)
        rows = cur.fetchall()
        result = []
        for r in rows:
            d = dict(zip(MACHINE_COLUMNS, r))
            emb = d["embedding"]
            if emb is not None and isinstance(emb, (list, tuple)):
                d["embedding"] = list(emb)
            result.append(d)
        return result
    finally:
        cur.close()


def generate_and_store_embeddings(conn) -> int:
    from src import database
    machines = database.obtener_catalogo()
    if not machines:
        machines = _get_all_machines_embeddings(conn)

    count = 0
    cur = conn.cursor()
    try:
        for m in machines:
            text = _build_text_for_embedding(m)
            emb = _get_embedding(text)
            if emb:
                cur.execute(
                    "UPDATE maquinas SET embedding = %s WHERE id = %s",
                    (emb, m["id"]),
                )
                count += 1
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
    return count


def bm25_search(conn, termino: str, limit: int = 20) -> List[Dict]:
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT m.id, m.nombre, m.nombre_comun, m.marcas,
                   m.modelos_tipicos, c.nombre AS categoria,
                   m.especificaciones, m.precio_renta,
                   ts_rank(
                       setweight(to_tsvector('spanish', COALESCE(m.nombre, '')), 'A') ||
                       setweight(to_tsvector('spanish', COALESCE(m.nombre_comun, '')), 'B') ||
                       setweight(to_tsvector('spanish', COALESCE(array_to_string(m.sinonimos, ' '), '')), 'C') ||
                       setweight(to_tsvector('spanish', COALESCE(m.especificaciones::text, '')), 'D'),
                       plainto_tsquery('spanish', %s)
                   ) AS rank
            FROM maquinas m
            JOIN categorias c ON c.id = m.categoria_id
            WHERE to_tsvector('spanish',
                  COALESCE(m.nombre, '') || ' ' ||
                  COALESCE(m.nombre_comun, '') || ' ' ||
                  COALESCE(array_to_string(m.sinonimos, ' '), '')
            ) @@ plainto_tsquery('spanish', %s)
            ORDER BY rank DESC
            LIMIT %s
        """, (termino, termino, limit))

        rows = cur.fetchall()
        COLUMNS = ["id", "nombre", "nombre_comun", "marcas", "modelos_tipicos",
                    "categoria", "especificaciones", "precio_renta", "rank"]
        result = [dict(zip(COLUMNS, r)) for r in rows]

        if not result:
            unaccented = termino.strip()
            like = f"%{unaccented}%"
            cur.execute("""
                SELECT DISTINCT m.id, m.nombre, m.nombre_comun, m.precio_renta,
                       m.marcas, m.modelos_tipicos,
                       c.nombre AS categoria,
                       m.especificaciones, 0.0 AS rank
                FROM maquinas m
                JOIN categorias c ON c.id = m.categoria_id
                WHERE unaccent(m.nombre) ILIKE unaccent(%s)
                   OR unaccent(m.nombre_comun) ILIKE unaccent(%s)
                ORDER BY m.nombre
                LIMIT %s
            """, (like, like, limit))
            rows = cur.fetchall()
            COLUMNS_ILIKE = ["id", "nombre", "nombre_comun", "precio_renta",
                              "marcas", "modelos_tipicos", "categoria",
                              "especificaciones", "rank"]
            ike_results = [dict(zip(COLUMNS_ILIKE, r)) for r in rows]

            if not ike_results:
                words = [w for w in re.findall(r'\w+', termino) if len(w) > 3]
                for word in words:
                    w_like = f"%{word}%"
                    cur.execute("""
                        SELECT DISTINCT m.id, m.nombre, m.nombre_comun, m.precio_renta,
                               m.marcas, m.modelos_tipicos,
                               c.nombre AS categoria,
                               m.especificaciones, 0.0 AS rank
                        FROM maquinas m
                        JOIN categorias c ON c.id = m.categoria_id
                        WHERE unaccent(m.nombre) ILIKE unaccent(%s)
                           OR unaccent(m.nombre_comun) ILIKE unaccent(%s)
                        ORDER BY m.nombre
                        LIMIT %s
                    """, (w_like, w_like, limit))
                    rows = cur.fetchall()
                    if rows:
                        ike_results = [dict(zip(COLUMNS_ILIKE, r)) for r in rows]
                        break

            result = ike_results

        return result
    finally:
        cur.close()


def vector_search(conn, termino: str, limit: int = 20) -> List[Dict]:
    machines = _get_all_machines_embeddings(conn)
    if not machines:
        return []

    query_emb = _get_embedding(termino)
    if not query_emb:
        return []

    scored = []
    for m in machines:
        if m["embedding"]:
            sim = _cosine_similarity(query_emb, m["embedding"])
            scored.append((sim, m))

    scored.sort(key=lambda x: x[0], reverse=True)
    scored = scored[:limit]

    return [
        {
            "id": m["id"],
            "nombre": m["nombre"],
            "nombre_comun": m["nombre_comun"],
            "categoria": m["categoria"],
            "score": sim,
        }
        for sim, m in scored
    ]


def hybrid_search(
    conn, termino: str, limit: int = 10
) -> List[Dict]:
    bm25_results = bm25_search(conn, termino, limit=limit * 2)
    vector_results = vector_search(conn, termino, limit=limit * 2)

    combined: Dict[str, Dict] = {}

    for rank, r in enumerate(bm25_results):
        name = r["nombre"]
        combined.setdefault(name, {"nombre": name, "bm25_rank": rank, "vector_rank": None, "categoria": r.get("categoria", "")})
        combined[name]["bm25_rank"] = rank
        combined[name]["categoria"] = r.get("categoria", "")

    for rank, r in enumerate(vector_results):
        name = r["nombre"]
        combined.setdefault(name, {"nombre": name, "bm25_rank": None, "vector_rank": rank, "categoria": r.get("categoria", "")})
        combined[name]["vector_rank"] = rank
        combined[name]["categoria"] = r.get("categoria", "")

    scored_results = []
    for name, data in combined.items():
        rrf_score = 0.0
        if data["bm25_rank"] is not None:
            rrf_score += 1.0 / (RRF_K + data["bm25_rank"] + 1)
        if data["vector_rank"] is not None:
            rrf_score += 1.0 / (RRF_K + data["vector_rank"] + 1)
        data["rrf_score"] = rrf_score
        scored_results.append(data)

    scored_results.sort(key=lambda x: x["rrf_score"], reverse=True)
    return scored_results[:limit]


def rerank(conn, results: List[Dict], termino: str) -> List[Dict]:
    if not results:
        return results

    prompt = (
        "Eres un evaluador de relevancia. "
        "Para la consulta del usuario, clasifica cada resultado como:\n"
        "  EXACTO (3 puntos) — coincide perfectamente\n"
        "  PARCIAL (2 puntos) — relacionado pero no exacto\n"
        "  MARGINAL (1 punto) — tangencialmente relevante\n"
        "  IRRELEVANTE (0 puntos)\n\n"
        f"Consulta: {termino}\n\n"
        "Resultados:\n"
    )
    for i, r in enumerate(results):
        prompt += f"{i+1}. {r['nombre']} - {r.get('categoria', '')}\n"

    prompt += "\nResponde solo con una línea por resultado, formato: 'i: PUNTOS'. Ejemplo:\n1: EXACTO\n2: PARCIAL\n"

    try:
        r = requests.post(
            "http://ollama:11434/api/generate",
            json={
                "model": "qwen2.5:7b",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 200},
            },
            timeout=30,
        )
        text = r.json().get("response", "")
        scores = {}
        for line in text.strip().split("\n"):
            line = line.strip().lower()
            m = re.match(r"(\d+)\s*:\s*(\w+)", line)
            if m:
                idx = int(m.group(1)) - 1
                label = m.group(2)
                score_map = {"exacto": 3, "parcial": 2, "marginal": 1, "irrelevante": 0}
                scores[idx] = score_map.get(label, 0)
        for i, r in enumerate(results):
            r["rerank_score"] = scores.get(i, 0)
        results.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
    except Exception:
        pass

    return results
