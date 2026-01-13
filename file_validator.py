"""
File Validator for TezgahTakip Update System
Handles file integrity checking, dependency validation, and permission verification
"""

import os
import sys
import hashlib
import zipfile
import logging
from typing import Optional, List, Dict, Tuple, Set
from pathlib import Path
import json
import stat
import time
from dataclasses import dataclass


@dataclass
class FileInfo:
    """Information about a file"""
    path: str
    size: int
    modified_time: float
    checksum: Optional[str] = None
    permissions: Optional[str] = None
    is_executable: bool = False


@dataclass
class ValidationResult:
    """Result of file validation"""
    is_valid: bool
    file_info: Optional[FileInfo] = None
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


@dataclass
class DependencyInfo:
    """Information about a dependency"""
    name: str
    required: bool
    found: bool
    path: Optional[str] = None
    version: Optional[str] = None
    issues: List[str] = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []


class FileValidator:
    """
    Validates files for integrity, dependencies, and permissions
    """
    
    def __init__(self, path_resolver=None):
        self.logger = logging.getLogger("FileValidator")
        self.path_resolver = path_resolver
        
        # Expected file checksums (would be populated from a manifest)
        self.expected_checksums = {}
        
        # Critical files that must exist
        self.critical_files = {
            'base_library.zip': {
                'required': True,
                'min_size': 1024,  # At least 1KB
                'extensions': ['.zip'],
                'description': 'Python runtime libraries'
            },
            'tezgah_takip_app.py': {
                'required': True,
                'min_size': 100,
                'extensions': ['.py'],
                'description': 'Main application file'
            },
            'main_window.py': {
                'required': True,
                'min_size': 100,
                'extensions': ['.py'],
                'description': 'Main window module'
            },
            'launcher.py': {
                'required': False,
                'min_size': 50,
                'extensions': ['.py'],
                'description': 'Application launcher'
            },
            'config.json': {
                'required': False,
                'min_size': 10,
                'extensions': ['.json'],
                'description': 'Configuration file'
            }
        }
        
        # Python dependencies that should be available
        self.python_dependencies = [
            'tkinter',
            'sqlite3',
            'json',
            'os',
            'sys',
            'logging',
            'datetime',
            'pathlib'
        ]
        
        self.logger.debug("FileValidator initialized")
    
    def check_file_integrity(self, file_path: str) -> ValidationResult:
        """
        Check the integrity of a single file
        """
        self.logger.debug(f"Checking integrity of {file_path}")
        
        if not os.path.exists(file_path):
            return ValidationResult(
                is_valid=False,
                errors=[f"File does not exist: {file_path}"]
            )
        
        try:
            # Get file information
            stat_info = os.stat(file_path)
            file_info = FileInfo(
                path=file_path,
                size=stat_info.st_size,
                modified_time=stat_info.st_mtime,
                is_executable=self._is_executable(file_path)
            )
            
            # Calculate checksum
            file_info.checksum = self._calculate_checksum(file_path)
            
            # Get permissions
            file_info.permissions = self._get_permissions_string(stat_info.st_mode)
            
            # Validate file
            errors = []
            warnings = []
            
            # Check file size
            if stat_info.st_size == 0:
                errors.append("File is empty")
            elif stat_info.st_size < 10:
                warnings.append("File is very small, might be corrupted")
            
            # Check if file is readable
            if not os.access(file_path, os.R_OK):
                errors.append("File is not readable")
            
            # Check specific file types
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext == '.zip':
                zip_errors = self._validate_zip_file(file_path)
                errors.extend(zip_errors)
            elif file_ext == '.py':
                py_errors = self._validate_python_file(file_path)
                errors.extend(py_errors)
            elif file_ext == '.json':
                json_errors = self._validate_json_file(file_path)
                errors.extend(json_errors)
            
            # Check against expected checksum if available
            expected_checksum = self.expected_checksums.get(os.path.basename(file_path))
            if expected_checksum and file_info.checksum != expected_checksum:
                errors.append(f"Checksum mismatch. Expected: {expected_checksum}, Got: {file_info.checksum}")
            
            is_valid = len(errors) == 0
            
            self.logger.debug(f"File integrity check for {file_path}: {'PASS' if is_valid else 'FAIL'}")
            
            return ValidationResult(
                is_valid=is_valid,
                file_info=file_info,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            self.logger.error(f"Error checking file integrity for {file_path}: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Failed to check file integrity: {str(e)}"]
            )
    
    def validate_dependencies(self) -> List[DependencyInfo]:
        """
        Validate that all required dependencies are available
        """
        self.logger.debug("Validating dependencies")
        
        dependency_results = []
        
        # Check Python dependencies
        for dep_name in self.python_dependencies:
            dep_info = self._check_python_dependency(dep_name)
            dependency_results.append(dep_info)
        
        # Check file dependencies
        for filename, file_spec in self.critical_files.items():
            dep_info = self._check_file_dependency(filename, file_spec)
            dependency_results.append(dep_info)
        
        # Check system dependencies
        system_deps = self._check_system_dependencies()
        dependency_results.extend(system_deps)
        
        self.logger.debug(f"Dependency validation completed. {len(dependency_results)} dependencies checked")
        return dependency_results
    
    def verify_executable_structure(self) -> bool:
        """
        Verify that the executable has the expected structure
        """
        self.logger.debug("Verifying executable structure")
        
        if not self.path_resolver:
            self.logger.warning("No path resolver available for structure verification")
            return True  # Assume valid if we can't check
        
        exe_dir = self.path_resolver.get_executable_directory()
        
        # Check for critical files
        critical_found = 0
        critical_required = 0
        
        for filename, file_spec in self.critical_files.items():
            if file_spec['required']:
                critical_required += 1
            
            file_path = os.path.join(exe_dir, filename)
            if os.path.exists(file_path):
                critical_found += 1
                
                # Validate file meets minimum requirements
                try:
                    stat_info = os.stat(file_path)
                    if stat_info.st_size < file_spec.get('min_size', 0):
                        self.logger.warning(f"File {filename} is smaller than expected")
                except OSError:
                    pass
        
        # Structure is valid if we found at least half of the critical files
        structure_valid = critical_found >= (critical_required // 2)
        
        self.logger.debug(f"Executable structure validation: {'PASS' if structure_valid else 'FAIL'} "
                         f"({critical_found}/{critical_required} critical files found)")
        
        return structure_valid
    
    def check_permissions(self, path: str) -> bool:
        """
        Check if the application has sufficient permissions for the given path
        """
        self.logger.debug(f"Checking permissions for {path}")
        
        if not os.path.exists(path):
            self.logger.warning(f"Path does not exist: {path}")
            return False
        
        try:
            # Check read permission
            if not os.access(path, os.R_OK):
                self.logger.warning(f"No read permission for {path}")
                return False
            
            # Check write permission (for updates)
            if not os.access(path, os.W_OK):
                self.logger.warning(f"No write permission for {path}")
                return False
            
            # If it's a directory, check execute permission
            if os.path.isdir(path) and not os.access(path, os.X_OK):
                self.logger.warning(f"No execute permission for directory {path}")
                return False
            
            self.logger.debug(f"Permissions check for {path}: PASS")
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking permissions for {path}: {e}")
            return False
    
    def _calculate_checksum(self, file_path: str, algorithm: str = 'sha256') -> str:
        """
        Calculate checksum of a file
        """
        hash_obj = hashlib.new(algorithm)
        
        try:
            with open(file_path, 'rb') as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_obj.update(chunk)
            
            return hash_obj.hexdigest()
            
        except Exception as e:
            self.logger.error(f"Error calculating checksum for {file_path}: {e}")
            return ""
    
    def _is_executable(self, file_path: str) -> bool:
        """
        Check if a file is executable
        """
        try:
            return os.access(file_path, os.X_OK)
        except Exception:
            return False
    
    def _get_permissions_string(self, mode: int) -> str:
        """
        Convert file mode to readable permissions string
        """
        permissions = []
        
        # Owner permissions
        permissions.append('r' if mode & stat.S_IRUSR else '-')
        permissions.append('w' if mode & stat.S_IWUSR else '-')
        permissions.append('x' if mode & stat.S_IXUSR else '-')
        
        # Group permissions
        permissions.append('r' if mode & stat.S_IRGRP else '-')
        permissions.append('w' if mode & stat.S_IWGRP else '-')
        permissions.append('x' if mode & stat.S_IXGRP else '-')
        
        # Other permissions
        permissions.append('r' if mode & stat.S_IROTH else '-')
        permissions.append('w' if mode & stat.S_IWOTH else '-')
        permissions.append('x' if mode & stat.S_IXOTH else '-')
        
        return ''.join(permissions)
    
    def _validate_zip_file(self, file_path: str) -> List[str]:
        """
        Validate a ZIP file
        """
        errors = []
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                # Test the ZIP file integrity
                bad_file = zip_file.testzip()
                if bad_file:
                    errors.append(f"ZIP file is corrupted. Bad file: {bad_file}")
                
                # Check if ZIP file is not empty
                if len(zip_file.namelist()) == 0:
                    errors.append("ZIP file is empty")
                
                # For base_library.zip, check for Python files
                if 'base_library.zip' in file_path:
                    python_files = [name for name in zip_file.namelist() if name.endswith('.py') or name.endswith('.pyc')]
                    if len(python_files) == 0:
                        errors.append("base_library.zip does not contain Python files")
                
        except zipfile.BadZipFile:
            errors.append("File is not a valid ZIP file")
        except Exception as e:
            errors.append(f"Error validating ZIP file: {str(e)}")
        
        return errors
    
    def _validate_python_file(self, file_path: str) -> List[str]:
        """
        Validate a Python file
        """
        errors = []
        
        try:
            # Try to compile the Python file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic syntax check
            try:
                compile(content, file_path, 'exec')
            except SyntaxError as e:
                errors.append(f"Python syntax error: {str(e)}")
            
            # Check for basic structure (if it's a main file)
            if 'main' in os.path.basename(file_path).lower():
                if 'if __name__' not in content:
                    # This is a warning, not an error
                    pass
        
        except UnicodeDecodeError:
            errors.append("File contains invalid characters (encoding issue)")
        except Exception as e:
            errors.append(f"Error validating Python file: {str(e)}")
        
        return errors
    
    def _validate_json_file(self, file_path: str) -> List[str]:
        """
        Validate a JSON file
        """
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            errors.append(f"Error validating JSON file: {str(e)}")
        
        return errors
    
    def _check_python_dependency(self, dep_name: str) -> DependencyInfo:
        """
        Check if a Python module is available
        """
        try:
            __import__(dep_name)
            return DependencyInfo(
                name=dep_name,
                required=True,
                found=True,
                version=self._get_module_version(dep_name)
            )
        except ImportError as e:
            return DependencyInfo(
                name=dep_name,
                required=True,
                found=False,
                issues=[f"Import error: {str(e)}"]
            )
    
    def _get_module_version(self, module_name: str) -> Optional[str]:
        """
        Get version of a Python module if available
        """
        try:
            module = __import__(module_name)
            return getattr(module, '__version__', None)
        except Exception:
            return None
    
    def _check_file_dependency(self, filename: str, file_spec: Dict) -> DependencyInfo:
        """
        Check if a file dependency exists and is valid
        """
        if not self.path_resolver:
            return DependencyInfo(
                name=filename,
                required=file_spec['required'],
                found=False,
                issues=["No path resolver available"]
            )
        
        file_path = self.path_resolver.find_file(filename)
        
        if not file_path:
            return DependencyInfo(
                name=filename,
                required=file_spec['required'],
                found=False,
                issues=["File not found in search paths"]
            )
        
        # Validate the found file
        validation_result = self.check_file_integrity(file_path)
        
        return DependencyInfo(
            name=filename,
            required=file_spec['required'],
            found=True,
            path=file_path,
            issues=validation_result.errors
        )
    
    def _check_system_dependencies(self) -> List[DependencyInfo]:
        """
        Check system-level dependencies
        """
        dependencies = []
        
        # Check Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        python_ok = sys.version_info >= (3, 6)  # Minimum Python 3.6
        
        dependencies.append(DependencyInfo(
            name="Python",
            required=True,
            found=True,
            version=python_version,
            issues=[] if python_ok else ["Python version too old (minimum 3.6 required)"]
        ))
        
        # Check if running as frozen executable
        is_frozen = getattr(sys, 'frozen', False)
        dependencies.append(DependencyInfo(
            name="Frozen Executable",
            required=False,
            found=is_frozen,
            issues=[] if is_frozen else ["Running as script, not frozen executable"]
        ))
        
        return dependencies
    
    def get_validation_summary(self, dependency_results: List[DependencyInfo]) -> Dict[str, any]:
        """
        Get a summary of validation results
        """
        summary = {
            'total_dependencies': len(dependency_results),
            'found_dependencies': 0,
            'missing_required': 0,
            'missing_optional': 0,
            'issues_found': 0,
            'critical_issues': [],
            'warnings': []
        }
        
        for dep in dependency_results:
            if dep.found:
                summary['found_dependencies'] += 1
            else:
                if dep.required:
                    summary['missing_required'] += 1
                    summary['critical_issues'].append(f"Missing required dependency: {dep.name}")
                else:
                    summary['missing_optional'] += 1
                    summary['warnings'].append(f"Missing optional dependency: {dep.name}")
            
            if dep.issues:
                summary['issues_found'] += len(dep.issues)
                for issue in dep.issues:
                    if dep.required:
                        summary['critical_issues'].append(f"{dep.name}: {issue}")
                    else:
                        summary['warnings'].append(f"{dep.name}: {issue}")
        
        return summary