; ============================================================
;  GivorPartners Merkez Yönetim — Windows Installer (Inno Setup 6)
;  https://jrsoftware.org/isinfo.php
;
;  Kullanım:
;    1. PyInstaller ile önce exe derle (build_center.bat)
;    2. Bu dosyayı Inno Setup Compiler ile aç → Derle
;    3. Output\yazarkasa-merkez-setup.exe dağıtıma hazır
; ============================================================

#define AppName    "GivorPartners Merkez"
#define AppVersion "1.0.0"
#define Publisher  "GivorPartners"
#define AppURL     "https://givorpartners.com"

[Setup]
AppId={{E4F7C1A2-3B8D-4F6E-A9C5-2D1E0F8B7A63}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} v{#AppVersion}
AppPublisher={#Publisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
DefaultDirName={autopf}\GivorPartners\Merkez
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=Output
OutputBaseFilename=yazarkasa-merkez-setup-v{#AppVersion}
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
Name: "desktopicon"; Description: "Masaüstüne kısayol oluştur"; GroupDescription: "Kisayollar:"
Name: "startup";     Description: "Windows baslangicinда otomatik baslat"; GroupDescription: "Otomatik Baslatma:"

[Files]
; Merkez exe
Source: "..\dist\yazarkasa-merkez.exe"; DestDir: "{app}"; Flags: ignoreversion
; Config template
Source: "..\config.json.example"; DestDir: "{app}"; DestName: "config.json"; Flags: onlyifdoesntexist
; Rehberler
Source: "..\BAYILERE_DEPLOYMENT_REHBERI.md"; DestDir: "{app}"
Source: "..\KURULUM_REHBERI.md"; DestDir: "{app}"
Source: "..\TEKNIK_ANALIZ.md"; DestDir: "{app}"
Source: "..\README.md"; DestDir: "{app}"

[Icons]
; Başlat Menüsü
Name: "{group}\{#AppName}"; Filename: "{app}\yazarkasa-merkez.exe"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"

; Masaüstü kısayolu
Name: "{autodesktop}\GivorPartners Merkez"; Filename: "{app}\yazarkasa-merkez.exe"; Tasks: desktopicon

[Registry]
; Otomatik başlatma
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "GivorPartnersMerkez"; \
  ValueData: """{app}\yazarkasa-merkez.exe"""; \
  Flags: uninsdeletevalue; Tasks: startup

[Run]
; Kurulum tamamlandıkça Merkez'i aç
Filename: "{app}\yazarkasa-merkez.exe"; \
  Description: "Merkez Yönetimini simdi baslat"; \
  Flags: nowait postinstall skipifsilent
