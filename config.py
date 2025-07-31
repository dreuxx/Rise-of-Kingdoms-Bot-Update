import json
import logging
import os
from utils import resource_path
from cryptography.fernet import Fernet
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HAO_I = 'haoi'
TWO_CAPTCHA = '2captcha'
NONE = 'none'

# Security: Generate or load encryption key
def get_encryption_key():
    """Get or generate encryption key for sensitive data"""
    key_file = resource_path('.config_key')
    if os.path.exists(key_file):
        try:
            with open(key_file, 'rb') as f:
                return f.read()
        except (IOError, OSError) as e:
            logger.warning(f"Could not read encryption key: {e}")
    
    # Generate new key if none exists
    key = Fernet.generate_key()
    try:
        with open(key_file, 'wb') as f:
            f.write(key)
        os.chmod(key_file, 0o600)  # Restrict permissions
    except (IOError, OSError) as e:
        logger.error(f"Could not save encryption key: {e}")
    
    return key

def encrypt_sensitive_data(data):
    """Encrypt sensitive data like API keys"""
    if not data:
        return None
    try:
        key = get_encryption_key()
        f = Fernet(key)
        return f.encrypt(data.encode()).decode()
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        return None

def decrypt_sensitive_data(encrypted_data):
    """Decrypt sensitive data like API keys"""
    if not encrypted_data:
        return None
    try:
        key = get_encryption_key()
        f = Fernet(key)
        return f.decrypt(encrypted_data.encode()).decode()
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        return None

def validate_api_key(key, service_name):
    """Validate API key format"""
    if not key:
        return False
    
    # Basic validation based on service
    if service_name == 'twocaptcha':
        return len(key) >= 32 and key.isalnum()
    elif service_name == 'haoi':
        return len(key) >= 10
    
    return len(key) >= 8

def load_config():
    """Load configuration with improved error handling"""
    config = None
    try:
        config_path = resource_path('config.json')
        if not os.path.exists(config_path):
            logger.info("Config file not found, creating default configuration")
            config = Config({})
            write_config(config)
            return config
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config_json = json.load(f)
            config = Config(config_json)
            logger.info("Configuration loaded successfully")
            
    except (FileNotFoundError, PermissionError) as e:
        logger.error(f"File access error: {e}")
        config = Config({})
        write_config(config)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}")
        # Backup corrupted config
        backup_corrupted_config()
        config = Config({})
        write_config(config)
    except Exception as e:
        logger.error(f"Unexpected error loading config: {e}")
        config = Config({})
        write_config(config)
        
    return config

def backup_corrupted_config():
    """Backup corrupted configuration file"""
    try:
        import shutil
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"config_corrupted_{timestamp}.json"
        shutil.copy2(resource_path('config.json'), resource_path(backup_name))
        logger.info(f"Corrupted config backed up as {backup_name}")
    except Exception as e:
        logger.error(f"Could not backup corrupted config: {e}")


def write_config(config):
    """Write configuration with improved error handling"""
    try:
        config_data = config.to_dict()
        config_json = json.dumps(config_data, indent=2)
        config_path = resource_path("config.json")
        
        # Create backup before writing
        if os.path.exists(config_path):
            backup_path = config_path + '.backup'
            try:
                import shutil
                shutil.copy2(config_path, backup_path)
            except Exception as e:
                logger.warning(f"Could not create config backup: {e}")
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_json)
        
        # Set secure file permissions
        try:
            os.chmod(config_path, 0o600)
        except (OSError, AttributeError) as e:
            logger.warning(f"Could not set secure file permissions: {e}")
            
        logger.info("Configuration saved successfully")
        
    except (IOError, OSError) as e:
        logger.error(f"Failed to write config file: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error writing config: {e}")
        raise


class Config:
    """Enhanced configuration class with security improvements"""
    
    def __init__(self, config=None):
        if config is None:
            config = {}
            
        # Basic settings
        self.screenSize = config.get('screenSize', [470, 850])
        self.method = config.get('method', NONE)
        
        # Handle encrypted sensitive data
        encrypted_haoi_user = config.get('haoiUser_encrypted')
        encrypted_haoi_rebate = config.get('haoiRebate_encrypted') 
        encrypted_twocaptcha_key = config.get('twocaptchaKey_encrypted')
        
        # For backwards compatibility, check for unencrypted data
        plain_haoi_user = config.get('haoiUser')
        plain_haoi_rebate = config.get('haoiRebate')
        plain_twocaptcha_key = config.get('twocaptchaKey')
        
        # Decrypt or use plain data (with migration)
        self._haoiUser = self._handle_sensitive_data(encrypted_haoi_user, plain_haoi_user)
        self._haoiRebate = self._handle_sensitive_data(encrypted_haoi_rebate, plain_haoi_rebate)
        self._twocaptchaKey = self._handle_sensitive_data(encrypted_twocaptcha_key, plain_twocaptcha_key)
        
        # Validate sensitive data
        self._validate_sensitive_data()
    
    def _handle_sensitive_data(self, encrypted_value, plain_value):
        """Handle both encrypted and plain sensitive data for migration"""
        if encrypted_value:
            decrypted = decrypt_sensitive_data(encrypted_value)
            if decrypted:
                return decrypted
            else:
                logger.warning("Failed to decrypt sensitive data, falling back to plain")
        
        return plain_value
    
    def _validate_sensitive_data(self):
        """Validate all sensitive configuration data"""
        if self._twocaptchaKey and not validate_api_key(self._twocaptchaKey, 'twocaptcha'):
            logger.warning("Invalid 2captcha API key format")
            
        if self._haoiUser and not validate_api_key(self._haoiUser, 'haoi'):
            logger.warning("Invalid haoi user key format")
    
    @property
    def haoiUser(self):
        return self._haoiUser
    
    @haoiUser.setter 
    def haoiUser(self, value):
        if value and validate_api_key(value, 'haoi'):
            self._haoiUser = value
        else:
            logger.warning("Invalid haoi user key provided")
            
    @property
    def haoiRebate(self):
        return self._haoiRebate
        
    @haoiRebate.setter
    def haoiRebate(self, value):
        self._haoiRebate = value
        
    @property 
    def twocaptchaKey(self):
        return self._twocaptchaKey
        
    @twocaptchaKey.setter
    def twocaptchaKey(self, value):
        if value and validate_api_key(value, 'twocaptcha'):
            self._twocaptchaKey = value
        else:
            logger.warning("Invalid 2captcha API key provided")
    
    def to_dict(self):
        """Convert config to dictionary with encrypted sensitive data"""
        return {
            'screenSize': self.screenSize,
            'method': self.method,
            'haoiUser_encrypted': encrypt_sensitive_data(self._haoiUser) if self._haoiUser else None,
            'haoiRebate_encrypted': encrypt_sensitive_data(self._haoiRebate) if self._haoiRebate else None,
            'twocaptchaKey_encrypted': encrypt_sensitive_data(self._twocaptchaKey) if self._twocaptchaKey else None
        }



global_config = Config()
