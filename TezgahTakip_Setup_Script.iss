; Tezgah Takip Inno Setup Script

[Setup]
AppId={{8A7B6C5D-4E3F-2G1H-0I9J-8K7L6M5N4O3P}
AppName=Tezgah Takip
AppVersion=2.1.4
AppPublisher=Tezgah Takip Uygulaması
AppPublisherURL=https://github.com/PobloMert/tezgah-takip
DefaultDirName={autopf}\TezgahTakip
DefaultGroupName=Tezgah Takip
AllowNoIcons=yes
OutputDir=dist
OutputBaseFilename=TezgahTakip_Setup_v2.1.4
SetupIconFile=tezgah_icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\TezgahTakip_Launcher.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\TezgahTakip.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "config.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "settings.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "tezgah_icon.ico"; DestDir: "{app}"; Flags: ignoreversion
; Diğer gerekli dosyaları buraya ekleyin (ikonlar, resimler vb.)

[Icons]
Name: "{group}\Tezgah Takip"; Filename: "{app}\TezgahTakip_Launcher.exe"
Name: "{autodesktop}\Tezgah Takip"; Filename: "{app}\TezgahTakip_Launcher.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\TezgahTakip_Launcher.exe"; Description: "{cm:LaunchProgram,Tezgah Takip}"; Flags: nowait postinstall skipifsilent
