EnableExplicit

#NoSymbol = 0

ImportC "-lX11"
  XOpenDisplay(display)
  XCloseDisplay(*display)
  XStringToKeysym(string.p-utf8)
  XKeysymToKeycode(*display, keysym)
  XFlush(*display)
EndImport

ImportC "-lXtst"
  XTestFakeKeyEvent(display, keycode, is_press, delay)
EndImport

Procedure KeyStringToKeycode(*display, key.s)
  Protected symbol = XStringToKeysym(key)
  
  If symbol = #NoSymbol
    ProcedureReturn #Null
  EndIf
  
  Protected code = XKeysymToKeycode(*display, symbol)
  If code = 0
    ProcedureReturn #Null
  EndIf
  
  ProcedureReturn code
EndProcedure

Procedure SendKey(*display, key.s)
  Protected shiftModifier.b
  
  If key = " "
    key = "space"
  EndIf
  
  If key <> LCase(key)
    shiftModifier = #True
  EndIf
  
  Protected shiftCode = KeyStringToKeycode(*display, "Shift_L")
  Protected keyCode = KeyStringToKeycode(*display, key)
  
  If keyCode = #Null
    Debug key
    ProcedureReturn
  EndIf
  
  If shiftModifier
    XTestFakeKeyEvent(*display, shiftCode, #True, 0)
  EndIf
  
  XTestFakeKeyEvent(*display, keyCode, #True, 0)
  XTestFakeKeyEvent(*display, keyCode, #False, 0)
  
  If shiftModifier
    XTestFakeKeyEvent(*display, shiftCode, #False, 0)
  EndIf
  
  XFlush(*display)
EndProcedure

Procedure SendKeyCombination(*display, combination.s)
  Protected NewList pressedKeyCodes()
  
  Protected keyIndex
  For keyIndex = 0 To CountString(combination, "+")
    Protected keyString.s = StringField(combination, keyIndex + 1, "+")
    Protected keyCode = KeyStringToKeycode(*display, keyString)
    If keyCode = #Null
      Continue
    EndIf
    
    XTestFakeKeyEvent(*display, keyCode, #True, 10)
    
    AddElement(pressedKeyCodes())
    pressedKeyCodes() = keyCode
  Next
  
  Protected listIndex
  ;For listIndex = ListSize(pressedKeyCodes()) - 1 To 0 Step -1
  For listIndex = 0 To ListSize(pressedKeyCodes()) - 1
    SelectElement(pressedKeyCodes(), listIndex)
    
    XTestFakeKeyEvent(*display, pressedKeyCodes(), #False, 10)
  Next
  
  XFlush(*display)
EndProcedure

Procedure SendKeySequence(*display, sequence.s)
  Protected combinationIndex
  
  For combinationIndex = 0 To CountString(sequence, " ")
    SendKeyCombination(*display, StringField(sequence, combinationIndex + 1, " "))
  Next
EndProcedure

Procedure ExecuteActionForKey(key, actionHandling)
  Protected keyString.s = Str(key)
  
  If Not FindMapElement(shortcuts(), keyString)
    ProcedureReturn
  EndIf
  
  Protected *display
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
        Protected oldClipboardText.s = GetClipboardText()
        SetClipboardText(shortcut\actionData)
        *display = XOpenDisplay(0)
        SendKeyCombination(*display, "Control_L+V")
        XCloseDisplay(*display)
        SetClipboardText(oldClipboardText)
      Case #Action_InputKeySequence
        *display = XOpenDisplay(0)
        SendKeySequence(*display, shortcut\actionData)
        XCloseDisplay(*display)
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
