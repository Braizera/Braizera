#!/usr/bin/env python3
"""
Script para desativação em massa de usuários no DEXBoard.

Fluxo padrão:
1) Carrega uma lista de usuários (CSV/TXT)
2) (Opcional) resolve ID por e-mail
3) Executa chamada de desativação por usuário
4) Gera relatório final de sucesso/falha

Exemplo de uso:
python3 scripts/desativar_usuarios_dexboard.py \
  --base-url "https://seu-dexboard.com" \
  --token "SEU_TOKEN" \
  --input "usuarios.csv" \
  --id-column "user_id" \
  --dry-run
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import requests


@dataclass
class UserEntry:
    raw: Dict[str, str]
    user_id: Optional[str] = None
    email: Optional[str] = None


class DexBoardBulkDeactivator:
    def __init__(self, args: argparse.Namespace) -> None:
        self.base_url = args.base_url.rstrip("/")
        self.timeout = args.timeout
        self.pause_seconds = args.pause_seconds
        self.max_retries = args.max_retries
        self.dry_run = args.dry_run
        self.lookup_endpoint = args.lookup_endpoint
        self.deactivate_endpoint = args.deactivate_endpoint
        self.deactivate_method = args.deactivate_method.upper()
        self.deactivate_payload = args.deactivate_payload

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {args.token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(method, url, timeout=self.timeout, **kwargs)
                if response.status_code >= 500 and attempt < self.max_retries:
                    time.sleep(1 + attempt)
                    continue
                return response
            except requests.RequestException as err:
                last_error = err
                if attempt < self.max_retries:
                    time.sleep(1 + attempt)
                    continue
                raise err
        if last_error:
            raise last_error
        raise RuntimeError("Falha inesperada na requisição")

    def resolve_user_id_by_email(self, email: str) -> Optional[str]:
        endpoint = self.lookup_endpoint.format(email=email)
        url = f"{self.base_url}{endpoint}"
        response = self._request("GET", url)

        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            raise RuntimeError(
                f"Erro ao consultar usuário por e-mail {email}: "
                f"HTTP {response.status_code} - {response.text}"
            )

        data = response.json()
        # Ajuste esta lógica conforme o contrato real do DEXBoard
        if isinstance(data, dict):
            for key in ("id", "user_id", "uuid"):
                if key in data and data[key]:
                    return str(data[key])
            if "data" in data and isinstance(data["data"], dict):
                for key in ("id", "user_id", "uuid"):
                    if key in data["data"] and data["data"][key]:
                        return str(data["data"][key])
        return None

    def deactivate_user(self, user_id: str) -> requests.Response:
        endpoint = self.deactivate_endpoint.format(user_id=user_id)
        url = f"{self.base_url}{endpoint}"

        payload = None
        if self.deactivate_payload:
            payload = json.loads(self.deactivate_payload)

        if self.dry_run:
            print(f"[DRY-RUN] {self.deactivate_method} {url} payload={payload}")
            return _fake_success_response()

        if self.deactivate_method in {"POST", "PUT", "PATCH"}:
            return self._request(self.deactivate_method, url, json=payload)

        return self._request(self.deactivate_method, url)


def _fake_success_response() -> requests.Response:
    response = requests.Response()
    response.status_code = 200
    response._content = b'{"ok": true, "dry_run": true}'
    return response


def parse_input_file(
    path: Path, id_column: str, email_column: str, separator: str
) -> List[UserEntry]:
    users: List[UserEntry] = []

    if path.suffix.lower() == ".txt":
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                value = line.strip()
                if not value:
                    continue
                users.append(UserEntry(raw={"value": value}, user_id=value))
        return users

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=separator)
        for row in reader:
            user_id = (row.get(id_column) or "").strip() or None
            email = (row.get(email_column) or "").strip() or None
            users.append(UserEntry(raw=row, user_id=user_id, email=email))

    return users


def validate_users(users: Iterable[UserEntry]) -> None:
    total = 0
    valid = 0
    for item in users:
        total += 1
        if item.user_id or item.email:
            valid += 1

    if total == 0:
        raise ValueError("Arquivo de entrada vazio ou sem registros válidos")
    if valid == 0:
        raise ValueError("Nenhum registro contém user_id ou email")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Desativação em massa de usuários no DEXBoard"
    )
    parser.add_argument("--base-url", required=True, help="URL base da API DEXBoard")
    parser.add_argument("--token", required=True, help="Token Bearer de autenticação")
    parser.add_argument("--input", required=True, help="Arquivo CSV ou TXT com usuários")

    parser.add_argument(
        "--id-column",
        default="user_id",
        help="Nome da coluna de ID no CSV (default: user_id)",
    )
    parser.add_argument(
        "--email-column",
        default="email",
        help="Nome da coluna de e-mail no CSV (default: email)",
    )
    parser.add_argument(
        "--separator",
        default=",",
        help="Separador do CSV (default: ,)",
    )

    parser.add_argument(
        "--lookup-endpoint",
        default="/api/users/by-email/{email}",
        help=(
            "Endpoint para buscar usuário por e-mail (default: /api/users/by-email/{email})"
        ),
    )
    parser.add_argument(
        "--deactivate-endpoint",
        default="/api/users/{user_id}/deactivate",
        help=(
            "Endpoint de desativação (default: /api/users/{user_id}/deactivate)"
        ),
    )
    parser.add_argument(
        "--deactivate-method",
        default="POST",
        choices=["POST", "PUT", "PATCH", "DELETE"],
        help="Método HTTP para desativar usuário (default: POST)",
    )
    parser.add_argument(
        "--deactivate-payload",
        default='{"active": false}',
        help=(
            "Payload JSON enviado na desativação. "
            "Ex: '{\"active\": false, \"reason\": \"offboarding\"}'"
        ),
    )

    parser.add_argument(
        "--timeout", type=int, default=30, help="Timeout de cada request em segundos"
    )
    parser.add_argument(
        "--max-retries", type=int, default=2, help="Tentativas extras em falhas transitórias"
    )
    parser.add_argument(
        "--pause-seconds",
        type=float,
        default=0.2,
        help="Intervalo entre chamadas para evitar rate-limit",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Não envia alterações, só simula chamadas",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Arquivo não encontrado: {input_path}", file=sys.stderr)
        return 2

    users = parse_input_file(
        path=input_path,
        id_column=args.id_column,
        email_column=args.email_column,
        separator=args.separator,
    )

    try:
        validate_users(users)
    except ValueError as err:
        print(f"Erro de validação: {err}", file=sys.stderr)
        return 2

    client = DexBoardBulkDeactivator(args)

    total = len(users)
    success = 0
    failed = 0

    print(f"Iniciando processamento de {total} usuários...")

    for idx, item in enumerate(users, start=1):
        user_id = item.user_id

        if not user_id and item.email:
            try:
                user_id = client.resolve_user_id_by_email(item.email)
            except Exception as err:  # noqa: BLE001
                failed += 1
                print(f"[{idx}/{total}] ERRO lookup email={item.email}: {err}")
                continue

        if not user_id:
            failed += 1
            print(f"[{idx}/{total}] IGNORADO sem user_id/email válido. Linha={item.raw}")
            continue

        try:
            response = client.deactivate_user(user_id)
            if response.status_code < 300:
                success += 1
                print(f"[{idx}/{total}] OK user_id={user_id} (HTTP {response.status_code})")
            else:
                failed += 1
                print(
                    f"[{idx}/{total}] FALHA user_id={user_id} "
                    f"(HTTP {response.status_code}) body={response.text}"
                )
        except Exception as err:  # noqa: BLE001
            failed += 1
            print(f"[{idx}/{total}] ERRO user_id={user_id}: {err}")

        if args.pause_seconds > 0:
            time.sleep(args.pause_seconds)

    print("\nResumo:")
    print(f"  Total:    {total}")
    print(f"  Sucesso:  {success}")
    print(f"  Falhas:   {failed}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
