; Inno Setup 脚本 - VirtualCam Companion 安装包
; 编译环境: Inno Setup 6.x

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
LicenseFile=LICENSE
OutputDir=installer
OutputBaseFilename=VirtualCamCompanion-Setup
SetupIconFile=icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "autostart"; Description: "开机自动启动"; GroupDescription: "其他选项:"; Flags: unchecked

[Files]
; 主程序
Source: "dist\VirtualCamCompanion.exe"; DestDir: "{app}"; Flags: ignoreversion
; OBS 虚拟摄像头驱动 (从 pyvirtualcam 提取)
Source: "driver\obs-virtualcam-module.dll"; DestDir: "{app}\driver"; Flags: regserver ignoreversion
; 其他文件
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
; 开机启动
Name: "{autostartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: autostart

[Run]
; 安装完成后运行
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; 卸载前取消注册驱动
Filename: "regsvr32"; Parameters: "/s /u ""{app}\driver\obs-virtualcam-module.dll"""; Flags: runhidden; RunOnceId: "UnregVCam"

[Code]
// 检查是否已安装 OBS Studio（可选提示）
function InitializeSetup(): Boolean;
var
  OBSPath: String;
begin
  Result := True;
  if RegQueryStringValue(HKEY_LOCAL_MACHINE, 'SOFTWARE\OBS Studio', '', OBSPath) then
  begin
    // OBS 已安装，无需额外处理
  end;
end;

// 卸载时清理配置文件
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if MsgBox('是否删除配置文件和用户数据？', mbConfirmation, MB_YESNO) = IDYES then
    begin
      DelTree(ExpandConstant('{app}'), True, True, True);
    end;
  end;
end;
