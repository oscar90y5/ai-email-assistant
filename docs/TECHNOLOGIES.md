# Decisiones tecnológicas

## Stack principal

| Componente | Tecnología | Notas |
|---|---|---|
| Backend / ORM | Django | Modelos, admin, gestión de configuración |
| Orquestación LLM | LangChain | Agente que clasifica y decide acciones sobre emails |
| LLM | Groq (modelos gratuitos) | Inferencia rápida y gratuita vía LangChain |
| Email | Google Gmail API (`google-api-python-client`) | OAuth2, scope `gmail.modify` |
| Notificaciones | Telegram (`python-telegram-bot`) | Bot que avisa de emails importantes |
| Tareas periódicas | Celery + Redis | Polling del buzón cada X minutos |
| Base de datos | PostgreSQL | Persistencia de emails procesados y configuración |
| API REST | Django REST Framework | Endpoints de configuración (futuro) |
| Contenedores | Docker Compose | Orquestación de todos los servicios |

## Servicios Docker Compose

1. `web` — Django (servidor principal)
2. `worker` — Celery worker (procesamiento de tareas)
3. `beat` — Celery beat (scheduler de tareas periódicas)
4. `redis` — Broker de mensajes para Celery
5. `db` — PostgreSQL

## Gmail API — Conexión y autenticación

### Setup requerido

1. Crear proyecto en Google Cloud Console (gratis)
2. Habilitar Gmail API
3. Configurar pantalla de consentimiento OAuth (modo testing)
4. Añadir usuario de prueba (email personal)
5. Crear credenciales OAuth 2.0 (tipo "Desktop app")
6. Scope necesario: `gmail.modify` (lectura + modificar mensajes y labels)

### Tokens y caducidad

| Modo | Verificación Google | Caducidad token | Coste |
|---|---|---|---|
| **Testing** (desarrollo) | No | 7 días | Gratis |
| **App publicada** (producción) | Sí (días/semanas) | No caduca | Gratis |
| **Workspace interno** | No | No caduca | ~6€/mes |

**Estrategia**: desarrollar en modo testing, publicar la app cuando esté lista para producción.

### Integración con LangChain

La Gmail API se integra con LangChain mediante **custom tools**:

1. Capa de servicio fina sobre `google-api-python-client`
2. Cada operación (leer, marcar leído, etiquetar, archivar) se envuelve como `langchain.tools.Tool`
3. El agente LangChain usa estas tools para actuar sobre el buzón
