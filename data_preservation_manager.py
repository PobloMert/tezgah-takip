"""
Data Preservation Manager for TezgahTakip Update System
Ensures user data integrity during rollback operations
"""

import os
import sys
import shutil
import logging
import json
import sqlite3
from typing import Optional, List, Dict, Set
from pathlib import Path
from dataclasses import dataclass
import hashlib


@dataclass
class DataFile:
    """Information about a user data file"""
    path: str
    file_type: str  # 'database', 'config', 'user_data', 'log'
    is_critical: bool
    backup_path: Optional[str] = None
    checksum: Optional[str] = None


class DataPreservationManager:
    """
    Manages preservation of user data during rollback operations
    """
    
    def __init__(self, path_resolver=None):
        self.logger = logging.getLogger("DataPreservationManager")
        self.path_resolver = path_resolver
        
        # Define critical user data patterns
        self.user_data_patterns = {
            'database': {
                'patterns': ['*.db', '*.sqlite', '*.sqlite3'],
                'critical': True,
                'description': 'Database files containing user data'
            },
            'config': {
                'patterns': ['config.json', 'settings.json', '*.ini'],
                'critical': True,
                'description': 'Configuration files'
            },
            'user_data': {
                'patterns': ['exports/*', 'backups/*', 'reports/*', 'logs/*.log'],
                'critical': False,
                'description': 'User-generated content'
            },
            'cache': {
                'patterns': ['*.cache', 'temp/*', '__pycache__/*'],
                'critical': False,
                'description': 'Cache and temporary files'
            }
        }
        
        self.logger.debug("DataPreservationManager initialized")
    
    def identify_user_data(self, directory: str) -> List[DataFile]:
        """
        Identify all user data files in the given directory
        """
        self.logger.debug(f"Identifying user data in {directory}")
        
        user_data_files = []
        
        if not os.path.exists(directory):
            self.logger.warning(f"Directory does not exist: {directory}")
            return user_data_files
        
        try:
            for root, dirs, files in os.walk(directory):
                # Skip system directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__']]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, directory)
                    
                    # Check against patterns
                    file_type, is_critical = self._classify_file(rel_path)
                    
                    if file_type:
                        data_file = DataFile(
                            path=file_path,
                            file_type=file_type,
                            is_critical=is_critical,
                            checksum=self._calculate_checksum(file_path)
                        )
                        user_data_files.append(data_file)
            
            self.logger.info(f"Identified {len(user_data_files)} user data files")
            return user_data_files
            
        except Exception as e:
            self.logger.error(f"Error identifying user data: {e}")
            return []
    
    def preserve_data_before_rollback(self, data_files: List[DataFile], preservation_dir: str) -> bool:
        """
        Preserve user data before performing rollback
        """
        self.logger.info(f"Preserving {len(data_files)} data files before rollback")
        
        try:
            # Create preservation directory
            os.makedirs(preservation_dir, exist_ok=True)
            
            preserved_count = 0
            
            for data_file in data_files:
                if not os.path.exists(data_file.path):
                    self.logger.warning(f"Data file no longer exists: {data_file.path}")
                    continue
                
                # Create backup path
                rel_path = os.path.basename(data_file.path)
                backup_path = os.path.join(preservation_dir, f"{data_file.file_type}_{rel_path}")
                
                # Ensure unique backup path
                counter = 1
                original_backup_path = backup_path
                while os.path.exists(backup_path):
                    name, ext = os.path.splitext(original_backup_path)
                    backup_path = f"{name}_{counter}{ext}"
                    counter += 1
                
                # Copy file
                try:
                    if data_file.file_type == 'database':
                        # Special handling for database files
                        success = self._preserve_database(data_file.path, backup_path)
                    else:
                        # Regular file copy
                        shutil.copy2(data_file.path, backup_path)
                        success = True
                    
                    if success:
                        data_file.backup_path = backup_path
                        preserved_count += 1
                        self.logger.debug(f"Preserved: {data_file.path} -> {backup_path}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to preserve {data_file.path}: {e}")
                    continue
            
            self.logger.info(f"Successfully preserved {preserved_count}/{len(data_files)} data files")
            return preserved_count > 0
            
        except Exception as e:
            self.logger.error(f"Error during data preservation: {e}")
            return False
    
    def restore_preserved_data(self, data_files: List[DataFile]) -> bool:
        """
        Restore preserved user data after rollback
        """
        self.logger.info(f"Restoring {len(data_files)} preserved data files")
        
        try:
            restored_count = 0
            
            for data_file in data_files:
                if not data_file.backup_path or not os.path.exists(data_file.backup_path):
                    self.logger.warning(f"No backup available for: {data_file.path}")
                    continue
                
                # Ensure target directory exists
                target_dir = os.path.dirname(data_file.path)
                os.makedirs(target_dir, exist_ok=True)
                
                try:
                    if data_file.file_type == 'database':
                        # Special handling for database files
                        success = self._restore_database(data_file.backup_path, data_file.path)
                    else:
                        # Regular file copy
                        shutil.copy2(data_file.backup_path, data_file.path)
                        success = True
                    
                    if success:
                        # Verify integrity
                        if self._verify_restored_file(data_file):
                            restored_count += 1
                            self.logger.debug(f"Restored: {data_file.backup_path} -> {data_file.path}")
                        else:
                            self.logger.warning(f"Integrity check failed for restored file: {data_file.path}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to restore {data_file.path}: {e}")
                    continue
            
            self.logger.info(f"Successfully restored {restored_count}/{len(data_files)} data files")
            return restored_count > 0
            
        except Exception as e:
            self.logger.error(f"Error during data restoration: {e}")
            return False
    
    def validate_data_integrity(self, data_files: List[DataFile]) -> Dict[str, bool]:
        """
        Validate integrity of user data files
        """
        self.logger.debug("Validating data integrity")
        
        validation_results = {}
        
        for data_file in data_files:
            try:
                if not os.path.exists(data_file.path):
                    validation_results[data_file.path] = False
                    continue
                
                # Check file integrity based on type
                if data_file.file_type == 'database':
                    is_valid = self._validate_database_integrity(data_file.path)
                elif data_file.file_type == 'config':
                    is_valid = self._validate_config_integrity(data_file.path)
                else:
                    # Basic file existence and readability check
                    is_valid = os.access(data_file.path, os.R_OK)
                
                # Verify checksum if available
                if is_valid and data_file.checksum:
                    current_checksum = self._calculate_checksum(data_file.path)
                    is_valid = current_checksum == data_file.checksum
                
                validation_results[data_file.path] = is_valid
                
            except Exception as e:
                self.logger.error(f"Error validating {data_file.path}: {e}")
                validation_results[data_file.path] = False
        
        valid_count = sum(1 for v in validation_results.values() if v)
        self.logger.info(f"Data integrity validation: {valid_count}/{len(validation_results)} files valid")
        
        return validation_results
    
    def _classify_file(self, file_path: str) -> tuple[Optional[str], bool]:
        """
        Classify a file based on patterns
        """
        import fnmatch
        
        for file_type, config in self.user_data_patterns.items():
            for pattern in config['patterns']:
                if fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(os.path.basename(file_path), pattern):
                    return file_type, config['critical']
        
        return None, False
    
    def _preserve_database(self, source_path: str, backup_path: str) -> bool:
        """
        Preserve database file with integrity checks
        """
        try:
            # First, try to backup using SQLite backup API if it's a SQLite database
            if source_path.endswith(('.db', '.sqlite', '.sqlite3')):
                return self._backup_sqlite_database(source_path, backup_path)
            else:
                # Regular file copy for other database types
                shutil.copy2(source_path, backup_path)
                return True
                
        except Exception as e:
            self.logger.error(f"Error preserving database {source_path}: {e}")
            return False
    
    def _backup_sqlite_database(self, source_path: str, backup_path: str) -> bool:
        """
        Backup SQLite database using proper SQLite backup API
        """
        try:
            # Connect to source database
            source_conn = sqlite3.connect(source_path)
            
            # Create backup database
            backup_conn = sqlite3.connect(backup_path)
            
            # Perform backup
            source_conn.backup(backup_conn)
            
            # Close connections
            backup_conn.close()
            source_conn.close()
            
            self.logger.debug(f"SQLite database backed up: {source_path} -> {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error backing up SQLite database: {e}")
            # Fallback to regular file copy
            try:
                shutil.copy2(source_path, backup_path)
                return True
            except Exception as e2:
                self.logger.error(f"Fallback copy also failed: {e2}")
                return False
    
    def _restore_database(self, backup_path: str, target_path: str) -> bool:
        """
        Restore database file with integrity checks
        """
        try:
            if target_path.endswith(('.db', '.sqlite', '.sqlite3')):
                # For SQLite databases, validate before restoring
                if self._validate_database_integrity(backup_path):
                    shutil.copy2(backup_path, target_path)
                    return True
                else:
                    self.logger.error(f"Backup database integrity check failed: {backup_path}")
                    return False
            else:
                # Regular file copy for other database types
                shutil.copy2(backup_path, target_path)
                return True
                
        except Exception as e:
            self.logger.error(f"Error restoring database {target_path}: {e}")
            return False
    
    def _validate_database_integrity(self, db_path: str) -> bool:
        """
        Validate SQLite database integrity
        """
        try:
            if not db_path.endswith(('.db', '.sqlite', '.sqlite3')):
                # For non-SQLite databases, just check if file is readable
                return os.access(db_path, os.R_OK)
            
            # SQLite integrity check
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Run integrity check
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            
            conn.close()
            
            # Result should be 'ok' for a valid database
            is_valid = result and result[0].lower() == 'ok'
            
            if not is_valid:
                self.logger.warning(f"Database integrity check failed: {db_path}")
            
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Error validating database integrity {db_path}: {e}")
            return False
    
    def _validate_config_integrity(self, config_path: str) -> bool:
        """
        Validate configuration file integrity
        """
        try:
            if config_path.endswith('.json'):
                # Validate JSON format
                with open(config_path, 'r', encoding='utf-8') as f:
                    json.load(f)
                return True
            else:
                # For other config files, just check readability
                return os.access(config_path, os.R_OK)
                
        except Exception as e:
            self.logger.error(f"Error validating config integrity {config_path}: {e}")
            return False
    
    def _verify_restored_file(self, data_file: DataFile) -> bool:
        """
        Verify that a restored file is intact
        """
        try:
            if not os.path.exists(data_file.path):
                return False
            
            # Check file size
            if os.path.getsize(data_file.path) == 0:
                return False
            
            # Verify checksum if available
            if data_file.checksum:
                current_checksum = self._calculate_checksum(data_file.path)
                return current_checksum == data_file.checksum
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying restored file {data_file.path}: {e}")
            return False
    
    def _calculate_checksum(self, file_path: str) -> str:
        """
        Calculate SHA256 checksum of a file
        """
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating checksum for {file_path}: {e}")
            return ""
    
    def get_preservation_summary(self, data_files: List[DataFile]) -> Dict[str, any]:
        """
        Get summary of data preservation status
        """
        summary = {
            'total_files': len(data_files),
            'critical_files': 0,
            'preserved_files': 0,
            'file_types': {},
            'total_size_bytes': 0
        }
        
        for data_file in data_files:
            if data_file.is_critical:
                summary['critical_files'] += 1
            
            if data_file.backup_path and os.path.exists(data_file.backup_path):
                summary['preserved_files'] += 1
            
            # Count by file type
            if data_file.file_type not in summary['file_types']:
                summary['file_types'][data_file.file_type] = 0
            summary['file_types'][data_file.file_type] += 1
            
            # Add file size
            try:
                if os.path.exists(data_file.path):
                    summary['total_size_bytes'] += os.path.getsize(data_file.path)
            except Exception:
                pass
        
        return summary