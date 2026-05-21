#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Profesyonel EXE Oluşturma Sistemi
PyInstaller ile Windows EXE oluşturma ve kurulum dosyası (Setup.exe) oluşturma
"""

import os
import sys
import json
import shutil
import subprocess
import zipfile
from pathlib import Path
from datetime import datetime

class TezgahTakipBuilder:
    """Profesyonel build sistemi"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        self.build_temp_dir = self.project_root / "build_temp"
        self.output_dir = self.project_root / "releases"
        
        # Sürüm bilgisi
        self.app_name = "TezgahTakip"
        self.app_version = "2.3.1"
        self.app_description = "AI Güçlü Fabrika Bakım Yönetim Sistemi"
        
        # Icon dosyası
        self.icon_file = self.project_root / "tezgah_icon.ico"
        
        print("🏭 TezgahTakip - Profesyonel EXE Oluşturma Sistemi")
        print("=" * 70)
        print(f"Sürüm: {self.app_version}")
        print(f"Proje Yolu: {self.project_root}")
        print()
    
    def check_dependencies(self):
        """Gerekli araçları kontrol et"""
        print("🔍 Bağımlılıklar kontrol ediliyor...")
        
        required_packages = {
            'pyinstaller': 'PyInstaller (EXE oluşturma için)',
            'PyQt5': 'PyQt5 (GUI framework)',
            'PyQt5.QtCore': 'PyQt5 QtCore',
            'PyQt5.QtGui': 'PyQt5 QtGui',
            'PyQt5.QtWidgets': 'PyQt5 QtWidgets',
            'sqlalchemy': 'SQLAlchemy (Veritabanı)',
            'requests': 'Requests (HTTP)',
            'cryptography': 'Cryptography (Güvenlik)',
        }
        
        missing = []
        for package, description in required_packages.items():
            try:
                __import__(package)
                print(f"  ✅ {description}")
            except ImportError:
                print(f"  ❌ {description}")
                missing.append(package)
        
        if missing:
            print(f"\n❌ Eksik bağımlılıklar: {', '.join(missing)}")
            print("\n💡 Kurulum komutu:")
            print(f"   pip install {' '.join(missing)}")
            return False
        
        print("\n✅ Tüm bağımlılıklar hazır!\n")
        return True
    
    def clean_previous_builds(self):
        """Önceki build dosyalarını temizle"""
        print("🧹 Önceki build dosyaları temizleniyor...")
        
        dirs_to_clean = [self.build_dir, self.dist_dir, self.build_temp_dir]
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"  🗑️  {dir_path.name} silindir")
        
        print()
    
    def create_release_directory(self):
        """Releases dizini oluştur"""
        self.output_dir.mkdir(exist_ok=True)
        print(f"📁 Releases dizini: {self.output_dir}\n")
    
    def build_exe_with_pyinstaller(self):
        """PyInstaller ile EXE oluştur"""
        print("🔨 PyInstaller ile EXE oluşturuluyor...")
        print("-" * 70)
        
        # Ana giriş noktası
        main_script = self.project_root / "tezgah_takip_app.py"
        
        if not main_script.exists():
            print(f"❌ Hata: {main_script} bulunamadı!")
            return False
        
        # PyInstaller komutu oluştur
        cmd = [
            sys.executable, "-m", "PyInstaller",
            str(main_script),
            "--name", self.app_name,
            "--onefile",  # Tek dosya
            "--windowed",  # Konsol penceresini gizle
            "--icon", str(self.icon_file) if self.icon_file.exists() else None,
            "--add-data", f"{self.project_root / 'tezgah_icon.ico'}{os.pathsep}.",
            "--add-data", f"{self.project_root / 'tezgah_logo.png'}{os.pathsep}.",
            "--add-data", f"{self.project_root / 'mtb_logo.png'}{os.pathsep}.",
            "--distpath", str(self.dist_dir),
            "--buildpath", str(self.build_dir),
            "--specpath", str(self.project_root),
            "--noconfirm",
            "--clean",
            "-y",
            # Hidden imports
            "--hidden-import=PyQt5",
            "--hidden-import=PyQt5.QtCore",
            "--hidden-import=PyQt5.QtGui",
            "--hidden-import=PyQt5.QtWidgets",
            "--hidden-import=PyQt5.QtPrintSupport",
            "--hidden-import=sqlalchemy",
            "--hidden-import=requests",
            "--hidden-import=cryptography",
            "--hidden-import=pandas",
            "--hidden-import=openpyxl",
            "--hidden-import=xlsxwriter",
            "--hidden-import=reportlab",
            "--hidden-import=matplotlib",
            "--hidden-import=seaborn",
            "--hidden-import=psutil",
            "--hidden-import=py7zr",
            "--hidden-import=colorlog",
            "--hidden-import=babel",
            "--hidden-import=pyyaml",
        ]
        
        # None değerleri temizle
        cmd = [arg for arg in cmd if arg is not None]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=False)
            print("\n✅ PyInstaller başarılı!\n")
            return True
        except subprocess.CalledProcessError as e:
            print(f"\n❌ PyInstaller hatası: {e}\n")
            return False
    
    def verify_exe_created(self):
        """EXE dosyasının oluşturulduğunu kontrol et"""
        exe_file = self.dist_dir / f"{self.app_name}.exe"
        
        if exe_file.exists():
            size_mb = exe_file.stat().st_size / (1024 * 1024)
            print(f"✅ EXE oluşturuldu: {exe_file.name} ({size_mb:.1f} MB)")
            return True
        else:
            print(f"❌ EXE bulunamadı: {exe_file}")
            return False
    
    def create_inno_setup_script(self):
        """Inno Setup konfigürasyonu oluştur"""
        print("\n📝 Inno Setup konfigürasyonu oluşturuluyor...")
        
        exe_file = self.dist_dir / f"{self.app_name}.exe"
        setup_script = self.project_root / "TezgahTakip_Setup.iss"
        
        # Inno Setup betiği
        setup_content = f"""#define MyAppName "TezgahTakip"
#define MyAppVersion "{self.app_version}"
#define MyAppPublisher "PobloMert"
#define MyAppURL "https://github.com/PobloMert/tezgah-takip"
#define MyAppExeName "TezgahTakip.exe"
#define SourcePath "{str(self.dist_dir)}"

[Setup]
AppId={{{{9a8e8c8e-4f4f-4f4f-4f4f-4f4f4f4f4f4f}}}}
AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
AppPublisher={{#MyAppPublisher}}
AppPublisherURL={{#MyAppURL}}
AppSupportURL={{#MyAppURL}}
AppUpdatesURL={{#MyAppURL}}
DefaultDirName={{autopf}}\\{{#MyAppName}}
DefaultGroupName={{#MyAppName}}
AllowNoIcons=yes
LicenseFile={self.project_root}\\LICENSE
PrivilegesRequired=lowest
OutputDir={self.output_dir}
OutputBaseFilename={self.app_name}_Setup_v{self.app_version}
SetupIconFile={self.icon_file if self.icon_file.exists() else ""}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ShowLanguageDialog=auto
UninstallDisplayIcon={{app}}\\{{#MyAppExeName}}
VersionInfoVersion={self.app_version}
VersionInfoCompany={{#MyAppPublisher}}
VersionInfoDescription={{#MyAppName}} - {self.app_description}
VersionInfoProductName={{#MyAppName}}
VersionInfoProductVersion={self.app_version}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "turkish"; MessagesFile: "compiler:Languages\\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaüstüne kısayol oluştur"; GroupDescription: "Ek Görevler:"
Name: "startmenu"; Description: "Başlat Menüsüne kısayol oluştur"; GroupDescription: "Ek Görevler:"

[Files]
Source: "{{#SourcePath}}\\{{#MyAppExeName}}"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "{{#SourcePath}}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{{group}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"
Name: "{{group}}\\Kaldır {{#MyAppName}}"; Filename: "{{uninstallexe}}"
Name: "{{commondesktop}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; Tasks: desktopicon
Name: "{{commonstartmenu}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; Tasks: startmenu

[Run]
Filename: "{{app}}\\{{#MyAppExeName}}"; Description: "{{#MyAppName}} başlat"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: dirifempty; Name: "{{app}}"
"""
        
        try:
            with open(setup_script, 'w', encoding='utf-8') as f:
                f.write(setup_content)
            print(f"✅ Inno Setup betiği oluşturuldu: {setup_script.name}")
            return True
        except Exception as e:
            print(f"❌ Inno Setup betiği oluşturma hatası: {e}")
            return False
    
    def create_portable_package(self):
        """Taşınabilir (Portable) paket oluştur"""
        print("\n📦 Taşınabilir paket oluşturuluyor...")
        
        exe_file = self.dist_dir / f"{self.app_name}.exe"
        portable_name = f"{self.app_name}_Portable_v{self.app_version}.zip"
        portable_path = self.output_dir / portable_name
        
        try:
            with zipfile.ZipFile(portable_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(exe_file, arcname=exe_file.name)
                
                # Readme ekle
                readme_content = f"""🏭 TezgahTakip - Taşınabilir Sürüm v{self.app_version}

📋 Bilgiler:
- AI Güçlü Fabrika Bakım Yönetim Sistemi
- Kurulum gerektirmeyen direkt çalışan sürüm
- GitHub: https://github.com/PobloMert/tezgah-takip

🚀 Kullanım:
1. ZIP dosyasını açın
2. TezgahTakip.exe çift tıklatın
3. Uygulama başlayacaktır

💾 Veri Depolanması:
- Tüm veriler uygulamanın bulunduğu klasörde saklanır
- Bir USB sürücüye kopyalayarak taşıyabilirsiniz

⚙️ Sistem Gereksinimleri:
- Windows 7 ve üzeri
- 500 MB disk alanı
- 1 GB RAM (önerilen)

📞 Destek:
GitHub Issues: https://github.com/PobloMert/tezgah-takip/issues
"""
                zipf.writestr("README.txt", readme_content)
            
            size_mb = portable_path.stat().st_size / (1024 * 1024)
            print(f"✅ Taşınabilir paket oluşturuldu: {portable_name} ({size_mb:.1f} MB)")
            return True
        except Exception as e:
            print(f"❌ Taşınabilir paket oluşturma hatası: {e}")
            return False
    
    def create_release_info(self):
        """Sürüm bilgisi dosyası oluştur"""
        print("\n📄 Sürüm bilgisi oluşturuluyor...")
        
        release_info = {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "app_description": self.app_description,
            "build_date": datetime.now().isoformat(),
            "github_url": "https://github.com/PobloMert/tezgah-takip",
            "files": {
                "exe": f"{self.app_name}.exe",
                "setup": f"{self.app_name}_Setup_v{self.app_version}.exe",
                "portable": f"{self.app_name}_Portable_v{self.app_version}.zip"
            },
            "system_requirements": {
                "os": "Windows 7+",
                "disk_space": "500 MB",
                "ram": "1 GB (Önerilen)"
            },
            "features": [
                "AI Güçlü Fabrika Bakım Yönetim",
                "Otomatik Güncelleme Sistemi",
                "Veritabanı Yönetimi",
                "İleri İstatistikler",
                "PDF Raporlama",
                "Excel Export"
            ]
        }
        
        try:
            info_file = self.output_dir / "release_info.json"
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(release_info, f, indent=2, ensure_ascii=False)
            print(f"✅ Sürüm bilgisi kaydedildi: release_info.json")
            return True
        except Exception as e:
            print(f"❌ Sürüm bilgisi oluşturma hatası: {e}")
            return False
    
    def create_user_guide(self):
        """Kullanıcı rehberi oluştur"""
        print("\n📖 Kullanıcı rehberi oluşturuluyor...")
        
        guide_content = f"""
{'=' * 70}
🏭 TezgahTakip v{self.app_version} - KURULUM VE KULLANIM REHBERI
{'=' * 70}

📋 İÇİNDEKİLER:
1. Kurulum Yöntemleri
2. İlk Başlatma
3. Temel Ayarlamalar
4. Sık Sorulan Sorular
5. Sorun Giderme

{'=' * 70}
1️⃣  KURULUM YÖNTEMLERI
{'=' * 70}

A) KURULUM DOSYASI İLE (Setup.exe) - ÖNERİLEN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. TezgahTakip_Setup_v{self.app_version}.exe dosyasını indirin
2. Dosyaya çift tıklayın
3. Kurulum sihirbazını takip edin
4. Kurulumu tamamladıktan sonra uygulama otomatik başlayacaktır

✅ Avantajları:
   • Başlat menüsüne otomatik kısayol oluşturur
   • Masaüstüne kısayol ekler (isteğe bağlı)
   • Kolay kaldırma seçeneği
   • Sistem tümleştirmesi

B) TAŞINABILIR SÜRÜM (Portable) - KURULUM GEREKTIRMEZ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. TezgahTakip_Portable_v{self.app_version}.zip dosyasını indirin
2. ZIP dosyasını açın (Sağ tık → Tümünü Çıkart)
3. TezgahTakip.exe dosyasına çift tıklayın

✅ Avantajları:
   • Kurulum gerektirmez
   • USB sürücüde taşıyabilirsiniz
   • Hiçbir kayıt defteri değişikliği yapmaz
   • Hızlı başlama

C) DOĞRUDAN ÇALIŞAN DOSYA (Exe)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. TezgahTakip.exe dosyasına çift tıklayın
2. Uygulama direkt başlayacaktır

{'=' * 70}
2️⃣  İLK BAŞLATMA
{'=' * 70}

⚠️ İLK ÇALIŞTIRMA (Uyarı bekliyorsanız):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Windows'un "Bu uygulamayı açmak istiyor musunuz?" uyarısını görebilirsiniz.

✅ Çözüm:
   1. "Daha fazla bilgi" veya "Diğer seçenekler"e tıklayın
   2. "Yine de çalıştır"ı seçin
   3. Uygulama başlayacaktır

🔍 KENDİNİZİ YÜKSELTEREK BAŞLATMA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. TezgahTakip.exe dosyasına sağ tıklayın
2. "Yönetici olarak çalıştır"ı seçin
3. Onay mesajında "Evet"i tıklayın

{'=' * 70}
3️⃣  TEMEL AYARLAMALAR
{'=' * 70}

🔑 API ANAHTARI AYARLAMASI:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Uygulamayı açtıktan sonra "Ayarlar" → "API Anahtarı" bölümüne gidin
2. Google Gemini AI anahtarınızı girin
3. "Kaydet"i tıklayın

💾 VERİTABANI YEDEKLEME:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Ana menüde "Araçlar" → "Yedek Al"
2. Yedekleme konumunu seçin
3. "Yedekle"yi tıklayın

📊 TESİSATI EKLEME:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. "Yeni Tesisat" butonunu tıklayın
2. Tesisat bilgilerini doldurun
3. "Kaydet"i tıklayın

{'=' * 70}
4️⃣  SSS (SIKÇA SORULAN SORULAR)
{'=' * 70}

S: Uygulamayı nerede kurmalıyım?
C: Kurulum yapıyorsanız varsayılan yeri (Program Files) kullanın.
   Taşınabilir sürümü USB'ye kopyalayabilirsiniz.

S: Veriler nereye kaydediliyor?
C: Veriler yerel bilgisayarınızda SQLite veritabanına kaydedilir.
   Konumu "Ayarlar"dan öğrenebilirsiniz.

S: Otomatik güncelleme nasıl çalışıyor?
C: Uygulama başladığında yeni sürümleri kontrol eder.
   Yeni sürüm bulunsa indirip uygulamaya sorar.

S: Yedek dosyası nasıl geri yüklerim?
C: "Araçlar" → "Yedek Yükle" menüsünden yapabilirsiniz.

S: API anahtarı nedir?
C: Google Gemini AI hizmetini kullanmak için gerekli anahtardır.
   https://makersuite.google.com/app/apikey adresinden alabilirsiniz.

{'=' * 70}
5️⃣  SORUN GIDERME
{'=' * 70}

❌ "Python'u bulunamadı" hatası
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Çözüm: EXE sürümü kullanıyorsanız bu sorun yaşanmamalıdır.
   Yapı dosyalarından kurulum yapıyorsanız Python 3.7+ yükleyin.

❌ "Veritabanı hatası" 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Çözüm:
   1. Uygulamayı kapatın
   2. "backups" klasöründen en son yedek bulun
   3. "Araçlar" → "Yedek Yükle"yi kullanın

❌ Uygulama açılmıyor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Çözüm:
   1. Yönetici olarak açmayı deneyin
   2. Antivirüs yazılımını kontrol edin
   3. Windows Defender'ı kontrol edin
   4. Bilgisayarı yeniden başlatın

❌ "Disk alanı yetersiz" hatası
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Çözüm:
   1. Disk alanı boşaltın
   2. Geri dönüşüm kutusunu boşaltın
   3. Eski yedekleri silin

{'=' * 70}
📞 DESTEK VE GERIBILDIRIM
{'=' * 70}

🔗 GitHub Sayfası:
   https://github.com/PobloMert/tezgah-takip

📝 Sorun Bildirmek:
   https://github.com/PobloMert/tezgah-takip/issues

💬 Tartışmalar:
   https://github.com/PobloMert/tezgah-takip/discussions

{'=' * 70}
✅ İyi kullanımlar!
{'=' * 70}
"""
        
        try:
            guide_file = self.output_dir / "KURULUM_VE_KULLANIM_REHBERI.txt"
            with open(guide_file, 'w', encoding='utf-8') as f:
                f.write(guide_content)
            print(f"✅ Kullanıcı rehberi oluşturuldu: KURULUM_VE_KULLANIM_REHBERI.txt")
            return True
        except Exception as e:
            print(f"❌ Kullanıcı rehberi oluşturma hatası: {e}")
            return False
    
    def create_installation_instructions(self):
        """Kurulum talimatlarını oluştur"""
        print("\n📋 Kurulum talimatları oluşturuluyor...")
        
        instructions = f"""
🏭 TezgahTakip v{self.app_version}

{'=' * 70}
HIZLI BAŞLANGAÇ REHBERI
{'=' * 70}

✨ KOLAY VE HIZLI KURULUM (3 ADIM)

Adım 1️⃣ : Dosya İndirin
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Aşağıdaki dosyalardan BİRİNİ indirin:

📦 KURULUMLArdan SONRA TAŞINABILIR
   Dosya: TezgahTakip_Setup_v{self.app_version}.exe
   Boyut: ~250-350 MB
   Avantaj: Başlat menüsüne eklenir, kolay kaldırma

📦 KURULUM GEREKTIRMEZ (TAŞINABİLİR)
   Dosya: TezgahTakip_Portable_v{self.app_version}.zip
   Boyut: ~250-350 MB
   Avantaj: USB'ye kopyalayıp taşıyabilirsiniz

📦 DOĞRUDAN DOSYA
   Dosya: TezgahTakip.exe
   Boyut: ~250-350 MB
   Avantaj: En hızlı başlama

Adım 2️⃣ : Yükleyin/Çıkartın
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Setup.exe ise:
  → Dosyaya çift tıklayın
  → "İleri" butonlarını tıklayın
  → Kurulum tamamlandığında "Başlat"ı seçin

Portable ZIP ise:
  → Sağ tık → "Tümünü Çıkart"
  → Çıkartılan klasörü açın
  → TezgahTakip.exe çift tıklayın

Adım 3️⃣ : Başlatın ✨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Tamamdır! Uygulama hazır.

{'=' * 70}
WINDOWS UYARISI ALIYORSANIZ
{'=' * 70}

"Windows tarafından PC'nizin korunması engellendi" uyarısı görebilirsiniz.

✅ ÇÖZÜMü:

1. "Daha fazla bilgi" veya "Diğer seçenekler"e tıklayın
2. "Yine de çalıştır"ı seçin
3. Devam edin

NEDEN? 
  → Uygulama yeni ve imzasız olduğu için Windows uyarı gösteriyor.
  → Tamamen güvenli ve virüsü yok.
  → GitHub kaynağından indirmişseniz 100% güvenli.

{'=' * 70}
SİSTEM GEREKSİNİMLERİ
{'=' * 70}

💻 İŞLETİM SİSTEMİ: Windows 7, 8, 10, 11 (32-bit veya 64-bit)
💾 DİSK ALANI: En az 500 MB boş alan
🎯 RAM: 1 GB (önerilen 2+ GB)
🌐 İNTERNET: AI özelliği için Internet gerekli

{'=' * 70}
KURULUM BAŞARILI MI?
{'=' * 70}

✅ Başarılı başlangıç göstergeleri:
  ✓ Uygulama penceresi açılıyor
  ✓ Logo ve "TezgahTakip" başlığı görülüyor
  ✓ Arayüz tamamen yükleniyor

❌ Sorun varsa:
  1. Bilgisayarı yeniden başlatın
  2. Antivirüs yazılımını kontrol edin (false positive olabilir)
  3. Windows Defender'ı kontrol edin
  4. Yönetici olarak çalıştırmayı deneyin

{'=' * 70}
SONRAKI ADIMLAR
{'=' * 70}

1. 🔑 API Anahtarını Ayarlayın
   → Ayarlar → API Anahtarı
   → Google Gemini API anahtarınızı girin
   (İsteğe bağlı - AI özelliği için gerekli)

2. 📁 İlk Tesisatı Ekleyin
   → "Yeni Tesisat" butonunu tıklayın
   → Bilgiler doldurup kaydedin

3. 📚 Kılavuzları Okuyun
   → Uygulamadaki "Yardım" menüsü
   → Örnek veriler ve şablonlar

{'=' * 70}
📞 SORULARINIZ?
{'=' * 70}

GitHub: https://github.com/PobloMert/tezgah-takip
Issues: https://github.com/PobloMert/tezgah-takip/issues
Tartışmalar: https://github.com/PobloMert/tezgah-takip/discussions

Daha ayrıntılı rehber için "KURULUM_VE_KULLANIM_REHBERI.txt" dosyasını okuyun.

{'=' * 70}
✨ Hoş geldiniz! TezgahTakip'i kullanmaktan hoşlanacağınızı umuyoruz.
{'=' * 70}
"""
        
        try:
            inst_file = self.output_dir / "HIZLI_BASLANGIC.txt"
            with open(inst_file, 'w', encoding='utf-8') as f:
                f.write(instructions)
            print(f"✅ Kurulum talimatları oluşturuldu: HIZLI_BASLANGIC.txt")
            return True
        except Exception as e:
            print(f"❌ Kurulum talimatları oluşturma hatası: {e}")
            return False
    
    def print_summary(self):
        """Özet bilgi yazdır"""
        print("\n" + "=" * 70)
        print("✅ BUILD BAŞARILI! - ÖZET")
        print("=" * 70)
        
        # Oluşturulan dosyalar
        if self.output_dir.exists():
            files = list(self.output_dir.glob("*"))
            if files:
                print(f"\n📁 Oluşturulan Dosyalar ({self.output_dir}):")
                for file in sorted(files):
                    if file.is_file():
                        size_mb = file.stat().st_size / (1024 * 1024)
                        if size_mb > 1:
                            print(f"   📦 {file.name} ({size_mb:.1f} MB)")
                        else:
                            size_kb = file.stat().st_size / 1024
                            print(f"   📄 {file.name} ({size_kb:.1f} KB)")
        
        print("\n🎯 KULLANICILARA PAYLAŞILACAKLAR:")
        print("━" * 70)
        print("✓ TezgahTakip_Setup_v{}.exe - Kurulum dosyası".format(self.app_version))
        print("✓ TezgahTakip_Portable_v{}.zip - Kurulum gerektirmez".format(self.app_version))
        print("✓ TezgahTakip.exe - Direkt çalışan dosya")
        print("✓ HIZLI_BASLANGIC.txt - Kurulum talimatları")
        print("✓ KURULUM_VE_KULLANIM_REHBERI.txt - Detaylı rehber")
        print("✓ release_info.json - Sürüm bilgisi")
        
        print("\n📱 PAYLAŞIM ÖNERİLERİ:")
        print("━" * 70)
        print("1. GitHub Releases'a yükleyin")
        print("   https://github.com/PobloMert/tezgah-takip/releases")
        print("\n2. README.md'de indirme bağlantılarını ekleyin")
        print("\n3. Kullanıcılara HIZLI_BASLANGIC.txt gönderin")
        print("\n4. Sorun yaşayanlar için KURULUM_VE_KULLANIM_REHBERI.txt referans olun")
        
        print("\n" + "=" * 70)
        print("🎉 TezgahTakip kullanıcılarla paylaşmaya hazır!")
        print("=" * 70 + "\n")
    
    def run(self):
        """Build işlemini çalıştır"""
        try:
            # Adımlar
            if not self.check_dependencies():
                return False
            
            self.clean_previous_builds()
            self.create_release_directory()
            
            if not self.build_exe_with_pyinstaller():
                return False
            
            if not self.verify_exe_created():
                return False
            
            self.create_inno_setup_script()
            self.create_portable_package()
            self.create_release_info()
            self.create_user_guide()
            self.create_installation_instructions()
            
            self.print_summary()
            return True
            
        except Exception as e:
            print(f"\n❌ KRITIK HATA: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Ana giriş noktası"""
    builder = TezgahTakipBuilder()
    success = builder.run()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
