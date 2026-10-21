[Setup]
AppName=YAVIS
AppVersion=1.0
DefaultDirName={autopf}\YAVIS
DefaultGroupName=YAVIS
OutputBaseFilename=YAVIS-Setup
OutputDir=installer
Compression=lzma2
PrivilegesRequired=lowest
[Files]
Source: "dist\YAVIS\*"; DestDir: "{app}"; Flags: recursesubdirs
[Icons]
Name: "{autodesktop}\YAVIS"; Filename: "{app}\YAVIS.exe"
Name: "{group}\YAVIS"; Filename: "{app}\YAVIS.exe"
Name: "{userstartup}\YAVIS"; Filename: "{app}\YAVIS.exe"; Tasks: autostart
[Tasks]
Name: "autostart"; Description: "Mit Windows starten"; Flags: unchecked
[Run]
Filename: "{app}\YAVIS.exe"; Description: "YAVIS starten"; Flags: nowait postinstall skipifsilent
