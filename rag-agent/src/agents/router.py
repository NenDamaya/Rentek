import re
from typing import Literal

Intent = Literal["rag", "transaccional", "off_topic"]


class Router:
    """
    Router híbrido: clasifica la intención del mensaje usando regex primero,
    y si el mensaje es ambiguo, usa el LLM para decidir.
    """

    # ============ PATRONES RAG ============
    RAG_PATTERNS = [
        r"\b(qu[eé]\s+es|qu[eé]\s+son|qu[eé]\s+significa)\b",
        r"\b(especificaciones\s*t[eé]cnicas|ficha\s*t[eé]cnica|caracter[ií]sticas)\b",
        r"\b(detalles?\s+t[eé]cnicos?|detalle\s+de\b)",
        r"\b(diferencia|comparar|compara|mejor\s+opci[oó]n)\b",
        r"\b(para\s+qu[eé]\s+sirve|c[uá]l\s+es\s+mejor)\b",
        r"\b(casos?\s+de\s+uso|recomendado\s+para|aplicaciones)\b",
        r"\b(c[uú]anto\s+pesa|dimensiones|capacidad|potencia|consumo)\b",
        r"\b(documentaci[oó]n|manual|gu[ií]a|informativo)\b",
        r"\b(categor[ií]as?|cat[aá]logo|tipos?\s+de\s+maquinaria)\b",
        r"\b(qu[eé]\s+maquinaria\s+(tienen|manejan|ofrecen|hay))\b",
    ]

    # ============ PATRONES TRANSACCIONALES ============
    TRANS_PATTERNS = [
        r"\b(rentar|alquilar|quiero\s+rentar|necesito\s+rentar|busco\s+renta)\b",
        r"\b(registra\w*|solicitud|cotizaci[oó]n|cotiza\w*)\b",
        r"\b(precio|costo|cu[aá]nto\s+cuesta|cu[aá]nto\s+sale)\b",
        r"\b(disponib\w+|fecha|d[ií]as\s+de\s+renta|por\s+cu[aá]ntos?\s+d[ií]as)\b",
        r"\b(mis\s+(cotizaciones|solicitudes))\b",
        r"\b(procede|adelante|confirmo|acepto)\b.*\b(solicitud|renta|cotizaci[oó]n)\b",
        r"\b(presupuesto|orçamento|budget)\b",
        r"\b(mis\s+datos\s+son|me\s+llamo|nombre.*(?:es|:))\b",
        r"\b(hola|buenas|buen[oa]\s+(d[ií]a|tarde|noche))\s*(?:,|!)?\s*(?:necesito|quisiera|quiero|busco|me\s+ayudan)\b",
    ]

    # ============ PATRONES OFF-TOPIC ============
    OFFTOPIC_PATTERNS = [
        r"\b(presidente|pol[ií]tica|elecciones|gobierno|partido)\b",
        r"\b(deporte|f[uú]tbol|b[eé]isbol|boxeo|nba|nfl)\b",
        r"\b(receta|cocinar|comida|restaurante)\b",
        r"\b(\d+\s*\+\s*\d+|suma|resta|multiplic|divisi[oó]n)\b",
        r"\b(ignora\s*(?:las\s*)?instrucciones|olvida\s*(?:todo\s*)?|no\s+hagas\s+caso)\b",
        r"\b(c[oó]digo|programaci[oó]n|script|funci[oó]n\s+call|tool_call|endpoint|api)\b",
        r"\b(quien\s+eres|qui[eé]n\s+te\s+cre[oó]|que\s+puedes\s+hacer|para\s+qu[eé]\s+sirves)\b",
        r"\b(minecraft|nether|fortnite|videojuego|juego)\b",
    ]

    @classmethod
    def classify(cls, message: str) -> Intent:
        u = message.lower().strip()

        if not u:
            return "off_topic"

        # 1. Check off-topic first (security)
        if cls._matches_any(u, cls.OFFTOPIC_PATTERNS):
            return "off_topic"

        # 2. Check RAG patterns
        if cls._matches_any(u, cls.RAG_PATTERNS):
            return "rag"

        # 3. Check transactional patterns
        if cls._matches_any(u, cls.TRANS_PATTERNS):
            return "transaccional"

        # 4. Ambiguous: check for unresolved off-topic via simple heuristics
        # If the message has no machinery-related words at all, it's off-topic
        machinery_words = [
            "maquinaria", "excavadora", "retroexcavadora", "bulldozer", "minicargador",
            "compactadora", "cargador", "camión", "camion", "tractor", "motoniveladora",
            "pavimentadora", "grúa", "grua", "bomba", "carretilla", "apisonador",
            "obra", "construcción", "construccion", "renta", "alquiler", "proyecto",
            "terreno", "tierra", "excavación", "excavacion", "cimentación", "cimentacion",
            "pavimento", "rampa", "cochera", "piscina", "zanja", "barda", "muro",
            "losa", "concreto", "cemento", "materiales", "obra", "edificio",
            "rentar", "cotizar", "solicitud", "precio", "costo", "presupuesto",
        ]
        has_machinery = any(mw in u for mw in machinery_words)
        if not has_machinery and len(u.split()) > 1:
            # Double-check: if user says something short like "sí", "no", "ok" it's context-dependent
            short_answers = {"si", "sí", "no", "ok", "okay", "vale", "claro", "adelante", "procede"}
            if u.strip() not in short_answers:
                return "off_topic"

        # 5. Default to transactional (most common use case for Rentek)
        return "transaccional"

    @classmethod
    def _matches_any(cls, text: str, patterns: list) -> bool:
        for p in patterns:
            if re.search(p, text):
                return True
        return False
