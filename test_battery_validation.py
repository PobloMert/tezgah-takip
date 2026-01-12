#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify battery change validation fixes
"""

from database_models import DatabaseManager, Pil, Bakim, Tezgah
from datetime import datetime, timezone

def test_battery_validation():
    """Test the fixed validation rules"""
    print("🧪 Testing battery validation fixes...")
    
    try:
        # Initialize database
        db = DatabaseManager()
        
        with db.get_session() as session:
            # Get first tezgah
            tezgah = session.query(Tezgah).first()
            if not tezgah:
                print("❌ No tezgah found in database")
                return
            
            print(f"✅ Using tezgah: {tezgah.numarasi}")
            
            # Test new battery status values
            print("\n🔋 Testing new battery status values...")
            
            test_statuses = ['Test Edildi', 'Yeni', 'Aktif']
            for status in test_statuses:
                try:
                    pil = Pil(
                        tezgah_id=tezgah.id,
                        eksen='X',
                        pil_modeli='Test Battery',
                        degisim_tarihi=datetime.now(timezone.utc),
                        degistiren_kisi='Test User',
                        durum=status
                    )
                    session.add(pil)
                    session.flush()  # Validate without committing
                    print(f"  ✅ Status '{status}' - PASSED")
                    session.rollback()  # Don't save test data
                except Exception as e:
                    print(f"  ❌ Status '{status}' - FAILED: {e}")
                    session.rollback()
            
            # Test new maintenance type
            print("\n🔧 Testing new maintenance type...")
            
            try:
                bakim = Bakim(
                    tezgah_id=tezgah.id,
                    tarih=datetime.now(timezone.utc),
                    bakim_yapan='Test User',
                    aciklama='Test maintenance',
                    durum='Tamamlandı',
                    bakim_turu='Pil Değişimi'
                )
                session.add(bakim)
                session.flush()  # Validate without committing
                print("  ✅ Maintenance type 'Pil Değişimi' - PASSED")
                session.rollback()  # Don't save test data
            except Exception as e:
                print(f"  ❌ Maintenance type 'Pil Değişimi' - FAILED: {e}")
                session.rollback()
        
        print("\n🎉 Validation test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_battery_validation()