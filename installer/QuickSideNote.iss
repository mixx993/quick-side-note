#define MyAppName "Quick Side Note"
#define MyAppVersion "1.2.0"
#define MyAppPublisher "Quick Side Note"
#define MyAppExeName "QuickSideNote.exe"
#define MyAppPackageDir "..\release\QuickSideNote_App_v" + MyAppVersion

[Setup]
AppId={{9D14C1B2-329C-4B85-A2F8-33A87F8BA7F4}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\QuickSideNote
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\release
OutputBaseFilename=QuickSideNote_Setup_v{#MyAppVersion}
SetupIconFile=..\assets\quick_note_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
CloseApplications=yes
CloseApplicationsFilter={#MyAppExeName}
RestartIfNeededByRun=no
InfoBeforeFile=..\docs\README_RUN.txt
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Installer
VersionInfoProductName={#MyAppName}
ShowLanguageDialog=no

[Languages]
Name: "chinesesimplified"; MessagesFile: ".\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "快捷方式："; Flags: unchecked

[Files]
Source: "{#MyAppPackageDir}\QuickSideNote.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppPackageDir}\README_RUN.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppPackageDir}\QuickSideNote_intro.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppPackageDir}\quick_note_ui_preview.png"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Quick Side Note"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\使用说明"; Filename: "{app}\README_RUN.txt"; WorkingDir: "{app}"
Name: "{group}\软件介绍"; Filename: "{app}\QuickSideNote_intro.html"; WorkingDir: "{app}"
Name: "{group}\卸载 Quick Side Note"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Quick Side Note"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 Quick Side Note 并进行首次配置"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\tmp"
