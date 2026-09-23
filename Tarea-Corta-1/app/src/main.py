from flask import Flask, request
from models import Reserva, ValidationError
from auth import requiere_rol
import psycopg
import os

app = Flask(__name__)

def get_db_connection():
    conn = psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )
    return conn

@app.get("/health")
def health():
    return {"status": "ok"}, 200


@app.get("/ready")
def ready():
    try:
        conn = get_db_connection()
        conn.close()
        return {"status": "ok"}, 200
    except Exception:
        return {"status": "no disponible"}, 503

@app.post('/reservas')
@requiere_rol("admin")
def crear_reserva():
    request_json = request.get_json(silent=True)  # None si el JSON viene mal formado

    # 1. Validar la entrada usando el modelo
    try:
        reserva = Reserva.from_dict(request_json)
    except ValidationError as e:
        return {"errores": e.errores}, 400

    

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Se envían los atributos ya validados y "limpios" de la instancia reserva
        cur.execute(
            """
            SELECT * FROM crear_reserva(%s, %s, %s, %s);
            """,
            (reserva.nombre, reserva.fecha, reserva.hora, reserva.cantidad)
        )
        
        # Obtenemos la fila recién creada (tupla)
        fila = cur.fetchone()
        
        # IMPORTANTE: Guardar los cambios (Commit)
        conn.commit()
        
        # Convertimos la tupla devuelta por la BD en un objeto Reserva y luego a dict
        reserva_creada = Reserva.from_db_row(fila)
        
        return reserva_creada.to_dict(), 201

    except Exception as e:
        conn.rollback()  # Revierte si hay error en la BD
        return {"error": str(e)}, 500
        
    finally:
        cur.close()
        conn.close()


@app.put("/reservas/<int:id>")
@requiere_rol("admin")
def actualizar_reserva(id):
    request_json = request.get_json(silent=True)

    # 1. Validar la entrada usando el modelo, pasando el ID de la URL
    try:
        reserva = Reserva.from_dict(request_json, id=id)
    except ValidationError as e:
        return {"errores": e.errores}, 400
    

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Llamamos a la función de PostgreSQL
        cur.execute(
            """
            SELECT * FROM actualizar_reserva(%s, %s, %s, %s, %s);
            """,
            (reserva.id, reserva.nombre, reserva.fecha, reserva.hora, reserva.cantidad)
        )
        
        fila = cur.fetchone()
        conn.commit()
        
        # Intentamos mapear la tupla. Si era ID inválido, fila vendrá con nulos.
        reserva_actualizada = Reserva.from_db_row(fila)
        
        if reserva_actualizada is None:
            return {"error": "Reserva no encontrada"}, 404
            
        return reserva_actualizada.to_dict(), 200

    except Exception as e:
        conn.rollback()
        return {"error": str(e)}, 500
        
    finally:
        cur.close()
        conn.close()


@app.delete("/reservas/<int:id>")
@requiere_rol("admin")
def borrar_reserva(id):
    
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # IMPORTANTE: (id,) con coma para que sea una tupla válida en Python
        cur.execute("SELECT eliminar_reserva(%s);", (id,))
        
        # Extraemos el valor booleano (True/False)
        fue_eliminada = cur.fetchone()[0]
        conn.commit()
    
        if fue_eliminada:
            return {"mensaje": "Reserva eliminada correctamente"}, 204
        else:
            return {"error": "Reserva no encontrada"}, 404
            
    except Exception as e:
        conn.rollback()
        return {"error": str(e)}, 500
        
    finally:
        cur.close()
        conn.close()


@app.get("/reservas/<int:id>")
def filtrado_id(id):
 
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # IMPORTANTE: (id,) con coma
        cur.execute("SELECT * FROM obtener_reserva(%s);", (id,))
        fila = cur.fetchone()
        
        # Parseamos la tupla a objeto
        reserva = Reserva.from_db_row(fila)
        
        if reserva:
            return reserva.to_dict(), 200
        else:
            return {"error": "Reserva no encontrada"}, 404
            
    except Exception as e:
        return {"error": str(e)}, 500
        
    finally:
        cur.close()
        conn.close()


@app.get("/reservas")
def listar_o_filtrar_fecha():
    # Obtiene ?fecha=YYYY-MM-DD de la URL, devuelve None si no se envía
    fecha_filtro = request.args.get('fecha') 
    

    
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM listar_reservas(%s);", (fecha_filtro,))
        filas = cur.fetchall()
        
        # 1. Mapear cada tupla válida a un objeto Reserva usando from_db_row()
        # 2. Convertir cada objeto a dict usando to_dict()
        lista_json = []
        for fila in filas:
            reserva_obj = Reserva.from_db_row(fila)
            if reserva_obj:
                lista_json.append(reserva_obj.to_dict())
                
        return lista_json, 200
        
    except Exception as e:
        return {"error": str(e)}, 500
        
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, host=os.getenv("Server"))