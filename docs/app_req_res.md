
# API DOCUMENTATION - SESSION & COGNITIVE SERVICES

## AUTENTICACIÓN

Todas las peticiones REST requieren API Key en el header:

```http
Authorization: Bearer pk_mobile_production_abc123xyz
```

El API Key identifica automáticamente a qué empresa pertenece la aplicación.

---

## SESSION_SERVICE - REST API

Base URL: `http://your-domain:3004`

---

### POST /sessions
Crear nueva sesión de aprendizaje

**Headers:**
```http
Authorization: Bearer pk_mobile_production_abc123xyz
```

**Request:**
```json
{
  "user_id": 12,
  "disability_type": "auditiva",
  "cognitive_analysis_enabled": true
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "activa",
  "created_at": "2025-11-12T10:00:00Z"
}
```

---

### POST /sessions/{session_id}/heartbeat
Actualizar heartbeat de la sesión (enviar cada 10 segundos)

**Headers:**
```http
Authorization: Bearer pk_mobile_production_abc123xyz
```

**Response:**
```json
{
  "status": "ok",
  "last_heartbeat_at": "2025-11-12T10:05:00Z"
}
```

**Nota:** Si no se recibe heartbeat por 30 segundos, la sesión se marca como `pausada_automaticamente`.

---

### POST /sessions/{session_id}/pause
Pausar sesión

**Headers:**
```http
Authorization: Bearer pk_mobile_production_abc123xyz
```

**Response:**
```json
{
  "status": "pausada"
}
```

---

### POST /sessions/{session_id}/resume
Reanudar sesión

**Headers:**
```http
Authorization: Bearer pk_mobile_production_abc123xyz
```

**Response:**
```json
{
  "status": "activa"
}
```

---

### DELETE /sessions/{session_id}
Finalizar sesión

**Headers:**
```http
Authorization: Bearer pk_mobile_production_abc123xyz
```

**Response:**
```json
{
  "status": "finalizada",
  "ended_at": "2025-11-12T11:00:00Z"
}
```

---

### POST /sessions/{session_id}/activity/start
Iniciar actividad

**Headers:**
```http
Authorization: Bearer pk_mobile_production_abc123xyz
```

**Request:**
```json
{
  "external_activity_id": 1,
  "title": "Aprendiendo a pronunciar la O",
  "subtitle": "Un sonido redondo como una boca abierta",
  "content": "Aprenderás a pronunciar correctamente...",
  "activity_type": "lectura"
}
```

**Response:**
```json
{
  "status": "activity_started"
}
```

---

### POST /sessions/{session_id}/activity/complete
Completar actividad

**Headers:**
```http
Authorization: Bearer pk_mobile_production_abc123xyz
```

**Request (lectura):**
```json
{
  "external_activity_id": 1,
  "feedback": {
    "precision": 84.21
  }
}
```

**Request (escritura):**
```json
{
  "external_activity_id": 1,
  "feedback": {
    "structural_similarity": 0.68
  }
}
```

**Response:**
```json
{
  "status": "completada"
}
```

---

### POST /sessions/{session_id}/activity/abandon
Abandonar actividad

**Headers:**
```http
Authorization: Bearer pk_mobile_production_abc123xyz
```

**Request:**
```json
{
  "external_activity_id": 1
}
```

**Response:**
```json
{
  "status": "abandonada"
}
```

---

### GET /sessions/{session_id}
Obtener información de sesión

**Headers:**
```http
Authorization: Bearer pk_mobile_production_abc123xyz
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": 12,
  "status": "activa",
  "current_activity": {
    "external_activity_id": 1,
    "title": "Aprendiendo a pronunciar la O",
    "started_at": "2025-11-12T10:30:00Z"
  },
  "created_at": "2025-11-12T10:00:00Z",
  "last_heartbeat_at": "2025-11-12T10:35:00Z"
}
```

**Response (sesión expirada):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "expirada",
  "codigo": "SESSION_TIMEOUT"
}
```

---

### POST /sessions/{session_id}/config
Configurar preferencias de análisis cognitivo

**Headers:**
```http
Authorization: Bearer pk_mobile_production_abc123xyz
```

**Request:**
```json
{
  "cognitive_analysis_enabled": true,
  "text_notifications": true,
  "video_suggestions": true,
  "vibration_alerts": false,
  "pause_suggestions": true
}
```

**Response:**
```json
{
  "status": "configuracion_actualizada"
}
```

---

## COGNITIVE_SERVICE - WebSocket

Base URL: `ws://your-domain:3005/ws/cognitive?session_id={uuid}`

**Conexión:**
```javascript
const ws = new WebSocket('ws://your-domain:3005/ws/cognitive?session_id=550e8400-...');
```

**Nota:** El `session_id` debe ser de una sesión activa creada previamente en SESSION_SERVICE.

---

### Envío de video - Opción 1: Chunks binarios (Recomendado)

**Paso 1: Enviar metadata (JSON)**
```json
{
  "tipo": "video_chunk",
  "session_id": "550e8400-e29b-41d4-a716-446655440001",
  "timestamp": 1731340512000
}
```

**Paso 2: Enviar binario inmediatamente después**
```
[bytes del video chunk]
```

**Descripción:** Cliente graba video en chunks de 1-2 segundos. Servidor no responde a cada chunk.

---

### Envío de video - Opción 2: Frames base64

**Mensaje:**
```json
{
  "tipo": "video_frame",
  "session_id": "550e8400-e29b-41d4-a716-446655440001",
  "frame_base64": "/9j/4AAQSkZJRgABAQEA...",
  "timestamp": 1731340512000
}
```

**Descripción:** Más simple pero más pesado en ancho de banda.

---

### Pausar análisis

**Cliente envía:**
```json
{
  "tipo": "pausar_analisis",
  "session_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

**Servidor responde:**
```json
{
  "estado": "analisis_pausado"
}
```

---

### Reanudar análisis

**Cliente envía:**
```json
{
  "tipo": "reanudar_analisis",
  "session_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

**Servidor responde:**
```json
{
  "estado": "analisis_activo"
}
```

---

## FEEDBACK (SERVIDOR → CLIENTE) - FUTURO

**Nota:** Estos mensajes aún no están implementados. Se enviarán cuando se implemente el módulo de ML.

### Texto de apoyo o instruccion
```json
{
  "accion": "texto",
  "motivo": "Confundido",
  "precision_cognitiva": 0.87,
  "contenido": {
    "mensaje": "Tranquilo, tómate tu tiempo."
  }
}
```

### Video instructivo
```json
{
  "accion": "video",
  "motivo": "Frustracion",
  "precision_cognitiva": 0.91,
  "contenido": {
    "url": "https://mi-servidor.com/videos/lsm_vocal_o.mp4",
    "titulo": "Pronunciación correcta de la vocal O",
    "descripcion": "Observa cómo se forma el sonido..."
  }
}
```

### Vibración
```json
{
  "accion": "vibracion",
  "motivo": "Atención baja",
  "precision_cognitiva": 0.79,
  "contenido": {
    "duracion_ms": 500,
    "intensidad": "media"
  }
}
```

### Sugerencia de pausa
```json
{
  "accion": "sugerir_pausa",
  "motivo": "Cansancio cognitivo",
  "precision_cognitiva": 0.65,
  "contenido": {
    "mensaje": "Has trabajado muy bien. ¿Quieres tomar un descanso?"
  }
}
```

---

## FLUJOS COMPLETOS

### Flujo 1: Sesión normal

```
1. POST /sessions
   → Crear sesión

2. WebSocket connect
   → Conectar a cognitive service

3. POST /sessions/{id}/activity/start
   → Iniciar actividad

4. Enviar video chunks por WebSocket
   → Stream de video

5. POST /sessions/{id}/heartbeat (cada 10s)
   → Mantener sesión activa

6. POST /sessions/{id}/activity/complete
   → Completar actividad

7. DELETE /sessions/{id}
   → Finalizar sesión

8. WebSocket close
   → Cerrar conexión
```

---

### Flujo 2: Reconexión automática

```
1. Usuario pierde internet
   → WebSocket se desconecta

2. Servidor deja de recibir heartbeats
   → Después de 30s marca sesión como pausada_automaticamente

3. Internet regresa
   → Cliente reconecta WebSocket automáticamente

4. GET /sessions/{id}
   → Validar si sesión sigue activa

5. Si status="activa"
   → Continuar enviando video

6. Si status="expirada"
   → Crear nueva sesión (POST /sessions)
```

---

### Flujo 3: Usuario ve video instructivo (futuro)

```
1. Servidor detecta frustración
   → Envía feedback tipo "video" por WebSocket

2. App recibe video instructivo
   → Muestra video al usuario

3. App envía pausar_analisis por WebSocket
   → Servidor deja de procesar video

4. Usuario termina de ver video

5. App envía reanudar_analisis por WebSocket
   → Servidor continúa procesando
```

---

## ERRORES COMUNES

### 401 Unauthorized
```json
{
  "detail": "API key requerida"
}
```
**Solución:** Incluir header `Authorization: Bearer {api_key}`

---

### 404 Not Found
```json
{
  "detail": "Session not found"
}
```
**Solución:** Verificar que el `session_id` exista y sea válido

---

### 4000 WebSocket Close
```
Reason: "Invalid session"
```
**Solución:** Crear sesión válida antes de conectar WebSocket

---

## NOTAS IMPORTANTES

1. **Expiración automática:** Sesiones sin heartbeat por 30 segundos se marcan como `pausada_automaticamente`. Sesiones inactivas por más de 1 hora se marcan como `expirada`.

2. **WebSocket requiere sesión activa:** Antes de conectar el WebSocket, debe existir una sesión creada vía REST.

3. **Feedback futuro:** Los mensajes de feedback (texto, video, vibración, pausa) aún no están implementados. Por ahora el WebSocket solo recibe video.

4. **API Key por empresa:** Un API Key pertenece a una empresa. Todos los usuarios de esa empresa comparten el mismo API Key.

5. **Solo para estudiantes:** SESSION_SERVICE está diseñado solo para estudiantes que realizan actividades de aprendizaje.
