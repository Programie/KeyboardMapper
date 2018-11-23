EnableExplicit

Enumeration
  #File_InputDevice
EndEnumeration

Structure Shortcut
  name.s
  action.s
  actionData.s
EndStructure

Structure Config
  keyboardInputDevice.s
  trayIcon.s
  trayIconEnable.b
EndStructure

Structure InputEvent
  timestamp.b[16]
  type.w
  code.w
  value.b[4]
EndStructure

;- Actions
#Action_LaunchApplication = "launchApplication"
#Action_ExecuteCommand = "executeCommand"
#Action_OpenFolder = "openFolder"
#Action_InputText = "inputText"

Global NewMap shortcuts.Shortcut()
Global NewList applicationList.DesktopEntry()
Global config.Config
Global configDir.s
Global configFile.s
Global shortcutsFile.s
Global inputEventListenerThread
Global inputEventKey
Global allowActionHandling.b = #True
Global appPath.s = GetPathPart(ProgramFilename())

Procedure.b StrToBool(string.s)
  Select LCase(string)
    Case "true"
      ProcedureReturn #True
    Case "false"
      ProcedureReturn #False
    Default
      ProcedureReturn #Null
  EndSelect
EndProcedure

Procedure.s BoolToStr(boolean.b)
  If boolean
    ProcedureReturn "true"
  Else
    ProcedureReturn "false"
  EndIf
EndProcedure

Procedure.b IsStringFieldInStringField(string1.s, string2.s, separator1.s, separator2.s)
  Protected index1
  Protected index2
  
  For index1 = 0 To CountString(string1, separator1)
    Protected field1.s = StringField(string1, index1 + 1, separator1)
    
    For index2 = 0 To CountString(string2, separator2)
      If field1 = StringField(string2, index2 + 1, separator2)
        ProcedureReturn #True
      EndIf
    Next
  Next
  
  ProcedureReturn #False
EndProcedure

Procedure LoadConfig()
  If OpenPreferences(configFile)
    config\keyboardInputDevice = ReadPreferenceString("keyboard-input-device", "")
    config\trayIconEnable = StrToBool(ReadPreferenceString("tray-icon-enable", "true"))
    config\trayIcon = ReadPreferenceString("tray-icon", "dark")
    ClosePreferences()
  EndIf
EndProcedure

Procedure SaveConfig()
  If CreatePreferences(configFile)
    WritePreferenceString("keyboard-input-device", config\keyboardInputDevice)
    WritePreferenceString("tray-icon-enable", BoolToStr(config\trayIconEnable))
    WritePreferenceString("tray-icon", config\trayIcon)
    ClosePreferences()
  EndIf
EndProcedure

Procedure LoadShortcutsFromFile()
  ClearMap(shortcuts())
  
  If OpenPreferences(shortcutsFile)
    ExaminePreferenceGroups()
    While NextPreferenceGroup()
      Protected keyString.s = PreferenceGroupName()
      
      shortcuts(keyString)\name = ReadPreferenceString("name", "")
      shortcuts(keyString)\action = ReadPreferenceString("action", "")
      shortcuts(keyString)\actionData = ReadPreferenceString("data", "")
    Wend
    
    ClosePreferences()
  EndIf
EndProcedure

Procedure SaveShortcutsToFile()
  If CreatePreferences(shortcutsFile, #PB_Preference_GroupSeparator)
    ForEach shortcuts()
      PreferenceGroup(MapKey(shortcuts()))
      
      WritePreferenceString("name", shortcuts()\name)
      WritePreferenceString("action", shortcuts()\action)
      WritePreferenceString("data", shortcuts()\actionData)
    Next
    
    ClosePreferences()
  EndIf
EndProcedure

Procedure.b Invert(boolean.b)
  If boolean
    ProcedureReturn #False
  Else
    ProcedureReturn #True
  EndIf
EndProcedure

Procedure.s ActionToString(action.s)
  Select action
    Case #Action_LaunchApplication
      ProcedureReturn "Launch application"
    Case #Action_ExecuteCommand
      ProcedureReturn "Execute command"
    Case #Action_OpenFolder
      ProcedureReturn "Open folder"
    Case #Action_InputText
      ProcedureReturn "Input text"
  EndSelect
EndProcedure
