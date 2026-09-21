"""Modelo de dominio: Reserva.

Solo usa la biblioteca estándar, así que se puede probar de forma aislada
(sin base de datos ni Keycloak). Las rutas capturan ValidationError y
responden 400 con el detalle de los campos inválidos.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any, Optional

NOMBRE_MAX = 100
EMAIL_MAX = 254
CANTIDAD_MIN = 1
CANTIDAD_MAX = 50

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_FECHA_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ValidationError(Exception):
    """Error de validación. `errores` mapea campo -> mensaje."""

    def __init__(self, errores: dict[str, str]):
        self.errores = errores
        super().__init__(errores)

# Regla para validar nombre
def _validar_nombre(valor: Any) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError("es obligatorio y debe ser texto no vacío")
    valor = valor.strip()
    if len(valor) > NOMBRE_MAX:
        raise ValueError(f"no puede superar {NOMBRE_MAX} caracteres")
    return valor

# Regla para validar email
def _validar_email(valor: Any) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError("es obligatorio y debe ser texto")
    valor = valor.strip()
    if len(valor) > EMAIL_MAX or not _EMAIL_RE.match(valor):
        raise ValueError("no tiene un formato de correo válido")
    return valor

# Regla para validar fecha
def _validar_fecha(valor: Any) -> date:
    # Acepta un date (p. ej. el que devuelve PostgreSQL) o un texto YYYY-MM-DD.
    if isinstance(valor, date):
        return valor
    if not isinstance(valor, str) or not _FECHA_RE.match(valor.strip()):
        raise ValueError("debe tener el formato YYYY-MM-DD")
    try:
        return date.fromisoformat(valor.strip())
    except ValueError:
        raise ValueError("no es una fecha real del calendario")

# Regla para validar que la cantidad sea un entero entre 1 y 50
def _validar_cantidad(valor: Any) -> int:
    # bool es subclase de int en Python: True no debe pasar como cantidad.
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ValueError("debe ser un número entero")
    if not CANTIDAD_MIN <= valor <= CANTIDAD_MAX:
        raise ValueError(f"debe estar entre {CANTIDAD_MIN} y {CANTIDAD_MAX}")
    return valor


_VALIDADORES = {
    "nombre": _validar_nombre,
    "email": _validar_email,
    "fecha": _validar_fecha,
    "cantidad": _validar_cantidad,
}


@dataclass
class Reserva:
    # Atributos de la clase
    nombre: str
    email: str
    fecha: date
    cantidad: int
    id: Optional[int] = None # Es opcional y nulo hasta que Postgres lo añade.

    # Metodos de la clase

    """
    Reserva.from_dict(datos) = Validar JSON/Diccionario que recibe y devuelve la reserva, si algo falla, lanza todos los errores
    a la vez para ver todo lo que esta mal
    """
    @classmethod
    def from_dict(cls, datos: Any, id: Optional[int] = None) -> "Reserva":
        if not isinstance(datos, dict):
            raise ValidationError({"cuerpo": "debe ser un objeto JSON"})

        errores: dict[str, str] = {}
        limpios: dict[str, Any] = {}
        for campo, validar in _VALIDADORES.items():
            if campo not in datos:
                errores[campo] = "es obligatorio"
                continue
            try:
                limpios[campo] = validar(datos[campo])
            except ValueError as exc:
                errores[campo] = str(exc) # Guarda el error del campo en mal formato o faltante

        if errores:
            raise ValidationError(errores)
        return cls(id=id, **limpios)

    """
    Metodo para pasar de una lista a un JSON/Diccionario
    
    """
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "email": self.email,
            "fecha": self.fecha.isoformat(),
            "cantidad": self.cantidad,
        }