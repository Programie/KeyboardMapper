EnableExplicit

ImportC "-no-pie"
EndImport

Declare.b IsStringFieldInStringField(string1.s, string2.s, separator1.s, separator2.s)
Declare.b StrToBool(string.s)

IncludeFile "desktop-entry.pbi"
IncludeFile "common.pbi"
IncludeFile "input-handler.pbi"
IncludeFile "CLI_Helper.pbi"

Define defaultConfigDir.s = GetHomeDirectory() + ".config/keyboard-mapper"

CLI_AddOption("c", "config-dir", #True , "path", "path to the config dir (default: " + defaultConfigDir + ")")
CLI_AddOption("h", "help", #False, "", "show this help message")

CLI_ScanCommandline()

If CLI_HasOption("help")
  CLI_Usage()
  End
EndIf

If CLI_HasOption("config-dir")
  configDir = CLI_GetOptionValue("config-dir")
Else
  configDir = defaultConfigDir
EndIf

CreateDirectory(configDir)

configFile = configDir + "/config.ini"
shortcutsFile = configDir + "/shortcuts.ini"

LoadConfig()
LoadShortcutsFromFile()

If OpenConsole()
  If ReadFile(#File_InputDevice, config\keyboardInputDevice, #PB_File_NoBuffering)
    Print("Waiting for input from device " + config\keyboardInputDevice)
    InputEventListener(0)
  Else
    ConsoleError("Can't open keyboard input file: " + config\keyboardInputDevice)
    End 1
  EndIf
EndIf