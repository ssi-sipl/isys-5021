import ctypes
from ctypes import c_uint8, c_uint16, c_uint32, c_float, POINTER, Structure, byref
import time
import logging
from enum import IntEnum
from typing import List, Tuple, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("iSYS5021Radar")

# Constants from the header files
ETH_MAX_TARGETS = 512


# Enum types from the header files
class ETHResult(IntEnum):
    ETH_ERR_OK = 0x0000
    ETH_ERR_HANDLE_NOT_INITIALISED = 0x0001
    ETH_ERR_SYSTEM_ALREADY_INITIALISED = 0x0002
    ETH_ERR_SYSTEM_NOT_INITIALISED = 0x0003
    ETH_ERR_CREATE_HANDLE = 0x0004
    ETH_ERR_NULL_POINTER = 0x0005
    ETH_ERR_FUNCTION_DEPRECATED = 0x0006
    ETH_ERR_PORT_ALREADY_INITIALISED = 0x0007
    ETH_ERR_PORT_IN_USE = 0x0008
    ETH_ERR_CONNECTION_CLOSED = 0x0009
    ETH_ERR_CONNECTION_RESET = 0x000A
    ETH_ERR_COMMUNICATION_TIMEOUT = 0x000B
    ETH_ERR_COMMUNICATION_ERROR = 0x000C
    ETH_ERR_CONNECTION_LOST = 0x000D
    ETH_ERR_TARGET_NOT_ENOUGH_DATA_AVAILABLE = 0x000E
    ETH_ERR_TARGET_DATA_CORRUPTED = 0x000F
    ETH_ERR_TARGET_DATA_SIZE = 0x0010
    ETH_ERR_RAW_NOT_ENOUGH_DATA_AVAILABLE = 0x0011
    ETH_ERR_RAW_DATA_CORRUPTED = 0x0012
    ETH_ERR_RAW_DATA_SIZE = 0x0013
    ETH_ERR_MUTEX_ERROR = 0x0014
    ETH_ERR_NETWORK_INTERFACE = 0x0015


class ETHTargetListError(IntEnum):
    ETH_TARGET_LIST_OK = 0x00
    ETH_TARGET_LIST_FULL = 0x01
    ETH_TARGET_LIST_ALREADY_REQUESTED = 0x02
    ETH_TARGET_LIST_NOT_ACTIVE = 0x03
    ETH_TARGET_LIST_DATA_CORRUPTED = 0x04


# Structures from the header files
class ETHTargetListError_u(Structure):
    _fields_ = [
        ("ETHTargetListError", c_uint32)
    ]


class ETHTarget(Structure):
    _fields_ = [
        ("signalStrength", c_float),  # [dB]
        ("range", c_float),           # [m]
        ("velocity", c_float),        # [m/s]
        ("angleAzimuth", c_float),    # [°]
        ("reserved1", c_float),
        ("reserved2", c_float)
    ]


class ETHTargetList(Structure):
    _fields_ = [
        ("ETHTargetListError", ETHTargetListError_u),
        ("targetList", ETHTarget * ETH_MAX_TARGETS),
        ("nrOfTargets", c_uint16),
        ("frameID", c_uint16)
    ]


class RadarError(Exception):
    """Base exception for radar errors."""
    def __init__(self, result_code: ETHResult, message: str = None):
        self.result_code = result_code
        self.message = message or f"Radar error: {result_code.name}"
        super().__init__(self.message)


class Target:
    """Python class representation of a radar target with additional metadata."""
    def __init__(self, eth_target: ETHTarget):
        self.signal_strength = eth_target.signalStrength  # dB
        self.range = eth_target.range                     # m
        self.velocity = eth_target.velocity               # m/s
        self.angle_azimuth = eth_target.angleAzimuth      # degrees
        
    def __str__(self) -> str:
        return (f"Target: Range={self.range:.2f}m, Velocity={self.velocity:.2f}m/s, "
                f"Angle={self.angle_azimuth:.2f}°, Signal={self.signal_strength:.2f}dB")


class iSYS5021Radar:
    """Python wrapper for the InnoSenT iSYS-5021 radar."""
    
    def __init__(self, dll_path):
        self.handle = None
        self.connected = False
        
        try:
            # Load the DLL
            self.dll = ctypes.CDLL(dll_path)
            
            # Define argument and return types for DLL functions
            self._setup_dll_functions()
            
            # Check API version
            self.api_version = self._get_api_version()
            logger.info(f"Loaded InnoSenT API version {self.api_version}")
            
        except OSError as e:
            logger.error(f"Failed to load DLL: {e}")
            raise
            
    def _setup_dll_functions(self):
        """Set up the function signatures for the DLL functions."""
        # ETH_initSystem
        self.dll.ETH_initSystem.argtypes = [
            POINTER(ctypes.c_void_p),  # ETHHandle_t *pHandle
            c_uint8,                   # uint8_t ipPart1
            c_uint8,                   # uint8_t ipPart2
            c_uint8,                   # uint8_t ipPart3
            c_uint8,                   # uint8_t ipPart4
            c_uint32                   # uint32_t udpPortNumber
        ]
        self.dll.ETH_initSystem.restype = c_uint32  # ETHResult_t
        
        # ETH_exitSystem
        self.dll.ETH_exitSystem.argtypes = [ctypes.c_void_p]  # ETHHandle_t pHandle
        self.dll.ETH_exitSystem.restype = c_uint32  # ETHResult_t
        
        # ETH_getApiVersion
        self.dll.ETH_getApiVersion.argtypes = [POINTER(c_float)]  # float32_t *version
        self.dll.ETH_getApiVersion.restype = c_uint32  # ETHResult_t
        
        # ETH_getTargetList
        self.dll.ETH_getTargetList.argtypes = [
            ctypes.c_void_p,           # ETHHandle_t pHandle
            POINTER(ETHTargetList)     # ETHTargetList_t *pTargetList
        ]
        self.dll.ETH_getTargetList.restype = c_uint32  # ETHResult_t
    
    def _get_api_version(self) -> float:
        """Get the API version from the DLL.
        
        Returns:
            The API version as a float
        """
        version = c_float()
        result = self.dll.ETH_getApiVersion(byref(version))
        
        if result != ETHResult.ETH_ERR_OK:
            raise RadarError(ETHResult(result), "Failed to get API version")
            
        return version.value
    
    def _check_result(self, result: int, error_message: str):
        """Check the result code and raise an exception if it's not OK.
        
        Args:
            result: The result code from the API function
            error_message: The error message to include in the exception
            
        Raises:
            RadarError: If the result is not ETH_ERR_OK
        """
        if result != ETHResult.ETH_ERR_OK:
            logger.error(f"{error_message}: {ETHResult(result).name}")
            raise RadarError(ETHResult(result), f"{error_message}: {ETHResult(result).name}")
    
    def connect(self, ip_address: str, port: int = 45454) -> None:
        """Connect to the radar device.
        
        Args:
            ip_address: The IP address of the radar in format "xxx.xxx.xxx.xxx"
            port: The UDP port number (default: 45454)
            
        Raises:
            ValueError: If the IP address format is invalid
            RadarError: If the connection fails
        """
        if self.connected:
            logger.warning("Already connected to radar. Disconnecting first.")
            self.disconnect()
            
        # Parse IP address
        try:
            ip_parts = [int(part) for part in ip_address.split(".")]
            if len(ip_parts) != 4 or any(part < 0 or part > 255 for part in ip_parts):
                raise ValueError("Invalid IP address format")
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid IP address format: {ip_address}")
        
        # Create handle pointer
        handle_ptr = ctypes.c_void_p()
        
        # Initialize system
        logger.info(f"Connecting to radar at {ip_address}:{port}")
        result = self.dll.ETH_initSystem(
            byref(handle_ptr),
            c_uint8(ip_parts[0]), 
            c_uint8(ip_parts[1]), 
            c_uint8(ip_parts[2]), 
            c_uint8(ip_parts[3]),
            c_uint32(port)
        )
        
        self._check_result(result, f"Failed to connect to radar at {ip_address}:{port}")
        
        self.handle = handle_ptr
        self.connected = True
        logger.info(f"Successfully connected to radar at {ip_address}:{port}")
        
    def disconnect(self) -> None:
        """Disconnect from the radar device.
        
        Raises:
            RadarError: If the disconnection fails
        """
        if not self.connected or not self.handle:
            logger.warning("Not connected to radar")
            return
            
        logger.info("Disconnecting from radar")
        result = self.dll.ETH_exitSystem(self.handle)
        
        # Even if there's an error, we'll consider ourselves disconnected
        self.connected = False
        self.handle = None
        
        self._check_result(result, "Failed to disconnect from radar")
        logger.info("Successfully disconnected from radar")
    
    def get_targets(self) -> List[Target]:
        """Get the current list of targets from the radar.
        
        Returns:
            A list of Target objects
            
        Raises:
            RadarError: If the radar is not connected or the target list retrieval fails
        """
        if not self.connected or not self.handle:
            raise RadarError(ETHResult.ETH_ERR_HANDLE_NOT_INITIALISED, "Not connected to radar")
            
        # Create target list structure
        target_list = ETHTargetList()
        
        # Get target list
        result = self.dll.ETH_getTargetList(self.handle, byref(target_list))
        self._check_result(result, "Failed to get target list")
        
        # Check target list error
        target_list_error = target_list.ETHTargetListError.ETHTargetListError
        if target_list_error != ETHTargetListError.ETH_TARGET_LIST_OK:
            logger.warning(f"Target list error: {ETHTargetListError(target_list_error).name}")
            
        # Convert targets to Python objects
        targets = []
        for i in range(target_list.nrOfTargets):
            if i >= ETH_MAX_TARGETS:
                logger.warning(f"Target list exceeded maximum capacity ({ETH_MAX_TARGETS})")
                break
                
            targets.append(Target(target_list.targetList[i]))
            
        logger.debug(f"Retrieved {len(targets)} targets (frame ID: {target_list.frameID})")
        return targets
        
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic disconnect."""
        self.disconnect()

def main():

    RADAR_IP = "192.168.252.2"
    RADAR_PORT = 2050
    
    # radar = iSYS5021Radar("./Docs/EthernetAPI/library_v1.3/Linux_x64/libethernetAPI.so")
    radar = iSYS5021Radar("Docs/EthernetAPI/library_v1.3/Linux_aarch64/libethernetAPI.so")
    try:
        print(f"Radar API Version: {radar._get_api_version()}")

        print(f"Connecting to radar at {RADAR_IP}:{RADAR_PORT}")
        radar.connect(RADAR_IP, RADAR_PORT)
        time.sleep(1)

        # radar.set_simulation(0)
        print("Simulation mode: ", "True" if radar.get_simulation() == 1 else "False")

        while True:      
            # objects = radar.get_object_list()
            # parse_object_list(objects)
            # time.sleep(0.1)

            targets = radar.get_targets()
            print(f"Found {len(targets)} targets:")
                
            for i, target in enumerate(targets):
                print(f"  {i+1}: {target}")
                    
            # Sleep briefly to avoid flooding the console
            time.sleep(0.5)
    except RadarError as e:
        print(f"Radar error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        radar.disconnect()

if __name__ == "__main__":
    main()