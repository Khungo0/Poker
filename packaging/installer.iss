[Setup]
AppId={{C671E21D-9DF7-4BF3-B14A-9C307A1D96C2}
AppName=Spin Population Lab
AppVersion=0.4.0
DefaultDirName={localappdata}\Programs\SpinPopulationLab
DefaultGroupName=Spin Population Lab
PrivilegesRequired=lowest
OutputDir=..\dist\installer
OutputBaseFilename=SpinPopulationLab-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\SpinPopulationLab.exe

[Files]
Source: "..\dist\SpinPopulationLab\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Spin Population Lab"; Filename: "{app}\SpinPopulationLab.exe"
Name: "{autodesktop}\Spin Population Lab"; Filename: "{app}\SpinPopulationLab.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; Flags: unchecked

[Run]
Filename: "{app}\SpinPopulationLab.exe"; Description: "Abrir Spin Population Lab"; Flags: nowait postinstall skipifsilent
