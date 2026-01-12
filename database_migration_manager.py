#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Database Migration Manager
Veritabanı migration araçları - veri taşıma, yedek doğrulama, rollback yetenekleri
"""

import os
import shutil
import sqlite3
import logging
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from database_error_models import DatabaseStatus, FallbackType, ErrorSeverity
from database_integrity_checker import DatabaseIntegrityChecker
from automatic_retry_manager import AutomaticRetryManager, retry_database_operation

class MigrationType(Enum):
    """Migration türleri"""
    FULL_COPY = "full_copy"
    INCREMENTAL = "incremental"
    SCHEMA_ONLY = "schema_only"
    DATA_ONLY = "data_only"

class MigrationStatus(Enum):
    """Migration durumları"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

@dataclass
class MigrationPlan:
    """Migration planı"""
    migration_id: str
    source_path: str
    target_path: str
    migration_type: MigrationType
    backup_before: bool
    verify_after: bool
    rollback_enabled: bool
    estimated_size: int
    estimated_duration: float
    created_at: datetime

@dataclass
class MigrationResult:
    """Migration sonucu"""
    migration_id: str
    status: MigrationStatus
    success: bool
    source_path: str
    target_path: str
    backup_path: Optional[str]
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: float
    records_migrated: int
    data_size_bytes: int
    checksum_source: str
    checksum_target: str
    error_message: Optional[str]
    warnings: List[str]

class DatabaseMigrationManager:
    """
    Veritabanı migration yöneticisi
    
    Özellikler:
    - Veritabanları arası veri taşıma
    - Migration öncesi yedekleme
    - Veri bütünlük doğrulama
    - Rollback yetenekleri
    - İlerleme takibi
    """
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Migration Manager başlat
        
        Args:
            temp_dir: Geçici dosyalar için dizin
        """
        self.logger = logging.getLogger(__name__)
        self.temp_dir = temp_dir or os.path.join(os.getcwd(), "temp_migrations")
        self.retry_manager = AutomaticRetryManager(max_retries=3, base_delay=1.0, max_delay=30.0)
        
        # Migration geçmişi
        self.migration_history: List[MigrationResult] = []
        
        # Temp dizini oluştur
        os.makedirs(self.temp_dir, exist_ok=True)
        
        self.logger.info(f"🚀 Database Migration Manager başlatıldı: {self.temp_dir}")
    
    def create_migration_plan(self, 
                            source_path: str, 
                            target_path: str,
                            migration_type: MigrationType = MigrationType.FULL_COPY,
                            backup_before: bool = True,
                            verify_after: bool = True,
                            rollback_enabled: bool = True) -> MigrationPlan:
        """
        Migration planı oluştur
        
        Args:
            source_path: Kaynak veritabanı yolu
            target_path: Hedef veritabanı yolu
            migration_type: Migration türü
            backup_before: Migration öncesi yedekleme
            verify_after: Migration sonrası doğrulama
            rollback_enabled: Rollback desteği
            
        Returns:
            MigrationPlan: Migration planı
        """
        migration_id = self._generate_migration_id()
        
        # Kaynak veritabanı analizi
        estimated_size = 0
        estimated_duration = 0.0
        
        try:
            if os.path.exists(source_path):
                estimated_size = os.path.getsize(source_path)
                # Basit duration tahmini (MB başına ~2 saniye)
                estimated_duration = max(5.0, (estimated_size / (1024 * 1024)) * 2.0)
            
        except Exception as e:
            self.logger.warning(f"⚠️ Kaynak analizi hatası: {e}")
        
        plan = MigrationPlan(
            migration_id=migration_id,
            source_path=source_path,
            target_path=target_path,
            migration_type=migration_type,
            backup_before=backup_before,
            verify_after=verify_after,
            rollback_enabled=rollback_enabled,
            estimated_size=estimated_size,
            estimated_duration=estimated_duration,
            created_at=datetime.now(timezone.utc)
        )
        
        self.logger.info(f"📋 Migration planı oluşturuldu: {migration_id}")
        self.logger.info(f"   Kaynak: {source_path}")
        self.logger.info(f"   Hedef: {target_path}")
        self.logger.info(f"   Tür: {migration_type.value}")
        self.logger.info(f"   Tahmini boyut: {estimated_size / (1024*1024):.1f} MB")
        self.logger.info(f"   Tahmini süre: {estimated_duration:.1f} saniye")
        
        return plan
    
    def execute_migration(self, plan: MigrationPlan) -> MigrationResult:
        """
        Migration planını çalıştır
        
        Args:
            plan: Migration planı
            
        Returns:
            MigrationResult: Migration sonucu
        """
        start_time = datetime.now(timezone.utc)
        
        self.logger.info(f"🚀 Migration başlatılıyor: {plan.migration_id}")
        
        result = MigrationResult(
            migration_id=plan.migration_id,
            status=MigrationStatus.IN_PROGRESS,
            success=False,
            source_path=plan.source_path,
            target_path=plan.target_path,
            backup_path=None,
            start_time=start_time,
            end_time=None,
            duration_seconds=0.0,
            records_migrated=0,
            data_size_bytes=0,
            checksum_source="",
            checksum_target="",
            error_message=None,
            warnings=[]
        )
        
        try:
            # 1. Ön kontroller
            self._validate_migration_preconditions(plan, result)
            
            # 2. Yedekleme (gerekirse)
            if plan.backup_before:
                result.backup_path = self._create_backup_before_migration(plan, result)
            
            # 3. Kaynak checksum
            result.checksum_source = self._calculate_database_checksum(plan.source_path)
            
            # 4. Migration işlemi
            if plan.migration_type == MigrationType.FULL_COPY:
                self._execute_full_copy_migration(plan, result)
            elif plan.migration_type == MigrationType.INCREMENTAL:
                self._execute_incremental_migration(plan, result)
            elif plan.migration_type == MigrationType.SCHEMA_ONLY:
                self._execute_schema_only_migration(plan, result)
            elif plan.migration_type == MigrationType.DATA_ONLY:
                self._execute_data_only_migration(plan, result)
            
            # 5. Hedef checksum
            result.checksum_target = self._calculate_database_checksum(plan.target_path)
            
            # 6. Doğrulama (gerekirse)
            if plan.verify_after:
                self._verify_migration_integrity(plan, result)
            
            # 7. Başarılı tamamlama
            result.status = MigrationStatus.COMPLETED
            result.success = True
            result.end_time = datetime.now(timezone.utc)
            result.duration_seconds = (result.end_time - result.start_time).total_seconds()
            
            self.logger.info(f"✅ Migration başarıyla tamamlandı: {plan.migration_id}")
            self.logger.info(f"   Süre: {result.duration_seconds:.2f} saniye")
            self.logger.info(f"   Kayıt sayısı: {result.records_migrated}")
            self.logger.info(f"   Veri boyutu: {result.data_size_bytes / (1024*1024):.1f} MB")
            
        except Exception as e:
            result.status = MigrationStatus.FAILED
            result.success = False
            result.error_message = str(e)
            result.end_time = datetime.now(timezone.utc)
            result.duration_seconds = (result.end_time - result.start_time).total_seconds()
            
            self.logger.error(f"❌ Migration başarısız: {plan.migration_id} - {e}")
            
            # Rollback dene (eğer etkinse)
            if plan.rollback_enabled and result.backup_path:
                try:
                    self.rollback_migration(result)
                except Exception as rollback_error:
                    self.logger.error(f"❌ Rollback başarısız: {rollback_error}")
                    result.warnings.append(f"Rollback başarısız: {rollback_error}")
        
        # Geçmişe ekle
        self.migration_history.append(result)
        
        return result
    
    def _validate_migration_preconditions(self, plan: MigrationPlan, result: MigrationResult):
        """Migration ön koşullarını kontrol et"""
        self.logger.info("🔍 Migration ön koşulları kontrol ediliyor...")
        
        # Kaynak dosya kontrolü
        if not os.path.exists(plan.source_path):
            raise FileNotFoundError(f"Kaynak veritabanı bulunamadı: {plan.source_path}")
        
        if not os.access(plan.source_path, os.R_OK):
            raise PermissionError(f"Kaynak veritabanı okuma izni yok: {plan.source_path}")
        
        # Hedef dizin kontrolü
        target_dir = os.path.dirname(plan.target_path)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
            result.warnings.append(f"Hedef dizin oluşturuldu: {target_dir}")
        
        if not os.access(target_dir, os.W_OK):
            raise PermissionError(f"Hedef dizin yazma izni yok: {target_dir}")
        
        # Hedef dosya varsa kontrol et
        if os.path.exists(plan.target_path):
            if not os.access(plan.target_path, os.W_OK):
                raise PermissionError(f"Hedef veritabanı yazma izni yok: {plan.target_path}")
            result.warnings.append(f"Mevcut hedef dosya üzerine yazılacak: {plan.target_path}")
        
        # Disk alanı kontrolü
        source_size = os.path.getsize(plan.source_path)
        free_space = shutil.disk_usage(target_dir).free
        
        # En az 2x kaynak boyutu kadar alan gerekli (yedek + hedef)
        required_space = source_size * 2
        if free_space < required_space:
            raise OSError(f"Yetersiz disk alanı. Gerekli: {required_space/(1024*1024):.1f} MB, Mevcut: {free_space/(1024*1024):.1f} MB")
        
        self.logger.info("✅ Migration ön koşulları uygun")
    
    def _create_backup_before_migration(self, plan: MigrationPlan, result: MigrationResult) -> str:
        """Migration öncesi yedek oluştur"""
        self.logger.info("💾 Migration öncesi yedek oluşturuluyor...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_before_migration_{plan.migration_id}_{timestamp}.db"
        backup_path = os.path.join(self.temp_dir, backup_filename)
        
        def backup_operation():
            shutil.copy2(plan.source_path, backup_path)
            return backup_path
        
        # Retry ile yedekleme
        retry_result = self.retry_manager.retry_with_backoff(
            backup_operation,
            retry_on_exceptions=(OSError, PermissionError)
        )
        
        if not retry_result.success:
            raise Exception(f"Yedekleme başarısız: {retry_result.error}")
        
        # Yedek doğrulama
        if not os.path.exists(backup_path):
            raise Exception("Yedek dosyası oluşturulamadı")
        
        backup_size = os.path.getsize(backup_path)
        source_size = os.path.getsize(plan.source_path)
        
        if backup_size != source_size:
            raise Exception(f"Yedek boyutu uyuşmuyor. Kaynak: {source_size}, Yedek: {backup_size}")
        
        self.logger.info(f"✅ Yedek oluşturuldu: {backup_path}")
        return backup_path
    
    def _calculate_database_checksum(self, db_path: str) -> str:
        """Veritabanı checksum hesapla"""
        try:
            hasher = hashlib.md5()
            
            with open(db_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            
            checksum = hasher.hexdigest()
            self.logger.debug(f"Checksum hesaplandı: {db_path} -> {checksum}")
            return checksum
            
        except Exception as e:
            self.logger.warning(f"⚠️ Checksum hesaplama hatası: {e}")
            return ""
    
    def _execute_full_copy_migration(self, plan: MigrationPlan, result: MigrationResult):
        """Tam kopya migration"""
        self.logger.info("📋 Tam kopya migration çalıştırılıyor...")
        
        def copy_operation():
            shutil.copy2(plan.source_path, plan.target_path)
            return True
        
        # Retry ile kopyalama
        retry_result = self.retry_manager.retry_with_backoff(
            copy_operation,
            retry_on_exceptions=(OSError, PermissionError)
        )
        
        if not retry_result.success:
            raise Exception(f"Dosya kopyalama başarısız: {retry_result.error}")
        
        # İstatistikleri güncelle
        result.data_size_bytes = os.path.getsize(plan.target_path)
        result.records_migrated = self._count_database_records(plan.target_path)
        
        self.logger.info("✅ Tam kopya migration tamamlandı")
    
    def _execute_incremental_migration(self, plan: MigrationPlan, result: MigrationResult):
        """Artımlı migration"""
        self.logger.info("📈 Artımlı migration çalıştırılıyor...")
        
        # Bu implementasyon için basit: tam kopya yap
        # Gerçek implementasyonda timestamp/ID bazlı artımlı sync olabilir
        self._execute_full_copy_migration(plan, result)
        result.warnings.append("Artımlı migration tam kopya olarak gerçekleştirildi")
    
    def _execute_schema_only_migration(self, plan: MigrationPlan, result: MigrationResult):
        """Sadece şema migration"""
        self.logger.info("🏗️ Şema migration çalıştırılıyor...")
        
        # Kaynak şemayı al
        schema_sql = self._extract_database_schema(plan.source_path)
        
        # Hedef veritabanını oluştur
        self._create_database_with_schema(plan.target_path, schema_sql)
        
        result.data_size_bytes = os.path.getsize(plan.target_path)
        result.records_migrated = 0  # Sadece şema, veri yok
        
        self.logger.info("✅ Şema migration tamamlandı")
    
    def _execute_data_only_migration(self, plan: MigrationPlan, result: MigrationResult):
        """Sadece veri migration"""
        self.logger.info("📊 Veri migration çalıştırılıyor...")
        
        # Hedef veritabanının var olduğunu kontrol et
        if not os.path.exists(plan.target_path):
            raise Exception("Veri migration için hedef veritabanı mevcut olmalı")
        
        # Veri transferi
        records_migrated = self._transfer_database_data(plan.source_path, plan.target_path)
        
        result.data_size_bytes = os.path.getsize(plan.target_path)
        result.records_migrated = records_migrated
        
        self.logger.info("✅ Veri migration tamamlandı")
    
    def _extract_database_schema(self, db_path: str) -> str:
        """Veritabanı şemasını çıkar"""
        schema_sql = ""
        
        def extract_operation():
            nonlocal schema_sql
            conn = sqlite3.connect(db_path)
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL")
                tables = cursor.fetchall()
                
                schema_parts = []
                for table in tables:
                    if table[0]:
                        schema_parts.append(table[0] + ";")
                
                schema_sql = "\n".join(schema_parts)
                return schema_sql
                
            finally:
                conn.close()
        
        retry_result = retry_database_operation(extract_operation)
        if not retry_result.success:
            raise Exception(f"Şema çıkarma başarısız: {retry_result.error}")
        
        return schema_sql
    
    def _create_database_with_schema(self, db_path: str, schema_sql: str):
        """Şema ile veritabanı oluştur"""
        def create_operation():
            # Hedef dosyayı sil (varsa)
            if os.path.exists(db_path):
                os.remove(db_path)
            
            conn = sqlite3.connect(db_path)
            try:
                cursor = conn.cursor()
                # Şema SQL'ini satır satır çalıştır
                for statement in schema_sql.split(';'):
                    statement = statement.strip()
                    if statement:
                        cursor.execute(statement)
                conn.commit()
                return True
            finally:
                conn.close()
        
        retry_result = retry_database_operation(create_operation)
        if not retry_result.success:
            raise Exception(f"Şema oluşturma başarısız: {retry_result.error}")
    
    def _transfer_database_data(self, source_path: str, target_path: str) -> int:
        """Veritabanları arası veri transferi"""
        total_records = 0
        
        def transfer_operation():
            nonlocal total_records
            
            source_conn = sqlite3.connect(source_path)
            target_conn = sqlite3.connect(target_path)
            
            try:
                source_cursor = source_conn.cursor()
                target_cursor = target_conn.cursor()
                
                # Tablo listesini al
                source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = source_cursor.fetchall()
                
                for table_name in tables:
                    table_name = table_name[0]
                    
                    # Kaynak tablodan veri al
                    source_cursor.execute(f"SELECT * FROM {table_name}")
                    rows = source_cursor.fetchall()
                    
                    if rows:
                        # Hedef tabloya veri ekle
                        placeholders = ",".join(["?" for _ in range(len(rows[0]))])
                        target_cursor.executemany(
                            f"INSERT OR REPLACE INTO {table_name} VALUES ({placeholders})",
                            rows
                        )
                        total_records += len(rows)
                
                target_conn.commit()
                return total_records
                
            finally:
                source_conn.close()
                target_conn.close()
        
        retry_result = retry_database_operation(transfer_operation)
        if not retry_result.success:
            raise Exception(f"Veri transferi başarısız: {retry_result.error}")
        
        return total_records
    
    def _count_database_records(self, db_path: str) -> int:
        """Veritabanındaki toplam kayıt sayısını say"""
        total_records = 0
        
        try:
            def count_operation():
                nonlocal total_records
                conn = sqlite3.connect(db_path)
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    
                    for table_name in tables:
                        table_name = table_name[0]
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]
                        total_records += count
                    
                    return total_records
                finally:
                    conn.close()
            
            retry_result = retry_database_operation(count_operation)
            if retry_result.success:
                total_records = retry_result.result
                
        except Exception as e:
            self.logger.warning(f"⚠️ Kayıt sayma hatası: {e}")
        
        return total_records
    
    def _verify_migration_integrity(self, plan: MigrationPlan, result: MigrationResult):
        """Migration bütünlük doğrulaması"""
        self.logger.info("🔍 Migration bütünlük doğrulaması...")
        
        # Hedef dosya varlık kontrolü
        if not os.path.exists(plan.target_path):
            raise Exception("Hedef veritabanı dosyası bulunamadı")
        
        # Boyut kontrolü (tam kopya için)
        if plan.migration_type == MigrationType.FULL_COPY:
            source_size = os.path.getsize(plan.source_path)
            target_size = os.path.getsize(plan.target_path)
            
            if source_size != target_size:
                raise Exception(f"Dosya boyutları uyuşmuyor. Kaynak: {source_size}, Hedef: {target_size}")
        
        # Checksum kontrolü
        if result.checksum_source and result.checksum_target:
            if plan.migration_type == MigrationType.FULL_COPY:
                if result.checksum_source != result.checksum_target:
                    raise Exception("Checksum uyuşmazlığı tespit edildi")
        
        # Veritabanı bütünlük kontrolü
        integrity_checker = DatabaseIntegrityChecker(plan.target_path)
        integrity_result = integrity_checker.check_database_integrity(create_backup=False)
        
        if not integrity_result.is_valid:
            raise Exception(f"Hedef veritabanı bütünlük kontrolü başarısız: {integrity_result.error_details}")
        
        self.logger.info("✅ Migration bütünlük doğrulaması başarılı")
    
    def rollback_migration(self, migration_result: MigrationResult) -> bool:
        """Migration'ı geri al"""
        try:
            self.logger.info(f"🔄 Migration rollback başlatılıyor: {migration_result.migration_id}")
            
            if not migration_result.backup_path or not os.path.exists(migration_result.backup_path):
                raise Exception("Rollback için yedek dosyası bulunamadı")
            
            # Yedekten geri yükle
            def rollback_operation():
                shutil.copy2(migration_result.backup_path, migration_result.target_path)
                return True
            
            retry_result = self.retry_manager.retry_with_backoff(
                rollback_operation,
                retry_on_exceptions=(OSError, PermissionError)
            )
            
            if not retry_result.success:
                raise Exception(f"Rollback kopyalama başarısız: {retry_result.error}")
            
            # Durumu güncelle
            migration_result.status = MigrationStatus.ROLLED_BACK
            
            self.logger.info(f"✅ Migration rollback başarılı: {migration_result.migration_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Migration rollback başarısız: {e}")
            return False
    
    def get_migration_history(self) -> List[MigrationResult]:
        """Migration geçmişini al"""
        return self.migration_history.copy()
    
    def cleanup_migration_files(self, days_to_keep: int = 7):
        """Eski migration dosyalarını temizle"""
        try:
            self.logger.info(f"🧹 Migration dosyaları temizleniyor: {days_to_keep} gün")
            
            cutoff_time = datetime.now() - timedelta(days=days_to_keep)
            cleaned_count = 0
            
            for filename in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, filename)
                
                if os.path.isfile(file_path):
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        cleaned_count += 1
                        self.logger.debug(f"Temizlendi: {filename}")
            
            self.logger.info(f"✅ {cleaned_count} migration dosyası temizlendi")
            
        except Exception as e:
            self.logger.error(f"❌ Migration temizleme hatası: {e}")
    
    def _generate_migration_id(self) -> str:
        """Benzersiz migration ID oluştur"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        import uuid
        short_uuid = str(uuid.uuid4())[:8]
        return f"migration_{timestamp}_{short_uuid}"
    
    def get_migration_statistics(self) -> Dict[str, Any]:
        """Migration istatistikleri"""
        if not self.migration_history:
            return {
                'total_migrations': 0,
                'successful_migrations': 0,
                'failed_migrations': 0,
                'rolled_back_migrations': 0,
                'success_rate': 0.0,
                'average_duration': 0.0,
                'total_data_migrated_mb': 0.0
            }
        
        successful = [m for m in self.migration_history if m.success]
        failed = [m for m in self.migration_history if not m.success]
        rolled_back = [m for m in self.migration_history if m.status == MigrationStatus.ROLLED_BACK]
        
        total_duration = sum(m.duration_seconds for m in self.migration_history if m.duration_seconds > 0)
        total_data = sum(m.data_size_bytes for m in self.migration_history)
        
        return {
            'total_migrations': len(self.migration_history),
            'successful_migrations': len(successful),
            'failed_migrations': len(failed),
            'rolled_back_migrations': len(rolled_back),
            'success_rate': (len(successful) / len(self.migration_history)) * 100,
            'average_duration': total_duration / len(self.migration_history) if self.migration_history else 0.0,
            'total_data_migrated_mb': total_data / (1024 * 1024)
        }