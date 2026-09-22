# Aquí se tiene que poner en todo lo que se usó la IA en esta tarea corta
1. Inicialmente se uso para la division del trabajo de forma equitativa en 2 roles, la persona A (Andres Baldi) la cual es la encargada de la lógica de negocio: el modelo de Reserva, el acceso a PostgreSQL y las rutas CRUD, mientras que la persona B (Andrey Jimenez) es la encargada del empaquetado en Docker, autenticación vía Keycloak, tests de integración y el README final.
Esto no significa que cada uno haga su parte de forma totalmente independiente, acordamos en explicar la parte de cada uno a la otra persona gradualmente para que ambors reforcemos nuestro aprendizaje y que genuinamente no dependamos de la IA


2. con respecto al docker compose, cuando se estaba probando al inicio se le pidio a Claude los comandos en consola para comprobar si funcionalidades, como por ejemplo para ver que el volumen persista los datos guardados despues de meter un registro, bajando el contenedor y volviendolo a levantar 


3. Para empezar la tarea corta le pedimos a Claude code que nos fuera dando indicaciones de donde empezar para no estar tan "perdidos", no le pedimos que escribiera una linea de codigo, solo que nos fuera describiendo lo que hay que hacer con ciertas pistas para ayudarnos y tratar de hacerlo a mano.

Ya en todo caso de que al hacerlo a mano no nos sirviese y tampoco investigando en internet, le pedimos a claude una ayuda parcial para seguir avanzando, como por ejemplo en el siguiente fragmento donde se intento hacer una parte y Claude nos dio retroalimentacion:



Vas bien: DB_HOST=db correcto (coincide con el nombre del servicio), DB_PORT=5432 correcto (puerto interno real de Postgres, el que usan los contenedores entre sí — con razón lo devolviste a como estaba). Y las variables ${...} en el environment: quedaron exactamente como debían.

Sobre el volumen: tu intento tiene dos problemas de sintaxis, no de concepto — vas bien encaminado.

Volume: con mayúscula — YAML es sensible a mayúsculas, y Docker Compose busca exactamente la clave volumes: (plural, minúscula). Con Volume: Compose simplemente lo ignora, no da error, pero tampoco hace nada.

Le falta contenido — bajo volumes: a nivel raíz, tienes que darle un nombre al volumen (tú lo inventas, ej. postgres_data), así:


volumes:
  postgres_data:
Eso solo lo declara. Falta la segunda mitad: decirle al servicio db que use ese volumen, montándolo en la carpeta donde Postgres realmente escribe sus datos dentro del contenedor (/var/lib/postgresql/data). Eso va en una lista volumes: dentro del servicio db, con la sintaxis nombre_del_volumen:ruta_dentro_del_contenedor.

¿Te animas a escribir esa lista dentro de db: tú mismo, usando ese patrón? Como pista extra: en ese mismo bloque volumes: del servicio db es también donde vas a agregar, en otra línea, el montaje de tu init.sql que vimos antes — así que ese bloque va a tener dos líneas al final, una para los datos persistentes y otra para el script de inicialización.

Una cosa más para que la revises con calma: las líneas comentadas de shm_size y tmpfs que vienen del ejemplo de Docker Hub — la consigna exige que puedan justificar cada instrucción que dejen en el archivo. shm_size: 128mb en particular sí está activa (no comentada). ¿Sabes para qué sirve, o prefieres que te explique qué hace y decides si les sirve o si es ruido que conviene borrar?


4. Para la parte de Andrey (Persona B: Docker, Keycloak, tests de integración, README), se siguió la misma dinámica que en el punto 3, pero de forma más sostenida a lo largo de varias sesiones: antes de escribir cualquier archivo (Dockerfile, .dockerignore, requirements.txt, entrypoint.sh) se le pidió a Claude que explicara las decisiones de diseño en juego con sus ventajas y desventajas (por ejemplo: imagen base slim vs. alpine, psycopg2 vs. psycopg3, PyJWT+cryptography vs. python-jose vs. Authlib, orden de las capas del Dockerfile para el cacheo, por qué separar ENTRYPOINT de CMD), y Andrey tomaba la decisión final y escribía el archivo a mano. Claude revisó cada intento y señaló errores puntuales sin corregirlos directamente (por ejemplo: un COPY con una ruta que no existía en el build context, una mezcla de ASGI/uvicorn con un framework WSGI como Flask, dos instrucciones ENTRYPOINT donde la segunda pisaba a la primera, y un CMD/ENTRYPOINT invertidos), dejando que Andrey volviera a intentarlo hasta llegar a la versión correcta. Al final se verificó de forma manual y real que lo escrito funcionara: se corrió `docker build` sobre la imagen de la app y se confirmó que compilaba sin errores antes de seguir avanzando. Las versiones exactas fijadas en requirements.txt también se comprobaron así, instalándose sin conflictos.