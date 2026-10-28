#ifndef AppSource
  #error AppSource is required
#endif
#ifndef BuildCommit
  #error BuildCommit is required
#endif
#ifndef InstallerOutput
  #error InstallerOutput is required
#endif

#ifdef AcceptanceId
  #define ProductId "BioImageTools.WB.Acceptance." + AcceptanceId
  #define ProductName "BioImage WB 验收 " + AcceptanceId
  #define ProductExecutable "BioImageWB-Acceptance.exe"
  #define VersionLabel "Acceptance-" + AcceptanceId
  #define InstallerName "BioImage-WB-Acceptance-" + AcceptanceId
  #define ProductReadme AppSource + "\安装与使用说明.txt"
#else
  #define ProductId "BioImageTools.WB.Laboratory"
  #define ProductName "BioImage WB 实验室版"
  #define ProductExecutable "BioImageWB.exe"
  #define VersionLabel "Lab"
  #define InstallerName "BioImage-WB-Lab"
  #define ProductReadme "windows_laboratory_readme.txt"
#endif

[Setup]
AppId={#ProductId}
AppName={#ProductName}
AppVersion=0.14.0-{#VersionLabel}-{#BuildCommit}
AppPublisher=BioImage Tools
DefaultDirName={localappdata}\Programs\{#ProductName}
DefaultGroupName={#ProductName}
PrivilegesRequired=lowest
MinVersion=10.0.17763
ArchitecturesAllowed=x64os
ArchitecturesInstallIn64BitMode=x64os
OutputDir={#InstallerOutput}
OutputBaseFilename={#InstallerName}-Windows-x64-{#BuildCommit}-Setup
SetupIconFile={#AppSource}\bioimage.ico
UninstallDisplayIcon={app}\{#ProductExecutable}
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
CloseApplications=no
RestartApplications=no
DisableProgramGroupPage=yes
DisableWelcomePage=no
DisableDirPage=auto
InfoBeforeFile={#ProductReadme}
VersionInfoVersion=0.14.0.80

[Files]
Source: "{#AppSource}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userdesktop}\{#ProductName}"; Filename: "{app}\{#ProductExecutable}"; WorkingDir: "{app}"; AppUserModelID: {#ProductId}
Name: "{userprograms}\{#ProductName}\{#ProductName}"; Filename: "{app}\{#ProductExecutable}"; WorkingDir: "{app}"; AppUserModelID: {#ProductId}
Name: "{userprograms}\{#ProductName}\环境自检"; Filename: "{app}\环境自检.cmd"; WorkingDir: "{app}"
Name: "{userprograms}\{#ProductName}\安装与使用说明"; Filename: "{app}\安装与使用说明.txt"
Name: "{userprograms}\{#ProductName}\卸载"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\{#ProductExecutable}"; Description: "启动 {#ProductName}"; Flags: nowait postinstall skipifsilent

; No blanket UninstallDelete: user originals, projects and results survive uninstall.
