# `realm-export.json` — qué es cada bloque

JSON no admite comentarios, así que la explicación del archivo vive acá al
lado. Keycloak lo importa solo al arrancar (ver `--import-realm` y el bind
mount en `compose.yml`) — nadie tiene que configurar nada a mano desde la
consola.

## `realm` / `enabled` / `sslRequired` / `registrationAllowed`

Define un realm propio llamado `bases2` (un espacio aislado dentro de
Keycloak, con sus propios usuarios/roles/clients — no usamos el realm
`master`, ese es para administrar Keycloak mismo). `sslRequired: "none"`
desactiva la exigencia de HTTPS: para el alcance de esta tarea corremos todo
en HTTP local, y en producción real esto se pondría en `"external"` o
`"all"`. `registrationAllowed: false` porque los usuarios los define el
propio `realm-export.json` (fixtures de prueba), no hace falta que cualquiera
se pueda registrar solo.

## `roles.realm`

Un único rol, `admin`. Es el rol que la app exige (chequeo de 403) en las
rutas de crear/actualizar/eliminar. Vive a nivel de realm, no de client,
porque no necesitamos roles distintos por aplicación en este alcance.

## `users`

Dos usuarios de prueba (fixtures, no datos reales — por eso las contraseñas
están a la vista, documentado también en el README principal):

- **`admin-tester`**: tiene el rol `admin`. Sirve para probar el camino
  feliz de las rutas protegidas (200/201/204).
- **`sin-rol-tester`**: sin roles. Sirve para probar el 403 — un token
  válido (la firma y el login son correctos) pero sin el permiso requerido.

Ambos están para que los tests de integración puedan pedir tokens de forma
automática, sin que un humano tenga que loguearse a mano en un navegador.

## `clients`

Un único client, `comidas-api`, que representa a nuestro backend Flask ante
Keycloak:

- **`publicClient: false`** + **`secret`**: es un client *confidencial* (tiene
  contraseña propia, `client-secret`). Se usa así porque quien pide tokens es
  un backend/tests de confianza, no una SPA en el navegador (que no podría
  guardar un secreto de forma segura).
- **`directAccessGrantsEnabled: true`**: habilita el flujo "usuario +
  contraseña → token" (Resource Owner Password Credentials) contra el
  endpoint de token de Keycloak. Es lo que usan los tests de integración para
  conseguir un JWT sin pasar por una pantalla de login.
- **`standardFlowEnabled: false`** / **`implicitFlowEnabled: false`**: no
  usamos el flujo de login por navegador (Authorization Code), así que los
  desactivamos — no hace falta y reduce superficie de configuración
  (`redirectUris` queda vacío por lo mismo).
- **`serviceAccountsEnabled: false`**: no necesitamos que el client mismo
  actúe como un "usuario máquina" (Client Credentials Grant); los tokens
  siempre representan a un usuario real (`admin-tester` o `sin-rol-tester`).

## Dato importante para `auth.py` y los tests

El claim `iss` (issuer) de cualquier token que emita Keycloak depende de la
URL con la que se pidió ese token, no es un valor fijo en este archivo.
Tanto `auth.py` como los tests de integración corren *dentro* de la red de
Docker, así que siempre tienen que hablar con Keycloak como
`http://keycloak:8080` (variable `KEYCLOAK_URL` en `.env`), nunca como
`http://localhost:8090` (ese puerto es solo para que un humano entre a la
consola de administración desde su navegador) — si se mezclan las dos URLs,
el `iss` del token no va a coincidir con lo que la app espera validar, y la
verificación de la firma va a fallar aunque el token sea perfectamente
válido.
