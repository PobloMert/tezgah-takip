"""
Manual Update Manager for TezgahTakip Update System
Handles manual update workflows when automatic updates fail
"""

import os
import sys
import logging
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ManualStep:
    """A single manual update step"""
    step_number: int
    title: str
    description: str
    instructions: List[str]
    verification: Optional[str] = None
    is_critical: bool = True


@dataclass
class ManualUpdatePlan:
    """Complete manual update plan"""
    plan_id: str
    target_version: str
    steps: List[ManualStep]
    estimated_time_minutes: int
    difficulty_level: str  # 'easy', 'medium', 'hard'
    prerequisites: List[str]
    warnings: List[str]


class ManualUpdateManager:
    """
    Manages manual update workflows and step-by-step instructions
    """
    
    def __init__(self, path_resolver=None, file_validator=None):
        self.logger = logging.getLogger("ManualUpdateManager")
        self.path_resolver = path_resolver
        self.file_validator = file_validator
        
        self.logger.debug("ManualUpdateManager initialized")
    
    def create_manual_update_plan(self, target_version: str, error_context: Dict = None) -> ManualUpdatePlan:
        """
        Create a manual update plan based on the target version and error context
        """
        self.logger.info(f"Creating manual update plan for version {target_version}")
        
        if error_context is None:
            error_context = {}
        
        # Determine plan based on error type
        error_type = error_context.get('error_type', 'general')
        
        if 'base_library' in str(error_context.get('error_message', '')).lower():
            return self._create_base_library_fix_plan(target_version)
        elif 'permission' in str(error_context.get('error_message', '')).lower():
            return self._create_permission_fix_plan(target_version)
        else:
            return self._create_general_update_plan(target_version)
    
    def _create_base_library_fix_plan(self, target_version: str) -> ManualUpdatePlan:
        """Create plan for base_library.zip issues"""
        
        steps = [
            ManualStep(
                step_number=1,
                title="Backup Current Installation",
                description="Create a backup of your current TezgahTakip installation",
                instructions=[
                    "Close TezgahTakip application completely",
                    "Navigate to your TezgahTakip installation folder",
                    "Copy the entire folder to a safe location (e.g., Desktop)",
                    "Rename the backup folder to 'TezgahTakip_Backup_[date]'"
                ],
                verification="Verify backup folder contains all original files"
            ),
            
            ManualStep(
                step_number=2,
                title="Download Latest Version",
                description="Download the latest TezgahTakip version",
                instructions=[
                    "Go to the official TezgahTakip releases page",
                    f"Download TezgahTakip-{target_version}-Release.zip",
                    "Save the file to your Downloads folder",
                    "Do NOT extract yet"
                ],
                verification="Verify downloaded file size is reasonable (>10MB)"
            ),
            
            ManualStep(
                step_number=3,
                title="Extract New Version",
                description="Extract the new version to a temporary location",
                instructions=[
                    "Create a new folder on Desktop called 'TezgahTakip_New'",
                    "Right-click the downloaded ZIP file",
                    "Select 'Extract All' and choose the new folder",
                    "Wait for extraction to complete"
                ],
                verification="Verify extracted folder contains base_library.zip file"
            ),
            
            ManualStep(
                step_number=4,
                title="Locate Missing base_library.zip",
                description="Find and copy the base_library.zip file",
                instructions=[
                    "Navigate to the extracted TezgahTakip_New folder",
                    "Look for base_library.zip file in the main folder",
                    "If not found, check 'lib' or 'libs' subfolder",
                    "Copy base_library.zip file"
                ],
                verification="Confirm base_library.zip file is found and copied"
            ),
            
            ManualStep(
                step_number=5,
                title="Replace Missing File",
                description="Replace the missing base_library.zip in your installation",
                instructions=[
                    "Navigate to your original TezgahTakip installation folder",
                    "Paste the base_library.zip file into the main folder",
                    "If asked to replace, click 'Yes'",
                    "Ensure file permissions allow reading"
                ],
                verification="Verify base_library.zip exists in installation folder"
            ),
            
            ManualStep(
                step_number=6,
                title="Test Application",
                description="Test that TezgahTakip now works correctly",
                instructions=[
                    "Double-click TezgahTakip.exe or launcher.py",
                    "Wait for application to start",
                    "Check that no error messages appear",
                    "Verify your data is still accessible"
                ],
                verification="Application starts without base_library.zip errors"
            )
        ]
        
        return ManualUpdatePlan(
            plan_id="base_library_fix",
            target_version=target_version,
            steps=steps,
            estimated_time_minutes=15,
            difficulty_level="medium",
            prerequisites=[
                "Administrative access to computer",
                "Internet connection for download",
                "Basic file management skills"
            ],
            warnings=[
                "Always backup your data before manual updates",
                "Do not delete original files until new version is confirmed working",
                "If problems persist, restore from backup"
            ]
        )
    
    def _create_permission_fix_plan(self, target_version: str) -> ManualUpdatePlan:
        """Create plan for permission-related issues"""
        
        steps = [
            ManualStep(
                step_number=1,
                title="Run as Administrator",
                description="Try running TezgahTakip with administrator privileges",
                instructions=[
                    "Right-click on TezgahTakip.exe",
                    "Select 'Run as administrator'",
                    "Click 'Yes' when prompted by Windows",
                    "Test if the application works"
                ],
                verification="Check if application starts without permission errors"
            ),
            
            ManualStep(
                step_number=2,
                title="Check Folder Permissions",
                description="Verify and fix folder permissions",
                instructions=[
                    "Right-click on TezgahTakip installation folder",
                    "Select 'Properties' > 'Security' tab",
                    "Click 'Edit' button",
                    "Select your username and check 'Full control'",
                    "Click 'OK' to apply changes"
                ],
                verification="Verify you have full control permissions"
            ),
            
            ManualStep(
                step_number=3,
                title="Move to User Directory",
                description="Move installation to user directory if needed",
                instructions=[
                    "Create folder: C:\\Users\\[YourName]\\TezgahTakip",
                    "Copy all files from current installation to new folder",
                    "Update any shortcuts to point to new location",
                    "Test application from new location"
                ],
                verification="Application runs from user directory without errors"
            ),
            
            ManualStep(
                step_number=4,
                title="Add Antivirus Exclusion",
                description="Add TezgahTakip to antivirus exclusions",
                instructions=[
                    "Open Windows Defender Security Center",
                    "Go to Virus & threat protection",
                    "Click 'Manage settings' under Virus & threat protection settings",
                    "Click 'Add or remove exclusions'",
                    "Add your TezgahTakip folder as exclusion"
                ],
                verification="TezgahTakip folder is listed in exclusions"
            )
        ]
        
        return ManualUpdatePlan(
            plan_id="permission_fix",
            target_version=target_version,
            steps=steps,
            estimated_time_minutes=10,
            difficulty_level="easy",
            prerequisites=[
                "Administrative access to computer",
                "Basic Windows knowledge"
            ],
            warnings=[
                "Be careful when changing security settings",
                "Only add trusted applications to antivirus exclusions"
            ]
        )
    
    def _create_general_update_plan(self, target_version: str) -> ManualUpdatePlan:
        """Create general manual update plan"""
        
        steps = [
            ManualStep(
                step_number=1,
                title="Prepare for Update",
                description="Prepare your system for manual update",
                instructions=[
                    "Close TezgahTakip application",
                    "Backup your current installation folder",
                    "Backup your data files (databases, configs)",
                    "Ensure you have administrator privileges"
                ],
                verification="All backups created and application closed"
            ),
            
            ManualStep(
                step_number=2,
                title="Download New Version",
                description="Download the latest TezgahTakip version",
                instructions=[
                    "Visit the official TezgahTakip releases page",
                    f"Download TezgahTakip-{target_version}-Release.zip",
                    "Verify download completed successfully",
                    "Scan downloaded file with antivirus"
                ],
                verification="Downloaded file is complete and virus-free"
            ),
            
            ManualStep(
                step_number=3,
                title="Install New Version",
                description="Install the new version over the old one",
                instructions=[
                    "Extract downloaded ZIP to temporary folder",
                    "Copy new files to your TezgahTakip installation folder",
                    "Replace old files when prompted",
                    "Preserve your data files (don't overwrite .db files)"
                ],
                verification="New version files are in place, data files preserved"
            ),
            
            ManualStep(
                step_number=4,
                title="Verify Installation",
                description="Test the new installation",
                instructions=[
                    "Start TezgahTakip application",
                    "Check version number in About dialog",
                    "Verify your data is accessible",
                    "Test main application functions"
                ],
                verification="Application works correctly with new version"
            ),
            
            ManualStep(
                step_number=5,
                title="Clean Up",
                description="Clean up temporary files",
                instructions=[
                    "Delete temporary extraction folder",
                    "Delete downloaded ZIP file (optional)",
                    "Remove old backup after confirming new version works",
                    "Update any shortcuts if needed"
                ],
                verification="System is clean and organized"
            )
        ]
        
        return ManualUpdatePlan(
            plan_id="general_update",
            target_version=target_version,
            steps=steps,
            estimated_time_minutes=20,
            difficulty_level="medium",
            prerequisites=[
                "Administrative access to computer",
                "Internet connection",
                "Basic file management skills",
                "Antivirus software"
            ],
            warnings=[
                "Always backup before updating",
                "Do not skip verification steps",
                "Keep backups until new version is confirmed stable"
            ]
        )
    
    def validate_manual_update_completion(self, plan: ManualUpdatePlan) -> Dict[str, bool]:
        """
        Validate that manual update steps were completed successfully
        """
        self.logger.info(f"Validating manual update completion for plan {plan.plan_id}")
        
        validation_results = {}
        
        try:
            # Check if target version is now running
            if plan.plan_id == "base_library_fix":
                validation_results["base_library_exists"] = self._check_base_library_exists()
                validation_results["application_starts"] = self._check_application_starts()
            
            elif plan.plan_id == "permission_fix":
                validation_results["folder_permissions"] = self._check_folder_permissions()
                validation_results["application_starts"] = self._check_application_starts()
            
            else:  # general_update
                validation_results["version_updated"] = self._check_version_updated(plan.target_version)
                validation_results["application_starts"] = self._check_application_starts()
                validation_results["data_preserved"] = self._check_data_preserved()
            
            # Overall success
            validation_results["overall_success"] = all(validation_results.values())
            
        except Exception as e:
            self.logger.error(f"Error during validation: {e}")
            validation_results["validation_error"] = str(e)
            validation_results["overall_success"] = False
        
        return validation_results
    
    def _check_base_library_exists(self) -> bool:
        """Check if base_library.zip exists"""
        try:
            if self.path_resolver:
                base_lib_path = self.path_resolver.find_base_library()
                return base_lib_path is not None
            else:
                # Check in current directory
                return os.path.exists("base_library.zip")
        except Exception:
            return False
    
    def _check_application_starts(self) -> bool:
        """Check if application can start (basic check)"""
        try:
            # This is a simplified check - in reality, you'd try to import main modules
            if self.path_resolver:
                exe_dir = self.path_resolver.get_executable_directory()
                main_files = ['tezgah_takip_app.py', 'main_window.py', 'launcher.py']
                return any(os.path.exists(os.path.join(exe_dir, f)) for f in main_files)
            return True
        except Exception:
            return False
    
    def _check_folder_permissions(self) -> bool:
        """Check if folder has proper permissions"""
        try:
            if self.path_resolver:
                exe_dir = self.path_resolver.get_executable_directory()
                return os.access(exe_dir, os.R_OK | os.W_OK)
            return True
        except Exception:
            return False
    
    def _check_version_updated(self, target_version: str) -> bool:
        """Check if version was updated (simplified)"""
        try:
            # In a real implementation, this would check the actual application version
            # For now, we'll assume success if basic files exist
            return self._check_application_starts()
        except Exception:
            return False
    
    def _check_data_preserved(self) -> bool:
        """Check if user data was preserved"""
        try:
            if self.path_resolver:
                exe_dir = self.path_resolver.get_executable_directory()
                # Check for common data files
                data_files = ['config.json', 'tezgah_takip_v2.db', 'settings.json']
                return any(os.path.exists(os.path.join(exe_dir, f)) for f in data_files)
            return True
        except Exception:
            return False
    
    def get_user_friendly_instructions(self, plan: ManualUpdatePlan) -> List[str]:
        """
        Convert manual update plan to user-friendly instructions
        """
        instructions = []
        
        instructions.append(f"Manual Update Instructions for TezgahTakip {plan.target_version}")
        instructions.append("=" * 60)
        instructions.append("")
        
        instructions.append(f"Estimated time: {plan.estimated_time_minutes} minutes")
        instructions.append(f"Difficulty: {plan.difficulty_level.title()}")
        instructions.append("")
        
        if plan.prerequisites:
            instructions.append("Prerequisites:")
            for prereq in plan.prerequisites:
                instructions.append(f"  • {prereq}")
            instructions.append("")
        
        if plan.warnings:
            instructions.append("⚠️  Important Warnings:")
            for warning in plan.warnings:
                instructions.append(f"  • {warning}")
            instructions.append("")
        
        instructions.append("Steps:")
        instructions.append("-" * 30)
        
        for step in plan.steps:
            instructions.append(f"\nStep {step.step_number}: {step.title}")
            instructions.append(f"Description: {step.description}")
            instructions.append("Instructions:")
            
            for i, instruction in enumerate(step.instructions, 1):
                instructions.append(f"  {i}. {instruction}")
            
            if step.verification:
                instructions.append(f"✓ Verification: {step.verification}")
        
        instructions.append("")
        instructions.append("=" * 60)
        instructions.append("If you encounter problems during these steps:")
        instructions.append("1. Stop and restore from your backup")
        instructions.append("2. Contact support with details about which step failed")
        instructions.append("3. Include any error messages you received")
        
        return instructions