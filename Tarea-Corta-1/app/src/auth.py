"""Validación de tokens de acceso (JWT) emitidos por Keycloak.

No implementamos login, emisión ni firma de tokens acá -- eso lo hace
Keycloak. Este módulo solo verifica que un token que llega en una petición
sea genuino (firmado por el Keycloak de este proyecto, sin vencer) y que su
dueño tenga el rol necesario para la operación que está pidiendo.
"""
from __future__ import annotations

import os
from functools import wraps
from typing import Callable

import jwt
from flask import jsonify, request
from jwt import PyJWKClient

# Estas dos variables las define realm-export.json (KEYCLOAK_REALM) y
# el compose, el nombre del
# servicio en la red interna de Docker, que es solo
# para que una persona entre a la consola desde su navegador). Si no están
# definidas preferimos que la app falle fuerte y temprano al arrancar
# (KeyError), en vez de arrancar mal configurada en silencio
_KEYCLOAK_URL = os.environ["KEYCLOAK_URL"]
_KEYCLOAK_REALM = os.environ["KEYCLOAK_REALM"]

# Toda la configuración OIDC de un realm de Keycloak cuelga de esto
# El "iss" (issuer) que trae cada token tiene que coincidir si o si con esto
_ISSUER = f"{_KEYCLOAK_URL}/realms/{_KEYCLOAK_REALM}"

# Ruta fija que expone cualquier realm de Keycloak con las llaves públicas
# (formato JWKS) usadas para verificar la firma de sus tokens
_JWKS_URL = f"{_ISSUER}/protocol/openid-connect/certs"

# PyJWKClient se crea UNA sola vez, al importar el módulo (no en cada
# request) Guarda las llaves en memoria la primera vez que las necesita y
# las reutiliza en los pedidos siguientes (cacheado( así evitamos un viaje HTTP a
# Keycloak por cada petición protegida
_jwks_client = PyJWKClient(_JWKS_URL)


class TokenInvalido(Exception):
    """El request no trae un token válido (falta, firma mala, vencido, etc.)."""


def _extraer_token() -> str:
    """Saca el JWT del header 'Authorization: Bearer <token>'.

    Lanza TokenInvalido si el header falta o no tiene ese formato -- eso
    siempre termina en un 401
    """
    encabezado = request.headers.get("Authorization", "")
    if not encabezado.startswith("Bearer "):
        raise TokenInvalido("falta el header Authorization: Bearer <token>")
    return encabezado.removeprefix("Bearer ").strip()


def _validar_token(token: str) -> dict:
    """Verifica firma, vencimiento y emisor de un JWT. Devuelve su payload.

    "Verificar la firma" es lo que garantiza que el token realmente lo
    emitió nuestro Keycloak y que nadie lo alteró -- no es solo leer el
    contenido (eso cualquiera lo puede fabricar), sino confirmar que la
    firma RS256 coincide con la llave pública correspondiente.
    """
    try:
        # get_signing_key_from_jwt mira el "kid" (key id) del header del
        # token, sin todavía confiar en el token, y por eso busca esa llave puntual
        # en la caché de PyJWKClient (o la trae de Keycloak si es la
        # primera vez que la ve)
        llave_de_firma = _jwks_client.get_signing_key_from_jwt(token)

        # Acá pasan TODAS las verificaciones reales:
        # - la firma RS256 coincide con la llave pública -> el token es
        #   genuino y no fue modificado
        # - "exp" (expiración) no venció -- PyJWT lo revisa solo, por
        #   defecto, si el claim está presente
        # - "iss" (issuer) coincide EXACTO con nuestro Keycloak -- sin
        #   esto, un token de cualquier otro Keycloak (o de otro realm)
        #   pasaría igual con solo tener una firma válida
        return jwt.decode(
            token,
            llave_de_firma.key,
            algorithms=["RS256"],
            issuer=_ISSUER,
        )
    except jwt.PyJWTError as error:
        # PyJWTError es la clase base de TODOS los errores de PyJWT, no nos interesa distinguirlos: cualquiera de
        # ellos significa "no confío en este token", osea tiraria un 401
        raise TokenInvalido(str(error)) from error


def requiere_rol(rol_requerido: str) -> Callable:
    """Decorador para proteger una ruta de Flask con un rol de Keycloak.

    Uso: @requiere_rol("admin") arriba de la función de la ruta, ej.:

        @app.post("/reservas")
        @requiere_rol("admin")
        def crear_reserva():
            ...

    Sin token o con token inválido -> 401
    Con token válido pero sin el rol -> 403
    """

    def decorador(vista: Callable) -> Callable:
        @wraps(vista)  # conserva el nombre/docstring original de la vista
        def envoltura(*args, **kwargs):
            try:
                token = _extraer_token()
                payload = _validar_token(token)
            except TokenInvalido as error:
                return jsonify({"error": str(error)}), 401

            # Los roles de realm (los que definimos en realm-export.json,
            # como "admin") viajan en el payload del token bajo esta
            # estructura anidada cosa que expone Keycloak siempre
            roles = payload.get("realm_access", {}).get("roles", [])
            if rol_requerido not in roles:
                return jsonify({"error": "no tiene el rol requerido"}), 403

            return vista(*args, **kwargs)

        return envoltura

    return decorador
