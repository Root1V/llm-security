import os
import secrets
import string
import argparse
from typing import Dict
import logging

logger = logging.getLogger("security.credentials")


# -----------------------------
# Roles
# -----------------------------

ROLE_MAP = {
    "USRS": "user",
    "MNTR": "monitoring",
    "ADMN": "admin",
    "AGNR": "agent_reasoning",
    "AGNF": "agent_fast",
    "AGIA": "agi",
}


# -----------------------------
# Utils (solo para bootstrap)
# -----------------------------

def generate_random_string(length: int) -> str:
    """Genera una cadena aleatoria de un determinado tamaño."""

    return "".join(
        secrets.choice(string.ascii_letters + string.digits)
        for _ in range(length)
    )


def generate_user_passwords(num_users_per_prefix: int) -> Dict[str, str]:
    """
    SOLO para bootstrap inicial.
    No se usa en runtime.
    Genera una cantidad num_users_per_prefix de usuarios y contraseñas aleatorias.
    """
    users = {}

    for prefix in ROLE_MAP:
        for _ in range(num_users_per_prefix):
            username = f"{prefix}{generate_random_string(6).upper()}"
            password = generate_random_string(21)
            users[username] = password

    return users


def save_to_env_file(user_passwords: Dict[str, str], filepath: str ='.env') -> None:
    """Guarda los usuarios y contraseñas en el formato de variables de entorno en un archivo .env."""

    with open(filepath, "w") as f:
        for username, password in sorted(user_passwords.items()):
            f.write(f"{username}={password}\n")


# -----------------------------
# Runtime Loader (CRÍTICO)
# -----------------------------

def load_users_from_env(filepath: str ='.env') -> Dict[str, dict]:
    """
    Carga usuarios UNA SOLA VEZ al arranque.
    """

    logger.info(f"Loading users from env file: {filepath}")
    if not os.path.exists(filepath):
        raise RuntimeError(f"Env file not found: {filepath}")

    users: Dict[str, dict] = {}

    with open(filepath, "r") as file:
        for line in file:
            line = line.strip()

            if not line or "=" not in line:
                continue

            username, password = line.split("=", 1)
            prefix = username[:4]

            role = ROLE_MAP.get(prefix)
            if not role:
                raise ValueError(f"Unknown role prefix: {prefix}")

            users[username] = {
                "password": password,
                "role": role,
            }

    return users

# -----------------------------
# Utils (solo para bootstrap)
# -----------------------------

def main():
    logger.info("Starting credential management utility")

    parser = argparse.ArgumentParser(
        description="Credential management utility"
    )

    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate users and passwords"
    )

    parser.add_argument(
        "--users-per-role",
        type=int,
        default=1,
        help="Number of users per role"
    )

    parser.add_argument(
        "--output",
        type=str,
        default=".env",
        help="Output env file"
    )

    args = parser.parse_args()

    if args.generate:
        users = generate_user_passwords(args.users_per_role)
        save_to_env_file(users, args.output)
        logger.info(f"Generated {len(users)} users and saved to {args.output}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()