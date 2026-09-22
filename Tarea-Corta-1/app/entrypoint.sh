#!/bin/sh
# entrypoint.sh
#
# Este script es el ENTRYPOINT del contenedor de la app. Se ejecuta SIEMPRE
# antes que el comando real (gunicorn), y su único trabajo es esperar a que
# Postgres esté realmente aceptando conexiones antes de dejar arrancar la app.
#
# Es la segunda capa de la estrategia de "arranque ordenado" que pide el
# enunciado: la primera capa es el healthcheck + depends_on con condición en
# el compose.yml (evita que el contenedor de la app ni siquiera se cree hasta
# que Postgres esté "healthy"); esta es una capa extra de seguridad por si esa
# condición no alcanza (por ejemplo, "healthy" según Docker pero la base
# todavía está inicializando datos la primera vez).
set -e

MAX_INTENTOS=30
ESPERA_SEGUNDOS=2
intento=1

echo "entrypoint: esperando a que Postgres (${DB_HOST}:${DB_PORT}) acepte conexiones..."

# "until <comando> ; do ... ; done" repite el bloque MIENTRAS <comando> falle
# (código de salida distinto de 0). Acá <comando> es un script de Python de
# una línea (via "python -c") que intenta abrir una conexión real con
# psycopg -el mismo driver que usa la app-, no solo comprobar si el puerto
# TCP responde. Si psycopg.connect() lanza una excepción, hacemos sys.exit(1)
# y el "until" interpreta eso como "todavía falló, repetí".
until python -c "
import sys
import psycopg
try:
    conexion = psycopg.connect(
        host='${DB_HOST}',
        port='${DB_PORT}',
        user='${POSTGRES_USER}',
        password='${POSTGRES_PASSWORD}',
        dbname='${POSTGRES_DB}',
        connect_timeout=3,
    )
    conexion.close()
except Exception as error:
    print(f'entrypoint: intento fallido -> {error}', file=sys.stderr)
    sys.exit(1)
"
do
    # Si ya gastamos todos los intentos permitidos, no tiene sentido seguir
    # esperando: algo está mal configurado (host/puerto/credenciales) y es
    # mejor que el contenedor falle rápido y visible, en vez de colgarse
    # esperando para siempre.
    if [ "$intento" -ge "$MAX_INTENTOS" ]; then
        echo "entrypoint: se agotaron los ${MAX_INTENTOS} intentos. Postgres nunca respondió. Abortando." >&2
        exit 1
    fi

    echo "entrypoint: intento ${intento}/${MAX_INTENTOS} fallido, reintentando en ${ESPERA_SEGUNDOS}s..."
    intento=$((intento + 1))
    sleep "$ESPERA_SEGUNDOS"
done

echo "entrypoint: Postgres está listo. Arrancando la aplicación..."

# "exec" reemplaza este proceso de shell (que hasta acá era el PID 1 del
# contenedor) por el comando real, en vez de dejarlo corriendo como proceso
# padre de gunicorn. "$@" son los argumentos que Docker le pasa a este script,
# que van a ser justo el CMD del Dockerfile (gunicorn -b ... main:app).
#
# Por qué importa: si gunicorn es el PID 1, recibe directamente las señales
# que manda Docker (por ejemplo SIGTERM en un "docker stop"), y puede
# apagarse de forma ordenada. Si en cambio quedara corriendo detrás de este
# script de shell, las señales le llegarían al shell y no a gunicorn.
exec "$@"
