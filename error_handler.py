"""
Error Handler for TezgahTakip Update System
Comprehensive error logging, user notification, and error report generation
"""

import os
import sys
import logging
import traceback
import json
import time
import platform
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path


@dataclass
class ErrorReport:
    """Comprehensive error report"""
    error_id: str
    timestamp: float
    error_type: str
    error_message: str
    stack_trace: str
    system_info: Dict[str, Any]
    context: Dict[str, Any]
    recovery_suggestions: List[str]
    log_file_path: Optional[str] = None


class ErrorHandler:
    """
    Handles comprehensive error logging, user notification, and recovery suggestions
    """
    
    def __init__(self, log_dir: str = "logs"):
        self.logger = logging.getLogger("ErrorHandler")
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Error report storage
        self.error_reports_file = self.log_dir / "error_reports.json"
        self.error_reports = self._load_error_reports()
        
        # System information cache
        self.system_info = self._collect_system_info()
        
        self.logger.debug("ErrorHandler initialized")
    
    def handle_update_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle update-related errors with comprehensive logging and recovery suggestions
        """
        if context is None:
            context = {}
        
        self.logger.error(f"Handling update error: {error}")
        
        try:
            # Generate error report
            error_report = self._create_error_report(error, context)
            
            # Log the error
            self.log_error(error, context)
            
            # Store error report
            self.error_reports[error_report.error_id] = error_report
            self._save_error_reports()
            
            # Generate recovery suggestions
            recovery_options = self.suggest_recovery_options(str(error), context)
            
            # Notify user
            self.notify_user(f"Update Error: {str(error)}", "error")
            
            return {
                'error_id': error_report.error_id,
                'error_message': str(error),
                'recovery_options': recovery_options,
                'error_report_path': str(self.error_reports_file),
                'log_file_path': error_report.log_file_path
            }
            
        except Exception as e:
            self.logger.critical(f"Error in error handler: {e}")
            return {
                'error_id': 'handler_error',
                'error_message': f"Error handler failed: {e}",
                'recovery_options': ['Contact support', 'Restart application'],
                'error_report_path': None,
                'log_file_path': None
            }
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None) -> None:
        """
        Log error with detailed information
        """
        if context is None:
            context = {}
        
        # Create detailed log entry
        log_entry = {
            'timestamp': time.time(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'stack_trace': traceback.format_exc(),
            'context': context,
            'system_info': self.system_info
        }
        
        # Log to main logger
        self.logger.error(f"Error: {error}")
        self.logger.debug(f"Error context: {context}")
        self.logger.debug(f"Stack trace: {traceback.format_exc()}")
        
        # Write to dedicated error log file
        error_log_file = self.log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
        
        try:
            with open(error_log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"ERROR LOGGED AT: {datetime.fromtimestamp(log_entry['timestamp'])}\n")
                f.write(f"ERROR TYPE: {log_entry['error_type']}\n")
                f.write(f"ERROR MESSAGE: {log_entry['error_message']}\n")
                f.write(f"CONTEXT: {json.dumps(log_entry['context'], indent=2)}\n")
                f.write(f"STACK TRACE:\n{log_entry['stack_trace']}\n")
                f.write(f"SYSTEM INFO: {json.dumps(log_entry['system_info'], indent=2)}\n")
                f.write(f"{'='*80}\n")
        
        except Exception as e:
            self.logger.critical(f"Failed to write to error log file: {e}")
    
    def notify_user(self, message: str, severity: str = "info") -> None:
        """
        Notify user of errors or important information
        """
        # For now, just log the notification
        # In a real GUI application, this would show a dialog or notification
        
        severity_map = {
            'info': self.logger.info,
            'warning': self.logger.warning,
            'error': self.logger.error,
            'critical': self.logger.critical
        }
        
        log_func = severity_map.get(severity, self.logger.info)
        log_func(f"USER NOTIFICATION [{severity.upper()}]: {message}")
        
        # Store notification for potential UI display
        notification_file = self.log_dir / "user_notifications.json"
        
        try:
            notifications = []
            if notification_file.exists():
                with open(notification_file, 'r', encoding='utf-8') as f:
                    notifications = json.load(f)
            
            notifications.append({
                'timestamp': time.time(),
                'message': message,
                'severity': severity,
                'read': False
            })
            
            # Keep only last 50 notifications
            notifications = notifications[-50:]
            
            with open(notification_file, 'w', encoding='utf-8') as f:
                json.dump(notifications, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Failed to store user notification: {e}")
    
    def suggest_recovery_options(self, error_message: str, context: Dict[str, Any] = None) -> List[str]:
        """
        Suggest recovery options based on error type and context
        """
        if context is None:
            context = {}
        
        suggestions = []
        error_lower = error_message.lower()
        
        # Base library specific errors
        if 'base_library' in error_lower or 'library.zip' in error_lower:
            suggestions.extend([
                "Check if base_library.zip exists in the application directory",
                "Try running the application as administrator",
                "Reinstall the application to restore missing files",
                "Check Windows Defender exclusions for the application folder"
            ])
        
        # Permission errors
        if 'permission' in error_lower or 'access' in error_lower:
            suggestions.extend([
                "Run the application as administrator",
                "Check file and folder permissions",
                "Ensure the application folder is not read-only",
                "Add application folder to antivirus exclusions"
            ])
        
        # File not found errors
        if 'not found' in error_lower or 'no such file' in error_lower:
            suggestions.extend([
                "Verify all application files are present",
                "Check if files were quarantined by antivirus",
                "Reinstall the application",
                "Restore from backup if available"
            ])
        
        # Import/module errors
        if 'import' in error_lower or 'module' in error_lower:
            suggestions.extend([
                "Check Python installation and dependencies",
                "Verify base_library.zip contains required modules",
                "Try running from a different location",
                "Check for conflicting Python installations"
            ])
        
        # Network/download errors
        if 'network' in error_lower or 'download' in error_lower or 'connection' in error_lower:
            suggestions.extend([
                "Check internet connection",
                "Try again later if servers are busy",
                "Check firewall and proxy settings",
                "Use manual download if automatic update fails"
            ])
        
        # Disk space errors
        if 'space' in error_lower or 'disk' in error_lower:
            suggestions.extend([
                "Free up disk space",
                "Clean temporary files",
                "Move application to drive with more space",
                "Check disk health"
            ])
        
        # Generic suggestions if no specific ones found
        if not suggestions:
            suggestions.extend([
                "Restart the application",
                "Restart your computer",
                "Check system requirements",
                "Contact support with error details"
            ])
        
        # Add context-specific suggestions
        if context.get('update_in_progress'):
            suggestions.insert(0, "Wait for current update to complete before trying again")
        
        if context.get('backup_available'):
            suggestions.insert(0, "Restore from backup to previous working state")
        
        return suggestions[:8]  # Limit to 8 suggestions
    
    def generate_error_report(self, error_id: str = None) -> str:
        """
        Generate comprehensive error report for support
        """
        if error_id and error_id in self.error_reports:
            error_report = self.error_reports[error_id]
            
            report_lines = [
                "=" * 80,
                "TEZGAH TAKIP ERROR REPORT",
                "=" * 80,
                f"Error ID: {error_report.error_id}",
                f"Timestamp: {datetime.fromtimestamp(error_report.timestamp)}",
                f"Error Type: {error_report.error_type}",
                f"Error Message: {error_report.error_message}",
                "",
                "SYSTEM INFORMATION:",
                "-" * 40,
                json.dumps(error_report.system_info, indent=2),
                "",
                "CONTEXT:",
                "-" * 40,
                json.dumps(error_report.context, indent=2),
                "",
                "STACK TRACE:",
                "-" * 40,
                error_report.stack_trace,
                "",
                "RECOVERY SUGGESTIONS:",
                "-" * 40,
            ]
            
            for i, suggestion in enumerate(error_report.recovery_suggestions, 1):
                report_lines.append(f"{i}. {suggestion}")
            
            report_lines.extend([
                "",
                "=" * 80,
                "END OF REPORT",
                "=" * 80
            ])
            
            return "\n".join(report_lines)
        
        else:
            # Generate general system report
            return self._generate_system_report()
    
    def _create_error_report(self, error: Exception, context: Dict[str, Any]) -> ErrorReport:
        """
        Create comprehensive error report
        """
        error_id = f"error_{int(time.time())}_{hash(str(error)) % 10000}"
        
        # Get current log file
        current_log_file = None
        for handler in self.logger.handlers:
            if hasattr(handler, 'baseFilename'):
                current_log_file = handler.baseFilename
                break
        
        return ErrorReport(
            error_id=error_id,
            timestamp=time.time(),
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            system_info=self.system_info,
            context=context,
            recovery_suggestions=self.suggest_recovery_options(str(error), context),
            log_file_path=current_log_file
        )
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """
        Collect comprehensive system information
        """
        try:
            return {
                'platform': platform.platform(),
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'python_implementation': platform.python_implementation(),
                'python_executable': sys.executable,
                'working_directory': os.getcwd(),
                'environment_variables': {
                    'PATH': os.environ.get('PATH', ''),
                    'PYTHONPATH': os.environ.get('PYTHONPATH', ''),
                    'TEMP': os.environ.get('TEMP', ''),
                    'USERNAME': os.environ.get('USERNAME', ''),
                    'COMPUTERNAME': os.environ.get('COMPUTERNAME', '')
                },
                'disk_usage': self._get_disk_usage(),
                'memory_info': self._get_memory_info(),
                'application_info': {
                    'frozen': getattr(sys, 'frozen', False),
                    'argv': sys.argv,
                    'path': sys.path[:5]  # First 5 paths only
                }
            }
        except Exception as e:
            self.logger.error(f"Error collecting system info: {e}")
            return {'error': f"Failed to collect system info: {e}"}
    
    def _get_disk_usage(self) -> Dict[str, Any]:
        """Get disk usage information"""
        try:
            import shutil
            usage = shutil.disk_usage(os.getcwd())
            return {
                'total_gb': round(usage.total / (1024**3), 2),
                'used_gb': round((usage.total - usage.free) / (1024**3), 2),
                'free_gb': round(usage.free / (1024**3), 2),
                'free_percent': round((usage.free / usage.total) * 100, 1)
            }
        except Exception:
            return {'error': 'Could not get disk usage'}
    
    def _get_memory_info(self) -> Dict[str, Any]:
        """Get memory information"""
        try:
            if platform.system() == 'Windows':
                import ctypes
                kernel32 = ctypes.windll.kernel32
                c_ulong = ctypes.c_ulong
                
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ('dwLength', c_ulong),
                        ('dwMemoryLoad', c_ulong),
                        ('ullTotalPhys', ctypes.c_ulonglong),
                        ('ullAvailPhys', ctypes.c_ulonglong),
                        ('ullTotalPageFile', ctypes.c_ulonglong),
                        ('ullAvailPageFile', ctypes.c_ulonglong),
                        ('ullTotalVirtual', ctypes.c_ulonglong),
                        ('ullAvailVirtual', ctypes.c_ulonglong),
                        ('ullAvailExtendedVirtual', ctypes.c_ulonglong),
                    ]
                
                memoryStatus = MEMORYSTATUSEX()
                memoryStatus.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                kernel32.GlobalMemoryStatusEx(ctypes.byref(memoryStatus))
                
                return {
                    'total_gb': round(memoryStatus.ullTotalPhys / (1024**3), 2),
                    'available_gb': round(memoryStatus.ullAvailPhys / (1024**3), 2),
                    'used_percent': memoryStatus.dwMemoryLoad
                }
            else:
                return {'error': 'Memory info only available on Windows'}
        except Exception:
            return {'error': 'Could not get memory info'}
    
    def _generate_system_report(self) -> str:
        """Generate general system report"""
        report_lines = [
            "=" * 80,
            "TEZGAH TAKIP SYSTEM REPORT",
            "=" * 80,
            f"Generated: {datetime.now()}",
            "",
            "SYSTEM INFORMATION:",
            "-" * 40,
            json.dumps(self.system_info, indent=2),
            "",
            "RECENT ERRORS:",
            "-" * 40
        ]
        
        # Add recent errors
        recent_errors = sorted(self.error_reports.values(), key=lambda x: x.timestamp, reverse=True)[:5]
        
        for error in recent_errors:
            report_lines.extend([
                f"- {error.error_type}: {error.error_message}",
                f"  Time: {datetime.fromtimestamp(error.timestamp)}",
                f"  ID: {error.error_id}",
                ""
            ])
        
        if not recent_errors:
            report_lines.append("No recent errors found.")
        
        report_lines.extend([
            "",
            "=" * 80,
            "END OF REPORT",
            "=" * 80
        ])
        
        return "\n".join(report_lines)
    
    def _load_error_reports(self) -> Dict[str, ErrorReport]:
        """Load error reports from file"""
        if not self.error_reports_file.exists():
            return {}
        
        try:
            with open(self.error_reports_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            reports = {}
            for error_id, report_data in data.items():
                reports[error_id] = ErrorReport(**report_data)
            
            return reports
            
        except Exception as e:
            self.logger.error(f"Error loading error reports: {e}")
            return {}
    
    def _save_error_reports(self) -> None:
        """Save error reports to file"""
        try:
            # Keep only last 100 error reports
            if len(self.error_reports) > 100:
                sorted_reports = sorted(self.error_reports.items(), key=lambda x: x[1].timestamp, reverse=True)
                self.error_reports = dict(sorted_reports[:100])
            
            data = {}
            for error_id, report in self.error_reports.items():
                data[error_id] = asdict(report)
            
            with open(self.error_reports_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Error saving error reports: {e}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        if not self.error_reports:
            return {
                'total_errors': 0,
                'error_types': {},
                'recent_errors': 0,
                'most_common_error': None
            }
        
        # Count by error type
        error_types = {}
        recent_count = 0
        recent_threshold = time.time() - (24 * 60 * 60)  # Last 24 hours
        
        for report in self.error_reports.values():
            error_types[report.error_type] = error_types.get(report.error_type, 0) + 1
            
            if report.timestamp > recent_threshold:
                recent_count += 1
        
        most_common = max(error_types.items(), key=lambda x: x[1]) if error_types else None
        
        return {
            'total_errors': len(self.error_reports),
            'error_types': error_types,
            'recent_errors': recent_count,
            'most_common_error': most_common[0] if most_common else None
        }