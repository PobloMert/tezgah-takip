#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip v2.1.4 Hotfix Release Creator
Complete automated release system for GitHub
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import time

# Import our release components
from github_release_manager import GitHubReleaseManager, ReleaseData, ReleaseAsset
from build_system import BuildOrchestrator
from documentation_generator import ReleaseNotesGenerator, ChangelogUpdater


class TezgahTakipReleaseCreator:
    """
    Complete release creation system for TezgahTakip v2.1.4 hotfix
    """
    
    def __init__(self, config_path: str = "release_config.json", dry_run: bool = False):
        self.config_path = config_path
        self.dry_run = dry_run
        self.config = self._load_config()
        
        # Setup logging
        log_level = logging.DEBUG if self.dry_run else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'release_v2.1.4_{int(time.time())}.log'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("TezgahTakipReleaseCreator")
        
        # Initialize components
        self.github_manager = None
        self.build_orchestrator = None
        self.docs_generator = None
        self.changelog_updater = None
        
        self.logger.info(f"TezgahTakip Release Creator initialized (dry_run={dry_run})")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load release configuration"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
    
    def initialize_components(self):
        """Initialize all release components"""
        self.logger.info("Initializing release components...")
        
        try:
            # GitHub manager
            if not self.dry_run:
                self.github_manager = GitHubReleaseManager(
                    repo_owner=self.config['repo_owner'],
                    repo_name=self.config['repo_name']
                )
            
            # Build orchestrator
            self.build_orchestrator = BuildOrchestrator(self.config_path)
            
            # Documentation generator
            self.docs_generator = ReleaseNotesGenerator(self.config_path)
            
            # Changelog updater
            self.changelog_updater = ChangelogUpdater()
            
            self.logger.info("All components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise
    
    def create_complete_release(self, version: str = "2.1.4") -> Dict[str, Any]:
        """
        Create complete GitHub release with all assets and documentation
        """
        self.logger.info(f"🚀 Starting complete release creation for v{version}")
        
        release_results = {
            'version': version,
            'success': False,
            'steps_completed': [],
            'errors': [],
            'assets_created': [],
            'documentation_created': [],
            'github_release_url': None
        }
        
        try:
            # Step 1: Generate documentation
            self.logger.info("📝 Step 1: Generating documentation...")
            docs_result = self._generate_documentation(version)
            release_results['steps_completed'].append('documentation')
            release_results['documentation_created'] = docs_result
            
            # Step 2: Build assets
            self.logger.info("🔨 Step 2: Building release assets...")
            build_result = self._build_assets(version)
            release_results['steps_completed'].append('build')
            release_results['assets_created'] = build_result
            
            # Step 3: Create GitHub release
            if not self.dry_run:
                self.logger.info("🌐 Step 3: Creating GitHub release...")
                github_result = self._create_github_release(version, docs_result, build_result)
                release_results['steps_completed'].append('github_release')
                release_results['github_release_url'] = github_result.get('html_url')
            else:
                self.logger.info("🌐 Step 3: Skipping GitHub release (dry run mode)")
                release_results['steps_completed'].append('github_release_skipped')
            
            # Step 4: Update repository files
            self.logger.info("📋 Step 4: Updating repository files...")
            repo_update_result = self._update_repository_files(version, docs_result)
            release_results['steps_completed'].append('repository_update')
            
            release_results['success'] = True
            self.logger.info("✅ Complete release creation successful!")
            
        except Exception as e:
            self.logger.error(f"❌ Release creation failed: {e}")
            release_results['errors'].append(str(e))
            import traceback
            self.logger.debug(f"Full traceback: {traceback.format_exc()}")
        
        return release_results
    
    def _generate_documentation(self, version: str) -> Dict[str, Any]:
        """Generate all release documentation"""
        self.logger.info("Generating release documentation...")
        
        # Generate release notes
        release_notes = self.docs_generator.generate_release_notes(version)
        
        # Save release notes to files
        docs_files = self.docs_generator.save_release_notes(release_notes)
        
        # Update changelog
        changelog_path = self.changelog_updater.update_changelog(
            version, 
            release_notes.bug_fixes
        )
        docs_files['changelog'] = changelog_path
        
        self.logger.info(f"Documentation generated: {len(docs_files)} files created")
        
        return {
            'release_notes': release_notes,
            'files_created': docs_files,
            'success': True
        }
    
    def _build_assets(self, version: str) -> Dict[str, Any]:
        """Build all release assets"""
        self.logger.info("Building release assets...")
        
        # Find main script
        main_scripts = ['launcher.py', 'run_tezgah_takip.py', 'tezgah_takip_app.py']
        main_script = None
        
        for script in main_scripts:
            if os.path.exists(script):
                main_script = script
                break
        
        if not main_script:
            raise FileNotFoundError(f"No main script found. Checked: {main_scripts}")
        
        self.logger.info(f"Using main script: {main_script}")
        
        # Build all assets
        build_results = self.build_orchestrator.build_all_assets(version, main_script)
        
        # Check build success
        successful_builds = [name for name, result in build_results.items() if result.success]
        failed_builds = [name for name, result in build_results.items() if not result.success]
        
        if failed_builds:
            self.logger.warning(f"Some builds failed: {failed_builds}")
        
        self.logger.info(f"Assets built: {len(successful_builds)} successful, {len(failed_builds)} failed")
        
        return {
            'build_results': build_results,
            'successful_builds': successful_builds,
            'failed_builds': failed_builds,
            'success': len(successful_builds) > 0
        }
    
    def _create_github_release(self, version: str, docs_result: Dict, build_result: Dict) -> Dict[str, Any]:
        """Create GitHub release with assets"""
        self.logger.info("Creating GitHub release...")
        
        # Prepare release data
        release_notes = docs_result['release_notes']
        
        # Create release body (combine Turkish and English)
        release_body = f"""# 🏭 TezgahTakip v{version} - Critical Hotfix Release

## 🚨 Important Update
This is a critical hotfix that resolves major compatibility issues during updates from v2.0.0 to v2.1.3.

## 🔧 Key Fixes
- ✅ Resolved "base_library.zip not found" errors
- ✅ Fixed frozen_importlib_bootstrap startup issues  
- ✅ Added comprehensive backup and recovery system
- ✅ Implemented enhanced update compatibility system
- ✅ 88.9% success rate in comprehensive testing

## 📥 Download Options
- **Windows Executable**: Download `TezgahTakip-v{version}-Windows.exe` for ready-to-run application
- **Source Code**: Download `TezgahTakip-v{version}-Source.zip` for development or custom builds

## 📋 Full Release Notes
See attached release notes files for complete details in Turkish and English.

---

Bu kritik güncelleme v2.0.0'dan v2.1.3'e güncelleme sorunlarını çözmektedir. Tüm kullanıcılar için önerilir.

**Automatic update available through TezgahTakip Launcher.**"""
        
        release_data = ReleaseData(
            version=version,
            tag_name=f"v{version}",
            name=f"TezgahTakip v{version} - Critical Hotfix Release",
            body=release_body,
            draft=False,
            prerelease=False
        )
        
        # Create the release
        create_result = self.github_manager.create_release(release_data)
        
        if not create_result['success']:
            raise Exception(f"Failed to create GitHub release: {create_result['error']}")
        
        release_id = create_result['release_id']
        self.logger.info(f"GitHub release created: {create_result['html_url']}")
        
        # Upload assets
        assets_uploaded = []
        
        # Upload build assets
        for build_name, build_info in build_result['build_results'].items():
            if build_info.success and build_info.output_path:
                asset = ReleaseAsset(
                    name=os.path.basename(build_info.output_path),
                    path=build_info.output_path,
                    content_type="application/octet-stream" if build_name == "executable" else "application/zip",
                    size=build_info.size,
                    checksum=build_info.checksum
                )
                
                upload_result = self.github_manager.upload_asset(release_id, asset)
                if upload_result['success']:
                    assets_uploaded.append(asset.name)
                    self.logger.info(f"Asset uploaded: {asset.name}")
                else:
                    self.logger.error(f"Failed to upload asset {asset.name}: {upload_result['error']}")
        
        # Upload documentation assets
        docs_files = docs_result['files_created']
        for doc_type, doc_path in docs_files.items():
            if os.path.exists(doc_path) and doc_type in ['combined', 'technical', 'installation']:
                asset = ReleaseAsset(
                    name=os.path.basename(doc_path),
                    path=doc_path,
                    content_type="text/markdown",
                    size=os.path.getsize(doc_path),
                    checksum=self._calculate_checksum(doc_path)
                )
                
                upload_result = self.github_manager.upload_asset(release_id, asset)
                if upload_result['success']:
                    assets_uploaded.append(asset.name)
                    self.logger.info(f"Documentation uploaded: {asset.name}")
        
        return {
            'success': True,
            'release_id': release_id,
            'html_url': create_result['html_url'],
            'assets_uploaded': assets_uploaded
        }
    
    def _update_repository_files(self, version: str, docs_result: Dict) -> Dict[str, Any]:
        """Update repository files (README, etc.)"""
        self.logger.info("Updating repository files...")
        
        # Update README with latest release info
        readme_updated = self._update_readme(version)
        
        # Files are already updated locally by previous steps
        # In a real implementation, you might want to commit and push these changes
        
        return {
            'readme_updated': readme_updated,
            'changelog_updated': True,  # Already done in docs generation
            'success': True
        }
    
    def _update_readme(self, version: str) -> bool:
        """Update README with latest release information"""
        readme_path = "README.md"
        
        if not os.path.exists(readme_path):
            self.logger.warning("README.md not found, skipping update")
            return False
        
        try:
            # Read current README
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update version badge or add release info
            # This is a simple implementation - you might want more sophisticated updating
            
            # Add release announcement at the top if not already there
            release_announcement = f"""## 🚨 Latest Release: v{version} - Critical Hotfix

**Important Update Available!** This release fixes critical compatibility issues.

- 🔧 Resolves v2.0.0 to v2.1.3 update problems
- ✅ Enhanced update system with 88.9% success rate  
- 🛡️ Automatic backup and recovery
- 📥 [Download v{version}](https://github.com/{self.config['repo_owner']}/{self.config['repo_name']}/releases/tag/v{version})

---

"""
            
            # Check if announcement already exists
            if f"Latest Release: v{version}" not in content:
                # Add announcement after main title
                lines = content.split('\n')
                title_end = 0
                for i, line in enumerate(lines):
                    if line.startswith('# '):
                        title_end = i + 1
                        break
                
                updated_content = '\n'.join(lines[:title_end]) + '\n\n' + release_announcement + '\n'.join(lines[title_end:])
                
                # Write updated README
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                
                self.logger.info("README.md updated with release announcement")
                return True
            else:
                self.logger.info("README.md already contains release announcement")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update README: {e}")
            return False
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum"""
        import hashlib
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def cleanup(self):
        """Clean up temporary files"""
        if self.build_orchestrator:
            self.build_orchestrator.cleanup()


def main():
    """Main function with CLI interface"""
    parser = argparse.ArgumentParser(description='TezgahTakip v2.1.4 Hotfix Release Creator')
    parser.add_argument('--version', default='2.1.4', help='Release version (default: 2.1.4)')
    parser.add_argument('--config', default='release_config.json', help='Configuration file path')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no GitHub operations)')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    print("🏭 TezgahTakip v2.1.4 Hotfix Release Creator")
    print("=" * 50)
    
    if args.dry_run:
        print("🧪 Running in DRY RUN mode - no GitHub operations will be performed")
    
    try:
        # Initialize release creator
        creator = TezgahTakipReleaseCreator(
            config_path=args.config,
            dry_run=args.dry_run
        )
        
        # Initialize components
        creator.initialize_components()
        
        # Create complete release
        print(f"\n🚀 Creating release v{args.version}...")
        results = creator.create_complete_release(args.version)
        
        # Display results
        print(f"\n📊 Release Results:")
        print(f"Version: {results['version']}")
        print(f"Success: {'✅ YES' if results['success'] else '❌ NO'}")
        print(f"Steps completed: {', '.join(results['steps_completed'])}")
        
        if results['assets_created']:
            print(f"\n📦 Assets created:")
            for asset_type, asset_info in results['assets_created']['build_results'].items():
                status = "✅" if asset_info.success else "❌"
                print(f"  {status} {asset_type}: {asset_info.output_path if asset_info.success else asset_info.error_message}")
        
        if results['documentation_created']:
            print(f"\n📝 Documentation created:")
            for doc_type, doc_path in results['documentation_created']['files_created'].items():
                print(f"  ✅ {doc_type}: {doc_path}")
        
        if results['github_release_url']:
            print(f"\n🌐 GitHub Release: {results['github_release_url']}")
        
        if results['errors']:
            print(f"\n❌ Errors encountered:")
            for error in results['errors']:
                print(f"  - {error}")
        
        # Cleanup
        creator.cleanup()
        
        if results['success']:
            print(f"\n🎉 Release v{args.version} created successfully!")
            if not args.dry_run:
                print("🔗 Users can now download the update from GitHub Releases")
                print("🔄 Automatic update will be available through TezgahTakip Launcher")
        else:
            print(f"\n💥 Release creation failed. Check logs for details.")
            sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()