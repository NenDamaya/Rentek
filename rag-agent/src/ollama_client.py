import requests
import httpx
import numpy as np
import json
from typing import List, Optional, Generator, AsyncGenerator
from .config import config


class OllamaClient:
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or config.OLLAMA_BASE_URL
        self.model = model or config.OLLAMA_MODEL

    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        response = requests.post(
            f"{self.base_url}/api/embed",
            json={
                "model": config.EMBEDDING_MODEL,
                "input": texts,
                "keep_alive": config.KEEP_ALIVE,
            }
        )
        response.raise_for_status()
        data = response.json()
        return np.array(data["embeddings"])

    def generate(self, prompt: str, context: str = None, system_prompt: Optional[str] = None) -> str:
        if system_prompt is None:
            system_prompt = """Eres un asesor CONSULTIVO de renta de maquinaria pesada.

INSTRUCCIONES:
- Responde de forma natural y directa usando SOLO el contexto proporcionado.
- EL contexto contiene máquinas reales con especificaciones y precios. USA esa información para recomendar.
- Si el usuario pide una recomendación pero no ha dado suficiente contexto (tipo de trabajo, condiciones del sitio, plazo, etc.), indaga primero con preguntas antes de soltar una recomendación.
- Menciona al menos 1 máquina con sus especificaciones clave cuando el contexto lo permita.
- Si el contexto NO contiene NADA sobre maquinaria relevante, responde: "Por el momento no contamos con maquinaria específica para tu caso, pero estamos revisando tu solicitud y te contactaremos pronto."
- NO inventes maquinarias, modelos, precios ni especificaciones que no estén en el contexto."""

        full_prompt = f"Contexto:\n{context}\n\nPregunta: {prompt}\n\nRespuesta:"
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": full_prompt,
                "system": system_prompt,
                "stream": False,
                "keep_alive": config.KEEP_ALIVE,
                "options": {
                    "num_gpu": 999,
                    "main_gpu": 0,
                    "num_predict": config.NUM_PREDICT,
                    "num_ctx": config.NUM_CTX,
                    "temperature": config.TEMPERATURE,
                }
            }
        )
        response.raise_for_status()
        return response.json()["response"]

    def chat(
        self,
        messages: List[dict],
        tools: Optional[List[dict]] = None,
        system_prompt: Optional[str] = None,
    ) -> dict:
        if system_prompt:
            if not messages or messages[0].get("role") != "system":
                messages = [{"role": "system", "content": system_prompt}] + messages

        body = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "keep_alive": config.KEEP_ALIVE,
            "options": {"num_gpu": 999, "main_gpu": 0, "num_predict": config.NUM_PREDICT, "num_ctx": config.NUM_CTX, "temperature": config.TEMPERATURE},
        }
        if tools:
            body["tools"] = tools

        response = requests.post(
            f"{self.base_url}/api/chat",
            json=body,
        )
        response.raise_for_status()
        return response.json()

    def chat_stream(
        self,
        messages: List[dict],
        tools: Optional[List[dict]] = None,
        system_prompt: Optional[str] = None,
    ) -> Generator[dict, None, None]:
        if system_prompt:
            if not messages or messages[0].get("role") != "system":
                messages = [{"role": "system", "content": system_prompt}] + messages

        body = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "keep_alive": config.KEEP_ALIVE,
            "options": {"num_gpu": 999, "main_gpu": 0, "num_predict": config.NUM_PREDICT, "num_ctx": config.NUM_CTX, "temperature": config.TEMPERATURE},
        }
        if tools:
            body["tools"] = tools

        response = requests.post(
            f"{self.base_url}/api/chat",
            json=body,
            stream=True,
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    yield chunk
                except json.JSONDecodeError:
                    continue

    async def chat_stream_async(
        self,
        messages: List[dict],
        tools: Optional[List[dict]] = None,
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[dict, None]:
        if system_prompt:
            if not messages or messages[0].get("role") != "system":
                messages = [{"role": "system", "content": system_prompt}] + messages

        body = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "keep_alive": config.KEEP_ALIVE,
            "options": {"num_gpu": 999, "main_gpu": 0, "num_predict": config.NUM_PREDICT, "num_ctx": config.NUM_CTX, "temperature": config.TEMPERATURE},
        }
        if tools:
            body["tools"] = tools

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=body,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            yield chunk
                        except json.JSONDecodeError:
                            continue