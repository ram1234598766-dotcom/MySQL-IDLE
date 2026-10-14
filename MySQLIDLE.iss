#define MyAppName "MySQL IDLE"
#define MyAppVersion "3.0.0"
#define MyAppPublisher "MySQL IDLE"
#define MyAppExeName "mysql_idle.exe"
#define MyDistDir "dist\mysql_idle"

[Setup]
AppId={{8E9A39E8-9F59-4FA3-AD4E-7B0A54A93F11}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=https://github.com/ram1234598766-dotcom/MySQL-IDLE
AppSupportURL=https://github.com/ram1234598766-dotcom/MySQL-IDLE/issues
AppUpdatesURL=https://github.com/ram1234598766-dotcom/MySQL-IDLE/releases
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=MySQL IDLE SQL Workspace
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
DefaultDirName={localappdata}\Programs\MySQL IDLE
DefaultGroupName=MySQL IDLE
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist\installer
OutputBaseFilename=MySQLIDLE-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern dynamic polar includetitlebar
SetupIconFile=assets\mysqlidle.ico
WizardImageFile=assets\wizard-image.bmp
WizardSmallImageFile=assets\wizard-small.bmp
WizardImageFileDynamicDark=assets\wizard-image.bmp
WizardSmallImageFileDynamicDark=assets\wizard-small.bmp
UninstallDisplayIcon={app}\assets\mysqlidle.ico
SetupLogging=yes
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

; The desktop shortcut is always created so the installed app is easy to find.

[Files]
Source: "{#MyDistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\MySQL IDLE"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\assets\mysqlidle.ico"; IconIndex: 0
Name: "{autodesktop}\MySQL IDLE"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\assets\mysqlidle.ico"; IconIndex: 0

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch MySQL IDLE"; Flags: nowait postinstall skipifsilent


; Installed files are removed by Inno Setup using its file manifest.
; Per-user settings/logs are handled by an explicit opt-in prompt.


[Code]
var
  RemoveUserData: Boolean;

function InitializeUninstall(): Boolean;
begin
  Result := True;
  RemoveUserData := False;

  { Preserve per-user preferences unless an interactive user explicitly opts in. }
  if not UninstallSilent then
    RemoveUserData := MsgBox(
      'Also remove local settings, SQL history (if disk history was enabled), and diagnostic logs for this Windows account?' + #13#10 + #13#10 +
      'Choose No to keep these files. This does not delete MySQL databases, database files, or files outside MySQL IDLE''s own settings locations. The choice to remove settings cannot be undone.',
      mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES;
end;

procedure InitializeUninstallProgressForm();
begin
  if not UninstallSilent then
  begin
    UninstallProgressForm.ProgressBar.Style := npbstMarquee;
    UninstallProgressForm.StatusLabel.Caption := 'Preparing to remove MySQL IDLE...';
  end;
end;
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir: String;
  LegacyConfig: String;
begin
  if CurUninstallStep = usUninstall then
  begin
    if not UninstallSilent then
      UninstallProgressForm.StatusLabel.Caption := 'Removing MySQL IDLE program files and shortcuts...';
  end
  else if CurUninstallStep = usPostUninstall then
  begin
    if RemoveUserData then
    begin
      if not UninstallSilent then
        UninstallProgressForm.StatusLabel.Caption := 'Removing saved settings and diagnostic logs...';

      DataDir := ExpandConstant('{localappdata}\MySQL IDLE');
      if DirExists(DataDir) and not DelTree(DataDir, True, True, True) then
        Log('Some MySQL IDLE settings or log files could not be removed from: ' + DataDir);

      LegacyConfig := ExpandConstant('{userprofile}\.mysql_idle.json');
      if FileExists(LegacyConfig) and not DeleteFile(LegacyConfig) then
        Log('Could not remove legacy MySQL IDLE settings: ' + LegacyConfig);
    end;
    if not UninstallSilent then
      UninstallProgressForm.StatusLabel.Caption := 'Uninstall cleanup finished.';
  end;
end;
