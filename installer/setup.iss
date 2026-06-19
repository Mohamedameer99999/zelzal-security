; AI Task Manager Installer
; Requires Inno Setup 6+ (https://jrsoftware.org/isdl.php)

#define MyAppName "AI Task Manager"
#define MyAppVersion "1.0"
#define MyAppPublisher "Your Company"
#define MyAppURL "http://localhost:5000"
#define MyAppExeName "AiTaskManager.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=.
OutputBaseFilename=AiTaskManager-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "arabic"; MessagesFile: "compiler:Languages\Arabic.isl"

[Dirs]
Name: "{app}\instance"

[Files]
; Application files
Source: "..\*.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\app\*"; DestDir: "{app}\app"; Flags: ignoreversion recursesubdirs
Source: "..\migrations\*"; DestDir: "{app}\migrations"; Flags: ignoreversion recursesubdirs
Source: "..\translations\*"; DestDir: "{app}\translations"; Flags: ignoreversion recursesubdirs
Source: "..\templates\*"; DestDir: "{app}\templates"; Flags: ignoreversion recursesubdirs
Source: "..\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\.env"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
Source: "..\babel.cfg"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\start_server.bat"; DestDir: "{app}"; Flags: ignoreversion

; Include embeddable Python (download from python.org first)
; Source: "python-3.12-embed-amd64\*"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\start_server.bat"; WorkingDir: "{app}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\start_server.bat"; WorkingDir: "{app}"

[Run]
Filename: "{app}\start_server.bat"; Description: "Launch {#MyAppName}"; Flags: postinstall nowait skipifsilent shellexec

[Code]
function InitializeSetup: Boolean;
begin
  Result := True;
end;
