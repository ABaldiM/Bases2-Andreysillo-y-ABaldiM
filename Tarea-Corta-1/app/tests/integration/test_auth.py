"""Autenticación/autorización en las rutas de modificación.

Cubre exactamente el contrato del enunciado: sin token -> 401; con token
válido pero sin el rol requerido -> 403
"""
import requests


# --- crear ---

def test_crear_sin_token_da_401(base_url, reserva_valida):
    r = requests.post(f"{base_url}/reservas", json=reserva_valida, timeout=5)
    assert r.status_code == 401


def test_crear_con_token_sin_rol_da_403(base_url, headers_sin_rol, reserva_valida):
    r = requests.post(
        f"{base_url}/reservas", json=reserva_valida, headers=headers_sin_rol, timeout=5
    )
    assert r.status_code == 403


# --- actualizar ---
# NOTA: PUT /reservas/<id> ya existe en main.py, así que estos dos sí
# deberían pasar ahora mismo (no dependen de rutas todavía sin escribir).

def test_actualizar_sin_token_da_401(base_url):
    r = requests.put(f"{base_url}/reservas/1", json={}, timeout=5)
    assert r.status_code == 401


def test_actualizar_con_token_sin_rol_da_403(base_url, headers_sin_rol):
    r = requests.put(f"{base_url}/reservas/1", json={}, headers=headers_sin_rol, timeout=5)
    assert r.status_code == 403


# --- eliminar ---
# NOTA: DELETE /reservas/<id> todavía no existe en main.py -- estos dos
# van a fallar hasta que se implemente y se le agregue @requiere_rol("admin").

def test_eliminar_sin_token_da_401(base_url):
    r = requests.delete(f"{base_url}/reservas/1", timeout=5)
    assert r.status_code == 401


def test_eliminar_con_token_sin_rol_da_403(base_url, headers_sin_rol):
    r = requests.delete(f"{base_url}/reservas/1", headers=headers_sin_rol, timeout=5)
    assert r.status_code == 403
