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

IncludeFile "CLI_Helper.pbi"

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

Procedure ExecuteActionForKey(key)
  Protected keyString.s = Str(key)
  
  If Not FindMapElement(shortcuts(), keyString)
    ProcedureReturn
  EndIf
  
  Protected shortcut.Shortcut = shortcuts(keyString)
  
  Select shortcut\action
    Case #Action_ExecuteCommand
      Protected firstSpace = FindString(shortcut\actionData, " ")
      Protected program.s
      Protected parameters.s
      
      If firstSpace = 0
        program = shortcut\actionData
        parameters = ""
      Else
        program = Mid(shortcut\actionData, 1, firstSpace - 1)
        parameters = Mid(shortcut\actionData, firstSpace + 1)
      EndIf
      
      RunProgram(program, parameters, "")
    Case #Action_OpenFolder
      RunProgram("xdg-open", shortcut\actionData, "")
    Case #Action_InputText
      ; TODO: Send keys to active application
  EndSelect
EndProcedure

Procedure InputEventListener(*param)
  Protected inputEvent.InputEvent
  
  Repeat
    ReadData(#File_InputDevice, inputEvent, SizeOf(InputEvent))
    
    ; Skip non-key press/release events
    If inputEvent\type <> 1
      Continue
    EndIf
    
    ; value 0 = key released
    ; value 1 = key pressed
    If inputEvent\value <> 0
      Continue
    EndIf
    
    inputEventKey = inputEvent\code
    
    If allowActionHandling
      ExecuteActionForKey(inputEvent\code)
    EndIf
  ForEver
EndProcedure

Procedure.b RestartInputEventListener()
  If config\keyboardInputDevice = ""
    ProcedureReturn #False
  EndIf
  
  If IsThread(inputEventListenerThread)
    KillThread(inputEventListenerThread)
  EndIf
  
  If ReadFile(#File_InputDevice, config\keyboardInputDevice, #PB_File_NoBuffering)
    inputEventListenerThread = CreateThread(@InputEventListener(), 0)
    
    ProcedureReturn #True
  Else
    ProcedureReturn #False
  EndIf
EndProcedure

Procedure UpdateShortcutActionState()
  DisableGadget(#Gadget_EditShortcut_Action_ExecuteCommand_CommandLine, Invert(GetGadgetState(#Gadget_EditShortcut_Action_ExecuteCommand)))
  DisableGadget(#Gadget_EditShortcut_Action_OpenFolder_Path, Invert(GetGadgetState(#Gadget_EditShortcut_Action_OpenFolder)))
  DisableGadget(#Gadget_EditShortcut_Action_OpenFolder_Browse, Invert(GetGadgetState(#Gadget_EditShortcut_Action_OpenFolder)))
  DisableGadget(#Gadget_EditShortcut_Action_InputText_Text, Invert(GetGadgetState(#Gadget_EditShortcut_Action_InputText)))
EndProcedure

Procedure UpdateListEntry(item, shortcut)
  If item = -1
    AddGadgetItem(#Gadget_ShortcutList, -1, shortcuts(Str(shortcut))\name)
    item = CountGadgetItems(#Gadget_ShortcutList) - 1
  Else
    SetGadgetItemText(#Gadget_ShortcutList, item, shortcuts(Str(shortcut))\name)
  EndIf
  
  SetGadgetItemText(#Gadget_ShortcutList, item, ActionToString(shortcuts(Str(shortcut))\action) + ": " + shortcuts(Str(shortcut))\actionData, 1)
  SetGadgetItemText(#Gadget_ShortcutList, item, Str(shortcut), 2)
  SetGadgetItemData(#Gadget_ShortcutList, item, shortcut)
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

Procedure SaveShortcut()
  Protected shortcut.Shortcut
  Protected key = GetGadgetData(#Gadget_EditShortcut_Shortcut)
  Protected oldKey = -1
  
  If Not key
    MessageRequester("Missing shortcut", "Please specify a shortcut to use!", #PB_MessageRequester_Error)
    ProcedureReturn #False
  EndIf
  
  If editShortcutItem <> -1
    oldKey = GetGadgetItemData(#Gadget_ShortcutList, editShortcutItem)
  EndIf
  
  Protected item
  For item = 0 To CountGadgetItems(#Gadget_ShortcutList) - 1
    If item = editShortcutItem
      Continue
    EndIf
    
    If GetGadgetItemData(#Gadget_ShortcutList, item) = key
      MessageRequester("Duplicate entry", "An entry for shortcut '" + Str(key) + "' already exists!", #PB_MessageRequester_Error)
      ProcedureReturn #False
    EndIf
  Next
  
  shortcut\name = GetGadgetText(#Gadget_EditShortcut_Name)
  
  If GetGadgetState(#Gadget_EditShortcut_Action_ExecuteCommand)
    shortcut\action = #Action_ExecuteCommand
    shortcut\actionData = Trim(GetGadgetText(#Gadget_EditShortcut_Action_ExecuteCommand_CommandLine))
    
    If shortcut\actionData = ""
      MessageRequester("Missing command", "Please specify the command to execute!", #PB_MessageRequester_Error)
      ProcedureReturn #False
    EndIf
  ElseIf GetGadgetState(#Gadget_EditShortcut_Action_OpenFolder)
    shortcut\action = #Action_OpenFolder
    shortcut\actionData = GetGadgetText(#Gadget_EditShortcut_Action_OpenFolder_Path)
    
    If shortcut\actionData = ""
      MessageRequester("Missing folder path", "Please selected the path to the folder to open!", #PB_MessageRequester_Error)
      ProcedureReturn #False
    EndIf
  ElseIf GetGadgetState(#Gadget_EditShortcut_Action_InputText)
    shortcut\action = #Action_InputText
    shortcut\actionData = GetGadgetText(#Gadget_EditShortcut_Action_InputText_Text)
    
    If shortcut\actionData = ""
      MessageRequester("Missing text", "Please specify the text to input!", #PB_MessageRequester_Error)
      ProcedureReturn #False
    EndIf
  EndIf
  
  If oldKey <> -1 And oldKey <> key
    DeleteMapElement(shortcuts(), Str(oldKey))
  EndIf
  
  shortcuts(Str(key)) = shortcut
  
  UpdateListEntry(editShortcutItem, key)
  SaveShortcutsToFile()
  
  ProcedureReturn #True
EndProcedure

Procedure EditShortcut(item)
  If config\keyboardInputDevice = ""
    MessageRequester("Missing keyboard input device", "Please configure the input device to use first!", #PB_MessageRequester_Error)
    ProcedureReturn
  EndIf
  
  Protected windowTitle.s
  Protected shortcut.Shortcut
  Protected shortcutKey
  Protected shortcutText.s
  Protected name.s
  
  editShortcutItem = item
  
  If editShortcutItem = -1
    windowTitle = "Add shortcut"
    shortcutText = "Press to set shortcut"
    name = ""
  Else
    windowTitle = "Edit shortcut"
    
    shortcutKey = GetGadgetItemData(#Gadget_ShortcutList, editShortcutItem)
    shortcut = shortcuts(Str(shortcutKey))
    shortcutText = "Key " + Str(shortcutKey)
    name = shortcut\name
  EndIf
  
  If OpenWindow(#Window_EditShortcut, 0, 0, 600, 320, windowTitle, #PB_Window_WindowCentered, WindowID(#Window_Main))
    FrameGadget(#Gadget_EditShortcut_Shortcut_Frame, 10, 10, 580, 60, "Shortcut")
    ButtonGadget(#Gadget_EditShortcut_Shortcut, 20, 30, 560, 20, shortcutText)
    
    FrameGadget(#Gadget_EditShortcut_Name_Frame, 10, 80, 580, 60, "Name")
    StringGadget(#Gadget_EditShortcut_Name, 20, 100, 560, 20, name)
    
    FrameGadget(#Gadget_EditShortcut_Action_Frame, 10, 150, 580, 120, "Action")
    OptionGadget(#Gadget_EditShortcut_Action_ExecuteCommand, 20, 170, 0, 20, "Execute command")
    OptionGadget(#Gadget_EditShortcut_Action_OpenFolder, 20, 200, 0, 20, "Open folder")
    OptionGadget(#Gadget_EditShortcut_Action_InputText, 20, 230, 0, 20, "Input text")
    StringGadget(#Gadget_EditShortcut_Action_ExecuteCommand_CommandLine, 200, 170, 380, 20, "")
    StringGadget(#Gadget_EditShortcut_Action_OpenFolder_Path, 200, 200, 250, 20, "", #PB_String_ReadOnly)
    ButtonGadget(#Gadget_EditShortcut_Action_OpenFolder_Browse, 460, 200, 0, 20, "Browse...")
    StringGadget(#Gadget_EditShortcut_Action_InputText_Text, 200, 300, 380, 20, "")
    
    ButtonGadget(#Gadget_EditShortcut_Save, 380, 280, 100, 30, "Save")
    ButtonGadget(#Gadget_EditShortcut_Cancel, 490, 280, 100, 30, "Cancel")
    
    AddKeyboardShortcut(#Window_EditShortcut, #PB_Shortcut_Return, #Menu_EditShortcut_Save)
    AddKeyboardShortcut(#Window_EditShortcut, #PB_Shortcut_Escape, #Menu_EditShortcut_Cancel)
    
    Select shortcut\action
      Case #Action_ExecuteCommand
        SetGadgetState(#Gadget_EditShortcut_Action_ExecuteCommand, #True)
        SetGadgetText(#Gadget_EditShortcut_Action_ExecuteCommand_CommandLine, shortcut\actionData)
      Case #Action_OpenFolder
        SetGadgetState(#Gadget_EditShortcut_Action_OpenFolder, #True)
        SetGadgetText(#Gadget_EditShortcut_Action_OpenFolder_Path, shortcut\actionData)
      Case #Action_InputText
        SetGadgetState(#Gadget_EditShortcut_Action_InputText, #True)
        SetGadgetText(#Gadget_EditShortcut_Action_InputText_Text, shortcut\actionData)
    EndSelect
    
    SetGadgetData(#Gadget_EditShortcut_Shortcut, shortcutKey)
    
    UpdateShortcutActionState()
    
    DisableWindow(#Window_Main, #True)
    
    allowActionHandling = #False
    
    Repeat
      Select WaitWindowEvent()
        Case #PB_Event_Menu
          Select EventMenu()
            Case #Menu_EditShortcut_Save
              If SaveShortcut()
                Break
              EndIf
            Case #Menu_EditShortcut_Cancel
              Break
          EndSelect
        Case #PB_Event_Gadget
          Select EventGadget()
            Case #Gadget_EditShortcut_Shortcut
              Protected newKey = KeyRequester()
              If newKey
                SetGadgetData(#Gadget_EditShortcut_Shortcut, newKey)
                SetGadgetText(#Gadget_EditShortcut_Shortcut, "Key " + Str(newKey))
              EndIf
            Case #Gadget_EditShortcut_Action_ExecuteCommand
              UpdateShortcutActionState()
            Case #Gadget_EditShortcut_Action_OpenFolder
              UpdateShortcutActionState()
            Case #Gadget_EditShortcut_Action_InputText
              UpdateShortcutActionState()
            Case #Gadget_EditShortcut_Action_OpenFolder_Browse
              Protected path.s = PathRequester("Select the folder to open", GetGadgetText(#Gadget_EditShortcut_Action_OpenFolder_Path))
              If path
                SetGadgetText(#Gadget_EditShortcut_Action_OpenFolder_Path, path)
              EndIf
            Case #Gadget_EditShortcut_Save
              If SaveShortcut()
                Break
              EndIf
            Case #Gadget_EditShortcut_Cancel
              Break
          EndSelect
        Case #PB_Event_CloseWindow
          If EventWindow() = #Window_EditShortcut
            Break
          EndIf
      EndSelect
    ForEver
    
    CloseWindow(#Window_EditShortcut)
    DisableWindow(#Window_Main, #False)
    
    allowActionHandling = #True
  EndIf
EndProcedure

Procedure UpdateMainGadgetSizes()
  ResizeGadget(#Gadget_ShortcutList, 10, 10, WindowWidth(#Window_Main) - 20, WindowHeight(#Window_Main) - ToolBarHeight(#Toolbar_Main) - MenuHeight() - 20)
EndProcedure

Procedure OpenSettingsWindow()
  If OpenWindow(#Window_Settings, 0, 0, 400, 100, "Settings", #PB_Window_WindowCentered, WindowID(#Window_Main))
    FrameGadget(#Gadget_Settings_KeyboardInputDevice, 10, 10, 380, 60, "Keyboard input device")
    StringGadget(#Gadget_Settings_KeyboardInputDevice_Path, 20, 30, 260, 20, config\keyboardInputDevice, #PB_String_ReadOnly)
    ButtonGadget(#Gadget_Settings_KeyboardInputDevice_Browse, 290, 30, 0, 20, "Browse...")
    
    AddKeyboardShortcut(#Window_Settings, #PB_Shortcut_Escape, #Menu_Settings_Close)
    
    DisableWindow(#Window_Main, #True)
    
    Repeat
      Select WaitWindowEvent()
        Case #PB_Event_Menu
          Select EventMenu()
            Case #Menu_Settings_Close
              Break
          EndSelect
        Case #PB_Event_Gadget
          Select EventGadget()
            Case #Gadget_Settings_KeyboardInputDevice_Browse
              Protected file.s = OpenFileRequester("Select keyboard input device file", GetGadgetText(#Gadget_Settings_KeyboardInputDevice_Path), "*.*", 0)
              If file
                config\keyboardInputDevice = file
                SetGadgetText(#Gadget_Settings_KeyboardInputDevice_Path, file)
                SaveConfig()
                RestartInputEventListener()
              EndIf
          EndSelect
        Case #PB_Event_CloseWindow
          If EventWindow() = #Window_Settings
            Break
          EndIf
      EndSelect
    ForEver
    
    CloseWindow(#Window_Settings)
    DisableWindow(#Window_Main, #False)
  EndIf
EndProcedure

Procedure UpdateMenuItems()
  Protected item = GetGadgetState(#Gadget_ShortcutList)
  Protected itemFound.b
  
  If item = -1
    itemFound = #False
  Else
    itemFound = #True
  EndIf
  
  DisableMenuItem(#Menu_Main, #Menu_EditShortcut, Invert(itemFound))
  DisableMenuItem(#Menu_Main, #Menu_RemoveShortcut, Invert(itemFound))
  DisableToolBarButton(#Toolbar_Main, #Menu_EditShortcut, Invert(itemFound))
  DisableToolBarButton(#Toolbar_Main, #Menu_RemoveShortcut, Invert(itemFound))
EndProcedure

Define defaultConfigDir.s = GetHomeDirectory() + ".config/keyboard-mapper"
Define startHidden.b = #False

CLI_AddOption("c", "config-dir", #True , "path", "path to the config dir (default: " + defaultConfigDir + ")")
CLI_AddOption("H", "hidden", #False, "", "start hidden")
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

If CLI_HasOption("hidden")
  startHidden = #True
EndIf

CreateDirectory(configDir)

configFile = configDir + "/config.ini"
shortcutsFile = configDir + "/shortcuts.ini"

LoadConfig()
LoadShortcutsFromFile()

RestartInputEventListener()

If OpenWindow(#Window_Main, 0, 0, 600, 400, "Keyboard Mapper", #PB_Window_MaximizeGadget | #PB_Window_MinimizeGadget | #PB_Window_ScreenCentered | #PB_Window_Invisible)
  If CreateMenu(#Menu_Main, WindowID(#Window_Main))
    MenuTitle("File")
    MenuItem(#Menu_Settings, "Settings...")
    MenuBar()
    MenuItem(#Menu_Quit, "Quit")
    
    MenuTitle("Edit")
    MenuItem(#Menu_AddShortcut, "Add shortcut...")
    MenuItem(#Menu_EditShortcut, "Edit shortcut...")
    MenuItem(#Menu_RemoveShortcut, "Remove shortcut")
  EndIf
  
  If CreateToolBar(#Toolbar_Main, WindowID(#Window_Main))
    ToolBarStandardButton(#Menu_AddShortcut, #PB_ToolBarIcon_New)
    ToolBarStandardButton(#Menu_EditShortcut, #PB_ToolBarIcon_Properties)
    ToolBarStandardButton(#Menu_RemoveShortcut, #PB_ToolBarIcon_Delete)
    
    ToolBarToolTip(#Toolbar_Main, #Menu_AddShortcut, "Add shortcut")
    ToolBarToolTip(#Toolbar_Main, #Menu_EditShortcut, "Edit shortcut")
    ToolBarToolTip(#Toolbar_Main, #Menu_RemoveShortcut, "Remove shortcut")
  EndIf
  
  ListIconGadget(#Gadget_ShortcutList, 10, 10, 0, 0, "Name", 200, #PB_ListIcon_FullRowSelect | #PB_ListIcon_GridLines)
  AddGadgetColumn(#Gadget_ShortcutList, 1, "Action", 300)
  AddGadgetColumn(#Gadget_ShortcutList, 2, "Key", 100)
  
  UpdateMainGadgetSizes()
  UpdateMenuItems()
  
  ForEach shortcuts()
    UpdateListEntry(-1, Val(MapKey(shortcuts())))
  Next
  
  HideWindow(#Window_Main, startHidden)
  
  Repeat
    Select WaitWindowEvent(10)
      Case #PB_Event_Menu
        Select EventMenu()
          Case #Menu_Settings
            OpenSettingsWindow()
          Case #Menu_Quit
            Break
          Case #Menu_AddShortcut
            EditShortcut(-1)
          Case #Menu_EditShortcut
            Define item = GetGadgetState(#Gadget_ShortcutList)
            If item <> -1
              EditShortcut(item)
            EndIf
          Case #Menu_RemoveShortcut
            Define item = GetGadgetState(#Gadget_ShortcutList)
            If item <> -1
              DeleteMapElement(shortcuts(), Str(GetGadgetItemData(#Gadget_ShortcutList, item)))
              RemoveGadgetItem(#Gadget_ShortcutList, item)
              SaveShortcutsToFile()
            EndIf
        EndSelect
      Case #PB_Event_Gadget
        Select EventGadget()
          Case #Gadget_ShortcutList
            UpdateMenuItems()
            
            Select EventType()
              Case #PB_EventType_LeftDoubleClick
                Define item = GetGadgetState(#Gadget_ShortcutList)
                If item <> -1
                  EditShortcut(item)
                EndIf
            EndSelect
        EndSelect
      Case #PB_Event_SizeWindow
        UpdateMainGadgetSizes()
      Case #PB_Event_CloseWindow
        If EventWindow() = #Window_Main
          Break
        EndIf
    EndSelect
  ForEver
EndIf

If IsThread(inputEventListenerThread)
  KillThread(inputEventListenerThread)
EndIf
; IDE Options = PureBasic 5.62 (Linux - x64)
; CursorPosition = 526
; FirstLine = 506
; Folding = ---
; EnableXP
; Executable = keyboard-mapper