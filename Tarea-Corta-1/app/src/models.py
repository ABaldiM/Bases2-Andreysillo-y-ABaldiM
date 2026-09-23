"""Modelo de dominio: Reserva.

Solo usa la biblioteca estándar, así que se puede probar de forma aislada
(sin base de datos ni Keycloak). Las rutas capturan ValidationError y
responden 400 con el detalle de los campos inválidos.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, time
from typing import Any, Optional

NOMBRE_MAX = 100
CANTIDAD_MIN = 1
CANTIDAD_MAX = 50

_FECHA_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_HORA_RE = re.compile(r"^\d{2}:\d{2}(:\d{2})?$") # Acepta HH:MM o HH:MM:SS


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


# Regla para validar fecha
def _validar_fecha(valor: Any) -> date:
    if isinstance(valor, date):
        return valor
    if not isinstance(valor, str) or not _FECHA_RE.match(valor.strip()):
        raise ValueError("debe tener el formato YYYY-MM-DD")
    try:
        return date.fromisoformat(valor.strip())
    except ValueError:
        raise ValueError("no es una fecha real del calendario")


# Regla para validar hora (NUEVO)
def _validar_hora(valor: Any) -> time:
    # Si psycopg2 ya lo convirtió a objeto time de Python
    if isinstance(valor, time):
        return valor
    if not isinstance(valor, str) or not _HORA_RE.match(valor.strip()):
        raise ValueError("debe tener el formato HH:MM o HH:MM:SS")
    try:
        return time.fromisoformat(valor.strip())
    except ValueError:
        raise ValueError("no es una hora válida")


# Regla para validar que la cantidad sea un entero entre 1 y 50
def _validar_cantidad(valor: Any) -> int:
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ValueError("debe ser un número entero")
    if not CANTIDAD_MIN <= valor <= CANTIDAD_MAX:
        raise ValueError(f"debe estar entre {CANTIDAD_MIN} y {CANTIDAD_MAX}")
    return valor


_VALIDADORES = {
    "nombre": _validar_nombre,
    "fecha": _validar_fecha,
    "hora": _validar_hora,         
    "cantidad": _validar_cantidad,
}


@dataclass
class Reserva:
    # Atributos de la clase
    nombre: str
    fecha: date
    hora: time                     
    cantidad: int
    id: Optional[int] = None       # Es opcional y nulo hasta que Postgres lo añade.

    # ---------------------------------------------------------
    # 1. PARSEAR DESDE JSON (FRONTEND -> BACKEND)
    # ---------------------------------------------------------
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
                errores[campo] = str(exc)

        if errores:
            raise ValidationError(errores)
        return cls(id=id, **limpios)

    # ---------------------------------------------------------
    # 2. PARSEAR DESDE POSTGRES (BASE DE DATOS -> BACKEND)
    # ---------------------------------------------------------
    @classmethod
    def from_db_row(cls, fila: tuple) -> Optional["Reserva"]:
        """Convierte una tupla de psycopg2 en una instancia de Reserva."""
        if not fila or fila[0] is None:
            return None
        
        # El orden depende del SELECT en Postgres: 
        # id(0), nombre_cliente(1), fecha(2), hora(3), cantidad_personas(4), created_at(5)
        return cls(
            id=fila[0],
            nombre=fila[1],
            fecha=fila[2],
            hora=fila[3],
            cantidad=fila[4]
        )

    # ---------------------------------------------------------
    # 3. EXPORTAR A JSON (BACKEND -> FRONTEND)
    # ---------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        """Metodo para pasar del objeto en memoria a un JSON/Diccionario"""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "fecha": self.fecha.isoformat(),
            "hora": self.hora.isoformat(), # Formatea HH:MM:SS
            "cantidad": self.cantidad,
        }