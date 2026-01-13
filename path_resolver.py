"""
Path Resolver for TezgahTakip Update System
Handles dynamic path detection and multi-location search for critical files
"""

import os
import sys
import platform
from pathlib import Path
from typing import Optional, List, Dict
import logging


class PathResolver:
    """
    Resolves paths for critical application files, especially base_library.zip
    """
    
    def __init__(self):
        self.logger = logging.getLogger("PathResolver")
        self.system_info = self._get_system_info()
        self.executable_dir = self._detect_executable_directory()
        self.search_paths = self._initialize_search_paths()
        
        self.logger.debug(f"PathResolver initialized for {self.system_info}")
        self.logger.debug(f"Executable directory: {self.executable_dir}")
    
    def _get_system_info(self) -> Dict[str, str]:
        """Get system information for path resolution"""
        return {
            'platform': platform.system(),
            'architecture': platform.architecture()[0],
            'python_version': platform.python_version(),
            'executable': sys.executable
        }
    
    def _detect_executable_directory(self) -> str:
        """
        Detect the directory where the executable is located
        """
        try:
            # Try to get the directory of the frozen executable
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                if hasattr(sys, '_MEIPASS'):
                    # PyInstaller temporary directory
                    executable_dir = os.path.dirname(sys.executable)
                else:
                    # Other freezing methods
                    executable_dir = os.path.dirname(sys.executable)
            else:
                # Running as script
                executable_dir = os.path.dirname(os.path.abspath(__file__))
            
            self.logger.debug(f"Detected executable directory: {executable_dir}")
            return executable_dir
            
        except Exception as e:
            self.logger.error(f"Failed to detect executable directory: {e}")
            # Fallback to current working directory
            return os.getcwd()
    
    def _initialize_search_paths(self) -> List[str]:
        """
        Initialize list of paths to search for critical files
        """
        paths = []
        
        # Primary paths
        paths.append(self.executable_dir)
        paths.append(os.getcwd())
        
        # PyInstaller specific paths
        if hasattr(sys, '_MEIPASS'):
            paths.append(sys._MEIPASS)
        
        # Common installation directories
        if self.system_info['platform'] == 'Windows':
            # Windows specific paths
            program_files = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
            program_files_x86 = os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')
            
            paths.extend([
                os.path.join(program_files, 'TezgahTakip'),
                os.path.join(program_files_x86, 'TezgahTakip'),
                os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'TezgahTakip'),
                os.path.join(os.path.expanduser('~'), 'Documents', 'TezgahTakip')
            ])
        
        # User directory paths
        user_home = os.path.expanduser('~')
        paths.extend([
            os.path.join(user_home, 'TezgahTakip'),
            os.path.join(user_home, 'Desktop', 'TezgahTakip'),
            os.path.join(user_home, 'Downloads', 'TezgahTakip')
        ])
        
        # Relative paths from executable
        exe_parent = os.path.dirname(self.executable_dir)
        paths.extend([
            exe_parent,
            os.path.join(exe_parent, 'lib'),
            os.path.join(exe_parent, 'libs'),
            os.path.join(exe_parent, 'resources'),
            os.path.join(self.executable_dir, 'lib'),
            os.path.join(self.executable_dir, 'libs'),
            os.path.join(self.executable_dir, 'resources')
        ])
        
        # Remove duplicates while preserving order
        unique_paths = []
        for path in paths:
            if path not in unique_paths:
                unique_paths.append(path)
        
        self.logger.debug(f"Initialized {len(unique_paths)} search paths")
        return unique_paths
    
    def get_executable_directory(self) -> str:
        """
        Get the directory where the executable is located
        """
        return self.executable_dir
    
    def find_base_library(self) -> Optional[str]:
        """
        Find base_library.zip file using multi-location search
        """
        self.logger.debug("Searching for base_library.zip")
        
        # Common names for the base library file
        possible_names = [
            'base_library.zip',
            'library.zip',
            'python_library.zip',
            'base.zip'
        ]
        
        for search_path in self.search_paths:
            if not os.path.exists(search_path):
                continue
                
            for filename in possible_names:
                file_path = os.path.join(search_path, filename)
                if os.path.isfile(file_path):
                    self.logger.info(f"Found base library at: {file_path}")
                    return file_path
        
        # If not found in standard locations, try recursive search in key directories
        return self._recursive_search_base_library(possible_names)
    
    def _recursive_search_base_library(self, possible_names: List[str]) -> Optional[str]:
        """
        Perform recursive search for base library in key directories
        """
        self.logger.debug("Performing recursive search for base_library.zip")
        
        # Limit recursive search to most likely directories
        key_directories = [
            self.executable_dir,
            os.path.dirname(self.executable_dir),
            os.getcwd()
        ]
        
        for base_dir in key_directories:
            if not os.path.exists(base_dir):
                continue
                
            try:
                for root, dirs, files in os.walk(base_dir):
                    # Limit search depth to avoid performance issues
                    depth = root[len(base_dir):].count(os.sep)
                    if depth >= 3:
                        dirs[:] = []  # Don't recurse deeper
                        continue
                    
                    for filename in possible_names:
                        if filename in files:
                            file_path = os.path.join(root, filename)
                            self.logger.info(f"Found base library via recursive search: {file_path}")
                            return file_path
                            
            except (PermissionError, OSError) as e:
                self.logger.warning(f"Could not search directory {base_dir}: {e}")
                continue
        
        self.logger.warning("base_library.zip not found in any location")
        return None
    
    def scan_alternative_paths(self) -> List[str]:
        """
        Scan for alternative paths where files might be located
        """
        self.logger.debug("Scanning for alternative paths")
        
        alternative_paths = []
        
        # Check environment variables
        env_paths = [
            os.environ.get('TEZGAH_HOME'),
            os.environ.get('PYTHONPATH'),
            os.environ.get('PATH')
        ]
        
        for env_path in env_paths:
            if env_path:
                if os.pathsep in env_path:
                    # Multiple paths in environment variable
                    for path in env_path.split(os.pathsep):
                        if path and os.path.exists(path):
                            alternative_paths.append(path)
                else:
                    # Single path
                    if os.path.exists(env_path):
                        alternative_paths.append(env_path)
        
        # Check registry on Windows
        if self.system_info['platform'] == 'Windows':
            registry_paths = self._check_windows_registry()
            alternative_paths.extend(registry_paths)
        
        # Check common temporary directories
        temp_dirs = [
            os.environ.get('TEMP'),
            os.environ.get('TMP'),
            '/tmp',
            '/var/tmp'
        ]
        
        for temp_dir in temp_dirs:
            if temp_dir and os.path.exists(temp_dir):
                tezgah_temp = os.path.join(temp_dir, 'TezgahTakip')
                if os.path.exists(tezgah_temp):
                    alternative_paths.append(tezgah_temp)
        
        # Remove duplicates and non-existent paths
        valid_paths = []
        for path in alternative_paths:
            if path and os.path.exists(path) and path not in valid_paths:
                valid_paths.append(path)
        
        self.logger.debug(f"Found {len(valid_paths)} alternative paths")
        return valid_paths
    
    def _check_windows_registry(self) -> List[str]:
        """
        Check Windows registry for installation paths
        """
        registry_paths = []
        
        try:
            import winreg
            
            # Common registry locations for installed software
            registry_keys = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\TezgahTakip"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\TezgahTakip"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\TezgahTakip"),
            ]
            
            for hkey, subkey in registry_keys:
                try:
                    with winreg.OpenKey(hkey, subkey) as key:
                        install_path, _ = winreg.QueryValueEx(key, "InstallPath")
                        if install_path and os.path.exists(install_path):
                            registry_paths.append(install_path)
                except (FileNotFoundError, OSError):
                    continue
                    
        except ImportError:
            # winreg not available (not Windows)
            pass
        except Exception as e:
            self.logger.warning(f"Error checking Windows registry: {e}")
        
        return registry_paths
    
    def validate_path_structure(self, path: str) -> bool:
        """
        Validate that a path has the expected structure for TezgahTakip
        """
        if not os.path.exists(path):
            return False
        
        # Check for expected files/directories
        expected_items = [
            'tezgah_takip_app.py',
            'main_window.py',
            'launcher.py',
            'config.json'
        ]
        
        found_items = 0
        for item in expected_items:
            item_path = os.path.join(path, item)
            if os.path.exists(item_path):
                found_items += 1
        
        # Consider valid if at least half of expected items are found
        is_valid = found_items >= len(expected_items) // 2
        
        self.logger.debug(f"Path structure validation for {path}: {is_valid} ({found_items}/{len(expected_items)} items found)")
        return is_valid
    
    def resolve_relative_path(self, relative_path: str) -> str:
        """
        Resolve a relative path to an absolute path based on executable directory
        """
        if os.path.isabs(relative_path):
            return relative_path
        
        # Try relative to executable directory first
        abs_path = os.path.join(self.executable_dir, relative_path)
        if os.path.exists(abs_path):
            return abs_path
        
        # Try relative to current working directory
        abs_path = os.path.join(os.getcwd(), relative_path)
        if os.path.exists(abs_path):
            return abs_path
        
        # Return the path relative to executable directory even if it doesn't exist
        return os.path.join(self.executable_dir, relative_path)
    
    def get_search_paths(self) -> List[str]:
        """
        Get all configured search paths
        """
        return self.search_paths.copy()
    
    def add_search_path(self, path: str) -> None:
        """
        Add a new search path
        """
        if path and os.path.exists(path) and path not in self.search_paths:
            self.search_paths.append(path)
            self.logger.debug(f"Added search path: {path}")
    
    def find_file(self, filename: str) -> Optional[str]:
        """
        Find any file using the configured search paths
        """
        self.logger.debug(f"Searching for file: {filename}")
        
        for search_path in self.search_paths:
            if not os.path.exists(search_path):
                continue
                
            file_path = os.path.join(search_path, filename)
            if os.path.isfile(file_path):
                self.logger.debug(f"Found {filename} at: {file_path}")
                return file_path
        
        self.logger.warning(f"File {filename} not found in any search path")
        return None