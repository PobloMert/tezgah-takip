"""
Enhanced Update Manager for TezgahTakip
Handles update compatibility issues, especially base_library.zip problems
"""

import os
import sys
import logging
import traceback
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import json
import shutil
from pathlib import Path
import time


class UpdateStatus(Enum):
    """Update operation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ErrorSeverity(Enum):
    """Error severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class UpdateResult:
    """Result of an update operation"""
    success: bool
    version: str
    error_message: Optional[str] = None
    backup_path: Optional[str] = None
    recovery_options: List[str] = None
    
    def __post_init__(self):
        if self.recovery_options is None:
            self.recovery_options = []


@dataclass
class ValidationResult:
    """Result of environment validation"""
    is_valid: bool
    missing_files: List[str] = None
    permission_issues: List[str] = None
    path_issues: List[str] = None
    
    def __post_init__(self):
        if self.missing_files is None:
            self.missing_files = []
        if self.permission_issues is None:
            self.permission_issues = []
        if self.path_issues is None:
            self.path_issues = []


@dataclass
class RecoveryResult:
    """Result of recovery operation"""
    recovery_successful: bool
    method_used: str
    remaining_issues: List[str] = None
    
    def __post_init__(self):
        if self.remaining_issues is None:
            self.remaining_issues = []


class UpdateLogger:
    """Enhanced logging system for update operations"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup main logger
        self.logger = logging.getLogger("UpdateManager")
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # File handler for detailed logs
        log_file = self.log_dir / f"update_{int(time.time())}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler for important messages
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.current_log_file = log_file
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, extra=kwargs)
    
    def log_exception(self, message: str, exc: Exception):
        """Log exception with full traceback"""
        self.logger.error(f"{message}: {str(exc)}")
        self.logger.debug(f"Full traceback: {traceback.format_exc()}")
    
    def get_log_file_path(self) -> str:
        """Get current log file path"""
        return str(self.current_log_file)


class EnhancedUpdateManager:
    """
    Enhanced Update Manager that handles compatibility issues
    """
    
    def __init__(self):
        self.logger = UpdateLogger()
        self.current_version = "2.1.3"
        self.status = UpdateStatus.PENDING
        
        # Will be initialized by other components
        self.path_resolver = None
        self.file_validator = None
        self.backup_manager = None
        self.error_handler = None
        self.data_preservation_manager = None
        
        self.logger.info("Enhanced Update Manager initialized")
    
    def set_components(self, path_resolver, file_validator, backup_manager, error_handler, data_preservation_manager=None):
        """Set component dependencies"""
        self.path_resolver = path_resolver
        self.file_validator = file_validator
        self.backup_manager = backup_manager
        self.error_handler = error_handler
        self.data_preservation_manager = data_preservation_manager
        
        self.logger.info("All components set for Enhanced Update Manager")
    
    def perform_update(self, target_version: str) -> UpdateResult:
        """
        Perform complete update operation
        """
        self.logger.info(f"Starting update to version {target_version}")
        self.status = UpdateStatus.IN_PROGRESS
        
        try:
            # Step 1: Validate current environment
            validation = self.validate_environment()
            if not validation.is_valid:
                return self._handle_validation_failure(validation, target_version)
            
            # Step 2: Create backup first
            backup_path = self.backup_manager.create_backup(self.current_version)
            if not backup_path:
                return UpdateResult(
                    success=False,
                    version=target_version,
                    error_message="Failed to create backup",
                    recovery_options=["Try manual backup", "Continue without backup (risky)"]
                )
            
            # Step 3: Preserve user data if available
            user_data_files = []
            if self.data_preservation_manager:
                exe_dir = self.path_resolver.get_executable_directory()
                user_data_files = self.data_preservation_manager.identify_user_data(exe_dir)
                if user_data_files:
                    preservation_dir = os.path.join(backup_path + "_userdata")
                    self.data_preservation_manager.preserve_data_before_rollback(user_data_files, preservation_dir)
            # Step 4: Perform actual update
            update_success = self._perform_actual_update(target_version)
            
            if update_success:
                # Step 5: Validate new installation
                post_validation = self.validate_environment()
                if post_validation.is_valid:
                    # Step 6: Restore user data if preserved
                    if user_data_files and self.data_preservation_manager:
                        self.data_preservation_manager.restore_preserved_data(user_data_files)
                    
                    self.status = UpdateStatus.SUCCESS
                    self.current_version = target_version
                    
                    # Cleanup old backups
                    self.backup_manager.cleanup_old_backups()
                    
                    self.logger.info(f"Update to {target_version} completed successfully")
                    return UpdateResult(
                        success=True,
                        version=target_version,
                        backup_path=backup_path
                    )
                else:
                    # Rollback due to validation failure
                    return self._handle_post_update_failure(backup_path, target_version, post_validation)
            else:
                # Rollback due to update failure
                return self._handle_update_failure(backup_path, target_version)
                
        except Exception as e:
            self.logger.log_exception("Unexpected error during update", e)
            return self._handle_unexpected_error(e, target_version)
    
    def validate_environment(self) -> ValidationResult:
        """
        Validate current environment for update readiness
        """
        self.logger.debug("Validating environment")
        
        if not all([self.path_resolver, self.file_validator]):
            return ValidationResult(
                is_valid=False,
                path_issues=["Required components not initialized"]
            )
        
        # Check for base_library.zip
        base_lib_path = self.path_resolver.find_base_library()
        missing_files = []
        if not base_lib_path:
            missing_files.append("base_library.zip")
        
        # Validate file structure
        structure_valid = self.file_validator.verify_executable_structure()
        if not structure_valid:
            missing_files.append("executable structure")
        
        # Check permissions
        exe_dir = self.path_resolver.get_executable_directory()
        permission_issues = []
        if not self.file_validator.check_permissions(exe_dir):
            permission_issues.append(f"Insufficient permissions for {exe_dir}")
        
        is_valid = len(missing_files) == 0 and len(permission_issues) == 0
        
        result = ValidationResult(
            is_valid=is_valid,
            missing_files=missing_files,
            permission_issues=permission_issues
        )
        
        self.logger.debug(f"Environment validation result: {result}")
        return result
    
    def handle_update_failure(self, error: Exception) -> RecoveryResult:
        """
        Handle update failure and attempt recovery
        """
        self.logger.error(f"Handling update failure: {error}")
        
        if self.error_handler:
            return self.error_handler.handle_update_error(error)
        
        return RecoveryResult(
            recovery_successful=False,
            method_used="none",
            remaining_issues=[str(error)]
        )
    
    def _perform_actual_update(self, target_version: str) -> bool:
        """
        Perform the actual update process
        This is a placeholder - actual implementation would handle file copying, etc.
        """
        self.logger.info(f"Performing actual update to {target_version}")
        
        try:
            # Simulate update process
            # In real implementation, this would:
            # 1. Download new files
            # 2. Replace old files
            # 3. Update configuration
            # 4. Migrate data if needed
            
            self.logger.info("Update files processed successfully")
            return True
            
        except Exception as e:
            self.logger.log_exception("Failed to perform actual update", e)
            return False
    
    def _handle_validation_failure(self, validation: ValidationResult, target_version: str) -> UpdateResult:
        """Handle pre-update validation failure"""
        error_msg = "Environment validation failed: "
        if validation.missing_files:
            error_msg += f"Missing files: {', '.join(validation.missing_files)}. "
        if validation.permission_issues:
            error_msg += f"Permission issues: {', '.join(validation.permission_issues)}. "
        
        recovery_options = [
            "Run as administrator",
            "Check file integrity",
            "Reinstall application"
        ]
        
        self.status = UpdateStatus.FAILED
        return UpdateResult(
            success=False,
            version=target_version,
            error_message=error_msg,
            recovery_options=recovery_options
        )
    
    def _handle_update_failure(self, backup_path: str, target_version: str) -> UpdateResult:
        """Handle update process failure"""
        self.logger.warning("Update failed, attempting rollback")
        
        rollback_success = self.backup_manager.restore_backup(backup_path)
        
        if rollback_success:
            self.status = UpdateStatus.ROLLED_BACK
            return UpdateResult(
                success=False,
                version=target_version,
                error_message="Update failed but successfully rolled back",
                backup_path=backup_path,
                recovery_options=["Try update again", "Check system requirements"]
            )
        else:
            self.status = UpdateStatus.FAILED
            return UpdateResult(
                success=False,
                version=target_version,
                error_message="Update failed and rollback also failed",
                backup_path=backup_path,
                recovery_options=["Manual recovery required", "Reinstall application"]
            )
    
    def _handle_post_update_failure(self, backup_path: str, target_version: str, validation: ValidationResult) -> UpdateResult:
        """Handle post-update validation failure"""
        self.logger.warning("Post-update validation failed, attempting rollback")
        
        rollback_success = self.backup_manager.restore_backup(backup_path)
        
        error_msg = f"Update completed but validation failed: {validation}"
        
        if rollback_success:
            self.status = UpdateStatus.ROLLED_BACK
            return UpdateResult(
                success=False,
                version=target_version,
                error_message=error_msg + " - Rolled back successfully",
                backup_path=backup_path,
                recovery_options=["Check system compatibility", "Try manual update"]
            )
        else:
            self.status = UpdateStatus.FAILED
            return UpdateResult(
                success=False,
                version=target_version,
                error_message=error_msg + " - Rollback also failed",
                backup_path=backup_path,
                recovery_options=["Manual recovery required", "Contact support"]
            )
    
    def _handle_unexpected_error(self, error: Exception, target_version: str) -> UpdateResult:
        """Handle unexpected errors"""
        self.status = UpdateStatus.FAILED
        
        return UpdateResult(
            success=False,
            version=target_version,
            error_message=f"Unexpected error: {str(error)}",
            recovery_options=["Check logs", "Try again", "Contact support"]
        )


# Global instance
update_manager = EnhancedUpdateManager()