"""Ciclo de vida completo del recurso /reservas: crear, listar (con
filtro), consultar por id, actualizar, eliminar.

NOTA IMPORTANTE: GET /reservas, GET /reservas/<id> y DELETE /reservas/<id>
todavía no existen en main.py, y el POST actual no inserta de verdad en
Postgres (está comentado "# insertar_en_bd"). La mayoría de estos tests
van a fallar/dar error hasta que Persona A termine esas partes -- es a
propósito: sirven de lista de verificación ejecutable de lo que falta del
contrato pedido por el enunciado, no son un bug de este archivo.
"""
import requests


def test_crear_reserva_valida_devuelve_201_con_id(base_url, headers_admin, reserva_valida):
    r = requests.post(
        f"{base_url}/reservas", json=reserva_valida, headers=headers_admin, timeout=5
    )
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["id"] is not None
    assert cuerpo["nombre"] == reserva_valida["nombre"]


def test_crear_reserva_invalida_devuelve_400(base_url, headers_admin):
    cuerpo_invalido = {
        "nombre": "",
        "fecha": "fecha-invalida",
        "hora": "25:99",
        "cantidad": -1,
    }
    r = requests.post(
        f"{base_url}/reservas", json=cuerpo_invalido, headers=headers_admin, timeout=5
    )
    assert r.status_code == 400


def test_listar_reservas_devuelve_200_con_lista(base_url, headers_admin, reserva_valida):
    requests.post(f"{base_url}/reservas", json=reserva_valida, headers=headers_admin, timeout=5)

    r = requests.get(f"{base_url}/reservas", timeout=5)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_listar_reservas_admite_filtro_por_fecha(base_url, headers_admin, reserva_valida):
    requests.post(f"{base_url}/reservas", json=reserva_valida, headers=headers_admin, timeout=5)

    r = requests.get(f"{base_url}/reservas", params={"fecha": reserva_valida["fecha"]}, timeout=5)
    assert r.status_code == 200
    resultados = r.json()
    assert len(resultados) >= 1
    assert all(item["fecha"] == reserva_valida["fecha"] for item in resultados)


def test_obtener_reserva_por_id_existente(base_url, headers_admin, reserva_valida):
    creada = requests.post(
        f"{base_url}/reservas", json=reserva_valida, headers=headers_admin, timeout=5
    ).json()

    r = requests.get(f"{base_url}/reservas/{creada['id']}", timeout=5)
    assert r.status_code == 200
    assert r.json()["id"] == creada["id"]


def test_obtener_reserva_inexistente_devuelve_404(base_url):
    r = requests.get(f"{base_url}/reservas/999999", timeout=5)
    assert r.status_code == 404


def test_actualizar_reserva_existente(base_url, headers_admin, reserva_valida):
    creada = requests.post(
        f"{base_url}/reservas", json=reserva_valida, headers=headers_admin, timeout=5
    ).json()

    datos_actualizados = {**reserva_valida, "cantidad": 8}
    r = requests.put(
        f"{base_url}/reservas/{creada['id']}",
        json=datos_actualizados,
        headers=headers_admin,
        timeout=5,
    )
    assert r.status_code == 200
    assert r.json()["cantidad"] == 8


def test_actualizar_reserva_inexistente_devuelve_404(base_url, headers_admin, reserva_valida):
    r = requests.put(
        f"{base_url}/reservas/999999", json=reserva_valida, headers=headers_admin, timeout=5
    )
    assert r.status_code == 404


def test_eliminar_reserva_existente_devuelve_204(base_url, headers_admin, reserva_valida):
    creada = requests.post(
        f"{base_url}/reservas", json=reserva_valida, headers=headers_admin, timeout=5
    ).json()

    r = requests.delete(f"{base_url}/reservas/{creada['id']}", headers=headers_admin, timeout=5)
    assert r.status_code == 204


def test_eliminar_reserva_inexistente_devuelve_404(base_url, headers_admin):
    r = requests.delete(f"{base_url}/reservas/999999", headers=headers_admin, timeout=5)
    assert r.status_code == 404
