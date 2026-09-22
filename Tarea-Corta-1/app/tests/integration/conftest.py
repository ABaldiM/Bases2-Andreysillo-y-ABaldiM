"""

Estos tests corren DENTRO del contenedor de la app (vía
"docker compose exec app pytest"), contra la pila real que levanta
Compose -- no contra mocks ni contra el cliente de pruebas en memoria de
Flask
Por esto aqui se usan "requests" para hablar HTTP de verdad con el propio
proceso de gunicorn, y piden tokens reales al Keycloak real
"""
from __future__ import annotations

import os

import pytest
import requests

# La app se prueba a sí misma por "localhost": estos tests corren adentro
# del mismo contenedor que gunicorn, así que localhost:8080 es el propio
# proceso de la app (no hace falta pasar por el nombre de servicio "app").
BASE_URL = "http://localhost:8080"

# Keycloak, en cambio, SIEMPRE por la URL interna de la red de Docker
# (KEYCLOAK_URL = "http://keycloak:8080"). Si pidiéramos el token contra
# localhost:8090 (el puerto publicado hacia el host), el "iss" del token no
# coincidiría con lo que auth.py espera, y todo fallaría con 401 aunque el
# flujo esté bien -- ya nos pasó una vez probando esto a mano con curl.
_KEYCLOAK_URL = os.environ["KEYCLOAK_URL"]
_KEYCLOAK_REALM = os.environ["KEYCLOAK_REALM"]
_CLIENT_ID = os.environ["KEYCLOAK_CLIENT_ID"]
_CLIENT_SECRET = os.environ["KEYCLOAK_CLIENT_SECRET"]

_TOKEN_URL = f"{_KEYCLOAK_URL}/realms/{_KEYCLOAK_REALM}/protocol/openid-connect/token"


def _pedir_token(username: str, password: str) -> str:
    """Pide un token real a Keycloak con usuario+contraseña.

    Este flujo (Resource Owner Password Credentials / "Direct Access
    Grant") está habilitado a propósito en el client "comidas-api" -- ver
    realm-export.json -- para que un script como este pueda conseguir un
    token sin pasar por una pantalla de login en el navegador.
    admin-tester y sin-rol-tester son usuarios de prueba (fixtures) que ya
    vienen definidos en el propio realm, con y sin el rol "admin".
    """
    respuesta = requests.post(
        _TOKEN_URL,
        data={
            "grant_type": "password",
            "client_id": _CLIENT_ID,
            "client_secret": _CLIENT_SECRET,
            "username": username,
            "password": password,
        },
        timeout=5,
    )
    respuesta.raise_for_status()
    return respuesta.json()["access_token"]


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL


@pytest.fixture(scope="session")
def token_admin() -> str:
    """Token de un usuario CON el rol 'admin' -- crear/editar/borrar
    deberían aceptarlo. scope="session": se pide una sola vez para toda
    la corrida de tests, no en cada test (Keycloak no hace falta
    molestarlo más de lo necesario)."""
    return _pedir_token("admin-tester", "AdminTester123!")


@pytest.fixture(scope="session")
def token_sin_rol() -> str:
    """Token válido, pero de un usuario SIN el rol 'admin' -- las rutas
    protegidas deberían responder 403, no 401 (el token en sí es
    perfectamente válido, solo que sin permiso)."""
    return _pedir_token("sin-rol-tester", "SinRolTester123!")


@pytest.fixture()
def headers_admin(token_admin: str) -> dict:
    return {"Authorization": f"Bearer {token_admin}"}


@pytest.fixture()
def headers_sin_rol(token_sin_rol: str) -> dict:
    return {"Authorization": f"Bearer {token_sin_rol}"}


@pytest.fixture()
def reserva_valida() -> dict:
    """Payload válido para crear una reserva, según el contrato actual de
    models.py (nombre, fecha, hora, cantidad -- coincide con las columnas
    reales de la tabla "reserva" en db/init.sql: nombre_cliente, fecha,
    hora, cantidad_personas)."""
    return {
        "nombre": "Cliente de prueba",
        "fecha": "2026-12-24",
        "hora": "20:00",
        "cantidad": 4,
    }
