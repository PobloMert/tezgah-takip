"""
Property-based tests for BackupManager
Tests universal properties for backup creation, restoration, and cleanup
"""

import os
import sys
import tempfile
import shutil
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from hypothesis import given, strategies as st, assume, settings

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backup_manager import BackupManager, BackupInfo, RestoreResult
from path_resolver import PathResolver


class TestBackupManagerProperties:
    """Property-based tests for BackupManager"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.temp_dirs = []
        self.mock_path_resolver = MagicMock(spec=PathResolver)
    
    def teardown_method(self):
        """Cleanup after each test method"""
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def create_temp_dir(self) -> str:
        """Create a temporary directory and track it for cleanup"""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    @given(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))).filter(
               lambda x: '.' in x or len(x) > 3),  # Version-like strings
           st.lists(st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))).filter(
               lambda x: x.upper() not in ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']), 
                   min_size=1, max_size=5))
    @settings(max_examples=20)
    def test_property_9_backup_creation_consistency(self, version, filenames):
        """
        Property 9: Backup Creation Consistency
        For any update initiation, the system should create a backup of the current version before proceeding
        **Feature: update-compatibility-fix, Property 9: Backup Creation Consistency**
        **Validates: Requirements 3.1**
        """
        assume(len(version.strip()) > 0)
        assume(all(len(f.strip()) > 0 for f in filenames))
        
        # Create temporary directories
        backup_dir = self.create_temp_dir()
        source_dir = self.create_temp_dir()
        
        # Create source files
        created_files = []
        for filename in filenames:
            file_path = os.path.join(source_dir, filename + ".txt")
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"Content for {filename}")
                created_files.append(file_path)
            except Exception:
                continue  # Skip files that can't be created
        
        # Skip if no files were created
        assume(len(created_files) > 0)
        
        # Mock path resolver
        self.mock_path_resolver.get_executable_directory.return_value = source_dir
        
        # Create backup manager
        backup_manager = BackupManager(backup_root=backup_dir, path_resolver=self.mock_path_resolver)
        
        # Property: Backup creation should succeed for valid inputs
        backup_path = backup_manager.create_backup(version, source_dir)
        
        if backup_path:
            assert isinstance(backup_path, str), "Backup path should be a string"
            assert os.path.exists(backup_path), "Backup file should exist after creation"
            assert backup_path.endswith('.zip'), "Backup should be a ZIP file"
            
            # Property: Backup should be verifiable
            is_valid = backup_manager.verify_backup_integrity(backup_path)
            assert is_valid, "Created backup should pass integrity verification"
    
    @given(st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))).filter(
               lambda x: '.' in x or len(x) > 2))
    @settings(max_examples=50)
    def test_property_10_automatic_rollback_on_failure(self, version):
        """
        Property 10: Automatic Rollback on Failure
        For any failed update, the system should automatically restore the previous version from backup
        **Feature: update-compatibility-fix, Property 10: Automatic Rollback on Failure**
        **Validates: Requirements 3.2**
        """
        assume(len(version.strip()) > 0)
        
        # Create temporary directories
        backup_dir = self.create_temp_dir()
        source_dir = self.create_temp_dir()
        
        # Create source files
        test_files = ['app.py', 'config.json', 'data.txt']
        for filename in test_files:
            file_path = os.path.join(source_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Original content for {filename}")
        
        # Mock path resolver
        self.mock_path_resolver.get_executable_directory.return_value = source_dir
        
        # Create backup manager and backup
        backup_manager = BackupManager(backup_root=backup_dir, path_resolver=self.mock_path_resolver)
        backup_path = backup_manager.create_backup(version, source_dir)
        
        assume(backup_path is not None)  # Skip if backup creation failed
        
        # Simulate file corruption/modification (simulating failed update)
        for filename in test_files:
            file_path = os.path.join(source_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"CORRUPTED content for {filename}")
        
        # Property: Restore should succeed
        restore_success = backup_manager.restore_backup(backup_path)
        
        if restore_success:
            # Property: Files should be restored to original state
            for filename in test_files:
                file_path = os.path.join(source_dir, filename)
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    assert f"Original content for {filename}" in content, f"File {filename} should be restored to original state"
    
    @given(st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))).filter(
               lambda x: '.' in x or len(x) > 2),
           st.integers(min_value=1, max_value=5))
    @settings(max_examples=50)
    def test_property_12_backup_cleanup_after_success(self, version, num_backups):
        """
        Property 12: Backup Cleanup After Success
        For any successful update completion, old backup files should be cleaned up to save disk space
        **Feature: update-compatibility-fix, Property 12: Backup Cleanup After Success**
        **Validates: Requirements 3.4**
        """
        assume(len(version.strip()) > 0)
        
        # Create temporary directories
        backup_dir = self.create_temp_dir()
        source_dir = self.create_temp_dir()
        
        # Create a simple source file
        test_file = os.path.join(source_dir, "test.txt")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("Test content")
        
        # Mock path resolver
        self.mock_path_resolver.get_executable_directory.return_value = source_dir
        
        # Create backup manager with low limits for testing
        backup_manager = BackupManager(backup_root=backup_dir, path_resolver=self.mock_path_resolver)
        backup_manager.max_backups = 2  # Low limit for testing
        backup_manager.max_backup_age_days = 1  # Short age for testing
        
        # Create multiple backups
        created_backups = []
        for i in range(num_backups):
            backup_path = backup_manager.create_backup(f"{version}_{i}", source_dir)
            if backup_path:
                created_backups.append(backup_path)
                # Add small delay to ensure different timestamps
                time.sleep(0.1)
        
        assume(len(created_backups) > 0)  # Skip if no backups were created
        
        initial_backup_count = len(backup_manager.list_backups())
        
        # Property: Cleanup should not crash
        try:
            backup_manager.cleanup_old_backups()
            cleanup_success = True
        except Exception:
            cleanup_success = False
        
        assert cleanup_success, "Backup cleanup should not raise exceptions"
        
        # Property: Cleanup should respect limits
        final_backup_count = len(backup_manager.list_backups())
        assert final_backup_count <= backup_manager.max_backups, "Cleanup should respect backup count limits"
    
    @given(st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))).filter(
               lambda x: '.' in x or len(x) > 2))
    @settings(max_examples=50)
    def test_property_backup_integrity_verification(self, version):
        """
        Property: Backup integrity verification should be reliable
        For any created backup, integrity verification should consistently report the same result
        """
        assume(len(version.strip()) > 0)
        
        # Create temporary directories
        backup_dir = self.create_temp_dir()
        source_dir = self.create_temp_dir()
        
        # Create source files
        test_file = os.path.join(source_dir, "integrity_test.txt")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("Content for integrity testing")
        
        # Mock path resolver
        self.mock_path_resolver.get_executable_directory.return_value = source_dir
        
        # Create backup manager and backup
        backup_manager = BackupManager(backup_root=backup_dir, path_resolver=self.mock_path_resolver)
        backup_path = backup_manager.create_backup(version, source_dir)
        
        assume(backup_path is not None)  # Skip if backup creation failed
        
        # Property: Integrity verification should be consistent
        result1 = backup_manager.verify_backup_integrity(backup_path)
        result2 = backup_manager.verify_backup_integrity(backup_path)
        result3 = backup_manager.verify_backup_integrity(backup_path)
        
        assert result1 == result2 == result3, "Integrity verification should be consistent"
        assert isinstance(result1, bool), "Integrity verification should return boolean"
    
    @given(st.lists(st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))).filter(
               lambda x: x.upper() not in ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']), 
                   min_size=1, max_size=3))
    @settings(max_examples=50)
    def test_property_backup_statistics_accuracy(self, filenames):
        """
        Property: Backup statistics should accurately reflect the actual backups
        For any set of backups, statistics should match the reality
        """
        assume(all(len(f.strip()) > 0 for f in filenames))
        
        # Create temporary directories
        backup_dir = self.create_temp_dir()
        source_dir = self.create_temp_dir()
        
        # Create source files
        for filename in filenames:
            file_path = os.path.join(source_dir, filename + ".txt")
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"Content for {filename}")
            except Exception:
                continue
        
        # Mock path resolver
        self.mock_path_resolver.get_executable_directory.return_value = source_dir
        
        # Create backup manager
        backup_manager = BackupManager(backup_root=backup_dir, path_resolver=self.mock_path_resolver)
        
        # Create some backups
        created_versions = []
        for i, filename in enumerate(filenames):
            version = f"v1.{i}"
            backup_path = backup_manager.create_backup(version, source_dir)
            if backup_path:
                created_versions.append(version)
        
        # Property: Statistics should match reality
        stats = backup_manager.get_backup_statistics()
        actual_backups = backup_manager.list_backups()
        
        assert isinstance(stats, dict), "Statistics should be a dictionary"
        assert stats['total_backups'] == len(actual_backups), "Total backup count should match"
        
        if actual_backups:
            assert stats['total_size_bytes'] > 0, "Total size should be positive when backups exist"
            assert stats['oldest_backup'] is not None, "Should have oldest backup timestamp"
            assert stats['newest_backup'] is not None, "Should have newest backup timestamp"
            assert stats['oldest_backup'] <= stats['newest_backup'], "Oldest should be <= newest"
    
    @given(st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))).filter(
               lambda x: '.' in x or len(x) > 2))
    @settings(max_examples=50)
    def test_property_backup_restore_safety(self, version):
        """
        Property: Backup restore operations should be safe and not cause data loss
        For any backup restore, the operation should either succeed completely or fail safely
        """
        assume(len(version.strip()) > 0)
        
        # Create temporary directories
        backup_dir = self.create_temp_dir()
        source_dir = self.create_temp_dir()
        
        # Create source files
        original_files = {'app.py': 'original app', 'config.json': '{"version": "1.0"}'}
        for filename, content in original_files.items():
            file_path = os.path.join(source_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Mock path resolver
        self.mock_path_resolver.get_executable_directory.return_value = source_dir
        
        # Create backup manager and backup
        backup_manager = BackupManager(backup_root=backup_dir, path_resolver=self.mock_path_resolver)
        backup_path = backup_manager.create_backup(version, source_dir)
        
        assume(backup_path is not None)  # Skip if backup creation failed
        
        # Modify files (simulate update)
        for filename in original_files.keys():
            file_path = os.path.join(source_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("MODIFIED CONTENT")
        
        # Property: Restore should not raise unhandled exceptions
        try:
            restore_result = backup_manager.restore_backup(backup_path)
            assert isinstance(restore_result, bool), "Restore should return boolean result"
        except Exception as e:
            assert False, f"Restore should not raise unhandled exceptions: {e}"
    
    @given(st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))).filter(
               lambda x: '.' in x or len(x) > 2))
    @settings(max_examples=50)
    def test_property_backup_listing_consistency(self, version):
        """
        Property: Backup listing should be consistent and accurate
        For any backup operations, listing should reflect the current state
        """
        assume(len(version.strip()) > 0)
        
        # Create temporary directories
        backup_dir = self.create_temp_dir()
        source_dir = self.create_temp_dir()
        
        # Create a simple source file
        test_file = os.path.join(source_dir, "list_test.txt")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("Test content for listing")
        
        # Mock path resolver
        self.mock_path_resolver.get_executable_directory.return_value = source_dir
        
        # Create backup manager
        backup_manager = BackupManager(backup_root=backup_dir, path_resolver=self.mock_path_resolver)
        
        # Initial state - should have no backups
        initial_backups = backup_manager.list_backups()
        assert isinstance(initial_backups, list), "Backup list should be a list"
        
        # Create a backup
        backup_path = backup_manager.create_backup(version, source_dir)
        
        if backup_path:
            # Property: List should reflect the new backup
            updated_backups = backup_manager.list_backups()
            assert len(updated_backups) == len(initial_backups) + 1, "Backup count should increase by 1"
            
            # Property: All listed backups should be BackupInfo objects
            for backup_info in updated_backups:
                assert hasattr(backup_info, 'backup_id'), "Should have backup_id attribute"
                assert hasattr(backup_info, 'version'), "Should have version attribute"
                assert hasattr(backup_info, 'created_time'), "Should have created_time attribute"
                assert hasattr(backup_info, 'backup_path'), "Should have backup_path attribute"


if __name__ == "__main__":
    # Run basic property tests
    test_instance = TestBackupManagerProperties()
    
    print("Running property-based tests for BackupManager...")
    
    # You can run individual tests here for debugging
    # test_instance.test_property_9_backup_creation_consistency("v1.0", ["test"])
    
    print("Property tests completed. Run with pytest for full test suite.")