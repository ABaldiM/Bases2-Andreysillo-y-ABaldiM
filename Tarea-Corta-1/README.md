# Sistema de Gestión de Reservas - Tarea Corta 1

Este repositorio contiene la contenerización de un servicio HTTP para la gestión de reservas de un restaurante, orquestado mediante Docker Compose. El sistema incluye la aplicación en Python, una base de datos PostgreSQL y un proveedor de identidad (Keycloak).

## 1. Requisitos previos y comando de arranque

Para ejecutar este proyecto es necesario tener instalado Docker y Docker Compose.

1. Clone este repositorio.
2. Configure las variables de entorno copiando el archivo de ejemplo:
   ```bash
   cp .env.example .env
   ```
3. Levante el sistema completo en segundo plano:
   ```bash
   docker compose up -d
   ```

El sistema estará listo cuando los healthchecks de la base de datos y de Keycloak marquen el estado `healthy`, permitiendo que el script `entrypoint.sh` de la aplicación levante Gunicorn en el puerto 8080. La inicialización de la tabla de reservas ocurre automáticamente en el primer arranque mediante el archivo `init.sql` montado en el contenedor de PostgreSQL.

## 2. Contrato de rutas del servicio

El servicio expone una entidad de dominio (Reserva). Las rutas de escritura y eliminación están protegidas y exigen un token JWT emitido por Keycloak.

### Rutas públicas (liveness y readiness)

**`GET /health`** — Comprueba que el proceso está vivo sin consultar la base de datos.
- Respuesta: `200 OK` con el cuerpo `{"status": "ok"}`.

**`GET /ready`** — Verifica la disponibilidad de la conexión con PostgreSQL.
- Respuesta: `200 OK` (disponible) o `503 Service Unavailable` (no disponible).

### Rutas de la entidad (CRUD de reservas)

**`POST /reservas`** *(protegida — rol `admin`)* — Crea una nueva reserva.
- Cuerpo esperado:
  ```json
  {"nombre": "Cliente", "fecha": "2026-12-24", "hora": "20:00", "cantidad": 4}
  ```
- Respuesta exitosa: `201 Created` con el JSON de la reserva creada (incluye el ID generado).
- Errores: `400 Bad Request` si falta un campo o el formato es inválido.

**`GET /reservas`** *(pública)* — Lista las reservas almacenadas. Admite un filtro opcional por parámetro de consulta.
- Ejemplo de uso: `/reservas?fecha=2026-12-24`
- Respuesta: `200 OK` con un arreglo JSON de reservas.

**`GET /reservas/<id>`** *(pública)* — Consulta una reserva por su identificador único.
- Respuesta: `200 OK` con el JSON de la reserva, o `404 Not Found` si no existe.

**`PUT /reservas/<id>`** *(protegida — rol `admin`)* — Actualiza íntegramente una reserva existente.
- Cuerpo esperado: igual al método `POST`.
- Respuesta exitosa: `200 OK` con el recurso actualizado.
- Errores: `400 Bad Request` ante cuerpo inválido, `404 Not Found` si el ID no existe.

**`DELETE /reservas/<id>`** *(protegida — rol `admin`)* — Elimina una reserva del sistema.
- Respuesta: `204 No Content` sin cuerpo, o `404 Not Found` si no existe.

### Autenticación y manejo de errores

Las rutas protegidas responden con `401 Unauthorized` si el token falta o es inválido, y con `403 Forbidden` si el token es válido pero el usuario carece del rol exigido. El servicio permanece operativo ante entradas mal formadas (`400`).

## 3. Pruebas automatizadas

El proyecto incluye pruebas unitarias (para la validación aislada del modelo) y pruebas de integración (que ejercitan los endpoints contra la base de datos y Keycloak). Los scripts de prueba viajan empaquetados dentro de la imagen de la aplicación para evitar dependencias locales.

Para ejecutar toda la suite de forma automatizada:

```bash
docker compose exec app pytest
```

## 4. Comprobación de persistencia y apagado

Los datos de la base de datos residen en el volumen nombrado `volumen_de_postgres` declarado en Docker Compose. Para verificar la persistencia de la información:

1. Inserte un registro mediante la ruta de escritura (`POST /reservas`).
2. Apague los contenedores sin destruir los volúmenes:
   ```bash
   docker compose down
   ```
3. Vuelva a levantar el sistema y lea los datos a través de la ruta de lectura:
   ```bash
   docker compose up -d
   curl -i http://localhost:8080/reservas
   ```

Para apagar el sistema y eliminar definitivamente los volúmenes y la red:

```bash
docker compose down -v
```

## 5. Justificación de decisiones técnicas

**Selección de la imagen base.** Se optó por `python:3.13-slim` (basada en Debian) en lugar de una variante Alpine. Esto se debe a que la instalación del controlador `psycopg` en Alpine requeriría instalar compiladores de C y librerías de desarrollo (`gcc`, `libpq-dev`), lo que inflaría el tamaño de la imagen e incumpliría el principio de instalar únicamente lo necesario.

**Dependencia y arranque ordenado.** Se implementó una estrategia de doble capa para garantizar que la aplicación no se declare lista antes que sus dependencias:
- La instrucción `depends_on` con la condición `service_healthy` en Compose, evaluando los healthchecks de PostgreSQL (`pg_isready`) y Keycloak (petición TCP al puerto 8080).
- El script `entrypoint.sh`, que efectúa reintentos activos de conexión contra la base de datos utilizando `psycopg` antes de ceder el control del proceso principal a Gunicorn mediante `exec "$@"`.

**Gestión de configuración y secretos.** Las credenciales, el host y el puerto se inyectan a los contenedores como variables de entorno a través del archivo `.env`. No existen contraseñas quemadas en los archivos de configuración ni en el código fuente.

**Exclusión de archivos y pruebas en el contenedor.** Mediante `.dockerignore` se evita copiar historiales de Git o entornos virtuales. La inclusión de la carpeta `tests` dentro de la imagen se realizó de manera deliberada para cumplir con el requisito de ejecución de pruebas mediante un solo comando automatizado (`docker compose exec app pytest`), evitando que el evaluador instale dependencias en el sistema anfitrión.
