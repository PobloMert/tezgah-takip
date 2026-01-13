#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build System for TezgahTakip v2.1.4 Hotfix Release
Handles executable building and source code packaging
"""

import os
import sys
import subprocess
import shutil
import zipfile
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
import tempfile


@dataclass
class BuildResult:
    """Build operation result"""
    success: bool
    output_path: Optional[str] = None
    size: int = 0
    checksum: str = ""
    error_message: Optional[str] = None
    build_time: float = 0.0


class ExecutableBuilder:
    """
    Builds Windows executable using PyInstaller
    """
    
    def __init__(self, config_path: str = "release_config.json"):
        self.config = self._load_config(config_path)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("ExecutableBuilder")
        
        # Build directories
        self.build_dir = Path(self.config.get('build_dir', 'dist'))
        self.temp_dir = Path(self.config.get('temp_dir', 'temp_release'))
        
        # Ensure directories exist
        self.build_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        self.logger.info("Executable Builder initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load build configuration"""
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def build_executable(self, main_script: str = "launcher.py", version: str = "2.1.4") -> BuildResult:
        """
        Build Windows executable using PyInstaller
        """
        import time
        start_time = time.time()
        
        self.logger.info(f"Building executable for version {version}")
        
        if not os.path.exists(main_script):
            return BuildResult(
                success=False,
                error_message=f"Main script not found: {main_script}"
            )
        
        # Output executable name
        exe_name = self.config.get('assets', {}).get('executable_name', 'TezgahTakip-v{version}-Windows.exe')
        exe_name = exe_name.format(version=version)
        exe_path = self.build_dir / exe_name
        
        try:
            # PyInstaller command
            cmd = [
                sys.executable, '-m', 'PyInstaller',
                '--onefile',  # Single executable
                '--windowed',  # No console window
                '--clean',  # Clean cache
                f'--distpath={self.build_dir}',
                f'--workpath={self.temp_dir / "build"}',
                f'--specpath={self.temp_dir}',
                f'--name={exe_name.replace(".exe", "")}',
            ]
            
            # Add icon if exists
            icon_files = ['tezgah_icon.ico', 'mtb_logo.ico', 'icon.ico']
            for icon_file in icon_files:
                if os.path.exists(icon_file):
                    cmd.extend(['--icon', icon_file])
                    break
            
            # Add additional files
            additional_files = [
                'config.json',
                'settings.json',
                'tezgah_logo.png',
                'mtb_logo.png'
            ]
            
            for file_path in additional_files:
                if os.path.exists(file_path):
                    cmd.extend(['--add-data', f'{file_path};.'])
            
            # Add main script
            cmd.append(main_script)
            
            self.logger.info(f"Running PyInstaller: {' '.join(cmd)}")
            
            # Run PyInstaller
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode != 0:
                return BuildResult(
                    success=False,
                    error_message=f"PyInstaller failed: {result.stderr}",
                    build_time=time.time() - start_time
                )
            
            # Find the generated executable
            generated_exe = self.build_dir / f"{exe_name.replace('.exe', '')}.exe"
            final_exe = self.build_dir / exe_name
            
            if generated_exe.exists():
                # Rename to final name if needed
                if generated_exe != final_exe:
                    shutil.move(str(generated_exe), str(final_exe))
            elif not final_exe.exists():
                return BuildResult(
                    success=False,
                    error_message=f"Executable not found after build: {final_exe}",
                    build_time=time.time() - start_time
                )
            
            # Calculate size and checksum
            size = final_exe.stat().st_size
            checksum = self._calculate_checksum(str(final_exe))
            
            self.logger.info(f"Executable built successfully: {final_exe}")
            self.logger.info(f"Size: {size:,} bytes, Checksum: {checksum}")
            
            return BuildResult(
                success=True,
                output_path=str(final_exe),
                size=size,
                checksum=checksum,
                build_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"Build failed with exception: {e}")
            return BuildResult(
                success=False,
                error_message=str(e),
                build_time=time.time() - start_time
            )
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def cleanup_build_artifacts(self):
        """Clean up temporary build files"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.temp_dir.mkdir(exist_ok=True)
            self.logger.info("Build artifacts cleaned up")
        except Exception as e:
            self.logger.warning(f"Failed to cleanup build artifacts: {e}")


class SourcePackager:
    """
    Packages source code into ZIP archive
    """
    
    def __init__(self, config_path: str = "release_config.json"):
        self.config = self._load_config(config_path)
        
        # Setup logging
        self.logger = logging.getLogger("SourcePackager")
        
        # Build directories
        self.build_dir = Path(self.config.get('build_dir', 'dist'))
        self.build_dir.mkdir(exist_ok=True)
        
        # Files to exclude from source package
        self.exclude_patterns = [
            '__pycache__',
            '*.pyc',
            '*.pyo',
            '.git',
            '.gitignore',
            '.hypothesis',
            '.pytest_cache',
            'dist',
            'build',
            'temp_release',
            '*.log',
            'logs',
            'backups',
            'exports',
            'reports',
            '*.db',
            '*.exe',
            '*.zip',
            '.kiro/specs',  # Exclude specs from source
            'version_backup_*',
            'TezgahTakip-v*'
        ]
        
        self.logger.info("Source Packager initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load packaging configuration"""
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def package_source_code(self, version: str = "2.1.4") -> BuildResult:
        """
        Package source code into ZIP archive
        """
        import time
        start_time = time.time()
        
        self.logger.info(f"Packaging source code for version {version}")
        
        # Output ZIP name
        zip_name = self.config.get('assets', {}).get('source_name', 'TezgahTakip-v{version}-Source.zip')
        zip_name = zip_name.format(version=version)
        zip_path = self.build_dir / zip_name
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add all Python files and important assets
                for root, dirs, files in os.walk('.'):
                    # Skip excluded directories
                    dirs[:] = [d for d in dirs if not self._should_exclude(d)]
                    
                    for file in files:
                        if self._should_exclude(file):
                            continue
                        
                        file_path = os.path.join(root, file)
                        
                        # Skip if path contains excluded patterns
                        if any(pattern in file_path for pattern in self.exclude_patterns):
                            continue
                        
                        # Add to ZIP
                        arcname = file_path.replace('\\', '/')
                        if arcname.startswith('./'):
                            arcname = arcname[2:]
                        
                        zipf.write(file_path, arcname)
                        self.logger.debug(f"Added to ZIP: {arcname}")
                
                # Add special files
                special_files = [
                    'README.md',
                    'requirements.txt',
                    'CHANGELOG_v2.1.4.md',  # Will be created later
                    'RELEASE_NOTES_v2.1.4.md'  # Will be created later
                ]
                
                for special_file in special_files:
                    if os.path.exists(special_file):
                        zipf.write(special_file, special_file)
                        self.logger.debug(f"Added special file: {special_file}")
            
            # Calculate size and checksum
            size = zip_path.stat().st_size
            checksum = self._calculate_checksum(str(zip_path))
            
            self.logger.info(f"Source package created: {zip_path}")
            self.logger.info(f"Size: {size:,} bytes, Checksum: {checksum}")
            
            return BuildResult(
                success=True,
                output_path=str(zip_path),
                size=size,
                checksum=checksum,
                build_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"Source packaging failed: {e}")
            return BuildResult(
                success=False,
                error_message=str(e),
                build_time=time.time() - start_time
            )
    
    def _should_exclude(self, name: str) -> bool:
        """Check if file/directory should be excluded"""
        for pattern in self.exclude_patterns:
            if pattern.startswith('*'):
                if name.endswith(pattern[1:]):
                    return True
            elif pattern.endswith('*'):
                if name.startswith(pattern[:-1]):
                    return True
            elif pattern in name:
                return True
        return False
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


class BuildOrchestrator:
    """
    Orchestrates the complete build process
    """
    
    def __init__(self, config_path: str = "release_config.json"):
        self.config_path = config_path
        self.executable_builder = ExecutableBuilder(config_path)
        self.source_packager = SourcePackager(config_path)
        
        # Setup logging
        self.logger = logging.getLogger("BuildOrchestrator")
        self.logger.info("Build Orchestrator initialized")
    
    def build_all_assets(self, version: str = "2.1.4", main_script: str = "launcher.py") -> Dict[str, BuildResult]:
        """
        Build all release assets
        """
        self.logger.info(f"Building all assets for version {version}")
        
        results = {}
        
        # Build executable
        self.logger.info("Building executable...")
        exe_result = self.executable_builder.build_executable(main_script, version)
        results['executable'] = exe_result
        
        if exe_result.success:
            self.logger.info(f"✅ Executable built: {exe_result.output_path}")
        else:
            self.logger.error(f"❌ Executable build failed: {exe_result.error_message}")
        
        # Package source code
        self.logger.info("Packaging source code...")
        source_result = self.source_packager.package_source_code(version)
        results['source'] = source_result
        
        if source_result.success:
            self.logger.info(f"✅ Source packaged: {source_result.output_path}")
        else:
            self.logger.error(f"❌ Source packaging failed: {source_result.error_message}")
        
        # Summary
        successful_builds = sum(1 for result in results.values() if result.success)
        total_builds = len(results)
        
        self.logger.info(f"Build summary: {successful_builds}/{total_builds} successful")
        
        return results
    
    def cleanup(self):
        """Clean up build artifacts"""
        self.executable_builder.cleanup_build_artifacts()


def main():
    """Test the build system"""
    print("🔨 TezgahTakip Build System Test")
    print("=" * 40)
    
    try:
        # Initialize build orchestrator
        builder = BuildOrchestrator()
        
        # Check if main script exists
        main_scripts = ['launcher.py', 'run_tezgah_takip.py', 'tezgah_takip_app.py']
        main_script = None
        
        for script in main_scripts:
            if os.path.exists(script):
                main_script = script
                break
        
        if not main_script:
            print("❌ No main script found. Please ensure one of these exists:")
            for script in main_scripts:
                print(f"  - {script}")
            return
        
        print(f"📋 Using main script: {main_script}")
        
        # Build all assets
        results = builder.build_all_assets(version="2.1.4", main_script=main_script)
        
        # Display results
        print("\n📊 Build Results:")
        for asset_type, result in results.items():
            status = "✅ SUCCESS" if result.success else "❌ FAILED"
            print(f"  {asset_type.title()}: {status}")
            
            if result.success:
                print(f"    Path: {result.output_path}")
                print(f"    Size: {result.size:,} bytes")
                print(f"    Checksum: {result.checksum[:16]}...")
                print(f"    Build time: {result.build_time:.2f}s")
            else:
                print(f"    Error: {result.error_message}")
        
        # Cleanup
        builder.cleanup()
        
        print("\n✅ Build system test completed!")
        
    except Exception as e:
        print(f"❌ Build system test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()