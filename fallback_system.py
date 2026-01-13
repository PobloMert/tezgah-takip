"""
Fallback System for TezgahTakip Update Manager
Handles alternative paths and manual recovery suggestions when files are not found
"""

import os
import sys
import logging
from typing import Optional, List, Dict, Tuple
from pathlib import Path
import json
import time
from dataclasses import dataclass


@dataclass
class FallbackOption:
    """Represents a fallback option for file recovery"""
    path: str
    confidence: float  # 0.0 to 1.0
    reason: str
    manual_steps: List[str]


@dataclass
class RecoveryPlan:
    """Complete recovery plan with multiple options"""
    primary_issue: str
    fallback_options: List[FallbackOption]
    manual_suggestions: List[str]
    emergency_contacts: List[str]


class FallbackSystem:
    """
    Manages fallback mechanisms and manual recovery suggestions
    """
    
    def __init__(self, path_resolver=None):
        self.logger = logging.getLogger("FallbackSystem")
        self.path_resolver = path_resolver
        
        # Common file patterns and their alternatives
        self.file_alternatives = {
            'base_library.zip': [
                'library.zip',
                'python_library.zip', 
                'base.zip',
                'python.zip',
                'stdlib.zip'
            ],
            'python.exe': [
                'python3.exe',
                'python.exe',
                'pythonw.exe'
            ],
            'config.json': [
                'config.ini',
                'settings.json',
                'configuration.json',
                'app.config'
            ]
        }
        
        # Recovery strategies by error type
        self.recovery_strategies = {
            'missing_base_library': self._recover_missing_base_library,
            'missing_executable': self._recover_missing_executable,
            'permission_denied': self._recover_permission_issues,
            'corrupted_files': self._recover_corrupted_files,
            'path_not_found': self._recover_path_issues
        }
        
        self.logger.debug("FallbackSystem initialized")
    
    def find_alternative_file(self, original_filename: str, search_paths: List[str] = None) -> Optional[str]:
        """
        Find alternative files when the original is not found
        """
        self.logger.debug(f"Searching for alternatives to {original_filename}")
        
        if search_paths is None:
            search_paths = self.path_resolver.get_search_paths() if self.path_resolver else [os.getcwd()]
        
        # Get alternative filenames
        alternatives = self.file_alternatives.get(original_filename, [])
        
        # Add variations of the original filename
        base_name, ext = os.path.splitext(original_filename)
        alternatives.extend([
            f"{base_name}_backup{ext}",
            f"{base_name}.bak",
            f"{base_name}_old{ext}",
            f"backup_{original_filename}",
            f"old_{original_filename}"
        ])
        
        # Search for alternatives in all paths
        for search_path in search_paths:
            if not os.path.exists(search_path):
                continue
                
            for alt_filename in alternatives:
                alt_path = os.path.join(search_path, alt_filename)
                if os.path.isfile(alt_path):
                    self.logger.info(f"Found alternative file: {alt_path}")
                    return alt_path
        
        self.logger.warning(f"No alternatives found for {original_filename}")
        return None
    
    def suggest_manual_paths(self, filename: str) -> List[FallbackOption]:
        """
        Suggest manual paths where the user might find the file
        """
        self.logger.debug(f"Generating manual path suggestions for {filename}")
        
        suggestions = []
        
        # Common download locations
        user_home = os.path.expanduser('~')
        common_locations = [
            os.path.join(user_home, 'Downloads'),
            os.path.join(user_home, 'Desktop'),
            os.path.join(user_home, 'Documents'),
            'C:\\Program Files\\TezgahTakip',
            'C:\\Program Files (x86)\\TezgahTakip',
            os.path.join(user_home, 'AppData', 'Local', 'TezgahTakip'),
            os.path.join(user_home, 'AppData', 'Roaming', 'TezgahTakip')
        ]
        
        for location in common_locations:
            if os.path.exists(location):
                confidence = 0.8 if 'TezgahTakip' in location else 0.5
                
                suggestions.append(FallbackOption(
                    path=location,
                    confidence=confidence,
                    reason=f"Common installation/download location",
                    manual_steps=[
                        f"Check if {filename} exists in {location}",
                        f"If found, copy it to the application directory",
                        "Restart the application"
                    ]
                ))
        
        # Previous installation locations (from registry or config)
        previous_locations = self._get_previous_installation_paths()
        for location in previous_locations:
            suggestions.append(FallbackOption(
                path=location,
                confidence=0.9,
                reason="Previous installation location",
                manual_steps=[
                    f"Check previous installation at {location}",
                    f"Copy {filename} from old installation",
                    "Verify file integrity after copying"
                ]
            ))
        
        # Sort by confidence
        suggestions.sort(key=lambda x: x.confidence, reverse=True)
        
        self.logger.debug(f"Generated {len(suggestions)} manual path suggestions")
        return suggestions
    
    def _get_previous_installation_paths(self) -> List[str]:
        """
        Get paths from previous installations
        """
        paths = []
        
        # Check for backup configuration files
        config_locations = [
            'config.json.backup',
            'settings.json.backup',
            os.path.join(os.path.expanduser('~'), '.tezgah_config'),
            os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'TezgahTakip', 'config.json')
        ]
        
        for config_path in config_locations:
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        
                    # Look for installation path in config
                    install_path = config.get('installation_path') or config.get('app_path')
                    if install_path and os.path.exists(install_path):
                        paths.append(install_path)
                        
                except (json.JSONDecodeError, IOError) as e:
                    self.logger.warning(f"Could not read config file {config_path}: {e}")
        
        return paths
    
    def create_recovery_plan(self, error_type: str, missing_files: List[str], context: Dict = None) -> RecoveryPlan:
        """
        Create a comprehensive recovery plan for the given error
        """
        self.logger.info(f"Creating recovery plan for error type: {error_type}")
        
        if context is None:
            context = {}
        
        # Get specific recovery strategy
        recovery_func = self.recovery_strategies.get(error_type, self._generic_recovery)
        
        # Generate recovery plan
        plan = recovery_func(missing_files, context)
        
        # Add general manual suggestions
        plan.manual_suggestions.extend([
            "Try running the application as administrator",
            "Check Windows Defender or antivirus exclusions",
            "Verify disk space availability",
            "Restart the computer and try again",
            "Download and reinstall the latest version"
        ])
        
        # Add emergency contacts
        plan.emergency_contacts = [
            "GitHub Issues: https://github.com/PobloMert/tezgah-takip/issues",
            "Check documentation for troubleshooting guide",
            "Contact system administrator if in corporate environment"
        ]
        
        self.logger.info(f"Recovery plan created with {len(plan.fallback_options)} options")
        return plan
    
    def _recover_missing_base_library(self, missing_files: List[str], context: Dict) -> RecoveryPlan:
        """
        Recovery strategy for missing base_library.zip
        """
        fallback_options = []
        
        # Try to find alternative library files
        for filename in missing_files:
            if 'library' in filename.lower():
                alternatives = self.suggest_manual_paths(filename)
                fallback_options.extend(alternatives)
        
        # Add specific base_library recovery options
        fallback_options.append(FallbackOption(
            path="PyInstaller temporary directory",
            confidence=0.7,
            reason="base_library.zip might be in PyInstaller temp folder",
            manual_steps=[
                "Check %TEMP% folder for _MEI* directories",
                "Look for base_library.zip in these temporary folders",
                "Copy the file to application directory",
                "Restart application"
            ]
        ))
        
        fallback_options.append(FallbackOption(
            path="Application installation directory",
            confidence=0.9,
            reason="File might be in a subdirectory",
            manual_steps=[
                "Navigate to application installation folder",
                "Check 'lib', 'libs', or 'resources' subdirectories",
                "Look for any .zip files containing Python libraries",
                "Rename found library file to 'base_library.zip'"
            ]
        ))
        
        return RecoveryPlan(
            primary_issue="Missing base_library.zip - Python runtime libraries not found",
            fallback_options=fallback_options,
            manual_suggestions=[
                "Reinstall the application to restore missing files",
                "Check if antivirus software quarantined the file",
                "Verify the application was extracted completely from ZIP"
            ],
            emergency_contacts=[]
        )
    
    def _recover_missing_executable(self, missing_files: List[str], context: Dict) -> RecoveryPlan:
        """
        Recovery strategy for missing executable files
        """
        fallback_options = []
        
        # Look for alternative executables
        for filename in missing_files:
            if filename.endswith('.exe'):
                alternatives = self.suggest_manual_paths(filename)
                fallback_options.extend(alternatives)
        
        return RecoveryPlan(
            primary_issue="Missing executable files",
            fallback_options=fallback_options,
            manual_suggestions=[
                "Check if Windows Defender blocked the executable",
                "Verify the application has proper permissions",
                "Re-extract from original ZIP file if available"
            ],
            emergency_contacts=[]
        )
    
    def _recover_permission_issues(self, missing_files: List[str], context: Dict) -> RecoveryPlan:
        """
        Recovery strategy for permission-related issues
        """
        fallback_options = []
        
        # Suggest alternative locations with better permissions
        user_locations = [
            os.path.join(os.path.expanduser('~'), 'Documents', 'TezgahTakip'),
            os.path.join(os.path.expanduser('~'), 'Desktop', 'TezgahTakip'),
            os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'TezgahTakip')
        ]
        
        for location in user_locations:
            fallback_options.append(FallbackOption(
                path=location,
                confidence=0.8,
                reason="User directory with full permissions",
                manual_steps=[
                    f"Create directory: {location}",
                    "Copy application files to this location",
                    "Run application from new location"
                ]
            ))
        
        return RecoveryPlan(
            primary_issue="Permission denied - insufficient access rights",
            fallback_options=fallback_options,
            manual_suggestions=[
                "Run application as administrator",
                "Change folder permissions to allow full access",
                "Move application to user directory instead of Program Files"
            ],
            emergency_contacts=[]
        )
    
    def _recover_corrupted_files(self, missing_files: List[str], context: Dict) -> RecoveryPlan:
        """
        Recovery strategy for corrupted files
        """
        fallback_options = []
        
        # Look for backup files
        for filename in missing_files:
            backup_locations = [
                f"{filename}.backup",
                f"{filename}.bak",
                f"backup_{filename}",
                os.path.join("backups", filename)
            ]
            
            for backup_name in backup_locations:
                if self.path_resolver:
                    backup_path = self.path_resolver.find_file(backup_name)
                    if backup_path:
                        fallback_options.append(FallbackOption(
                            path=backup_path,
                            confidence=0.9,
                            reason="Found backup file",
                            manual_steps=[
                                f"Copy {backup_path} to {filename}",
                                "Verify file integrity",
                                "Restart application"
                            ]
                        ))
        
        return RecoveryPlan(
            primary_issue="Corrupted files detected",
            fallback_options=fallback_options,
            manual_suggestions=[
                "Download fresh copy of the application",
                "Run disk check utility (chkdsk)",
                "Check for hardware issues if corruption persists"
            ],
            emergency_contacts=[]
        )
    
    def _recover_path_issues(self, missing_files: List[str], context: Dict) -> RecoveryPlan:
        """
        Recovery strategy for path-related issues
        """
        fallback_options = []
        
        # Suggest path fixes
        current_dir = os.getcwd()
        exe_dir = os.path.dirname(sys.executable) if hasattr(sys, 'executable') else current_dir
        
        suggested_paths = [current_dir, exe_dir]
        
        for path in suggested_paths:
            fallback_options.append(FallbackOption(
                path=path,
                confidence=0.6,
                reason="Alternative working directory",
                manual_steps=[
                    f"Change working directory to {path}",
                    "Copy missing files to this directory",
                    "Run application from this location"
                ]
            ))
        
        return RecoveryPlan(
            primary_issue="Path resolution issues",
            fallback_options=fallback_options,
            manual_suggestions=[
                "Check if application path contains special characters",
                "Avoid paths with spaces or non-ASCII characters",
                "Use shorter path names if possible"
            ],
            emergency_contacts=[]
        )
    
    def _generic_recovery(self, missing_files: List[str], context: Dict) -> RecoveryPlan:
        """
        Generic recovery strategy for unknown error types
        """
        fallback_options = []
        
        # Generate generic suggestions for each missing file
        for filename in missing_files:
            suggestions = self.suggest_manual_paths(filename)
            fallback_options.extend(suggestions[:2])  # Limit to top 2 suggestions per file
        
        return RecoveryPlan(
            primary_issue="General application error",
            fallback_options=fallback_options,
            manual_suggestions=[
                "Try restarting the application",
                "Check system requirements",
                "Update Windows and drivers"
            ],
            emergency_contacts=[]
        )
    
    def execute_fallback_option(self, option: FallbackOption, target_filename: str) -> bool:
        """
        Execute a fallback option automatically if possible
        """
        self.logger.info(f"Executing fallback option for {target_filename}")
        
        try:
            # Check if the fallback path exists and contains the target file
            if os.path.exists(option.path):
                source_file = os.path.join(option.path, target_filename)
                
                if os.path.isfile(source_file):
                    # Copy file to current directory or appropriate location
                    target_dir = self.path_resolver.get_executable_directory() if self.path_resolver else os.getcwd()
                    target_file = os.path.join(target_dir, target_filename)
                    
                    import shutil
                    shutil.copy2(source_file, target_file)
                    
                    self.logger.info(f"Successfully copied {source_file} to {target_file}")
                    return True
                    
        except Exception as e:
            self.logger.error(f"Failed to execute fallback option: {e}")
        
        return False
    
    def get_user_friendly_suggestions(self, recovery_plan: RecoveryPlan) -> List[str]:
        """
        Convert recovery plan to user-friendly suggestions
        """
        suggestions = []
        
        suggestions.append(f"Issue: {recovery_plan.primary_issue}")
        suggestions.append("")
        
        if recovery_plan.fallback_options:
            suggestions.append("Automatic recovery options:")
            for i, option in enumerate(recovery_plan.fallback_options[:3], 1):
                suggestions.append(f"{i}. Check {option.path}")
                suggestions.append(f"   Reason: {option.reason}")
                if option.manual_steps:
                    suggestions.append(f"   Steps: {'; '.join(option.manual_steps[:2])}")
                suggestions.append("")
        
        if recovery_plan.manual_suggestions:
            suggestions.append("Manual troubleshooting steps:")
            for i, suggestion in enumerate(recovery_plan.manual_suggestions[:5], 1):
                suggestions.append(f"{i}. {suggestion}")
            suggestions.append("")
        
        if recovery_plan.emergency_contacts:
            suggestions.append("If problems persist:")
            for contact in recovery_plan.emergency_contacts:
                suggestions.append(f"- {contact}")
        
        return suggestions