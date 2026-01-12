#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Otomatik Güncelleme Sistemi
GitHub Releases üzerinden otomatik güncelleme
"""

import os
import sys
import json
import requests
import zipfile
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
import logging

# packaging modülünü güvenli şekilde import et
try:
    from packaging import version
except ImportError:
    # Fallback version comparison
    class version:
        @staticmethod
        def parse(v):
            return tuple(map(int, v.split('.')))
        
        @staticmethod
        def __gt__(a, b):
            return version.parse(a) > version.parse(b)

class AutoUpdater:
    """Otomatik güncelleme sınıfı"""
    
    def __init__(self, current_version="2.0.0", github_repo="PobloMert/tezgah-takip"):
        self.current_version = current_version
        self.github_repo = github_repo
        self.api_url = f"https://api.github.com/repos/{github_repo}/releases/latest"
        self.logger = logging.getLogger(__name__)
        
        # Uygulama dizinleri
        self.app_dir = Path(__file__).parent
        self.temp_dir = self.app_dir / "temp_update"
        self.backup_dir = self.app_dir / "backup_before_update"
        
    def check_for_updates(self):
        """Güncellemeleri kontrol et"""
        try:
            self.logger.info("🔍 Güncellemeler kontrol ediliyor...")
            
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()
            
            release_data = response.json()
            latest_version = release_data['tag_name'].lstrip('v')
            
            if version.parse(latest_version) > version.parse(self.current_version):
                return {
                    'available': True,
                    'version': latest_version,
                    'download_url': release_data['assets'][0]['browser_download_url'] if release_data['assets'] else None,
                    'release_notes': release_data['body'],
                    'published_at': release_data['published_at']
                }
            else:
                return {'available': False, 'message': 'Uygulama güncel'}
                
        except requests.RequestException as e:
            self.logger.error(f"Güncelleme kontrolü hatası: {e}")
            return {'available': False, 'error': str(e)}
        except Exception as e:
            self.logger.error(f"Beklenmeyen hata: {e}")
            return {'available': False, 'error': str(e)}
    
    def download_update(self, download_url, progress_callback=None):
        """Güncellemeyi indir"""
        try:
            self.logger.info(f"📥 Güncelleme indiriliyor: {download_url}")
            
            # Temp dizini oluştur
            self.temp_dir.mkdir(exist_ok=True)
            
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            zip_path = self.temp_dir / "update.zip"
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            progress_callback(progress)
            
            self.logger.info("✅ Güncelleme başarıyla indirildi")
            return zip_path
            
        except Exception as e:
            self.logger.error(f"İndirme hatası: {e}")
            raise
    
    def backup_current_version(self):
        """Mevcut versiyonu yedekle"""
        try:
            self.logger.info("💾 Mevcut versiyon yedekleniyor...")
            
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)
            
            self.backup_dir.mkdir(exist_ok=True)
            
            # Kritik dosyaları yedekle
            critical_files = [
                "main_window.py",
                "database_models.py", 
                "config.json",
                "settings.json",
                "requirements.txt",
                "run_tezgah_takip.py"
            ]
            
            for file_name in critical_files:
                src = self.app_dir / file_name
                if src.exists():
                    shutil.copy2(src, self.backup_dir / file_name)
            
            # Veritabanını yedekle (kullanıcı verisi)
            db_files = list(self.app_dir.glob("*.db"))
            for db_file in db_files:
                shutil.copy2(db_file, self.backup_dir / db_file.name)
            
            self.logger.info("✅ Yedekleme tamamlandı")
            return True
            
        except Exception as e:
            self.logger.error(f"Yedekleme hatası: {e}")
            return False
    
    def apply_update(self, zip_path):
        """Güncellemeyi uygula"""
        try:
            self.logger.info("🔄 Güncelleme uygulanıyor...")
            
            # ZIP dosyasını çıkart
            extract_dir = self.temp_dir / "extracted"
            extract_dir.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Güncelleme dosyalarını kopyala
            update_files = [
                "main_window.py",
                "database_models.py",
                "gemini_ai.py",
                "api_key_manager.py",
                "config_manager.py",
                "backup_manager.py",
                "requirements.txt",
                "run_tezgah_takip.py",
                "auto_updater.py"
            ]
            
            for file_name in update_files:
                src = extract_dir / file_name
                dst = self.app_dir / file_name
                
                if src.exists():
                    shutil.copy2(src, dst)
                    self.logger.info(f"✅ {file_name} güncellendi")
            
            # Kullanıcı verilerini koru (config, db, settings)
            user_files = ["config.json", "settings.json"]
            for file_name in user_files:
                backup_file = self.backup_dir / file_name
                if backup_file.exists():
                    shutil.copy2(backup_file, self.app_dir / file_name)
                    self.logger.info(f"🔒 {file_name} korundu")
            
            # Veritabanını koru
            db_files = list(self.backup_dir.glob("*.db"))
            for db_file in db_files:
                shutil.copy2(db_file, self.app_dir / db_file.name)
                self.logger.info(f"🔒 {db_file.name} korundu")
            
            self.logger.info("✅ Güncelleme başarıyla uygulandı")
            return True
            
        except Exception as e:
            self.logger.error(f"Güncelleme uygulama hatası: {e}")
            return False
    
    def cleanup(self):
        """Geçici dosyaları temizle"""
        try:
            # Windows'ta dosyalar hala kullanımda olabilir, birkaç kez dene
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    if self.temp_dir.exists():
                        # Önce dosyaları readonly'den çıkar ve handle'ları kapat
                        for root, dirs, files in os.walk(self.temp_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                try:
                                    # Dosya özelliklerini değiştir
                                    os.chmod(file_path, 0o777)
                                    # Windows'ta dosya handle'larını zorla kapat
                                    if sys.platform == "win32":
                                        try:
                                            import gc
                                            gc.collect()  # Garbage collection
                                        except:
                                            pass
                                except Exception:
                                    pass
                        
                        shutil.rmtree(self.temp_dir)
                        break
                except PermissionError:
                    if attempt < max_attempts - 1:
                        import time
                        time.sleep(1)  # 1 saniye bekle ve tekrar dene
                        continue
                    else:
                        # Son denemede başarısız olursa, sadece uyar
                        self.logger.warning(f"Geçici dizin temizlenemedi: {self.temp_dir}")
            
            # Eski yedekleri temizle (7 günden eski)
            try:
                if self.backup_dir.exists():
                    backup_age = datetime.now().timestamp() - self.backup_dir.stat().st_mtime
                    if backup_age > 7 * 24 * 3600:  # 7 gün
                        shutil.rmtree(self.backup_dir)
            except Exception as e:
                self.logger.warning(f"Eski yedek temizleme hatası: {e}")
            
            self.logger.info("🧹 Temizlik tamamlandı")
            
        except Exception as e:
            self.logger.error(f"Temizlik hatası: {e}")
    
    def rollback(self):
        """Güncellemeyi geri al"""
        try:
            self.logger.info("⏪ Güncelleme geri alınıyor...")
            
            if not self.backup_dir.exists():
                raise Exception("Yedek bulunamadı!")
            
            # Yedek dosyaları geri yükle
            for backup_file in self.backup_dir.iterdir():
                if backup_file.is_file():
                    dst = self.app_dir / backup_file.name
                    shutil.copy2(backup_file, dst)
                    self.logger.info(f"⏪ {backup_file.name} geri yüklendi")
            
            self.logger.info("✅ Geri alma tamamlandı")
            return True
            
        except Exception as e:
            self.logger.error(f"Geri alma hatası: {e}")
            return False
    
    def restart_application(self):
        """Uygulamayı yeniden başlat"""
        try:
            self.logger.info("🔄 Uygulama yeniden başlatılıyor...")
            
            # Geçici dosyaları temizle
            self.cleanup()
            
            # Windows'ta daha güvenli yeniden başlatma
            if sys.platform == "win32":
                # Windows'ta subprocess ile yeni process başlat
                if getattr(sys, 'frozen', False):
                    # PyInstaller ile paketlenmiş
                    subprocess.Popen([sys.executable] + sys.argv[1:])
                else:
                    # Normal Python script
                    subprocess.Popen([sys.executable] + sys.argv)
                
                # Mevcut process'i sonlandır
                import time
                time.sleep(1)  # Yeni process'in başlaması için bekle
                os._exit(0)
            else:
                # Linux/Mac için eski yöntem
                if getattr(sys, 'frozen', False):
                    os.execv(sys.executable, [sys.executable] + sys.argv)
                else:
                    python = sys.executable
                    os.execl(python, python, *sys.argv)
                
        except Exception as e:
            self.logger.error(f"Yeniden başlatma hatası: {e}")
            raise

def check_and_update():
    """Ana güncelleme fonksiyonu"""
    updater = AutoUpdater()
    
    try:
        # Güncellemeleri kontrol et
        update_info = updater.check_for_updates()
        
        if update_info['available']:
            print(f"🎉 Yeni versiyon mevcut: v{update_info['version']}")
            print(f"📝 Yenilikler:\n{update_info['release_notes']}")
            
            # Kullanıcıdan onay al
            response = input("\n🤔 Güncellemeyi şimdi yüklemek istiyor musunuz? (e/h): ")
            
            if response.lower() in ['e', 'evet', 'yes', 'y']:
                # Yedekleme
                if not updater.backup_current_version():
                    raise Exception("Yedekleme başarısız!")
                
                # İndirme
                zip_path = updater.download_update(update_info['download_url'])
                
                # Uygulama
                if updater.apply_update(zip_path):
                    print("✅ Güncelleme başarıyla tamamlandı!")
                    updater.cleanup()
                    
                    # Yeniden başlat
                    restart = input("🔄 Uygulamayı şimdi yeniden başlatmak istiyor musunuz? (e/h): ")
                    if restart.lower() in ['e', 'evet', 'yes', 'y']:
                        try:
                            updater.restart_application()
                        except Exception as restart_error:
                            print(f"⚠️ Yeniden başlatma hatası: {restart_error}")
                            print("ℹ️ Lütfen uygulamayı manuel olarak yeniden başlatın.")
                    else:
                        print("ℹ️ Güncelleme tamamlandı. Değişikliklerin etkili olması için uygulamayı yeniden başlatın.")
                else:
                    print("❌ Güncelleme başarısız! Geri alınıyor...")
                    updater.rollback()
            else:
                print("ℹ️ Güncelleme iptal edildi")
        else:
            print("✅ Uygulama güncel!")
            
    except Exception as e:
        print(f"❌ Güncelleme hatası: {e}")
        return False
    
    return True

if __name__ == "__main__":
    check_and_update()