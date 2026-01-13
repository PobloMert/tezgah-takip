"""
Backup Manager for TezgahTakip Update System
Handles automatic backup creation, rollback functionality, and backup cleanup
"""

import os
import sys
import shutil
import logging
import json
import time
import zipfile
from typing import Optional, List, Dict, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import hashlib


@dataclass
class BackupInfo:
    """Information about a backup"""
    backup_id: str
    version: str
    created_time: float
    backup_path: str
    original_path: str
    size_bytes: int
    file_count: int
    checksum: str
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class RestoreResult:
    """Result of a restore operation"""
    success: bool
    backup_info: Optional[BackupInfo] = None
    restored_files: List[str] = None
    failed_files: List[str] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.restored_files is None:
            self.restored_files = []
        if self.failed_files is None:
            self.failed_files = []


class BackupManager:
    """
    Manages backup creation, restoration, and cleanup for update operations
    """
    
    def __init__(self, backup_root: str = "backups", path_resolver=None):
        self.logger = logging.getLogger("BackupManager")
        self.backup_root = Path(backup_root)
        self.path_resolver = path_resolver
        
        # Create backup directory if it doesn't exist
        self.backup_root.mkdir(exist_ok=True)
        
        # Backup metadata file
        self.metadata_file = self.backup_root / "backup_metadata.json"
        
        # Load existing backup metadata
        self.backup_registry = self._load_backup_registry()
        
        # Configuration
        self.max_backups = 10  # Maximum number of backups to keep
        self.max_backup_age_days = 30  # Maximum age of backups in days
        self.compression_level = 6  # ZIP compression level (0-9)
        
        self.logger.debug(f"BackupManager initialized with backup root: {self.backup_root}")
    
    def create_backup(self, version: str, source_path: str = None) -> Optional[str]:
        """
        Create a backup of the current application state
        """
        self.logger.info(f"Creating backup for version {version}")
        
        try:
            # Determine source path
            if source_path is None:
                if self.path_resolver:
                    source_path = self.path_resolver.get_executable_directory()
                else:
                    source_path = os.getcwd()
            
            if not os.path.exists(source_path):
                self.logger.error(f"Source path does not exist: {source_path}")
                return None
            
            # Generate backup ID and path
            backup_id = self._generate_backup_id(version)
            backup_filename = f"backup_{backup_id}.zip"
            backup_path = self.backup_root / backup_filename
            
            # Create backup
            backup_info = self._create_zip_backup(
                backup_id=backup_id,
                version=version,
                source_path=source_path,
                backup_path=str(backup_path)
            )
            
            if backup_info:
                # Register backup
                self.backup_registry[backup_id] = backup_info
                self._save_backup_registry()
                
                self.logger.info(f"Backup created successfully: {backup_path}")
                return str(backup_path)
            else:
                self.logger.error("Failed to create backup")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return None
    
    def restore_backup(self, backup_path: str) -> bool:
        """
        Restore from a backup
        """
        self.logger.info(f"Restoring from backup: {backup_path}")
        
        try:
            if not os.path.exists(backup_path):
                self.logger.error(f"Backup file does not exist: {backup_path}")
                return False
            
            # Find backup info
            backup_info = self._find_backup_by_path(backup_path)
            if not backup_info:
                self.logger.warning(f"Backup info not found for {backup_path}, attempting restore anyway")
                # Create minimal backup info
                backup_info = BackupInfo(
                    backup_id="unknown",
                    version="unknown",
                    created_time=time.time(),
                    backup_path=backup_path,
                    original_path=self.path_resolver.get_executable_directory() if self.path_resolver else os.getcwd(),
                    size_bytes=os.path.getsize(backup_path),
                    file_count=0,
                    checksum=""
                )
            
            # Perform restore
            restore_result = self._restore_from_zip(backup_info)
            
            if restore_result.success:
                self.logger.info(f"Backup restored successfully. Files restored: {len(restore_result.restored_files)}")
                return True
            else:
                self.logger.error(f"Backup restore failed: {restore_result.error_message}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error restoring backup: {e}")
            return False
    
    def cleanup_old_backups(self) -> None:
        """
        Clean up old backups based on age and count limits
        """
        self.logger.info("Cleaning up old backups")
        
        try:
            current_time = time.time()
            backups_to_remove = []
            
            # Sort backups by creation time (newest first)
            sorted_backups = sorted(
                self.backup_registry.items(),
                key=lambda x: x[1].created_time,
                reverse=True
            )
            
            # Check age limit
            age_limit = current_time - (self.max_backup_age_days * 24 * 60 * 60)
            
            for backup_id, backup_info in sorted_backups:
                should_remove = False
                
                # Remove if too old
                if backup_info.created_time < age_limit:
                    should_remove = True
                    self.logger.debug(f"Backup {backup_id} is too old, marking for removal")
                
                # Remove if exceeds count limit (keep newest ones)
                if len(sorted_backups) - len(backups_to_remove) > self.max_backups:
                    should_remove = True
                    self.logger.debug(f"Backup {backup_id} exceeds count limit, marking for removal")
                
                if should_remove:
                    backups_to_remove.append(backup_id)
            
            # Remove marked backups
            for backup_id in backups_to_remove:
                self._remove_backup(backup_id)
            
            self.logger.info(f"Cleanup completed. Removed {len(backups_to_remove)} old backups")
            
        except Exception as e:
            self.logger.error(f"Error during backup cleanup: {e}")
    
    def verify_backup_integrity(self, backup_path: str) -> bool:
        """
        Verify the integrity of a backup file
        """
        self.logger.debug(f"Verifying backup integrity: {backup_path}")
        
        try:
            if not os.path.exists(backup_path):
                self.logger.error(f"Backup file does not exist: {backup_path}")
                return False
            
            # Test ZIP file integrity
            with zipfile.ZipFile(backup_path, 'r') as zip_file:
                # Test all files in the ZIP
                bad_file = zip_file.testzip()
                if bad_file:
                    self.logger.error(f"Backup integrity check failed. Corrupted file: {bad_file}")
                    return False
                
                # Verify file count
                file_list = zip_file.namelist()
                if len(file_list) == 0:
                    self.logger.error("Backup is empty")
                    return False
            
            # Verify checksum if available
            backup_info = self._find_backup_by_path(backup_path)
            if backup_info and backup_info.checksum:
                current_checksum = self._calculate_file_checksum(backup_path)
                if current_checksum != backup_info.checksum:
                    self.logger.error(f"Backup checksum mismatch. Expected: {backup_info.checksum}, Got: {current_checksum}")
                    return False
            
            self.logger.debug("Backup integrity verification passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying backup integrity: {e}")
            return False
    
    def list_backups(self) -> List[BackupInfo]:
        """
        List all available backups
        """
        return list(self.backup_registry.values())
    
    def get_latest_backup(self, version: str = None) -> Optional[BackupInfo]:
        """
        Get the latest backup, optionally filtered by version
        """
        backups = self.list_backups()
        
        if version:
            backups = [b for b in backups if b.version == version]
        
        if not backups:
            return None
        
        # Return the most recent backup
        return max(backups, key=lambda b: b.created_time)
    
    def _generate_backup_id(self, version: str) -> str:
        """
        Generate a unique backup ID
        """
        timestamp = int(time.time())
        return f"{version}_{timestamp}"
    
    def _create_zip_backup(self, backup_id: str, version: str, source_path: str, backup_path: str) -> Optional[BackupInfo]:
        """
        Create a ZIP backup of the source directory
        """
        self.logger.debug(f"Creating ZIP backup from {source_path} to {backup_path}")
        
        try:
            file_count = 0
            total_size = 0
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=self.compression_level) as zip_file:
                # Add files to ZIP
                for root, dirs, files in os.walk(source_path):
                    # Skip backup directory itself
                    if self.backup_root.name in root:
                        continue
                    
                    # Skip temporary and cache directories
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'temp', 'tmp']]
                    
                    for file in files:
                        # Skip temporary and backup files
                        if file.startswith('.') or file.endswith(('.tmp', '.bak', '.log')):
                            continue
                        
                        file_path = os.path.join(root, file)
                        
                        try:
                            # Calculate relative path for ZIP
                            rel_path = os.path.relpath(file_path, source_path)
                            
                            # Add file to ZIP
                            zip_file.write(file_path, rel_path)
                            
                            file_count += 1
                            total_size += os.path.getsize(file_path)
                            
                        except Exception as e:
                            self.logger.warning(f"Could not add file to backup: {file_path} - {e}")
                            continue
            
            # Calculate backup checksum
            backup_checksum = self._calculate_file_checksum(backup_path)
            
            # Create backup info
            backup_info = BackupInfo(
                backup_id=backup_id,
                version=version,
                created_time=time.time(),
                backup_path=backup_path,
                original_path=source_path,
                size_bytes=os.path.getsize(backup_path),
                file_count=file_count,
                checksum=backup_checksum,
                metadata={
                    'original_size_bytes': total_size,
                    'compression_ratio': round((1 - os.path.getsize(backup_path) / max(total_size, 1)) * 100, 2),
                    'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                    'platform': sys.platform
                }
            )
            
            self.logger.debug(f"ZIP backup created: {file_count} files, {total_size} bytes original, "
                            f"{backup_info.size_bytes} bytes compressed")
            
            return backup_info
            
        except Exception as e:
            self.logger.error(f"Error creating ZIP backup: {e}")
            # Clean up partial backup file
            if os.path.exists(backup_path):
                try:
                    os.remove(backup_path)
                except Exception:
                    pass
            return None
    
    def _restore_from_zip(self, backup_info: BackupInfo) -> RestoreResult:
        """
        Restore files from a ZIP backup
        """
        self.logger.debug(f"Restoring from ZIP backup: {backup_info.backup_path}")
        
        restored_files = []
        failed_files = []
        
        try:
            # Determine restore destination
            restore_path = backup_info.original_path
            if not os.path.exists(restore_path):
                os.makedirs(restore_path, exist_ok=True)
            
            with zipfile.ZipFile(backup_info.backup_path, 'r') as zip_file:
                file_list = zip_file.namelist()
                
                for file_path in file_list:
                    try:
                        # Extract file
                        zip_file.extract(file_path, restore_path)
                        
                        # Restore full path
                        full_path = os.path.join(restore_path, file_path)
                        restored_files.append(full_path)
                        
                    except Exception as e:
                        self.logger.warning(f"Could not restore file {file_path}: {e}")
                        failed_files.append(file_path)
                        continue
            
            success = len(failed_files) == 0 or len(restored_files) > len(failed_files)
            
            return RestoreResult(
                success=success,
                backup_info=backup_info,
                restored_files=restored_files,
                failed_files=failed_files,
                error_message=None if success else f"Failed to restore {len(failed_files)} files"
            )
            
        except Exception as e:
            error_msg = f"Error restoring from ZIP backup: {e}"
            self.logger.error(error_msg)
            
            return RestoreResult(
                success=False,
                backup_info=backup_info,
                restored_files=restored_files,
                failed_files=failed_files,
                error_message=error_msg
            )
    
    def _find_backup_by_path(self, backup_path: str) -> Optional[BackupInfo]:
        """
        Find backup info by backup file path
        """
        for backup_info in self.backup_registry.values():
            if backup_info.backup_path == backup_path:
                return backup_info
        return None
    
    def _remove_backup(self, backup_id: str) -> bool:
        """
        Remove a backup and its files
        """
        if backup_id not in self.backup_registry:
            self.logger.warning(f"Backup ID not found: {backup_id}")
            return False
        
        backup_info = self.backup_registry[backup_id]
        
        try:
            # Remove backup file
            if os.path.exists(backup_info.backup_path):
                os.remove(backup_info.backup_path)
                self.logger.debug(f"Removed backup file: {backup_info.backup_path}")
            
            # Remove from registry
            del self.backup_registry[backup_id]
            self._save_backup_registry()
            
            self.logger.debug(f"Removed backup: {backup_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing backup {backup_id}: {e}")
            return False
    
    def _calculate_file_checksum(self, file_path: str) -> str:
        """
        Calculate SHA256 checksum of a file
        """
        hash_sha256 = hashlib.sha256()
        
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating checksum for {file_path}: {e}")
            return ""
    
    def _load_backup_registry(self) -> Dict[str, BackupInfo]:
        """
        Load backup registry from metadata file
        """
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            registry = {}
            for backup_id, backup_data in data.items():
                registry[backup_id] = BackupInfo(**backup_data)
            
            self.logger.debug(f"Loaded {len(registry)} backup entries from registry")
            return registry
            
        except Exception as e:
            self.logger.error(f"Error loading backup registry: {e}")
            return {}
    
    def _save_backup_registry(self) -> None:
        """
        Save backup registry to metadata file
        """
        try:
            data = {}
            for backup_id, backup_info in self.backup_registry.items():
                data[backup_id] = asdict(backup_info)
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug("Backup registry saved")
            
        except Exception as e:
            self.logger.error(f"Error saving backup registry: {e}")
    
    def get_backup_statistics(self) -> Dict[str, any]:
        """
        Get statistics about backups
        """
        backups = self.list_backups()
        
        if not backups:
            return {
                'total_backups': 0,
                'total_size_bytes': 0,
                'oldest_backup': None,
                'newest_backup': None,
                'average_size_bytes': 0
            }
        
        total_size = sum(b.size_bytes for b in backups)
        oldest = min(backups, key=lambda b: b.created_time)
        newest = max(backups, key=lambda b: b.created_time)
        
        return {
            'total_backups': len(backups),
            'total_size_bytes': total_size,
            'oldest_backup': oldest.created_time,
            'newest_backup': newest.created_time,
            'average_size_bytes': total_size // len(backups),
            'versions': list(set(b.version for b in backups))
        }