; Inno Setup script: wraps dist\District Lookup\ in a Windows installer.
;     iscc /DAppVersion=1.0.0 packaging\windows\district_lookup.iss
; Installs for the current user only, so no administrator password is needed.
; Running a newer installer over an older one updates it in place.

#ifndef AppVersion
  #error Pass the version: iscc /DAppVersion=1.2.3 ...
#endif

[Setup]
; Never change AppId: it's how a new installer recognizes an older install to update.
AppId={{DFD5EDCE-0D25-4423-B4C6-E9EB471415DC}
AppName=District Lookup
AppVersion={#AppVersion}
AppVerName=District Lookup {#AppVersion}
AppPublisher=Drew Siegler
AppPublisherURL=https://github.com/drewsiegler/district-lookup
AppSupportURL=https://github.com/drewsiegler/district-lookup/issues
AppUpdatesURL=https://github.com/drewsiegler/district-lookup/releases/latest
DefaultDirName={autopf}\District Lookup
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\..\dist
OutputBaseFilename=District-Lookup-{#AppVersion}-windows-setup
SetupIconFile=..\..\assets\AppIcon.ico
UninstallDisplayIcon={app}\District Lookup.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; An update closes a copy that's still open before replacing its files.
CloseApplications=yes

[Tasks]
Name: "desktopicon"; Description: "Put a District Lookup shortcut on the desktop"

[InstallDelete]
; Clear out the previous version's files, so nothing stale is left behind.
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "..\..\dist\District Lookup\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\District Lookup"; Filename: "{app}\District Lookup.exe"
Name: "{autodesktop}\District Lookup"; Filename: "{app}\District Lookup.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\District Lookup.exe"; Description: "Open District Lookup now"; Flags: nowait postinstall skipifsilent
