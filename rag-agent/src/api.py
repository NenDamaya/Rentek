import asyncio
import json
import re
import uuid
from collections import defaultdict
from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, RedirectResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Tuple
import uvicorn
import time
import os
import tempfile
import httpx
from datetime import date
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from src.rag import RAGSystem
from src.catalogo import Catalogo
from src.ollama_client import OllamaClient
from src.tools_schemas import get_all_tools, get_tool_names
from src import database
from src import operaciones as ops
from src.security import security
from src.sessions import session_manager
from src.auth import hash_password, verify_password, create_token, verify_token
from .config import config

enable_docs = os.getenv("ENABLE_DOCS", "false").lower() == "true"

app = FastAPI(
    title="API RAG - Renta de Maquinaria Pesada",
    description="API para consultar el catálogo de maquinaria pesada y hacer preguntas al sistema RAG. "
                "Diseñada para ser consumida por IAs locales via tool calling/functions.",
    version="2.0.0",
    docs_url="/docs" if enable_docs else None,
    redoc_url="/redoc" if enable_docs else None,
    openapi_url="/openapi.json" if enable_docs else None,
)

frontend_url = os.getenv("FRONTEND_URL", "https://rentek-frontend.onrender.com").strip()
origins_env = os.getenv("ALLOWED_ORIGINS", "")
origins_list = [o.strip() for o in origins_env.split(",") if o.strip() and o.strip() != "*"]
if frontend_url and frontend_url not in origins_list:
    origins_list.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list if origins_list else [frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)


app.add_middleware(
    SessionMiddleware,
    secret_key=config.AUTH_SECRET_KEY,
    same_site="lax",
    https_only=config.HTTPS_ONLY,
)

oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

rag = RAGSystem()
catalogo_md = Catalogo()


def _format_tool_fallback(tools_executed: list, messages_raw: list) -> str:
    """Format a human-readable response from tool results when the model returns empty content."""

    # Get the last tool result from messages
    last_result_str = None
    for msg in reversed(messages_raw):
        if msg.get("role") == "tool" and msg.get("content"):
            last_result_str = msg["content"]
            break

    if not last_result_str:
        return "He consultado la información disponible. ¿En qué más puedo ayudarte?"

    try:
        last_result = json.loads(last_result_str)
    except (json.JSONDecodeError, TypeError):
        return "He consultado la información disponible. ¿En qué más puedo ayudarte?"

    last_tool = tools_executed[-1]["function"] if tools_executed else ""
    last_args = tools_executed[-1]["arguments"] if tools_executed else {}

    if "error" in last_result:
        error_msg = last_result["error"]
        return f"Lo siento, ocurrió un error: {error_msg}"

    if last_tool == "listar_categorias":
        categorias = last_result if isinstance(last_result, list) else last_result.get("data", [])
        if not categorias:
            return "No hay categorías disponibles en este momento."
        lines = [f"Estas son las categorías de maquinaria disponibles ({len(categorias)} en total):"]
        for cat in categorias:
            name = cat.get("categoria", cat.get("nombre", ""))
            total = cat.get("total_maquinas", cat.get("total", ""))
            if name:
                lines.append(f"  - {name}" + (f": {total}" if total else ""))
        return "\n".join(lines)

    if last_tool == "buscar_maquinaria":
        resultados = last_result.get("resultados", [])
        if not resultados:
            termino = last_args.get("termino", "")
            return f"No encontré maquinaria relacionada con '{termino}'."
        lines = [f"Encontré {len(resultados)} máquina(s) relacionadas con '{last_args.get('termino', '')}':"]
        for m in resultados[:8]:
            nombre = m.get("nombre") or m.get("maquina") or m.get("marca", "?")
            precio = m.get("precio_renta", "")
            lines.append(f"  - {nombre}" + (f" | {precio}" if precio else ""))
        return "\n".join(lines)

    if last_tool == "recomendar_por_trabajo":
        maquinas = last_result.get("maquinas_recomendadas", [])
        if not maquinas:
            return f"No encontré recomendaciones para '{last_args.get('tipo_trabajo', '')}'. Intenta con otro tipo de trabajo."
        lines = [f"Para trabajo de {last_args.get('tipo_trabajo', '')}, te recomiendo las siguientes opciones:"]
        for m in maquinas:
            nombre = m.get("nombre", "?")
            costo = m.get("precio_dia_estimado")
            if costo:
                lines.append(f"  - {nombre} (~${costo}/día)")
            else:
                lines.append(f"  - {nombre}")
        if len(maquinas) <= 3:
            total = last_result.get("costo_dia_estimado_total")
            if total:
                lines.append(f"Costo estimado combinado por día: ${total}")
        else:
            lines.append("Cada máquina tiene su costo individual. Solicita una cotización para el precio exacto.")
        return "\n".join(lines)

    if last_tool == "detalle_maquinaria":
        detalle_data = last_result.get("detalle", last_result)
        if not detalle_data:
            return f"No encontré detalles para '{last_args.get('nombre', '')}'."
        nombre = detalle_data.get("nombre", detalle_data.get("maquina", "?"))
        lines = [f"Detalles de {nombre}:"]
        precio = detalle_data.get("precio_renta", "")
        if precio:
            lines.append(f"  Precio de renta: {precio}")
        especs = detalle_data.get("especificaciones", {})
        if especs:
            if isinstance(especs, dict):
                for k, v in list(especs.items())[:6]:
                    lines.append(f"  {k}: {v}")
            elif isinstance(especs, str):
                lines.append(f"  {especs[:200]}")
        casos = detalle_data.get("casos_uso", [])
        if casos:
            lines.append(f"  Casos de uso: {', '.join(casos[:3])}")
        return "\n".join(lines)

    if last_tool == "calcular_costo_renta":
        maquina = last_result.get("maquina", last_args.get("maquina", ""))
        dias = last_result.get("dias", last_args.get("dias", ""))
        lines = [f"Costo de renta para {maquina}:"]
        if dias:
            lines.append(f"  Días: {dias}")
        subtotal = last_result.get("subtotal")
        if subtotal:
            lines.append(f"  Subtotal: ${subtotal}")
        descuento = last_result.get("descuento")
        if descuento:
            lines.append(f"  Descuento: ${descuento}")
        total = last_result.get("total")
        if total:
            lines.append(f"  Total: ${total}")
        return "\n".join(lines)

    if last_tool in ("consultar_mis_cotizaciones",):
        cotizaciones = last_result if isinstance(last_result, list) else last_result.get("cotizaciones", [])
        if not cotizaciones:
            return "No tienes cotizaciones registradas."
        lines = [f"Tienes {len(cotizaciones)} cotización(es):"]
        for c in cotizaciones[:5]:
            folio = c.get("folio", "")
            total = c.get("total", c.get("monto", ""))
            vigencia = c.get("vigencia", "")
            if folio:
                lines.append(f"  - Folio: {folio}" + (f", Total: ${total}" if total else "") + (f", Vigencia: {vigencia}" if vigencia else ""))
        return "\n".join(lines)

    if last_tool in ("consultar_mis_solicitudes",):
        solicitudes = last_result if isinstance(last_result, list) else last_result.get("solicitudes", [])
        if not solicitudes:
            return "No tienes solicitudes registradas."
        lines = [f"Tienes {len(solicitudes)} solicitud(es):"]
        for s in solicitudes[:5]:
            folio = s.get("folio", "")
            estado = s.get("estado", "")
            fecha = s.get("fecha", "")
            if folio:
                lines.append(f"  - Folio: {folio}" + (f", Estado: {estado}" if estado else "") + (f", Fecha: {fecha}" if fecha else ""))
        return "\n".join(lines)

    return "He consultado la información. ¿Hay algo más en lo que pueda ayudarte?"


def usar_db() -> bool:
    return database.db_disponible()


def listar_categorias_fallback():
    if usar_db():
        data = database.listar_categorias()
        if data:
            return data
    return catalogo_md.resumen_categorias()


def obtener_categoria_fallback(nombre: str):
    if usar_db():
        data = database.obtener_categoria(nombre)
        if data:
            return data
    return catalogo_md.get_categoria(nombre)


def buscar_maquinaria_fallback(termino: str):
    if usar_db():
        data = database.buscar_maquinaria(termino)
        if data:
            return {"origen": "postgresql", "resultados": data}
    results = catalogo_md.buscar(termino)
    return {"origen": "markdown", "resultados": results}


def detalle_maquinaria_fallback(nombre: str):
    if usar_db():
        data = database.detalle_maquinaria(nombre)
        if data:
            return {"origen": "postgresql", "detalle": data}
    data = catalogo_md.get_maquina(nombre)
    if data:
        return {"origen": "markdown", "detalle": data}
    return None


def listar_proyectos_fallback():
    if usar_db():
        data = database.listar_proyectos()
        if data:
            return data
    return catalogo_md.get_proyectos()


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5


class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    latency_ms: float


class ToolResponse(BaseModel):
    success: bool
    data: Any
    error: Optional[str] = None


class ChatMessage(BaseModel):
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model: Optional[str] = None
    messages: List[ChatMessage]
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = "auto"
    conversation_id: Optional[str] = None
    chat_id: Optional[str] = None
    stream: bool = False
    user_name: Optional[str] = None
    user_email: Optional[str] = None


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    conversation_id: Optional[str] = None


class RegisterRequest(BaseModel):
    email: str
    password: str
    display_name: Optional[str] = ""


class LoginRequest(BaseModel):
    email: str
    password: str


def get_current_user(request: Request) -> Optional[Tuple[int, str]]:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        verified = verify_token(token)
        if not verified:
            return None
        user_id, username = verified
        conn = database.get_conn()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT blocked FROM users WHERE id = %s", (user_id,))
                row = cur.fetchone()
                cur.close()
                if row and row[0]:
                    return None
            except Exception:
                pass
            finally:
                conn.close()
        return verified
    return None


_auth_attempts = defaultdict(list)


def check_auth_rate_limit(client_ip: str) -> bool:
    now = time.time()
    _auth_attempts[client_ip] = [t for t in _auth_attempts[client_ip] if t > now - 60]
    if len(_auth_attempts[client_ip]) >= 5:
        return True
    _auth_attempts[client_ip].append(now)
    return False


def get_current_user_details(request: Request) -> Optional[dict]:
    res = get_current_user(request)
    if not res:
        return None
    user_id, username = res
    conn = database.get_conn()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, username, email, role, display_name, blocked FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        if row and not row[5]:
            return {"id": row[0], "username": row[1], "email": row[2], "role": row[3], "display_name": row[4]}
        return None
    except Exception:
        return None
    finally:
        conn.close()


def require_admin(request: Request) -> dict:
    user = get_current_user_details(request)
    if not user:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Permisos de administrador requeridos")
    return user



def seed_default_admin():
    if os.getenv("SEED_DEFAULT_ADMIN", "false").lower() not in ("1", "true", "yes"):
        return
    admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "")
    if len(admin_password) < 8:
        return
    admin_username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    conn = database.get_conn()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = %s", (admin_username,))
        if not cur.fetchone():
            pw_hash = hash_password(admin_password)
            cur.execute(
                "INSERT INTO users (username, password_hash, display_name, role) VALUES (%s, %s, %s, %s)",
                (admin_username, pw_hash, "Administrador", "admin")
            )
            conn.commit()
        cur.close()
    except Exception:
        pass
    finally:
        conn.close()


ollama_client = OllamaClient()


def log_observability(
    session_id: str,
    user_prompt: str,
    system_response: str,
    ttft_ms: float,
    total_latency_ms: float,
    tools_executed: List[Dict],
    was_blocked: bool = False,
    block_reason: str = "",
    tokens_input: int = 0,
    tokens_output: int = 0,
):
    tokens_per_second = 0
    if total_latency_ms > 0 and tokens_output > 0:
        tokens_per_second = (tokens_output / total_latency_ms) * 1000

    conn = database.get_conn()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO observability_logs
                   (session_id, user_prompt, system_response, ttft_ms, total_latency_ms,
                    tokens_per_second, was_blocked, block_reason, tools_executed,
                    model_used, tokens_input, tokens_output)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    session_id,
                    user_prompt[:2000],
                    system_response[:5000] if system_response else "",
                    ttft_ms,
                    total_latency_ms,
                    tokens_per_second,
                    was_blocked,
                    block_reason,
                    json.dumps(tools_executed, ensure_ascii=False),
                    config.OLLAMA_MODEL,
                    tokens_input,
                    tokens_output,
                )
            )
            conn.commit()
            cur.close()
        except Exception:
            pass
        finally:
            conn.close()


def query_maquinaria_backend(question: str, top_k: int = 5) -> dict:
    result = rag.query(question, top_k)
    return {
        "answer": result["answer"],
        "sources": result["sources"][:3],
        "fuentes_usadas": len(result["sources"]),
        "latencia_ms": round(result["latency_ms"], 0),
    }


def clean_latex(text: str) -> str:
    if not text:
        return text
    def replace_block(match):
        formula = match.group(1)
        formula = re.sub(r'\\text\s*\{(.*?)\}', r'\1', formula)
        formula = formula.replace(r'\times', ' x ')
        formula = formula.replace(r'\cdot', ' x ')
        formula = formula.replace(r'\$', '$')
        formula = formula.replace(r'\\', '\n')
        return formula.strip()

    text = re.sub(r'\\\[(.*?)\\\]', replace_block, text, flags=re.DOTALL)
    text = re.sub(r'\$\$(.*?)\$\$', replace_block, text, flags=re.DOTALL)
    text = re.sub(r'\\\((.*?)\\\)', replace_block, text, flags=re.DOTALL)
    text = text.replace(r'\$', '$')
    return text


def parse_text_tool_call(text: str) -> Optional[tuple]:
    patterns = [
        # (pattern, tool_name_group_idx, args_group_idx)
        (r"(FunctionFlags\.call\(['\"](\w+)['\"],\s*(\{.*?\})\))", 2, 3),
        (r"(function\s+call\s*[:]\s*(\w+)\s*\((.*?)\))", 2, 3),
        (r"(<function_call>\s*(\w+)\s*(?:\((.*?)\))?\s*</function_call>)", 2, 3),
        (r"(<tool_call>\s*(\w+)\s*(?:\((.*?)\))?\s*</tool_call>)", 2, 3),
        (r"(\[(\w+)\]\s*(\{.*?\}))", 2, 3),
        # JSON patterns
        (r"(<tool_call>\s*(\{.*?\})\s*</tool_call>)", None, 2),
        (r"((?:Locker|Llamada|ToolCall|tool_call)\s*[:]\s*(\{.*?\}))", None, 2),
        (r"(\{\s*[\"']name[\"']\s*:\s*[\"']\w+[\"']\s*,\s*[\"']arguments[\"']\s*:\s*\{.*?\}\})", None, 1),
    ]
    for pattern, name_idx, args_idx in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            matched_text = match.group(1)
            if name_idx is not None:
                tool_name = match.group(name_idx)
                args_str = match.group(args_idx) or "{}"
                try:
                    arguments = json.loads(args_str)
                except json.JSONDecodeError:
                    args_str = args_str.replace("'", '"')
                    try:
                        arguments = json.loads(args_str)
                    except json.JSONDecodeError:
                        arguments = {}
                return (tool_name, arguments, matched_text)
            else:
                json_str = match.group(args_idx)
                try:
                    data = json.loads(json_str)
                except json.JSONDecodeError:
                    json_str = json_str.replace("'", '"')
                    try:
                        data = json.loads(json_str)
                    except json.JSONDecodeError:
                        data = {}
                if isinstance(data, dict) and "name" in data:
                    tool_name = data["name"]
                    arguments = data.get("arguments", {})
                    return (tool_name, arguments, matched_text)
    return None


def execute_tool(tool_name: str, arguments: dict, messages_raw: Optional[List[Dict[str, Any]]] = None, user_id: Optional[int] = None) -> Any:
    if tool_name == "listar_categorias":
        return listar_categorias_fallback()
    elif tool_name == "obtener_categoria":
        return obtener_categoria_fallback(arguments.get("nombre", ""))
    elif tool_name == "buscar_maquinaria":
        return buscar_maquinaria_fallback(arguments.get("termino", ""))
    elif tool_name == "detalle_maquinaria":
        result = detalle_maquinaria_fallback(arguments.get("nombre", ""))
        if result is None:
            return {"error": f"No se encontró maquinaria con el nombre '{arguments.get('nombre', '')}'"}
        return result
    elif tool_name == "listar_proyectos":
        return listar_proyectos_fallback()
    elif tool_name == "obtener_proyecto":
        data = catalogo_md.get_proyecto(arguments.get("nombre", ""))
        if not data:
            return {"error": f"No se encontró el proyecto '{arguments.get('nombre', '')}'"}
        return {"detalle": data}
    elif tool_name == "query_maquinaria":
        return query_maquinaria_backend(
            arguments.get("question", ""),
            arguments.get("top_k", 5),
        )
    elif tool_name == "calcular_costo_renta":
        return ops.calcular_costo_renta(
            arguments.get("maquina", ""),
            arguments.get("dias", 1),
            arguments.get("cantidad", 1),
        )
    elif tool_name == "verificar_disponibilidad":
        return ops.verificar_disponibilidad(
            arguments.get("maquina", ""),
            arguments.get("fecha_inicio", ""),
            arguments.get("fecha_fin", ""),
        )
    elif tool_name == "recomendar_por_trabajo":
        return ops.recomendar_por_trabajo(
            arguments.get("tipo_trabajo", ""),
            arguments.get("presupuesto"),
        )
    elif tool_name == "comparar_maquinas":
        return ops.comparar_maquinas(
            arguments.get("nombres", []),
        )
    elif tool_name == "calcular_costo_proyecto":
        return ops.calcular_costo_proyecto(
            arguments.get("maquinas", []),
            arguments.get("dias", 1),
        )
    elif tool_name == "registrar_solicitud":
        return ops.registrar_solicitud(
            arguments.get("cliente", ""),
            arguments.get("contacto", ""),
            arguments.get("maquinas", []),
            arguments.get("fecha_inicio", ""),
            arguments.get("fecha_fin", ""),
            user_id=user_id,
        )
    elif tool_name == "generar_cotizacion":
        return ops.generar_cotizacion(
            arguments.get("cliente", ""),
            arguments.get("contacto", ""),
            arguments.get("maquinas", []),
            arguments.get("dias", 1),
            user_id=user_id,
        )
    elif tool_name == "consultar_mis_cotizaciones":
        if not user_id:
            return {"error": "Debes iniciar sesión para consultar tus cotizaciones."}
        return ops.consultar_mis_cotizaciones(user_id)
    elif tool_name == "consultar_mis_solicitudes":
        if not user_id:
            return {"error": "Debes iniciar sesión para consultar tus solicitudes."}
        return ops.consultar_mis_solicitudes(user_id)
    elif tool_name == "validar_fecha":
        return ops.validar_fecha(
            arguments.get("fecha", ""),
        )
    elif tool_name == "agregar_al_carrito":
        if not user_id:
            return {"error": "Debes iniciar sesión para agregar al carrito."}
        return ops.agregar_al_carrito(
            user_id,
            arguments.get("maquina", ""),
            arguments.get("duration", 1),
            arguments.get("duration_unit", "dias"),
            arguments.get("start_date"),
            arguments.get("end_date"),
            arguments.get("cantidad", 1),
        )
    elif tool_name == "ver_carrito":
        if not user_id:
            return {"error": "Debes iniciar sesión para ver tu carrito."}
        return ops.ver_carrito(user_id)
    elif tool_name == "quitar_del_carrito":
        if not user_id:
            return {"error": "Debes iniciar sesión."}
        return ops.quitar_del_carrito(
            user_id,
            maquina_nombre=arguments.get("maquina"),
        )
    return {"error": f"Tool '{tool_name}' no encontrada"}


@app.post(
    "/api/auth/register",
    summary="Registrar nuevo usuario",
    tags=["Auth"],
)
async def register(req: RegisterRequest, request: Request):
    ip = request.client.host if request.client else "anonymous"
    if check_auth_rate_limit(ip):
        raise HTTPException(429, "Demasiados intentos. Por favor espera 1 minuto.")

    import re
    if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', req.email):
        raise HTTPException(400, "Correo electrónico inválido")
    conn = database.get_conn()
    if not conn:
        raise HTTPException(503, "Base de datos no disponible")
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE email = %s", (req.email,))
        if cur.fetchone():
            raise HTTPException(400, "Error en el registro. Verifica los datos o intenta iniciar sesión.")

        pw_hash = hash_password(req.password)
        username = req.email.split("@")[0]
        cur.execute(
            "INSERT INTO users (username, email, password_hash, display_name, role) VALUES (%s, %s, %s, %s, 'cliente') RETURNING id",
            (username, req.email, pw_hash, req.display_name or username)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        token = create_token(user_id, req.email)
        display_name = req.display_name or username
        return {"token": token, "user": {"id": user_id, "username": req.email, "email": req.email, "display_name": display_name, "name": display_name, "role": "cliente", "blocked": False}}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(500, "Error interno al procesar el registro")
    finally:
        conn.close()


@app.post(
    "/api/auth/login",
    summary="Iniciar sesión",
    tags=["Auth"],
)
async def login(req: LoginRequest, request: Request):
    ip = request.client.host if request.client else "anonymous"
    if check_auth_rate_limit(ip):
        raise HTTPException(429, "Demasiados intentos de inicio de sesión. Por favor espera 1 minuto.")

    conn = database.get_conn()
    if not conn:
        raise HTTPException(503, "Base de datos no disponible")
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, password_hash, display_name, role, username, email, blocked FROM users WHERE email = %s OR username = %s", (req.email, req.email))
        row = cur.fetchone()
        cur.close()
        if not row or not verify_password(req.password, row[1]):
            raise HTTPException(401, "Credenciales incorrectas")
        if row[6]:
            raise HTTPException(403, "Tu cuenta ha sido bloqueada por medidas de seguridad.")
        cur = conn.cursor()
        cur.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (row[0],))
        conn.commit()
        cur.close()
        user_identifier = row[5] or row[4]
        token = create_token(row[0], user_identifier)
        return {"token": token, "user": {"id": row[0], "username": user_identifier, "email": row[5], "display_name": row[2], "name": row[2], "role": row[3], "blocked": False}}

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(500, "Error interno al iniciar sesión")
    finally:
        conn.close()


@app.post(
    "/api/auth/logout",
    summary="Cerrar sesión",
    tags=["Auth"],
)
async def logout():
    return {"mensaje": "Sesión cerrada exitosamente"}



@app.get(
    "/api/auth/me",
    summary="Obtener usuario actual",
    tags=["Auth"],
)
async def get_me(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "No autenticado")
    conn = database.get_conn()
    if not conn:
        return {"id": user[0], "username": user[1], "display_name": user[1], "role": "user", "blocked": False}
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, username, display_name, role, blocked FROM users WHERE id = %s", (user[0],))
        row = cur.fetchone()
        cur.close()
        if not row:
            raise HTTPException(401, "Usuario no encontrado")
        return {"id": row[0], "username": row[1], "display_name": row[2], "role": row[3], "blocked": row[4]}
    except HTTPException:
        raise
    except Exception:
        return {"id": user[0], "username": user[1], "display_name": user[1], "role": "user", "blocked": False}
    finally:
        conn.close()


@app.get("/auth/google/login", tags=["Auth"])
async def google_login(request: Request):
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
    return await oauth.google.authorize_redirect(request, redirect_uri, prompt="select_account")


@app.get("/auth/google/callback", tags=["Auth"])
async def google_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(url=f"{frontend_url}/?error=oauth_failed")

    user_info = token.get("userinfo")
    if not user_info:
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(url=f"{frontend_url}/?error=no_user_info")

    conn = database.get_conn()
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    user_data = {
        "provider": "google",
        "provider_id": user_info.get("sub", ""),
        "email": user_info.get("email", ""),
        "name": user_info.get("name", ""),
        "picture": user_info.get("picture", ""),
    }

    if not conn:
        import base64, urllib.parse
        payload = base64.b64encode(json.dumps(user_data).encode()).decode()
        return RedirectResponse(url=f"{frontend_url}/?oauth_user={urllib.parse.quote(payload)}")

    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, display_name, role, blocked FROM users WHERE provider = 'google' AND provider_id = %s",
            (user_data["provider_id"],)
        )
        row = cur.fetchone()

        if not row:
            cur.execute(
                "SELECT id FROM users WHERE email = %s",
                (user_data["email"],)
            )
            existing = cur.fetchone()
            if existing:
                cur.execute(
                    "UPDATE users SET provider = 'google', provider_id = %s, avatar_url = %s WHERE id = %s RETURNING id, username, display_name, role, blocked",
                    (user_data["provider_id"], user_data["picture"], existing[0])
                )
                row = cur.fetchone()
            else:
                username = user_data["email"].split("@")[0]
                cur.execute(
                    """INSERT INTO users (username, email, password_hash, display_name, role, provider, provider_id, avatar_url)
                       VALUES (%s, %s, '', %s, 'user', 'google', %s, %s)
                       RETURNING id, username, display_name, role, blocked""",
                    (username, user_data["email"], user_data["name"], user_data["provider_id"], user_data["picture"])
                )
                row = cur.fetchone()

        conn.commit()
        cur.close()

        app_token = create_token(row[0], row[1])
        import base64, urllib.parse
        user_payload = base64.b64encode(json.dumps({
            "id": row[0], "username": row[1], "display_name": row[2], "role": row[3],
            "token": app_token, "picture": user_data.get("picture", ""),
            "email": user_data.get("email", ""), "blocked": row[4]
        }).encode()).decode()
        return RedirectResponse(url=f"{frontend_url}/?oauth_user={urllib.parse.quote(user_payload)}")

    except Exception as e:
        import base64, urllib.parse
        payload = base64.b64encode(json.dumps({**user_data, "error": str(e)}).encode()).decode()
        return RedirectResponse(url=f"{frontend_url}/?oauth_user={urllib.parse.quote(payload)}")
    finally:
        conn.close()


@app.get("/api/chats", tags=["Chats"])
async def list_chats(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "No autenticado")
    conn = database.get_conn()
    if not conn:
        return {"chats": []}
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT c.id, c.title, c.created_at, c.updated_at,
                      (SELECT COUNT(*) FROM conversation_messages cm
                       JOIN conversations cv ON cm.conversation_id = cv.id
                       WHERE cv.chat_id = c.id) as message_count,
                      EXISTS (
                          SELECT 1 FROM conversation_messages cm
                          JOIN conversations cv ON cm.conversation_id = cv.id
                          WHERE cv.chat_id = c.id
                            AND (cm.content LIKE '%registrar_solicitud%' OR cm.content LIKE '%SOL-%' OR cm.content LIKE '%exito%')
                      ) as has_solicitud
               FROM chats c
               WHERE c.user_id = %s
               ORDER BY c.updated_at DESC""",
            (user[0],)
        )
        rows = cur.fetchall() or []
        cur.close()
        chats_list = []
        for r in rows:
            if len(r) >= 6:
                chats_list.append({
                    "id": r[0],
                    "title": r[1],
                    "created_at": r[2].isoformat() if r[2] else None,
                    "updated_at": r[3].isoformat() if r[3] else None,
                    "message_count": r[4] or 0,
                    "has_solicitud": bool(r[5])
                })
        return {"chats": chats_list}
    except Exception:
        return {"chats": []}
    finally:
        conn.close()



@app.post("/api/chats", tags=["Chats"])
async def create_chat(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "No autenticado")

    block_msg = _check_user_blocked(user[0])
    if block_msg:
        raise HTTPException(403, block_msg)

    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    chat_id = body.get("id") or body.get("chat_id") or str(uuid.uuid4())
    conn = database.get_conn()
    if not conn:
        raise HTTPException(503, "Base de datos no disponible")
    try:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO chats (id, user_id, title) VALUES (%s, %s, 'Nuevo chat')
               ON CONFLICT (id) DO NOTHING
               RETURNING id, title, created_at""",
            (chat_id, user[0])
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
        created_at = row[2].isoformat() if row and row[2] else None
        return {"id": chat_id, "title": row[1] if row else "Nuevo chat", "created_at": created_at}
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        conn.close()


@app.put("/api/chats/{chat_id}", tags=["Chats"])
async def update_chat(chat_id: str, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "No autenticado")
    body = await request.json()
    title = body.get("title", "")
    conn = database.get_conn()
    if not conn:
        raise HTTPException(503, "Base de datos no disponible")
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE chats SET title = %s, updated_at = NOW() WHERE id = %s AND user_id = %s",
            (title, chat_id, user[0])
        )
        conn.commit()
        cur.close()
        return {"ok": True}
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        conn.close()


@app.delete("/api/chats/{chat_id}", tags=["Chats"])
async def delete_chat(chat_id: str, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "No autenticado")
    conn = database.get_conn()
    if not conn:
        raise HTTPException(503, "Base de datos no disponible")
    try:
        cur = conn.cursor()
        # Cancel any solicitudes registered in this chat/user
        cur.execute(
            """UPDATE solicitudes_renta
               SET estado = 'cancelada'
               WHERE user_id = %s AND estado = 'pendiente'""",
            (user[0],)
        )
        cur.execute("DELETE FROM chats WHERE id = %s AND user_id = %s", (chat_id, user[0]))
        conn.commit()
        cur.close()
        return {"ok": True, "message": "Chat eliminado y citas canceladas"}
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        conn.close()


@app.get("/api/chats/{chat_id}/messages", tags=["Chats"])
async def get_chat_messages(chat_id: str, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "No autenticado")
    conn = database.get_conn()
    if not conn:
        return {"messages": [], "conversation_id": None, "chat_status": None}
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, status FROM chats WHERE id = %s AND user_id = %s", (chat_id, user[0]))
        chat_row = cur.fetchone()
        if not chat_row:
            cur.close()
            raise HTTPException(404, "Chat no encontrado")
        chat_status = chat_row[1]

        cur.execute(
            "SELECT id FROM conversations WHERE chat_id = %s ORDER BY created_at DESC LIMIT 1",
            (chat_id,)
        )
        conv_row = cur.fetchone()
        conversation_id = conv_row[0] if conv_row else None

        cur.execute(
            """SELECT cm.role, cm.content
               FROM conversation_messages cm
               JOIN conversations cv ON cm.conversation_id = cv.id
               WHERE cv.chat_id = %s AND cm.role IN ('user', 'assistant')
               ORDER BY cm.created_at""",
            (chat_id,)
        )
        rows = cur.fetchall()
        cur.close()
        messages = []
        for r in rows:
            msg = {"role": r[0]}
            if r[1] is not None:
                msg["content"] = r[1]
            messages.append(msg)
        return {"messages": messages, "conversation_id": conversation_id, "chat_status": chat_status}
    except HTTPException:
        raise
    except Exception:
        return {"messages": [], "conversation_id": None, "chat_status": None}
    finally:
        conn.close()


@app.get(
    "/v1/tools",
    summary="Obtener esquemas de herramientas",
    description="Devuelve todos los tool schemas disponibles para function calling.",
    tags=["Function Calling"],
)
async def get_tools():
    return {"tools": get_all_tools()}


def _count_tokens(text: str) -> int:
    """Estimación conservadora de tokens (español + JSON ≈ 3.5 chars/token).

    Se sobreestima a propósito para compactar antes de que Ollama trunque el
    prompt en silencio. No depende de descargar tokenizers en runtime.
    """
    if not text:
        return 0
    return max(1, int(len(text) / 3.5))


def _message_tokens(message: dict) -> int:
    parts = [str(message.get("content") or ""), str(message.get("name") or "")]
    if message.get("tool_calls"):
        parts.append(json.dumps(message["tool_calls"], ensure_ascii=False, default=str))
    return _count_tokens(" ".join(parts))


def _prompt_tokens(messages_raw: list) -> int:
    return sum(_message_tokens(m) for m in messages_raw)


def _tool_content(result: Any) -> str:
    """Serializa el resultado de una herramienta y lo trunca antes de
    devolverlo al modelo. Un tool result completo puede ocupar miles de
    tokens y desplazar el historial de la conversación."""
    text = json.dumps(result, ensure_ascii=False, default=str)
    limit = config.TOOL_RESULT_MAX_CHARS
    if len(text) > limit:
        text = text[:limit] + "... [resultado truncado]"
    return text


def _compact_messages_history(messages_raw: list, max_tokens: int = None) -> tuple:
    """
    Compacta el historial cuando el prompt supera el presupuesto real.
    Conserva el system prompt, un resumen de hechos anteriores y los últimos
    turnos completos. Nunca parte un par assistant(tool_calls) / tool.
    Returns: (new_messages_raw, was_compacted)
    """
    if not messages_raw:
        return messages_raw, False

    max_tokens = max_tokens or config.COMPACT_THRESHOLD_TOKENS
    keep_recent = max(2, config.COMPACT_KEEP_RECENT)

    sys_msg = messages_raw[0] if messages_raw[0].get("role") == "system" else None
    dialogue = messages_raw[1:] if sys_msg else messages_raw

    if _prompt_tokens(messages_raw) <= max_tokens or len(dialogue) <= keep_recent:
        return messages_raw, False

    cut = max(0, len(dialogue) - keep_recent)
    # Si el primer mensaje conservado es un tool result, su assistant quedó
    # fuera: retrocedemos para no romper el protocolo de tool calling.
    while cut > 0 and cut < len(dialogue) and dialogue[cut].get("role") == "tool":
        cut -= 1
    if cut <= 0:
        return messages_raw, False

    older_messages = dialogue[:cut]
    recent_messages = dialogue[cut:]

    key_terms = ["piso", "losa", "muro", "terreno", "pasillo", "cm", "ancho", "excavación",
                 "corte", "demol", "casa", "obra", "solicitud", "cotización", "cliente",
                 "rechazo", "eléctrico", "electrico", "neumático", "neumatico", "gasolina",
                 "diésel", "diesel", "presupuesto", "mxn", "$", "días", "dias", "operador",
                 "flete", "local", "comercial", "fecha", "máquina", "maquina"]

    facts = []
    for m in older_messages:
        role = m.get("role")
        if role not in ("user", "assistant"):
            continue  # los resultados crudos y memorias previas no se re-resumen
        content = str(m.get("content") or "").strip()
        if not content:
            continue
        if role == "user" or any(k in content.lower() for k in key_terms):
            label = "Cliente" if role == "user" else "Asesor"
            facts.append(f"- {label}: {content[:300]}")

    # Conservamos lo más reciente de la memoria antigua y acotamos el resumen
    summary_body = "\n".join(facts[-12:]) if facts else "Conversación de renta de maquinaria en curso."
    if len(summary_body) > 2800:
        summary_body = summary_body[-2800:]

    compact_summary_text = (
        "[MEMORIA COMPACTADA DEL HISTORIAL PREVIO — CONTEXTO CONTINUO]\n"
        "La conversación ya está avanzada (Turno 2 o posterior). NO saludes de nuevo "
        "ni repitas el sondeo inicial. Responde directamente con estos antecedentes:\n"
        + summary_body
    )

    new_history = []
    if sys_msg:
        new_history.append(sys_msg)
    new_history.append({"role": "system", "content": compact_summary_text})
    new_history.extend(recent_messages)
    return new_history, True


@app.post(
    "/v1/chat/completions",
    summary="Chat con Function Calling (OpenAI-compatible)",
    description="Endpoint compatible con OpenAI /v1/chat/completions que soporta tool calling. "
                "Acepta messages + tools y ejecuta automáticamente las funciones del catálogo. "
                "Diseñado para ser consumido por IAs o frontends que hablen el protocolo OpenAI.",
    tags=["Function Calling"],
)
async def chat_completions(req: ChatCompletionRequest, request: Request = None) -> ChatCompletionResponse:
    start_time = time.time()
    model = req.model or config.OLLAMA_MODEL
    ollama_client.model = model

    session_id = req.conversation_id or str(uuid.uuid4())

    user_msg = ""
    for m in reversed(req.messages):
        if m.role == "user" and m.content:
            user_msg = m.content
            break

    # Check for unclear input — respond directly without strike
    if security.detect_unclear_input(user_msg):
        unclear_msg = "No entendí tu mensaje. ¿Podrías explicarme con más detalle lo que necesitas sobre maquinaria pesada?"
        elapsed = (time.time() - start_time) * 1000
        log_observability(
            session_id=session_id,
            user_prompt=user_msg,
            system_response="",
            ttft_ms=0,
            total_latency_ms=elapsed,
            tools_executed=[],
        )
        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
            created=int(time.time()),
            model=model,
            choices=[{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": unclear_msg,
                },
                "finish_reason": "stop",
            }],
            conversation_id=session_id,
        )

    # Check user block and chat status
    user = get_current_user(request) if request else None
    user_id = user[0] if user else None
    block_msg = None
    chat_closed_msg = None
    if user_id:
        block_msg = _check_user_blocked(user_id)
    if not block_msg and req.chat_id and user_id:
        status = _get_chat_status(req.chat_id, user_id)
        if status == "closed_security":
            chat_closed_msg = "Por seguridad, este chat fue cerrado."

    blocked, block_reason = security.validate_input(user_msg, session_id)
    if blocked or block_msg or chat_closed_msg:
        # Increment strike if blocked by off-topic detection
        if blocked and not block_msg and not chat_closed_msg and req.chat_id and user_id:
            strike_result = _increment_strike(req.chat_id, user_id)
            if strike_result["chat_closed"]:
                chat_closed_msg = strike_result["message"]

        elapsed = (time.time() - start_time) * 1000
        response_msg = block_msg or chat_closed_msg or "Lo siento, no puedo procesar esa solicitud. Por favor, reformula tu pregunta."
        log_observability(
            session_id=session_id,
            user_prompt=user_msg,
            system_response="",
            ttft_ms=0,
            total_latency_ms=elapsed,
            tools_executed=[],
            was_blocked=True,
            block_reason=block_reason or block_msg or chat_closed_msg or "",
        )
        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
            created=int(time.time()),
            model=model,
            choices=[{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_msg,
                },
                "finish_reason": "stop",
            }],
            conversation_id=session_id,
        )

    messages_raw = []
    for m in req.messages:
        msg = {"role": m.role}
        if m.content is not None:
            msg["content"] = m.content
        if m.tool_calls:
            msg["tool_calls"] = m.tool_calls
        if m.tool_call_id:
            msg["tool_call_id"] = m.tool_call_id
        if m.name:
            msg["name"] = m.name
        messages_raw.append(msg)

    # Router: classify intent and select sub-agent
    from src.agents import Router, RAGAgent, TransactionalAgent
    intent = Router.classify(user_msg)

    # Off-topic → reject immediately
    if intent == "off_topic":
        rejection = "Esta asistente solo atiende consultas de renta de maquinaria pesada. ¿En qué puedo ayudarte?"
        elapsed = (time.time() - start_time) * 1000
        log_observability(
            session_id=session_id,
            user_prompt=user_msg,
            system_response="",
            ttft_ms=0,
            total_latency_ms=elapsed,
            tools_executed=[],
            was_blocked=True,
            block_reason="off_topic",
        )
        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
            created=int(time.time()),
            model=model,
            choices=[{"index": 0, "message": {"role": "assistant", "content": rejection}, "finish_reason": "stop"}],
            conversation_id=session_id,
        )

    # Select sub-agent based on intent
    agent = RAGAgent(ollama_client) if intent == "rag" else TransactionalAgent(ollama_client)

    # Set agent-specific system prompt
    sys_prompt = agent.get_system_prompt()
    if not messages_raw or messages_raw[0].get("role") != "system":
        messages_raw.insert(0, {"role": "system", "content": sys_prompt})
    else:
        messages_raw[0]["content"] = sys_prompt

    if req.user_name or req.user_email:
        user_info = "\n\nDATOS DEL USUARIO AUTENTICADO POR OAUTH:"
        if req.user_name:
            user_info += f"\n- Nombre (cliente): {req.user_name}"
        if req.user_email:
            user_info += f"\n- Contacto (correo): {req.user_email}"
        user_info += "\nPuedes usar esta información directamente para llenar los campos 'cliente' y 'contacto' en las herramientas (como registrar_solicitud o generar_cotizacion).\nNO le vuelvas a pedir estos datos al usuario. Antes de llamar a registrar_solicitud, simplemente confírmale al usuario: '¿Los datos [nombre] y [contacto] están bien? ¿Procedemos?' y si dice que sí, ejecútalo."
        messages_raw[0]["content"] += user_info

    today_str = date.today().strftime("%Y-%m-%d")
    messages_raw[0]["content"] += f"\n\nHOY ES: {today_str}. Las solicitudes de renta deben ser para fechas futuras (al menos un día después de hoy). Si el usuario pide una fecha anterior a hoy, INDÍCALE que la fecha ya pasó."

    tools = agent.get_tools() if not req.tools else req.tools
    max_tool_rounds = config.MAX_TOOL_ROUNDS
    tools_executed = []

    messages_raw, was_compacted = _compact_messages_history(messages_raw)

    for _ in range(max_tool_rounds):
        ollama_response = ollama_client.chat(messages_raw, tools=tools)

        choice = ollama_response.get("message", {})
        content = choice.get("content", "")
        tool_calls = choice.get("tool_calls")

        # Parse text-based tool call if native tool_calls is empty
        text_tool_call = None
        if not tool_calls and content:
            text_tool_call = parse_text_tool_call(content)

        if not tool_calls and not text_tool_call:
            if not content and tools_executed:
                # Model returned empty with no tool call but tools were executed — use fallback
                final_content = _format_tool_fallback(tools_executed, messages_raw)
            else:
                final_content = clean_latex(content)

            # Anti-tool-leakage check: If model leaks internal tool function names or technical code explanations
            _tool_leak_pattern = re.compile(r'\b(buscar_maquinaria|comparar_maquinas|generar_cotizacion|registrar_solicitud|obtener_categoria|detalle_maquinaria|listar_categorias|listar_proyectos|obtener_proyecto|recomendar_por_trabajo|calcular_costo_renta|calcular_costo_proyecto|validar_fecha)\b', re.IGNORECASE)
            if _tool_leak_pattern.search(final_content) or "tool_call" in final_content.lower() or ("función" in final_content.lower() and "nombre común" in final_content.lower()):
                final_content = "Como tu Asesor de Maquinaria Pesada en Rentek, puedo ayudarte a:\n\n1. **Indagar las necesidades de tu proyecto**: Recomendarte la maquinaria ideal según el terreno, espacio y alcance de la obra.\n2. **Consultar especificaciones y comparar equipos**: Evaluar fichas técnicas y ventajas entre distintas máquinas.\n3. **Verificar disponibilidad y calcular costos**: Obtener desgloses transparentes con descuentos por duración de renta.\n4. **Generar tu solicitud formal de renta y cotizaciones**: Tramitar tu folio oficial de alquiler.\n\n¿En qué tipo de proyecto estás trabajando para asesorarte?"

            # Post-response off-topic detection and strike increment
            if user_id and req.chat_id and not tools_executed:
                if security.detect_refusal(final_content) or security.detect_off_topic(user_msg):
                    strike_result = _increment_strike(req.chat_id, user_id)
                    if strike_result["chat_closed"]:
                        final_content = strike_result["message"]

            elapsed = (time.time() - start_time) * 1000
            log_observability(
                session_id=session_id,
                user_prompt=user_msg,
                system_response=final_content,
                ttft_ms=elapsed * 0.3,
                total_latency_ms=elapsed,
                tools_executed=tools_executed,
            )

            return ChatCompletionResponse(
                id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
                created=int(time.time()),
                model=model,
                choices=[{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": final_content,
                    },
                    "finish_reason": "stop",
                }],
                conversation_id=session_id,
            )

        if tool_calls:
            assistant_msg = {"role": "assistant", "content": content}
            assistant_msg["tool_calls"] = tool_calls
            messages_raw.append(assistant_msg)

            for tc in tool_calls:
                func = tc.get("function", tc)
                tool_name = func.get("name", "")
                try:
                    raw_args = func.get("arguments", "{}")
                    if isinstance(raw_args, str):
                        arguments = json.loads(raw_args)
                    else:
                        arguments = raw_args
                except json.JSONDecodeError:
                    arguments = {}

                tool_result = execute_tool(tool_name, arguments, messages_raw, user_id)
                if tool_result is None:
                    tool_result = {"error": f"Tool '{tool_name}' no devolvió resultado"}
                tool_call_id = tc.get("id", f"call_{uuid.uuid4().hex[:12]}")

                tools_executed.append({
                    "function": tool_name,
                    "arguments": arguments,
                    "status": "SUCCESS" if "error" not in tool_result else "ERROR",
                })

                messages_raw.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "name": tool_name,
                    "content": _tool_content(tool_result),
                })
        else:
            # Handle text_tool_call
            tool_name, arguments, matched_text = text_tool_call
            clean_content = content.replace(matched_text, "").strip()
            assistant_msg = {"role": "assistant", "content": clean_content}
            messages_raw.append(assistant_msg)

            tool_result = execute_tool(tool_name, arguments, messages_raw, user_id)
            if tool_result is None:
                tool_result = {"error": f"Tool '{tool_name}' no devolvió resultado"}
            tool_call_id = f"call_{uuid.uuid4().hex[:12]}"

            tools_executed.append({
                "function": tool_name,
                "arguments": arguments,
                "status": "SUCCESS" if "error" not in tool_result else "ERROR",
            })

            messages_raw.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "name": tool_name,
                "content": _tool_content(tool_result),
            })

    final_response = ollama_client.chat(messages_raw, tools=tools)
    final_content = clean_latex(final_response.get("message", {}).get("content", ""))

    # Fallback: if model returned empty but tools were executed, format a response from tool results
    if not final_content and tools_executed:
        final_content = _format_tool_fallback(tools_executed, messages_raw)

    # Force Spanish — if response is in English, replace with redirect
    _en_pattern = re.compile(r'\b(Sure|could|would|please|provide|details|assist|let\s+me\s+know|what\s+can\s+I|how\s+can\s+I|do\s+you\s+need)\b', re.IGNORECASE)
    if _en_pattern.search(final_content) and not re.search(r'[áéíóúñ]', final_content):
        final_content = "Esta asistente solo atiende consultas de renta de maquinaria pesada. ¿En qué puedo ayudarte?"

    # Post-response off-topic detection and strike increment
    if user_id and req.chat_id and not tools_executed:
        if security.detect_refusal(final_content) or security.detect_off_topic(user_msg):
            strike_result = _increment_strike(req.chat_id, user_id)
            if strike_result["chat_closed"]:
                final_content = strike_result["message"]

    elapsed = (time.time() - start_time) * 1000
    log_observability(
        session_id=session_id,
        user_prompt=user_msg,
        system_response=final_content,
        ttft_ms=elapsed * 0.3,
        total_latency_ms=elapsed,
        tools_executed=tools_executed,
    )

    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
        created=int(time.time()),
        model=model,
        choices=[{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": final_content,
            },
            "finish_reason": "stop",
        }],
        conversation_id=session_id,
    )


def _save_chat_messages(session_id: str, chat_id: str, user_msg: str, assistant_msg: str, tools_executed: list):
    conn = database.get_conn()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM conversations WHERE id = %s", (session_id,))
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO conversations (id, chat_id) VALUES (%s, %s)",
                (session_id, chat_id)
            )

        cur.execute(
            """INSERT INTO conversation_messages (conversation_id, role, content)
               VALUES (%s, 'user', %s)""",
            (session_id, user_msg)
        )

        cur.execute(
            """INSERT INTO conversation_messages (conversation_id, role, content)
               VALUES (%s, 'assistant', %s)""",
            (session_id, assistant_msg)
        )

        if chat_id:
            cur.execute("UPDATE chats SET updated_at = NOW() WHERE id = %s", (chat_id,))

        conn.commit()
        cur.close()
    except Exception:
        pass
    finally:
        conn.close()


def _check_user_blocked(user_id: int) -> Optional[str]:
    conn = database.get_conn()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT blocked, closed_chats FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        if row and row[0]:
            return "Tu cuenta ha sido bloqueada por medidas de seguridad."
        if row and row[1] >= 3:
            cur = conn.cursor()
            cur.execute("UPDATE users SET blocked = TRUE, blocked_at = NOW() WHERE id = %s AND blocked = FALSE", (user_id,))
            conn.commit()
            cur.close()
            return "Tu cuenta ha sido bloqueada por medidas de seguridad."
        return None
    except Exception:
        return None
    finally:
        conn.close()


def _get_chat_status(chat_id: str, user_id: int) -> Optional[str]:
    conn = database.get_conn()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT status FROM chats WHERE id = %s AND user_id = %s", (chat_id, user_id))
        row = cur.fetchone()
        cur.close()
        if row and row[0] == "closed_security":
            return "closed_security"
        if row:
            return row[0]
        return None
    except Exception:
        return None
    finally:
        conn.close()


def _increment_strike(chat_id: str, user_id: int) -> dict:
    result = {"off_topic_strikes": 0, "chat_closed": False, "user_blocked": False, "message": ""}
    conn = database.get_conn()
    if not conn:
        return result
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE chats SET off_topic_strikes = off_topic_strikes + 1 WHERE id = %s RETURNING off_topic_strikes",
            (chat_id,)
        )
        row = cur.fetchone()
        if row:
            result["off_topic_strikes"] = row[0]
            if row[0] >= 3:
                cur.execute(
                    "UPDATE chats SET status = 'closed_security' WHERE id = %s",
                    (chat_id,)
                )
                result["chat_closed"] = True
                result["message"] = "Por seguridad, este chat fue cerrado."

                cur.execute(
                    "UPDATE users SET closed_chats = closed_chats + 1 WHERE id = %s RETURNING closed_chats",
                    (user_id,)
                )
                user_row = cur.fetchone()
                if user_row and user_row[0] >= 3:
                    cur.execute(
                        "UPDATE users SET blocked = TRUE, blocked_at = NOW() WHERE id = %s",
                        (user_id,)
                    )
                    result["user_blocked"] = True
        conn.commit()
        cur.close()
    except Exception:
        pass
    finally:
        conn.close()
    return result


@app.post(
    "/v1/chat/completions/stream",
    summary="Chat con Function Calling y Streaming (SSE)",
    description="Endpoint con streaming usando Server-Sent Events. Devuelve tokens en tiempo real.",
    tags=["Function Calling"],
)
async def chat_completions_stream(req: ChatCompletionRequest, request: Request = None):
    start_time = time.time()
    model = req.model or config.OLLAMA_MODEL
    ollama_client.model = model

    session_id = req.conversation_id or str(uuid.uuid4())

    # Check user block and chat status
    user = get_current_user(request) if request else None
    user_id = user[0] if user else None
    block_msg = None
    chat_closed_msg = None
    if user_id:
        block_msg = _check_user_blocked(user_id)
    if not block_msg and req.chat_id and user_id:
        status = _get_chat_status(req.chat_id, user_id)
        if status == "closed_security":
            chat_closed_msg = "Por seguridad, este chat fue cerrado."

    if req.chat_id:
        conn = database.get_conn()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    "UPDATE conversations SET chat_id = %s, user_id = (SELECT user_id FROM chats WHERE id = %s) WHERE id = %s",
                    (req.chat_id, req.chat_id, session_id)
                )
                cur.execute(
                    "UPDATE chats SET updated_at = NOW() WHERE id = %s",
                    (req.chat_id,)
                )
                conn.commit()
                cur.close()
            except Exception:
                pass
            finally:
                conn.close()

    user_msg = ""
    for m in reversed(req.messages):
        if m.role == "user" and m.content:
            user_msg = m.content
            break

    # Check for unclear input — respond directly without strike
    if security.detect_unclear_input(user_msg):
        unclear_msg = "No entendí tu mensaje. ¿Podrías explicarme con más detalle lo que necesitas sobre maquinaria pesada?"

        async def unclear_stream():
            yield f"data: {json.dumps({'type': 'token', 'content': unclear_msg})}\n\n"
            yield "data: [DONE]\n\n"

        elapsed = (time.time() - start_time) * 1000
        log_observability(
            session_id=session_id,
            user_prompt=user_msg,
            system_response=unclear_msg,
            ttft_ms=0,
            total_latency_ms=elapsed,
            tools_executed=[],
        )
        return StreamingResponse(unclear_stream(), media_type="text/event-stream")

    blocked, block_reason = security.validate_input(user_msg, session_id)
    if blocked or block_msg or chat_closed_msg:
        # Increment strike if blocked by off-topic detection
        if blocked and not block_msg and not chat_closed_msg and req.chat_id and user_id:
            strike_result = _increment_strike(req.chat_id, user_id)
            if strike_result["chat_closed"]:
                chat_closed_msg = strike_result["message"]

        elapsed = (time.time() - start_time) * 1000
        response_msg = block_msg or chat_closed_msg or "Solicitud bloqueada por seguridad"
        log_observability(
            session_id=session_id,
            user_prompt=user_msg,
            system_response="",
            ttft_ms=0,
            total_latency_ms=elapsed,
            tools_executed=[],
            was_blocked=True,
            block_reason=block_reason or block_msg or chat_closed_msg or "",
        )

        async def blocked_stream():
            yield f"data: {json.dumps({'type': 'error', 'content': response_msg})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(blocked_stream(), media_type="text/event-stream")

    messages_raw = []
    for m in req.messages:
        msg = {"role": m.role}
        if m.content is not None:
            msg["content"] = m.content
        if m.tool_calls:
            msg["tool_calls"] = m.tool_calls
        if m.tool_call_id:
            msg["tool_call_id"] = m.tool_call_id
        if m.name:
            msg["name"] = m.name
        messages_raw.append(msg)

    # Router: classify intent and select sub-agent
    from src.agents import Router, RAGAgent, TransactionalAgent
    intent = Router.classify(user_msg)

    if intent == "off_topic":
        rejection = "Esta asistente solo atiende consultas de renta de maquinaria pesada. ¿En qué puedo ayudarte?"
        async def off_topic_stream():
            yield f"data: {json.dumps({'type': 'token', 'content': rejection})}\n\n"
            yield "data: [DONE]\n\n"
        elapsed = (time.time() - start_time) * 1000
        log_observability(
            session_id=session_id, user_prompt=user_msg, system_response="",
            ttft_ms=0, total_latency_ms=elapsed, tools_executed=[], was_blocked=True, block_reason="off_topic",
        )
        return StreamingResponse(off_topic_stream(), media_type="text/event-stream")

    agent = RAGAgent(ollama_client) if intent == "rag" else TransactionalAgent(ollama_client)

    sys_prompt = agent.get_system_prompt()
    if not messages_raw or messages_raw[0].get("role") != "system":
        messages_raw.insert(0, {"role": "system", "content": sys_prompt})
    else:
        messages_raw[0]["content"] = sys_prompt

    if req.user_name or req.user_email:
        user_info = "\n\nDATOS DEL USUARIO AUTENTICADO POR OAUTH:"
        if req.user_name:
            user_info += f"\n- Nombre (cliente): {req.user_name}"
        if req.user_email:
            user_info += f"\n- Contacto (correo): {req.user_email}"
        user_info += "\nPuedes usar esta información directamente para llenar los campos 'cliente' y 'contacto' en las herramientas (como registrar_solicitud o generar_cotizacion).\nNO le vuelvas a pedir estos datos al usuario. Antes de llamar a registrar_solicitud, simplemente confírmale al usuario: '¿Los datos [nombre] y [contacto] están bien? ¿Procedemos?' y si dice que sí, ejecútalo."
        messages_raw[0]["content"] += user_info

    today_str = date.today().strftime("%Y-%m-%d")
    messages_raw[0]["content"] += f"\n\nHOY ES: {today_str}. Las solicitudes de renta deben ser para fechas futuras (al menos un día después de hoy). Si el usuario pide una fecha anterior a hoy, INDÍCALE que la fecha ya pasó."

    tools = agent.get_tools() if not req.tools else req.tools
    max_tool_rounds = config.MAX_TOOL_ROUNDS
    tools_executed = []
    SEARCH_TOOLS = {"query_maquinaria", "buscar_maquinaria", "detalle_maquinaria", "listar_categorias", "obtener_categoria", "listar_proyectos", "obtener_proyecto"}
    messages_raw, was_compacted = _compact_messages_history(messages_raw)

    async def stream_generator():
        nonlocal tools_executed
        full_response = ""
        tool_round = 0
        error_msg = None

        try:
            for round_num in range(max_tool_rounds):
                tool_round = round_num
                ttft_sent = False
                stream_start = time.time()
                round_response = ""
                found_native_tool_calls = False

                yield f"data: {json.dumps({'type': 'status', 'status': 'thinking'})}\n\n"

                async for chunk in ollama_client.chat_stream_async(messages_raw, tools=tools):
                    if not ttft_sent:
                        ttft_ms = (time.time() - stream_start) * 1000
                        yield f"data: {json.dumps({'type': 'ttft', 'ms': round(ttft_ms, 1)})}\n\n"
                        ttft_sent = True

                    if chunk.get("message", {}).get("tool_calls"):
                        found_native_tool_calls = True
                        tool_calls = chunk["message"]["tool_calls"]
                        assistant_msg = {"role": "assistant", "content": chunk["message"].get("content", "")}
                        assistant_msg["tool_calls"] = tool_calls
                        messages_raw.append(assistant_msg)

                        for tc in tool_calls:
                            func = tc.get("function", tc)
                            tool_name = func.get("name", "")
                            if tool_name in SEARCH_TOOLS:
                                yield f"data: {json.dumps({'type': 'status', 'status': 'searching'})}\n\n"


                            else:
                                yield f"data: {json.dumps({'type': 'status', 'status': 'executing'})}\n\n"



                            try:
                                raw_args = func.get("arguments", "{}")
                                if isinstance(raw_args, str):
                                    arguments = json.loads(raw_args)
                                else:
                                    arguments = raw_args
                            except json.JSONDecodeError:
                                arguments = {}

                            tool_result = execute_tool(tool_name, arguments, messages_raw, user_id)
                            if tool_result is None:
                                tool_result = {"error": f"Tool '{tool_name}' no devolvió resultado"}
                            tool_call_id = tc.get("id", f"call_{uuid.uuid4().hex[:12]}")

                            tools_executed.append({
                                "function": tool_name,
                                "arguments": arguments,
                                "status": "SUCCESS" if "error" not in tool_result else "ERROR",
                            })

                            messages_raw.append({
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "name": tool_name,
                                "content": _tool_content(tool_result),
                            })

                        break

                    elif chunk.get("message", {}).get("content"):
                        token = chunk["message"]["content"]

                        token = token.replace(r'\[', '').replace(r'\]', '').replace(r'	imes', ' x ').replace(r'\$', '$')
                        token = re.sub(r'```json\s*', '', token).replace('```', '')

                        round_response += token

                        text_call = parse_text_tool_call(round_response)
                        if text_call:
                            tool_name, arguments, matched_text = text_call
                            if tool_name in SEARCH_TOOLS:
                                yield f"data: {json.dumps({'type': 'status', 'status': 'searching'})}\n\n"


                            else:
                                yield f"data: {json.dumps({'type': 'status', 'status': 'executing'})}\n\n"



                            tool_result = execute_tool(tool_name, arguments, messages_raw, user_id)
                            if tool_result is None:
                                tool_result = {"error": f"Tool '{tool_name}' no devolvió resultado"}

                            tools_executed.append({
                                "function": tool_name,
                                "arguments": arguments,
                                "status": "SUCCESS" if "error" not in tool_result else "ERROR",
                            })

                            clean_text = round_response.replace(matched_text, "").strip()
                            if clean_text:
                                clean_text = clean_latex(clean_text)
                                full_response += clean_text
                                yield f"data: {json.dumps({'type': 'token', 'content': clean_text})}\n\n"



                            messages_raw.append({"role": "assistant", "content": round_response})
                            messages_raw.append({
                                "role": "tool",
                                "tool_call_id": f"call_{uuid.uuid4().hex[:12]}",
                                "name": tool_name,
                                "content": _tool_content(tool_result),
                            })
                            found_native_tool_calls = True
                            break
                        else:
                            full_response += token
                            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"



                    if chunk.get("done"):
                        break
                if found_native_tool_calls:
                    continue
                break

            full_response = clean_latex(full_response)
            if full_response:
                full_response = re.sub(r'```json\s*', '', full_response)
                full_response = re.sub(r'```\s*', '', full_response).strip()

            # Fallback: if streaming response is empty but tools were executed, format from tool results
            if not full_response and tools_executed:
                full_response = _format_tool_fallback(tools_executed, messages_raw)
                yield f"data: {json.dumps({'type': 'token', 'content': full_response})}\n\n"

            # Anti-tool-leakage check: If model leaks internal tool function names or technical code explanations
            _tool_leak_pattern = re.compile(r'\b(buscar_maquinaria|comparar_maquinas|generar_cotizacion|registrar_solicitud|obtener_categoria|detalle_maquinaria|listar_categorias|listar_proyectos|obtener_proyecto|recomendar_por_trabajo|calcular_costo_renta|calcular_costo_proyecto|validar_fecha)\b', re.IGNORECASE)
            if _tool_leak_pattern.search(full_response) or "tool_call" in full_response.lower() or ("función" in full_response.lower() and "nombre común" in full_response.lower()):
                full_response = "Como tu Asesor de Maquinaria Pesada en Rentek, puedo ayudarte a:\n\n1. **Indagar las necesidades de tu proyecto**: Recomendarte la maquinaria ideal según el terreno, espacio y alcance de la obra.\n2. **Consultar especificaciones y comparar equipos**: Evaluar fichas técnicas y ventajas entre distintas máquinas.\n3. **Verificar disponibilidad y calcular costos**: Obtener desgloses transparentes con descuentos por duración de renta.\n4. **Generar tu solicitud formal de renta y cotizaciones**: Tramitar tu folio oficial de alquiler.\n\n¿En qué tipo de proyecto estás trabajando para asesorarte?"

            # Post-response off-topic detection and strike increment
            if user_id and req.chat_id and not tools_executed:
                if security.detect_refusal(full_response) or security.detect_off_topic(user_msg):
                    strike_result = _increment_strike(req.chat_id, user_id)
                    if strike_result["chat_closed"]:
                        full_response = strike_result["message"]

            elapsed = (time.time() - start_time) * 1000
            log_observability(
                session_id=session_id,
                user_prompt=user_msg,
                system_response=full_response,
                ttft_ms=elapsed * 0.3,
                total_latency_ms=elapsed,
                tools_executed=tools_executed,
            )

            _save_chat_messages(session_id, req.chat_id, user_msg, full_response, tools_executed)

            token_count = _count_tokens(full_response)
            context_tokens = _prompt_tokens(messages_raw)
            max_context = config.NUM_CTX
            yield f"data: {json.dumps({'type': 'done', 'conversation_id': session_id, 'tokens': token_count, 'context_tokens': context_tokens, 'max_context': max_context, 'was_compacted': was_compacted})}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as e:
            error_msg = str(e)
            yield f"data: {json.dumps({'type': 'error', 'content': 'Ocurrió un error al procesar tu solicitud. Intenta de nuevo.'})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")


@app.get(
    "/api/observability",
    summary="Obtener logs de observabilidad",
    description="Devuelve los últimos registros de observabilidad con métricas de rendimiento.",
    tags=["Observabilidad"],
)
async def get_observability_logs(request: Request, limit: int = 50):
    user = require_admin(request)
    conn = database.get_conn()
    if not conn:
        return {"logs": [], "message": "Base de datos no disponible"}
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT id, session_id, timestamp, user_prompt, system_response,
                      ttft_ms, total_latency_ms, tokens_per_second,
                      was_blocked, block_reason, tools_executed, model_used
               FROM observability_logs
               ORDER BY timestamp DESC
               LIMIT %s""",
            (limit,)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()

        logs = []
        for row in rows:
            logs.append({
                "id": row[0],
                "session_id": row[1],
                "timestamp": row[2].isoformat() if row[2] else None,
                "user_prompt": row[3],
                "system_response": row[4][:200] if row[4] else "",
                "ttft_ms": round(row[5], 1) if row[5] else 0,
                "total_latency_ms": round(row[6], 1) if row[6] else 0,
                "tokens_per_second": round(row[7], 2) if row[7] else 0,
                "was_blocked": row[8],
                "block_reason": row[9],
                "tools_executed": row[10] if isinstance(row[10], list) else json.loads(row[10]) if row[10] else [],
                "model_used": row[11],
            })
        return {"logs": logs, "total": len(logs)}
    except Exception:
        return {"logs": [], "error": "Error al obtener registros"}


@app.get(
    "/api/admin/users",
    summary="Listar usuarios (solo administradores)",
    description="Devuelve los usuarios registrados sin datos sensibles como el hash de contraseña.",
    tags=["Administración"],
)
async def admin_list_users(request: Request):
    require_admin(request)
    conn = database.get_conn()
    if not conn:
        raise HTTPException(503, "Base de datos no disponible")
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT id, username, email, display_name, role, blocked,
                      blocked_at, created_at, last_login
               FROM users
               ORDER BY created_at DESC NULLS LAST, id"""
        )
        rows = cur.fetchall() or []
        cur.close()
        users = []
        for row in rows:
            users.append({
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "display_name": row[3],
                "role": row[4],
                "blocked": bool(row[5]),
                "blocked_at": row[6].isoformat() if row[6] else None,
                "created_at": row[7].isoformat() if row[7] else None,
                "last_login": row[8].isoformat() if row[8] else None,
            })
        return {"users": users, "total": len(users)}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(500, "Error al obtener los usuarios")
    finally:
        conn.close()


def _get_admin_target(cur, user_id: int):
    cur.execute(
        "SELECT id, username, role, blocked FROM users WHERE id = %s",
        (user_id,),
    )
    return cur.fetchone()


@app.post(
    "/api/admin/users/{user_id}/block",
    summary="Bloquear usuario (solo administradores)",
    tags=["Administración"],
)
async def admin_block_user(user_id: int, request: Request):
    actor = require_admin(request)
    if user_id == actor["id"]:
        raise HTTPException(400, "No puedes bloquear tu propia cuenta")
    conn = database.get_conn()
    if not conn:
        raise HTTPException(503, "Base de datos no disponible")
    try:
        cur = conn.cursor()
        target = _get_admin_target(cur, user_id)
        if not target:
            raise HTTPException(404, "Usuario no encontrado")
        if target[2] == "admin":
            raise HTTPException(400, "No puedes bloquear a otro administrador")
        cur.execute(
            "UPDATE users SET blocked = TRUE, blocked_at = NOW() WHERE id = %s",
            (user_id,),
        )
        conn.commit()
        cur.close()
        return {"ok": True, "message": f"Usuario {target[1]} bloqueado"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(500, "Error al bloquear el usuario")
    finally:
        conn.close()


@app.post(
    "/api/admin/users/{user_id}/unblock",
    summary="Desbloquear usuario (solo administradores)",
    tags=["Administración"],
)
async def admin_unblock_user(user_id: int, request: Request):
    require_admin(request)
    conn = database.get_conn()
    if not conn:
        raise HTTPException(503, "Base de datos no disponible")
    try:
        cur = conn.cursor()
        target = _get_admin_target(cur, user_id)
        if not target:
            raise HTTPException(404, "Usuario no encontrado")
        cur.execute(
            "UPDATE users SET blocked = FALSE, blocked_at = NULL, closed_chats = 0 WHERE id = %s",
            (user_id,),
        )
        conn.commit()
        cur.close()
        return {"ok": True, "message": f"Usuario {target[1]} desbloqueado"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(500, "Error al desbloquear el usuario")
    finally:
        conn.close()


@app.get("/", tags=["Salud"])
async def root():
    db_status = "disponible" if usar_db() else "no disponible"
    return {
        "api": "RAG - Renta de Maquinaria Pesada",
        "version": "2.0.0",
        "postgresql": db_status,
        "docs": "/docs" if enable_docs else None,
    }


@app.post(
    "/api/query",
    summary="Preguntar al sistema RAG",
    description="Tool: query_maquinaria(question, top_k). "
                "Haz una pregunta en lenguaje natural sobre maquinaria pesada.",
    tags=["RAG"],
)
async def query(req: QueryRequest, request: Request) -> QueryResponse:
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Autenticación requerida para realizar consultas RAG")
    result = rag.query(req.question, req.top_k)
    return QueryResponse(
        answer=result["answer"],
        sources=result["sources"],
        latency_ms=result["latency_ms"],
    )



@app.get(
    "/api/catalog",
    summary="Obtener catálogo estructurado completo de maquinaria para e-commerce",
    description="Consulta PostgreSQL directamente para retornar la lista de maquinaria con categorías, especificaciones e imágenes.",
    tags=["Catálogo"],
)
async def get_catalog():
    if usar_db():
        data = database.obtener_catalogo()
        if data and len(data) > 0:
            return data
    return catalogo_md.get_catalog_flat() if hasattr(catalogo_md, "get_catalog_flat") else []


@app.get(
    "/api/maquinaria",
    summary="Listar categorías de maquinaria",
    description="Tool: listar_categorias(). "
                "Obtén todas las categorías de maquinaria disponibles "
                "con un resumen de las máquinas en cada una.",
    tags=["Catálogo"],
)
async def listar_categorias():
    return listar_categorias_fallback()


@app.get(
    "/api/maquinaria/{categoria}",
    summary="Obtener una categoría completa",
    description="Tool: obtener_categoria(nombre). "
                "Obtén todos los detalles de una categoría específica "
                "con especificaciones, precios, FAQ, etc.",
    tags=["Catálogo"],
)
async def obtener_categoria(categoria: str):
    data = obtener_categoria_fallback(categoria)
    if not data:
        disponibles = [c for c in catalogo_md.get_categorias().keys()]
        raise HTTPException(
            status_code=404,
            detail=f"Categoría '{categoria}' no encontrada. Disponibles: {disponibles}",
        )
    return data


@app.get(
    "/api/maquinaria/buscar/{termino}",
    summary="Buscar maquinaria por término",
    description="Tool: buscar_maquinaria(termino). "
                "Busca maquinaria por palabra clave. "
                "Ej: 'excavadora', 'compactar', 'grúa'.",
    tags=["Catálogo"],
)
async def buscar_maquinaria(termino: str):
    result = buscar_maquinaria_fallback(termino)
    if not result["resultados"]:
        return {"mensaje": f"No se encontró maquinaria relacionada con '{termino}'", "resultados": [], "origen": result["origen"]}
    return result


@app.get(
    "/api/maquinaria/detalle/{nombre}",
    summary="Obtener detalle de una máquina específica",
    description="Tool: detalle_maquinaria(nombre). "
                "Obtén la ficha completa de una máquina. "
                "Ej: 'Excavadora Hidráulica de Orugas', 'Bulldozer'.",
    tags=["Catálogo"],
)
async def detalle_maquinaria(nombre: str):
    result = detalle_maquinaria_fallback(nombre)
    if not result:
        return {"mensaje": f"No se encontró maquinaria con el nombre '{nombre}'", "detalle": None}
    return result


@app.get(
    "/api/proyectos",
    summary="Listar proyectos y combinaciones frecuentes",
    description="Tool: listar_proyectos(). "
                "Obtén combinaciones típicas de maquinaria para proyectos comunes.",
    tags=["Proyectos"],
)
async def listar_proyectos():
    return listar_proyectos_fallback()


@app.get(
    "/api/proyectos/{nombre}",
    summary="Obtener detalle de un proyecto",
    description="Tool: obtener_proyecto(nombre). "
                "Obtén maquinaria recomendada para un proyecto específico.",
    tags=["Proyectos"],
)
async def obtener_proyecto(nombre: str):
    if usar_db():
        data = database.listar_proyectos()
        for p in data:
            if nombre.lower() in p["nombre"].lower():
                return {"detalle": p}
    data = catalogo_md.get_proyecto(nombre)
    if not data:
        return {"mensaje": f"No se encontró el proyecto '{nombre}'", "detalle": None}
    return {"detalle": data}


@app.get(
    "/api/stats",
    summary="Estadísticas del sistema",
    description="Obtén estadísticas del sistema RAG: documentos, métricas, latencias.",
    tags=["Sistema"],
)
async def stats(request: Request):
    user = require_admin(request)
    return rag.get_stats()



@app.post(
    "/api/ingest",
    summary="Ingestar un documento",
    description="Tool: ingestar_documento(archivo). "
                "Sube un archivo (PDF, HTML, TXT) para agregarlo a la base de conocimiento.",
    tags=["Sistema"],
)
async def ingest(request: Request, file: UploadFile = File(...)):
    user = require_admin(request)
    if not file.filename:
        raise HTTPException(status_code=400, detail="No se proporcionó ningún archivo")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".txt", ".md", ".pdf", ".html", ".htm"]:
        raise HTTPException(status_code=400, detail="Tipo de archivo no permitido. Formatos permitidos: .txt, .md, .pdf, .html")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        content = await file.read()
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="El archivo excede el tamaño máximo permitido de 5MB")
        tmp.write(content)
        tmp_path = tmp.name

    try:
        num_chunks = rag.ingest_document(tmp_path, metadata={"fuente": file.filename, "autor": user["username"]})
        os.unlink(tmp_path)
        return {
            "mensaje": f"Documento '{file.filename}' ingestado correctamente",
            "fragmentos_creados": num_chunks,
        }
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail="Error interno al ingestar documento")


@app.get(
    "/api/db/status",
    summary="Estado de PostgreSQL",
    description="Verifica si la base de datos PostgreSQL está disponible.",
    tags=["Base de Datos"],
)
async def db_status():
    disponible = usar_db()
    return {
        "disponible": disponible,
        "mensaje": "PostgreSQL conectado correctamente" if disponible else "PostgreSQL no disponible"
    }


@app.post(
    "/api/db/seed",
    summary="Poblar la base de datos",
    description="Ejecuta el seed para poblar PostgreSQL con el catálogo completo de maquinaria.",
    tags=["Base de Datos"],
)
async def db_seed(request: Request):
    user = require_admin(request)
    from db.seed import seed_all
    try:
        seed_all(args=[
            "--host", config.DB_HOST,
            "--port", str(config.DB_PORT),
            "--db", config.DB_NAME,
            "--user", config.DB_USER,
            "--password", config.DB_PASSWORD,
        ])
        return {"mensaje": "Base de datos poblada exitosamente"}
    except Exception:
        raise HTTPException(status_code=500, detail="Error al poblar la base de datos")



_whisper_model = None


def _get_whisper():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        _whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
    return _whisper_model


@app.post(
    "/api/transcribe",
    summary="Transcribir audio a texto",
    description="Recibe un archivo de audio y devuelve el texto transcrito usando Whisper.",
    tags=["Audio"],
)
async def transcribe_audio(request: Request, audio: UploadFile = File(...)):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name

        model = _get_whisper()
        segments, info = model.transcribe(tmp_path, language="es")
        text = " ".join(seg.text.strip() for seg in segments)

        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

        if not text.strip():
            return {"text": "", "mensaje": "No se detectó voz"}
        return {"text": text, "language": info.language}
    except Exception:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(status_code=503, detail="Servicio de transcripción no disponible")



@app.get("/api/carrito")
async def api_ver_carrito(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")
    user_id = user[0]
    result = ops.ver_carrito(user_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/carrito")
async def api_agregar_al_carrito(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")
    user_id = user[0]
    body = await request.json()
    result = ops.agregar_al_carrito(
        user_id,
        body.get("maquina_nombre", ""),
        body.get("duration", 1),
        body.get("duration_unit", "dias"),
        body.get("start_date"),
        body.get("end_date"),
        body.get("cantidad", 1),
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.delete("/api/carrito/{item_id}")
async def api_quitar_del_carrito(item_id: int, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")
    user_id = user[0]
    result = ops.quitar_del_carrito(user_id, item_id=item_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.delete("/api/carrito")
async def api_limpiar_carrito(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")
    user_id = user[0]
    result = ops.quitar_del_carrito(user_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/carrito/checkout")
async def api_checkout_carrito(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")
    user_id = user[0]
    result = ops.checkout_carrito(user_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.on_event("startup")
async def startup_event():
    seed_default_admin()


if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True,
    )
