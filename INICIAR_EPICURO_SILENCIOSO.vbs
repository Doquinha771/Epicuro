Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
base = fso.GetParentFolderName(WScript.ScriptFullName)
cmd = "cmd /c cd /d """ & base & """ && call INICIAR_EPICURO.bat"
shell.Run cmd, 0, False
