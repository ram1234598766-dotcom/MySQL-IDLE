#define MyAppName "MySQL IDLE"
#define MyAppVersion "3.0.0"
#define MyAppPublisher "MySQL IDLE"
#define MyAppExeName "mysql_idle.exe"
#define MyDistDir "dist\mysql_idle"

[Setup]
AppId={{8E9A39E8-9F59-4FA3-AD4E-7B0A54A93F11}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\MySQL IDLE
DefaultGroupName=MySQL IDLE
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist\installer
OutputBaseFilename=MySQLIDLE-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupLogging=yes
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "{#MyDistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\MySQL IDLE"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\MySQL IDLE"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch MySQL IDLE"; Flags: nowait postinstall skipifsilent
