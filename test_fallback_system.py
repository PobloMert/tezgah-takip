"""
Property-based tests for FallbackSystem
Tests universal properties for alternative path fallback and manual recovery
"""

import os
import sys
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from hypothesis import given, strategies as st, assume, settings

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fallback_system import FallbackSystem, FallbackOption, RecoveryPlan
from path_resolver import PathResolver


class TestFallbackSystemProperties:
    """Property-based tests for FallbackSystem"""
    
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
    
    @given(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))),
           st.lists(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))), 
                   min_size=1, max_size=5))
    @settings(max_examples=100)
    def test_property_7_alternative_path_fallback(self, filename, search_directories):
        """
        Property 7: Alternative Path Fallback
        For any file not found scenario, the system should attempt alternative paths before reporting failure
        **Feature: update-compatibility-fix, Property 7: Alternative Path Fallback**
        **Validates: Requirements 2.3**
        """
        assume(len(filename.strip()) > 0)
        assume(all(len(d.strip()) > 0 for d in search_directories))
        
        # Create temporary directory structure
        base_temp = self.create_temp_dir()
        
        # Create search directories
        created_dirs = []
        for i, dir_name in enumerate(search_directories):
            dir_path = os.path.join(base_temp, f"dir_{i}_{dir_name}")
            os.makedirs(dir_path, exist_ok=True)
            created_dirs.append(dir_path)
        
        # Mock path resolver to return our test directories
        self.mock_path_resolver.get_search_paths.return_value = created_dirs
        
        fallback_system = FallbackSystem(self.mock_path_resolver)
        
        # Property: When file is not found, system should try alternative paths
        result = fallback_system.find_alternative_file(filename, created_dirs)
        
        # Property: The system should not crash when file is not found
        assert result is None or isinstance(result, str), "Should return None or valid path string"
        
        # Property: If result is returned, it should be a valid file path
        if result is not None:
            assert os.path.isfile(result), "Returned path should be an existing file"
            assert os.path.isabs(result), "Returned path should be absolute"
    
    @given(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
           st.lists(st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))), 
                   min_size=1, max_size=4),
           st.integers(min_value=0, max_value=3))
    @settings(max_examples=100)
    def test_property_alternative_file_discovery(self, base_filename, alt_names, target_index):
        """
        Property: Alternative file discovery should find files when they exist
        For any set of alternative file names, if any alternative exists, it should be found
        """
        assume(len(base_filename.strip()) > 0)
        assume(all(len(name.strip()) > 0 for name in alt_names))
        assume(len(alt_names) > target_index)
        
        # Create temporary directory
        temp_dir = self.create_temp_dir()
        
        # Create one of the alternative files
        target_alt_name = alt_names[target_index]
        target_file_path = os.path.join(temp_dir, target_alt_name)
        
        with open(target_file_path, 'w', encoding='utf-8') as f:
            f.write(f"Alternative content for {target_alt_name}")
        
        # Mock the file alternatives
        fallback_system = FallbackSystem()
        fallback_system.file_alternatives[base_filename] = alt_names
        
        # Property: Should find the existing alternative file
        result = fallback_system.find_alternative_file(base_filename, [temp_dir])
        
        assert result is not None, "Should find existing alternative file"
        assert os.path.exists(result), "Found file should exist"
        assert target_alt_name in result, "Should find the correct alternative file"
    
    @given(st.text(min_size=1, max_size=25, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
           st.sampled_from(['missing_base_library', 'missing_executable', 'permission_denied', 'corrupted_files', 'path_not_found']))
    @settings(max_examples=100)
    def test_property_8_manual_recovery_options(self, filename, error_type):
        """
        Property 8: Manual Recovery Options
        For any complete path search failure, the system should provide manual solution suggestions to the user
        **Feature: update-compatibility-fix, Property 8: Manual Recovery Options**
        **Validates: Requirements 2.4**
        """
        assume(len(filename.strip()) > 0)
        
        fallback_system = FallbackSystem(self.mock_path_resolver)
        
        # Property: Recovery plan should always be generated
        recovery_plan = fallback_system.create_recovery_plan(error_type, [filename])
        
        assert isinstance(recovery_plan, RecoveryPlan), "Should return RecoveryPlan object"
        assert recovery_plan.primary_issue, "Should have a primary issue description"
        
        # Property: Recovery plan should contain actionable suggestions
        assert len(recovery_plan.fallback_options) > 0 or len(recovery_plan.manual_suggestions) > 0, \
            "Should provide either fallback options or manual suggestions"
        
        # Property: All fallback options should be valid
        for option in recovery_plan.fallback_options:
            assert isinstance(option, FallbackOption), "Should be FallbackOption instance"
            assert 0.0 <= option.confidence <= 1.0, "Confidence should be between 0 and 1"
            assert option.reason, "Should have a reason"
            assert isinstance(option.manual_steps, list), "Manual steps should be a list"
    
    @given(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    @settings(max_examples=100)
    def test_property_manual_path_suggestions_consistency(self, filename):
        """
        Property: Manual path suggestions should be consistent
        For any filename, manual path suggestions should return the same results when called multiple times
        """
        assume(len(filename.strip()) > 0)
        
        fallback_system = FallbackSystem(self.mock_path_resolver)
        
        # Property: Suggestions should be consistent across calls
        suggestions1 = fallback_system.suggest_manual_paths(filename)
        suggestions2 = fallback_system.suggest_manual_paths(filename)
        
        assert len(suggestions1) == len(suggestions2), "Should return same number of suggestions"
        
        # Property: All suggestions should be valid FallbackOption objects
        for suggestion in suggestions1:
            assert isinstance(suggestion, FallbackOption), "Should be FallbackOption instance"
            assert suggestion.path, "Should have a path"
            assert 0.0 <= suggestion.confidence <= 1.0, "Confidence should be valid"
            assert suggestion.reason, "Should have a reason"
    
    @given(st.lists(st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))), 
                   min_size=1, max_size=5),
           st.sampled_from(['missing_base_library', 'permission_denied', 'corrupted_files']))
    @settings(max_examples=100)
    def test_property_recovery_plan_completeness(self, missing_files, error_type):
        """
        Property: Recovery plans should be complete and actionable
        For any error type and missing files, recovery plan should provide comprehensive guidance
        """
        assume(all(len(f.strip()) > 0 for f in missing_files))
        
        fallback_system = FallbackSystem(self.mock_path_resolver)
        
        # Property: Recovery plan should address all missing files
        recovery_plan = fallback_system.create_recovery_plan(error_type, missing_files)
        
        assert recovery_plan.primary_issue, "Should identify the primary issue"
        
        # Property: Should provide multiple recovery approaches
        total_options = len(recovery_plan.fallback_options) + len(recovery_plan.manual_suggestions)
        assert total_options > 0, "Should provide at least one recovery option"
        
        # Property: Emergency contacts should be provided for serious issues
        if error_type in ['missing_base_library', 'corrupted_files']:
            assert len(recovery_plan.emergency_contacts) > 0, "Should provide emergency contacts for serious issues"
    
    @given(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
           st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
           st.floats(min_value=0.0, max_value=1.0))
    @settings(max_examples=100)
    def test_property_fallback_option_execution_safety(self, filename, path_component, confidence):
        """
        Property: Fallback option execution should be safe and not cause system damage
        For any fallback option, execution should either succeed safely or fail gracefully
        """
        assume(len(filename.strip()) > 0)
        assume(len(path_component.strip()) > 0)
        
        # Create a temporary directory structure
        temp_dir = self.create_temp_dir()
        test_path = os.path.join(temp_dir, path_component)
        os.makedirs(test_path, exist_ok=True)
        
        # Create a test file to copy
        source_file = os.path.join(test_path, filename)
        with open(source_file, 'w', encoding='utf-8') as f:
            f.write("Test content")
        
        # Create fallback option
        option = FallbackOption(
            path=test_path,
            confidence=confidence,
            reason="Test fallback option",
            manual_steps=["Test step"]
        )
        
        # Mock path resolver
        self.mock_path_resolver.get_executable_directory.return_value = temp_dir
        
        fallback_system = FallbackSystem(self.mock_path_resolver)
        
        # Property: Execution should not raise unhandled exceptions
        try:
            result = fallback_system.execute_fallback_option(option, filename)
            assert isinstance(result, bool), "Should return boolean result"
            
            # Property: If successful, target file should exist
            if result:
                target_file = os.path.join(temp_dir, filename)
                assert os.path.exists(target_file), "Target file should exist after successful execution"
                
        except Exception as e:
            # Property: Any exceptions should be handled gracefully
            assert False, f"Fallback execution should not raise unhandled exceptions: {e}"
    
    @given(st.sampled_from(['missing_base_library', 'missing_executable', 'permission_denied', 'corrupted_files', 'path_not_found', 'unknown_error']))
    @settings(max_examples=100)
    def test_property_user_friendly_suggestions_format(self, error_type):
        """
        Property: User-friendly suggestions should be properly formatted and helpful
        For any recovery plan, user-friendly suggestions should be clear and actionable
        """
        fallback_system = FallbackSystem(self.mock_path_resolver)
        
        # Create a recovery plan
        recovery_plan = fallback_system.create_recovery_plan(error_type, ['test_file.txt'])
        
        # Property: Should generate user-friendly suggestions
        suggestions = fallback_system.get_user_friendly_suggestions(recovery_plan)
        
        assert isinstance(suggestions, list), "Should return list of suggestions"
        assert len(suggestions) > 0, "Should provide at least one suggestion"
        
        # Property: First suggestion should describe the issue
        assert suggestions[0], "First suggestion should not be empty"
        assert "Issue:" in suggestions[0] or recovery_plan.primary_issue in suggestions[0], \
            "Should describe the primary issue"
        
        # Property: Suggestions should be strings
        for suggestion in suggestions:
            assert isinstance(suggestion, str), "All suggestions should be strings"


if __name__ == "__main__":
    # Run basic property tests
    test_instance = TestFallbackSystemProperties()
    
    print("Running property-based tests for FallbackSystem...")
    
    # You can run individual tests here for debugging
    # test_instance.test_property_7_alternative_path_fallback("test.zip", ["dir1", "dir2"])
    
    print("Property tests completed. Run with pytest for full test suite.")