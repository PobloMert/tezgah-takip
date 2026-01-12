#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - File Access Validator
Dosya ve dizin erişim izinlerini kontrol eder
"""

import os
import stat
import logging
import tempfile
from pathlib import Path
from typing import List
from database_error_models import PermissionResult, PermissionLevel

class FileAccessValidator:
    """Dosya erişim izinlerini kontrol eder"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def check_directory_permissions(self, path: str) -> PermissionResult:
        """
        Dizin izinlerini kontrol et
        
        Args:
            path: Kontrol edilecek dizin yolu
            
        Returns:
            PermissionResult: İzin kontrolü sonucu
        """
        self.logger.info(f"🔐 Dizin izinleri kontrol ediliyor: {path}")
        
        try:
            path_obj = Path(path)
            
            # Yol mevcut değilse
            if not path_obj.exists():
                self.logger.debug(f"   📁 Dizin mevcut değil: {path}")
                
                # Parent dizin var mı?
                parent = path_obj.parent
                if not parent.exists():
                    self.logger.warning(f"   ❌ Üst dizin de mevcut değil: {parent}")
                    return PermissionResult(
                        can_read=False,
                        can_write=False,
                        can_create=False,
                        permission_level=PermissionLevel.PATH_NOT_EXISTS,
                        error_message="Üst dizin mevcut değil",
                        suggested_fix="Dizin yolunu kontrol edin veya oluşturun"
                    )
                
                # Parent dizinde oluşturma izni var mı?
                can_create = os.access(parent, os.W_OK)
                self.logger.debug(f"   🔧 Parent dizin yazma izni: {can_create}")
                
                if can_create:
                    self.logger.info(f"   ✅ Dizin oluşturulabilir: {path}")
                else:
                    self.logger.warning(f"   ❌ Dizin oluşturma izni yok: {parent}")
                
                return PermissionResult(
                    can_read=False,
                    can_write=False,
                    can_create=can_create,
                    permission_level=PermissionLevel.PATH_NOT_EXISTS if not can_create else PermissionLevel.FULL_ACCESS,
                    error_message=None if can_create else "Dizin oluşturma izni yok",
                    suggested_fix=None if can_create else "Yönetici olarak çalıştırın"
                )
            
            # Dizin mevcut - izinleri kontrol et
            can_read = os.access(path, os.R_OK)
            can_write = os.access(path, os.W_OK)
            can_create = can_write  # Yazma izni varsa oluşturma da var
            
            self.logger.debug(f"   📖 Okuma izni: {can_read}")
            self.logger.debug(f"   ✏️ Yazma izni: {can_write}")
            self.logger.debug(f"   🆕 Oluşturma izni: {can_create}")
            
            # İzin seviyesini belirle
            if can_read and can_write:
                permission_level = PermissionLevel.FULL_ACCESS
                error_message = None
                suggested_fix = None
                self.logger.info(f"   ✅ Tam erişim izni mevcut")
            elif can_read:
                permission_level = PermissionLevel.READ_ONLY
                error_message = "Sadece okuma izni var"
                suggested_fix = "Yazma izni için yönetici olarak çalıştırın"
                self.logger.warning(f"   ⚠️ Sadece okuma izni: {path}")
            else:
                permission_level = PermissionLevel.NO_ACCESS
                error_message = "Erişim izni yok"
                suggested_fix = "Dosya izinlerini kontrol edin"
                self.logger.error(f"   ❌ Erişim izni yok: {path}")
            
            result = PermissionResult(
                can_read=can_read,
                can_write=can_write,
                can_create=can_create,
                permission_level=permission_level,
                error_message=error_message,
                suggested_fix=suggested_fix
            )
            
            self.logger.info(f"✅ Dizin izin kontrolü tamamlandı: {permission_level.value}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Dizin izin kontrolü hatası: {e}")
            self.logger.debug(f"   Hata türü: {type(e).__name__}")
            self.logger.debug(f"   Hata detayı: {str(e)}")
            
            return PermissionResult(
                can_read=False,
                can_write=False,
                can_create=False,
                permission_level=PermissionLevel.NO_ACCESS,
                error_message=f"İzin kontrolü hatası: {e}",
                suggested_fix="Sistem yöneticisine başvurun"
            )
    
    def check_file_permissions(self, file_path: str) -> PermissionResult:
        """
        Dosya izinlerini kontrol et
        
        Args:
            file_path: Kontrol edilecek dosya yolu
            
        Returns:
            PermissionResult: İzin kontrolü sonucu
        """
        self.logger.info(f"📄 Dosya izinleri kontrol ediliyor: {file_path}")
        
        try:
            file_obj = Path(file_path)
            
            # Dosya mevcut değilse dizin izinlerini kontrol et
            if not file_obj.exists():
                return self.check_directory_permissions(str(file_obj.parent))
            
            # Dosya mevcut - izinleri kontrol et
            can_read = os.access(file_path, os.R_OK)
            can_write = os.access(file_path, os.W_OK)
            
            # İzin seviyesini belirle
            if can_read and can_write:
                permission_level = PermissionLevel.FULL_ACCESS
                error_message = None
                suggested_fix = None
            elif can_read:
                permission_level = PermissionLevel.READ_ONLY
                error_message = "Dosya sadece okunabilir"
                suggested_fix = "Dosya özelliklerinden yazma iznini açın"
            else:
                permission_level = PermissionLevel.NO_ACCESS
                error_message = "Dosyaya erişim izni yok"
                suggested_fix = "Dosya izinlerini kontrol edin"
            
            result = PermissionResult(
                can_read=can_read,
                can_write=can_write,
                can_create=can_write,  # Yazma izni varsa oluşturma da var
                permission_level=permission_level,
                error_message=error_message,
                suggested_fix=suggested_fix
            )
            
            self.logger.info(f"✅ Dosya izin kontrolü tamamlandı: {permission_level.value}")
            return result
            
        except Exception as e:
            self.logger.error(f"Dosya izin kontrolü hatası: {e}")
            return PermissionResult(
                can_read=False,
                can_write=False,
                can_create=False,
                permission_level=PermissionLevel.NO_ACCESS,
                error_message=f"İzin kontrolü hatası: {e}",
                suggested_fix="Sistem yöneticisine başvurun"
            )
    
    def test_write_access(self, directory: str) -> bool:
        """
        Dizinde yazma erişimini test et
        
        Args:
            directory: Test edilecek dizin
            
        Returns:
            bool: Yazma erişimi var mı?
        """
        try:
            # Geçici dosya oluşturmayı dene
            test_file = os.path.join(directory, f".tezgahtakip_test_{os.getpid()}")
            
            with open(test_file, 'w') as f:
                f.write("test")
            
            # Dosyayı sil
            os.remove(test_file)
            
            self.logger.info(f"✅ Yazma erişimi test edildi: {directory}")
            return True
            
        except Exception as e:
            self.logger.warning(f"❌ Yazma erişimi testi başarısız: {directory} - {e}")
            return False
    
    def get_permission_issues(self, path: str) -> List[str]:
        """
        İzin sorunlarını listele
        
        Args:
            path: Kontrol edilecek yol
            
        Returns:
            List[str]: Sorun listesi
        """
        issues = []
        
        try:
            path_obj = Path(path)
            
            # Dosya/dizin var mı?
            if not path_obj.exists():
                issues.append("Dosya veya dizin mevcut değil")
                
                # Parent dizin var mı?
                parent = path_obj.parent
                if not parent.exists():
                    issues.append("Üst dizin mevcut değil")
                elif not os.access(parent, os.W_OK):
                    issues.append("Üst dizinde yazma izni yok")
            else:
                # Okuma izni
                if not os.access(path, os.R_OK):
                    issues.append("Okuma izni yok")
                
                # Yazma izni
                if not os.access(path, os.W_OK):
                    issues.append("Yazma izni yok")
                
                # Dosya kilitli mi?
                if path_obj.is_file():
                    try:
                        with open(path, 'a'):
                            pass
                    except PermissionError:
                        issues.append("Dosya başka bir işlem tarafından kullanılıyor")
                    except Exception:
                        pass
            
            # Windows özel kontroller
            if os.name == 'nt':
                # Yol çok uzun mu?
                if len(str(path)) > 260:
                    issues.append("Dosya yolu çok uzun (Windows sınırı: 260 karakter)")
                
                # Özel karakterler var mı?
                invalid_chars = '<>:"|?*'
                if any(char in str(path) for char in invalid_chars):
                    issues.append("Dosya yolunda geçersiz karakterler var")
            
        except Exception as e:
            issues.append(f"İzin kontrolü hatası: {e}")
        
        return issues
    
    def suggest_alternative_locations(self, failed_path: str) -> List[str]:
        """
        Alternatif konum önerileri
        
        Args:
            failed_path: Başarısız olan yol
            
        Returns:
            List[str]: Alternatif yol önerileri
        """
        alternatives = []
        
        try:
            # Kullanıcı belgeler klasörü
            documents = Path.home() / "Documents" / "TezgahTakip"
            alternatives.append(str(documents))
            
            # AppData Local (Windows)
            if os.name == 'nt':
                appdata = os.environ.get('LOCALAPPDATA')
                if appdata:
                    alternatives.append(os.path.join(appdata, "TezgahTakip"))
            
            # Kullanıcı ana dizini
            home_app = Path.home() / ".tezgahtakip"
            alternatives.append(str(home_app))
            
            # Geçici dizin
            temp_dir = tempfile.gettempdir()
            alternatives.append(os.path.join(temp_dir, "TezgahTakip"))
            
        except Exception as e:
            self.logger.error(f"Alternatif konum önerisi hatası: {e}")
        
        return alternatives