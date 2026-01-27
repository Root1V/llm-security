# LLM Security Gateway

**Sistema de autenticación y autorización centralizado para modelos de lenguaje (LLM) desplegados localmente.**

Este módulo actúa como gateway de seguridad que valida y autoriza las aplicaciones antes de permitirles consumir modelos LLM locales. Proporciona autenticación basada en roles, gestión de tokens JWT con TTL diferenciado y validación mediante endpoints para integración con proxies inversos como NGINX.

---

## 🎯 Objetivo

Proveer una capa de seguridad robusta que:
- **Autentica** aplicaciones y agentes antes de acceder a modelos LLM
- **Autoriza** acceso basado en roles con diferentes niveles de privilegios
- **Gestiona** tokens JWT con tiempo de vida (TTL) personalizado por rol
- **Valida** requests en tiempo real para proxies como NGINX
- **Protege** recursos computacionales costosos (modelos LLM) de accesos no autorizados

---

## 🏗️ Arquitectura de la Solución

### Diagrama de Componentes

```
                    ┌──────────────────────────────────┐
                    │     CLIENTES / CONSUMIDORES      │
                    │  (Agentes IA, Apps, Usuarios)    │
                    └────────────────┬─────────────────┘
                                     │
                                     │ 
                                     │ (login , requests)
                                     │
                    ┌────────────────▼─────────────────┐
                    │                                  │
                    │        NGINX / PROXY             │
                    │   (Reverse Proxy Gateway)        │
                    │     🔒 Punto de entrada único    │
                    │                                  │
                    │  ┌────────────────────────────┐  │
                    │  │  Login: proxy_pass a Auth  │  │
                    │  │  Requests: auth_request +  │  │
                    │  │            proxy_pass LLM  │  │
                    │  └────────────────────────────┘  │
                    └─────┬──────────────────────┬─────┘
                          │                      │
                  Proxy/Subrequest               │ Proxy Pass
                  (Auth/Validación)              │ (a LLM Server)
                          │                      │
              ┌───────────▼──────────┐           │
              │                      │           │
              │  LLM Security API    │           │
              │  (Auth Backend)      │           │
              │   Port: 9000         │           │
              │                      │           │
              │  ┌────────────────┐  │           │
              │  │ POST /llm/login│  │           │
              │  │ POST /login    │  │           │
              │  │ POST /validate │  │           │
              │  │                │  │           │
              │  │ Token Cache    │  │           │
              │  │ Role RBAC      │  │           │
              │  └────────────────┘  │           │
              │                      │           │
              └──────────────────────┘           │
                                                 │
                                ┌────────────────▼─────────────────┐
                                │                                  │
                                │         LLM SERVER(S)            │
                                │   (Ollama, vLLM, LocalAI)        │
                                │                                  │
                                └──────────────────────────────────┘
```

---

### Flujos de Secuencia

#### **Flujo 1: Login / Autenticación (obtener token)**

```sequence
┌─────────┐       ┌─────────┐       ┌──────────┐
│ Cliente │       │  NGINX  │       │ Auth API │
└────┬────┘       └────┬────┘       └────┬─────┘
     │                 │                  │
     │  1. POST /auth/llm/login           │
     │     Basic Auth                     │
     │     (username:password)            │
     ├────────────────►│                  │
     │                 │                  │
     │                 │  2. proxy_pass   │
     │                 │     (forward)    │
     │                 ├─────────────────►│
     │                 │                  │
     │                 │                  │ 3. Verifica:
     │                 │                  │    • Credenciales
     │                 │                  │    • Role válido
     │                 │                  │ 4. Genera JWT
     │                 │                  │ 5. Cache token
     │                 │                  │
     │                 │  6. 200 OK       │
     │                 │     {token, exp} │
     │                 │◄─────────────────┤
     │                 │                  │
     │  7. 200 OK      │                  │
     │     Token JWT   │                  │
     │◄────────────────┤                  │
     │                 │                  │
     │ ✅ Cliente guarda token            │
     │                 │                  │
```

#### **Flujo 2: Request a LLM con Token Válido**

```sequence
┌─────────┐       ┌─────────┐       ┌──────────┐       ┌──────────┐
│ Cliente │       │  NGINX  │       │ Auth API │       │ LLM Server│
└────┬────┘       └────┬────┘       └────┬─────┘       └────┬─────┘
     │                 │                  │                  │
     │  1. GET /llm/chat                  │                  │
     │     Bearer: <token>                │                  │
     ├────────────────►│                  │                  │
     │                 │                  │                  │
     │                 │  2. INTERCEPTA   │                  │
     │                 │     auth_request │                  │
     │                 │     (subrequest) │                  │
     │                 │                  │                  │
     │                 │  3. POST /validate                  │
     │                 │     {token: "..."}                  │
     │                 ├─────────────────►│                  │
     │                 │                  │                  │
     │                 │                  │ 4. Verifica:     │
     │                 │                  │    • JWT válido  │
     │                 │                  │    • En cache    │
     │                 │                  │    • No expirado │
     │                 │                  │                  │
     │                 │  5. 200 OK       │                  │
     │                 │     {valid: true}│                  │
     │                 │◄─────────────────┤                  │
     │                 │                  │                  │
     │                 │  6. proxy_pass (forward request)    │
     │                 ├────────────────────────────────────►│
     │                 │                  │                  │
     │                 │                  │   7. Procesa LLM │
     │                 │                  │                  │
     │                 │  8. LLM Response                    │
     │                 │◄────────────────────────────────────┤
     │                 │                  │                  │
     │  9. Response    │                  │                  │
     │◄────────────────┤                  │                  │
     │                 │                  │                  │
```

#### **Flujo 3: Request con Token Inválido/Expirado**

```sequence
┌─────────┐       ┌─────────┐       ┌──────────┐
│ Cliente │       │  NGINX  │       │ Auth API │
└────┬────┘       └────┬────┘       └────┬─────┘
     │                 │                  │
     │  1. GET /llm/chat                  │
     │     Bearer: <bad_token>            │
     ├────────────────►│                  │
     │                 │                  │
     │                 │  2. auth_request │
     │                 │     POST /validate                  
     │                 │     {token: "bad"}                  
     │                 ├─────────────────►│
     │                 │                  │
     │                 │                  │ 3. Token:
     │                 │                  │    • Inválido
     │                 │                  │    • O expirado
     │                 │                  │    • No en cache
     │                 │                  │
     │                 │  4. 401          │
     │                 │     {valid: false}
     │                 │◄─────────────────┤
     │                 │                  │
     │  5. 401         │                  │
     │  Unauthorized   │                  │
     │◄────────────────┤                  │
     │                 │                  │
     │ ❌ NO llega al LLM Server          │
     │ ⚠️  Debe hacer login nuevamente    │
     │                 │                  │
```

---

### Notas de Arquitectura

**🔑 Puntos Clave:**

1. **NGINX como Gateway Único**: Todos los clientes se conectan únicamente a NGINX, nunca directamente al Auth API o LLM Server

2. **Interceptación Transparente**: NGINX usa `auth_request` para validar cada petición antes de hacer proxy al LLM

3. **Validación Centralizada**: Auth API solo expone `/validate` para NGINX, no para clientes directos

4. **Protección del LLM**: El servidor LLM nunca está expuesto directamente, solo accesible vía NGINX con token válido

5. **Separación de Responsabilidades**:
   - **NGINX**: Gateway, routing, validación de requests
   - **Auth API**: Autenticación, generación/validación de tokens
   - **LLM Server**: Procesamiento de modelos (protegido)

---

### 🔌 SDK para Clientes

**Para facilitar la integración con este sistema de seguridad, existe un SDK oficial:**

📦 **[LLM Architecture SDK](https://github.com/Root1V/llm-arch-sdk.git)**

Este SDK maneja automáticamente:
- ✅ **Autenticación** con el Auth Gateway
- ✅ **Gestión de tokens JWT** (obtención, renovación, caché)
- ✅ **Renovación automática** de tokens expirados
- ✅ **Manejo de errores** de autenticación
- ✅ **Conexión simplificada** al LLM Server vía NGINX

**Instalación:**
```bash
pip install git+https://github.com/Root1V/llm-arch-sdk.git
```

**📖 Ejemplo de Uso:**

Para ver ejemplos completos de integración y uso del SDK, consulta el proyecto de ejemplo:

👉 **[LLM SDK Client - Proyecto de Ejemplo](https://github.com/Root1V/llm-sdk-client.git)**

Este repositorio contiene ejemplos prácticos de:
- Configuración del cliente con el SDK
- Autenticación y gestión de tokens
- Diferentes patrones de uso (agentes, usuarios, monitoring)
- Manejo de errores y reintentos
- Integración en aplicaciones reales

El SDK abstrae toda la complejidad del flujo de autenticación, gestión de tokens y comunicación con el gateway, permitiendo a los desarrolladores enfocarse en la lógica de su aplicación.

---

## 👥 Sistema de Roles

| Rol | Código | TTL Token | Uso |
|-----|--------|-----------|-----|
| **Agent Reasoning** | `AGNR` | 2 min | Agentes con razonamiento complejo |
| **Agent Fast** | `AGNF` | 1 min | Agentes de respuesta rápida |
| **AGI** | `AGIA` | 30 min | Sistemas AGI avanzados |
| **User** | `USRS` | 15 min | Usuarios web estándar |
| **Monitoring** | `MNTR` | 20 min | Sistemas de monitoreo |
| **Admin** | `ADMN` | 60 min | Administradores |

---

## 🚀 Inicio Rápido

### 1. Instalación

```bash
# Clonar el repositorio
git clone https://github.com/Root1V/llm-security.git
cd llm_security

# Instalar dependencias con uv
uv sync
```

### 2. Configuración

Crear archivo `.env` con las credenciales de usuarios:

```bash
# Formato: USERNAME=PASSWORD
USRS123ABC=password123
AGNRXYZ456=agentpass456
MNTR789DEF=monitorpass789
```

### 3. Ejecutar el servidor

```bash
uv run dev
```

El servidor estará disponible en: `http://0.0.0.0:9000`

---

## 📡 Endpoints API

### `POST /llm/login`
Autenticación para agentes IA (HTTP Basic Auth)

**Roles permitidos:** `agent_reasoning`, `agent_fast`

**Request:**
```bash
curl -X POST http://localhost:9000/llm/login \
  -u "AGNRXYZ456:agentpass456"
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 1706294400
}
```

### `POST /login`
Login web para usuarios (Form-based)

**Roles permitidos:** `user`, `monitoring`

**Request:**
```bash
curl -X POST http://localhost:9000/login \
  -d "username=USRS123ABC&password=password123"
```

**Response:** Redirección con cookie `auth_token`

### `POST /validate`
Validación de token para NGINX/Proxy

**Request:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response:**
```json
{
  "valid": true
}
```

---

## 🔧 Configuración Avanzada

### Variables de entorno (`.env`)

```bash

# Configuración JWT (opcional en settings.env)
SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
TOKEN_CACHE_SIZE=100
TOKEN_TTL_SECONDS=3600
```

### Generación de credenciales

El sistema incluye una utilidad para generar usuarios y contraseñas:

```bash
uv run python -m security.credentials --generate 5
```

Genera 5 usuarios por cada rol con contraseñas seguras aleatorias.

---

## 📦 Estructura del Proyecto

```
llm_security/
├── api/                    # Rutas y endpoints
│   └── auth_routes.py     # Endpoints de autenticación
├── core/                   # Configuración central
│   ├── config.py          # Settings con Pydantic
│   └── dependecies.py     # Inyección de dependencias
├── security/               # Lógica de seguridad
│   ├── auth.py            # Validación de credenciales
│   ├── tokens.py          # Generación y validación JWT
│   └── credentials.py     # Gestión de usuarios
├── scripts/                # Scripts de automatización
│   ├── dev.py             # Script de desarrollo
│   └── start.py           # Script de producción
├── utils/                  # Utilidades
│   └── logging_config.py  # Configuración de logs
├── main.py                 # Punto de entrada FastAPI
├── pyproject.toml         # Configuración del proyecto
└── .env                    # Credenciales (no versionado)
```

---

## 🛠️ Tecnologías

- **FastAPI** - Framework web de alto rendimiento
- **Uvicorn** - Servidor ASGI
- **PyJWT** - Gestión de tokens JWT
- **Bcrypt** - Hashing de contraseñas
- **Cachetools** - Cache de tokens en memoria
- **Pydantic** - Validación de configuración
- **uv** - Gestor de paquetes y entornos Python

---

## 🔒 Seguridad

- ✅ Autenticación HTTP Basic para agentes
- ✅ Tokens JWT firmados con HS256
- ✅ TTL diferenciado por rol
- ✅ Cache de tokens con expiración automática
- ✅ Validación de contraseñas con timing-safe comparison
- ✅ Logs detallados de autenticación
- ⚠️ En producción: habilitar HTTPS y cookies seguras

---

## 📝 Comandos Útiles

```bash
# Desarrollo
uv run dev              # Servidor con auto-reload

# Producción
uv run start            # Servidor sin auto-reload

# Gestión
uv sync                 # Sincronizar dependencias
uv add <paquete>        # Agregar nueva dependencia
```

---

## 🔗 Integración con NGINX

Ejemplo de configuración NGINX para validar tokens:

```nginx
location /llm/ {
    auth_request /auth-validate;
    proxy_pass http://llm-backend:8000/;
}

location = /auth-validate {
    internal;
    proxy_pass http://localhost:9000/validate;
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_set_header X-Original-URI $request_uri;
}
```

---

## 📄 Licencia

**Licencia de Libre Uso (Free License)**

Este proyecto está disponible bajo una licencia de libre uso. Puedes:
- ✅ Usar el software libremente para cualquier propósito
- ✅ Modificar el código fuente según tus necesidades
- ✅ Distribuir copias del software
- ✅ Usar en proyectos comerciales y no comerciales

No se proporciona ninguna garantía. El software se distribuye "tal cual", sin garantías de ningún tipo.

## 👨‍💻 Autor

**Emerice Espiritu Santiago**

- GitHub: [@Root1V](https://github.com/Root1V)
- Proyecto: [llm-security](https://github.com/Root1V/llm-security)

---

**Proyectos Relacionados:**
- [LLM Architecture SDK](https://github.com/Root1V/llm-arch-sdk) - SDK oficial para clientes
- [LLM SDK Client](https://github.com/Root1V/llm-sdk-client) - Ejemplos de uso del SDK
