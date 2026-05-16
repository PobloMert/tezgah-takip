; Tezgah Takip Inno Setup Script
; Bu dosya profesyonel bir Windows kurulum dosyası (Setup.exe) oluşturmak için kullanılır.

[Setup]
AppId={{8A7B6C5D-4E3F-2G1H-0I9J-8K7L6M5N4O3P}
AppName=Tezgah Takip
AppVersion=2.1.4
AppPublisher=Tezgah Takip Uygulaması
AppPublisherURL=https://github.com/PobloMert/tezgah-takip
DefaultDirName={autopf}\TezgahTakip
DefaultGroupName=Tezgah Takip
AllowNoIcons=yes
; Kurulum dosyasının çıkış dizini ve adı
OutputDir=dist
OutputBaseFilename=TezgahTakip_Setup_v2.1.4
; Uygulama simgesi
SetupIconFile=tezgah_icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Ana uygulama ve başlatıcı
Source: "dist\TezgahTakip_Launcher.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\TezgahTakip.exe"; DestDir: "{app}"; Flags: ignoreversion
; Yapılandırma dosyaları
Source: "config.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "settings.json"; DestDir: "{app}"; Flags: ignoreversion
; Görsel varlıklar
Source: "tezgah_icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "mtb_logo.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "tezgah_logo.png"; DestDir: "{app}"; Flags: ignoreversion
; Not: Diğer tüm bağımlılıklar PyInstaller tarafından EXE içine gömülmüştür.

[Icons]
; Başlat menüsü ve masaüstü kısayolları (Launcher üzerinden çalıştırılır)
Name: "{group}\Tezgah Takip"; Filename: "{app}\TezgahTakip_Launcher.exe"; IconFilename: "{app}\tezgah_icon.ico"
Name: "{autodesktop}\Tezgah Takip"; Filename: "{app}\TezgahTakip_Launcher.exe"; Tasks: desktopicon; IconFilename: "{app}\tezgah_icon.ico"

[Run]
; Kurulum bittikten sonra uygulamayı başlatma seçeneği
Filename: "{app}\TezgahTakip_Launcher.exe"; Description: "{cm:LaunchProgram,Tezgah Takip}"; Flags: nowait postinstall skipifsilent
