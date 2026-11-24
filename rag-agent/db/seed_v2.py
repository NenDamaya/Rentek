"""
Seed completo: categorías, 100+ máquinas, proyectos, precios estructurados.
Uso: python db/seed_v2.py
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import psycopg2
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    import psycopg2


CATEGORIAS = [
    ("Movimiento de Tierra", "Máquinas para excavación, nivelación y compactación de suelos"),
    ("Elevación y Grúas", "Equipos para izaje y elevación de cargas en altura"),
    ("Pavimentación y Asfalto", "Maquinaria para construcción y mantenimiento de vías"),
    ("Perforación y Cimentación", "Equipos para perforación de pozos y cimentaciones profundas"),
    ("Manejo de Concreto", "Bombas, mezcladoras y equipo para manejo de concreto"),
    ("Generación de Energía y Servicios", "Generadores, compresores y equipos de servicios"),
    ("Maquinaria Agrícola", "Tractores, cosechadoras y equipo agrícola"),
    ("Maquinaria para Demolición", "Equipos especializados en demolición"),
    ("Equipos para Agua y Saneamiento", "Bombas, vacuotanques y equipo hidráulico"),
    ("Equipos Compactos a Gasolina", "Herramientas compactas motorizadas"),
    ("Maquinaria para Espacios Reducidos", "Equipos para acceso limitado y espacios confinados"),
    ("Manejo de Materiales", "Montacargas, hornos y equipo de acarreo"),
    ("Iluminación y Seguridad", "Torres de iluminación y equipo de seguridad vial"),
    ("Túneles y Minería", "Equipos especializados para excavación en túneles"),
    ("Riego y Agricultura", "Sistemas de riego y equipo agrícola especializado"),
]

MAQUINAS_EXTRA = [
    # --- Movimiento de Tierra (9 extra) ---
    {"categoria": "Movimiento de Tierra", "nombre": "Excavadora de Orugas Grande (50 ton)", "nombre_comun": "Excavadora grande", "marcas": "Caterpillar, Komatsu, Hitachi", "modelos_tipicos": "CAT 374, Komatsu PC490", "precio_renta": "$9,000 - $15,000 MXN/día", "precio_dia": 9000, "precio_semana": 56000, "precio_mes": 190000, "sinonimos": ["excavadora grande", "excavadora 50 ton", "pala grande"], "especificaciones": {"peso": "50,000 kg", "potencia": "300 - 400 HP", "capacidad_cucharon": "2.5 - 3.5 m³"}, "recomendado": ["Minería", "Gran movimiento de tierra"], "no_recomendado": ["Obras pequeñas"], "casos_uso": ["Minería a cielo abierto", "Excavación masiva"], "costo_operador_dia": 2500, "costo_transporte": 6000},
    {"categoria": "Movimiento de Tierra", "nombre": "Retroexcavadora con Martillo", "nombre_comun": "Retro con martillo", "marcas": "Caterpillar, John Deere, Case", "modelos_tipicos": "CAT 430F2 con martillo, Case 590SN", "precio_renta": "$3,500 - $5,500 MXN/día", "precio_dia": 3500, "precio_semana": 22000, "precio_mes": 73000, "sinonimos": ["retro martillo", "retroexcavadora martillo"], "especificaciones": {"peso": "8,000 kg", "potencia": "90 HP"}, "recomendado": ["Demolición ligera", "Rocas"], "no_recomendado": ["Grandes demoliciones"], "casos_uso": ["Demolición de banquetas", "Rompimiento de rocas"], "costo_operador_dia": 1600, "costo_transporte": 2500},
    {"categoria": "Movimiento de Tierra", "nombre": "Cargador Frontal de Orugas", "nombre_comun": "Cargador de orugas", "marcas": "Caterpillar, Komatsu, Liebherr", "modelos_tipicos": "CAT 973, Komatsu D155", "precio_renta": "$5,000 - $9,000 MXN/día", "precio_dia": 5000, "precio_semana": 32000, "precio_mes": 105000, "sinonimos": ["cargador orugas", "track loader"], "especificaciones": {"peso": "15,000 kg", "capacidad_cucharon": "3.0 m³"}, "recomendado": ["Terrenos blandos", "Minas"], "no_recomendado": ["Pavimentos"], "casos_uso": ["Carga en terrenos difíciles"], "costo_operador_dia": 2000, "costo_transporte": 4500},
    {"categoria": "Movimiento de Tierra", "nombre": "Tractor de Orugas (Dozer Mediano)", "nombre_comun": "Tractor orugas", "marcas": "Caterpillar, Komatsu, John Deere", "modelos_tipicos": "CAT D8, Komatsu D85", "precio_renta": "$7,000 - $12,000 MXN/día", "precio_dia": 7000, "precio_semana": 44000, "precio_mes": 145000, "sinonimos": ["dozer mediano", "tractor orugas mediano"], "especificaciones": {"peso": "30,000 kg", "potencia": "300 HP"}, "recomendado": ["Empuje de tierra", "Desmonte"], "no_recomendado": ["Obras ligeras"], "casos_uso": ["Desmonte pesado", "Empuje de material"], "costo_operador_dia": 2200, "costo_transporte": 5000},
    {"categoria": "Movimiento de Tierra", "nombre": "Pipa de Agua para Compactación", "nombre_comun": "Pipa", "marcas": "International, Kenworth, Freightliner", "modelos_tipicos": "International 7600, Kenworth T800", "precio_renta": "$3,000 - $5,000 MXN/día", "precio_dia": 3000, "precio_semana": 19000, "precio_mes": 65000, "sinonimos": ["pipa", "camión pipa", "pipa de agua"], "especificaciones": {"capacidad": "10,000 - 20,000 L"}, "recomendado": ["Compactación de suelos", "Control de polvo"], "no_recomendado": ["Transporte de agua potable"], "casos_uso": ["Riego para compactación", "Control de polvo en obra"], "costo_operador_dia": 1500, "costo_transporte": 3000},
    {"categoria": "Movimiento de Tierra", "nombre": "Camión de Volteo Sencillo (14 m³)", "nombre_comun": "Volteo sencillo", "marcas": "International, Kenworth, Ford", "modelos_tipicos": "International HX520, Kenworth T880", "precio_renta": "$3,500 - $5,500 MXN/día", "precio_dia": 3500, "precio_semana": 22000, "precio_mes": 73000, "sinonimos": ["volteo sencillo", "camión de volteo 14m3"], "especificaciones": {"capacidad": "14 m³", "potencia": "350 - 450 HP"}, "recomendado": ["Acarreo en obras urbanas"], "no_recomendado": ["Minería pesada"], "casos_uso": ["Acarreo de tierra", "Transporte de escombro"], "costo_operador_dia": 1800, "costo_transporte": 2000},
    {"categoria": "Movimiento de Tierra", "nombre": "Camión Fuera de Carretera (Articulado 40 ton)", "nombre_comun": "Camión articulado", "marcas": "Caterpillar, Volvo, Komatsu", "modelos_tipicos": "CAT 740, Volvo A60H", "precio_renta": "$12,000 - $20,000 MXN/día", "precio_dia": 12000, "precio_semana": 75000, "precio_mes": 250000, "sinonimos": ["camión articulado 40 ton", "dumper articulado"], "especificaciones": {"capacidad": "40 ton", "potencia": "450 HP"}, "recomendado": ["Minería", "Grandes movimientos de tierra"], "no_recomendado": ["Vías públicas"], "casos_uso": ["Acarreo en mina", "Grandes obras"], "costo_operador_dia": 3000, "costo_transporte": 8000},
    {"categoria": "Movimiento de Tierra", "nombre": "Cargador Frontal Pequeño (1.5 m³)", "nombre_comun": "Cargador pequeño", "marcas": "Caterpillar, Volvo, John Deere", "modelos_tipicos": "CAT 908, Volvo L60H", "precio_renta": "$2,500 - $4,000 MXN/día", "precio_dia": 2500, "precio_semana": 16000, "precio_mes": 52000, "sinonimos": ["cargador pequeño", "payloader chico"], "especificaciones": {"capacidad_cucharon": "1.5 m³", "potencia": "80 HP"}, "recomendado": ["Obras medianas", "Carga de camiones"], "no_recomendado": ["Minería"], "casos_uso": ["Carga de materiales", "Obras de construcción"], "costo_operador_dia": 1400, "costo_transporte": 2000},
    {"categoria": "Movimiento de Tierra", "nombre": "Niveladora Pequeña (Mini Grader)", "nombre_comun": "Mini grader", "marcas": "Caterpillar, John Deere, Wacker Neuson", "modelos_tipicos": "CAT 120, John Deere 770G", "precio_renta": "$3,000 - $5,000 MXN/día", "precio_dia": 3000, "precio_semana": 19000, "precio_mes": 65000, "sinonimos": ["mini grader", "niveladora pequeña"], "especificaciones": {"peso": "6,000 kg", "potencia": "80 HP"}, "recomendado": ["Obras pequeñas", "Jardinería"], "no_recomendado": ["Carreteras"], "casos_uso": ["Nivelación de estacionamientos", "Jardinería"], "costo_operador_dia": 1400, "costo_transporte": 2000},

    # --- Elevación y Grúas (7 extra) ---
    {"categoria": "Elevación y Grúas", "nombre": "Grúa Telescópica Mediana (20 ton)", "nombre_comun": "Grúa 20 ton", "marcas": "Tadano, Grove, Link-Belt", "modelos_tipicos": "Tadano GR-200E, Grove RT530", "precio_renta": "$10,000 - $16,000 MXN/día", "precio_dia": 10000, "precio_semana": 63000, "precio_mes": 210000, "sinonimos": ["grúa 20 ton", "grúa mediana"], "especificaciones": {"capacidad": "20 ton", "altura_max": "35 m"}, "recomendado": ["Montaje de estructura", "Izaje de equipos"], "no_recomendado": ["Edificios muy altos"], "casos_uso": ["Montaje de naves", "Izaje de maquinaria"], "costo_operador_dia": 2500, "costo_transporte": 5000},
    {"categoria": "Elevación y Grúas", "nombre": "Grúa Torre de Brazo Basculante", "nombre_comun": "Grúa brazo basculante", "marcas": "Liebherr, Potain, Comansa", "modelos_tipicos": "Liebherr 125C, Potain IGO T130", "precio_renta": "$20,000 - $40,000 MXN/mes", "precio_dia": 20000, "precio_semana": 70000, "precio_mes": 200000, "sinonimos": ["grúa torre basculante", "luffing jib"], "especificaciones": {"capacidad": "4 - 8 ton", "altura": "50 m"}, "recomendado": ["Edificios en zonas urbanas", "Espacios reducidos"], "no_recomendado": ["Obras pequeñas"], "casos_uso": ["Construcción en zonas densas"], "costo_operador_dia": 2500, "costo_transporte": 12000},
    {"categoria": "Elevación y Grúas", "nombre": "Plataforma de Tijera de Gran Altura (20 m)", "nombre_comun": "Tijera grande", "marcas": "JLG, Genie, Skyjack", "modelos_tipicos": "JLG 2646ES, Genie GS-4047", "precio_renta": "$2,500 - $4,500 MXN/día", "precio_dia": 2500, "precio_semana": 16000, "precio_mes": 52000, "sinonimos": ["tijera grande", "tijera 20m"], "especificaciones": {"altura_max": "20 m", "capacidad": "600 kg"}, "recomendado": ["Mantenimiento de naves altas"], "no_recomendado": ["Espacios interiores bajos"], "casos_uso": ["Mantenimiento de naves", "Instalación de tuberías"], "costo_operador_dia": 0, "costo_transporte": 1800},
    {"categoria": "Elevación y Grúas", "nombre": "Elevador de Mástil (Mast Climber)", "nombre_comun": "Elevador de mástil", "marcas": "Alimak, Hek, Fraco", "modelos_tipicos": "Alimak SC-45, Hek 2000", "precio_renta": "$3,000 - $6,000 MXN/mes", "precio_dia": 3000, "precio_semana": 10000, "precio_mes": 35000, "sinonimos": ["elevador de mástil", "mast climber"], "especificaciones": {"capacidad": "500 - 2,000 kg", "altura": "100 m"}, "recomendado": ["Fachadas", "Acabados en altura"], "no_recomendado": ["Cargas puntuales"], "casos_uso": ["Instalación de fachadas", "Mantenimiento"], "costo_operador_dia": 0, "costo_transporte": 3000},
    {"categoria": "Elevación y Grúas", "nombre": "Grúa Todo Terreno (All Terrain)", "nombre_comun": "Grúa todo terreno", "marcas": "Liebherr, Grove, Tadano", "modelos_tipicos": "Liebherr LTM 1050, Grove GMK3050", "precio_renta": "$18,000 - $35,000 MXN/día", "precio_dia": 18000, "precio_semana": 110000, "precio_mes": 370000, "sinonimos": ["grúa all terrain", "grúa todo terreno"], "especificaciones": {"capacidad": "50 - 100 ton", "altura_max": "60 m"}, "recomendado": ["Terrenos difíciles", "Grandes obras"], "no_recomendado": ["Obras pequeñas"], "casos_uso": ["Montaje de equipos pesados", "Obras viales"], "costo_operador_dia": 3500, "costo_transporte": 10000},
    {"categoria": "Elevación y Grúas", "nombre": "Polipasto Eléctrico de Cadena", "nombre_comun": "Polipasto", "marcas": "Kone, Demag, Harrington", "modelos_tipicos": "Kone CLX, Demag DC-Com 5", "precio_renta": "$500 - $1,500 MXN/día", "precio_dia": 500, "precio_semana": 3200, "precio_mes": 10000, "sinonimos": ["polipasto", "hoist eléctrico"], "especificaciones": {"capacidad": "500 - 5,000 kg"}, "recomendado": ["Talleres", "Almacenes"], "no_recomendado": ["Obras grandes"], "casos_uso": ["Izaje en talleres", "Carga en bodegas"], "costo_operador_dia": 0, "costo_transporte": 300},
    {"categoria": "Elevación y Grúas", "nombre": "Grúa Viajera (Puente Grúa)", "nombre_comun": "Puente grúa", "marcas": "Kone, Demag, Street", "modelos_tipicos": "Kone CXT-10, Demag DC 10", "precio_renta": "$5,000 - $12,000 MXN/mes", "precio_dia": 5000, "precio_semana": 18000, "precio_mes": 60000, "sinonimos": ["puente grúa", "grúa viajera"], "especificaciones": {"capacidad": "5 - 20 ton", "vano": "10 - 30 m"}, "recomendado": ["Naves industriales", "Talleres"], "no_recomendado": ["Exteriores"], "casos_uso": ["Manejo de carga en naves"], "costo_operador_dia": 0, "costo_transporte": 5000},

    # --- Pavimentación y Asfalto (5 extra) ---
    {"categoria": "Pavimentación y Asfalto", "nombre": "Rodillo Tándem (Compactadora de Asfalto)", "nombre_comun": "Rodillo tándem", "marcas": "Hamm, BOMAG, Dynapac", "modelos_tipicos": "Hamm HD+ 90, BOMAG BW151AC", "precio_renta": "$3,500 - $6,000 MXN/día", "precio_dia": 3500, "precio_semana": 22000, "precio_mes": 73000, "sinonimos": ["rodillo tándem", "compactadora tándem"], "especificaciones": {"peso": "8,000 kg", "ancho": "1.5 m"}, "recomendado": ["Compactación de asfalto"], "no_recomendado": ["Suelos"], "casos_uso": ["Compactación de carpeta asfáltica"], "costo_operador_dia": 1800, "costo_transporte": 3500},
    {"categoria": "Pavimentación y Asfalto", "nombre": "Rodillo Neumático", "nombre_comun": "Rodillo llantas", "marcas": "Hamm, BOMAG, Dynapac", "modelos_tipicos": "Hamm GRW 280, BOMAG BW24RH", "precio_renta": "$3,000 - $5,000 MXN/día", "precio_dia": 3000, "precio_semana": 19000, "precio_mes": 65000, "sinonimos": ["rodillo neumático", "rodillo de llantas"], "especificaciones": {"peso": "15,000 kg"}, "recomendado": ["Sellado de asfalto"], "no_recomendado": ["Compactación de suelos"], "casos_uso": ["Sellado de carpeta asfáltica"], "costo_operador_dia": 1800, "costo_transporte": 3500},
    {"categoria": "Pavimentación y Asfalto", "nombre": "Extendedora de Concreto Hidráulico", "nombre_comun": "Extendedora concreto", "marcas": "Gomaco, Wirtgen, Power Curbers", "modelos_tipicos": "Gomaco GP-2600, Wirtgen SP 250", "precio_renta": "$10,000 - $20,000 MXN/día", "precio_dia": 10000, "precio_semana": 63000, "precio_mes": 210000, "sinonimos": ["extendedora concreto", "pavimentadora concreto"], "especificaciones": {"ancho": "4 - 10 m"}, "recomendado": ["Pavimentos de concreto hidráulico"], "no_recomendado": ["Asfalto"], "casos_uso": ["Carreteras de concreto", "Aeropistas"], "costo_operador_dia": 2500, "costo_transporte": 8000},
    {"categoria": "Pavimentación y Asfalto", "nombre": "Barredora Industrial", "nombre_comun": "Barredora", "marcas": "Sweepster, Elgin, Johnston", "modelos_tipicos": "Elgin Crosswind, Johnston 610", "precio_renta": "$2,000 - $4,000 MXN/día", "precio_dia": 2000, "precio_semana": 12500, "precio_mes": 42000, "sinonimos": ["barredora", "barredora industrial"], "especificaciones": {"capacidad_tolva": "2 - 5 m³"}, "recomendado": ["Limpieza de calles", "Obras viales"], "no_recomendado": ["Limpieza de interiores"], "casos_uso": ["Limpieza de calles", "Barrido de obras"], "costo_operador_dia": 1200, "costo_transporte": 2000},
    {"categoria": "Pavimentación y Asfalto", "nombre": "Máquina de Sellado de Juntas", "nombre_comun": "Selladora juntas", "marcas": "Cimline, Marathon, Wirtgen", "modelos_tipicos": "Cimline DuraPatch, Marathon 150", "precio_renta": "$1,500 - $3,000 MXN/día", "precio_dia": 1500, "precio_semana": 9500, "precio_mes": 32000, "sinonimos": ["selladora juntas", "selladora asfalto"], "especificaciones": {"capacidad_tanque": "200 L"}, "recomendado": ["Mantenimiento de pavimentos"], "no_recomendado": ["Obras nuevas"], "casos_uso": ["Sellado de grietas"], "costo_operador_dia": 0, "costo_transporte": 1500},

    # --- Perforación y Cimentación (5 extra) ---
    {"categoria": "Perforación y Cimentación", "nombre": "Perforadora de Pozos de Agua", "nombre_comun": "Perforadora pozos", "marcas": "Schramm, Atlas Copco, IMT", "modelos_tipicos": "Schramm T300, IMT 800", "precio_renta": "$15,000 - $30,000 MXN/día", "precio_dia": 15000, "precio_semana": 95000, "precio_mes": 320000, "sinonimos": ["perforadora pozos agua"], "especificaciones": {"profundidad": "200 - 500 m", "diametro": "150 - 400 mm"}, "recomendado": ["Pozos de agua"], "no_recomendado": ["Cimentaciones"], "casos_uso": ["Perforación de pozos de agua"], "costo_operador_dia": 3000, "costo_transporte": 8000},
    {"categoria": "Perforación y Cimentación", "nombre": "Equipo de Jet Grouting", "nombre_comun": "Jet grouting", "marcas": "TREVI, Keller, Bauer", "modelos_tipicos": "TREVI GM-20, Bauer BG 36", "precio_renta": "$18,000 - $35,000 MXN/día", "precio_dia": 18000, "precio_semana": 110000, "precio_mes": 370000, "sinonimos": ["jet grouting", "mejoramiento de suelos"], "especificaciones": {"presion": "400 - 600 bar"}, "recomendado": ["Mejoramiento de suelos"], "no_recomendado": ["Obras pequeñas"], "casos_uso": ["Mejoramiento de suelos blandos"], "costo_operador_dia": 3500, "costo_transporte": 10000},
    {"categoria": "Perforación y Cimentación", "nombre": "Ancladora de Suelos", "nombre_comun": "Ancladora", "marcas": "Atlas Copco, Epiroc, Comacchio", "modelos_tipicos": "Atlas Copco FlexiROC D65, Comacchio MC1100", "precio_renta": "$10,000 - $18,000 MXN/día", "precio_dia": 10000, "precio_semana": 63000, "precio_mes": 210000, "sinonimos": ["ancladora", "equipo de anclajes"], "especificaciones": {"profundidad": "20 - 50 m"}, "recomendado": ["Muros de contención"], "no_recomendado": ["Anclajes pequeños"], "casos_uso": ["Anclajes para muros milán"], "costo_operador_dia": 3000, "costo_transporte": 6000},
    {"categoria": "Perforación y Cimentación", "nombre": "Equipo de Pantalla (Muro Milán)", "nombre_comun": "Pantalla milán", "marcas": "Bauer, Liebherr, Casagrande", "modelos_tipicos": "Bauer BC 40, Liebherr HS 855", "precio_renta": "$25,000 - $50,000 MXN/día", "precio_dia": 25000, "precio_semana": 150000, "precio_mes": 500000, "sinonimos": ["pantalla milán", "muro milán"], "especificaciones": {"profundidad": "30 - 60 m", "espesor": "0.6 - 1.2 m"}, "recomendado": ["Sótanos profundos", "Contenciones"], "no_recomendado": ["Obras pequeñas"], "casos_uso": ["Construcción de sótanos"], "costo_operador_dia": 4000, "costo_transporte": 15000},
    {"categoria": "Perforación y Cimentación", "nombre": "Equipo de Sondeo Exploratorio", "nombre_comun": "Sondeo", "marcas": "Atlas Copco, Diedrich, CME", "modelos_tipicos": "Diedrich D120, CME 75", "precio_renta": "$4,000 - $8,000 MXN/día", "precio_dia": 4000, "precio_semana": 25000, "precio_mes": 85000, "sinonimos": ["sondeo", "exploración de suelos"], "especificaciones": {"profundidad": "30 - 60 m"}, "recomendado": ["Estudios de suelo"], "no_recomendado": ["Perforación productiva"], "casos_uso": ["Muestreo de suelo", "Estudios geotécnicos"], "costo_operador_dia": 2000, "costo_transporte": 3000},

    # --- Manejo de Concreto (4 extra) ---
    {"categoria": "Manejo de Concreto", "nombre": "Pluma de Concreto para Mixer", "nombre_comun": "Pluma mixer", "marcas": "Putzmeister, Schwing, Alliance", "modelos_tipicos": "Putzmeister M20, Schwing S 24 X", "precio_renta": "$4,000 - $8,000 MXN/día", "precio_dia": 4000, "precio_semana": 25000, "precio_mes": 85000, "sinonimos": ["pluma mixer", "pluma concreto"], "especificaciones": {"alcance": "20 - 30 m"}, "recomendado": ["Colados en obra"], "no_recomendado": ["Colados masivos"], "casos_uso": ["Colado de losas", "Colado de columnas"], "costo_operador_dia": 1500, "costo_transporte": 3000},
    {"categoria": "Manejo de Concreto", "nombre": "Vibrador de Concreto", "nombre_comun": "Vibrador", "marcas": "Wacker Neuson, Multiquip, Husqvarna", "modelos_tipicos": "Wacker IREN 60, Multiquip MQ 55", "precio_renta": "$200 - $500 MXN/día", "precio_dia": 200, "precio_semana": 1300, "precio_mes": 4200, "sinonimos": ["vibrador concreto", "vibrador de inmersión"], "especificaciones": {"diametro": "35 - 60 mm", "potencia": "2 HP"}, "recomendado": ["Colado de concreto"], "no_recomendado": ["Concreto sin refuerzo"], "casos_uso": ["Vibrado de losas", "Vibrado de columnas"], "costo_operador_dia": 0, "costo_transporte": 200},
    {"categoria": "Manejo de Concreto", "nombre": "Allanadora de Concreto (Helicóptero)", "nombre_comun": "Allanadora", "marcas": "Wacker Neuson, Multiquip, MBW", "modelos_tipicos": "Wacker CT 48, Multiquip 48J", "precio_renta": "$500 - $1,200 MXN/día", "precio_dia": 500, "precio_semana": 3200, "precio_mes": 10000, "sinonimos": ["allanadora", "helicóptero concreto"], "especificaciones": {"diametro": "1,200 mm", "motor": "Gasolina 6 HP"}, "recomendado": ["Acabado de pisos de concreto"], "no_recomendado": ["Superficies pequeñas"], "casos_uso": ["Pulido de pisos de concreto"], "costo_operador_dia": 0, "costo_transporte": 400},
    {"categoria": "Manejo de Concreto", "nombre": "Lanzadora de Concreto (Shotcrete)", "nombre_comun": "Shotcrete", "marcas": "Putzmeister, Sika, Aliva", "modelos_tipicos": "Putzmeister SPM 500, Aliva AL-500", "precio_renta": "$3,000 - $6,000 MXN/día", "precio_dia": 3000, "precio_semana": 19000, "precio_mes": 65000, "sinonimos": ["shotcrete", "lanzadora concreto", "concreto lanzado"], "especificaciones": {"capacidad": "5 - 20 m³/hr"}, "recomendado": ["Túneles", "Estabilización de taludes"], "no_recomendado": ["Losas"], "casos_uso": ["Revestimiento de túneles", "Estabilización de taludes"], "costo_operador_dia": 1500, "costo_transporte": 3000},

    # --- Generación de Energía y Servicios (5 extra) ---
    {"categoria": "Generación de Energía y Servicios", "nombre": "Generador Eléctrico Pequeño (20 kVA)", "nombre_comun": "Generador 20 kVA", "marcas": "Cummins, Kohler, Generac", "modelos_tipicos": "Cummins C20D5, Kohler 20RZ", "precio_renta": "$1,500 - $3,000 MXN/día", "precio_dia": 1500, "precio_semana": 9500, "precio_mes": 32000, "sinonimos": ["generador 20kva", "planta luz 20"], "especificaciones": {"potencia": "20 kVA", "combustible": "Diésel"}, "recomendado": ["Obras pequeñas", "Oficinas"], "no_recomendado": ["Industria pesada"], "casos_uso": ["Respaldo de oficinas", "Obras en construcción"], "costo_operador_dia": 0, "costo_transporte": 1500},
    {"categoria": "Generación de Energía y Servicios", "nombre": "Generador Inverter Silencioso", "nombre_comun": "Generador silencioso", "marcas": "Honda, Yamaha, Generac", "modelos_tipicos": "Honda EU70is, Generac IQ2000", "precio_renta": "$600 - $1,500 MXN/día", "precio_dia": 600, "precio_semana": 3800, "precio_mes": 12000, "sinonimos": ["generador inverter", "generador silencioso"], "especificaciones": {"potencia": "2 - 7 kVA", "ruido": "52 - 60 dB"}, "recomendado": ["Eventos", "Equipos sensibles"], "no_recomendado": ["Cargas pesadas"], "casos_uso": ["Eventos", "Computadoras", "Audio"], "costo_operador_dia": 0, "costo_transporte": 500},
    {"categoria": "Generación de Energía y Servicios", "nombre": "Calentador de Agua Industrial", "nombre_comun": "Calentador industrial", "marcas": "Rinnai, Rheem, Bosch", "modelos_tipicos": "Rinnai RU100i, Rheem RTG-84D", "precio_renta": "$800 - $2,000 MXN/día", "precio_dia": 800, "precio_semana": 5000, "precio_mes": 16000, "sinonimos": ["calentador industrial", "boiler portátil"], "especificaciones": {"capacidad": "50 - 200 L/min"}, "recomendado": ["Obras", "Campamentos"], "no_recomendado": ["Uso doméstico permanente"], "casos_uso": ["Agua caliente para obras"], "costo_operador_dia": 0, "costo_transporte": 600},
    {"categoria": "Generación de Energía y Servicios", "nombre": "Transformador Eléctrico Portátil", "nombre_comun": "Transformador", "marcas": "ABB, Siemens, Eaton", "modelos_tipicos": "ABB 500 kVA, Siemens GEAFOL", "precio_renta": "$3,000 - $8,000 MXN/mes", "precio_dia": 3000, "precio_semana": 10000, "precio_mes": 35000, "sinonimos": ["transformador portátil"], "especificaciones": {"potencia": "100 - 1,000 kVA"}, "recomendado": ["Obras temporales"], "no_recomendado": ["Instalaciones permanentes"], "casos_uso": ["Suministro temporal de energía"], "costo_operador_dia": 0, "costo_transporte": 2000},
    {"categoria": "Generación de Energía y Servicios", "nombre": "Tablero Eléctrico de Distribución", "nombre_comun": "Tablero distribución", "marcas": "Square D, Siemens, Eaton", "modelos_tipicos": "Square D I-Line, Siemens P1", "precio_renta": "$500 - $2,000 MXN/mes", "precio_dia": 500, "precio_semana": 2000, "precio_mes": 6000, "sinonimos": ["tablero eléctrico"], "especificaciones": {"capacidad": "100 - 600 A"}, "recomendado": ["Distribución temporal"], "no_recomendado": ["Instalaciones fijas"], "casos_uso": ["Distribución en obras"], "costo_operador_dia": 0, "costo_transporte": 500},

    # --- Maquinaria Agrícola (6 extra) ---
    {"categoria": "Maquinaria Agrícola", "nombre": "Tractor Agrícola Mediano (120 HP)", "nombre_comun": "Tractor mediano", "marcas": "John Deere, New Holland, Massey Ferguson", "modelos_tipicos": "John Deere 6125M, New Holland T6.175", "precio_renta": "$2,500 - $4,500 MXN/día", "precio_dia": 2500, "precio_semana": 16000, "precio_mes": 52000, "sinonimos": ["tractor mediano", "tractor 120 hp"], "especificaciones": {"potencia": "120 HP"}, "recomendado": ["Labranza media"], "no_recomendado": ["Grandes extensiones"], "casos_uso": ["Arado de parcelas medianas"], "costo_operador_dia": 1500, "costo_transporte": 3000},
    {"categoria": "Maquinaria Agrícola", "nombre": "Tractor Agrícola Pequeño (75 HP)", "nombre_comun": "Tractor pequeño", "marcas": "Kubota, John Deere, Massey Ferguson", "modelos_tipicos": "Kubota M7060, John Deere 5075E", "precio_renta": "$1,500 - $3,000 MXN/día", "precio_dia": 1500, "precio_semana": 9500, "precio_mes": 32000, "sinonimos": ["tractor pequeño", "tractor 75 hp"], "especificaciones": {"potencia": "75 HP"}, "recomendado": ["Huertos", "Parcelas pequeñas"], "no_recomendado": ["Labranza pesada"], "casos_uso": ["Jardinería", "Huertos", "Parcelas pequeñas"], "costo_operador_dia": 1000, "costo_transporte": 2000},
    {"categoria": "Maquinaria Agrícola", "nombre": "Rastrillo de Discos", "nombre_comun": "Rastrillo", "marcas": "John Deere, Bush Hog, Land Pride", "modelos_tipicos": "John Deere 630, Bush Hog 2615", "precio_renta": "$800 - $1,500 MXN/día", "precio_dia": 800, "precio_semana": 5000, "precio_mes": 16000, "sinonimos": ["rastrillo discos", "rastra"], "especificaciones": {"ancho": "2 - 4 m"}, "recomendado": ["Preparación de terreno"], "no_recomendado": ["Suelos rocosos"], "casos_uso": ["Preparación de semillero"], "costo_operador_dia": 0, "costo_transporte": 600},
    {"categoria": "Maquinaria Agrícola", "nombre": "Arado de Vertedera", "nombre_comun": "Arado", "marcas": "John Deere, Lemken, Kverneland", "modelos_tipicos": "John Deere 2715, Lemken Juwel 8", "precio_renta": "$1,000 - $2,000 MXN/día", "precio_dia": 1000, "precio_semana": 6300, "precio_mes": 21000, "sinonimos": ["arado", "arado vertedera"], "especificaciones": {"numero_surcos": "3 - 6"}, "recomendado": ["Arado profundo"], "no_recomendado": ["Siembra directa"], "casos_uso": ["Arado de tierra"], "costo_operador_dia": 0, "costo_transporte": 800},
    {"categoria": "Maquinaria Agrícola", "nombre": "Cosechadora de Forraje", "nombre_comun": "Cosechadora forraje", "marcas": "John Deere, New Holland, Claas", "modelos_tipicos": "John Deere 7450, New Holland FX58", "precio_renta": "$4,000 - $8,000 MXN/día", "precio_dia": 4000, "precio_semana": 25000, "precio_mes": 85000, "sinonimos": ["cosechadora forraje", "ensiladora"], "especificaciones": {"capacidad": "10 - 20 ton/hr"}, "recomendado": ["Ensilado", "Forraje"], "no_recomendado": ["Granos"], "casos_uso": ["Cosecha de maíz forrajero"], "costo_operador_dia": 2000, "costo_transporte": 5000},
    {"categoria": "Maquinaria Agrícola", "nombre": "Fumigadora de Mochila Motorizada", "nombre_comun": "Fumigadora motorizada", "marcas": "Stihl, Solo, Husqvarna", "modelos_tipicos": "Stihl SR 450, Solo 475", "precio_renta": "$200 - $500 MXN/día", "precio_dia": 200, "precio_semana": 1300, "precio_mes": 4200, "sinonimos": ["fumigadora motorizada", "aspersora motorizada"], "especificaciones": {"capacidad_tanque": "14 L", "motor": "2 HP"}, "recomendado": ["Fumigación localizada"], "no_recomendado": ["Grandes extensiones"], "casos_uso": ["Fumigación de hortalizas", "Jardinería"], "costo_operador_dia": 0, "costo_transporte": 200},

    # --- Maquinaria para Demolición (5 extra) ---
    {"categoria": "Maquinaria para Demolición", "nombre": "Martillo Rompedor Eléctrico", "nombre_comun": "Rompedor eléctrico", "marcas": "Hilti, Bosch, Makita", "modelos_tipicos": "Hilti TE 3000, Bosch GSH 27 VC", "precio_renta": "$400 - $1,000 MXN/día", "precio_dia": 400, "precio_semana": 2500, "precio_mes": 8000, "sinonimos": ["rompedor eléctrico", "martillo rompedor eléctrico"], "especificaciones": {"energia": "20 - 40 Joules", "peso": "15 - 25 kg"}, "recomendado": ["Demolición ligera"], "no_recomendado": ["Grandes volúmenes"], "casos_uso": ["Demolición de muros", "Banquetas"], "costo_operador_dia": 0, "costo_transporte": 200},
    {"categoria": "Maquinaria para Demolición", "nombre": "Compactador de Roca (Jumping Jack)", "nombre_comun": "Compactador roca", "marcas": "Wacker Neuson, Mikasa, Multiquip", "modelos_tipicos": "Wacker BS 60, Mikasa MTR-80", "precio_renta": "$300 - $700 MXN/día", "precio_dia": 300, "precio_semana": 1900, "precio_mes": 6300, "sinonimos": ["compactador roca", "jumping jack"], "especificaciones": {"peso": "60 - 80 kg", "fuerza": "15 - 20 kN"}, "recomendado": ["Compactación en zanjas"], "no_recomendado": ["Grandes áreas"], "casos_uso": ["Compactación en zanjas angostas"], "costo_operador_dia": 0, "costo_transporte": 300},
    {"categoria": "Maquinaria para Demolición", "nombre": "Sierra de Muro (Wall Saw)", "nombre_comun": "Sierra de muro", "marcas": "Husqvarna, Stihl, Hilti", "modelos_tipicos": "Husqvarna WS 440, Hilti DCH 300", "precio_renta": "$800 - $2,000 MXN/día", "precio_dia": 800, "precio_semana": 5000, "precio_mes": 16000, "sinonimos": ["sierra muro", "wall saw", "cortadora de muro"], "especificaciones": {"profundidad": "300 - 500 mm"}, "recomendado": ["Corte de muros", "Apertura de vanos"], "no_recomendado": ["Corte de pisos"], "casos_uso": ["Apertura de puertas", "Ventanas en muros"], "costo_operador_dia": 0, "costo_transporte": 400},
    {"categoria": "Maquinaria para Demolición", "nombre": "Cortadora de Concreto de Mano", "nombre_comun": "Cortadora concreto", "marcas": "Stihl, Husqvarna, Makita", "modelos_tipicos": "Stihl TS 420, Husqvarna K770", "precio_renta": "$300 - $700 MXN/día", "precio_dia": 300, "precio_semana": 1900, "precio_mes": 6300, "sinonimos": ["cortadora concreto mano", "cortadora manual concreto"], "especificaciones": {"diametro": "300 mm", "motor": "Gasolina 4 HP"}, "recomendado": ["Cortes pequeños", "Bacheo"], "no_recomendado": ["Grandes cortes"], "casos_uso": ["Corte de banqueta", "Bacheo"], "costo_operador_dia": 0, "costo_transporte": 200},
    {"categoria": "Maquinaria para Demolición", "nombre": "Pinza de Demolición (Grapple)", "nombre_comun": "Pinza demolición", "marcas": "La Bounty, Genesis, Caterpillar", "modelos_tipicos": "La Bounty M-250, Genesis G-P 450", "precio_renta": "$3,500 - $7,000 MXN/día", "precio_dia": 3500, "precio_semana": 22000, "precio_mes": 73000, "sinonimos": ["pinza demolición", "grapple demolición"], "especificaciones": {"apertura": "1 - 2 m"}, "recomendado": ["Manejo de escombro", "Clasificación"], "no_recomendado": ["Demolición primaria"], "casos_uso": ["Clasificación de escombros", "Carga de material"], "costo_operador_dia": 2000, "costo_transporte": 3000},

    # --- Equipos para Agua y Saneamiento (6 extra) ---
    {"categoria": "Equipos para Agua y Saneamiento", "nombre": "Bomba Sumergible Eléctrica", "nombre_comun": "Bomba sumergible", "marcas": "Tsurumi, Flygt, Grundfos", "modelos_tipicos": "Tsurumi 80UZ, Flygt 3085", "precio_renta": "$800 - $2,000 MXN/día", "precio_dia": 800, "precio_semana": 5000, "precio_mes": 16000, "sinonimos": ["bomba sumergible", "bomba eléctrica sumergible"], "especificaciones": {"capacidad": "50 - 200 m³/hr"}, "recomendado": ["Achique de obras"], "no_recomendado": ["Aguas negras"], "casos_uso": ["Achique en construcción"], "costo_operador_dia": 0, "costo_transporte": 600},
    {"categoria": "Equipos para Agua y Saneamiento", "nombre": "Bomba de Lodos", "nombre_comun": "Bomba lodos", "marcas": "Gorman-Rupp, Godwin, Grindex", "modelos_tipicos": "Gorman-Rupp 4100, Grindex Master", "precio_renta": "$2,000 - $4,000 MXN/día", "precio_dia": 2000, "precio_semana": 12500, "precio_mes": 42000, "sinonimos": ["bomba lodos", "bomba de lodos"], "especificaciones": {"capacidad": "30 - 150 m³/hr"}, "recomendado": ["Lodos industriales"], "no_recomendado": ["Agua limpia"], "casos_uso": ["Manejo de lodos en minas"], "costo_operador_dia": 0, "costo_transporte": 1000},
    {"categoria": "Equipos para Agua y Saneamiento", "nombre": "Bomba de Diafragma", "nombre_comun": "Bomba diafragma", "marcas": "Wilden, SandPiper, Graco", "modelos_tipicos": "Wilden P1, SandPiper SB1", "precio_renta": "$500 - $1,500 MXN/día", "precio_dia": 500, "precio_semana": 3200, "precio_mes": 10000, "sinonimos": ["bomba diafragma"], "especificaciones": {"capacidad": "10 - 50 m³/hr"}, "recomendado": ["Químicos", "Lodos viscosos"], "no_recomendado": ["Grandes volúmenes"], "casos_uso": ["Transferencia de químicos"], "costo_operador_dia": 0, "costo_transporte": 400},
    {"categoria": "Equipos para Agua y Saneamiento", "nombre": "Equipo de Hidrodesazolve", "nombre_comun": "Hidrodesazolve", "marcas": "Vac-Con, Vactor, Guzzler", "modelos_tipicos": "Vac-Con VX8100, Vactor 2100 Plus", "precio_renta": "$7,000 - $14,000 MXN/día", "precio_dia": 7000, "precio_semana": 44000, "precio_mes": 145000, "sinonimos": ["hidrodesazolve", "limpieza drenajes alta presión"], "especificaciones": {"presion": "300 bar"}, "recomendado": ["Desazolve pesado"], "no_recomendado": ["Limpieza ligera"], "casos_uso": ["Limpieza de drenajes obstruidos"], "costo_operador_dia": 2500, "costo_transporte": 5000},
    {"categoria": "Equipos para Agua y Saneamiento", "nombre": "Balsa de Flotación / Skimmer", "nombre_comun": "Skimmer", "marcas": "Elastec, Desmi, Lamor", "modelos_tipicos": "Elastec TDS-200, Desmi IMTT", "precio_renta": "$3,000 - $5,000 MXN/día", "precio_dia": 3000, "precio_semana": 19000, "precio_mes": 65000, "sinonimos": ["skimmer", "balsa desnatadora"], "especificaciones": {"capacidad": "10 - 50 m³/hr"}, "recomendado": ["Derrames de hidrocarburos"], "no_recomendado": ["Aguas limpias"], "casos_uso": ["Limpieza de derrames", "Tratamiento de aguas"], "costo_operador_dia": 0, "costo_transporte": 3000},
    {"categoria": "Equipos para Agua y Saneamiento", "nombre": "Planta de Tratamiento Portátil", "nombre_comun": "PTAR portátil", "marcas": "Ecofluent, Fluence, Suez", "modelos_tipicos": "Ecofluent EF-10, Fluence NIROBOX", "precio_renta": "$8,000 - $20,000 MXN/mes", "precio_dia": 8000, "precio_semana": 35000, "precio_mes": 120000, "sinonimos": ["ptar portátil", "planta tratamiento portátil"], "especificaciones": {"capacidad": "10 - 100 m³/día"}, "recomendado": ["Campamentos", "Obras temporales"], "no_recomendado": ["Ciudades"], "casos_uso": ["Tratamiento de aguas en campamentos"], "costo_operador_dia": 2000, "costo_transporte": 8000},

    # --- Equipos Compactos a Gasolina (6 extra) ---
    {"categoria": "Equipos Compactos a Gasolina", "nombre": "Sopladora de Mochila", "nombre_comun": "Sopladora", "marcas": "Stihl, Husqvarna, Echo", "modelos_tipicos": "Stihl BR 600, Husqvarna 570BTS", "precio_renta": "$200 - $500 MXN/día", "precio_dia": 200, "precio_semana": 1300, "precio_mes": 4200, "sinonimos": ["sopladora", "sopladora mochila"], "especificaciones": {"caudal": "800 - 1,200 m³/hr", "motor": "Gasolina 4 HP"}, "recomendado": ["Limpieza de obras"], "no_recomendado": ["Interiores"], "casos_uso": ["Limpieza de calles", "Jardinería"], "costo_operador_dia": 0, "costo_transporte": 200},
    {"categoria": "Equipos Compactos a Gasolina", "nombre": "Motodesbrosadora", "nombre_comun": "Desbrozadora", "marcas": "Stihl, Husqvarna, Shindaiwa", "modelos_tipicos": "Stihl FS 130, Husqvarna 545FR", "precio_renta": "$200 - $400 MXN/día", "precio_dia": 200, "precio_semana": 1300, "precio_mes": 4200, "sinonimos": ["desbrozadora", "motodesbrozadora"], "especificaciones": {"motor": "Gasolina 2 HP"}, "recomendado": ["Limpieza de maleza"], "no_recomendado": ["Árboles grandes"], "casos_uso": ["Limpieza de terrenos"], "costo_operador_dia": 0, "costo_transporte": 200},
    {"categoria": "Equipos Compactos a Gasolina", "nombre": "Motosierra", "nombre_comun": "Motosierra", "marcas": "Stihl, Husqvarna, Echo", "modelos_tipicos": "Stihl MS 661, Husqvarna 395 XP", "precio_renta": "$300 - $700 MXN/día", "precio_dia": 300, "precio_semana": 1900, "precio_mes": 6300, "sinonimos": ["motosierra"], "especificaciones": {"espada": "16 - 36 pulgadas", "motor": "Gasolina 5 HP"}, "recomendado": ["Tala de árboles", "Poda"], "no_recomendado": ["Corte de concreto"], "casos_uso": ["Tala", "Poda de jardinería"], "costo_operador_dia": 0, "costo_transporte": 200},
    {"categoria": "Equipos Compactos a Gasolina", "nombre": "Motobomba Portátil 2 pulgadas", "nombre_comun": "Motobomba 2\"", "marcas": "Honda, Yamaha, Briggs & Stratton", "modelos_tipicos": "Honda WB20XT, Yamaha YP30X", "precio_renta": "$300 - $600 MXN/día", "precio_dia": 300, "precio_semana": 1900, "precio_mes": 6300, "sinonimos": ["motobomba 2", "bomba portátil 2\""], "especificaciones": {"capacidad": "30 - 60 m³/hr", "motor": "Gasolina 5.5 HP"}, "recomendado": ["Achique ligero"], "no_recomendado": ["Grandes volúmenes"], "casos_uso": ["Achique de zanjas"], "costo_operador_dia": 0, "costo_transporte": 200},
    {"categoria": "Equipos Compactos a Gasolina", "nombre": "Revolvedora de Cemento (Bolsa)", "nombre_comun": "Revolvedora", "marcas": "Mikasa, Multiquip, Belle", "modelos_tipicos": "Mikasa MVC-88, Multiquip MC-60", "precio_renta": "$300 - $600 MXN/día", "precio_dia": 300, "precio_semana": 1900, "precio_mes": 6300, "sinonimos": ["revolvedora", "mezcladora cemento"], "especificaciones": {"capacidad": "200 - 400 L"}, "recomendado": ["Colados pequeños"], "no_recomendado": ["Colados grandes"], "casos_uso": ["Colado de banqueta", "Reparaciones"], "costo_operador_dia": 0, "costo_transporte": 300},
    {"categoria": "Equipos Compactos a Gasolina", "nombre": "Generador Portátil Inverter 2 kVA", "nombre_comun": "Inverter 2kVA", "marcas": "Honda, Yamaha, Generac", "modelos_tipicos": "Honda EU22i, Yamaha EF2600", "precio_renta": "$400 - $800 MXN/día", "precio_dia": 400, "precio_semana": 2500, "precio_mes": 8000, "sinonimos": ["generador inverter 2kva", "planta portátil"], "especificaciones": {"potencia": "2 kVA", "ruido": "52 dB"}, "recomendado": ["Camping", "Equipos sensibles"], "no_recomendado": ["Obras"], "casos_uso": ["Electrónica sensible", "Equipos médicos"], "costo_operador_dia": 0, "costo_transporte": 200},

    # --- Maquinaria para Espacios Reducidos (5 extra) ---
    {"categoria": "Maquinaria para Espacios Reducidos", "nombre": "Mini Cargador de Orugas (Compact Track)", "nombre_comun": "Mini cargador orugas", "marcas": "Bobcat, Caterpillar, ASV", "modelos_tipicos": "Bobcat T590, CAT 279D3", "precio_renta": "$1,500 - $2,500 MXN/día", "precio_dia": 1500, "precio_semana": 9500, "precio_mes": 32000, "sinonimos": ["mini cargador orugas", "compact track loader"], "especificaciones": {"peso": "3,500 kg", "potencia": "70 HP"}, "recomendado": ["Terrenos blandos"], "no_recomendado": ["Pavimentos"], "casos_uso": ["Carga en terrenos difíciles"], "costo_operador_dia": 0, "costo_transporte": 1500},
    {"categoria": "Maquinaria para Espacios Reducidos", "nombre": "Excavadora Zero Tail Swing", "nombre_comun": "Zero tail", "marcas": "Bobcat, Kubota, Yanmar", "modelos_tipicos": "Bobcat E35Z, Kubota U27-4", "precio_renta": "$1,600 - $2,800 MXN/día", "precio_dia": 1600, "precio_semana": 10000, "precio_mes": 33000, "sinonimos": ["zero tail swing", "excavadora sin contrapeso"], "especificaciones": {"peso": "3,500 kg"}, "recomendado": ["Espacios confinados"], "no_recomendado": ["Excavación profunda"], "casos_uso": ["Interiores", "Cerca de muros"], "costo_operador_dia": 1200, "costo_transporte": 1500},
    {"categoria": "Maquinaria para Espacios Reducidos", "nombre": "Perforadora de Núcleo (Core Drill)", "nombre_comun": "Core drill", "marcas": "Husqvarna, Hilti, Diamond Products", "modelos_tipicos": "Husqvarna DM 650, Hilti DD 200", "precio_renta": "$400 - $1,000 MXN/día", "precio_dia": 400, "precio_semana": 2500, "precio_mes": 8000, "sinonimos": ["perforadora núcleo", "core drill", "brocacero"], "especificaciones": {"diametro": "100 - 300 mm"}, "recomendado": ["Muestreo de concreto", "Pases para tubería"], "no_recomendado": ["Perforación profunda"], "casos_uso": ["Muestreo de concreto"], "costo_operador_dia": 0, "costo_transporte": 300},
    {"categoria": "Maquinaria para Espacios Reducidos", "nombre": "Mezcladora de Concreto Compacta", "nombre_comun": "Mezcladora compacta", "marcas": "Mikasa, Multiquip, Belle", "modelos_tipicos": "Belle Mini 120, Mikasa MC-44", "precio_renta": "$300 - $600 MXN/día", "precio_dia": 300, "precio_semana": 1900, "precio_mes": 6300, "sinonimos": ["mezcladora compacta", "concretera pequeña"], "especificaciones": {"capacidad": "120 - 200 L"}, "recomendado": ["Obras pequeñas"], "no_recomendado": ["Producción masiva"], "casos_uso": ["Colados domiciliarios"], "costo_operador_dia": 0, "costo_transporte": 200},
    {"categoria": "Maquinaria para Espacios Reducidos", "nombre": "Compactador de Placa Reversible", "nombre_comun": "Placa reversible", "marcas": "Wacker Neuson, Bomag, Weber", "modelos_tipicos": "Wacker DPU 130, Bomag BPR 80/80D", "precio_renta": "$600 - $1,200 MXN/día", "precio_dia": 600, "precio_semana": 3800, "precio_mes": 12000, "sinonimos": ["placa reversible", "compactadora reversible"], "especificaciones": {"peso": "300 - 600 kg"}, "recomendado": ["Zanjas", "Rellenos"], "no_recomendado": ["Superficies grandes"], "casos_uso": ["Compactación de zanjas"], "costo_operador_dia": 0, "costo_transporte": 400},

    # --- Manejo de Materiales (6 extra) ---
    {"categoria": "Manejo de Materiales", "nombre": "Montacargas Eléctrico (3 ton)", "nombre_comun": "Montacargas eléctrico", "marcas": "Toyota, Raymond, Yale", "modelos_tipicos": "Toyota 3FBC18, Raymond 3500", "precio_renta": "$1,800 - $3,500 MXN/día", "precio_dia": 1800, "precio_semana": 11000, "precio_mes": 38000, "sinonimos": ["montacargas eléctrico"], "especificaciones": {"capacidad": "3,000 kg", "altura": "4.5 m"}, "recomendado": ["Interiores", "Almacenes"], "no_recomendado": ["Exteriores"], "casos_uso": ["Almacenes techados"], "costo_operador_dia": 0, "costo_transporte": 1200},
    {"categoria": "Manejo de Materiales", "nombre": "Montacargas Diesel (5 ton)", "nombre_comun": "Montacargas diesel", "marcas": "Toyota, Hyster, Yale", "modelos_tipicos": "Toyota 5FD30, Hyster H50FT", "precio_renta": "$2,000 - $4,000 MXN/día", "precio_dia": 2000, "precio_semana": 12500, "precio_mes": 42000, "sinonimos": ["montacargas diesel 5 ton"], "especificaciones": {"capacidad": "5,000 kg", "altura": "5 m"}, "recomendado": ["Exteriores", "Patios"], "no_recomendado": ["Interiores techados"], "casos_uso": ["Carga de camiones", "Patios de materiales"], "costo_operador_dia": 0, "costo_transporte": 1500},
    {"categoria": "Manejo de Materiales", "nombre": "Transpaleta Eléctrica", "nombre_comun": "Transpaleta", "marcas": "Toyota, Raymond, Crown", "modelos_tipicos": "Toyota 8TB50, Crown WP 3000", "precio_renta": "$400 - $1,000 MXN/día", "precio_dia": 400, "precio_semana": 2500, "precio_mes": 8000, "sinonimos": ["transpaleta", "pato", "patín hidráulico eléctrico"], "especificaciones": {"capacidad": "2,000 - 3,000 kg"}, "recomendado": ["Bodegas", "Carga de camiones"], "no_recomendado": ["Rampas"], "casos_uso": ["Manejo de pallets en bodega"], "costo_operador_dia": 0, "costo_transporte": 400},
    {"categoria": "Manejo de Materiales", "nombre": "Apilador Eléctrico (Stacker)", "nombre_comun": "Apilador", "marcas": "Toyota, Raymond, Crown", "modelos_tipicos": "Toyota 4TB30, Crown SP 3200", "precio_renta": "$600 - $1,500 MXN/día", "precio_dia": 600, "precio_semana": 3800, "precio_mes": 12000, "sinonimos": ["apilador", "stacker", "montacargas pequeño"], "especificaciones": {"capacidad": "1,500 kg", "altura": "3.5 m"}, "recomendado": ["Bodegas pequeñas"], "no_recomendado": ["Cargas pesadas"], "casos_uso": ["Apilado en bodegas"], "costo_operador_dia": 0, "costo_transporte": 500},
    {"categoria": "Manejo de Materiales", "nombre": "Grúa de Pluma (Jib Crane)", "nombre_comun": "Pluma", "marcas": "Kone, Demag, Street", "modelos_tipicos": "Demag PK 5, Street JIB-500", "precio_renta": "$1,000 - $3,000 MXN/mes", "precio_dia": 1000, "precio_semana": 4000, "precio_mes": 12000, "sinonimos": ["pluma", "grúa de pluma"], "especificaciones": {"capacidad": "500 - 3,000 kg"}, "recomendado": ["Talleres", "Carga localizada"], "no_recomendado": ["Grandes distancias"], "casos_uso": ["Carga en talleres"], "costo_operador_dia": 0, "costo_transporte": 1000},
    {"categoria": "Manejo de Materiales", "nombre": "Cinta Transportadora Portátil", "nombre_comun": "Banda transportadora", "marcas": "Link-Belt, Superior, Masaba", "modelos_tipicos": "Link-Belt 30x60, Superior 36x80", "precio_renta": "$2,000 - $5,000 MXN/día", "precio_dia": 2000, "precio_semana": 12500, "precio_mes": 42000, "sinonimos": ["cinta transportadora", "banda transportadora portátil"], "especificaciones": {"ancho": "30 - 42 pulgadas", "largo": "15 - 30 m"}, "recomendado": ["Acopio de material"], "no_recomendado": ["Distancias cortas"], "casos_uso": ["Acopio de áridos", "Carga de camiones"], "costo_operador_dia": 0, "costo_transporte": 2000},

    # --- Iluminación y Seguridad (5 extra) ---
    {"categoria": "Iluminación y Seguridad", "nombre": "Torre de Iluminación LED", "nombre_comun": "Torre LED", "marcas": "Generac, Wacker Neuson, Gillette", "modelos_tipicos": "Generac MLT6 LED, Wacker LTN6L LED", "precio_renta": "$1,500 - $3,000 MXN/día", "precio_dia": 1500, "precio_semana": 9500, "precio_mes": 32000, "sinonimos": ["torre iluminación led", "torre de luz led"], "especificaciones": {"potencia": "6 - 8 kW LED"}, "recomendado": ["Obras nocturnas"], "no_recomendado": ["Interiores"], "casos_uso": ["Iluminación de obras nocturnas"], "costo_operador_dia": 0, "costo_transporte": 1000},
    {"categoria": "Iluminación y Seguridad", "nombre": "Señalización Vial Tipo Mensaje Variable", "nombre_comun": "Señal variable", "marcas": "Ver-Mac, ADDCO, Wanco", "modelos_tipicos": "Ver-Mac VMS-200, ADDCO VMS-16", "precio_renta": "$800 - $2,000 MXN/día", "precio_dia": 800, "precio_semana": 5000, "precio_mes": 16000, "sinonimos": ["señal variable", "vms", "pantalla vial"], "especificaciones": {"tamaño": "1.2 x 2.4 m"}, "recomendado": ["Obras viales", "Desvíos"], "no_recomendado": ["Obras estáticas"], "casos_uso": ["Señalización de desvíos"], "costo_operador_dia": 0, "costo_transporte": 800},
    {"categoria": "Iluminación y Seguridad", "nombre": "Barrera de Seguridad Tipo Jersey", "nombre_comun": "Jersey", "marcas": "Plastibeton, Barrier Systems", "modelos_tipicos": "Plastibeton JB-100", "precio_renta": "$200 - $500 MXN/día", "precio_dia": 200, "precio_semana": 1300, "precio_mes": 4200, "sinonimos": ["barrera jersey", "jersey", "barrera de concreto"], "especificaciones": {"largo": "2 m", "material": "Polietileno/Concreto"}, "recomendado": ["Protección de obras"], "no_recomendado": ["Larga distancia"], "casos_uso": ["Protección de carriles"], "costo_operador_dia": 0, "costo_transporte": 200},
    {"categoria": "Iluminación y Seguridad", "nombre": "Cono de Seguridad con Base", "nombre_comun": "Conos", "marcas": "Vulcan, 3M, Plastibeton", "modelos_tipicos": "Vulcan VC-36, 3M PG-28", "precio_renta": "$20 - $50 MXN/día", "precio_dia": 20, "precio_semana": 130, "precio_mes": 420, "sinonimos": ["cono vial", "cono seguridad"], "especificaciones": {"altura": "28 - 36 pulgadas"}, "recomendado": ["Señalización temporal"], "no_recomendado": ["Velocidad alta"], "casos_uso": ["Señalización de obras"], "costo_operador_dia": 0, "costo_transporte": 100},
    {"categoria": "Iluminación y Seguridad", "nombre": "Lámpara de Destello (Strobe)", "nombre_comun": "Destellantes", "marcas": "Federal Signal, Whelen, Star Headlight", "modelos_tipicos": "Federal Signal LP3, Whelen 6000", "precio_renta": "$50 - $150 MXN/día", "precio_dia": 50, "precio_semana": 320, "precio_mes": 1000, "sinonimos": ["destellantes", "luz estroboscópica"], "especificaciones": {"potencia": "50W LED"}, "recomendado": ["Advertencia nocturna"], "no_recomendado": ["Iluminación general"], "casos_uso": ["Señalización nocturna"], "costo_operador_dia": 0, "costo_transporte": 100},

    # --- Túneles y Minería (5 extra) ---
    {"categoria": "Túneles y Minería", "nombre": "Jumbo de Perforación", "nombre_comun": "Jumbo", "marcas": "Epiroc, Atlas Copco, Sandvik", "modelos_tipicos": "Epiroc Boomer 281, Sandvik DT820", "precio_renta": "$25,000 - $50,000 MXN/día", "precio_dia": 25000, "precio_semana": 150000, "precio_mes": 500000, "sinonimos": ["jumbo perforación", "equipo de perforación túnel"], "especificaciones": {"brazos": "2 - 3", "potencia": "200 HP"}, "recomendado": ["Perforación de túneles"], "no_recomendado": ["Obras superficiales"], "casos_uso": ["Perforación de túneles viales"], "costo_operador_dia": 4000, "costo_transporte": 20000},
    {"categoria": "Túneles y Minería", "nombre": "Roboshot (Lanzadora Shotcrete Robótica)", "nombre_comun": "Roboshot", "marcas": "Epiroc, CIFA, Putzmeister", "modelos_tipicos": "Epiroc Roboshot 820, CIFA Spritz", "precio_renta": "$20,000 - $40,000 MXN/día", "precio_dia": 20000, "precio_semana": 125000, "precio_mes": 420000, "sinonimos": ["roboshot", "shotcrete robótico"], "especificaciones": {"capacidad": "20 m³/hr"}, "recomendado": ["Revestimiento de túneles"], "no_recomendado": ["Obras pequeñas"], "casos_uso": ["Revestimiento de túneles"], "costo_operador_dia": 3500, "costo_transporte": 15000},
    {"categoria": "Túneles y Minería", "nombre": "Ventilador de Túnel", "nombre_comun": "Ventilador túnel", "marcas": "Zitron, Howden, Korfmann", "modelos_tipicos": "Zitron Z200, Howden Buffalo", "precio_renta": "$3,000 - $8,000 MXN/mes", "precio_dia": 3000, "precio_semana": 15000, "precio_mes": 50000, "sinonimos": ["ventilador túnel", "ventilador axial"], "especificaciones": {"caudal": "50,000 - 200,000 m³/hr"}, "recomendado": ["Ventilación en túneles"], "no_recomendado": ["Espacios abiertos"], "casos_uso": ["Ventilación de túneles"], "costo_operador_dia": 0, "costo_transporte": 4000},
    {"categoria": "Túneles y Minería", "nombre": "Scaler (Equipo de Desquinche)", "nombre_comun": "Scaler", "marcas": "Epiroc, Normet, MacLean", "modelos_tipicos": "Epiroc COMMANDER, Normet SP 100", "precio_renta": "$12,000 - $25,000 MXN/día", "precio_dia": 12000, "precio_semana": 75000, "precio_mes": 250000, "sinonimos": ["scaler", "desquinchadora"], "especificaciones": {"altura": "8 - 12 m"}, "recomendado": ["Limpieza de túneles"], "no_recomendado": ["Obras nuevas"], "casos_uso": ["Desquinche de túneles"], "costo_operador_dia": 3000, "costo_transporte": 10000},
    {"categoria": "Túneles y Minería", "nombre": "Dumper Subterráneo (LHD)", "nombre_comun": "LHD", "marcas": "Sandvik, Caterpillar, Epiroc", "modelos_tipicos": "Sandvik LH514, CAT R1600H", "precio_renta": "$15,000 - $30,000 MXN/día", "precio_dia": 15000, "precio_semana": 95000, "precio_mes": 320000, "sinonimos": ["lhd", "dumper minería", "scoop"], "especificaciones": {"capacidad": "6 - 14 ton"}, "recomendado": ["Minería subterránea"], "no_recomendado": ["Obras superficiales"], "casos_uso": ["Carga y acarreo subterráneo"], "costo_operador_dia": 3500, "costo_transporte": 15000},

    # --- Riego y Agricultura (5 extra) ---
    {"categoria": "Riego y Agricultura", "nombre": "Equipo de Riego por Aspersión Portátil", "nombre_comun": "Aspersión", "marcas": "Rain Bird, Nelson, Valmont", "modelos_tipicos": "Rain Bird TL-1, Nelson R2000", "precio_renta": "$500 - $1,500 MXN/día", "precio_dia": 500, "precio_semana": 3200, "precio_mes": 10000, "sinonimos": ["riego aspersión", "aspersión portátil"], "especificaciones": {"cobertura": "10 - 50 m"}, "recomendado": ["Riego de cultivos"], "no_recomendado": ["Grandes extensiones"], "casos_uso": ["Riego de hortalizas"], "costo_operador_dia": 0, "costo_transporte": 400},
    {"categoria": "Riego y Agricultura", "nombre": "Sistema de Riego por Goteo Portátil", "nombre_comun": "Riego goteo", "marcas": "Netafim, John Deere, Toro", "modelos_tipicos": "Netafim DripNet, Toro DL200", "precio_renta": "$400 - $1,200 MXN/día", "precio_dia": 400, "precio_semana": 2500, "precio_mes": 8000, "sinonimos": ["riego goteo", "goteo portátil"], "especificaciones": {"cobertura": "0.5 - 5 ha"}, "recomendado": ["Cultivos de alta densidad"], "no_recomendado": ["Pastizales"], "casos_uso": ["Riego de invernaderos"], "costo_operador_dia": 0, "costo_transporte": 500},
    {"categoria": "Riego y Agricultura", "nombre": "Pivote Central de Riego", "nombre_comun": "Pivote", "marcas": "Valmont, Lindsay, Reinke", "modelos_tipicos": "Valmont 8000, Lindsay Zimmatic", "precio_renta": "$8,000 - $20,000 MXN/mes", "precio_dia": 8000, "precio_semana": 30000, "precio_mes": 100000, "sinonimos": ["pivote central", "pivote riego"], "especificaciones": {"longitud": "200 - 500 m", "cobertura": "30 - 100 ha"}, "recomendado": ["Grandes extensiones"], "no_recomendado": ["Terrenos irregulares"], "casos_uso": ["Riego de maíz", "Riego de soya"], "costo_operador_dia": 0, "costo_transporte": 15000},
    {"categoria": "Riego y Agricultura", "nombre": "Motobomba para Riego 6 pulgadas", "nombre_comun": "Motobomba riego", "marcas": "Honda, Dongfeng, Caterpillar", "modelos_tipicos": "Honda WHB80, Dongfeng 6\"", "precio_renta": "$800 - $2,000 MXN/día", "precio_dia": 800, "precio_semana": 5000, "precio_mes": 16000, "sinonimos": ["motobomba riego", "bomba agrícola"], "especificaciones": {"capacidad": "100 - 400 m³/hr"}, "recomendado": ["Riego por gravedad"], "no_recomendado": ["Presurizado"], "casos_uso": ["Riego de arroz"], "costo_operador_dia": 0, "costo_transporte": 600},
    {"categoria": "Riego y Agricultura", "nombre": "Desgranadora de Maíz", "nombre_comun": "Desgranadora", "marcas": "Molina, Swissmex, Bear Cat", "modelos_tipicos": "Molina SM-200, Bear Cat 1200", "precio_renta": "$300 - $800 MXN/día", "precio_dia": 300, "precio_semana": 1900, "precio_mes": 6300, "sinonimos": ["desgranadora maíz", "desgranadora"], "especificaciones": {"capacidad": "2 - 5 ton/hr"}, "recomendado": ["Postcosecha"], "no_recomendado": ["Producción industrial"], "casos_uso": ["Desgrane de maíz"], "costo_operador_dia": 0, "costo_transporte": 300},
]


def get_connection(args):
    return psycopg2.connect(
        host=args.host, port=args.port, dbname=args.db,
        user=args.user, password=args.password,
    )

def seed_categorias(conn):
    cur = conn.cursor()
    cats_map = {}
    for nombre, desc in CATEGORIAS:
        cur.execute(
            "INSERT INTO categorias (nombre, descripcion) VALUES (%s, %s) ON CONFLICT (nombre) DO UPDATE SET descripcion=EXCLUDED.descripcion RETURNING id",
            (nombre, desc),
        )
        cats_map[nombre] = cur.fetchone()[0]
        print(f"  [OK] {nombre}")
    conn.commit()
    return cats_map

def seed_maquinas_catalogo(conn, cats_map):
    cur = conn.cursor()
    from src.catalogo import Catalogo
    catalogo = Catalogo()
    cats = catalogo.get_categorias()
    total = 0
    for cat_name, cat_data in cats.items():
        cat_id = cats_map.get(cat_name)
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
                """INSERT INTO maquinas
                    (categoria_id, nombre, nombre_comun, marcas, modelos_tipicos,
                     precio_renta, sinonimos, perfil_cliente,
                     especificaciones, recomendado, no_recomendado,
                     casos_uso, preguntas_frecuentes, reglas_negocio)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING""",
                (cat_id, mach_name, machine.get("nombre_comun", ""),
                 machine.get("marcas", ""), machine.get("modelos_tipicos", ""),
                 machine.get("precio_renta", ""), sinonimos,
                 "\n".join(machine.get("perfil_cliente", [])),
                 json.dumps(machine.get("especificaciones", {})),
                 recomendado, no_recomendado, casos_uso,
                 json.dumps(preguntas), reglas_negocio),
            )
            total += 1
            print(f"  [OK] {mach_name}")
    conn.commit()
    return total

def seed_maquinas_extra(conn, cats_map):
    cur = conn.cursor()
    total = 0
    for m in MAQUINAS_EXTRA:
        cat_id = cats_map.get(m["categoria"])
        if not cat_id:
            continue
        precio_dia = m.get("precio_dia")
        precio_semana = m.get("precio_semana")
        precio_mes = m.get("precio_mes")
        cur.execute(
            """INSERT INTO maquinas
                (categoria_id, nombre, nombre_comun, marcas, modelos_tipicos,
                 precio_renta, sinonimos, perfil_cliente,
                 especificaciones, recomendado, no_recomendado, casos_uso,
                 preguntas_frecuentes, reglas_negocio,
                 precio_dia, precio_semana, precio_mes,
                 moneda, costo_operador_dia, costo_transporte)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING""",
            (cat_id, m["nombre"], m.get("nombre_comun", ""),
             m.get("marcas", ""), m.get("modelos_tipicos", ""),
             m.get("precio_renta", ""), m.get("sinonimos", []),
             m.get("perfil_cliente", ""),
             json.dumps(m.get("especificaciones", {})),
             m.get("recomendado", []), m.get("no_recomendado", []),
             m.get("casos_uso", []), json.dumps([]), [],
             precio_dia, precio_semana, precio_mes,
             "MXN", m.get("costo_operador_dia"), m.get("costo_transporte")),
        )
        total += 1
        print(f"  [OK] {m['nombre']}")
    conn.commit()
    return total

def seed_proyectos(conn):
    cur = conn.cursor()
    from src.catalogo import Catalogo
    catalogo = Catalogo()
    proyectos = catalogo.get_proyectos()
    for proj in proyectos:
        cur.execute(
            """INSERT INTO proyectos (nombre, maquinarias, consideraciones)
            VALUES (%s, %s, %s) ON CONFLICT (nombre) DO NOTHING""",
            (proj["nombre"], proj["maquinarias"], proj.get("consideraciones", "")),
        )
        print(f"  [OK] {proj['nombre']}")
    conn.commit()
    return len(proyectos)

def seed_all(args=None):
    parser = argparse.ArgumentParser(description="Seed completo Rentek")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=5432)
    parser.add_argument("--db", default="maquinaria_rag")
    parser.add_argument("--user", default="rag_user")
    parser.add_argument("--password", default="rag_pass_2026")
    args = parser.parse_args(args)

    print("=" * 60)
    print("  SEED COMPLETO - Rentek")
    print("=" * 60)

    conn = get_connection(args)

    print("\n[1/6] Categorías...")
    cats_map = seed_categorias(conn)

    print(f"\n[2/6] Máquinas (catálogo markdown)...")
    total_md = seed_maquinas_catalogo(conn, cats_map)

    print(f"\n[3/6] Máquinas extras (programáticas)...")
    total_extra = seed_maquinas_extra(conn, cats_map)

    print(f"\n[4/6] Proyectos...")
    total_proyectos = seed_proyectos(conn)

    conn.close()

    print()
    print("=" * 60)
    print(f"  ¡COMPLETADO!")
    print(f"  Categorías: {len(cats_map)}")
    print(f"  Máquinas:   {total_md + total_extra} ({total_md} del catálogo + {total_extra} extras)")
    print(f"  Proyectos:  {total_proyectos}")
    print("=" * 60)

if __name__ == "__main__":
    seed_all()
