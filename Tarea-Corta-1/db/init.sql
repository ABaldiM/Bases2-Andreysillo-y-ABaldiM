-- esto se ejecuta solo una vez cuando Postgres arranca con la carpeta de datos vacía
-- (ver el bind mount hacia /docker-entrypoint-initdb.d/ en compose.yml

-- Entidad del dominio: una reserva de mesa en un restaurante.
-- ademas el id sube automaticamente con lo del SERIAL PRIMARY KEY
CREATE TABLE IF NOT EXISTS reserva (
    id SERIAL PRIMARY KEY,
    nombre_cliente VARCHAR(100) NOT NULL,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    cantidad_personas INTEGER NOT NULL CHECK (cantidad_personas > 0 AND cantidad_personas <= 20),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Índice para el filtro por fecha que pide la ruta GET /reservas?fecha=...
CREATE INDEX IF NOT EXISTS idx_reserva_fecha ON reserva(fecha);

CREATE TABLE IF NOT EXISTS cliente (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    correo_electronico VARCHAR(100) UNIQUE NOT NULL,
    telefono VARCHAR(15),
    metodo_de_pago VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mesa (
    id SERIAL PRIMARY KEY,
    numero_mesa INTEGER UNIQUE NOT NULL,
    capacidad INTEGER NOT NULL CHECK (capacidad > 0 AND capacidad <= 20),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tipo_orden (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) UNIQUE NOT NULL,
    descripcion TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orden(
    id SERIAL PRIMARY KEY,
    id_reserva INTEGER NOT NULL REFERENCES reserva(id),
    id_cliente INTEGER REFERENCES cliente(id),
    id_mesa INTEGER REFERENCES mesa(id),
    id_tipo_orden INTEGER REFERENCES tipo_orden(id),
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    total DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);



-- ============================================================
-- Crear reserva nueva
-- ============================================================
CREATE OR REPLACE FUNCTION crear_reserva(
    p_nombre_cliente   VARCHAR(100), -- Parametro de entrada para el nombre del cliente en el SP/Funcion
    p_fecha            DATE, -- Parametro de entrada para fecha de la reserva del cliente en el SP/Funcion
    p_hora             TIME, -- Parametro de entrada para la hora de la reserva del cliente en el SP/Funcion
    p_cantidad_personas INTEGER -- Parametro de entrada para la cantidad de personas de la reserva del cliente en el SP/Funcion
)
RETURNS reserva -- Es lo que devuelve la funcion, es una fila completa con la misma estructura de la tabla
LANGUAGE plpgsql
AS $$ -- Equivalente a Begin en SQL-Server
DECLARE
    nueva_reserva reserva; -- Variable local para almacenar en memoria los datos temporales
                            -- Algo interesante es que el tipo de dato (reserva) se crea cuando se crea la tabla
BEGIN
    INSERT INTO reserva (nombre_cliente, fecha, hora, cantidad_personas)
    VALUES (p_nombre_cliente, p_fecha, p_hora, p_cantidad_personas)
    RETURNING * INTO nueva_reserva; -- Al momento de  insertar en la tabla se capturan todos los datos de esa nueva fila y los guarda en la varible temporal
                            -- Es util porque captura datos que no se envian como el id o la fecha de creacion

    RETURN nueva_reserva; -- Devuelve la fila (reserva) creada 
END;
$$; -- Equivalente a End en SQL-Server

-- ============================================================
-- READ (por id)
-- ============================================================
CREATE OR REPLACE FUNCTION obtener_reserva(p_id INTEGER)
RETURNS reserva
LANGUAGE plpgsql
AS $$
DECLARE
    fila reserva;
BEGIN
    SELECT * INTO fila FROM reserva WHERE id = p_id;
    RETURN fila; -- fila.id es NULL si no existe; el backend lo interpreta como 404
END;
$$;

-- ============================================================
-- LIST (con filtro opcional por fecha)
-- ============================================================
CREATE OR REPLACE FUNCTION listar_reservas(p_fecha DATE DEFAULT NULL)
RETURNS SETOF reserva
LANGUAGE sql
AS $$
    SELECT *
    FROM reserva
    WHERE p_fecha IS NULL OR fecha = p_fecha
    ORDER BY fecha, hora;
$$;

-- ============================================================
-- UPDATE
-- ============================================================
CREATE OR REPLACE FUNCTION actualizar_reserva(
    p_id                INTEGER,
    p_nombre_cliente    VARCHAR(100),
    p_fecha             DATE,
    p_hora              TIME,
    p_cantidad_personas INTEGER
)
RETURNS reserva
LANGUAGE plpgsql
AS $$
DECLARE
    reserva_actualizada reserva;
BEGIN
    UPDATE reserva
    SET nombre_cliente = p_nombre_cliente,
        fecha = p_fecha,
        hora = p_hora,
        cantidad_personas = p_cantidad_personas
    WHERE id = p_id
    RETURNING * INTO reserva_actualizada;

    RETURN reserva_actualizada; -- actualizada.id es NULL si el id no existía
END;
$$;

-- ============================================================
-- DELETE
-- ============================================================
CREATE OR REPLACE FUNCTION eliminar_reserva(p_id INTEGER)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    filas_afectadas INTEGER;
BEGIN
    DELETE FROM reserva WHERE id = p_id;
    GET DIAGNOSTICS filas_afectadas = ROW_COUNT; -- Obtiene el numero de filas que fueron afectadas por la instruccion SQL
    RETURN filas_afectadas > 0; -- false si el id no existía
END;
$$;