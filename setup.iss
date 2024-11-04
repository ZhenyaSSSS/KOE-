[Setup]
AppName=KOE!
AppVersion=1.2 Alpha
AppPublisher=Eugene S
AppPublisherURL=https://github.com/your-username/KOE
AppSupportURL=https://github.com/your-username/KOE/issues
AppUpdatesURL=https://github.com/your-username/KOE/releases
DefaultDirName={autopf}\KOE
DefaultGroupName=KOE!
OutputBaseFilename=KOE!_Setup
Compression=lzma2/ultra64
SolidCompression=yes
SetupIconFile=assets\icons\koe_icon.ico
PrivilegesRequired=lowest
WizardStyle=modern
UninstallDisplayIcon={app}\koe!.exe
OutputDir=installer
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "rus"; MessagesFile: "compiler:Languages\Russian.isl"

[Files]
Source: "main.dist\main.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs
Source: "settings.json"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\KOE!"; Filename: "{app}\koe!.exe"; IconFilename: "{app}\assets\icons\koe_icon.ico"
Name: "{userdesktop}\KOE!"; Filename: "{app}\koe!.exe"; IconFilename: "{app}\assets\icons\koe_icon.ico"; Tasks: desktopicon
Name: "{group}\Удалить KOE!"; Filename: "{uninstallexe}"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительные задания:"; Flags: unchecked

[Run]
Filename: "{app}\koe!.exe"; Description: "Запустить KOE!"; Flags: nowait postinstall skipifsilent