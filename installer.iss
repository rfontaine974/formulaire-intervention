; Script Inno Setup - Template Manager
; Généré pour être compilé avec Inno Setup 6+
; Téléchargement : https://jrsoftware.org/isdl.php
;
; Pour compiler : ouvrir ce fichier avec Inno Setup, ou lancer :
;   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss

#define AppName "Template Manager"
#define AppVersion "1.0"
#define AppPublisher "Rodolphe FONTAINE"
#define AppExeName "TemplateManager.exe"
#define AppDir "{localappdata}\TemplateManager"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\TemplateManager
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=setup_TemplateManager
SetupIconFile=assets\icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#AppExeName}

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le Bureau"; GroupDescription: "Raccourcis :"; Flags: checked
Name: "startupicon"; Description: "Lancer automatiquement au démarrage de Windows"; GroupDescription: "Options :"; Flags: unchecked

[Files]
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Inclure templates.json si déjà créé, sinon il sera créé au 1er lancement
Source: "templates.json"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: startupicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Lancer {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "taskkill"; Parameters: "/f /im {#AppExeName}"; Flags: runhidden waituntilterminated

[Registry]
; Nettoyage du menu contextuel lors de la désinstallation
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\TemplateManager\command"; Flags: deletekey uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\TemplateManager"; Flags: deletekey uninsdeletekey

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Supprimer le dossier restant si vide (templates.json créé par l'app)
    DelTree(ExpandConstant('{app}'), True, True, True);
  end;
end;
