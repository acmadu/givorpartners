; ============================================================
;  Yazar Kasa — Windows Installer (Inno Setup 6)
;  https://jrsoftware.org/isinfo.php
;
;  Kullanım:
;    1. PyInstaller ile önce exe'leri derle (build_all.bat)
;    2. Bu dosyayı Inno Setup Compiler ile aç → Derle
;    3. Output\yazarkasa-setup.exe dağıtıma hazır
; ============================================================

#define AppName    "GivorPartners"
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
DefaultDirName={autopf}\YazarKasa
DefaultGroupName={#AppName}
AllowNoIcons=yes
; Kurulum paketi çıktı dizini ve dosya adı
OutputDir=Output
OutputBaseFilename=yazarkasa-setup-v{#AppVersion}
; Kurulumu sıkıştır
Compression=lzma2/ultra64
SolidCompression=yes
; Windows Vista veya üstü
MinVersion=6.1
; 64-bit kurulum
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
; UAC — yönetici izni ister
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon_merkez"; Description: "Masaüstüne Merkez kısayolu oluştur"; GroupDescription: "Kısayollar:"; Flags: unchecked
Name: "desktopicon_kasa";   Description: "Masaüstüne Kasa kısayolu oluştur";   GroupDescription: "Kısayollar:"
Name: "startup_kasa";       Description: "Windows başlangıcında Kasa'yı otomatik başlat"; GroupDescription: "Otomatik Başlatma:"; Flags: unchecked

[Files]
; Merkez exe (Linux: yazarkasa-merkez, Windows: yazarkasa-merkez.exe)
Source: "..\dist\yazarkasa-merkez*"; DestDir: "{app}"; Flags: ignoreversion
; Kasa exe (Linux: yazarkasa-kasa, Windows: yazarkasa-kasa.exe)
Source: "..\dist\yazarkasa-kasa*";   DestDir: "{app}"; Flags: ignoreversion
; Yapılandırma dosyası (config.json varsa üzerine yazma)
Source: "..\config.json"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist

[Icons]
; Baslat Menusu
Name: "{group}\Merkez Yonetim"; Filename: "{app}\yazarkasa-merkez.exe"
Name: "{group}\Kasa (POS)";     Filename: "{app}\yazarkasa-kasa.exe"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"

; Masaustu kisayollari (istege bagli)
Name: "{autodesktop}\Yazar Kasa Merkez"; Filename: "{app}\yazarkasa-merkez.exe"; Tasks: desktopicon_merkez
Name: "{autodesktop}\Yazar Kasa Kasa";   Filename: "{app}\yazarkasa-kasa.exe";   Tasks: desktopicon_kasa

[Registry]
; Otomatik baslatma
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "YazarKasaKasa"; \
  ValueData: """{app}\yazarkasa-kasa.exe"""; \
  Flags: uninsdeletevalue; Tasks: startup_kasa

[Run]
; Kurulum tamamlaninca Merkez'i ac (istege bagli)
Filename: "{app}\yazarkasa-merkez.exe"; \
  Description: "Yazar Kasa Merkez'i simdi baslat"; \
  Flags: nowait postinstall skipifsilent

[UninstallRun]
; Kaldırma sırasında çalışan uygulamayı durdur
Filename: "taskkill.exe"; Parameters: "/F /IM yazarkasa-merkez.exe /IM yazarkasa-kasa.exe"; \
  Flags: skipifdoesntexist runhidden

[Code]
// Kurulum sırasında config.json'un varlığını bildir
procedure InitializeWizard();
begin
  WizardForm.WelcomeLabel2.Caption :=
    'Bu sihirbaz {#AppName} v{#AppVersion} sürümünü bilgisayarınıza kuracak.'#13#10#13#10 +
    'Devam etmek için İleri''yi tıklayın.';
end;
