#ifndef AppSource
  #error AppSource is required
#endif
#ifndef BuildCommit
  #error BuildCommit is required
#endif
#ifndef InstallerOutput
  #error InstallerOutput is required
#endif

[Setup]
AppId=BioImageTools.WB.Laboratory
AppName=BioImage WB 实验室版
AppVersion=0.14.0-Lab-{#BuildCommit}
AppPublisher=BioImage Tools
DefaultDirName={localappdata}\Programs\BioImage WB 实验室版
DefaultGroupName=BioImage WB 实验室版
PrivilegesRequired=lowest
MinVersion=10.0.17763
ArchitecturesAllowed=x64os
ArchitecturesInstallIn64BitMode=x64os
OutputDir={#InstallerOutput}
OutputBaseFilename=BioImage-WB-Lab-Windows-x64-{#BuildCommit}-Setup
SetupIconFile={#AppSource}\bioimage.ico
UninstallDisplayIcon={app}\BioImageWB.exe
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
CloseApplications=no
RestartApplications=no
DisableProgramGroupPage=yes
DisableWelcomePage=no
DisableDirPage=auto
InfoBeforeFile=windows_laboratory_readme.txt
VersionInfoVersion=0.14.0.79

[Files]
Source: "{#AppSource}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userdesktop}\BioImage WB 实验室版"; Filename: "{app}\BioImageWB.exe"; WorkingDir: "{app}"; AppUserModelID: BioImageTools.WB.Laboratory
Name: "{userprograms}\BioImage WB 实验室版\BioImage WB 实验室版"; Filename: "{app}\BioImageWB.exe"; WorkingDir: "{app}"; AppUserModelID: BioImageTools.WB.Laboratory
Name: "{userprograms}\BioImage WB 实验室版\环境自检"; Filename: "{app}\环境自检.cmd"; WorkingDir: "{app}"
Name: "{userprograms}\BioImage WB 实验室版\安装与使用说明"; Filename: "{app}\安装与使用说明.txt"
Name: "{userprograms}\BioImage WB 实验室版\卸载"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\BioImageWB.exe"; Description: "启动 BioImage WB 实验室版"; Flags: nowait postinstall skipifsilent

; No blanket UninstallDelete: user originals, projects and results survive uninstall.
