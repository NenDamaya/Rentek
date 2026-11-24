import os
from datetime import datetime

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")


def _fmt_time(seconds):
    if seconds < 60:
        return f"{seconds:.1f}s"
    return f"{seconds // 60}m {seconds % 60:.0f}s"


def _safe(s, maxlen=80):
    s = str(s).replace("\n", " ").strip()
    return s[:maxlen] + ("..." if len(s) > maxlen else "")


def generate_agent_report(persona: dict, metrics: dict) -> str:
    p = persona
    duration = metrics.get("end_time", 0) - metrics.get("start_time", 0)
    latencies = metrics.get("rentek_latencies_ms", [])
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    tool_counts = {}
    for t in metrics.get("tools_used", []):
        tool_counts[t] = tool_counts.get(t, 0) + 1
    sorted_tools = sorted(tool_counts.items(), key=lambda x: -x[1])

    goal_emoji = "✅" if metrics.get("goal_achieved") else ("❌" if not metrics.get("goal_achieved") else "⚠️")
    block_emoji = "🔒" if metrics.get("was_blocked") else "✅"

    lines = []
    lines.append(f"# Reporte: {p['nombre']}")
    lines.append("")
    lines.append("## Resumen")
    lines.append("")
    lines.append(f"- **Persona:** {p['nombre']}")
    lines.append(f"- **Descripción:** {p['descripcion']}")
    lines.append(f"- **Autenticado:** {'Sí' if p['authenticated'] else 'No'}")
    lines.append(f"- **Turnos:** {metrics.get('turnos', 0)} / {p['turn_limit']} máx")
    lines.append(f"- **Duración:** {_fmt_time(duration)}")
    lines.append(f"- **Latencia promedio Rentek:** {avg_latency:.0f}ms")
    lines.append(f"- **Objetivo:** {p['goal']}")
    lines.append(f"- **Resultado:** {goal_emoji} {'LOGRADO' if metrics.get('goal_achieved') else 'NO LOGRADO'}")
    lines.append(f"- **Bloqueado:** {block_emoji} {'Sí' if metrics.get('was_blocked') else 'No'}")
    if metrics.get("block_reason"):
        lines.append(f"- **Razón bloqueo:** {_safe(metrics['block_reason'], 200)}")
    if metrics.get("error"):
        lines.append(f"- **Error:** ⚠️ {_safe(metrics['error'], 200)}")
    lines.append("")

    if sorted_tools:
        lines.append("## Herramientas usadas por Rentek")
        lines.append("")
        lines.append(f"| Herramienta | Veces |")
        lines.append(f"|------------|-------|")
        for name, count in sorted_tools:
            lines.append(f"| {name} | {count} |")
        lines.append("")

    lines.append("## Conversación completa")
    lines.append("")
    lines.append(f"| # | Rol | Mensaje |")
    lines.append(f"|---|-----|---------|")

    for i, turn in enumerate(metrics.get("conversation", persona.get("conversation", [])), 1):
        role = turn.get("source", turn.get("role", "?"))
        content = turn.get("content", "")
        content_short = content.replace("\n", " | ")
        if len(content_short) > 200:
            content_short = content_short[:200] + "..."
        lines.append(f"| {i} | {role} | {content_short} |")

    lines.append("")
    lines.append("## Observaciones")
    lines.append("")
    if metrics.get("was_blocked"):
        lines.append("- El sistema detectó y bloqueó correctamente el comportamiento inapropiado.")
    if not latencies:
        lines.append("- No se pudieron obtener métricas de latencia (posible error de conexión).")
    lines.append("- Revisar la conversación completa para análisis cualitativo.")
    lines.append("")

    return "\n".join(lines)


def generate_comparative_report(agent_reports: list) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = []
    lines.append("# Reporte Comparativo Multi-Agente")
    lines.append("")
    lines.append(f"**Generado:** {now}")
    lines.append(f"**Sistema:** Rentek AI Assistant")
    lines.append(f"**Modelo:** qwen2.5:7b")
    lines.append(f"**Total agentes:** {len(agent_reports)}")
    lines.append("")

    lines.append("## Tabla Comparativa")
    lines.append("")
    lines.append("| # | Agente | Turnos | Duración | Latencia (ms) | Objetivo | Bloqueado | Tools usadas |")
    lines.append("|---|--------|--------|----------|---------------|----------|-----------|-------------|")

    for r in agent_reports:
        p = r["persona"]
        m = r["metrics"]
        duration = m.get("end_time", 0) - m.get("start_time", 0)
        latencies = m.get("rentek_latencies_ms", [])
        avg_lat = int(sum(latencies) / len(latencies)) if latencies else 0
        goal_status = "✅" if m.get("goal_achieved") else "❌"
        blocked = "🔒" if m.get("was_blocked") else "✓"
        tools_set = set(m.get("tools_used", []))
        tools_str = ", ".join(sorted(tools_set)[:5]) if tools_set else "-"

        lines.append(
            f"| {p['id']} | {p['nombre']} | {m.get('turnos', 0)} | "
            f"{_fmt_time(duration)} | {avg_lat} | {goal_status} | {blocked} | {tools_str} |"
        )

    lines.append("")
    lines.append("## Métricas Globales")
    lines.append("")

    total_turns = sum(r["metrics"].get("turnos", 0) for r in agent_reports)
    total_duration = sum(r["metrics"].get("end_time", 0) - r["metrics"].get("start_time", 0) for r in agent_reports)
    all_latencies = []
    for r in agent_reports:
        all_latencies.extend(r["metrics"].get("rentek_latencies_ms", []))
    global_avg_lat = sum(all_latencies) / len(all_latencies) if all_latencies else 0
    goals_achieved = sum(1 for r in agent_reports if r["metrics"].get("goal_achieved"))
    blocked_count = sum(1 for r in agent_reports if r["metrics"].get("was_blocked"))

    lines.append(f"- **Turnos totales:** {total_turns}")
    lines.append(f"- **Duración total:** {_fmt_time(total_duration)}")
    lines.append(f"- **Latencia promedio global:** {global_avg_lat:.0f}ms")
    lines.append(f"- **Objetivos logrados:** {goals_achieved}/{len(agent_reports)} ({goals_achieved * 100 // len(agent_reports) if agent_reports else 0}%)")
    lines.append(f"- **Bloqueos:** {blocked_count}/{len(agent_reports)}")
    lines.append("")

    lines.append("## Hallazgos por Agente")
    lines.append("")
    for r in agent_reports:
        p = r["persona"]
        m = r["metrics"]
        lines.append(f"### {p['id']}. {p['nombre']}")
        lines.append("")
        if m.get("was_blocked"):
            lines.append("- **⚠️ Fue bloqueado por el sistema** — revisar triggers.")
        if m.get("goal_achieved"):
            lines.append("- **✅ Logró su objetivo** — el flujo funcionó correctamente.")
        else:
            lines.append("- **❌ No logró su objetivo** — posible área de mejora.")
        if m.get("error"):
            lines.append(f"- **Error:** {m['error']}")
        lines.append("")

    lines.append("## Recomendaciones")
    lines.append("")
    lines.append("_Basado en los resultados de la simulación multi-agente:_")
    lines.append("")
    lines.append("1. ")
    lines.append("2. ")
    lines.append("3. ")
    lines.append("")

    return "\n".join(lines)


def save_report(filename: str, content: str):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    filepath = os.path.join(REPORTS_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath
