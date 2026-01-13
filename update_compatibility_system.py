"""
Complete Update Compatibility System Integration
Integrates all components to solve v2.0.0 to v2.1.3 update issues
"""

import os
import sys
import logging
from typing import Optional, Dict, Any

# Import all components
from enhanced_update_manager import EnhancedUpdateManager, UpdateStatus
from path_resolver import PathResolver
from file_validator import FileValidator
from backup_manager import BackupManager
from error_handler import ErrorHandler
from fallback_system import FallbackSystem
from data_preservation_manager import DataPreservationManager
from manual_update_manager import ManualUpdateManager


class UpdateCompatibilitySystem:
    """
    Complete system integration for update compatibility fixes
    """
    
    def __init__(self, log_level=logging.INFO):
        # Setup logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('update_compatibility.log'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("UpdateCompatibilitySystem")
        
        # Initialize all components
        self.path_resolver = None
        self.file_validator = None
        self.backup_manager = None
        self.error_handler = None
        self.fallback_system = None
        self.data_preservation_manager = None
        self.manual_update_manager = None
        self.enhanced_updater = None
        
        self.logger.info("UpdateCompatibilitySystem initializing...")
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all system components"""
        try:
            # Core components
            self.path_resolver = PathResolver()
            self.file_validator = FileValidator(self.path_resolver)
            self.backup_manager = BackupManager(path_resolver=self.path_resolver)
            self.error_handler = ErrorHandler()
            
            # Advanced components
            self.fallback_system = FallbackSystem(self.path_resolver)
            self.data_preservation_manager = DataPreservationManager(self.path_resolver)
            self.manual_update_manager = ManualUpdateManager(self.path_resolver, self.file_validator)
            
            # Enhanced update manager
            self.enhanced_updater = EnhancedUpdateManager()
            self.enhanced_updater.set_components(
                self.path_resolver,
                self.file_validator,
                self.backup_manager,
                self.error_handler,
                self.data_preservation_manager
            )
            
            self.logger.info("All components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Component initialization failed: {e}")
            raise
    
    def diagnose_update_issue(self) -> Dict[str, Any]:
        """
        Diagnose current update-related issues
        """
        self.logger.info("Diagnosing update issues...")
        
        diagnosis = {
            'base_library_found': False,
            'executable_structure_valid': False,
            'permissions_ok': False,
            'dependencies_valid': False,
            'issues_found': [],
            'recommendations': []
        }
        
        try:
            # Check for base_library.zip
            base_lib_path = self.path_resolver.find_base_library()
            diagnosis['base_library_found'] = base_lib_path is not None
            
            if not diagnosis['base_library_found']:
                diagnosis['issues_found'].append("base_library.zip not found")
                diagnosis['recommendations'].append("Use fallback system to locate alternative library files")
            
            # Check executable structure
            diagnosis['executable_structure_valid'] = self.file_validator.verify_executable_structure()
            
            if not diagnosis['executable_structure_valid']:
                diagnosis['issues_found'].append("Invalid executable structure")
                diagnosis['recommendations'].append("Reinstall application or restore from backup")
            
            # Check permissions
            exe_dir = self.path_resolver.get_executable_directory()
            diagnosis['permissions_ok'] = self.file_validator.check_permissions(exe_dir)
            
            if not diagnosis['permissions_ok']:
                diagnosis['issues_found'].append("Insufficient permissions")
                diagnosis['recommendations'].append("Run as administrator or move to user directory")
            
            # Check dependencies
            dependencies = self.file_validator.validate_dependencies()
            missing_critical = [dep for dep in dependencies if dep.required and not dep.found]
            diagnosis['dependencies_valid'] = len(missing_critical) == 0
            
            if not diagnosis['dependencies_valid']:
                diagnosis['issues_found'].append(f"Missing critical dependencies: {[dep.name for dep in missing_critical]}")
                diagnosis['recommendations'].append("Install missing dependencies or restore from backup")
            
            self.logger.info(f"Diagnosis complete. Issues found: {len(diagnosis['issues_found'])}")
            return diagnosis
            
        except Exception as e:
            self.logger.error(f"Diagnosis failed: {e}")
            diagnosis['issues_found'].append(f"Diagnosis error: {str(e)}")
            return diagnosis
    
    def fix_base_library_issue(self) -> bool:
        """
        Attempt to fix base_library.zip issues using fallback system
        """
        self.logger.info("Attempting to fix base_library.zip issue...")
        
        try:
            # Try to find alternative base library files
            alternative_path = self.fallback_system.find_alternative_file('base_library.zip')
            
            if alternative_path:
                self.logger.info(f"Found alternative base library: {alternative_path}")
                
                # Copy to correct location
                exe_dir = self.path_resolver.get_executable_directory()
                target_path = os.path.join(exe_dir, 'base_library.zip')
                
                import shutil
                shutil.copy2(alternative_path, target_path)
                
                # Verify the fix
                if self.file_validator.check_file_integrity(target_path).is_valid:
                    self.logger.info("base_library.zip issue fixed successfully")
                    return True
                else:
                    self.logger.error("Copied base_library.zip failed integrity check")
                    return False
            else:
                self.logger.warning("No alternative base_library.zip found")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to fix base_library.zip issue: {e}")
            return False
    
    def perform_safe_update(self, target_version: str) -> Dict[str, Any]:
        """
        Perform a safe update with comprehensive error handling
        """
        self.logger.info(f"Starting safe update to version {target_version}")
        
        try:
            # Pre-update diagnosis
            diagnosis = self.diagnose_update_issue()
            
            if diagnosis['issues_found']:
                self.logger.warning(f"Pre-update issues detected: {diagnosis['issues_found']}")
                
                # Try to fix common issues
                if not diagnosis['base_library_found']:
                    if self.fix_base_library_issue():
                        self.logger.info("base_library.zip issue resolved")
                    else:
                        return {
                            'success': False,
                            'error': 'Could not resolve base_library.zip issue',
                            'manual_plan': self.manual_update_manager.create_manual_update_plan(
                                target_version, {'error_type': 'missing_base_library'}
                            )
                        }
            
            # Perform the update
            update_result = self.enhanced_updater.perform_update(target_version)
            
            if update_result.success:
                self.logger.info("Safe update completed successfully")
                return {
                    'success': True,
                    'version': target_version,
                    'backup_path': update_result.backup_path
                }
            else:
                self.logger.error(f"Update failed: {update_result.error_message}")
                
                # Generate manual update plan
                manual_plan = self.manual_update_manager.create_manual_update_plan(
                    target_version, {
                        'error_type': 'update_failure',
                        'error_message': update_result.error_message
                    }
                )
                
                return {
                    'success': False,
                    'error': update_result.error_message,
                    'recovery_options': update_result.recovery_options,
                    'manual_plan': manual_plan
                }
                
        except Exception as e:
            self.logger.error(f"Safe update failed with exception: {e}")
            
            # Handle the error
            error_result = self.error_handler.handle_update_error(e, {
                'target_version': target_version,
                'update_in_progress': True
            })
            
            return {
                'success': False,
                'error': str(e),
                'error_report': error_result,
                'manual_plan': self.manual_update_manager.create_manual_update_plan(
                    target_version, {'error_type': 'exception', 'error_message': str(e)}
                )
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status
        """
        try:
            diagnosis = self.diagnose_update_issue()
            
            # Get component statuses
            backup_stats = self.backup_manager.get_backup_statistics()
            error_stats = self.error_handler.get_error_statistics()
            
            # Get file validation summary
            dependencies = self.file_validator.validate_dependencies()
            validation_summary = self.file_validator.get_validation_summary(dependencies)
            
            return {
                'overall_health': 'healthy' if not diagnosis['issues_found'] else 'issues_detected',
                'diagnosis': diagnosis,
                'backup_statistics': backup_stats,
                'error_statistics': error_stats,
                'validation_summary': validation_summary,
                'components_initialized': {
                    'path_resolver': self.path_resolver is not None,
                    'file_validator': self.file_validator is not None,
                    'backup_manager': self.backup_manager is not None,
                    'error_handler': self.error_handler is not None,
                    'fallback_system': self.fallback_system is not None,
                    'data_preservation_manager': self.data_preservation_manager is not None,
                    'manual_update_manager': self.manual_update_manager is not None,
                    'enhanced_updater': self.enhanced_updater is not None
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get system status: {e}")
            return {
                'overall_health': 'error',
                'error': str(e)
            }
    
    def emergency_recovery(self) -> Dict[str, Any]:
        """
        Emergency recovery for severe update issues
        """
        self.logger.warning("Starting emergency recovery...")
        
        try:
            recovery_steps = []
            
            # Step 1: Try to restore from latest backup
            latest_backup = self.backup_manager.get_latest_backup()
            if latest_backup:
                self.logger.info(f"Attempting restore from backup: {latest_backup.backup_id}")
                
                if self.backup_manager.restore_backup(latest_backup.backup_path):
                    recovery_steps.append("Successfully restored from backup")
                    
                    # Verify restoration
                    if self.file_validator.verify_executable_structure():
                        recovery_steps.append("Backup restoration verified")
                        return {
                            'success': True,
                            'method': 'backup_restoration',
                            'steps': recovery_steps
                        }
                    else:
                        recovery_steps.append("Backup restoration verification failed")
                else:
                    recovery_steps.append("Backup restoration failed")
            else:
                recovery_steps.append("No backup available for restoration")
            
            # Step 2: Try fallback system recovery
            self.logger.info("Attempting fallback system recovery...")
            
            recovery_plan = self.fallback_system.create_recovery_plan(
                'emergency_recovery', 
                ['base_library.zip', 'tezgah_takip_app.py'],
                {'emergency': True}
            )
            
            recovery_steps.append(f"Generated recovery plan with {len(recovery_plan.fallback_options)} options")
            
            # Try to execute top fallback options
            for option in recovery_plan.fallback_options[:3]:
                if self.fallback_system.execute_fallback_option(option, 'base_library.zip'):
                    recovery_steps.append(f"Successfully executed fallback option: {option.reason}")
                    break
            else:
                recovery_steps.append("All fallback options failed")
            
            # Step 3: Generate manual recovery instructions
            manual_plan = self.manual_update_manager.create_manual_update_plan(
                '2.1.3', {'error_type': 'emergency_recovery'}
            )
            
            recovery_steps.append("Generated manual recovery instructions")
            
            return {
                'success': False,
                'method': 'manual_recovery_required',
                'steps': recovery_steps,
                'manual_plan': manual_plan,
                'recovery_plan': recovery_plan
            }
            
        except Exception as e:
            self.logger.error(f"Emergency recovery failed: {e}")
            return {
                'success': False,
                'method': 'recovery_failed',
                'error': str(e)
            }


# Global instance for easy access
update_compatibility_system = None

def get_update_compatibility_system():
    """Get or create the global update compatibility system instance"""
    global update_compatibility_system
    
    if update_compatibility_system is None:
        update_compatibility_system = UpdateCompatibilitySystem()
    
    return update_compatibility_system


def main():
    """Main function for testing the system"""
    print("🔧 TezgahTakip Update Compatibility System")
    print("=" * 50)
    
    try:
        # Initialize system
        system = UpdateCompatibilitySystem()
        
        # Get system status
        print("📊 System Status:")
        status = system.get_system_status()
        print(f"Overall Health: {status['overall_health']}")
        
        if status['diagnosis']['issues_found']:
            print(f"Issues Found: {status['diagnosis']['issues_found']}")
            print(f"Recommendations: {status['diagnosis']['recommendations']}")
        else:
            print("✅ No issues detected")
        
        # Test diagnosis
        print("\n🔍 Running Diagnosis:")
        diagnosis = system.diagnose_update_issue()
        
        print(f"Base Library Found: {diagnosis['base_library_found']}")
        print(f"Executable Structure Valid: {diagnosis['executable_structure_valid']}")
        print(f"Permissions OK: {diagnosis['permissions_ok']}")
        print(f"Dependencies Valid: {diagnosis['dependencies_valid']}")
        
        if diagnosis['issues_found']:
            print(f"\n⚠️ Issues: {diagnosis['issues_found']}")
            print(f"💡 Recommendations: {diagnosis['recommendations']}")
        
        print("\n✅ Update Compatibility System is working correctly!")
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()