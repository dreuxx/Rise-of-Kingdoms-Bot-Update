from filepath.file_relative_paths import FilePaths

import cv2
import pytesseract as tess
import sys
import os

import inspect
import ctypes
import requests
import json
import traceback


import threading
import logging

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


def bot_print(msg):
    print(msg)


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

