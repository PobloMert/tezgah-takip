#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TezgahTakip - Professional EXE Build System
PyInstaller + Inno Setup ile kullanıcı dostu kurulum dosyası oluşturur
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

class TezgahTakipBuilder:
    """TezgahTakip EXE ve Setup Dosyası Oluşturucusu"""
    
    def __init__(self):
        self.version = "2.3.1"
        self.app_name = "TezgahTakip"
        self.company_name = "TezgahTakip"
        
        # Dizin yapısı
        self.root_dir = Path(__file__).parent
        self.build_dir = self.root_dir / "build"
        self.dist_dir = self.root_dir / "dist"
        self.setup_dir = self.root_dir / "setup"
        self.output_dir = self.root_dir / "releases"
        
        # PyInstaller çıktısı
        self.exe_name = f"{self.app_name}.exe"
        self.setup_exe = f"{self.app_name}_Setup_v{self.version}.exe"
        
    def cleanup(self):
        """Eski build dosyalarını temizle"""
        print("🧹 Eski build dosyaları temizleniyor...")
        
        for folder in [self.build_dir, self.dist_dir, self.setup_dir]:
            if folder.exists():
                shutil.rmtree(folder)
                print(f"  ✓ {folder.name} klasörü silindi")
        
        # Output klasörü oluştur
        self.output_dir.mkdir(exist_ok=True)
    
    def install_build_tools(self):
        """Gerekli build araçlarını yükle"""
        print("\n📦 Build araçları kontrol ediliyor...")
        
        try:
            # PyInstaller kontrol et
            import PyInstaller
            print("  ✓ PyInstaller zaten yüklü")
        except ImportError:
            print("  📥 PyInstaller yükleniyor...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "pyinstaller"],
                check=True
            )
        
        # Inno Setup kontrol et (Windows'ta)
        if sys.platform == "win32":
            inno_setup_path = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
            if not Path(inno_setup_path).exists():
                print("\n  ⚠️  Inno Setup 6 yüklü değil!")
                print("  📥 Yüklemek için: https://jrsoftware.org/isdl.php")
                print("  Not: Inno Setup kurulduktan sonra build_system.py yeniden çalıştırın\n")
    
    def create_pyinstaller_spec(self):
        """PyInstaller spec dosyası oluştur"""
        print("\n📝 PyInstaller konfigürasyonu oluşturuluyor...")
        
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
"""
{self.app_name} PyInstaller Spec File
Version: {self.version}
"""

block_cipher = None

a = Analysis(
    ['tezgah_takip_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Veri dosyalarını buraya ekleyin
        # ('assets', 'assets'),
    ],
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.QtChart',
        'sqlalchemy',
        'requests',
        'pandas',
        'openpyxl',
        'reportlab',
        'matplotlib',
        'seaborn',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{self.exe_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Konsol penceresini gizle
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # İkon dosyası: 'assets/icon.ico'
)

# İsteğe bağlı: Tek dosya olarak yapıştır (yavaş başlatır)
# uncomment et: --onefile parametresi
'''
        
        spec_path = self.root_dir / f"{self.app_name}.spec"
        spec_path.write_text(spec_content, encoding='utf-8')
        print(f"  ✓ Spec dosyası oluşturuldu: {spec_path.name}")
        
        return spec_path
    
    def build_exe_with_pyinstaller(self):
        """PyInstaller ile EXE dosyasını oluştur"""
        print("\n🔨 PyInstaller ile EXE oluşturuluyor (Bu işlem 2-5 dakika alabilir)...")
        
        spec_path = self.create_pyinstaller_spec()
        
        try:
            # PyInstaller komutunu çalıştır
            cmd = [
                sys.executable,
                "-m", "PyInstaller",
                "--onedir",  # Klasörde paketlenmiş format
                "--windowed",  # GUI uygulaması (konsol yok)
                "--name", self.app_name,
                "--distpath", str(self.dist_dir),
                "--buildpath", str(self.build_dir),
                "--specpath", str(self.root_dir),
                str(spec_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"  ❌ PyInstaller hatası:\n{result.stderr}")
                return False
            
            exe_path = self.dist_dir / self.app_name / self.exe_name
            if exe_path.exists():
                file_size = exe_path.stat().st_size / (1024 * 1024)  # MB
                print(f"  ✅ EXE başarıyla oluşturuldu!")
                print(f"     📦 Dosya: {exe_path}")
                print(f"     📊 Boyut: {file_size:.1f} MB")
                return True
            else:
                print(f"  ❌ EXE dosyası bulunmadı")
                return False
                
        except Exception as e:
            print(f"  ❌ PyInstaller çalıştırılırken hata: {e}")
            return False
    
    def create_inno_setup_script(self):
        """Inno Setup script dosyası oluştur"""
        print("\n📝 Inno Setup konfigürasyonu oluşturuluyor...")
        
        setup_script = f"""[Setup]
AppName={self.app_name}
AppVersion={self.version}
AppPublisher={self.company_name}
AppPublisherURL=https://github.com/PobloMert/tezgah-takip
AppSupportURL=https://github.com/PobloMert/tezgah-takip/issues
AppUpdatesURL=https://github.com/PobloMert/tezgah-takip/releases
DefaultDirName={{autopf}}\\{self.app_name}
DefaultGroupName={self.app_name}
OutputDir=.\\releases
OutputBaseFilename={self.app_name}_Setup_v{self.version}
SetupIconFile=
Compression=lzma
SolidCompression=yes
WizardStyle=modern
LanguageDetectionMethod=uilanguage
ShowLanguageDialog=no
AllowNoIcons=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "turkish"; MessagesFile: "compiler:Languages\\Turkish.isl"

[CustomMessages]
turkish.WelcomeLabel1={self.app_name} v{self.version} Kurulum Sihirbazına Hoş Geldiniz
turkish.WelcomeLabel2=Bu program {self.app_name} [AI Güçlü Fabrika Bakım Yönetim Sistemi] uygulamasını bilgisayarınıza yükleyecektir.
turkish.FinishedLabelNoIcons={self.app_name} bilgisayarınıza başarıyla yüklendi.
turkish.FinishedLabel=Kurulum tamamlandı. {self.app_name} kullanmaya başlamak için "Bitir" düğmesine tıklayın.

[Files]
Source: "dist\\{self.app_name}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{group}}\\{self.app_name}"; Filename: "{{app}}\\{self.app_name}.exe"
Name: "{{group}}\\{{cm:UninstallProgram,{self.app_name}}}"; Filename: "{{uninstallexe}}"
Name: "{{commondesktop}}\\{self.app_name}"; Filename: "{{app}}\\{self.app_name}.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"

[Run]
Filename: "{{app}}\\{self.app_name}.exe"; Description: "{{cm:LaunchProgram,{self.app_name}}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: dirifempty; Name: "{{app}}"
"""
        
        self.setup_dir.mkdir(exist_ok=True)
        setup_script_path = self.setup_dir / f"{self.app_name}_Setup.iss"
        setup_script_path.write_text(setup_script, encoding='utf-8')
        print(f"  ✓ Inno Setup script oluşturuldu: {setup_script_path.name}")
        
        return setup_script_path
    
    def build_setup_exe(self):
        """Inno Setup ile Setup.exe oluştur"""
        if sys.platform != "win32":
            print("\n⚠️  Inno Setup sadece Windows'ta mevcuttur")
            return False
        
        print("\n🔧 Inno Setup ile kurulum dosyası oluşturuluyor...")
        
        setup_script = self.create_inno_setup_script()
        
        # Inno Setup yol
        inno_paths = [
            r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
            r"C:\Program Files\Inno Setup 6\ISCC.exe",
            r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        ]
        
        inno_exe = None
        for path in inno_paths:
            if Path(path).exists():
                inno_exe = path
                break
        
        if not inno_exe:
            print("  ❌ Inno Setup bulunamadı!")
            print("  📥 Lütfen https://jrsoftware.org/isdl.php adresinden Inno Setup 6'yı yükleyin")
            return False
        
        try:
            cmd = [inno_exe, str(setup_script)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"  ❌ Inno Setup hatası:\n{result.stderr}")
                return False
            
            setup_exe_path = self.output_dir / self.setup_exe
            if setup_exe_path.exists():
                file_size = setup_exe_path.stat().st_size / (1024 * 1024)
                print(f"  ✅ Setup.exe başarıyla oluşturuldu!")
                print(f"     📦 Dosya: {setup_exe_path}")
                print(f"     📊 Boyut: {file_size:.1f} MB")
                return True
            else:
                print(f"  ❌ Setup.exe dosyası bulunmadı")
                return False
                
        except Exception as e:
            print(f"  ❌ Inno Setup çalıştırılırken hata: {e}")
            return False
    
    def create_readme(self):
        """Kurulum talimatları için README oluştur"""
        print("\n📄 Kurulum talimatları oluşturuluyor...")
        
        readme_content = f"""# {self.app_name} v{self.version} - Kurulum Kılavuzu

## 🚀 Hızlı Kurulum

### Seçenek 1: Setup.exe ile Kurulum (Önerilen) ✅

1. **{self.app_name}_Setup_v{self.version}.exe** dosyasını çift tıklayın
2. Kurulum sihirbazını takip edin
3. Kurulum tamamlandıktan sonra otomatik olarak başlayacaktır

### Seçenek 2: Portable EXE (Kurulum Gerektirmez)

1. **dist/{self.app_name}** klasöründeki **{self.app_name}.exe** dosyasını çalıştırın
2. Python yüklü değilse sorun yok - her şey paketlenmiştir

## 💻 Sistem Gereksinimleri

- **İşletim Sistemi**: Windows 7 veya üstü
- **İşlemci**: Intel/AMD x86-64
- **RAM**: Minimum 2GB
- **Disk**: 500 MB

## ⚙️ Teknik Detaylar

- **Oluşturma Tarihi**: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
- **Python Sürümü**: 3.7+
- **GUI Framework**: PyQt5
- **Veritabanı**: SQLAlchemy + SQLite

## 🔧 Build Sistemi

EXE dosyaları PyInstaller kullanılarak oluşturulmuştur:
- **PyInstaller**: Tüm Python bağımlılıklarını paketler
- **Inno Setup**: Profesyonel Windows kurulum deneyimi

## 📁 Dosya Yapısı

```
{self.app_name}_Setup_v{self.version}.exe    - Kurulum dosyası
dist/{self.app_name}/                        - Portable EXE klasörü
dist/{self.app_name}/{self.app_name}.exe     - Ana uygulama EXE dosyası
releases/                                     - Son sürümler
```

## 🆘 Sorun Giderme

### "Windows Defender/Antivirus uyarısı alıyorum"
- PyInstaller tarafından oluşturulan EXE dosyaları bazı antivirus programları tarafından uyarı verebilir
- Bu normal ve güvenlidir. GitHub deposundaki kaynak kodları inceleyebilirsiniz.

### "Uygulama başlamıyor"
1. Windows'u yeniden başlatın
2. Microsoft Visual C++ Runtime yükleyin: https://support.microsoft.com/en-us/help/2977003
3. Python 3.7+ yüklü olduğundan emin olun

## 📝 Notlar

- Bu sürüm tamamen bağımsız ve Python yüklü olmayabilir
- Tüm gerekli kütüphaneler paketlenmiştir
- Veritabanı dosyaları otomatik olarak oluşturulacaktır

## 🔄 Güncelleme

Yeni sürümler için: https://github.com/PobloMert/tezgah-takip/releases

---

**TezgahTakip** - AI Güçlü Fabrika Bakım Yönetim Sistemi
"""
        
        readme_path = self.output_dir / "KURULUM_KILAVUZU.txt"
        readme_path.write_text(readme_content, encoding='utf-8')
        print(f"  ✓ Kurulum kılavuzu oluşturuldu: {readme_path.name}")
    
    def generate_build_report(self, success: bool, build_time: str):
        """Build raporu oluştur"""
        report_content = f"""
╔════════════════════════════════════════════════════════════════╗
║         {self.app_name} v{self.version} - BUILD RAPORU              ║
╚════════════════════════════════════════════════════════════════╝

📅 Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
⏱️  Build Süresi: {build_time}
✅ Durum: {"BAŞARILI" if success else "BAŞARISIZ"}

{'📦 ÇIKTI DOSYALARI:' if success else '❌ HATALAR MEYDANA GELDI'}
{'-' * 62}

"""
        
        if success:
            if (self.dist_dir / self.app_name / self.exe_name).exists():
                exe_size = (self.dist_dir / self.app_name / self.exe_name).stat().st_size / (1024 * 1024)
                report_content += f"""
📦 EXE Dosyası (Portable):
   └─ dist/{self.app_name}/{self.exe_name}
   └─ Boyut: {exe_size:.1f} MB
   └─ Açıklama: Kurulum gerektirmez, doğrudan çalıştırılabilir

"""
            
            if (self.output_dir / self.setup_exe).exists():
                setup_size = (self.output_dir / self.setup_exe).stat().st_size / (1024 * 1024)
                report_content += f"""
📦 Setup Dosyası (Kurulum):
   └─ releases/{self.setup_exe}
   └─ Boyut: {setup_size:.1f} MB
   └─ Açıklama: Windows kurulum sihirbazı

"""
        
        report_content += f"""
{'─' * 62}
🚀 ÖNERİLEN DAĞITIM ADIMLAR:

1. EXE dosyalarını GitHub Releases bölümüne yükleyin
2. Kullanıcılar setup.exe indirebilir ve kurabilir
3. Veya dist/ klasöründeki EXE'yi doğrudan çalıştırabilir

📋 KONTROL LİSTESİ:

✓ PyInstaller kuruldu ve EXE oluşturuldu
{'✓ Inno Setup kuruldu ve Setup.exe oluşturuldu' if sys.platform == "win32" else '⚠ Inno Setup (Windows-only) - kurulum dosyası oluşturulamadı'}
✓ Kurulum kılavuzu oluşturuldu
✓ Build raporu oluşturuldu

{'─' * 62}
💾 DİSK KULLANIMı:

dist/ klasörü boyutu: {sum(f.stat().st_size for f in (self.dist_dir / self.app_name).rglob('*')) / (1024 * 1024):.1f} MB
releases/ klasörü boyutu: {sum(f.stat().st_size for f in self.output_dir.rglob('*')) / (1024 * 1024):.1f} MB

{'─' * 62}
📞 DESTEK:

Hata veya soru için: https://github.com/PobloMert/tezgah-takip/issues

═════════════════════════════════════════════════════════════════
"""
        
        report_path = self.output_dir / "BUILD_RAPORU.txt"
        report_path.write_text(report_content, encoding='utf-8')
        print(report_content)
    
    def run(self):
        """Tüm build işlemini çalıştır"""
        import time
        start_time = time.time()
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║     {self.app_name} v{self.version} - EXE Build Sistemi              ║
║  Profesyonel Windows Kurulum Dosyası Oluşturma              ║
╚══════════════════════════════════════════════════════════════╝
""")
        
        # Adım 1: Ortamı hazırla
        self.cleanup()
        
        # Adım 2: Build araçlarını kontrol et
        self.install_build_tools()
        
        # Adım 3: PyInstaller ile EXE oluştur
        exe_success = self.build_exe_with_pyinstaller()
        
        if not exe_success:
            print("\n❌ EXE oluşturma başarısız. Build durduruldu.")
            self.generate_build_report(False, "N/A")
            return
        
        # Adım 4: Setup dosyası oluştur (opsiyonel, Windows-only)
        setup_success = False
        if sys.platform == "win32":
            setup_success = self.build_setup_exe()
        else:
            print("\n⚠️  Inno Setup sadece Windows'ta mevcuttur")
        
        # Adım 5: Açıklama dosyaları oluştur
        self.create_readme()
        
        # Build raporu
        elapsed_time = f"{(time.time() - start_time) / 60:.1f} dakika"
        self.generate_build_report(exe_success or setup_success, elapsed_time)
        
        print("\n🎉 Build işlemi tamamlandı!")
        print(f"   📁 Çıktı klasörü: {self.output_dir.resolve()}")


def main():
    """Ana giriş noktası"""
    try:
        builder = TezgahTakipBuilder()
        builder.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Build iptal edildi (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Ciddi hata: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
