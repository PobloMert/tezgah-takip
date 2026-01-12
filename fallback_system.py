#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Fallback System
Ana veritabanı erişimi başarısız olduğunda alternatif çözümler sunar
"""

import os
import sqlite3
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
from datetime import datetime, timezone
from database_error_models import FallbackResult, FallbackType
from database_models import Base, DatabaseManager
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

class FallbackSystem:
    """Ana veritabanı erişimi başarısız olduğunda alternatif çözümler sunar"""
    
    def __init__(self, primary_db_path: str = "tezgah_takip_v2.db"):
        self.logger = logging.getLogger(__name__)
        self.primary_db_path = primary_db_path
        self.backup_dir = Path("backups")
        self.current_fallback_path = None
        self.current_fallback_type = None
        
        # Yedek dizinini oluştur
        self._ensure_backup_directory()
        
        # Notification manager'ı import et (GUI olmadan)
        try:
            # Test ortamında GUI başlatmayı önle
            import os
            if os.environ.get('PYTEST_CURRENT_TEST') or 'pytest' in os.environ.get('_', ''):
                # Test ortamında mock kullan
                self.notification_manager = None
                self.NotificationType = None
                self.NotificationPriority = None
                self.logger.info("Test environment detected, notification manager disabled")
            else:
                from notification_manager import notification_manager, NotificationType, NotificationPriority
                self.notification_manager = notification_manager
                self.NotificationType = NotificationType
                self.NotificationPriority = NotificationPriority
        except (ImportError, Exception) as e:
            self.logger.warning(f"Notification manager not available: {e}")
            self.notification_manager = None
            self.NotificationType = None
            self.NotificationPriority = None
    
    def _ensure_backup_directory(self):
        """Yedek dizinini güvenli şekilde oluştur"""
        try:
            self.backup_dir.mkdir(exist_ok=True, mode=0o755)
            self.logger.debug(f"Backup directory ensured: {self.backup_dir}")
        except OSError as e:
            self.logger.warning(f"Failed to create backup directory: {e}")
    
    def _notify_user(self, title: str, message: str, notification_type=None, priority=None, **kwargs):
        """Kullanıcıya bildirim gönder"""
        if self.notification_manager:
            try:
                # Varsayılan değerler
                if notification_type is None:
                    notification_type = self.NotificationType.WARNING
                if priority is None:
                    priority = self.NotificationPriority.HIGH
                
                return self.notification_manager.create_notification(
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    priority=priority,
                    source="fallback_system",
                    **kwargs
                )
            except Exception as e:
                self.logger.error(f"Failed to send notification: {e}")
        else:
            # Fallback: sadece log
            self.logger.warning(f"USER NOTIFICATION: {title} - {message}")
        return None
    
    def create_memory_database(self) -> FallbackResult:
        """
        Bellek içi veritabanı oluştur
        
        Returns:
            FallbackResult: Fallback işlem sonucu
        """
        self.logger.info("🧠 Bellek içi veritabanı oluşturuluyor...")
        
        try:
            # SQLite bellek veritabanı oluştur
            memory_db_path = ":memory:"
            
            # SQLAlchemy engine oluştur
            engine = create_engine(
                'sqlite:///:memory:',
                echo=False,
                pool_pre_ping=True,
                poolclass=StaticPool,
                connect_args={'check_same_thread': False}
            )
            
            # Tabloları oluştur
            Base.metadata.create_all(engine)
            
            # Test bağlantısı
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Basit test sorgusu - SQLAlchemy 2.0 uyumlu
            from sqlalchemy import text
            result = session.execute(text("SELECT 1")).fetchone()
            session.close()
            
            if result and result[0] == 1:
                self.current_fallback_path = memory_db_path
                self.current_fallback_type = FallbackType.MEMORY_DATABASE
                
                self.logger.info("✅ Bellek içi veritabanı başarıyla oluşturuldu")
                
                # Kullanıcıya bildirim gönder
                self._notify_user(
                    title="⚠️ Geçici Veritabanı Kullanımda",
                    message="Ana veritabanına erişilemiyor. Geçici bellek veritabanı kullanılıyor. Veriler uygulama kapandığında kaybolacak.",
                    notification_type=self.NotificationType.WARNING if self.notification_manager else None,
                    priority=self.NotificationPriority.HIGH if self.notification_manager else None,
                    expires_in_minutes=30,
                    data={
                        'fallback_type': 'memory_database',
                        'primary_db_path': self.primary_db_path,
                        'data_persistence': False
                    }
                )
                
                return FallbackResult(
                    success=True,
                    fallback_type=FallbackType.MEMORY_DATABASE,
                    database_path=memory_db_path,
                    message="Bellek içi veritabanı oluşturuldu",
                    warnings=["Veriler geçici - uygulama kapandığında kaybolacak"],
                    engine=engine
                )
            else:
                raise Exception("Bellek veritabanı test sorgusu başarısız")
                
        except Exception as e:
            error_msg = f"Bellek içi veritabanı oluşturma hatası: {e}"
            self.logger.error(f"❌ {error_msg}")
            
            return FallbackResult(
                success=False,
                fallback_type=FallbackType.MEMORY_DATABASE,
                database_path=None,
                message=error_msg,
                warnings=[],
                engine=None
            )
    
    def restore_from_backup(self, backup_path: Optional[str] = None) -> FallbackResult:
        """
        Yedekten geri yükleme yap
        
        Args:
            backup_path: Belirli bir yedek dosyası yolu (None ise en son yedeği kullan)
            
        Returns:
            FallbackResult: Fallback işlem sonucu
        """
        self.logger.info("💾 Yedekten geri yükleme başlatılıyor...")
        
        try:
            # Yedek dosyasını belirle
            if backup_path is None:
                backup_path = self._find_latest_backup()
                if backup_path is None:
                    return FallbackResult(
                        success=False,
                        fallback_type=FallbackType.BACKUP_RESTORE,
                        database_path=None,
                        message="Kullanılabilir yedek dosyası bulunamadı",
                        warnings=[],
                        engine=None
                    )
            
            self.logger.info(f"📁 Kullanılacak yedek: {backup_path}")
            
            # Yedek dosyasının varlığını kontrol et
            if not os.path.exists(backup_path):
                return FallbackResult(
                    success=False,
                    fallback_type=FallbackType.BACKUP_RESTORE,
                    database_path=None,
                    message=f"Yedek dosyası bulunamadı: {backup_path}",
                    warnings=[],
                    engine=None
                )
            
            # Geçici geri yükleme yolu oluştur
            restore_path = self._create_restore_path()
            
            # Yedek dosyasını kopyala
            if backup_path.endswith('.zip'):
                success = self._extract_compressed_backup(backup_path, restore_path)
            else:
                success = self._copy_simple_backup(backup_path, restore_path)
            
            if not success:
                return FallbackResult(
                    success=False,
                    fallback_type=FallbackType.BACKUP_RESTORE,
                    database_path=None,
                    message="Yedek dosyası kopyalanamadı",
                    warnings=[],
                    engine=None
                )
            
            # Geri yüklenen veritabanını test et
            test_result = self._test_database_integrity(restore_path)
            if not test_result:
                return FallbackResult(
                    success=False,
                    fallback_type=FallbackType.BACKUP_RESTORE,
                    database_path=None,
                    message="Geri yüklenen veritabanı bozuk",
                    warnings=[],
                    engine=None
                )
            
            # SQLAlchemy engine oluştur
            engine = create_engine(
                f'sqlite:///{restore_path}',
                echo=False,
                pool_pre_ping=True,
                poolclass=StaticPool,
                connect_args={
                    'check_same_thread': False,
                    'timeout': 30
                }
            )
            
            # Test bağlantısı
            Session = sessionmaker(bind=engine)
            session = Session()
            from sqlalchemy import text
            result = session.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")).fetchone()
            session.close()
            
            if result and result[0] > 0:
                self.current_fallback_path = restore_path
                self.current_fallback_type = FallbackType.BACKUP_RESTORE
                
                # Yedek bilgilerini al
                backup_info = self._get_backup_info(backup_path)
                
                self.logger.info(f"✅ Yedekten geri yükleme başarılı: {restore_path}")
                
                # Kullanıcıya bildirim gönder
                self._notify_user(
                    title="📁 Yedekten Geri Yüklendi",
                    message=f"Ana veritabanına erişilemiyor. {backup_info.get('date', 'Bilinmeyen tarihli')} yedekten geri yüklendi. Son değişiklikler kaybolmuş olabilir.",
                    notification_type=self.NotificationType.WARNING if self.notification_manager else None,
                    priority=self.NotificationPriority.HIGH if self.notification_manager else None,
                    expires_in_minutes=60,
                    action_text="Veritabanı Durumunu Kontrol Et",
                    data={
                        'fallback_type': 'backup_restore',
                        'backup_path': backup_path,
                        'backup_date': backup_info.get('date'),
                        'primary_db_path': self.primary_db_path,
                        'data_loss_risk': True
                    }
                )
                
                return FallbackResult(
                    success=True,
                    fallback_type=FallbackType.BACKUP_RESTORE,
                    database_path=restore_path,
                    message=f"Yedekten geri yüklendi: {os.path.basename(backup_path)}",
                    warnings=[
                        f"Yedek tarihi: {backup_info.get('date', 'Bilinmiyor')}",
                        "Yedek sonrası değişiklikler kaybolmuş olabilir"
                    ],
                    engine=engine
                )
            else:
                raise Exception("Geri yüklenen veritabanında tablo bulunamadı")
                
        except Exception as e:
            error_msg = f"Yedekten geri yükleme hatası: {e}"
            self.logger.error(f"❌ {error_msg}")
            
            return FallbackResult(
                success=False,
                fallback_type=FallbackType.BACKUP_RESTORE,
                database_path=None,
                message=error_msg,
                warnings=[],
                engine=None
            )
    
    def create_clean_database(self, path: Optional[str] = None) -> FallbackResult:
        """
        Temiz veritabanı oluştur
        
        Args:
            path: Veritabanı yolu (None ise geçici yol kullan)
            
        Returns:
            FallbackResult: Fallback işlem sonucu
        """
        self.logger.info("🆕 Temiz veritabanı oluşturuluyor...")
        
        try:
            # Veritabanı yolunu belirle
            if path is None:
                path = self._create_clean_database_path()
            
            self.logger.info(f"📁 Temiz veritabanı yolu: {path}")
            
            # Mevcut dosyayı sil (varsa)
            if os.path.exists(path):
                try:
                    os.remove(path)
                    self.logger.debug(f"Mevcut dosya silindi: {path}")
                except Exception as e:
                    self.logger.warning(f"Mevcut dosya silinemedi: {e}")
            
            # Dizini oluştur (gerekirse)
            directory = os.path.dirname(path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                self.logger.debug(f"Dizin oluşturuldu: {directory}")
            
            # SQLAlchemy engine oluştur
            engine = create_engine(
                f'sqlite:///{path}',
                echo=False,
                pool_pre_ping=True,
                poolclass=StaticPool,
                connect_args={
                    'check_same_thread': False,
                    'timeout': 30
                }
            )
            
            # Tabloları oluştur
            Base.metadata.create_all(engine)
            
            # Varsayılan verileri ekle
            self._create_default_data(engine)
            
            # Test bağlantısı
            Session = sessionmaker(bind=engine)
            session = Session()
            from sqlalchemy import text
            result = session.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")).fetchone()
            session.close()
            
            if result and result[0] > 0:
                self.current_fallback_path = path
                self.current_fallback_type = FallbackType.CLEAN_DATABASE
                
                self.logger.info(f"✅ Temiz veritabanı başarıyla oluşturuldu: {path}")
                
                # Kullanıcıya bildirim gönder
                self._notify_user(
                    title="🆕 Yeni Veritabanı Oluşturuldu",
                    message="Ana veritabanına erişilemiyor. Temiz bir veritabanı oluşturuldu. Tüm eski veriler kayboldu.",
                    notification_type=self.NotificationType.ERROR if self.notification_manager else None,
                    priority=self.NotificationPriority.CRITICAL if self.notification_manager else None,
                    expires_in_minutes=120,
                    action_text="Yedek Geri Yükle",
                    data={
                        'fallback_type': 'clean_database',
                        'new_db_path': path,
                        'primary_db_path': self.primary_db_path,
                        'data_loss': True,
                        'recovery_possible': True
                    }
                )
                
                return FallbackResult(
                    success=True,
                    fallback_type=FallbackType.CLEAN_DATABASE,
                    database_path=path,
                    message="Temiz veritabanı oluşturuldu",
                    warnings=["Tüm eski veriler kayboldu", "Varsayılan verilerle başlanıyor"],
                    engine=engine
                )
            else:
                raise Exception("Temiz veritabanında tablo oluşturulamadı")
                
        except Exception as e:
            error_msg = f"Temiz veritabanı oluşturma hatası: {e}"
            self.logger.error(f"❌ {error_msg}")
            
            return FallbackResult(
                success=False,
                fallback_type=FallbackType.CLEAN_DATABASE,
                database_path=None,
                message=error_msg,
                warnings=[],
                engine=None
            )
    
    def migrate_data_to_new_location(self, old_path: str, new_path: str) -> Tuple[bool, str]:
        """
        Verileri yeni konuma taşı
        
        Args:
            old_path: Eski veritabanı yolu
            new_path: Yeni veritabanı yolu
            
        Returns:
            Tuple[bool, str]: Başarı durumu ve mesaj
        """
        self.logger.info(f"📦 Veri taşıma başlatılıyor: {old_path} -> {new_path}")
        
        try:
            # Kaynak dosyasının varlığını kontrol et
            if not os.path.exists(old_path):
                return False, f"Kaynak veritabanı bulunamadı: {old_path}"
            
            # Hedef dizini oluştur (gerekirse)
            new_directory = os.path.dirname(new_path)
            if new_directory and not os.path.exists(new_directory):
                os.makedirs(new_directory, exist_ok=True)
                self.logger.debug(f"Hedef dizin oluşturuldu: {new_directory}")
            
            # Hedef dosya varsa yedekle
            if os.path.exists(new_path):
                backup_name = f"{new_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(new_path, backup_name)
                self.logger.info(f"Mevcut dosya yedeklendi: {backup_name}")
            
            # SQLite veritabanını güvenli şekilde kopyala
            source_conn = sqlite3.connect(old_path)
            target_conn = sqlite3.connect(new_path)
            
            # Veritabanını kopyala
            source_conn.backup(target_conn)
            
            # Bağlantıları kapat
            target_conn.close()
            source_conn.close()
            
            # Kopyalanan dosyayı test et
            if self._test_database_integrity(new_path):
                self.logger.info(f"✅ Veri taşıma başarılı: {new_path}")
                
                # Kullanıcıya başarı bildirimi gönder
                self._notify_user(
                    title="✅ Veri Taşıma Tamamlandı",
                    message=f"Veritabanı başarıyla yeni konuma taşındı: {new_path}",
                    notification_type=self.NotificationType.SUCCESS if self.notification_manager else None,
                    priority=self.NotificationPriority.NORMAL if self.notification_manager else None,
                    expires_in_minutes=15,
                    data={
                        'operation': 'data_migration',
                        'old_path': old_path,
                        'new_path': new_path,
                        'success': True
                    }
                )
                
                return True, f"Veriler başarıyla taşındı: {new_path}"
            else:
                return False, "Taşınan veritabanı bozuk"
                
        except Exception as e:
            error_msg = f"Veri taşıma hatası: {e}"
            self.logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    def get_fallback_status(self) -> Dict[str, Any]:
        """
        Mevcut fallback durumunu al
        
        Returns:
            Dict[str, Any]: Fallback durum bilgileri
        """
        return {
            'is_fallback_active': self.current_fallback_path is not None,
            'fallback_type': self.current_fallback_type.value if self.current_fallback_type else None,
            'fallback_path': self.current_fallback_path,
            'primary_db_path': self.primary_db_path,
            'available_backups': len(self._list_available_backups())
        }
    
    def get_user_friendly_status(self) -> Dict[str, Any]:
        """
        Kullanıcı dostu fallback durum bilgisi
        
        Returns:
            Dict[str, Any]: Kullanıcı dostu durum bilgileri
        """
        status = self.get_fallback_status()
        
        if not status['is_fallback_active']:
            return {
                'status': 'normal',
                'title': '✅ Normal Çalışma',
                'message': 'Ana veritabanı kullanılıyor',
                'risk_level': 'none',
                'recommendations': []
            }
        
        fallback_type = status['fallback_type']
        
        if fallback_type == FallbackType.MEMORY_DATABASE.value:
            return {
                'status': 'temporary',
                'title': '⚠️ Geçici Veritabanı',
                'message': 'Bellek içi veritabanı kullanılıyor - veriler kalıcı değil',
                'risk_level': 'high',
                'recommendations': [
                    'Ana veritabanı sorununu çözün',
                    'Önemli verileri kaydedin',
                    'Uygulamayı kapatmadan önce yedek alın'
                ]
            }
        
        elif fallback_type == FallbackType.BACKUP_RESTORE.value:
            return {
                'status': 'restored',
                'title': '📁 Yedekten Geri Yüklendi',
                'message': 'Eski yedek kullanılıyor - son değişiklikler kaybolmuş olabilir',
                'risk_level': 'medium',
                'recommendations': [
                    'Ana veritabanı sorununu çözün',
                    'Kayıp verileri kontrol edin',
                    'Yeni yedek alın'
                ]
            }
        
        elif fallback_type == FallbackType.CLEAN_DATABASE.value:
            return {
                'status': 'new',
                'title': '🆕 Yeni Veritabanı',
                'message': 'Temiz veritabanı oluşturuldu - tüm eski veriler kayboldu',
                'risk_level': 'critical',
                'recommendations': [
                    'Mümkünse yedekten geri yükleyin',
                    'Verileri yeniden girin',
                    'Düzenli yedekleme ayarlayın'
                ]
            }
        
        else:
            return {
                'status': 'unknown',
                'title': '❓ Bilinmeyen Durum',
                'message': 'Fallback durumu belirlenemiyor',
                'risk_level': 'unknown',
                'recommendations': ['Sistem yöneticisine başvurun']
            }
    
    def _find_latest_backup(self) -> Optional[str]:
        """En son yedeği bul"""
        try:
            backup_files = []
            
            # Yedek dosyalarını bul
            for backup_file in self.backup_dir.glob("tezgah_takip_backup_*"):
                if backup_file.is_file():
                    backup_files.append({
                        'path': str(backup_file),
                        'mtime': backup_file.stat().st_mtime
                    })
            
            if not backup_files:
                self.logger.warning("Hiç yedek dosyası bulunamadı")
                return None
            
            # En son yedeği bul
            latest_backup = max(backup_files, key=lambda x: x['mtime'])
            self.logger.info(f"En son yedek bulundu: {latest_backup['path']}")
            
            return latest_backup['path']
            
        except Exception as e:
            self.logger.error(f"En son yedek bulma hatası: {e}")
            return None
    
    def _list_available_backups(self) -> List[str]:
        """Mevcut yedekleri listele"""
        try:
            backups = []
            for backup_file in self.backup_dir.glob("tezgah_takip_backup_*"):
                if backup_file.is_file():
                    backups.append(str(backup_file))
            return sorted(backups, reverse=True)  # En yeni önce
        except Exception:
            return []
    
    def _create_restore_path(self) -> str:
        """Geri yükleme için geçici yol oluştur"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"tezgah_takip_restored_{timestamp}.db"
    
    def _create_clean_database_path(self) -> str:
        """Temiz veritabanı için yol oluştur"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"tezgah_takip_clean_{timestamp}.db"
    
    def _extract_compressed_backup(self, backup_path: str, restore_path: str) -> bool:
        """Sıkıştırılmış yedeği çıkart"""
        try:
            import zipfile
            
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Veritabanı dosyasını bul
                db_files = [f for f in zipf.namelist() if f.endswith('.db')]
                
                if not db_files:
                    self.logger.error("Zip dosyasında veritabanı bulunamadı")
                    return False
                
                # İlk veritabanı dosyasını çıkart
                db_file = db_files[0]
                with zipf.open(db_file) as source, open(restore_path, 'wb') as target:
                    shutil.copyfileobj(source, target)
                
                self.logger.debug(f"Sıkıştırılmış yedek çıkartıldı: {db_file} -> {restore_path}")
                return True
                
        except Exception as e:
            self.logger.error(f"Sıkıştırılmış yedek çıkartma hatası: {e}")
            return False
    
    def _copy_simple_backup(self, backup_path: str, restore_path: str) -> bool:
        """Basit yedeği kopyala"""
        try:
            shutil.copy2(backup_path, restore_path)
            self.logger.debug(f"Basit yedek kopyalandı: {backup_path} -> {restore_path}")
            return True
        except Exception as e:
            self.logger.error(f"Basit yedek kopyalama hatası: {e}")
            return False
    
    def _test_database_integrity(self, db_path: str) -> bool:
        """Veritabanı bütünlüğünü test et"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # PRAGMA integrity_check
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            
            conn.close()
            
            is_ok = result and result[0] == 'ok'
            self.logger.debug(f"Veritabanı bütünlük kontrolü: {db_path} -> {is_ok}")
            
            return is_ok
            
        except Exception as e:
            self.logger.error(f"Veritabanı bütünlük testi hatası: {e}")
            return False
    
    def _get_backup_info(self, backup_path: str) -> Dict[str, Any]:
        """Yedek dosyası bilgilerini al"""
        try:
            stat = os.stat(backup_path)
            return {
                'path': backup_path,
                'size': stat.st_size,
                'date': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'type': 'compressed' if backup_path.endswith('.zip') else 'simple'
            }
        except Exception:
            return {'path': backup_path, 'date': 'Bilinmiyor', 'size': 0, 'type': 'unknown'}
    
    def create_alternative_database(self, alternative_paths: Optional[List[str]] = None) -> FallbackResult:
        """
        Alternatif konumda veritabanı oluştur
        
        Args:
            alternative_paths: Alternatif yol listesi (None ise otomatik belirle)
            
        Returns:
            FallbackResult: Fallback işlem sonucu
        """
        self.logger.info("🔄 Alternatif konumda veritabanı oluşturuluyor...")
        
        try:
            # Alternatif yolları belirle
            if alternative_paths is None:
                alternative_paths = self._get_alternative_paths()
            
            for alt_path in alternative_paths:
                try:
                    self.logger.info(f"📁 Alternatif yol deneniyor: {alt_path}")
                    
                    # Dizini oluştur (gerekirse)
                    directory = os.path.dirname(alt_path)
                    if directory and not os.path.exists(directory):
                        os.makedirs(directory, exist_ok=True)
                        self.logger.debug(f"Alternatif dizin oluşturuldu: {directory}")
                    
                    # Yazma izni kontrol et
                    if not os.access(directory, os.W_OK):
                        self.logger.warning(f"Yazma izni yok: {directory}")
                        continue
                    
                    # Mevcut dosyayı sil (varsa)
                    if os.path.exists(alt_path):
                        try:
                            os.remove(alt_path)
                        except Exception as e:
                            self.logger.warning(f"Mevcut dosya silinemedi: {e}")
                            continue
                    
                    # SQLAlchemy engine oluştur
                    engine = create_engine(
                        f'sqlite:///{alt_path}',
                        echo=False,
                        pool_pre_ping=True,
                        poolclass=StaticPool,
                        connect_args={
                            'check_same_thread': False,
                            'timeout': 30
                        }
                    )
                    
                    # Tabloları oluştur
                    Base.metadata.create_all(engine)
                    
                    # Varsayılan verileri ekle
                    self._create_default_data(engine)
                    
                    # Test bağlantısı
                    Session = sessionmaker(bind=engine)
                    session = Session()
                    from sqlalchemy import text
                    result = session.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")).fetchone()
                    session.close()
                    
                    if result and result[0] > 0:
                        self.current_fallback_path = alt_path
                        self.current_fallback_type = FallbackType.ALTERNATIVE_LOCATION
                        
                        self.logger.info(f"✅ Alternatif veritabanı başarıyla oluşturuldu: {alt_path}")
                        
                        # Kullanıcıya bildirim gönder
                        self._notify_user(
                            title="📁 Alternatif Konum Kullanılıyor",
                            message=f"Ana veritabanına erişilemiyor. Alternatif konumda yeni veritabanı oluşturuldu: {alt_path}",
                            notification_type=self.NotificationType.WARNING if self.notification_manager else None,
                            priority=self.NotificationPriority.HIGH if self.notification_manager else None,
                            expires_in_minutes=60,
                            data={
                                'fallback_type': 'alternative_location',
                                'alternative_path': alt_path,
                                'primary_db_path': self.primary_db_path,
                                'data_loss': True
                            }
                        )
                        
                        return FallbackResult(
                            success=True,
                            fallback_type=FallbackType.ALTERNATIVE_LOCATION,
                            database_path=alt_path,
                            message=f"Alternatif konumda veritabanı oluşturuldu: {alt_path}",
                            warnings=["Eski veriler kayboldu", "Alternatif konum kullanılıyor"],
                            engine=engine
                        )
                    else:
                        raise Exception("Alternatif veritabanında tablo oluşturulamadı")
                        
                except Exception as e:
                    self.logger.warning(f"Alternatif yol başarısız: {alt_path} - {e}")
                    continue
            
            # Tüm alternatif yollar başarısız
            error_msg = "Tüm alternatif konumlar başarısız oldu"
            self.logger.error(f"❌ {error_msg}")
            
            return FallbackResult(
                success=False,
                fallback_type=FallbackType.ALTERNATIVE_LOCATION,
                database_path=None,
                message=error_msg,
                warnings=[],
                engine=None
            )
            
        except Exception as e:
            error_msg = f"Alternatif veritabanı oluşturma hatası: {e}"
            self.logger.error(f"❌ {error_msg}")
            
            return FallbackResult(
                success=False,
                fallback_type=FallbackType.ALTERNATIVE_LOCATION,
                database_path=None,
                message=error_msg,
                warnings=[],
                engine=None
            )
    
    def get_available_options(self) -> List[Dict[str, Any]]:
        """
        Mevcut fallback seçeneklerini al
        
        Returns:
            List[Dict[str, Any]]: Fallback seçenekleri listesi
        """
        options = []
        
        try:
            # 1. Yedekten geri yükleme seçenekleri
            available_backups = self._list_available_backups()
            if available_backups:
                for backup_path in available_backups[:5]:  # En son 5 yedek
                    backup_info = self._get_backup_info(backup_path)
                    options.append({
                        'type': 'backup_restore',
                        'title': f"Yedekten Geri Yükle ({backup_info['date']})",
                        'description': f"Boyut: {backup_info['size']} bytes",
                        'path': backup_path,
                        'risk_level': 'medium',
                        'data_loss': 'partial'
                    })
            
            # 2. Alternatif konum seçenekleri
            alternative_paths = self._get_alternative_paths()
            for alt_path in alternative_paths[:3]:  # İlk 3 alternatif
                options.append({
                    'type': 'alternative_location',
                    'title': f"Alternatif Konum: {os.path.dirname(alt_path)}",
                    'description': f"Yeni veritabanı: {os.path.basename(alt_path)}",
                    'path': alt_path,
                    'risk_level': 'high',
                    'data_loss': 'complete'
                })
            
            # 3. Temiz veritabanı seçeneği
            options.append({
                'type': 'clean_database',
                'title': 'Temiz Veritabanı Oluştur',
                'description': 'Tüm veriler silinir, sıfırdan başlanır',
                'path': self._create_clean_database_path(),
                'risk_level': 'critical',
                'data_loss': 'complete'
            })
            
            # 4. Bellek içi veritabanı seçeneği
            options.append({
                'type': 'memory_database',
                'title': 'Geçici Bellek Veritabanı',
                'description': 'Veriler geçici - uygulama kapandığında kaybolur',
                'path': ':memory:',
                'risk_level': 'critical',
                'data_loss': 'temporary'
            })
            
            self.logger.debug(f"Mevcut fallback seçenekleri: {len(options)} adet")
            return options
            
        except Exception as e:
            self.logger.error(f"Fallback seçenekleri alma hatası: {e}")
            return []
    
    def cleanup_old_backups(self, days_to_keep: int = 30):
        """
        Eski yedekleri temizle
        
        Args:
            days_to_keep: Kaç günlük yedek saklanacak
        """
        self.logger.info(f"🧹 Eski yedekler temizleniyor (>{days_to_keep} gün)")
        
        try:
            cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            cleaned_count = 0
            
            # Yedek dosyalarını kontrol et
            for backup_file in self.backup_dir.glob("tezgah_takip_backup_*"):
                try:
                    if backup_file.is_file():
                        file_time = backup_file.stat().st_mtime
                        
                        if file_time < cutoff_time:
                            backup_file.unlink()
                            cleaned_count += 1
                            self.logger.debug(f"Eski yedek silindi: {backup_file}")
                            
                except Exception as e:
                    self.logger.warning(f"Yedek dosyası silinemedi {backup_file}: {e}")
            
            # Geçici fallback dosyalarını temizle
            for temp_file in Path(".").glob("tezgah_takip_*_*.db"):
                try:
                    if temp_file.is_file():
                        file_time = temp_file.stat().st_mtime
                        
                        if file_time < cutoff_time:
                            temp_file.unlink()
                            cleaned_count += 1
                            self.logger.debug(f"Geçici dosya silindi: {temp_file}")
                            
                except Exception as e:
                    self.logger.warning(f"Geçici dosya silinemedi {temp_file}: {e}")
            
            self.logger.info(f"✅ Temizlik tamamlandı: {cleaned_count} dosya silindi")
            
        except Exception as e:
            self.logger.error(f"❌ Yedek temizleme hatası: {e}")
    
    def _get_alternative_paths(self) -> List[str]:
        """Alternatif veritabanı yolları al"""
        alternative_paths = []
        
        try:
            # 1. Kullanıcı temp dizini
            user_temp = tempfile.gettempdir()
            alternative_paths.append(os.path.join(user_temp, "tezgah_takip_alt.db"))
            
            # 2. Kullanıcı home dizini
            home_dir = Path.home()
            alternative_paths.append(str(home_dir / "tezgah_takip_alt.db"))
            
            # 3. Mevcut dizin
            alternative_paths.append("tezgah_takip_alt.db")
            
            # 4. AppData (Windows) veya .local (Linux/Mac)
            if os.name == 'nt':  # Windows
                appdata = os.environ.get('APPDATA')
                if appdata:
                    app_dir = os.path.join(appdata, "TezgahTakip")
                    os.makedirs(app_dir, exist_ok=True)
                    alternative_paths.append(os.path.join(app_dir, "tezgah_takip_alt.db"))
            else:  # Linux/Mac
                local_dir = home_dir / ".local" / "share" / "TezgahTakip"
                local_dir.mkdir(parents=True, exist_ok=True)
                alternative_paths.append(str(local_dir / "tezgah_takip_alt.db"))
            
            # 5. Desktop (son çare)
            desktop = home_dir / "Desktop"
            if desktop.exists():
                alternative_paths.append(str(desktop / "tezgah_takip_alt.db"))
            
            self.logger.debug(f"Alternatif yollar: {alternative_paths}")
            return alternative_paths
            
        except Exception as e:
            self.logger.error(f"Alternatif yol belirleme hatası: {e}")
            return ["tezgah_takip_alt.db"]  # Fallback
    
    def _create_default_data(self, engine):
        """Temiz veritabanı için varsayılan verileri oluştur"""
        try:
            from database_models import Kullanici, Ayar
            
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Varsayılan kullanıcı
            admin_user = Kullanici(
                kullanici_adi='admin',
                ad_soyad='Sistem Yöneticisi',
                email='admin@tezgahtakip.com',
                rol='Admin',
                aktif=True
            )
            session.add(admin_user)
            
            # Varsayılan ayarlar
            default_settings = [
                ('bakim_uyari_gun', '7', 'Bakım uyarısı kaç gün önceden verilsin', 'Bakım'),
                ('pil_uyari_gun', '30', 'Pil uyarısı kaç gün önceden verilsin', 'Pil'),
                ('otomatik_yedekleme', 'true', 'Otomatik yedekleme aktif mi', 'Sistem'),
                ('yedekleme_periyodu', '7', 'Yedekleme periyodu (gün)', 'Sistem'),
                ('tema', 'dark', 'Uygulama teması', 'Görünüm'),
                ('dil', 'tr', 'Uygulama dili', 'Görünüm')
            ]
            
            for anahtar, deger, aciklama, kategori in default_settings:
                ayar = Ayar(
                    anahtar=anahtar,
                    deger=deger,
                    aciklama=aciklama,
                    kategori=kategori
                )
                session.add(ayar)
            
            session.commit()
            session.close()
            
            self.logger.debug("Varsayılan veriler oluşturuldu")
            
        except Exception as e:
            self.logger.error(f"Varsayılan veri oluşturma hatası: {e}")