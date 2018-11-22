EnableExplicit

;- Windows
Enumeration
  #Window_Main
  #Window_EditShortcut
  #Window_KeyRequester
  #Window_Settings
EndEnumeration

;- Menus
Enumeration
  #Menu_Main
EndEnumeration

;- Toolbars
Enumeration
  #Toolbar_Main
EndEnumeration

;- Menu items
Enumeration
  #Menu_Settings
  #Menu_Quit
  #Menu_AddShortcut
  #Menu_EditShortcut
  #Menu_RemoveShortcut
  #Menu_EditShortcut_Save
  #Menu_EditShortcut_Cancel
  #Menu_Settings_Close
EndEnumeration

;- Gadgets
Enumeration
  #Gadget_ShortcutList
  #Gadget_EditShortcut_Shortcut_Frame
  #Gadget_EditShortcut_Shortcut
  #Gadget_EditShortcut_Name_Frame
  #Gadget_EditShortcut_Name
  #Gadget_EditShortcut_Action_Frame
  #Gadget_EditShortcut_Action_ExecuteCommand
  #Gadget_EditShortcut_Action_ExecuteCommand_CommandLine
  #Gadget_EditShortcut_Action_OpenFolder
  #Gadget_EditShortcut_Action_OpenFolder_Path
  #Gadget_EditShortcut_Action_OpenFolder_Browse
  #Gadget_EditShortcut_Action_InputText
  #Gadget_EditShortcut_Action_InputText_Text
  #Gadget_EditShortcut_Save
  #Gadget_EditShortcut_Cancel
  #Gadget_KeyRequester_Text
  #Gadget_Settings_KeyboardInputDevice
  #Gadget_Settings_KeyboardInputDevice_Path
  #Gadget_Settings_KeyboardInputDevice_Browse
EndEnumeration

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
EndStructure

Structure InputEvent
  timestamp.b[16]
  type.w
  code.w
  value.b[4]
EndStructure

;- Actions
#Action_ExecuteCommand = "executeCommand"
#Action_OpenFolder = "openFolder"
#Action_InputText = "inputText"

Global NewMap shortcuts.Shortcut()
Global config.Config
Global configDir.s
Global configFile.s
Global shortcutsFile.s
Global editShortcutItem
Global inputEventListenerThread
Global inputEventKey
Global allowActionHandling.b = #True

Procedure LoadConfig()
  If OpenPreferences(configFile)
    config\keyboardInputDevice = ReadPreferenceString("keyboard-input-device", "")
    ClosePreferences()
  EndIf
EndProcedure

Procedure SaveConfig()
  If CreatePreferences(configFile)
    WritePreferenceString("keyboard-input-device", config\keyboardInputDevice)
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
    Case #Action_ExecuteCommand
      ProcedureReturn "Execute command"
    Case #Action_OpenFolder
      ProcedureReturn "Open folder"
    Case #Action_InputText
      ProcedureReturn "Input text"
  EndSelect
EndProcedure

Procedure KeyRequester()
  inputEventKey = 0
  
  Protected newKey
  
  If OpenWindow(#Window_KeyRequester, 0, 0, 200, 100, "Configure key", #PB_Window_WindowCentered, WindowID(#Window_EditShortcut))
    TextGadget(#Gadget_KeyRequester_Text, 10, 10, 180, 80, "Press the key to use.", #PB_Text_Center)
    
    DisableWindow(#Window_EditShortcut, #True)
    
    Repeat
      Select WaitWindowEvent(10)
        Case #PB_Event_CloseWindow
          If EventWindow() = #Window_KeyRequester
            Break
          EndIf
      EndSelect
      
      If inputEventKey
        newKey = inputEventKey
        Break
      EndIf
    ForEver
    
    CloseWindow(#Window_KeyRequester)
    DisableWindow(#Window_EditShortcut, #False)
  EndIf
  
  ProcedureReturn newKey
EndProcedure
; IDE Options = PureBasic 5.62 (Linux - x64)
; Folding = --
; EnableXP