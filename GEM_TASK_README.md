# Tarea de Recolección de Gemas (GatherGem)

## 📋 Descripción

La tarea `GatherGem` permite al bot buscar y recolectar automáticamente gemas en el mapa del juego. Esta tarea es similar a la recolección de recursos normales pero específicamente diseñada para gemas.

## 🎯 Funcionalidades

### ✅ Características Implementadas

- **Búsqueda automática** de minas de gemas en el mapa
- **Movimiento inteligente** por el mapa para encontrar gemas
- **Detección de gemas** ya recolectadas para evitar duplicados
- **Envío de tropas** automático para recolectar
- **Manejo de comandantes** secundarios
- **Sistema de debug** para troubleshooting
- **Logs en tiempo real** para monitoreo

### 🔧 Configuración

#### Parámetros en `bot_config.py`:

```python
# Gather gem
self.enableGatherGem = config.get('enableGatherGem', False)           # Activar/desactivar
self.gatherGemDistance = config.get('gatherGemDistance', 50)          # Distancia de búsqueda
self.gatherGemNoSecondaryCommander = config.get('gatherGemNoSecondaryCommander', True)  # Sin comandante secundario
self.gatherGemUseMultipleImages = config.get('gatherGemUseMultipleImages', True)        # Usar múltiples imágenes
self.gatherGemMinImagesFound = config.get('gatherGemMinImagesFound', 3)                # Mínimo de imágenes para confirmar
```

#### Configuración en la GUI:

1. **enableGatherGem**: Activar recolección de gemas
2. **gatherGemDistance**: Distancia máxima de búsqueda (1-100)
3. **gatherGemNoSecondaryCommander**: No usar comandante secundario
4. **gatherGemUseMultipleImages**: Usar múltiples imágenes para confirmación
5. **gatherGemMinImagesFound**: Mínimo de imágenes para confirmar (1-15)

## 🖼️ Imágenes Requeridas

### Archivos de imagen necesarios:

**Imagen principal:**
- **`resource/GemDeposit.png`** - Imagen principal de la mina de gemas

**Imágenes de confirmación (opcionales):**
- **`resource/GemDeposit1.png`** - Primera imagen de confirmación
- **`resource/GemDeposit2.png`** - Segunda imagen de confirmación
- **`resource/GemDeposit3.png`** - Tercera imagen de confirmación
- **`resource/GemDeposit4.png`** - Cuarta imagen de confirmación
- **`resource/GemDeposit5.png`** - Quinta imagen de confirmación
- **`resource/GemDeposit6.png`** - Sexta imagen de confirmación
- **`resource/GemDeposit7.png`** - Séptima imagen de confirmación
- **`resource/GemDeposit8.png`** - Octava imagen de confirmación
- **`resource/GemDeposit9.png`** - Novena imagen de confirmación
- **`resource/GemDeposit10.png`** - Décima imagen de confirmación
- **`resource/GemDeposit11.png`** - Undécima imagen de confirmación
- **`resource/GemDeposit20.png`** - Duodécima imagen de confirmación
- **`resource/GemDeposit21.png`** - Decimotercera imagen de confirmación
- **`resource/GemDeposit22.png`** - Decimocuarta imagen de confirmación
- **`resource/GemDepositZ1.png`** - Decimoquinta imagen de confirmación

### Cómo obtener las imágenes:

**Captura manual (recomendado):**
1. **Abrir el juego** y ir al mapa
2. **Encontrar minas de gemas** (puntos brillantes en el mapa)
3. **Hacer screenshots** de diferentes minas de gemas
4. **Recortar las imágenes** para incluir solo las minas
5. **Guardar como** `gem_mine.png`, `gem_mine1.png`, etc. en la carpeta `resource/`

### Especificaciones de la imagen:

- **Formato**: PNG
- **Tamaño**: Recomendado 50x50 píxeles
- **Fondo**: Transparente o del color del mapa
- **Contenido**: Solo la mina de gemas brillante

## 🚀 Uso

### 1. Preparación

```bash
# Asegúrate de tener la imagen de gemas
ls resource/gem_mine.png
```

### 2. Configuración

En la GUI del bot:
- ✅ Marcar "Enable Gather Gem"
- 🔢 Ajustar "Gather Gem Distance" (recomendado: 50)
- ✅ Marcar "No Secondary Commander" (recomendado)
- ✅ Marcar "Use Multiple Images" (recomendado: True)
- 🔢 Ajustar "Min Images Found" (recomendado: 3)

### 3. Ejecución

```bash
python3 main.py
```

## 🔍 Debug Mode

Para activar el modo debug y obtener más información:

```python
# En tasks/GatherGem.py, cambiar:
self.debug_mode = True
```

### Logs de debug disponibles:

- `gem_not_found` - No se encontraron gemas
- `gem_gather_button_not_found` - No se puede recolectar
- `gem_new_troops_button_not_found` - No hay espacio para tropas
- `gem_troops_match_button_not_found` - Error al enviar tropas
- `gem_match_query_not_found` - Error en consulta de marchas

## ⚙️ Funcionamiento Interno

### 1. Búsqueda de Gemas
```python
found, _, gempost = self.gui.check_any(ImagePathAndProps.GEM_IMG_PATH.value)
```

### 2. Movimiento en el Mapa
```python
def get_next_move(self, allowed_time=50):
    # Algoritmo de búsqueda sistemática
```

### 3. Recolección
```python
# 1. Tocar en la mina de gemas
# 2. Verificar si es recolectable
# 3. Enviar tropas
# 4. Confirmar marcha
```

## 🐛 Troubleshooting

### Problema: No encuentra gemas
**Solución:**
- Verificar que `GemDeposit.png` existe y es correcta
- Ajustar `gatherGemDistance` a un valor mayor
- Activar debug mode para ver logs detallados

### Problema: No puede recolectar
**Solución:**
- Verificar que hay tropas disponibles
- Comprobar que no hay marchas en curso
- Revisar logs de debug

### Problema: Bot se queda atascado
**Solución:**
- Reducir `gatherGemDistance`
- Verificar que las imágenes están actualizadas
- Revisar logs en tiempo real

## 📊 Métricas

La tarea registra las siguientes métricas:
- **Gemas encontradas** por ciclo
- **Gemas recolectadas** exitosamente
- **Tiempo de búsqueda** promedio
- **Errores** y excepciones

## 🔄 Integración

La tarea está integrada en el bucle principal del bot:

```python
tasks = [
    # ... otras tareas
    [self.gather_gem_task, 'enableGatherGem'],
    # ... más tareas
]
```

## 📝 Notas Importantes

1. **Imagen crítica**: La calidad de `gem_mine.png` es crucial
2. **Configuración**: Ajustar `gatherGemDistance` según el mapa
3. **Tropas**: Asegurar que hay tropas disponibles
4. **Marchas**: Verificar que no hay demasiadas marchas activas
5. **Debug**: Usar modo debug para problemas específicos

## 🎯 Próximas Mejoras

- [ ] **Detección automática** de diferentes tipos de gemas
- [ ] **Priorización** de gemas por valor
- [ ] **Optimización** del algoritmo de búsqueda
- [ ] **Métricas avanzadas** de rendimiento
- [ ] **Configuración granular** por tipo de gema 