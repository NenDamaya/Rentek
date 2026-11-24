#!/usr/bin/env python3
"""
Seeder de estrés — puebla PostgreSQL con 10,000+ registros realistas.
Uso: python3 scripts/seed_db.py [--host HOST] [--port PORT] [--rows N]
"""

import argparse
import json
import random
import sys
import os
from datetime import date, timedelta
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:
    psycopg2 = None
    execute_values = None
    print("ADVERTENCIA: psycopg2 no instalado. Solo modo simulación.")

# ============================================================
# DATOS GENERADORES
# ============================================================

NOMBRES = [
    "Juan Pérez", "María García", "Carlos López", "Ana Martínez", "José Hernández",
    "Laura Sánchez", "Miguel Ángel Ruiz", "Sofía Ramírez", "Fernando Castillo", "Diana Torres",
    "Roberto Vargas", "Gabriela Mendoza", "Alejandro Cruz", "Verónica Ortega", "Ricardo Flores",
    "Patricia Navarro", "Luis Miguel Ríos", "Carmen Delgado", "Jorge Herrera", "Alicia Medina",
    "Daniel Guzmán", "Mónica Peña", "Eduardo Vega", "Ruth Aguilar", "Francisco Mena",
    "Claudia Rivas", "Héctor Paredes", "Liliana Campos", "Manuel Solís", "Rosa Bautista",
    "Oscar Vázquez", "Lourdes Téllez", "Rafael Cárdenas", "Silvia Núñez", "Ignacio León",
    "Adriana Soto", "Alberto Pacheco", "Beatriz Lara", "Salvador Miranda", "Elena Farías",
]

EMPRESAS = [
    "Constructora ARCO S.A.", "Desarrollos del Norte", "Obras Viales S.A.",
    "Constructora Río Seco", "Inmobiliaria Torres", "Comisión Nacional del Agua",
    "Municipalidad de León", "Gobierno del Estado", "Ingeniería y Cimentaciones",
    "Movimiento de Tierra Profesional", "Vialidades y Pavimentos", "Construcciones Modernas",
    "Edificaciones Urbanas", "Cimentaciones Profundas", "Desarrollos Inmobiliarios",
    "Maquinaria y Equipos del Bajío", "Transportes y Acarreos", "Minas y Canteras",
]

MACHINE_NAMES = [
    "Excavadora Hidráulica de Orugas", "Retroexcavadora (Backhoe)", "Bulldozer / Topadora",
    "Miniexcavadora", "Cargador Frontal (Payloader)", "Motoniveladora (Grader)",
    "Compactadora de Suelos / Vibrocompactador", "Minicargador (Skid Steer)",
    "Camión de Volteo / Camión Articulado", "Grúa Telescópica sobre Camión (Grúa Móvil)",
    "Pavimentadora de Asfalto (Finisher)", "Rodillo Vibratorio Doble Tambor",
    "Fresadora de Asfalto (Cold Planer)", "Planta de Asfalto Móvil",
    "Bomba de Concreto Estacionaria", "Camión Revolvedor / Mixer de Concreto",
    "Generador Eléctrico Industrial", "Compresor de Aire Industrial Portátil",
    "Plataforma Elevadora de Tijera (Scissor Lift)", "Plataforma Articulada (Boom Lift)",
    "Montacargas Telescópico (Telehandler)", "Perforadora Rotaria (Drilling Rig)",
    "Bomba de Achique / Bomba de Drenaje", "Motobomba a Gasolina",
    "Carretilla Motorizada / Dumper de Obra", "Apisonador / Compactadora Manual Tipo Rana",
    "Martillo Demoledor Eléctrico", "Cortadora de Concreto",
    "Equipo de Soldadura", "Andamio Multidireccional",
    "Tractor Agrícola de Gran Potencia", "Cosechadora de Forraje",
]

ESTADOS = ["pendiente", "confirmada", "cancelada", "completada"]


def random_phone() -> str:
    return f"555-{random.randint(1000, 9999)}"


def random_email(first: str, last: str) -> str:
    domains = ["email.com", "mail.com", "correo.mx", "outlook.com", "gmail.com"]
    return f"{first.lower()}.{last.lower()}{random.randint(1, 99)}@{random.choice(domains)}"


def random_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def generate_solicitudes(n: int) -> List[Dict]:
    records = []
    for i in range(1, n + 1):
        es_empresa = random.random() < 0.6
        if es_empresa:
            cliente = random.choice(EMPRESAS)
            contacto_nombre = random.choice(NOMBRES)
        else:
            cliente = random.choice(NOMBRES)
            contacto_nombre = cliente

        parts = contacto_nombre.split()
        contacto_email = random_email(parts[0], parts[-1])
        contacto_tel = random_phone()

        num_maquinas = random.choices([1, 1, 1, 2, 2, 3], weights=[40, 30, 20, 7, 2, 1])[0]
        maquinas = []
        for _ in range(num_maquinas):
            m = random.choice(MACHINE_NAMES)
            maquinas.append({"nombre": m, "cantidad": random.randint(1, 3)})

        fecha_inicio = random_date(date(2025, 1, 1), date(2026, 12, 1))
        duracion = random.randint(1, 90)
        fecha_fin = fecha_inicio + timedelta(days=duracion)
        estado = random.choices(ESTADOS, weights=[30, 35, 15, 20])[0]

        records.append({
            "folio": f"SOL-2026-{i:05d}",
            "cliente": cliente,
            "contacto": f"{contacto_nombre} | {contacto_email} | {contacto_tel}",
            "maquinas": json.dumps(maquinas),
            "fecha_inicio": fecha_inicio.isoformat(),
            "fecha_fin": fecha_fin.isoformat(),
            "estado": estado,
            "notas": f"Generado automáticamente - solicitud #{i}",
        })
    return records


def generate_carrito_items(n: int, user_ids: List[int]) -> List[Dict]:
    records = []
    for i in range(n):
        user_id = random.choice(user_ids)
        maquina = random.choice(MACHINE_NAMES)
        duration = random.randint(1, 30)
        duration_unit = random.choices(["dias", "semanas", "meses"], weights=[80, 15, 5])[0]
        if duration_unit == "semanas":
            duration = random.randint(1, 4)
        elif duration_unit == "meses":
            duration = random.randint(1, 3)

        precio_dia = round(random.uniform(500, 15000), 2)
        start_date = random_date(date(2026, 1, 1), date(2026, 12, 1))
        from datetime import timedelta as td2
        end_date = start_date + td2(days=duration if duration_unit == "dias" else duration * 7 if duration_unit == "semanas" else duration * 30)

        maquina_json = {
            "nombre": maquina,
            "nombre_comun": maquina,
            "categoria": random.choice(["Excavación", "Compactación", "Transporte", "Elevación", "Demolición"]),
            "precio_renta": f"${precio_dia:,.0f} MXN/día",
        }

        records.append({
            "user_id": user_id,
            "maquina_nombre": maquina,
            "maquina_json": json.dumps(maquina_json, ensure_ascii=False),
            "duration": duration,
            "duration_unit": duration_unit,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "precio_dia": precio_dia,
        })
    return records


def generate_users(n: int) -> List[Dict]:
    records = []
    for i in range(n):
        name = random.choice(NOMBRES)
        suffix = i // len(NOMBRES) + 1
        parts = name.split()
        username = f"{parts[0].lower()}.{parts[-1].lower()}{suffix}_{i}"
        email = random_email(parts[0], parts[-1])
        records.append({
            "username": username,
            "email": email,
            "password_hash": "seed_dummy_hash",
            "display_name": name,
            "role": random.choices(["user", "user", "user", "admin"], weights=[70, 20, 9, 1])[0],
        })
    return records


def _batch_insert(cur, insert_sql, items, template, conn, batch_size=500, label=""):
    import sys
    inserted = 0
    total = len(items)
    for i in range(0, total, batch_size):
        batch = items[i : i + batch_size]
        values = [tuple(item[k] for k in template) for item in batch]
        try:
            execute_values(cur, insert_sql, values, page_size=len(values))
            conn.commit()
            inserted += len(values)
        except Exception as e:
            conn.rollback()
            sys.stderr.write(f"  Error en lote {i//batch_size}: {e}\n")
        sys.stderr.write(f"  {label}: {inserted}/{total}\n")
    sys.stderr.write(f"  {label} completados: {inserted}\n")


def seed(conn, num_solicitudes: int, num_carrito: int, num_users: int, batch_size: int = 500):
    cur = conn.cursor()

    # --- Users ---
    print(f"\n[1/3] Insertando {num_users} usuarios...")
    users = generate_users(num_users)
    _batch_insert(
        cur,
        "INSERT INTO users (username, email, password_hash, display_name, role) VALUES %s ON CONFLICT (username) DO NOTHING",
        users,
        ["username", "email", "password_hash", "display_name", "role"],
        conn, batch_size, "Usuarios",
    )

    # Get actual user IDs from DB
    cur.execute("SELECT id FROM users ORDER BY id")
    user_ids = [r[0] for r in cur.fetchall()]

    # --- Solicitudes ---
    print(f"\n[2/3] Insertando {num_solicitudes} solicitudes...")
    solicitudes = generate_solicitudes(num_solicitudes)
    _batch_insert(
        cur,
        "INSERT INTO solicitudes_renta (folio, cliente, contacto, maquinas, fecha_inicio, fecha_fin, estado, notas) VALUES %s ON CONFLICT (folio) DO NOTHING",
        solicitudes,
        ["folio", "cliente", "contacto", "maquinas", "fecha_inicio", "fecha_fin", "estado", "notas"],
        conn, batch_size, "Solicitudes",
    )

    # --- Carrito items (antes cotizaciones) ---
    print(f"\n[3/3] Insertando {num_carrito} items en carrito...")
    carrito_items = generate_carrito_items(num_carrito, user_ids)
    _batch_insert(
        cur,
        "INSERT INTO carrito_items (user_id, maquina_nombre, maquina_json, duration, duration_unit, start_date, end_date, precio_dia) VALUES %s ON CONFLICT DO NOTHING",
        carrito_items,
        ["user_id", "maquina_nombre", "maquina_json", "duration", "duration_unit", "start_date", "end_date", "precio_dia"],
        conn, batch_size, "Carrito",
    )

    cur.close()


def main():
    parser = argparse.ArgumentParser(description="Seeder de estrés — 10,000+ registros")
    parser.add_argument("--host", default="postgres")
    parser.add_argument("--port", type=int, default=5432)
    parser.add_argument("--db", default="maquinaria_rag")
    parser.add_argument("--user", default="rag_user")
    parser.add_argument("--password", default="rag_pass_2026")
    parser.add_argument("--rows", type=int, default=10000, help="Número de solicitudes a generar (default: 10000)")
    parser.add_argument("--users", type=int, default=0, help="Número de usuarios (default: rows/20)")
    parser.add_argument("--carrito", type=int, default=0, help="Número de items en carrito (default: rows/2)")
    parser.add_argument("--simulate", action="store_true", help="Solo simular, no insertar")
    args = parser.parse_args()

    num_solicitudes = args.rows
    num_carrito = args.carrito or num_solicitudes // 2
    num_users = args.users or max(500, num_solicitudes // 20)

    print("=" * 60)
    print("  SEEDER DE ESTRÉS — RENTEK")
    print("=" * 60)
    print(f"  Solicitudes:  {num_solicitudes:,}")
    print(f"  Carrito:      {num_carrito:,}")
    print(f"  Usuarios:     {num_users:,}")
    print(f"  Total:        {num_solicitudes + num_carrito + num_users:,} registros")
    print()

    if args.simulate:
        print("  MODO SIMULACIÓN — generando datos de prueba...")
        sols = generate_solicitudes(5)
        print(f"  Ejemplo solicitud: {json.dumps(sols[0], indent=2)[:200]}")
        items = generate_carrito_items(3, [1])
        print(f"  Ejemplo carrito: {json.dumps(items[0], indent=2)[:200]}")
        print("  Modo simulación completado.")
        return

    if psycopg2 is None:
        print("ERROR: psycopg2 no está instalado. No se puede conectar a PostgreSQL.")
        sys.exit(1)

    conn = psycopg2.connect(
        host=args.host, port=args.port, dbname=args.db,
        user=args.user, password=args.password,
    )
    seed(conn, num_solicitudes, num_carrito, num_users)
    conn.close()

    print()
    print("=" * 60)
    print(f"  ¡SEED COMPLETADO! {num_solicitudes + num_carrito + num_users:,} registros insertados.")
    print("=" * 60)


if __name__ == "__main__":
    main()
