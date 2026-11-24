#!/usr/bin/env python3
"""
Evaluación del buscador híbrido Rentek — genera PDF con métricas.
Uso: python3 scripts/evaluar_agente.py [--output INFORME.pdf]
"""

import argparse
import json
import math
import os
import sys
import time
from datetime import date
from typing import List, Dict, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

try:
    import psycopg2
except ImportError:
    psycopg2 = None

# ============================================================
# CASOS DE PRUEBA
# ============================================================

TEST_CASES = [
    {
        "id": 1,
        "query": "excavadora para hacer zanjas",
        "expected": ["Excavadora Hidráulica de Orugas", "Retroexcavadora (Backhoe)", "Miniexcavadora"],
        "description": "Excavacion de zanjas — maquinas de excavacion primaria",
    },
    {
        "id": 2,
        "query": "compactar tierra para cimentacion",
        "expected": ["Compactadora de Suelos / Vibrocompactador", "Apisonador / Compactadora Manual Tipo Rana", "Rodillo Vibratorio Doble Tambor"],
        "description": "Compactacion de suelo — maquinas compactadoras",
    },
    {
        "id": 3,
        "query": "bomba para sacar agua de pozo",
        "expected": ["Bomba de Achique / Bomba de Drenaje", "Motobomba a Gasolina", "Bomba Sumergible Eléctrica"],
        "description": "Bombeo de agua — equipos de achique y drenaje",
    },
    {
        "id": 4,
        "query": "camion para mover material de construccion",
        "expected": ["Camión de Volteo / Camión Articulado", "Camión Revolvedor / Mixer de Concreto"],
        "description": "Transporte de materiales — volteo y mixer",
    },
    {
        "id": 5,
        "query": "grua para levantar estructuras metalicas",
        "expected": ["Grúa Telescópica sobre Camión (Grúa Móvil)", "Grúa Todo Terreno (All Terrain)", "Grúa Torre de Brazo Basculante"],
        "description": "Elevacion de estructuras — gruas moviles y torre",
    },
    {
        "id": 6,
        "query": "pavimentar calle de asfalto",
        "expected": ["Pavimentadora de Asfalto (Finisher)", "Rodillo Vibratorio Doble Tambor", "Fresadora de Asfalto (Cold Planer)"],
        "description": "Pavimentacion asfaltica — finisher, rodillo, fresadora",
    },
    {
        "id": 7,
        "query": "taladro para perforar roca en mina",
        "expected": ["Perforadora Rotaria (Drilling Rig)", "Martillo Rompedor Eléctrico", "Jumbo de Perforación"],
        "description": "Perforacion en mineria — rotaria y demoledor",
    },
    {
        "id": 8,
        "query": "montacargas para mover tarimas en bodega",
        "expected": ["Montacargas Telescópico (Telehandler)", "Plataforma Elevadora de Tijera (Scissor Lift)", "Montacargas Eléctrico (3 ton)"],
        "description": "Manejo de materiales en bodega — telehandler",
    },
    {
        "id": 9,
        "query": "demoler losa de concreto",
        "expected": ["Martillo Rompedor Eléctrico", "Cortadora de Concreto de Mano", "Pinza de Demolición (Grapple)", "Bulldozer / Topadora"],
        "description": "Demolicion de concreto — martillo, cortadora, bulldozer",
    },
    {
        "id": 10,
        "query": "generador electrico para obra sin conexion",
        "expected": ["Generador Eléctrico Industrial", "Compresor de Aire Industrial Portátil", "Generador Portátil a Gasolina"],
        "description": "Generacion electrica para obra — generador y compresor",
    },
]


def get_db_conn(args):
    if psycopg2 is None:
        return None
    return psycopg2.connect(
        host=args.host, port=args.port, dbname=args.db,
        user=args.user, password=args.password,
    )


def run_hybrid_search(conn, query: str, limit: int = 10) -> List[str]:
    from src.hybrid_search import hybrid_search, rerank
    results = hybrid_search(conn, query, limit=limit)
    results = rerank(conn, results, query)
    return [r["nombre"] for r in results]


def run_old_search(conn, query: str, limit: int = 10) -> List[str]:
    from src.database import buscar_maquinaria
    results = buscar_maquinaria(query)
    return [r["nombre"] for r in results[:limit]]


def compute_metrics(
    retrieved: List[str], expected: List[str], k: int = 5
) -> Dict:
    retrieved_k = retrieved[:k]
    relevant = sum(1 for r in retrieved_k if r in expected)
    precision = relevant / k if k > 0 else 0
    recall = relevant / len(expected) if expected else 0

    mrr = 0.0
    for i, r in enumerate(retrieved):
        if r in expected:
            mrr = 1.0 / (i + 1)
            break

    return {
        "precision_at_5": round(precision, 3),
        "recall": round(recall, 3),
        "mrr": round(mrr, 3),
        "relevant_in_top_5": relevant,
        "expected_total": len(expected),
    }


def sanitize(text: str) -> str:
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'ñ': 'n', 'Ñ': 'N', 'ü': 'u', 'Ü': 'U',
        '—': '-', '–': '-', '"': '"', '"': '"',
        "'": "'", "'": "'",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def generate_pdf(results: List[Dict], output_path: str):
    if FPDF is None:
        print("ERROR: fpdf2 no instalado. pip install fpdf2")
        sys.exit(1)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 15, sanitize("Informe de Evaluacion - Busqueda Hibrida Rentek"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, sanitize(f"Generado: {date.today().isoformat()}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, sanitize(f"Casos de prueba: {len(results)}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 12, sanitize("Resumen Global"), new_x="LMARGIN", new_y="NEXT")

    avg_p = sum(r["metrics"]["precision_at_5"] for r in results) / len(results)
    avg_r = sum(r["metrics"]["recall"] for r in results) / len(results)
    avg_mrr = sum(r["metrics"]["mrr"] for r in results) / len(results)
    total_relevant = sum(r["metrics"]["relevant_in_top_5"] for r in results)
    total_expected = sum(r["metrics"]["expected_total"] for r in results)

    pdf.set_font("Helvetica", "", 11)
    metrics_data = [
        (sanitize("Precision@5 promedio"), f"{avg_p:.3f}"),
        (sanitize("Recall promedio"), f"{avg_r:.3f}"),
        (sanitize("MRR promedio"), f"{avg_mrr:.3f}"),
        (sanitize("Relevantes encontrados / total esperados"), f"{total_relevant}/{total_expected}"),
    ]
    for label, value in metrics_data:
        pdf.cell(80, 8, label, border=1)
        pdf.cell(40, 8, value, border=1)
        pdf.ln()

    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 12, sanitize("Detalle por Caso"), new_x="LMARGIN", new_y="NEXT")

    for r in results:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, sanitize(f"Caso #{r['id']}: {r['query']}"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, sanitize(f"  Descripcion: {r['description']}"), new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 5, sanitize(f"  Esperado: {', '.join(r['expected'][:5])}"), new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 5, sanitize(f"  Obtenido (top 5): {', '.join(r['retrieved'][:5])}"), new_x="LMARGIN", new_y="NEXT")

        m = r["metrics"]
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, sanitize(f"  P@5={m['precision_at_5']}  Recall={m['recall']}  MRR={m['mrr']}  Relevantes={m['relevant_in_top_5']}/{m['expected_total']}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    pdf.output(output_path)
    print(f"PDF generado: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Evaluacion del buscador hibrido Rentek")
    parser.add_argument("--host", default="postgres")
    parser.add_argument("--port", type=int, default=5432)
    parser.add_argument("--db", default="maquinaria_rag")
    parser.add_argument("--user", default="rag_user")
    parser.add_argument("--password", default="rag_pass_2026")
    parser.add_argument("--output", default=f"informe_evaluacion_{date.today().isoformat()}.pdf")
    parser.add_argument("--compare", action="store_true", help="Comparar vs busqueda antigua (ILIKE)")
    args = parser.parse_args()

    print("=" * 60)
    print("  EVALUACION DEL BUSCADOR HIBRIDO - RENTEK")
    print("=" * 60)
    print(f"  Casos: {len(TEST_CASES)}")
    print(f"  Comparar vs anterior: {'Si' if args.compare else 'No'}")
    print()

    conn = get_db_conn(args)
    if not conn:
        print("ERROR: No se pudo conectar a PostgreSQL")
        sys.exit(1)

    results = []

    for tc in TEST_CASES:
        print(f"  [{tc['id']}/{len(TEST_CASES)}] {tc['query']}...")
        t0 = time.time()

        retrieved = run_hybrid_search(conn, tc["query"])
        elapsed = time.time() - t0
        metrics = compute_metrics(retrieved, tc["expected"])

        tc_result = dict(tc)
        tc_result["retrieved"] = retrieved
        tc_result["metrics"] = metrics
        tc_result["latency_ms"] = round(elapsed * 1000, 1)
        results.append(tc_result)

        old_metrics_str = ""
        if args.compare:
            old_retrieved = run_old_search(conn, tc["query"])
            old_metrics = compute_metrics(old_retrieved, tc["expected"])

            def _fmt_latex(d):
                return f"P@5={d['precision_at_5']:.3f} R={d['recall']:.3f} MRR={d['mrr']:.3f}"

            print(f"     HIBRIDO: {_fmt_latex(metrics)}")
            print(f"     ANTERIOR: {_fmt_latex(old_metrics)}")
        else:
            print(f"     P@5={metrics['precision_at_5']:.3f} Recall={metrics['recall']:.3f} MRR={metrics['mrr']:.3f} ({elapsed:.2f}s)")

    conn.close()

    generate_pdf(results, args.output)

    avg_p = sum(r["metrics"]["precision_at_5"] for r in results) / len(results)
    avg_r = sum(r["metrics"]["recall"] for r in results) / len(results)
    avg_mrr = sum(r["metrics"]["mrr"] for r in results) / len(results)
    print()
    print("=" * 60)
    print("  RESULTADOS GLOBALES")
    print(f"  Precision@5 promedio: {avg_p:.3f}")
    print(f"  Recall promedio:      {avg_r:.3f}")
    print(f"  MRR promedio:         {avg_mrr:.3f}")
    print(f"  PDF: {args.output}")
    print("=" * 60)


if __name__ == "__main__":
    main()
