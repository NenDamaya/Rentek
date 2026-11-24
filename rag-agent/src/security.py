"""
Módulo de seguridad: Detección de prompt injection, off-topic y rate limiting.
"""

import re
import time
from typing import Tuple, Optional
from collections import defaultdict


class SecurityGuard:
    def __init__(self):
        self.request_counts = defaultdict(list)
        self.RATE_LIMIT_WINDOW = 60
        self.MAX_REQUESTS_PER_WINDOW = 30

        self.injection_patterns = [
            r"(?i)ignora\s+(las?\s+)?(instrucciones|reglas|directrices)",
            r"(?i)ignor(?:a|ar)\s+(?:el\s+)?(?:system|tu)\s+(?:prompt|instrucciones)",
            r"(?i)reve(?:la|lar)\s+(?:tu\s+)?(?:system\s+)?prompt",
            r"(?i)mu(?:estra|estra)\s+(?:tu\s+)?(?:system\s+)?prompt",
            r"(?i)asum(?:e|ir)\s+(?:el\s+)?rol\s+de",
            r"(?i)act(?:úa|ua|uar)\s+como\s+(?:si\s+)?(?: fueras?|si\s+fuera)",
            r"(?i)eres\s+un\s+(?:nuevo|diferente|otro)",
            r"(?i)cambia\s+(?:tu\s+)?(?:rol|personalidad|identidad)",
            r"(?i)olvida\s+(?:todo\s+)?(?:lo\s+)?(?:que|anterior)",
            r"(?i)reset(?:ea)?(?:ar)?\s+(?:todo|system|instrucciones)",
            r"(?i)new\s+instructions?",
            r"(?i)ignore\s+(?:all\s+)?(?:previous|above|prior)",
            r"(?i)you\s+are\s+now",
            r"(?i)from\s+now\s+on",
            r"(?i)system\s*:\s*",
            r"(?i)<<\s*SYS\s*>>",
            r"(?i)\[SYSTEM\]",
            r"(?i)###\s*INSTRUCTION",
            r"(?i)(respond\w*|contesta|contéstame|escribe|genera|habla)\s+(en|con|usando|mediante)\s+(c[oó]digo\s+morse|morse|binario|leet|hex|base64|ingl[eé]s|portugu[eé]s|n[aá]huatl|otro\s+idioma|formato)",
            r"(?i)(cambia|cambiar|modifica|modificar|ajusta|ajustar)\s+(las\s+)?(respuestas|formato|estilo|manera\s+de\s+(responder|contestar|hablar))",
            r"(?i)(siempre|de\s+ahora\s+en\s+adelante|a\s+partir\s+de\s+ahora)\s+(me\s+)?(contestes|respondas|hables|escribes|responder[aá]s)",
            r"(?i)aprend[ae]s?\s+(c[oó]digo\s+morse|nuevo\s+(formato|idioma|estilo)|a\s+(responder|hablar|contestar))",
            # Role impersonation: pretending to be admin/support/employee
            r"(?i)(soy|sou|eres|sos)\s+(el\s+|la\s+|un\s+|una\s+)?(administrador|admin|soporte|support|empleado|employee|trabajador|worker|staff|gerente|manager|dueño|owner|encargado|supervisor|jefe|boss)",
            r"(?i)(tengo|tienes)\s+(permisos\s+de|acceso\s+de|rol\s+de)\s+(administrador|admin|soporte|support|superior)",
        ]

        self.off_topic_patterns = [
            # Comida / recetas
            r"(?i)receta\s+(de|para|para\s+hacer)",
            r"(?i)cómo\s+(hacer|cocinar|preparar)\s+",
            r"(?i)(ingredientes|receta\s+de\s+cocina)",
            # Clima / tiempo
            r"(?i)(clima|temperatura)",
            r"(?i)(lluvia|llover|nevar|tormenta|soleado|nublado)",
            r"(?i)qué\s+(tal\s+)?(está|estara|estará)\s+el\s+(clima|tiempo)",
            # Deportes
            r"(?i)(fútbol|futbol|béisbol|beisbol|baloncesto|tenis|natación)",
            r"(?i)(partido\s+de|equipo\s+de|jugador\s+de)\s+(fútbol|futbol)",
            # Videojuegos / entretenimiento
            r"(?i)(minecraft|nether|fortnite|roblox|gta|videojuego)",
            r"(?i)(película|serie|canción|música|artista)\s+(de|que|favorita)",
            # Instalación de software / herramientas
            r"(?i)(instal[aeo]|descarg[au]|configur[aeo])\s+(un|el|esa|este\s+)?(programa|software|app|aplicación|herramienta|paquete|librería|plug[ií]n|sqlit)",
            r"(?i)(sqlite|mysql|postgresql|mongodb|redis)\s*(tui|gui|shell|console|connector|driver)",
            r"(?i)(terminal|consola|shell|bash|zsh|powershell)\s+(comando|command|instrucción)",
            # Programación / tecnología
            r"(?i)(c[oó]digo|codigo|codpgo|programa|script|función)\s+(para|que|en|de|fuente)",
            r"(?i)(pyth?on|pyhon|javascript|java|html|css|docker|kubernetes|nodejs|npm|pip|git|typescript|sqlite)",
            r"(?i)c[oó]mo\s+(se\s+)?(instala|descarga|ejecuta|configura|programa|crea|conecta|conectar|instalar)",
            r"(?i)api\s+endpoint|tool_call|function_call",
            r"(?i)(puedes\s+(darme|poner|mostrar|dar|escribir|enseñar)|mu[eé]strame|ens[eé]ñame|d[aá]me)\s+(un\s+)?(c[oó]digo|ejemplo|script|programa)",
            r"(?i)quiero\s+(un\s+)?(c[oó]digo|programa|script|ejemplo)\s+(en|de|para|que)",
            r"(?i)ejemplo\s+(de\s+)?(c[oó]digo|codigo|programa|script|función)",
            # Política / religión
            r"(?i)(política|político|presidente|gobierno|elecciones|votar)",
            r"(?i)(dios|religión|iglesia|rezar|biblia)",
            # Salud / médico
            r"(?i)(diagnóstico|enfermedad|síntoma|medicamento|doctor|hospital)",
            r"(?i)(dolor\s+de|cómo\s+curar|tratamiento\s+para)",
            # Educación / tareas
            r"(?i)(tarea\s+de|deberes|examen|estudio|aprender)\s+(matemáticas|historia|geografía)",
            r"(?i)resuelve\s+(esta\s+)?(ecuación|problema\s+matemático)",
            # Temas absurdos / ficticios
            r"(?i)(bajo\s+el\s+agua|en\s+el\s+cielo|en\s+el\s+espacio|en\s+marte)",
            r"(?i)construir\s+(una\s+)?(casa\s+en\s+un\s+árbol|nave\s+espacial|submarino)",
            # Conversación genérica / chit-chat — meta-preguntas (NO incluir saludos básicos)
            r"(?i)(c[oó]mo\s+(est[aá]s|estas|te\s+llamas|te\s+va)|qui[eé]n\s+(eres|creaste|hizo|te\s+cre[oó])|cu[aá]l\s+es\s+tu\s+(nombre|apellido))",
            r"(?i)(cu[aá]ntos?\s+a[nñ]os\s+tienes|de\s+d[oó]nde\s+eres|qu[eé]\s+haces|a\s+qu[eé]\s+te\s+dedicas)",
            # Operaciones matemáticas sin contexto
            r"(?i)^\d+[\s]*[\+\-\*\/x\^][\s]*\d+[\s]*$",
            r"(?i)^[a-z][\s]*[\+\-\*\/x\^][\s]*\d+[\s]*$",
            r"(?i)^\d+[\s]*[\+\-\*\/x\^][\s]*[a-z][\s]*$",
            r"(?i)^[a-z][\s]*[\+\-\*\/x\^][\s]*[a-z][\s]*$",
            r"(?i)^[a-z]\s+\d+[\s]*[\+\-\*\/x\^][\s]*\d+",
            r"(?i)^(pi|π|e)\s*[\+\-\*\/x\^]\s*\d+",
            r"(?i)cu[aá]nto\s+(es|da|sale|vale)\s+(\d+|pi|π|e|[a-z])\s*[\+\-\*\/x\^]\s*(\d+|pi|π|e|[a-z])",
            r"(?i)cu[aá]nto\s+(es|da|sale|vale)\s+(pi|π|e)\s*$",
            r"(?i)cu[aá]nto\s+(es|da|sale|vale)\s+(pi|π|e)\s+(m[aá]s|menos|por|entre|dividido|partido|multiplicado)",
            r"(?i)(\d+|pi|π|e|[a-z])\s*[\+\-\*\/x\^]\s*(\d+|pi|π|e|[a-z])\s+(es|da|cu[aá]nto|igual)",
            r"(?i)(\d+|pi|π|e|[a-z])\s+(m[aá]s|menos|por|entre|dividido|partido|multiplicado)\s+(\d+|pi|π|e|[a-z])\s+(es|da|cu[aá]nto|igual)",
            r"(?i)(dime|cual|cu[aá]l)\s+(es\s+)?(el\s+)?(resultado|respuesta)\s+de\s+(\d+|pi|π|e|[a-z])\s*[\+\-\*\/x\^]\s*(\d+|pi|π|e|[a-z])",
            r"(?i)cu[aá]nto\s+(es|da|vale)\s+el\s+(valor\s+de\s+)?(pi|π|euler)",
            r"(?i)(pi|π|euler|constante)\s*(multiplicado|por|dividido|entre|m[aá]s|menos)",
            r"(?i)(valor\s+de\s+pi|valor\s+de\s+π)",
            r"(?i)cu[aá]nto\s+(es|da)\s+\d+\s+(m[aá]s|menos|por|entre|dividido|partido)",
            r"(?i)\d+\s+(m[aá]s|menos|por|entre|dividido|partido|multiplicado)\s+\d+\s+(es|da|cu[aá]nto|igual)",
            r"(?i)\d+\s+(m[aá]s|menos|por|entre|dividido|multiplicado)\s+[a-z]\s+(es|da|cu[aá]nto|igual)",
            r"(?i)[a-z]\s+(m[aá]s|menos|por|entre|dividido|multiplicado)\s+\d+\s+(es|da|cu[aá]nto|igual)",
            r"(?i)(ra[ií]z|cuadrado|potencia|elevado|al\s+cuadrado|al\s+cubo)\s*(cuadrada|c[uú]bica|de\s+\d+|a\s+la|al\s+cuadrado|al\s+cubo)",
            r"(?i)\d+\s+(al\s+cuadrado|al\s+cubo|a\s+la\s+\d+)",
            # Filosofía / consejo de vida
            r"(?i)(sentido\s+de\s+la\s+vida|propósito\s+de\s+la\s+existencia)",
            # Meta-preguntas sobre el asistente / sistema
            r"(?i)(qu[eé]\s+es\s+lo\s+que\s+(eres|puedes\s+hacer|no\s+puedes\s+hacer|sabes\s+hacer|haces|capaz\s+de|si\s+puedes\s+hacer))",
            r"(?i)(qu[eé]\s+es\s+(lo\s+que\s+)?(eres|puedes|haces|capaz))",
            r"(?i)en\s+qu[eé]\s+(puedes|consistes|ayudas|contribuyes)",
            r"(?i)para\s+qu[eé]\s+(sirves|eres|est[aá]s|fuiste\s+(creado|diseñado|programado))",
            r"(?i)(dime|cu[aá]les\s+son|expl[ií]came|cu[aá]l\s+es)\s+(tus\s+)?(funciones|capacidades|l[ií]mites|limitaciones|h?err?a?mi[eé]n[dt]a[s]?|prop[oó]sito|objetivo|caracter[ií]sticas)",
            r"(?i)(puedes\s+(cambiar|modificar|ajustar|personalizar))\s+(las\s+)?(respuestas|formato|estilo|manera)",
            # Meta-solicitudes: pedir al asistente que genere contenido off-topic
            r"(?i)gener[ae]?\s*(un|me)\s+(un\s+)?(off.?topic|tema\s+aleatorio|conversación|charla)",
            r"(?i)h[aá]blame\s+de\s+(lo\s+)?(que\s+)?(quieras|cualquier\s+tema|algo|otra\s+cosa)",
            # Meta-preguntas: "con qué puedes ayudar" / "para qué sirves" variants with typos
            r"(?i)(con\s+(las\s+|lo\s+|la\s+)?(qué|que)\s+(me\s+)?(puedes|puedas)\s+(ayudar|ofrecer|contribuir|servir|hacer))",
            r"(?i)(pa[ra]?\s+qu[ée]\s+(sirves|sirvas|eres|funcionas|ayudas))",
            # Preguntas sobre inteligencia artificial / tecnología general
            r"(?i)(qu[eé]\s+es|sobre\s+que\s+es|dime\s+(que\s+es|sobre)|explica)\s+(la\s+)?(inteligencia\s+artificial|IA\b|machine\s+learning|deep\s+learning|chatgpt|openai|modelo\s+de\s+lenguaje|LLM)",
            r"(?i)(c[oó]mo\s+funciona|explicame|c[oó]mo\s+se\s+llama)\s+(la\s+)?(IA|inteligencia\s+artificial|este\s+sistema|esta\s+app|esta\s+aplicación)",
            # Preguntas directas sobre el sistema
            r"(?i)(qu[eé]\s+h?err?a?mi[eé]n[dt]a[s]?\s+tienes|muéstrame\s+las\s+funciones)",
            r"(?i)(dame\s+un\s+ejemplo\s+de\s+tool_call|cómo\s+llamas\s+a\s+una\s+función)",
            # Idiomas / traducciones
            r"(?i)traduce\s+(esto|al|esta|este)",
            r"(?i)(say|tell|speak)\s+(in|me)\s+(english|portuguese|nahuatl)",
            # Codificación / formatos
            r"(?i)(c[oó]digo\s+morse|morse|binario|base64|hexadecimal|leet|formato\s+distinto)\s+(para\s+)?(responder|contestes|comunicarte|hablar)",
            r"(?i)(aprender|enseñar|aprendo|enseña)\s+(c[oó]digo\s+morse|morse|binario|leet)",
        ]

        self.refusal_patterns = [
            r"(?i)solo\s+para\s+renta\s+de\s+maquinaria",
            r"(?i)no\s+pierdas\s+mi\s+tiempo",
            r"(?i)asesor\s+especializado\s+en\s+renta\s+de\s+maquinaria",
            r"(?i)no\s+cambio\s+mi\s+comportamiento",
            r"(?i)no\s+puedo\s+procesar\s+esa\s+solicitud",
            r"(?i)por\s+favor\s+(escribe|pregunta)\s+en\s+español",
            r"(?i)no\s+(respondo|contesto|puedo)\s+(a\s+)?(eso|esa)",
            r"(?i)asistente\s+es\s+(solo\s+)?para\s+renta",
        ]

        self.repetitive_pattern_threshold = 5

    def detect_prompt_injection(self, text: str) -> Tuple[bool, Optional[str]]:
        if not text or len(text.strip()) == 0:
            return False, None

        for pattern in self.injection_patterns:
            if re.search(pattern, text):
                return True, "Patrón de inyección de prompt detectado"

        STOPWORDS = {"por", "que", "para", "con", "del", "las", "los", "una", "uno", "mas", "más", "dias", "días", "como", "cómo", "esta", "está", "este", "esto", "pero", "dime", "cuánto", "cuanto", "cuál", "cual"}
        words = [re.sub(r'[^\w]', '', w.lower()) for w in text.split()]
        if len(words) > 10:
            word_freq = defaultdict(int)
            for w in words:
                if w and w not in STOPWORDS and len(w) > 3:
                    word_freq[w] += 1
            for word, count in word_freq.items():
                if count >= 7:
                    return True, "Patrón repetitivo sospechoso detectado"

        if len(text) > 2000:
            return True, "Prompt excesivamente largo"

        return False, None

    def detect_off_topic(self, text: str) -> bool:
        if not text or len(text.strip()) == 0:
            return False
        for pattern in self.off_topic_patterns:
            if re.search(pattern, text):
                return True
        return False

    def detect_refusal(self, text: str) -> bool:
        # Un texto vacío no es un rechazo: es una respuesta fallida y no debe
        # contar como strike de off-topic. Tampoco una respuesta corta válida
        # ("Sí.", "Claro.", "Listo.") debe cerrar el chat.
        if not text or not text.strip():
            return False
        for pattern in self.refusal_patterns:
            if re.search(pattern, text):
                return True
        return False

    def check_rate_limit(self, session_id: str = "anonymous") -> Tuple[bool, Optional[str]]:
        now = time.time()
        window_start = now - self.RATE_LIMIT_WINDOW

        self.request_counts[session_id] = [
            t for t in self.request_counts[session_id] if t > window_start
        ]

        if len(self.request_counts[session_id]) >= self.MAX_REQUESTS_PER_WINDOW:
            return True, f"Límite de {self.MAX_REQUESTS_PER_WINDOW} requests por minuto excedido"

        self.request_counts[session_id].append(now)
        return False, None

    def detect_unclear_input(self, text: str) -> bool:
        if not text or len(text.strip()) == 0:
            return False
        stripped = text.strip()
        # Solo signos de interrogación: ?, ??, ???, ¿?, ¿¿, etc.
        if re.match(r"^[\s¿?]{1,5}$", stripped):
            return True
        # Respuestas de una palabra sin contexto de máquinaria
        single_word = stripped.lower().strip(".!?")
        if re.match(r"^(s[ií]|no|ok|okey|okay|aye|np|nop|tal\s*vez|quiz[aá]|duda|claro|see|simon|simón)$", single_word):
            return True
        # Símbolos sueltos sin sentido
        if re.match(r"^[^a-záéíóúñA-ZÁÉÍÓÚÑ0-9]{1,3}$", stripped):
            return True
        return False

    def validate_input(self, text: str, session_id: str = "anonymous") -> Tuple[bool, str]:
        rate_limited, rate_msg = self.check_rate_limit(session_id)
        if rate_limited:
            return True, rate_msg

        blocked, reason = self.detect_prompt_injection(text)
        if blocked:
            return True, reason

        off_topic = self.detect_off_topic(text)
        if off_topic:
            return True, "Mensaje fuera de tema"

        return False, ""


security = SecurityGuard()
