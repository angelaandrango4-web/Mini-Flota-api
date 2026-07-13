# Mini Flota API

API REST desarrollada con **FastAPI** para la gestión de vehículos y conductores.

El proyecto implementa autenticación mediante JWT, operaciones CRUD sobre vehículos y la asignación de conductores, utilizando MongoDB como base de datos.

| Información            | Detalle     |
| ---------------------- | ----------- |
| Lenguaje               | Python 3.12 |
| Framework              | FastAPI     |
| Base de datos          | MongoDB     |
| Contenedor             | Docker      |
| Gestor de dependencias | Poetry      |
| Autenticación          | JWT         |
| Documentación          | Swagger     |
| Arquitectura           | API REST    |



---

## Tecnologías utilizadas

- Python 3.12
- FastAPI
- MongoDB
- Motor, como controlador asíncrono para MongoDB
- Pydantic v2
- Poetry
- JWT
- bcrypt
- pytest
- Docker

---

## Arquitectura

El proyecto sigue una arquitectura por capas para separar responsabilidades.

```text
app/
├── api/          # Endpoints HTTP
├── schemas/      # Validación de datos con Pydantic
├── services/     # Lógica de negocio
├── database.py   # Conexión con MongoDB
├── config.py     # Configuración del proyecto
└── main.py       # Punto de entrada de la aplicación
```

### Responsabilidad de cada capa

- **Endpoints:** reciben las solicitudes HTTP y devuelven las respuestas.
- **Schemas:** validan la información recibida y enviada.
- **Services:** contienen la lógica de negocio.
- **Database:** administra la conexión con MongoDB.
- **Config:** carga la configuración y las variables de entorno.
- **Main:** crea la aplicación, registra los routers y configura los middlewares.

---

## Requisitos

Antes de ejecutar el proyecto, asegúrate de tener instalado:

- Python 3.12 o superior
- Poetry
- Docker
- Git

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/angelaandrango4-web/Mini-Flota-api
```

Entrar al proyecto:

```bash
cd mini-flota-api
```

---

### 2. Instalar las dependencias

```bash
poetry install
```

---

### 3. Configurar las variables de entorno

Crear un archivo llamado `.env` en la raíz del proyecto.

```env
MONGODB_URL=mongodb://localhost:27017
SECRET_KEY=tu_clave_secreta
```

> Los nombres de las variables deben coincidir exactamente con los definidos en `app/config.py`.

El archivo `.env` contiene información sensible y no debe subirse al repositorio.

---

### 4. Base de datos

Este proyecto utiliza **MongoDB** como base de datos.

Durante el desarrollo, MongoDB se ejecutó mediante un contenedor de **Docker**, por lo que no es necesario instalar MongoDB directamente en el sistema operativo.

#### Crear el contenedor por primera vez

```bash
docker run -d \
  --name mini-flota-mongo \
  -p 27017:27017 \
  mongo
```

#### Iniciar un contenedor existente

Si el contenedor ya fue creado anteriormente, solo es necesario iniciarlo:

```bash
docker start mini-flota-mongo
```

#### Verificar que MongoDB esté ejecutándose

```bash
docker ps
```

Debe aparecer un contenedor llamado:

```text
mini-flota-mongo
```

con el puerto:

```text
27017
```

---

### 5. Configuración de CORS

El backend está configurado para aceptar solicitudes desde el frontend ejecutado en:

```text
http://localhost:5173
http://127.0.0.1:5173
```

Esta configuración se encuentra en `app/main.py` mediante `CORSMiddleware`.

Si el frontend se ejecuta desde otro dominio o puerto, se deberá agregar el nuevo origen dentro de la lista:

```python
allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
```

Actualmente, los orígenes permitidos no se cargan desde variables de entorno.

---

### 6. Instalar el hook de pre-commit

El proyecto utiliza Conventional Commits para mantener un historial de cambios consistente.

```bash
poetry run pre-commit install
```

Este paso configura las validaciones locales asociadas al repositorio.

---

### 7. Ejecutar la aplicación

```bash
poetry run uvicorn app.main:app --reload
```

La API estará disponible en:

```text
http://127.0.0.1:8000
```

La documentación interactiva de Swagger estará disponible en:

```text
http://127.0.0.1:8000/docs
```

El endpoint de comprobación de estado estará disponible en:

```text
http://127.0.0.1:8000/health
```

---

## Funcionalidades

### Autenticación

- Inicio de sesión mediante JWT.
- Contraseñas protegidas mediante hash con bcrypt.
- Protección de endpoints mediante Bearer Token.
- Validación de credenciales.
- Tokens con tiempo de expiración.

### Vehículos

- Crear un vehículo.
- Listar vehículos.
- Obtener un vehículo por ID.
- Actualizar un vehículo.
- Eliminar un vehículo.
- Validar el formato de la placa.
- Validar el año del vehículo.
- Validar la capacidad de carga.
- Controlar placas duplicadas mediante un índice único.

### Conductores

- Crear un conductor.
- Listar conductores.
- Validar licencias duplicadas.
- Asignar un conductor a un vehículo.
- Cambiar el conductor asignado a un vehículo.
- Impedir que un conductor sea asignado simultáneamente a dos vehículos.

---

## Endpoints principales

### Autenticación

```text
POST /auth/login
```

### Vehículos

```text
POST   /vehicles
GET    /vehicles
GET    /vehicles/{vehicle_id}
PUT    /vehicles/{vehicle_id}
DELETE /vehicles/{vehicle_id}
PATCH  /vehicles/{vehicle_id}/assign-driver
```

### Conductores

```text
POST /drivers
GET  /drivers
```

### Estado de la API

```text
GET /health
```

---

## Decisiones técnicas

### Separación de entidades

Los conductores se almacenan en una colección independiente de MongoDB.

Los vehículos almacenan únicamente una referencia al conductor mediante el campo:

```text
driver_id
```

Esto evita duplicar el nombre y la licencia del conductor dentro de cada vehículo.

También permite que un conductor exista independientemente de su asignación actual y pueda ser reasignado posteriormente.

---

### Uso de ObjectId

MongoDB guarda los identificadores internos de vehículos y conductores como `ObjectId`.

Los identificadores recibidos mediante la API se convierten desde texto antes de realizar consultas en MongoDB.

El campo `driver_id` también se almacena como `ObjectId`.

---

### Enriquecimiento de respuestas

MongoDB almacena únicamente la referencia `driver_id` dentro del documento del vehículo.

Al listar u obtener vehículos, el backend busca el conductor relacionado y construye una respuesta enriquecida:

```json
{
  "driver": {
    "id": "...",
    "name": "Juan Pérez",
    "license": "LIC-12345"
  }
}
```

De esta forma, el frontend recibe los datos completos y no necesita realizar una consulta adicional para mostrar el nombre del conductor.

Si un `driver_id` apunta a un conductor inexistente, la API devuelve:

```json
{
  "driver": null
}
```

Esto evita que una referencia inconsistente rompa la lista completa de vehículos.

---

### Restricción de asignación

Un conductor solamente puede estar asignado a un vehículo al mismo tiempo.

Al intentar asignar un conductor que ya pertenece a otro vehículo, la API responde con:

```text
400 Bad Request
```

La validación excluye al vehículo actual, lo que permite conservar o reasignar el mismo conductor al mismo vehículo sin producir un falso conflicto.

---

### Cambio de conductor

Un vehículo puede cambiar de conductor.

Cuando se asigna un nuevo conductor, el valor anterior de `driver_id` es reemplazado.

El conductor anterior queda disponible automáticamente para una asignación posterior.

En esta versión no se implementó una operación de desasignación sin reemplazo.

---

### Índices únicos

Se utilizan índices únicos en MongoDB para evitar datos duplicados en:

- `plate`, dentro de la colección de vehículos.
- `license`, dentro de la colección de conductores.

Los índices se crean durante el inicio de la aplicación mediante el ciclo de vida de FastAPI.

---

### Hash de contraseñas

Se utiliza **bcrypt** directamente para generar y verificar el hash de las contraseñas.

Inicialmente se evaluó el uso de **passlib**, pero se descartó debido a problemas de compatibilidad con versiones recientes de bcrypt.

Esta decisión evita errores relacionados con la detección de versiones y mantiene el flujo de autenticación funcionando de forma estable.

---

### Operaciones asíncronas

Las consultas a MongoDB se realizan de forma asíncrona mediante Motor.

Esto permite que FastAPI atienda otras solicitudes mientras espera las respuestas de la base de datos.

---

### Enriquecimiento individual

En esta primera versión, el backend realiza una consulta individual para obtener el conductor relacionado con cada vehículo.

Se priorizó la claridad y facilidad de explicación del código.

Como mejora futura, este proceso puede optimizarse mediante:

- consultas con `$in`;
- agregaciones con `$lookup`;
- construcción de un diccionario de conductores en memoria.

---

## Pruebas

Para ejecutar las pruebas automatizadas:

```bash
poetry run pytest
```

Las pruebas deben ejecutarse sin depender de una base de datos real cuando se utilicen mocks.

También se recomienda verificar manualmente los endpoints desde Swagger:

```text
http://127.0.0.1:8000/docs
```

Casos principales de comprobación:

- inicio de sesión correcto;
- credenciales incorrectas;
- creación de vehículos;
- placa duplicada;
- validaciones de vehículos;
- creación de conductores;
- licencia duplicada;
- asignación de conductor;
- intento de asignar un conductor ocupado;
- cambio de conductor;
- consulta de vehículos con conductor enriquecido.

---

## Estado del proyecto

Proyecto desarrollado como parte de las prácticas preprofesionales, con el objetivo de fortalecer conocimientos en desarrollo backend utilizando FastAPI, MongoDB y arquitecturas basadas en APIs REST.

Estado actual:

- Autenticación JWT implementada.
- CRUD de vehículos implementado.
- Gestión básica de conductores implementada.
- Asignación de conductores implementada.
- Validaciones de negocio implementadas.
- Integración con MongoDB mediante Docker.
- Documentación interactiva disponible mediante Swagger.
- Backend preparado para trabajar con el frontend de Mini Flota.

---
## Flujo de contribución

El proyecto sigue un flujo de trabajo basado en ramas para mantener un desarrollo organizado.

### Creación de nuevas funcionalidades

1. Actualizar la rama `qa`.
2. Crear una nueva rama de trabajo a partir de `qa`.

```bash
git switch qa
git pull origin qa

git switch -c feat/nombre-funcionalidad
```

3. Desarrollar la funcionalidad en la rama creada.
4. Realizar commits utilizando el estándar **Conventional Commits**.
5. Subir la rama al repositorio remoto.
6. Abrir un Pull Request hacia `qa`.
7. Una vez aprobada e integrada en `qa`, abrir un Pull Request de `qa` hacia `main`.

### Convención de commits

Algunos ejemplos utilizados en este proyecto son:

```text
feat: agregar asignación de conductores
fix: corregir validación de placas
docs: actualizar README
refactor: mejorar experiencia de asignación de conductores
test: agregar pruebas de autenticación
chore: actualizar dependencias
```

El proyecto utiliza **pre-commit** para validar automáticamente el formato de los mensajes de commit.

---
## Mejoras futuras

- Editar conductores.
- Eliminar conductores.
- Desasignar un conductor sin reemplazarlo.
- Implementar historial de asignaciones.
- Agregar fechas de inicio y finalización de cada asignación.
- Optimizar el enriquecimiento mediante `$lookup` o consultas agrupadas.
- Incrementar la cobertura de pruebas automatizadas.
- Mover los orígenes CORS a variables de entorno.
- Implementar paginación para vehículos y conductores.
- Agregar roles y permisos de usuario.
- Mejorar el manejo centralizado de errores.

---

## Proyecto relacionado

Este backend trabaja junto con el frontend de Mini Flota:

```text
mini-flota-web
```

Repositorio del frontend:

```text
https://github.com/angelaandrango4-web/Mini-flota-web
```

Ambos repositorios fueron desarrollados para trabajar de forma conjunta.

---

## Autor

Proyecto desarrollado por Angela Andrango como parte de sus prácticas preprofesionales.