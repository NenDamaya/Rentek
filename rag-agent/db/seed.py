"""
Script para poblar PostgreSQL con el catálogo de maquinaria.

Uso:
    python db/seed.py                        # localhost:5432 por defecto
    python db/seed.py --host localhost --port 5432 --db maquinaria_rag --user rag_user --password rag_pass_2026
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import psycopg2
except ImportError:
    print("Instalando psycopg2-binary...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    import psycopg2

from src.catalogo import Catalogo


def get_connection(args):
    return psycopg2.connect(
        host=args.host,
        port=args.port,
        dbname=args.db,
        user=args.user,
        password=args.password,
    )


def seed_categorias(conn, catalogo):
    cur = conn.cursor()
    categorias_insertadas = {}

    cats = catalogo.resumen_categorias()
    for cat in cats:
        cur.execute(
            "INSERT INTO categorias (nombre, descripcion) VALUES (%s, %s) ON CONFLICT (nombre) DO UPDATE SET nombre=EXCLUDED.nombre RETURNING id",
            (cat["nombre"], ""),
        )
        cat_id = cur.fetchone()[0]
        categorias_insertadas[cat["nombre"]] = cat_id
        print(f"  [OK] Categoría: {cat['nombre']}")

    conn.commit()
    return categorias_insertadas


def seed_maquinas(conn, catalogo, categorias_map):
    cur = conn.cursor()

    cats = catalogo.get_categorias()
    total = 0
    for cat_name, cat_data in cats.items():
        cat_id = categorias_map.get(cat_name)
        if not cat_id:
            continue

        for mach_name, machine in cat_data["maquinas"].items():
            sinonimos = machine.get("sinonimos", [])
            recomendado = machine.get("recomendado", [])
            no_recomendado = machine.get("no_recomendado", [])
            casos_uso = machine.get("casos_uso", [])
            reglas_negocio = machine.get("reglas_negocio", [])

            preguntas = machine.get("preguntas_frecuentes", [])

            cur.execute(
                """
                INSERT INTO maquinas
                    (categoria_id, nombre, nombre_comun, marcas, modelos_tipicos,
                     precio_renta, sinonimos, perfil_cliente,
                     especificaciones, recomendado, no_recomendado,
                     casos_uso, preguntas_frecuentes, reglas_negocio)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (
                    cat_id,
                    mach_name,
                    machine.get("nombre_comun", ""),
                    machine.get("marcas", ""),
                    machine.get("modelos_tipicos", ""),
                    machine.get("precio_renta", ""),
                    sinonimos,
                    "\n".join(machine.get("perfil_cliente", [])),
                    json.dumps(machine.get("especificaciones", {})),
                    recomendado,
                    no_recomendado,
                    casos_uso,
                    json.dumps(preguntas),
                    reglas_negocio,
                ),
            )
            total += 1
            print(f"  [OK] Máquina: {mach_name}")

    conn.commit()
    return total


def seed_proyectos(conn, catalogo):
    cur = conn.cursor()

    proyectos = catalogo.get_proyectos()
    for proj in proyectos:
        cur.execute(
            """
            INSERT INTO proyectos (nombre, maquinarias, consideraciones)
            VALUES (%s, %s, %s)
            ON CONFLICT (nombre) DO NOTHING
            """,
            (proj["nombre"], proj["maquinarias"], proj.get("consideraciones", "")),
        )
        print(f"  [OK] Proyecto: {proj['nombre']}")

    conn.commit()
    return len(proyectos)


def seed_all(args=None):
    parser = argparse.ArgumentParser(description="Poblar PostgreSQL con catálogo de maquinaria")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=5432)
    parser.add_argument("--db", default="maquinaria_rag")
    parser.add_argument("--user", default="rag_user")
    parser.add_argument("--password", default="rag_pass_2026")
    args = parser.parse_args(args)

    print("=" * 60)
    print("  SEED - Poblando base de datos PostgreSQL")
    print("=" * 60)
    print(f"  Host:     {args.host}")
    print(f"  Puerto:   {args.port}")
    print(f"  Base:     {args.db}")
    print(f"  Usuario:  {args.user}")
    print()

    conn = get_connection(args)

    print("[1/3] Poblando categorías...")
    categorias_map = seed_categorias(conn, Catalogo())

    print(f"\n[2/3] Poblando máquinas...")
    total_maquinas = seed_maquinas(conn, Catalogo(), categorias_map)

    print(f"\n[3/3] Poblando proyectos...")
    total_proyectos = seed_proyectos(conn, Catalogo())

    conn.close()

    print()
    print("=" * 60)
    print(f"  ¡BASE DE DATOS POBLADA EXITOSAMENTE!")
    print(f"  Categorías: {len(categorias_map)}")
    print(f"  Máquinas:   {total_maquinas}")
    print(f"  Proyectos:  {total_proyectos}")
    print("=" * 60)


if __name__ == "__main__":
    seed_all()
