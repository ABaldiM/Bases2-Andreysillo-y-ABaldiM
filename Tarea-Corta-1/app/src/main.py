from flask import Flask, request
from models import Reserva, ValidationError

app = Flask(__name__)

@app.post('/reservas')
def crear_reserva():
    request_json = request.get_json(silent=True)  # None si el JSON viene mal formado

    try:
        reserva = Reserva.from_dict(request_json)
    except ValidationError as e:
        return {"errores": e.errores}, 400
    

    # Aquí llega solo si todo es válido insertar en PostgreSQL
    # y devolver el recurso creado con su id
    # reserva.id = insertar_en_bd(reserva)
    return reserva.to_dict(), 201


@app.put("/reservas/<int:id>")
def actualizar_reserva(id):
    request_json = request.get_json(silent=True)

    try:
        reserva = Reserva.from_dict(request_json, id=id)
    except ValidationError as e:
        return {"errores": e.errores}, 400
    
    actualizado = True
    # actualizado = actualizar_en_bd(reserva)

    if not actualizado:
        return {"error": "Reserva no encontrada"}, 404
    
    return reserva.to_dict(), 200

