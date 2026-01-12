#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Database Path Resolver
Güvenli ve erişilebilir veritabanı yolları belirler
"""

import os
import logging
from pathlib import Path
from typing import List, Optional
import tempfile
from datetime import datetime
from database_error_models import PathResolutionResult, PermissionResult, PermissionLevel

class DatabasePathResolver:
    """Veritabanı dosyası için güvenli yollar belirler"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.default_db_name = "tezgah_takip_v2.db"
        
    def resolve_database_path(self, preferred_path: Optional[str] = None) -> PathResolutionResult:
        """
        Ana veritabanı yolu çözümleme metodu
        
        Args:
            preferred_path: Tercih edilen veritabanı yolu
            
        Returns:
            PathResolutionResult: Çözümlenmiş yol bilgisi
        """
        self.logger.info("🔍 Veritabanı yolu çözümleme başlatılıyor...")
        self.logger.info(f"📋 Tercih edilen yol: {preferred_path or 'Belirtilmemiş'}")
        
        # Yol öncelik listesi
        candidate_paths = self.get_fallback_paths(preferred_path)
        self.logger.info(f"📊 Toplam {len(candidate_paths)} aday yol belirlendi")
        
        for level, path_info in enumerate(candidate_paths):
            path_str = path_info["path"]
            description = path_info["description"]
            
            self.logger.info(f"📁 Denenen yol ({level}): {path_str}")
            self.logger.debug(f"   Açıklama: {description}")
            
            # Yol erişilebilirlik kontrolü
            accessibility_start = datetime.now()
            is_accessible = self.validate_path_accessibility(path_str)
            accessibility_time = (datetime.now() - accessibility_start).total_seconds()
            
            self.logger.debug(f"   Erişilebilirlik kontrolü: {accessibility_time:.3f}s -> {is_accessible}")
            
            if is_accessible:
                # Dizin oluşturma gerekli mi?
                directory = os.path.dirname(path_str)
                creation_required = not os.path.exists(directory)
                
                self.logger.debug(f"   Dizin mevcut: {not creation_required}")
                
                if creation_required:
                    creation_start = datetime.now()
                    creation_success = self.create_directory_if_needed(path_str)
                    creation_time = (datetime.now() - creation_start).total_seconds()
                    
                    self.logger.info(f"   📁 Dizin oluşturma: {creation_time:.3f}s -> {creation_success}")
                    
                    if not creation_success:
                        self.logger.warning(f"❌ Dizin oluşturulamadı: {directory}")
                        continue
                
                # Permission kontrolü
                permission_start = datetime.now()
                try:
                    from file_access_validator import FileAccessValidator
                    validator = FileAccessValidator()
                    permission_result = validator.check_directory_permissions(directory)
                except ImportError:
                    self.logger.warning("⚠️ FileAccessValidator import edilemedi, basit kontrol kullanılıyor")
                    # Fallback permission check
                    permission_result = PermissionResult(
                        can_read=os.access(directory, os.R_OK) if os.path.exists(directory) else True,
                        can_write=os.access(directory, os.W_OK) if os.path.exists(directory) else True,
                        can_create=True,
                        permission_level=PermissionLevel.FULL_ACCESS
                    )
                
                permission_time = (datetime.now() - permission_start).total_seconds()
                self.logger.debug(f"   İzin kontrolü: {permission_time:.3f}s -> {permission_result.permission_level.value}")
                
                if permission_result.has_full_access:
                    result = PathResolutionResult(
                        resolved_path=path_str,
                        is_primary_path=(level == 0),
                        fallback_level=level,
                        permission_result=permission_result,
                        creation_required=creation_required,
                        warnings=[]
                    )
                    
                    self.logger.info(f"✅ Veritabanı yolu başarıyla çözümlendi!")
                    self.logger.info(f"   📍 Yol: {path_str}")
                    self.logger.info(f"   🎯 Birincil yol: {result.is_primary_path}")
                    self.logger.info(f"   📊 Fallback seviyesi: {level}")
                    self.logger.info(f"   🔐 İzin durumu: {permission_result.permission_level.value}")
                    
                    return result
                else:
                    self.logger.warning(f"⚠️ Yetersiz izinler: {path_str}")
                    self.logger.debug(f"   İzin detayı: {permission_result.error_message}")
            else:
                self.logger.warning(f"❌ Yol erişilemez: {path_str}")
        
        # Hiçbir yol çalışmazsa geçici dizin kullan
        temp_path = self._get_temp_database_path()
        self.logger.warning(f"🚨 Tüm yollar başarısız! Geçici veritabanı yolu kullanılıyor")
        self.logger.warning(f"   📍 Geçici yol: {temp_path}")
        self.logger.warning(f"   ⚠️ Bu veritabanı geçici olup sistem yeniden başlatıldığında kaybolabilir!")
        
        return PathResolutionResult(
            resolved_path=temp_path,
            is_primary_path=False,
            fallback_level=99,  # En son çare
            permission_result=PermissionResult(
                can_read=True,
                can_write=True,
                can_create=True,
                permission_level=PermissionLevel.FULL_ACCESS
            ),
            creation_required=False,
            warnings=["Geçici dizin kullanılıyor - veriler kalıcı olmayabilir"]
        )
    
    def get_fallback_paths(self, preferred_path: Optional[str] = None) -> List[dict]:
        """
        Fallback yol listesi oluştur
        
        Args:
            preferred_path: Tercih edilen yol
            
        Returns:
            List[dict]: Yol bilgileri listesi
        """
        self.logger.debug("📋 Fallback yol listesi oluşturuluyor...")
        paths = []
        
        # 1. Tercih edilen yol (varsa)
        if preferred_path:
            paths.append({
                "path": preferred_path,
                "description": "Konfigürasyonda belirtilen yol"
            })
            self.logger.debug(f"   ✅ Tercih edilen yol eklendi: {preferred_path}")
        
        # 2. Mevcut çalışma dizini
        current_dir = os.getcwd()
        current_path = os.path.join(current_dir, self.default_db_name)
        paths.append({
            "path": current_path,
            "description": "Mevcut çalışma dizini"
        })
        self.logger.debug(f"   ✅ Çalışma dizini eklendi: {current_path}")
        
        # 3. Kullanıcının Belgeler klasörü
        try:
            documents_path = Path.home() / "Documents" / "TezgahTakip"
            documents_full_path = str(documents_path / self.default_db_name)
            paths.append({
                "path": documents_full_path,
                "description": "Kullanıcı Belgeler klasörü"
            })
            self.logger.debug(f"   ✅ Belgeler klasörü eklendi: {documents_full_path}")
        except Exception as e:
            self.logger.warning(f"   ❌ Belgeler klasörü alınamadı: {e}")
        
        # 4. AppData/Local klasörü (Windows)
        if os.name == 'nt':
            try:
                appdata_local = os.environ.get('LOCALAPPDATA')
                if appdata_local:
                    app_dir = Path(appdata_local) / "TezgahTakip"
                    appdata_path = str(app_dir / self.default_db_name)
                    paths.append({
                        "path": appdata_path,
                        "description": "AppData Local klasörü"
                    })
                    self.logger.debug(f"   ✅ AppData Local eklendi: {appdata_path}")
                else:
                    self.logger.debug("   ⚠️ LOCALAPPDATA environment variable bulunamadı")
            except Exception as e:
                self.logger.warning(f"   ❌ AppData Local klasörü alınamadı: {e}")
        
        # 5. Kullanıcı ana dizini
        try:
            home_dir = Path.home() / ".tezgahtakip"
            home_path = str(home_dir / self.default_db_name)
            paths.append({
                "path": home_path,
                "description": "Kullanıcı ana dizini"
            })
            self.logger.debug(f"   ✅ Ana dizin eklendi: {home_path}")
        except Exception as e:
            self.logger.warning(f"   ❌ Kullanıcı ana dizini alınamadı: {e}")
        
        # 6. Program Files (sadece okuma için)
        if os.name == 'nt':
            try:
                program_files = os.environ.get('PROGRAMFILES')
                if program_files:
                    app_dir = Path(program_files) / "TezgahTakip"
                    pf_path = str(app_dir / self.default_db_name)
                    paths.append({
                        "path": pf_path,
                        "description": "Program Files klasörü"
                    })
                    self.logger.debug(f"   ✅ Program Files eklendi: {pf_path}")
                else:
                    self.logger.debug("   ⚠️ PROGRAMFILES environment variable bulunamadı")
            except Exception as e:
                self.logger.warning(f"   ❌ Program Files klasörü alınamadı: {e}")
        
        self.logger.info(f"📋 Toplam {len(paths)} adet fallback yol belirlendi")
        
        # Debug için tüm yolları logla
        for i, path_info in enumerate(paths):
            self.logger.debug(f"   {i}: {path_info['path']} ({path_info['description']})")
        
        return paths
    
    def validate_path_accessibility(self, path: str) -> bool:
        """
        Yolun erişilebilirliğini kontrol et
        
        Args:
            path: Kontrol edilecek yol
            
        Returns:
            bool: Erişilebilir mi?
        """
        self.logger.debug(f"🔍 Yol erişilebilirlik kontrolü: {path}")
        
        try:
            # Yol geçerli mi?
            path_obj = Path(path)
            self.logger.debug(f"   Yol objesi oluşturuldu: {path_obj}")
            
            # Dizin var mı?
            directory = path_obj.parent
            self.logger.debug(f"   Üst dizin: {directory}")
            
            # Eğer dizin yoksa oluşturulabilir mi?
            if not directory.exists():
                self.logger.debug(f"   Dizin mevcut değil, parent kontrol ediliyor...")
                # Parent dizin var mı ve yazılabilir mi?
                parent = directory.parent
                if not parent.exists():
                    self.logger.debug(f"   Parent dizin mevcut değil: {parent}")
                    return False
                
                # Yazma izni var mı?
                if not os.access(parent, os.W_OK):
                    self.logger.debug(f"   Parent dizinde yazma izni yok: {parent}")
                    return False
                
                self.logger.debug(f"   Parent dizin yazılabilir: {parent}")
            
            # Dizin varsa yazılabilir mi?
            elif not os.access(directory, os.W_OK):
                self.logger.debug(f"   Dizin yazılabilir değil: {directory}")
                return False
            
            # Dosya varsa yazılabilir mi?
            if path_obj.exists() and not os.access(path, os.W_OK):
                self.logger.debug(f"   Dosya yazılabilir değil: {path}")
                return False
            
            self.logger.debug(f"   ✅ Yol erişilebilir: {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Yol erişilebilirlik kontrolü hatası: {e}")
            self.logger.debug(f"   Hata detayı: {type(e).__name__}: {str(e)}")
            return False
    
    def create_directory_if_needed(self, file_path: str) -> bool:
        """
        Gerekirse dizin oluştur
        
        Args:
            file_path: Dosya yolu
            
        Returns:
            bool: Başarılı mı?
        """
        try:
            directory = os.path.dirname(file_path)
            self.logger.debug(f"📁 Dizin oluşturma kontrolü: {directory}")
            
            if not os.path.exists(directory):
                self.logger.info(f"📁 Dizin oluşturuluyor: {directory}")
                creation_start = datetime.now()
                
                os.makedirs(directory, exist_ok=True)
                
                creation_time = (datetime.now() - creation_start).total_seconds()
                self.logger.info(f"✅ Dizin başarıyla oluşturuldu: {directory} ({creation_time:.3f}s)")
                
                # Oluşturulan dizinin izinlerini kontrol et
                if os.access(directory, os.W_OK):
                    self.logger.debug(f"   ✅ Oluşturulan dizin yazılabilir")
                else:
                    self.logger.warning(f"   ⚠️ Oluşturulan dizin yazılabilir değil")
            else:
                self.logger.debug(f"   ✅ Dizin zaten mevcut: {directory}")
            
            return True
            
        except PermissionError as e:
            self.logger.error(f"❌ Dizin oluşturma izin hatası: {e}")
            self.logger.debug(f"   Dosya yolu: {file_path}")
            return False
        except OSError as e:
            self.logger.error(f"❌ Dizin oluşturma sistem hatası: {e}")
            self.logger.debug(f"   Dosya yolu: {file_path}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Dizin oluşturma beklenmeyen hatası: {e}")
            self.logger.debug(f"   Hata türü: {type(e).__name__}")
            self.logger.debug(f"   Dosya yolu: {file_path}")
            return False
    
    def _get_temp_database_path(self) -> str:
        """Geçici veritabanı yolu al"""
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"tezgahtakip_temp_{os.getpid()}.db")
        
        self.logger.debug(f"🔄 Geçici veritabanı yolu oluşturuluyor:")
        self.logger.debug(f"   Temp dizin: {temp_dir}")
        self.logger.debug(f"   Process ID: {os.getpid()}")
        self.logger.debug(f"   Tam yol: {temp_path}")
        
        return temp_path