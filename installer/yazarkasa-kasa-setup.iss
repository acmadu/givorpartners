; ============================================================
;  GivorPartners Kasa (POS) — Windows Installer (Inno Setup 6)
;  https://jrsoftware.org/isinfo.php
;
;  Kullanım:
;    1. PyInstaller ile önce exe derle (build_pos.bat)
;    2. Bu dosyayı Inno Setup Compiler ile aç → Derle
;    3. Output\yazarkasa-kasa-setup.exe bayilere gönder
; ============================================================

#define AppName    "GivorPartners Kasa"
#define AppVersion "1.0.0"
#define Publisher  "GivorPartners"
#define AppURL     "https://givorpartners.com"

[Setup]
AppId={{B5E8D3F1-4C9E-5G7F-B0D6-3E2F1G9C8B74}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} v{#AppVersion}
AppPublisher={#Publisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
DefaultDirName={autopf}\GivorPartners\Kasa
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=Output
OutputBaseFilename=yazarkasa-kasa-setup-v{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
MinVersion=6.1
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaustu kisayol olustur"; GroupDescription: "Kisayollar:"
Name: "startup";     Description: "Windows baslangicindan otomatik baslat"; GroupDescription: "Otomatik Baslatma:"

[Files]
; Kasa exe
Source: "..\dist\yazarkasa-kasa.exe"; DestDir: "{app}"; Flags: ignoreversion
; Config template
Source: "..\config.json.example"; DestDir: "{app}"; DestName: "config.json"; Flags: onlyifdoesntexist
; Rehberler
Source: "..\BAYILERE_DEPLOYMENT_REHBERI.md"; DestDir: "{app}"
Source: "..\KURULUM_REHBERI.md"; DestDir: "{app}"
Source: "..\README.md"; DestDir: "{app}"

[Icons]
; Başlat Menüsü
Name: "{group}\{#AppName}"; Filename: "{app}\yazarkasa-kasa.exe"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"

; Masaüstü kısayolu
Name: "{autodesktop}\GivorPartners Kasa"; Filename: "{app}\yazarkasa-kasa.exe"; Tasks: desktopicon

[Registry]
; Otomatik başlatma
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "GivorPartnersKasa"; \
  ValueData: """{app}\yazarkasa-kasa.exe"""; \
  Flags: uninsdeletevalue; Tasks: startup

[Run]
; Kurulum tamamlandıkça Kasa'yı aç
Filename: "{app}\yazarkasa-kasa.exe"; \
  Description: "Kasa'yi simdi baslat"; \
  Flags: nowait postinstall skipifsilent
