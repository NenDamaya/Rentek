#!/usr/bin/env python3
"""
Orquestador de pruebas multi-agente para Rentek.

Ejecuta múltiples agentes de prueba en paralelo, cada uno simulando un perfil
de usuario diferente, y genera reportes individuales y comparativos.

Uso:
    python -m tests.agents.orchestrator
    python -m tests.agents.orchestrator --agentes 1,3,5
    python -m tests.agents.orchestrator --list
    python -m tests.agents.orchestrator --output ./reports
"""

import asyncio
import json
import sys
import time
import os

from .personas import PERSONAS
from .agent import Agent
from .reporter import generate_agent_report, generate_comparative_report, save_report


def print_banner():
    print("=" * 64)
    print("  RENTEK — Simulador Multi-Agente (secuencial)")
    print("  Pruebas de perfiles de usuario contra Rentek AI")
    print("=" * 64)
    print()


def list_personas():
    print(f"{'ID':>3} | {'Nombre':<30} | {'Auth':<5} | {'Turnos':<6} | {'Descripción'}")
    print("-" * 90)
    for p in PERSONAS:
        auth = "Sí" if p["authenticated"] else "No"
        print(f"{p['id']:>3} | {p['nombre']:<30} | {auth:<5} | {p['turn_limit']:<6} | {p['descripcion']}")
    print()


def parse_agent_ids(raw: str) -> list:
    ids = []
    for part in raw.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            ids.extend(range(int(a), int(b) + 1))
        else:
            ids.append(int(part))
    return ids


async def run_agent(persona: dict) -> dict:
    agent = Agent(persona)
    print(f"  ▶ [{persona['id']}] {persona['nombre']} — iniciando...")
    t0 = time.time()
    try:
        metrics = await agent.run()
        duration = time.time() - t0
        status = "✅" if metrics.get("goal_achieved") else "⚠️" if metrics.get("was_blocked") else "❌"
        blocked = "🔒" if metrics.get("was_blocked") else ""
        print(f"  {'✓' if status else '✗'} [{persona['id']}] {persona['nombre']} — "
              f"{metrics.get('turnos', 0)} turnos, {duration:.1f}s {status} {blocked}")
        return {"persona": persona, "metrics": metrics}
    except Exception as e:
        print(f"  ✗ [{persona['id']}] {persona['nombre']} — ERROR: {e}")
        return {
            "persona": persona,
            "metrics": {
                "error": str(e),
                "turnos": 0,
                "start_time": t0,
                "end_time": time.time(),
                "rentek_latencies_ms": [],
                "tools_used": [],
                "was_blocked": False,
                "goal_achieved": False,
            }
        }


async def main():
    print_banner()

    agent_ids = None
    output_dir = os.path.join(os.path.dirname(__file__), "reports")

    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == "--list":
            list_personas()
            return
        elif arg == "--agentes" and i + 1 < len(args):
            agent_ids = parse_agent_ids(args[i + 1])
        elif arg == "--output" and i + 1 < len(args):
            output_dir = args[i + 1]

    personas_to_run = [p for p in PERSONAS if agent_ids is None or p["id"] in agent_ids]

    if not personas_to_run:
        print("No hay agentes seleccionados. Usa --list para ver los disponibles.")
        return

    print(f"Agentes a ejecutar: {len(personas_to_run)}")
    for p in personas_to_run:
        print(f"  • [{p['id']}] {p['nombre']} ({p['descripcion'][:50]}...)")
    print()
    print("Ejecutando agentes UNO POR UNO para no sobrecargar la GPU...\n")

    t_start = time.time()
    results = []
    for p in personas_to_run:
        result = await run_agent(p)
        results.append(result)
        print("  --- (pausa entre agentes para enfriar) ---\n")
    total_time = time.time() - t_start

    print(f"\nTodos los agentes completados en {total_time:.1f}s")
    print("Generando reportes...\n")

    saved_files = []

    for r in results:
        p = r["persona"]
        m = r["metrics"]
        m["conversation"] = m.get("conversation", [])

        report = generate_agent_report(p, m)
        filename = f"reporte_agente_{p['id']:02d}_{p['nombre'].lower().replace(' ', '_')}.md"
        filepath = save_report(filename, report)
        saved_files.append(filepath)

        conv_filename = f"conversacion_agente_{p['id']:02d}_{p['nombre'].lower().replace(' ', '_')}.json"
        conv_path = save_report(conv_filename, json.dumps({
            "persona": p["nombre"],
            "metrics": {k: v for k, v in m.items() if k != "conversation"},
            "conversation": m.get("conversation", []),
        }, indent=2, ensure_ascii=False))
        saved_files.append(conv_path)

    comparative = generate_comparative_report(results)
    comp_path = save_report("reporte_comparativo.md", comparative)
    saved_files.append(comp_path)

    print("Reportes generados:")
    for f in saved_files:
        print(f"  • {f}")

    print()
    print("Resumen rápido:")
    print(f"  {'ID':>3} {'Nombre':<25} {'Turnos':<7} {'Objetivo':<9} {'Bloqueado':<10}")
    print(f"  {'-'*3} {'-'*25} {'-'*7} {'-'*9} {'-'*10}")
    for r in results:
        p = r["persona"]
        m = r["metrics"]
        goal = "✅" if m.get("goal_achieved") else "❌"
        block = "🔒" if m.get("was_blocked") else "✓"
        print(f"  {p['id']:>3} {p['nombre']:<25} {m.get('turnos', 0):<7} {goal:<9} {block:<10}")


if __name__ == "__main__":
    asyncio.run(main())
