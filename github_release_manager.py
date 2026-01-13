#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Release Manager for TezgahTakip v2.1.4 Hotfix
Handles automated GitHub release creation and management
"""

import os
import sys
import json
import logging
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import zipfile
import shutil
from datetime import datetime


@dataclass
class ReleaseAsset:
    """Release asset information"""
    name: str
    path: str
    content_type: str
    size: int
    checksum: str


@dataclass
class BugFix:
    """Bug fix information"""
    id: str
    title: str
    description: str
    severity: str
    affected_versions: List[str]
    solution_summary: str
    technical_details: str
    test_results: str


@dataclass
class ReleaseData:
    """GitHub release data"""
    version: str
    tag_name: str
    name: str
    body: str
    draft: bool = False
    prerelease: bool = False
    assets: List[ReleaseAsset] = None
    
    def __post_init__(self):
        if self.assets is None:
            self.assets = []


class GitHubReleaseManager:
    """
    Main GitHub Release Manager for TezgahTakip hotfix releases
    """
    
    def __init__(self, repo_owner: str, repo_name: str, github_token: str = None):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        
        if not self.github_token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN environment variable.")
        
        self.api_base = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("GitHubReleaseManager")
        
        self.logger.info(f"Initialized GitHub Release Manager for {repo_owner}/{repo_name}")
    
    def create_release(self, release_data: ReleaseData) -> Dict[str, Any]:
        """
        Create a GitHub release
        """
        self.logger.info(f"Creating GitHub release {release_data.version}")
        
        url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/releases"
        
        payload = {
            "tag_name": release_data.tag_name,
            "target_commitish": "main",  # or master
            "name": release_data.name,
            "body": release_data.body,
            "draft": release_data.draft,
            "prerelease": release_data.prerelease
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            release_info = response.json()
            self.logger.info(f"Successfully created release: {release_info['html_url']}")
            
            return {
                'success': True,
                'release_id': release_info['id'],
                'upload_url': release_info['upload_url'],
                'html_url': release_info['html_url'],
                'tag_name': release_info['tag_name']
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to create release: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def upload_asset(self, release_id: int, asset: ReleaseAsset) -> Dict[str, Any]:
        """
        Upload an asset to a GitHub release
        """
        self.logger.info(f"Uploading asset: {asset.name}")
        
        if not os.path.exists(asset.path):
            return {
                'success': False,
                'error': f"Asset file not found: {asset.path}"
            }
        
        # Get upload URL
        url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/releases/{release_id}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            return {
                'success': False,
                'error': f"Failed to get release info: {response.status_code}"
            }
        
        upload_url_template = response.json()['upload_url']
        upload_url = upload_url_template.replace('{?name,label}', f'?name={asset.name}')
        
        # Upload the asset
        upload_headers = {
            "Authorization": f"token {self.github_token}",
            "Content-Type": asset.content_type
        }
        
        try:
            with open(asset.path, 'rb') as f:
                upload_response = requests.post(upload_url, headers=upload_headers, data=f)
                upload_response.raise_for_status()
            
            asset_info = upload_response.json()
            self.logger.info(f"Successfully uploaded asset: {asset_info['browser_download_url']}")
            
            return {
                'success': True,
                'download_url': asset_info['browser_download_url'],
                'asset_id': asset_info['id']
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to upload asset {asset.name}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_release_assets(self, assets: List[ReleaseAsset]) -> Dict[str, Any]:
        """
        Validate release assets before upload
        """
        self.logger.info("Validating release assets")
        
        validation_results = {
            'valid': True,
            'missing_files': [],
            'checksum_mismatches': [],
            'size_mismatches': []
        }
        
        for asset in assets:
            # Check if file exists
            if not os.path.exists(asset.path):
                validation_results['missing_files'].append(asset.path)
                validation_results['valid'] = False
                continue
            
            # Check file size
            actual_size = os.path.getsize(asset.path)
            if actual_size != asset.size:
                validation_results['size_mismatches'].append({
                    'file': asset.path,
                    'expected': asset.size,
                    'actual': actual_size
                })
                validation_results['valid'] = False
            
            # Check checksum
            actual_checksum = self._calculate_checksum(asset.path)
            if actual_checksum != asset.checksum:
                validation_results['checksum_mismatches'].append({
                    'file': asset.path,
                    'expected': asset.checksum,
                    'actual': actual_checksum
                })
                validation_results['valid'] = False
        
        if validation_results['valid']:
            self.logger.info("All assets validated successfully")
        else:
            self.logger.error(f"Asset validation failed: {validation_results}")
        
        return validation_results
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def get_latest_release(self) -> Dict[str, Any]:
        """Get the latest release information"""
        url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get latest release: {e}")
            return None
    
    def list_releases(self, per_page: int = 10) -> List[Dict[str, Any]]:
        """List repository releases"""
        url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/releases"
        params = {'per_page': per_page}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to list releases: {e}")
            return []


class ReleaseConfiguration:
    """
    Configuration management for releases
    """
    
    def __init__(self, config_path: str = "release_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Default configuration
            default_config = {
                "repo_owner": "your-username",
                "repo_name": "TezgahTakip",
                "build_dir": "dist",
                "temp_dir": "temp_release",
                "assets": {
                    "executable_name": "TezgahTakip-v{version}-Windows.exe",
                    "source_name": "TezgahTakip-v{version}-Source.zip"
                },
                "release_template": {
                    "name_template": "TezgahTakip v{version} - Hotfix Release",
                    "tag_template": "v{version}"
                }
            }
            
            # Save default config
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            
            return default_config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self._save_config()
    
    def _save_config(self) -> None:
        """Save configuration to file"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)


def main():
    """Test the GitHub Release Manager"""
    print("🚀 GitHub Release Manager Test")
    print("=" * 40)
    
    try:
        # Load configuration
        config = ReleaseConfiguration()
        
        # Initialize release manager
        manager = GitHubReleaseManager(
            repo_owner=config.get('repo_owner'),
            repo_name=config.get('repo_name')
        )
        
        # Test: Get latest release
        print("📋 Getting latest release...")
        latest = manager.get_latest_release()
        if latest:
            print(f"Latest release: {latest['tag_name']} - {latest['name']}")
        else:
            print("No releases found or error occurred")
        
        # Test: List releases
        print("\n📋 Listing recent releases...")
        releases = manager.list_releases(5)
        for release in releases:
            print(f"  - {release['tag_name']}: {release['name']}")
        
        print("\n✅ GitHub Release Manager is working correctly!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()