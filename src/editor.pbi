EnableExplicit

Enumeration Gadget
  #Gadget_EditShortcut_Shortcut_Frame
  #Gadget_EditShortcut_Shortcut
  #Gadget_EditShortcut_Name_Frame
  #Gadget_EditShortcut_Name
  #Gadget_EditShortcut_Action_Frame
  #Gadget_EditShortcut_Action_LaunchApplication
  #Gadget_EditShortcut_Action_LaunchApplication_List
  #Gadget_EditShortcut_Action_ExecuteCommand
  #Gadget_EditShortcut_Action_ExecuteCommand_CommandLine
  #Gadget_EditShortcut_Action_OpenFolder
  #Gadget_EditShortcut_Action_OpenFolder_Path
  #Gadget_EditShortcut_Action_OpenFolder_Browse
  #Gadget_EditShortcut_Action_InputText
  #Gadget_EditShortcut_Action_InputText_Text
  #Gadget_EditShortcut_Action_InputKeySequence
  #Gadget_EditShortcut_Action_InputKeySequence_Sequence
  #Gadget_EditShortcut_Action_LockKeys
  #Gadget_EditShortcut_Save
  #Gadget_EditShortcut_Cancel
  #Gadget_KeyRequester_Text
  #Gadget_KeyRequester_Cancel
EndEnumeration

Enumeration MenuItem
  #Menu_EditShortcut_Save
  #Menu_EditShortcut_Cancel
EndEnumeration

Procedure IconTheme_LoadIconFromName(iconName.s, iconSize, flags)
  Protected *error.GError
  Protected *buffer = gtk_icon_theme_load_icon(gtk_icon_theme_get_default_(), iconName, iconSize, flags, @*error)
  
  ProcedureReturn *buffer
EndProcedure

Procedure KeyRequester()
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
        Case #Event_KeyInput
          CloseWindow(#Window_KeyRequester)
          DisableWindow(#Window_EditShortcut, #False)
          ProcedureReturn EventData()
      EndSelect
    ForEver
    
    CloseWindow(#Window_KeyRequester)
    DisableWindow(#Window_EditShortcut, #False)
  EndIf
EndProcedure

Procedure UpdateLaunchApplicationActionToolTip()
  Protected item = GetGadgetState(#Gadget_EditShortcut_Action_LaunchApplication_List)
  
  If item = -1
    GadgetToolTip(#Gadget_EditShortcut_Action_LaunchApplication_List, "")
  Else
    SelectElement(applicationList(), item)
    GadgetToolTip(#Gadget_EditShortcut_Action_LaunchApplication_List, applicationList()\exec)
  EndIf
EndProcedure

Procedure UpdateShortcutActionState()
  DisableGadget(#Gadget_EditShortcut_Action_LaunchApplication_List, Invert(GetGadgetState(#Gadget_EditShortcut_Action_LaunchApplication)))
  DisableGadget(#Gadget_EditShortcut_Action_ExecuteCommand_CommandLine, Invert(GetGadgetState(#Gadget_EditShortcut_Action_ExecuteCommand)))
  DisableGadget(#Gadget_EditShortcut_Action_OpenFolder_Path, Invert(GetGadgetState(#Gadget_EditShortcut_Action_OpenFolder)))
  DisableGadget(#Gadget_EditShortcut_Action_OpenFolder_Browse, Invert(GetGadgetState(#Gadget_EditShortcut_Action_OpenFolder)))
  DisableGadget(#Gadget_EditShortcut_Action_InputText_Text, Invert(GetGadgetState(#Gadget_EditShortcut_Action_InputText)))
  DisableGadget(#Gadget_EditShortcut_Action_InputKeySequence_Sequence, Invert(GetGadgetState(#Gadget_EditShortcut_Action_InputKeySequence)))
EndProcedure

Procedure LoadApplicationList()
  ClearList(applicationList())
  LoadApplicationDesktopFiles("/usr/share/applications", applicationList())
  LoadApplicationDesktopFiles(GetHomeDirectory() + ".local/share/applications", applicationList())
  SortStructuredList(applicationList(), 0, OffsetOf(DesktopEntry\name), TypeOf(DesktopEntry\name))
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
  
  If GetGadgetState(#Gadget_EditShortcut_Action_LaunchApplication)
    item = GetGadgetState(#Gadget_EditShortcut_Action_LaunchApplication_List)
    
    If item = -1
      MessageRequester("Missing application", "Please selected the application to launch!", #PB_MessageRequester_Error)
      ProcedureReturn #False
    EndIf
    
    SelectElement(applicationList(), item)
    shortcut\action = #Action_LaunchApplication
    shortcut\actionData = applicationList()\filename
  ElseIf GetGadgetState(#Gadget_EditShortcut_Action_ExecuteCommand)
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
  ElseIf GetGadgetState(#Gadget_EditShortcut_Action_InputKeySequence)
    shortcut\action = #Action_InputKeySequence
    shortcut\actionData = GetGadgetText(#Gadget_EditShortcut_Action_InputKeySequence_Sequence)
    
    If shortcut\actionData = ""
      MessageRequester("Missing key sequence", "Please specify the key sequence to input!", #PB_MessageRequester_Error)
      ProcedureReturn #False
    EndIf
  ElseIf GetGadgetState(#Gadget_EditShortcut_Action_LockKeys)
    shortcut\action = #Action_LockKeys
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
    shortcutText = "Click to set shortcut"
    name = ""
  Else
    windowTitle = "Edit shortcut"
    
    shortcutKey = GetGadgetItemData(#Gadget_ShortcutList, editShortcutItem)
    shortcut = shortcuts(Str(shortcutKey))
    shortcutText = "Key " + Str(shortcutKey)
    name = shortcut\name
  EndIf
  
  If OpenWindow(#Window_EditShortcut, 0, 0, 600, 400, windowTitle, #PB_Window_WindowCentered, WindowID(#Window_Main))
    FrameGadget(#Gadget_EditShortcut_Shortcut_Frame, 10, 10, 580, 60, "Shortcut")
    ButtonGadget(#Gadget_EditShortcut_Shortcut, 20, 30, 560, 20, shortcutText)
    
    FrameGadget(#Gadget_EditShortcut_Name_Frame, 10, 80, 580, 60, "Name")
    StringGadget(#Gadget_EditShortcut_Name, 20, 100, 560, 20, name)
    
    FrameGadget(#Gadget_EditShortcut_Action_Frame, 10, 150, 580, 200, "Action")
    OptionGadget(#Gadget_EditShortcut_Action_LaunchApplication, 20, 170, 150, 20, "Launch application")
    OptionGadget(#Gadget_EditShortcut_Action_ExecuteCommand, 20, 200, 150, 20, "Execute command")
    OptionGadget(#Gadget_EditShortcut_Action_OpenFolder, 20, 230, 150, 20, "Open folder")
    OptionGadget(#Gadget_EditShortcut_Action_InputText, 20, 260, 150, 20, "Input text")
    OptionGadget(#Gadget_EditShortcut_Action_InputKeySequence, 20, 290, 150, 20, "Input key sequence")
    OptionGadget(#Gadget_EditShortcut_Action_LockKeys, 20, 320, 150, 20, "Lock keys")
    ComboBoxGadget(#Gadget_EditShortcut_Action_LaunchApplication_List, 200, 170, 380, 20, #PB_ComboBox_Image)
    StringGadget(#Gadget_EditShortcut_Action_ExecuteCommand_CommandLine, 200, 200, 380, 20, "")
    StringGadget(#Gadget_EditShortcut_Action_OpenFolder_Path, 200, 230, 250, 20, "", #PB_String_ReadOnly)
    ButtonGadget(#Gadget_EditShortcut_Action_OpenFolder_Browse, 460, 230, 120, 20, "Browse...")
    StringGadget(#Gadget_EditShortcut_Action_InputText_Text, 200, 260, 380, 20, "")
    StringGadget(#Gadget_EditShortcut_Action_InputKeySequence_Sequence, 200, 290, 380, 20, "")
    
    ButtonGadget(#Gadget_EditShortcut_Save, 380, 360, 100, 30, "Save")
    ButtonGadget(#Gadget_EditShortcut_Cancel, 490, 360, 100, 30, "Cancel")
    
    AddKeyboardShortcut(#Window_EditShortcut, #PB_Shortcut_Return, #Menu_EditShortcut_Save)
    AddKeyboardShortcut(#Window_EditShortcut, #PB_Shortcut_Escape, #Menu_EditShortcut_Cancel)
    
    If Not ListSize(applicationList())
      LoadApplicationList()
    EndIf
    
    ForEach applicationList()
      Protected imageID = 0
      
      If applicationList()\icon
        If Mid(applicationList()\icon, 1, 1) = "/"
          If LoadImage(#Image_ApplicationListIcon, applicationList()\icon)
            ResizeImage(#Image_ApplicationListIcon, 20, 20)
            imageID = ImageID(#Image_ApplicationListIcon)
          EndIf
        Else
          imageID = IconTheme_LoadIconFromName(applicationList()\icon, 20, 16)
        EndIf
      EndIf
      
      AddGadgetItem(#Gadget_EditShortcut_Action_LaunchApplication_List, -1, applicationList()\name, imageID)
    Next
    
    Select shortcut\action
      Case #Action_LaunchApplication
        SetGadgetState(#Gadget_EditShortcut_Action_LaunchApplication, #True)
        
        ForEach applicationList()
          If applicationList()\filename = shortcut\actionData
            SetGadgetState(#Gadget_EditShortcut_Action_LaunchApplication_List, ListIndex(applicationList()))
            Break
          EndIf
        Next
      Case #Action_ExecuteCommand
        SetGadgetState(#Gadget_EditShortcut_Action_ExecuteCommand, #True)
        SetGadgetText(#Gadget_EditShortcut_Action_ExecuteCommand_CommandLine, shortcut\actionData)
      Case #Action_OpenFolder
        SetGadgetState(#Gadget_EditShortcut_Action_OpenFolder, #True)
        SetGadgetText(#Gadget_EditShortcut_Action_OpenFolder_Path, shortcut\actionData)
      Case #Action_InputText
        SetGadgetState(#Gadget_EditShortcut_Action_InputText, #True)
        SetGadgetText(#Gadget_EditShortcut_Action_InputText_Text, shortcut\actionData)
      Case #Action_InputKeySequence
        SetGadgetState(#Gadget_EditShortcut_Action_InputKeySequence, #True)
        SetGadgetText(#Gadget_EditShortcut_Action_InputKeySequence_Sequence, shortcut\actionData)
      Case #Action_LockKeys
        SetGadgetState(#Gadget_EditShortcut_Action_LockKeys, #True)
    EndSelect
    
    SetGadgetData(#Gadget_EditShortcut_Shortcut, shortcutKey)
    
    UpdateLaunchApplicationActionToolTip()
    UpdateShortcutActionState()
    
    DisableWindow(#Window_Main, #True)
    DisableWindow(#Window_EditShortcut, #False); With QT5 the child window is disabled after disabling the parent
    
    allowActionHandling = #ActionHandling_None
    
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
            Case #Gadget_EditShortcut_Action_LaunchApplication
              UpdateShortcutActionState()
            Case #Gadget_EditShortcut_Action_ExecuteCommand
              UpdateShortcutActionState()
            Case #Gadget_EditShortcut_Action_OpenFolder
              UpdateShortcutActionState()
            Case #Gadget_EditShortcut_Action_InputText
              UpdateShortcutActionState()
            Case #Gadget_EditShortcut_Action_InputKeySequence
              UpdateShortcutActionState()
            Case #Gadget_EditShortcut_Action_LockKeys
              UpdateShortcutActionState()
            Case #Gadget_EditShortcut_Action_LaunchApplication_List
              Select EventType()
                Case #PB_EventType_Change
                  UpdateLaunchApplicationActionToolTip()
              EndSelect
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
    
    allowActionHandling = #ActionHandling_All
  EndIf
EndProcedure
