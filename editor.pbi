EnableExplicit

Procedure UpdateShortcutActionState()
  DisableGadget(#Gadget_EditShortcut_Action_ExecuteCommand_CommandLine, Invert(GetGadgetState(#Gadget_EditShortcut_Action_ExecuteCommand)))
  DisableGadget(#Gadget_EditShortcut_Action_OpenFolder_Path, Invert(GetGadgetState(#Gadget_EditShortcut_Action_OpenFolder)))
  DisableGadget(#Gadget_EditShortcut_Action_OpenFolder_Browse, Invert(GetGadgetState(#Gadget_EditShortcut_Action_OpenFolder)))
  DisableGadget(#Gadget_EditShortcut_Action_InputText_Text, Invert(GetGadgetState(#Gadget_EditShortcut_Action_InputText)))
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
    shortcutText = "Click to set shortcut"
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
    OptionGadget(#Gadget_EditShortcut_Action_ExecuteCommand, 20, 170, 150, 20, "Execute command")
    OptionGadget(#Gadget_EditShortcut_Action_OpenFolder, 20, 200, 150, 20, "Open folder")
    OptionGadget(#Gadget_EditShortcut_Action_InputText, 20, 230, 150, 20, "Input text")
    StringGadget(#Gadget_EditShortcut_Action_ExecuteCommand_CommandLine, 200, 170, 380, 20, "")
    StringGadget(#Gadget_EditShortcut_Action_OpenFolder_Path, 200, 200, 250, 20, "", #PB_String_ReadOnly)
    ButtonGadget(#Gadget_EditShortcut_Action_OpenFolder_Browse, 460, 200, 120, 20, "Browse...")
    StringGadget(#Gadget_EditShortcut_Action_InputText_Text, 200, 230, 380, 20, "")
    
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
    DisableWindow(#Window_EditShortcut, #False); With QT5 the child window is disabled after disabling the parent
    
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
