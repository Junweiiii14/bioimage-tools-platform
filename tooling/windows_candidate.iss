#ifndef AppSource
  #error AppSource must identify the verified standalone directory
#endif
#ifndef BuildCommit
  #error BuildCommit is required
#endif
#ifndef InstallerOutput
  #error InstallerOutput is required
#endif

[Setup]
AppId=BioImageTools.WB.Candidate
AppName=BioImage WB（候选版）
AppVersion=0.14.0-T047-{#BuildCommit}
AppPublisher=BioImage Tools
DefaultDirName={localappdata}\Programs\BioImage WB Candidate
DefaultGroupName=BioImage WB（候选版）
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#InstallerOutput}
OutputBaseFilename=BioImage-WB-Candidate-T047-{#BuildCommit}-Setup
SetupIconFile={#AppSource}\bioimage.ico
UninstallDisplayIcon={app}\BioImageWB-Candidate.exe
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
CloseApplications=no
RestartApplications=no
DisableProgramGroupPage=yes
VersionInfoVersion=0.14.0.47

[Tasks]
Name: desktopicon; Description: "创建桌面快捷方式"; GroupDescription: "程序入口："
Name: startmenuicon; Description: "创建开始菜单快捷方式"; GroupDescription: "程序入口："

[Files]
Source: "{#AppSource}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userdesktop}\BioImage WB（候选版）"; Filename: "{app}\BioImageWB-Candidate.exe"; WorkingDir: "{app}"; Tasks: desktopicon; AppUserModelID: BioImageTools.WB.Candidate
Name: "{userprograms}\BioImage WB（候选版）\BioImage WB（候选版）"; Filename: "{app}\BioImageWB-Candidate.exe"; WorkingDir: "{app}"; Tasks: startmenuicon; AppUserModelID: BioImageTools.WB.Candidate
Name: "{userprograms}\BioImage WB（候选版）\卸载候选版"; Filename: "{uninstallexe}"; Tasks: startmenuicon

[Run]
Filename: "{app}\BioImageWB-Candidate.exe"; Description: "启动 BioImage WB 候选版"; Flags: nowait postinstall skipifsilent

; No [UninstallDelete] entries: project folders, originals and local settings are retained.
