EnableExplicit

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
; IDE Options = PureBasic 5.62 (Linux - x64)
; Folding = -
; EnableXP