import pytest
from datetime import date, time
from models import Reserva, ValidationError

@pytest.fixture
def datos_validos():
    return {
        "nombre": "Cliente Unitario",
        "fecha": "2026-12-31",
        "hora": "19:30",
        "cantidad": 4
    }

def test_reserva_desde_dict_valido(datos_validos):
    reserva = Reserva.from_dict(datos_validos)
    
    assert reserva.nombre == "Cliente Unitario"
    assert reserva.fecha == date(2026, 12, 31)
    assert reserva.hora == time(19, 30)
    assert reserva.cantidad == 4
    assert reserva.id is None

def test_reserva_rechaza_campos_faltantes():
    datos_incompletos = {"nombre": "Falta todo lo demas"}
    
    with pytest.raises(ValidationError) as excinfo:
        Reserva.from_dict(datos_incompletos)
        
    errores = excinfo.value.errores
    assert "fecha" in errores
    assert "hora" in errores
    assert "cantidad" in errores

def test_reserva_rechaza_cantidad_fuera_de_rango(datos_validos):
    datos_validos["cantidad"] = 100  # Supera el máximo
    
    with pytest.raises(ValidationError) as excinfo:
        Reserva.from_dict(datos_validos)
        
    assert "cantidad" in excinfo.value.errores

def test_reserva_rechaza_formatos_invalidos(datos_validos):
    datos_validos["fecha"] = "31-12-2026"  # Formato incorrecto, se espera YYYY-MM-DD
    datos_validos["hora"] = "99:99"
    
    with pytest.raises(ValidationError) as excinfo:
        Reserva.from_dict(datos_validos)
        
    errores = excinfo.value.errores
    assert "fecha" in errores
    assert "hora" in errores

def test_reserva_to_dict_serializa_correctamente(datos_validos):
    reserva = Reserva.from_dict(datos_validos, id=15)
    resultado = reserva.to_dict()
    
    assert resultado["id"] == 15
    assert resultado["fecha"] == "2026-12-31"
    assert resultado["hora"] == "19:30:00"


def test_reserva_desde_tupla_bd_valida():
    # Simula la tupla que devuelve psycopg2: id, nombre, fecha, hora, cantidad
    fila = (42, "Cliente Tupla", date(2026, 8, 20), time(14, 0), 5)
    reserva = Reserva.from_db_row(fila)
    
    assert reserva is not None
    assert reserva.id == 42
    assert reserva.nombre == "Cliente Tupla"
    assert reserva.cantidad == 5

def test_reserva_desde_tupla_bd_nula():
    # Comprueba el manejo seguro cuando la base de datos no devuelve resultados
    assert Reserva.from_db_row(None) is None
    assert Reserva.from_db_row((None,)) is None

def test_reserva_rechaza_nombre_vacio(datos_validos):
    datos_validos["nombre"] = "   "  # Solo espacios
    
    with pytest.raises(ValidationError) as excinfo:
        Reserva.from_dict(datos_validos)
        
    assert "nombre" in excinfo.value.errores

def test_reserva_rechaza_tipos_incorrectos(datos_validos):
    # En Python, los booleanos son subclases de enteros, hay que probar que se rechacen
    datos_validos["cantidad"] = True 
    
    with pytest.raises(ValidationError) as excinfo:
        Reserva.from_dict(datos_validos)
        
    assert "cantidad" in excinfo.value.errores

def test_reserva_acepta_limites_exactos(datos_validos):
    # Prueba los bordes de la restricción CANTIDAD_MIN y CANTIDAD_MAX
    datos_validos["cantidad"] = 1
    reserva_min = Reserva.from_dict(datos_validos)
    assert reserva_min.cantidad == 1
    
    # Asumiendo que ajustaste CANTIDAD_MAX a 20 para coincidir con init.sql
    datos_validos["cantidad"] = 20 
    reserva_max = Reserva.from_dict(datos_validos)
    assert reserva_max.cantidad == 20