#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backup Veritabanından Veri Aktarım Scripti
Gerçek verilerinizi yeni uygulamaya aktarır
"""

import sqlite3
import os
import shutil
from datetime import datetime
from database_models import DatabaseManager, Tezgah, Bakim, Pil

def backup_current_database():
    """Mevcut veritabanını yedekle"""
    current_db = "tezgah_takip_v2.db"
    if os.path.exists(current_db):
        backup_name = f"tezgah_takip_v2_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(current_db, backup_name)
        print(f"✅ Mevcut veritabanı yedeklendi: {backup_name}")
        return backup_name
    return None

def migrate_data():
    """Backup verilerini yeni veritabanına aktar"""
    
    backup_path = "backups/tezgah_takip.db"
    
    if not os.path.exists(backup_path):
        print(f"❌ Backup dosyası bulunamadı: {backup_path}")
        return False
    
    try:
        print("🔄 Veri aktarımı başlıyor...")
        
        # Mevcut veritabanını yedekle
        backup_current_database()
        
        # Yeni veritabanı yöneticisi oluştur
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        # Backup veritabanına bağlan
        backup_conn = sqlite3.connect(backup_path)
        backup_cursor = backup_conn.cursor()
        
        print("\n📊 Tezgah verilerini aktarıyor...")
        
        # Tezgah verilerini aktar
        backup_cursor.execute("SELECT id, numarasi, aciklama, durum, created_at, updated_at FROM tezgah ORDER BY id")
        tezgah_rows = backup_cursor.fetchall()
        
        tezgah_mapping = {}  # Eski ID -> Yeni ID mapping
        
        for row in tezgah_rows:
            old_id, numarasi, aciklama, durum, created_at, updated_at = row
            
            # Mevcut tezgah var mı kontrol et
            existing = session.query(Tezgah).filter_by(numarasi=numarasi).first()
            
            if existing:
                # Güncelle
                existing.aciklama = aciklama
                existing.durum = durum or 'Aktif'
                if created_at:
                    existing.created_at = datetime.fromisoformat(created_at.replace(' ', 'T')) if isinstance(created_at, str) else created_at
                if updated_at:
                    existing.updated_at = datetime.fromisoformat(updated_at.replace(' ', 'T')) if isinstance(updated_at, str) else updated_at
                
                tezgah_mapping[old_id] = existing.id
                print(f"  ✅ Güncellendi: {numarasi}")
            else:
                # Yeni ekle
                new_tezgah = Tezgah(
                    numarasi=numarasi,
                    aciklama=aciklama,
                    durum=durum or 'Aktif'
                )
                
                if created_at:
                    try:
                        new_tezgah.created_at = datetime.fromisoformat(created_at.replace(' ', 'T')) if isinstance(created_at, str) else created_at
                    except:
                        new_tezgah.created_at = datetime.now()
                
                if updated_at:
                    try:
                        new_tezgah.updated_at = datetime.fromisoformat(updated_at.replace(' ', 'T')) if isinstance(updated_at, str) else updated_at
                    except:
                        new_tezgah.updated_at = datetime.now()
                
                session.add(new_tezgah)
                session.flush()  # ID'yi al
                
                tezgah_mapping[old_id] = new_tezgah.id
                print(f"  ➕ Eklendi: {numarasi}")
        
        session.commit()
        print(f"✅ {len(tezgah_rows)} tezgah aktarıldı")
        
        print("\n🔧 Bakım verilerini aktarıyor...")
        
        # Bakım verilerini aktar
        backup_cursor.execute("""
            SELECT id, tezgah_id, tarih, bakim_yapan, aciklama, durum 
            FROM bakimlar 
            ORDER BY tarih DESC
        """)
        bakim_rows = backup_cursor.fetchall()
        
        bakim_count = 0
        for row in bakim_rows:
            old_id, old_tezgah_id, tarih, bakim_yapan, aciklama, durum = row
            
            # Tezgah ID mapping
            if old_tezgah_id not in tezgah_mapping:
                print(f"  ⚠️ Tezgah ID bulunamadı: {old_tezgah_id}")
                continue
            
            new_tezgah_id = tezgah_mapping[old_tezgah_id]
            
            # Mevcut bakım kaydı var mı kontrol et (tarih ve tezgah ile)
            try:
                tarih_obj = datetime.fromisoformat(tarih.replace(' ', 'T')) if isinstance(tarih, str) else tarih
            except:
                tarih_obj = datetime.now()
            
            existing = session.query(Bakim).filter_by(
                tezgah_id=new_tezgah_id,
                tarih=tarih_obj
            ).first()
            
            if not existing:
                new_bakim = Bakim(
                    tezgah_id=new_tezgah_id,
                    tarih=tarih_obj,
                    bakim_yapan=bakim_yapan or 'Bilinmiyor',
                    aciklama=aciklama,
                    durum=durum or 'Tamamlandı',
                    bakim_turu='Arızalı' if 'arıza' in (aciklama or '').lower() else 'Periyodik'
                )
                
                session.add(new_bakim)
                bakim_count += 1
                
                if bakim_count % 50 == 0:
                    print(f"  📝 {bakim_count} bakım kaydı aktarıldı...")
        
        session.commit()
        print(f"✅ {bakim_count} bakım kaydı aktarıldı")
        
        print("\n🔋 Pil verilerini aktarıyor...")
        
        # Pil verilerini aktar
        backup_cursor.execute("""
            SELECT id, tezgah_id, eksen, pil_modeli, degisim_tarihi, degistiren_kisi, aciklama 
            FROM pil_degisimler 
            ORDER BY degisim_tarihi DESC
        """)
        pil_rows = backup_cursor.fetchall()
        
        pil_count = 0
        for row in pil_rows:
            old_id, old_tezgah_id, eksen, pil_modeli, degisim_tarihi, degistiren_kisi, aciklama = row
            
            # Tezgah ID mapping
            if old_tezgah_id not in tezgah_mapping:
                print(f"  ⚠️ Tezgah ID bulunamadı: {old_tezgah_id}")
                continue
            
            new_tezgah_id = tezgah_mapping[old_tezgah_id]
            
            try:
                degisim_tarihi_obj = datetime.fromisoformat(degisim_tarihi.replace(' ', 'T')) if isinstance(degisim_tarihi, str) else degisim_tarihi
            except:
                degisim_tarihi_obj = datetime.now()
            
            # Mevcut pil kaydı var mı kontrol et
            existing = session.query(Pil).filter_by(
                tezgah_id=new_tezgah_id,
                eksen=eksen,
                degisim_tarihi=degisim_tarihi_obj
            ).first()
            
            if not existing:
                new_pil = Pil(
                    tezgah_id=new_tezgah_id,
                    eksen=eksen,
                    pil_modeli=pil_modeli,
                    degisim_tarihi=degisim_tarihi_obj,
                    degistiren_kisi=degistiren_kisi or 'Bilinmiyor',
                    aciklama=aciklama,
                    takma_tarihi=degisim_tarihi_obj,
                    durum='Aktif'
                )
                
                session.add(new_pil)
                pil_count += 1
        
        session.commit()
        print(f"✅ {pil_count} pil kaydı aktarıldı")
        
        # Bağlantıları kapat
        backup_conn.close()
        session.close()
        
        print("\n" + "=" * 50)
        print("🎉 Veri aktarımı başarıyla tamamlandı!")
        print(f"📊 Özet:")
        print(f"  • {len(tezgah_rows)} tezgah")
        print(f"  • {bakim_count} bakım kaydı")
        print(f"  • {pil_count} pil değişimi")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Veri aktarım hatası: {e}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False

def verify_migration():
    """Aktarım sonucunu doğrula"""
    try:
        print("\n🔍 Aktarım doğrulaması...")
        
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        # İstatistikler
        tezgah_count = session.query(Tezgah).count()
        bakim_count = session.query(Bakim).count()
        pil_count = session.query(Pil).count()
        
        print(f"📊 Yeni veritabanı istatistikleri:")
        print(f"  • Toplam tezgah: {tezgah_count}")
        print(f"  • Toplam bakım kaydı: {bakim_count}")
        print(f"  • Toplam pil kaydı: {pil_count}")
        
        # Örnek veriler
        print(f"\n📋 Örnek tezgahlar:")
        sample_tezgahlar = session.query(Tezgah).limit(5).all()
        for tezgah in sample_tezgahlar:
            print(f"  • {tezgah.numarasi}: {tezgah.aciklama} ({tezgah.durum})")
        
        print(f"\n🔧 Son bakım kayıtları:")
        recent_bakimlar = session.query(Bakim).order_by(Bakim.tarih.desc()).limit(3).all()
        for bakim in recent_bakimlar:
            tezgah = session.query(Tezgah).filter_by(id=bakim.tezgah_id).first()
            print(f"  • {tezgah.numarasi if tezgah else 'N/A'}: {bakim.tarih.strftime('%Y-%m-%d')} - {bakim.bakim_yapan}")
        
        session.close()
        
        print("✅ Doğrulama tamamlandı!")
        
    except Exception as e:
        print(f"❌ Doğrulama hatası: {e}")

def main():
    """Ana fonksiyon"""
    print("🏭 TezgahTakip Veri Aktarım Aracı")
    print("=" * 50)
    
    # Onay al
    response = input("Backup verilerini aktarmak istediğinizden emin misiniz? (e/h): ")
    if response.lower() != 'e':
        print("❌ İşlem iptal edildi.")
        return
    
    # Aktarımı başlat
    success = migrate_data()
    
    if success:
        # Doğrulama yap
        verify_migration()
        
        print("\n🚀 Artık uygulamayı başlatabilirsiniz!")
        print("   python run_tezgah_takip.py")
    else:
        print("\n❌ Aktarım başarısız oldu. Lütfen hataları kontrol edin.")

if __name__ == "__main__":
    main()