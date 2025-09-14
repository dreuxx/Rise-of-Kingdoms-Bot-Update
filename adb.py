try:
    from ppadb.client import Client as PPADBClient
except Exception:
    PPADBClient = None

from utils import resource_path
from utils import build_command
from filepath.file_relative_paths import FilePaths
import subprocess
import traceback
import logging
import time
import shutil
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bridge = None


class Adb:
    """Enhanced ADB client with improved error handling and security"""

    def __init__(self, host='127.0.0.1', port=5037):
        """Initialize ADB client with validation"""
        try:
            if PPADBClient is None:
                raise RuntimeError('ppadb (pure-python-adb) is not installed. Please install with: pip install pure-python-adb')
            # Validate host and port
            if not self._validate_host(host):
                raise ValueError(f"Invalid host address: {host}")
            if not self._validate_port(port):
                raise ValueError(f"Invalid port number: {port}")
                
            self.host = host
            self.port = port
            self.client = PPADBClient(host, port)
            logger.info(f"ADB client initialized for {host}:{port}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ADB client: {e}")
            raise

    def _validate_host(self, host):
        """Validate host address format"""
        if not host or not isinstance(host, str):
            return False
        # Basic IP validation (can be enhanced)
        parts = host.split('.')
        if len(parts) == 4 and host != '0.0.0.0':
            try:
                return all(0 <= int(part) <= 255 for part in parts)
            except ValueError:
                pass
        # Also allow localhost
        return host in ['localhost', '127.0.0.1']

    def _validate_port(self, port):
        """Validate port number"""
        try:
            port_int = int(port)
            return 1024 <= port_int <= 65535  # Safe port range
        except (ValueError, TypeError):
            return False

    def connect_to_device(self, host='127.0.0.1', port=5555, retries=3):
        """Connect to device with improved error handling and retries"""
        if not self._validate_host(host) or not self._validate_port(port):
            raise ValueError(f"Invalid connection parameters: {host}:{port}")
            
        adb_path = resource_path(FilePaths.ADB_EXE_PATH.value)
        # Prefer system adb if available and executable
        system_adb = shutil.which('adb')
        if system_adb:
            adb_path = system_adb

        target = f"{host}:{port}"
        cmd = [adb_path, 'connect', target]
        
        for attempt in range(retries):
            try:
                logger.info(f"Attempting to connect to {target} (attempt {attempt + 1}/{retries})")
                
                ret = subprocess.check_output(
                    cmd,
                    shell=False,
                    stderr=subprocess.PIPE,
                    encoding="utf-8",
                    timeout=10  # Increased timeout
                )
                
                logger.info(f"ADB connect result: {ret.strip()}")
                
                # Verify connection worked
                device = self.get_device(host, port)
                if device is not None:
                    logger.info(f"Successfully connected to {target}")
                    return device
                else:
                    logger.warning(f"Connection appeared successful but device not available")
                    
            except subprocess.TimeoutExpired:
                logger.warning(f"Connection timeout on attempt {attempt + 1}")
            except subprocess.CalledProcessError as e:
                logger.warning(f"ADB connect failed on attempt {attempt + 1}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            
            if attempt < retries - 1:
                time.sleep(2)  # Wait before retry
                
        raise RuntimeError(f"Failed to connect to {target} after {retries} attempts")

    def get_client_devices(self):
        """Get list of connected devices with error handling"""
        try:
            devices = self.client.devices()
            logger.info(f"Found {len(devices)} connected devices")
            return devices
        except Exception as e:
            logger.error(f"Error getting device list: {e}")
            return []

    def get_device(self, host='127.0.0.1', port=5555):
        """Get device with improved error handling"""
        if not self._validate_host(host) or not self._validate_port(port):
            logger.error(f"Invalid device parameters: {host}:{port}")
            return None
            
        target = f"{host}:{port}"
        
        try:
            device = self.client.device(target)
            
            # Test if device is responsive
            if device is not None:
                try:
                    # Simple test command
                    device.shell('echo test', timeout=5)
                    logger.info(f"Device {target} is responsive")
                    return device
                except Exception as e:
                    logger.warning(f"Device {target} not responsive: {e}")
                    device = None
            
            if device is None:
                logger.info(f"Device {target} not found, attempting to connect")
                return self.connect_to_device(host, port)
                
        except Exception as e:
            logger.error(f"Error accessing device {target}: {e}")
            
        return None


def enable_adb(host='127.0.0.1', port=5037, required_version=41):
    """Enable ADB with improved error handling and validation"""
    
    if not isinstance(required_version, int) or required_version <= 0:
        raise ValueError(f"Invalid required version: {required_version}")
    
    logger.info(f"Initializing ADB connection to {host}:{port}")
    
    # First attempt - try to connect to existing server
    try:
        adb = Adb(host, port)
        version = adb.client.version()
        logger.info(f"Connected to existing ADB server, version: {version}")
        
        if version == required_version:
            logger.info("ADB version matches requirements")
            return adb
        else:
            logger.warning(f"ADB version mismatch: required {required_version}, found {version}")
            # Continue to restart server with correct version
            
    except Exception as e:
        logger.info(f"Could not connect to existing ADB server: {e}")
        # Continue to start new server

    # Restart ADB server
    try:
        adb_path = resource_path(FilePaths.ADB_EXE_PATH.value)
        # Prefer system adb if available and executable
        system_adb = shutil.which('adb')
        if system_adb:
            adb_path = system_adb

        # Normalize path for Windows-style paths in repo on Linux
        adb_path = os.path.normpath(adb_path)
        logger.info(f"Using ADB executable: {adb_path}")
        
        # Kill existing server
        logger.info("Stopping existing ADB server")
        kill_cmd = [adb_path, '-P', str(port), 'kill-server']
        ret = subprocess.run(
            kill_cmd,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            timeout=10
        )
        
        if ret.returncode != 0:
            logger.warning(f"ADB kill-server returned {ret.returncode}: {ret.stderr}")
        else:
            logger.info("ADB server stopped successfully")
        
        # Wait a moment for cleanup
        time.sleep(1)
        
        # Start new server
        logger.info("Starting new ADB server")
        start_cmd = [adb_path, '-P', str(port), 'start-server']
        ret = subprocess.run(
            start_cmd,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            timeout=15
        )

        if ret.returncode != 0:
            error_msg = f"Failed to start ADB server. Return code: {ret.returncode}"
            if ret.stderr:
                error_msg += f"\nError output: {ret.stderr}"
            if ret.stdout:
                error_msg += f"\nStandard output: {ret.stdout}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        logger.info("ADB server started successfully")
        
        # Wait for server to be ready
        time.sleep(2)
        
        # Verify new connection
        adb = Adb(host, port)
        version = adb.client.version()
        logger.info(f"New ADB server version: {version}")
        
        if version != required_version:
            logger.error(f"ADB version still incorrect after restart: {version} (required: {required_version})")
            raise RuntimeError(f"ADB version mismatch: required {required_version}, got {version}")
        
        logger.info("ADB enabled successfully")
        return adb
        
    except subprocess.TimeoutExpired:
        logger.error("Timeout while managing ADB server")
        raise RuntimeError("ADB server operation timed out")
    except Exception as e:
        logger.error(f"Fatal error enabling ADB: {e}")
        raise RuntimeError(f"Failed to enable ADB: {e}")
