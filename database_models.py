#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Veritabanı Modelleri
SQLAlchemy ORM modelleri
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, validates
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
import os
import re
import logging
from contextlib import contextmanager
import re
from sqlalchemy import event
from sqlalchemy.pool import StaticPool

Base = declarative_base()

# Validation functions
def validate_tezgah_numarasi(numarasi):
    """Tezgah numarası format kontrolü"""
    if not numarasi:
        raise ValueError("Tezgah numarası boş olamaz")
    
    # Sadece alfanumerik ve tire/alt çizgi
    if not re.match(r'^[A-Za-z0-9_-]{2,20}$', numarasi):
        raise ValueError("Tezgah numarası sadece harf, rakam, tire ve alt çizgi içerebilir (2-20 karakter)")
    
    return numarasi.upper()

def validate_text_field(text, field_name, min_len=1, max_len=255):
    """Metin alanı validasyonu"""
    if text and len(text.strip()) < min_len:
        raise ValueError(f"{field_name} en az {min_len} karakter olmalı")
    
    if text and len(text.strip()) > max_len:
        raise ValueError(f"{field_name} en fazla {max_len} karakter olabilir")
    
    # Tehlikeli karakterleri temizle
    if text:
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
        for char in dangerous_chars:
            if char in text:
                raise ValueError(f"{field_name} geçersiz karakter içeriyor: {char}")
    
    return text.strip() if text else None

Base = declarative_base()

class Tezgah(Base):
    """Tezgah tablosu"""
    __tablename__ = 'tezgah'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    numarasi = Column(String(50), nullable=False, unique=True, index=True)  # Eski: tezgah_no -> numarasi
    aciklama = Column(String(255), nullable=True)  # Eski: tezgah_adi -> aciklama
    durum = Column(String(20), nullable=True, default='Aktif', index=True)
    created_at = Column(DateTime, nullable=True, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=True, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Ek alanlar (yeni uygulama için)
    lokasyon = Column(String(100), nullable=True)
    son_bakim_tarihi = Column(DateTime, nullable=True, index=True)
    sonraki_bakim_tarihi = Column(DateTime, nullable=True, index=True)
    bakim_periyodu = Column(Integer, nullable=False, default=30)  # gün
    
    # İlişkiler
    bakimlar = relationship("Bakim", back_populates="tezgah", cascade="all, delete-orphan")
    piller = relationship("Pil", back_populates="tezgah", cascade="all, delete-orphan")
    
    @validates('numarasi')
    def validate_numarasi(self, key, value):
        return validate_tezgah_numarasi(value)
    
    @validates('aciklama')
    def validate_aciklama(self, key, value):
        return validate_text_field(value, "Açıklama", min_len=0, max_len=255)
    
    @validates('lokasyon')
    def validate_lokasyon(self, key, value):
        return validate_text_field(value, "Lokasyon", min_len=0, max_len=100)
    
    @validates('durum')
    def validate_durum(self, key, value):
        valid_durumlar = ['Aktif', 'Bakımda', 'Arızalı', 'Devre Dışı']
        if value and value not in valid_durumlar:
            raise ValueError(f"Durum şunlardan biri olmalı: {', '.join(valid_durumlar)}")
        return value
    
    @validates('bakim_periyodu')
    def validate_bakim_periyodu(self, key, value):
        if value is not None and (value < 1 or value > 365):
            raise ValueError("Bakım periyodu 1-365 gün arasında olmalı")
        return value
    
    def __repr__(self):
        return f"<Tezgah(numarasi='{self.numarasi}', aciklama='{self.aciklama}', durum='{self.durum}')>"
    
    @property
    def tezgah_no(self):
        """Geriye uyumluluk için"""
        return self.numarasi
    
    @property
    def tezgah_adi(self):
        """Geriye uyumluluk için"""
        return self.aciklama or self.numarasi

class Bakim(Base):
    """Bakım kayıtları tablosu - gerçek verilerle uyumlu"""
    __tablename__ = 'bakimlar'  # Gerçek tabloda 'bakimlar'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tezgah_id = Column(Integer, ForeignKey('tezgah.id'), nullable=False, index=True)
    tarih = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)  # Eski: bakim_tarihi -> tarih
    bakim_yapan = Column(String(100), nullable=False, index=True)  # Gerçek veride var
    aciklama = Column(String(500), nullable=True)  # Gerçek veride var
    durum = Column(String(50), nullable=False, default='Planlandı', index=True)  # Gerçek veride var
    
    # Ek alanlar (yeni uygulama için)
    bakim_turu = Column(String(50), nullable=True, index=True)  # Periyodik, Arızalı, Acil
    baslangic_saati = Column(DateTime, nullable=True)
    bitis_saati = Column(DateTime, nullable=True)
    maliyet = Column(Float, nullable=True)
    yedek_parca = Column(Text, nullable=True)
    sonuc = Column(Text, nullable=True)
    olusturma_tarihi = Column(DateTime, nullable=True, default=lambda: datetime.now(timezone.utc))
    guncelleme_tarihi = Column(DateTime, nullable=True, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # İlişkiler
    tezgah = relationship("Tezgah", back_populates="bakimlar")
    
    @validates('bakim_yapan')
    def validate_bakim_yapan(self, key, value):
        return validate_text_field(value, "Bakım Yapan", min_len=2, max_len=100)
    
    @validates('aciklama')
    def validate_aciklama(self, key, value):
        return validate_text_field(value, "Açıklama", min_len=0, max_len=500)
    
    @validates('durum')
    def validate_durum(self, key, value):
        valid_durumlar = ['Planlandı', 'Devam Ediyor', 'Tamamlandı', 'İptal Edildi']
        if value and value not in valid_durumlar:
            raise ValueError(f"Durum şunlardan biri olmalı: {', '.join(valid_durumlar)}")
        return value
    
    @validates('bakim_turu')
    def validate_bakim_turu(self, key, value):
        valid_turler = ['Periyodik', 'Arızalı', 'Acil', 'Önleyici']
        if value and value not in valid_turler:
            raise ValueError(f"Bakım türü şunlardan biri olmalı: {', '.join(valid_turler)}")
        return value
    
    @validates('maliyet')
    def validate_maliyet(self, key, value):
        if value is not None and value < 0:
            raise ValueError("Maliyet negatif olamaz")
        return value
    
    def __repr__(self):
        return f"<Bakim(tezgah_id={self.tezgah_id}, tarih='{self.tarih}', durum='{self.durum}')>"
    
    @property
    def bakim_tarihi(self):
        """Geriye uyumluluk için"""
        return self.tarih

class Pil(Base):
    """Pil takip tablosu - gerçek verilerle uyumlu"""
    __tablename__ = 'pil_degisimler'  # Gerçek tabloda 'pil_degisimler'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tezgah_id = Column(Integer, ForeignKey('tezgah.id'), nullable=False, index=True)
    eksen = Column(String(50), nullable=True)  # Gerçek veride var (X, Y, Z, A)
    pil_modeli = Column(String(100), nullable=True)  # Gerçek veride var
    degisim_tarihi = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)  # Gerçek veride var
    degistiren_kisi = Column(String(100), nullable=False)  # Gerçek veride var
    aciklama = Column(String(255), nullable=True)  # Gerçek veride var
    
    # Ek alanlar (yeni uygulama için)
    pil_seri_no = Column(String(100), nullable=True)
    pil_tipi = Column(String(50), nullable=True)
    takma_tarihi = Column(DateTime, nullable=True, index=True)
    beklenen_omur = Column(Integer, nullable=False, default=365)  # gün
    son_kontrol_tarihi = Column(DateTime, nullable=True, index=True)
    voltaj = Column(Float, nullable=True)
    durum = Column(String(50), nullable=False, default='Aktif', index=True)  # Aktif, Zayıf, Değiştirilmeli, Değiştirildi
    olusturma_tarihi = Column(DateTime, nullable=True, default=lambda: datetime.now(timezone.utc))
    guncelleme_tarihi = Column(DateTime, nullable=True, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # İlişkiler
    tezgah = relationship("Tezgah", back_populates="piller")
    
    @validates('eksen')
    def validate_eksen(self, key, value):
        valid_eksenler = ['X', 'Y', 'Z', 'A', 'B', 'C', 'TÜM EKSENLER']
        if value and value.upper() not in valid_eksenler:
            raise ValueError(f"Eksen şunlardan biri olmalı: {', '.join(valid_eksenler)}")
        return value.upper() if value else None
    
    @validates('pil_modeli')
    def validate_pil_modeli(self, key, value):
        return validate_text_field(value, "Pil Modeli", min_len=0, max_len=100)
    
    @validates('degistiren_kisi')
    def validate_degistiren_kisi(self, key, value):
        return validate_text_field(value, "Değiştiren Kişi", min_len=2, max_len=100)
    
    @validates('aciklama')
    def validate_aciklama(self, key, value):
        return validate_text_field(value, "Açıklama", min_len=0, max_len=255)
    
    @validates('beklenen_omur')
    def validate_beklenen_omur(self, key, value):
        if value is not None and (value < 1 or value > 3650):  # 1 gün - 10 yıl
            raise ValueError("Beklenen ömür 1-3650 gün arasında olmalı")
        return value
    
    @validates('voltaj')
    def validate_voltaj(self, key, value):
        if value is not None and (value < 0 or value > 50):
            raise ValueError("Voltaj 0-50V arasında olmalı")
        return value
    
    @validates('durum')
    def validate_durum(self, key, value):
        valid_durumlar = ['Aktif', 'Zayıf', 'Değiştirilmeli', 'Değiştirildi']
        if value and value not in valid_durumlar:
            raise ValueError(f"Durum şunlardan biri olmalı: {', '.join(valid_durumlar)}")
        return value
    
    def __repr__(self):
        return f"<Pil(tezgah_id={self.tezgah_id}, eksen='{self.eksen}', model='{self.pil_modeli}')>"

class Kullanici(Base):
    """Kullanıcı tablosu"""
    __tablename__ = 'kullanici'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    kullanici_adi = Column(String(50), nullable=False, unique=True, index=True)
    ad_soyad = Column(String(100), nullable=False)
    email = Column(String(100), nullable=True, index=True)
    telefon = Column(String(20), nullable=True)
    rol = Column(String(50), nullable=False, default='Kullanıcı', index=True)  # Admin, Teknisyen, Kullanıcı
    aktif = Column(Boolean, nullable=False, default=True, index=True)
    son_giris = Column(DateTime, nullable=True)
    olusturma_tarihi = Column(DateTime, nullable=False, default=datetime.now)
    guncelleme_tarihi = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<Kullanici(adi='{self.kullanici_adi}', rol='{self.rol}', aktif={self.aktif})>"

class Rapor(Base):
    """Rapor tablosu"""
    __tablename__ = 'rapor'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rapor_adi = Column(String(100), nullable=False)
    rapor_turu = Column(String(50), nullable=False, index=True)  # Günlük, Haftalık, Aylık, Özel
    olusturma_tarihi = Column(DateTime, nullable=False, default=datetime.now, index=True)
    olusturan = Column(String(100), nullable=True)
    baslangic_tarihi = Column(DateTime, nullable=True)
    bitis_tarihi = Column(DateTime, nullable=True)
    filtre_kriterleri = Column(Text, nullable=True)  # JSON format
    rapor_verisi = Column(Text, nullable=True)  # JSON format
    dosya_yolu = Column(String(255), nullable=True)
    durum = Column(String(50), nullable=False, default='Oluşturuldu', index=True)
    
    def __repr__(self):
        return f"<Rapor(adi='{self.rapor_adi}', tur='{self.rapor_turu}', durum='{self.durum}')>"

class Ayar(Base):
    """Sistem ayarları tablosu"""
    __tablename__ = 'ayar'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    anahtar = Column(String(100), nullable=False, unique=True, index=True)
    deger = Column(Text, nullable=True)
    aciklama = Column(String(255), nullable=True)
    kategori = Column(String(50), nullable=False, default='Genel', index=True)
    olusturma_tarihi = Column(DateTime, nullable=False, default=datetime.now)
    guncelleme_tarihi = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<Ayar(anahtar='{self.anahtar}', kategori='{self.kategori}')>"

class DatabaseManager:
    """Veritabanı yönetim sınıfı"""
    
    # Constants
    DEFAULT_DB_PATH = "tezgah_takip_v2.db"
    CONNECTION_TIMEOUT = 30
    MAX_CONNECTIONS = 20
    
    def __init__(self, db_path=None):
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self.engine = None
        self.Session = None
        self.logger = logging.getLogger(__name__)
        self.init_database()
    
    def init_database(self):
        """Veritabanını başlat"""
        try:
            # SQLite veritabanı oluştur
            self.engine = create_engine(
                f'sqlite:///{self.db_path}',
                echo=False,  # SQL sorgularını göster (debug için)
                pool_pre_ping=True,
                poolclass=StaticPool,
                connect_args={
                    'check_same_thread': False,
                    'timeout': self.CONNECTION_TIMEOUT
                }
            )
            
            # Performance monitoring kur
            try:
                setup_performance_monitoring(self.engine)
            except Exception as e:
                self.logger.warning(f"Performance monitoring setup failed: {e}")
            
            # Session factory oluştur
            self.Session = sessionmaker(bind=self.engine)
            
            # Tabloları oluştur
            Base.metadata.create_all(self.engine)
            
            # Varsayılan verileri ekle
            self.create_default_data()
            
            self.logger.info("✅ Veritabanı başarıyla başlatıldı")
            
        except Exception as e:
            self.logger.error(f"❌ Veritabanı başlatma hatası: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """Context manager ile güvenli session yönetimi"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_session_direct(self):
        """Direkt session al (geriye uyumluluk için)"""
        return self.Session()
    
    def create_default_data(self):
        """Varsayılan verileri oluştur"""
        try:
            with self.get_session() as session:
                # Varsayılan kullanıcı kontrolü
                existing_user = session.query(Kullanici).filter_by(kullanici_adi='admin').first()
                if not existing_user:
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
                    existing_setting = session.query(Ayar).filter_by(anahtar=anahtar).first()
                    if not existing_setting:
                        ayar = Ayar(
                            anahtar=anahtar,
                            deger=deger,
                            aciklama=aciklama,
                            kategori=kategori
                        )
                        session.add(ayar)
                
                # Örnek tezgah verileri (sadece boş veritabanında ve backup yoksa)
                tezgah_count = session.query(Tezgah).count()
                if tezgah_count == 0 and not os.path.exists("backups/tezgah_takip.db"):
                    sample_tezgahlar = [
                        ('TZ001', 'CNC Torna Tezgahı 1', 'Atölye A', 'Aktif'),
                        ('TZ002', 'CNC Freze Tezgahı 1', 'Atölye A', 'Aktif'),
                        ('TZ003', 'Konvansiyonel Torna', 'Atölye B', 'Aktif'),
                        ('TZ004', 'Kaynak Tezgahı 1', 'Atölye C', 'Bakımda'),
                        ('TZ005', 'Planya Tezgahı', 'Atölye B', 'Aktif')
                    ]
                    
                    for no, adi, lokasyon, durum in sample_tezgahlar:
                        tezgah = Tezgah(
                            numarasi=no,
                            aciklama=adi,
                            lokasyon=lokasyon,
                            durum=durum,
                            bakim_periyodu=30
                        )
                        session.add(tezgah)
            
            self.logger.info("✅ Varsayılan veriler oluşturuldu")
            
        except Exception as e:
            self.logger.error(f"❌ Varsayılan veri oluşturma hatası: {e}")
    
    def get_tezgah_count(self):
        """Toplam tezgah sayısını al"""
        try:
            with self.get_session() as session:
                return session.query(Tezgah).count()
        except Exception as e:
            self.logger.error(f"Tezgah sayısı alınırken hata: {e}")
            return 0
    
    def get_active_tezgah_count(self):
        """Aktif tezgah sayısını al"""
        try:
            with self.get_session() as session:
                return session.query(Tezgah).filter_by(durum='Aktif').count()
        except Exception as e:
            self.logger.error(f"Aktif tezgah sayısı alınırken hata: {e}")
            return 0
    
    def get_pending_maintenance_count(self):
        """Bekleyen bakım sayısını al"""
        try:
            with self.get_session() as session:
                return session.query(Bakim).filter_by(durum='Planlandı').count()
        except Exception as e:
            self.logger.error(f"Bekleyen bakım sayısı alınırken hata: {e}")
            return 0
    
    def get_battery_warning_count(self):
        """Pil uyarısı sayısını al (365+ gün olanlar)"""
        try:
            from datetime import timedelta
            with self.get_session() as session:
                # 365 gün önceki tarihi hesapla (timezone aware)
                warning_date = datetime.now(timezone.utc) - timedelta(days=365)
                
                # 365+ gün olan piller
                return session.query(Pil).filter(Pil.degisim_tarihi <= warning_date).count()
        except Exception as e:
            self.logger.error(f"Pil uyarısı sayısı alınırken hata: {e}")
            return 0
    
    def get_tezgahlar_with_bakimlar(self, limit=None, offset=None):
        """N+1 query problemini çözmek için JOIN kullan"""
        try:
            with self.get_session() as session:
                query = session.query(Tezgah).options(
                    selectinload(Tezgah.bakimlar),
                    selectinload(Tezgah.piller)
                )
                
                if limit:
                    query = query.limit(limit)
                if offset:
                    query = query.offset(offset)
                
                return query.all()
        except Exception as e:
            self.logger.error(f"Tezgah verileri alınırken hata: {e}")
            return []
    
    def get_bakimlar_with_tezgah(self, limit=None, offset=None):
        """Bakım kayıtlarını tezgah bilgileriyle birlikte al"""
        try:
            with self.get_session() as session:
                query = session.query(Bakim, Tezgah).join(
                    Tezgah, Bakim.tezgah_id == Tezgah.id
                ).order_by(Bakim.tarih.desc())
                
                if limit:
                    query = query.limit(limit)
                if offset:
                    query = query.offset(offset)
                
                return query.all()
        except Exception as e:
            self.logger.error(f"Bakım verileri alınırken hata: {e}")
            return []
    
    def close(self):
        """Veritabanı bağlantısını kapat"""
        if self.engine:
            self.engine.dispose()
            self.logger.info("Veritabanı bağlantısı kapatıldı")

# Test fonksiyonu
def test_database():
    """Veritabanını test et"""
    print("🧪 Veritabanı Test Başlıyor...")
    
    try:
        # Veritabanı oluştur
        db = DatabaseManager("test_tezgah_takip.db")
        
        # Test verileri
        print(f"Toplam tezgah: {db.get_tezgah_count()}")
        print(f"Aktif tezgah: {db.get_active_tezgah_count()}")
        print(f"Bekleyen bakım: {db.get_pending_maintenance_count()}")
        print(f"Pil uyarısı: {db.get_battery_warning_count()}")
        
        # Temizlik
        db.close()
        if os.path.exists("test_tezgah_takip.db"):
            os.remove("test_tezgah_takip.db")
        
        print("✅ Veritabanı testi başarılı!")
        
    except Exception as e:
        print(f"❌ Veritabanı testi başarısız: {e}")

if __name__ == "__main__":
    test_database()
    # Query optimization methods
    def get_tezgah_with_stats(self, limit: int = 100, offset: int = 0):
        """Optimized tezgah query with statistics"""
        with self.get_session() as session:
            # Single query with joins to avoid N+1 problem
            query = session.query(
                Tezgah,
                func.count(Bakim.id).label('bakim_count'),
                func.count(Pil.id).label('pil_count'),
                func.max(Bakim.tarih).label('last_maintenance'),
                func.max(Pil.degisim_tarihi).label('last_battery_change')
            ).outerjoin(Bakim).outerjoin(Pil)\
             .group_by(Tezgah.id)\
             .order_by(Tezgah.numarasi)\
             .limit(limit).offset(offset)
            
            return query.all()
    
    def get_maintenance_summary(self, days: int = 30):
        """Optimized maintenance summary"""
        with self.get_session() as session:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Single query for maintenance statistics
            query = session.query(
                Bakim.durum,
                func.count(Bakim.id).label('count'),
                func.avg(
                    func.julianday(Bakim.bitis_saati) - func.julianday(Bakim.baslangic_saati)
                ).label('avg_duration_days')
            ).filter(Bakim.tarih >= cutoff_date)\
             .group_by(Bakim.durum)
            
            return query.all()
    
    def get_battery_alerts(self, warning_days: int = 30):
        """Optimized battery alert query"""
        with self.get_session() as session:
            warning_date = datetime.now(timezone.utc) - timedelta(days=warning_days)
            
            # Efficient query for battery warnings
            query = session.query(Pil, Tezgah)\
                          .join(Tezgah)\
                          .filter(
                              Pil.durum == 'Aktif',
                              Pil.degisim_tarihi <= warning_date
                          )\
                          .order_by(Pil.degisim_tarihi)
            
            return query.all()
    
    def bulk_insert_maintenance(self, maintenance_records: List[Dict]):
        """Bulk insert for maintenance records"""
        with self.get_session() as session:
            # Use bulk_insert_mappings for better performance
            session.bulk_insert_mappings(Bakim, maintenance_records)
            return len(maintenance_records)
    
    def get_dashboard_stats(self):
        """Optimized dashboard statistics in single query"""
        with self.get_session() as session:
            # Use subqueries for complex statistics
            total_tezgah = session.query(func.count(Tezgah.id)).scalar()
            
            active_tezgah = session.query(func.count(Tezgah.id))\
                                  .filter(Tezgah.durum == 'Aktif').scalar()
            
            # Recent maintenance count (last 7 days)
            week_ago = datetime.now(timezone.utc) - timedelta(days=7)
            recent_maintenance = session.query(func.count(Bakim.id))\
                                       .filter(Bakim.tarih >= week_ago).scalar()
            
            # Battery warnings
            month_ago = datetime.now(timezone.utc) - timedelta(days=365)
            battery_warnings = session.query(func.count(Pil.id))\
                                     .filter(
                                         Pil.durum == 'Aktif',
                                         Pil.degisim_tarihi <= month_ago
                                     ).scalar()
            
            return {
                'total_tezgah': total_tezgah or 0,
                'active_tezgah': active_tezgah or 0,
                'recent_maintenance': recent_maintenance or 0,
                'battery_warnings': battery_warnings or 0
            }
    
    def search_tezgah(self, search_term: str, limit: int = 50):
        """Optimized tezgah search with indexing"""
        with self.get_session() as session:
            # Use LIKE with proper indexing
            search_pattern = f"%{search_term}%"
            
            query = session.query(Tezgah)\
                          .filter(
                              or_(
                                  Tezgah.numarasi.like(search_pattern),
                                  Tezgah.aciklama.like(search_pattern),
                                  Tezgah.lokasyon.like(search_pattern)
                              )
                          )\
                          .order_by(Tezgah.numarasi)\
                          .limit(limit)
            
            return query.all()
    
    def get_maintenance_history_paginated(self, tezgah_id: int = None, 
                                        page: int = 1, per_page: int = 50):
        """Paginated maintenance history"""
        with self.get_session() as session:
            query = session.query(Bakim, Tezgah)\
                          .join(Tezgah)\
                          .order_by(Bakim.tarih.desc())
            
            if tezgah_id:
                query = query.filter(Bakim.tezgah_id == tezgah_id)
            
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Get total count for pagination
            total = query.count()
            
            # Get paginated results
            results = query.limit(per_page).offset(offset).all()
            
            return {
                'results': results,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
    
    def optimize_database(self):
        """Database optimization operations"""
        try:
            with self.get_session() as session:
                # VACUUM for SQLite
                session.execute("VACUUM")
                
                # ANALYZE for query planner
                session.execute("ANALYZE")
                
                # Update statistics
                session.execute("PRAGMA optimize")
                
            self.logger.info("Database optimization completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Database optimization failed: {e}")
            return False
    
    def create_indexes(self):
        """Create additional indexes for performance"""
        try:
            with self.get_session() as session:
                # Additional indexes for better performance
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_bakim_tarih_durum ON bakimlar(tarih, durum)",
                    "CREATE INDEX IF NOT EXISTS idx_pil_degisim_durum ON pil_degisimler(degisim_tarihi, durum)",
                    "CREATE INDEX IF NOT EXISTS idx_tezgah_durum_lokasyon ON tezgah(durum, lokasyon)",
                    "CREATE INDEX IF NOT EXISTS idx_bakim_tezgah_tarih ON bakimlar(tezgah_id, tarih DESC)",
                    "CREATE INDEX IF NOT EXISTS idx_pil_tezgah_eksen ON pil_degisimler(tezgah_id, eksen, durum)"
                ]
                
                for index_sql in indexes:
                    session.execute(index_sql)
                
            self.logger.info("Additional indexes created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Index creation failed: {e}")
            return False

# Add SQLAlchemy event listeners for performance monitoring
from sqlalchemy import event
from advanced_logger import log_database_operation
import time

# Event listener'ları DatabaseManager instance'ı oluşturulduktan sonra ekleyeceğiz
def setup_performance_monitoring(engine):
    """Performance monitoring event listener'larını kur"""
    
    @event.listens_for(engine, "before_cursor_execute")
    def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        context._query_start_time = time.time()

    @event.listens_for(engine, "after_cursor_execute")  
    def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total = time.time() - context._query_start_time
        
        # Log slow queries
        if total > 0.1:  # 100ms threshold
            try:
                log_database_operation(
                    operation="SLOW_QUERY",
                    table="multiple" if "JOIN" in statement.upper() else "unknown",
                    execution_time=total
                )
            except:
                # Fallback logging
                logging.getLogger(__name__).warning(f"Slow query: {total:.3f}s")