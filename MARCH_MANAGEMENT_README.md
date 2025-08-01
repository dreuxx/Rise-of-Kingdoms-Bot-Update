# 🚀 Sistema de Gestión de Marchas - Rise of Kingdoms Bot

## 📋 Descripción

El **Sistema de Gestión de Marchas** es una mejora inteligente que permite al bot usar las 5 marchas disponibles de manera eficiente, evitando errores cuando no hay espacios disponibles y optimizando el rendimiento general.

## ⚙️ Configuraciones Nuevas

### **Configuraciones Principales:**

| Configuración | Descripción | Valor por Defecto |
|---------------|-------------|-------------------|
| `useAllMarches` | Usar las 5 marchas al máximo | `True` |
| `waitForMarches` | Esperar espacios disponibles | `True` |
| `maxWaitTime` | Tiempo máximo de espera (segundos) | `300` |
| `autoSwitchTasks` | Cambiar tareas automáticamente | `True` |
| `marchPriority` | Prioridad de marchas | `RESOURCE` |

### **Opciones de Prioridad:**
- `RESOURCE` - Prioridad a recursos
- `BARBARIANS` - Prioridad a bárbaros  
- `GEMS` - Prioridad a gemas

## 🎯 Funcionalidades

### **1. Gestión Inteligente de Espacios**
```python
# Verificar si se puede iniciar marcha
if bot.march_manager.can_start_march():
    # Iniciar marcha
    pass
else:
    # Esperar o cambiar tarea
    pass
```

### **2. Espera Inteligente**
```python
# Esperar hasta que haya espacio disponible
if bot.march_manager.wait_for_march_space(timeout=300, task_name="Gather Resource"):
    # Continuar con la tarea
    pass
else:
    # Timeout - cambiar tarea
    pass
```

### **3. Cambio Automático de Tareas**
```python
# Cambiar a tarea que no use marchas
next_task = bot.march_manager.switch_to_available_task()
```

### **4. Optimización de Uso**
```python
# Optimizar uso de marchas
bot.march_manager.optimize_march_usage()
```

## 📊 Monitoreo y Logging

### **Logs Detallados:**
- ✅ `Marchas disponibles: 3/5`
- ⚠️ `Solo quedan 2 espacios de marcha`
- 🔴 `Todas las marchas están ocupadas`
- 📈 `Eficiencia de marchas: 80.0% (4/5)`

### **Estados Visuales:**
- 🟢 **Verde**: Espacios disponibles
- 🟡 **Amarillo**: Pocos espacios (≤2)
- 🔴 **Rojo**: Sin espacios disponibles

## 🔧 Configuración en GUI

### **Nuevas Opciones Disponibles:**

1. **✅ Use All Marches (5/5)**
   - Activa el uso máximo de marchas
   - Desactiva la limitación de `holdOneQuerySpace`

2. **⏳ Wait for March Space**
   - Espera inteligente por espacios disponibles
   - Evita errores por falta de marchas

3. **🔄 Auto Switch Tasks**
   - Cambia automáticamente a tareas sin marchas
   - Mantiene el bot activo sin interrupciones

4. **⏰ Max Wait Time (seconds)**
   - Tiempo máximo de espera por espacios
   - Valor recomendado: 300 segundos (5 minutos)

5. **🎯 March Priority**
   - Define la prioridad de uso de marchas
   - Opciones: RESOURCE, BARBARIANS, GEMS

## 🚀 Estrategias de Uso

### **Estrategia 1: Máximo Rendimiento**
```python
useAllMarches = True
waitForMarches = True
autoSwitchTasks = True
marchPriority = "RESOURCE"
```
**Resultado:** Usa las 5 marchas, espera espacios, cambia tareas automáticamente.

### **Estrategia 2: Balanceado**
```python
useAllMarches = True
waitForMarches = True
autoSwitchTasks = False
marchPriority = "BARBARIANS"
```
**Resultado:** Prioriza bárbaros, espera espacios, no cambia tareas automáticamente.

### **Estrategia 3: Conservador**
```python
useAllMarches = False
holdOneQuerySpace = True
```
**Resultado:** Mantiene 1 espacio libre (comportamiento anterior).

## 📈 Beneficios

### **✅ Sin Errores:**
- Manejo inteligente de espacios ocupados
- Espera automática por espacios disponibles
- Cambio automático de tareas

### **✅ Máximo Rendimiento:**
- Uso de las 5 marchas disponibles
- Optimización automática de prioridades
- Eficiencia mejorada

### **✅ Flexibilidad:**
- Configuraciones avanzadas
- Múltiples estrategias de uso
- Adaptación automática

### **✅ Estabilidad:**
- Sin bloqueos por falta de espacios
- Recuperación automática de errores
- Logging detallado para debugging

## 🔍 Troubleshooting

### **Problema: Bot se queda esperando**
**Solución:**
- Verificar `maxWaitTime` (aumentar si es necesario)
- Revisar logs para ver el estado de marchas
- Verificar que `autoSwitchTasks` esté activado

### **Problema: No cambia de tarea**
**Solución:**
- Verificar que `autoSwitchTasks` esté activado
- Revisar que haya tareas sin marchas disponibles
- Verificar logs de `switch_to_available_task()`

### **Problema: Bajo rendimiento**
**Solución:**
- Activar `useAllMarches = True`
- Configurar `marchPriority` apropiadamente
- Revisar `get_march_efficiency()` en logs

## 📝 Ejemplos de Uso

### **Configuración Recomendada:**
```python
# Configuración óptima para la mayoría de usuarios
{
    "useAllMarches": True,
    "waitForMarches": True,
    "maxWaitTime": 300,
    "autoSwitchTasks": True,
    "marchPriority": "RESOURCE"
}
```

### **Configuración para Bárbaros:**
```python
# Priorizar ataque a bárbaros
{
    "useAllMarches": True,
    "waitForMarches": True,
    "autoSwitchTasks": True,
    "marchPriority": "BARBARIANS"
}
```

### **Configuración para Gemas:**
```python
# Priorizar recolección de gemas
{
    "useAllMarches": True,
    "waitForMarches": True,
    "autoSwitchTasks": True,
    "marchPriority": "GEMS"
}
```

## 🎉 Resultado Final

**¡El bot ahora puede usar las 5 marchas de manera inteligente sin errores!**

- ✅ **Sin interrupciones** por falta de espacios
- ✅ **Máximo rendimiento** con las 5 marchas
- ✅ **Configuración flexible** según necesidades
- ✅ **Logging detallado** para monitoreo
- ✅ **Recuperación automática** de errores

**¡Sistema completamente funcional y optimizado!** 🚀 