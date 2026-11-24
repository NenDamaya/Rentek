import json
import time
import uuid
import httpx

OLLAMA_URL = "http://localhost:11435/api/chat"
OLLAMA_MODEL = "qwen2.5:7b"
RENTEK_URL = "http://localhost:8000"


class AgentError(Exception):
    pass


class Agent:
    def __init__(self, persona: dict):
        self.p = persona
        self.conversation = []
        self.metrics = {
            "turnos": 0,
            "rentek_latencies_ms": [],
            "tools_used": [],
            "was_blocked": False,
            "block_reason": "",
            "goal_achieved": False,
            "chat_id": None,
            "token": None,
            "user_data": None,
            "start_time": None,
            "end_time": None,
            "rentek_responses": [],
        }

    async def _ollama_chat(self, messages: list) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(
                OLLAMA_URL,
                json={"model": OLLAMA_MODEL, "messages": messages, "stream": False},
            )
            r.raise_for_status()
            data = r.json()
            return data["message"]["content"].strip()

    async def _rentek_post(self, endpoint: str, body: dict, headers: dict = None) -> dict:
        url = f"{RENTEK_URL}{endpoint}"
        if headers is None:
            headers = {"Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=180) as client:
            r = await client.post(url, json=body, headers=headers)
            if r.status_code >= 400:
                try:
                    err = r.json()
                except Exception:
                    err = {"error": r.text[:200]}
                raise AgentError(f"Rentek {endpoint} {r.status_code}: {err}")
            return r.json()

    async def _rentek_get(self, endpoint: str, headers: dict = None) -> dict:
        url = f"{RENTEK_URL}{endpoint}"
        if headers is None:
            headers = {"Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url, headers=headers)
            if r.status_code >= 400:
                try:
                    err = r.json()
                except Exception:
                    err = {"error": r.text[:200]}
                raise AgentError(f"Rentek {endpoint} {r.status_code}: {err}")
            return r.json()

    async def _setup_user(self):
        if not self.p["authenticated"]:
            return
        username = f"test_agent_{self.p['id']}_{uuid.uuid4().hex[:6]}"
        password = "test123"
        try:
            resp = await self._rentek_post("/api/auth/register", {
                "username": username,
                "password": password,
                "display_name": self.p["user_name"],
            })
            self.metrics["token"] = resp["token"]
            self.metrics["user_data"] = resp["user"]
        except AgentError as e:
            if "ya existe" in str(e):
                resp = await self._rentek_post("/api/auth/login", {
                    "username": username,
                    "password": password,
                })
                self.metrics["token"] = resp["token"]
                self.metrics["user_data"] = resp["user"]
            else:
                raise

    async def _create_chat(self):
        if not self.metrics["token"]:
            return
        headers = {"Authorization": f"Bearer {self.metrics['token']}", "Content-Type": "application/json"}
        resp = await self._rentek_post("/api/chats", {}, headers=headers)
        self.metrics["chat_id"] = resp["id"]

    async def _think(self, history_context: list) -> str:
        client_name = self.p.get("user_name", "Cliente") or "Cliente"
        his_lines = []
        for turn in history_context:
            source = turn.get("source", "")
            who = client_name if source == "agent" else "Asistente Rentek"
            content = turn.get("content", "")
            if not source or source == "system":
                continue
            his_lines.append(f"[{who}]: {content}")

        history_text = "\n".join(his_lines)

        rentek_responses = [t["content"] for t in history_context if t.get("source") == "rentek"]
        repeats = 0
        if len(rentek_responses) >= 2:
            for i in range(1, len(rentek_responses)):
                if rentek_responses[i].strip() == rentek_responses[i - 1].strip():
                    repeats += 1

        hints = []

        if rentek_responses and "ocurrió un error" in rentek_responses[-1].lower():
            hints.append(
                "⚠️ Rentek acaba de dar un ERROR. NO repitas tu mensaje anterior.\n"
                "En su lugar, pregunta: 'Entiendo, ¿qué pasos debo seguir para continuar?'\n"
                "O sigue la instrucción que Rentek te haya dado en el error."
            )

        if repeats >= 2:
            hints.append(
                "⚠️ Rentek está repitiendo respuestas genéricas. CAMBIA DE ESTRATEGIA:\n"
                "- Si pedías datos técnicos, ya no preguntes por eso\n"
                "- Sé directo: proporciónale todos tus datos y pídele que registre\n"
                "- Ejemplo: 'Mis datos son Carlos Mendoza, carlos@email.com. Quiero la retroexcavadora por 5 días. Registra mi solicitud por favor'\n"
            )

        urgency_hint = "\n".join(hints) + "\n" if hints else ""

        task = (
            "Eres el CLIENTE en esta conversación. Rentek es el asistente de renta de maquinaria.\n\n"
            f"Historial de la conversación:\n{history_text}\n\n"
            f"{urgency_hint}"
            "INSTRUCCIÓN: Escribe el siguiente mensaje que enviarías como cliente.\n"
            "REGLAS ESTRICTAS:\n"
            "- Eres el CLIENTE, NO el asistente. NO respondas por Rentek.\n"
            "- NO proporciones cálculos, precios ni catálogos\n"
            "- Habla natural, como una persona normal\n"
            "- Responde SOLO el texto del mensaje, sin etiquetas ni explicaciones\n"
            "- No uses FIN, END ni ninguna marca especial\n"
            "- Si el sistema te bloqueó, responde solo 'ADIOS'\n"
            "Mensaje:"
        )

        messages = [
            {"role": "system", "content": self.p["persona_prompt"]},
            {"role": "user", "content": task},
        ]

        return await self._ollama_chat(messages)

    def _extract_tools(self, rentek_response: dict) -> list:
        tools = []
        content = rentek_response.get("choices", [{}])[0].get("message", {}).get("content", "")
        self.metrics["rentek_responses"].append(content)

        if "categorías" in content.lower() or "categorias" in content.lower():
            tools.append("listar_categorias")
        if "costo" in content.lower() or "$" in content:
            tools.append("calcular_costo_renta")
        if "recomend" in content.lower():
            tools.append("recomendar_por_trabajo")
        if "detalle" in content.lower() or "especificaciones" in content.lower():
            tools.append("detalle_maquinaria")
        if "busc" in content.lower():
            tools.append("buscar_maquinaria")
        if "compar" in content.lower():
            tools.append("comparar_maquinas")
        if "cotización" in content.lower() or "cotizacion" in content.lower() or "folio" in content.lower():
            tools.append("generar_cotizacion")
        if "solicitud" in content.lower() or "registrad" in content.lower():
            tools.append("registrar_solicitud")
        if "disponibilidad" in content.lower() or "disponible" in content.lower():
            tools.append("verificar_disponibilidad")
        if "proyecto" in content.lower():
            tools.append("calcular_costo_proyecto")
        if "no tienes" in content.lower() or "no tiene" in content.lower():
            tools.append("consultar_mis_cotizaciones/solicitudes")

        return tools

    def _check_strikes_or_block(self, content: str) -> bool:
        block_phrases = [
            "has sido bloqueado",
            "chat ha sido cerrado",
            "demasiadas advertencias",
            "no puedes continuar",
            "superaste el límite",
        ]
        for phrase in block_phrases:
            if phrase in content.lower():
                self.metrics["was_blocked"] = True
                self.metrics["block_reason"] = content[:200]
                return True
        return False

    def _check_goal_achieved(self, content: str) -> bool:
        c = content.lower()
        tools = set(self.metrics.get("tools_used", []))

        if self.p["id"] == 1:
            if "registrar_solicitud" in tools:
                return True
            goal_phrases = ["folio", "cotización", "cotizacion"]
            explicit = any(p in c for p in ["folio:", "folio ", "cotización:", "cotizacion:", "ha sido registrada", "solicitud registrada"])
            return explicit or (sum(1 for p in goal_phrases if p in c) >= 2 and "cuánto" not in c and "gusta" not in c)
        elif self.p["id"] == 2:
            return any(p in c for p in ["categoría", "categoria", "maquinaria", "precio", "renta"])
        elif self.p["id"] == 3:
            detail_phrases = ["especificaciones", "detalle", "comparación", "comparacion", "recomendación", "recomendacion", "potencia", "capacidad"]
            return sum(1 for p in detail_phrases if p in c) >= 2
        elif self.p["id"] == 4:
            return any(p in c for p in ["nombre", "correo", "datos", "contacto", "necesito"])
        elif self.p["id"] == 5:
            return self.metrics["was_blocked"]
        elif self.p["id"] == 6:
            return self.metrics["was_blocked"] or any(
                p in c for p in [
                    "no puedo", "instrucciones", "política", "seguridad",
                    "violación", "violacion", "no está permitido",
                    "políticas", "politica", "politicas",
                ]
            )
        elif self.p["id"] == 7:
            if "registrar_solicitud" in tools:
                return True
            explicit = any(p in c for p in ["folio:", "folio ", "cotización:", "cotizacion:", "ha sido registrada", "solicitud registrada"])
            return explicit
        elif self.p["id"] == 8:
            return any(p in c for p in ["español", "espanol", "por favor escribe en español"])
        return False

    async def run(self) -> dict:
        self.metrics["start_time"] = time.time()

        try:
            await self._setup_user()
            await self._create_chat()
        except AgentError as e:
            self.metrics["error"] = f"Setup failed: {e}"
            self.metrics["end_time"] = time.time()
            return self.metrics

        messages_for_rentek = []

        first_msg = self.p["first_message"]
        messages_for_rentek.append({"role": "user", "content": first_msg})
        self.conversation.append({"role": "user", "content": first_msg, "source": "agent"})

        for turn in range(self.p["turn_limit"]):
            self.metrics["turnos"] = turn + 1

            rentek_body = {
                "messages": messages_for_rentek[-8:],
            }

            if self.p["authenticated"] and self.p.get("user_name"):
                rentek_body["user_name"] = self.p["user_name"]
                rentek_body["user_email"] = self.p["user_email"]

            if self.metrics.get("chat_id"):
                rentek_body["chat_id"] = self.metrics["chat_id"]

            try:
                t0 = time.time()
                resp = await self._rentek_post("/v1/chat/completions", rentek_body)
                latency = (time.time() - t0) * 1000
                self.metrics["rentek_latencies_ms"].append(latency)

                content = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
                self.conversation.append({"role": "assistant", "content": content, "source": "rentek"})
                messages_for_rentek.append({"role": "assistant", "content": content})

                tools = self._extract_tools(resp)
                self.metrics["tools_used"].extend(tools)

                if self._check_strikes_or_block(content):
                    self.conversation.append({
                        "role": "user", "content": "[AGENTE DETECTÓ BLOQUEO]", "source": "system"
                    })
                    break

                if self._check_goal_achieved(content):
                    self.metrics["goal_achieved"] = True

                if self.metrics["goal_achieved"] and turn >= 3:
                    self.conversation.append({
                        "role": "user", "content": "[AGENTE LOGRO OBJETIVO - FIN]", "source": "system"
                    })
                    break

            except AgentError as e:
                self.metrics["error"] = f"Turn {turn + 1}: {e}"
                self.conversation.append({
                    "role": "system", "content": f"[ERROR: {e}]", "source": "system"
                })
                break

            if turn == self.p["turn_limit"] - 1:
                break

            agent_msg = await self._think(self.conversation)
            if agent_msg.strip().upper() in ("FIN", "ADIOS", "ADIOS."):
                break

            self.conversation.append({"role": "user", "content": agent_msg, "source": "agent"})
            messages_for_rentek.append({"role": "user", "content": agent_msg})

        self.metrics["end_time"] = time.time()
        self.metrics["conversation"] = self.conversation

        if self.metrics.get("chat_id"):
            try:
                headers = {"Authorization": f"Bearer {self.metrics['token']}"}
                msgs_resp = await self._rentek_get(
                    f"/api/chats/{self.metrics['chat_id']}/messages",
                    headers=headers,
                )
                self.metrics["saved_messages"] = msgs_resp
            except Exception:
                pass

        return self.metrics
