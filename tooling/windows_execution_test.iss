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
; Separate identity: never upgrade the original or the user's T047/T048 candidates.
AppId=BioImageTools.WB.E7Test
AppName=BioImage WB（图像识别测试版）
AppVersion=0.14.0-T061-{#BuildCommit}
AppPublisher=BioImage Tools
DefaultDirName={localappdata}\Programs\BioImage WB E7 测试版
DefaultGroupName=BioImage WB（图像识别测试版）
PrivilegesRequired=lowest
MinVersion=10.0.17763
ArchitecturesAllowed=x64os
ArchitecturesInstallIn64BitMode=x64os
OutputDir={#InstallerOutput}
OutputBaseFilename=BioImage-WB-x64-T061-Test-{#BuildCommit}-Setup
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
InfoBeforeFile=windows_execution_test_readme.txt
VersionInfoVersion=0.14.0.61

[Files]
Source: "{#AppSource}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userdesktop}\BioImage WB（图像识别测试版）"; Filename: "{app}\BioImageWB-Candidate.exe"; WorkingDir: "{app}"; AppUserModelID: BioImageTools.WB.E7Test
Name: "{userprograms}\BioImage WB（图像识别测试版）\BioImage WB（图像识别测试版）"; Filename: "{app}\BioImageWB-Candidate.exe"; WorkingDir: "{app}"; AppUserModelID: BioImageTools.WB.E7Test
Name: "{userprograms}\BioImage WB（图像识别测试版）\环境自检"; Filename: "{app}\测试版环境自检.cmd"; WorkingDir: "{app}"
Name: "{userprograms}\BioImage WB（图像识别测试版）\卸载测试版"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\BioImageWB-Candidate.exe"; Description: "启动 BioImage WB 测试版"; Flags: nowait postinstall skipifsilent

; Deliberately no UninstallDelete: keep user projects, originals and results.
