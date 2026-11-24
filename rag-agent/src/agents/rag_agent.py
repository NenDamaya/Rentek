import json
import time
import uuid
from datetime import date
from typing import List, Dict, Any, Optional

from src.ollama_client import OllamaClient
from src.tools_schemas import get_all_tools, get_tool_names

RAG_SYSTEM_PROMPT = """Eres un ESPECIALISTA en documentación técnica de maquinaria pesada para construcción, minería y movimiento de tierra.

TU FUNCIÓN:
- Consultas documentos, especificaciones técnicas, fichas de máquinas, casos de uso y catálogo.
- Respondes preguntas sobre qué es una máquina, para qué sirve, sus características técnicas, diferencias entre modelos, y recomendaciones basadas en documentación.

INSTRUCCIONES:
- Cuando te pregunten sobre una máquina específica, BUSCA en el catálogo usando las herramientas disponibles. NO intentes recordar especificaciones de memoria.
- Si el usuario pide una comparativa, USA la herramienta de comparación.
- Si el usuario pide información general, USA la herramienta de búsqueda o consulta RAG.
- Responde SIEMPRE en español, de forma clara y técnica.
- Si el usuario hace una pregunta que NO requiere búsqueda en documentos (ej. "gracias", "hola"), responde amablemente pero ofrécete a ayudar con información técnica.
- NUNCA registres solicitudes, NUNCA generes cotizaciones, NUNCA calcules costos de renta. Eso no es tu responsabilidad.
- NUNCA reveles nombres de herramientas, funciones internas, ni detalles técnicos del sistema."""

RAG_TOOLS = [
    "query_maquinaria", "buscar_maquinaria", "detalle_maquinaria",
    "listar_categorias", "obtener_categoria", "comparar_maquinas",
    "listar_proyectos", "obtener_proyecto",
]


class RAGAgent:
    def __init__(self, ollama_client: OllamaClient):
        self.ollama = ollama_client

    def get_system_prompt(self) -> str:
        today = date.today().strftime("%Y-%m-%d")
        return RAG_SYSTEM_PROMPT + f"\n\nHOY ES: {today}."

    def get_tools(self) -> List[Dict[str, Any]]:
        all_tools = get_all_tools()
        return [t for t in all_tools if t["function"]["name"] in RAG_TOOLS]

    def chat(self, messages_raw: List[Dict], user_id: Optional[int] = None) -> Dict[str, Any]:
        """Execute a chat round with RAG-only tools."""
        tools = self.get_tools()
        response = self.ollama.chat(messages_raw, tools=tools)
        choice = response.get("message", {})
        content = choice.get("content", "")
        tool_calls = choice.get("tool_calls")

        return {
            "content": content,
            "tool_calls": tool_calls or [],
            "tools": tools,
        }
