#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tezgah verilerini kontrol et
"""

from database_models import DatabaseManager, Tezgah

def check_tezgah_data():
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    
    try:
        # İlk 10 tezgahı kontrol et
        tezgahlar = session.query(Tezgah).limit(10).all()
        
        print("🔍 Tezgah Verileri Kontrolü:")
        print("=" * 50)
        
        for tezgah in tezgahlar:
            print(f"ID: {tezgah.id}")
            print(f"Numara: {tezgah.numarasi}")
            print(f"Açıklama: {tezgah.aciklama}")
            print(f"Lokasyon: {tezgah.lokasyon}")
            print(f"Durum: {tezgah.durum}")
            print(f"Marka: {tezgah.marka}")
            print(f"Model: {tezgah.model}")
            print(f"Tip: {tezgah.tip}")
            print(f"Son Bakım: {tezgah.son_bakim_tarihi}")
            print("-" * 30)
        
        # Toplam sayı
        total = session.query(Tezgah).count()
        print(f"\n📊 Toplam Tezgah Sayısı: {total}")
        
        # Durum dağılımı
        durumlar = session.query(Tezgah.durum, session.query(Tezgah).filter(Tezgah.durum == Tezgah.durum).count()).distinct().all()
        print(f"\n📈 Durum Dağılımı:")
        for durum in durumlar:
            count = session.query(Tezgah).filter(Tezgah.durum == durum[0]).count()
            print(f"  {durum[0]}: {count}")
            
    finally:
        session.close()

if __name__ == "__main__":
    check_tezgah_data()