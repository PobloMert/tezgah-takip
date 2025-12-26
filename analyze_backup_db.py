#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backup veritabanını analiz et
"""

import sqlite3
import os

def analyze_backup_database():
    """Backup veritabanının yapısını analiz et"""
    
    backup_path = "backups/tezgah_takip.db"
    
    if not os.path.exists(backup_path):
        print(f"❌ Backup dosyası bulunamadı: {backup_path}")
        return
    
    try:
        # Veritabanına bağlan
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        
        print("🔍 Backup Veritabanı Analizi")
        print("=" * 50)
        
        # Tabloları listele
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"\n📋 Tablolar ({len(tables)} adet):")
        for table in tables:
            table_name = table[0]
            print(f"  • {table_name}")
        
        print("\n" + "=" * 50)
        
        # Her tablo için detay
        for table in tables:
            table_name = table[0]
            
            print(f"\n📊 Tablo: {table_name}")
            print("-" * 30)
            
            # Tablo yapısını al
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            print("Sütunlar:")
            for col in columns:
                col_id, col_name, col_type, not_null, default_val, pk = col
                pk_str = " (PRIMARY KEY)" if pk else ""
                null_str = " NOT NULL" if not_null else ""
                default_str = f" DEFAULT {default_val}" if default_val else ""
                print(f"  • {col_name}: {col_type}{pk_str}{null_str}{default_str}")
            
            # Kayıt sayısını al
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"Kayıt sayısı: {count}")
            
            # Örnek veri (ilk 3 kayıt)
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                sample_data = cursor.fetchall()
                
                print("Örnek veriler:")
                for i, row in enumerate(sample_data, 1):
                    print(f"  {i}. {row}")
        
        conn.close()
        
        print("\n" + "=" * 50)
        print("✅ Analiz tamamlandı!")
        
    except Exception as e:
        print(f"❌ Analiz hatası: {e}")

if __name__ == "__main__":
    analyze_backup_database()