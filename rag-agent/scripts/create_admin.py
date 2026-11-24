#!/usr/bin/env python3
"""Crea o promueve una cuenta como administrador de Rentek.

Uso:
    python scripts/create_admin.py --email admin@rentek.com --password "ClaveSegura123"

La contraseña se guarda con el mismo hash PBKDF2 que usa la API; nunca en texto plano.
Si el correo ya existe, se actualiza su rol a "admin" y su contraseña.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import psycopg2

from src.auth import hash_password
from src.config import config


def main() -> int:
    parser = argparse.ArgumentParser(description="Crea o promueve un administrador")
    parser.add_argument("--email", required=True, help="Correo del administrador")
    parser.add_argument("--username", default=None, help="Usuario (por defecto, la parte antes de @)")
    parser.add_argument("--password", required=True, help="Contraseña (mínimo 8 caracteres)")
    parser.add_argument("--name", default="Administrador", help="Nombre visible")
    parser.add_argument("--host", default=config.DB_HOST)
    parser.add_argument("--port", type=int, default=config.DB_PORT)
    parser.add_argument("--db", default=config.DB_NAME)
    parser.add_argument("--user", default=config.DB_USER)
    parser.add_argument("--db-password", default=config.DB_PASSWORD)
    args = parser.parse_args()

    if len(args.password) < 8:
        parser.error("La contraseña debe tener al menos 8 caracteres")

    conn = psycopg2.connect(
        host=args.host,
        port=args.port,
        dbname=args.db,
        user=args.user,
        password=args.db_password,
    )
    username = args.username or args.email.split("@")[0]
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM users WHERE email = %s OR username = %s",
            (args.email, username),
        )
        row = cur.fetchone()
        if row:
            cur.execute(
                """UPDATE users
                   SET email = %s, password_hash = %s, role = 'admin', display_name = %s,
                       blocked = FALSE, blocked_at = NULL, closed_chats = 0
                   WHERE id = %s""",
                (args.email, hash_password(args.password), args.name, row[0]),
            )
            message = f"Usuario existente promovido a administrador (id={row[0]})"
        else:
            cur.execute(
                """INSERT INTO users (username, email, password_hash, display_name, role)
                   VALUES (%s, %s, %s, %s, 'admin') RETURNING id""",
                (username, args.email, hash_password(args.password), args.name),
            )
            message = f"Administrador creado (id={cur.fetchone()[0]})"
        conn.commit()
        cur.close()
        print(message)
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
