EnableExplicit

Procedure ExecuteActionForKey(key, actionHandling)
  Protected keyString.s = Str(key)
  
  If Not FindMapElement(shortcuts(), keyString)
    ProcedureReturn
  EndIf
  
  Protected shortcut.Shortcut = shortcuts(keyString)
  If actionHandling = #ActionHandling_All Or shortcut\action = #Action_LockKeys
    Select shortcut\action
      Case #Action_LaunchApplication
        ; Workaround as gtk-launch only wants the filename, not the full path
        Protected tempDesktopFile.s = GetHomeDirectory() + "/.local/share/applications/keyboard-mapper-tmp.desktop"
        CopyFile(shortcut\actionData, tempDesktopFile)
        
        RunProgram("gtk-launch", GetFilePart(tempDesktopFile), "", #PB_Program_Wait)
        
        DeleteFile(tempDesktopFile)
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
        RunStandardProgram(shortcut\actionData, "")
      Case #Action_InputText
        ; TODO: Send keys to active application
      Case #Action_LockKeys
        If actionHandling = #ActionHandling_All
          allowActionHandling = #ActionHandling_LockKeys
        Else
          allowActionHandling = #ActionHandling_All
        EndIf
    EndSelect
  EndIf
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
    
    If allowActionHandling <> #ActionHandling_None
      ExecuteActionForKey(inputEvent\code, allowActionHandling)
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