"""Rutas de liveness/readiness -- deben quedar siempre abiertas (sin token).

NOTA: /health y /ready todavía no están implementadas en main.py (falta de
Persona A). Estos tests van a fallar hasta que existan -- es intencional,
sirven de lista de verificación ejecutable, no es un bug de este archivo.
"""
import requests


def test_health_responde_200_sin_tocar_la_base(base_url):
    # /health es la ruta de liveness: solo confirma que el proceso está
    # vivo, sin consultar Postgres, osea es la ruta en la que se apoya el
    # healthcheck del contenedor de la app en el compose
    r = requests.get(f"{base_url}/health", timeout=5)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/json")


def test_ready_responde_200_cuando_la_base_esta_disponible(base_url):
    # /ready sí revisa la conexión con Postgres. Como en estos tests la
    # base ya está healthy (Compose no deja arrancar la app si no lo
    # está), acá esperamos 200 -- el caso 503 (base caída) no se puede
    # probar sin apagar el contenedor de "db" a mitad de la corrida
    r = requests.get(f"{base_url}/ready", timeout=5)
    assert r.status_code == 200
