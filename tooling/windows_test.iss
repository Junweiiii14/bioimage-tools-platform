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
; Separate identity: never upgrade the original or the user's T047 candidate.
AppId=BioImageTools.WB.Win10Test
AppName=BioImage WB（测试版）
AppVersion=0.14.0-T048-{#BuildCommit}
AppPublisher=BioImage Tools
DefaultDirName={localappdata}\Programs\BioImage WB Test
DefaultGroupName=BioImage WB（测试版）
PrivilegesRequired=lowest
MinVersion=10.0.17763
ArchitecturesAllowed=x64os
ArchitecturesInstallIn64BitMode=x64os
OutputDir={#InstallerOutput}
OutputBaseFilename=BioImage-WB-Win10-x64-Test-T048-{#BuildCommit}-Setup
SetupIconFile={#AppSource}\bioimage.ico
UninstallDisplayIcon={app}\BioImageWB-Candidate.exe
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
CloseApplications=no
RestartApplications=no
DisableProgramGroupPage=yes
DisableWelcomePage=yes
DisableDirPage=yes
InfoBeforeFile=windows_test_readme.txt
VersionInfoVersion=0.14.0.48

[Files]
Source: "{#AppSource}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userdesktop}\BioImage WB（测试版）"; Filename: "{app}\BioImageWB-Candidate.exe"; WorkingDir: "{app}"; AppUserModelID: BioImageTools.WB.Win10Test
Name: "{userprograms}\BioImage WB（测试版）\BioImage WB（测试版）"; Filename: "{app}\BioImageWB-Candidate.exe"; WorkingDir: "{app}"; AppUserModelID: BioImageTools.WB.Win10Test
Name: "{userprograms}\BioImage WB（测试版）\环境自检"; Filename: "{app}\测试版环境自检.cmd"; WorkingDir: "{app}"
Name: "{userprograms}\BioImage WB（测试版）\卸载测试版"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\BioImageWB-Candidate.exe"; Description: "启动 BioImage WB 测试版"; Flags: nowait postinstall skipifsilent

; Deliberately no UninstallDelete: keep user projects, originals and results.
