# State Space Visualizer v0.1

**STATUS:** OPEN
**DEPENDENCIA:** Freedeon Engine v0.1 (Phase 16 sellada)

---

# PROPÓSITO

Permitir observar visualmente la diferencia entre:

* Connectivity
* Reachability
* Discoverability

sin leer código.

La UI representa.

El Engine decide.

---

# FUENTE DE VERDAD

El State Space Visualizer no implementa:

* Connectivity
* Reachability
* Discoverability

Toda evaluación proviene exclusivamente de:

* `exists_path()`
* `can_reach()`
* `can_discover()`

del Freedeon Engine.

La UI representa.

El Engine decide.

---

# PREGUNTAS DE DISEÑO

## 1. ¿Qué debe ser visible sobre un State?

### Mínimo

* Identificador
* Posición visual en el grafo

### Opcional

* Metadatos (tooltip)
* Tipo de estado (si aplica)

### Decisión

Mantener el grafo limpio.

Información bajo demanda.

---

## 2. ¿Qué debe ser visible sobre una Transition?

### Mínimo

* Origen
* Destino

### Opcional

* Capability requerida (tooltip)
* Flecha de dirección

### Decisión

Transition = arista dirigida.

Metadatos bajo demanda.

---

## 3. ¿Cómo se representa un Path?

| Estado              | Representación                  |
| ------------------- | ------------------------------- |
| Camino existente    | Línea gris punteada             |
| Camino seleccionado | Línea azul gruesa               |
| Camino recorrido    | Línea verde sólida con marcador |

### Decisión

Estructura, intención e historia tienen lenguajes visuales distintos.

Los caminos existentes son visibles aunque no estén seleccionados.

---

## 4. ¿Cómo se representa un Abyss?

Abyss:

`exists_path(A, B) = False`

### Decisión

Visible, pero tenue.

Representación:

* Opacidad 20%
* Borde rojo discontinuo
* Tooltip:

> Sin camino desde origen

### Motivo

Nodo inexistente ≠ Nodo existente sin camino.

---

## 5. ¿Cómo se colorea?

| Categoría         | Color         | Condición                                                   |
| ----------------- | ------------- | ----------------------------------------------------------- |
| Reachable         | 🟢 Verde      | exists_path=True AND can_reach=True                         |
| Discoverable only | 🔵 Azul       | exists_path=True AND can_reach=False AND can_discover=True  |
| Connected only    | ⚪ Gris        | exists_path=True AND can_reach=False AND can_discover=False |
| Abyss             | 🔴 Rojo tenue | exists_path=False                                           |

### Nota

Los colores distinguen categorías ontológicas.

No representan:

* valor
* utilidad
* prioridad
* preferencia

---

## 6. ¿Qué selecciona el usuario?

1. EON
2. Estado origen (A)
3. Estado destino (B)

### Decisión

Nada más.

Mantener minimalista.

---

## 7. ¿Qué preguntas responde?

* `exists_path(A, B)`
* `can_reach(EON, A, B)`
* `can_discover(EON, A, B)`

### Decisión

El visualizador consume resultados.

No produce ontología.

---

## 8. ¿Cómo se actualiza?

### Eventos

* Cambio de EON
* Cambio de origen
* Cambio de destino

### Opcional

Animación de recorrido.

### Decisión

Actualización por eventos.

Sin polling continuo.

---

## 9. ¿Cuál es la unidad mínima visible?

### Decisión

El State es la unidad mínima visible.

Toda representación emerge de:

* States
* Transitions
* Paths

No existen elementos visuales adicionales obligatorios.

---

# TEST VISUAL 001

Grafo:

A ─ B ─ C
│
D

Caso:

* exists_path(A,C) = True
* can_reach(A,C) = False
* can_discover(A,C) = True

Resultado esperado:

* C visible
* C azul
* A→B→C gris punteado

Validación:

* Verde → Reachability contaminó Discoverability ❌
* Gris → Discoverability se perdió ❌
* Azul → Distinción correcta ✅

---

# NO OBJETIVOS (v0.1)

El visualizador no:

* calcula ontología
* selecciona caminos
* optimiza rutas
* evalúa valor
* ejecuta acciones

Solo representa resultados producidos por el Engine.

---

# ESTADO ACTUAL

* PHASE 16: SEALED
* ENGINE v0.1: LIVE
* POST-SEAL OBSERVATIONS: ACTIVE
* PSO-16C-001: RECORDED
* STATE SPACE VISUALIZER v0.1: OPEN

---

# PRÓXIMOS PASOS

1. Documento
2. Commit
3. Implementación HTML/CSS/JS
4. Validación Test Visual 001

---

# NOTA FINAL

"La implementación no viene después de la ontología.

La implementación es una herramienta de excavación ontológica."

🌱⚡🍄
