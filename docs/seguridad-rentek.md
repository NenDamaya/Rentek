# Actividades de seguridad — Rentek

**Proyecto:** Rentek, sistema de gestión y renta de maquinaria pesada
**Componentes analizados:** `rag-frontend` (Svelte + Vite) y `rag-agent` (FastAPI + PostgreSQL)
**Nota:** `rag-api` no se utilizó en esta entrega, tal como se solicitó.

---

## Actividad 1. Identificación de datos

Se identificaron cinco tipos de datos que administra la aplicación. La clasificación se hizo considerando quién debe poder consultarlos y qué daño causaría su exposición.

| # | Tipo de dato | Dónde vive | Ejemplos | Clasificación | Justificación |
|---|---|---|---|---|---|
| 1 | Catálogo, precios y disponibilidad | `categorias`, `maquinas`, `disponibilidad`, `sucursales`, `inventario_sucursal` | Nombre de la máquina, especificaciones, precio por día, sucursal, fechas disponibles | **Público** | Es la información comercial que necesita cualquier visitante para decidir qué rentar. No contiene datos personales. |
| 2 | Datos de cuenta | `users` | `username`, `email`, `display_name`, `avatar_url`, `provider`, fecha de registro | **Privado** | Identifica a una persona. Solo el propietario y el personal autorizado deben consultarlos completos. |
| 3 | Carrito, cotizaciones y solicitudes de renta | `carrito_items`, `cotizaciones`, `solicitudes_renta` | Folio, cliente, contacto, máquinas, fechas, subtotal, total | **Privado** | Revela la operación y la situación económica de un cliente. Solo su propietario y administradores deben verlo. |
| 4 | Conversaciones del chat | `chats`, `conversations`, `conversation_messages` | Título del chat, mensajes, tool calls, estado del chat | **Privado** | Puede contener datos del proyecto, presupuesto y datos de contacto proporcionados durante la asesoría. |
| 5 | Credenciales, tokens y registros internos | `users.password_hash`, token HMAC, `observability_logs` | Hash PBKDF2, firma del token, prompts, respuestas, latencias, errores | **Restringido** | No debe verlo el usuario final. Solo el sistema y, para los logs, el personal administrador. |

> El `password_hash` es un caso especial: ni siquiera el propietario de la cuenta debe poder leerlo. La API nunca lo devuelve.

---

## Actividad 2. Análisis de riesgos

### 1. ¿Qué pasaría si una persona accede a la base de datos sin autorización?

- **Confidencialidad:** podría leer correos, nombres, contactos, cotizaciones, solicitudes y conversaciones completas de todos los clientes.
- **Integridad:** podría modificar precios, disponibilidad, estados de solicitudes, roles de usuario o bloquear cuentas.
- **Disponibilidad:** podría borrar tablas o registros y dejar la operación sin servicio.
- **Fraude:** con los datos de contacto y cotizaciones podría suplantar clientes, desviar pagos o negociar a nombre de Rentek.
- **Reputación y cumplimiento:** pérdida de confianza y posibles obligaciones legales por tratamiento de datos personales.
- **Escalamiento:** si obtiene `password_hash` y el secreto de firma, podría intentar crackear contraseñas o fabricar tokens de administrador.

### 2. ¿Qué información de la aplicación necesita mayor protección?

En orden de criticidad:

1. `password_hash` y el secreto `AUTH_SECRET_KEY`: permiten comprometer cuentas y emitir tokens.
2. Datos de contacto de clientes (`email`, `contacto`, `cliente`): identifican personas y permiten fraude.
3. Cotizaciones y solicitudes: contienen montos, fechas y relaciones comerciales.
4. Conversaciones del chat: pueden incluir datos del proyecto y del negocio.
5. Logs de observabilidad: exponen prompts, respuestas y comportamiento del sistema.
6. Roles y estado de bloqueo: un cambio no autorizado otorga privilegios de administrador.

### 3. ¿Cómo evitarían que un usuario consulte información de otro usuario?

Medidas aplicadas o verificadas en el proyecto:

- **Identidad desde el token, no desde el cuerpo de la petición.** El `user_id` se obtiene de `get_current_user(request)`; nunca se acepta un `user_id` enviado por el cliente.
- **Filtro por propietario en cada consulta.** Chats, carrito, cotizaciones y solicitudes usan `WHERE user_id = %s` con el identificador del token.
- **Verificación de propiedad antes de operar.** `get_chat_messages` comprueba que el chat pertenezca al usuario y responde `404` si no existe o no es suyo; `update_chat` y `delete_chat` incluyen `user_id` en el `WHERE`.
- **Consultas parametrizadas.** Todas las consultas usan `%s` con psycopg2; no se concatenan valores del usuario.
- **Respuesta uniforme.** Cuando el recurso no pertenece al usuario se devuelve `404`, no `403`, para no confirmar la existencia de datos ajenos.
- **Control de acceso en el servidor, no solo en la interfaz.** Ocultar un botón no protege nada: los endpoints de administración vuelven a validar el rol con `require_admin`.
- **Bloqueo efectivo.** Un usuario bloqueado ya no puede iniciar sesión (`403`) ni usar un token emitido antes del bloqueo (`401`) en los endpoints que exigen autenticación.

### 4. ¿Qué medidas implementarían para proteger miles de registros?

- **Contraseñas:** PBKDF2 con salt (ya implementado). A futuro, migrar a Argon2id y aumentar el costo según hardware.
- **Secretos:** `AUTH_SECRET_KEY` fuera del repositorio y sin valor por defecto en producción.
- **Base de datos:** usuario de aplicación con privilegios mínimos (sin `SUPERUSER`, sin `DROP`), conexiones TLS y respaldos cifrados.
- **Consultas:** parametrizadas, con índices en `user_id`, `email`, `folio` y fechas para mantener el rendimiento al crecer.
- **Autorización:** validar rol y propiedad en cada endpoint; considerar Row-Level Security (RLS) de PostgreSQL como defensa adicional.
- **Sesiones:** tokens con expiración corta, rotación y revocación; almacenar el token en cookie `HttpOnly` en lugar de `localStorage`.
- **Límites:** rate limiting en login, registro y chat (ya existe para autenticación), y límites de tamaño en cargas.
- **Auditoría:** registrar accesos administrativos, bloqueos y cambios de rol; no borrar logs.
- **Operación:** monitoreo, alertas, backups automáticos, pruebas de restauración y revisión periódica de accesos.
- **Pruebas:** pruebas automatizadas de autorización (401/403/200) que corran en cada cambio.

### Hallazgos reales durante la revisión

| Hallazgo | Riesgo | Estado |
|---|---|---|
| `seed_default_admin()` creaba `admin` / `admin123` en cada arranque | Cualquier persona que conociera la contraseña obtenía rol administrador | **Corregido:** ahora solo se ejecuta si `SEED_DEFAULT_ADMIN=true` y `DEFAULT_ADMIN_PASSWORD` tiene al menos 8 caracteres. |
| El login no revisaba `blocked` | Un usuario bloqueado seguía iniciando sesión | **Corregido:** responde `403`; además el token deja de servir en endpoints protegidos. |
| La sección de administración no existía en el frontend y `getObservabilityLogs()` no enviaba el token | El rol admin no era aprovechable desde la interfaz | **Corregido:** nueva sección y envío de `Authorization`. |
| `/v1/chat/completions` y `/v1/chat/completions/stream` aceptan peticiones sin token | Uso anónimo del chat y del consumo de IA | **Documentado** para una siguiente iteración; no se modificó en esta entrega para no romper el flujo actual. |
| `AUTH_SECRET_KEY` tiene un valor por defecto en `auth.py` | Si no se configura, los tokens son predecibles | **Documentado**; en producción debe definirse en el entorno. |

---

## Actividad 3. Implementación práctica — Opción B: control de acceso

### Qué se implementó

Se agregó una sección de **Administración** que solo puede usar una cuenta con rol `admin`. La restricción se aplica dos veces: en la interfaz y en el servidor.

#### Backend (`rag-agent`)

| Endpoint | Método | Protección | Función |
|---|---|---|---|
| `/api/admin/users` | `GET` | `require_admin` | Lista usuarios sin `password_hash` |
| `/api/admin/users/{id}/block` | `POST` | `require_admin` | Bloquea un usuario cliente |
| `/api/admin/users/{id}/unblock` | `POST` | `require_admin` | Desbloquea y reinicia contadores de seguridad |
| `/api/observability` | `GET` | `require_admin` (ya existía) | Logs del sistema |

Reglas adicionales:

- Un administrador **no puede bloquear su propia cuenta** (`400`).
- Un administrador **no puede bloquear a otro administrador** (`400`).
- Un usuario inexistente devuelve `404`.
- La lista de usuarios no incluye `password_hash`.
- El bloqueo impide el login (`403`) y el uso de tokens previos (`401`) en los endpoints autenticados.

#### Frontend (`rag-frontend`)

- `AdminView.svelte`: pestañas **Usuarios** y **Observabilidad**, con tarjetas de resumen, tabla de usuarios y acciones de bloquear/desbloquear.
- `Navbar.svelte`: la pestaña **Administración** solo se renderiza si `user.role === 'admin'` (escritorio y móvil; también en el menú de usuario).
- `App.svelte`: si el estado intenta abrir `admin` sin rol, muestra **Acceso denegado**; al iniciar o cerrar sesión se vuelve al catálogo.
- `api.js`: `getAdminUsers`, `blockUser`, `unblockUser` y envío del token en `getObservabilityLogs`.

#### Administrador de prueba

`rag-agent/scripts/create_admin.py` crea o promueve una cuenta con contraseña hasheada:

```bash
cd rag-agent
python scripts/create_admin.py \
  --email admin@rentek.com \
  --username admin \
  --password 'AdminSeguro2026' \
  --name 'Administrador Rentek'
```

> Si tu base de datos ya tiene el usuario `admin` creado por versiones anteriores, usa `--username admin` para encontrarlo, rotar su contraseña y eliminar el acceso con `admin123`.

### Evidencia de la demostración

#### 1. Pruebas automatizadas

```bash
cd rag-agent
python -m pytest -q
```

Resultado:

```text
11 passed
```

Las pruebas cubren: 401 sin token, 403 con rol cliente, 200 con admin, lista sin `password_hash`, bloqueo de cliente, rechazo de auto-bloqueo, rechazo de bloqueo a otro admin, 404 de usuario inexistente, token de usuario bloqueado en administración y en chats, y login de usuario bloqueado.

#### 2. Prueba HTTP contra la API real

| Caso | Resultado esperado | Resultado obtenido |
|---|---|---|
| `GET /api/admin/users` sin token | 401 | **401** |
| `GET /api/admin/users` con token de cliente | 403 | **403** |
| `GET /api/admin/users` con token de admin | 200 | **200** |
| Admin intenta bloquear su propia cuenta | 400 | **400** |
| Admin bloquea a un cliente | 200 | **200** |
| Cliente bloqueado intenta iniciar sesión | 403 | **403** |
| Admin desbloquea al cliente | 200 | **200** |
| Cliente desbloqueado inicia sesión | 200 | **200** |

La respuesta de `/api/admin/users` incluye `id`, `username`, `email`, `display_name`, `role`, `blocked`, `blocked_at`, `created_at` y `last_login`; **no** incluye `password_hash`.

#### 3. Evidencia visual

- `docs/evidencia/admin-usuarios.png`: administrador con la pestaña **Administración**, listado de usuarios y acción de bloqueo.
- `docs/evidencia/admin-observabilidad.png`: pestaña de logs disponible para el administrador.
- `docs/evidencia/cliente-sin-admin.png`: cliente autenticado; la pestaña **Administración** no aparece.

### Cómo reproducirlo

1. Levantar PostgreSQL y el backend:

   ```bash
   docker compose up -d postgres
   cd rag-agent
   uvicorn src.api:app --reload
   ```

2. Crear el administrador:

   ```bash
   cd rag-agent
   python scripts/create_admin.py --email admin@rentek.com --username admin --password 'AdminSeguro2026'
   ```

3. Levantar el frontend:

   ```bash
   cd rag-frontend
   VITE_API_URL=http://localhost:8000 pnpm dev
   ```

4. Iniciar sesión como administrador y abrir **Administración**. Cerrar sesión, entrar como cliente y comprobar que la pestaña no aparece.

5. Probar la barrera del servidor:

   ```bash
   curl -i http://localhost:8000/api/admin/users
   curl -i http://localhost:8000/api/admin/users -H "Authorization: Bearer <TOKEN_CLIENTE>"
   curl -i http://localhost:8000/api/admin/users -H "Authorization: Bearer <TOKEN_ADMIN>"
   ```

### Archivos modificados o creados

| Archivo | Cambio |
|---|---|
| `rag-agent/src/api.py` | Endpoints de administración, bloqueo efectivo, validación de `blocked` y seed de admin seguro |
| `rag-agent/scripts/create_admin.py` | Nuevo script para crear/promover administradores |
| `rag-agent/tests/conftest.py` | Stubs de dependencias pesadas para pruebas |
| `rag-agent/tests/test_admin_access.py` | 11 pruebas de control de acceso |
| `rag-agent/.env.example` | Variables `SEED_DEFAULT_ADMIN`, `DEFAULT_ADMIN_USERNAME`, `DEFAULT_ADMIN_PASSWORD` |
| `rag-frontend/src/lib/AdminView.svelte` | Nueva vista de administración |
| `rag-frontend/src/lib/Navbar.svelte` | Pestaña condicionada por rol |
| `rag-frontend/src/App.svelte` | Ruta protegida y reinicio de pestaña al cambiar sesión |
| `rag-frontend/src/lib/api.js` | Cliente de endpoints administrativos y token en observabilidad |
| `rag-frontend/src/lib/LucideIcons.svelte` | Iconos `users`, `activity` y `refresh` |
| `docs/evidencia/*.png` | Capturas de la demostración |

---

## Conclusión

La mejora no se limita a esconder un botón: el servidor valida el rol en cada petición, el `user_id` siempre proviene del token, los usuarios bloqueados pierden acceso y la información sensible (hash de contraseña, datos de otras cuentas) no se expone. Con esto, Rentek cuenta con una base demostrable de control de acceso para seguir creciendo hacia miles de registros.
