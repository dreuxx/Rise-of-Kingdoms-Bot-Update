import requests
import string
import random
import base64
import time
import json
import logging

from io import BytesIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from requests_toolbelt import MultipartEncoder
except ImportError:
    logger.error("requests_toolbelt not found. Install with: pip install requests-toolbelt")
    # Fallback implementation for basic functionality
    class MultipartEncoder:
        def __init__(self, fields):
            raise ImportError("requests_toolbelt is required for 2captcha functionality")

'''
    2captcha API Integration
    Documentation: https://2captcha.com/2captcha-api
    
    Security Note: API key should be provided securely through configuration
'''

# Global API key - should be set through secure configuration
_api_key = None

def set_api_key(api_key):
    """Set API key securely with validation"""
    global _api_key, key
    if not api_key:
        logger.warning("Empty API key provided")
        _api_key = None
        key = None  # Backwards compatibility
        return False
    
    if len(api_key) < 32:
        logger.error("Invalid 2captcha API key format (too short)")
        return False
    
    if not api_key.replace('-', '').isalnum():
        logger.error("Invalid 2captcha API key format (invalid characters)")
        return False
    
    _api_key = api_key
    key = api_key  # Backwards compatibility
    logger.info("2captcha API key set successfully")
    return True

def get_api_key():
    """Get current API key"""
    return _api_key

# Backwards compatibility
key = None  # This will be updated by set_api_key


def send_base64_image(img):
    """Send image to 2captcha with improved error handling"""
    if _api_key is None:
        logger.error("No API key configured for 2captcha")
        return None
    
    # Use HTTPS for secure transmission
    url = 'https://2captcha.com/in.php'
    
    try:
        mp_encoder = MultipartEncoder(
            fields={
                'method': 'base64',
                'coordinatescaptcha': '1',
                'key': _api_key,
                'body': img
            }
        )
        headers = {'Content-Type': mp_encoder.content_type}
        
        # Add timeout and proper error handling
        resp = requests.post(url, data=mp_encoder, headers=headers, timeout=30)
        resp.raise_for_status()  # Raise exception for HTTP errors
        
        resp_text_arr = resp.text.split('|')
        if len(resp_text_arr) >= 2 and resp_text_arr[0] == 'OK':
            task_id = resp_text_arr[1]
            logger.info(f"2captcha task submitted successfully: {task_id}")
            return task_id
        else:
            error_msg = resp.text if resp.text else "Unknown error"
            logger.error(f"2captcha API error: {error_msg}")
            raise RuntimeError(f'2Captcha Error: {error_msg}')
            
    except requests.exceptions.Timeout:
        logger.error("Timeout while sending image to 2captcha")
        raise RuntimeError("2captcha request timed out")
    except requests.exceptions.ConnectionError:
        logger.error("Connection error while contacting 2captcha")
        raise RuntimeError("Failed to connect to 2captcha")
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error from 2captcha: {e}")
        raise RuntimeError(f"2captcha HTTP error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error sending to 2captcha: {e}")
        raise


def get_answer(tid):
    """Get captcha solution with improved error handling"""
    if _api_key is None:
        logger.error("No API key configured for 2captcha")
        return None
    
    if not tid:
        logger.error("No task ID provided")
        return None
    
    # Use HTTPS for secure transmission
    url = f'https://2captcha.com/res.php?key={_api_key}&action=get&id={tid}&json=1'
    
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        
        try:
            return resp.json()
        except json.JSONDecodeError:
            # Fallback to text response for backwards compatibility
            logger.warning("2captcha returned non-JSON response, falling back to text")
            return resp.text
            
    except requests.exceptions.Timeout:
        logger.error("Timeout while getting answer from 2captcha")
        return None
    except requests.exceptions.ConnectionError:
        logger.error("Connection error while contacting 2captcha")
        return None
    except Exception as e:
        logger.error(f"Error getting answer from 2captcha: {e}")
        return None


def refund(tid):
    """Request refund for failed captcha with error handling"""
    if _api_key is None:
        logger.error("No API key configured for 2captcha refund")
        return False
    
    if not tid:
        logger.error("No task ID provided for refund")
        return False
    
    url = f"https://2captcha.com/res.php?key={_api_key}&action=reportbad&id={tid}"
    
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        logger.info(f"Refund requested for task {tid}: {resp.text}")
        return True
    except Exception as e:
        logger.error(f"Error requesting refund for task {tid}: {e}")
        return False


def solve_verification(img, max_wait_time=300):
    """Solve verification captcha with improved error handling"""
    if _api_key is None:
        logger.error("No API key configured for 2captcha")
        return None
    
    if img is None:
        logger.error("No image provided for verification")
        return None
    
    try:
        # Optimize image for better recognition
        img = img.quantize(colors=64, method=2)
        buffered = BytesIO()
        img.save(buffered, format="PNG", optimize=True, quality=5)
        img_base64 = base64.b64encode(buffered.getvalue())

        tid = send_base64_image(img_base64)
        if not tid:
            logger.error("Failed to submit image to 2captcha")
            return None

        logger.info(f"Waiting for 2captcha solution for task {tid}")
        start_time = time.time()
        initial_wait = 5
        time.sleep(initial_wait)

        while time.time() - start_time < max_wait_time:
            try:
                ans = get_answer(tid)
                if ans is None:
                    logger.warning("Failed to get response from 2captcha, retrying...")
                    time.sleep(5)
                    continue
                
                # Handle both JSON and text responses
                if isinstance(ans, str):
                    try:
                        ans = json.loads(ans)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid response format: {ans}")
                        time.sleep(5)
                        continue
                
                if ans.get('status') == 1:
                    # Success
                    points = []
                    try:
                        request_data = ans.get('request', [])
                        if isinstance(request_data, list):
                            for p in request_data:
                                if isinstance(p, dict) and 'x' in p and 'y' in p:
                                    points.append([int(p['x']), int(p['y'])])
                        logger.info(f"2captcha solved successfully with {len(points)} points")
                        return points
                    except (ValueError, KeyError, TypeError) as e:
                        logger.error(f"Error parsing captcha solution: {e}")
                        refund(tid)
                        return None
                        
                elif ans.get('request') == 'CAPCHA_NOT_READY':
                    # Still processing
                    time.sleep(5)
                    continue
                elif ans.get('status') == 0:
                    # Error
                    error_msg = ans.get('request', 'Unknown error')
                    logger.error(f"2captcha error: {error_msg}")
                    raise RuntimeError(f'2Captcha Error: {error_msg}')
                else:
                    logger.warning(f"Unexpected response: {ans}")
                    time.sleep(5)
                    
            except Exception as e:
                logger.error(f"Error during captcha solving: {e}")
                time.sleep(5)

        # Timeout reached
        logger.error(f"Timeout waiting for 2captcha solution (task {tid})")
        refund(tid)
        return None
        
    except Exception as e:
        logger.error(f"Fatal error in solve_verification: {e}")
        return None
