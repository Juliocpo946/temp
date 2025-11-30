# Monitoring Service

Servicio de monitoreo cognitivo en tiempo real que utiliza Machine Learning para analizar patrones biométricos y emocionales de usuarios durante sesiones de aprendizaje. Determina cuándo es necesario intervenir y qué tipo de intervención aplicar, evitando notificaciones excesivas.

---

## Tabla de Contenidos

1. [Arquitectura General](#arquitectura-general)
2. [Datos de Entrada](#datos-de-entrada)
3. [Datos de Salida](#datos-de-salida)
4. [Flujo de Procesamiento](#flujo-de-procesamiento)
5. [Modelo de Machine Learning](#modelo-de-machine-learning)
6. [Sistema Anti-Spam](#sistema-anti-spam)
7. [Persistencia](#persistencia)
8. [Entrenamiento](#entrenamiento)
9. [Configuración](#configuración)
10. [Ejecución](#ejecución)
11. [Estructura del Proyecto](#estructura-del-proyecto)

---

## Arquitectura General

```
┌─────────────────┐         ┌─────────────────────┐         ┌─────────────────────┐
│   Flutter App   │   WS    │  Monitoring Service │  AMQP   │ Recommendation Svc  │
│                 │────────>│        (ML)         │────────>│                     │
└─────────────────┘         └─────────────────────┘         └─────────────────────┘
                                     │
                                     │ SQL
                                     v
                            ┌─────────────────┐
                            │     MySQL       │
                            │  (persistencia) │
                            └─────────────────┘
```

| Componente | Protocolo | Función |
|------------|-----------|---------|
| Flutter App | WebSocket | Envía frames biométricos en tiempo real |
| Monitoring Service | WS + AMQP | Procesa frames, detecta patrones, decide intervenciones |
| Recommendation Service | AMQP | Recibe eventos y genera contenido de intervención |
| MySQL | TCP | Almacena intervenciones y muestras de entrenamiento |

---

## Datos de Entrada

### Conexión WebSocket

```
ws://{host}:3008/ws/{session_id}
```

El `session_id` corresponde al UUID de sesión creado por el Session Service.

### Estructura del Frame

Cada mensaje WebSocket contiene un frame con la siguiente estructura JSON:

```json
{
  "metadata": {
    "user_id": 12345,
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "external_activity_id": 101,
    "timestamp": "2025-11-29T10:05:23.456Z"
  },
  "analisis_sentimiento": {
    "emocion_principal": {
      "nombre": "Happiness",
      "confianza": 0.78,
      "estado_cognitivo": "entendiendo"
    },
    "desglose_emociones": [
      {"emocion": "Happiness", "confianza": 78.0},
      {"emocion": "Neutral", "confianza": 15.0},
      {"emocion": "Surprise", "confianza": 5.0},
      {"emocion": "Anger", "confianza": 0.5},
      {"emocion": "Contempt", "confianza": 0.5},
      {"emocion": "Disgust", "confianza": 0.2},
      {"emocion": "Fear", "confianza": 0.3},
      {"emocion": "Sadness", "confianza": 0.5}
    ]
  },
  "datos_biometricos": {
    "atencion": {
      "mirando_pantalla": true,
      "orientacion_cabeza": {
        "pitch": 4.5,
        "yaw": -1.2
      }
    },
    "somnolencia": {
      "esta_durmiendo": false,
      "apertura_ojos_ear": 0.32
    },
    "rostro_detectado": true
  }
}
```

### Descripción de Campos

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `user_id` | int | Identificador del usuario |
| `session_id` | UUID | Identificador de sesión (del Session Service) |
| `external_activity_id` | int | Identificador de la actividad actual |
| `timestamp` | ISO 8601 | Momento de captura del frame |
| `emocion_principal.nombre` | string | Emoción dominante detectada |
| `emocion_principal.confianza` | float | Nivel de confianza (0-1) |
| `emocion_principal.estado_cognitivo` | string | `entendiendo`, `neutral`, `confundido` |
| `desglose_emociones` | array | 8 emociones con su confianza (0-100) |
| `mirando_pantalla` | bool | Si el usuario mira la pantalla |
| `orientacion_cabeza.pitch` | float | Inclinación vertical de cabeza (grados) |
| `orientacion_cabeza.yaw` | float | Rotación horizontal de cabeza (grados) |
| `esta_durmiendo` | bool | Detección de sueño |
| `apertura_ojos_ear` | float | Eye Aspect Ratio (0-1, menor = ojos más cerrados) |
| `rostro_detectado` | bool | Si se detectó un rostro en el frame |

---

## Datos de Salida

### Respuesta WebSocket

Cuando se determina una intervención, el servicio responde al cliente:

```json
{
  "intervention_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "type": "instruction",
  "confidence": 0.82
}
```

### Publicación a RabbitMQ

Cola: `monitoring_events`

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": 12345,
  "external_activity_id": 101,
  "evento_cognitivo": "frustracion",
  "accion_sugerida": "instruction",
  "precision_cognitiva": 0.65,
  "confianza": 0.82,
  "contexto": {
    "precision_cognitiva": 0.65,
    "intentos_previos": 1,
    "tiempo_en_estado": 30
  },
  "timestamp": 1732878323456
}
```

### Tipos de Intervención

| Tipo | Valor | Evento Cognitivo Mapeado | Acción del Recommendation Service |
|------|-------|--------------------------|-----------------------------------|
| NO_INTERVENTION | 0 | - | No se publica nada |
| VIBRATION | 1 | desatencion | Enviar vibración al dispositivo |
| INSTRUCTION | 2 | frustracion | Enviar video o texto de ayuda |
| PAUSE | 3 | cansancio_cognitivo | Sugerir tomar un descanso |

---

## Flujo de Procesamiento

### Diagrama de Flujo Completo

```
                              ┌─────────────────────┐
                              │  Frame llega por WS │
                              └──────────┬──────────┘
                                         │
                                         v
                              ┌─────────────────────┐
                              │ ¿Cambió activity_id │
                              │   desde el último   │
                              │       frame?        │
                              └──────────┬──────────┘
                                         │
                         ┌───────────────┴───────────────┐
                         │ SI                            │ NO
                         v                               v
              ┌─────────────────────┐         ┌─────────────────────┐
              │  Reiniciar buffer   │         │      Continuar      │
              │  Reiniciar contexto │         │                     │
              └──────────┬──────────┘         └──────────┬──────────┘
                         │                               │
                         └───────────────┬───────────────┘
                                         │
                                         v
                              ┌─────────────────────┐
                              │  Extraer 16 features│
                              │      del frame      │
                              └──────────┬──────────┘
                                         │
                                         v
                              ┌─────────────────────┐
                              │ Agregar al buffer   │
                              │ circular (FIFO)     │
                              └──────────┬──────────┘
                                         │
                                         v
                              ┌─────────────────────┐
                              │ ¿Buffer tiene 30    │
                              │     frames?         │
                              └──────────┬──────────┘
                                         │
                         ┌───────────────┴───────────────┐
                         │ NO                            │ SI
                         v                               v
              ┌─────────────────────┐         ┌─────────────────────┐
              │ Esperar más frames  │         │ Construir tensores  │
              │ (no hay inferencia) │         │ Secuencia: (30, 16) │
              └─────────────────────┘         │ Contexto: (6,)      │
                                              └──────────┬──────────┘
                                                         │
                                                         v
                                              ┌─────────────────────┐
                                              │   Inferencia ML     │
                                              │   (GRU + Dense)     │
                                              └──────────┬──────────┘
                                                         │
                                                         v
                                              ┌─────────────────────┐
                                              │ Predicción:         │
                                              │ - Clase (0-3)       │
                                              │ - Confianza (0-1)   │
                                              └──────────┬──────────┘
                                                         │
                                                         v
                                              ┌─────────────────────┐
                                              │ ¿Clase != 0 AND     │
                                              │ Confianza >= 0.6?   │
                                              └──────────┬──────────┘
                                                         │
                         ┌───────────────────────────────┴───────────────────────────────┐
                         │ NO                                                            │ SI
                         v                                                               v
              ┌─────────────────────┐                                         ┌─────────────────────┐
              │ 5% probabilidad:    │                                         │ ¿Cooldown activo    │
              │ guardar como        │                                         │ para este tipo?     │
              │ muestra negativa    │                                         └──────────┬──────────┘
              └─────────────────────┘                                                    │
                                                                      ┌──────────────────┴──────────────────┐
                                                                      │ SI                                  │ NO
                                                                      v                                     v
                                                           ┌─────────────────────┐             ┌─────────────────────┐
                                                           │ Descartar (anti-spam│             │ Publicar a RabbitMQ │
                                                           └─────────────────────┘             │ Guardar en BD       │
                                                                                               │ Actualizar contexto │
                                                                                               │ Responder por WS    │
                                                                                               └──────────┬──────────┘
                                                                                                          │
                                                                                                          v
                                                                                               ┌─────────────────────┐
                                                                                               │ Programar evaluación│
                                                                                               │ de resultado (45s)  │
                                                                                               └─────────────────────┘
```

### Paso a Paso Detallado

#### 1. Recepción del Frame

Ubicación: `src/presentation/routes/ws_routes.py`

El WebSocket recibe el mensaje JSON y lo pasa al `FrameHandler`.

#### 2. Detección de Cambio de Actividad

Ubicación: `src/application/use_cases/process_biometric_frame.py`

```python
def _activity_changed(self, external_activity_id: int) -> bool:
    if self.context.current_external_activity_id is None:
        return True
    return self.context.current_external_activity_id != external_activity_id
```

Si el `external_activity_id` cambió desde el último frame, se reinician:
- Buffer de secuencia (30 frames vacíos)
- Contadores de intervenciones (vibraciones, instrucciones, pausas)
- Tiempos de última intervención

Esto evita que patrones de una actividad afecten las decisiones de otra.

#### 3. Extracción de Features

Ubicación: `src/infrastructure/ml/feature_extractor.py`

Cada frame se convierte en un vector de 16 valores normalizados:

| Índice | Feature | Origen | Normalización |
|--------|---------|--------|---------------|
| 0 | happiness | desglose_emociones | /100 (0-1) |
| 1 | neutral | desglose_emociones | /100 (0-1) |
| 2 | surprise | desglose_emociones | /100 (0-1) |
| 3 | anger | desglose_emociones | /100 (0-1) |
| 4 | contempt | desglose_emociones | /100 (0-1) |
| 5 | disgust | desglose_emociones | /100 (0-1) |
| 6 | fear | desglose_emociones | /100 (0-1) |
| 7 | sadness | desglose_emociones | /100 (0-1) |
| 8 | mirando_pantalla | atencion | 0 o 1 |
| 9 | pitch | orientacion_cabeza | /45, clip(-1,1) |
| 10 | yaw | orientacion_cabeza | /45, clip(-1,1) |
| 11 | esta_durmiendo | somnolencia | 0 o 1 |
| 12 | apertura_ojos_ear | somnolencia | ya normalizado (0-1) |
| 13 | rostro_detectado | datos_biometricos | 0 o 1 |
| 14 | estado_cognitivo | emocion_principal | 0=confundido, 0.5=neutral, 1=entendiendo |
| 15 | confianza_emocion | emocion_principal | ya normalizado (0-1) |

#### 4. Buffer de Secuencia

Ubicación: `src/infrastructure/ml/sequence_buffer.py`

Buffer circular (FIFO) de tamaño 30:
- Cada nuevo frame se agrega al final
- Si el buffer está lleno, el frame más antiguo se descarta
- Se almacenan tanto los features (numpy array) como el frame raw (dict)

```python
class SequenceBuffer:
    def __init__(self, max_length: int = 30):
        self.buffer = deque(maxlen=max_length)
        self.raw_frames = deque(maxlen=max_length)
```

#### 5. Construcción del Vector de Contexto

Ubicación: `src/domain/services/intervention_controller.py`

Vector de 6 valores que captura el historial de intervenciones:

| Índice | Feature | Cálculo |
|--------|---------|---------|
| 0 | tiempo_desde_ultima_vibracion | segundos / 300, max 1.0 |
| 1 | tiempo_desde_ultima_instruccion | segundos / 300, max 1.0 |
| 2 | tiempo_desde_ultima_pausa | segundos / 300, max 1.0 |
| 3 | cantidad_vibraciones | count / 10, max 1.0 |
| 4 | cantidad_instrucciones | count / 5, max 1.0 |
| 5 | cantidad_pausas | count / 3, max 1.0 |

Este contexto permite al modelo aprender:
- No enviar vibraciones si ya se enviaron recientemente
- Escalar a pausa si las instrucciones no funcionaron
- Considerar el historial acumulado de la actividad

#### 6. Inferencia del Modelo

Ubicación: `src/infrastructure/ml/intervention_classifier.py`

El modelo recibe:
- Tensor de secuencia: `(1, 30, 16)`
- Tensor de contexto: `(1, 6)`

Retorna:
- Clase predicha: 0, 1, 2 o 3
- Confianza: probabilidad de la clase predicha (0-1)

#### 7. Decisión de Intervención

Condiciones para intervenir:
1. Clase predicha != 0 (NO_INTERVENTION)
2. Confianza >= umbral (default: 0.6)
3. Cooldown no activo para ese tipo de intervención

#### 8. Publicación y Persistencia

Si se decide intervenir:
1. Publicar evento a cola `monitoring_events` de RabbitMQ
2. Guardar registro en tabla `interventions` con snapshot de la ventana
3. Crear muestra de entrenamiento en tabla `training_samples`
4. Actualizar contadores y tiempos en el contexto de sesión
5. Responder al cliente WebSocket

#### 9. Evaluación de Resultado

Ubicación: `src/application/use_cases/evaluate_intervention_result.py`

45 segundos después de cada intervención:
1. Obtener últimos 10 frames del buffer actual
2. Comparar con los 10 últimos frames del momento de la intervención
3. Calcular cambio en emociones negativas y atención
4. Clasificar resultado: `improved`, `no_change`, `worsened`
5. Actualizar registro de intervención
6. Ajustar label de muestra de entrenamiento si empeoró

---

## Modelo de Machine Learning

### Arquitectura de Red

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Input Secuencia          Input Contexto                        │
│  (30, 16)                 (6,)                                  │
│      │                        │                                 │
│      v                        v                                 │
│  ┌─────────┐              ┌─────────┐                           │
│  │ GRU(64) │              │Dense(16)│                           │
│  │ return  │              │  ReLU   │                           │
│  │ seq=True│              └────┬────┘                           │
│  └────┬────┘                   │                                │
│       │                        │                                │
│       v                        │                                │
│  ┌─────────┐                   │                                │
│  │Dropout  │                   │                                │
│  │  0.3    │                   │                                │
│  └────┬────┘                   │                                │
│       │                        │                                │
│       v                        │                                │
│  ┌─────────┐                   │                                │
│  │ GRU(32) │                   │                                │
│  └────┬────┘                   │                                │
│       │                        │                                │
│       v                        │                                │
│  ┌─────────┐                   │                                │
│  │Dropout  │                   │                                │
│  │  0.3    │                   │                                │
│  └────┬────┘                   │                                │
│       │                        │                                │
│       └────────────┬───────────┘                                │
│                    │                                            │
│                    v                                            │
│              ┌───────────┐                                      │
│              │Concatenate│                                      │
│              └─────┬─────┘                                      │
│                    │                                            │
│                    v                                            │
│              ┌─────────┐                                        │
│              │Dense(32)│                                        │
│              │  ReLU   │                                        │
│              └────┬────┘                                        │
│                   │                                             │
│                   v                                             │
│              ┌─────────┐                                        │
│              │Dropout  │                                        │
│              │  0.3    │                                        │
│              └────┬────┘                                        │
│                   │                                             │
│                   v                                             │
│              ┌─────────┐                                        │
│              │Dense(4) │                                        │
│              │ Softmax │                                        │
│              └────┬────┘                                        │
│                   │                                             │
│                   v                                             │
│           [p0, p1, p2, p3]                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Justificación de la Arquitectura

| Componente | Justificación |
|------------|---------------|
| GRU | Captura dependencias temporales en la secuencia de 30 frames. Más eficiente que LSTM para secuencias cortas. |
| Dos capas GRU | Primera capa (64 unidades) extrae patrones de bajo nivel. Segunda capa (32 unidades) sintetiza patrones de alto nivel. |
| Dropout 0.3 | Previene overfitting, especialmente importante con datos sintéticos. |
| Rama de contexto separada | El historial de intervenciones es información estructurada, no secuencial. Dense layer es más apropiado. |
| Concatenación tardía | Permite que cada rama aprenda representaciones especializadas antes de combinar. |
| Softmax final | Clasificación multiclase con probabilidades interpretables. |

### Modo Sintético (Fallback)

Ubicación: `src/infrastructure/ml/model_loader.py`

Cuando no existe modelo entrenado, se usan heurísticas:

```python
def _synthetic_predict(self, sequence, context):
    avg_anger = np.mean(sequence[:, 3])
    avg_contempt = np.mean(sequence[:, 4])
    avg_disgust = np.mean(sequence[:, 5])
    avg_sadness = np.mean(sequence[:, 7])
    
    avg_looking = np.mean(sequence[:, 8])
    avg_sleeping = np.mean(sequence[:, 11])
    avg_eye_openness = np.mean(sequence[:, 12])
    avg_face_detected = np.mean(sequence[:, 13])
    
    frustration_score = (avg_anger + avg_contempt + avg_disgust + avg_sadness) / 4.0
    attention_score = (avg_looking + avg_face_detected + (1.0 - avg_sleeping)) / 3.0
    
    # Lógica de escalamiento
    if frustration_score > 0.4 and prev_instructions >= 1:
        return 3, confidence  # PAUSE
    if (attention_score < 0.5 or drowsiness > 0.6) and prev_vibrations >= 2:
        return 3, confidence  # PAUSE
    if frustration_score > 0.35:
        return 2, confidence  # INSTRUCTION
    if attention_score < 0.6:
        return 1, confidence  # VIBRATION
    return 0, 0.8  # NO_INTERVENTION
```

---

## Sistema Anti-Spam

### Cooldowns por Tipo de Intervención

| Intervención | Cooldown | Justificación |
|--------------|----------|---------------|
| VIBRATION | 30 segundos | Permite tiempo para que el usuario reaccione |
| INSTRUCTION | 60 segundos | El usuario necesita tiempo para procesar la ayuda |
| PAUSE | 180 segundos | Evita sugerir pausas repetitivas |

### Lógica de Cooldown

Ubicación: `src/domain/services/intervention_controller.py`

```python
def is_cooldown_active(self, intervention_type, context):
    now = datetime.utcnow()
    cooldown = self.cooldowns.get(intervention_type)
    last_time = None
    
    if intervention_type == InterventionType.VIBRATION:
        last_time = context.last_vibration_at
    # ... similar para otros tipos
    
    if last_time is None:
        return False
    
    return (now - last_time) < cooldown
```

### Escalamiento de Intervenciones

El contexto de sesión incluye contadores que el modelo usa para aprender patrones de escalamiento:

| Situación | Decisión Esperada |
|-----------|-------------------|
| Distracción leve, sin intervenciones previas | VIBRATION |
| Distracción persistente, 2+ vibraciones previas | PAUSE |
| Frustración detectada, sin instrucciones previas | INSTRUCTION |
| Frustración persistente, 1+ instrucción previa | PAUSE |

---

## Persistencia

### Base de Datos

MySQL con 3 tablas.

### Tabla: interventions

Almacena cada intervención realizada.

```sql
CREATE TABLE interventions (
    id CHAR(36) PRIMARY KEY,
    session_id CHAR(36) NOT NULL,
    external_activity_id VARCHAR(50) NOT NULL,
    intervention_type VARCHAR(20) NOT NULL,
    confidence FLOAT NOT NULL,
    triggered_at DATETIME NOT NULL,
    window_snapshot JSON NOT NULL,
    context_snapshot JSON NOT NULL,
    result VARCHAR(20) DEFAULT 'pending',
    result_evaluated_at DATETIME,
    INDEX idx_session_activity (session_id, external_activity_id, triggered_at)
);
```

| Campo | Descripción |
|-------|-------------|
| window_snapshot | JSON con los 30 frames que causaron la intervención |
| context_snapshot | JSON con el estado de contadores al momento |
| result | `pending`, `improved`, `no_change`, `worsened` |

### Tabla: state_transitions

Registra cambios de estado cognitivo significativos.

```sql
CREATE TABLE state_transitions (
    id CHAR(36) PRIMARY KEY,
    session_id CHAR(36) NOT NULL,
    external_activity_id VARCHAR(50) NOT NULL,
    from_state VARCHAR(50) NOT NULL,
    to_state VARCHAR(50) NOT NULL,
    transitioned_at DATETIME NOT NULL,
    trigger_reason VARCHAR(100) NOT NULL,
    INDEX idx_session_time (session_id, transitioned_at)
);
```

### Tabla: training_samples

Muestras para reentrenamiento del modelo.

```sql
CREATE TABLE training_samples (
    id CHAR(36) PRIMARY KEY,
    intervention_id CHAR(36),
    external_activity_id VARCHAR(50) NOT NULL,
    window_data JSON NOT NULL,
    context_data JSON NOT NULL,
    label INT NOT NULL,
    source VARCHAR(20) NOT NULL,
    created_at DATETIME NOT NULL,
    used_in_training BOOLEAN DEFAULT FALSE,
    INDEX idx_source_unused (source, used_in_training, label),
    FOREIGN KEY (intervention_id) REFERENCES interventions(id)
);
```

| Campo | Descripción |
|-------|-------------|
| intervention_id | NULL para muestras negativas (no intervención) |
| window_data | JSON con secuencia de 30x16 features |
| context_data | JSON con vector de 6 features de contexto |
| label | 0=NO_INTERVENTION, 1=VIBRATION, 2=INSTRUCTION, 3=PAUSE |
| source | `synthetic`, `production`, `manual_labeled` |

### Frecuencia de Escrituras

| Evento | Frecuencia Estimada |
|--------|---------------------|
| Intervención | 5-10 por sesión de 30 min |
| Muestra negativa | 5% de frames sin intervención |
| Transición de estado | 5-15 por sesión |

Para 100 usuarios concurrentes: ~100-150 escrituras/hora (manejable sin optimizaciones).

---

## Entrenamiento

### Generación de Datos Sintéticos

Ubicación: `training/dataset_generator.py`

Genera 10,000 muestras balanceadas (2,500 por clase).

#### Patrones Simulados

**Clase 0 - NO_INTERVENTION:**
- Emociones estables y positivas
- happiness alto (0.3-0.8)
- Emociones negativas bajas (<0.05)
- Atención constante (mirando_pantalla=1)
- Rostro detectado
- Ojos abiertos

**Clase 1 - VIBRATION:**
- Distracción intermitente (5-12 frames)
- Puede ser: no mirando pantalla, somnolencia leve, o rostro no detectado
- Emociones relativamente estables
- Pocas intervenciones previas

**Clase 2 - INSTRUCTION:**
- Frustración gradual creciente
- anger, contempt, disgust aumentan progresivamente
- happiness disminuye
- estado_cognitivo baja hacia "confundido"
- Sin instrucciones previas recientes

**Clase 3 - PAUSE:**
- Frustración persistente post-instrucción
- Distracción persistente post-vibraciones (15-25 frames)
- Somnolencia persistente post-vibraciones
- Historial de intervenciones fallidas

### Proceso de Entrenamiento

Ubicación: `training/train.py`

```bash
# 1. Generar datos sintéticos
python training/dataset_generator.py

# 2. Entrenar modelo
python training/train.py
```

**Hiperparámetros:**

| Parámetro | Valor |
|-----------|-------|
| Epochs | 50 (con early stopping) |
| Batch size | 32 |
| Learning rate | 0.001 |
| Optimizer | Adam |
| Loss | Sparse Categorical Crossentropy |
| Early stopping patience | 10 epochs |
| Train/Test split | 80/20 |

**Salida:**
- Modelo guardado en `models/intervention_model.h5`
- Métricas de accuracy y loss en consola

### Reentrenamiento con Datos de Producción

Ubicación: `training/export_training_data.py`

```bash
# Exportar datos de producción
python training/export_training_data.py

# Reentrenar (cambiar data_dir en train.py)
python training/train.py
```

**Ciclo de mejora:**

```
┌─────────────────┐
│ Modelo inicial  │
│  (sintético)    │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Producción      │
│ (recolección)   │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Evaluación de   │
│ resultados      │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Ajuste de       │
│ labels          │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Exportar        │
│ training data   │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Reentrenar      │
│ modelo          │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Evaluar mejora  │
│ vs anterior     │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Desplegar si    │
│ mejora          │
└─────────────────┘
```

**Ajuste automático de labels:**
- Si intervención resultó en `worsened`, el label se cambia a 0 (no debió intervenir)
- Esto permite que el modelo aprenda de sus errores

---

## Configuración

### Variables de Entorno

Archivo: `.env`

```env
# Servicio
SERVICE_NAME=monitoring-service
SERVICE_PORT=3008

# MySQL
MYSQL_HOST=host.docker.internal
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=123456
MYSQL_DATABASE=monitoring_service

# RabbitMQ
AMQP_URL=amqps://user:pass@host/vhost
MONITORING_EVENTS_QUEUE=monitoring_events
LOG_SERVICE_QUEUE=logs

# Modelo ML
MODEL_PATH=models/intervention_model.keras
SEQUENCE_LENGTH=30
CONFIDENCE_THRESHOLD=0.6

# Cooldowns (segundos)
COOLDOWN_VIBRATION_SECONDS=30
COOLDOWN_INSTRUCTION_SECONDS=60
COOLDOWN_PAUSE_SECONDS=180

# Evaluación y muestreo
RESULT_EVALUATION_DELAY_SECONDS=45
NEGATIVE_SAMPLE_RATE=0.05
```

### Parámetros Ajustables

| Parámetro | Default | Efecto de aumentar | Efecto de disminuir |
|-----------|---------|--------------------|--------------------|
| CONFIDENCE_THRESHOLD | 0.6 | Menos intervenciones, más precisas | Más intervenciones, posibles falsos positivos |
| SEQUENCE_LENGTH | 30 | Decisiones más informadas, más latencia | Decisiones más rápidas, menos contexto |
| COOLDOWN_* | 30/60/180 | Menos spam, posible demora en ayuda | Más responsivo, riesgo de spam |
| NEGATIVE_SAMPLE_RATE | 0.05 | Dataset más balanceado, más storage | Dataset desbalanceado hacia positivos |

---

## Ejecución

### Requisitos

- Python 3.11+
- MySQL 8.0+
- RabbitMQ 3.x

### Instalación Local

```bash
# Clonar/copiar el servicio
cd monitoring_service

# Instalar dependencias
pip install -r requirements.txt

# Crear base de datos
mysql -u root -p -e "CREATE DATABASE monitoring_service;"

# Configurar .env
cp .env.example .env
# Editar valores según ambiente

# Generar datos sintéticos
python training/dataset_generator.py

# Entrenar modelo
python training/train.py

# Ejecutar servicio
uvicorn main:app --host 0.0.0.0 --port 3008
```

### Docker

```bash
# Build
docker build -t monitoring-service .

# Run
docker run -d \
  --name monitoring-service \
  -p 3008:3008 \
  --env-file .env \
  monitoring-service
```

### Endpoints

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/health` | GET | Estado del servicio y modelo |
| `/ready` | GET | Readiness check |
| `/ws/{session_id}` | WebSocket | Conexión para streaming de frames |
| `/ws/connections` | GET | Lista de conexiones activas |

---

## Estructura del Proyecto

```
monitoring_service/
├── .env                          # Variables de entorno
├── Dockerfile                    # Imagen Docker
├── main.py                       # Punto de entrada FastAPI
├── requirements.txt              # Dependencias Python
├── README.md                     # Esta documentación
│
├── models/                       # Modelos entrenados
│   └── intervention_model.h5     # Modelo Keras
│
├── training/                     # Scripts de entrenamiento
│   ├── data/
│   │   ├── production/           # Datos exportados de producción
│   │   └── synthetic/            # Datos generados sintéticamente
│   ├── dataset_generator.py      # Genera datos sintéticos
│   ├── export_training_data.py   # Exporta datos de BD
│   └── train.py                  # Entrena el modelo
│
└── src/
    ├── application/              # Casos de uso
    │   ├── dtos/
    │   │   ├── biometric_frame_dto.py    # DTO de entrada
    │   │   └── monitoring_event_dto.py   # DTO de salida
    │   └── use_cases/
    │       ├── evaluate_intervention_result.py  # Evalúa resultados
    │       └── process_biometric_frame.py       # Procesa frames
    │
    ├── domain/                   # Lógica de negocio
    │   ├── entities/
    │   │   ├── intervention.py         # Entidad de intervención
    │   │   ├── state_transition.py     # Entidad de transición
    │   │   └── training_sample.py      # Entidad de muestra
    │   ├── services/
    │   │   └── intervention_controller.py  # Control de cooldowns
    │   └── value_objects/
    │       ├── cognitive_state.py      # Estados cognitivos
    │       ├── intervention_result.py  # Resultados de intervención
    │       └── intervention_type.py    # Tipos de intervención
    │
    ├── infrastructure/           # Implementaciones técnicas
    │   ├── config/
    │   │   └── settings.py             # Configuración centralizada
    │   ├── messaging/
    │   │   ├── monitoring_publisher.py # Publica a RabbitMQ
    │   │   └── rabbitmq_client.py      # Cliente RabbitMQ
    │   ├── ml/
    │   │   ├── feature_extractor.py    # Extrae features de frames
    │   │   ├── intervention_classifier.py  # Wrapper del modelo
    │   │   ├── model_loader.py         # Carga/inferencia del modelo
    │   │   └── sequence_buffer.py      # Buffer circular
    │   ├── persistence/
    │   │   ├── database.py             # Conexión SQLAlchemy
    │   │   ├── models/
    │   │   │   ├── intervention_model.py      # Modelo SQLAlchemy
    │   │   │   ├── state_transition_model.py  # Modelo SQLAlchemy
    │   │   │   └── training_sample_model.py   # Modelo SQLAlchemy
    │   │   └── repositories/
    │   │       ├── intervention_repository.py      # CRUD intervenciones
    │   │       ├── state_transition_repository.py  # CRUD transiciones
    │   │       └── training_sample_repository.py   # CRUD muestras
    │   └── websocket/
    │       ├── connection_manager.py   # Gestión de conexiones WS
    │       └── frame_handler.py        # Procesa mensajes WS
    │
    └── presentation/             # Capa de presentación
        └── routes/
            ├── health_routes.py        # Endpoints de salud
            └── ws_routes.py            # Endpoint WebSocket
```

---

## Limitaciones Conocidas

1. **Cold Start**: Los primeros 30 frames de cada actividad no generan inferencia (buffer incompleto).

2. **Modelo Sintético**: El modelo inicial está entrenado con datos sintéticos. Su precisión en producción será menor hasta reentrenar con datos reales.

3. **Expresiones Atípicas**: Usuarios que expresan frustración de forma no convencional (ej: risa nerviosa) pueden no ser detectados correctamente.

4. **Latencia de Evaluación**: El resultado de una intervención se evalúa 45 segundos después. Si el usuario cambió de actividad, la evaluación puede no ser precisa.

5. **Sin Fallback de Seguridad**: Si el modelo consistentemente predice NO_INTERVENTION pero el usuario está claramente en problemas, no hay mecanismo de override automático.

---

