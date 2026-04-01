; Inno Setup 脚本 - VirtualCam Companion 安装包
#define MyAppName "VirtualCam Companion"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "GreenhandTan"
#define MyAppURL "https://github.com/GreenhandTan/virtual-cam-companion"
#define MyAppExeName "VirtualCamCompanion.exe"

[Setup]
AppId={{A7D8E3F2-5B4C-4E6A-9C1D-8F2A3B4C5D6E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\VirtualCam Companion
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer
OutputBaseFilename=VirtualCamCompanion-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "driver\obs-virtualcam-module.dll"; DestDir: "{app}\driver"; Flags: regserver ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "regsvr32"; Parameters: "/s /u ""{app}\driver\obs-virtualcam-module.dll"""; Flags: runhidden
