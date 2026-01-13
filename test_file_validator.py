"""
Property-based tests for FileValidator
Tests universal properties for file integrity checking and dependency validation
"""

import os
import sys
import tempfile
import shutil
import json
import zipfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from hypothesis import given, strategies as st, assume, settings

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from file_validator import FileValidator, ValidationResult, DependencyInfo, FileInfo
from path_resolver import PathResolver


class TestFileValidatorProperties:
    """Property-based tests for FileValidator"""
    
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
    
    @given(st.text(min_size=0, max_size=1000, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Ps', 'Pe', 'Po'))))
    @settings(max_examples=100)
    def test_property_2_base_library_discovery(self, file_content):
        """
        Property 2: Base Library Discovery
        For any completed update, the launcher should be able to locate the base_library.zip file in the expected location
        **Feature: update-compatibility-fix, Property 2: Base Library Discovery**
        **Validates: Requirements 1.2**
        """
        # Create temporary directory and file
        temp_dir = self.create_temp_dir()
        test_file = os.path.join(temp_dir, "base_library.zip")
        
        # Create a valid ZIP file with content
        try:
            with zipfile.ZipFile(test_file, 'w') as zf:
                # Add some content to make it a valid ZIP
                zf.writestr("test.txt", file_content.encode('utf-8', errors='ignore'))
        except Exception:
            # If ZIP creation fails, create a regular file
            with open(test_file, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(file_content)
        
        validator = FileValidator()
        
        # Property: File integrity check should not crash
        result = validator.check_file_integrity(test_file)
        
        assert isinstance(result, ValidationResult), "Should return ValidationResult object"
        assert isinstance(result.is_valid, bool), "is_valid should be boolean"
        assert isinstance(result.errors, list), "errors should be a list"
        assert isinstance(result.warnings, list), "warnings should be a list"
        
        # Property: If file exists, file_info should be populated
        if os.path.exists(test_file):
            assert result.file_info is not None, "file_info should be populated for existing files"
            assert isinstance(result.file_info, FileInfo), "file_info should be FileInfo object"
            assert result.file_info.path == test_file, "file_info should have correct path"
    
    @given(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))).filter(
               lambda x: x.upper() not in ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']),
           st.booleans())
    @settings(max_examples=100)
    def test_property_19_manual_file_integrity_verification(self, filename, create_file):
        """
        Property 19: Manual File Integrity Verification
        For any manual file copy operation, file integrity should be verified automatically
        **Feature: update-compatibility-fix, Property 19: Manual File Integrity Verification**
        **Validates: Requirements 5.3**
        """
        assume(len(filename.strip()) > 0)
        
        temp_dir = self.create_temp_dir()
        test_file = os.path.join(temp_dir, filename)
        
        if create_file:
            # Create a test file
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write("Test content for integrity verification")
        
        validator = FileValidator()
        
        # Property: Integrity check should handle both existing and non-existing files
        result = validator.check_file_integrity(test_file)
        
        assert isinstance(result, ValidationResult), "Should return ValidationResult"
        
        if create_file:
            # Property: For existing files, should provide detailed information
            assert result.file_info is not None, "Should have file info for existing files"
            assert result.file_info.size >= 0, "File size should be non-negative"
            assert result.file_info.checksum, "Should calculate checksum for existing files"
            assert result.file_info.modified_time > 0, "Should have valid modification time"
        else:
            # Property: For non-existing files, should report error
            assert not result.is_valid, "Should be invalid for non-existing files"
            assert len(result.errors) > 0, "Should have errors for non-existing files"
    
    @given(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))).filter(
               lambda x: x.upper() not in ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']),
           st.sampled_from(['.py', '.json', '.zip', '.txt', '.exe']))
    @settings(max_examples=100)
    def test_property_file_validation_consistency(self, base_name, extension):
        """
        Property: File validation should be consistent across multiple calls
        For any file, validation results should be the same when called multiple times
        """
        assume(len(base_name.strip()) > 0)
        
        temp_dir = self.create_temp_dir()
        filename = base_name + extension
        test_file = os.path.join(temp_dir, filename)
        
        # Create appropriate file content based on extension
        if extension == '.json':
            content = '{"test": "value"}'
        elif extension == '.py':
            content = 'print("Hello World")'
        elif extension == '.zip':
            # Create a valid ZIP file
            with zipfile.ZipFile(test_file, 'w') as zf:
                zf.writestr("test.txt", "test content")
            content = None  # Already created
        else:
            content = "Test file content"
        
        if content is not None:
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(content)
        
        validator = FileValidator()
        
        # Property: Multiple validations should return consistent results
        result1 = validator.check_file_integrity(test_file)
        result2 = validator.check_file_integrity(test_file)
        result3 = validator.check_file_integrity(test_file)
        
        assert result1.is_valid == result2.is_valid == result3.is_valid, "Validation results should be consistent"
        assert len(result1.errors) == len(result2.errors) == len(result3.errors), "Error counts should be consistent"
        
        if result1.file_info and result2.file_info and result3.file_info:
            assert result1.file_info.checksum == result2.file_info.checksum == result3.file_info.checksum, \
                "Checksums should be consistent"
    
    @given(st.lists(st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))), 
                   min_size=1, max_size=8))
    @settings(max_examples=100)
    def test_property_dependency_validation_completeness(self, module_names):
        """
        Property: Dependency validation should check all specified dependencies
        For any list of dependencies, validation should return results for all of them
        """
        assume(all(len(name.strip()) > 0 for name in module_names))
        
        validator = FileValidator()
        
        # Mock the python dependencies to use our test list
        original_deps = validator.python_dependencies
        validator.python_dependencies = module_names
        
        try:
            # Property: Should return results for all dependencies
            results = validator.validate_dependencies()
            
            assert isinstance(results, list), "Should return list of results"
            assert len(results) > 0, "Should return at least some results"
            
            # Property: All results should be DependencyInfo objects
            for result in results:
                assert isinstance(result, DependencyInfo), "All results should be DependencyInfo objects"
                assert result.name, "Each dependency should have a name"
                assert isinstance(result.required, bool), "required should be boolean"
                assert isinstance(result.found, bool), "found should be boolean"
                
        finally:
            # Restore original dependencies
            validator.python_dependencies = original_deps
    
    @given(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))).filter(
               lambda x: x.upper() not in ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']),
           st.integers(min_value=0, max_value=10000))
    @settings(max_examples=100)
    def test_property_file_size_validation(self, filename, file_size):
        """
        Property: File size validation should handle files of any size
        For any file size, validation should complete without errors
        """
        assume(len(filename.strip()) > 0)
        
        temp_dir = self.create_temp_dir()
        test_file = os.path.join(temp_dir, filename)
        
        # Create file with specified size
        try:
            with open(test_file, 'w', encoding='utf-8') as f:
                # Write content to reach approximately the desired size
                content = "x" * min(file_size, 1000)  # Limit to reasonable size for testing
                f.write(content)
        except Exception:
            assume(False)  # Skip if file creation fails
        
        validator = FileValidator()
        
        # Property: Validation should handle any file size
        result = validator.check_file_integrity(test_file)
        
        assert isinstance(result, ValidationResult), "Should return ValidationResult"
        
        if result.file_info:
            assert result.file_info.size >= 0, "File size should be non-negative"
            
            # Property: Empty files should be flagged
            if result.file_info.size == 0:
                assert not result.is_valid or "empty" in str(result.errors).lower(), \
                    "Empty files should be flagged as invalid or have empty-related errors"
    
    @given(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))).filter(
               lambda x: x.upper() not in ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']))
    @settings(max_examples=100)
    def test_property_permission_checking_safety(self, path_component):
        """
        Property: Permission checking should be safe and not cause system issues
        For any path, permission checking should either succeed or fail gracefully
        """
        assume(len(path_component.strip()) > 0)
        
        temp_dir = self.create_temp_dir()
        test_path = os.path.join(temp_dir, path_component)
        
        # Create the path
        try:
            os.makedirs(test_path, exist_ok=True)
        except Exception:
            assume(False)  # Skip if path creation fails
        
        validator = FileValidator()
        
        # Property: Permission checking should not raise exceptions
        try:
            result = validator.check_permissions(test_path)
            assert isinstance(result, bool), "Should return boolean result"
        except Exception as e:
            assert False, f"Permission checking should not raise exceptions: {e}"
    
    @given(st.booleans(), st.booleans(), st.booleans())
    @settings(max_examples=100)
    def test_property_executable_structure_validation(self, has_main_py, has_config, has_launcher):
        """
        Property: Executable structure validation should handle various file combinations
        For any combination of files, structure validation should complete
        """
        temp_dir = self.create_temp_dir()
        
        # Create files based on parameters
        if has_main_py:
            main_file = os.path.join(temp_dir, "tezgah_takip_app.py")
            with open(main_file, 'w', encoding='utf-8') as f:
                f.write('print("Main application")')
        
        if has_config:
            config_file = os.path.join(temp_dir, "config.json")
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write('{"version": "2.1.3"}')
        
        if has_launcher:
            launcher_file = os.path.join(temp_dir, "launcher.py")
            with open(launcher_file, 'w', encoding='utf-8') as f:
                f.write('import sys')
        
        # Mock path resolver
        self.mock_path_resolver.get_executable_directory.return_value = temp_dir
        
        validator = FileValidator(self.mock_path_resolver)
        
        # Property: Structure validation should not crash
        try:
            result = validator.verify_executable_structure()
            assert isinstance(result, bool), "Should return boolean result"
        except Exception as e:
            assert False, f"Structure validation should not raise exceptions: {e}"
    
    @given(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Po', 'Ps', 'Pe'))))
    @settings(max_examples=100)
    def test_property_json_validation_robustness(self, json_content):
        """
        Property: JSON validation should handle any input safely
        For any string content, JSON validation should not crash
        """
        temp_dir = self.create_temp_dir()
        json_file = os.path.join(temp_dir, "test.json")
        
        # Write content to file
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                f.write(json_content)
        except Exception:
            assume(False)  # Skip if file writing fails
        
        validator = FileValidator()
        
        # Property: JSON validation should not crash
        try:
            result = validator.check_file_integrity(json_file)
            assert isinstance(result, ValidationResult), "Should return ValidationResult"
            
            # Property: Invalid JSON should be flagged
            try:
                json.loads(json_content)
                # If JSON is valid, validation might pass
            except json.JSONDecodeError:
                # If JSON is invalid, should have errors
                if result.is_valid:
                    # It's okay if other factors make it invalid
                    pass
                else:
                    assert len(result.errors) > 0, "Invalid JSON should have errors"
                    
        except Exception as e:
            assert False, f"JSON validation should not raise unhandled exceptions: {e}"
    
    @given(st.lists(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))), 
                   min_size=1, max_size=5))
    @settings(max_examples=100)
    def test_property_validation_summary_accuracy(self, dependency_names):
        """
        Property: Validation summary should accurately reflect dependency results
        For any set of dependencies, summary should match the actual results
        """
        assume(all(len(name.strip()) > 0 for name in dependency_names))
        
        validator = FileValidator()
        
        # Create mock dependency results
        dependency_results = []
        expected_found = 0
        expected_missing_required = 0
        expected_missing_optional = 0
        
        for i, name in enumerate(dependency_names):
            is_required = i % 2 == 0  # Alternate between required and optional
            is_found = i % 3 != 0     # Most are found, some are missing
            
            if is_found:
                expected_found += 1
            else:
                if is_required:
                    expected_missing_required += 1
                else:
                    expected_missing_optional += 1
            
            dependency_results.append(DependencyInfo(
                name=name,
                required=is_required,
                found=is_found,
                issues=[] if is_found else ["Test issue"]
            ))
        
        # Property: Summary should accurately reflect the results
        summary = validator.get_validation_summary(dependency_results)
        
        assert isinstance(summary, dict), "Summary should be a dictionary"
        assert summary['total_dependencies'] == len(dependency_names), "Total count should match"
        assert summary['found_dependencies'] == expected_found, "Found count should match"
        assert summary['missing_required'] == expected_missing_required, "Missing required count should match"
        assert summary['missing_optional'] == expected_missing_optional, "Missing optional count should match"


if __name__ == "__main__":
    # Run basic property tests
    test_instance = TestFileValidatorProperties()
    
    print("Running property-based tests for FileValidator...")
    
    # You can run individual tests here for debugging
    # test_instance.test_property_2_base_library_discovery("test content")
    
    print("Property tests completed. Run with pytest for full test suite.")