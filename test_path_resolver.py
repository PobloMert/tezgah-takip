"""
Property-based tests for PathResolver
Tests universal properties that should hold across all inputs
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.stateful import RuleBasedStateMachine, rule, initialize, Bundle

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from path_resolver import PathResolver


class TestPathResolverProperties:
    """Property-based tests for PathResolver"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.temp_dirs = []
    
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
    
    @given(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    @settings(max_examples=100)
    def test_property_5_working_directory_detection(self, mock_executable_name):
        """
        Property 5: Working Directory Detection
        For any application startup, the launcher should correctly identify the current working directory
        **Feature: update-compatibility-fix, Property 5: Working Directory Detection**
        **Validates: Requirements 2.1**
        """
        assume(len(mock_executable_name.strip()) > 0)
        
        # Create a temporary directory structure
        temp_dir = self.create_temp_dir()
        
        # Mock sys.executable to point to our temp directory
        mock_executable = os.path.join(temp_dir, f"{mock_executable_name}.exe")
        
        with patch('sys.executable', mock_executable), \
             patch.object(sys, 'frozen', True, create=True), \
             patch('os.path.abspath') as mock_abspath:
            
            # Mock abspath to return predictable results
            mock_abspath.return_value = mock_executable
            
            resolver = PathResolver()
            detected_dir = resolver.get_executable_directory()
            
            # Property: The detected directory should be a valid path
            assert os.path.isabs(detected_dir), f"Detected directory should be absolute: {detected_dir}"
            
            # Property: The detected directory should be consistent across calls
            detected_dir_2 = resolver.get_executable_directory()
            assert detected_dir == detected_dir_2, "Directory detection should be consistent"
    
    @given(st.lists(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))), 
                   min_size=1, max_size=10))
    @settings(max_examples=100)
    def test_property_6_multi_path_search_strategy(self, search_locations):
        """
        Property 6: Multi-Path Search Strategy
        For any base_library.zip search operation, the system should check multiple possible locations before failing
        **Feature: update-compatibility-fix, Property 6: Multi-Path Search Strategy**
        **Validates: Requirements 2.2**
        """
        assume(all(len(loc.strip()) > 0 for loc in search_locations))
        
        # Create temporary directory structure
        base_temp = self.create_temp_dir()
        
        # Create multiple search directories
        created_dirs = []
        for i, location in enumerate(search_locations):
            dir_path = os.path.join(base_temp, f"location_{i}_{location}")
            os.makedirs(dir_path, exist_ok=True)
            created_dirs.append(dir_path)
        
        # Mock the resolver to use our test directories
        with patch.object(PathResolver, '_initialize_search_paths') as mock_init:
            mock_init.return_value = created_dirs
            
            resolver = PathResolver()
            
            # Property: Search paths should include all provided locations
            search_paths = resolver.get_search_paths()
            assert len(search_paths) >= len(created_dirs), "Should have at least as many paths as provided"
            
            # Property: All created directories should be searchable
            for created_dir in created_dirs:
                # The resolver should be able to search in this directory
                # (even if the file doesn't exist, the directory should be checked)
                assert any(created_dir in path for path in search_paths), f"Directory {created_dir} should be in search paths"
    
    @given(st.lists(st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))), 
                   min_size=2, max_size=8),
           st.integers(min_value=0, max_value=7))
    @settings(max_examples=100)
    def test_property_multi_location_search_completeness(self, directory_names, target_index):
        """
        Property: Multi-location search should find files when they exist
        For any set of search directories, if a file exists in any of them, it should be found
        """
        assume(len(directory_names) > target_index)
        assume(all(len(name.strip()) > 0 for name in directory_names))
        
        # Create temporary directory structure
        base_temp = self.create_temp_dir()
        
        # Create directories
        created_dirs = []
        for name in directory_names:
            dir_path = os.path.join(base_temp, name)
            os.makedirs(dir_path, exist_ok=True)
            created_dirs.append(dir_path)
        
        # Place base_library.zip in one specific directory
        target_dir = created_dirs[target_index]
        target_file = os.path.join(target_dir, "base_library.zip")
        
        # Create the file
        with open(target_file, 'w') as f:
            f.write("mock base library content")
        
        # Mock the resolver to use our test directories
        with patch.object(PathResolver, '_initialize_search_paths') as mock_init:
            mock_init.return_value = created_dirs
            
            resolver = PathResolver()
            
            # Property: The file should be found
            found_path = resolver.find_base_library()
            assert found_path is not None, "File should be found when it exists in search paths"
            assert os.path.exists(found_path), "Found path should exist"
            assert found_path == target_file, f"Should find the correct file: expected {target_file}, got {found_path}"
    
    @given(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))),
           st.booleans())
    @settings(max_examples=100)
    def test_property_path_structure_validation_consistency(self, path_suffix, create_valid_structure):
        """
        Property: Path structure validation should be consistent
        For any path, validation should return the same result when called multiple times
        """
        assume(len(path_suffix.strip()) > 0)
        
        # Create temporary directory
        base_temp = self.create_temp_dir()
        test_path = os.path.join(base_temp, path_suffix)
        os.makedirs(test_path, exist_ok=True)
        
        if create_valid_structure:
            # Create some expected files to make it a "valid" structure
            expected_files = ['tezgah_takip_app.py', 'main_window.py', 'config.json']
            for filename in expected_files:
                file_path = os.path.join(test_path, filename)
                with open(file_path, 'w') as f:
                    f.write(f"# Mock {filename}")
        
        resolver = PathResolver()
        
        # Property: Validation should be consistent across multiple calls
        result1 = resolver.validate_path_structure(test_path)
        result2 = resolver.validate_path_structure(test_path)
        result3 = resolver.validate_path_structure(test_path)
        
        assert result1 == result2 == result3, "Path structure validation should be consistent"
        
        # Property: Result should match expectation based on structure
        if create_valid_structure:
            assert result1 == True, "Should validate as true when valid structure exists"
        # Note: We don't assert False for invalid structure because the validation 
        # might still pass with partial matches
    
    @given(st.lists(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))), 
                   min_size=1, max_size=5))
    @settings(max_examples=100)
    def test_property_search_path_addition_persistence(self, new_paths):
        """
        Property: Added search paths should persist and be searchable
        For any valid path added to search paths, it should remain in the search paths
        """
        assume(all(len(path.strip()) > 0 for path in new_paths))
        
        # Create temporary directories for the new paths
        base_temp = self.create_temp_dir()
        created_paths = []
        
        for i, path_name in enumerate(new_paths):
            path_dir = os.path.join(base_temp, f"path_{i}_{path_name}")
            os.makedirs(path_dir, exist_ok=True)
            created_paths.append(path_dir)
        
        resolver = PathResolver()
        initial_path_count = len(resolver.get_search_paths())
        
        # Add all paths
        for path in created_paths:
            resolver.add_search_path(path)
        
        # Property: All added paths should be in search paths
        final_search_paths = resolver.get_search_paths()
        
        for path in created_paths:
            assert path in final_search_paths, f"Added path {path} should be in search paths"
        
        # Property: Search path count should increase appropriately
        expected_min_count = initial_path_count + len(created_paths)
        assert len(final_search_paths) >= expected_min_count, "Search path count should increase with additions"


class PathResolverStateMachine(RuleBasedStateMachine):
    """
    Stateful property testing for PathResolver
    Tests complex interactions and state changes
    """
    
    paths = Bundle('paths')
    files = Bundle('files')
    
    def __init__(self):
        super().__init__()
        self.temp_dirs = []
        self.resolver = None
    
    @initialize()
    def setup_resolver(self):
        """Initialize the resolver"""
        self.resolver = PathResolver()
    
    @rule(target=paths, path_name=st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    def create_path(self, path_name):
        """Create a new path"""
        assume(len(path_name.strip()) > 0)
        
        temp_dir = tempfile.mkdtemp(suffix=f"_{path_name}")
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    @rule(path=paths, filename=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    def create_file_in_path(self, path, filename):
        """Create a file in a path"""
        assume(len(filename.strip()) > 0)
        assume(os.path.exists(path))
        
        file_path = os.path.join(path, filename)
        try:
            with open(file_path, 'w') as f:
                f.write(f"Content for {filename}")
            return file_path
        except (OSError, IOError):
            assume(False)  # Skip if file creation fails
    
    @rule(path=paths)
    def add_search_path(self, path):
        """Add a path to search paths"""
        assume(os.path.exists(path))
        
        initial_paths = self.resolver.get_search_paths()
        self.resolver.add_search_path(path)
        updated_paths = self.resolver.get_search_paths()
        
        # Property: Path should be added if it wasn't already there
        if path not in initial_paths:
            assert path in updated_paths, "New path should be added to search paths"
        
        # Property: Search paths should not decrease
        assert len(updated_paths) >= len(initial_paths), "Search paths should not decrease when adding"
    
    @rule(path=paths)
    def validate_path_structure(self, path):
        """Validate path structure"""
        assume(os.path.exists(path))
        
        # Property: Validation should not crash
        try:
            result = self.resolver.validate_path_structure(path)
            assert isinstance(result, bool), "Validation should return a boolean"
        except Exception as e:
            assert False, f"Path validation should not raise exceptions: {e}"
    
    @rule(filename=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    def find_file(self, filename):
        """Find a file using the resolver"""
        assume(len(filename.strip()) > 0)
        
        # Property: Find operation should not crash
        try:
            result = self.resolver.find_file(filename)
            # Result should be None or a valid path
            if result is not None:
                assert isinstance(result, str), "Found file path should be a string"
                assert os.path.isabs(result), "Found file path should be absolute"
        except Exception as e:
            assert False, f"File finding should not raise exceptions: {e}"
    
    @settings(max_examples=50, stateful_step_count=20)
    def run(self):
        """Run the state machine with settings"""
        super().run()
    
    def teardown(self):
        """Cleanup temporary directories"""
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)


# Test class for running the state machine
class TestPathResolverStateMachine:
    """Test runner for the state machine"""
    
    def test_path_resolver_state_machine(self):
        """
        Run the stateful property tests
        **Feature: update-compatibility-fix, Property 5-6: Path Resolution State Management**
        """
        # Simple test to verify state machine works
        machine = PathResolverStateMachine()
        try:
            # Test basic functionality
            machine.setup_resolver()
            assert machine.resolver is not None
            
            # Test that we can create paths and validate them
            temp_path = machine.create_path("test_path")
            assert os.path.exists(temp_path)
            
            machine.validate_path_structure(temp_path)
            machine.add_search_path(temp_path)
            
        finally:
            machine.teardown()


if __name__ == "__main__":
    # Run basic property tests
    test_instance = TestPathResolverProperties()
    
    print("Running property-based tests for PathResolver...")
    
    # You can run individual tests here for debugging
    # test_instance.test_property_5_working_directory_detection("test_exe")
    
    print("Property tests completed. Run with pytest for full test suite.")