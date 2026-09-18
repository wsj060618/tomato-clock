; 番茄钟 Inno Setup 脚本
; 编译：iscc /DAppVersion=2.3.0 installer\TomatoClock.iss
; 本文件需为 UTF-8 with BOM

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

#define AppName    "番茄钟"
#define DirName    "TomatoClock"
#define AppExeName "TomatoClock-v" + AppVersion + ".exe"
#define SourceDir  "..\dist\TomatoClock-v" + AppVersion

[Setup]
; AppId 一旦发布不要再改，否则无法识别旧版本做覆盖升级
AppId={{8F3B2C1A-9D4E-4A7B-9C2F-1E5D6A7B8C90}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppName}
DefaultDirName={localappdata}\Programs\{#DirName}
DefaultGroupName={#AppName}
DisableDirPage=no
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist\installer
OutputBaseFilename=TomatoClock-Setup-v{#AppVersion}
SetupIconFile=..\assets\tomato.ico
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "chinesesimplified"; MessagesFile: "ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务："; Flags: checkedonce

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\卸载 {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "立即运行 {#AppName}"; Flags: nowait postinstall skipifsilent

; 卸载只删程序目录（Inno 默认行为）；用户数据在 %USERPROFILE%\.pomodoro_timer，故意保留
