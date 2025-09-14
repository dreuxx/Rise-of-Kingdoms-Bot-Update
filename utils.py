from filepath.file_relative_paths import FilePaths

try:
    import cv2
except Exception:
    cv2 = None

try:
    import pytesseract as tess
except Exception:
    tess = None

import sys
import os

import inspect
import ctypes
import requests
import json
import traceback


import threading
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SafeThread(threading.Thread):
    """Thread wrapper with proper shutdown mechanism"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stop_event = threading.Event()
        self.daemon = True
    
    def stop(self):
        """Signal thread to stop gracefully"""
        self._stop_event.set()
    
    def stopped(self):
        """Check if stop was requested"""
        return self._stop_event.is_set()
    
    def run(self):
        """Override this method in subclasses"""
        while not self.stopped():
            # Your thread work here
            pass

def stop_thread(thread):
    """Safely stop a thread - DEPRECATED: Use SafeThread instead"""
    logger.warning("stop_thread() is deprecated and unsafe. Use SafeThread class instead.")
    
    if hasattr(thread, 'stop'):
        # New safe thread
        thread.stop()
        thread.join(timeout=5.0)
        if thread.is_alive():
            logger.error(f"Thread {thread.name} did not stop gracefully")
    else:
        # Legacy thread - try unsafe method as last resort
        logger.warning("Using unsafe thread termination method")
        try:
            _async_raise_legacy(thread.ident, SystemExit)
        except Exception as e:
            logger.error(f"Failed to stop thread unsafely: {e}")

def _async_raise_legacy(tid, exctype):
    """LEGACY UNSAFE METHOD - DO NOT USE FOR NEW CODE"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def build_command(program_path, *args):
    return [program_path, *args]


def img_to_string(pil_image):
    # pil_image.save(resource_path("test.png"))
    tess.pytesseract.tesseract_cmd = resource_path(FilePaths.TESSERACT_EXE_PATH.value)
    result = tess.image_to_string(pil_image, lang='eng', config='--psm 6') \
        .replace('\t', '').replace('\n', '').replace('\f', '')
    return result


def img_remove_background_and_enhance_word(cv_image, lower, upper):
    hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
    return cv2.inRange(hsv, lower, upper)


def aircv_rectangle_to_box(rectangle):
    return rectangle[0][0], rectangle[0][1], rectangle[3][0], rectangle[3][1]


# Global reference to GUI log handler
_gui_log_handler = None

def set_gui_log_handler(handler):
    """Set the GUI log handler for real-time logging"""
    global _gui_log_handler
    _gui_log_handler = handler

def bot_print(msg):
    """Print message to console and GUI if available"""
    print(msg)
    
    # Also send to GUI if handler is available
    if _gui_log_handler is not None:
        try:
            _gui_log_handler.add_log_message(msg, "INFO")
        except Exception as e:
            # Don't let GUI errors break console logging
            print(f"GUI logging error: {e}")

def gui_log(message, level="INFO"):
    """Log message to GUI in real-time"""
    if _gui_log_handler is not None:
        try:
            _gui_log_handler.add_log_message(message, level)
        except Exception as e:
            print(f"GUI logging error: {e}")
    else:
        # Fallback to console if GUI not available
        print(f"[{level}] {message}")

def check_bot_health():
    """Check if bot is responsive and not frozen"""
    import psutil
    import os
    
    try:
        # Get current process
        current_process = psutil.Process(os.getpid())
        
        # Check CPU usage (if too high, might be stuck)
        cpu_percent = current_process.cpu_percent(interval=0.1)
        
        # Check memory usage
        memory_info = current_process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        # Log health metrics
        gui_log(f"CPU: {cpu_percent:.1f}%, Memoria: {memory_mb:.1f}MB", "INFO")
        
        # Warning if resources are high
        if cpu_percent > 80:
            gui_log(f"Advertencia: Alto uso de CPU ({cpu_percent:.1f}%)", "WARNING")
        if memory_mb > 500:
            gui_log(f"Advertencia: Alto uso de memoria ({memory_mb:.1f}MB)", "WARNING")
            
        return True
        
    except Exception as e:
        gui_log(f"Error al verificar salud del bot: {e}", "ERROR")
        return False

def safe_operation(operation_name, timeout=30):
    """Execute operation with timeout to prevent freezing"""
    import threading
    import time
    
    def operation_wrapper():
        try:
            gui_log(f"Iniciando operación: {operation_name}", "INFO")
            # Here you would call the actual operation
            time.sleep(0.1)  # Simulate work
            gui_log(f"Operación completada: {operation_name}", "SUCCESS")
        except Exception as e:
            gui_log(f"Error en operación {operation_name}: {e}", "ERROR")
    
    # Run operation in separate thread with timeout
    thread = threading.Thread(target=operation_wrapper)
    thread.daemon = True
    thread.start()
    
    # Wait for completion with timeout
    thread.join(timeout=timeout)
    
    if thread.is_alive():
        gui_log(f"Operación {operation_name} excedió el timeout de {timeout}s", "ERROR")
        return False
    
    return True


def safe_request_get(url, timeout=10, retries=3):
    """Make HTTP request with timeout and retry logic"""
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()  # Raise exception for bad status codes
            return response
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout on attempt {attempt + 1} for URL: {url}")
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error on attempt {attempt + 1} for URL: {url}")
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {e.response.status_code} for URL: {url}")
            break  # Don't retry HTTP errors
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
        
        if attempt < retries - 1:
            import time
            time.sleep(2 ** attempt)  # Exponential backoff
    
    return None

def get_last_info():
    """Get latest version info with improved error handling"""
    try:
        url = 'https://raw.githubusercontent.com/Dylan-Zheng/Rise-of-Kingdoms-Bot/main/docs/version.json'
        response = safe_request_get(url)
        
        if response is None:
            logger.error("Failed to fetch version info after all retries")
            return {}
        
        try:
            data = response.json()
            logger.info("Version info retrieved successfully")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in version info: {e}")
            return {}
            
    except Exception as e:
        logger.error(f"Unexpected error getting version info: {e}")
        return {}


class MarchManager:
    """Sistema inteligente para gestionar las marchas del bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.max_marches = 5
        self.current_marches = 0
        self.waiting_tasks = []
        self.last_check_time = 0
        self.check_interval = 5  # segundos entre verificaciones
        
    def get_available_marches(self):
        """Obtener número de marchas disponibles"""
        try:
            curr_q, max_q = self.bot.gui.match_query_to_string()
            if curr_q is None or max_q is None:
                logger.warning("No se pudo leer el estado de marchas, usando valor por defecto")
                return self.max_marches
            available = max_q - curr_q
            self.current_marches = curr_q
            logger.info(f"Marchas disponibles: {available}/{max_q}")
            return available
        except Exception as e:
            logger.error(f"Error al obtener marchas disponibles: {e}")
            return 0
    
    def can_start_march(self):
        """Verificar si se puede iniciar una nueva marcha"""
        available = self.get_available_marches()
        can_start = available > 0
        
        if can_start:
            logger.info(f"✅ Se puede iniciar marcha. Espacios disponibles: {available}")
        else:
            logger.warning(f"❌ No hay espacios de marcha disponibles")
            
        return can_start
    
    def wait_for_march_space(self, timeout=300, task_name="Tarea"):
        """Esperar hasta que haya espacio de marcha disponible"""
        start_time = time.time()
        logger.info(f"⏳ {task_name}: Esperando espacio de marcha (timeout: {timeout}s)")
        
        while time.time() - start_time < timeout:
            if self.can_start_march():
                logger.info(f"✅ {task_name}: Espacio de marcha disponible")
                return True
                
            elapsed = int(time.time() - start_time)
            remaining = timeout - elapsed
            logger.info(f"⏳ {task_name}: Esperando... ({elapsed}/{timeout}s restantes: {remaining}s)")
            
            time.sleep(self.check_interval)
        
        logger.error(f"⏰ {task_name}: Timeout esperando espacio de marcha")
        return False
    
    def optimize_march_usage(self):
        """Optimizar el uso de marchas basado en prioridades"""
        available = self.get_available_marches()
        
        if available == 0:
            logger.warning("No hay marchas disponibles para optimizar")
            return False
            
        # Prioridades: Bárbaros > Gemas > Recursos
        priorities = {
            'barbarians': 3,  # Alta prioridad
            'gems': 2,        # Media prioridad  
            'resources': 1     # Baja prioridad
        }
        
        logger.info(f"🔧 Optimizando uso de {available} marchas disponibles")
        return True
    
    def switch_to_available_task(self):
        """Cambiar a una tarea que no use marchas cuando no hay espacio"""
        logger.info("🔄 Cambiando a tarea sin marchas")
        
        # Tareas que no usan marchas
        available_tasks = [
            'training',      # Entrenamiento
            'tavern',        # Taberna
            'materials',     # Materiales
            'collecting',    # Recolección de recompensas
            'quests',        # Misiones
            'alliance'       # Alianza
        ]
        
        for task in available_tasks:
            if self.bot.config.__dict__.get(f'enable{task.capitalize()}', False):
                logger.info(f"✅ Cambiando a tarea: {task}")
                return task
                
        logger.warning("❌ No hay tareas disponibles sin marchas")
        return None
    
    def log_march_status(self):
        """Registrar el estado actual de las marchas"""
        try:
            curr_q, max_q = self.bot.gui.match_query_to_string()
            if curr_q is not None and max_q is not None:
                available = max_q - curr_q
                status_emoji = "🟢" if available > 0 else "🔴"
                logger.info(f"{status_emoji} Estado de marchas: {curr_q}/{max_q} (Disponibles: {available})")
                
                # Log detailed status
                if available == 0:
                    logger.warning("⚠️ Todas las marchas están ocupadas")
                elif available <= 2:
                    logger.warning(f"⚠️ Solo quedan {available} espacios de marcha")
                else:
                    logger.info(f"✅ {available} espacios de marcha disponibles")
                    
            else:
                logger.warning("❓ No se pudo leer el estado de marchas")
        except Exception as e:
            logger.error(f"Error al registrar estado de marchas: {e}")
    
    def get_march_efficiency(self):
        """Calcular la eficiencia de uso de marchas"""
        try:
            curr_q, max_q = self.bot.gui.match_query_to_string()
            if curr_q is not None and max_q is not None:
                efficiency = (curr_q / max_q) * 100
                logger.info(f"📈 Eficiencia de marchas: {efficiency:.1f}% ({curr_q}/{max_q})")
                return efficiency
            return 0
        except Exception as e:
            logger.error(f"Error al calcular eficiencia de marchas: {e}")
            return 0

