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
  #Gadget_KeyRequester_Cancel
  #Gadget_Settings_KeyboardInputDevice_Frame
  #Gadget_Settings_KeyboardInputDevice_List
  #Gadget_Settings_Tray_Frame
  #Gadget_Settings_Tray_Enable
  #Gadget_Settings_Tray_DarkTheme
  #Gadget_Settings_Save
  #Gadget_Settings_Cancel
EndEnumeration

Enumeration
  #File_InputDevice
EndEnumeration

Enumeration
  #Systray
EndEnumeration

Enumeration
  #TrayIcon_Menu_Show
  #TrayIcon_Menu_Quit
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
Global quit.b
Global appIndicator
Global appPath.s = GetPathPart(ProgramFilename())

ImportC ""
  gtk_menu_item_new_with_label.i(label.p-utf8)
  g_signal_connect_data.i(*instance, detailed_signal.p-utf8, *c_handler, *data_=0, *destroy_data=0, *connect_flags=0)
EndImport

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
    TextGadget(#Gadget_KeyRequester_Text, 10, 10, 180, 50, "Press the key to use.", #PB_Text_Center)
    ButtonGadget(#Gadget_KeyRequester_Cancel, 10, 60, 180, 30, "Cancel")
    
    DisableWindow(#Window_EditShortcut, #True)
    DisableWindow(#Window_KeyRequester, #False); With QT5 the child window is disabled after disabling the parent
    
    Repeat
      Select WaitWindowEvent(10)
        Case #PB_Event_Gadget
          Select EventGadget()
            Case #Gadget_KeyRequester_Cancel
              Break
          EndSelect
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
