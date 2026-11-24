"""
Seed datos semi-reales para operaciones de negocio:
disponibilidad, solicitudes_renta, cotizaciones.
"""

import argparse
import json
import random
from datetime import date, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import psycopg2
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    import psycopg2

random.seed(42)

SILLA_MAQUINAS = [
    "Excavadora Hidráulica de Orugas",
    "Miniexcavadora",
    "Bulldozer / Topadora",
    "Motoniveladora (Grader)",
    "Compactadora de Suelos / Vibrocompactador",
    "Cargador Frontal (Payloader)",
    "Retroexcavadora (Backhoe)",
    "Camión de Volteo / Camión Articulado",
    "Minicargador (Skid Steer)",
    "Grúa Telescópica sobre Camión (Grúa Móvil)",
    "Plataforma Elevadora de Tijera (Scissor Lift)",
    "Plataforma Articulada (Boom Lift)",
    "Montacargas Telescópico (Telehandler)",
    "Pavimentadora de Asfalto (Finisher)",
    "Fresadora de Asfalto (Cold Planer)",
    "Perforadora Rotaria (Drilling Rig)",
    "Martinete / Hinca de Pilotes",
    "Bomba de Concreto Estacionaria",
    "Camión Revolvedor / Mixer de Concreto",
    "Generador Eléctrico Industrial",
    "Compresor de Aire Industrial Portátil",
    "Tractor Agrícola de Gran Potencia",
    "Cosechadora Combinada",
    "Robot de Demolición",
    "Camión Vacuosucción (Vac Truck)",
    "Bomba de Achique / Bomba de Drenaje",
    "Apisonador / Compactadora Manual Tipo Rana",
    "Motobomba a Gasolina",
    "Cortadora de Concreto y Asfalto",
    "Lavadora de Alta Presión a Gasolina",
    "Generador Portátil a Gasolina",
    "Miniexcavadora de Ancho Ultrareducido (< 1.5 m)",
    "Apisonador Manual Compacto",
    "Carretilla Motorizada / Dumper de Obra",
]

MAQUINAS_ALTA_DEMANDA = {
    "Excavadora Hidráulica de Orugas": 0.55,
    "Retroexcavadora (Backhoe)": 0.50,
    "Bulldozer / Topadora": 0.50,
    "Miniexcavadora": 0.45,
    "Cargador Frontal (Payloader)": 0.45,
    "Camión de Volteo / Camión Articulado": 0.45,
    "Grúa Telescópica sobre Camión (Grúa Móvil)": 0.40,
    "Compactadora de Suelos / Vibrocompactador": 0.35,
}

MAQUINAS_MEDIA_DEMANDA = {
    "Motoniveladora (Grader)": 0.25,
    "Plataforma Elevadora de Tijera (Scissor Lift)": 0.20,
    "Plataforma Articulada (Boom Lift)": 0.20,
    "Montacargas Telescópico (Telehandler)": 0.20,
    "Minicargador (Skid Steer)": 0.25,
    "Generador Eléctrico Industrial": 0.20,
    "Compresor de Aire Industrial Portátil": 0.15,
    "Bomba de Concreto Estacionaria": 0.20,
    "Camión Revolvedor / Mixer de Concreto": 0.25,
    "Pavimentadora de Asfalto (Finisher)": 0.20,
    "Perforadora Rotaria (Drilling Rig)": 0.15,
    "Tractor Agrícola de Gran Potencia": 0.20,
}

NOTAS_RESERVA = [
    "Reservado: Constructora ARCO",
    "Reservado: Municipalidad de León",
    "En obra: Proyecto Vía Rápida",
    "En obra: Edificio Corporativo Centro",
    "Mantenimiento programado - servicio mensual",
    "Reservado: Desarrollos del Norte",
    "En obra: Fraccionamiento Los Pinos",
    "Reservado: Obras Viales S.A.",
    "Reservado: Constructora Río Seco",
    "Mantenimiento mayor - fuera de servicio",
    "Reservado: Ing. María García",
    "En obra: Puente Vehicular Santa Fe",
]

SOLICITUDES_EJEMPLO = [
    {
        "folio": "SOL-2026-0001",
        "cliente": "Constructora ARCO S.A.",
        "contacto": "Carlos Mendoza | carlos@arco.com | 555-0101",
        "maquinas": [
            {"nombre": "Excavadora Hidráulica de Orugas", "cantidad": 2},
            {"nombre": "Bulldozer / Topadora", "cantidad": 1},
        ],
        "fecha_inicio": date(2026, 6, 15),
        "fecha_fin": date(2026, 6, 30),
        "estado": "confirmada",
        "notas": "Proyecto de excavación para cimentación de edificio de 10 pisos",
    },
    {
        "folio": "SOL-2026-0002",
        "cliente": "Ing. María García López",
        "contacto": "María García | maria.garcia@email.com | 555-0202",
        "maquinas": [
            {"nombre": "Miniexcavadora", "cantidad": 1},
        ],
        "fecha_inicio": date(2026, 6, 10),
        "fecha_fin": date(2026, 6, 12),
        "estado": "pendiente",
        "notas": "Excavación para cisterna en casa particular",
    },
    {
        "folio": "SOL-2026-0003",
        "cliente": "Desarrollos del Norte S.A.P.I.",
        "contacto": "Ana Torres | ana.torres@dnorte.com | 555-0303",
        "maquinas": [
            {"nombre": "Grúa Telescópica sobre Camión (Grúa Móvil)", "cantidad": 1},
        ],
        "fecha_inicio": date(2026, 6, 20),
        "fecha_fin": date(2026, 6, 25),
        "estado": "pendiente",
        "notas": "Montaje de estructura metálica para nave industrial",
    },
    {
        "folio": "SOL-2026-0004",
        "cliente": "Municipalidad de León",
        "contacto": "Ing. Roberto Sánchez | r.sanchez@leon.gob.mx | 555-0404",
        "maquinas": [
            {"nombre": "Motoniveladora (Grader)", "cantidad": 1},
            {"nombre": "Compactadora de Suelos / Vibrocompactador", "cantidad": 1},
        ],
        "fecha_inicio": date(2026, 7, 5),
        "fecha_fin": date(2026, 7, 19),
        "estado": "confirmada",
        "notas": "Mantenimiento de caminos rurales - temporada de lluvias",
    },
    {
        "folio": "SOL-2026-0005",
        "cliente": "Juan Pérez López",
        "contacto": "Juan Pérez | juan.perez@email.com | 555-0505",
        "maquinas": [
            {"nombre": "Retroexcavadora (Backhoe)", "cantidad": 1},
        ],
        "fecha_inicio": date(2026, 6, 8),
        "fecha_fin": date(2026, 6, 10),
        "estado": "cancelada",
        "notas": "Cliente canceló por cambio de fechas del proyecto",
    },
    {
        "folio": "SOL-2026-0006",
        "cliente": "Constructora Río Seco S.A.",
        "contacto": "Ricardo Flores | r.flores@rioseco.com | 555-0606",
        "maquinas": [
            {"nombre": "Compactadora de Suelos / Vibrocompactador", "cantidad": 2},
            {"nombre": "Cargador Frontal (Payloader)", "cantidad": 1},
        ],
        "fecha_inicio": date(2026, 7, 1),
        "fecha_fin": date(2026, 7, 15),
        "estado": "pendiente",
        "notas": "Compactación de terraplén para nuevo fraccionamiento",
    },
    {
        "folio": "SOL-2026-0007",
        "cliente": "Obras Viales S.A. de C.V.",
        "contacto": "Lic. Diana Muñoz | d.munoz@obrasviales.com | 555-0707",
        "maquinas": [
            {"nombre": "Pavimentadora de Asfalto (Finisher)", "cantidad": 1},
            {"nombre": "Fresadora de Asfalto (Cold Planer)", "cantidad": 1},
            {"nombre": "Camión de Volteo / Camión Articulado", "cantidad": 3},
        ],
        "fecha_inicio": date(2026, 8, 10),
        "fecha_fin": date(2026, 9, 10),
        "estado": "pendiente",
        "notas": "Rehabilitación de carpeta asfáltica en carretera federal",
    },
    {
        "folio": "SOL-2026-0008",
        "cliente": "Rancho San Isidro",
        "contacto": "José Ángel Ruiz | jose.ruiz@live.com | 555-0808",
        "maquinas": [
            {"nombre": "Tractor Agrícola de Gran Potencia", "cantidad": 1},
        ],
        "fecha_inicio": date(2026, 6, 12),
        "fecha_fin": date(2026, 6, 14),
        "estado": "confirmada",
        "notas": "Preparación de terreno para siembra de maíz",
    },
    {
        "folio": "SOL-2026-0009",
        "cliente": "Inmobiliaria Torres Gemelas",
        "contacto": "Arq. Laura Vega | l.vega@torresgemelas.com | 555-0909",
        "maquinas": [
            {"nombre": "Grúa Telescópica sobre Camión (Grúa Móvil)", "cantidad": 1},
            {"nombre": "Plataforma Elevadora de Tijera (Scissor Lift)", "cantidad": 2},
        ],
        "fecha_inicio": date(2026, 7, 10),
        "fecha_fin": date(2026, 8, 10),
        "estado": "pendiente",
        "notas": "Montaje de fachada y acabados en torre de 15 niveles",
    },
    {
        "folio": "SOL-2026-0010",
        "cliente": "Comisión Nacional del Agua",
        "contacto": "Ing. Héctor Ramírez | h.ramirez@conagua.gob.mx | 555-1010",
        "maquinas": [
            {"nombre": "Bomba de Achique / Bomba de Drenaje", "cantidad": 4},
            {"nombre": "Generador Eléctrico Industrial", "cantidad": 1},
            {"nombre": "Camión Vacuosucción (Vac Truck)", "cantidad": 1},
        ],
        "fecha_inicio": date(2026, 6, 20),
        "fecha_fin": date(2026, 7, 20),
        "estado": "confirmada",
        "notas": "Desazolve y drenaje en zona inundable - Tabasco",
    },
]

COTIZACIONES_EJEMPLO = [
    {
        "folio": "COT-2026-001",
        "cliente": "Constructora ARCO S.A.",
        "contacto": "Carlos Mendoza | carlos@arco.com | 555-0101",
        "maquinas": [
            {"nombre": "Excavadora Hidráulica de Orugas", "cantidad": 2, "precio_unitario": 5250.00, "subtotal": 10500.00},
            {"nombre": "Bulldozer / Topadora", "cantidad": 1, "precio_unitario": 6500.00, "subtotal": 6500.00},
        ],
        "dias": 7,
        "subtotal": 119000.00,
        "descuento": 11900.00,
        "total": 107100.00,
        "valida_hasta": date(2026, 7, 15),
    },
    {
        "folio": "COT-2026-002",
        "cliente": "Ing. María García López",
        "contacto": "María García | maria.garcia@email.com | 555-0202",
        "maquinas": [
            {"nombre": "Miniexcavadora", "cantidad": 1, "precio_unitario": 2250.00, "subtotal": 2250.00},
        ],
        "dias": 3,
        "subtotal": 6750.00,
        "descuento": 0.00,
        "total": 6750.00,
        "valida_hasta": date(2026, 7, 10),
    },
    {
        "folio": "COT-2026-003",
        "cliente": "Municipalidad de León",
        "contacto": "Roberto Sánchez | r.sanchez@leon.gob.mx | 555-0404",
        "maquinas": [
            {"nombre": "Motoniveladora (Grader)", "cantidad": 1, "precio_unitario": 6500.00, "subtotal": 6500.00},
        ],
        "dias": 15,
        "subtotal": 97500.00,
        "descuento": 14625.00,
        "total": 82875.00,
        "valida_hasta": date(2026, 8, 5),
    },
    {
        "folio": "COT-2026-004",
        "cliente": "Rancho San Isidro",
        "contacto": "José Ángel Ruiz | jose.ruiz@live.com | 555-0808",
        "maquinas": [
            {"nombre": "Tractor Agrícola de Gran Potencia", "cantidad": 1, "precio_unitario": 4000.00, "subtotal": 4000.00},
        ],
        "dias": 5,
        "subtotal": 20000.00,
        "descuento": 1000.00,
        "total": 19000.00,
        "valida_hasta": date(2026, 7, 12),
    },
    {
        "folio": "COT-2026-005",
        "cliente": "Desarrollos del Norte S.A.P.I.",
        "contacto": "Ana Torres | ana.torres@dnorte.com | 555-0303",
        "maquinas": [
            {"nombre": "Grúa Telescópica sobre Camión (Grúa Móvil)", "cantidad": 1, "precio_unitario": 28500.00, "subtotal": 28500.00},
        ],
        "dias": 5,
        "subtotal": 142500.00,
        "descuento": 7125.00,
        "total": 135375.00,
        "valida_hasta": date(2026, 7, 20),
    },
    {
        "folio": "COT-2026-006",
        "cliente": "Constructora Río Seco S.A.",
        "contacto": "Ricardo Flores | r.flores@rioseco.com | 555-0606",
        "maquinas": [
            {"nombre": "Compactadora de Suelos / Vibrocompactador", "cantidad": 2, "precio_unitario": 4000.00, "subtotal": 8000.00},
            {"nombre": "Cargador Frontal (Payloader)", "cantidad": 1, "precio_unitario": 4750.00, "subtotal": 4750.00},
        ],
        "dias": 15,
        "subtotal": 191250.00,
        "descuento": 28687.50,
        "total": 162562.50,
        "valida_hasta": date(2026, 8, 1),
    },
]


def get_connection(args):
    return psycopg2.connect(
        host=args.host,
        port=args.port,
        dbname=args.db,
        user=args.user,
        password=args.password,
    )


def seed_disponibilidad(conn):
    cur = conn.cursor()
    cur.execute("SELECT id, nombre FROM maquinas ORDER BY nombre")
    maquinas = {row[1]: row[0] for row in cur.fetchall()}

    hoy = date(2026, 6, 4)
    fin = date(2026, 9, 30)
    delta = (fin - hoy).days

    insertados = 0
    saltados = 0

    for nombre_maquina, maquina_id in maquinas.items():
        prob_no_disponible = MAQUINAS_ALTA_DEMANDA.get(nombre_maquina, 0)
        if prob_no_disponible == 0:
            prob_no_disponible = MAQUINAS_MEDIA_DEMANDA.get(nombre_maquina, 0.10)

        prob_no_disponible = max(0.05, min(0.60, prob_no_disponible))

        for dia_offset in range(delta):
            fecha = hoy + timedelta(days=dia_offset)
            es_fin_semana = fecha.weekday() >= 5

            disponible = True
            notas = ""

            if random.random() < prob_no_disponible:
                disponible = False
                notas = random.choice(NOTAS_RESERVA)

            if es_fin_semana and random.random() < 0.3:
                disponible = False
                if not notas:
                    notas = "Fin de semana - disponible solo con solicitud previa"

            cur.execute(
                """INSERT INTO disponibilidad (maquina_id, fecha, disponible, notas)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT (maquina_id, fecha) DO NOTHING""",
                (maquina_id, fecha, disponible, notas),
            )
            if cur.rowcount > 0:
                insertados += 1
            else:
                saltados += 1

    conn.commit()
    cur.close()
    print(f"  Disponibilidad: {insertados} insertados, {saltados} saltados")
    return insertados


def seed_solicitudes(conn):
    cur = conn.cursor()
    count = 0
    for sol in SOLICITUDES_EJEMPLO:
        cur.execute(
            """INSERT INTO solicitudes_renta
               (folio, cliente, contacto, maquinas, fecha_inicio, fecha_fin, estado, notas)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (folio) DO NOTHING""",
            (
                sol["folio"],
                sol["cliente"],
                sol["contacto"],
                json.dumps(sol["maquinas"]),
                sol["fecha_inicio"],
                sol["fecha_fin"],
                sol["estado"],
                sol["notas"],
            ),
        )
        if cur.rowcount > 0:
            count += 1
            print(f"  [OK] Solicitud: {sol['folio']} - {sol['cliente']}")
    conn.commit()
    cur.close()
    return count


def seed_cotizaciones(conn):
    cur = conn.cursor()
    count = 0
    for cot in COTIZACIONES_EJEMPLO:
        cur.execute(
            """INSERT INTO cotizaciones
               (folio, cliente, contacto, maquinas, dias, subtotal, descuento, total, valida_hasta)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (folio) DO NOTHING""",
            (
                cot["folio"],
                cot["cliente"],
                cot["contacto"],
                json.dumps(cot["maquinas"]),
                cot["dias"],
                cot["subtotal"],
                cot["descuento"],
                cot["total"],
                cot["valida_hasta"],
            ),
        )
        if cur.rowcount > 0:
            count += 1
            print(f"  [OK] Cotización: {cot['folio']} - {cot['cliente']}")
    conn.commit()
    cur.close()
    return count


def seed_all(args=None):
    parser = argparse.ArgumentParser(description="Poblar datos de negocio en PostgreSQL")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=5432)
    parser.add_argument("--db", default="maquinaria_rag")
    parser.add_argument("--user", default="rag_user")
    parser.add_argument("--password", default="rag_pass_2026")
    parser.add_argument("--skip-disponibilidad", action="store_true", help="Saltar seed de disponibilidad")
    args = parser.parse_args(args)

    print("=" * 60)
    print("  SEED BUSINESS - Poblando datos de negocio")
    print("=" * 60)
    print(f"  Host:     {args.host}")
    print(f"  Puerto:   {args.port}")
    print(f"  Fecha ref: Junio - Septiembre 2026")
    print()

    conn = get_connection(args)

    if not args.skip_disponibilidad:
        print("\n[1/3] Poblando disponibilidad...")
        seed_disponibilidad(conn)

    print("\n[2/3] Poblando solicitudes de renta...")
    total_sol = seed_solicitudes(conn)
    print(f"  Total solicitudes insertadas: {total_sol}")

    print("\n[3/3] Poblando cotizaciones...")
    total_cot = seed_cotizaciones(conn)
    print(f"  Total cotizaciones insertadas: {total_cot}")

    conn.close()

    print()
    print("=" * 60)
    print("  ¡DATOS DE NEGOCIO POBLADOS EXITOSAMENTE!")
    print("=" * 60)


if __name__ == "__main__":
    seed_all()
