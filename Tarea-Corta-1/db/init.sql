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